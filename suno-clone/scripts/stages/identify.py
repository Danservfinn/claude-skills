#!/usr/bin/env python3
"""Identify songs via audio fingerprinting (Chromaprint → AcoustID → MusicBrainz)."""

import json
import os
import subprocess
import sys
import time

import requests


ACOUSTID_API = "https://api.acoustid.org/v2/lookup"
MUSICBRAINZ_API = "https://musicbrainz.org/ws/2"
USER_AGENT = "SunoClone/1.0 (https://github.com/openclaw)"

# MusicBrainz rate limit: 1 request per second
_last_mb_request = 0.0


def _rate_limit_mb():
    """Enforce MusicBrainz 1 req/s rate limit."""
    global _last_mb_request
    elapsed = time.time() - _last_mb_request
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_mb_request = time.time()


def fingerprint(audio_path: str) -> dict:
    """Generate Chromaprint fingerprint via fpcalc.

    Returns:
        dict with "fingerprint" and "duration" keys
    """
    try:
        result = subprocess.run(
            ["fpcalc", "-json", audio_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"error": f"fpcalc failed: {result.stderr}"}
        return json.loads(result.stdout)
    except FileNotFoundError:
        return {"error": "fpcalc not found — install chromaprint: brew install chromaprint"}
    except subprocess.TimeoutExpired:
        return {"error": "fpcalc timed out"}


def lookup_acoustid(fp: str, duration: float, api_key: str) -> dict:
    """Look up a fingerprint on AcoustID.

    Returns:
        dict with "score", "recording_id", "title", "artist" if found
    """
    params = {
        "client": api_key,
        "fingerprint": fp,
        "duration": int(duration),
        "meta": "recordings releasegroups compress",
    }

    try:
        resp = requests.get(ACOUSTID_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"AcoustID lookup failed: {e}"}

    if data.get("status") != "ok" or not data.get("results"):
        return {"score": 0, "source": "acoustid_no_match"}

    best = data["results"][0]
    score = best.get("score", 0)

    if score < 0.5:
        return {"score": score, "source": "acoustid_low_confidence"}

    recordings = best.get("recordings", [])
    if not recordings:
        return {"score": score, "source": "acoustid_no_recordings"}

    rec = recordings[0]
    release_groups = rec.get("releasegroups", [])

    return {
        "score": score,
        "recording_id": rec.get("id"),
        "title": rec.get("title", ""),
        "artists": [a.get("name", "") for a in rec.get("artists", [])],
        "release_group": release_groups[0].get("title", "") if release_groups else "",
        "source": "acoustid",
    }


def lookup_musicbrainz(recording_id: str) -> dict:
    """Fetch detailed metadata from MusicBrainz for a recording ID.

    Returns:
        dict with artist, album, year, genre_tags, credits
    """
    _rate_limit_mb()

    url = f"{MUSICBRAINZ_API}/recording/{recording_id}"
    params = {
        "inc": "artists artist-credits releases tags genres",
        "fmt": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"MusicBrainz lookup failed: {e}"}

    # Extract artist
    artists = []
    for ac in data.get("artist-credit", []):
        if "artist" in ac:
            artists.append(ac["artist"].get("name", ""))

    # Extract release info (album, year)
    album = ""
    year = None
    releases = data.get("releases", [])
    if releases:
        album = releases[0].get("title", "")
        date_str = releases[0].get("date", "")
        if date_str and len(date_str) >= 4:
            try:
                year = int(date_str[:4])
            except ValueError:
                pass

    # Extract tags/genres
    tags = [t.get("name", "") for t in data.get("tags", [])]
    genres = [g.get("name", "") for g in data.get("genres", [])]

    return {
        "title": data.get("title", ""),
        "artist": ", ".join(artists) if artists else "",
        "album": album,
        "year": year,
        "genre_tags": list(set(tags + genres)),
        "musicbrainz_id": recording_id,
        "source": "musicbrainz",
    }


def identify(audio_path: str, api_key: str = None) -> dict:
    """Identify a song from an audio file.

    Args:
        audio_path: Path to audio file (FLAC, WAV, etc.)
        api_key: AcoustID API key. If None, reads from ACOUSTID_API_KEY env var.

    Returns:
        dict with identification results matching the style card schema
    """
    api_key = api_key or os.environ.get("ACOUSTID_API_KEY")

    if not api_key:
        return {
            "title": "",
            "artist": "",
            "album": "",
            "year": None,
            "genre_tags": [],
            "identification_confidence": 0.0,
            "source": "no_api_key",
            "warning": "Set ACOUSTID_API_KEY for song identification",
        }

    # Step 1: Fingerprint
    print("  Fingerprinting audio...", file=sys.stderr)
    fp_result = fingerprint(audio_path)
    if "error" in fp_result:
        return {
            "title": "", "artist": "", "album": "", "year": None,
            "genre_tags": [], "identification_confidence": 0.0,
            "source": "fingerprint_error",
            "error": fp_result["error"],
        }

    # Step 2: AcoustID lookup
    print("  Looking up on AcoustID...", file=sys.stderr)
    aid_result = lookup_acoustid(
        fp_result["fingerprint"], fp_result["duration"], api_key
    )
    if aid_result.get("score", 0) < 0.5 or "error" in aid_result:
        return {
            "title": "", "artist": "", "album": "", "year": None,
            "genre_tags": [], "identification_confidence": aid_result.get("score", 0),
            "source": aid_result.get("source", "acoustid_error"),
        }

    # Step 3: MusicBrainz enrichment
    recording_id = aid_result.get("recording_id")
    if recording_id:
        print("  Enriching from MusicBrainz...", file=sys.stderr)
        mb_result = lookup_musicbrainz(recording_id)
        if "error" not in mb_result:
            return {
                "title": mb_result.get("title") or aid_result.get("title", ""),
                "artist": mb_result.get("artist") or ", ".join(aid_result.get("artists", [])),
                "album": mb_result.get("album", ""),
                "year": mb_result.get("year"),
                "genre_tags": mb_result.get("genre_tags", []),
                "identification_confidence": aid_result["score"],
                "musicbrainz_id": recording_id,
                "source": "acoustid+musicbrainz",
            }

    # Fallback: AcoustID data only
    return {
        "title": aid_result.get("title", ""),
        "artist": ", ".join(aid_result.get("artists", [])),
        "album": aid_result.get("release_group", ""),
        "year": None,
        "genre_tags": [],
        "identification_confidence": aid_result["score"],
        "source": "acoustid_only",
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Identify a song from audio file")
    parser.add_argument("audio_path", help="Path to audio file")
    parser.add_argument("--api-key", help="AcoustID API key")
    args = parser.parse_args()

    result = identify(args.audio_path, args.api_key)
    print(json.dumps(result, indent=2))

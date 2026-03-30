#!/usr/bin/env python3
"""Main orchestrator for suno-clone audio analysis pipeline.

Usage:
    python analyze.py <youtube-url-or-file-path>
    python analyze.py --regenerate <video-id>
    python analyze.py --skip-download <video-id>
"""

import argparse
import json
import os
import sys
import time

# Add stages and utils to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from stages.download import download, extract_video_id, is_url
from stages.identify import identify
from stages.audio_analysis import analyze
from stages.source_separation import separate
from stages.structure_analysis import analyze_structure
from stages.vocal_analysis import analyze_vocals
from stages.prompt_generator import (
    generate_style_card, generate_suno_prompt,
    prepare_claude_translation_prompt, save_outputs,
)
from utils.cleanup import cleanup, check_disk_space, get_free_space_gb


DATA_DIR = os.path.expanduser("~/.openclaw/data/suno-clone")
TMP_DIR = "/tmp/suno-clone"
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.json")


def load_catalog() -> dict:
    """Load the catalog of analyzed songs."""
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH) as f:
            return json.load(f)
    return {}


def save_catalog(catalog: dict):
    """Save the catalog with file locking for concurrent safety."""
    import fcntl
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CATALOG_PATH, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            existing = json.load(f)
        except (json.JSONDecodeError, ValueError):
            existing = {}
        existing.update(catalog)
        f.seek(0)
        f.truncate()
        json.dump(existing, f, indent=2, default=str)


def update_catalog(video_id: str, identification: dict, output_dir: str):
    """Add or update an entry in the catalog."""
    catalog = load_catalog()
    catalog[video_id] = {
        "title": identification.get("title", ""),
        "artist": identification.get("artist", ""),
        "output_dir": output_dir,
        "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_catalog(catalog)


def log(stage: str, msg: str):
    """Log progress to stderr."""
    print(f"[{stage}] {msg}", file=sys.stderr)


def main(url_or_path: str, skip_download: bool = False,
         regenerate: bool = False) -> dict:
    """Run the full analysis pipeline.

    Args:
        url_or_path: YouTube URL, file path, or video ID (for regenerate)
        skip_download: If True, use existing audio in /tmp/suno-clone/
        regenerate: If True, regenerate prompt from existing style card

    Returns:
        dict with video_id, output_dir, style_card, suno_prompt, claude_translation_prompt
    """
    t_total = time.time()

    # Determine video ID
    video_id = extract_video_id(url_or_path)
    output_dir = os.path.join(DATA_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)

    log("INIT", f"Video ID: {video_id}")
    log("INIT", f"Output: {output_dir}")

    # --- REGENERATE MODE ---
    if regenerate:
        style_card_path = os.path.join(output_dir, "style-card.json")
        if not os.path.exists(style_card_path):
            raise FileNotFoundError(f"No style card found at {style_card_path}")

        log("REGEN", "Loading existing style card...")
        with open(style_card_path) as f:
            style_card = json.load(f)

        suno_prompt = generate_suno_prompt(style_card)
        claude_prompt = prepare_claude_translation_prompt(style_card, suno_prompt)
        save_outputs(style_card, suno_prompt, claude_prompt, output_dir)

        elapsed = time.time() - t_total
        log("DONE", f"Prompt regenerated in {elapsed:.1f}s")

        return {
            "video_id": video_id,
            "output_dir": output_dir,
            "style_card": style_card,
            "suno_prompt": suno_prompt,
            "claude_translation_prompt": claude_prompt,
        }

    # --- FULL ANALYSIS MODE ---

    # Pre-flight
    free_gb = get_free_space_gb()
    log("PREFLIGHT", f"Free disk: {free_gb:.1f} GB")
    if not check_disk_space(min_gb=5.0):
        raise RuntimeError(f"Insufficient disk space: {free_gb:.1f} GB free (need >= 5 GB)")

    # Stage 1: Download
    if skip_download:
        import glob
        audio_files = glob.glob(os.path.join(TMP_DIR, f"{video_id}.*"))
        flacs = [f for f in audio_files if f.endswith(".flac")]
        if not flacs:
            raise FileNotFoundError(f"No FLAC found for {video_id} in {TMP_DIR}")
        audio_path = flacs[0]
        metadata = {}
        log("DOWNLOAD", "Skipped (using existing file)")
    else:
        t = time.time()
        log("DOWNLOAD", "Downloading audio...")
        dl_result = download(url_or_path)
        audio_path = dl_result["audio_path"]
        metadata = dl_result.get("metadata", {})
        video_id = dl_result.get("video_id", video_id)
        output_dir = os.path.join(DATA_DIR, video_id)
        os.makedirs(output_dir, exist_ok=True)
        log("DOWNLOAD", f"Done in {time.time()-t:.1f}s — {os.path.basename(audio_path)}")

        if dl_result.get("warnings"):
            log("DOWNLOAD", f"Warnings: {dl_result['warnings']}")

    # Save raw metadata
    if metadata:
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

    # Stage 2: Identify
    t = time.time()
    log("IDENTIFY", "Identifying song...")
    identification = identify(audio_path)
    # Merge YouTube metadata into identification
    if metadata and not identification.get("title"):
        identification["title"] = metadata.get("title", "")
        identification["artist"] = metadata.get("artist", "")
    log("IDENTIFY", f"Done in {time.time()-t:.1f}s — {identification.get('title', 'Unknown')} by {identification.get('artist', 'Unknown')}")

    # Stage 3a: Audio analysis (Essentia + librosa)
    t = time.time()
    log("ANALYZE", "Running audio analysis...")
    analysis = analyze(audio_path)
    log("ANALYZE", f"Done in {time.time()-t:.1f}s — BPM={analysis['tempo']['bpm']}, Key={analysis['key']['key']} {analysis['key']['scale']}")

    # Stage 3b: Source separation
    t = time.time()
    log("SEPARATE", "Separating sources (demucs-mlx)...")
    try:
        stems = separate(audio_path)
        log("SEPARATE", f"Done in {time.time()-t:.1f}s")
    except Exception as e:
        log("SEPARATE", f"FAILED: {e} — skipping vocal analysis")
        stems = {"vocals": None, "drums": None, "bass": None, "other": None}

    # Stage 3c: Structure analysis
    t = time.time()
    log("STRUCTURE", "Analyzing song structure...")
    try:
        structure = analyze_structure(audio_path)
        log("STRUCTURE", f"Done in {time.time()-t:.1f}s — {len(structure)} sections")
    except Exception as e:
        log("STRUCTURE", f"FAILED: {e} — using basic structure")
        from librosa import get_duration
        dur = get_duration(path=audio_path)
        structure = [
            {"section": "intro", "start": 0, "end": dur * 0.1, "duration": dur * 0.1},
            {"section": "verse", "start": dur * 0.1, "end": dur * 0.4, "duration": dur * 0.3},
            {"section": "chorus", "start": dur * 0.4, "end": dur * 0.6, "duration": dur * 0.2},
            {"section": "verse", "start": dur * 0.6, "end": dur * 0.8, "duration": dur * 0.2},
            {"section": "outro", "start": dur * 0.8, "end": dur, "duration": dur * 0.2},
        ]

    # Stage 3d: Vocal analysis
    t = time.time()
    if stems.get("vocals") and os.path.exists(stems["vocals"]):
        log("VOCALS", "Analyzing vocals...")
        try:
            vocals = analyze_vocals(stems["vocals"])
            log("VOCALS", f"Done in {time.time()-t:.1f}s — {'present' if vocals.get('present') else 'not present'}")
        except Exception as e:
            log("VOCALS", f"FAILED: {e}")
            vocals = {"present": False, "error": str(e)}
    else:
        log("VOCALS", "No vocal stem available — skipping")
        vocals = {"present": False, "classifier_source": "no_stem"}

    # Stage 4: Generate style card
    t = time.time()
    log("STYLECRD", "Generating Style Reference Card...")
    style_card = generate_style_card(
        analysis, identification, structure, vocals,
        video_id=video_id, source_url=url_or_path, stems=stems,
    )
    log("STYLECRD", f"Done in {time.time()-t:.1f}s")

    # Stage 5: Generate Suno prompt
    t = time.time()
    log("PROMPT", "Generating Suno prompt...")
    suno_prompt = generate_suno_prompt(style_card)
    claude_prompt = prepare_claude_translation_prompt(style_card, suno_prompt)
    log("PROMPT", f"Done in {time.time()-t:.1f}s")

    # Save all outputs
    save_outputs(style_card, suno_prompt, claude_prompt, output_dir)
    update_catalog(video_id, identification, output_dir)

    # Cleanup temp files
    freed = cleanup(video_id)
    if freed > 0:
        log("CLEANUP", f"Freed {freed / 1024 / 1024:.1f} MB of temp files")

    elapsed = time.time() - t_total
    log("DONE", f"Complete pipeline in {elapsed:.1f}s")
    log("DONE", f"Output: {output_dir}")

    return {
        "video_id": video_id,
        "output_dir": output_dir,
        "style_card": style_card,
        "suno_prompt": suno_prompt,
        "claude_translation_prompt": claude_prompt,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Suno Clone — analyze music and generate Suno v5.5 prompts"
    )
    parser.add_argument(
        "url_or_path",
        help="YouTube URL, local audio file path, or video ID (with --regenerate)"
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download, use existing audio in /tmp/suno-clone/"
    )
    parser.add_argument(
        "--regenerate", action="store_true",
        help="Regenerate Suno prompt from existing style card"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON to stdout"
    )
    args = parser.parse_args()

    try:
        result = main(
            args.url_or_path,
            skip_download=args.skip_download,
            regenerate=args.regenerate,
        )

        if args.json:
            # Output full result as JSON
            print(json.dumps(result, indent=2, default=str))
        else:
            # Print the Suno prompt to stdout
            print("\n" + "=" * 60)
            print("SUNO v5.5 PROMPT")
            print("=" * 60)
            print(result["suno_prompt"])
            print("\n" + "=" * 60)
            print(f"Style card saved to: {result['output_dir']}/style-card.json")
            print(f"Full prompt saved to: {result['output_dir']}/suno-prompt.md")
            print("=" * 60)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

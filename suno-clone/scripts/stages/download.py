#!/usr/bin/env python3
"""Download audio from YouTube or handle local files for analysis."""

import json
import os
import re
import shutil
import subprocess
import sys
import time


TMP_DIR = "/tmp/suno-clone"


def extract_video_id(url_or_path: str) -> str:
    """Extract YouTube video ID from URL, or generate ID for local files."""
    # YouTube URL patterns
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # bare video ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_path)
        if match:
            return match.group(1)

    # Local file — use filename without extension as ID
    if os.path.exists(url_or_path):
        base = os.path.splitext(os.path.basename(url_or_path))[0]
        # Sanitize
        return re.sub(r'[^a-zA-Z0-9_-]', '_', base)[:50]

    # Fallback: hash the input
    import hashlib
    return hashlib.md5(url_or_path.encode()).hexdigest()[:11]


def is_url(s: str) -> bool:
    """Check if input is a URL (vs local file path)."""
    return bool(re.match(r'https?://', s)) or 'youtube.com' in s or 'youtu.be' in s


def download(url_or_path: str, output_dir: str = TMP_DIR) -> dict:
    """Download audio from YouTube URL or prepare local file for analysis.

    Args:
        url_or_path: YouTube URL or path to local audio file
        output_dir: Directory to write files to

    Returns:
        dict with keys: audio_path, metadata_path, video_id, metadata, warnings
    """
    os.makedirs(output_dir, exist_ok=True)
    video_id = extract_video_id(url_or_path)
    warnings = []

    if is_url(url_or_path):
        return _download_youtube(url_or_path, video_id, output_dir, warnings)
    elif os.path.exists(url_or_path):
        return _handle_local_file(url_or_path, video_id, output_dir, warnings)
    else:
        raise FileNotFoundError(f"Not a valid URL or file path: {url_or_path}")


def _download_youtube(url: str, video_id: str, output_dir: str, warnings: list) -> dict:
    """Download audio from YouTube via yt-dlp."""
    output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")
    info_path = os.path.join(output_dir, f"{video_id}.info.json")

    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "flac", "--audio-quality", "0",
        "--write-info-json",
        "--no-playlist",
        "-o", output_template,
        url,
    ]

    # Try with cookies first for age-restricted content
    for attempt in range(3):
        try:
            if attempt > 0:
                print(f"  Retry {attempt}/2...", file=sys.stderr)
                time.sleep(2 * attempt)

            # Add cookies on retry
            if attempt >= 1:
                cmd_with_cookies = cmd + ["--cookies-from-browser", "safari"]
                result = subprocess.run(
                    cmd_with_cookies, capture_output=True, text=True, timeout=120
                )
            else:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

            if result.returncode == 0:
                break

            stderr = result.stderr.lower()
            if "age" in stderr or "sign in" in stderr:
                warnings.append("age_restricted")
                continue
            elif "geo" in stderr or "not available" in stderr:
                raise RuntimeError(f"Video geo-blocked or unavailable: {result.stderr}")
            elif attempt == 2:
                raise RuntimeError(f"yt-dlp failed after 3 attempts: {result.stderr}")

        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise RuntimeError("yt-dlp timed out after 3 attempts")

    # Find the output FLAC file
    audio_path = os.path.join(output_dir, f"{video_id}.flac")
    if not os.path.exists(audio_path):
        # yt-dlp may have used a different name
        import glob
        flacs = glob.glob(os.path.join(output_dir, f"{video_id}*.flac"))
        if flacs:
            audio_path = flacs[0]
        else:
            raise FileNotFoundError(f"FLAC file not found after download in {output_dir}")

    # Parse metadata
    metadata = {}
    if os.path.exists(info_path):
        with open(info_path) as f:
            raw = json.load(f)
        metadata = {
            "title": raw.get("track") or raw.get("title", ""),
            "artist": raw.get("artist") or raw.get("uploader", ""),
            "album": raw.get("album", ""),
            "description": raw.get("description", "")[:500],
            "tags": raw.get("tags", []),
            "duration": raw.get("duration", 0),
            "upload_date": raw.get("upload_date", ""),
            "categories": raw.get("categories", []),
            "channel": raw.get("channel", ""),
        }
    else:
        warnings.append("no_metadata_json")

    # Duration check
    duration = metadata.get("duration", 0)
    if duration and duration < 30:
        warnings.append("short_clip")

    return {
        "audio_path": audio_path,
        "metadata_path": info_path if os.path.exists(info_path) else None,
        "video_id": video_id,
        "metadata": metadata,
        "warnings": warnings,
    }


def _handle_local_file(file_path: str, video_id: str, output_dir: str, warnings: list) -> dict:
    """Prepare a local audio file for analysis."""
    ext = os.path.splitext(file_path)[1].lower()
    supported = {".flac", ".wav", ".mp3", ".m4a", ".ogg", ".opus", ".aac", ".wma"}

    if ext not in supported:
        raise ValueError(f"Unsupported audio format: {ext}")

    # Copy or symlink to output dir
    dest = os.path.join(output_dir, f"{video_id}{ext}")
    if not os.path.exists(dest):
        shutil.copy2(file_path, dest)

    # If not FLAC, convert
    if ext != ".flac":
        flac_path = os.path.join(output_dir, f"{video_id}.flac")
        if not os.path.exists(flac_path):
            subprocess.run(
                ["ffmpeg", "-i", dest, "-c:a", "flac", flac_path],
                capture_output=True, check=True
            )
        audio_path = flac_path
    else:
        audio_path = dest

    metadata = {
        "title": os.path.splitext(os.path.basename(file_path))[0],
        "artist": "",
        "album": "",
        "description": "",
        "tags": [],
        "duration": 0,
        "source": "local_file",
        "original_path": file_path,
    }
    warnings.append("local_file_no_youtube_metadata")

    return {
        "audio_path": audio_path,
        "metadata_path": None,
        "video_id": video_id,
        "metadata": metadata,
        "warnings": warnings,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download audio for suno-clone analysis")
    parser.add_argument("url_or_path", help="YouTube URL or local audio file path")
    parser.add_argument("--output-dir", default=TMP_DIR, help="Output directory")
    args = parser.parse_args()

    result = download(args.url_or_path, args.output_dir)
    print(json.dumps(result, indent=2))

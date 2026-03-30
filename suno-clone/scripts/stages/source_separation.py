#!/usr/bin/env python3
"""Source separation using demucs-mlx (Apple Silicon optimized)."""

import json
import os
import sys
import time


def separate(audio_path: str, output_dir: str = "/tmp/suno-clone") -> dict:
    """Separate audio into 4 stems using demucs-mlx.

    Args:
        audio_path: Path to input audio file
        output_dir: Directory for output stems

    Returns:
        dict with stem paths: vocals, drums, bass, other, plus timing
    """
    from demucs_mlx import Separator, save_audio

    video_id = os.path.splitext(os.path.basename(audio_path))[0]
    stems_dir = os.path.join(output_dir, f"{video_id}_stems")
    os.makedirs(stems_dir, exist_ok=True)

    print("  Separating sources (demucs-mlx)...", file=sys.stderr)
    t0 = time.time()

    try:
        # demucs-mlx API: Separator returns (origin_ndarray, dict_of_stem_ndarrays)
        separator = Separator()
        _, outputs = separator.separate_audio_file(audio_path)

        # outputs is a dict: {"drums": ndarray, "bass": ndarray, "other": ndarray, "vocals": ndarray}
        # Each ndarray has shape (channels, samples)
        import soundfile as sf
        import numpy as np

        result = {"processing_time_s": 0, "model": "htdemucs"}
        for stem_name, stem_data in outputs.items():
            stem_path = os.path.join(stems_dir, f"{stem_name}.wav")
            # soundfile expects (samples, channels) so transpose
            sf.write(stem_path, stem_data.T, samplerate=getattr(separator, 'samplerate', 44100))
            result[stem_name] = stem_path

        elapsed = time.time() - t0
        result["processing_time_s"] = round(elapsed, 1)
        print(f"  Source separation complete in {elapsed:.1f}s", file=sys.stderr)

        return result

    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Source separation failed after {elapsed:.1f}s: {e}", file=sys.stderr)
        return {
            "error": str(e),
            "vocals": None,
            "drums": None,
            "bass": None,
            "other": None,
            "processing_time_s": round(elapsed, 1),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Separate audio into stems")
    parser.add_argument("audio_path", help="Path to audio file")
    parser.add_argument("--output-dir", default="/tmp/suno-clone")
    args = parser.parse_args()

    result = separate(args.audio_path, args.output_dir)
    print(json.dumps(result, indent=2))

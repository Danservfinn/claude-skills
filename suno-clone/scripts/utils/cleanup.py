#!/usr/bin/env python3
"""Temp file cleanup and disk space management for suno-clone."""

import glob
import os
import shutil


TMP_DIR = "/tmp/suno-clone"


def check_disk_space(min_gb: float = 5.0) -> bool:
    """Check if sufficient disk space is available.

    Returns True if free space >= min_gb.
    """
    stat = os.statvfs(os.path.expanduser("~"))
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
    return free_gb >= min_gb


def get_free_space_gb() -> float:
    """Return free disk space in GB."""
    stat = os.statvfs(os.path.expanduser("~"))
    return (stat.f_bavail * stat.f_frsize) / (1024 ** 3)


def cleanup(video_id: str, keep_outputs: bool = True) -> int:
    """Remove temp files for a given video_id.

    Args:
        video_id: The video ID whose temp files to remove
        keep_outputs: If True, don't touch ~/.openclaw/data/suno-clone/{video_id}/

    Returns:
        Bytes freed
    """
    bytes_freed = 0
    patterns = [
        os.path.join(TMP_DIR, f"{video_id}.*"),
        os.path.join(TMP_DIR, f"{video_id}_*"),
    ]

    for pattern in patterns:
        for path in glob.glob(pattern):
            if os.path.isfile(path):
                bytes_freed += os.path.getsize(path)
                os.remove(path)
            elif os.path.isdir(path):
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        bytes_freed += os.path.getsize(fp)
                shutil.rmtree(path)

    return bytes_freed


def cleanup_all() -> int:
    """Remove all temp files in /tmp/suno-clone/."""
    bytes_freed = 0
    if os.path.exists(TMP_DIR):
        for item in os.listdir(TMP_DIR):
            path = os.path.join(TMP_DIR, item)
            if os.path.isfile(path):
                bytes_freed += os.path.getsize(path)
                os.remove(path)
            elif os.path.isdir(path):
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        bytes_freed += os.path.getsize(fp)
                shutil.rmtree(path)
    return bytes_freed


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        vid = sys.argv[1]
        freed = cleanup(vid)
        print(f"Cleaned up {freed / 1024 / 1024:.1f} MB for {vid}")
    else:
        free = get_free_space_gb()
        print(f"Free disk space: {free:.1f} GB")
        print(f"Sufficient (>= 5 GB): {check_disk_space()}")

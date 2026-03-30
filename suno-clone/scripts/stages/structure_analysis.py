#!/usr/bin/env python3
"""Song structure analysis — detects intro, verse, chorus, bridge, outro sections.

Uses librosa-based self-similarity analysis since allin1/madmom are
incompatible with Python 3.10+.
"""

import json
import sys
import time

import librosa
import numpy as np


# Suno-compatible section labels
SECTION_LABELS = [
    "intro", "verse", "pre-chorus", "chorus", "post-chorus",
    "bridge", "breakdown", "build", "drop", "hook",
    "interlude", "outro", "instrumental",
]


def analyze_structure(audio_path: str) -> list:
    """Analyze song structure using self-similarity matrix and novelty detection.

    Returns:
        List of dicts: [{"section": str, "start": float, "end": float, "duration": float}]
    """
    print("  Analyzing song structure...", file=sys.stderr)
    t0 = time.time()

    y, sr = librosa.load(audio_path, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)

    # Compute features for segmentation
    # MFCCs for timbral similarity
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=512)

    # Chroma for harmonic similarity
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)

    # Combine features
    features = np.vstack([mfccs, chroma])

    # Self-similarity matrix
    sim = librosa.segment.recurrence_matrix(
        features, mode="affinity", sym=True, width=3
    )

    # Novelty curve from the self-similarity matrix
    novelty = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)

    # Detect segment boundaries using structural features
    # Use agglomerative clustering on the feature matrix
    n_segments = _estimate_segment_count(duration)

    try:
        boundaries = librosa.segment.agglomerative(features, k=n_segments)
        # Convert frame indices to time
        boundary_times = librosa.frames_to_time(boundaries, sr=sr, hop_length=512)
    except Exception:
        # Fallback: evenly spaced boundaries
        boundary_times = np.linspace(0, duration, n_segments + 1)

    # Ensure boundaries start at 0 and end at duration
    boundary_times = np.unique(np.concatenate([[0], boundary_times, [duration]]))
    boundary_times = np.sort(boundary_times)

    # Remove very short segments (< 5 seconds)
    filtered = [boundary_times[0]]
    for bt in boundary_times[1:]:
        if bt - filtered[-1] >= 5.0 or bt == boundary_times[-1]:
            filtered.append(bt)
    boundary_times = np.array(filtered)

    # Label sections heuristically
    sections = _label_sections(features, boundary_times, sr, duration)

    elapsed = time.time() - t0
    print(f"  Structure analysis complete in {elapsed:.1f}s — {len(sections)} sections", file=sys.stderr)

    return sections


def _estimate_segment_count(duration: float) -> int:
    """Estimate number of segments based on song duration."""
    if duration < 60:
        return 3
    elif duration < 120:
        return 5
    elif duration < 240:
        return 7
    elif duration < 360:
        return 9
    else:
        return 11


def _label_sections(features: np.ndarray, boundaries: np.ndarray,
                     sr: int, duration: float) -> list:
    """Label segments using heuristic rules based on feature similarity.

    Strategy:
    - First segment: "intro" if short (< 15% of song)
    - Last segment: "outro" if short (< 15% of song)
    - Cluster remaining segments by feature similarity
    - Most common cluster = "verse", second most = "chorus"
    - Remaining outlier segments = "bridge"
    """
    n_segments = len(boundaries) - 1
    if n_segments < 1:
        return [{"section": "intro", "start": 0.0, "end": duration, "duration": duration}]

    # Compute mean features per segment
    segment_features = []
    for i in range(n_segments):
        start_frame = librosa.time_to_frames(boundaries[i], sr=sr, hop_length=512)
        end_frame = librosa.time_to_frames(boundaries[i + 1], sr=sr, hop_length=512)
        end_frame = min(end_frame, features.shape[1] - 1)
        if start_frame >= end_frame:
            segment_features.append(np.zeros(features.shape[0]))
        else:
            segment_features.append(np.mean(features[:, start_frame:end_frame], axis=1))

    segment_features = np.array(segment_features)

    # Simple clustering: compute pairwise cosine similarity
    labels = ["verse"] * n_segments

    # First segment heuristic
    first_dur = boundaries[1] - boundaries[0]
    if first_dur < duration * 0.15 and n_segments > 2:
        labels[0] = "intro"

    # Last segment heuristic
    last_dur = boundaries[-1] - boundaries[-2]
    if last_dur < duration * 0.15 and n_segments > 2:
        labels[-1] = "outro"

    # Find similar segments via cosine similarity
    if n_segments >= 4:
        from sklearn.metrics.pairwise import cosine_similarity
        sim_matrix = cosine_similarity(segment_features)

        # For middle segments, find the two most common patterns
        middle_start = 1 if labels[0] == "intro" else 0
        middle_end = n_segments - 1 if labels[-1] == "outro" else n_segments
        middle_indices = list(range(middle_start, middle_end))

        if len(middle_indices) >= 3:
            # Simple 2-cluster: split into more/less energetic
            energies = []
            for i in middle_indices:
                # Use spectral centroid (first MFCC) as energy proxy
                energies.append(float(np.mean(np.abs(segment_features[i]))))

            median_energy = np.median(energies)

            for idx, i in enumerate(middle_indices):
                if energies[idx] >= median_energy:
                    labels[i] = "chorus"
                else:
                    labels[i] = "verse"

            # If there's a single segment that's very different, call it bridge
            if len(middle_indices) >= 5:
                for idx, i in enumerate(middle_indices):
                    # Check similarity to neighbors
                    sims_to_others = []
                    for j in middle_indices:
                        if j != i:
                            sims_to_others.append(sim_matrix[i, j])
                    avg_sim = np.mean(sims_to_others)
                    if avg_sim < 0.5:  # outlier
                        labels[i] = "bridge"

    # Build result list
    sections = []
    for i in range(n_segments):
        start = round(float(boundaries[i]), 1)
        end = round(float(boundaries[i + 1]), 1)
        sections.append({
            "section": labels[i],
            "start": start,
            "end": end,
            "duration": round(end - start, 1),
        })

    return sections


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze song structure")
    parser.add_argument("audio_path", help="Path to audio file")
    args = parser.parse_args()

    sections = analyze_structure(args.audio_path)
    print(json.dumps(sections, indent=2))

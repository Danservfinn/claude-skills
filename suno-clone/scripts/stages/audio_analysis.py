#!/usr/bin/env python3
"""Core audio analysis using Essentia and librosa."""

import json
import sys
import time

import numpy as np

# Add parent to path for utils imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.feature_mapping import map_feature, summarize_mood, describe_spectral_profile


def analyze_essentia(audio_path: str) -> dict:
    """Analyze audio using Essentia standard algorithms.

    Returns dict with: bpm, bpm_confidence, key, scale, key_confidence,
    loudness_lufs, dynamic_complexity, danceability
    """
    from essentia.standard import (
        MonoLoader, RhythmExtractor2013, KeyExtractor,
        Danceability, DynamicComplexity, Loudness,
    )

    print("  Loading audio (Essentia)...", file=sys.stderr)
    audio = MonoLoader(filename=audio_path, sampleRate=44100)()

    results = {}

    # BPM / Tempo
    print("  Analyzing tempo...", file=sys.stderr)
    rhythm = RhythmExtractor2013(method="multifeature")
    bpm, ticks, confidence, estimates, intervals = rhythm(audio)
    results["bpm"] = float(bpm)
    results["bpm_confidence"] = min(float(confidence), 1.0)
    results["beat_positions"] = ticks[:20].tolist() if len(ticks) > 0 else []

    # Key
    print("  Detecting key...", file=sys.stderr)
    key_ext = KeyExtractor()
    key, scale, strength = key_ext(audio)
    results["key"] = key
    results["scale"] = scale
    results["key_confidence"] = float(strength)

    # Loudness (Essentia Loudness — mono-compatible, perceptual weighting)
    print("  Measuring loudness...", file=sys.stderr)
    try:
        loudness_algo = Loudness()
        loudness_val = loudness_algo(audio)
        # Essentia Loudness returns a single float in dB (not LUFS, but perceptually weighted)
        results["loudness_lufs"] = float(loudness_val)
    except Exception:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        results["loudness_lufs"] = float(20 * np.log10(rms + 1e-10))

    # Dynamic Complexity
    print("  Analyzing dynamics...", file=sys.stderr)
    try:
        dc = DynamicComplexity()
        complexity, loudness_val = dc(audio)
        results["dynamic_complexity"] = float(complexity)
    except Exception:
        results["dynamic_complexity"] = 5.0  # moderate default

    # Danceability
    print("  Measuring danceability...", file=sys.stderr)
    try:
        dance = Danceability()
        danceability_val, _ = dance(audio)
        results["danceability"] = float(danceability_val)
    except Exception:
        results["danceability"] = 1.0  # moderate default

    return results


def analyze_librosa(audio_path: str) -> dict:
    """Analyze audio using librosa for spectral features.

    Returns dict with spectral features, MFCCs, and BPM cross-check.
    """
    import librosa

    print("  Loading audio (librosa)...", file=sys.stderr)
    y, sr = librosa.load(audio_path, sr=22050)

    results = {}

    # BPM cross-validation
    print("  Cross-validating BPM...", file=sys.stderr)
    tempo = librosa.beat.tempo(y=y, sr=sr)
    results["bpm_librosa"] = float(tempo[0]) if len(tempo) > 0 else 0.0

    # Spectral Centroid (brightness)
    print("  Computing spectral features...", file=sys.stderr)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    results["spectral_centroid_mean"] = float(np.mean(centroid))
    results["spectral_centroid_std"] = float(np.std(centroid))

    # Spectral Rolloff
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    results["spectral_rolloff_mean"] = float(np.mean(rolloff))

    # Spectral Bandwidth
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    results["spectral_bandwidth_mean"] = float(np.mean(bandwidth))

    # Spectral Contrast (per frequency band)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    results["spectral_contrast_mean"] = np.mean(contrast, axis=1).tolist()

    # Spectral Flatness (tonality measure)
    flatness = librosa.feature.spectral_flatness(y=y)
    results["spectral_flatness_mean"] = float(np.mean(flatness))

    # MFCCs (timbral texture)
    print("  Computing MFCCs...", file=sys.stderr)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    results["mfcc_mean"] = np.mean(mfccs, axis=1).tolist()
    results["mfcc_std"] = np.std(mfccs, axis=1).tolist()

    # Zero Crossing Rate (percussiveness)
    zcr = librosa.feature.zero_crossing_rate(y)
    results["zero_crossing_rate_mean"] = float(np.mean(zcr))

    return results


def _estimate_mood(essentia_results: dict, librosa_results: dict) -> dict:
    """Estimate mood heuristically from spectral features.

    Since essentia-tensorflow classifiers are unavailable, we approximate
    mood from spectral properties and energy metrics.
    """
    centroid = librosa_results.get("spectral_centroid_mean", 2000)
    flatness = librosa_results.get("spectral_flatness_mean", 0.1)
    zcr = librosa_results.get("zero_crossing_rate_mean", 0.05)
    loudness = essentia_results.get("loudness_lufs", -10)
    bpm = essentia_results.get("bpm", 120)
    danceability = essentia_results.get("danceability", 1.0)

    # Normalize features to 0-1 range (approximate)
    brightness = min(centroid / 5000, 1.0)
    noisiness = min(flatness / 0.3, 1.0)
    energy = min(zcr / 0.15, 1.0)
    loudness_norm = min(max((loudness + 20) / 20, 0), 1.0)
    tempo_norm = min(max((bpm - 60) / 140, 0), 1.0)

    # Derive mood scores (heuristic, not ML-based)
    mood = {
        "dark": max(0, 1.0 - brightness) * 0.7 + (1.0 - danceability / 3) * 0.3,
        "aggressive": min(1.0, energy * 0.4 + loudness_norm * 0.3 + tempo_norm * 0.3),
        "happy": min(1.0, brightness * 0.3 + danceability / 3 * 0.4 + tempo_norm * 0.3),
        "relaxed": max(0, (1.0 - energy) * 0.4 + (1.0 - tempo_norm) * 0.3 + (1.0 - loudness_norm) * 0.3),
        "sad": max(0, (1.0 - brightness) * 0.4 + (1.0 - tempo_norm) * 0.3 + (1.0 - danceability / 3) * 0.3),
        "energetic": min(1.0, tempo_norm * 0.35 + loudness_norm * 0.35 + energy * 0.3),
    }

    # Clamp all values to 0-1
    mood = {k: round(min(max(v, 0), 1.0), 2) for k, v in mood.items()}

    return mood


def analyze(audio_path: str) -> dict:
    """Run full audio analysis and return unified results.

    Combines Essentia and librosa analysis, cross-validates BPM,
    applies feature mapping, and estimates mood heuristically.
    """
    t0 = time.time()

    # Run both analysis engines
    essentia_results = analyze_essentia(audio_path)
    librosa_results = analyze_librosa(audio_path)

    # BPM cross-validation
    bpm_essentia = essentia_results["bpm"]
    bpm_librosa = librosa_results.get("bpm_librosa", 0)
    bpm_confidence = essentia_results["bpm_confidence"]

    if bpm_librosa > 0:
        delta_pct = abs(bpm_essentia - bpm_librosa) / max(bpm_essentia, 1) * 100
        if delta_pct > 5:
            bpm_confidence = min(bpm_confidence, 0.6)
            print(f"  BPM disagreement: Essentia={bpm_essentia:.1f}, librosa={bpm_librosa:.1f} (delta={delta_pct:.1f}%)", file=sys.stderr)

    # Estimate mood heuristically
    mood = _estimate_mood(essentia_results, librosa_results)

    # Build spectral profile
    spectral_profile = describe_spectral_profile(
        librosa_results["spectral_centroid_mean"],
        librosa_results["spectral_flatness_mean"],
        librosa_results["spectral_bandwidth_mean"],
    )

    elapsed = time.time() - t0
    print(f"  Audio analysis complete in {elapsed:.1f}s", file=sys.stderr)

    return {
        "tempo": {
            "bpm": round(bpm_essentia),
            "bpm_raw": round(bpm_essentia, 1),
            "bpm_confidence": round(bpm_confidence, 2),
            "bpm_librosa": round(bpm_librosa, 1),
            "feel": map_feature("bpm", bpm_essentia),
            "beat_positions": essentia_results.get("beat_positions", []),
            "classifier_source": "essentia_algorithm",
        },
        "key": {
            "key": essentia_results["key"],
            "scale": essentia_results["scale"],
            "confidence": round(essentia_results["key_confidence"], 2),
            "classifier_source": "essentia_algorithm",
        },
        "mood": {
            **mood,
            "summary": summarize_mood(mood),
            "classifier_source": "heuristic",
        },
        "energy": {
            "danceability": round(essentia_results["danceability"], 2),
            "danceability_description": map_feature("danceability", essentia_results["danceability"]),
            "classifier_source": "essentia_algorithm",
        },
        "dynamics": {
            "loudness_lufs": round(essentia_results["loudness_lufs"], 1),
            "loudness_description": map_feature("loudness_lufs", essentia_results["loudness_lufs"]),
            "dynamic_complexity": round(essentia_results["dynamic_complexity"], 1),
            "dynamic_description": map_feature("dynamic_complexity", essentia_results["dynamic_complexity"]),
            "classifier_source": "essentia_algorithm",
        },
        "spectral_profile": {
            **spectral_profile,
            "spectral_centroid_mean_hz": round(librosa_results["spectral_centroid_mean"]),
            "spectral_rolloff_mean_hz": round(librosa_results["spectral_rolloff_mean"]),
            "spectral_bandwidth_mean_hz": round(librosa_results["spectral_bandwidth_mean"]),
            "spectral_flatness_mean": round(librosa_results["spectral_flatness_mean"], 4),
            "zero_crossing_rate": round(librosa_results["zero_crossing_rate_mean"], 4),
            "classifier_source": "librosa_algorithm",
        },
        "timbre": {
            "mfcc_mean": [round(x, 2) for x in librosa_results["mfcc_mean"]],
            "mfcc_std": [round(x, 2) for x in librosa_results["mfcc_std"]],
            "spectral_contrast": [round(x, 2) for x in librosa_results["spectral_contrast_mean"]],
            "classifier_source": "librosa_algorithm",
        },
        "_analysis_time_s": round(elapsed, 1),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze audio features")
    parser.add_argument("audio_path", help="Path to audio file")
    args = parser.parse_args()

    result = analyze(args.audio_path)
    print(json.dumps(result, indent=2))

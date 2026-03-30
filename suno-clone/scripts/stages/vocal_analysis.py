#!/usr/bin/env python3
"""Vocal analysis on isolated vocal stem — pitch, gender, breathiness, raspiness."""

import json
import sys
import time

import librosa
import numpy as np

# Add parent to path for utils imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.feature_mapping import map_feature


def analyze_vocals(vocal_stem_path: str) -> dict:
    """Analyze vocal characteristics from an isolated vocal stem.

    Args:
        vocal_stem_path: Path to vocal stem WAV file (from Demucs)

    Returns:
        dict with: present, gender, register, pitch_range_hz,
        breathiness, raspiness, vibrato, style_summary
    """
    print("  Analyzing vocals...", file=sys.stderr)
    t0 = time.time()

    y, sr = librosa.load(vocal_stem_path, sr=22050)

    # Check if vocals are actually present (RMS energy check)
    rms = float(np.sqrt(np.mean(y ** 2)))
    if rms < 0.005:
        print("  No significant vocal energy detected", file=sys.stderr)
        return {"present": False, "classifier_source": "rms_energy"}

    # Pitch tracking via pYIN
    print("  Tracking pitch...", file=sys.stderr)
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=65, fmax=1047, sr=sr
    )

    # Filter to voiced frames
    voiced_f0 = f0[~np.isnan(f0)]
    if len(voiced_f0) < 10:
        print("  Too few voiced frames for analysis", file=sys.stderr)
        return {"present": False, "classifier_source": "insufficient_voiced_frames"}

    pitch_min = float(np.percentile(voiced_f0, 5))
    pitch_max = float(np.percentile(voiced_f0, 95))
    pitch_median = float(np.median(voiced_f0))

    # Gender estimation from median pitch
    if pitch_median < 165:
        gender = "male"
    elif pitch_median > 220:
        gender = "female"
    else:
        gender = "ambiguous"

    # Register
    register = map_feature("pitch_register", pitch_median, gender=gender)

    # Breathiness: spectral flatness in 2-5kHz band of vocal stem
    print("  Measuring breathiness...", file=sys.stderr)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    # Find frequency bin indices for 2-5kHz
    low_bin = np.argmin(np.abs(freqs - 2000))
    high_bin = np.argmin(np.abs(freqs - 5000))

    if high_bin > low_bin:
        breath_band = S[low_bin:high_bin, :]
        # Spectral flatness in this band
        geometric_mean = np.exp(np.mean(np.log(breath_band + 1e-10), axis=0))
        arithmetic_mean = np.mean(breath_band, axis=0)
        flatness_breath = geometric_mean / (arithmetic_mean + 1e-10)
        breathiness = float(np.mean(flatness_breath))
    else:
        breathiness = 0.1

    # Raspiness (HNR estimate via autocorrelation)
    print("  Estimating HNR...", file=sys.stderr)
    hnr = _estimate_hnr(y, sr)

    # Vibrato detection: modulation rate in f0 contour
    print("  Detecting vibrato...", file=sys.stderr)
    vibrato_rate, vibrato_depth = _detect_vibrato(voiced_f0, sr)

    # Build style summary
    style_parts = [gender if gender != "ambiguous" else ""]
    style_parts.append(register)

    if breathiness > 0.15:
        style_parts.append("breathy")
    hnr_desc = map_feature("hnr", hnr)
    if "raspy" in hnr_desc.lower():
        style_parts.append("raspy")
    elif "clean" in hnr_desc.lower():
        style_parts.append("clean")

    if vibrato_depth > 0.3:
        style_parts.append("with vibrato")
    else:
        style_parts.append("minimal vibrato")

    style_summary = ", ".join(p for p in style_parts if p)

    elapsed = time.time() - t0
    print(f"  Vocal analysis complete in {elapsed:.1f}s", file=sys.stderr)

    return {
        "present": True,
        "gender": gender,
        "register": register,
        "pitch_range_hz": {
            "min": round(pitch_min, 1),
            "max": round(pitch_max, 1),
            "median": round(pitch_median, 1),
        },
        "breathiness": round(breathiness, 3),
        "raspiness_hnr": round(hnr, 1),
        "raspiness_description": map_feature("hnr", hnr),
        "vibrato_rate_hz": round(vibrato_rate, 1),
        "vibrato_depth": round(vibrato_depth, 3),
        "style_summary": style_summary,
        "classifier_source": "heuristic",
    }


def _estimate_hnr(y: np.ndarray, sr: int) -> float:
    """Estimate Harmonics-to-Noise Ratio via autocorrelation.

    Higher HNR = cleaner voice. Lower = raspy/breathy.
    """
    # Use windowed frames
    frame_length = int(0.04 * sr)  # 40ms frames
    hop_length = int(0.02 * sr)

    hnr_values = []
    for start in range(0, len(y) - frame_length, hop_length):
        frame = y[start:start + frame_length]
        if np.max(np.abs(frame)) < 0.01:
            continue

        # Autocorrelation
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr) // 2:]
        autocorr = autocorr / (autocorr[0] + 1e-10)

        # Find first peak after zero-lag (pitch period)
        # Look in range corresponding to 65-1000 Hz
        min_lag = int(sr / 1000)
        max_lag = int(sr / 65)
        max_lag = min(max_lag, len(autocorr) - 1)

        if min_lag >= max_lag:
            continue

        search_region = autocorr[min_lag:max_lag]
        if len(search_region) == 0:
            continue

        peak_val = float(np.max(search_region))
        if peak_val > 0 and peak_val < 1:
            hnr = 10 * np.log10(peak_val / (1 - peak_val + 1e-10))
            hnr_values.append(hnr)

    if not hnr_values:
        return 15.0  # moderate default

    return float(np.median(hnr_values))


def _detect_vibrato(f0_voiced: np.ndarray, sr: int) -> tuple:
    """Detect vibrato in the f0 contour.

    Returns:
        (vibrato_rate_hz, vibrato_depth)
        vibrato_rate: typical vibrato is 4-8 Hz
        vibrato_depth: amplitude of modulation (normalized)
    """
    if len(f0_voiced) < 50:
        return 0.0, 0.0

    # Detrend the f0 contour
    f0_detrended = f0_voiced - np.convolve(f0_voiced, np.ones(20) / 20, mode='same')

    # FFT of the f0 contour
    # Hop rate for pYIN is typically 512/22050 ≈ 43 fps
    hop_rate = 22050 / 512
    fft_f0 = np.abs(np.fft.rfft(f0_detrended))
    freqs = np.fft.rfftfreq(len(f0_detrended), d=1.0 / hop_rate)

    # Look for peak in vibrato range (4-8 Hz)
    vibrato_mask = (freqs >= 4) & (freqs <= 8)
    if not np.any(vibrato_mask):
        return 0.0, 0.0

    vibrato_spectrum = fft_f0[vibrato_mask]
    vibrato_freqs = freqs[vibrato_mask]

    peak_idx = np.argmax(vibrato_spectrum)
    vibrato_rate = float(vibrato_freqs[peak_idx])
    vibrato_amplitude = float(vibrato_spectrum[peak_idx])

    # Normalize depth relative to overall spectral energy
    total_energy = float(np.sum(fft_f0))
    vibrato_depth = vibrato_amplitude / (total_energy + 1e-10)

    return vibrato_rate, vibrato_depth


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze vocal characteristics")
    parser.add_argument("vocal_stem_path", help="Path to vocal stem WAV file")
    args = parser.parse_args()

    result = analyze_vocals(args.vocal_stem_path)
    print(json.dumps(result, indent=2))

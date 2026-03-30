#!/usr/bin/env python3
"""Maps numerical audio features to perceptual descriptors for Suno prompts."""

from typing import Optional

# Each map is a list of (range_tuple, descriptor) pairs.
# Ranges are (min_inclusive, max_exclusive) except the last which is unbounded.

SPECTRAL_CENTROID_MAP = [
    (0, 1500, "dark, muffled"),
    (1500, 2500, "warm, balanced"),
    (2500, 4000, "bright, present"),
    (4000, float('inf'), "shimmery, airy, crisp"),
]

SPECTRAL_FLATNESS_MAP = [
    (0, 0.05, "highly tonal, clean"),
    (0.05, 0.15, "natural texture"),
    (0.15, float('inf'), "noisy, gritty, lo-fi"),
]

HNR_MAP = [
    (20, float('inf'), "clean vocals"),
    (15, 20, "slightly raspy"),
    (5, 15, "raspy, gritty"),
    (float('-inf'), 5, "very raspy, distorted"),
]

DANCEABILITY_MAP = [
    (0, 1.0, "not danceable"),
    (1.0, 2.0, "moderate groove"),
    (2.0, float('inf'), "highly danceable"),
]

LOUDNESS_LUFS_MAP = [
    (-8, float('inf'), "loud, compressed, in-your-face"),
    (-14, -8, "standard modern production"),
    (float('-inf'), -14, "dynamic, spacious, quiet"),
]

BPM_FEEL_MAP = [
    (0, 80, "slow, languorous"),
    (80, 110, "moderate, laid-back"),
    (110, 130, "driving, upbeat"),
    (130, 160, "fast, energetic"),
    (160, float('inf'), "frantic, breakneck"),
]

PITCH_REGISTER_MALE = [
    (0, 130, "bass"),
    (130, 200, "baritone"),
    (200, 350, "tenor"),
    (350, float('inf'), "countertenor"),
]

PITCH_REGISTER_FEMALE = [
    (0, 200, "contralto"),
    (200, 350, "mezzo-soprano"),
    (350, 500, "soprano"),
    (500, float('inf'), "coloratura soprano"),
]

DYNAMIC_RANGE_MAP = [
    (0, 3, "very compressed"),
    (3, 6, "compressed"),
    (6, 10, "moderate dynamics"),
    (10, float('inf'), "wide dynamic range"),
]

# Maps for spectral bandwidth → texture
SPECTRAL_BANDWIDTH_MAP = [
    (0, 1500, "thin, narrow"),
    (1500, 2500, "focused"),
    (2500, 3500, "full, rich"),
    (3500, float('inf'), "dense, wide"),
]

# Feature name → lookup table
FEATURE_TABLES = {
    "spectral_centroid": SPECTRAL_CENTROID_MAP,
    "spectral_flatness": SPECTRAL_FLATNESS_MAP,
    "hnr": HNR_MAP,
    "danceability": DANCEABILITY_MAP,
    "loudness_lufs": LOUDNESS_LUFS_MAP,
    "bpm": BPM_FEEL_MAP,
    "dynamic_complexity": DYNAMIC_RANGE_MAP,
    "spectral_bandwidth": SPECTRAL_BANDWIDTH_MAP,
}


def _lookup(table: list, value: float) -> str:
    """Look up a value in a range table. Returns descriptor string."""
    for lo, hi, descriptor in table:
        if lo <= value < hi:
            return descriptor
    # Fallback: return last entry
    return table[-1][2]


def map_feature(feature_name: str, value: float, gender: Optional[str] = None) -> str:
    """Map a numerical audio feature to a perceptual descriptor.

    Args:
        feature_name: Name of the feature (e.g., "spectral_centroid", "bpm")
        value: Numerical value to map
        gender: For pitch register mapping, "male" or "female"

    Returns:
        Perceptual descriptor string
    """
    if feature_name == "pitch_register":
        if gender == "female":
            return _lookup(PITCH_REGISTER_FEMALE, value)
        return _lookup(PITCH_REGISTER_MALE, value)

    table = FEATURE_TABLES.get(feature_name)
    if table is None:
        return f"unknown feature: {feature_name}"
    return _lookup(table, value)


def summarize_mood(mood_dict: dict) -> str:
    """Summarize mood scores into a 2-4 word descriptor.

    Args:
        mood_dict: Dict with keys like "dark", "aggressive", "happy",
                   "relaxed", "sad", "energetic" mapping to 0.0-1.0 scores.

    Returns:
        Summary string like "dark, brooding, melancholic"
    """
    if not mood_dict:
        return "neutral"

    # Sort by score descending, take top 2-3
    sorted_moods = sorted(mood_dict.items(), key=lambda x: x[1], reverse=True)

    # Filter to significant moods (> 0.3)
    significant = [(k, v) for k, v in sorted_moods if v > 0.3]

    if not significant:
        # Nothing strong — use top 2 anyway
        significant = sorted_moods[:2]

    # Take top 3 at most
    top = significant[:3]

    # Map mood keys to more expressive descriptors
    MOOD_EXPANDERS = {
        "dark": "dark",
        "aggressive": "aggressive",
        "happy": "uplifting",
        "relaxed": "mellow",
        "sad": "melancholic",
        "energetic": "energetic",
        "brooding": "brooding",
        "ethereal": "ethereal",
        "nostalgic": "nostalgic",
        "triumphant": "triumphant",
        "playful": "playful",
        "somber": "somber",
        "intimate": "intimate",
        "anthemic": "anthemic",
    }

    descriptors = [MOOD_EXPANDERS.get(k, k) for k, _ in top]
    return ", ".join(descriptors)


def describe_spectral_profile(centroid_hz: float, flatness: float,
                               bandwidth_hz: float) -> dict:
    """Produce a complete spectral profile description.

    Returns dict with brightness, warmth, texture descriptors.
    """
    brightness = map_feature("spectral_centroid", centroid_hz)
    texture = map_feature("spectral_flatness", flatness)
    width = map_feature("spectral_bandwidth", bandwidth_hz)

    # Derive warmth from centroid (inverse relationship)
    if centroid_hz < 2000:
        warmth = "warm"
    elif centroid_hz < 3000:
        warmth = "neutral"
    else:
        warmth = "cool, bright"

    return {
        "brightness": brightness,
        "warmth": warmth,
        "texture": texture,
        "width": width,
    }


if __name__ == "__main__":
    # Quick self-test
    print("Feature mapping self-test:")
    print(f"  spectral_centroid(1850) = {map_feature('spectral_centroid', 1850)}")
    print(f"  spectral_centroid(3500) = {map_feature('spectral_centroid', 3500)}")
    print(f"  bpm(128) = {map_feature('bpm', 128)}")
    print(f"  loudness_lufs(-10) = {map_feature('loudness_lufs', -10)}")
    print(f"  hnr(18) = {map_feature('hnr', 18)}")
    print(f"  pitch_register(165, male) = {map_feature('pitch_register', 165, gender='male')}")
    print(f"  pitch_register(300, female) = {map_feature('pitch_register', 300, gender='female')}")
    print(f"  danceability(2.1) = {map_feature('danceability', 2.1)}")

    mood = {"dark": 0.85, "sad": 0.45, "aggressive": 0.35, "happy": 0.05, "relaxed": 0.15}
    print(f"  summarize_mood({mood}) = {summarize_mood(mood)}")

    profile = describe_spectral_profile(1850, 0.08, 2800)
    print(f"  spectral_profile(1850, 0.08, 2800) = {profile}")
    print("All tests passed.")

#!/usr/bin/env python3
"""Generate Style Reference Cards and Suno v5.5 prompts from analysis data."""

import json
import os
import sys
import time
from datetime import datetime, timezone


def generate_style_card(analysis: dict, identification: dict,
                        structure: list, vocals: dict,
                        video_id: str = "", source_url: str = "",
                        stems: dict = None) -> dict:
    """Compile all analysis results into a Style Reference Card.

    Args:
        analysis: Output from audio_analysis.analyze()
        identification: Output from identify.identify()
        structure: Output from structure_analysis.analyze_structure()
        vocals: Output from vocal_analysis.analyze_vocals()
        video_id: Video/file identifier
        source_url: Original YouTube URL or file path

    Returns:
        Complete style card dict
    """
    # Derive instrument list from stems + heuristics
    instruments = _infer_instruments(analysis, vocals, stems or {})

    style_card = {
        "meta": {
            "analyzed": datetime.now(timezone.utc).isoformat(),
            "source_url": source_url,
            "video_id": video_id,
            "pipeline_version": "1.0.0",
        },
        "identification": {
            "title": identification.get("title", ""),
            "artist": identification.get("artist", ""),
            "album": identification.get("album", ""),
            "year": identification.get("year"),
            "genre_tags": identification.get("genre_tags", []),
            "identification_confidence": identification.get("identification_confidence", 0),
            "source": identification.get("source", "unknown"),
        },
        "tempo": analysis.get("tempo", {}),
        "key": analysis.get("key", {}),
        "genre": _derive_genre(identification, analysis),
        "mood": analysis.get("mood", {}),
        "energy": analysis.get("energy", {}),
        "instruments": instruments,
        "vocals": vocals,
        "spectral_profile": analysis.get("spectral_profile", {}),
        "structure": structure,
        "dynamics": analysis.get("dynamics", {}),
        "timbre": analysis.get("timbre", {}),
    }

    return style_card


def _infer_instruments(analysis: dict, vocals: dict, stems: dict = None) -> dict:
    """Infer instrument presence from demucs stem energy + spectral hints.

    Primary: check RMS energy of each demucs stem (drums, bass, other, vocals).
    Secondary: use spectral features on the "other" stem to guess guitar vs synth vs piano.
    """
    import os
    detected = []
    prominent = []
    stem_energies = {}

    # Primary: detect from demucs stem RMS energy
    if stems:
        try:
            import soundfile as sf
            import numpy as np
            ENERGY_THRESHOLD = 0.005

            for stem_name in ["drums", "bass", "other", "vocals"]:
                stem_path = stems.get(stem_name)
                if stem_path and os.path.exists(stem_path):
                    data, sr = sf.read(stem_path)
                    rms = float(np.sqrt(np.mean(data ** 2)))
                    stem_energies[stem_name] = rms
                    if rms > ENERGY_THRESHOLD:
                        if stem_name == "other":
                            # "other" contains guitars, synths, keys, pads
                            detected.append("melodic_instruments")
                        elif stem_name == "vocals":
                            pass  # handled separately below
                        else:
                            detected.append(stem_name)
        except Exception:
            pass

    # Sort by energy for prominence
    if stem_energies:
        sorted_stems = sorted(stem_energies.items(), key=lambda x: x[1], reverse=True)
        for name, energy in sorted_stems[:2]:
            if energy > 0.005 and name != "vocals":
                if name == "other":
                    prominent.append("melodic_instruments")
                else:
                    prominent.append(name)

    # Refine "melodic_instruments" using spectral hints from full mix
    if "melodic_instruments" in detected:
        detected.remove("melodic_instruments")
        centroid = analysis.get("spectral_profile", {}).get("spectral_centroid_mean_hz", 2000)
        flatness = analysis.get("spectral_profile", {}).get("spectral_flatness_mean", 0.1)

        if flatness > 0.08:
            detected.append("synthesizer")
        elif centroid > 2500:
            detected.append("guitar_electric")
        elif centroid > 1500:
            detected.append("piano")
        else:
            detected.append("guitar_acoustic")

    if "melodic_instruments" in prominent:
        prominent = [p if p != "melodic_instruments" else detected[-1] for p in prominent]

    # Vocals
    if vocals.get("present"):
        detected.append("vocals")

    # Fallback if stems weren't available
    if not detected:
        centroid = analysis.get("spectral_profile", {}).get("spectral_centroid_mean_hz", 2000)
        detected = ["drums", "bass"]
        if centroid > 2500:
            detected.append("guitar_electric")
        else:
            detected.append("synthesizer")
        if vocals.get("present"):
            detected.append("vocals")

    return {
        "detected": list(dict.fromkeys(detected)),  # dedupe preserving order
        "prominent": list(dict.fromkeys(prominent)) if prominent else detected[:2],
        "stem_energies": {k: round(v, 4) for k, v in stem_energies.items()},
        "style_notes": "",
        "classifier_source": "demucs_stems" if stem_energies else "heuristic",
    }


def _derive_genre(identification: dict, analysis: dict) -> dict:
    """Derive genre information from identification and analysis."""
    genre_tags = identification.get("genre_tags", [])

    if genre_tags:
        return {
            "primary": genre_tags[0] if genre_tags else "unknown",
            "secondary": genre_tags[1:4],
            "source_tags": genre_tags,
            "classifier_source": "musicbrainz",
        }

    # Heuristic genre from spectral features
    centroid = analysis.get("spectral_profile", {}).get("spectral_centroid_mean_hz", 2000)
    bpm = analysis.get("tempo", {}).get("bpm", 120)
    danceability = analysis.get("energy", {}).get("danceability", 1.0)

    if bpm > 150 and centroid > 3000:
        primary = "electronic"
    elif bpm < 90 and centroid < 1800:
        primary = "ambient"
    elif bpm > 130 and danceability > 2.0:
        primary = "dance"
    elif centroid > 2500:
        primary = "rock"
    else:
        primary = "pop"

    return {
        "primary": primary,
        "secondary": [],
        "source_tags": [],
        "classifier_source": "heuristic",
    }


def generate_suno_prompt(style_card: dict) -> str:
    """Generate a Suno v5.5 prompt from a Style Reference Card.

    Returns:
        Formatted prompt string with Title, Style, and structural meta tags
    """
    # --- Title ---
    title = _generate_title(style_card)

    # --- Style field (max 1000 chars) ---
    style_parts = []

    # 1. Genre (highest priority)
    genre = style_card.get("genre", {})
    primary_genre = genre.get("primary", "")
    secondary = genre.get("secondary", [])
    if primary_genre:
        genre_str = primary_genre
        if secondary:
            genre_str += f", {secondary[0]}"
        style_parts.append(genre_str)

    # 2. Tempo
    tempo = style_card.get("tempo", {})
    bpm = tempo.get("bpm", 0)
    feel = tempo.get("feel", "")
    if bpm:
        style_parts.append(f"{feel} {bpm} BPM")

    # 3. Key instruments
    instruments = style_card.get("instruments", {})
    detected = instruments.get("detected", [])
    # Map internal names to Suno-friendly names
    INSTRUMENT_NAMES = {
        "guitar_electric": "electric guitar",
        "guitar_acoustic": "acoustic guitar",
        "bass_guitar": "bass guitar",
        "bass": "bass",
        "drums": "drums",
        "synthesizer": "synthesizer",
        "piano": "piano",
        "strings": "strings",
        "brass": "brass",
        "vocals": None,  # handled separately
    }
    inst_strs = []
    for inst in detected:
        if inst in INSTRUMENT_NAMES and INSTRUMENT_NAMES[inst]:
            inst_strs.append(INSTRUMENT_NAMES[inst])
        elif inst != "vocals":
            inst_strs.append(inst.replace("_", " "))
    if inst_strs:
        style_parts.append(", ".join(inst_strs[:4]))

    # 4. Vocal description
    vocals = style_card.get("vocals", {})
    if vocals.get("present"):
        vocal_desc = vocals.get("style_summary", "")
        if vocal_desc:
            style_parts.append(f"{vocal_desc} vocals")

    # 5. Mood
    mood = style_card.get("mood", {})
    mood_summary = mood.get("summary", "")
    if mood_summary:
        style_parts.append(f"{mood_summary} atmosphere")

    # 6. Production qualities
    spectral = style_card.get("spectral_profile", {})
    prod_parts = []
    warmth = spectral.get("warmth", "")
    if warmth:
        prod_parts.append(warmth)
    brightness = spectral.get("brightness", "")
    if brightness and brightness != warmth:
        prod_parts.append(brightness)
    texture = spectral.get("texture", "")
    if texture and texture not in ("natural texture",):
        prod_parts.append(texture)
    dynamics = style_card.get("dynamics", {})
    loudness_desc = dynamics.get("loudness_description", "")
    if loudness_desc and "production" not in loudness_desc:
        prod_parts.append(loudness_desc)
    if prod_parts:
        style_parts.append(", ".join(prod_parts))

    # 7. Danceability / groove
    energy = style_card.get("energy", {})
    dance_desc = energy.get("danceability_description", "")
    if dance_desc and dance_desc != "not danceable":
        style_parts.append(dance_desc)

    # 8. Key signature hint
    key_info = style_card.get("key", {})
    if key_info.get("key") and key_info.get("scale"):
        style_parts.append(f"{key_info['scale']} key")

    # 9. Era (from identification year, or fallback from genre hints)
    year = style_card.get("identification", {}).get("year")
    if year:
        decade = (year // 10) * 10
        style_parts.append(f"{decade}s influence")

    # Assemble Style field, respecting 1000 char limit
    style_field = ", ".join(style_parts)
    if len(style_field) > 1000:
        # Trim from the end
        while len(style_field) > 1000 and style_parts:
            style_parts.pop()
            style_field = ", ".join(style_parts)

    # --- Structural meta tags ---
    structure = style_card.get("structure", [])
    meta_tags = _generate_meta_tags(structure, style_card)

    # --- Slider recommendations (derived from genre/energy) ---
    danceability = style_card.get("energy", {}).get("danceability", 1.0)
    weirdness = 25 if danceability > 1.5 else 30 if primary_genre in ("ambient", "electronic") else 20
    style_influence = 85 if danceability > 1.5 else 75 if primary_genre in ("ambient", "electronic") else 90
    sliders = f"Recommended sliders: Weirdness {weirdness}%, Style Influence {style_influence}%"

    # --- Description (song listing metadata for Suno) ---
    ident = style_card.get("identification", {})
    desc_parts = []
    if primary_genre:
        desc_parts.append(f"Style clone of a {primary_genre} track")
    if ident.get("title") and ident.get("artist"):
        desc_parts.append(f"inspired by the sound of \"{ident['title']}\" by {ident['artist']}")
    tempo_info = style_card.get("tempo", {})
    if tempo_info.get("bpm"):
        key_info_str = f"{key_info.get('key', '')} {key_info.get('scale', '')}" if key_info.get("key") else ""
        desc_parts.append(f"{tempo_info['bpm']} BPM{', ' + key_info_str if key_info_str else ''}")
    description = ". ".join(desc_parts) + "." if desc_parts else ""

    # --- Assemble full prompt ---
    prompt = f"Title: {title}\n\n"
    if description:
        prompt += f"Description: {description}\n\n"
    prompt += f"Style: {style_field}\n\n"
    if meta_tags:
        prompt += f"Lyrics:\n{meta_tags}\n\n"
    prompt += sliders

    return prompt


def _generate_title(style_card: dict) -> str:
    """Generate an evocative title based on mood and genre."""
    mood = style_card.get("mood", {})
    genre = style_card.get("genre", {}).get("primary", "")
    key_info = style_card.get("key", {})
    scale = key_info.get("scale", "")

    # Title word pools by mood
    DARK_WORDS = ["Shadow", "Midnight", "Eclipse", "Void", "Obsidian", "Raven", "Cathedral", "Phantom"]
    BRIGHT_WORDS = ["Dawn", "Prism", "Horizon", "Radiant", "Golden", "Skyline", "Nova", "Cascade"]
    MELLOW_WORDS = ["Drift", "Amber", "Whisper", "Solace", "Twilight", "Harbor", "Gentle", "Reverie"]
    INTENSE_WORDS = ["Thunder", "Surge", "Blaze", "Tempest", "Fury", "Voltage", "Apex", "Inferno"]
    SECOND_WORDS = ["Frequency", "Signal", "Protocol", "Chronicle", "Passage", "Meridian", "Circuit", "Archive"]

    import random
    import hashlib
    seed_str = json.dumps(style_card.get("identification", {}), sort_keys=True)
    random.seed(int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**32))

    dark_score = mood.get("dark", 0) + mood.get("sad", 0)
    bright_score = mood.get("happy", 0) + mood.get("energetic", 0)
    intense_score = mood.get("aggressive", 0) + mood.get("energetic", 0)

    if intense_score > 0.7:
        first = random.choice(INTENSE_WORDS)
    elif dark_score > 0.6:
        first = random.choice(DARK_WORDS)
    elif bright_score > 0.5:
        first = random.choice(BRIGHT_WORDS)
    else:
        first = random.choice(MELLOW_WORDS)

    second = random.choice(SECOND_WORDS)
    return f"{first} {second}"


def _generate_meta_tags(structure: list, style_card: dict) -> str:
    """Generate Suno structural meta tags from analysis."""
    if not structure:
        return ""

    vocals = style_card.get("vocals", {})
    instruments = style_card.get("instruments", {})
    detected = instruments.get("detected", [])
    inst_str = ", ".join(i.replace("_", " ") for i in detected[:3] if i != "vocals")

    section_counts = {}
    lines = []
    total_sections = len(structure)

    for i, section in enumerate(structure):
        label = section["section"]
        section_counts[label] = section_counts.get(label, 0) + 1
        count = section_counts[label]
        is_last_of_type = not any(s["section"] == label for s in structure[i+1:])

        # Number repeated sections
        display = label.title()
        if sum(1 for s in structure if s["section"] == label) > 1:
            display = f"{label.title()} {count}"

        tag = f"[{display}"

        if label == "intro":
            tag += f": {inst_str or 'atmospheric'}, building"
        elif label == "verse":
            if vocals.get("present"):
                vs = vocals.get("style_summary", "vocals")
                if count == 1:
                    tag += f": {vs}, moderate energy"
                elif count == 2:
                    tag += f": {vs}, slight variation"
                else:
                    tag += f": {vs}, building intensity"
            else:
                tag += f": {inst_str}, {'rhythmic' if count == 1 else 'varied pattern'}"
        elif label == "chorus":
            if vocals.get("present"):
                if is_last_of_type:
                    tag += ": full instrumentation, climactic, final energy"
                elif count == 1:
                    tag += ": full instrumentation, powerful vocals"
                else:
                    tag += ": full band, anthemic, vocal harmonies"
            else:
                if is_last_of_type:
                    tag += ": maximum energy, climactic"
                else:
                    tag += ": full instrumentation, peak energy"
        elif label == "bridge":
            tag += ": contrasting arrangement, stripped back"
        elif label == "outro":
            tag += ": winding down, fading naturally"
        elif label == "pre-chorus":
            tag += ": building energy, transitional"
        elif label == "breakdown":
            tag += ": stripped to core elements"
        elif label == "interlude":
            tag += ": instrumental, atmospheric"

        tag += "]"
        lines.append(tag)

    return "\n".join(lines)


def prepare_claude_translation_prompt(style_card: dict, draft_prompt: str) -> str:
    """Prepare the prompt for Claude to refine the Suno prompt.

    This is what SKILL.md feeds to Claude for final human-quality translation.
    """
    # Load reference and examples
    skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ref_path = os.path.join(skill_dir, "references", "suno-v5.5-reference.md")
    examples_path = os.path.join(skill_dir, "references", "example-prompts.md")

    ref_content = ""
    if os.path.exists(ref_path):
        with open(ref_path) as f:
            ref_content = f.read()

    examples_content = ""
    if os.path.exists(examples_path):
        with open(examples_path) as f:
            examples_content = f.read()

    prompt = f"""You are refining a Suno v5.5 style-clone prompt. Your goal is to translate measured audio features into natural language that Suno understands well.

## Style Reference Card (measured data)
```json
{json.dumps(style_card, indent=2, default=str)}
```

## Draft Prompt (starting point — improve this)
```
{draft_prompt}
```

## Suno v5.5 Reference
{ref_content[:8000]}

## Example Prompts (few-shot)
{examples_content[:10000]}

## Translation Rules
1. Style field MUST be <= 1000 characters
2. Lead with genre, then stack 4-7 descriptors
3. Use Suno-native vocabulary from the reference
4. NO negations ("no X") — describe what IS present
5. NO artist names — use style descriptions instead
6. Include structural meta tags matching the detected structure
7. Parameterize each section tag with instrumentation/vocal hints
8. Generate a descriptive Title that captures the vibe (NOT the original song title)
9. Note which values are heuristic-derived (lower confidence) vs ML-measured

## Your Task
Produce the final refined Suno v5.5 prompt with:
- Title: [evocative name]
- Style: [optimized descriptors, <= 1000 chars]
- [Structural meta tags with parameterized descriptors]
- Recommended sliders: Weirdness and Style Influence values

Also note any confidence concerns (e.g., "mood is heuristic-derived, consider adjusting").
"""
    return prompt


def save_outputs(style_card: dict, suno_prompt: str,
                 claude_prompt: str, output_dir: str):
    """Save all outputs to the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    # Style card JSON
    with open(os.path.join(output_dir, "style-card.json"), "w") as f:
        json.dump(style_card, f, indent=2, default=str)

    # Style card Markdown
    md = _render_style_card_markdown(style_card)
    with open(os.path.join(output_dir, "style-card.md"), "w") as f:
        f.write(md)

    # Suno prompt
    with open(os.path.join(output_dir, "suno-prompt.md"), "w") as f:
        f.write(suno_prompt)

    # Claude translation prompt (for regeneration)
    with open(os.path.join(output_dir, "claude-translation-prompt.md"), "w") as f:
        f.write(claude_prompt)


def _render_style_card_markdown(card: dict) -> str:
    """Render style card as human-readable Markdown."""
    lines = ["# Style Reference Card\n"]

    # Identification
    ident = card.get("identification", {})
    if ident.get("title"):
        lines.append(f"**Song:** {ident['title']}")
        if ident.get("artist"):
            lines.append(f"**Artist:** {ident['artist']}")
        if ident.get("album"):
            lines.append(f"**Album:** {ident['album']}")
        if ident.get("year"):
            lines.append(f"**Year:** {ident['year']}")
        lines.append(f"**ID Confidence:** {ident.get('identification_confidence', 0):.0%}")
        lines.append("")

    # Tempo & Key
    tempo = card.get("tempo", {})
    key = card.get("key", {})
    lines.append("## Tempo & Key")
    lines.append(f"- **BPM:** {tempo.get('bpm', '?')} ({tempo.get('feel', '?')})")
    lines.append(f"- **BPM Confidence:** {tempo.get('bpm_confidence', 0):.0%}")
    lines.append(f"- **Key:** {key.get('key', '?')} {key.get('scale', '?')}")
    lines.append(f"- **Key Confidence:** {key.get('confidence', 0):.0%}")
    lines.append("")

    # Genre & Mood
    genre = card.get("genre", {})
    mood = card.get("mood", {})
    lines.append("## Genre & Mood")
    lines.append(f"- **Primary Genre:** {genre.get('primary', '?')}")
    if genre.get("secondary"):
        lines.append(f"- **Secondary:** {', '.join(genre['secondary'])}")
    lines.append(f"- **Mood:** {mood.get('summary', '?')}")
    lines.append(f"- **Genre Source:** {genre.get('classifier_source', '?')}")
    lines.append("")

    # Instruments
    inst = card.get("instruments", {})
    lines.append("## Instruments")
    lines.append(f"- **Detected:** {', '.join(inst.get('detected', []))}")
    lines.append(f"- **Prominent:** {', '.join(inst.get('prominent', []))}")
    lines.append("")

    # Vocals
    vocals = card.get("vocals", {})
    lines.append("## Vocals")
    if vocals.get("present"):
        lines.append(f"- **Gender:** {vocals.get('gender', '?')}")
        lines.append(f"- **Register:** {vocals.get('register', '?')}")
        pitch = vocals.get("pitch_range_hz", {})
        lines.append(f"- **Pitch Range:** {pitch.get('min', '?')}-{pitch.get('max', '?')} Hz (median {pitch.get('median', '?')})")
        lines.append(f"- **Style:** {vocals.get('style_summary', '?')}")
    else:
        lines.append("- **Vocals:** Not present (instrumental)")
    lines.append("")

    # Spectral Profile
    spectral = card.get("spectral_profile", {})
    lines.append("## Spectral Profile")
    lines.append(f"- **Brightness:** {spectral.get('brightness', '?')}")
    lines.append(f"- **Warmth:** {spectral.get('warmth', '?')}")
    lines.append(f"- **Texture:** {spectral.get('texture', '?')}")
    lines.append("")

    # Structure
    structure = card.get("structure", [])
    if structure:
        lines.append("## Structure")
        lines.append("| Section | Start | End | Duration |")
        lines.append("|---------|-------|-----|----------|")
        for s in structure:
            lines.append(f"| {s['section']} | {s['start']:.1f}s | {s['end']:.1f}s | {s['duration']:.1f}s |")
        lines.append("")

    # Dynamics
    dynamics = card.get("dynamics", {})
    lines.append("## Dynamics")
    lines.append(f"- **Loudness:** {dynamics.get('loudness_lufs', '?')} LUFS ({dynamics.get('loudness_description', '?')})")
    lines.append(f"- **Dynamic Range:** {dynamics.get('dynamic_description', '?')}")
    lines.append("")

    # Meta
    meta = card.get("meta", {})
    lines.append(f"---\n*Analyzed: {meta.get('analyzed', '?')} | Pipeline v{meta.get('pipeline_version', '?')}*")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Suno prompt from style card")
    parser.add_argument("style_card_json", help="Path to style-card.json")
    args = parser.parse_args()

    with open(args.style_card_json) as f:
        card = json.load(f)

    prompt = generate_suno_prompt(card)
    print(prompt)

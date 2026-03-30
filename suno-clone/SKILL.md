---
name: suno-clone
description: >
  Analyzes YouTube music or local audio files to generate Suno v5.5
  style-clone prompts. Performs deep audio analysis (BPM, key, genre, mood,
  instruments, vocals, structure) and produces a Style Reference Card plus
  ready-to-paste Suno prompt. Use when the user asks to clone a song style,
  analyze music for Suno, create a Suno prompt from a YouTube video,
  or generate a style reference card.
---

# Suno Clone

Analyze music and generate Suno v5.5 style-clone prompts with deep audio analysis.

## Setup (first time only)

```bash
bash ~/.claude/skills/suno-clone/scripts/setup.sh
```

Optionally set AcoustID API key for song identification:
```bash
export ACOUSTID_API_KEY="your-key-here"
```

Register free at https://acoustid.org/my-applications

## Invocation

```
/suno-clone <youtube-url>
/suno-clone <local-audio-file-path>
/suno-clone --regenerate <video-id>
```

## Workflows

### New Analysis (~2-4 minutes)

1. Validate the URL or file path
2. Check `~/.openclaw/data/suno-clone/catalog.json` — if already analyzed, ask user: re-analyze or show existing?
3. Run the analysis pipeline:

```bash
source ~/.openclaw/envs/suno-clone/bin/activate
python ~/.claude/skills/suno-clone/scripts/analyze.py "<url_or_path>"
```

4. The pipeline runs 5 stages:
   - **Download** — yt-dlp → FLAC (or accepts local file)
   - **Identify** — Chromaprint → AcoustID → MusicBrainz
   - **Analyze** — Essentia (BPM/key/loudness/danceability) + librosa (spectral features)
   - **Separate & Structure** — demucs-mlx (4 stems) + librosa structure segmentation + vocal analysis
   - **Generate** — Style Reference Card (JSON + MD) + draft Suno prompt

5. After the pipeline completes, read the outputs:
   - `~/.openclaw/data/suno-clone/{video_id}/style-card.md` — human-readable style card
   - `~/.openclaw/data/suno-clone/{video_id}/suno-prompt.md` — draft Suno prompt
   - `~/.openclaw/data/suno-clone/{video_id}/claude-translation-prompt.md` — Claude refinement prompt

6. Read the `claude-translation-prompt.md` and use it to refine the draft Suno prompt. This is where Claude adds the human-quality translation layer — converting measured numerical features into natural language that Suno responds well to.

7. Present to user:
   - Style Reference Card (formatted from style-card.md)
   - Refined Suno prompt (Title + Style + structural meta tags)
   - Slider recommendations (Weirdness: 20-40%, Style Influence: 70-90%)
   - Confidence notes on heuristic-derived values

### Async via Kurultai Agent

For long-running analysis, dispatch to @temujin via agent-collaboration:

```
---PLAN-HANDOFF---
Plan ID: suno-{timestamp}
Priority: medium
To: @kublai

## Objective
Analyze audio and generate Suno v5.5 style clone prompt.

## Steps
1. source ~/.openclaw/envs/suno-clone/bin/activate
2. python ~/.claude/skills/suno-clone/scripts/analyze.py "<URL>"
3. Return contents of style-card.json + suno-prompt.md

## Success Criteria
- [ ] style-card.json exists with all fields populated
- [ ] suno-prompt.md has Style field <= 1000 chars
---END-PLAN---
```

### Regenerate Prompt (instant)

To re-generate or adjust a prompt for an already-analyzed song:

```bash
source ~/.openclaw/envs/suno-clone/bin/activate
python ~/.claude/skills/suno-clone/scripts/analyze.py --regenerate <video_id>
```

Then read the `claude-translation-prompt.md` and apply user's requested modifications (e.g., "make it darker", "emphasize the bass more", "change the genre to synthwave").

### Direct File Analysis

Accept local audio file paths — skips download and identification stages:

```bash
python ~/.claude/skills/suno-clone/scripts/analyze.py "/path/to/audio.flac"
```

## Suno v5.5 Output Fields

The generated prompt covers ALL Suno input fields:

- **Title** — descriptive, evocative name matching the vibe (never the original song title)
- **Style** — ≤1000 chars of optimized descriptors: genre, tempo, instruments, vocals, mood, production, era
- **Structural meta tags** — `[Intro]`, `[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]` etc. with parameterized descriptors
- **Slider recommendations** — Weirdness and Style Influence values

## Output Location

```
~/.openclaw/data/suno-clone/{video_id}/
├── style-card.json              # Machine-readable style reference (reusable)
├── style-card.md                # Human-readable style reference
├── suno-prompt.md               # Ready-to-paste Suno prompt
├── claude-translation-prompt.md # For Claude to refine the prompt
└── metadata.json                # YouTube + MusicBrainz metadata
```

## Suno Reference

For detailed Suno v5.5 prompt engineering guidance, read:
- `~/.claude/skills/suno-clone/references/suno-v5.5-reference.md`
- `~/.claude/skills/suno-clone/references/example-prompts.md`

## Technical Notes

- **Python 3.11 venv** at `~/.openclaw/envs/suno-clone/` — essentia requires 3.11
- **allin1 unavailable** — madmom incompatible with Python 3.10+; structure analysis uses librosa fallback (self-similarity matrix + novelty detection)
- **essentia-tensorflow unavailable** — genre/mood/instrument classifiers use heuristic alternatives (MusicBrainz tags + spectral features); style card marks these as `classifier_source: "heuristic"`
- **Temp files** cleaned up automatically after analysis; only final outputs persist (~5MB per song)

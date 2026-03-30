# Suno v5.5 Prompt Reference

Complete reference for generating Suno v5.5 style-clone prompts.

## Input Fields

### Title
- Names the generation for metadata. Minimal effect on musical output.
- For style cloning: use a descriptive, evocative title matching the vibe (NOT the original song title).

### Style Field (1000 character limit)
- Natural language descriptors defining how the song sounds.
- **Optimal: 4-7 comma-separated descriptors.**
- Order matters: first descriptor carries most weight.
- Priority ordering: Genre → Tempo → Key instruments → Vocal style → Mood → Production → Era

### Lyrics Field (5000 character limit)
- Song text with structural meta tags in square brackets.
- For instrumental style cloning: use `[Instrumental]` tag throughout with section markers.
- For style-only cloning (no lyrics): populate with structural tags + parameterized descriptors only.

### Creative Sliders
- **Weirdness** (Safe → Chaos): Controls sampling temperature. For style cloning: 20-40% recommended.
- **Style Influence** (Loose → Strong): Adherence to Style field. For style cloning: 70-90% recommended.
- **Audio Influence**: Only for covers/remixes with audio reference. N/A for text-based style cloning.

## Style Field Rules

1. **Lead with genre** — primary genre first, most impact on output
2. **Stack 3-5 descriptors** — fewer = too vague; more = competing constraints
3. **Be specific, not contradictory** — "upbeat melancholic" confuses; "bittersweet indie pop" works
4. **Include instrumentation** — 1-2 instrument callouts dramatically improve specificity
5. **Specify vocal direction** — prevents random voice selection
6. **No negations** — "no drums", "without autotune" does NOT work. Describe what IS present.
7. **No artist names** — "sounds like Radiohead" is inconsistent. Use style descriptions instead.
8. **Include era/decade hints** — "80s", "90s alternative", "modern trap" help guide the output

## Structural Meta Tags

### Song Structure Tags
| Tag | Purpose | Musical Effect |
|-----|---------|----------------|
| `[Intro]` | Opening | Usually instrumental or sparse |
| `[Verse]` / `[Verse 1]` | Narrative | Moderate energy, varied melody |
| `[Pre-Chorus]` | Build transition | Rising energy, transitional harmony |
| `[Chorus]` | Hook/refrain | Peak energy, full instrumentation |
| `[Post-Chorus]` | After chorus | Maintains energy, transitions down |
| `[Bridge]` | Contrasting section | Different chords, different energy |
| `[Breakdown]` | Stripped-back | Reduced instrumentation |
| `[Build]` / `[Build-Up]` | Energy ramp | Progressive intensity increase |
| `[Drop]` | High-energy payoff | Maximum instrumentation |
| `[Hook]` | Catchy phrase | Short, memorable musical phrase |
| `[Interlude]` | Instrumental break | Connects sections |
| `[Outro]` | Closing | Winds down energy |
| `[End]` | Hard stop | Signals song should end |

### Instrumental Tags
`[Instrumental]` · `[Instrumental Intro]` · `[Instrumental Break]` · `[Guitar Solo]` · `[Piano Solo]` · `[Drum Solo]` · `[Bass Solo]` · `[Saxophone Solo]` · `[Strings Rise]` · `[Percussion Break]` · `[Synth Solo]`

### Vocal Tags
`[Male Vocal]` · `[Female Vocal]` · `[Androgynous Vocals]` · `[Duet]` · `[Choir]` · `[Harmony]` · `[Rap]` · `[Spoken Word]` · `[Whisper]` · `[Scream]` · `[Ad-lib]` · `[Humming]` · `[Backing Vocals]`

### Dynamic Tags
`[Fade In]` · `[Fade Out]` · `[Silence]` · `[Crescendo]` · `[Decrescendo]` · `[Tempo: slow]` · `[Key Change]`

### Parameterized Tags (DAW-level control)
Append descriptive modifiers after a colon:
```
[Verse: whispered vocals, acoustic guitar only]
[Chorus: full band, powerful vocals, anthemic]
[Bridge: piano only, vulnerable vocals]
[Intro: synthesizer pad, atmospheric, 8 bars]
```

## Suno-Native Vocabulary

### High-Confidence Genre Tags
Pop, Rock, Hip-Hop/Rap, Electronic/EDM, R&B/Soul, Country, Folk, Jazz, Blues, Metal, Punk, Reggae, Latin, Afrobeat, K-Pop, Indie, Alternative, Soul, Funk, Gospel, Ambient, Lo-fi, Trap, Drill, House, Techno, Drum and Bass, Synthwave, Shoegaze, Grunge, Emo, Post-Punk, Bossa Nova, Ska, Darkwave, Gothic Rock, Bedroom Pop, Dream Pop, Psychedelic, Progressive Rock, Neo-Soul

### Mood/Emotion Tags
Melancholic, euphoric, aggressive, dreamy, haunting, uplifting, dark, ethereal, nostalgic, triumphant, brooding, playful, somber, energetic, intimate, anthemic, bittersweet, cinematic, hypnotic, raw, tender, fierce, contemplative, joyful

### Instrumentation Tags
Acoustic guitar, electric guitar, distorted guitar, jangly guitars, piano, synthesizer, analog synths, strings, brass, horns, 808s, drum machine, fingerpicking, orchestral, choir, organ, banjo, mandolin, slide guitar, theremin, bass guitar, upright bass, vinyl crackle, ambient pads

### Vocal Descriptors
Male vocals, female vocals, deep voice, falsetto, raspy vocals, whispered, operatic, spoken word, rap, harmonies, vocal chops, auto-tuned, breathy, soulful, powerful, delicate, ethereal, gritty

### Production Qualities
Lo-fi, polished, raw, overdriven, reverb-heavy, minimalist, lush, stripped-down, wall of sound, sparse, compressed, warm, bright, airy, dense, crisp, muddy, saturated, clean

### Era/Influence Tags
80s, 90s, 70s disco, 60s psychedelic, vintage, modern, retro, futuristic, classic, golden age, Y2K, early 2000s

## Known Limitations

- **No precise tempo control** — BPM tags are suggestive, not prescriptive
- **No key/tuning control** — cannot specify "in the key of E minor"
- **No mixing control** — cannot adjust volume, panning, EQ
- **No precise duration** — song length is approximate
- **Negation doesn't work** — cannot say "no reverb"
- **Extended instrumentals** — hard to generate; sections tend to be short
- **Vocal consistency** — same prompt may produce different voices
- **Odd time signatures** — 4/4 dominates; 7/8, 5/4 very hard
- **Dynamic range** — gradual buildups hard to control precisely

## Sources
- [Suno v5.5 Guide (HookGenius)](https://hookgenius.app/learn/suno-v5-5-guide/)
- [Suno v5 Knowledge Base](https://help.suno.com/en/articles/8105153)
- [Suno Technical Reference (Blake Crosley)](https://blakecrosley.com/guides/suno)
- [Suno Meta Tags Guide (Jack Righteous)](https://jackrighteous.com/en-us/pages/suno-ai-meta-tags-guide)
- [Suno Meta Tags Creator](https://sunometatagcreator.com/metatags-guide)

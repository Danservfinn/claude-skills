# Example Suno v5.5 Style Clone Prompts

Curated examples showing how Style Reference Card data translates to effective Suno prompts.

---

## Example 1: Dark Post-Punk / Gothic Rock

**Style being cloned:** A driving, dark post-punk track with prominent bass, angular guitar, sparse synth pads, and deep male baritone vocals. Bb minor, ~132 BPM. Late 1970s gothic rock aesthetic.

**Key analysis data:**
```json
{"bpm": 132, "key": "Bb minor", "mood": "dark, melancholic, aggressive",
 "instruments": ["bass_guitar", "guitar_electric", "synthesizer", "drums"],
 "vocals": {"gender": "male", "register": "baritone", "style": "clean, minimal vibrato"},
 "spectral": {"brightness": "medium-dark", "warmth": "warm"}}
```

**Suno prompt:**
```
Title: Cathedral of Echoes

Style: gothic rock, post-punk, driving 132 BPM, prominent bass guitar, angular electric guitar, sparse analog synth pads, drum machine, deep male baritone vocals clean and commanding, dark brooding atmosphere, warm reverb-heavy production, late 70s darkwave influence, minor key

[Intro: bass guitar solo, reverb-heavy, atmospheric, 8 bars]
[Verse: bass and drums driving, angular guitar accents, restrained baritone vocals]
[Chorus: full instrumentation, synth pads swell, vocals more intense]
[Verse: same instrumentation, slight variation]
[Chorus: full band, powerful vocals]
[Bridge: synth pads only, ethereal, stripped back]
[Chorus: full instrumentation, climactic]
[Outro: bass and reverb fade, atmospheric]
```

**Slider recommendations:** Weirdness 25%, Style Influence 85%

---

## Example 2: Lo-fi Hip Hop / Boom Bap

**Style being cloned:** Mellow, sample-based hip-hop beat with jazzy piano chops, vinyl crackle, and boom bap drums. No vocals. ~85 BPM, relaxed.

**Key analysis data:**
```json
{"bpm": 85, "key": "D minor", "mood": "relaxed, dark, sad",
 "instruments": ["piano", "drums", "bass"],
 "vocals": {"present": false},
 "spectral": {"brightness": "dark, muffled", "warmth": "warm", "texture": "lo-fi"}}
```

**Suno prompt:**
```
Title: Dusty Afternoon

Style: lo-fi hip hop, boom bap, jazzy piano samples, vinyl crackle, mellow laid-back 85 BPM, warm muffled production, sparse bass, head-nod drums, minor key, nostalgic late-night vibe

[Instrumental]
[Intro: vinyl crackle, piano chords fade in, 4 bars]
[Verse: boom bap drums enter, jazzy piano loop, bass groove]
[Interlude: drums drop out, piano solo with vinyl texture]
[Verse: drums return, slight variation on piano loop]
[Outro: fade out, vinyl crackle remains]
```

**Slider recommendations:** Weirdness 20%, Style Influence 80%

---

## Example 3: Modern Pop / Dance

**Style being cloned:** High-energy pop-dance track with pulsing synths, four-on-the-floor beat, female soprano vocals with auto-tune sheen, euphoric drops. ~128 BPM, Eb major.

**Key analysis data:**
```json
{"bpm": 128, "key": "Eb major", "mood": "happy, energetic",
 "instruments": ["synthesizer", "drum_machine", "bass_synth"],
 "vocals": {"gender": "female", "register": "soprano", "style": "bright, auto-tuned"},
 "spectral": {"brightness": "bright, present", "warmth": "cool"}}
```

**Suno prompt:**
```
Title: Neon Pulse

Style: pop dance, EDM-influenced, pulsing synthesizers, four-on-the-floor beat, 128 BPM, female soprano vocals bright and polished, auto-tuned sheen, euphoric and energetic, crisp modern production, major key, stadium-ready anthem

[Intro: synth arpeggios building, atmospheric, 8 bars]
[Verse: light drums, vocal melody over pulsing synth bass]
[Pre-Chorus: energy building, vocal harmonies layer in]
[Chorus: full drop, powerful vocals, massive synths, euphoric]
[Verse: pull back energy, intimate vocals]
[Pre-Chorus: building again, synth risers]
[Chorus: full energy, anthemic vocals, synth lead]
[Bridge: breakdown, stripped to vocal and piano, vulnerable]
[Build: synth riser, drums building, crescendo]
[Chorus: final drop, maximum energy]
[Outro: fade, synth pad lingers]
```

**Slider recommendations:** Weirdness 20%, Style Influence 85%

---

## Example 4: Acoustic Folk / Americana

**Style being cloned:** Intimate fingerpicked acoustic guitar, female mezzo-soprano with breathy delivery, sparse arrangement. ~95 BPM, G major, warm and organic.

**Key analysis data:**
```json
{"bpm": 95, "key": "G major", "mood": "relaxed, sad, intimate",
 "instruments": ["guitar_acoustic"],
 "vocals": {"gender": "female", "register": "mezzo-soprano", "style": "breathy, clean, with vibrato"},
 "spectral": {"brightness": "warm, balanced", "warmth": "warm", "texture": "tonal, clean"}}
```

**Suno prompt:**
```
Title: Morning Window

Style: intimate folk, fingerpicked acoustic guitar, female mezzo-soprano vocals breathy and gentle with natural vibrato, sparse stripped-down arrangement, warm organic production, 95 BPM laid-back, Americana influence, quiet and contemplative

[Intro: fingerpicked acoustic guitar only, gentle, 4 bars]
[Verse: vocals enter softly, guitar continues fingerpicking pattern]
[Chorus: vocals open up slightly, harmonies enter, still sparse]
[Verse: same intimate feel, subtle variation]
[Chorus: gentle crescendo, fuller harmonies]
[Bridge: guitar changes pattern, vocals more vulnerable]
[Chorus: final, most open and emotional]
[Outro: guitar alone, fade naturally]
```

**Slider recommendations:** Weirdness 15%, Style Influence 90%

---

## Example 5: Ambient Electronic / Synthscape

**Style being cloned:** Expansive ambient electronic with evolving synth textures, no drums, no vocals. Slow-moving, atmospheric. ~70 BPM feel, A minor.

**Key analysis data:**
```json
{"bpm": 70, "key": "A minor", "mood": "dark, relaxed, ethereal",
 "instruments": ["synthesizer"],
 "vocals": {"present": false},
 "spectral": {"brightness": "warm, balanced", "warmth": "warm", "texture": "dense, wide"}}
```

**Suno prompt:**
```
Title: Deep Frequency Drift

Style: ambient electronic, evolving synthesizer textures, expansive atmospheric pads, no drums, slow 70 BPM, dark ethereal mood, warm dense production, reverb-heavy, minor key, cinematic drone, modern ambient

[Instrumental]
[Intro: low frequency drone, slowly evolving pad, atmospheric]
[Interlude: second synth layer enters, shimmering high frequencies]
[Verse: main texture fully developed, slow harmonic movement]
[Bridge: texture shifts, new tonal color, brighter]
[Verse: return to darker palette, deeper bass drone]
[Outro: slow fade, reverb tail extends, silence]
```

**Slider recommendations:** Weirdness 35%, Style Influence 75%

---

## Example 6: Heavy Metal / Thrash

**Style being cloned:** Fast, aggressive thrash metal with distorted guitars, double bass drums, male tenor vocals with gritty delivery. ~170 BPM, E minor.

**Key analysis data:**
```json
{"bpm": 170, "key": "E minor", "mood": "aggressive, energetic, dark",
 "instruments": ["guitar_electric", "drums", "bass_guitar"],
 "vocals": {"gender": "male", "register": "tenor", "style": "raspy, gritty, powerful"},
 "spectral": {"brightness": "bright, present", "warmth": "cool", "texture": "gritty, lo-fi"}}
```

**Suno prompt:**
```
Title: Iron Verdict

Style: thrash metal, fast aggressive 170 BPM, heavily distorted electric guitars, double bass drum blast beats, male tenor vocals raspy and powerful, dark and fierce, raw overdriven production, minor key, 80s Bay Area thrash influence

[Intro: distorted guitar riff, drums kick in hard, 4 bars]
[Verse: full band assault, rapid-fire vocals, driving riff]
[Pre-Chorus: half-time feel briefly, building tension]
[Chorus: anthemic riff, vocals at full power, headbang groove]
[Verse: back to speed, new riff variation]
[Chorus: same intensity, double bass relentless]
[Guitar Solo: shredding lead guitar, wah pedal]
[Bridge: breakdown, slower crushing riff]
[Chorus: final, maximum aggression]
[Outro: drum fill, abrupt stop]
```

**Slider recommendations:** Weirdness 20%, Style Influence 90%

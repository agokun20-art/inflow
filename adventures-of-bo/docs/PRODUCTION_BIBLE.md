# Adventures of Bo - Episode 1: "The Mysterious Boop"
## Production Bible & Shot Package  ·  A Boopmo Original

Runtime 2:00 (120.0 s) · 24 fps · 16:9 master, composed for 2.39:1 · no dialogue · stereo 48 kHz, -16 LUFS / -1 dBTP

---

## 0. Status - what exists and what does not

| Deliverable | Status | File |
|---|---|---|
| Full 120 s animatic, timed to picture lock, with final audio | **Done**: 2.5D procedural animatic, not final CGI | `output/Adventures_of_Bo_E01_The_Mysterious_Boop_ANIMATIC_master.mp4` (CRF 15) + `_web.mp4` (46 MB) |
| Original score (9 cues), signature boop, full sound design | **Done**: final-mix quality, synthesized from scratch | `output/audio/mix_stereo.wav` |
| M&E stems (music / sfx / boops / ambience) | **Done** | `output/audio/stem_*.wav` |
| Signature boop library (4 variants) | **Done** | `output/audio/boop_*.wav` |
| Storyboard (29 panels) + first/last layout frame per shot | **Done** | `output/storyboard_contact_sheet.png`, `output/shot_refs/` |
| Per-shot generation prompts, character lock, QC gates, conform plan | **Done** | this document |
| End-card typography as an edit layer | **Done** | rendered in the animatic; frame in `output/shot_refs/9B_endcard.png` |
| **Feature-quality CGI shots (photoreal fur, 3D lighting)** | **Not produced**: no video/3D generation model is available in this environment | Produce with section 8 prompts, gate with section 9, conform with section 10 |

The animatic is the **timing and staging master**. Every action, cut and camera move in it is final. The CGI pass replaces its pixels shot by shot; the audio is already locked to its frames.

## 1. The episode on one page

**Logline.** On a quiet evening Bo hears a mysterious *boop* and, with the utmost seriousness, investigates the world's smallest mystery. Pip makes it chaotic, Mimi makes it cheerful, Blu makes it make sense. The culprit is Bo's own headphones. Then a boop comes from somewhere else.

**The comedic engine: the Boop Rule.** Every boop before the reveal is caused by Bo tilting his head past ~8.6°, which presses an earcup into his fur. Each of those boops makes his earcup ring flicker (subtly in wide shots). All of Bo's other tilts stay under 5°. The rule makes the reveal fair, makes Bo endearing rather than foolish (the harder he investigates, the more he causes it), and rewards a second viewing. The final boop (1:55.8) breaks the rule on purpose: it is pitched a fourth lower, comes from the hallway, and Bo's ring does **not** flicker.

**Rewatch plants.** (1) Boop 2 happens *because* Bo leans toward the sound. (2) Boop 3 happens as he tilts to look up. (3) In 6B Blu is the only one watching Bo instead of the room. (4) In 9A Bo keeps his head deliberately upright. (5) The hallway has a faint warm-lit room at its far end, which is where the next boop lives.

## 2. Character lock sheet

Source of truth: `refs/boopmo_official_reference.png` (crops: `refs/ref_*.png`). Palette sampled from the official art, then lifted for a warm interior key.

| | Bo | Mimi | Pip | Blu |
|---|---|---|---|---|
| Fur (lit / animatic base) | charcoal `#0c0c0e`-`#1e1e22` / `#1f1f24` | cream `#f2dcd1` / `#ead3c4` | violet `#a323f2` / `#7a12cc` | cobalt `#0053ed` / `#0638c4` |
| Size (H × W, relative to Bo) | 1.00 × 1.10 | 0.89 × 0.97 | 0.91 × 0.97 | 0.81 × 0.87 |
| Eyes | small glossy black ovals, close-set, highlight upper-right | two black ∩ arcs (closed happy eyes); "widen" lifts the arcs, never opens them | glossy black ovals, larger, thin white rim reflection | glossy black ovals, highlight upper-right |
| Accessory | black over-ear headphones, cool blue-white illuminated ring per earcup (`#e4f1ff`), ring flickers only on Bo's boops | black ribbed knit beanie, folded cuff, square black patch with white smiley | none, ever | clear translucent frames, dark smoky lenses, resting on top of head |
| Movement personality | deliberate, curious, still between moves; squash 1.0; lean max 5° except boop tilts | warm, buoyant, soft landings; squash 0.9; happy wiggles | quick, springy, overshoots; squash 1.3; biggest hops | precise; identical evenly-timed hops on the beat; squash 0.7; eye moves in discrete steps |

**Never:** mouths, noses, brows, limbs, humanoid bodies; accessory swaps; new characters; pink characters; bows; colour drift; fur style changes.

## 3. Set bible: Bo's miniature bedroom

Frontal 2.5D stage, single horizon (y = -500); depth z: 0 = stage line, 1 = back wall. Positions in world units (Bo is 300 tall).

| Element | Position | Story function |
|---|---|---|
| Dusk window + rust curtains | x -1385..-885, wall | Establishes evening; cool fill light |
| Patchwork bed + bedside lamp | x -1680..-745 | Warm practical #1 |
| Sage pouf (Bo's seat) | x -550, z 0.10 | Scene 1-2 home base |
| Upright picture book | x -250, z 0.30 | False lead 1 (3A) |
| Book stack (3) | x 60, z 0.45 | Pip's false lead, the top book slides (5C) |
| Mustard floor cushion | x 400 -> 335 (askew after 46.55 s) | False lead 2 (3B); Pip's bonk; Mimi's "pff" |
| Wall clock (second hand ticks with the SFX) | x 130, wall | Makes the silences audible |
| Desk + green desk lamp | x 790..1330, z 0.55 | Warm practical #2; boop 3 / freeze |
| Arched doorway -> hallway | x 1395..1615 | All entrances; source of the final boop |

Lighting: warm tungsten key (lamps), dusk-blue fill (window), ceiling falloff, soft vignette, light grain. Palette keeps the characters' official colours dominant: no saturated set colour sits behind a character of similar hue.

## 4. Shot list (picture-locked)

| Shot | In | Out | Dur | Size | Camera | Action |
|---|---|---|---|---|---|---|
| **1A** | 0:00:00 | 0:07:00 | 7.00s | Extreme wide | Slow dolly-right & push-in | Evening in the miniature bedroom; camera drifts from the dusk window to Bo relaxing on his pouf. |
| **1B** | 0:07:00 | 0:12:00 | 5.00s | Medium | Slow push-in | Bo sways to the music in his headphones, eyes contentedly half-closed. |
| **2A** | 0:12:00 | 0:17:00 | 5.00s | Medium close-up | Locked off | Silence. Bo settles, leans... BOOP. Eyes flick left. He waits. Leans toward the sound... BOOP. |
| **2B** | 0:17:00 | 0:25:00 | 8.00s | Close-up -> extreme close-up | Slow push to eyes | Bo is intrigued; suspicious glances left and right; eyes narrow; a decisive little nod. |
| **3A** | 0:25:00 | 0:31:00 | 6.00s | Medium wide | Follow pan | Bo hops off the pouf, scoots to the standing book and peers around it. Nothing. |
| **3B** | 0:31:00 | 0:35:00 | 4.00s | Medium | Slow push | Bo presses against the floor cushion and stretches to peek over it. Nothing. He deflates. |
| **3C** | 0:35:00 | 0:40:00 | 5.00s | Medium wide -> crash zoom MCU | Track, then snap zoom | Bo rolls to the desk, looks up... BOOP. He freezes. The camera slams in on his frozen face. |
| **4A** | 0:40:00 | 0:43:12 | 3.50s | Medium (doorway) | Slow push | Pip peeks around the doorway, spots Bo, wiggles with excitement. |
| **4B** | 0:43:12 | 0:47:12 | 4.00s | Wide | Pan left with action | Pip bounces across the room, zips past Bo, and bonks the floor cushion out of place. |
| **4C** | 0:47:12 | 0:51:17 | 4.20s | Two-shot | Creeping push | Bo looks at Pip. Pip looks at Bo. Awkward silence. Bo tilts awkwardly... BOOP. |
| **4D** | 0:51:17 | 0:55:00 | 3.30s | Wide | Locked off | Both whip around to stare at the empty left side of the room. Pip bounces; Bo squints. |
| **5A** | 0:55:00 | 0:58:12 | 3.50s | Medium wide | Pan left | Mimi bounces in from the hallway and cheerfully joins the investigators. |
| **5B** | 0:58:12 | 1:02:12 | 4.00s | Wide | Slow push | The search fans out. Mimi bounces onto the cushion - pff! - false alarm. Bo listens. |
| **5C** | 1:02:12 | 1:05:00 | 2.50s | Medium | Slow push | Pip investigates the book stack, bumps it - bop! - and looks hopefully at the others. |
| **5D** | 1:05:00 | 1:07:00 | 2.00s | Close-up | Locked off | Bo, still listening, answers with one slow blink: no. |
| **5E** | 1:07:00 | 1:10:00 | 3.00s | Wide | Slow push | Pip deflates. The trio regroups, puzzled, looking every which way. |
| **6A** | 1:10:00 | 1:13:00 | 3.00s | Medium wide | Slow push | Blu arrives with four perfectly even hops, then scans the room in precise steps. |
| **6B** | 1:13:00 | 1:17:12 | 4.50s | Group | Slow push | Bo tilts toward Blu... BOOP. Pip and Mimi look everywhere. Blu only looks at Bo. |
| **6C** | 1:17:12 | 1:20:00 | 2.50s | Close-up | Slow push | Blu's eyes: Bo... headphones... Bo... headphones. A thoughtful tilt. Idea. |
| **6D** | 1:20:00 | 1:25:00 | 5.00s | Group | Slow push | Bo tilts in confusion... BOOP. Everyone freezes. All eyes slowly travel to Bo. His eyes roll up to his own headphones. |
| **7A** | 1:25:00 | 1:29:12 | 4.50s | Macro insert | Tracking the earcup | The earcup presses into the fur... BOOP. The ring flickers. Mystery solved. |
| **7B** | 1:29:12 | 1:34:12 | 5.00s | Medium close-up | Slow push | Bo tries it again. BOOP. One more time. BOOP! The orchestra erupts. |
| **7C** | 1:34:12 | 1:37:00 | 2.50s | Group | Locked off | Pip bounces wildly, Mimi glows with delight, Blu gives one satisfied tilt. |
| **7D** | 1:37:00 | 1:42:00 | 5.00s | Close-up (to lens) | Imperceptible push | Bo turns and looks straight into the lens. One tiny, embarrassed blink. Hold. |
| **8A** | 1:42:00 | 1:48:18 | 6.75s | Wide group | Slow push | Celebration: Bo bounces, Pip bounces bigger, Mimi joins, all on the beat. Blu stays composed... mostly. |
| **8B** | 1:48:18 | 1:50:10 | 1.65s | Medium | Locked off | Blu launches one tiny, unexpectedly enthusiastic bounce - then re-composes as if nothing happened. |
| **8C** | 1:50:10 | 1:53:00 | 2.60s | Wide group | Slight pull-back | All four bounce together on the final chord. |
| **9A** | 1:53:00 | 1:57:12 | 4.50s | Wide | Hold, then creeping push to the doorway | Peace. Then, from the dark hallway: boop. Four heads turn. Silence. |
| **9B** | 1:57:12 | 2:00:00 | 2.50s | End card | - | Cut to black. ADVENTURES OF BO / A BOOPMO ORIGINAL. A final tiny boop. |

Scenes: 1. A Very Quiet Evening (0:00:00) · 2. The First Boop (0:12:00) · 3. Detective Bo (0:25:00) · 4. Pip Makes an Entrance (0:40:00) · 5. The Investigation Grows (0:55:00) · 6. Blu Has a Theory (1:10:00) · 7. Mystery Solved (1:25:00) · 8. The Celebration (1:42:00) · 9. One More Boop (1:53:00)

## 5. Boop cue sheet (sync-critical: frame-accurate in picture and sound)

| # | Time | Frame | Trigger | Variant | Ring flicker | Read |
|---|---|---|---|---|---|---|
| 1 | 0:13:05 | 317 | Bo settles with a contented lean (8.6 deg) | head | yes | Mystery begins |
| 2 | 0:16:14 | 398 | Bo leans toward "the sound" | head | yes | He causes it by investigating it |
| 3 | 0:37:10 | 898 | Bo tilts to look up at the desk | head | yes | Dramatic freeze + crash zoom |
| 4 | 0:51:14 | 1238 | Bo's awkward tilt in the silence | room | yes | Extra room reverb - seems to come from elsewhere |
| 5 | 1:14:14 | 1790 | Bo tilts curiously toward Blu | head | yes | Blu alone watches Bo, not the room |
| 6 | 1:21:00 | 1944 | Bo tilts in confusion | head | yes | Everyone freezes; realisation dawns |
| 7 | 1:27:00 | 2088 | Macro: cup presses into fur | head | yes | The reveal |
| 8 | 1:30:10 | 2170 | "Again?" | head | yes | Confirmation |
| 9 | 1:32:05 | 2213 | "One more time" - decisive | head | yes | Musical payoff |
| 10 | 1:55:19 | 2779 | NOT Bo - from the hallway; no ring flicker | outside | **no** | Episode hook: lower pitch (A4) = someone else |
| 11 | 1:59:00 | 2856 | End-card button | tiny | **no** | Series mark (ring) pulses |

## 6. Music cue sheet (original, written for this episode)

| Cue | In | Out | Key / tempo | Instrumentation | Function |
|---|---|---|---|---|---|
| 1M1 "Bo's Room" | 0:00:00 | 0:12:00 | F major, 80 BPM | Celesta theme, warm string pad, pizzicato bass, soft flute | Cozy. Bo sways in time. Resolves into silence. |
| 1M2 "Something's There" | 0:19:12 | 0:25:00 | D minor, 100 BPM | Low pizzicato, celesta two-note question, creeping clarinet | Mystery motif; button on the nod. |
| 1M3 "Detective Bo" | 0:25:00 | 0:39:19 | D minor, 120 BPM | Tiptoe pizzicato + staccato clarinet, brushes, shaker; tremolo suspensions; stab + timpani | Stops on every "nothing"; dramatic stab on boop 3. |
| 1M4 "Pip!" | 0:40:00 | 0:46:14 | C major colour | Plucked synth, marimba runs mickey-moused to each hop | Cuts dead on the bonk; 5 s of awkward silence. |
| 1M5 "Search Party" | 0:55:00 | 1:10:00 | F major, 120 BPM | Flute (Mimi motif), marimba off-beats, chromatic clarinet, pizzicato | Built around false-lead stops (pff, bop, slow blink). |
| 1M6 "Blu's Theory" | 1:10:00 | 1:19:14 | D minor rising sequence, 120 BPM | Plucked-synth 16th ostinato, woodblock ticks, marimba doubling | Blu hops on the beat; sequence climbs to an unresolved A7 and cuts at the idea. |
| 1M7 "Boop!" | 1:24:00 | 1:42:00 | D -> F major, 120 BPM | Low swell; celesta answers boop pitch (D); pizz "ta-da" in D major; roll; full payoff hit + fanfare | Silence held for Bo's look to camera; one celesta plink on the blink. |
| 1M8 "Celebration" | 1:42:00 | 1:53:12 | F major, 120 BPM | Full Bo theme: flute/celesta/clarinet, marimba, pizz, kick + brushes | Every bounce lands on a beat; break + slide whistle for Blu's bounce. |
| 1M9 "Settle" + end card | 1:53:00 | 2:00:00 | F major | Fmaj9 pad, celesta arpeggio; title: celesta Bo-theme fragment | Fades to total silence before the hallway boop. |

**Bo theme** (F major): A4 C5 F5 E5 | D5 C5 A4 | Bb4 D5 G5 F5 | E5 G5 ... resolving to F. It is stated gently in 1M1, as a fanfare in 1M7 and in full in 1M8; the end card quotes its first three notes. The boop sits on D5, so the score can answer it (1M7: celesta D6).

## 7. Sound design

**Signature boop** (series asset, `output/audio/boop_signature.wav`): a soft "b" onset (4 ms low-passed burst + 150 Hz thump), a rounded pitched "oo" body on D5 (sine + 2nd/3rd/4th harmonics at -13/-25/-32 dB) with a tiny contour (starts 15% flat, rises ~3.5% sharp at 30 ms, settles, droops 3.5% at the end), a 32 Hz plush wobble, and a gentle "p" closure (3 ms pop) at 165 ms. Variants: *headphones* (adds a 70 ms fabric-compression pre-layer), *room* (extra reflections, -1.7 dB), *outside* (A4, darker, longer, hallway reverb, -4 dB: clearly "someone else"), *end card* (A5, 110 ms).

**Foley/SFX events generated from the animation** (bonk: 1, book_slide: 1, bop: 1, deflate: 2, freeze: 2, land: 57, nod: 1, pff: 2, pouf: 1, scan: 4, scoot: 8, stretch: 2, takeoff: 57, whip: 4, wiggle: 2). Plush landings scale with hop height and character size, and each character has its own thump pitch. Scoots are amplitude-modulated at the 4.2 Hz squish cycle; pans follow on-screen position per shot. Ambience is a low room tone and the wall clock ticking once per second, in sync with its painted second hand. Both drop to absolute silence on the final head-turn (1:56.0).

**Mix:** -16.0 LUFS integrated, -1.0 dBTP (4x-oversampled); limiter acts only on the four orchestral hits (max 5.8 dB, 0.16% of runtime). Head-boops sit at -14.6 dB RMS, 6-40 dB above their bed. For broadcast (-23/-24 LUFS), re-mix from stems instead of turning the master down.

## 8. Shot-by-shot generation prompts

**Recommended pipeline (per shot):** (a) generate 1-3 CGI *keyframes* with an image model, using the official reference crops as character references and the `output/shot_refs/<shot>_first.png` / `_last.png` frames as **layout/composition guides only** (not style); (b) QC the keyframes (section 9); (c) image-to-video from first/last keyframes with the prompt below at the exact duration; (d) QC again; (e) conform (section 10). Never use the animatic frames as direct start frames: their 2D look will bleed into the output.

**Global style lock (prepend to every prompt):** Premium feature-animation CGI. Photoreal plush fur with fine individual strands, soft clumping and subsurface softness. Warm practical evening interior light: tungsten desk lamp and small bedside lamp as key, dusk-blue window as fill, natural shadow falloff. Shallow cinematic depth of field, 2.39:1 composition, gentle film grain, soft warm grade. A miniature bedroom built to the characters' scale: honey-oak plank floor, terracotta oval rug, sage-green wainscot, apricot striped wallpaper, dusk window with rust curtains, patchwork-quilt bed, wall clock, bookshelf, small wooden desk with a green desk lamp, arched doorway to a dim cool hallway with a faint warm light at its far end.

**Character lock (prepend; attach reference images):** Attach refs/ref_bo.png, ref_mimi.png, ref_pip.png, ref_blu.png. Round soft plush creatures with NO mouth, nose, eyebrows, arms, hands or legs; they move only by tilting, squashing, stretching, scooting and hopping. BO: charcoal-black fur; small glossy black oval eyes, set fairly close, with white highlights; black over-ear headphones, each earcup with a subtle cool blue-white illuminated ring. MIMI: warm cream-white fur; black ribbed knit beanie with a small square black patch showing a white smiley; eyes are two curved black arcs (closed happy eyes). PIP: vibrant violet-purple fur; glossy black oval eyes with a thin white rim reflection; no accessories. BLU: electric cobalt-blue fur; clear translucent sunglasses with dark lenses resting on top of the head; glossy black oval eyes.

**Negative prompt (every shot):** mouth, teeth, tongue, nose, eyebrows, arms, hands, fingers, legs, feet, humanoid body, text, logo, watermark, extra characters, pink characters, bows, headwear on anyone but Mimi, headphones on anyone but Bo, glasses on anyone but Blu, color drift, neon, glowing particles, sparkles, magic effects, oversharpening, warped or melting accessories, duplicated eyes, camera shake

### 1A: 0:00:00-0:07:00 (7.00s) · Extreme wide · Slow dolly-right & push-in
Extreme wide establishing shot, slow dolly right with a gentle push-in. Evening in the miniature bedroom: dusk sky in the window, warm bedside lamp glowing beside the patchwork bed. The camera drifts from the window to Bo sitting on a round sage-green pouf in the middle of the rug, headphones on, swaying very gently to music. Calm, cozy, still.
*References:* layout `shot_refs/1A_first.png` -> `_last.png`; characters in shot: bo.

### 1B: 0:07:00-0:12:00 (5.00s) · Medium · Slow push-in
Medium shot of Bo on his pouf, slow push-in. Bo sways softly side to side in rhythm (2-3 degrees, never more), eyes contentedly half-lidded; the earcup rings glow faintly. Warm lamp bokeh behind him.
*References:* layout `shot_refs/1B_first.png` -> `_last.png`; characters in shot: bo.

### 2A: 0:12:00-0:17:00 (5.00s) · Medium close-up · Locked off
Medium close-up, locked off, quiet room. Bo settles with a contented lean to his right (about 9 degrees); at that instant his right earcup presses into his fur and its ring flickers briefly. His eyes open fully and flick left. He straightens slowly and waits, perfectly still. Then he leans left toward where he thinks the sound came from (about 9 degrees); the left ring flickers; his eyes widen slightly.
*References:* layout `shot_refs/2A_first.png` -> `_last.png`; characters in shot: bo. *Sync points:* boop at 0:13:05 (head), 0:16:14 (head); ring flicker must land on that frame.

### 2B: 0:17:00-0:25:00 (8.00s) · Close-up -> extreme close-up · Slow push to eyes
Slow push from close-up to extreme close-up on Bo's eyes. He straightens. Eyes glance suspiciously left, then right, then centre. One blink; his upper lids lower into a determined squint (inner corners lower). One small decisive nod made by squashing down slightly. Background deeply out of focus.
*References:* layout `shot_refs/2B_first.png` -> `_last.png`; characters in shot: bo.

### 3A: 0:25:00-0:31:00 (6.00s) · Medium wide · Follow pan
Medium-wide follow pan. Bo hops off the pouf (anticipation squash, soft landing squash), scoots to a large upright picture book standing on the floor, turns three-quarters and stretches sideways to peek around its edge (tilt under 5 degrees). Nothing. A blink, he pulls back, then two small hops toward a mustard floor cushion.
*References:* layout `shot_refs/3A_first.png` -> `_last.png`; characters in shot: bo.

### 3B: 0:31:00-0:35:00 (4.00s) · Medium · Slow push
Medium shot. Bo presses against the side of a puffy mustard floor cushion, stretches tall and leans to peek over it, eyes looking down behind it. Nothing. He deflates - a slow squash down and outward - then recovers into a determined squint, eyes turning toward the desk.
*References:* layout `shot_refs/3B_first.png` -> `_last.png`; characters in shot: bo.

### 3C: 0:35:00-0:40:00 (5.00s) · Medium wide -> crash zoom MCU · Track, then snap zoom
Medium-wide tracking shot: Bo scoots across the floor to the foot of the wooden desk, stops, looks up and tilts back to his right; his earcup presses into his fur and the ring flickers. He freezes instantly - eyes wide, no breathing, no motion. On the freeze the camera snap-zooms to a medium close-up of his frozen face.
*References:* layout `shot_refs/3C_first.png` -> `_last.png`; characters in shot: bo. *Sync points:* boop at 0:37:10 (head); ring flicker must land on that frame.

### 4A: 0:40:00-0:43:12 (3.50s) · Medium (doorway) · Slow push
Medium shot on the arched doorway. Pip, the violet fuzzball, slides into view from behind the right side of the door frame, half hidden, eyes scanning the room. Pip spots something off-screen left; eyes widen; a rapid excited wiggle.
*References:* layout `shot_refs/4A_first.png` -> `_last.png`; characters in shot: bo, pip.

### 4B: 0:43:12-0:47:12 (4.00s) · Wide · Pan left with action
Wide shot, camera panning left with the action. Pip bounces into the room in four quick springy hops with big squash and stretch, zips right past Bo (whose eyes track Pip), and on the fifth hop bonks into the mustard floor cushion, knocking it askew; Pip rebounds with a small hop. Soft muffled impact; nothing breaks.
*References:* layout `shot_refs/4B_first.png` -> `_last.png`; characters in shot: bo, pip.

### 4C: 0:47:12-0:51:17 (4.20s) · Two-shot · Creeping push
Two-shot: Pip on the left, Bo on the right, facing each other in awkward silence. Pip blinks. Bo blinks. Pip squishes down a little, sheepish. Then Bo slowly tilts his head to the right past 9 degrees; his ring flickers.
*References:* layout `shot_refs/4C_first.png` -> `_last.png`; characters in shot: bo, pip. *Sync points:* boop at 0:51:14 (room); ring flicker must land on that frame.

### 4D: 0:51:17-0:55:00 (3.30s) · Wide · Locked off
Wide shot, locked off. Bo and Pip, small on the right of frame, whip their gaze and bodies to the left at the same instant and stare at the empty left side of the room. Pip bounces excitedly twice in place; Bo narrows his eyes suspiciously.
*References:* layout `shot_refs/4D_first.png` -> `_last.png`; characters in shot: bo, pip.

### 5A: 0:55:00-0:58:12 (3.50s) · Medium wide · Pan left
Medium-wide, slow pan left. Mimi - cream fuzzball, black beanie with the smiley patch - bounces in from the dim hallway through the arched doorway in four cheerful hops and lands near Bo and Pip, who turn to look. Mimi does a happy little wiggle; her arc eyes lift.
*References:* layout `shot_refs/5A_first.png` -> `_last.png`; characters in shot: bo, mimi, pip.

### 5B: 0:58:12-1:02:12 (4.00s) · Wide · Slow push
Wide shot. The search fans out: Pip hops toward a stack of books by the wall; Bo scoots to centre and goes still, eyes squinted, listening; Mimi bounces up onto the mustard cushion and sinks into it as it deflates with a comic puff of air. Everyone glances at the cushion. Mimi bounces once more - another puff. Not it. Mimi gives a happy shrug-stretch.
*References:* layout `shot_refs/5B_first.png` -> `_last.png`; characters in shot: bo, mimi, pip.

### 5C: 1:02:12-1:05:00 (2.50s) · Medium · Slow push
Medium shot focused on Pip at a small stack of three books. Pip leans in curiously and bumps the stack; the top book slides a little. Pip freezes, eyes wide, then turns hopefully toward the others with a small hopeful bounce. Mimi soft and out of focus in the foreground.
*References:* layout `shot_refs/5C_first.png` -> `_last.png`; characters in shot: bo, mimi, pip.

### 5D: 1:05:00-1:07:00 (2.00s) · Close-up · Locked off
Close-up of Bo, still squinting, listening. He answers Pip's hopeful look with one slow, deliberate blink: no. Mimi soft and out of focus at frame left.
*References:* layout `shot_refs/5D_first.png` -> `_last.png`; characters in shot: bo, mimi, pip.

### 5E: 1:07:00-1:10:00 (3.00s) · Wide · Slow push
Wide shot. Pip deflates, then the three regroup in the middle of the rug, each looking a different way, puzzled: Mimi tilts, Pip's eyes dart left and right, Bo stares at the floor, thinking.
*References:* layout `shot_refs/5E_first.png` -> `_last.png`; characters in shot: bo, mimi, pip.

### 6A: 1:10:00-1:13:00 (3.00s) · Medium wide · Slow push
Medium-wide on the doorway. Blu - cobalt fuzzball with clear sunglasses on top of his head - enters with four perfectly identical, evenly timed hops and stops precisely. A small glint slides across the lenses. His eyes scan the room in four exact steps, left to right.
*References:* layout `shot_refs/6A_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 6B: 1:13:00-1:17:12 (4.50s) · Group · Slow push
Group shot. Pip, Mimi and Bo notice Blu and turn toward him. Bo tilts curiously toward Blu past 9 degrees; his ring flickers. Pip and Mimi whip around looking everywhere else (up, left). Blu does not look away: his eyes narrow and lock onto Bo. Bo straightens and does a little shrug-stretch.
*References:* layout `shot_refs/6B_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu. *Sync points:* boop at 1:14:14 (head); ring flicker must land on that frame.

### 6C: 1:17:12-1:20:00 (2.50s) · Close-up · Slow push
Close-up of Blu, slow push-in. Narrowed eyes move with precision: to Bo... up to Bo's headphones... back to Bo... up to the headphones. A small thoughtful tilt. Then his eyes widen slightly: an idea. Bo soft and out of focus at frame left.
*References:* layout `shot_refs/6C_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 6D: 1:20:00-1:25:00 (5.00s) · Group · Slow push
Group shot, slow push. Blu stares pointedly at Bo's headphones. Bo, confused, tilts his head past 9 degrees; his ring flickers; everyone freezes completely. Blu's eyes travel up to the headphones again. Pip and Mimi slowly turn to stare at Bo. Bo, frozen mid-tilt, slowly rolls his eyes up toward his own headphones. Hold.
*References:* layout `shot_refs/6D_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu. *Sync points:* boop at 1:21:00 (head); ring flicker must land on that frame.

### 7A: 1:25:00-1:29:12 (4.50s) · Macro insert · Tracking the earcup
Macro insert, tracking the earcup: extreme close-up of Bo's right earcup against charcoal fur, his eye at frame left. Bo slowly straightens, then slowly tilts again: the earcup cushion presses into the fur, the fur visibly compresses around it, and the blue-white ring flickers at the exact moment of contact. Blu's cobalt fur deeply out of focus behind.
*References:* layout `shot_refs/7A_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu. *Sync points:* boop at 1:27:00 (head); ring flicker must land on that frame.

### 7B: 1:29:12-1:34:12 (5.00s) · Medium close-up · Slow push
Medium close-up of Bo. He tries it again: tilt, ring flicker, eyes widen. He straightens. One more decisive tilt: ring flicker, and his eyes go wide with delight.
*References:* layout `shot_refs/7B_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu. *Sync points:* boop at 1:30:10 (head), 1:32:05 (head); ring flicker must land on that frame.

### 7C: 1:34:12-1:37:00 (2.50s) · Group · Locked off
Group shot, locked off. Pip bounces rapidly four times; Mimi bounces twice, arc eyes lifted in delight; Blu, composed, gives one small satisfied tilt. Bo looks from friend to friend.
*References:* layout `shot_refs/7C_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 7D: 1:37:00-1:42:00 (5.00s) · Close-up (to lens) · Imperceptible push
Close-up, near-imperceptible push-in. Bo turns and looks straight into the lens. One tiny, slow, embarrassed blink. He sinks down just a little. Hold the look. Friends soft and out of focus at the frame edges.
*References:* layout `shot_refs/7D_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 8A: 1:42:00-1:48:18 (6.75s) · Wide group · Slow push
Wide group shot, motion on a 120 BPM beat. Bo does a small celebratory bounce; Pip answers with a much bigger, wobbling bounce; Mimi joins; then the three bounce together on every beat. Blu stays perfectly composed, only his eyes following them and a tiny dip on each beat.
*References:* layout `shot_refs/8A_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 8B: 1:48:18-1:50:10 (1.65s) · Medium · Locked off
Medium shot on Blu. Without warning Blu launches one tiny but unexpectedly high, springy, enthusiastic bounce with a little wobble, a glint on the sunglasses at the apex, and a precise landing. A tiny shimmy resettles the sunglasses and he resumes composure as if nothing happened. Friends, out of focus, stare at him.
*References:* layout `shot_refs/8B_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 8C: 1:50:10-1:53:00 (2.60s) · Wide group · Slight pull-back
Wide group shot. All four bounce together on the last two beats and land in a neat row on the rug, happy.
*References:* layout `shot_refs/8C_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu.

### 9A: 1:53:00-1:57:12 (4.50s) · Wide · Hold, then creeping push to the doorway
Wide shot including the dark arched doorway at frame right. Peace: the four relax, breathing slowly; Mimi leans gently toward Pip; Bo keeps his head carefully upright. Then all four heads snap simultaneously toward the dark doorway, eyes slightly widened. Bo's rings do NOT flicker. Absolute stillness. Slow creeping push toward the doorway.
*References:* layout `shot_refs/9A_first.png` -> `_last.png`; characters in shot: bo, mimi, pip, blu. *Sync points:* boop at 1:55:19 (outside); ring flicker must land on that frame.

### 9B: End card (not generated)
Black. "ADVENTURES OF BO" (Inter Display ExtraBold, +7% tracking, #F6F5F2) fades and rises in at 1:57.9; "A BOOPMO ORIGINAL" (Inter Display Medium, +42% tracking, #B8BDC7) at 1:58.4; Bo's headphone ring as the series mark above, which pulses with the final tiny boop at 1:59.0. Build as editorial text layers, never generated.

## 9. QC gates (apply to every keyframe and every generated clip)

A shot is rejected, not patched into the edit, if it fails any of these:

1. Bo's headphones present, correct (black, over-ear, both cups), ring cool blue-white and subtle; ring flicker only on boop frames.
2. Mimi's black ribbed beanie and square smiley patch intact and legible (no garbled glyphs); eyes remain arcs.
3. Pip is violet-purple (not pink or magenta) and has no accessories.
4. Blu's clear sunglasses sit on top of the head, one pair, undistorted.
5. Eyes match the lock sheet: shape, size and spacing, no added whites (except Pip's thin rim), no duplicated eyes.
6. Fur texture and proportions match the references; relative sizes Bo > Pip ≈ Mimi > Blu.
7. No mouths, noses, brows, arms, hands, legs or humanoid features in any frame.
8. Lighting, set geometry and prop state match neighbouring shots (cushion askew after 0:46.55; top book offset after 1:03.75).
9. Motion has weight: anticipation, squash/stretch, settle; no floating or jitter; Bo's non-boop tilts stay under ~5°.
10. The shot advances the story exactly as the animatic does; timing within ±2 frames at every sync point.

Known failure modes to screen for: accessory migration between characters in group shots; beanie patch turning into text; extra creature appearing in doorway shots; fur colour drifting under warm light (re-grade, don't accept); headphone band merging into fur; glasses duplicating during Blu's bounce.

## 10. Conform & delivery

1. Import `Adventures_of_Bo_E01_..._ANIMATIC_master.mp4` (24 fps) as the offline reference and `output/audio/mix_stereo.wav` + stems on locked tracks.
2. Replace shots one at a time on V2 over the animatic. Each generated clip must match the shot's duration; retime only between sync points and keep every boop frame (section 5) exact.
3. Grade to the animatic's look: warm evening, protected character colours, light vignette, fine grain; 2.39:1 matte (138 px bars at 1080p).
4. End card from editorial text layers (section 8, 9B).
5. Deliver: ProRes 4444 master, H.264 web (CRF 16-18), stereo 48 kHz -16 LUFS / -1 dBTP; M&E stems for localisation.

## 11. Series notes: the Boopmo universe

- **Recurring devices:** the signature boop (always D5 for Bo's headphones); the ring flicker as a visual "tell"; Blu's one tiny unexpectedly enthusiastic bounce; Pip's collisions with soft objects; Mimi's "pff" cushion.
- **Episode 2 hook, already planted:** the hallway boop is a different pitch (A4) and comes from the warm-lit room at the end of the hallway. Whatever makes it is new to the crew, and the audience has heard it first.
- **Spin-offs:** *Adventures of Mimi* (cheer as a superpower), *of Pip* (chaos with good intentions), *of Blu* (the precise one who secretly loves to bounce).
- Every episode should stay understandable with the sound off and funny with the sound on.

## 12. Reproducing this package

```bash
pip install scipy skia-python pyloudnorm pillow numpy    # + ffmpeg, libegl1
python src/timeline.py            # continuity validation (Boop Rule, shot coverage)
python src/audio.py               # score + SFX + master + stems
python src/render.py video         # 120 s picture (4 workers)
python src/render.py contact       # storyboard sheet
python src/build_docs.py          # this document + shot reference frames
```

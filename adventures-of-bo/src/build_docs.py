"""Builds docs/PRODUCTION_BIBLE.md from the master timeline (so timings never drift)
and exports first/last layout frames per shot to output/shot_refs/."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import timeline as TL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tc(t):
    f = int(round((t % 1) * TL.FPS))
    s = int(t)
    if f == TL.FPS:
        s, f = s + 1, 0
    return f'{s // 60}:{s % 60:02d}:{f:02d}'


STYLE_LOCK = (
    "Premium feature-animation CGI. Photoreal plush fur with fine individual strands, soft clumping and subsurface softness. "
    "Warm practical evening interior light: tungsten desk lamp and small bedside lamp as key, dusk-blue window as fill, natural shadow falloff. "
    "Shallow cinematic depth of field, 2.39:1 composition, gentle film grain, soft warm grade. A miniature bedroom built to the characters' scale: "
    "honey-oak plank floor, terracotta oval rug, sage-green wainscot, apricot striped wallpaper, dusk window with rust curtains, patchwork-quilt bed, "
    "wall clock, bookshelf, small wooden desk with a green desk lamp, arched doorway to a dim cool hallway with a faint warm light at its far end.")

CHAR_LOCK = (
    "Attach refs/ref_bo.png, ref_mimi.png, ref_pip.png, ref_blu.png. Round soft plush creatures with NO mouth, nose, eyebrows, arms, hands or legs; "
    "they move only by tilting, squashing, stretching, scooting and hopping. "
    "BO: charcoal-black fur; small glossy black oval eyes, set fairly close, with white highlights; black over-ear headphones, each earcup with a subtle cool blue-white illuminated ring. "
    "MIMI: warm cream-white fur; black ribbed knit beanie with a small square black patch showing a white smiley; eyes are two curved black arcs (closed happy eyes). "
    "PIP: vibrant violet-purple fur; glossy black oval eyes with a thin white rim reflection; no accessories. "
    "BLU: electric cobalt-blue fur; clear translucent sunglasses with dark lenses resting on top of the head; glossy black oval eyes.")

NEGATIVE = ("mouth, teeth, tongue, nose, eyebrows, arms, hands, fingers, legs, feet, humanoid body, text, logo, watermark, extra characters, "
            "pink characters, bows, headwear on anyone but Mimi, headphones on anyone but Bo, glasses on anyone but Blu, color drift, neon, "
            "glowing particles, sparkles, magic effects, oversharpening, warped or melting accessories, duplicated eyes, camera shake")

PROMPTS = {
    '1A': "Extreme wide establishing shot, slow dolly right with a gentle push-in. Evening in the miniature bedroom: dusk sky in the window, warm bedside lamp glowing beside the patchwork bed. The camera drifts from the window to Bo sitting on a round sage-green pouf in the middle of the rug, headphones on, swaying very gently to music. Calm, cozy, still.",
    '1B': "Medium shot of Bo on his pouf, slow push-in. Bo sways softly side to side in rhythm (2-3 degrees, never more), eyes contentedly half-lidded; the earcup rings glow faintly. Warm lamp bokeh behind him.",
    '2A': "Medium close-up, locked off, quiet room. Bo settles with a contented lean to his right (about 9 degrees); at that instant his right earcup presses into his fur and its ring flickers briefly. His eyes open fully and flick left. He straightens slowly and waits, perfectly still. Then he leans left toward where he thinks the sound came from (about 9 degrees); the left ring flickers; his eyes widen slightly.",
    '2B': "Slow push from close-up to extreme close-up on Bo's eyes. He straightens. Eyes glance suspiciously left, then right, then centre. One blink; his upper lids lower into a determined squint (inner corners lower). One small decisive nod made by squashing down slightly. Background deeply out of focus.",
    '3A': "Medium-wide follow pan. Bo hops off the pouf (anticipation squash, soft landing squash), scoots to a large upright picture book standing on the floor, turns three-quarters and stretches sideways to peek around its edge (tilt under 5 degrees). Nothing. A blink, he pulls back, then two small hops toward a mustard floor cushion.",
    '3B': "Medium shot. Bo presses against the side of a puffy mustard floor cushion, stretches tall and leans to peek over it, eyes looking down behind it. Nothing. He deflates - a slow squash down and outward - then recovers into a determined squint, eyes turning toward the desk.",
    '3C': "Medium-wide tracking shot: Bo scoots across the floor to the foot of the wooden desk, stops, looks up and tilts back to his right; his earcup presses into his fur and the ring flickers. He freezes instantly - eyes wide, no breathing, no motion. On the freeze the camera snap-zooms to a medium close-up of his frozen face.",
    '4A': "Medium shot on the arched doorway. Pip, the violet fuzzball, slides into view from behind the right side of the door frame, half hidden, eyes scanning the room. Pip spots something off-screen left; eyes widen; a rapid excited wiggle.",
    '4B': "Wide shot, camera panning left with the action. Pip bounces into the room in four quick springy hops with big squash and stretch, zips right past Bo (whose eyes track Pip), and on the fifth hop bonks into the mustard floor cushion, knocking it askew; Pip rebounds with a small hop. Soft muffled impact; nothing breaks.",
    '4C': "Two-shot: Pip on the left, Bo on the right, facing each other in awkward silence. Pip blinks. Bo blinks. Pip squishes down a little, sheepish. Then Bo slowly tilts his head to the right past 9 degrees; his ring flickers.",
    '4D': "Wide shot, locked off. Bo and Pip, small on the right of frame, whip their gaze and bodies to the left at the same instant and stare at the empty left side of the room. Pip bounces excitedly twice in place; Bo narrows his eyes suspiciously.",
    '5A': "Medium-wide, slow pan left. Mimi - cream fuzzball, black beanie with the smiley patch - bounces in from the dim hallway through the arched doorway in four cheerful hops and lands near Bo and Pip, who turn to look. Mimi does a happy little wiggle; her arc eyes lift.",
    '5B': "Wide shot. The search fans out: Pip hops toward a stack of books by the wall; Bo scoots to centre and goes still, eyes squinted, listening; Mimi bounces up onto the mustard cushion and sinks into it as it deflates with a comic puff of air. Everyone glances at the cushion. Mimi bounces once more - another puff. Not it. Mimi gives a happy shrug-stretch.",
    '5C': "Medium shot focused on Pip at a small stack of three books. Pip leans in curiously and bumps the stack; the top book slides a little. Pip freezes, eyes wide, then turns hopefully toward the others with a small hopeful bounce. Mimi soft and out of focus in the foreground.",
    '5D': "Close-up of Bo, still squinting, listening. He answers Pip's hopeful look with one slow, deliberate blink: no. Mimi soft and out of focus at frame left.",
    '5E': "Wide shot. Pip deflates, then the three regroup in the middle of the rug, each looking a different way, puzzled: Mimi tilts, Pip's eyes dart left and right, Bo stares at the floor, thinking.",
    '6A': "Medium-wide on the doorway. Blu - cobalt fuzzball with clear sunglasses on top of his head - enters with four perfectly identical, evenly timed hops and stops precisely. A small glint slides across the lenses. His eyes scan the room in four exact steps, left to right.",
    '6B': "Group shot. Pip, Mimi and Bo notice Blu and turn toward him. Bo tilts curiously toward Blu past 9 degrees; his ring flickers. Pip and Mimi whip around looking everywhere else (up, left). Blu does not look away: his eyes narrow and lock onto Bo. Bo straightens and does a little shrug-stretch.",
    '6C': "Close-up of Blu, slow push-in. Narrowed eyes move with precision: to Bo... up to Bo's headphones... back to Bo... up to the headphones. A small thoughtful tilt. Then his eyes widen slightly: an idea. Bo soft and out of focus at frame left.",
    '6D': "Group shot, slow push. Blu stares pointedly at Bo's headphones. Bo, confused, tilts his head past 9 degrees; his ring flickers; everyone freezes completely. Blu's eyes travel up to the headphones again. Pip and Mimi slowly turn to stare at Bo. Bo, frozen mid-tilt, slowly rolls his eyes up toward his own headphones. Hold.",
    '7A': "Macro insert, tracking the earcup: extreme close-up of Bo's right earcup against charcoal fur, his eye at frame left. Bo slowly straightens, then slowly tilts again: the earcup cushion presses into the fur, the fur visibly compresses around it, and the blue-white ring flickers at the exact moment of contact. Blu's cobalt fur deeply out of focus behind.",
    '7B': "Medium close-up of Bo. He tries it again: tilt, ring flicker, eyes widen. He straightens. One more decisive tilt: ring flicker, and his eyes go wide with delight.",
    '7C': "Group shot, locked off. Pip bounces rapidly four times; Mimi bounces twice, arc eyes lifted in delight; Blu, composed, gives one small satisfied tilt. Bo looks from friend to friend.",
    '7D': "Close-up, near-imperceptible push-in. Bo turns and looks straight into the lens. One tiny, slow, embarrassed blink. He sinks down just a little. Hold the look. Friends soft and out of focus at the frame edges.",
    '8A': "Wide group shot, motion on a 120 BPM beat. Bo does a small celebratory bounce; Pip answers with a much bigger, wobbling bounce; Mimi joins; then the three bounce together on every beat. Blu stays perfectly composed, only his eyes following them and a tiny dip on each beat.",
    '8B': "Medium shot on Blu. Without warning Blu launches one tiny but unexpectedly high, springy, enthusiastic bounce with a little wobble, a glint on the sunglasses at the apex, and a precise landing. A tiny shimmy resettles the sunglasses and he resumes composure as if nothing happened. Friends, out of focus, stare at him.",
    '8C': "Wide group shot. All four bounce together on the last two beats and land in a neat row on the rug, happy.",
    '9A': "Wide shot including the dark arched doorway at frame right. Peace: the four relax, breathing slowly; Mimi leans gently toward Pip; Bo keeps his head carefully upright. Then all four heads snap simultaneously toward the dark doorway, eyes slightly widened. Bo's rings do NOT flicker. Absolute stillness. Slow creeping push toward the doorway.",
}

BOOP_NOTES = {
    13.2: ('Bo settles with a contented lean (8.6 deg)', 'Mystery begins'),
    16.6: ('Bo leans toward "the sound"', 'He causes it by investigating it'),
    37.4: ('Bo tilts to look up at the desk', 'Dramatic freeze + crash zoom'),
    51.6: ('Bo\'s awkward tilt in the silence', 'Extra room reverb - seems to come from elsewhere'),
    74.6: ('Bo tilts curiously toward Blu', 'Blu alone watches Bo, not the room'),
    81.0: ('Bo tilts in confusion', 'Everyone freezes; realisation dawns'),
    87.0: ('Macro: cup presses into fur', 'The reveal'),
    90.4: ('"Again?"', 'Confirmation'),
    92.2: ('"One more time" - decisive', 'Musical payoff'),
    115.8: ('NOT Bo - from the hallway; no ring flicker', 'Episode hook: lower pitch (A4) = someone else'),
    119.0: ('End-card button', 'Series mark (ring) pulses'),
}

MUSIC = [
    ('1M1 "Bo\'s Room"', 0.0, 12.0, 'F major, 80 BPM', 'Celesta theme, warm string pad, pizzicato bass, soft flute', 'Cozy. Bo sways in time. Resolves into silence.'),
    ('1M2 "Something\'s There"', 19.5, 25.0, 'D minor, 100 BPM', 'Low pizzicato, celesta two-note question, creeping clarinet', 'Mystery motif; button on the nod.'),
    ('1M3 "Detective Bo"', 25.0, 39.8, 'D minor, 120 BPM', 'Tiptoe pizzicato + staccato clarinet, brushes, shaker; tremolo suspensions; stab + timpani', 'Stops on every "nothing"; dramatic stab on boop 3.'),
    ('1M4 "Pip!"', 40.0, 46.6, 'C major colour', 'Plucked synth, marimba runs mickey-moused to each hop', 'Cuts dead on the bonk; 5 s of awkward silence.'),
    ('1M5 "Search Party"', 55.0, 70.0, 'F major, 120 BPM', 'Flute (Mimi motif), marimba off-beats, chromatic clarinet, pizzicato', 'Built around false-lead stops (pff, bop, slow blink).'),
    ('1M6 "Blu\'s Theory"', 70.0, 79.6, 'D minor rising sequence, 120 BPM', 'Plucked-synth 16th ostinato, woodblock ticks, marimba doubling', 'Blu hops on the beat; sequence climbs to an unresolved A7 and cuts at the idea.'),
    ('1M7 "Boop!"', 84.0, 102.0, 'D -> F major, 120 BPM', 'Low swell; celesta answers boop pitch (D); pizz "ta-da" in D major; roll; full payoff hit + fanfare', 'Silence held for Bo\'s look to camera; one celesta plink on the blink.'),
    ('1M8 "Celebration"', 102.0, 113.5, 'F major, 120 BPM', 'Full Bo theme: flute/celesta/clarinet, marimba, pizz, kick + brushes', 'Every bounce lands on a beat; break + slide whistle for Blu\'s bounce.'),
    ('1M9 "Settle" + end card', 113.0, 120.0, 'F major', 'Fmaj9 pad, celesta arpeggio; title: celesta Bo-theme fragment', 'Fades to total silence before the hallway boop.'),
]


def export_refs():
    from PIL import Image
    import render as R
    d = os.path.join(ROOT, 'output', 'shot_refs')
    os.makedirs(d, exist_ok=True)
    A = R.Assets()
    for s in TL.SHOTS:
        if s.sid == '9B':
            t = 119.2
            Image.fromarray(R.render_frame(A, t, 0)).save(os.path.join(d, '9B_endcard.png'))
            continue
        for tag, t in (('first', s.t0 + 0.01), ('last', s.t1 - 1 / TL.FPS)):
            arr = R.render_frame(A, t, int(t * TL.FPS))
            Image.fromarray(arr[R.BAR:R.H - R.BAR]).save(os.path.join(d, f'{s.sid}_{tag}.png'))


def build():
    L = []
    w = L.append
    w('# Adventures of Bo - Episode 1: "The Mysterious Boop"')
    w('## Production Bible & Shot Package  ·  A Boopmo Original\n')
    w('Runtime 2:00 (120.0 s) · 24 fps · 16:9 master, composed for 2.39:1 · no dialogue · stereo 48 kHz, -16 LUFS / -1 dBTP\n')
    w('---\n')
    w('## 0. Status - what exists and what does not\n')
    w('| Deliverable | Status | File |')
    w('|---|---|---|')
    w('| Full 120 s animatic, timed to picture lock, with final audio | **Done**: 2.5D procedural animatic, not final CGI | `output/Adventures_of_Bo_E01_The_Mysterious_Boop_ANIMATIC_master.mp4` (CRF 15) + `_web.mp4` (46 MB) |')
    w('| Original score (9 cues), signature boop, full sound design | **Done**: final-mix quality, synthesized from scratch | `output/audio/mix_stereo.wav` |')
    w('| M&E stems (music / sfx / boops / ambience) | **Done** | `output/audio/stem_*.wav` |')
    w('| Signature boop library (4 variants) | **Done** | `output/audio/boop_*.wav` |')
    w('| Storyboard (29 panels) + first/last layout frame per shot | **Done** | `output/storyboard_contact_sheet.png`, `output/shot_refs/` |')
    w('| Per-shot generation prompts, character lock, QC gates, conform plan | **Done** | this document |')
    w('| End-card typography as an edit layer | **Done** | rendered in the animatic; frame in `output/shot_refs/9B_endcard.png` |')
    w('| **Feature-quality CGI shots (photoreal fur, 3D lighting)** | **Not produced**: no video/3D generation model is available in this environment | Produce with section 8 prompts, gate with section 9, conform with section 10 |')
    w('')
    w('The animatic is the **timing and staging master**. Every action, cut and camera move in it is final. The CGI pass replaces its pixels shot by shot; the audio is already locked to its frames.\n')

    w('## 1. The episode on one page\n')
    w('**Logline.** On a quiet evening Bo hears a mysterious *boop* and, with the utmost seriousness, investigates the world\'s smallest mystery. '
      'Pip makes it chaotic, Mimi makes it cheerful, Blu makes it make sense. The culprit is Bo\'s own headphones. Then a boop comes from somewhere else.\n')
    w('**The comedic engine: the Boop Rule.** Every boop before the reveal is caused by Bo tilting his head past ~8.6°, which presses an earcup into his fur. '
      'Each of those boops makes his earcup ring flicker (subtly in wide shots). All of Bo\'s other tilts stay under 5°. The rule makes the reveal fair, '
      'makes Bo endearing rather than foolish (the harder he investigates, the more he causes it), and rewards a second viewing. '
      'The final boop (1:55.8) breaks the rule on purpose: it is pitched a fourth lower, comes from the hallway, and Bo\'s ring does **not** flicker.\n')
    w('**Rewatch plants.** (1) Boop 2 happens *because* Bo leans toward the sound. (2) Boop 3 happens as he tilts to look up. '
      '(3) In 6B Blu is the only one watching Bo instead of the room. (4) In 9A Bo keeps his head deliberately upright. '
      '(5) The hallway has a faint warm-lit room at its far end, which is where the next boop lives.\n')

    w('## 2. Character lock sheet\n')
    w('Source of truth: `refs/boopmo_official_reference.png` (crops: `refs/ref_*.png`). Palette sampled from the official art, then lifted for a warm interior key.\n')
    w('| | Bo | Mimi | Pip | Blu |')
    w('|---|---|---|---|---|')
    w('| Fur (lit / animatic base) | charcoal `#0c0c0e`-`#1e1e22` / `#1f1f24` | cream `#f2dcd1` / `#ead3c4` | violet `#a323f2` / `#7a12cc` | cobalt `#0053ed` / `#0638c4` |')
    w('| Size (H × W, relative to Bo) | 1.00 × 1.10 | 0.89 × 0.97 | 0.91 × 0.97 | 0.81 × 0.87 |')
    w('| Eyes | small glossy black ovals, close-set, highlight upper-right | two black ∩ arcs (closed happy eyes); "widen" lifts the arcs, never opens them | glossy black ovals, larger, thin white rim reflection | glossy black ovals, highlight upper-right |')
    w('| Accessory | black over-ear headphones, cool blue-white illuminated ring per earcup (`#e4f1ff`), ring flickers only on Bo\'s boops | black ribbed knit beanie, folded cuff, square black patch with white smiley | none, ever | clear translucent frames, dark smoky lenses, resting on top of head |')
    w('| Movement personality | deliberate, curious, still between moves; squash 1.0; lean max 5° except boop tilts | warm, buoyant, soft landings; squash 0.9; happy wiggles | quick, springy, overshoots; squash 1.3; biggest hops | precise; identical evenly-timed hops on the beat; squash 0.7; eye moves in discrete steps |')
    w('')
    w('**Never:** mouths, noses, brows, limbs, humanoid bodies; accessory swaps; new characters; pink characters; bows; colour drift; fur style changes.\n')

    w('## 3. Set bible: Bo\'s miniature bedroom\n')
    w('Frontal 2.5D stage, single horizon (y = -500); depth z: 0 = stage line, 1 = back wall. Positions in world units (Bo is 300 tall).\n')
    w('| Element | Position | Story function |')
    w('|---|---|---|')
    for row in [('Dusk window + rust curtains', 'x -1385..-885, wall', 'Establishes evening; cool fill light'),
                ('Patchwork bed + bedside lamp', 'x -1680..-745', 'Warm practical #1'),
                ('Sage pouf (Bo\'s seat)', 'x -550, z 0.10', 'Scene 1-2 home base'),
                ('Upright picture book', 'x -250, z 0.30', 'False lead 1 (3A)'),
                ('Book stack (3)', 'x 60, z 0.45', 'Pip\'s false lead, the top book slides (5C)'),
                ('Mustard floor cushion', 'x 400 -> 335 (askew after 46.55 s)', 'False lead 2 (3B); Pip\'s bonk; Mimi\'s "pff"'),
                ('Wall clock (second hand ticks with the SFX)', 'x 130, wall', 'Makes the silences audible'),
                ('Desk + green desk lamp', 'x 790..1330, z 0.55', 'Warm practical #2; boop 3 / freeze'),
                ('Arched doorway -> hallway', 'x 1395..1615', 'All entrances; source of the final boop')]:
        w(f'| {row[0]} | {row[1]} | {row[2]} |')
    w('\nLighting: warm tungsten key (lamps), dusk-blue fill (window), ceiling falloff, soft vignette, light grain. Palette keeps the characters\' official colours dominant: '
      'no saturated set colour sits behind a character of similar hue.\n')

    w('## 4. Shot list (picture-locked)\n')
    w('| Shot | In | Out | Dur | Size | Camera | Action |')
    w('|---|---|---|---|---|---|---|')
    for s in TL.SHOTS:
        w(f'| **{s.sid}** | {tc(s.t0)} | {tc(s.t1)} | {s.t1 - s.t0:.2f}s | {s.size} | {s.move} | {s.action} |')
    w('\nScenes: ' + ' · '.join(f'{k}. {v[0]} ({tc(v[1])})' for k, v in TL.SCENES.items()) + '\n')

    w('## 5. Boop cue sheet (sync-critical: frame-accurate in picture and sound)\n')
    w('| # | Time | Frame | Trigger | Variant | Ring flicker | Read |')
    w('|---|---|---|---|---|---|---|')
    for i, (t, v) in enumerate(TL.BOOPS, 1):
        trig, read = BOOP_NOTES.get(t, ('', ''))
        w(f'| {i} | {tc(t)} | {int(round(t * TL.FPS))} | {trig} | {v} | {"yes" if v in ("head", "room") else "**no**"} | {read} |')
    w('')

    w('## 6. Music cue sheet (original, written for this episode)\n')
    w('| Cue | In | Out | Key / tempo | Instrumentation | Function |')
    w('|---|---|---|---|---|---|')
    for c in MUSIC:
        w(f'| {c[0]} | {tc(c[1])} | {tc(c[2])} | {c[3]} | {c[4]} | {c[5]} |')
    w('\n**Bo theme** (F major): A4 C5 F5 E5 | D5 C5 A4 | Bb4 D5 G5 F5 | E5 G5 ... resolving to F. It is stated gently in 1M1, as a fanfare in 1M7 and in full in 1M8; the end card quotes its first three notes. '
      'The boop sits on D5, so the score can answer it (1M7: celesta D6).\n')

    w('## 7. Sound design\n')
    w('**Signature boop** (series asset, `output/audio/boop_signature.wav`): a soft "b" onset (4 ms low-passed burst + 150 Hz thump), a rounded pitched "oo" body on D5 '
      '(sine + 2nd/3rd/4th harmonics at -13/-25/-32 dB) with a tiny contour (starts 15% flat, rises ~3.5% sharp at 30 ms, settles, droops 3.5% at the end), a 32 Hz plush wobble, '
      'and a gentle "p" closure (3 ms pop) at 165 ms. Variants: *headphones* (adds a 70 ms fabric-compression pre-layer), *room* (extra reflections, -1.7 dB), '
      '*outside* (A4, darker, longer, hallway reverb, -4 dB: clearly "someone else"), *end card* (A5, 110 ms).\n')
    counts = {}
    for k, *_ in TL.EVENTS:
        counts[k] = counts.get(k, 0) + 1
    w('**Foley/SFX events generated from the animation** (' + ', '.join(f'{k}: {v}' for k, v in sorted(counts.items())) + '). '
      'Plush landings scale with hop height and character size, and each character has its own thump pitch. Scoots are amplitude-modulated at the 4.2 Hz squish cycle; pans follow on-screen position per shot. '
      'Ambience is a low room tone and the wall clock ticking once per second, in sync with its painted second hand. Both drop to absolute silence on the final head-turn (1:56.0).\n')
    w('**Mix:** -16.0 LUFS integrated, -1.0 dBTP (4x-oversampled); limiter acts only on the four orchestral hits (max 5.8 dB, 0.16% of runtime). '
      'Head-boops sit at -14.6 dB RMS, 6-40 dB above their bed. For broadcast (-23/-24 LUFS), re-mix from stems instead of turning the master down.\n')

    w('## 8. Shot-by-shot generation prompts\n')
    w('**Recommended pipeline (per shot):** (a) generate 1-3 CGI *keyframes* with an image model, using the official reference crops as character references and the '
      '`output/shot_refs/<shot>_first.png` / `_last.png` frames as **layout/composition guides only** (not style); (b) QC the keyframes (section 9); '
      '(c) image-to-video from first/last keyframes with the prompt below at the exact duration; (d) QC again; (e) conform (section 10). '
      'Never use the animatic frames as direct start frames: their 2D look will bleed into the output.\n')
    w(f'**Global style lock (prepend to every prompt):** {STYLE_LOCK}\n')
    w(f'**Character lock (prepend; attach reference images):** {CHAR_LOCK}\n')
    w(f'**Negative prompt (every shot):** {NEGATIVE}\n')
    for s in TL.SHOTS:
        if s.sid == '9B':
            w('### 9B: End card (not generated)\nBlack. "ADVENTURES OF BO" (Inter Display ExtraBold, +7% tracking, #F6F5F2) fades and rises in at 1:57.9; '
              '"A BOOPMO ORIGINAL" (Inter Display Medium, +42% tracking, #B8BDC7) at 1:58.4; Bo\'s headphone ring as the series mark above, which pulses with the final tiny boop at 1:59.0. '
              'Build as editorial text layers, never generated.\n')
            continue
        chars = [n for n, c in TL.CHARS.items() if c.state((s.t0 + s.t1) / 2)['visible']]
        w(f'### {s.sid}: {tc(s.t0)}-{tc(s.t1)} ({s.t1 - s.t0:.2f}s) · {s.size} · {s.move}')
        w(f'{PROMPTS[s.sid]}')
        sync = [f'{tc(t)} ({v})' for t, v in TL.BOOPS if s.t0 <= t < s.t1]
        w(f'*References:* layout `shot_refs/{s.sid}_first.png` -> `_last.png`; characters in shot: {", ".join(chars)}.'
          + (f' *Sync points:* boop at {", ".join(sync)}; ring flicker must land on that frame.' if sync else '') + '\n')

    w('## 9. QC gates (apply to every keyframe and every generated clip)\n')
    w('A shot is rejected, not patched into the edit, if it fails any of these:\n')
    for i, q in enumerate([
        'Bo\'s headphones present, correct (black, over-ear, both cups), ring cool blue-white and subtle; ring flicker only on boop frames.',
        'Mimi\'s black ribbed beanie and square smiley patch intact and legible (no garbled glyphs); eyes remain arcs.',
        'Pip is violet-purple (not pink or magenta) and has no accessories.',
        'Blu\'s clear sunglasses sit on top of the head, one pair, undistorted.',
        'Eyes match the lock sheet: shape, size and spacing, no added whites (except Pip\'s thin rim), no duplicated eyes.',
        'Fur texture and proportions match the references; relative sizes Bo > Pip ≈ Mimi > Blu.',
        'No mouths, noses, brows, arms, hands, legs or humanoid features in any frame.',
        'Lighting, set geometry and prop state match neighbouring shots (cushion askew after 0:46.55; top book offset after 1:03.75).',
        'Motion has weight: anticipation, squash/stretch, settle; no floating or jitter; Bo\'s non-boop tilts stay under ~5°.',
        'The shot advances the story exactly as the animatic does; timing within ±2 frames at every sync point.']):
        w(f'{i + 1}. {q}')
    w('\nKnown failure modes to screen for: accessory migration between characters in group shots; beanie patch turning into text; extra creature appearing in doorway shots; '
      'fur colour drifting under warm light (re-grade, don\'t accept); headphone band merging into fur; glasses duplicating during Blu\'s bounce.\n')

    w('## 10. Conform & delivery\n')
    w('1. Import `Adventures_of_Bo_E01_..._ANIMATIC_master.mp4` (24 fps) as the offline reference and `output/audio/mix_stereo.wav` + stems on locked tracks.')
    w('2. Replace shots one at a time on V2 over the animatic. Each generated clip must match the shot\'s duration; retime only between sync points and keep every boop frame (section 5) exact.')
    w('3. Grade to the animatic\'s look: warm evening, protected character colours, light vignette, fine grain; 2.39:1 matte (138 px bars at 1080p).')
    w('4. End card from editorial text layers (section 8, 9B).')
    w('5. Deliver: ProRes 4444 master, H.264 web (CRF 16-18), stereo 48 kHz -16 LUFS / -1 dBTP; M&E stems for localisation.\n')

    w('## 11. Series notes: the Boopmo universe\n')
    w('- **Recurring devices:** the signature boop (always D5 for Bo\'s headphones); the ring flicker as a visual "tell"; Blu\'s one tiny unexpectedly enthusiastic bounce; '
      'Pip\'s collisions with soft objects; Mimi\'s "pff" cushion.')
    w('- **Episode 2 hook, already planted:** the hallway boop is a different pitch (A4) and comes from the warm-lit room at the end of the hallway. Whatever makes it is new to the crew, and the audience has heard it first.')
    w('- **Spin-offs:** *Adventures of Mimi* (cheer as a superpower), *of Pip* (chaos with good intentions), *of Blu* (the precise one who secretly loves to bounce).')
    w('- Every episode should stay understandable with the sound off and funny with the sound on.\n')

    w('## 12. Reproducing this package\n')
    w('```bash\npip install scipy skia-python pyloudnorm pillow numpy    # + ffmpeg, libegl1\npython src/timeline.py            # continuity validation (Boop Rule, shot coverage)\n'
      'python src/audio.py               # score + SFX + master + stems\npython src/render.py video         # 120 s picture (4 workers)\npython src/render.py contact       # storyboard sheet\n'
      'python src/build_docs.py          # this document + shot reference frames\n```\n')
    p = os.path.join(ROOT, 'docs', 'PRODUCTION_BIBLE.md')
    with open(p, 'w') as fh:
        fh.write('\n'.join(L))
    return p


if __name__ == '__main__':
    print(build())
    if '--refs' in sys.argv:
        export_refs()

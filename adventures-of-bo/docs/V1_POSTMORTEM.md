# Adventures of Bo, Ep.1 v1: Postmortem

**Verdict:** v1 is a timed animatic with a competent audio pass. It is not an animated film, and it is not a good animatic of a good story. The client review is correct on all eight points. These are the measured causes.

## 1. What the numbers say

| Measure (from `src/timeline.py`) | v1 value | What it means on screen |
|---|---|---|
| Bo on screen and effectively motionless (breathing only) | **62%** of 111.5 s | A main character who mostly waits |
| Blu motionless | **76%** | "Clever and observant" was expressed as standing still |
| Character time spent travelling or hopping | Bo 8%, Pip 23% | Hops were the only action verb, 57 of them |
| Distinct camera axes | **1** (all 28 picture shots frontal, same horizon) | "The same room" 28 times, only cropped differently |
| Boops caused by the same action | **9 of 11** (a head tilt) | The core beat repeats without escalating |
| Objects the cast physically affects in 2 minutes | **3** (cushion, one book, pouf) | No physical comedy to speak of |
| Fur response to motion | **none** (pre-rendered static sprite) | Plush creatures that move like stickers |
| 3D turns | **none** (yaw faked by sliding the eyes) | No body language, no turning away, no reveal of the back |
| Motion blur, camera rotation, parallax | **none** | Nothing reads as cinema |

## 2. Root causes, most important first

1. **Wrong pipeline, chosen without checking alternatives.** I built a 2D procedural sprite renderer (skia) because nothing with a GPU or video model was available. I never checked whether a CPU 3D renderer was installable. It was: Blender 5.2 (`bpy`, Cycles) installs from PyPI. That one unchecked assumption capped every other dimension (camera, fur, turns, light, materials).
2. **The story was transcribed, not written.** I executed the brief's nine-scene outline literally and added a "Boop Rule" that made Bo cause every boop by tilting. That was clever on paper but visually monotonous: the same small action nine times, with nothing escalating. The mystery never got bigger, stranger or funnier, and no scene changed the situation.
3. **Personality was assigned, not acted.** Pip hopped faster, Blu hopped evenly, Mimi wiggled. None of them *did* anything that only they would do. Without limbs or mouths, personality has to come from **choices** (what they try, how they fail), and I wrote no choices.
4. **The rig had too few expressive controls.** It had position, tilt, squash, eye offset, blink and lid. It had no real turns, no fur bristle (fluffing), no asymmetric eyes, no overlap or follow-through, no weight shifts, no contact with props. Acting quality cannot exceed the rig.
5. **Physical comedy needs physical props.** The set was a painted plate with four movable sprites. Nothing could be knocked over, rolled, pushed, opened or reflected.
6. **Lighting was painted, not simulated.** Characters didn't receive light from the lamps, cast real shadows or pick up reflections, so they never sat in the room.
7. **Music was synthesized from sine waves, and I never heard it.** The cue structure was sound but the instruments were thin. I mixed by meter only.
8. **I reported technical success as quality.** Sync checks, loudness numbers and "29 shots" are hygiene, not craft. That framing hid points 1–7.

## 3. Changes in v2

| v1 | v2 |
|---|---|
| 2D sprites, one camera axis | Real 3D set and characters in **Blender/Cycles**; real cameras (lens, height, angle, DOF, motion blur) |
| Static fur texture | Per-frame simulated fur strands that lag, flow and **bristle** on startle |
| Fake yaw | True 3D turns, including turning away from camera |
| 6-control rig | Rig with squash/stretch (volume-preserving), spring overlap, lean, heading, asymmetric eyes, fur fluff |
| Story that repeats one beat | New story built on an escalating, relatable mystery engine with personality-driven set-pieces (see `V2_TREATMENT.md`) |
| Additive-synth score | Sampled orchestral instruments (FluidSynth + GM soundfont) with a written score; layered foley |
| "It rendered" = done | Every shot critiqued against the treatment's intent before acceptance |

The remaining hard limit is compute: 4 CPU cores, no GPU. Section 6 of the treatment covers how that constrains render resolution and sample counts, and what a production studio would do differently.

# Adventures of Bo, Ep.1 v2: Production plan for the full episode

## 1. What the proof sequence establishes
- **Rendering and look:** real 3D characters with simulated fur strands, path-traced light, shadows and reflections, depth of field and motion blur in a dressed, lit set. Achieved on this machine.
- **Asset consistency:** all four characters exist as locked 3D assets driven by one rig and one deformation field, so they look identical in every shot (`output/v2/cast_lock_sheet.png`).
- **Pipeline:** treatment → keyed performance → physics pass → camera solving → previs → final render → scored and foley'd mix. It's reproducible from code (`v2/README.md`).
- **Acting and comedy (for one character):** anticipation, lean, deflate, whip-turn, startle, fur bristle and a deadpan look to camera, cut to a 9-setup sequence with sound timed to the frame.

**Not yet proven:** multi-character interaction (Pip, Mimi and Blu exist as assets but haven't been animated), and story clarity across the whole two minutes.

## 2. Recommended method for the remaining ~100 seconds

**Recommended: a hybrid.** Keep these assets, this treatment and this render and sound pipeline, and put a character animator on the hero acting.

| Workstream | Who / what | Why |
|---|---|---|
| Story and boards | Treatment `V2_TREATMENT.md`, 8 beats; storyboard each beat as 3D previs with these assets (≈2.6 s/frame) | Locks timing and staging before any expensive render |
| Hero character animation | **A character animator** keying in Blender, using a rig ported to Geometry Nodes so the same deformation field (squash/stretch, bend, fur inertia, bristle) runs interactively | Code-keyed animation is principled but stiffer than an animator's hand-polished arcs and spacing; multi-character interaction (Pip booping objects, Mimi cuddling Bo, the cable gag) needs that hand |
| Secondary motion and fur | Keep the physics pass (springs integrated at 480 Hz) | Consistent and cheap; an animator shouldn't key fur |
| Rendering | Cycles on GPU (OptiX); same scene files | Hair renders roughly 10–20× faster than on these 4 CPU cores |
| Music | Composer orchestrates from the MIDI sketches (`v2/out/stakeout_score.mid`) with a real or high-end sampled orchestra | The FluidSynth GM soundfont is credible for a proof, not for a series |
| Sound design | Recorded plush, fabric and wood foley; keep the signature boop | Synthesized foley is the weakest layer of the mix |
| Review | Human screening at each gate (previs, animation, lighting, final mix) | I can measure but can't watch or listen |

**Not recommended for hero shots:** text-to-video or image-to-video generation. Character-consistency risk is high (accessories migrate, limbs or mouths appear), and comedic timing can't be controlled to the frame. It's acceptable only for background plates, if at all.

## 3. Compute estimates (measured)
| Configuration | Per frame (Bo only) | Full episode, 2,880 frames, ≈2.5× for four furry characters |
|---|---|---|
| This machine, 4 CPU cores, 1280×536, 16 spp | 22 s | ≈44 hours |
| Single modern GPU (estimate, OptiX) | 1.5–3 s at 1920×804 | ≈3–6 hours |
| Render farm, 20 GPUs | — | well under 1 hour per full pass |

## 4. Remaining production list (by beat)
1. **Night Music** (cold open): headphones' music warble-out; rain; Bo's sway. New: none.
2. **The Stakeout**: done (proof).
3. **Pip's Method**: book-tower domino rig, lamp ding, cushion, clock *RRRING* (bell-hammer animation exists), Pip's bounce physics. New props: book tower.
4. **Mimi's Method**: tiny bed prop, call-and-response timing, the cuddle (two-body contact deformation).
5. **Blu's Method**: overhead camera for the triangulation, Bo's tail-chasing spin (the rig already supports spin flare and lag).
6. **The Mirror**: reflection close-up in Blu's dark lenses (Cycles handles it natively), the ring blink in the reflection.
7. **The Fix**: charging cable (curve with physics), tangle gag, cable-yank on Bo's bounce.
8. **The Button**: circle of glances, hallway boop, end card.

## 5. Risks
| Risk | Mitigation |
|---|---|
| Multi-character fur render cost | GPU rendering; render fur per character in separate passes, then composite |
| Contact between characters (cuddle, nudges) | Add a simple collision/contact deformation to the field (a pressure dent) |
| Acting quality from code-keyed animation | Animator on hero shots (section 2) |
| Colour drift of characters under coloured light | Per-shot lighting cheats, plus a grading check against the cast lock sheet |

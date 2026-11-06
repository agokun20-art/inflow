# Adventures of Bo: v2 production pipeline

A real 3D pipeline: Blender 5.2 as a Python module (`bpy`), Cycles path tracing, simulated fur strands, and a sampled-orchestra score. Built to replace the v1 2D sprite animatic (see `../docs/V1_POSTMORTEM.md`).

## Setup
```bash
pip install bpy==5.2.3 scipy numpy pillow skia-python mido pyloudnorm   # bpy wheel needs Python 3.13
apt-get install -y libegl1 fluidsynth fluid-soundfont-gm ffmpeg
python textures.py                        # art-directed textures -> tex/
```

## Modules
| File | Role |
|---|---|
| `rig.py` | Character rig (pure numpy). Superellipsoid body; area-weighted, clumped fur strands with a "bristle" alternate shape; glossy eyes with gaze, blink and asymmetric squint; Bo's headphones. **One deformation field** (volume-preserving squash/stretch, bend, weight-shift, heading, translation) moves body, fur, eyes and accessories together. |
| `cast.py` | Mimi (ribbed knit beanie, smiley patch, arc eyes), Pip, Blu (clear-frame sunglasses) built on the same rig. |
| `scene.py` | Blender set: attic room, round moonlit window with falling rain, plank floor, kilim rug, wainscot, curtains, bookshelf, records, brass lamp, door to a dark hallway, ceiling beams, hero alarm clock. Lights, materials, render settings. |
| `anim_stakeout.py` | Proof-sequence animation: keyed performance (anticipation, overshoot, settle), step and hop layers, then a physics pass (springs integrated at 480 Hz) for body overlap, fur inertia, spin flare and trailing lag. Shot list and boop cues. |
| `tune_cams.py` | Virtual camera operator: solves each shot's camera from compositional targets (thirds, frame fill, foreground placement) and hard constraints (not inside Bo, the clock or the floor; pitch limits). Writes `out/cams.json`. |
| `framing.py` | Independent numeric framing check (screen position and frame fill per shot). |
| `render_stakeout.py` | Per-frame render: rig at t and t±½ frame gives **velocity motion blur**; camera keyed only inside the current shot (no blur across cuts); eye-targeted focus pulls; per-shot lighting cheats; resumable. `previs` = fast timing pass, `final` = 1280×536. |
| `sound_stakeout.py` | Score written as MIDI and rendered through FluidSynth (pizzicato, bassoon, tremolo strings, harp, timpani, whistle, glockenspiel), layered foley, rain and room tone, a distance-attenuated clock, the signature boop. Mastered to -16 LUFS / -1 dBTP. |
| `comp_stakeout.py` | Upscale to 1920×804, letterbox 2.39:1 in 1080p, temporal grain, black tail, mux. |
| `review_sheet.py` | Per-shot contact strips for review. |
| `lock_cast.py` | Cast lock-sheet renders. |

## Run the proof sequence
```bash
python tune_cams.py                                   # solve cameras (seconds)
python render_stakeout.py previs 0 456 2              # timing pass, ~2.6 s/frame
SPP=16 DIFF=1 python render_stakeout.py final 0 456   # ~22 s/frame on 4 CPU cores
python sound_stakeout.py                              # score + SFX + master
python comp_stakeout.py                               # -> ../output/v2/*.mp4
```

## Measured costs (4-core Xeon, no GPU)
| Pass | Resolution | Samples | Time per frame |
|---|---|---|---|
| Previs (fur ÷3, no motion blur) | 640×268 | 6 | 2.6 s |
| Final (95k strands, motion blur, DOF) | 1280×536 | 16, 1 diffuse bounce | 22 s |
| Final, higher quality | 1280×536 | 24, 2 diffuse bounces | 35 s |

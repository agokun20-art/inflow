"""Render 'The Stakeout'.

  python render_stakeout.py previs [f0 f1 step]   fast timing pass (640x268, decimated fur)
  python render_stakeout.py final  [f0 f1 step]   1280x536, full fur, motion blur, DOF
Resumable: existing frames are skipped.
"""
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scene as S  # noqa: E402
import anim_stakeout as A  # noqa: E402
from rig import Character, BO  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else 'previs'
f0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
f1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(A.DUR * A.FPS)
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
OUT = os.path.join(HERE, 'out', os.environ.get('OUTDIR', mode))
os.makedirs(OUT, exist_ok=True)
PREV = mode == 'previs'

bpy.ops.wm.read_factory_settings(use_empty=True)
handles = S.build_set()
S.build_lights()
clock, hands = S.build_clock()
ch = Character(BO)
co = S.CharObjects(ch, decimate=3 if PREV else 1)
cam_d = bpy.data.cameras.new('cam')
cam_d.sensor_width = 36
cam = bpy.data.objects.new('cam', cam_d)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
if PREV:
    S.setup_render(res=(640, 268), spp=6, mb=False, preview=True)
else:
    S.setup_render(res=(1280, 536), spp=int(os.environ.get('SPP', 28)), mb=True)
sc = bpy.context.scene
sc.render.motion_blur_shutter = 0.5
rain_map = handles['rain_map']

H = 0.5 / A.FPS
# per-shot lighting cheats (as a DP re-balances each setup); multipliers on base energy
LIGHT_CHEATS = {'2': {'moon': 0.55, 'fill': 1.8, 'room_bounce': 1.4}, '5': {'room_bounce': 3.2, 'fill': 2.0}, '6': {'room_bounce': 1.8}, '7a': {'moon': 0.45, 'room_bounce': 1.6},
                '7b': {'moon': 0.25}, '9': {'moon': 0.5, 'room_bounce': 1.6, 'fill': 1.8}, '3': {'moon': 0.8}}
BASE_E = {o.name: o.data.energy for o in bpy.data.objects if o.type == 'LIGHT'}


def look(loc, tgt, roll_deg=0.0):
    q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y')
    e = q.to_euler()
    if roll_deg:
        m = q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(roll_deg), 4, 'Z')
        e = m.to_euler()
    return e


def eyes_center(geo, which):
    if which == 'eyeL':
        return geo['eyeL'].mean(0)
    return (geo['eyeL'].mean(0) + geo['eyeR'].mean(0)) / 2


def cam_at(shot, t, geo):
    sp = getattr(shot, 'spec', None)
    if sp:
        u = min(1, max(0, (t - shot.t0) / (shot.t1 - shot.t0)))
        u = u * u * (3 - 2 * u)
        loc = np.asarray(sp['loc0']) * (1 - u) + np.asarray(sp['loc1']) * u + A.handheld(t, A.HANDHELD.get(shot.sid, 0.0))
        off = np.asarray(sp['aim_off'])
        base = {'bo': np.array([geo['body'][:, 0].mean(), geo['body'][:, 1].mean(), geo['body'][:, 2].mean()]),
                'eyes': eyes_center(geo, 'eyes'), 'eyeL': eyes_center(geo, 'eyeL'), 'dial': A.DIAL, 'fixed': np.zeros(3)}[sp['aim']]
        tgt = base + off
        if shot.sid == '6' and t > 11.84:   # operator overshoots the whip, then settles
            w = math.exp(-(t - 11.9) / 0.12) * math.sin((t - 11.84) * 40) * 0.035 if t > 11.9 else math.sin((t - 11.84) * 40) * 0.035
            tgt = tgt + np.array([0, w, 0])
        return loc, tgt
    loc, tgt = shot.fn(t)
    if tgt is None:
        tgt = eyes_center(geo, 'eyeL' if shot.sid == '3' else 'eyes')
    return np.asarray(loc), np.asarray(tgt)


def focus_point(shot, t, geo, loc):
    f = shot.focus
    if f == 'bo':
        c = np.array([geo['body'][:, 0].mean(), geo['body'][:, 1].mean(), geo['body'][:, 2].mean()])
        # focus on the near surface of Bo, not his centre
        d = c - loc
        return c - d / np.linalg.norm(d) * 0.12
    if f == 'mid':
        return (eyes_center(geo, 'eyes') + A.DIAL) / 2
    if f in ('eyeL', 'eyes'):
        return eyes_center(geo, f)
    if f == 'dial':
        return A.DIAL


t_start = time.time()
done = 0
FR = [int(x) for x in os.environ['FRAMES'].split(',')] if os.environ.get('FRAMES') else range(f0, f1, step)
for f in FR:
    path = os.path.join(OUT, f'f_{f:04d}.png')
    if os.path.exists(path):
        continue
    t = f / A.FPS
    shot = A.shot_at(t)
    st, sa, sb = A.state(t), A.state(t - H), A.state(t + H)
    geo, ga, gb = ch.evaluate(st), ch.evaluate(sa), ch.evaluate(sb)
    # camera: keys at f-0.5, f, f+0.5 from THIS shot only (no blur across cuts)
    cam.animation_data_clear()
    cam_d.animation_data_clear()
    for df, g in ((-0.5, ga), (0.0, geo), (0.5, gb)):
        tt = t + df / A.FPS
        loc, tgt = cam_at(shot, tt, g)
        cam.location = Vector(loc)
        cam.rotation_euler = look(loc, tgt, shot.roll)
        cam.keyframe_insert('location', frame=f + df)
        cam.keyframe_insert('rotation_euler', frame=f + df)
    sc.frame_set(f)
    loc, tgt = cam_at(shot, t, geo)
    cam_d.lens = shot.lens
    cam_d.dof.use_dof = True
    cam_d.dof.aperture_fstop = shot.fstop
    fp = focus_point(shot, t, geo, loc)
    cam_d.dof.focus_distance = float(np.linalg.norm(fp - loc))
    for nm, e0 in BASE_E.items():
        bpy.data.objects[nm].data.energy = e0 * LIGHT_CHEATS.get(shot.sid, {}).get(nm, 1.0)
    co.apply(geo, ga, gb, H, ring=st['ring'], cam=cam)
    hands['second'].rotation_euler = (0, A.clock_second_angle(t), 0)
    rain_map.inputs['Location'].default_value = (0, -t * 0.9, 0)
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    done += 1
    el = time.time() - t_start
    print(f'[{mode}] f{f:04d} shot {shot.sid} {time.time() - t0:5.1f}s  avg {el / done:5.1f}s/frame', flush=True)
print('finished', mode, f0, f1, step, round(time.time() - t_start), 's')

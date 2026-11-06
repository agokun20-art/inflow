"""Virtual camera operator: solve each shot's camera from compositional targets.

Targets are screen-space (x right, y up, both in [-1, 1]) plus subject size as a
fraction of frame height; constraints keep the lens out of Bo, the clock and the
floor. Writes out/cams.json, which anim_stakeout loads.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_stakeout as A  # noqa: E402
from rig import Character, BO  # noqa: E402

ch = Character(BO)
ASP = 1280 / 536
CLOCK_C = np.array([0.0, 0.42, 0.085])
rng = np.random.default_rng(0)

GEO = {}


def geo_at(t):
    k = round(t, 3)
    if k not in GEO:
        g = ch.evaluate(A.state(t))
        B = g['body']
        GEO[k] = dict(c=B.mean(0), top=B[np.argmax(B[:, 2])], bot=B[np.argmin(B[:, 2])],
                      eyes=(g['eyeL'].mean(0) + g['eyeR'].mean(0)) / 2, eyeL=g['eyeL'].mean(0),
                      eyeL_t=g['eyeL'][np.argmax(g['eyeL'][:, 2])], eyeL_b=g['eyeL'][np.argmin(g['eyeL'][:, 2])],
                      eyeR=g['eyeR'].mean(0))
    return GEO[k]


def proj(loc, tgt, lens, p, roll=0.0):
    f = tgt - loc
    f = f / np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    if roll:
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        r, u = r * c + u * s, -r * s + u * c
    d = p - loc
    z = d @ f
    th = 18 / lens
    return np.array([(d @ r) / z / th, (d @ u) / z / (th / ASP)]), z


def target_point(spec, t):
    g = geo_at(t)
    mode, off = spec['aim'], np.asarray(spec['aim_off'])
    base = {'bo': g['c'], 'eyes': g['eyes'], 'eyeL': g['eyeL'], 'dial': A.DIAL, 'fixed': np.zeros(3)}[mode]
    return base + off


def cam_loc(spec, t, s):
    u = min(1, max(0, (t - s.t0) / (s.t1 - s.t0)))
    u = u * u * (3 - 2 * u)
    return np.asarray(spec['loc0']) * (1 - u) + np.asarray(spec['loc1']) * u


def penalty_loc(loc, t):
    g = geo_at(t)
    p = 0.0
    p += 50 * max(0, 0.235 - np.linalg.norm(loc - g['c'])) ** 2 * 100
    p += 50 * max(0, 0.11 - np.linalg.norm(loc - CLOCK_C)) ** 2 * 100
    p += 50 * max(0, 0.035 - loc[2]) ** 2 * 100
    if not (-1.25 < loc[0] < 1.25 and -1.2 < loc[1] < 1.15 and loc[2] < 1.0):
        p += 10
    return p


def evaluate(spec, s, objectives):
    err = 0.0
    for (t, obj) in objectives:
        loc = cam_loc(spec, t, s)
        tgt = target_point(spec, t)
        if np.linalg.norm(tgt - loc) < 0.02:
            return 1e9
        err += penalty_loc(loc, t)
        dv = tgt - loc
        pitch = math.degrees(math.atan2(dv[2], math.hypot(dv[0], dv[1])))
        lo, hi = PLAN_PITCH.get(s.sid, (-22, 22))
        err += 0.02 * (max(0, lo - pitch) + max(0, pitch - hi)) ** 2
        if tgt[2] < 0.0:
            err += 10
        if s.sid in FACE_SHOTS:     # lens must see Bo's face: within 60 deg of his facing direction
            stf = A.state(t)
            face = np.array([math.sin(stf['heading']), -math.cos(stf['heading'])])
            v = loc[:2] - geo_at(t)['c'][:2]
            ang = math.degrees(math.acos(np.clip(v @ face / (np.linalg.norm(v) + 1e-9), -1, 1)))
            err += 0.004 * max(0, ang - 55) ** 2
        g = geo_at(t)
        for key, want in obj.items():
            if key == 'bo_h':
                a, za = proj(loc, tgt, s.lens, g['top'], s.roll)
                b, zb = proj(loc, tgt, s.lens, g['bot'], s.roll)
                if za <= 0 or zb <= 0:
                    return 1e9
                err += 4 * (abs(a[1] - b[1]) / 2 - want) ** 2
            elif key == 'eye_h':
                a, _ = proj(loc, tgt, s.lens, g['eyeL_t'], s.roll)
                b, _ = proj(loc, tgt, s.lens, g['eyeL_b'], s.roll)
                err += 4 * (abs(a[1] - b[1]) / 2 - want) ** 2
            elif key == 'dial_h':
                a, _ = proj(loc, tgt, s.lens, A.DIAL + np.array([0, 0, 0.049]), s.roll)
                b, _ = proj(loc, tgt, s.lens, A.DIAL - np.array([0, 0, 0.049]), s.roll)
                err += 4 * (abs(a[1] - b[1]) / 2 - want) ** 2
            else:
                pt = {'bo': g['c'], 'eyes': g['eyes'], 'eyeL': g['eyeL'], 'clock': CLOCK_C, 'top': g['top']}[key]
                xy, z = proj(loc, tgt, s.lens, pt, s.roll)
                if z <= 0:
                    err += 5
                    continue
                w = want[2] if len(want) > 2 else 1.0
                err += w * ((xy[0] - want[0]) ** 2 + (xy[1] - want[1]) ** 2)
    return err


# shot -> (camera spec template with search ranges, objectives)
# loc ranges are boxes; aim offsets small boxes.
PLAN = {
    '1': dict(aim='fixed', box=((-0.4, 0.6), (0.2, 1.1), (0.045, 0.09)), push=0.12, aim_box=((-0.6, 0.2), (-0.5, 0.3), (0.08, 0.16)),
              obj=[(0.2, {'bo': (-0.42, -0.08), 'clock': (0.82, -0.12, 0.6), 'bo_h': 0.30}),
                   (1.5, {'bo': (-0.3, -0.06), 'clock': (0.8, -0.12, 0.6)}),
                   (2.9, {'bo': (-0.18, -0.02), 'clock': (0.78, -0.12, 0.6), 'bo_h': 0.52})]),
    '2': dict(aim='fixed', box=((0.25, 1.1), (0.45, 1.1), (0.09, 0.2)), push=0.05, aim_box=((-0.15, 0.2), (0.05, 0.35), (0.1, 0.18)),
              obj=[(3.7, {'eyes': (0.15, 0.15), 'bo_h': 0.55}), (4.9, {'eyes': (0.12, 0.2), 'clock': (-0.45, -0.25, 0.6), 'bo_h': 0.62}),
                   (6.2, {'eyes': (0.08, 0.22), 'clock': (-0.45, -0.25, 0.6)})]),
    '3': dict(aim='eyeL', box=((0.03, 0.3), (0.25, 0.5), (0.13, 0.24)), push=0.004, aim_box=((-0.004, 0.004), (-0.004, 0.004), (-0.003, 0.003)),
              obj=[(6.3, {'eyeL': (0.08, 0.05), 'eye_h': 0.42}), (7.3, {'eyeL': (0.08, 0.05), 'eye_h': 0.42})]),
    '4': dict(aim='fixed', box=((-0.2, 0.9), (0.2, 1.1), (0.08, 0.2)), push=0.05, aim_box=((-0.3, 0.2), (-0.4, 0.2), (0.08, 0.18)),
              obj=[(8.3, {'bo': (-0.22, -0.05), 'clock': (0.72, -0.25, 0.5), 'bo_h': 0.62}),
                   (9.6, {'bo': (-0.18, -0.05)}), (10.7, {'bo': (-0.12, -0.08), 'bo_h': 0.5})]),
    '5': dict(aim='bo', box=((-0.4, 0.4), (-1.1, -0.4), (0.08, 0.22)), push=0.0, aim_box=((-0.03, 0.03), (-0.03, 0.03), (0.0, 0.06)),
              obj=[(10.8, {'eyes': (0.0, 0.22), 'bo_h': 0.8}), (11.6, {'eyes': (0.05, 0.22)})]),
    '6': dict(aim='bo', box=((0.3, 1.2), (-0.8, 0.4), (0.08, 0.2)), push=0.0, aim_box=((-0.03, 0.03), (-0.03, 0.03), (0.0, 0.05)),
              obj=[(11.76, {'bo': (-0.12, -0.02), 'bo_h': 0.62}), (12.6, {'bo': (-0.12, -0.02), 'bo_h': 0.62, 'clock': (0.62, -0.25, 0.3)})]),
    '7a': dict(aim='eyes', box=((-0.25, 0.25), (0.15, 0.45), (0.05, 0.13)), push=0.004, aim_box=((-0.01, 0.01), (-0.01, 0.01), (-0.03, -0.005)),
               obj=[(12.8, {'eyes': (-0.05, 0.28)}), (13.6, {'eyes': (-0.05, 0.3), 'bo_h': 2.2})]),
    '7b': dict(aim='dial', box=((-0.45, 0.1), (-0.6, -0.1), (0.22, 0.42)), push=0.01, aim_box=((-0.01, 0.01), (-0.01, 0.01), (-0.01, 0.01)),
               obj=[(13.8, {'clock': (0.25, 0.08), 'top': (-0.55, -0.7, 0.4), 'dial_h': 0.5}), (14.6, {'clock': (0.25, 0.08), 'dial_h': 0.5})]),
    '9': dict(aim='eyes', box=((-0.2, 0.3), (0.4, 1.0), (0.14, 0.32)), push=0.04, aim_box=((-0.01, 0.01), (-0.01, 0.01), (-0.06, -0.02)),
              obj=[(17.3, {'eyes': (0.0, 0.25), 'bo_h': 1.25}), (18.6, {'eyes': (0.0, 0.25)})]),
}


FACE_SHOTS = {'2'}
PLAN_PITCH = {'7b': (-40, -10), '7a': (5, 35), '1': (-8, 18)}


def solve(sid, n=4000):
    s = [x for x in A.SHOTS if x.sid == sid][0]
    P = PLAN[sid]
    best, bspec = 1e18, None
    for i in range(n):
        if bspec is None or i < n * 0.5:
            loc0 = np.array([rng.uniform(*P['box'][k]) for k in range(3)])
            aoff = np.array([rng.uniform(*P['aim_box'][k]) for k in range(3)])
        else:   # local refinement around the best
            loc0 = np.asarray(bspec['loc0']) + rng.normal(0, 0.02, 3)
            aoff = np.asarray(bspec['aim_off']) + rng.normal(0, 0.01, 3)
            loc0 = np.array([np.clip(loc0[k], *P['box'][k]) for k in range(3)])
            aoff = np.array([np.clip(aoff[k], *P['aim_box'][k]) for k in range(3)])
        aim_pt = aoff if P['aim'] == 'fixed' else None
        tgt0 = aoff if P['aim'] == 'fixed' else None
        # push-in: move toward the aim by 'push' metres over the shot
        ref = aoff if P['aim'] == 'fixed' else geo_at(s.t0 + 0.01)['eyes']
        dvec = ref - loc0
        loc1 = loc0 + dvec / (np.linalg.norm(dvec) + 1e-9) * P['push']
        spec = dict(aim=P['aim'], aim_off=aoff.tolist(), loc0=loc0.tolist(), loc1=loc1.tolist())
        e = evaluate(spec, s, P['obj'])
        if e < best:
            best, bspec = e, spec
    return best, bspec


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'cams.json')
    cams = json.load(open(path)) if os.path.exists(path) else {}
    for sid in (sys.argv[1:] or PLAN.keys()):
        e, spec = solve(sid)
        cams[sid] = spec
        print(f'SH{sid}: err {e:.4f}  loc0 {np.round(spec["loc0"], 3)}  aim {spec["aim"]} {np.round(spec["aim_off"], 3)}')
    json.dump(cams, open(path, 'w'), indent=1)

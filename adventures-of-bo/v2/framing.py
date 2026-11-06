"""Numeric framing check: screen-space position/size of Bo, eyes, clock per shot."""
import math, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_stakeout as A
from rig import Character, BO
ch = Character(BO)
ASP = 1280 / 536
def project(loc, tgt, lens, p, roll=0.0):
    f = np.asarray(tgt, float) - loc; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    if roll:
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll)); r, u = r * c + u * s, -r * s + u * c
    d = np.asarray(p, float) - loc; z = d @ f
    th = 18 / lens
    return np.array([(d @ r) / z / th, (d @ u) / z / (th / ASP)]), z
def report(shots=None):
    for s in A.SHOTS:
        if shots and s.sid not in shots: continue
        for t in (s.t0 + 0.01, (s.t0 + s.t1) / 2, s.t1 - 0.05):
            st = A.state(t); geo = ch.evaluate(st)
            loc, tgt = s.fn(t)
            loc = np.asarray(loc)
            eyes = (geo['eyeL'].mean(0) + geo['eyeR'].mean(0)) / 2
            if tgt is None: tgt = geo['eyeL'].mean(0) if s.sid == '3' else eyes
            B = geo['body']
            pts = {'bo_top': B[np.argmax(B[:, 2])], 'bo_bot': B[np.argmin(B[:, 2])], 'eyes': eyes, 'clock': A.DIAL}
            out = []
            for k, p in pts.items():
                xy, z = project(loc, tgt, s.lens, p, s.roll)
                out.append(f'{k}=({xy[0]:+.2f},{xy[1]:+.2f}) d{z:.2f}')
            top, _ = project(loc, tgt, s.lens, pts['bo_top'], s.roll); bot, _ = project(loc, tgt, s.lens, pts['bo_bot'], s.roll)
            # inside-body test: camera distance to Bo's centre vs radius
            c = B.mean(0); inside = np.linalg.norm(loc - c) < 0.19
            print(f"SH{s.sid:3s} t{t:5.2f} bo_h={abs(top[1]-bot[1])/2:4.2f}frame " + ' '.join(out) + ('  !!INSIDE BO' if inside else ''))
if __name__ == '__main__':
    report(sys.argv[1:] or None)

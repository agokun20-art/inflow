"""Full cast as locked 3D assets: Bo, Mimi, Pip, Blu.

Same rig and deformation field as rig.Character; each character adds its own
accessory geometry and fur exclusion. Sizes, palette and eye design follow the
official reference (refs/boopmo_official_reference.png).
"""
import math

import numpy as np
from scipy.spatial import cKDTree

from rig import Character, BO, body_from_dirs

SPECS = {
    'bo': dict(BO, acc='headphones', eye='oval', fur_c=(0.011, 0.011, 0.013), tip_c=(0.055, 0.056, 0.064)),
    'mimi': dict(H=0.268, W=0.292, fur_len=0.0155, strands=80000, seed=23, eye_y=0.455, eye_lon=0.29,
                 eye_rx=0.0, eye_rz=0.0, eye_d=0.0, acc='beanie', eye='arc', fur_c=(0.74, 0.62, 0.54), tip_c=(0.97, 0.92, 0.86)),
    'pip': dict(H=0.272, W=0.292, fur_len=0.019, strands=82000, seed=37, eye_y=0.58, eye_lon=0.235,
                eye_rx=0.0138, eye_rz=0.0190, eye_d=0.0085, acc=None, eye='oval', fur_c=(0.17, 0.012, 0.42), tip_c=(0.42, 0.10, 0.80)),
    'blu': dict(H=0.242, W=0.262, fur_len=0.0155, strands=70000, seed=53, eye_y=0.56, eye_lon=0.26,
                eye_rx=0.0124, eye_rz=0.0176, eye_d=0.0080, acc='glasses', eye='oval', fur_c=(0.004, 0.05, 0.40), tip_c=(0.06, 0.22, 0.85)),
}


def _surf(W, H, lon, el, push=0.0):
    d = np.array([math.sin(lon) * math.cos(el), -math.cos(lon) * math.cos(el), math.sin(el)])
    p = body_from_dirs(d[None], W, H)[0]
    n = p - np.array([0, 0, H * 0.5])
    n /= np.linalg.norm(n)
    return p + n * push, n


def _tube(path, radius, segs=12):
    path = np.asarray(path)
    V, F = [], []
    for i, c in enumerate(path):
        tan = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        tan /= np.linalg.norm(tan)
        ref = np.array([0, 0, 1.0]) if abs(tan[2]) < 0.9 else np.array([1.0, 0, 0])
        a = np.cross(tan, ref)
        a /= np.linalg.norm(a)
        b = np.cross(tan, a)
        for k in range(segs):
            th = 2 * math.pi * k / segs
            V.append(c + (a * math.cos(th) + b * math.sin(th)) * radius)
    for i in range(len(path) - 1):
        for k in range(segs):
            F.append((i * segs + k, i * segs + (k + 1) % segs, (i + 1) * segs + (k + 1) % segs, (i + 1) * segs + k))
    return V, F


class CastChar(Character):
    """Character with a per-spec accessory and eye style."""

    def __init__(self, name):
        self.name = name
        spec = SPECS[name]
        super().__init__(spec)

    def _build_headphones(self):
        acc = self.s.get('acc')
        self.cups, self.band_path = [], np.zeros((2, 3)) + 99
        self.acc_parts = []          # (verts, faces, material_key)
        self.patch = None
        if acc == 'headphones':
            super()._build_headphones()
            return
        self.hp_V, self.hp_F, self.hp_M = np.zeros((0, 3)), [], []
        if acc == 'beanie':
            self._beanie()
        elif acc == 'glasses':
            self._glasses()

    # ---- Mimi: knit beanie with ribs, folded cuff, smiley patch
    def _beanie(self):
        W, H = self.W, self.H
        self.cut_el = math.asin((0.60 * H - H / 2) / (H / 2))
        nlon, nel = 120, 40
        lons = np.linspace(-math.pi, math.pi, nlon, endpoint=False)
        V, F = [], []
        cuff_el = self.cut_el + 0.38
        for j in range(nel):
            el = self.cut_el - 0.05 + (math.pi / 2 - self.cut_el + 0.05) * (j / (nel - 1)) ** 0.9
            for lon in lons:
                sag = 0.045 * max(0, math.cos(lon)) ** 2       # front of the hat sits lower
                rib = 0.0024 * (0.5 + 0.5 * math.cos(lon * 48))
                cuff = 0.006 if el < cuff_el else 0.0
                crown = 0.012 * max(0, (el - 0.6) / 0.97) ** 1.5
                p, n = _surf(W, H, lon, el - sag * (1 - min(1, max(0, (el - self.cut_el) / 0.5))), push=0.0125 + rib + cuff + crown)
                V.append(p)
        for j in range(nel - 1):
            for i in range(nlon):
                F.append((j * nlon + i, j * nlon + (i + 1) % nlon, (j + 1) * nlon + (i + 1) % nlon, (j + 1) * nlon + i))
        top = len(V)
        V.append(_surf(W, H, 0, math.pi / 2, 0.0125 + 0.012)[0])
        for i in range(nlon):
            F.append(((nel - 1) * nlon + i, (nel - 1) * nlon + (i + 1) % nlon, top))
        self.acc_parts.append((np.array(V), F, 'knit'))
        # rolled lower edge of the cuff
        rim = []
        for lon in np.linspace(-math.pi, math.pi, 121):
            sag = 0.045 * max(0, math.cos(lon)) ** 2
            rim.append(_surf(W, H, lon, self.cut_el - 0.05 - sag, push=0.0175)[0])
        v, f = _tube(rim, 0.0045, 10)
        self.acc_parts.append((np.array(v), f, 'knit'))
        # smiley patch on the cuff front
        el_p = (self.cut_el - 0.05 + cuff_el) / 2 - 0.02
        c, n = _surf(W, H, 0.0, el_p, push=0.0215)
        t1 = np.array([1.0, 0, 0])
        t2 = np.cross(n, t1)
        t2 /= np.linalg.norm(t2)
        if t2[2] < 0:
            t2 = -t2
        s = 0.017
        quad = [c - t1 * s - t2 * s, c + t1 * s - t2 * s, c + t1 * s + t2 * s, c - t1 * s + t2 * s]
        self.patch = (np.array(quad), [(0, 1, 2, 3)])

    # ---- Blu: clear-framed sunglasses resting on top of the head
    def _glasses(self):
        W, H = self.W, self.H
        frames, lenses = [], []
        for side in (-1, 1):
            cx = side * 0.058
            outline = []
            for k in range(48):
                a = 2 * math.pi * k / 48
                # rounded rectangle via superellipse, 0.104 x 0.05
                x = 0.052 * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.45
                y = 0.025 * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.45
                outline.append((cx + x, y))
            pts = []
            for (x, y) in outline:
                # lens plane rests on the crown, tilted back ~62 degrees
                tilt = math.radians(62)
                p = np.array([x, -0.012 + y * math.cos(tilt), H - 0.004 + y * math.sin(tilt) + 0.0006 * (x * 30) ** 2 * 0])
                d = p - np.array([0, 0, H * 0.5])
                pts.append(p)
            pts.append(pts[0])
            v, f = _tube(pts, 0.0032, 10)
            frames.append((np.array(v), f))
            cen = np.mean(pts[:-1], axis=0)
            lv = [cen] + pts[:-1]
            lf = [(0, i + 1, (i + 1) % 48 + 1) for i in range(48)]
            lenses.append((np.array(lv) + np.array([0, 0.0005, 0.0005]), lf))
            # temple arm: from the outer edge back along the head, just above the fur
            arm = []
            for u in np.linspace(0, 1, 16):
                lon = side * (math.radians(42) + u * math.radians(70))
                el = math.radians(62) - u * math.radians(22)
                arm.append(_surf(W, H, lon, el, push=0.017)[0])
            arm[0] = np.array([cx + side * 0.053, -0.012, H - 0.004])
            v, f = _tube(arm, 0.0026, 8)
            frames.append((np.array(v), f))
        bridge = [np.array([-0.006 - 0.0005, -0.012 + 0.012, H + 0.006]), np.array([0, -0.014, H + 0.012]),
                  np.array([0.006 + 0.0005, -0.012 + 0.012, H + 0.006])]
        bridge = [np.array([-0.0065, -0.004, H + 0.012]), np.array([0.0, -0.006, H + 0.016]), np.array([0.0065, -0.004, H + 0.012])]
        v, f = _tube(bridge, 0.0028, 10)
        frames.append((np.array(v), f))
        for v, f in frames:
            self.acc_parts.append((v, f, 'clear_frame'))
        for v, f in lenses:
            self.acc_parts.append((v, f, 'lens'))
        self.glasses_center = np.array([0, -0.01, H])

    # ---- Mimi's closed happy eyes: glossy black arcs (∩) set into the fur
    def arc_eye_path(self, side, gx=0.0, gy=0.0, blink=0.0, widen=0.0):
        s, W, H = self.s, self.W, self.H
        lon_c = side * s['eye_lon'] + gx * 0.15
        el_c = math.asin(((s['eye_y'] + gy * 0.05) * H - H / 2) / (H / 2))
        hgt = 0.0075 * (1 + 0.5 * widen) * (1 - 0.5 * blink)
        pts = []
        for u in np.linspace(-1, 1, 24):
            lon = lon_c + u * 0.125
            el = el_c + (hgt / (H / 2)) * (1 - u * u) ** 0.8
            pts.append(_surf(W, H, lon, el, push=0.0075)[0])
        return pts

    def _build_eyes(self):
        super()._build_eyes()

    def _build_fur(self, rng):
        super()._build_fur(rng)
        acc = self.s.get('acc')
        keep = np.ones(len(self.fur_roots), bool)
        r = self.fur_roots
        if acc == 'beanie':
            zc = 0.60 * self.H - 0.012
            keep &= r[:, 2] < zc + 0.02 * np.maximum(0, -r[:, 1] / (self.W / 2)) * 0 + 0.0
            near = (r[:, 2] > zc - 0.03)
            self.fur_L[near] *= 0.7
        if acc == 'glasses':
            gc = self.glasses_center
            d = np.linalg.norm(r - gc, axis=1)
            self.fur_L[d < 0.09] *= np.clip((d[d < 0.09] - 0.03) / 0.06, 0.35, 1.0)
        if self.s.get('eye') == 'arc':
            for side in (-1, 1):
                pts = np.array(self.arc_eye_path(side))
                dd, _ = cKDTree(pts).query(r)
                self.fur_L *= np.clip((dd - 0.004) / 0.018, 0.2, 1.0)
        # rebuild strand shapes with the adjusted lengths, dropping excluded roots
        K = self.fur_K
        t = np.linspace(0, 1, K)[None, :, None]
        base = self.fur_rest[:, :1, :]
        dirs = (self.fur_rest - base)
        old_L = np.linalg.norm(dirs[:, -1], axis=1) + 1e-9
        scale = (self.fur_L / old_L)
        self.fur_rest = base + dirs * scale[:, None, None] * (old_L / np.maximum(old_L, 1e-9))[:, None, None]
        bd = self.fur_bristle - self.fur_bristle[:, :1, :]
        bl = np.linalg.norm(bd[:, -1], axis=1) + 1e-9
        self.fur_bristle = self.fur_bristle[:, :1, :] + bd * (self.fur_L * 1.55 / bl)[:, None, None]
        idx = np.nonzero(keep)[0]
        for k in ('fur_rest', 'fur_bristle', 'fur_roots', 'fur_n', 'fur_L', 'fur_rand', 'fur_shade'):
            setattr(self, k, getattr(self, k)[idx])

    def evaluate(self, st):
        out = super().evaluate(st)
        out['acc'] = [self.field(v, st) for (v, f, m) in self.acc_parts]
        if self.patch is not None:
            out['patch'] = self.field(self.patch[0], st)
        if self.s.get('eye') == 'arc':
            for side, key in ((-1, 'eyeL'), (1, 'eyeR')):
                pts = self.arc_eye_path(side, st['gx'], st['gy'], st[f'blink{key[-1]}'], st.get('widen', 0.0))
                v, f = _tube(pts, 0.0034, 10)
                out[key] = self.field(np.array(v), st)
        return out

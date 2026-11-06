"""Adventures of Bo v2 - character rig (pure numpy, no Blender dependency).

One deformation field drives everything attached to a character: body mesh,
fur strands, eyes and accessories. Because every part is evaluated through the
same function, nothing can detach or drift between shots.

Conventions: metres, Z up. Character local space has its origin at the ground
contact point; the character faces -Y when heading == 0.
"""
import math
import numpy as np
from scipy.spatial import cKDTree

BO = dict(H=0.30, W=0.33, fur_len=0.0165, strands=95000, seed=11,
          eye_y=0.565, eye_lon=0.245, eye_rx=0.0105, eye_rz=0.0165, eye_d=0.0075)


# ---------------------------------------------------------------- body shape
def _sefun(v, e):
    return np.sign(v) * np.abs(v) ** (2.0 / e)


def body_from_dirs(u, W, H):
    """Map unit directions to the superellipsoid 'egg' surface (flatter seat)."""
    a, b = W / 2, H / 2
    x, y, z = u.T
    e = np.where(z < 0, 2.9, 2.15)
    wf = 1 + 0.05 * (-z)
    return np.stack([a * _sefun(x, e) * wf, a * _sefun(y, e) * wf, b + b * _sefun(z, e)], 1)


def uv_sphere(rings=72, segs=112):
    th = np.linspace(0, np.pi, rings + 1)[1:-1]
    ph = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing='ij')
    d = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], -1).reshape(-1, 3)
    d = np.vstack([[0, 0, 1], d, [0, 0, -1]])
    faces = []
    nr = rings - 1
    idx = lambda r, s: 1 + r * segs + (s % segs)
    for s in range(segs):
        faces.append((0, idx(0, s + 1), idx(0, s)))
    for r in range(nr - 1):
        for s in range(segs):
            faces.append((idx(r, s), idx(r, s + 1), idx(r + 1, s + 1), idx(r + 1, s)))
    last = len(d) - 1
    for s in range(segs):
        faces.append((last, idx(nr - 1, s), idx(nr - 1, s + 1)))
    return d, faces


def vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        pass
    tris = []
    for f in F:
        if len(f) == 3:
            tris.append(f)
        else:
            tris.append((f[0], f[1], f[2]))
            tris.append((f[0], f[2], f[3]))
    T = np.array(tris)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    return N, T


def surface_point(W, H, d, center_z=None):
    """Ray from the body centre along d to the surface (bisection on the map)."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    return body_from_dirs(d[None], W, H)[0]


# ---------------------------------------------------------------- character
class Character:
    def __init__(self, spec):
        self.s = spec
        W, H = spec['W'], spec['H']
        self.W, self.H = W, H
        rng = np.random.default_rng(spec['seed'])
        d, faces = uv_sphere()
        self.V = body_from_dirs(d, W, H) * np.array([0.985, 0.985, 0.985]) + np.array([0, 0, H * 0.0075])
        self.F = faces
        N, T = vertex_normals(self.V, faces)
        if np.mean(np.sum(N * (self.V - np.array([0, 0, H / 2])), axis=1)) < 0:
            # winding was inward: flip so normals (and fur) point out of the body
            faces = [tuple(reversed(f)) for f in faces]
            self.F = faces
            N, T = vertex_normals(self.V, faces)
        self.N, self.T = N, T
        self._eye_rest = {}
        self._build_eyes()
        self._build_headphones()
        self._build_fur(rng)

    # ---- eyes: anchor on surface at (lon, height) + local frame
    def eye_anchor(self, side, gx=0.0, gy=0.0):
        s, W, H = self.s, self.W, self.H
        lon = side * s['eye_lon'] + gx * 0.20
        zc = s['eye_y'] + gy * 0.06
        # direction whose surface point sits at height zc*H on the front (-Y)
        el = math.asin(np.clip((zc * H - H / 2) / (H / 2), -0.95, 0.95))
        for _ in range(6):   # refine elevation so the mapped point hits the height
            d = np.array([math.sin(lon) * math.cos(el), -math.cos(lon) * math.cos(el), math.sin(el)])
            p = body_from_dirs(d[None], W, H)[0]
            el += (zc * H - p[2]) / (H / 2) * 0.8
        eps = 1e-3
        dl = np.array([math.sin(lon + eps) * math.cos(el), -math.cos(lon + eps) * math.cos(el), math.sin(el)])
        de = np.array([math.sin(lon) * math.cos(el + eps), -math.cos(lon) * math.cos(el + eps), math.sin(el + eps)])
        pl, pe = body_from_dirs(dl[None], W, H)[0], body_from_dirs(de[None], W, H)[0]
        t1 = (pl - p) / np.linalg.norm(pl - p)
        t2 = (pe - p) / np.linalg.norm(pe - p)
        n = np.cross(t2, t1)
        n /= np.linalg.norm(n)
        if n[1] > 0:
            n = -n
        return p, n, t1, t2

    def _build_eyes(self):
        u, v = np.meshgrid(np.linspace(0, np.pi, 18), np.linspace(0, 2 * np.pi, 28, endpoint=False), indexing='ij')
        self.eye_unit = np.stack([np.sin(u) * np.cos(v), np.sin(u) * np.sin(v), np.cos(u)], -1).reshape(-1, 3)
        faces = []
        R, S = 18, 28
        for r in range(R - 1):
            for c in range(S):
                faces.append((r * S + c, r * S + (c + 1) % S, (r + 1) * S + (c + 1) % S, (r + 1) * S + c))
        self.eye_faces = faces

    def eye_rest_verts(self, side, gx, gy, blink, widen=0.0, squint=0.0):
        s = self.s
        p, n, t1, t2 = self.eye_anchor(side, gx, gy)
        open_ = max(0.07, (1 - blink) * (1 - 0.55 * squint)) * (1 + 0.16 * widen)
        rx, rz, rd = s['eye_rx'] * (1 + 0.1 * widen), s['eye_rz'] * open_, s['eye_d']
        e = self.eye_unit
        # squint flattens the top of the eye (lid), not the bottom
        top = np.clip(e[:, 2], 0, 1)
        zz = e[:, 2] * rz - top * rz * 0.35 * squint
        loc = p + n * (rd * 0.55)
        return loc + np.outer(e[:, 0] * rx, t1) + np.outer(zz, t2) + np.outer(e[:, 1] * rd, -n)

    # ---- headphones: two cups with rings + band, built in rest space
    def _build_headphones(self):
        W, H = self.W, self.H
        verts, faces, mats = [], [], []
        self.cups = []

        def add(vs, fs, m):
            o = len(verts)
            verts.extend(vs)
            for f in fs:
                faces.append(tuple(i + o for i in f))
                mats.append(m)

        def revolve(profile, axis_o, axis_n, ref, segs=56):
            """profile: [(r, h)], revolved around axis through axis_o along axis_n."""
            u = np.cross(axis_n, ref)
            u /= np.linalg.norm(u)
            w = np.cross(axis_n, u)
            vs, fs = [], []
            P = len(profile)
            for i in range(segs):
                a = 2 * np.pi * i / segs
                c, s_ = math.cos(a), math.sin(a)
                for (r, h) in profile:
                    vs.append(axis_o + axis_n * h + (u * c + w * s_) * r)
            for i in range(segs):
                for j in range(P - 1):
                    a0, a1 = i * P + j, ((i + 1) % segs) * P + j
                    fs.append((a0, a1, a1 + 1, a0 + 1))
            return vs, fs

        zc = 0.535 * H
        rc = 0.047
        for side in (-1, 1):
            lon = side * math.radians(78)
            el = math.asin((zc - H / 2) / (H / 2))
            d = np.array([math.sin(lon) * math.cos(el), -math.cos(lon) * math.cos(el), math.sin(el)])
            p = body_from_dirs(d[None], W, H)[0]
            n = np.array([math.sin(lon), -math.cos(lon), 0.0])
            base = p + n * 0.006                   # fur compressed under the cushion
            cushion = [(0.0, 0.0), (rc * 0.80, 0.0), (rc * 0.93, 0.003), (rc * 0.98, 0.009), (rc * 0.97, 0.013)]
            shell = [(rc * 0.99, 0.013), (rc, 0.022), (rc * 0.97, 0.030), (rc * 0.90, 0.034), (rc * 0.55, 0.036), (0.0, 0.036)]
            vs, fs = revolve(cushion, base, n, np.array([0, 0, 1.0]))
            add(vs, fs, 2)
            vs, fs = revolve(shell, base, n, np.array([0, 0, 1.0]))
            add(vs, fs, 0)
            # illuminated ring on the outer plate edge
            ring = [(rc * 0.86 + 0.0013 * math.cos(t), 0.0352 + 0.0013 * math.sin(t)) for t in np.linspace(-np.pi / 2, np.pi / 2, 7)]
            vs, fs = revolve(ring, base, n, np.array([0, 0, 1.0]), segs=64)
            add(vs, fs, 1)
            self.cups.append(dict(side=side, base=base, n=n, top=base + np.array([0, 0, rc * 0.92])))
        # band: swept rounded rectangle over the head, slightly behind centre
        L, R = self.cups[0], self.cups[1]
        a0 = L['base'] + L['n'] * 0.022 + np.array([0, 0, rc * 0.80])
        a1 = R['base'] + R['n'] * 0.022 + np.array([0, 0, rc * 0.80])
        # band path hugs the head: surface points along the arc between cups, pushed into the fur layer
        path = []
        y_off = 0.03
        for th in np.linspace(-math.radians(70), math.radians(70), 64):
            dd = np.array([math.sin(th), y_off, math.cos(th)])
            dd /= np.linalg.norm(dd)
            sp = body_from_dirs(dd[None], W, H)[0]
            nn = sp - np.array([0, 0, H * 0.5])
            nn /= np.linalg.norm(nn)
            path.append(sp + nn * 0.0105)
        path = np.array(path)
        # blend ends into the cup tops
        for i in range(10):
            w_ = (1 - i / 10) ** 2
            path[i] = path[i] * (1 - w_) + a0 * w_
            path[-1 - i] = path[-1 - i] * (1 - w_) + a1 * w_
        prof = [(math.cos(t) * 0.010, math.sin(t) * 0.0045) for t in np.linspace(0, 2 * np.pi, 16, endpoint=False)]
        vs = []
        for i, c in enumerate(path):
            tan = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
            tan /= np.linalg.norm(tan)
            outv = c - np.array([0, 0, H * 0.5])
            outv -= tan * outv.dot(tan)
            outv /= np.linalg.norm(outv)
            side_v = np.cross(tan, outv)
            for (wy, wn) in prof:
                vs.append(c + side_v * wy + outv * wn)
        fs = []
        P = len(prof)
        for i in range(len(path) - 1):
            for j in range(P):
                fs.append((i * P + j, i * P + (j + 1) % P, (i + 1) * P + (j + 1) % P, (i + 1) * P + j))
        add(vs, fs, 0)
        self.band_path = path
        self.hp_V = np.array(verts)
        self.hp_F = faces
        self.hp_M = mats

    # ---- fur: area-weighted roots, clumped, with a 'bristle' alternative shape
    def _build_fur(self, rng):
        s, W, H = self.s, self.W, self.H
        T = self.T
        V = self.V
        A = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 2
        n = s['strands']
        tri = rng.choice(len(T), n, p=A / A.sum())
        r1, r2 = rng.random(n), rng.random(n)
        sq = np.sqrt(r1)
        bw = np.stack([1 - sq, sq * (1 - r2), sq * r2], 1)
        roots = (V[T[tri]] * bw[:, :, None]).sum(1)
        nrm = (self.N[T[tri]] * bw[:, :, None]).sum(1)
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        L = s['fur_len'] * rng.uniform(0.75, 1.3, n)
        # shorter fur around the eyes (sockets) and compressed under headphones
        for side in (-1, 1):
            p, _, _, _ = self.eye_anchor(side)
            dd = np.linalg.norm(roots - p, axis=1)
            L *= np.clip((dd - 0.014) / 0.03, 0.18, 1.0)
        for c in self.cups:
            axis_d = np.linalg.norm(np.cross(roots - c['base'], c['n']), axis=1)
            along = (roots - c['base']) @ c['n']
            under = (axis_d < 0.05) & (along > -0.03)
            L[under] *= np.clip((axis_d[under] - 0.040) / 0.02, 0.15, 1.0)
        bp = cKDTree(self.band_path)
        dband, _ = bp.query(roots)
        L *= np.clip((dband - 0.008) / 0.012, 0.35, 1.0)
        # flow + clumping
        grav = np.array([0, 0, -0.38])
        d = nrm + grav + rng.normal(0, 0.28, (n, 3))
        d /= np.linalg.norm(d, axis=1)[:, None]
        nc = 2600
        cidx = rng.choice(n, nc, replace=False)
        _, owner = cKDTree(roots[cidx]).query(roots)
        cd = d[cidx][owner]
        d = d * 0.62 + cd * 0.38
        d /= np.linalg.norm(d, axis=1)[:, None]
        K = 6
        t = np.linspace(0, 1, K)[None, :, None]
        bend = rng.normal(0, 0.22, (n, 3))
        rest = roots[:, None, :] + (d[:, None, :] * t + bend[:, None, :] * t ** 2 * 0.45 + grav * 0.55 * t ** 2) * L[:, None, None]
        bris_d = nrm + rng.normal(0, 0.12, (n, 3))
        bris_d /= np.linalg.norm(bris_d, axis=1)[:, None]
        bristle = roots[:, None, :] + bris_d[:, None, :] * t * (L * 1.55)[:, None, None]
        self.fur_rest, self.fur_bristle = rest.astype(np.float64), bristle.astype(np.float64)
        self.fur_roots, self.fur_n, self.fur_L = roots, nrm, L
        self.fur_K = K
        self.fur_rand = rng.uniform(0.65, 1.35, n)
        self.fur_shade = rng.uniform(0, 1, n).astype(np.float32)
        self.fur_w = (np.linspace(0, 1, K) ** 1.6)[None, :, None]

    # ------------------------------------------------------------ deformation
    def field(self, P, st):
        """Rest-local points -> world, for one rig state."""
        H = self.H
        p = np.array(P, dtype=np.float64, copy=True)
        sy = st['sy']
        sh = 1 / math.sqrt(sy)
        # asymmetric width (weight shift) for the creep
        p[:, 0] *= sh * (1 + st.get('wx', 0.0))
        p[:, 1] *= sh * (1 - st.get('wx', 0.0) * 0.5)
        p[:, 2] *= sy
        h = np.clip(p[:, 2] / (H * sy), 0, 1.7)
        bx, by = st['bx'], st['by']
        p[:, 0] += bx * h ** 2
        p[:, 1] += by * h ** 2
        bl = math.hypot(bx, by)
        p[:, 2] -= (bl * bl) / (2.2 * H) * h ** 3          # bending shortens the arc
        hd = st['heading']
        c, s_ = math.cos(hd), math.sin(hd)
        x, y = p[:, 0].copy(), p[:, 1].copy()
        p[:, 0] = c * x - s_ * y
        p[:, 1] = s_ * x + c * y
        p += np.array([st['x'], st['y'], st['lift']])
        return p

    def evaluate(self, st):
        """All world-space geometry for one state (dict)."""
        out = {}
        out['body'] = self.field(self.V, st)
        out['hp'] = self.field(self.hp_V, st)
        for side, key in ((-1, 'eyeL'), (1, 'eyeR')):
            ev = self.eye_rest_verts(side, st['gx'], st['gy'], st[f'blink{key[-1]}'], st.get('widen', 0.0), st[f'squint{key[-1]}'])
            out[key] = self.field(ev, st)
        fl = st['fluff']
        shape = self.fur_rest * (1 - fl) + self.fur_bristle * fl
        K = self.fur_K
        fw = self.field(shape.reshape(-1, 3), st).reshape(-1, K, 3)
        # dynamic offsets: inertia (world), spin flare + trailing lag
        dyn = np.asarray(st['fur_dyn'])
        off = dyn[None, None, :] * self.fur_w * self.fur_rand[:, None, None]
        rxy = fw[:, :1, :2] - np.array([st['x'], st['y']])[None, None, :]
        w = st['omega']
        flare = 0.0028 * w * w
        lag = st['spinlag']
        rad = np.concatenate([rxy, np.zeros_like(rxy[..., :1])], -1)
        tang = np.stack([-rxy[..., 1], rxy[..., 0], np.zeros_like(rxy[..., 0])], -1)
        off = off + (rad * flare - tang * lag) * self.fur_w * self.fur_rand[:, None, None]
        Lm = (self.fur_L * 0.75)[:, None, None]
        mag = np.linalg.norm(off, axis=2, keepdims=True)
        off = off * np.minimum(1.0, Lm / (mag + 1e-9))
        out['fur'] = fw + off
        return out

"""Adventures of Bo - Episode 1 "The Mysterious Boop" - master timeline.

Single source of truth for picture AND sound: character animation, prop
animation, the 29-shot camera plan, boop cues and SFX events.  render.py and
audio.py both import this module, so sync is exact by construction.

CONTINUITY RULE (the episode's comedic engine): every boop before the reveal
is caused by Bo tilting his head past ~8.5 degrees - the earcup presses into
his fur. Each of those boops flickers his headphone ring. All other Bo tilts
stay under 5 degrees. The final boop (115.8s) comes from the hallway and has
NO ring flicker.
"""
import math
import random

FPS = 24
DUR = 120.0
BOOP_TILT = 8.6          # Bo's tilt that triggers the earcup boop
SAFE_TILT = 5.0          # max non-boop tilt for Bo

EVENTS = []              # (kind, t, who, data)


def ev(kind, t, who=None, **data):
    EVENTS.append((kind, float(t), who, data))


# --------------------------------------------------------------------------
# Easing + tracks
# --------------------------------------------------------------------------
def _outback(u):
    c1 = 1.70158
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


EASE = {
    'linear': lambda u: u,
    'inout': lambda u: u * u * (3 - 2 * u),
    'in': lambda u: u * u,
    'out': lambda u: 1 - (1 - u) ** 2,
    'out3': lambda u: 1 - (1 - u) ** 3,
    'outback': _outback,
}


class Track:
    """Keyframe track; a newer segment takes over at its start time."""

    def __init__(self, v0):
        self.v0 = v0
        self.segs = []

    def value(self, t):
        seg = None
        for s in self.segs:
            if s[0] <= t:
                seg = s
            else:
                break
        if seg is None:
            return self.v0
        t0, t1, a, b, e = seg
        if t >= t1:
            return b
        return a + (b - a) * EASE[e]((t - t0) / (t1 - t0))

    def to(self, t0, t1, b, ease='inout'):
        a = self.value(t0)
        if self.segs and t0 < self.segs[-1][0]:
            raise ValueError(f'out of order key at {t0}')
        self.segs.append((t0, max(t1, t0 + 1e-4), a, b, ease))


# --------------------------------------------------------------------------
# Characters
# --------------------------------------------------------------------------
SQUASH = {'bo': 1.0, 'mimi': 0.9, 'pip': 1.3, 'blu': 0.7}
PARAMS = dict(x=0.0, z=0.0, base=0.0, tilt=0.0, yaw=0.0, gx=0.0, gy=0.0, lid=0.0, slant=0.0,
              widen=0.0, sx=1.0, sy=1.0, visible=1.0, breath=1.0, glint=-1.0)


class Char:
    def __init__(self, name, **init):
        self.name = name
        self.tr = {k: Track(init.get(k, v)) for k, v in PARAMS.items()}
        self.hops, self.blinks, self.wobbles, self.sways, self.scoots = [], [], [], [], []
        self.boops = []
        self.blink_ok = []
        self.phase = random.Random(hash(name) % 1000).uniform(0, 6.28)

    # authoring API
    def go(self, p, t0, t1, v, ease='inout'):
        self.tr[p].to(t0, t1, v, ease)
        return self

    def set(self, p, t, v):
        self.tr[p].to(t, t + 1e-3, v, 'linear')
        return self

    def many(self, t0, t1, ease='inout', **kv):
        for k, v in kv.items():
            self.go(k, t0, t1, v, ease)
        return self

    def hop(self, t0, t1, h=60, x=None, z=None, base=None, k=1.0, land_k=None, sfx=True):
        if x is not None:
            self.go('x', t0, t1, x, 'linear')
        if z is not None:
            self.go('z', t0, t1, z, 'linear')
        if base is not None:
            self.go('base', t0, t1, base, 'linear')
        kk = k * SQUASH[self.name]
        self.hops.append(dict(t0=t0, t1=t1, h=h, k=kk, lk=(land_k if land_k is not None else k) * SQUASH[self.name]))
        if sfx:
            ev('takeoff', t0, self.name, h=h)
            ev('land', t1, self.name, h=h)
        return self

    def scoot(self, t0, t1, x=None, z=None, lean=4.0):
        x0 = self.tr['x'].value(t0)
        if x is not None:
            self.go('x', t0, t1, x, 'inout')
        if z is not None:
            self.go('z', t0, t1, z, 'inout')
        d = 0 if x is None else (1 if x > x0 else -1)
        self.scoots.append((t0, t1, lean * d))
        ev('scoot', t0, self.name, t1=t1)
        return self

    def blink(self, t, dur=0.16):
        self.blinks.append((t, dur))
        return self

    def wobble(self, t0, dur, amp, freq):
        self.wobbles.append((t0, dur, amp, freq))
        return self

    def sway(self, t0, t1, amp, period):
        self.sways.append((t0, t1, amp, period))
        return self

    def boop(self, t):
        self.boops.append(t)
        return self

    # evaluation
    def auto_blinks(self, seed):
        rng = random.Random(seed)
        for (a, b) in self.blink_ok:
            t = a + rng.uniform(0.6, 2.0)
            while t < b - 0.3:
                if all(abs(t - bt) > 1.2 for bt, _ in self.blinks):
                    self.blinks.append((t, rng.uniform(0.13, 0.18)))
                t += rng.uniform(2.8, 5.2)

    def state(self, t):
        st = {k: tr.value(t) for k, tr in self.tr.items()}
        sx, sy, lift, tilt = st['sx'], st['sy'], 0.0, st['tilt']
        for hp in self.hops:
            t0, t1, h, k, lk = hp['t0'], hp['t1'], hp['h'], hp['k'], hp['lk']
            pre = 0.13
            if t0 - pre <= t < t0:
                q = math.sin((t - (t0 - pre)) / pre * math.pi / 2)
                sy *= 1 - 0.15 * k * q
                sx *= 1 + 0.09 * k * q
            elif t0 <= t < t1:
                u = (t - t0) / (t1 - t0)
                lift += 4 * h * u * (1 - u)
                a = 0.13 * k * (1 - u) ** 2 + 0.05 * k * u ** 3
                sy *= 1 + a
                sx *= 1 - a * 0.6
            elif t1 <= t < t1 + 0.5:
                d = t - t1
                amp = 0.19 * lk * min(1.0, h / 70 + 0.35)
                q = amp * math.exp(-d / 0.09) * math.cos(2 * math.pi * d / 0.26)
                sy *= 1 - q
                sx *= 1 + q * 0.65
        for (t0, t1, lean) in self.scoots:
            if t0 <= t < t1:
                u = (t - t0) / (t1 - t0)
                env = math.sin(math.pi * u)
                tilt += lean * env
                sy *= 1 - 0.045 * abs(math.sin(2 * math.pi * 4.2 * (t - t0))) * env
                sx *= 1 + 0.03 * abs(math.sin(2 * math.pi * 4.2 * (t - t0))) * env
        for (t0, dur, amp, f) in self.wobbles:
            if t0 <= t < t0 + dur:
                u = (t - t0) / dur
                tilt += amp * math.sin(2 * math.pi * f * (t - t0)) * math.sin(math.pi * u)
        for (t0, t1, amp, per) in self.sways:
            if t0 <= t < t1:
                env = min(1.0, (t - t0) / 1.2, (t1 - t) / 1.2)
                tilt += amp * env * math.sin(2 * math.pi * (t - t0) / per)
        br = st['breath']
        b = math.sin(2 * math.pi * t / 3.4 + self.phase)
        sy *= 1 + 0.012 * br * b
        sx *= 1 - 0.006 * br * b
        blink = 0.0
        for (bt, dur) in self.blinks:
            if bt <= t < bt + dur:
                u = (t - bt) / dur
                blink = max(blink, u / 0.4 if u < 0.4 else 1 - (u - 0.4) / 0.6)
        st.update(sx=sx, sy=sy, lift=lift, tilt=tilt, blink=min(1.0, blink), visible=st['visible'] > 0.5)
        if self.name == 'bo':
            a = abs(tilt)
            st['press'] = min(1.0, max(0.0, (a - 4.5) / 4.0))
            ring = 0.0
            for tb in self.boops:
                if t >= tb:
                    ring = max(ring, math.exp(-(t - tb) / 0.18))
            st['ring'] = ring
        return st


bo = Char('bo', x=-550.0, z=0.10, base=62.0, lid=0.38, gy=0.15)
pip = Char('pip', x=1680.0, z=1.06, visible=0.0)
mimi = Char('mimi', x=1505.0, z=1.7, visible=0.0)
blu = Char('blu', x=1505.0, z=1.7, visible=0.0)
CHARS = {'bo': bo, 'mimi': mimi, 'pip': pip, 'blu': blu}

# props
PROP = {k: Track(v) for k, v in dict(pouf_sy=0.93, cushion_x=400.0, cushion_z=0.12, cushion_rot=0.0, cushion_sx=1.0,
                                       cushion_sy=1.0, top_dx=0.0).items()}


def pgo(k, t0, t1, v, ease='inout'):
    PROP[k].to(t0, t1, v, ease)


BOOPS = []   # (t, variant)


def bo_boop(t, variant='head'):
    bo.boop(t)
    BOOPS.append((t, variant))


# ==========================================================================
# CHOREOGRAPHY
# ==========================================================================
# ---- Scene 1: A Very Quiet Evening (0-12) ---------------------------------
bo.sway(1.5, 11.6, 2.2, 1.5)                      # sways with the music (80 BPM, 2 beats)
bo.go('lid', 5.6, 6.3, 0.58).go('lid', 6.9, 7.6, 0.38)
bo.blink(4.6, 0.3).blink(9.2, 0.3)

# ---- Scene 2: The First Boop (12-25) --------------------------------------
bo.go('tilt', 12.6, 13.18, BOOP_TILT)             # contented settle ... too far
bo_boop(13.2)
bo.many(13.25, 13.4, lid=0.0, ease='out')
bo.many(13.4, 13.62, gx=-0.45, gy=0.0, ease='out')
bo.go('tilt', 13.7, 14.6, 0.0)
bo.go('gx', 15.45, 15.7, 0.0)
bo.many(15.8, 16.58, tilt=-BOOP_TILT, gx=-0.7)    # leans toward the sound ... causes it
bo_boop(16.6)
bo.go('widen', 16.65, 16.8, 0.5, 'out')
bo.many(18.0, 19.0, tilt=0.0, widen=0.2)
bo.go('gx', 19.5, 19.85, -0.5).go('gx', 20.6, 20.95, 0.5).go('gx', 21.6, 21.9, 0.0)
bo.blink(22.1, 0.17)
bo.many(22.45, 22.9, lid=0.45, slant=0.7, widen=0.0)
bo.go('gy', 23.5, 23.62, 0.5, 'out').go('gy', 23.62, 23.85, 0.0)
bo.go('sy', 23.5, 23.6, 0.94, 'out').go('sy', 23.6, 23.85, 1.0)
ev('nod', 23.55, 'bo')

# ---- Scene 3: Detective Bo (25-40) ----------------------------------------
bo.many(25.0, 25.15, lid=0.18, slant=0.45)
bo.hop(25.35, 25.8, h=45, x=-430, z=0.15, base=0.0)
pgo('pouf_sy', 25.35, 25.7, 1.0, 'outback')
ev('pouf', 25.35, 'bo')
bo.scoot(25.95, 27.1, x=-440, z=0.28)
bo.many(27.4, 28.0, tilt=5.0, yaw=0.75, gx=0.6, sx=1.07, x=-420)
ev('stretch', 27.45, 'bo')
bo.go('gy', 28.3, 28.6, -0.2).go('gy', 28.6, 28.95, 0.2)
bo.blink(29.18, 0.16)
bo.many(29.4, 29.8, tilt=0.0, yaw=0.3, gx=0.2, gy=0.0, sx=1.0, x=-440)
bo.hop(30.0, 30.45, h=40, x=-100, z=0.18)
bo.hop(30.6, 31.05, h=40, x=230, z=0.10)
bo.many(31.5, 32.2, tilt=5.0, yaw=0.6, gx=0.8, gy=0.45, sy=1.12, sx=0.95)
pgo('cushion_sx', 31.5, 32.0, 0.96)
ev('stretch', 31.55, 'bo')
bo.go('gy', 32.6, 32.9, 0.65)
bo.blink(33.3, 0.17)
bo.many(33.5, 34.0, tilt=0.0, yaw=0.0, gx=0.0, gy=0.2, sy=0.9, sx=1.06, lid=0.35, slant=0.0, ease='out')
pgo('cushion_sx', 33.5, 33.8, 1.0)
ev('deflate', 33.5, 'bo')
bo.many(34.2, 34.8, sy=1.0, sx=1.0, lid=0.15, slant=0.4, gy=0.0)
bo.go('gx', 34.55, 34.8, 0.7)
bo.scoot(35.2, 36.9, x=860, z=0.20, lean=4.0)
bo.many(36.95, 37.37, gy=-0.8, tilt=BOOP_TILT)
bo_boop(37.4)
bo.set('breath', 37.42, 0.0)                      # FREEZE
bo.many(37.42, 37.5, widen=0.7, lid=0.0, slant=0.0, ease='out')
ev('freeze', 37.42, 'bo')
bo.many(41.0, 42.0, tilt=0.0, gy=0.0, widen=0.15, breath=1.0)   # (off screen)

# ---- Scene 4: Pip Makes an Entrance (40-55) -------------------------------
pip.set('visible', 40.0, 1.0)
pip.go('x', 40.3, 41.0, 1585).go('yaw', 40.3, 41.0, -0.3)
pip.go('gx', 41.1, 41.4, 0.4).go('gx', 41.9, 42.15, -0.9)
pip.go('widen', 42.15, 42.3, 1.0, 'out')
pip.wobble(42.6, 0.42, 7.0, 9.0)
ev('wiggle', 42.6, 'pip')
pip.scoot(43.1, 43.45, x=1505, lean=0)
pip.go('yaw', 43.5, 43.7, -0.5).go('gx', 43.5, 43.7, -0.8)
pip.hop(43.65, 44.15, h=85, x=1340, z=0.65)
pip.hop(44.30, 44.75, h=80, x=1170, z=0.35)
pip.hop(44.90, 45.35, h=80, x=1060, z=0.05)
pip.hop(45.50, 45.95, h=85, x=800, z=-0.05)
pip.hop(46.10, 46.55, h=90, x=560, z=0.08, land_k=1.5)
ev('bonk', 46.55, 'pip')
pgo('cushion_x', 46.55, 46.85, 335.0, 'out3')
pgo('cushion_rot', 46.55, 46.85, -11.0, 'out3')
pgo('cushion_z', 46.55, 46.85, 0.14, 'out3')
pgo('cushion_sx', 46.55, 46.62, 0.86, 'out')
pgo('cushion_sx', 46.62, 46.9, 1.0, 'outback')
pip.hop(46.62, 46.95, h=35, x=585, z=0.03)
pip.blink(46.72, 0.2)
pip.go('widen', 46.6, 46.8, 0.0)
pip.many(47.3, 47.6, yaw=0.35, gx=0.75)
bo.go('gx', 43.6, 43.9, 0.6).go('gx', 45.3, 45.8, -0.7).go('widen', 46.55, 46.7, 0.4, 'out')
bo.many(47.3, 47.6, yaw=-0.35, gx=-0.75, widen=0.1)
pip.blink(48.2, 0.17)
bo.blink(48.9, 0.17)
pip.many(49.5, 49.8, sy=0.93, sx=1.05).many(50.6, 50.9, sy=1.0, sx=1.0)
bo.go('gy', 49.9, 50.2, 0.12)
bo.go('tilt', 50.95, 51.57, BOOP_TILT)            # the awkward tilt...
bo_boop(51.6, 'room')
bo.many(51.78, 51.95, yaw=-0.55, gx=-1.0, tilt=0.0, gy=0.0, widen=0.5, ease='out')
pip.many(51.78, 51.9, yaw=-0.55, gx=-1.0, widen=0.5, ease='out')
ev('whip', 51.8, 'both')
pip.hop(52.55, 52.9, h=50)
pip.hop(53.15, 53.5, h=50)
bo.many(52.4, 52.8, lid=0.3, slant=0.6, widen=0.1)

# ---- Scene 5: The Investigation Grows (55-70) -----------------------------
mimi.set('visible', 55.0, 1.0)
mimi.go('yaw', 55.0, 55.1, -0.2)
mimi.hop(55.25, 55.70, h=55, z=1.1)
mimi.hop(55.95, 56.40, h=60, x=1380, z=0.7)
mimi.hop(56.60, 57.05, h=60, x=1180, z=0.38)
mimi.hop(57.30, 57.75, h=55, x=1040, z=0.12)
mimi.wobble(57.9, 0.5, 5.0, 5.0).go('widen', 57.9, 58.1, 0.4)
ev('wiggle', 57.9, 'mimi')
bo.many(56.5, 56.9, yaw=0.4, gx=0.8, lid=0.1, slant=0.2, widen=0.0)
pip.many(56.4, 56.7, yaw=0.4, gx=0.9, widen=0.0)
pip.hop(58.65, 59.10, h=70, x=380, z=0.25)
pip.hop(59.25, 59.70, h=70, x=190, z=0.40)
pip.many(59.8, 60.1, yaw=-0.45, gx=-0.7)
mimi.go('yaw', 58.8, 59.0, -0.3)
mimi.hop(58.95, 59.40, h=55, x=640, z=0.06)
mimi.hop(59.70, 60.30, h=120, x=345, z=0.13, base=100.0)
pgo('cushion_sy', 60.3, 60.45, 0.86, 'out')
bo.scoot(59.1, 59.9, x=700, z=0.12)
bo.many(59.9, 60.3, lid=0.5, slant=0.0, gy=0.25, gx=0.0, yaw=0.0, breath=0.4)
pgo('cushion_sy', 60.75, 61.0, 0.76, 'out')
mimi.go('base', 60.75, 61.0, 88.0, 'out')
ev('pff', 60.8, 'mimi', big=True)
mimi.go('widen', 60.85, 61.0, 0.85, 'out')
pip.many(61.0, 61.2, yaw=0.3, gx=0.8)
bo.many(61.0, 61.25, lid=0.1, gx=-0.6, gy=0.0)
mimi.hop(61.55, 61.90, h=30, sfx=False)
pgo('cushion_sy', 61.9, 62.0, 0.70, 'out')
pgo('cushion_sy', 62.0, 62.25, 0.76)
ev('pff', 61.9, 'mimi', big=False)
mimi.go('sy', 62.2, 62.35, 1.08).go('sy', 62.35, 62.6, 1.0).go('widen', 62.2, 62.5, 0.3)
pip.many(62.6, 63.0, tilt=-6.0, x=172, sy=1.05, yaw=-0.45, gx=-0.7)
pip.go('x', 63.3, 63.42, 150, 'out')
ev('bop', 63.4, 'pip')
pgo('top_dx', 63.4, 63.75, -32.0, 'out3')
ev('book_slide', 63.42, 'pip', t1=63.75)
pip.many(63.45, 63.6, widen=0.8, tilt=0.0, sy=1.0, ease='out')
pip.many(63.95, 64.2, yaw=0.5, gx=0.9)
pip.hop(64.3, 64.55, h=30)
bo.many(65.0, 65.2, lid=0.5, gy=0.25, gx=-0.3)
bo.blink(65.35, 0.6)                               # slow blink: "no."
pip.many(67.05, 67.5, sy=0.88, sx=1.06, widen=0.0, gy=0.3, ease='out')
ev('deflate', 67.05, 'pip')
pip.many(67.7, 68.0, sy=1.0, sx=1.0, gy=0.0)
pip.hop(67.9, 68.35, h=55, x=360, z=0.05)
mimi.hop(67.75, 68.25, h=60, x=610, z=-0.05, base=0.0)
pgo('cushion_sy', 67.75, 68.1, 1.0, 'outback')
bo.scoot(67.6, 68.3, x=880, z=0.08)
bo.many(67.6, 68.0, lid=0.15, breath=1.0)
pip.go('gx', 68.55, 68.65, -0.8).go('gx', 68.85, 68.95, 0.8).go('gx', 69.15, 69.25, -0.4).go('gx', 69.45, 69.55, 0.3)
mimi.many(68.6, 69.0, tilt=-5.0, gx=0.4, gy=-0.3, widen=0.0)
bo.many(68.5, 69.0, gy=0.35, lid=0.3, gx=0.0, yaw=0.0)

# ---- Scene 6: Blu Has a Theory (70-85) ------------------------------------
blu.set('visible', 70.0, 1.0)
blu.go('lid', 70.0, 70.1, 0.15)
blu.hop(70.1, 70.5, h=45, z=1.05, k=0.8)
blu.hop(70.6, 71.0, h=45, x=1400, z=0.65, k=0.8)
blu.hop(71.1, 71.5, h=45, x=1280, z=0.35, k=0.8)
blu.hop(71.6, 72.0, h=45, x=1160, z=0.12, k=0.8)
blu.go('glint', 72.05, 72.5, 1.0, 'linear').set('glint', 72.55, -1.0)
for i, g in enumerate([-1.0, -0.5, 0.0, 0.5]):
    blu.go('gx', 72.0 + 0.25 * i, 72.05 + 0.25 * i, g, 'linear')
    ev('scan', 72.0 + 0.25 * i, 'blu', i=i)
blu.go('gx', 73.0, 73.1, -0.6)
bo.many(73.4, 73.7, yaw=0.45, gx=0.8, gy=0.0, lid=0.05)
pip.many(73.3, 73.5, yaw=0.5, gx=1.0)
mimi.many(73.5, 73.8, yaw=0.4, gx=0.8, gy=0.0, tilt=0.0)
bo.go('tilt', 73.95, 74.57, BOOP_TILT)
bo_boop(74.6)
pip.many(74.75, 74.9, yaw=-0.6, gx=-1.0, gy=-0.6, ease='out')
mimi.many(74.75, 74.9, yaw=-0.3, gy=-0.8, gx=-0.2, ease='out')
ev('whip', 74.78, 'pip+mimi')
bo.many(74.8, 75.0, gx=-0.6, yaw=0.0, widen=0.5, ease='out')
blu.many(74.65, 74.85, lid=0.45, slant=0.3, gx=-0.8, yaw=-0.35)
bo.go('tilt', 75.1, 75.6, 0.0)
pip.hop(76.0, 76.3, h=35)
mimi.many(75.8, 76.2, gy=0.0, gx=0.3)
bo.go('sy', 76.6, 76.85, 1.07).go('sy', 76.85, 77.2, 1.0).go('widen', 76.6, 77.0, 0.1)
blu.many(77.6, 77.7, gy=0.0)
blu.go('gy', 78.15, 78.3, -0.55).go('gy', 78.65, 78.8, 0.0).go('gy', 79.05, 79.2, -0.55)
blu.go('tilt', 79.25, 79.6, -5.0)
blu.many(79.6, 79.7, widen=0.4, lid=0.1, ease='out')
blu.many(80.0, 80.4, tilt=0.0, gx=-0.85, gy=-0.5)
pip.hop(80.35, 80.75, h=40)
bo.many(80.1, 80.4, yaw=0.35, gx=0.8, gy=0.0, widen=0.1)
bo.go('tilt', 80.45, 80.97, BOOP_TILT)
bo_boop(81.0)
for c in (bo, pip, mimi, blu):
    c.set('breath', 81.02, 0.0)
ev('freeze', 81.02, 'all')
pip.go('widen', 81.02, 81.1, 0.6, 'out')
mimi.go('widen', 81.02, 81.1, 0.6, 'out')
bo.go('widen', 81.02, 81.1, 0.5, 'out')
blu.go('gy', 82.0, 82.25, -0.8)
pip.many(82.4, 83.0, yaw=0.4, gx=0.9, gy=0.0)
mimi.many(82.4, 83.0, yaw=0.35, gx=0.8, gy=-0.2)
bo.many(83.0, 83.9, gy=-1.0, gx=0.35)
bo.blink(84.5, 0.4)

# ---- Scene 7: Mystery Solved (85-102) -------------------------------------
bo.many(85.2, 86.0, tilt=0.0, gy=-0.6, breath=0.6)
bo.go('tilt', 86.2, 86.97, BOOP_TILT)
bo_boop(87.0)
bo.go('tilt', 87.6, 88.3, 0.0)
for c in (pip, mimi, blu):
    c.set('breath', 89.0, 1.0)
bo.many(89.4, 89.7, gy=-0.2, gx=0.2, widen=0.2)
bo.go('tilt', 89.75, 90.37, BOOP_TILT)
bo_boop(90.4)
bo.go('widen', 90.45, 90.6, 0.6, 'out')
bo.go('tilt', 90.6, 91.0, 0.0)
bo.go('tilt', 91.75, 92.17, 8.9, 'in')            # one more time - decisive
bo_boop(92.2)
bo.many(92.25, 92.4, widen=1.0, gy=-0.2, ease='out')
bo.go('tilt', 92.7, 93.2, 0.0)
bo.go('breath', 92.7, 93.2, 1.0)
for t0 in (94.55, 95.05, 95.55):
    pip.hop(t0, t0 + 0.4, h=90)
pip.hop(96.05, 96.45, h=70)
pip.many(94.4, 94.6, widen=0.6, gx=0.9, yaw=0.3, gy=0.0)
mimi.hop(94.8, 95.25, h=55)
mimi.hop(95.6, 96.05, h=55)
mimi.many(94.5, 94.8, widen=0.9, gx=0.6, yaw=0.3, gy=0.0, tilt=0.0)
blu.many(94.6, 95.0, lid=0.2, slant=0.0, widen=0.0, gx=-0.6, gy=0.0, yaw=-0.2)
blu.go('tilt', 95.1, 95.6, -6.0).go('tilt', 96.3, 96.8, 0.0)
bo.go('gx', 94.6, 94.8, -0.6).go('gx', 95.6, 95.8, 0.5)
bo.many(97.2, 97.5, yaw=0.0, gx=0.0, gy=0.0, lid=0.0, widen=0.25)
bo.blink(98.4, 0.45)
bo.many(99.2, 99.8, sy=0.95, sx=1.03, lid=0.15, gy=0.1)
pip.scoot(97.4, 99.0, x=330, z=0.04, lean=2)
mimi.scoot(97.6, 99.2, x=612, z=0.0, lean=2)
blu.scoot(97.8, 99.4, x=1150, z=0.10, lean=1)

# ---- Scene 8: The Celebration (102-113) -----------------------------------
bo.many(101.5, 102.0, sy=1.0, sx=1.0, lid=0.08, gy=0.0)
pip.many(101.5, 102.0, gx=0.0, yaw=0.0, widen=0.3)
mimi.many(101.5, 102.0, gx=0.0, yaw=0.0, widen=0.5)
blu.many(101.5, 102.0, gx=0.0, yaw=0.0, lid=0.2)
bo.hop(102.6, 103.0, h=40)
pip.hop(103.3, 104.0, h=150, k=1.1)
pip.wobble(103.35, 0.6, 8.0, 3.3)
mimi.hop(104.5, 105.0, h=80)
for land in (106.0, 107.0, 108.0):
    bo.hop(land - 0.4, land, h=50)
    pip.hop(land - 0.5, land, h=110)
    mimi.hop(land - 0.45, land, h=70)
pip.hop(106.55, 106.85, h=40)
pip.hop(107.55, 107.85, h=40)
blu.go('gx', 102.6, 102.75, -0.6).go('gx', 103.6, 103.75, -1.0).go('gx', 104.6, 104.75, -0.8)
for b in (106.0, 107.0, 108.0):
    blu.go('sy', b - 0.06, b, 0.975).go('sy', b, b + 0.15, 1.0)
blu.many(108.6, 108.85, gx=0.0, lid=0.25)
blu.hop(109.0, 109.6, h=175, k=1.6, land_k=0.45)
blu.wobble(109.05, 0.5, 9.0, 4.0)
blu.go('widen', 109.1, 109.3, 0.5, 'out').go('lid', 109.1, 109.3, 0.0)
blu.set('glint', 109.25, 0.0)
blu.go('glint', 109.25, 109.5, 1.0, 'linear').set('glint', 109.52, -1.0)
for c, g in ((bo, 1.0), (pip, 1.0), (mimi, 1.0)):
    c.many(109.05, 109.2, gx=g, widen=0.8, ease='out')
bo.go('yaw', 109.05, 109.2, 0.35)
ev('whip', 109.05, 'group')
blu.wobble(109.9, 0.3, 2.5, 10.0)
blu.many(109.9, 110.2, lid=0.2, widen=0.0, gx=0.0)
for c in (bo, pip, mimi):
    c.many(110.3, 110.5, gx=0.0, widen=0.5)
bo.go('yaw', 110.3, 110.5, 0.0)
for land in (111.0, 112.0):
    bo.hop(land - 0.4, land, h=45)
    pip.hop(land - 0.5, land, h=100)
    mimi.hop(land - 0.45, land, h=65)
    blu.hop(land - 0.3, land, h=25)
mimi.go('widen', 110.5, 110.8, 0.8)

# ---- Scene 9: One More Boop (113-117.5) -----------------------------------
for c in (bo, pip, blu):
    c.go('lid', 113.2, 114.0, 0.35)
mimi.go('widen', 113.2, 114.0, 0.3)
mimi.go('tilt', 113.6, 114.4, -5.0)
for c in (bo, pip, mimi, blu):
    c.go('breath', 113.0, 113.5, 0.7)
BOOPS.append((115.8, 'outside'))                   # NOT Bo: no ring flicker
for c in (bo, pip, mimi, blu):
    c.many(115.98, 116.12, yaw=0.55, gx=1.0, gy=-0.1, lid=0.0, widen=0.55, ease='out')
    c.set('breath', 116.0, 0.0)
mimi.go('tilt', 115.98, 116.12, 0.0, 'out')
mimi.go('widen', 116.12, 116.2, 0.75)
ev('whip', 115.98, 'all')
BOOPS.append((119.0, 'tiny'))                      # end-card button

# ---- blink windows --------------------------------------------------------
bo.blink_ok = [(0, 4.0), (42.0, 47.0), (53.0, 59.5), (68.5, 73.0), (102.5, 115.0)]
pip.blink_ok = [(53.5, 62.5), (65.0, 74.5), (75.5, 80.3), (94.0, 108.8), (110.5, 115.5)]
mimi.blink_ok = [(58.4, 60.7), (62.6, 74.5), (75.5, 80.5), (94.0, 108.8), (110.5, 115.5)]
blu.blink_ok = [(73.2, 74.5), (75.2, 77.5), (94.0, 108.5), (110.4, 115.5)]
for i, c in enumerate(CHARS.values()):
    c.auto_blinks(100 + i)
    c.blinks.sort()

# ==========================================================================
# CAMERA - 29 shots
# ==========================================================================
class Shot:
    def __init__(self, sid, t0, t1, keys, dof=0.0, cblur=0.0, focus=None, size='', move='', action='',
                 track=None, scene=0):
        self.sid, self.t0, self.t1 = sid, t0, t1
        self.keys = keys            # [(t, cx, cy, zoom, ease)]
        self.dof, self.cblur, self.focus = dof, cblur, focus
        self.size, self.move, self.action, self.track, self.scene = size, move, action, track, scene

    def cam(self, t):
        k = self.keys
        if t <= k[0][0]:
            c = k[0][1:4]
        elif t >= k[-1][0]:
            c = k[-1][1:4]
        else:
            for a, b in zip(k, k[1:]):
                if a[0] <= t < b[0]:
                    u = EASE[b[4] if len(b) > 4 else 'inout']((t - a[0]) / (b[0] - a[0]))
                    c = tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
                    break
        cx, cy, zm = c
        if self.track is not None:
            tx, ty = self.track(t)
            cx, cy = cx + tx, cy + ty
        # gentle operator drift (sub-pixel to ~2px)
        cx += 1.6 / zm * math.sin(0.61 * t + self.t0)
        cy += 1.2 / zm * math.sin(0.43 * t + 2 * self.t0)
        return cx, cy, zm


def _bo_cup_track(t):
    from art import cup_world_pos
    st = bo.state(t)
    x, y = cup_world_pos(st, side=1)
    return x - 1010.0 - 30.0, y + 172.0


SHOTS = [
    Shot('1A', 0.0, 7.0, [(0.0, -860, -440, 0.92), (7.0, -560, -300, 1.28)], scene=1, size='Extreme wide', move='Slow dolly-right & push-in',
         action='Evening in the miniature bedroom; camera drifts from the dusk window to Bo relaxing on his pouf.'),
    Shot('1B', 7.0, 12.0, [(7.0, -550, -272, 1.9), (12.0, -550, -280, 2.06)], dof=3.5, scene=1, size='Medium', move='Slow push-in',
         action='Bo sways to the music in his headphones, eyes contentedly half-closed.'),
    Shot('2A', 12.0, 17.0, [(12.0, -550, -276, 2.25), (17.0, -548, -279, 2.32)], dof=4.0, scene=2, size='Medium close-up', move='Locked off',
         action='Silence. Bo settles, leans... BOOP. Eyes flick left. He waits. Leans toward the sound... BOOP.'),
    Shot('2B', 17.0, 25.0, [(17.0, -552, -276, 2.45), (24.6, -550, -262, 3.7)], dof=6.0, scene=2, size='Close-up -> extreme close-up', move='Slow push to eyes',
         action='Bo is intrigued; suspicious glances left and right; eyes narrow; a decisive little nod.'),
    Shot('3A', 25.0, 31.0, [(25.0, -470, -215, 1.65), (27.2, -400, -235, 1.8), (29.9, -390, -235, 1.8), (31.0, -60, -215, 1.55)],
         dof=2.5, scene=3, size='Medium wide', move='Follow pan', action='Bo hops off the pouf, scoots to the standing book and peers around it. Nothing.'),
    Shot('3B', 31.0, 35.0, [(31.0, 300, -215, 2.0), (35.0, 310, -220, 2.08)], dof=3.5, scene=3, size='Medium', move='Slow push',
         action='Bo presses against the floor cushion and stretches to peek over it. Nothing. He deflates.'),
    Shot('3C', 35.0, 40.0, [(35.0, 450, -235, 1.35), (36.9, 760, -245, 1.45), (37.45, 790, -245, 1.45), (37.75, 865, -200, 2.75, 'out3'),
                            (40.0, 865, -204, 2.8)], dof=3.0, scene=3, size='Medium wide -> crash zoom MCU', move='Track, then snap zoom',
         action='Bo rolls to the desk, looks up... BOOP. He freezes. The camera slams in on his frozen face.'),
    Shot('4A', 40.0, 43.5, [(40.0, 1490, -365, 2.1), (43.5, 1478, -360, 2.18)], dof=2.0, scene=4, size='Medium (doorway)', move='Slow push',
         action='Pip peeks around the doorway, spots Bo, wiggles with excitement.'),
    Shot('4B', 43.5, 47.5, [(43.5, 1020, -285, 1.12), (47.5, 820, -255, 1.2)], dof=0.0, scene=4, size='Wide', move='Pan left with action',
         action='Pip bounces across the room, zips past Bo, and bonks the floor cushion out of place.'),
    Shot('4C', 47.5, 51.7, [(47.5, 722, -190, 1.9), (51.7, 722, -195, 1.97)], dof=3.0, scene=4, size='Two-shot', move='Creeping push',
         action='Bo looks at Pip. Pip looks at Bo. Awkward silence. Bo tilts awkwardly... BOOP.'),
    Shot('4D', 51.7, 55.0, [(51.7, 300, -330, 1.0), (55.0, 330, -330, 1.03)], dof=0.0, scene=4, size='Wide', move='Locked off',
         action='Both whip around to stare at the empty left side of the room. Pip bounces; Bo squints.'),
    Shot('5A', 55.0, 58.5, [(55.0, 1250, -320, 1.45), (58.5, 1140, -290, 1.5)], dof=1.5, scene=5, size='Medium wide', move='Pan left',
         action='Mimi bounces in from the hallway and cheerfully joins the investigators.'),
    Shot('5B', 58.5, 62.5, [(58.5, 520, -300, 1.2), (62.5, 480, -285, 1.26)], dof=0.0, scene=5, size='Wide', move='Slow push',
         action='The search fans out. Mimi bounces onto the cushion - pff! - false alarm. Bo listens.'),
    Shot('5C', 62.5, 65.0, [(62.5, 95, -235, 2.1), (65.0, 105, -235, 2.16)], dof=3.0, cblur=5.0, focus={'pip'}, scene=5, size='Medium', move='Slow push',
         action='Pip investigates the book stack, bumps it - bop! - and looks hopefully at the others.'),
    Shot('5D', 65.0, 67.0, [(65.0, 700, -200, 3.0), (67.0, 700, -201, 3.05)], dof=6.0, cblur=7.0, focus={'bo'}, scene=5, size='Close-up', move='Locked off',
         action='Bo, still listening, answers with one slow blink: no.'),
    Shot('5E', 67.0, 70.0, [(67.0, 620, -275, 1.25), (70.0, 640, -275, 1.28)], dof=0.0, scene=5, size='Wide', move='Slow push',
         action='Pip deflates. The trio regroups, puzzled, looking every which way.'),
    Shot('6A', 70.0, 73.0, [(70.0, 1360, -340, 1.55), (73.0, 1330, -310, 1.6)], dof=1.5, scene=6, size='Medium wide', move='Slow push',
         action='Blu arrives with four perfectly even hops, then scans the room in precise steps.'),
    Shot('6B', 73.0, 77.5, [(73.0, 760, -225, 1.45), (77.5, 770, -228, 1.5)], dof=1.5, scene=6, size='Group', move='Slow push',
         action='Bo tilts toward Blu... BOOP. Pip and Mimi look everywhere. Blu only looks at Bo.'),
    Shot('6C', 77.5, 80.0, [(77.5, 1150, -175, 2.9), (80.0, 1150, -178, 3.1)], dof=6.0, cblur=7.0, focus={'blu'}, scene=6, size='Close-up', move='Slow push',
         action="Blu's eyes: Bo... headphones... Bo... headphones. A thoughtful tilt. Idea."),
    Shot('6D', 80.0, 85.0, [(80.0, 760, -225, 1.45), (85.0, 760, -232, 1.56)], dof=1.5, scene=6, size='Group', move='Slow push',
         action='Bo tilts in confusion... BOOP. Everyone freezes. All eyes slowly travel to Bo. His eyes roll up to his own headphones.'),
    Shot('7A', 85.0, 89.5, [(85.0, 1010, -172, 5.6), (89.5, 1010, -172, 6.0)], dof=8.0, cblur=8.0, focus={'bo'}, track=_bo_cup_track, scene=7,
         size='Macro insert', move='Tracking the earcup', action='The earcup presses into the fur... BOOP. The ring flickers. Mystery solved.'),
    Shot('7B', 89.5, 94.5, [(89.5, 880, -190, 2.4), (94.5, 880, -194, 2.5)], dof=4.5, cblur=6.0, focus={'bo'}, scene=7, size='Medium close-up', move='Slow push',
         action='Bo tries it again. BOOP. One more time. BOOP! The orchestra erupts.'),
    Shot('7C', 94.5, 97.0, [(94.5, 760, -240, 1.4), (97.0, 760, -242, 1.43)], dof=1.0, scene=7, size='Group', move='Locked off',
         action='Pip bounces wildly, Mimi glows with delight, Blu gives one satisfied tilt.'),
    Shot('7D', 97.0, 102.0, [(97.0, 880, -195, 3.15), (102.0, 880, -197, 3.35)], dof=6.0, cblur=9.0, focus={'bo'}, scene=7, size='Close-up (to lens)', move='Imperceptible push',
         action='Bo turns and looks straight into the lens. One tiny, embarrassed blink. Hold.'),
    Shot('8A', 102.0, 108.75, [(102.0, 745, -235, 1.36), (108.75, 745, -238, 1.4)], dof=1.0, scene=8, size='Wide group', move='Slow push',
         action='Celebration: Bo bounces, Pip bounces bigger, Mimi joins, all on the beat. Blu stays composed... mostly.'),
    Shot('8B', 108.75, 110.4, [(108.75, 1150, -235, 1.9), (110.4, 1150, -236, 1.93)], dof=3.0, cblur=5.0, focus={'blu'}, scene=8, size='Medium', move='Locked off',
         action='Blu launches one tiny, unexpectedly enthusiastic bounce - then re-composes as if nothing happened.'),
    Shot('8C', 110.4, 113.0, [(110.4, 745, -235, 1.4), (113.0, 745, -235, 1.37)], dof=1.0, scene=8, size='Wide group', move='Slight pull-back',
         action='All four bounce together on the final chord.'),
    Shot('9A', 113.0, 117.5, [(113.0, 900, -250, 1.28), (115.8, 930, -255, 1.28), (117.5, 990, -268, 1.36)], dof=0.5, scene=9, size='Wide',
         move='Hold, then creeping push to the doorway', action='Peace. Then, from the dark hallway: boop. Four heads turn. Silence.'),
    Shot('9B', 117.5, 120.0, [(117.5, 0, 0, 1.0), (120.0, 0, 0, 1.0)], scene=9, size='End card', move='-',
         action='Cut to black. ADVENTURES OF BO / A BOOPMO ORIGINAL. A final tiny boop.'),
]


def shot_at(t):
    for s in SHOTS:
        if s.t0 <= t < s.t1:
            return s
    return SHOTS[-1]


def props_at(t):
    return {k: tr.value(t) for k, tr in PROP.items()}


SCENES = {
    1: ('A Very Quiet Evening', 0.0, 12.0), 2: ('The First Boop', 12.0, 25.0), 3: ('Detective Bo', 25.0, 40.0),
    4: ('Pip Makes an Entrance', 40.0, 55.0), 5: ('The Investigation Grows', 55.0, 70.0), 6: ('Blu Has a Theory', 70.0, 85.0),
    7: ('Mystery Solved', 85.0, 102.0), 8: ('The Celebration', 102.0, 113.0), 9: ('One More Boop', 113.0, 120.0),
}
END_CARD_T = 117.5


def validate():
    """Continuity checks: shot coverage, Bo's tilt rule, boop/tilt agreement."""
    errs = []
    for a, b in zip(SHOTS, SHOTS[1:]):
        if abs(a.t1 - b.t0) > 1e-6:
            errs.append(f'gap/overlap {a.sid}->{b.sid}')
    if SHOTS[0].t0 != 0 or SHOTS[-1].t1 != DUR:
        errs.append('shots do not span 0-120')
    head = sorted(t for t, v in BOOPS if v in ('head', 'room'))
    t = 0.0
    above = False
    crossings = []
    prev = 0.0
    while t < END_CARD_T:
        a = abs(bo.state(t)['tilt'])
        rising = a > prev + 1e-6
        prev = a
        if a >= BOOP_TILT - 0.25 and not above:
            crossings.append(t)
        above = a >= BOOP_TILT - 0.25
        if rising and SAFE_TILT < a < BOOP_TILT - 0.25 and not any(0 <= c - t < 1.0 for c in head):
            errs.append(f'Bo tilt {a:.1f} deg at {t:.2f}s is in the ambiguous zone')
        t += 1 / FPS
    for c in crossings:
        if not any(0 <= b - c < 0.12 for b in head):
            errs.append(f'Bo crosses boop tilt at {c:.2f}s with no boop')
    for b in head:
        if not any(0 <= b - c < 0.12 for c in crossings):
            errs.append(f'boop at {b:.2f}s without a matching tilt')
    return errs


if __name__ == '__main__':
    e = validate()
    print('shots:', len(SHOTS), 'events:', len(EVENTS), 'boops:', len(BOOPS))
    print('\n'.join(e) if e else 'continuity OK')

"""'The Stakeout' - proof sequence animation (19.0 s @ 24 fps).

Keys express intent (anticipation -> action -> overshoot -> settle); a physics
pass then adds body overlap and fur inertia from the actual trajectory.
"""
import math
import numpy as np

FPS = 24
DUR = 19.0
TAIL = 0.75                       # black tail after the cut, for the sound to ring
PI = math.pi
CLOCK = np.array([0.0, 0.42, 0.0])
DIAL = np.array([0.0119, 0.4058, 0.085])   # clock turned 40 deg toward the room
BOOPS = [10.95, 16.0, 18.5]


def _outback(u, s=1.70158):
    return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2


EASE = {'lin': lambda u: u, 'io': lambda u: u * u * (3 - 2 * u), 'in': lambda u: u * u * u,
        'out': lambda u: 1 - (1 - u) ** 3, 'back': _outback, 'io2': lambda u: 0.5 - 0.5 * math.cos(math.pi * u)}


class Track:
    def __init__(self, v0):
        self.v0, self.segs = v0, []

    def to(self, t0, t1, v, e='io'):
        a = self.at(t0)
        self.segs.append((t0, max(t1, t0 + 1e-4), a, v, e))
        self.segs.sort(key=lambda s: s[0])
        return self

    def at(self, t):
        seg = None
        for s in self.segs:
            if s[0] <= t:
                seg = s
        if seg is None:
            return self.v0
        t0, t1, a, b, e = seg
        if t >= t1:
            return b
        return a + (b - a) * EASE[e]((t - t0) / (t1 - t0))


P = dict(x=-0.46, y=-0.40, lift=0.0, heading=math.atan2(0.46, -0.52), sy=0.9, bx=0.0, by=0.0, wx=0.0, gx=0.0, gy=-0.1,
         blinkL=0.0, blinkR=0.0, squintL=0.35, squintR=0.35, widen=0.0, fluff=0.0, breath=1.0, ring=0.6)
T = {k: Track(v) for k, v in P.items()}
STEPS, HOPS, BLINKS, EVENTS, SHIVERS = [], [], [], [], []


def key(t0, t1, e='io', **kv):
    for k, v in kv.items():
        T[k].to(t0, t1, v, e)


def ev(kind, t, **d):
    EVENTS.append((kind, t, d))


# ============================================================ performance
# --- SH1/SH2: the creep (steps land on the 96 BPM beat: 0.625 s) ---------
S = (0.0, 0.12)
path = [(-0.46, -0.40), (-0.37, -0.29), (-0.27, -0.18), (-0.18, -0.08), (-0.10, 0.0), (-0.04, 0.07), S]
beat = 0.625
for i in range(len(path) - 1):
    t0 = 0.10 + i * beat
    x1, y1 = path[i + 1]
    key(t0, t0 + beat * 0.78, 'io', x=x1, y=y1)
    STEPS.append((t0 + beat * 0.78, (-1) ** i, 0.6))
    ev('creep_step', t0 + beat * 0.74, side=(-1) ** i)
key(3.2, 3.65, 'io', heading=PI)                    # squares up to the clock
key(3.55, 3.75, 'out', sy=0.97)
key(3.75, 4.1, 'back', sy=1.0)
ev('arrive', 3.65)
key(3.7, 4.0, 'io', gy=-0.32, gx=0.0, squintL=0.3, squintR=0.3)
BLINKS.append((3.82, 0.16))
# the lean - slow, then impossibly far
key(4.15, 5.35, 'io2', by=-0.105, sy=1.09, bx=0.012, squintL=0.68, squintR=0.42, breath=0.0)
key(4.15, 5.35, 'io2', y=0.135)
ev('lean', 4.15, dur=1.2)
# --- SH3: eye dart ------------------------------------------------------
key(7.15, 7.24, 'out', gx=-0.32)
key(7.62, 7.72, 'out', gx=0.05)
ev('dart', 7.15)
ev('dart', 7.62)
# --- SH4: nothing. deflate, turn away, shuffle --------------------------
key(8.45, 8.95, 'io', by=0.0, bx=0.0, y=0.12, sy=0.97, squintL=0.12, squintR=0.12, gy=-0.15)
key(8.95, 9.35, 'io', sy=0.88, breath=0.6, gy=-0.42)
ev('sigh', 8.95)
BLINKS.append((9.0, 0.32))
key(9.15, 9.28, 'io', heading=PI - 0.1)
key(9.28, 9.9, 'io', heading=2 * PI)
ev('turn', 9.3)
for i, (t0, yy) in enumerate([(9.95, 0.07), (10.38, 0.0), (10.78, -0.05)]):
    key(t0, t0 + 0.34, 'io', y=yy)
    STEPS.append((t0 + 0.34, (-1) ** i, 0.35))
    ev('shuffle_step', t0 + 0.3)
# --- SH5: BOOP #1 (10.95): freeze mid-step, eyes slide back --------------
tb = BOOPS[0]
key(tb + 0.02, tb + 0.08, 'out', sy=0.84, widen=0.35, fluff=0.22, gy=0.0)
key(tb + 0.08, tb + 0.3, 'io', fluff=0.12)
key(11.22, 11.5, 'io', gx=0.75)
key(11.3, 11.55, 'io', heading=2 * PI + 0.16)
# --- SH6: whip-turn ------------------------------------------------------
key(11.72, 11.84, 'io', heading=2 * PI + 0.16 - 0.28, sy=0.8, gx=0.4)
key(11.84, 12.06, 'io', heading=3 * PI + 0.14)
key(11.84, 11.95, 'out', sy=1.14)
key(12.06, 12.36, 'back', heading=3 * PI)
key(12.06, 12.12, 'out', sy=0.78)
key(12.12, 12.5, 'back', sy=0.9)
key(12.1, 12.35, 'io', gx=0.0, gy=-0.18, squintL=0.55, squintR=0.55, widen=0.0, fluff=0.05)
HOPS.append((11.86, 12.06, 0.03, False))
ev('whip', 11.84)
ev('skid', 12.06)
BLINKS.append((12.38, 0.12))
BLINKS.append((12.56, 0.12))
# --- SH7: standoff ------------------------------------------------------
key(12.9, 13.4, 'io', squintL=0.72, squintR=0.68, by=-0.03)
key(13.45, 13.6, 'out', squintL=0.78, squintR=0.6)
# --- SH8: back away... BOOP #2 -> startle leap, fur bristles ---------------
for i, (t0, yy) in enumerate([(14.85, -0.11), (15.35, -0.17), (15.82, -0.22)]):
    key(t0, t0 + 0.36, 'io', y=yy)
    STEPS.append((t0 + 0.36, (-1) ** i, 0.5))
    ev('back_step', t0 + 0.33)
key(14.8, 15.0, 'io', by=0.0, gy=-0.22)
tb2 = BOOPS[1]
HOPS.append((tb2 + 0.03, tb2 + 0.47, 0.135, True))
key(tb2 + 0.02, tb2 + 0.12, 'out', fluff=1.0, widen=1.0, squintL=0.0, squintR=0.0, gy=0.15)
ev('startle', tb2 + 0.03)
ev('land_big', tb2 + 0.47)
SHIVERS.append((tb2 + 0.5, 1.2, 0.006))
# --- SH9: fur settles; eyes to camera; ring blinks: BOOP #3 ---------------
key(17.35, 18.55, 'out', fluff=0.0, widen=0.15, breath=0.7)
key(17.45, 17.75, 'io', gx=0.18, gy=-0.2)
BLINKS.append((17.82, 0.3))
key(17.95, 18.25, 'io', gx=0.0, gy=0.04, squintL=0.12, squintR=0.12)
ev('fur_settle', 17.4)
tb3 = BOOPS[2]
key(tb3 + 0.14, tb3 + 0.32, 'io', gx=0.62, gy=0.02)
key(tb3 + 0.14, tb3 + 0.32, 'io', squintL=0.25, squintR=0.18)
ev('eye_slide', tb3 + 0.14)


# ============================================================ evaluation
def hop_layer(t):
    lift, sq = 0.0, 1.0
    for (t0, t1, h, startle) in HOPS:
        pre = 0.0 if startle else 0.1
        if t0 - pre <= t < t0 and pre:
            q = math.sin((t - (t0 - pre)) / pre * PI / 2)
            sq *= 1 - 0.12 * q
        elif t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            lift += 4 * h * u * (1 - u)
            a = (0.32 if startle else 0.12) * (1 - u) ** 2 + 0.05 * u ** 3
            sq *= 1 + a
        elif t1 <= t < t1 + 0.6:
            d = t - t1
            amp = 0.26 if startle else 0.14
            sq *= 1 - amp * math.exp(-d / 0.1) * math.cos(2 * PI * d / 0.3)
    return lift, sq


def step_layer(t):
    """Creep weight-shift: side sway, squash dip on each footfall."""
    wx = bx = 0.0
    sq = 1.0
    for (ts, side, amt) in STEPS:
        d = t - ts
        if -0.45 < d < 0.4:
            k = math.exp(-((d + 0.2) / 0.17) ** 2)
            wx += side * 0.05 * amt * k
            bx += side * 0.016 * amt * k
        if 0 <= d < 0.35:
            sq *= 1 - 0.06 * amt * math.exp(-d / 0.08) * math.cos(2 * PI * d / 0.3)
    return wx, bx, sq


def blink_layer(t):
    b = 0.0
    for (bt, dur) in BLINKS:
        if bt <= t < bt + dur:
            u = (t - bt) / dur
            b = max(b, u / 0.35 if u < 0.35 else 1 - (u - 0.35) / 0.65)
    return min(1.0, b)


def keyed(t):
    st = {k: tr.at(t) for k, tr in T.items()}
    hl, hs = hop_layer(t)
    wx, bx, ss = step_layer(t)
    st['lift'] += hl
    st['sy'] *= hs * ss * (1 + 0.012 * st['breath'] * math.sin(2 * PI * t / 2.7))
    st['wx'] += wx
    st['bx'] += bx
    return st


# physics pass ------------------------------------------------------------
DT = 1 / 480
_ts = np.arange(-0.5, DUR + TAIL + 0.5, DT)
_pos = np.array([[keyed(t)['x'], keyed(t)['y'], keyed(t)['lift']] for t in _ts])
_hd = np.array([keyed(t)['heading'] for t in _ts])
_vel = np.gradient(_pos, DT, axis=0)
_acc = np.gradient(_vel, DT, axis=0)
_om = np.gradient(_hd, DT)
_al = np.gradient(_om, DT)


def _spring(force, f, z):
    k, c = (2 * PI * f) ** 2, 2 * z * (2 * PI * f)
    x = np.zeros_like(force)
    v = np.zeros_like(force[0])
    xx = np.zeros_like(force[0])
    for i in range(len(force)):
        a = -k * xx - c * v - force[i]
        v = v + a * DT
        xx = xx + v * DT
        x[i] = xx
    return x


_lag = _spring(np.clip(_acc, -40, 40), 3.0, 0.42) * 4.0          # body overlap (m at top)
_fur = _spring(np.clip(_acc, -60, 60), 5.5, 0.3) * 3.2           # fur inertia
_spl = _spring(np.clip(_al, -400, 400)[:, None], 4.5, 0.35)[:, 0] * 0.3
_oms = np.convolve(_om, np.ones(24) / 24, mode='same')


def _interp(arr, t):
    i = (t - _ts[0]) / DT
    i0 = int(np.clip(math.floor(i), 0, len(_ts) - 2))
    f = i - i0
    return arr[i0] * (1 - f) + arr[i0 + 1] * f


def state(t):
    st = keyed(t)
    lag = _interp(_lag, t)
    h = st['heading']
    c, s_ = math.cos(-h), math.sin(-h)
    st['bx'] += c * lag[0] - s_ * lag[1]
    st['by'] += s_ * lag[0] + c * lag[1]
    st['sy'] *= 1 + float(np.clip(lag[2] * 1.5, -0.12, 0.12))
    fd = _interp(_fur, t)
    for (t0, dur, amp) in SHIVERS:
        if t0 <= t < t0 + dur:
            k = (1 - (t - t0) / dur)
            fd = fd + amp * k * np.array([math.sin(t * 61), math.sin(t * 53 + 1), math.sin(t * 47 + 2) * 0.5])
    st['fur_dyn'] = fd
    st['omega'] = float(_interp(_oms, t))
    st['spinlag'] = float(_interp(_spl, t))
    st['blinkL'] = st['blinkR'] = blink_layer(t)
    ring = 0.6
    for tb in BOOPS:
        if t >= tb:
            ring = max(ring, 0.6 + 11.0 * math.exp(-(t - tb) / 0.12))
    st['ring'] = ring
    return st


def clock_second_angle(t):
    """Second hand: one tick per second with a tiny overshoot (radians, clockwise)."""
    s = math.floor(t)
    frac = t - s
    base = (s + 17) * 2 * PI / 60
    over = 0.0
    if frac < 0.12:
        over = (2 * PI / 60) * (-(1 - frac / 0.12)) + 0.012 * math.sin(frac / 0.12 * PI) * 0.0
        over = -(2 * PI / 60) * (1 - EASE['back'](frac / 0.12))
    return base + over


# ============================================================ cameras
def _bo_center(t, dz=0.13):
    st = state(t)
    return np.array([st['x'], st['y'], st['lift'] + dz])


def _bo_eye(t, side=-1):
    from rig import Character  # noqa: F401 (eye position is computed by render loop)
    return None


class Shot:
    def __init__(self, sid, t0, t1, fn, lens, fstop, focus, roll=0.0, desc=''):
        self.sid, self.t0, self.t1, self.fn, self.lens, self.fstop, self.focus, self.roll, self.desc = sid, t0, t1, fn, lens, fstop, focus, roll, desc


def lerp(a, b, u):
    return np.asarray(a) + (np.asarray(b) - np.asarray(a)) * u


def sm(t, t0, t1):
    u = min(1, max(0, (t - t0) / (t1 - t0)))
    return u * u * (3 - 2 * u)


def handheld(t, amp=0.0012):
    return np.array([math.sin(t * 1.3) + 0.5 * math.sin(t * 2.9 + 1), math.sin(t * 1.1 + 2) + 0.4 * math.sin(t * 3.7), math.sin(t * 0.9 + 4)]) * amp


def sh1(t):
    u = sm(t, 0, 3.0)
    loc = lerp((0.25, 0.68, 0.05), (0.205, 0.59, 0.056), u) + handheld(t, 0.001)
    tgt = _bo_center(t, 0.11) * 0.85 + np.array([-0.05, 0.05, 0.11]) * 0.15
    return loc, tgt


def sh2(t):
    u = sm(t, 3.0, 6.25)
    loc = lerp((0.82, 0.22, 0.125), (0.70, 0.225, 0.13), u) + handheld(t, 0.0006)
    tgt = lerp((0.0, 0.22, 0.13), (0.0, 0.27, 0.135), u)
    return loc, tgt


def sh3(t):
    u = sm(t, 6.25, 8.25)
    loc = lerp((0.092, 0.392, 0.168), (0.084, 0.387, 0.169), u)
    return loc, None          # target = Bo's left eye (resolved in render loop)


def sh4(t):
    u = sm(t, 8.25, 10.75)
    loc = lerp((0.40, 0.66, 0.12), (0.36, 0.62, 0.125), u) + handheld(t, 0.0008)
    c = _bo_center(t, 0.12)
    return loc, c


def sh5(t):
    loc = np.array([-0.04, -0.64, 0.13]) + handheld(t, 0.0006)
    return loc, _bo_center(t, 0.14) * 0.7 + np.array([0, -0.05, 0.14]) * 0.3


def sh6(t):
    loc = np.array([0.74, -0.12, 0.12])
    c = _bo_center(t, 0.13)
    # whip: the operator overshoots the snap, then settles
    w = math.exp(-max(0, t - 11.9) / 0.12) * math.sin(max(0, t - 11.84) * 40) * 0.035 if t > 11.84 else 0
    return loc, c + np.array([0, w, 0])


def sh7a(t):
    loc = np.array([0.055, 0.30, 0.055])
    return loc, None


def sh7b(t):
    u = sm(t, 13.75, 14.75)
    loc = lerp((-0.105, -0.02, 0.135), (-0.098, 0.0, 0.133), u)
    return loc, DIAL


def sh8(t):
    loc = np.array([0.98, -0.30, 0.115]) + handheld(t, 0.0008)
    tgt = np.array([0.0, 0.07, 0.19])
    return loc, tgt


def sh9(t):
    u = sm(t, 17.25, 19.0)
    loc = lerp((0.115, 0.76, 0.245), (0.108, 0.70, 0.243), u)
    return loc, None


SHOTS = [
    Shot('1', 0.0, 3.0, sh1, 28, 2.0, 'bo', desc='Floor-level wide behind the clock: Bo creeps in on the beat'),
    Shot('2', 3.0, 6.25, sh2, 35, 4.0, 'mid', desc='Profile: arrival, then the impossibly long lean'),
    Shot('3', 6.25, 8.25, sh3, 100, 4.5, 'eyeL', desc='ECU: the clock reflected in Bo\'s eye; one dart'),
    Shot('4', 8.25, 10.75, sh4, 35, 2.8, 'bo', desc='Nothing. Deflate, turn away, dejected shuffle'),
    Shot('5', 10.75, 11.75, sh5, 50, 2.8, 'bo', desc='BOOP. Freeze. Eyes slide back'),
    Shot('6', 11.75, 12.75, sh6, 35, 3.5, 'bo', desc='Whip-turn: fur flares, crouched landing'),
    Shot('7a', 12.75, 13.75, sh7a, 85, 3.2, 'eyes', roll=-5, desc='Standoff: Bo\'s narrowed eyes, low angle'),
    Shot('7b', 13.75, 14.75, sh7b, 85, 4.0, 'dial', roll=8, desc='Standoff: the clock, innocent, dutch angle'),
    Shot('8', 14.75, 17.25, sh8, 28, 4.0, 'bo', desc='Backing away... BOOP: startle leap, fur bristles'),
    Shot('9', 17.25, 19.0, sh9, 85, 2.8, 'eyes', desc='Deadpan to camera. The ring blinks. BOOP.'),
]


def shot_at(t):
    for s in SHOTS:
        if s.t0 <= t < s.t1:
            return s
    return SHOTS[-1]


# solved camera specs (tune_cams.py) override the hand-placed functions
import json as _json, os as _os
_CP = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'out', 'cams.json')
CAMS = _json.load(open(_CP)) if _os.path.exists(_CP) else {}
HANDHELD = {'1': 0.0010, '2': 0.0006, '3': 0.00015, '4': 0.0008, '5': 0.0006, '6': 0.0, '7a': 0.0002, '7b': 0.0003, '8': 0.0008, '9': 0.0003}
for _s in SHOTS:
    _s.spec = CAMS.get(_s.sid)

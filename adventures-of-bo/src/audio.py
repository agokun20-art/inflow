"""Adventures of Bo - Ep.1 original score, signature boop and sound design.

Everything is synthesized from first principles (no samples, no third-party
music).  Cue timing is read from timeline.py, so picture and sound share one
clock.  Outputs (48 kHz / 24-bit WAV):
  output/audio/mix_stereo.wav           final mix, -16 LUFS integrated, <= -1 dBTP
  output/audio/stem_music.wav           M&E stems for the final conform
  output/audio/stem_sfx.wav
  output/audio/stem_boops.wav
  output/audio/stem_ambience.wav
  output/audio/boop_signature*.wav      the series' signature boop + variants
"""
import math
import os
import sys

import numpy as np
from scipy.signal import butter, sosfilt, lfilter, oaconvolve

sys.path.insert(0, os.path.dirname(__file__))
import timeline as TL  # noqa: E402

SR = 48000
LEN = TL.DUR + 0.25
NS = int(SR * LEN)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AOUT = os.path.join(ROOT, 'output', 'audio')
RNG = np.random.default_rng(2026)


# --------------------------------------------------------------------------
# DSP helpers
# --------------------------------------------------------------------------
def tv(d):
    return np.arange(int(round(max(d, 0.001) * SR))) / SR


def _sos(kind, f, order=2):
    return butter(order, f, kind, fs=SR, output='sos')


def lp(x, f, o=2):
    return sosfilt(_sos('lowpass', min(f, SR / 2 - 100), o), x)


def hp(x, f, o=2):
    return sosfilt(_sos('highpass', f, o), x)


def bp(x, lo, hi, o=2):
    return sosfilt(_sos('bandpass', [lo, min(hi, SR / 2 - 100)], o), x)


def noise(d):
    return RNG.uniform(-1, 1, int(round(d * SR)))


def fades(x, a=0.002, r=0.008):
    n = len(x)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nr:
        x[-nr:] *= np.linspace(1, 0, nr)
    return x


def smoothstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


NOTE_IDX = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(name):
    n = NOTE_IDX[name[0]]
    i = 1
    while i < len(name) and name[i] in '#b':
        n += 1 if name[i] == '#' else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def hz(n):
    m = midi(n) if isinstance(n, str) else n
    return 440.0 * 2 ** ((m - 69) / 12)


class Bus:
    def __init__(self):
        self.y = np.zeros((2, NS), np.float64)

    def add(self, sig, t, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            a = (pan + 1) * math.pi / 4
            sig = np.vstack([sig * math.cos(a), sig * math.sin(a)]) * math.sqrt(2)
        i = int(round(t * SR))
        if i >= NS or i + sig.shape[1] <= 0:
            return
        j0 = max(0, -i)
        n = min(sig.shape[1] - j0, NS - max(i, 0))
        self.y[:, max(i, 0):max(i, 0) + n] += gain * sig[:, j0:j0 + n]


def make_ir(rt60, pre=0.012, bright=6000, dark=1800, width=1.0, seed=1):
    rng = np.random.default_rng(seed)
    n = int(rt60 * 1.2 * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        x = rng.normal(0, 1, n) * np.exp(-t * 6.9 / rt60)
        b = lp(x, bright)
        d = lp(x, dark)
        w = np.clip(t / rt60, 0, 1)
        y = b * (1 - w) + d * w
        y = np.concatenate([np.zeros(int(pre * SR)), y])
        out.append(y)
    ir = np.vstack(out)
    mid = ir.mean(0, keepdims=True)
    ir = mid + (ir - mid) * width
    return ir / np.sqrt((ir ** 2).sum() / 2)


IR_HALL = make_ir(2.1, pre=0.018, bright=7000, dark=2200, seed=3)
IR_ROOM = make_ir(0.55, pre=0.006, bright=6500, dark=2600, seed=5)
IR_HALLWAY = make_ir(1.25, pre=0.02, bright=2600, dark=900, seed=8)


def reverb(y, ir, wet):
    out = np.zeros_like(y)
    for c in range(2):
        out[c] = oaconvolve(y[c], ir[c], mode='full')[:y.shape[1]]
    return y + wet * out


# --------------------------------------------------------------------------
# Instruments (mono, normalized-ish)
# --------------------------------------------------------------------------
def ks_string(f, d, g=0.996, bright=0.55, tau=None, seed=0):
    n = int(d * SR)
    P = SR / f
    p = int(P - 0.6)
    dd = P - 0.5 - p
    c = (1 - dd) / (1 + dd)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    burst = lfilter([bright], [1, -(1 - bright)], rng.uniform(-1, 1, p))
    x[:p] = burst - burst.mean()
    a = np.zeros(p + 3)
    a[0] = 1
    a[1] = c
    a[p] += -0.5 * g * c
    a[p + 1] += -0.5 * g * (1 + c)
    a[p + 2] += -0.5 * g
    y = lfilter([1, c], a, x)
    if tau:
        y *= np.exp(-np.arange(n) / SR / tau)
    return y / (np.abs(y).max() + 1e-9)


def pizz(f, dur, vel):
    tau = 0.10 + 0.22 * (220 / max(f, 60)) ** 0.5
    y = ks_string(f, max(0.35, tau * 4), g=0.997, bright=0.45, tau=tau, seed=int(f))
    body = bp(y, 180, 1800) * 0.6 + y * 0.5
    return fades(body * vel * 1.2)


def celesta(f, dur, vel):
    t = tv(min(2.6, max(dur, 1.0) + 0.9))
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t / 1.0) + 0.30 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.32)
         + 0.10 * np.sin(2 * np.pi * 3.0 * f * t) * np.exp(-t / 0.16) + 0.05 * np.sin(2 * np.pi * 4.1 * f * t) * np.exp(-t / 0.08))
    y += 0.04 * lp(noise(len(t) / SR), 3000) * np.exp(-t / 0.004)
    return fades(y * vel * 0.32, 0.0015, 0.05)


def glock(f, dur, vel):
    t = tv(2.0)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.3) \
        + 0.15 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / 0.12)
    return fades(y * vel * 0.18, 0.001, 0.05)


def marimba(f, dur, vel):
    t = tv(1.0)
    dec = 0.42 * (440 / f) ** 0.35
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.30 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.05) \
        + 0.08 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t / 0.015)
    y += 0.08 * lp(noise(1.0), 2200) * np.exp(-t / 0.003)
    return fades(y * vel * 0.42, 0.001, 0.05)


def pluck_synth(f, dur, vel):
    t = tv(0.55)
    y = np.zeros_like(t)
    K = max(1, min(18, int(9000 / f)))
    for k in range(1, K + 1):
        y += (1 / k) * np.sin(2 * np.pi * k * f * t + RNG.uniform(0, 6.28)) * np.exp(-t * (4 + 2.6 * k))
    return fades(y * vel * 0.42, 0.002, 0.04)


def additive(f, t, amps, phase=None):
    ph = 2 * np.pi * np.cumsum(f) / SR if phase is None else phase
    return sum(a * np.sin(k * ph) for k, a in amps if a)


def flute(f, dur, vel):
    t = tv(dur + 0.18)
    vib = 1 + 0.0045 * np.sin(2 * np.pi * 5.1 * t) * smoothstep(0.15, 0.5, t)
    y = additive(f * vib, t, [(1, 1.0), (2, 0.26), (3, 0.09), (4, 0.035)])
    y += 0.05 * bp(noise(len(t) / SR), f * 1.5, min(f * 6, 16000)) * (0.5 + 0.5 * smoothstep(0, 0.08, t))
    env = smoothstep(0, 0.055, t) * (1 - smoothstep(dur, dur + 0.16, t))
    return fades(y * env * vel * 0.30)


def clarinet(f, dur, vel):
    t = tv(dur + 0.12)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5.4 * t) * smoothstep(0.2, 0.5, t)
    y = additive(f * vib, t, [(1, 1.0), (2, 0.05), (3, 0.45), (4, 0.04), (5, 0.24), (7, 0.12), (9, 0.05)])
    y = lp(y, 3200)
    y += 0.025 * bp(noise(len(t) / SR), 1200, 5000)
    env = smoothstep(0, 0.035, t) * (1 - smoothstep(dur, dur + 0.1, t))
    return fades(y * env * vel * 0.26)


def pad(freqs, dur, vel, attack=0.6, release=1.0, bright=2200, trem=0.0):
    t = tv(dur + release)
    y = np.zeros_like(t)
    for f in freqs:
        for det in (-0.0042, 0.0, 0.0047):
            ph0 = RNG.uniform(0, 6.28, 12)
            for k in range(1, 11):
                if k * f > 9000:
                    break
                y += (1 / k ** 1.35) * np.sin(2 * np.pi * k * f * (1 + det) * t + ph0[k - 1])
    y = lp(y, bright)
    env = smoothstep(0, attack, t) * (1 - smoothstep(dur, dur + release, t))
    if trem:
        env *= 1 - trem * 0.5 * (1 + np.sin(2 * np.pi * 12.5 * t))
    return fades(y * env * vel * 0.095 / max(1, len(freqs)) ** 0.5)


def stab(freqs, vel):
    t = tv(1.4)
    y = np.zeros_like(t)
    for f in freqs:
        for det in (-0.003, 0.003):
            K = max(1, min(30, int(7000 / f)))
            for k in range(1, K + 1):
                y += (1 / k) * np.sin(2 * np.pi * k * f * (1 + det) * t) * np.exp(-t * (2.2 + 0.9 * k))
    y = lp(y, 5000) * (smoothstep(0, 0.012, t))
    return fades(y * vel * 0.24 / len(freqs) ** 0.5)


def timpani(f, vel, d=2.4):
    t = tv(d)
    fr = f * (1 + 0.03 * np.exp(-t / 0.08))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) * np.exp(-t / 1.1) + 0.45 * np.sin(1.5 * ph) * np.exp(-t / 0.45) + 0.25 * np.sin(1.99 * ph) * np.exp(-t / 0.35) \
        + 0.12 * np.sin(2.44 * ph) * np.exp(-t / 0.25)
    y += 0.5 * lp(noise(d), 700) * np.exp(-t / 0.018)
    return fades(y * vel * 0.3, 0.001, 0.1)


def kick(vel):
    t = tv(0.4)
    f = 48 + 75 * np.exp(-t / 0.035)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    return fades(y * vel * 0.33, 0.0005, 0.05)


def brush(vel, d=0.16):
    t = tv(d + 0.05)
    y = bp(noise(len(t) / SR), 900, 7000) * np.exp(-t / (d * 0.45)) + 0.25 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    return fades(y * vel * 0.5)


def shaker(vel):
    t = tv(0.08)
    y = hp(noise(0.08), 5500) * np.exp(-((t - 0.015) / 0.012) ** 2)
    return fades(y * vel * 0.19)


def woodblock(f, vel):
    t = tv(0.12)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.025) + 0.4 * np.sin(2 * np.pi * 2.7 * f * t) * np.exp(-t / 0.012)
    return fades(y * vel * 0.4, 0.0005, 0.02)


def cymbal(vel, d=2.6, swell=False):
    t = tv(d)
    y = hp(noise(d), 3500) + 0.3 * bp(noise(d), 6000, 12000)
    env = (smoothstep(0, d, t) ** 2 * (1 - smoothstep(d - 0.05, d, t))) if swell else np.exp(-t / (d * 0.33))
    return fades(lp(y, 11000) * env * vel * 0.16, 0.001, 0.05)


def triangle(vel):
    t = tv(1.6)
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(4200, 1), (6650, 0.6), (9100, 0.3)]) * np.exp(-t / 0.6)
    return fades(y * vel * 0.05, 0.001, 0.05)


def slide_whistle(t0f, t1f, d, vel):
    t = tv(d)
    up = d * 0.58
    f = np.where(t < up, t0f + (t1f - t0f) * smoothstep(0, up, t), t1f + (t0f * 1.15 - t1f) * smoothstep(up, d, t))
    f = f * (1 + 0.006 * np.sin(2 * np.pi * 6 * t))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.06 * bp(noise(d), 1500, 6000)
    return fades(y * smoothstep(0, 0.03, t) * vel * 0.16, 0.003, 0.03)


def roll(bus, t0, t1, inst_fn, rate=16, v0=0.1, v1=0.8, pan=0.0):
    t = t0
    while t < t1:
        u = (t - t0) / (t1 - t0)
        bus.add(inst_fn(v0 + (v1 - v0) * u * u), t + RNG.uniform(-0.004, 0.004), pan=pan)
        t += 1 / rate


# --------------------------------------------------------------------------
# Signature boop
# --------------------------------------------------------------------------
def boop(f0=hz('D5'), d=0.165, bright=1.0, seed=0):
    """The Boopmo signature boop: a soft 'b' onset, a rounded pitched 'oo' body
    with a tiny rise-and-settle contour, and a gentle 'p' closure."""
    rng = np.random.default_rng(seed)
    t = tv(d + 0.03)
    f = f0 * (1 - 0.15 * np.exp(-t / 0.011) + 0.035 * np.exp(-((t - 0.03) / 0.018) ** 2) - 0.035 * smoothstep(0.09, d, t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) + 0.22 * np.sin(2 * ph + 0.3) + 0.055 * np.sin(3 * ph) + 0.025 * np.sin(4 * ph)
    body *= 1 + 0.03 * np.sin(2 * np.pi * 32 * t)            # plush wobble
    env = smoothstep(0, 0.006, t) * (1.0 - 0.18 * smoothstep(0.03, d - 0.02, t)) * (1 - smoothstep(d - 0.014, d, t))
    y = body * env
    b_on = lp(rng.uniform(-1, 1, len(t)), 1400) * np.exp(-t / 0.004) * 0.25 + 0.3 * np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.012)
    y += b_on
    pop = np.zeros_like(t)
    i = int((d - 0.004) * SR)
    k = int(0.003 * SR)
    pop[i:i + k] = lp(rng.uniform(-1, 1, k), 2000) * np.hanning(k)
    y += 0.12 * pop
    y = lp(y, 5200 * bright)
    return fades(y / np.abs(y).max(), 0.0005, 0.01)


def boop_variant(v):
    if v == 'outside':
        return lp(boop(hz('A4'), d=0.2, bright=0.6, seed=4), 2400) * 0.28
    if v == 'tiny':
        return boop(hz('A5'), d=0.11, seed=2) * 0.7
    y = boop()
    if v in ('head', 'room'):
        pre = np.zeros(int(0.03 * SR))
        fab = bp(noise(0.07), 2000, 6500) * np.hanning(int(0.07 * SR)) * 0.05
        y = np.concatenate([pre, y])
        y[:len(fab)] += fab
    return y * (0.7 if v == 'room' else 1.0)


# --------------------------------------------------------------------------
# Score
# --------------------------------------------------------------------------
class Music:
    def __init__(self):
        self.dry = Bus()

    def n(self, fn, t, note, dur=0.5, vel=0.7, pan=0.0):
        f = hz(note)
        self.dry.add(fn(f, dur, vel), t, pan=pan)

    def chord(self, t, notes, dur, vel=0.6, pan=0.0, **kw):
        self.dry.add(pad([hz(n) for n in notes], dur, vel, **kw), t, pan=pan)

    def perc(self, t, sig, pan=0.0, gain=1.0):
        self.dry.add(sig, t, pan=pan, gain=gain)


def compose():
    M = Music()
    P = dict(cel=0.15, pizz=-0.2, bass=-0.1, mar=0.25, fl=0.1, cl=-0.3, pad=0.0, pl=0.3)

    # ---- Cue 1 "Bo's Room" 0-12 (F major, 80 BPM) ------------------------
    b = 0.75
    for t0, ch, d in [(0.0, ['F3', 'A3', 'C4', 'E4'], 3.0), (3.0, ['D3', 'F3', 'A3', 'C4'], 3.0),
                      (6.0, ['G3', 'Bb3', 'D4', 'F4'], 3.0), (9.0, ['C3', 'G3', 'Bb3', 'E4'], 1.5), (10.5, ['F3', 'A3', 'C4'], 1.2)]:
        M.chord(t0, ch, d, 0.55, attack=0.9 if t0 == 0 else 0.4, release=1.4)
    for t0, nt in [(0.0, 'F2'), (1.5, 'C3'), (3.0, 'D2'), (4.5, 'A2'), (6.0, 'G2'), (7.5, 'D3'), (9.0, 'C2'), (9.75, 'C3'), (10.5, 'F2')]:
        M.n(pizz, t0, nt, 0.5, 0.45, P['bass'])
    for t0, nt, d in [(3.0, 'A4', b), (3.75, 'C5', b), (4.5, 'F5', 1.1), (5.625, 'E5', 0.37), (6.0, 'D5', b), (6.75, 'C5', b),
                      (7.5, 'A4', 1.5), (9.0, 'Bb4', b), (9.75, 'G4', b), (10.5, 'A4', 1.6)]:
        M.n(celesta, t0, nt, d, 0.55, P['cel'])
    M.n(celesta, 10.5, 'F5', 1.6, 0.25, P['cel'])
    M.n(flute, 6.0, 'F4', 2.6, 0.18, P['fl'])
    M.n(flute, 9.0, 'E4', 1.4, 0.16, P['fl'])

    # ---- Cue 2 mystery motif 19.5-25 (D minor) ---------------------------
    for t0, nt in [(19.5, 'D3'), (20.1, 'A2'), (20.7, 'D3'), (21.3, 'A2'), (21.9, 'Bb2'), (22.5, 'A2'), (23.1, 'D3')]:
        M.n(pizz, t0, nt, 0.4, 0.42, P['bass'])
    M.n(celesta, 19.8, 'A5', 0.5, 0.35, P['cel'])
    M.n(celesta, 20.4, 'F5', 1.0, 0.32, P['cel'])
    M.n(celesta, 21.6, 'A5', 0.5, 0.3, P['cel'])
    M.n(celesta, 22.2, 'E5', 1.0, 0.3, P['cel'])
    for i, nt in enumerate(['D4', 'E4', 'F4', 'G#4', 'A4']):
        M.n(clarinet, 21.9 + 0.3 * i, nt, 0.18 if i < 4 else 0.4, 0.5, P['cl'])
    M.n(pizz, 23.55, 'D3', 0.4, 0.8, P['pizz'])
    M.n(pizz, 23.55, 'D4', 0.4, 0.6, P['pizz'])
    M.perc(23.55, woodblock(900, 0.6), 0.2)
    M.chord(24.0, ['A3', 'E4'], 1.2, 0.35, attack=0.4, release=0.5, bright=3000, trem=0.6)

    # ---- Cue 3 Detective Bo 25-40 (D minor, 120 BPM) ---------------------
    def tiptoe(t0, bass, upper, brushes=(), shake=None, vel=0.5):
        for t, nt in bass:
            M.n(pizz, t, nt, 0.3, vel, P['bass'])
        for t, nt in upper:
            M.n(clarinet, t, nt, 0.13, vel * 0.9, P['cl'])
        for t in brushes:
            M.perc(t, brush(vel * 0.5), 0.1)
        if shake:
            t = shake[0]
            while t < shake[1]:
                M.perc(t, shaker(vel * 0.6), 0.35)
                t += 0.25
    tiptoe(25.0, [(25.0, 'D2'), (25.5, 'A2'), (26.0, 'D2'), (26.5, 'A2'), (27.0, 'F2'), (27.5, 'A2')],
           [(25.25, 'F4'), (25.75, 'E4'), (26.25, 'D4'), (26.75, 'E4'), (27.25, 'F4'), (27.5, 'G4'), (27.75, 'G#4')],
           brushes=(25.5, 26.5, 27.5), shake=(25.0, 28.0))
    M.chord(28.0, ['A4', 'D5'], 1.15, 0.28, attack=0.15, release=0.3, bright=3500, trem=0.7)
    M.n(pizz, 29.25, 'A3', 0.3, 0.75, P['pizz'])
    M.n(pizz, 29.55, 'D3', 0.3, 0.75, P['pizz'])
    tiptoe(29.9, [(29.9, 'D2'), (30.45, 'F3'), (31.05, 'A3'), (31.5, 'D2'), (32.0, 'A2')],
           [(30.15, 'F4'), (30.65, 'E4'), (31.15, 'D4'), (31.6, 'F4'), (31.85, 'G4'), (32.1, 'A4')], brushes=(30.5, 31.5), shake=(29.9, 32.2))
    M.chord(32.3, ['A4', 'D5'], 1.0, 0.25, attack=0.15, release=0.3, bright=3500, trem=0.7)
    M.n(clarinet, 33.55, 'A4', 0.18, 0.55, P['cl'])
    M.n(clarinet, 33.75, 'F4', 0.18, 0.5, P['cl'])
    M.n(clarinet, 33.95, 'D4', 0.6, 0.5, P['cl'])
    M.n(pizz, 33.95, 'D2', 0.4, 0.5, P['bass'])
    tiptoe(35.0, [(35.0, 'D2'), (35.5, 'A2'), (36.0, 'D2'), (36.5, 'A2'), (37.0, 'Bb2')],
           [(35.25, 'F4'), (35.75, 'G4'), (36.25, 'A4'), (36.75, 'Bb4')], brushes=(35.5, 36.5), shake=(35.0, 37.0), vel=0.6)
    tdun = 37.45
    M.perc(tdun, stab([hz(n) for n in ['D2', 'A2', 'D3', 'F3', 'Bb3']], 0.8), 0.0)
    M.perc(tdun, timpani(hz('D2'), 0.65), -0.1)
    M.perc(tdun, cymbal(0.6, 2.2), 0.2)
    M.chord(tdun + 0.05, ['D3', 'F3', 'Bb3'], 1.6, 0.6, attack=0.02, release=0.8, bright=3000, trem=0.65)

    # ---- Cue 4 Pip 40-47 ---------------------------------------------------
    for t0, nt in [(40.45, 'G5'), (40.75, 'A5'), (41.35, 'C6')]:
        M.n(pluck_synth, t0, nt, 0.3, 0.45, P['pl'])
    for i, nt in enumerate(['C5', 'E5', 'G5', 'C6']):
        M.n(marimba, 42.2 + 0.05 * i, nt, 0.2, 0.55, P['mar'])
    for i in range(12):
        M.n(marimba, 42.6 + 0.035 * i, 'C6' if i % 2 == 0 else 'D6', 0.1, 0.32, P['mar'])
    for t0, nt, bn in [(44.15, 'C5', 'C3'), (44.75, 'E5', 'E3'), (45.35, 'G5', 'G3'), (45.95, 'B5', 'G2')]:
        M.n(marimba, t0, nt, 0.3, 0.6, P['mar'])
        M.n(pizz, t0, bn, 0.3, 0.55, P['bass'])
    t = 43.65
    while t < 46.5:
        M.perc(t, shaker(0.5), 0.35)
        t += 0.3
    # awkward silence 46.6-51.6 (clock only), then:
    M.n(pizz, 51.85, 'D4', 0.3, 0.7, P['pizz'])
    M.n(pizz, 52.05, 'A3', 0.3, 0.65, P['pizz'])
    M.n(marimba, 52.9, 'G5', 0.2, 0.35, P['mar'])
    M.n(marimba, 53.5, 'A5', 0.2, 0.35, P['mar'])
    for t0, nt in [(53.75, 'D3'), (54.25, 'A2'), (54.75, 'D3')]:
        M.n(pizz, t0, nt, 0.3, 0.35, P['bass'])
    M.n(clarinet, 54.0, 'F4', 0.13, 0.35, P['cl'])
    M.n(clarinet, 54.5, 'E4', 0.13, 0.35, P['cl'])

    # ---- Cue 5 Mimi + the search 55-70 (F major, 120 BPM) ----------------
    for t0, nt, d in [(55.25, 'C5', 0.4), (55.7, 'F5', 0.6), (56.4, 'A5', 0.6), (57.05, 'G5', 0.3), (57.35, 'F5', 0.35),
                      (57.75, 'A5', 0.25), (58.0, 'C6', 0.07), (58.08, 'D6', 0.07), (58.16, 'C6', 0.3)]:
        M.n(flute, t0, nt, d, 0.55, P['fl'])
    M.chord(55.0, ['F3', 'A3', 'C4'], 1.5, 0.4, attack=0.3, release=0.5)
    M.chord(56.5, ['Bb2', 'D3', 'F3'], 1.5, 0.4, attack=0.2, release=0.5)
    M.chord(58.0, ['C3', 'E3', 'G3'], 0.5, 0.4, attack=0.1, release=0.4)
    for t0, nt in [(55.7, 'F2'), (56.4, 'F2'), (57.05, 'Bb2'), (57.75, 'C3')]:
        M.n(pizz, t0, nt, 0.3, 0.5, P['bass'])
    for t0, nt in [(58.5, 'F2'), (59.0, 'C3'), (59.5, 'F2'), (60.0, 'C3'), (60.5, 'F2')]:
        M.n(pizz, t0, nt, 0.3, 0.5, P['bass'])
    for t0 in (58.75, 59.25, 59.75, 60.25):
        for nt in ('F4', 'A4', 'C5'):
            M.n(marimba, t0, nt, 0.1, 0.22, P['mar'])
    for i, nt in enumerate(['F4', 'G4', 'A4', 'Bb4', 'B4', 'C5']):
        M.n(clarinet, 59.0 + 0.25 * i, nt, 0.12, 0.5, P['cl'])
    t = 58.5
    while t < 60.7:
        M.perc(t, shaker(0.45), 0.35)
        t += 0.25
    M.perc(59.0, brush(0.3), 0.1)
    M.perc(60.0, brush(0.3), 0.1)
    M.n(pizz, 62.25, 'C4', 0.3, 0.6, P['pizz'])
    M.n(pizz, 62.5, 'F3', 0.3, 0.6, P['pizz'])
    M.n(marimba, 62.75, 'A4', 0.2, 0.3, P['mar'])
    M.n(marimba, 63.0, 'C5', 0.2, 0.3, P['mar'])
    for t0, nt in [(64.0, 'C5'), (64.15, 'E5'), (64.3, 'G5'), (64.55, 'C6')]:
        M.n(marimba, t0, nt, 0.2, 0.45, P['mar'])
    M.n(pizz, 65.95, 'F2', 0.4, 0.6, P['bass'])
    for t0, nt in [(67.15, 'G5'), (67.3, 'E5'), (67.45, 'C5')]:
        M.n(marimba, t0, nt, 0.2, 0.35, P['mar'])
    M.n(pizz, 67.9, 'D3', 0.4, 0.45, P['bass'])
    M.n(pizz, 67.9, 'A3', 0.4, 0.35, P['pizz'])
    M.n(pizz, 68.9, 'Bb2', 0.4, 0.45, P['bass'])
    M.n(pizz, 68.9, 'F3', 0.4, 0.35, P['pizz'])
    M.chord(67.9, ['D3', 'F3', 'A3'], 1.0, 0.3, attack=0.3, release=0.4)
    M.chord(68.9, ['Bb2', 'D3', 'F3'], 0.9, 0.3, attack=0.2, release=0.6)
    for t0, nt, d in [(68.5, 'A5', 0.25), (68.75, 'G5', 0.25), (69.0, 'E5', 0.6)]:
        M.n(celesta, t0, nt, d, 0.3, P['cel'])

    # ---- Cue 6 Blu's theory 70-79.6 (analytical ostinato) -----------------
    for t0, nt in [(70.5, 'A4'), (71.0, 'A4'), (71.5, 'A4'), (72.0, 'D5')]:
        M.perc(t0, woodblock(1050, 0.55), 0.3)
        M.n(pluck_synth, t0, nt, 0.2, 0.5, P['pl'])
    M.n(pizz, 72.0, 'D2', 0.3, 0.5, P['bass'])
    M.n(pizz, 72.5, 'D2', 0.3, 0.4, P['bass'])
    prog = [(73.0, 75.0, ['D5', 'F5', 'A5', 'D6'], 'D2'), (75.0, 76.0, ['Bb4', 'D5', 'F5', 'Bb5'], 'Bb1'),
            (76.0, 77.0, ['C5', 'E5', 'G5', 'C6'], 'C2'), (77.0, 78.0, ['D5', 'F5', 'A5', 'D6'], 'D2'),
            (78.0, 79.0, ['E5', 'G#5', 'B5', 'D6'], 'E2'), (79.0, 79.6, ['A4', 'C#5', 'E5', 'G5'], 'A1')]
    pat = [0, 1, 2, 1, 3, 2, 1, 2]
    for (a, bnd, ch, root) in prog:
        t = a
        i = 0
        while t < bnd - 1e-6:
            if not (74.55 <= t < 75.0):
                u = (t - 73.0) / 6.6
                v = 0.30 + 0.35 * max(0, u - 0.55) / 0.45 if u > 0.55 else 0.30
                M.n(pluck_synth, t, ch[pat[i % 8]], 0.1, v, P['pl'] * (1 if i % 2 else -1))
                if t >= 77.0 and i % 2 == 0:
                    M.n(marimba, t, ch[pat[i % 8]], 0.1, v * 0.6, P['mar'])
                if i % 2 == 0:
                    M.perc(t, woodblock(1300 if i % 4 == 0 else 1100, 0.18 + 0.15 * u), 0.25)
                if i % 4 == 0:
                    M.n(pizz, t, root.replace('1', '2') if root.endswith('1') else root, 0.3, 0.45 + 0.2 * u, P['bass'])
            t += 0.125
            i += 1
    M.chord(77.0, ['D4', 'A4'], 1.0, 0.25, attack=0.5, release=0.1, bright=3000)
    M.chord(78.0, ['E4', 'B4'], 1.0, 0.3, attack=0.2, release=0.1, bright=3200)
    M.chord(79.0, ['E4', 'A4', 'C#5'], 0.6, 0.35, attack=0.1, release=0.05, bright=3400)
    # silence 79.6-84 ; swell into the macro shot
    M.chord(84.0, ['D3', 'A3'], 3.0, 0.45, attack=1.4, release=0.8, bright=1600)

    # ---- Cue 7 Mystery solved 85-102 --------------------------------------
    M.n(celesta, 87.25, 'D6', 1.2, 0.5, P['cel'])
    M.n(glock, 87.25, 'D6', 1.0, 0.4, P['cel'])
    M.n(pizz, 88.8, 'A3', 0.3, 0.5, P['pizz'])
    M.n(pizz, 89.4, 'D4', 0.3, 0.5, P['pizz'])
    for t0, nt in [(90.5, 'D4'), (90.62, 'F#4'), (90.75, 'A4')]:
        M.n(pizz, t0, nt, 0.3, 0.7, P['pizz'])
    roll(M.dry, 91.35, 92.18, lambda v: brush(v, 0.08), rate=22, v0=0.08, v1=0.7, pan=0.1)
    roll(M.dry, 91.6, 92.18, lambda v: timpani(hz('C2'), v * 0.5, 0.6), rate=14, v0=0.1, v1=0.6)
    tp = 92.25
    M.perc(tp, stab([hz(n) for n in ['F2', 'C3', 'F3', 'A3', 'C4', 'F4']], 0.72))
    M.perc(tp, timpani(hz('F2'), 0.65), -0.1)
    M.perc(tp, cymbal(0.55, 2.6), 0.2)
    M.n(glock, tp, 'F6', 1, 0.6, 0.2)
    M.n(glock, tp, 'A6', 1, 0.45, 0.2)
    fan = [(92.25, 'A4', 0.45), (92.75, 'C5', 0.45), (93.25, 'F5', 0.7), (94.0, 'E5', 0.22), (94.25, 'Bb4', 0.45),
           (94.75, 'C5', 0.45), (95.25, 'F5', 0.9)]
    for t0, nt, d in fan:
        M.n(flute, t0, nt, d, 0.7, P['fl'])
        M.n(celesta, t0, nt.replace('4', '5') if nt.endswith('4') else nt.replace('5', '6'), d, 0.35, P['cel'])
    for t0, ch, d in [(92.25, ['F3', 'A3', 'C4'], 2.0), (94.25, ['Bb2', 'D3', 'F3'], 0.5), (94.75, ['C3', 'E3', 'G3'], 0.5),
                      (95.25, ['F3', 'A3', 'C4'], 1.0)]:
        M.chord(t0, ch, d, 0.5, attack=0.05, release=0.3, bright=2800)
    for t0, nt in [(92.25, 'F2'), (92.75, 'C3'), (93.25, 'F2'), (93.75, 'C3'), (94.25, 'Bb2'), (94.75, 'C3'), (95.25, 'F2'), (95.75, 'C3')]:
        M.n(pizz, t0, nt, 0.3, 0.6, P['bass'])
    for t0 in (92.25, 93.25, 94.25, 95.25):
        M.perc(t0, kick(0.6))
    for t0 in (92.75, 93.75, 94.75, 95.75):
        M.perc(t0, brush(0.5), 0.1)
    t = 92.25
    while t < 96.2:
        M.perc(t, shaker(0.45), 0.35)
        t += 0.25
    for t0 in (92.5, 93.0, 93.5, 94.0):
        for nt in ('F4', 'A4', 'C5'):
            M.n(marimba, t0, nt, 0.1, 0.2, P['mar'])
    M.perc(96.25, stab([hz(n) for n in ['F2', 'F3', 'A3', 'C4', 'F4']], 0.55))
    M.perc(96.25, timpani(hz('F2'), 0.45), -0.1)
    M.n(pizz, 96.25, 'F2', 0.3, 0.7, P['bass'])
    M.n(pizz, 96.25, 'F3', 0.3, 0.6, P['pizz'])
    M.n(celesta, 98.6, 'F6', 0.6, 0.22, P['cel'])                 # the embarrassed blink
    roll(M.dry, 100.8, 102.0, lambda v: brush(v, 0.08), rate=20, v0=0.05, v1=0.55, pan=0.1)
    for t0, nt in [(101.25, 'C4'), (101.5, 'D4'), (101.75, 'E4')]:
        M.n(pizz, t0, nt, 0.3, 0.55, P['pizz'])

    # ---- Cue 8 Celebration 102-113 (F major, 120 BPM) ---------------------
    mel = [(102.0, 'A4', 0.45), (102.5, 'C5', 0.45), (103.0, 'F5', 0.7), (103.75, 'E5', 0.22),
           (104.0, 'D5', 0.45), (104.5, 'C5', 0.45), (105.0, 'A4', 0.95),
           (106.0, 'Bb4', 0.45), (106.5, 'D5', 0.45), (107.0, 'G5', 0.7), (107.75, 'F5', 0.22),
           (108.0, 'E5', 0.45), (108.5, 'G5', 0.42),
           (110.5, 'C5', 0.45), (111.0, 'E5', 0.45), (111.5, 'G5', 0.45), (112.0, 'F5', 1.2)]
    harm = {'A4': 'F4', 'C5': 'A4', 'F5': 'C5', 'E5': 'C5', 'D5': 'A4', 'Bb4': 'G4', 'G5': 'D5'}
    for t0, nt, d in mel:
        M.n(flute, t0, nt, d, 0.72, P['fl'])
        M.n(celesta, t0, nt[:-1] + str(int(nt[-1]) + 1), d, 0.3, P['cel'])
        M.n(clarinet, t0, harm.get(nt, 'A4'), d, 0.38, P['cl'])
    chords = [(102.0, 104.0, ['F4', 'A4', 'C5'], ['F2', 'C3']), (104.0, 106.0, ['D4', 'F4', 'A4', 'C5'], ['D2', 'A2']),
              (106.0, 108.0, ['G4', 'Bb4', 'D5', 'F5'], ['G2', 'D3']), (108.0, 109.0, ['C4', 'E4', 'G4', 'Bb4'], ['C2', 'G2']),
              (110.5, 112.0, ['C4', 'E4', 'G4', 'Bb4'], ['C2', 'G2'])]
    for (a, bnd, ch, bass) in chords:
        M.chord(a, [n[:-1] + str(int(n[-1]) - 1) for n in ch[:3]], bnd - a, 0.45, attack=0.05, release=0.2, bright=2600)
        t = a
        k = 0
        while t < bnd - 1e-6:
            M.n(pizz, t, bass[k % 2], 0.3, 0.6, P['bass'])
            if (t * 2) % 2 < 1e-6 or abs((t - a) % 1.0) < 1e-6:
                M.perc(t, kick(0.55))
            else:
                M.perc(t, brush(0.45), 0.1)
            for nt in ch[:3]:
                M.n(marimba, t + 0.25, nt, 0.1, 0.2, P['mar'])
            M.perc(t, shaker(0.45), 0.35)
            M.perc(t + 0.25, shaker(0.3), 0.35)
            t += 0.5
            k += 1
    M.dry.add(slide_whistle(700, 1500, 0.6, 0.9), 109.0, pan=0.35)
    M.perc(109.6, triangle(1.0), 0.3)
    M.perc(110.38, brush(0.5, 0.06), 0.1)
    M.perc(110.42, brush(0.6, 0.06), 0.1)
    tf = 112.0
    M.perc(tf, stab([hz(n) for n in ['F2', 'C3', 'F3', 'A3', 'C4', 'F4']], 0.65))
    M.perc(tf, timpani(hz('F2'), 0.55), -0.1)
    M.perc(tf, cymbal(0.6, 2.8), 0.2)
    M.chord(tf, ['F3', 'A3', 'C4', 'F4'], 1.0, 0.6, attack=0.02, release=1.2, bright=2800)
    M.n(pizz, tf, 'F2', 0.4, 0.7, P['bass'])
    M.n(glock, tf, 'F6', 1, 0.4, 0.2)

    # ---- Cue 9 settle 113-115.6, end card ---------------------------------
    M.chord(113.0, ['F3', 'A3', 'C4', 'E4', 'G4'], 1.8, 0.4, attack=0.5, release=0.9, bright=1800)
    for t0, nt in [(113.2, 'C5'), (113.7, 'E5'), (114.2, 'G5'), (114.7, 'A5')]:
        M.n(celesta, t0, nt, 0.8, 0.28, P['cel'])
    M.n(pizz, 113.0, 'F2', 0.4, 0.4, P['bass'])
    for t0, nt, d in [(117.9, 'A4', 0.25), (118.15, 'C5', 0.25), (118.4, 'F5', 1.2)]:
        M.n(celesta, t0, nt, d, 0.25, 0.0)
    M.chord(117.9, ['F3', 'A3', 'C4'], 1.6, 0.22, attack=0.4, release=0.8, bright=1500)
    return M


# --------------------------------------------------------------------------
# Sound design
# --------------------------------------------------------------------------
def pan_for(t, x):
    if t >= TL.END_CARD_T:
        return 0.0
    cx, cy, zm = TL.shot_at(t).cam(t)
    sx = (x - cx) * zm
    return float(np.clip(sx / 960 * 0.75, -0.75, 0.75))


SIZE = {'bo': 1.0, 'mimi': 0.85, 'pip': 0.9, 'blu': 0.75}


def sfx_thump(size, h, who):
    d = 0.22
    t = tv(d)
    f0 = {'pip': 115, 'blu': 125, 'mimi': 100, 'bo': 90}.get(who, 95)
    f = f0 * 0.55 + f0 * 0.45 * np.exp(-t / 0.03)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.055 if who == 'blu' else 0.07))
    fw = lp(noise(d), 450) * np.exp(-t / 0.05)
    rus = bp(noise(d), 2000, 6000) * np.exp(-t / 0.03) * 0.15
    g = size * min(1.3, math.sqrt(max(h, 10) / 60))
    return fades((0.7 * tone + 0.8 * fw + rus) * g * 0.2)


def sfx_swish(d=0.08, lo=1500, hi=5500, gain=0.12):
    t = tv(d)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return fades(bp(noise(d), lo, hi) * env * gain)


def sfx_sweep(d, f0, f1, gain, q=0.6):
    """Noise through a sweeping band (air/fabric gestures)."""
    t = tv(d)
    x = noise(d)
    out = np.zeros_like(x)
    seg = int(0.01 * SR)
    for i in range(0, len(x), seg):
        u = i / len(x)
        fc = f0 * (f1 / f0) ** u
        out[i:i + seg] = bp(x[max(0, i - 2 * seg):i + seg], fc * (1 - q / 2), fc * (1 + q / 2))[-len(x[i:i + seg]):]
    env = smoothstep(0, 0.03, t) * (1 - smoothstep(d * 0.4, d, t))
    return fades(out * env * gain)


def sfx_scoot(d):
    t = tv(d)
    am = 0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 4.2 * t))
    y = lp(noise(d), 650, 4) + 0.12 * bp(noise(d), 1800, 4500)
    y /= np.sqrt(np.mean(y ** 2)) + 1e-9
    env = smoothstep(0, 0.1, t) * (1 - smoothstep(d - 0.15, d, t))
    return fades(y * am * env * 0.022)


def sfx_bonk():
    d = 0.5
    t = tv(d)
    f = 45 + 40 * np.exp(-t / 0.04)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * 0.9
    y += lp(noise(d), 380) * np.exp(-t / 0.12) * 1.1
    y += bp(noise(d), 1500, 5000) * np.exp(-t / 0.05) * 0.12
    return fades(y * 0.4)


def sfx_slide(d, lo=300, hi=1400, gain=0.10, rough=True):
    t = tv(d)
    y = bp(noise(d), lo, hi)
    if rough:
        y *= 0.6 + 0.4 * lp(RNG.uniform(-1, 1, len(t)), 60) * 6
    env = smoothstep(0, 0.02, t) * (1 - smoothstep(d * 0.5, d, t))
    return fades(y * env * gain)


def sfx_bop():
    t = tv(0.2)
    y = np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.05) + 0.5 * np.sin(2 * np.pi * 520 * t) * np.exp(-t / 0.025)
    y += lp(noise(0.2), 2500) * np.exp(-t / 0.004) * 0.6
    return fades(y * 0.22)


def sfx_tick(f=3100, gain=0.03):
    t = tv(0.03)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.003) + 0.5 * np.sin(2 * np.pi * f * 0.52 * t) * np.exp(-t / 0.006)
    return fades(y * gain, 0.0002, 0.005)


def build_sfx():
    sfx, boops, amb = Bus(), Bus(), Bus()
    for kind, t, who, data in TL.EVENTS:
        x = TL.CHARS[who].state(t)['x'] if who in TL.CHARS else 700.0
        pn = pan_for(t, x)
        sz = SIZE.get(who, 1.0)
        if kind == 'land':
            sfx.add(sfx_thump(sz, data['h'], who), t, pan=pn)
        elif kind == 'takeoff':
            sfx.add(sfx_swish(0.07, 1800, 6000, 0.05 * sz), t - 0.02, pan=pn)
        elif kind == 'scoot':
            sfx.add(sfx_scoot(data['t1'] - t), t, pan=pn)
        elif kind == 'stretch':
            sfx.add(sfx_sweep(0.45, 700, 2400, 0.2), t, pan=pn)
        elif kind == 'deflate':
            sfx.add(sfx_sweep(0.5, 1800, 500, 0.2), t, pan=pn)
        elif kind in ('nod', 'pouf'):
            sfx.add(sfx_swish(0.09, 600, 2500, 0.06), t, pan=pn)
        elif kind == 'wiggle':
            d = 0.45
            tt = tv(d)
            sfx.add(fades(bp(noise(d), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt)) * np.sin(np.pi * tt / d) * 0.07), t, pan=pn)
        elif kind == 'bonk':
            sfx.add(sfx_bonk(), t, pan=pan_for(t, 400))
            sfx.add(sfx_slide(0.32, 250, 1200, 0.09), t + 0.02, pan=pan_for(t, 380))
        elif kind == 'pff':
            big = data.get('big', True)
            sfx.add(sfx_sweep(0.42 if big else 0.24, 2600, 900, 0.40 if big else 0.26, q=0.8), t, pan=pn)
        elif kind == 'bop':
            sfx.add(sfx_bop(), t, pan=pan_for(t, 60))
        elif kind == 'book_slide':
            sfx.add(sfx_slide(data['t1'] - t, 1000, 3200, 0.16), t, pan=pan_for(t, 60))
        elif kind == 'whip':
            sfx.add(sfx_sweep(0.14, 600, 3200, 0.22, q=0.9), t, pan=0.0)
        elif kind == 'scan':
            sfx.add(sfx_tick(4200 + 300 * data['i'], 0.04), t, pan=0.3)
    for t, v in TL.BOOPS:
        y = boop_variant(v)
        if v == 'outside':
            boops.add(y, t, pan=0.62)
        else:
            x = TL.bo.state(t)['x']
            boops.add(y, t - (0.03 if v in ('head', 'room') else 0), pan=pan_for(t, x) if v != 'tiny' else 0.0)
    # ambience: room tone + the wall clock (ticks once a second, in sync with its hand)
    d = TL.DUR
    tone = lp(np.cumsum(RNG.normal(0, 1, NS)) * 0.003, 700)
    tone = hp(tone, 40)
    tone = tone / np.abs(tone).max() * 0.006
    gate = np.ones(NS)
    tt = np.arange(NS) / SR
    gate *= 1 - smoothstep(115.98, 116.1, tt)                       # complete silence on the turn
    amb.y += np.vstack([tone, np.roll(tone, 977)]) * gate
    for s in range(0, int(TL.END_CARD_T) + 1):
        if s >= 116:
            break
        amb.add(sfx_tick(3100 if s % 2 == 0 else 2500, 0.035), float(s), pan=-0.35)
    return sfx, boops, amb


# --------------------------------------------------------------------------
# Mix + master
# --------------------------------------------------------------------------
def write_wav(path, y):
    import wave
    y = np.clip(y, -1, 1)
    data = (y.T * (2 ** 23 - 1)).astype(np.int32)
    b = np.zeros((data.shape[0], data.shape[1], 3), np.uint8)
    for k in range(3):
        b[..., k] = (data >> (8 * k)) & 0xFF
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b.tobytes())


def limiter(y, ceiling=0.871, hold=0.06, smooth=0.02):
    """Look-ahead brickwall: min-hold of the required gain followed by a
    moving average no longer than the hold, so gain <= required everywhere."""
    from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
    pk = np.abs(y).max(0)
    r = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = uniform_filter1d(minimum_filter1d(r, size=int(hold * SR) | 1), size=int(smooth * SR) | 1)
    return y * np.minimum(g, r)


def main():
    import pyloudnorm as pyln
    os.makedirs(AOUT, exist_ok=True)
    M = compose()
    music = reverb(M.dry.y, IR_HALL, 0.28)
    # musical fade-in at the head
    tt = np.arange(NS) / SR
    music *= smoothstep(0.0, 2.0, tt)
    sfx, boops, amb = build_sfx()
    sfx_y = reverb(sfx.y, IR_ROOM, 0.18)
    boop_y = boops.y.copy()
    room_part = np.zeros_like(boop_y)
    hall_part = np.zeros_like(boop_y)
    for t, v in TL.BOOPS:
        i0, i1 = int((t - 0.05) * SR), int((t + 0.4) * SR)
        if v == 'outside':
            hall_part[:, i0:i1] = boop_y[:, i0:i1]
        elif v == 'room':
            room_part[:, i0:i1] = boop_y[:, i0:i1] * 1.2
        else:
            room_part[:, i0:i1] = boop_y[:, i0:i1] * 0.6
    boop_y = boop_y + reverb(room_part, IR_ROOM, 0.35) - room_part + reverb(hall_part, IR_HALLWAY, 0.9) - hall_part

    def rms_db(y):
        return 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-12)

    stems = {'music': music * 0.80, 'sfx': sfx_y * 1.25, 'boops': boop_y * 0.42, 'ambience': amb.y * 1.0}
    mix = sum(stems.values())
    meter = pyln.Meter(SR)
    pk = np.abs(mix).max(0)
    for k, v in stems.items():
        p = np.abs(v).max(0)
        top = np.argsort(p)[-1]
        print(f'  {k:9s} peak {20*np.log10(p.max()+1e-12):6.1f} dBFS at {top/SR:6.2f}s  rms {rms_db(v):6.1f}')
    L = meter.integrated_loudness(mix.T)
    gain = 10 ** ((-16.0 - L) / 20)
    mix = limiter(mix * gain, ceiling=10 ** (-1.2 / 20))
    g2 = 10 ** ((-16.0 - meter.integrated_loudness(mix.T)) / 20)   # second pass after limiting
    mix = limiter(mix * g2, ceiling=10 ** (-1.2 / 20))
    gain *= g2
    # 4x oversampled true-peak check
    from scipy.signal import resample_poly
    tp = 20 * np.log10(np.abs(resample_poly(mix, 4, 1, axis=1)).max())
    L2 = meter.integrated_loudness(mix.T)
    write_wav(os.path.join(AOUT, 'mix_stereo.wav'), mix[:, :int(TL.DUR * SR)])
    for k, y in stems.items():
        write_wav(os.path.join(AOUT, f'stem_{k}.wav'), (y * gain)[:, :int(TL.DUR * SR)])
    # signature boop library
    for v, name in [('plain', 'boop_signature.wav'), ('head', 'boop_variant_headphones.wav'),
                    ('outside', 'boop_variant_outside_mystery.wav'), ('tiny', 'boop_variant_endcard.wav')]:
        y = boop() if v == 'plain' else boop_variant(v)
        y = np.concatenate([np.zeros(int(0.1 * SR)), y, np.zeros(int(0.6 * SR))])
        st = np.vstack([y, y]) * 0.7
        if v == 'outside':
            st = reverb(st, IR_HALLWAY, 0.9)
        write_wav(os.path.join(AOUT, name), st / np.abs(st).max() * 0.7)
    report = dict(integrated_lufs=round(L2, 2), true_peak_dbtp=round(tp, 2),
                  stem_rms_db={k: round(rms_db(v * gain), 1) for k, v in stems.items()})
    print(report)
    return report


if __name__ == '__main__':
    main()

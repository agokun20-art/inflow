"""'The Stakeout' - score (MIDI -> FluidSynth sampled orchestra) + sound design + mix.

Every musical hit and SFX is placed from anim_stakeout's own event list, so picture
and sound share one clock. Output: out/stakeout_mix.wav (48 kHz, -16 LUFS, <= -1 dBTP).
"""
import math
import os
import subprocess
import sys
import wave

import mido
import numpy as np
from scipy.signal import oaconvolve, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import anim_stakeout as A  # noqa: E402
from audio import (SR, bp, lp, hp, noise, fades, smoothstep, boop, make_ir, limiter)  # noqa: E402

LEN = A.DUR + A.TAIL
NS = int(LEN * SR)
OUT = os.path.join(HERE, 'out')
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
rng = np.random.default_rng(9)


def tv(d):
    return np.arange(int(round(d * SR))) / SR


class Bus:
    def __init__(self):
        self.y = np.zeros((2, NS))

    def add(self, sig, t, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            a = (pan + 1) * math.pi / 4
            sig = np.vstack([sig * math.cos(a), sig * math.sin(a)]) * math.sqrt(2)
        i = int(round(t * SR))
        j0 = max(0, -i)
        n = min(sig.shape[1] - j0, NS - max(i, 0))
        if n > 0:
            self.y[:, max(i, 0):max(i, 0) + n] += gain * sig[:, j0:j0 + n]


EV = {}
for kind, t, d in A.EVENTS:
    EV.setdefault(kind, []).append((t, d))


# ============================================================ score (MIDI)
def note_num(n):
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    v = names[n[0]]
    i = 1
    while n[i] in '#b':
        v += 1 if n[i] == '#' else -1
        i += 1
    return v + 12 * (int(n[i:]) + 1)


class Score:
    """Absolute-time MIDI writer: tempo 60 BPM, 960 tpb -> 1 tick = 1/960 s."""
    TPB = 960

    def __init__(self):
        self.ev = []   # (time_s, order, channel, msg)
        self.ch = {}

    def inst(self, name, program, ch, vol=100, pan=64):
        self.ch[name] = ch
        self.ev += [(0, 0, ch, mido.Message('program_change', channel=ch, program=program)),
                    (0, 0, ch, mido.Message('control_change', channel=ch, control=7, value=vol)),
                    (0, 0, ch, mido.Message('control_change', channel=ch, control=10, value=pan)),
                    (0, 0, ch, mido.Message('control_change', channel=ch, control=11, value=127))]

    def n(self, name, t, note, dur, vel=80):
        c = self.ch[name]
        k = note_num(note) if isinstance(note, str) else note
        self.ev.append((t, 2, c, mido.Message('note_on', channel=c, note=k, velocity=int(vel))))
        self.ev.append((t + dur, 1, c, mido.Message('note_off', channel=c, note=k, velocity=0)))

    def cc(self, name, t, ctl, val):
        c = self.ch[name]
        self.ev.append((t, 0, c, mido.Message('control_change', channel=c, control=ctl, value=int(np.clip(val, 0, 127)))))

    def ramp(self, name, t0, t1, ctl, v0, v1, steps=24):
        for k in range(steps + 1):
            u = k / steps
            self.cc(name, t0 + (t1 - t0) * u, ctl, v0 + (v1 - v0) * u)

    def bend(self, name, t0, t1, semis, steps=24, back=None):
        c = self.ch[name]
        for k in range(steps + 1):
            u = k / steps
            v = int(semis / 2 * 8191 * u * u)
            self.ev.append((t0 + (t1 - t0) * u, 0, c, mido.Message('pitchwheel', channel=c, pitch=int(np.clip(v, -8192, 8191)))))
        if back is not None:
            self.ev.append((back, 0, c, mido.Message('pitchwheel', channel=c, pitch=0)))

    def write(self, path):
        mid = mido.MidiFile(ticks_per_beat=self.TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=1000000))
        last = 0
        for t, _, _, msg in sorted(self.ev, key=lambda e: (e[0], e[1])):
            tick = int(round(max(0, t) * self.TPB))
            tr.append(msg.copy(time=tick - last))
            last = tick
        mid.save(path)


def compose():
    sc = Score()
    sc.inst('pizz', 45, 0, vol=112, pan=52)
    sc.inst('bsn', 70, 1, vol=100, pan=74)
    sc.inst('trem', 44, 2, vol=90, pan=64)
    sc.inst('harp', 46, 3, vol=96, pan=80)
    sc.inst('timp', 47, 4, vol=110, pan=60)
    sc.inst('whistle', 78, 5, vol=80, pan=70)
    sc.inst('glock', 9, 6, vol=84, pan=76)
    sc.inst('stab', 48, 7, vol=110, pan=64)
    sc.inst('cello', 42, 8, vol=96, pan=50)
    # --- the creep: pizz on every footfall, bassoon sneaks on the off-beats
    steps = [t for t, _ in EV['creep_step']]
    bass = ['D2', 'A2', 'D2', 'A2', 'F2', 'A2']
    for t, nt in zip(steps, bass):
        sc.n('pizz', t, nt, 0.3, 92)
        sc.n('pizz', t, nt[:-1] + str(int(nt[-1]) + 1), 0.3, 58)
    off = [steps[0] + 0.3125 + i * 0.625 for i in range(5)]
    for t, nt in zip(off, ['D3', 'E3', 'F3', 'G#3', 'A3']):
        sc.n('bsn', t, nt, 0.16, 78)
    sc.n('pizz', EV['arrive'][0][0], 'A3', 0.3, 70)
    # --- the lean: tremolo strings swell, ticking clock carries the tension
    tl = EV['lean'][0][0]
    sc.n('trem', tl, 'A4', 4.2, 70)
    sc.n('trem', tl, 'D5', 4.2, 55)
    sc.ramp('trem', tl, tl + 1.2, 11, 40, 100)
    sc.ramp('trem', 6.25, 8.3, 11, 100, 58)
    for t, _ in EV['dart']:
        sc.n('pizz', t + 0.02, 'E5', 0.15, 50)
    # --- nothing: the deflate (bassoon, a sad bent slide) and dejected steps
    ts = EV['sigh'][0][0]
    sc.n('bsn', ts - 0.05, 'A2', 0.42, 84)
    sc.n('bsn', ts + 0.42, 'G#2', 0.75, 80)
    sc.bend('bsn', ts + 0.75, ts + 1.15, -1.0, back=ts + 1.3)
    sh = [t for t, _ in EV['shuffle_step']]
    for t, nt in zip(sh, ['D3', 'C#3']):
        sc.n('pizz', t, nt, 0.3, 55)
    # BOOP #1 (10.95) lands in silence. Then the whip:
    tw = EV['whip'][0][0]
    for k, nt in enumerate(['D3', 'F3', 'A3', 'D4', 'F4', 'A4', 'D5']):
        sc.n('harp', tw - 0.06 + k * 0.022, nt, 0.4, 70 + k * 5)
    tk = EV['skid'][0][0]
    sc.n('timp', tk, 'D2', 1.2, 112)
    sc.n('stab', tk, 'D3', 0.22, 112)
    sc.n('stab', tk, 'A3', 0.22, 100)
    sc.n('stab', tk, 'F4', 0.22, 100)
    sc.n('pizz', tk, 'D2', 0.3, 110)
    # --- standoff: low tremolo + a mock-western whistle; the clock's 'innocent' ting
    sc.n('cello', 12.8, 'D2', 1.9, 76)
    sc.n('trem', 12.8, 'D3', 1.95, 60)
    sc.ramp('trem', 12.8, 13.6, 11, 60, 96)
    sc.n('whistle', 12.88, 'A4', 0.28, 80)
    sc.n('whistle', 13.18, 'D5', 0.55, 86)
    sc.bend('whistle', 13.55, 13.72, -0.6, back=13.8)
    sc.n('glock', 14.0, 'A6', 0.8, 70)
    # --- backing away: descending pizz on each step, tension rising... then nothing
    bs = [t for t, _ in EV['back_step']]
    for t, nt in zip(bs[:2], ['A2', 'G#2']):
        sc.n('pizz', t, nt, 0.3, 84)
    sc.n('trem', 14.85, 'A3', 1.13, 50)
    sc.n('trem', 14.85, 'Bb3', 1.13, 44)
    sc.ramp('trem', 14.85, 15.95, 11, 50, 112)
    # BOOP #2 (16.0): music cuts dead. Silence through the leap and the stare.
    # BOOP #3 (18.5), eye slide: one low bassoon + pizz 'bomp' as the button.
    te = EV['eye_slide'][0][0]
    sc.n('bsn', te + 0.04, 'D2', 0.5, 76)
    sc.n('pizz', te + 0.04, 'D2', 0.3, 70)
    path = os.path.join(OUT, 'stakeout_score.mid')
    sc.write(path)
    return path


def render_midi(mid):
    wav = os.path.join(OUT, 'stakeout_score_dry.wav')
    subprocess.run(['fluidsynth', '-ni', '-q', '-R', '0', '-C', '0', '-g', '0.9', '-r', str(SR), '-F', wav, SF2, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    w = wave.open(wav)
    n, ch, sw = w.getnframes(), w.getnchannels(), w.getsampwidth()
    a = np.frombuffer(w.readframes(n), np.int16).reshape(-1, ch).T / 32768.0
    y = np.zeros((2, NS))
    m = min(NS, a.shape[1])
    y[:, :m] = a[:, :m]
    return y


# ============================================================ sound design
def sfx_plush_step(level=1.0, soft=True):
    d = 0.22
    t = tv(d)
    th = np.sin(2 * np.pi * (70 + 40 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.045)
    fw = lp(noise(d), 380) * np.exp(-t / 0.04)
    rus = bp(noise(d), 1800, 6500) * np.exp(-t / (0.03 if soft else 0.05)) * 0.35
    return fades((0.6 * th + 0.9 * fw + rus) * 0.18 * level)


def sfx_sweep(d, f0, f1, gain, q=0.7, shape=1.0):
    t = tv(d)
    x = noise(d)
    out = np.zeros_like(x)
    seg = int(0.008 * SR)
    for i in range(0, len(x), seg):
        u = i / len(x)
        fc = f0 * (f1 / f0) ** u
        sl = x[max(0, i - 3 * seg):i + seg]
        out[i:i + seg] = bp(sl, max(40, fc * (1 - q / 2)), fc * (1 + q / 2))[-len(x[i:i + seg]):]
    env = smoothstep(0, 0.03 * shape, t) * (1 - smoothstep(d * 0.45, d, t))
    return fades(out * env * gain)


def sfx_clock_tick(tock=False):
    d = 0.09
    t = tv(d)
    imp = np.zeros_like(t)
    imp[:6] = rng.uniform(-1, 1, 6)
    modes = [(2150, 0.012), (3420, 0.008), (5230, 0.005), (1180, 0.02)] if not tock else [(1850, 0.014), (2980, 0.009), (4600, 0.005), (990, 0.022)]
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / tau) * a for (f, tau), a in zip(modes, (1, 0.7, 0.4, 0.5)))
    y += hp(noise(d), 4000) * np.exp(-t / 0.002) * 0.6
    return fades(y * 0.05, 0.0002, 0.01)


def rain_bed():
    n = noise(LEN)
    body = bp(n, 300, 5000, 2) * 0.012
    hiss = hp(noise(LEN), 6000) * 0.004
    drops = np.zeros(NS)
    for _ in range(int(LEN * 60)):
        i = rng.integers(0, NS - 2000)
        d = rng.uniform(0.3, 1.0)
        tt = np.arange(600) / SR
        f = rng.uniform(1800, 5200)
        drops[i:i + 600] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.004) * d * 0.012
    L = body + hiss + drops
    R = np.roll(body, 1731) + np.roll(hiss, 977) + np.roll(drops, 5113)
    return np.vstack([L, R])


def room_tone():
    t = lp(noise(LEN), 220, 2) * 0.006
    return np.vstack([t, np.roll(t, 4111)])


def cam_dist_gain(t, src):
    """Level by distance from the active camera to a source (inverse-ish, clamped)."""
    sh = A.shot_at(t)
    loc, tgt = sh.fn(t)
    d = np.linalg.norm(np.asarray(loc) - np.asarray(src))
    return float(np.clip(0.35 / max(d, 0.08), 0.25, 2.2))


def build_sfx():
    fol, clk, amb, bp_ = Bus(), Bus(), Bus(), Bus()
    E = EV
    for t, d in E['creep_step']:
        fol.add(sfx_plush_step(0.7), t, pan=-0.2)
    for t, d in E.get('shuffle_step', []):
        fol.add(sfx_plush_step(0.55), t, pan=0.0)
        fol.add(sfx_sweep(0.18, 900, 500, 0.05), t - 0.08)
    for t, d in E.get('back_step', []):
        fol.add(sfx_plush_step(0.6), t, pan=0.1)
    fol.add(sfx_plush_step(0.8), E['arrive'][0][0])
    tl = E['lean'][0][0]
    fol.add(sfx_sweep(1.2, 500, 1300, 0.045, q=0.4, shape=8), tl)            # fabric creak of the stretch
    for t, d in E['dart']:
        fol.add(sfx_sweep(0.05, 3000, 4500, 0.02), t)
    ts = E['sigh'][0][0]
    fol.add(sfx_sweep(0.75, 1500, 380, 0.11, q=0.9, shape=4), ts)           # deflating sigh of air + fur
    fol.add(sfx_sweep(0.55, 1400, 700, 0.08), E['turn'][0][0])
    tw = E['whip'][0][0]
    fol.add(sfx_sweep(0.32, 380, 3600, 0.30, q=1.0), tw - 0.05)             # whoosh
    tt = tv(0.3)
    flutter = bp(noise(0.3), 1500, 6500) * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * tt)) * np.sin(np.pi * tt / 0.3) * 0.08
    fol.add(fades(flutter), tw)
    tk = E['skid'][0][0]
    fol.add(sfx_sweep(0.22, 900, 350, 0.12, q=1.2), tk)                     # plush skid on wood
    fol.add(sfx_plush_step(1.4, soft=False), tk)
    t0 = E['startle'][0][0]
    fol.add(sfx_sweep(0.35, 500, 4200, 0.26, q=1.0), t0 - 0.01)             # leap whoosh
    t_ = tv(0.4)
    fwoomp = hp(noise(0.4), 2500) * smoothstep(0, 0.05, t_) * np.exp(-t_ / 0.12) * 0.13
    fol.add(fades(fwoomp), t0 + 0.02)                                          # fur bristling out
    fol.add(sfx_plush_step(2.0, soft=False), E['land_big'][0][0])
    # fur settling: a fine crackle that thins out
    d = 1.2
    tt = tv(d)
    cr = np.zeros(len(tt))
    for _ in range(140):
        i = int(rng.beta(1, 2.5) * (len(tt) - 300))
        cr[i:i + 200] += hp(rng.uniform(-1, 1, 200), 3000) * np.exp(-np.arange(200) / 40) * rng.uniform(0.2, 1)
    fol.add(fades(cr * 0.012), E['fur_settle'][0][0])
    # clock: one tick per second, alternating, level by camera distance
    for s in range(0, int(LEN) + 1):
        if s >= A.DUR:
            break
        g = cam_dist_gain(float(s), A.DIAL)
        clk.add(sfx_clock_tick(s % 2 == 1), float(s), gain=g, pan=0.15)
    # boops: the signature boop, heard 'inside the head' (close, centred)
    for k, tb in enumerate(A.BOOPS):
        y = boop()
        pre = bp(noise(0.06), 2000, 6000) * np.hanning(int(0.06 * SR)) * 0.04
        y = np.concatenate([np.zeros(int(0.02 * SR)), y])
        y[:len(pre)] += pre
        bp_.add(y * (1.0 if k < 2 else 1.08), tb - 0.02, pan=0.0)
    amb.y += rain_bed() + room_tone()
    return fol, clk, amb, bp_


def write24(path, y):
    y = np.clip(y, -1, 1)
    d = (y.T * (2 ** 23 - 1)).astype(np.int32)
    b = np.zeros((d.shape[0], d.shape[1], 3), np.uint8)
    for k in range(3):
        b[..., k] = (d >> (8 * k)) & 0xFF
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b.tobytes())


def main():
    import pyloudnorm as pyln
    music = render_midi(compose())
    ir_h = make_ir(1.8, pre=0.015, bright=6500, dark=2000, seed=3)
    ir_r = make_ir(0.45, pre=0.005, bright=6000, dark=2400, seed=5)

    def rev(y, ir, wet):
        o = np.zeros_like(y)
        for c in range(2):
            o[c] = oaconvolve(y[c], ir[c])[:NS]
        return y + wet * o
    music = rev(music, ir_h, 0.22)
    fol, clk, amb, bps = build_sfx()
    stems = dict(music=music * 1.0, foley=rev(fol.y, ir_r, 0.2) * 1.0, clock=rev(clk.y, ir_r, 0.15) * 1.0,
                 ambience=amb.y * 1.0, boops=rev(bps.y, ir_r, 0.12) * 0.42)
    # duck ambience under the deadpan for a cleaner silence, then cut to black
    tt = np.arange(NS) / SR
    end = 1 - smoothstep(A.DUR + 0.05, A.DUR + 0.6, tt)
    for k in stems:
        if k != 'boops':
            stems[k] = stems[k] * end
    mix = sum(stems.values())
    meter = pyln.Meter(SR)
    L = meter.integrated_loudness(mix.T)
    g = 10 ** ((-16 - L) / 20)
    mix = limiter(mix * g, ceiling=10 ** (-1.2 / 20))
    g2 = 10 ** ((-16 - meter.integrated_loudness(mix.T)) / 20)
    mix = limiter(mix * g2, ceiling=10 ** (-1.2 / 20))
    tp = 20 * np.log10(np.abs(resample_poly(mix, 4, 1, axis=1)).max())
    write24(os.path.join(OUT, 'stakeout_mix.wav'), mix)
    for k, v in stems.items():
        write24(os.path.join(OUT, f'stakeout_stem_{k}.wav'), v * g * g2)

    def db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    print('LUFS', round(meter.integrated_loudness(mix.T), 2), 'TP', round(tp, 2))
    for k, v in stems.items():
        print(f'  {k:9s} rms {db(v * g * g2):6.1f} dBFS')
    for tb in A.BOOPS:
        i = int(tb * SR)
        print(f'  boop {tb:5.2f}: boop {db(stems["boops"][:, i:i + 8000] * g * g2):6.1f}  bed {db((mix - stems["boops"] * g * g2)[:, i - 24000:i - 1000]):6.1f}')


if __name__ == '__main__':
    main()

"""Art-directed textures for the v2 set (numpy + skia -> PNG)."""
import math
import os

import numpy as np
import skia
from PIL import Image
from scipy.ndimage import gaussian_filter

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
os.makedirs(TEX, exist_ok=True)
rng = np.random.default_rng(42)


def save(name, arr):
    p = os.path.join(TEX, name)
    Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)).save(p)
    return p


def fbm(h, w, octaves=5, base=4, seed=0):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp = 1.0
    for o in range(octaves):
        s = base * 2 ** o
        g = r.normal(0, 1, (s + 1, int(s * w / h) + 1))
        img = np.array(Image.fromarray(g.astype(np.float32)).resize((w, h), Image.BICUBIC))
        out += img * amp
        amp *= 0.5
    out = (out - out.min()) / (out.max() - out.min())
    return out


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def night_sky(w=2048, h=1024):
    y = np.linspace(0, 1, h)[:, None]
    top, mid, low = hexrgb('#0b1430'), hexrgb('#1f2f5c'), hexrgb('#4a5a86')
    g = np.where(y < 0.6, top + (mid - top) * (y / 0.6), mid + (low - mid) * ((y - 0.6) / 0.4))
    img = np.broadcast_to(g[:, None, :] if g.ndim == 2 else g, (h, w, 3)).copy()
    img = np.repeat(g[:, None, :], w, axis=1) if img.shape != (h, w, 3) else img
    # soft clouds
    c = fbm(h, w, 6, 3, seed=3)
    img += (c[..., None] - 0.5) * 0.06 * hexrgb('#9fb2e0')
    # moon with halo
    yy, xx = np.mgrid[0:h, 0:w]
    mx, my, mr = w * 0.64, h * 0.28, h * 0.055
    d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    halo = np.exp(-(d / (mr * 3.2)) ** 2) * 0.35
    img += halo[..., None] * hexrgb('#a9c0ff')
    disc = np.clip((mr - d) / 2.0, 0, 1)
    moon = hexrgb('#f2f0e6') * (0.92 + 0.08 * fbm(h, w, 4, 16, seed=9)[..., None])
    img = img * (1 - disc[..., None]) + moon * disc[..., None] * 1.6
    # stars (sparse, not 'magical')
    for _ in range(60):
        sx, sy = rng.integers(0, w), rng.integers(0, int(h * 0.55))
        img[sy, sx] += 0.5
    # distant rooftops with a few warm windows
    roof = np.zeros((h, w))
    x = 0
    while x < w:
        bw = rng.integers(90, 230)
        bh = rng.integers(int(h * 0.12), int(h * 0.3))
        roof[h - bh:, x:x + bw] = 1
        if rng.random() < 0.5:
            for k in range(bw // 2):
                roof[h - bh - k // 1:h - bh, x + k:x + bw - k] = 1
        for _ in range(rng.integers(0, 4)):
            wx, wy = x + rng.integers(10, max(11, bw - 20)), h - rng.integers(20, max(21, bh - 20))
            img[wy:wy + 14, wx:wx + 10] = hexrgb('#ffc77a') * 1.4
            roof[wy:wy + 14, wx:wx + 10] = 0.0
        x += bw - 10
    img = img * (1 - roof[..., None]) + hexrgb('#0a0f22') * roof[..., None]
    return save('night_sky.png', np.clip(img, 0, 1))


def rain(w=512, h=1024):
    a = np.zeros((h, w))
    for _ in range(420):
        x, y = rng.integers(0, w), rng.integers(0, h)
        L = rng.integers(18, 60)
        a[y:y + L, x] = rng.uniform(0.25, 0.7)
    a = gaussian_filter(a, (1.2, 0.6))
    a = np.maximum(a, np.roll(a, h // 2, 0) * 0.0)
    img = np.dstack([a, a, a, a])
    p = os.path.join(TEX, 'rain.png')
    Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8), 'RGBA').save(p)
    return p


def rug(w=2048, h=1366):
    y, x = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    e = np.minimum.reduce([x, 1 - x, y * h / w, (1 - y) * h / w])
    field_c, cream, rust, ink, sage = hexrgb('#9a4b37'), hexrgb('#e6d5b8'), hexrgb('#b8653f'), hexrgb('#3b2a2a'), hexrgb('#7d8f74')
    img = np.ones((h, w, 3)) * field_c
    band = lambda lo, hi: (e > lo) & (e < hi)
    img[band(0.0, 0.035)] = cream
    img[band(0.035, 0.045)] = ink
    img[band(0.06, 0.07)] = cream
    img[band(0.08, 0.09)] = sage
    # central kilim diamonds
    cx, cy = 0.5, 0.5
    dd = np.abs(x - cx) * 1.0 + np.abs(y - cy) * h / w * 1.5
    for r, c in ((0.30, cream), (0.27, rust), (0.22, ink), (0.20, cream), (0.15, sage), (0.13, cream), (0.06, rust)):
        img[(dd < r) & (e > 0.1)] = c
    # repeated small diamonds near the ends
    for k in range(6):
        px = 0.16 + k * 0.136
        for py in (0.18, 0.82):
            d2 = np.abs(x - px) + np.abs(y - py) * h / w * 1.5
            img[(d2 < 0.035) & (e > 0.1)] = cream
            img[(d2 < 0.02) & (e > 0.1)] = ink
    # weave + fibre + wear
    weave = 0.5 + 0.5 * np.sin(x * w * 0.9) * np.sin(y * h * 0.9)
    img *= (0.9 + 0.1 * weave)[..., None]
    img *= (0.82 + 0.3 * fbm(h, w, 6, 6, seed=5))[..., None]
    return save('rug.png', np.clip(img, 0, 1))


def plaster(w=1024, h=1024):
    n = fbm(h, w, 7, 4, seed=11)
    base = hexrgb('#a08a70')
    img = base * (0.86 + 0.22 * n[..., None])
    return save('plaster.png', np.clip(img, 0, 1))


def clock_dial(size=1024):
    surf = skia.Surface(size, size)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    c = size / 2
    cv.drawCircle(c, c, c * 0.995, skia.Paint(AntiAlias=True, Color=skia.Color4f(0.96, 0.93, 0.85, 1)))
    cv.drawCircle(c, c, c * 0.995, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        skia.Point(c * 0.8, c * 0.7), c * 1.2, [skia.Color4f(1, 1, 1, 0).toColor(), skia.Color4f(0.4, 0.3, 0.2, 0.25).toColor()])))
    ink = skia.Paint(AntiAlias=True, Color=skia.Color4f(0.12, 0.11, 0.1, 1))
    for i in range(60):
        a = i / 60 * 2 * math.pi
        r0 = c * (0.80 if i % 5 else 0.74)
        ink.setStrokeWidth(size * (0.012 if i % 5 == 0 else 0.004))
        cv.drawLine(c + math.sin(a) * r0, c - math.cos(a) * r0, c + math.sin(a) * c * 0.88, c - math.cos(a) * c * 0.88, ink)
    tf = skia.Typeface('DejaVu Serif', skia.FontStyle.Bold())
    font = skia.Font(tf, size * 0.1)
    for i in range(1, 13):
        a = i / 12 * 2 * math.pi
        s = str(i)
        wdt = font.measureText(s)
        cv.drawString(s, c + math.sin(a) * c * 0.6 - wdt / 2, c - math.cos(a) * c * 0.6 + size * 0.036, font, ink)
    p = os.path.join(TEX, 'clock_dial.png')
    surf.makeImageSnapshot().save(p, skia.kPNG)
    return p


def record_sleeves(n=5, size=512):
    paths = []
    pals = [('#d9a441', '#2f4858', '#f2e8cf'), ('#7a3b69', '#e8c547', '#1d1d1d'), ('#3d7c74', '#f4d6a6', '#c8553d'),
            ('#264653', '#e76f51', '#e9c46a'), ('#ede0d4', '#9c6644', '#1b263b')]
    for k in range(n):
        a, b, c = [hexrgb(x) for x in pals[k % len(pals)]]
        y, x = np.mgrid[0:size, 0:size] / size
        img = np.ones((size, size, 3)) * a
        if k % 3 == 0:
            d = np.sqrt((x - 0.5) ** 2 + (y - 0.55) ** 2)
            img[d < 0.3] = b
            img[d < 0.12] = c
        elif k % 3 == 1:
            img[(y > 0.3) & (y < 0.45)] = b
            img[(y > 0.55) & (y < 0.62)] = c
        else:
            img[(x + y) % 0.25 < 0.08] = b
            img[np.abs(x - 0.7) < 0.12] = c
        img *= (0.85 + 0.2 * fbm(size, size, 5, 4, seed=20 + k))[..., None]
        paths.append(save(f'sleeve_{k}.png', np.clip(img, 0, 1)))
    return paths


def wood(w=1024, h=1024, seed=1, tone='#8a5a36'):
    n = fbm(h, w, 6, 3, seed=seed)
    y, x = np.mgrid[0:h, 0:w] / h
    grain = 0.5 + 0.5 * np.sin((x * 3 + n * 2.5) * 40)
    base = hexrgb(tone)
    img = base * (0.8 + 0.18 * grain[..., None] + 0.12 * (n[..., None] - 0.5))
    return save(f'wood_{seed}.png', np.clip(img, 0, 1))


def build_all():
    return dict(sky=night_sky(), rain=rain(), rug=rug(), plaster=plaster(), dial=clock_dial(),
                sleeves=record_sleeves(), wood=wood(), wood2=wood(seed=2, tone='#5e3b24'))


if __name__ == '__main__':
    print(build_all())

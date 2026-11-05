"""Adventures of Bo - art module.

Procedural 2.5D art for the animatic: fur sprites, character rigs (eyes,
headphones, beanie, sunglasses), dynamic props and the miniature room set.

Coordinate conventions (shared with timeline.py / render.py):
  * World units; y is negative upward.  Characters stand on the floor at
    depth z (0 = stage line, 1 = back wall).  Perspective scale s(z) and floor
    height yf(z) come from a single horizon model so floor, props and
    characters agree.
  * Character-local space: origin at the ground-contact point (bottom centre),
    y negative upward, unscaled body width W / height H.
"""
import math
import numpy as np
import skia

# --------------------------------------------------------------------------
# Perspective model
# --------------------------------------------------------------------------
YH = -500.0      # horizon (world y)
KZ = 0.6         # depth falloff
WALL_Z = 1.0


def s_of(z):
    return 1.0 / (1.0 + KZ * z)


def yf(z):
    """World y of the floor at depth z."""
    return YH * (1.0 - s_of(z))


WALL_Y = yf(WALL_Z)  # -187.5 : floor/wall junction


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def hexc(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color4f(r / 255, g / 255, b / 255, a)


def c4(rgb, a=1.0):
    return skia.Color4f(float(rgb[0]), float(rgb[1]), float(rgb[2]), float(a))


def col(rgb, a=1.0):
    """Color4f -> packed ARGB int (for gradients)."""
    return c4(rgb, a).toColor()


def hx(h, a=1.0):
    return hexc(h, a).toColor()


def rgb_of(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def paint(color=None, stroke=None, cap=skia.Paint.kRound_Cap, aa=True, shader=None,
          blend=None, blur=None, alpha=None):
    p = skia.Paint(AntiAlias=aa)
    if color is not None:
        p.setColor4f(color if isinstance(color, skia.Color4f) else hexc(color))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if shader is not None:
        p.setShader(shader)
    if blend is not None:
        p.setBlendMode(blend)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if alpha is not None:
        p.setAlphaf(alpha)
    return p


def lin(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], colors, pos)


def rad(c, r, colors, pos=None, m=None):
    if m is not None:
        return skia.GradientShader.MakeRadial(skia.Point(*c), r, colors, pos, skia.TileMode.kClamp, 0, m)
    return skia.GradientShader.MakeRadial(skia.Point(*c), r, colors, pos)


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


def poly_path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class ValueNoise:
    """Cheap smooth 2D noise from a few random sinusoids (deterministic)."""

    def __init__(self, rng, n=4, fmin=0.004, fmax=0.02):
        self.k = [(rng.uniform(fmin, fmax) * math.cos(a), rng.uniform(fmin, fmax) * math.sin(a), rng.uniform(0, 6.283))
                  for a in rng.uniform(0, 6.283, n)]

    def __call__(self, x, y):
        return sum(math.sin(kx * x + ky * y + ph) for kx, ky, ph in self.k) / len(self.k)


# --------------------------------------------------------------------------
# Body shape
# --------------------------------------------------------------------------
def outline_pts(W, H, n=240):
    a, b = W / 2.0, H / 2.0
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        e = 2.9 if s > 0 else 2.15            # flatter seat, rounder dome
        x = a * math.copysign(abs(c) ** (2 / e), c) * (1 + 0.05 * s)
        y = -b + b * math.copysign(abs(s) ** (2 / e), s)
        pts.append((x, y))
    return pts


def half_width_at(W, H, y):
    """Half-width of the body silhouette at local height y (negative up)."""
    b = H / 2.0
    v = (y + b) / b          # -1 top .. +1 bottom
    v = max(-1.0, min(1.0, v))
    e = 2.9 if v > 0 else 2.15
    # invert |s|^(2/e) = |v|  ->  |s| = |v|^(e/2); |c| = sqrt(1-s^2)
    s = abs(v) ** (e / 2)
    c = math.sqrt(max(0.0, 1 - s * s))
    return W / 2.0 * c ** (2 / e) * (1 + 0.05 * math.copysign(s, v))


# --------------------------------------------------------------------------
# Fur sprite
# --------------------------------------------------------------------------
class FurSprite:
    def __init__(self, image, W, H, margin, ppu):
        self.image = image
        self.W, self.H, self.m, self.ppu = W, H, margin, ppu
        self.dst = skia.Rect.MakeLTRB(-W / 2 - margin, -H - margin, W / 2 + margin, margin * 0.35)


def make_fur_sprite(W, H, ppu, base_hex, tip_hex, seed, fur_len=0.055, coverage=4.2, under=0.55,
                    clump=0.22, sheen=0.45, clump_dark=0.12):
    rng = np.random.default_rng(seed)
    m = 0.10 * W
    pw = int(math.ceil((W + 2 * m) * ppu))
    ph = int(math.ceil((H + m + m * 0.35) * ppu))
    surf = skia.Surface(pw, ph)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    cv.translate((W / 2 + m) * ppu, (H + m) * ppu)
    cv.scale(ppu, ppu)

    base = rgb_of(base_hex)
    tip = rgb_of(tip_hex)
    a, b = W / 2.0, H / 2.0
    outline = outline_pts(W, H, 360)

    # undercoat (slightly inset so the silhouette is defined by strands)
    inset = [(x * 0.975, -b + (y + b) * 0.975) for x, y in outline]
    cv.drawPath(poly_path(inset), paint(c4(base * under)))

    noise_a = ValueNoise(rng, 5, 0.008, 0.03)
    noise_v = ValueNoise(rng, 5, 0.01, 0.04)
    L0 = fur_len * W
    px = 1.0 / ppu

    def sample(n, rho_min=0.0):
        """Uniform roots inside the superellipse body; returns x, y, rho, nx, ny."""
        out = []
        while len(out) < n:
            k = int((n - len(out)) * 1.5) + 64
            x = rng.uniform(-a * 1.06, a * 1.06, k)
            y = rng.uniform(-2 * b, 0, k)
            v = (y + b) / b
            e = np.where(v > 0, 2.9, 2.15)
            ae = a * (1 + 0.05 * np.clip(v, -1, 1))
            F = np.abs(x / ae) ** e + np.abs(v) ** e
            rho = F ** (1 / e)
            keep = (rho <= 1.0) & (rho >= rho_min)
            gx = np.sign(x) * np.abs(x / ae) ** (e - 1) / ae
            gy = np.sign(v) * np.abs(v) ** (e - 1) / b
            for i in np.nonzero(keep)[0]:
                out.append((x[i], y[i], rho[i], gx[i], gy[i]))
        return out[:n]

    area_px = math.pi * a * b * ppu * ppu

    def strands(n, len_mul, width_px, vlo, vhi, alpha, tipmix, rho_min=0.0, spread=0.35, nb=18):
        pts = sample(n, rho_min)
        buckets = [skia.Path() for _ in range(nb)]
        for (x, y, rho, nx, ny) in pts:
            ln = math.hypot(nx, ny) + 1e-9
            nx, ny = nx / ln, ny / ln
            k = 0.05 + 1.1 * rho ** 2.2
            ra = rng.uniform(0, 2 * math.pi)
            rr = 0.55 * (1 - rho) ** 1.5
            ang = math.atan2(ny * k + 0.30 + rr * math.sin(ra), nx * k + rr * math.cos(ra))
            ang += noise_a(x, y) * clump * 2.2 + rng.normal(0, spread)
            L = L0 * len_mul * (0.30 + 0.85 * rho * rho) * rng.uniform(0.7, 1.3)
            ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
            bend = rng.normal(0, 0.18) * L
            mx, my = (x + ex) / 2 - math.sin(ang) * bend, (y + ey) / 2 + math.cos(ang) * bend
            i = rng.integers(nb)
            buckets[i].moveTo(x, y)
            buckets[i].quadTo(mx, my, ex, ey)
        for i, path in enumerate(buckets):
            v = vlo + (vhi - vlo) * (i + 0.5) / nb
            cl = np.clip(base * v * (1 - tipmix) + tip * tipmix * (0.6 + 0.4 * v), 0, 1)
            w = width_px * rng.uniform(0.8, 1.2) * px
            cv.drawPath(path, paint(c4(cl, alpha), stroke=w))

    def count(width_px, len_mul, cov):
        return int(cov * area_px / (width_px * L0 * len_mul * 0.8 * ppu))

    strands(count(2.4, 1.0, coverage * 0.9), 1.0, 2.4, 0.50, 0.85, 0.95, 0.0)
    strands(count(1.7, 1.05, coverage), 1.05, 1.7, 0.80, 1.12, 0.88, 0.08)
    strands(count(1.1, 1.15, coverage * 0.55), 1.15, 1.1, 1.0, 1.35, 0.62, sheen)
    # silhouette flyaways
    strands(int(count(1.0, 1.6, coverage) * 0.10), 1.6, 1.0, 0.9, 1.3, 0.5, sheen * 0.8, rho_min=0.9, spread=0.5)

    # clump shading (low-frequency value variation) - SrcATop so it stays on the fur
    cv.save()
    nb = 28
    for _ in range(int(160 * W / 300)):
        x = rng.uniform(-a, a)
        y = rng.uniform(-H, 0)
        r = rng.uniform(0.04, 0.10) * W
        v = noise_v(x, y)
        colr = (0, 0, 0, clump_dark * max(0, v)) if v > 0 else (1, 1, 1, 0.05 * -v)
        cv.drawCircle(x, y, r, paint(skia.Color4f(*colr), blend=skia.BlendMode.kSrcATop, blur=r * 0.5))
    # contact occlusion at the seat
    cv.drawRect(skia.Rect.MakeLTRB(-a * 1.2, -0.22 * H, a * 1.2, m),
                paint(shader=lin((0, -0.22 * H), (0, 0), [hx('#000000', 0), hx('#000000', 0.55)]),
                      blend=skia.BlendMode.kSrcATop))
    cv.restore()

    img = surf.makeImageSnapshot().withDefaultMipmaps()
    return FurSprite(img, W, H, m, ppu)


# --------------------------------------------------------------------------
# Character specs (official palette sampled from the reference art, lifted
# for a warm interior key light)
# --------------------------------------------------------------------------
SPECS = {
    'bo':   dict(W=330, H=300, base='#1f1f24', tip='#60646f', eye_y=0.57, eye_lon=0.25, erx=0.034, ery=0.052,
                 seed=11, fur=0.055, sheen=0.55, under=0.55, squash=1.0),
    'mimi': dict(W=292, H=268, base='#ead3c4', tip='#fffaf4', eye_y=0.46, eye_lon=0.29, erx=0.0, ery=0.0,
                 seed=23, fur=0.05, sheen=0.5, under=0.72, squash=0.9),
    'pip':  dict(W=292, H=272, base='#7a12cc', tip='#b45cff', eye_y=0.58, eye_lon=0.24, erx=0.046, ery=0.064,
                 seed=37, fur=0.062, sheen=0.30, under=0.55, squash=1.3),
    'blu':  dict(W=262, H=242, base='#0638c4', tip='#3f7dff', eye_y=0.56, eye_lon=0.26, erx=0.046, ery=0.066,
                 seed=53, fur=0.052, sheen=0.30, under=0.55, squash=0.7),
}
RING = rgb_of('#e4f1ff')


def build_sprites(ppu_map=None):
    ppu_map = ppu_map or {'bo': 6.0, 'mimi': 3.4, 'pip': 3.4, 'blu': 3.6}
    out = {}
    for k, sp in SPECS.items():
        out[k] = make_fur_sprite(sp['W'], sp['H'], ppu_map[k], sp['base'], sp['tip'], sp['seed'],
                                 fur_len=sp['fur'], sheen=sp['sheen'], under=sp['under'],
                                 clump_dark=0.05 if k == 'mimi' else 0.12)
    return out


# --------------------------------------------------------------------------
# Character drawing
# --------------------------------------------------------------------------
def _sphere_x(W, H, y, lon):
    return half_width_at(W, H, y) * math.sin(lon)


def draw_eye(cv, cx, cy, rx, ry, st, side, style):
    blink = st.get('blink', 0.0)
    lid = st.get('lid', 0.0)
    slant = st.get('slant', 0.0)
    widen = st.get('widen', 0.0)
    rx *= 1 + 0.12 * widen
    ry *= (1 + 0.18 * widen) * (1 - 0.9 * blink)
    if ry < 0.4:
        cv.drawLine(cx - rx, cy, cx + rx, cy, paint('#08080b', stroke=max(0.9, rx * 0.35)))
        return
    eye = skia.Path()
    eye.addOval(oval(cx, cy, rx, ry))
    # socket shadow sinks the eye into the fur
    cv.drawOval(oval(cx, cy + ry * 0.08, rx * 1.35, ry * 1.25), paint(skia.Color4f(0, 0, 0, 0.35), blur=rx * 0.35))
    cv.save()
    cv.clipPath(eye, doAntiAlias=True)
    if lid > 0:
        # upper lid line; slant tilts it inward (determined) - side=-1 left eye
        top = cy - ry
        yl = top + lid * 2 * ry * 0.62
        dy = slant * ry * 0.55 * (-1 if side < 0 else 1)
        lidp = poly_path([(cx - rx * 1.5, top - ry), (cx + rx * 1.5, top - ry),
                          (cx + rx * 1.5, yl - dy), (cx - rx * 1.5, yl + dy)])
        cv.clipPath(lidp, skia.ClipOp.kDifference, True)
    if style == 'pip':
        cv.drawOval(oval(cx, cy, rx, ry), paint('#f6f2f8'))
        cv.drawOval(oval(cx + rx * 0.16, cy - ry * 0.12, rx * 0.97, ry * 0.97),
                    paint(shader=rad((cx + rx * 0.1, cy + ry * 0.35), ry * 1.1, [hx('#2b2833'), hx('#050507')])))
    else:
        cv.drawOval(oval(cx, cy, rx, ry),
                    paint(shader=rad((cx - rx * 0.1, cy + ry * 0.45), ry * 1.15, [hx('#34323d'), hx('#060608')])))
    # specular (fixed world light from upper right) + small fill glint
    cv.drawOval(oval(cx + rx * 0.32, cy - ry * 0.40, rx * 0.30, ry * 0.21), paint('#ffffff', alpha=0.95))
    cv.drawOval(oval(cx - rx * 0.30, cy + ry * 0.42, rx * 0.12, ry * 0.08), paint('#ffffff', alpha=0.45))
    cv.restore()
    if lid > 0.05:
        # lid edge line so the squint reads
        top = cy - ry
        yl = top + lid * 2 * ry * 0.62
        dy = slant * ry * 0.55 * (-1 if side < 0 else 1)
        cv.save()
        cv.clipPath(eye, doAntiAlias=True)
        cv.drawLine(cx - rx * 1.2, yl + dy * 1.2, cx + rx * 1.2, yl - dy * 1.2,
                    paint('#000000', stroke=ry * 0.12, alpha=0.6))
        cv.restore()


def draw_arc_eye(cv, cx, cy, w, h, thick, st):
    blink = st.get('blink', 0.0)
    widen = st.get('widen', 0.0)
    hh = h * (1 + 0.6 * widen) * (1 - 0.55 * blink)
    cy = cy - widen * h * 0.6
    p = skia.Path()
    p.moveTo(cx - w / 2, cy + hh * 0.35)
    p.cubicTo(cx - w * 0.32, cy - hh, cx + w * 0.32, cy - hh, cx + w / 2, cy + hh * 0.35)
    cv.drawPath(p, paint(skia.Color4f(0, 0, 0, 0.25), stroke=thick * 1.8, blur=thick * 0.4))
    cv.drawPath(p, paint('#0b0b0d', stroke=thick))


def draw_eyes(cv, name, sp, st):
    W, H = sp['W'], sp['H']
    yaw = st.get('yaw', 0.0)
    gx, gy = st.get('gx', 0.0), st.get('gy', 0.0)
    ey = -sp['eye_y'] * H + gy * 0.045 * H
    lon0 = sp['eye_lon']
    for side in (-1, 1):
        lon = side * lon0 + yaw + gx * 0.16
        vis = math.cos(lon)
        if vis <= 0.05:
            continue
        ex = _sphere_x(W, H, ey, lon)
        fore = 0.55 + 0.45 * vis
        if name == 'mimi':
            draw_arc_eye(cv, ex, ey, 0.12 * W * fore, 0.034 * W, 0.021 * W, st)
        else:
            draw_eye(cv, ex, ey, sp['erx'] * W * fore, sp['ery'] * W, st, side, 'pip' if name == 'pip' else 'std')


# ---- Bo's headphones ------------------------------------------------------
def bo_cups(sp, st):
    """Return list of cup dicts (screen-local geometry) for both sides."""
    W, H = sp['W'], sp['H']
    yaw = st.get('yaw', 0.0)
    tilt = st.get('tilt', 0.0)
    press = st.get('press', 0.0)
    yc = -0.53 * H
    rc = 0.165 * W
    d = 0.075 * W
    R = half_width_at(W, H, yc)
    cups = []
    for side in (-1, 1):
        th = side * 1.22 + yaw
        # the cup on the side Bo tilts toward is pushed into the fur
        pr = press if (tilt > 0 and side > 0) or (tilt < 0 and side < 0) else 0.0
        Rin = R * (0.97 - 0.06 * pr)
        xi = Rin * math.sin(th)
        xo = (Rin + d) * math.sin(th)
        cups.append(dict(side=side, th=th, xi=xi, xo=xo, y=yc + pr * 0.02 * H, rc=rc, d=d,
                         w=max(0.12, abs(math.cos(th))), front=math.cos(th), press=pr))
    return cups


def draw_cup(cv, cup, W, ring_boost):
    rc = cup['rc']
    y = cup['y']
    xi, xo, w = cup['xi'], cup['xo'], cup['w']
    # contact shadow on fur
    if cup['front'] > -0.2:
        cv.drawOval(oval(xi, y + rc * 0.1, rc * (0.35 + 0.3 * w) + cup['press'] * rc * 0.2, rc * 1.08),
                    paint(skia.Color4f(0, 0, 0, 0.45 + 0.25 * cup['press']), blur=rc * 0.18))
    # cushion (inner) + shell body
    body = skia.Path()
    body.addOval(oval(xi, y, rc * w * 0.98, rc * 0.98))
    body.addOval(oval(xo, y, rc * w, rc))
    body.addRect(skia.Rect.MakeLTRB(min(xi, xo), y - rc * 0.985, max(xi, xo), y + rc * 0.985))
    body.setFillType(skia.PathFillType.kWinding)
    cv.drawPath(body, paint(shader=lin((0, y - rc), (0, y + rc), [hx('#33353c'), hx('#121317'), hx('#08090b')], [0, 0.55, 1])))
    if cup['front'] > -0.05:
        # outer plate
        face = oval(xo, y, rc * w * 0.97, rc * 0.97)
        cv.drawOval(face, paint(shader=rad((xo - rc * w * 0.3, y - rc * 0.4), rc * 1.3,
                                           [hx('#3a3d46'), hx('#15161a'), hx('#0b0b0e')], [0, 0.6, 1])))
        # illuminated ring - subtle, boosts briefly on every Bo boop
        ra = rc * 0.84
        g = 0.55 + 0.45 * ring_boost
        ringp = oval(xo, y, ra * w, ra)
        cv.drawOval(ringp, paint(c4(RING, 0.30 * g), stroke=rc * 0.13, blur=rc * (0.10 + 0.10 * ring_boost)))
        cv.drawOval(ringp, paint(c4(RING, 0.65 + 0.35 * ring_boost), stroke=rc * 0.045))
        # specular on plate
        cv.drawArc(oval(xo, y, rc * w * 0.62, rc * 0.62), 200, 70, False, paint('#ffffff', stroke=rc * 0.04, alpha=0.18))
    # rim highlight on shell
    cv.drawArc(oval(xo, y, rc * w, rc), 215, 80, False, paint('#9aa0ad', stroke=rc * 0.035, alpha=0.35))


def draw_band(cv, sp, cups):
    W, H = sp['W'], sp['H']
    L = min(cups, key=lambda c: c['xi'])
    R = max(cups, key=lambda c: c['xi'])
    top = -H + 0.035 * H
    p = skia.Path()
    x0, y0 = L['xi'] * 0.97, L['y'] - L['rc'] * 0.85
    x1, y1 = R['xi'] * 0.97, R['y'] - R['rc'] * 0.85
    p.moveTo(x0, y0)
    p.cubicTo(x0 * 1.05, top - 0.13 * H, x1 * 1.05, top - 0.13 * H, x1, y1)
    cv.drawPath(p, paint(skia.Color4f(0, 0, 0, 0.45), stroke=0.075 * W, blur=0.02 * W))
    bw = 0.052 * W
    cv.drawPath(p, paint('#0d0e11', stroke=bw * 1.15, cap=skia.Paint.kButt_Cap))
    cv.drawPath(p, paint(shader=lin((0, top - 0.1 * H), (0, y0), [hx('#41444d'), hx('#16171b')]), stroke=bw,
                         cap=skia.Paint.kButt_Cap))
    hl = skia.Path()
    hl.moveTo(x0 * 0.9, y0 - 0.06 * H)
    hl.cubicTo(x0 * 0.98, top - 0.14 * H, x1 * 0.98, top - 0.14 * H, x1 * 0.9, y1 - 0.06 * H)
    cv.drawPath(hl, paint('#8e94a3', stroke=bw * 0.14, alpha=0.45))


# ---- Mimi's beanie ----------------------------------------------------------
def draw_beanie(cv, sp, st):
    W, H = sp['W'], sp['H']
    yaw = st.get('yaw', 0.0)
    y_edge = -0.605 * H
    cuff_h = 0.165 * H
    sag = 0.035 * H
    grow = 1.045
    top = -H * 1.035
    # outline: inflated body silhouette above the edge, crown stretched to `top`
    n = 48
    span = (-H) - y_edge
    k_up = (top - y_edge) / span
    side = []
    for i in range(n + 1):
        y = y_edge + span * (i / n)
        side.append((half_width_at(W, H, y) * grow, y_edge + (y - y_edge) * k_up))
    xr = side[0][0]
    hat = skia.Path()
    hat.moveTo(-xr, y_edge)
    for x, y in side[1:]:
        hat.lineTo(-x, y)
    for x, y in reversed(side[:-1]):
        hat.lineTo(x, y)
    hat.cubicTo(xr * 0.5, y_edge + sag * 1.2, -xr * 0.5, y_edge + sag * 1.2, -xr, y_edge)
    hat.close()
    # shadow cast on fur below the hat
    edge = skia.Path()
    edge.moveTo(-xr, y_edge + 0.01 * H)
    edge.cubicTo(-xr * 0.5, y_edge + sag * 1.3, xr * 0.5, y_edge + sag * 1.3, xr, y_edge + 0.01 * H)
    cv.drawPath(edge, paint(skia.Color4f(0.15, 0.08, 0.05, 0.55), stroke=0.05 * H, blur=0.02 * H))
    cv.drawPath(hat, paint(shader=rad((-0.15 * W, -0.95 * H), 0.9 * W, [hx('#3b3a41'), hx('#1c1b20'), hx('#0d0c0f')],
                                      [0, 0.55, 1])))
    cv.save()
    cv.clipPath(hat, doAntiAlias=True)
    cuff_top = y_edge - cuff_h
    # cuff band (separate fold) with shading line
    fold = skia.Path()
    fold.moveTo(-xr * 1.05, cuff_top)
    fold.cubicTo(-xr * 0.5, cuff_top + sag * 1.15, xr * 0.5, cuff_top + sag * 1.15, xr * 1.05, cuff_top)
    cv.drawPath(fold, paint('#050506', stroke=0.018 * H, alpha=0.8))
    cv.drawPath(fold, paint('#4c4b53', stroke=0.006 * H, alpha=0.5))
    # ribs: meridians projected on the sphere
    for i in range(-14, 15):
        lon = i * 0.13 + yaw
        if math.cos(lon) <= 0.02:
            continue
        vis = math.cos(lon)
        rib = skia.Path()
        ys = np.linspace(y_edge + sag * (1 - min(1, abs(math.sin(lon)) ** 2)) * 1.1, cuff_top + sag * 0.9, 6)
        first = True
        for y in ys:
            yb = y_edge + (y - y_edge) / k_up
            x = half_width_at(W, H, yb) * grow * math.sin(lon)
            if first:
                rib.moveTo(x, y)
                first = False
            else:
                rib.lineTo(x, y)
        cv.drawPath(rib, paint('#4d4c55', stroke=0.011 * W * (0.4 + 0.6 * vis), alpha=0.55 * vis))
        crown = skia.Path()
        ys2 = np.linspace(cuff_top, top + 0.01 * H, 12)
        first = True
        for y in ys2:
            yb = y_edge + (y - y_edge) / k_up
            x = half_width_at(W, H, max(yb, -H)) * grow * math.sin(lon) * 0.97
            if first:
                crown.moveTo(x, y)
                first = False
            else:
                crown.lineTo(x, y)
        cv.drawPath(crown, paint('#3a3940', stroke=0.007 * W * (0.4 + 0.6 * vis), alpha=0.45 * vis))
    cv.restore()
    # smiley patch on the cuff front
    if math.cos(yaw) > 0.1:
        py = y_edge - cuff_h * 0.48 + sag * 0.9
        px = half_width_at(W, H, py) * grow * math.sin(yaw)
        f = math.cos(yaw)
        pw, phh = 0.135 * W * f, 0.12 * W
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(px - pw / 2, py - phh / 2, px + pw / 2, py + phh / 2),
                                  0.018 * W, 0.018 * W)
        cv.drawRRect(r, paint('#0a0a0c'))
        cv.drawRRect(r, paint('#34343a', stroke=0.006 * W))
        ink = paint('#f3f3f3', stroke=0.011 * W)
        cv.drawPoint(px - 0.022 * W * f, py - 0.018 * W, paint('#f3f3f3', stroke=0.014 * W))
        cv.drawPoint(px + 0.022 * W * f, py - 0.018 * W, paint('#f3f3f3', stroke=0.014 * W))
        sm = skia.Path()
        sm.moveTo(px - 0.034 * W * f, py + 0.006 * W)
        sm.quadTo(px, py + 0.042 * W, px + 0.034 * W * f, py + 0.006 * W)
        cv.drawPath(sm, ink)


# ---- Blu's sunglasses -------------------------------------------------------
def glasses_geom(sp, st):
    W, H = sp['W'], sp['H']
    yaw = st.get('yaw', 0.0)
    y = -0.885 * H
    lw, lh = 0.36 * W, 0.15 * W
    lenses = []
    for side in (-1, 1):
        lon = side * 0.47 + yaw * 0.9
        x = half_width_at(W, H, -0.85 * H) * 1.08 * math.sin(lon)
        f = 0.55 + 0.45 * max(0.0, math.cos(lon))
        lenses.append((x, y + 0.02 * H * abs(math.sin(lon)), lw * f, lh, side))
    return lenses


def lens_path(x, y, w, h, side):
    p = skia.Path()
    # slightly trapezoidal wayfarer-ish lens
    t = 0.08 * w
    p.moveTo(x - w / 2 + t * (1 if side < 0 else 0.4), y - h / 2)
    p.lineTo(x + w / 2 - t * (0.4 if side < 0 else 1), y - h / 2)
    p.quadTo(x + w / 2 + t * 0.2, y - h / 2, x + w / 2, y)
    p.quadTo(x + w / 2 - t * 0.5, y + h / 2, x + w * 0.2, y + h / 2)
    p.lineTo(x - w * 0.2, y + h / 2)
    p.quadTo(x - w / 2 + t * 0.5, y + h / 2, x - w / 2, y)
    p.quadTo(x - w / 2 - t * 0.2, y - h / 2, x - w / 2 + t, y - h / 2)
    p.close()
    return p


def draw_glasses_back(cv, sp, st):
    W, H = sp['W'], sp['H']
    for (x, y, w, h, side) in glasses_geom(sp, st):
        ex = x + side * w / 2
        cv.drawLine(ex, y - h * 0.2, ex + side * 0.05 * W, y - 0.09 * H, paint(skia.Color4f(0.85, 0.9, 0.97, 0.45), stroke=0.022 * W))


def draw_glasses(cv, sp, st):
    W, H = sp['W'], sp['H']
    glint = st.get('glint', -1.0)
    g = glasses_geom(sp, st)
    (xl, yl, wl, hl, _), (xr, yr, wr, hr, _) = g
    # contact shadow into the fur
    cv.drawOval(oval((xl + xr) / 2, yl + hl * 0.55, (xr - xl) / 2 + wl * 0.45, hl * 0.35),
                paint(skia.Color4f(0, 0, 0.05, 0.35), blur=hl * 0.25))
    for (x, y, w, h, side) in g:
        p = lens_path(x, y, w, h, side)
        cv.drawPath(p, paint(shader=lin((x, y - h / 2), (x, y + h / 2), [hx('#3a4256', 0.82), hx('#141823', 0.88)])))
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        cv.drawLine(x - w * 0.3, y + h * 0.6, x + w * 0.05, y - h * 0.6, paint('#ffffff', stroke=w * 0.07, alpha=0.18))
        if 0 <= glint <= 1:
            gxp = x - w + glint * 2 * w
            cv.drawLine(gxp - h * 0.4, y + h * 0.7, gxp + h * 0.4, y - h * 0.7, paint('#ffffff', stroke=w * 0.12, alpha=0.55, blur=w * 0.02))
        cv.restore()
        # clear translucent frame
        cv.drawPath(p, paint(skia.Color4f(0.86, 0.91, 0.98, 0.55), stroke=0.026 * W))
        cv.drawPath(p, paint(skia.Color4f(1, 1, 1, 0.55), stroke=0.007 * W))
    # bridge
    br = skia.Path()
    br.moveTo(xl + wl / 2 - 0.01 * W, yl - hl * 0.25)
    br.quadTo((xl + xr) / 2, yl - hl * 0.55, xr - wr / 2 + 0.01 * W, yr - hr * 0.25)
    cv.drawPath(br, paint(skia.Color4f(0.86, 0.91, 0.98, 0.6), stroke=0.024 * W))


# ---- full character ---------------------------------------------------------
def char_matrix(st, sp):
    """Local -> world matrix for a character state."""
    z = st['z']
    s = s_of(z)
    bx = st['x']
    by = yf(z) - (st.get('base', 0.0) + st.get('lift', 0.0)) * s
    m = skia.Matrix()
    m.setTranslate(bx, by)
    m.preScale(s, s)
    m.preRotate(st.get('tilt', 0.0))
    m.preScale(st.get('sx', 1.0), st.get('sy', 1.0))
    return m


def draw_shadow(cv, st, sp, on_floor_y=None):
    z = st['z']
    s = s_of(z)
    W = sp['W']
    lift = st.get('lift', 0.0)
    fy = yf(z) - st.get('base', 0.0) * s if on_floor_y is None else on_floor_y
    k = max(0.15, 1 - lift / 260)
    cv.drawOval(oval(st['x'], fy + 2 * s, W * 0.46 * s * (0.75 + 0.25 * k) * st.get('sx', 1.0), W * 0.07 * s * (0.7 + 0.3 * k)),
                paint(skia.Color4f(0.06, 0.03, 0.02, 0.55 * k), blur=W * 0.045 * s))


def draw_character(cv, name, sprite, st, light_dir=(-0.35, -0.85)):
    sp = SPECS[name]
    if not st.get('visible', True):
        return
    W, H = sp['W'], sp['H']
    cv.save()
    cv.concat(char_matrix(st, sp))
    tilt = st.get('tilt', 0.0)

    cups = None
    if name == 'bo':
        cups = bo_cups(sp, st)
        for c in cups:
            if c['front'] < -0.15:
                draw_cup(cv, c, W, st.get('ring', 0.0))
    if name == 'blu':
        draw_glasses_back(cv, sp, st)

    # fur body with world-fixed key light (SrcATop on its own layer)
    bounds = skia.Rect.MakeLTRB(-W, -H * 1.4, W, H * 0.2)
    cv.saveLayer(bounds, None)
    cv.drawImageRect(sprite.image, sprite.dst, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    lm = skia.Matrix()
    lm.setRotate(-tilt, 0, -H * 0.5)
    key = (light_dir[0] * W * 0.55, -H * 0.5 + light_dir[1] * H * 0.55)
    cv.drawRect(bounds, paint(shader=rad(key, H * 1.15, [hx('#fff1dc', 0.20), hx('#fff1dc', 0.0), hx('#000000', 0.0),
                                                         hx('#05030a', 0.42)], [0, 0.35, 0.6, 1.0], m=lm),
                              blend=skia.BlendMode.kSrcATop))
    cv.restore()

    if name == 'bo':
        draw_band(cv, sp, cups)
        for c in cups:
            if c['front'] >= -0.15:
                draw_cup(cv, c, W, st.get('ring', 0.0))
    if name == 'mimi':
        draw_beanie(cv, sp, st)
    draw_eyes(cv, name, sp, st)
    if name == 'blu':
        draw_glasses(cv, sp, st)
    cv.restore()


def cup_world_pos(st, side=1):
    """World position of one of Bo's earcups (used by the macro camera)."""
    sp = SPECS['bo']
    cups = bo_cups(sp, st)
    c = [c for c in cups if c['side'] == side][0]
    m = char_matrix(st, sp)
    p = m.mapXY((c['xi'] + c['xo']) / 2, c['y'])
    return p.x(), p.y()


def face_world_pos(name, st):
    sp = SPECS[name]
    m = char_matrix(st, sp)
    p = m.mapXY(0, -sp['eye_y'] * sp['H'])
    return p.x(), p.y()

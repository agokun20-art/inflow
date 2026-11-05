"""Adventures of Bo - set design: Bo's miniature bedroom, hallway and props.

The room is painted once into large raster plates (room with a transparent
arched doorway, plus a hallway plate seen through it).  Props that move in
the story (pouf, standing book, book stack, floor cushion, clock hand) are
separate sprites drawn per frame.
"""
import math
import numpy as np
import skia
from art import (hexc, hx, paint, lin, rad, oval, poly_path, s_of, yf, YH, WALL_Y)

ROOM_RECT = (-2000.0, -1300.0, 2150.0, 380.0)   # world L,T,R,B
DOOR = dict(x0=1395.0, x1=1615.0, top=-560.0)  # arched doorway (projected on wall)
CLOCK = (130.0, -830.0, 72.0)
RNG = np.random.default_rng(7)


def floor_pt(G, z, xv=0.0):
    s = s_of(z)
    return xv + (G - xv) * s, yf(z)


# --------------------------------------------------------------------------
# Room plate
# --------------------------------------------------------------------------
def _wall(cv):
    L, T, R, B = ROOM_RECT
    # upper wall: warm apricot-cream with soft vertical stripe paper
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, WALL_Y),
                paint(shader=lin((0, T), (0, WALL_Y), [hx('#b08a6c'), hx('#d4b394'), hx('#d8b89a')], [0, 0.55, 1])))
    x = L
    i = 0
    while x < R:
        w = 44
        if i % 2 == 0:
            cv.drawRect(skia.Rect.MakeLTRB(x, T, x + w, -420), paint('#c7a283', alpha=0.28))
        cv.drawLine(x, T, x, -420, paint('#fff3e2', stroke=1.2, alpha=0.10))
        x += w
        i += 1
    # wainscot (sage panels)
    cv.drawRect(skia.Rect.MakeLTRB(L, -420, R, WALL_Y),
                paint(shader=lin((0, -420), (0, WALL_Y), [hx('#8a9c8b'), hx('#748673')])))
    x = L + 20
    while x < R - 60:
        r = skia.Rect.MakeLTRB(x + 14, -390, x + 186, -228)
        cv.drawRect(r, paint('#5e6f5f', stroke=3, alpha=0.55))
        cv.drawLine(r.left() + 2, r.bottom() + 2, r.right() + 2, r.bottom() + 2, paint('#b9c7b5', stroke=2, alpha=0.4))
        cv.drawLine(r.right() + 2, r.top(), r.right() + 2, r.bottom(), paint('#b9c7b5', stroke=2, alpha=0.3))
        x += 200
    # chair rail + baseboard
    cv.drawRect(skia.Rect.MakeLTRB(L, -436, R, -414), paint(shader=lin((0, -436), (0, -414), [hx('#efe2cc'), hx('#c4b294')])))
    cv.drawRect(skia.Rect.MakeLTRB(L, -414, R, -408), paint('#3d3226', alpha=0.25))
    cv.drawRect(skia.Rect.MakeLTRB(L, WALL_Y - 30, R, WALL_Y),
                paint(shader=lin((0, WALL_Y - 30), (0, WALL_Y), [hx('#eadcc4'), hx('#bba98c')])))


def _floor(cv):
    L, T, R, B = ROOM_RECT
    cv.drawRect(skia.Rect.MakeLTRB(L, WALL_Y, R, B), paint('#9a6a40'))
    # planks converging to the vanishing point (0, YH)
    zs = np.linspace(1.0, -0.75, 2)
    plank = 88.0
    tones = ['#a9774a', '#9c6b41', '#b07e50', '#94653d', '#a57349', '#b5845a']
    G = -4200.0
    k = 0
    while G < 4200:
        p0 = floor_pt(G, 1.0)
        p1 = floor_pt(G + plank, 1.0)
        p2 = floor_pt(G + plank, -0.75)
        p3 = floor_pt(G, -0.75)
        cv.drawPath(poly_path([p0, p1, p2, p3]), paint(tones[k % len(tones)]))
        # subtle grain
        for j in range(3):
            g = G + plank * (0.25 + 0.25 * j)
            a0, a1 = floor_pt(g, 1.0), floor_pt(g, -0.75)
            cv.drawLine(*a0, *a1, paint('#6d4626', stroke=0.8, alpha=0.18))
        # board-end seams
        zseam = 1.0 - (RNG.uniform(0.15, 0.6))
        while zseam > -0.75:
            s0, s1 = floor_pt(G, zseam), floor_pt(G + plank, zseam)
            cv.drawLine(*s0, *s1, paint('#4a2f19', stroke=1.6 * s_of(zseam), alpha=0.6))
            zseam -= RNG.uniform(0.5, 1.0)
        a0, a1 = floor_pt(G, 1.0), floor_pt(G, -0.75)
        cv.drawLine(*a0, *a1, paint('#4a2f19', stroke=1.4, alpha=0.65))
        G += plank
        k += 1
    # rug (perspective ellipse on the floor)
    def rug(cx, cz, rx, rz, color, inset=0.0):
        pts = []
        for i in range(120):
            t = 2 * math.pi * i / 120
            pts.append(floor_pt(cx + (rx - inset) * math.cos(t), cz + (rz - inset / 900) * math.sin(t)))
        cv.drawPath(poly_path(pts), color)
    rug(150, 0.12, 1050, 0.42, paint(skia.Color4f(0, 0, 0, 0.25), blur=6))
    rug(150, 0.12, 1040, 0.41, paint('#efe1c8'))
    rug(150, 0.12, 1000, 0.39, paint('#a9563c'))
    rug(150, 0.12, 900, 0.34, paint('#e7d3b2', stroke=6))
    rug(150, 0.12, 860, 0.32, paint('#b7654a'))
    rug(150, 0.12, 520, 0.18, paint('#d9a77a', stroke=4, alpha=0.7))
    # floor ambient occlusion along the wall
    cv.drawRect(skia.Rect.MakeLTRB(L, WALL_Y, R, WALL_Y + 70),
                paint(shader=lin((0, WALL_Y), (0, WALL_Y + 70), [hx('#1a0f08', 0.45), hx('#1a0f08', 0.0)])))


def _window(cv):
    x0, x1, y0, y1 = -1385.0, -885.0, -1010.0, -520.0
    sky = skia.Rect.MakeLTRB(x0, y0, x1, y1)
    cv.drawRect(sky, paint(shader=lin((0, y0), (0, y1), [hx('#141c3f'), hx('#2b2d5c'), hx('#5d4673'), hx('#c27a63'), hx('#e2a070')],
                                      [0, 0.38, 0.66, 0.9, 1.0])))
    cv.save()
    cv.clipRect(sky)
    for (sx, sy, r) in [(-1300, -960, 1.6), (-1040, -930, 1.2), (-950, -985, 1.4), (-1180, -900, 1.0)]:
        cv.drawCircle(sx, sy, r, paint('#fff6e0', alpha=0.7))
    # far rooftops
    rng = np.random.default_rng(3)
    x = x0 - 20
    while x < x1:
        w = rng.uniform(50, 110)
        h = rng.uniform(40, 130)
        cv.drawRect(skia.Rect.MakeLTRB(x, y1 - h, x + w, y1), paint('#1d1f38'))
        if rng.random() < 0.5:
            cv.drawPath(poly_path([(x - 4, y1 - h), (x + w / 2, y1 - h - rng.uniform(15, 35)), (x + w + 4, y1 - h)]), paint('#1d1f38'))
        for _ in range(int(rng.integers(0, 3))):
            wx, wy = x + rng.uniform(8, w - 16), y1 - rng.uniform(15, h - 10)
            cv.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + 8, wy + 10), paint('#ffcf8a', alpha=0.85))
        x += w - 6
    cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), paint(shader=lin((x0, y0), (x1, y1), [hx('#ffffff', 0.07), hx('#ffffff', 0.0), hx('#ffffff', 0.05)])))
    cv.restore()
    # frame + mullions
    fr = paint('#efe6d6')
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 26, y0 - 26, x1 + 26, y0), fr)
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 26, y0, x0, y1), fr)
    cv.drawRect(skia.Rect.MakeLTRB(x1, y0, x1 + 26, y1), fr)
    cv.drawRect(skia.Rect.MakeLTRB((x0 + x1) / 2 - 8, y0, (x0 + x1) / 2 + 8, y1), fr)
    cv.drawRect(skia.Rect.MakeLTRB(x0, (y0 + y1) / 2 - 7, x1, (y0 + y1) / 2 + 7), fr)
    # sill
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 50, y1, x1 + 50, y1 + 22), paint(shader=lin((0, y1), (0, y1 + 22), [hx('#f6efe2'), hx('#cfc2aa')])))
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 46, y1 + 22, x1 + 46, y1 + 40), paint(skia.Color4f(0.2, 0.12, 0.06, 0.35), blur=6))
    # curtain rod + panels
    cv.drawLine(x0 - 140, y0 - 70, x1 + 140, y0 - 70, paint('#5a3d28', stroke=9))
    for (cx0, cx1) in [(x0 - 130, x0 + 10), (x1 - 10, x1 + 130)]:
        panel = skia.Rect.MakeLTRB(cx0, y0 - 70, cx1, y1 + 70)
        cv.drawRect(panel, paint('#9c4b33'))
        n = 7
        for i in range(n):
            fx = cx0 + (cx1 - cx0) * (i + 0.5) / n
            cv.drawRect(skia.Rect.MakeLTRB(fx - 9, y0 - 70, fx + 9, y1 + 70),
                        paint(shader=lin((fx - 9, 0), (fx + 9, 0), [hx('#6e2f1f', 0.0), hx('#6e2f1f', 0.55), hx('#c86e4f', 0.0)])))
        cv.drawRect(skia.Rect.MakeLTRB(cx0, y1 + 40, cx1, y1 + 70), paint(skia.Color4f(0, 0, 0, 0.12)))
    # window glow onto the wall (cool dusk light)
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 300, y0 - 200, x1 + 300, y1 + 300),
                paint(shader=rad(((x0 + x1) / 2, (y0 + y1) / 2), 520, [hx('#9fb0ff', 0.10), hx('#9fb0ff', 0.0)]), blend=skia.BlendMode.kScreen))


def _bed(cv):
    # headboard against the wall
    hb = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-1650, -640, -945, WALL_Y), 60, 60)
    cv.drawRRect(hb, paint(shader=lin((0, -640), (0, WALL_Y), [hx('#8a5d3c'), hx('#6a4329')])))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-1615, -605, -980, -330), 44, 44), paint('#5a3721', stroke=5, alpha=0.6))
    # bed volume z .55..1.0
    zf = 0.55
    yfront = yf(zf)
    h = 230 * s_of(zf)
    ytop_f = yfront - h
    ytop_b = WALL_Y - 230 * s_of(1.0)
    x0, x1 = -1680.0, -915.0
    # legs
    for lx in (x0 + 25, x1 - 45):
        cv.drawRect(skia.Rect.MakeLTRB(lx, yfront - 30, lx + 20, yfront), paint('#4a2f1d'))
    # top surface sliver + pillow
    cv.drawPath(poly_path([(x0 + 20, ytop_b), (x1 - 20, ytop_b), (x1, ytop_f), (x0, ytop_f)]), paint('#eadcc6'))
    cv.drawOval(skia.Rect.MakeLTRB(-1610, ytop_b - 70, -1380, ytop_f + 8), paint(shader=lin((0, ytop_b - 70), (0, ytop_f), [hx('#fbf3e6'), hx('#d9c9b0')])))
    # quilt front face, patchwork
    qtop, qbot = ytop_f, yfront - 30
    cv.drawRect(skia.Rect.MakeLTRB(x0, qtop, x1, qbot), paint('#d8c6a8'))
    cols = ['#e7d6ba', '#93a58e', '#7f93aa', '#b2664c', '#caa257', '#e7d6ba', '#a3b29b']
    nx, ny = 9, 2
    for i in range(nx):
        for j in range(ny):
            r = skia.Rect.MakeLTRB(x0 + (x1 - x0) * i / nx + 2, qtop + (qbot - qtop) * j / ny + 2,
                                   x0 + (x1 - x0) * (i + 1) / nx - 2, qtop + (qbot - qtop) * (j + 1) / ny - 2)
            cv.drawRect(r, paint(cols[(i * 3 + j * 5) % len(cols)]))
            cv.drawRect(r, paint('#fff8ea', stroke=1.4, alpha=0.5))
    # quilt drape shading (soft, puffy)
    cv.drawRect(skia.Rect.MakeLTRB(x0, qtop, x1, qbot),
                paint(shader=lin((0, qtop), (0, qbot), [hx('#ffffff', 0.12), hx('#000000', 0.0), hx('#2a160a', 0.30)])))
    cv.drawRect(skia.Rect.MakeLTRB(x0, qtop - 4, x1, qtop + 6), paint('#fff6e6', alpha=0.4, blur=3))


def _nightstand(cv):
    zf = 0.62
    yb = yf(zf)
    s = s_of(zf)
    x0, x1 = -890.0, -745.0
    top = yb - 170 * s
    cv.drawRect(skia.Rect.MakeLTRB(x0, top, x1, yb), paint(shader=lin((0, top), (0, yb), [hx('#c39b6d'), hx('#9b7450')])))
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 6, top - 10, x1 + 6, top), paint('#d8b385'))
    cv.drawRect(skia.Rect.MakeLTRB(x0 + 12, top + 25, x1 - 12, top + 70), paint('#8b6443', stroke=3))
    cv.drawCircle((x0 + x1) / 2, top + 47, 4, paint('#e6c99a'))
    # little lamp
    lx = (x0 + x1) / 2
    cv.drawRect(skia.Rect.MakeLTRB(lx - 6, top - 70, lx + 6, top - 10), paint('#7a5a3e'))
    cv.drawOval(oval(lx, top - 12, 26, 7), paint('#6b4c33'))
    shade = poly_path([(lx - 34, top - 70), (lx + 34, top - 70), (lx + 22, top - 125), (lx - 22, top - 125)])
    cv.drawPath(shade, paint(shader=lin((0, top - 125), (0, top - 70), [hx('#ffe2b0'), hx('#ffcf86')])))
    cv.drawRect(skia.Rect.MakeLTRB(lx - 500, top - 600, lx + 500, yb + 200),
                paint(shader=rad((lx, top - 95), 430, [hx('#ffb86a', 0.32), hx('#ffb86a', 0.10), hx('#ffb86a', 0.0)], [0, 0.4, 1]),
                      blend=skia.BlendMode.kScreen))
    cv.drawRect(skia.Rect.MakeLTRB(lx - 34, top - 70, lx + 34, top - 40), paint(shader=lin((0, top - 70), (0, top - 30), [hx('#fff0c8', 0.8), hx('#fff0c8', 0.0)])))


def _bookshelf(cv):
    rng = np.random.default_rng(12)
    cols = ['#7c3b2e', '#c49a49', '#3e5a6e', '#6b7d5a', '#a8664a', '#e1d3b5', '#4c3c5e', '#2f4a45', '#b57a3a']
    for y in (-880.0, -690.0):
        x = -420.0
        while x < -60:
            w = rng.uniform(18, 34)
            h = rng.uniform(95, 140)
            c = cols[int(rng.integers(len(cols)))]
            lean = 0
            if rng.random() < 0.12 and x < -120:
                lean = 12
            r = skia.Rect.MakeLTRB(x, y - h, x + w, y)
            cv.save()
            cv.rotate(lean, x + w, y)
            cv.drawRect(r, paint(shader=lin((x, 0), (x + w, 0), [hx(c), hx(c), hx('#000000', 0.0)])))
            cv.drawRect(r, paint(shader=lin((x, 0), (x + w, 0), [hx('#ffffff', 0.14), hx('#000000', 0.0), hx('#000000', 0.3)])))
            cv.drawRect(skia.Rect.MakeLTRB(x + 3, y - h * 0.8, x + w - 3, y - h * 0.72), paint('#f1e3c4', alpha=0.55))
            cv.restore()
            x += w + (24 if lean else 1.5)
            if rng.random() < 0.08:
                x += 50
        cv.drawRect(skia.Rect.MakeLTRB(-440, y, -40, y + 16), paint(shader=lin((0, y), (0, y + 16), [hx('#c89a68'), hx('#8f6741')])))
        cv.drawRect(skia.Rect.MakeLTRB(-440, y + 16, -40, y + 34), paint(skia.Color4f(0.15, 0.08, 0.03, 0.35), blur=7))
    # plant on top shelf
    px, py = -85.0, -880.0
    cv.drawPath(poly_path([(px - 26, py - 50), (px + 26, py - 50), (px + 19, py), (px - 19, py)]), paint('#c2724e'))
    for i in range(9):
        a = -math.pi / 2 + (i - 4) * 0.33
        L = 70 + 18 * math.sin(i * 2.1)
        cv.drawOval(oval(px + math.cos(a) * L * 0.6, py - 50 + math.sin(a) * L * 0.6, 15, 9), paint('#5d7f4e'))
    # trailing vine
    p = skia.Path()
    p.moveTo(px + 20, py - 40)
    p.cubicTo(px + 60, py + 10, px + 40, py + 120, px + 70, py + 170)
    cv.drawPath(p, paint('#4f6f42', stroke=3))
    for t in np.linspace(0.1, 1, 9):
        x = px + 20 + (50 * t) + 8 * math.sin(t * 9)
        y = py - 40 + 210 * t
        cv.drawOval(oval(x, y, 9, 6), paint('#5f8650'))


def _clock_face(cv):
    cx, cy, r = CLOCK
    cv.drawCircle(cx + 6, cy + 8, r + 6, paint(skia.Color4f(0.15, 0.08, 0.03, 0.35), blur=8))
    cv.drawCircle(cx, cy, r + 8, paint(shader=lin((0, cy - r), (0, cy + r), [hx('#a87a4e'), hx('#6c4a2e')])))
    cv.drawCircle(cx, cy, r, paint('#f5ecd9'))
    for i in range(12):
        a = i * math.pi / 6
        r0 = r * (0.78 if i % 3 else 0.70)
        cv.drawLine(cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9,
                    paint('#3a2c22', stroke=4 if i % 3 == 0 else 2))
    # 7:40 (hour and minute are static in the plate)
    for ang, L, w in [((7 + 40 / 60) / 12 * 360 - 90, 0.48, 6), (40 / 60 * 360 - 90, 0.72, 4)]:
        a = math.radians(ang)
        cv.drawLine(cx, cy, cx + math.cos(a) * r * L, cy + math.sin(a) * r * L, paint('#2a201a', stroke=w))
    cv.drawCircle(cx, cy, r, paint(shader=rad((cx - r * 0.3, cy - r * 0.4), r * 1.2, [hx('#ffffff', 0.25), hx('#ffffff', 0.0)])))


def _desk(cv):
    zf = 0.55
    yb = yf(zf)
    s = s_of(zf)
    x0, x1 = 790.0, 1330.0
    ytop_f = yb - 400 * s
    ytop_b = WALL_Y - 400 * s_of(1.0)
    # back legs (at wall) and under-desk shadow
    cv.drawRect(skia.Rect.MakeLTRB(x0 + 30, ytop_b, x1 - 30, WALL_Y), paint(skia.Color4f(0.12, 0.07, 0.04, 0.45)))
    for lx in (x0 + 34, x1 - 54):
        cv.drawRect(skia.Rect.MakeLTRB(lx, ytop_b, lx + 16, WALL_Y), paint('#6a4a31'))
    # front legs
    for lx in (x0 + 8, x1 - 36):
        cv.drawRect(skia.Rect.MakeLTRB(lx, ytop_f + 40, lx + 28, yb), paint(shader=lin((lx, 0), (lx + 28, 0), [hx('#a77b52'), hx('#7d5838')])))
    cv.drawOval(oval((x0 + x1) / 2, yb + 4, (x1 - x0) / 2 + 20, 16), paint(skia.Color4f(0.1, 0.05, 0.02, 0.35), blur=14))
    # top + apron with drawer
    cv.drawPath(poly_path([(x0 + 16, ytop_b), (x1 - 16, ytop_b), (x1 + 8, ytop_f), (x0 - 8, ytop_f)]), paint('#c99a68'))
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 8, ytop_f, x1 + 8, ytop_f + 14), paint('#a77a4f'))
    cv.drawRect(skia.Rect.MakeLTRB(x0, ytop_f + 14, x1, ytop_f + 44), paint(shader=lin((0, ytop_f + 14), (0, ytop_f + 44), [hx('#b5885d'), hx('#946a44')])))
    cv.drawRect(skia.Rect.MakeLTRB(x0 + 170, ytop_f + 18, x1 - 170, ytop_f + 40), paint('#7a5537', stroke=2))
    cv.drawCircle((x0 + x1) / 2, ytop_f + 29, 4, paint('#e8cfa0'))
    # desk items
    yt = (ytop_f + ytop_b) / 2
    for i, (w, h, c) in enumerate([(140, 22, '#3d5a6c'), (128, 18, '#b9643f'), (134, 16, '#d9c39a')]):
        y = yt - sum(hh for _, hh, _ in [(140, 22, 0), (128, 18, 0), (134, 16, 0)][:i])
        cv.drawRect(skia.Rect.MakeLTRB(860 + i * 4, y - h, 860 + i * 4 + w, y), paint(c))
        cv.drawRect(skia.Rect.MakeLTRB(860 + i * 4 + 4, y - h + 3, 860 + i * 4 + w - 2, y - 3), paint('#f3ead8', alpha=0.25))
    # pencil cup
    cv.drawRect(skia.Rect.MakeLTRB(1050, yt - 64, 1086, yt), paint('#6f8b84'))
    for dx, h, c in [(6, 40, '#e0b84b'), (16, 52, '#c4553b'), (26, 34, '#3f6b8a')]:
        cv.drawLine(1050 + dx, yt - 60, 1050 + dx - 4, yt - 60 - h, paint(c, stroke=5))
    # mug
    cv.drawRect(skia.Rect.MakeLTRB(1100, yt - 40, 1136, yt), paint('#e9e1d2'))
    cv.drawArc(oval(1140, yt - 20, 10, 11), -90, 180, False, paint('#e9e1d2', stroke=5))
    # desk lamp
    bx = 1250.0
    cv.drawOval(oval(bx, yt - 4, 40, 10), paint('#2e3f3a'))
    arm = skia.Path()
    arm.moveTo(bx, yt - 8)
    arm.lineTo(bx + 20, yt - 160)
    arm.lineTo(bx - 70, yt - 240)
    cv.drawPath(arm, paint('#2e3f3a', stroke=9))
    cv.drawCircle(bx + 20, yt - 160, 8, paint('#43584f'))
    shade = poly_path([(bx - 60, yt - 270), (bx - 30, yt - 250), (bx - 85, yt - 175), (bx - 150, yt - 215)])
    cv.drawPath(shade, paint('#33463f'))
    cv.drawOval(oval(bx - 117, yt - 196, 40, 13), paint('#fff2c9'))
    # lamp light pool on desk and wall
    cv.drawRect(skia.Rect.MakeLTRB(bx - 800, yt - 900, bx + 500, yb + 300),
                paint(shader=rad((bx - 130, yt - 120), 600, [hx('#ffc070', 0.38), hx('#ffb460', 0.12), hx('#ffb460', 0.0)], [0, 0.45, 1]),
                      blend=skia.BlendMode.kScreen))
    # framed print above the desk
    fx, fy = 1010.0, -790.0
    cv.drawRect(skia.Rect.MakeLTRB(fx - 86, fy - 110, fx + 86, fy + 110), paint(skia.Color4f(0.1, 0.06, 0.03, 0.3), blur=8))
    cv.drawRect(skia.Rect.MakeLTRB(fx - 80, fy - 104, fx + 80, fy + 104), paint('#3b2b20'))
    cv.drawRect(skia.Rect.MakeLTRB(fx - 66, fy - 90, fx + 66, fy + 90), paint('#efe5d2'))
    cv.drawCircle(fx + 22, fy - 34, 18, paint('#e3a95c'))
    cv.drawPath(poly_path([(fx - 66, fy + 90), (fx - 20, fy + 10), (fx + 10, fy + 50), (fx + 40, fy + 20), (fx + 66, fy + 70), (fx + 66, fy + 90)]), paint('#7d9a86'))


def _doorway(cv):
    x0, x1, top = DOOR['x0'], DOOR['x1'], DOOR['top']
    cxa = (x0 + x1) / 2
    ra = (x1 - x0) / 2
    p = skia.Path()
    p.moveTo(x0, WALL_Y)
    p.lineTo(x0, top + ra)
    p.arcTo(skia.Rect.MakeLTRB(x0, top, x1, top + 2 * ra), 180, 180, False)
    p.lineTo(x1, WALL_Y)
    p.close()
    # molding
    mold = skia.Path()
    mold.moveTo(x0 - 26, WALL_Y)
    mold.lineTo(x0 - 26, top + ra)
    mold.arcTo(skia.Rect.MakeLTRB(x0 - 26, top - 26, x1 + 26, top + 2 * ra + 26), 180, 180, False)
    mold.lineTo(x1 + 26, WALL_Y)
    mold.close()
    cv.drawPath(mold, paint(skia.Color4f(0.12, 0.07, 0.03, 0.35), blur=10))
    cv.drawPath(mold, paint('#eee3cf'))
    cv.drawPath(mold, paint('#bfae90', stroke=3))
    # punch the opening (transparent) so the hallway plate shows through
    cv.drawPath(p, paint(skia.Color4f(0, 0, 0, 0), blend=skia.BlendMode.kClear))
    return p


def _global_light(cv):
    L, T, R, B = ROOM_RECT
    # ceiling falloff and corner darkening (multiply)
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B),
                paint(shader=lin((0, T), (0, -500), [hx('#2b1a10', 0.55), hx('#2b1a10', 0.0)]), blend=skia.BlendMode.kSrcATop))
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B),
                paint(shader=lin((L, 0), (L + 700, 0), [hx('#1c120c', 0.45), hx('#1c120c', 0.0)]), blend=skia.BlendMode.kSrcATop))
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B),
                paint(shader=lin((R, 0), (R - 500, 0), [hx('#1c120c', 0.4), hx('#1c120c', 0.0)]), blend=skia.BlendMode.kSrcATop))
    cv.drawRect(skia.Rect.MakeLTRB(L, 120, R, B),
                paint(shader=lin((0, 120), (0, B), [hx('#1c120c', 0.0), hx('#1c120c', 0.45)]), blend=skia.BlendMode.kSrcATop))
    # evening: overall exposure down, lamp pools stay
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B), paint(skia.Color4f(0.10, 0.05, 0.03, 0.16), blend=skia.BlendMode.kSrcATop))
    # warm room fill
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B),
                paint(shader=rad((-150, -350), 1500, [hx('#ffb070', 0.10), hx('#ffb070', 0.0)]), blend=skia.BlendMode.kScreen))


def build_room_plate(ppu=2.0):
    L, T, R, B = ROOM_RECT
    w, h = int((R - L) * ppu), int((B - T) * ppu)
    surf = skia.Surface(w, h)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    cv.scale(ppu, ppu)
    cv.translate(-L, -T)
    _wall(cv)
    _floor(cv)
    _window(cv)
    _bookshelf(cv)
    _clock_face(cv)
    _bed(cv)
    _nightstand(cv)
    _desk(cv)
    _global_light(cv)
    _doorway(cv)
    return surf.makeImageSnapshot().withDefaultMipmaps()


def build_hall_plate(ppu=2.0):
    """Dim, cool hallway seen through the doorway; a faint warm glow far away."""
    L, T, R, B = 1300.0, -700.0, 1720.0, -150.0
    w, h = int((R - L) * ppu), int((B - T) * ppu)
    surf = skia.Surface(w, h)
    cv = surf.getCanvas()
    cv.scale(ppu, ppu)
    cv.translate(-L, -T)
    cx = 1505.0
    vy = YH
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B), paint('#2c2f3d'))
    # corridor: floor recedes from wall line to end wall (z=3)
    zend = 3.2
    yend = yf(zend)
    half0, half1 = 150.0, 150.0 * s_of(zend) / s_of(1.0)
    cv.drawPath(poly_path([(cx - half0, WALL_Y), (cx + half0, WALL_Y), (cx + half1, yend), (cx - half1, yend)]),
                paint(shader=lin((0, WALL_Y), (0, yend), [hx('#4b3b2e'), hx('#2b231d')])))
    for g in np.linspace(-1, 1, 6):
        cv.drawLine(cx + g * half0, WALL_Y, cx + g * half1, yend, paint('#1e1813', stroke=1.4, alpha=0.6))
    # side walls
    cv.drawPath(poly_path([(L, T), (cx - half1, yend - 300), (cx - half1, yend), (cx - half0, WALL_Y), (L, WALL_Y)]),
                paint(shader=lin((L, 0), (cx, 0), [hx('#2a2d3b'), hx('#3a3e50')])))
    cv.drawPath(poly_path([(R, T), (cx + half1, yend - 300), (cx + half1, yend), (cx + half0, WALL_Y), (R, WALL_Y)]),
                paint(shader=lin((R, 0), (cx, 0), [hx('#24263a'), hx('#33374a')])))
    # end wall with a far doorway glowing warm
    cv.drawRect(skia.Rect.MakeLTRB(cx - half1, yend - 300, cx + half1, yend), paint('#3d4154'))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - 26, yend - 95, cx + 26, yend), 26, 26), paint('#f2b86e', alpha=0.85))
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B), paint(shader=rad((cx, yend - 40), 220, [hx('#f2a85e', 0.28), hx('#f2a85e', 0.0)]),
                                                     blend=skia.BlendMode.kScreen))
    # open door leaf against the left jamb
    cv.drawPath(poly_path([(1398, WALL_Y), (1398, -540), (1440, -500), (1440, WALL_Y - 22)]), paint('#6b4a33'))
    cv.drawPath(poly_path([(1398, WALL_Y), (1398, -540), (1440, -500), (1440, WALL_Y - 22)]), paint('#3a281b', stroke=2))
    # overall dimness
    cv.drawRect(skia.Rect.MakeLTRB(L, T, R, B), paint(shader=lin((0, T), (0, B), [hx('#05060c', 0.55), hx('#05060c', 0.25)])))
    img = surf.makeImageSnapshot().withDefaultMipmaps()
    return img, skia.Rect.MakeLTRB(L, T, R, B)


# --------------------------------------------------------------------------
# Dynamic props (sprites in prop-local space: origin at floor contact centre)
# --------------------------------------------------------------------------
class Prop:
    def __init__(self, image, rect):
        self.image, self.rect = image, rect


def _sprite(w, h, draw, ppu=3.0, pad=30):
    W, H = int((w + 2 * pad) * ppu), int((h + 2 * pad) * ppu)
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    cv.scale(ppu, ppu)
    cv.translate(w / 2 + pad, h + pad)
    draw(cv)
    return Prop(surf.makeImageSnapshot().withDefaultMipmaps(), skia.Rect.MakeLTRB(-w / 2 - pad, -h - pad, w / 2 + pad, pad))


def make_props():
    props = {}

    def pouf(cv):
        w, h = 400, 78
        cv.drawOval(oval(0, -h + 26, w / 2, 26), paint('#7d9a8f'))
        body = skia.Path()
        body.moveTo(-w / 2, -h + 26)
        body.cubicTo(-w / 2 - 10, -10, -w / 2 + 30, 0, 0, 0)
        body.cubicTo(w / 2 - 30, 0, w / 2 + 10, -10, w / 2, -h + 26)
        body.close()
        cv.drawPath(body, paint(shader=lin((0, -h), (0, 0), [hx('#6f8c80'), hx('#4d675d')])))
        for i in range(-9, 10):
            x = i * w / 20
            cv.drawLine(x, -h + 28 + abs(i) * 0.6, x * 1.02, -4, paint('#3e554c', stroke=2, alpha=0.35))
        cv.drawOval(oval(0, -h + 26, w / 2, 26), paint(shader=rad((-60, -h + 18), w / 2, [hx('#9db8ad'), hx('#7d9a8f')])))
        for r in (0.7, 0.45, 0.2):
            cv.drawOval(oval(0, -h + 26, w / 2 * r, 26 * r), paint('#5f7b70', stroke=2, alpha=0.4))
    props['pouf'] = _sprite(400, 78, pouf)

    def standing_book(cv):
        w, h = 180, 250
        cv.drawRect(skia.Rect.MakeLTRB(w / 2 - 6, -h + 4, w / 2 + 22, -2), paint('#e8dcc0'))
        for i in range(8):
            cv.drawLine(w / 2 - 4 + i * 3.2, -h + 8, w / 2 - 4 + i * 3.2, -6, paint('#b9a885', stroke=0.8))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, 0), 6, 6),
                     paint(shader=lin((-w / 2, 0), (w / 2, 0), [hx('#2c5559'), hx('#36686b'), hx('#24484b')], [0, 0.35, 1])))
        cv.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, -w / 2 + 16, 0), paint('#1e3c3f', alpha=0.7))
        cv.drawRect(skia.Rect.MakeLTRB(-w / 2 + 34, -h + 44, w / 2 - 22, -h + 90), paint('#e9dcbc'))
        cv.drawCircle(4, -h * 0.42, 34, paint('#e6b960'))
        cv.drawCircle(18, -h * 0.42 - 8, 30, paint('#36686b'))
    props['book'] = _sprite(180 + 50, 250, standing_book)

    def flat_book(color, w, h):
        def d(cv):
            cv.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, 0), paint(color))
            cv.drawRect(skia.Rect.MakeLTRB(-w / 2 + 10, -h + 5, w / 2 - 6, -5), paint('#efe4cc'))
            for i in range(4):
                y = -h + 7 + i * (h - 14) / 4
                cv.drawLine(-w / 2 + 12, y, w / 2 - 8, y, paint('#c8b894', stroke=0.8))
            cv.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, -w / 2 + 12, 0), paint(color))
            cv.drawRect(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, -h + 4), paint('#ffffff', alpha=0.15))
        return d
    props['b1'] = _sprite(232, 44, flat_book('#8f4433', 232, 44))
    props['b2'] = _sprite(212, 38, flat_book('#c0913c', 212, 38))
    props['b3'] = _sprite(222, 40, flat_book('#34476a', 222, 40))

    def cushion(cv):
        w, h = 260, 120
        p = skia.Path()
        p.moveTo(-w / 2 + 18, -h)
        p.quadTo(0, -h - 14, w / 2 - 18, -h)
        p.quadTo(w / 2 + 12, -h / 2, w / 2 - 6, 0)
        p.quadTo(0, 10, -w / 2 + 6, 0)
        p.quadTo(-w / 2 - 12, -h / 2, -w / 2 + 18, -h)
        p.close()
        cv.drawPath(p, paint(shader=lin((0, -h), (0, 0), [hx('#d9a75a'), hx('#b9853d'), hx('#93652a')], [0, 0.6, 1])))
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            cv.drawLine(0, -h / 2, math.cos(a) * w, -h / 2 + math.sin(a) * h, paint('#7a5220', stroke=6, alpha=0.18, blur=5))
        cv.drawOval(oval(-40, -h * 0.78, 90, 30), paint('#ffe2a8', alpha=0.25, blur=14))
        cv.restore()
        cv.drawPath(p, paint('#8c5f27', stroke=4))
        cv.drawCircle(0, -h / 2, 8, paint('#8c5f27'))
        cv.drawCircle(-2, -h / 2 - 2, 4, paint('#d9a75a'))
    props['cushion'] = _sprite(280, 130, cushion)
    return props


def draw_prop(cv, prop, x, z, sx=1.0, sy=1.0, rot=0.0, lift=0.0, shadow=0.5, shadow_w=None):
    s = s_of(z)
    y = yf(z)
    if shadow > 0:
        sw = (shadow_w or prop.rect.width() * 0.45) * s * sx
        cv.drawOval(oval(x, y + 2 * s, sw, sw * 0.13), paint(skia.Color4f(0.06, 0.03, 0.02, shadow), blur=14 * s))
    cv.save()
    cv.translate(x, y - lift * s)
    cv.scale(s, s)
    cv.rotate(rot)
    cv.scale(sx, sy)
    cv.drawImageRect(prop.image, prop.rect, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    cv.restore()


def draw_clock_hand(cv, t):
    cx, cy, r = CLOCK
    sec = math.floor(t + 0.0001) + 23  # ticks once per second, synced to SFX
    a = math.radians(sec * 6 - 90)
    cv.drawLine(cx - math.cos(a) * r * 0.15, cy - math.sin(a) * r * 0.15, cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82,
                paint('#b0402c', stroke=2.2))
    cv.drawCircle(cx, cy, 5, paint('#2a201a'))

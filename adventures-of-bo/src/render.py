"""Adventures of Bo - animatic renderer.

usage:
  python render.py stills 13.2 37.6 ...        # review frames -> output/stills/
  python render.py contact                      # one frame per shot -> output/storyboard_contact_sheet.png
  python render.py video [--workers 4]          # full 120 s picture -> output/_video_only.mp4
"""
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(__file__))
import timeline as TL  # noqa: E402
from art import (SPECS, build_sprites, draw_character, draw_shadow, hexc, hx, paint, rad, lin, s_of, RING,
                 c4)  # noqa: E402
from set_design import (ROOM_RECT, build_room_plate, build_hall_plate, make_props, draw_prop,
                        draw_clock_hand)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'output')
W, H = 1920, 1080
BAR = 138                      # 2.39:1 active picture inside 16:9
ACTIVE = skia.Rect.MakeLTRB(0, BAR, W, H - BAR)
SO = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


class Assets:
    def __init__(self):
        self.sprites = build_sprites()
        self.room = build_room_plate()
        self.hall, self.hall_rect = build_hall_plate()
        self.props = make_props()
        self.surf = skia.Surface(W, H)
        self.bg = skia.Surface(W, H)
        self.layer = skia.Surface(W, H)
        rng = np.random.default_rng(5)
        self.grain = [rng.normal(0, 1, (H - 2 * BAR, W, 1)).astype(np.float32) for _ in range(8)]
        yy, xx = np.mgrid[0:H - 2 * BAR, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - (H - 2 * BAR) / 2) / ((H - 2 * BAR) * 0.78)) ** 2)
        self.vignette = (1 - 0.30 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None].astype(np.float32)
        self.title_tf = skia.Typeface('Inter Display', skia.FontStyle(800, 5, skia.FontStyle.kUpright_Slant))
        self.sub_tf = skia.Typeface('Inter Display', skia.FontStyle(500, 5, skia.FontStyle.kUpright_Slant))


def cam_matrix(cx, cy, zm):
    m = skia.Matrix()
    m.setTranslate(W / 2, H / 2)
    m.preScale(zm, zm)
    m.preTranslate(-cx, -cy)
    return m


def draw_background(cv, A, t, states):
    cv.drawImageRect(A.hall, A.hall_rect, SO)
    far = [(n, st) for n, st in states.items() if st['visible'] and st['z'] > 1.0]
    for n, st in sorted(far, key=lambda kv: -kv[1]['z']):
        draw_shadow(cv, st, SPECS[n])
        draw_character(cv, n, A.sprites[n], st)
    cv.drawImageRect(A.room, skia.Rect.MakeLTRB(*ROOM_RECT), SO)
    draw_clock_hand(cv, t)


def draw_midground(cv, A, t, states, P, shot, zm):
    items = []
    items.append((0.10, 0, lambda: draw_prop(cv, A.props['pouf'], -550, 0.10, sy=P['pouf_sy'], shadow=0.45)))
    items.append((0.30, 0, lambda: draw_prop(cv, A.props['book'], -250, 0.30, shadow=0.4)))

    def stack():
        draw_prop(cv, A.props['b1'], 60, 0.45, shadow=0.4)
        draw_prop(cv, A.props['b2'], 52, 0.45, lift=44, shadow=0)
        draw_prop(cv, A.props['b3'], 66 + P['top_dx'], 0.45, lift=82, shadow=0)
    items.append((0.45, 0, stack))
    items.append((P['cushion_z'], 0, lambda: draw_prop(cv, A.props['cushion'], P['cushion_x'], P['cushion_z'], sx=P['cushion_sx'],
                                                       sy=P['cushion_sy'], rot=P['cushion_rot'], shadow=0.45, shadow_w=125)))
    for n, st in states.items():
        if not st['visible'] or st['z'] > 1.0:
            continue
        def dc(n=n, st=st):
            blur = shot.cblur and shot.focus and n not in shot.focus
            if blur:
                cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(shot.cblur / zm, shot.cblur / zm)))
            draw_shadow(cv, st, SPECS[n])
            draw_character(cv, n, A.sprites[n], st)
            if blur:
                cv.restore()
        items.append((st['z'], 1, dc))
    for _, _, fn in sorted(items, key=lambda it: (-it[0], it[1])):
        fn()


def draw_end_card(cv, A, t):
    cv.clear(skia.Color4f(0, 0, 0, 1))
    u = t - TL.END_CARD_T
    a1 = min(1.0, max(0.0, (u - 0.4) / 0.6))
    a2 = min(1.0, max(0.0, (u - 0.9) / 0.5))
    rise = (1 - a1) ** 2 * 10
    title = 'ADVENTURES OF BO'
    f1 = skia.Font(A.title_tf, 92)
    track = 92 * 0.07
    widths = [f1.measureText(ch) for ch in title]
    total = sum(widths) + track * (len(title) - 1)
    x = W / 2 - total / 2
    y = H / 2 + 18 + rise
    p = paint(skia.Color4f(0.965, 0.96, 0.95, a1))
    for ch, w in zip(title, widths):
        cv.drawString(ch, x, y, f1, p)
        x += w + track
    sub = 'A BOOPMO ORIGINAL'
    f2 = skia.Font(A.sub_tf, 24)
    tr2 = 24 * 0.42
    w2 = [f2.measureText(ch) for ch in sub]
    tot2 = sum(w2) + tr2 * (len(sub) - 1)
    x = W / 2 - tot2 / 2
    p2 = paint(skia.Color4f(0.72, 0.74, 0.78, a2))
    for ch, w in zip(sub, w2):
        cv.drawString(ch, x, H / 2 + 86, f2, p2)
        x += w + tr2
    # Bo's headphone ring as the series mark - it flickers with the final boop
    tb = 119.0
    flash = math.exp(-(t - tb) / 0.22) if t >= tb else 0.0
    ra = min(1.0, max(0.0, (u - 0.2) / 0.6))
    cx, cy = W / 2, H / 2 - 96 + rise
    cv.drawOval(skia.Rect.MakeLTRB(cx - 22, cy - 22, cx + 22, cy + 22),
                paint(c4(RING, (0.25 + 0.5 * flash) * ra), stroke=7, blur=5 + 6 * flash))
    cv.drawOval(skia.Rect.MakeLTRB(cx - 22, cy - 22, cx + 22, cy + 22), paint(c4(RING, (0.75 + 0.25 * flash) * ra), stroke=2.4))


def render_frame(A, t, fidx=0, grade=True):
    cv = A.surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 1))
    if t >= TL.END_CARD_T:
        draw_end_card(cv, A, t)
        img = A.surf.makeImageSnapshot()
        return img.toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    shot = TL.shot_at(t)
    cx, cy, zm = shot.cam(t)
    M = cam_matrix(cx, cy, zm)
    states = {n: c.state(t) for n, c in TL.CHARS.items()}
    P = TL.props_at(t)
    cv.save()
    cv.clipRect(ACTIVE)
    if shot.dof > 0:
        bc = A.bg.getCanvas()
        bc.clear(skia.Color4f(0, 0, 0, 1))
        bc.save()
        bc.concat(M)
        draw_background(bc, A, t, states)
        bc.restore()
        cv.drawImage(A.bg.makeImageSnapshot(), 0, 0, SO, skia.Paint(ImageFilter=skia.ImageFilters.Blur(shot.dof, shot.dof)))
    else:
        cv.save()
        cv.concat(M)
        draw_background(cv, A, t, states)
        cv.restore()
    cv.concat(M)
    draw_midground(cv, A, t, states, P, shot, zm)
    cv.restore()
    arr = A.surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    if not grade:
        return arr
    # grade: warm lift, gentle contrast, vignette, grain; fade-in at head
    a = arr[BAR:H - BAR].astype(np.float32) / 255.0
    a = np.clip(a * np.array([1.02, 1.0, 0.965], np.float32) + np.array([0.012, 0.006, 0.0], np.float32), 0, 1)
    a = a * a * (3 - 2 * a) * 0.22 + a * 0.78
    a *= A.vignette
    a += A.grain[fidx % 8] * 0.012
    fade = min(1.0, max(0.0, t / 1.6)) ** 1.5
    a *= fade
    arr = arr.copy()
    arr[BAR:H - BAR] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    arr[:BAR] = 0
    arr[H - BAR:] = 0
    return arr


def _worker(args):
    k, f0, f1, path = args
    A = Assets()
    ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(TL.FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-tune', 'animation',
                           '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        ff.stdin.write(render_frame(A, f / TL.FPS, f).tobytes())
        if (f - f0) % 120 == 0:
            print(f'[w{k}] frame {f} ({f - f0}/{f1 - f0}) {time.time() - t0:.0f}s', flush=True)
    ff.stdin.close()
    ff.wait()
    return path


def video(workers=4):
    from multiprocessing import Pool
    os.makedirs(os.path.join(OUT, '_segments'), exist_ok=True)
    n = int(TL.DUR * TL.FPS)
    bounds = [round(n * i / workers) for i in range(workers + 1)]
    jobs = [(k, bounds[k], bounds[k + 1], os.path.join(OUT, '_segments', f'seg{k}.mp4')) for k in range(workers)]
    with Pool(workers) as p:
        paths = p.map(_worker, jobs)
    lst = os.path.join(OUT, '_segments', 'list.txt')
    with open(lst, 'w') as fh:
        fh.writelines(f"file '{p}'\n" for p in paths)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    os.path.join(OUT, '_video_only.mp4')], check=True)


def stills(times, tag='still'):
    from PIL import Image
    d = os.path.join(OUT, 'stills')
    os.makedirs(d, exist_ok=True)
    A = Assets()
    for t in times:
        arr = render_frame(A, t, int(t * TL.FPS))
        Image.fromarray(arr).save(os.path.join(d, f'{tag}_{t:06.2f}.png'))
    return d


def contact_sheet():
    """Storyboard: one representative frame per shot with ID, timecode and action."""
    from PIL import Image, ImageDraw, ImageFont
    A = Assets()
    picks = {'2A': 13.3, '2B': 23.0, '3A': 28.5, '3B': 32.8, '3C': 38.5, '4A': 42.4, '4B': 45.6, '4C': 49.8, '4D': 52.7,
             '5B': 61.1, '5C': 63.7, '6A': 72.3, '6B': 74.9, '6C': 79.2, '6D': 83.8, '7A': 87.05, '7B': 92.3, '7C': 95.2,
             '7D': 98.6, '8A': 104.0, '8B': 109.3, '8C': 111.0, '9A': 116.6, '9B': 119.1, '1A': 5.5, '1B': 9.0,
             '5A': 57.0, '5D': 65.6, '5E': 68.8}
    cols, tw = 3, 620
    th = int(tw * (H - 2 * BAR) / W)
    cap = 84
    rows = math.ceil(len(TL.SHOTS) / cols)
    sheet = Image.new('RGB', (cols * tw + (cols + 1) * 16, rows * (th + cap) + (rows + 1) * 16 + 70), (18, 18, 20))
    dr = ImageDraw.Draw(sheet)
    fb = ImageFont.truetype(_font_path('Inter', 'Bold'), 30)
    fs = ImageFont.truetype(_font_path('Inter', 'Regular'), 15)
    fm = ImageFont.truetype(_font_path('Inter', 'SemiBold'), 16)
    dr.text((16, 18), 'ADVENTURES OF BO  ·  Ep.1 "The Mysterious Boop"  ·  Animatic storyboard (29 shots, 120 s)', font=fb, fill=(240, 240, 236))
    for i, s in enumerate(TL.SHOTS):
        t = picks.get(s.sid, (s.t0 + s.t1) / 2)
        arr = render_frame(A, t, int(t * TL.FPS))
        im = Image.fromarray(arr[BAR:H - BAR] if s.sid != '9B' else arr[BAR:H - BAR]).resize((tw, th), Image.LANCZOS)
        x = 16 + (i % cols) * (tw + 16)
        y = 70 + 16 + (i // cols) * (th + cap + 16)
        sheet.paste(im, (x, y))
        tc = f'{int(s.t0 // 60)}:{s.t0 % 60:05.2f}-{int(s.t1 // 60)}:{s.t1 % 60:05.2f}'
        dr.text((x, y + th + 6), f'{s.sid}  {tc}  ·  {s.size}', font=fm, fill=(236, 214, 170))
        words, lines, cur = s.action.split(), [], ''
        for wd in words:
            trial = (cur + ' ' + wd).strip()
            if dr.textlength(trial, font=fs) <= tw - 4:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
        if len(lines) > 2:
            lines = lines[:2]
            while dr.textlength(lines[1] + '...', font=fs) > tw - 4:
                lines[1] = lines[1].rsplit(' ', 1)[0]
            lines[1] += '...'
        for li, ln in enumerate(lines):
            dr.text((x, y + th + 30 + 20 * li), ln, font=fs, fill=(200, 200, 200))
    p = os.path.join(OUT, 'storyboard_contact_sheet.png')
    sheet.save(p)
    return p


def _font_path(family, style):
    out = subprocess.run(['fc-match', '-f', '%{file}', f'{family}:style={style}'], capture_output=True, text=True).stdout
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'stills':
        print(stills([float(x) for x in sys.argv[2:]]))
    elif cmd == 'contact':
        print(contact_sheet())
    elif cmd == 'video':
        w = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
        t = time.time()
        video(w)
        print('video done', round(time.time() - t), 's')

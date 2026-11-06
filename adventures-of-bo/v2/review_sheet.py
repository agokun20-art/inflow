"""Per-shot strips from rendered frames: python review_sheet.py <dir> <out.png> [frames_per_shot]"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_stakeout as A
d, out = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 6
avail = sorted(int(f[2:6]) for f in os.listdir(d) if f.startswith('f_'))
rows = []
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
for s in A.SHOTS:
    fr = [f for f in avail if s.t0 * 24 <= f < s.t1 * 24]
    if not fr: continue
    pick = [fr[round(i * (len(fr) - 1) / max(1, k - 1))] for i in range(min(k, len(fr)))]
    ims = [Image.open(os.path.join(d, f'f_{f:04d}.png')).convert('RGB') for f in pick]
    w, h = ims[0].size; tw = 300; th = int(h * tw / w)
    row = Image.new('RGB', (k * (tw + 4) + 150, th + 4), (20, 20, 22))
    dr = ImageDraw.Draw(row)
    dr.text((6, 6), f'SH{s.sid}\n{s.t0:.2f}-{s.t1:.2f}s', font=font, fill=(240, 220, 170))
    for i, (im, f) in enumerate(zip(ims, pick)):
        row.paste(im.resize((tw, th)), (150 + i * (tw + 4), 2))
        dr.text((150 + i * (tw + 4) + 4, 4), f'{f/24:.2f}s', font=font, fill=(255, 255, 255))
    rows.append(row)
W = max(r.width for r in rows); Hh = sum(r.height for r in rows)
S = Image.new('RGB', (W, Hh), (0, 0, 0)); y = 0
for r in rows: S.paste(r, (0, y)); y += r.height
S.save(out); print(out, S.size)

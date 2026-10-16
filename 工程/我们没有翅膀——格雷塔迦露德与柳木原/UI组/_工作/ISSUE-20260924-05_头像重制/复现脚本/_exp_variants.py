# -*- coding: utf-8 -*-
"""临时实验：两种定框规则在全部 35 族上的观感对照（只写 _exp 目录，不碰 face/）。"""
import os
import sys
import collections
import re
from PIL import Image, ImageDraw

D1 = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\立绘"
D2 = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一_超分\立绘"
OUT = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作\ISSUE-20260924-05_头像重制\证据\_exp"
os.makedirs(OUT, exist_ok=True)
BW, BH = 276, 345
PAT = re.compile(r"^([a-z_]+?)(\d*)([a-z_]*)$")
K = 0.575


def rows_of(im):
    a = im.getchannel("A"); W, H = im.size; out = []
    for y in range(H):
        xs = [x for x in range(W) if a.getpixel((x, y)) > 8]
        out.append((y, xs[0], xs[-1], len(xs)) if len(xs) >= 2 else (y, 0, 0, 0))
    return [r for r in out if r[3] > 0]


def band_span(rows, y0, y1):
    sel = [r for r in rows if y0 <= r[0] <= y1]
    return (min(r[1] for r in sel), max(r[2] for r in sel)) if sel else (0, 0)


def crop_2x(name, x0, y0, w, h):
    im2 = Image.open(os.path.join(D2, name + ".png")).convert("RGBA"); W2, H2 = im2.size
    x0 = max(-w + 1, min(x0, W2 // 2 - 1)); y0 = max(-h + 1, min(y0, H2 // 2 - 1))
    c = im2.crop((max(0, x0) * 2, max(0, y0) * 2, min(W2, (x0 + w) * 2), min(H2, (y0 + h) * 2)))
    cv = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    cv.paste(c, (max(0, -x0) * 2, max(0, -y0) * 2))
    return cv.resize((BW, BH), Image.LANCZOS)


def is_sprite(p):
    with Image.open(p) as im:
        W, H = im.size
    return not (W == 1280 and H == 720) and H > W


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "A"   # A=纯 K 规则, B=K+band 装箱, C=K+下半段装箱
    files = sorted(x[:-4] for x in os.listdir(D1) if x.endswith(".png"))
    fam = collections.defaultdict(lambda: collections.defaultdict(list))
    for n in files:
        m = PAT.match(n)
        if not m:
            continue
        f, b, s = m.group(1), m.group(2) or "01", m.group(3)
        if not is_sprite(os.path.join(D1, n + ".png")):
            continue
        fam[f][b].append(s)
    print("%-5s %5s %5s %6s %6s %6s %6s %6s %6s %6s" % ("族", "ink_h", "T", "ch0", "bandw", "cw", "ch", "x0", "cx", "fit?"))
    tiles = []
    for f in sorted(fam):
        b = max(fam[f], key=lambda k: len(fam[f][k]))
        ref = f + b
        if not os.path.exists(os.path.join(D1, ref + ".png")):
            ref = f + b + sorted(fam[f][b])[0]
        with Image.open(os.path.join(D1, ref + ".png")).convert("RGBA") as imr:
            rows = rows_of(imr)
            W1, H1 = imr.size
        T = rows[0][0]; ink_h = rows[-1][0] - T
        ch = int(round(K * ink_h)); cw = int(round(ch / 1.25))
        cw0 = cw
        cap = float(os.environ.get("CAP", "1.35"))
        bodylo = float(mode)
        fit = ""
        for _ in range(6):
            lo = T + int(bodylo * ch)
            bx0, bx1 = band_span(rows, lo, T + ch)
            need = int(round((bx1 - bx0 + 1) * 1.04))
            if cw < need and need <= cw0 * cap:
                cw = need; ch = int(round(cw * 1.25)); fit = "fit%d" % (cw - cw0)
            else:
                break
        lo = T + int(bodylo * ch)
        bx0, bx1 = band_span(rows, lo, T + ch)
        cx = (bx0 + bx1) // 2
        x0 = int(round(cx - cw / 2))
        x0 = max(0, min(x0, max(0, W1 - cw)))
        tile = crop_2x(ref, x0, T, cw, ch)
        tiles.append((f, tile))
        print("%-5s %5d %5d %6d %6d %6d %6d %6d %6d %6s" % (f, ink_h, T, int(round(K * ink_h)),
              bx1 - bx0 + 1, cw, ch, x0, cx, fit))
    pad = 4; lh = 16; per = 7
    cols = per; rows_n = (len(tiles) + per - 1) // per
    sheet = Image.new("RGB", (cols * (BW + pad) + pad, rows_n * (BH + pad + lh) + pad), (22, 22, 26))
    d = ImageDraw.Draw(sheet)
    for i, (f, t) in enumerate(tiles):
        x = pad + (i % per) * (BW + pad); y = pad + (i // per) * (BH + pad + lh)
        bg = Image.new("RGBA", (BW, BH), (40, 40, 48, 255)); bg.alpha_composite(t)
        sheet.paste(bg.convert("RGB"), (x, y))
        d.text((x + 2, y + BH + 2), f, fill=(255, 255, 180))
    # 单张别超 2400px 宽
    sheet.save(os.path.join(OUT, "var_%s.png" % mode))
    print("saved", sheet.size, os.path.join(OUT, "var_%s.png" % mode))


main()

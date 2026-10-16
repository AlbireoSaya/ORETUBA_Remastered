# -*- coding: utf-8 -*-
r"""E5 工具：终选前的放大对照（播放键 / 派生版 / 若干候选，统一归一化到 119 后 4× 放大）。
用法：python _zoom_compare.py C5 C6 C7
输出：候选\_放大预选.png
"""
import os, sys, math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
CAND = os.path.join(BASE, "候选")
UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
REF = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_off.png")
DER = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_pause_off.png")
Z, T = 4, 119


def ring_bbox(im):
    a = im.getchannel("A"); W, H = im.size; px = a.load()
    xs = [x for x in range(W) if any(px[x, y] >= 250 for y in range(H))]
    ys = [y for y in range(H) if any(px[x, y] >= 250 for x in range(W))]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def norm119(im):
    """等比缩放使「环外径 → 108」，并把环 bbox 中心对准 (59,59)，裁 119×119。"""
    im = im.convert("RGBA")
    bb = ring_bbox(im)
    if bb is None:
        return None
    d = max(bb[2] - bb[0] + 1, bb[3] - bb[1] + 1)
    k = 108.0 / d
    im2 = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    # 缩放后环中心（等比，直接乘 k）
    n = d * k
    cx = (bb[0] + bb[2] + 1) / 2.0 * k
    cy = (bb[1] + bb[3] + 1) / 2.0 * k
    out = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    out.alpha_composite(im2, (round(59 - cx), round(59 - cy)))
    return out


def main():
    tags = sys.argv[1:] or ["C5", "C6", "C7"]
    items = [("pbkick_off（播放键·基准）", REF), ("pause_off（派生版·基准）", DER)]
    for t in tags:
        items.append(("pause_AI_" + t, os.path.join(CAND, "pause_AI_cand_%s.png" % t)))
    cell = T * Z
    lab = 34
    sheet = Image.new("RGB", (len(items) * (cell + 10) + 10, cell + lab + 20), (20, 21, 24))
    d = ImageDraw.Draw(sheet)
    fnt = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 18)
    for i, (name, p) in enumerate(items):
        im = Image.open(p)
        if "A" not in im.mode:
            continue
        n = norm119(im)
        if n is None:
            continue
        x = 10 + i * (cell + 10)
        d.text((x, 6), name, font=fnt, fill=(215, 226, 240))
        big = n.resize((cell, cell), Image.NEAREST)
        bg = Image.new("RGB", (cell, cell), (46, 49, 56))
        bg.paste(big.convert("RGB"), (0, 0), big)
        sheet.paste(bg, (x, lab))
    out = os.path.join(CAND, "_放大预选.png")
    sheet.save(out)
    print("->", out, sheet.size)


if __name__ == "__main__":
    main()

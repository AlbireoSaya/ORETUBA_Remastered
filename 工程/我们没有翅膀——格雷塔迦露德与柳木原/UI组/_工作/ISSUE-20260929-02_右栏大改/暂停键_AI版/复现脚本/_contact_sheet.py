# -*- coding: utf-8 -*-
r"""E5 工具：候选接触印相表（内容归一化后并排，供目视筛选）。
把每件输出按「盘面（alpha>=250 环）外径」归一化到同一口径，居中贴到 260×260 格里，供横向比较。
用法：python _contact_sheet.py
"""
import os, glob
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
CAND = os.path.join(BASE, "候选")
CELL, PAD = 260, 12
LABEL = 26


def ring_bbox(im):
    """alpha>=250 的包围盒（环+字形）；AI 件用它当「盘面外径」锚。"""
    a = im.getchannel("A")
    W, H = im.size
    px = a.load()
    xs, ys = [], []
    for y in range(H):
        for x in range(W):
            if px[x, y] >= 250:
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def norm(im, target=108 * 3):
    """按环 bbox 等比缩放到 target 像素，返回居中后的图（不裁）。"""
    bb = ring_bbox(im)
    if bb is None:
        return None, None
    x0, y0, x1, y1 = bb
    d = max(x1 - x0 + 1, y1 - y0 + 1)
    k = target / float(d)
    im2 = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cv = Image.new("RGBA", (CELL, CELL), (32, 34, 40, 255))
    ox = round(CELL / 2 - (x0 + (x1 - x0) / 2.0) * k)
    oy = round(CELL / 2 - (y0 + (y1 - y0) / 2.0) * k)
    cv.alpha_composite(im2, (ox, oy))
    return cv, dict(ring_bbox=bb, ring_d=d, k=round(k, 3))


def main():
    files = sorted(glob.glob(os.path.join(CAND, "pause_AI_cand_C*.png")))
    rows = []
    for f in files:
        im = Image.open(f)
        if "A" not in im.mode:
            rows.append((os.path.basename(f), None, "RGB 无 alpha"))
            continue
        cv, info = norm(im.convert("RGBA"))
        rows.append((os.path.basename(f), cv, json.dumps(info, ensure_ascii=False)))
    n = len(rows)
    cols = 4
    rws = (n + cols - 1) // cols
    W = cols * (CELL + PAD) + PAD
    H = rws * (CELL + LABEL + PAD) + PAD
    sheet = Image.new("RGB", (W, H), (18, 19, 22))
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (name, cv, note) in enumerate(rows):
        c, r = i % cols, i // cols
        x = PAD + c * (CELL + PAD); y = PAD + r * (CELL + LABEL + PAD)
        d.text((x, y), name.replace("pause_AI_cand_", "").replace(".png", ""), font=fnt, fill=(220, 228, 240))
        if cv is not None:
            sheet.paste(cv.convert("RGB"), (x, y + LABEL - 6))
        else:
            d.rectangle([x, y + LABEL - 6, x + CELL, y + LABEL - 6 + CELL], fill=(70, 30, 30))
            d.text((x + 8, y + LABEL + 100), note, font=fnt, fill=(255, 200, 200))
    out = os.path.join(BASE, "候选", "_接触印相_候选.png")
    sheet.save(out)
    print("->", out, sheet.size, "件数", n)
    for name, _, note in rows:
        print("  ", name, note)


if __name__ == "__main__":
    import json
    main()

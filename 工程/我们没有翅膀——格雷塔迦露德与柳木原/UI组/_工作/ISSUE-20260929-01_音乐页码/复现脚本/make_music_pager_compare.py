# -*- coding: utf-8 -*-
r"""make_music_pager_compare.py —— 给你看的对照图：音乐页码行「改前 / 改后 / 引擎实机」

三格纵向排列（同一裁剪区域，x 620..1300、y 900..1060，含左右翻页键与页码文本）：
  A. **改前**（HTML 复刻）：页码行 y939 + `mu.pg_tx_2` 为近白 `#E8E8F0`
  B. **改后**（HTML 复刻）：页码行 y964 + 三件皆深墨 `#4A4A56`
  C. **改后（引擎实机）**：krkr 巡演导出的音乐屏帧（页 2）
每格标注实测：墨迹行范围 / 墨迹色 / 对霜板对比度。HTML 三位小数口径与引擎帧的差异已注明。
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "证据")
OUT = os.path.join(EVID, "对照_音乐页码_改前改后实机.png")
FONT = r"C:\Windows\Fonts\msyh.ttc"
CROP = (620, 900, 1300, 1060)          # x0,y0,x1,y1
BOX = (858, 964, 204, 56)


def lum(c):
    v = [x / 255 for x in c]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def cr(c1, c2):
    a, b = lum(c1), lum(c2)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def load(p, composite=False):
    im = Image.open(p)
    if composite or im.mode == "RGBA":
        a = np.asarray(im.convert("RGBA")).astype(np.float32)
        al = a[:, :, 3:4] / 255.0
        rgb = (a[:, :, :3] * al).astype(np.uint8)
        im = Image.fromarray(rgb)
    else:
        im = im.convert("RGB")
    if im.width > 1920:
        im = im.crop((0, 0, 1920, 1080))
    return im


def measure(im, y_box):
    a = np.asarray(im).astype(np.int16)
    x, _, w, h = BOX
    seg = a[y_box - 30:y_box + h + 30, x:x + w]
    L = 0.299 * seg[:, :, 0] + 0.587 * seg[:, :, 1] + 0.114 * seg[:, :, 2]
    rows = [i + y_box - 30 for i in range(seg.shape[0]) if (L[i] < 150).sum() > 3]
    ins = a[y_box:y_box + h, x:x + w].reshape(-1, 3)
    li = 0.299 * ins[:, 0] + 0.587 * ins[:, 1] + 0.114 * ins[:, 2]
    ink = tuple(int(v) for v in np.median(ins[li < 140], axis=0)) if (li < 140).sum() else None
    bg = tuple(int(v) for v in np.median(ins[li > 200], axis=0)) if (li > 200).sum() else (252, 252, 252)
    return (rows[0], rows[-1]) if rows else None, ink, bg


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    items = [
        ("A｜改前（HTML 复刻）：页码行 y939 ＋ `mu.pg_tx_2` 近白", os.path.join(EVID, "对照_改前色_page2.png"), 939),
        ("B｜改后（HTML 复刻）：页码行 y964 ＋ 三件皆深墨", os.path.join(EVID, "复刻_music_page2.png"), 964),
        ("C｜改后（**引擎实机** krkr 巡演帧 · 页 2）", os.path.join(EVID, "引擎_页2_墨深_shot48_music.png"), 964),
    ]
    panels, notes = [], []
    for label, path, yb in items:
        if not os.path.exists(path):
            notes.append((label, "（缺帧：" + os.path.basename(path) + "）")); continue
        im = load(path, composite=True)
        rows, ink, bg = measure(im, yb)
        txt = "墨迹行 %s ｜ 墨迹色 %s ｜ 对底 %s 对比 %.2f:1" % (
            ("%d..%d" % rows) if rows else "未测到",
            ("#%02X%02X%02X" % ink) if ink else "（近白，未达深墨阈）",
            "#%02X%02X%02X" % bg, cr(ink, bg) if ink else 0.0)
        panels.append((label, im.crop(CROP), txt))
    if not panels:
        raise SystemExit("没有可用帧")
    w = panels[0][1].width
    h = panels[0][1].height
    canvas = Image.new("RGB", (w + 24, sum(h + 66 for _ in panels) + 8), (22, 24, 30))
    d = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 19, index=0)
    f2 = ImageFont.truetype(FONT, 16, index=0)
    y = 4
    for label, crop, txt in panels:
        d.text((12, y), label, font=f1, fill=(240, 240, 245)); y += 26
        d.text((12, y), txt, font=f2, fill=(170, 220, 180)); y += 22
        canvas.paste(crop, (12, y)); y += h + 18
    canvas.save(OUT)
    print("写出 %s（%d×%d）" % (OUT, canvas.width, canvas.height))
    for label, t in notes:
        print("  ⚠ %s %s" % (label, t))
    for label, _c, t in panels:
        print("  %s ⇒ %s" % (label.split("｜")[0], t))
    return 0


if __name__ == "__main__":
    sys.exit(main())

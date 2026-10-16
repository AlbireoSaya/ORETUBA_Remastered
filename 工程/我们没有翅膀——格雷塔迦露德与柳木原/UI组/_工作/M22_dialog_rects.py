# -*- coding: utf-8 -*-
r"""M22 · 对话框两矩形候选 + 红线叠加（原型，验证后并入 prep_generated.py）。"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
EVID = os.path.join(UI, "_工作", "M22_证据")

crop = Image.open(os.path.join(EVID, "dialog2_crop_raw.png")).convert("RGBA")
W, H = crop.size


def checker(size, tile=16):
    im = Image.new("RGB", size, (128, 128, 128))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if ((x // tile) + (y // tile)) % 2:
                d.rectangle([x, y, x + tile - 1, y + tile - 1], fill=(168, 168, 168))
    return im


NAMBOX_OUTER = [130, 12, 414, 74]      # x 130..544, y 12..86
NAMBOX_INNER = [185, 22, 345, 56]      # x 185..530, y 22..78
WIN_OUTER = [21, 60, 1596, 244]        # x 21..1617, y 60..304
TEXT_INNER = [100, 80, 1040, 210]      # x 100..1140, y 80..290

bg = checker(crop.size)
bg.paste(crop.convert("RGB"), (0, 0), crop.getchannel("A"))
big = bg.resize((W, H * 2), Image.LANCZOS)
d = ImageDraw.Draw(big)
for r, lb, col in ((NAMBOX_OUTER, "namebox.outer", (255, 0, 0)),
                   (NAMBOX_INNER, "namebox.inner", (0, 200, 0)),
                   (WIN_OUTER, "text.outer", (255, 0, 255)),
                   (TEXT_INNER, "text.inner", (0, 120, 255))):
    x, y, w, h = r
    d.rectangle([x, y * 2, x + w - 1, (y + h - 1) * 2], outline=col, width=2)
    d.text((x + 4, y * 2 + 3), lb, fill=col)
big.save(os.path.join(EVID, "overlay_dialog2.png"))
print("->", os.path.join(EVID, "overlay_dialog2.png"))
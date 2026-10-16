# -*- coding: utf-8 -*-
r"""M22 · 对话框裁切图叠加坐标网格（供目视读取框位）。"""
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


bg = checker(crop.size)
bg.paste(crop.convert("RGB"), (0, 0), crop.getchannel("A"))
big = bg.resize((W, H * 2), Image.LANCZOS)
d = ImageDraw.Draw(big)
for x in range(0, W, 50):
    c = (255, 0, 0) if x % 200 == 0 else (255, 140, 0)
    d.line([(x, 0), (x, H * 2)], fill=c, width=1)
    if x % 200 == 0:
        d.text((x + 2, 2), str(x), fill=(255, 0, 0))
for y in range(0, H * 2, 20):
    c = (255, 0, 0) if (y // 2) % 100 == 0 else (255, 140, 0)
    d.line([(0, y), (W, y)], fill=c, width=1)
    if (y // 2) % 100 == 0:
        d.text((2, y + 2), str(y // 2), fill=(255, 0, 0))
big.save(os.path.join(EVID, "dialog2_grid.png"))
print("->", os.path.join(EVID, "dialog2_grid.png"), big.size)
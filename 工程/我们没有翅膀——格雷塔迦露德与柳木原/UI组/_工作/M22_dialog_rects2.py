# -*- coding: utf-8 -*-
r"""M22 · 正文区右边界候选对比（在右侧雪花上画候选竖线）。"""
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
for x, col, lb in ((1000, (255, 0, 0), "1000"), (1050, (0, 200, 0), "1050"),
                   (1100, (255, 140, 0), "1100"), (1150, (0, 0, 255), "1150"),
                   (1200, (255, 0, 255), "1200")):
    d.line([(x, 60 * 2), (x, 304 * 2)], fill=col, width=2)
    d.text((x + 2, 62 * 2), lb, fill=col)
big.save(os.path.join(EVID, "overlay_textright.png"))
print("->", os.path.join(EVID, "overlay_textright.png"))
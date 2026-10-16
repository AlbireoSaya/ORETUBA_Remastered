# -*- coding: utf-8 -*-
"""裁实机导图里 4 行的左段（左栏按钮 + 文案首行），纵向叠成一图，放大 2× 便于目视对齐。
只写本证据目录，不改工程文件。
"""
import os, json
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
d = json.load(open(SCREEN, encoding="utf-8"))
lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
pitch = lst["item_h"] + lst["gap"]

def crop(src, out, x0=169, w=560, zoom=2):
    im = Image.open(src).convert("RGB")
    parts = []
    for i in range(4):
        y0 = lst["y"] + i * pitch
        parts.append(im.crop((x0, y0, x0 + w, y0 + lst["item_h"])))
    h = sum(p.height for p in parts)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    y = 0
    for p in parts:
        canvas.paste(p, (0, y)); y += p.height
    canvas = canvas.resize((w * zoom, h * zoom), Image.NEAREST)
    canvas.save(out)
    print("saved", out, canvas.size)

if __name__ == "__main__":
    root = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
    src = os.path.join(root, "临时", "ui_run", "runtime", "savedata", "shot_29_backlog.png")
    crop(src, os.path.join(HERE, "实机_四行左段_2x.png"))

# -*- coding: utf-8 -*-
"""W11f · 门控拆分组目视对照图（主产物 vs 拆出产物），供人工终裁。只读产物，输出 PNG 到工作区。"""
import os, sys
from PIL import Image, ImageDraw

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
LIR = os.path.join(UNI, "立绘")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")
OUT = os.path.join(WORK, "vis")
os.makedirs(OUT, exist_ok=True)

H = 280          # 每图显示高度
PAD = 8
LABEL = 18
BG = (250, 250, 250)
BORDER = (180, 180, 180)


def load_flat(path, h, maxw=480):
    im = Image.open(path).convert("RGBA")
    w0, h0 = im.size
    w = max(1, round(w0 * h / h0))
    im = im.resize((w, h), Image.LANCZOS)
    if im.width > maxw:                      # 超宽图（如 cit001 长条）等比缩到 maxw
        nh = max(1, round(im.height * maxw / im.width))
        im = im.resize((maxw, nh), Image.LANCZOS)
    w, hh = im.size
    bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    bg.alpha_composite(im, (0, (h - hh) // 2))
    return bg.convert("RGB")


def sheet(groups, fname):
    tiles = []
    for stem, alt in groups:
        mp = os.path.join(LIR, stem + ".png")
        ap = os.path.join(LIR, alt)
        m = load_flat(mp, H)
        a = load_flat(ap, H)
        w = m.width + a.width + PAD * 3
        t = Image.new("RGB", (w, H + LABEL + PAD), BG)
        t.paste(m, (PAD, LABEL))
        t.paste(a, (PAD * 2 + m.width, LABEL))
        d = ImageDraw.Draw(t)
        d.rectangle([PAD, LABEL, PAD + m.width, LABEL + H], outline=BORDER)
        d.rectangle([PAD * 2 + m.width, LABEL, PAD * 2 + m.width + a.width, LABEL + H], outline=BORDER)
        d.text((PAD + 2, 3), "%s  (MAIN)" % stem, fill=(0, 0, 0))
        d.text((PAD * 2 + m.width + 2, 3), "%s  (ALT)" % alt, fill=(180, 0, 0))
        tiles.append(t)
    W = max(t.width for t in tiles)
    Ht = sum(t.height for t in tiles) + PAD * (len(tiles) + 1)
    out = Image.new("RGB", (W + PAD * 2, Ht), (255, 255, 255))
    y = PAD
    for t in tiles:
        out.paste(t, (PAD, y))
        y += t.height + PAD
    out.save(os.path.join(OUT, fname))
    print("wrote", fname, out.size)


if __name__ == "__main__":
    import json
    # 读取拆分明细
    rows = []
    with open(os.path.join(UNI, "_w11e_拆分明细.tsv"), encoding="utf-8") as f:
        hdr = f.readline()
        for ln in f:
            if not ln.strip():
                continue
            c = ln.rstrip("\n").split("\t")
            stem = c[0][:-4]
            alts = c[4].split("、")
            for a in alts:
                rows.append((stem, a))
    print("split products:", len(rows))
    json.dump(rows, open(os.path.join(WORK, "_vis_groups.json"), "w"), ensure_ascii=False)
    # 每 5 组一张大图，便于 Read 目视
    PER = 5
    for i in range(0, len(rows), PER):
        sheet(rows[i:i + PER], "sheet_%02d.png" % (i // PER + 1))
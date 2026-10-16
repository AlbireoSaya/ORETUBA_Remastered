# -*- coding: utf-8 -*-
r"""M48 · 目视证据图（ISSUE-20260924-05）

产出（`_工作\ISSUE-20260924-05_头像重制\证据\`）：
  · 对照_六格_前后.png   —— mis/ai/ban/dai/nar/kan 每族 前|后 两格
  · 对照_21族_前后.png   —— 21 个「只有头部」族 每族 前|后 两格（3 族/行）
  · 对照_全族_现状.png   —— 35 族各一张**新状态**（7 族/行）
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m48_make_faces import OUT, WKDIR

OLD = os.path.join(WKDIR, "_旧_face_M44")
EVI = os.path.join(WKDIR, "证据")
BW, BH = 276, 345
BAD21 = ["ban", "chi", "bok", "dai", "eri", "hiy", "kab", "kaz", "kin", "kyo",
         "lr", "mar", "men", "min", "mit", "pur", "sak", "saw", "ten", "y", "yuu"]
BG = (34, 34, 40, 255)


def tile(path, label, lab_col=(255, 255, 170)):
    t = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", (BW, BH), BG)
    bg.alpha_composite(t)
    return bg.convert("RGB"), label, lab_col


def sheet(rows, per, name):
    """rows: list[list[(img,label)]]；每行 per 格。"""
    pad, lh = 6, 16
    cols = per
    h = len(rows) * (BH + pad + lh) + pad
    w = cols * (BW + pad) + pad
    sh = Image.new("RGB", (w, h), (20, 20, 24))
    d = ImageDraw.Draw(sh)
    for ri, row in enumerate(rows):
        for ci, (img, lab) in enumerate(row):
            x = pad + ci * (BW + pad)
            y = pad + ri * (BH + pad + lh)
            sh.paste(img, (x, y))
            d.text((x + 2, y + BH + 2), lab, fill=(120, 255, 140) if "新" in lab else (255, 170, 120))
    sh.save(os.path.join(EVI, name))
    print("saved", name, sh.size)


def pair_row(nm, pre):
    return [tile(os.path.join(OLD, nm + ".png"), pre + " 旧 M44", (255, 170, 120))[:2],
            tile(os.path.join(OUT, nm + ".png"), pre + " 新 M48", (120, 255, 140))[:2]]


def main():
    os.makedirs(EVI, exist_ok=True)
    # 1) 六格前后
    pairs = []
    for nm in ["mis01", "ai_01", "ban01", "dai01", "nar01", "kan01"]:
        pairs += pair_row(nm, "".join(ch for ch in nm if not ch.isdigit())[:4])
    sheet([pairs[0:6], pairs[6:12]], 6, "对照_六格_前后.png")

    # 2) 21 族前后（每行 3 族 = 6 格）
    items = []
    for f in BAD21:
        ext = {"y": "0301", "lr": "201", "kaz": "02", "asu": "07"}.get(f, "01")
        base = {"y": "y0301", "lr": "lr201"}.get(f)
        nm = base or (f + ext)
        if not os.path.exists(os.path.join(OLD, nm + ".png")):
            cand = [x[:-4] for x in os.listdir(OLD) if x.startswith(nm)]
            nm = sorted(cand)[0]
        items += pair_row(nm, f)
    rows = [items[i:i + 6] for i in range(0, len(items), 6)]
    sheet(rows, 6, "对照_21族_前后.png")

    # 3) 全族现状（35 族各一张）
    names = sorted(x[:-4] for x in os.listdir(OUT) if x.endswith(".png") and not x.startswith("_"))
    seen, fams = set(), []
    for n in names:
        key = n.rstrip("abcdefghijklmnopqrstuvwxyz_") if False else None
        # 每族取第一张
        import re
        m = re.match(r"^([a-z_]+?)(\d*)([a-z_]*)$", n)
        f = m.group(1)
        if f not in seen:
            seen.add(f)
            fams.append(n)
    fams.sort()
    rows = []
    for i in range(0, len(fams), 7):
        rows.append([tile(os.path.join(OUT, n + ".png"), n)[:2] for n in fams[i:i + 7]])
    sheet(rows, 7, "对照_全族_现状.png")


main()

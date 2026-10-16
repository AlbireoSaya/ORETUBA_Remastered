# -*- coding: utf-8 -*-
"""W11g · 为 38 组「非 4:3/16:9」门控候选构建目视证据图（每组一张）。
- 只读源 PNG；证据图为中间产物，写 子代理工作区\ISSUE-20260918-06\W11g\vis\
- 候选按整数倍最近邻放大（便于读小字），棋盘底显 alpha，逐条标注 源:原名 尺寸 ar。
"""
import os, re, json, math
from PIL import Image, ImageDraw

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
SRC = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
VIS = os.path.join(WORK, "vis")
assert VIS.startswith(r"E:\ZCode Workspace\Galgame")
os.makedirs(VIS, exist_ok=True)

PREF = {"CG背景": ["pic", "chr", "sys", "etc"],
        "系统UI": ["sys", "etc", "pic", "chr"]}


def find_cand(src, fname, cat):
    root = os.path.join(SRC, src)
    for sub in PREF.get(cat, []):
        p = os.path.join(root, sub, fname)
        if os.path.isfile(p):
            return p
    for dp, dn, fn in os.walk(root):
        if fname in fn:
            return os.path.join(dp, fname)
    return None


def checker(w, h, s=8):
    im = Image.new("RGB", (w, h), (200, 200, 200))
    d = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if ((x // s) + (y // s)) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(235, 235, 235))
    return im


def parse(cands):
    out = []
    for it in [c.strip() for c in cands.split(";")]:
        m = re.match(r"(\w+):(\S+)\s+(\d+)x(\d+)\s+ar=([\d.]+)", it)
        if m:
            out.append((m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), float(m.group(5))))
    return out


def build(group):
    cat, name, n, diff, cands = group["类别"], group["统一名"], group["候选数"], group["diff"], group["候选"]
    items = parse(cands)
    rows = []
    for src, fname, w, h, ar in items:
        p = find_cand(src, fname, cat)
        rows.append((src, fname, w, h, ar, p))
    # 缩放因子：目标宽 260..1100
    scale = 1
    for _, _, w, h, _, _ in rows:
        if w < 260:
            scale = max(scale, min(6, math.ceil(260 / w)))
    pad, lab = 8, 16
    widths, heights = [], []
    for src, fname, w, h, ar, p in rows:
        widths.append(w * scale + 2 * pad)
        heights.append(h * scale + lab + pad)
    W = max(widths + [420])
    H = sum(heights) + pad
    sheet = Image.new("RGB", (W, H), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    y = pad
    for (src, fname, w, h, ar, p), hh in zip(rows, heights):
        d.text((pad, y), "%s:%s  %dx%d  ar=%.4f" % (src, fname, w, h, ar), fill=(0, 0, 0))
        y2 = y + lab
        if p and os.path.isfile(p):
            im = Image.open(p)
            if im.mode == "P":
                im = im.convert("RGBA")
            if im.mode == "RGBA":
                bg = checker(im.width, im.height)
                bg.paste(im, (0, 0), im)
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
            if scale != 1:
                im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            sheet.paste(im, (pad, y2))
        else:
            d.text((pad, y2), "  [MISSING]", fill=(200, 0, 0))
        d.line([(0, y2 + h * scale + 4), (W, y2 + h * scale + 4)], fill=(120, 120, 120))
        y = y2 + h * scale + pad
    fn = os.path.join(VIS, "%s__%s.png" % (cat, name[:-4]))
    sheet.save(fn)
    return fn, [(s, f, w, h, a, bool(p)) for s, f, w, h, a, p in rows]


def main():
    gs = json.load(open(os.path.join(WORK, "_38组清单.json"), encoding="utf-8"))
    miss = []
    for g in gs:
        fn, rows = build(g)
        for s, f, w, h, a, ok in rows:
            if not ok:
                miss.append((g["统一名"], s, f))
        print("%-16s -> %s" % (g["统一名"], os.path.basename(fn)))
    print("\n缺失候选:", miss if miss else "无")


if __name__ == "__main__":
    main()
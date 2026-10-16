# -*- coding: utf-8 -*-
r"""M22 · 源素材几何实测（只读；不改任何源素材）

用途：为 M22 的三个 builder 定 k、为 M23 产出几何，并给「旧 vs 新倍率」取证。
"""
from __future__ import annotations

import os
import io
import json

from PIL import Image, ImageDraw

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
GEN = os.path.join(UI, "生图入料", "生成结果")
WORK = os.path.join(UI, "_工作")
EVID = os.path.join(WORK, "M22_证据")
os.makedirs(EVID, exist_ok=True)


def alpha_bbox(im, box=None, th=8):
    a = im.getchannel("A")
    if box:
        a = a.crop(box)
        bb = a.point(lambda v: 255 if v >= th else 0).getbbox()
        if bb is None:
            return None
        return (bb[0] + box[0], bb[1] + box[1], bb[2] + box[0], bb[3] + box[1])
    return a.point(lambda v: 255 if v >= th else 0).getbbox()


def checker(size, tile=16):
    im = Image.new("RGB", size, (128, 128, 128))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if ((x // tile) + (y // tile)) % 2:
                d.rectangle([x, y, x + tile - 1, y + tile - 1], fill=(168, 168, 168))
    return im


OUT = {}

# ---------------------------------------------------------------- ① 功能图标
src = Image.open(os.path.join(GEN, "功能图标.png")).convert("RGBA")
W, H = src.size
print("功能图标.png %dx%d" % (W, H))
print("old geometry icons:")
old = json.load(io.open(os.path.join(WORK, "M20_生成几何.json"), encoding="utf-8"))
old_icon_scales = []
for it in old["icons"]:
    bb = it["tight_bbox_in_cell"]
    tw, th_ = bb[2] - bb[0], bb[3] - bb[1]
    s = it["size"][0] / tw
    old_icon_scales.append(s)
    print("  %-30s tight %3dx%-3d old_out %3dx%-3d old_scale %.4f"
          % (it["file"], tw, th_, it["size"][0], it["size"][1], s))
print("  old scale range: %.4f .. %.4f (ratio max/min %.3f)"
      % (min(old_icon_scales), max(old_icon_scales), max(old_icon_scales) / min(old_icon_scales)))

cells = []
for r in range(3):
    for c in range(3):
        x0, y0 = round(W * c / 3), round(H * r / 3)
        x1, y1 = round(W * (c + 1) / 3), round(H * (r + 1) / 3)
        bb = alpha_bbox(src, (x0, y0, x1, y1), th=8)
        cells.append((r, c, (x0, y0, x1, y1), bb))
        print("  cell(%d,%d) %s -> alpha bbox %s (w=%d h=%d)"
              % (c, r, (x0, y0, x1, y1), bb, bb[2] - bb[0], bb[3] - bb[1]))
OUT["icons_cells"] = [{"row": r, "col": c, "cell": list(cl), "bbox": list(bb)} for r, c, cl, bb in cells]
# 内容在整图上的总包围盒
allbb = alpha_bbox(src, th=8)
print("  整图 alpha bbox(th=8) = %s (w=%d h=%d)" % (allbb, allbb[2] - allbb[0], allbb[3] - allbb[1]))

# ---------------------------------------------------------------- ② 菜单
src2 = Image.open(os.path.join(GEN, "系统屏底图重置.png")).convert("RGBA")
W2, H2 = src2.size
print("\n系统屏底图重置.png %dx%d" % (W2, H2))
old_menu = old["menu"]
print("old menu scales:")
om = []
for it in old_menu:
    for tag in ("normal", "hover"):
        s = it[tag]["scale"]
        om.append(s[0])
        print("  %-32s tight %3dx%-3d out %3dx%-3d scale %.4f/%.4f"
              % (it[tag]["file"], it[tag]["tight_size"][0], it[tag]["tight_size"][1],
                 it["size"][0], it["size"][1], s[0], s[1]))
print("  old menu scale-x range: %.4f .. %.4f (ratio %.3f)" % (min(om), max(om), max(om) / min(om)))

mcells = []
for r in range(7):
    row = []
    for c in range(2):
        x0, y0 = round(W2 * c / 2), round(H2 * r / 7)
        x1, y1 = round(W2 * (c + 1) / 2), round(H2 * (r + 1) / 7)
        bb = alpha_bbox(src2, (x0, y0, x1, y1), th=8)
        rel = [bb[0] - x0, bb[1] - y0, bb[2] - bb[0], bb[3] - bb[1]] if bb else None
        row.append(rel)
        print("  cell r%d c%d %s -> bbox %s rel %s" % (r, c, (x0, y0, x1, y1), bb, rel))
    mcells.append(row)
OUT["menu_cells"] = mcells

# 行内烘焙文字高度（用于判「中文可读」）：取常态格内容里暗像素的行分布
ap = src2.getchannel("A").point(lambda v: 255 if v >= 8 else 0)
px = src2.load()
for r in range(7):
    x0, y0 = 0, round(H2 * r / 7)
    x1, y1 = W2 // 2, round(H2 * (r + 1) / 7)
    ys = []
    for y in range(y0, y1):
        cnt = sum(1 for x in range(x0, x1)
                  if px[x, y][3] >= 8 and (px[x, y][0] * 299 + px[x, y][1] * 587 + px[x, y][2] * 114) // 1000 < 128)
        if cnt >= 3:
            ys.append(y)
    if ys:
        print("  常态行%d 暗像素(y) %d..%d 高 %d" % (r + 1, min(ys), max(ys), max(ys) - min(ys) + 1))

# ---------------------------------------------------------------- ③ 流程方框
src3 = Image.open(os.path.join(GEN, "流程图的章节方框.png")).convert("RGBA")
W3, H3 = src3.size
print("\n流程图的章节方框.png %dx%d" % (W3, H3))
old_flow = old["flownode"]
for it in old_flow:
    bb = it["src_crop_bbox"]
    tw = bb[2] - bb[0]
    print("  %-30s crop %s tight %dx%d old_out %dx%d old_scale %.4f"
          % (it["file"], bb, tw, bb[3] - bb[1], it["size"][0], it["size"][1], 1152.0 / tw))

a = src3.getchannel("A")
rowc = [sum(1 for x in range(W3) if a.getpixel((x, y)) >= 200) for y in range(H3)]
solid = [y for y, c in enumerate(rowc) if c >= 400]
bands = []
s = prev = None
for v in solid:
    if s is None:
        s = v
    elif v - prev > 6:
        bands.append((s, prev)); s = v
    prev = v
if s is not None:
    bands.append((s, prev))
print("  实心行段: %s" % bands)
# 剖面局部极小
cuts = [240, 468, 696]
print("  剖面在 y=240/468/696 的值: %s" % [rowc[y] for y in cuts])
# 按指定切点切 4 条带
segs = [(21, 240), (240, 468), (468, 696), (696, 921)]
flow = []
for i, (y0, y1) in enumerate(segs):
    bb = alpha_bbox(src3, (0, y0, W3, y1), th=8)
    flow.append({"seg": [y0, y1], "bbox": list(bb), "h": bb[3] - bb[1], "w": bb[2] - bb[0]})
    print("  band%d seg y%d..%d -> alpha bbox %s  w=%d h=%d"
          % (i + 1, y0, y1, bb, bb[2] - bb[0], bb[3] - bb[1]))
OUT["flow_bands"] = flow

# ---------------------------------------------------------------- ④ 暂定对话框
src4 = Image.open(os.path.join(GEN, "暂定对话框.png")).convert("RGBA")
W4, H4 = src4.size
print("\n暂定对话框.png %dx%d" % (W4, H4))
for th in (8, 32, 64, 128):
    print("  alpha bbox th=%d -> %s" % (th, alpha_bbox(src4, th=th)))
bb = alpha_bbox(src4, th=64)
crop = src4.crop(bb)
print("  裁切(th=64) -> %dx%d" % crop.size)
crop.save(os.path.join(EVID, "dialog2_crop_raw.png"))
bg = checker(crop.size)
bg.paste(crop.convert("RGB"), (0, 0), crop.getchannel("A"))
bg.save(os.path.join(EVID, "dialog2_crop_checker.png"))
prev = bg.copy()
prev.thumbnail((1000, 1000), Image.LANCZOS)
prev.save(os.path.join(EVID, "dialog2_preview_small.png"))
print("  预览 -> %s" % os.path.join(EVID, "dialog2_preview_small.png"))
OUT["dialog2"] = {"source_size": [W4, H4], "bbox_th64": list(bb), "crop_size": list(crop.size)}

# 亮度剖面（在裁切图上，用 RGB 亮度找描边）
cp = crop.convert("RGBA").load()
cw, ch = crop.size


def prof_v(x0, x1, y0, y1):
    n = max(1, x1 - x0)
    return [sum((cp[x, y][0] * 299 + cp[x, y][1] * 587 + cp[x, y][2] * 114) // 1000
                for x in range(x0, x1)) // n for y in range(y0, y1)]


def prof_h(y0, y1, x0, x1):
    n = max(1, y1 - y0)
    return [sum((cp[x, y][0] * 299 + cp[x, y][1] * 587 + cp[x, y][2] * 114) // 1000
                for y in range(y0, y1)) // n for x in range(x0, x1)]


def minima(vals, span, depth):
    return [i for i in range(span, len(vals) - span)
            if vals[i] <= vals[i - span] - depth and vals[i] <= vals[i + span] - depth]


def grp(pos, gap=8):
    out, s, prev = [], None, None
    for v in pos:
        if s is None:
            s = v
        elif v - prev > gap:
            out.append((s, prev)); s = v
        prev = v
    if s is not None:
        out.append((s, prev))
    return out


# 全图横向剖面（找水平描边）
hprof = prof_v(0, cw, 0, ch)
hm = grp(minima(hprof, 3, 8))
print("  裁切图水平描边候选(全宽平均): %s" % hm)
# 左半区竖直剖面（找名字框左右描边）
vprof_l = prof_h(0, ch // 2, 0, cw)
vm_l = grp(minima(vprof_l, 3, 8))
print("  裁切图竖直描边候选(上半区): %s" % vm_l)
vprof_full = prof_h(0, ch, 0, cw)
vm_f = grp(minima(vprof_full, 3, 8))
print("  裁切图竖直描边候选(全高): %s" % vm_f)

with open(os.path.join(WORK, "M22_analyze.json"), "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, ensure_ascii=False, indent=1)
print("\n-> %s" % os.path.join(WORK, "M22_analyze.json"))
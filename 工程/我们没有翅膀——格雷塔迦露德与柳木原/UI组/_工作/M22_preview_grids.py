# -*- coding: utf-8 -*-
r"""M22 · 网格叠加预览（只读源素材）——用于判定「等分网格」是否切到内容。"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
GEN = os.path.join(UI, "生图入料", "生成结果")
EVID = os.path.join(UI, "_工作", "M22_证据")
os.makedirs(EVID, exist_ok=True)


def checker(size, tile=16):
    im = Image.new("RGB", size, (128, 128, 128))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if ((x // tile) + (y // tile)) % 2:
                d.rectangle([x, y, x + tile - 1, y + tile - 1], fill=(168, 168, 168))
    return im


def on_checker(im):
    bg = checker(im.size)
    bg.paste(im.convert("RGB"), (0, 0), im.getchannel("A"))
    return bg


# 菜单：等分 vs 实测行带
src = Image.open(os.path.join(GEN, "系统屏底图重置.png")).convert("RGBA")
W, H = src.size
for name, rows, cols in (
        ("menu_equalgrid", [round(H * i / 7) for i in range(8)], [round(W * i / 2) for i in range(3)]),
        ("menu_actualbands", [23, 177, 197, 351, 373, 529, 548, 707, 731, 877, 885, 1040, 1060, 1219],
         [142, 570, 734, 1169])):
    bg = on_checker(src)
    d = ImageDraw.Draw(bg)
    for y in rows:
        d.line([(0, y), (W, y)], fill=(255, 0, 0), width=3)
    for x in cols:
        d.line([(x, 0), (x, H)], fill=(0, 128, 255), width=3)
    bg.save(os.path.join(EVID, name + ".png"))
    print("->", name)

# 图标：3×3 等分
src2 = Image.open(os.path.join(GEN, "功能图标.png")).convert("RGBA")
W2, H2 = src2.size
bg = on_checker(src2)
d = ImageDraw.Draw(bg)
for i in range(4):
    d.line([(0, round(H2 * i / 3)), (W2, round(H2 * i / 3))], fill=(255, 0, 0), width=4)
    d.line([(round(W2 * i / 3), 0), (round(W2 * i / 3), H2)], fill=(0, 128, 255), width=4)
bg.save(os.path.join(EVID, "icons_equalgrid.png"))
print("-> icons_equalgrid")

# 流程方框：切点 240/468/696
src3 = Image.open(os.path.join(GEN, "流程图的章节方框.png")).convert("RGBA")
W3, H3 = src3.size
bg = on_checker(src3)
d = ImageDraw.Draw(bg)
for y in (21, 240, 468, 696, 921):
    d.line([(0, y), (W3, y)], fill=(255, 0, 0), width=3)
bg.save(os.path.join(EVID, "flow_cuts.png"))
print("-> flow_cuts")

# 暂定对话框裁切图（放大 2× 便于目视）
crop = Image.open(os.path.join(EVID, "dialog2_crop_raw.png")).convert("RGBA")
bg = checker(crop.size)
bg.paste(crop.convert("RGB"), (0, 0), crop.getchannel("A"))
big = bg.resize((crop.size[0], crop.size[1] * 2), Image.NEAREST)
big.save(os.path.join(EVID, "dialog2_crop_x2.png"))
print("-> dialog2_crop_x2")

# 图标源图 3×3 单格预览（放大看内容）
for i in range(3):
    for j in range(3):
        pass
print("done")
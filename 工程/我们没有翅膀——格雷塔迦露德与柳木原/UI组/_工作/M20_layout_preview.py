# -*- coding: utf-8 -*-
r"""M20 · 标题屏合成预览（决定 logo / 菜单坐标的目视依据）

把 `krkr/assets/ui/` 里的 x_bg_system / x_gen_logo / x_gen_menu_* 按候选坐标合成，
输出对比图到 `_工作\M20_证据\`，供人工目视取舍。**不写任何资产、不改布局**。

坐标口径：1920×1080 画布；菜单 7 项竖排，高 104、间隙 12（总高 800）。
候选：
  A 轴心对齐（各按钮水平中心 = 1704，源自源图「列内居中」的排布）
  B 右对齐（各按钮右缘 = 1848，羽毛尖对齐）
垂直：y0 = 180 → 180..980（画布垂直居中偏下；署名行 y=1029）。
"""
import os
from PIL import Image

UI = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
OUT = os.path.join(UI, "krkr", "assets", "ui")
EV = os.path.join(UI, "_工作", "M20_证据")

SEM = ["start", "continue", "load", "flowchart", "extra", "config", "exit"]
W, H = 1920, 1080
Y0, IH, GAP = 180, 104, 12
AXIS_CENTER = 1704
AXIS_RIGHT = 1848


def load(n):
    return Image.open(os.path.join(OUT, n)).convert("RGBA")


def compose(mode):
    bg = load("x_bg_system.png").resize((W, H), Image.LANCZOS)
    logo = load("x_gen_logo.png")
    bg.alpha_composite(logo, (60, 45))
    boxes = []
    for i, s in enumerate(SEM):
        im = load("x_gen_menu_%d_%s.png" % (i + 1, s))
        y = Y0 + i * (IH + GAP)
        if mode == "center":
            x = AXIS_CENTER - im.size[0] // 2
        else:
            x = AXIS_RIGHT - im.size[0]
        bg.alpha_composite(im, (x, y))
        boxes.append((i + 1, s, x, y, im.size[0], im.size[1]))
    return bg.convert("RGB"), boxes


for mode in ("center", "right"):
    im, boxes = compose(mode)
    p = os.path.join(EV, "layout_preview_%s.png" % mode)
    im.save(p)
    print(mode, "->", p)
    for b in boxes:
        print("   #%d %-9s x=%4d y=%4d %3dx%d" % b)

# 左右并排对比（各缩到 0.5×）
a = Image.open(os.path.join(EV, "layout_preview_center.png")).resize((W // 2, H // 2), Image.LANCZOS)
b = Image.open(os.path.join(EV, "layout_preview_right.png")).resize((W // 2, H // 2), Image.LANCZOS)
cmp_ = Image.new("RGB", (W, H // 2 + 24), (16, 20, 28))
cmp_.paste(a, (0, 24)); cmp_.paste(b, (W // 2, 24))
from PIL import ImageDraw
d = ImageDraw.Draw(cmp_)
d.text((8, 6), "LEFT = A 轴心对齐(1704)   RIGHT = B 右对齐(1848)", fill=(230, 230, 240))
cmp_.save(os.path.join(EV, "layout_preview_compare.png"))
print("compare ->", os.path.join(EV, "layout_preview_compare.png"))
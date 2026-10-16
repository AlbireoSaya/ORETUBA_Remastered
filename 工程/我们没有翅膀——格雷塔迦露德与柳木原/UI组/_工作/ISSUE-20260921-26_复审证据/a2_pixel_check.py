# -*- coding: utf-8 -*-
"""A2 像素反向验证：pressed 到底从「常态」还是「悬停版」派生；
   以及 A2 引用的按钮文字/图标素材实际尺寸（是否会被拉伸涂抹）。"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops

UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
UIASSETS = os.path.join(UI, "krkr", "assets", "ui")

def diffstat(a, b):
    d = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
    bbox = d.getbbox()
    mx = 0; tot = 0; n = 0
    for px in d.getdata():
        m = max(px)
        if m > mx: mx = m
        tot += sum(px); n += 1
    return mx, tot / float(n * 4)

def load(p):
    return Image.open(os.path.join(UIASSETS, p)).convert("RGBA")

print("=" * 78)
print("A2：按钮文字 pressed 的派生源判定（常态 vs 悬停版）")
print("=" * 78)
for base in ("x_ui_btntxt2c_start", "x_ui_btntxt2c_exit", "x_ui_btntxt2_start"):
    n = load(base + ".png"); h = load(base + "_on.png"); p = load(base + "_press.png")
    print("\n%s: 尺寸 normal=%s hover=%s press=%s" % (base, n.size, h.size, p.size))
    mx1, av1 = diffstat(n, p); mx2, av2 = diffstat(h, p)
    print("   |normal - press|  max=%3d mean=%6.2f   ← 越小说明 press 越像「常态派生」" % (mx1, av1))
    print("   |hover  - press|  max=%3d mean=%6.2f   ← 越小说明 press 越像「悬停派生」" % (mx2, av2))
    # 按配方上限反推：press = normal*0.80 → 差异应是显著的；press = hover*0.80 → 与 normal 差异更大
    print("   判定：%s" % ("**press 更像由常态派生**" if mx1 < mx2 else "**press 更像由悬停版派生**"))

print("\n" + "=" * 78)
print("A2 附：选择支 pressed 的派生源")
print("=" * 78)
n = load("x_ui_choice_off.png"); h = load("x_ui_choice_over.png"); p = load("x_ui_choice_press.png")
print("  off=%s over=%s press=%s" % (n.size, h.size, p.size))
mx1, av1 = diffstat(n, p); mx2, av2 = diffstat(h, p)
print("   |off - press|   max=%3d mean=%6.2f" % (mx1, av1))
print("   |over - press|  max=%3d mean=%6.2f" % (mx2, av2))
mx0, av0 = diffstat(n, h)
print("   |off - over|    max=%3d mean=%6.2f   ← 悬停图与常态的差异（用户要求重出的理由）" % (mx0, av0))

print("\n" + "=" * 78)
print("A4/渲染一致性：标题菜单图标（hit 的 state_assets）与热区尺寸")
print("=" * 78)
import json, io
d = json.load(io.open(os.path.join(UI, "layout", "screens", "01_title.json"), encoding="utf-8"))
for e in d["elements"]:
    if e["id"] == "title.menu_hit_1":
        sa = e["state_assets"]
        print("  title.menu_hit_1 rect=%sx%s" % (e["w"], e["h"]))
        for k, v in sa.items():
            fn = os.path.basename(v)
            try:
                im = Image.open(os.path.join(UIASSETS, fn))
                print("     %-8s %-40s PNG=%s  → %s" % (
                    k, fn, im.size,
                    "尺寸相等(不拉伸)" if im.size == (e["w"], e["h"]) else "**尺寸不等 → 两端都会拉伸到热区**"))
            except Exception as ex:
                print("     %-8s %-40s 打不开 %r" % (k, fn, ex))

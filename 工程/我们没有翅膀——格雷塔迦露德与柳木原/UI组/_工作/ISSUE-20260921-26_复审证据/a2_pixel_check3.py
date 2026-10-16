# -*- coding: utf-8 -*-
"""A2 决定性验证：直接调用 btn_states.py 里**未被改动的** pressed() 配方，
分别从常态/悬停版算出候选，与盘上的 _press.png 逐像素比对。"""
import os, sys, importlib.util
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops

UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
A = os.path.join(UI, "krkr", "assets", "ui")
BS = os.path.join(UI, "_工作", "M35_生图脚本", "btn_states.py")

spec = importlib.util.spec_from_file_location("btn_states", BS)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

def load(p): return Image.open(os.path.join(A, p)).convert("RGBA")
def ident(x, y):
    if x.size != y.size: return "尺寸不同"
    return "**逐像素完全相同**" if ImageChops.difference(x, y).getbbox() is None else "不同"

print("=" * 82)
print("A2 决定性验证（调用 btn_states.pressed 原配方）")
print("=" * 82)
rows = []
for base in ("x_ui_btntxt2c_start", "x_ui_btntxt2c_exit", "x_ui_btntxt2c_config",
             "x_ui_btntxt2_load", "x_ui_btntxt2_gallery", "x_ui_btntxt2c_flowchart"):
    n, h, p = load(base + ".png"), load(base + "_on.png"), load(base + "_press.png")
    r_n, r_h = B.pressed(n), B.pressed(h)
    vn, vh = ident(r_n, p), ident(r_h, p)
    rows.append((base, vn, vh))
    print("%-26s  recipe(normal)==press: %-22s  recipe(hover)==press: %s" % (base, vn, vh))

print("\n" + "=" * 82)
print("选择支 x_ui_choice_press.png")
print("=" * 82)
off, over, pc = load("x_ui_choice_off.png"), load("x_ui_choice_over.png"), load("x_ui_choice_press.png")
print("  recipe(off)  ==press:", ident(B.pressed(off), pc))
print("  recipe(over) ==press:", ident(B.pressed(over), pc))
print("  实际 over 与 off 的差异:",
      "**逐像素相同**" if ImageChops.difference(off, over).getbbox() is None else "有差异")

print("\n" + "=" * 82)
print("★ 附：选择支 over 是否 = 用户裁定配方（提亮 30% + alpha×1.25，无外扩白晕）")
print("=" * 82)
r, g, b, a = off.split()
rgb = Image.merge("RGB", (r, g, b))
rgb = Image.blend(rgb, Image.new("RGB", off.size, (255, 255, 255)), 0.30)
r2, g2, b2 = rgb.split()
a2 = a.point(lambda v: min(255, int(round(v * 1.25))))
cand = Image.merge("RGBA", (r2, g2, b2, a2))
print("  按该配方重算 == 盘上 over：", ident(cand, over))

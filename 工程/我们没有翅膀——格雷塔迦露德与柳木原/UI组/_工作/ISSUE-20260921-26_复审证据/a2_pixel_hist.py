# -*- coding: utf-8 -*-
"""A2 决定性验证（历史版）：用 b4ea8a8 以来未改动的 btn_states.pressed()，
对 152ea7b（pressed 图被重新生成的提交）与 021d950（被审提交）的同名素材做逐像素比对。"""
import os, sys, importlib.util
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
BS = os.path.join(UI, "_工作", "M35_生图脚本", "btn_states.py")
spec = importlib.util.spec_from_file_location("btn_states", BS)
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

def load(d, p):
    return Image.open(os.path.join(HERE, "hist", d, p)).convert("RGBA")

def eq(x, y):
    if x.size != y.size: return "尺寸不同"
    return "一致" if ImageChops.difference(x, y).getbbox() is None else "不一致"

print("=" * 84)
print("A2 决定性验证 —— btn_states.pressed（配方 0.80/0.90/0.96，自 b4ea8a8 起未改动）")
print("=" * 84)
for commit in ("152ea7b", "021d950"):
    print("\n### 素材快照 @%s" % commit)
    for base in ("x_ui_btntxt2c_start",):
        n = load(commit, base + ".png")
        h = load(commit, base + "_on.png")
        p = load(commit, base + "_press.png")
        print("  %s: recipe(常态)==盘上 pressed ? %s   ｜ recipe(悬停)==盘上 pressed ? %s"
              % (base, eq(B.pressed(n), p), eq(B.pressed(h), p)))
    o, ov, pc = (load(commit, "x_ui_choice_off.png"),
                 load(commit, "x_ui_choice_over.png"),
                 load(commit, "x_ui_choice_press.png"))
    print("  x_ui_choice: recipe(off)==press ? %s  ｜ recipe(over)==press ? %s  ｜ over 与 off 相同? %s"
          % (eq(B.pressed(o), pc), eq(B.pressed(ov), pc), eq(o, ov)))

print("\n★ 交叉：用 152ea7b 的 over 与 021d950 的 press（判断 pressed 是否出自旧 over）")
o_old = load("152ea7b", "x_ui_choice_over.png")
pc_now = load("021d950", "x_ui_choice_press.png")
print("  recipe(over@152ea7b) == press@021d950 ? %s" % eq(B.pressed(o_old), pc_now))
print("  recipe(over@152ea7b) == press@152ea7b ? %s" % eq(B.pressed(o_old), load("152ea7b", "x_ui_choice_press.png")))

print("\n★ 用 152ea7b 的常态做交叉（排除「normal 之后被改过」）")
print("  normal@152ea7b 与 normal@021d950 相同? %s"
      % eq(load("152ea7b", "x_ui_btntxt2c_start.png"), load("021d950", "x_ui_btntxt2c_start.png")))
print("  hover@152ea7b  与 hover@021d950  相同? %s"
      % eq(load("152ea7b", "x_ui_btntxt2c_start_on.png"), load("021d950", "x_ui_btntxt2c_start_on.png")))

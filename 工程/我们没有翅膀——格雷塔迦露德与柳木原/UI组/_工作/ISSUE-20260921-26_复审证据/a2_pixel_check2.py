# -*- coding: utf-8 -*-
"""A2 严格反向验证：用脚本里写明的配方分别从「常态」与「悬停版」重算 pressed，
与盘上实际的 _press.png 逐像素比对 —— 差异小的那一侧才是真正的派生源。"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image

UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
A = os.path.join(UI, "krkr", "assets", "ui")

# btn_states.py 的 pressed() 配方（逐行抄自该文件）
P_RGB, P_ALPHA, P_SCALE = 0.80, 0.90, 0.96

def pressed(im):
    r, g, b, a = im.split()
    r = r.point(lambda v: min(255, int(v * P_RGB)))
    g = g.point(lambda v: min(255, int(v * P_RGB)))
    b = b.point(lambda v: min(255, int(v * P_RGB)))
    a = a.point(lambda v: min(255, int(v * P_ALPHA)))
    out = Image.merge("RGBA", (r, g, b, a))
    if P_SCALE != 1.0:
        w, h = out.size
        nw, nh = int(round(w * P_SCALE)), int(round(h * P_SCALE))
        small = out.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.paste(small, ((w - nw) // 2, (h - nh) // 2))
        out = canvas
    return out

def dstat(a, b):
    aa = a.convert("RGBA"); bb = b.convert("RGBA")
    if aa.size != bb.size:
        return None, None
    mx = 0; tot = 0
    for pa, pb in zip(aa.getdata(), bb.getdata()):
        for i in range(4):
            d = abs(pa[i] - pb[i])
            if d > mx: mx = d
            tot += d
    return mx, tot / float(4 * aa.size[0] * aa.size[1])

def load(p):
    return Image.open(os.path.join(A, p)).convert("RGBA")

print("=" * 82)
print("A2 严格验证：按配方重算 pressed，与实际盘上 _press.png 比对")
print("=" * 82)
cases = [("x_ui_btntxt2c_start", "x_ui_btntxt2c_start"),
         ("x_ui_btntxt2c_config", "x_ui_btntxt2c_config"),
         ("x_ui_btntxt2_load", "x_ui_btntxt2_load")]
verdict = []
for lbl, base in cases:
    n = load(base + ".png"); h = load(base + "_on.png"); p = load(base + "_press.png")
    pn = pressed(n); ph = pressed(h)
    m1, a1 = dstat(pn, p); m2, a2 = dstat(ph, p)
    tag = "常态派生" if (m1 is not None and m2 is not None and m1 < m2) else "悬停派生"
    if m1 == 0 and m2 != 0:
        tag = "**确定：常态派生（逐像素相等）**"
    elif m2 == 0 and m1 != 0:
        tag = "**确定：悬停派生（逐像素相等）**"
    verdict.append(tag)
    print("%-26s  |recipe(normal)-press| max=%-4s mean=%-7.3f   |recipe(hover)-press| max=%-4s mean=%-7.3f  → %s"
          % (base, m1, a1, m2, a2, tag))

print("\n" + "=" * 82)
print("A2 附：选择支 x_ui_choice_press.png 同样按配方反算")
print("=" * 82)
n = load("x_ui_choice_off.png"); h = load("x_ui_choice_over.png"); p = load("x_ui_choice_press.png")
m1, a1 = dstat(pressed(n), p); m2, a2 = dstat(pressed(h), p)
print("  |recipe(off)-press|   max=%-4s mean=%-7.3f" % (m1, a1))
print("  |recipe(over)-press|  max=%-4s mean=%-7.3f" % (m2, a2))
print("  → %s" % ("**确定：从常态 off 派生**" if (m1 == 0 and m2 != 0) else
                   ("从常态 off 派生（更近）" if m1 < m2 else "从悬停 over 派生（更近）")))

print("\n提示：mean 越小越接近；max=0 且 mean=0 即逐像素相等。")

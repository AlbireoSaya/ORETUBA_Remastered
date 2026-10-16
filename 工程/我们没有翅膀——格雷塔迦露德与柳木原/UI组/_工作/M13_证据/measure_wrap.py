# -*- coding: utf-8 -*-
"""M13 实测：dlg.text 正文区在 36px 字号 / 给定宽度下能容几行（逐条真实台词）。
用法：PYTHONPATH=工具/pylibs python measure_wrap.py [字号] [宽度]
"""
import re
import sys
from PIL import ImageFont

SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 36
MAXW = int(sys.argv[2]) if len(sys.argv) > 2 else 1568

src = open("krkr/game/ui_demo_script.tjs", encoding="utf-8").read()
m = re.search(r"var UIDemoText\s*=\s*\[(.*?)\];", src, re.S)
texts = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
print("台词条数 =", len(texts), " 字号 =", SIZE, " 文本区宽 =", MAXW)

f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", SIZE)


def w(s):
    return f.getlength(s)


worst = 0
over = 0
for i, t in enumerate(texts):
    lines = []
    cur = ""
    for ch in t:
        if w(cur + ch) <= MAXW or cur == "":
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    mx = max(w(l) for l in lines)
    worst = max(worst, len(lines))
    flag = ""
    if len(lines) > 3:
        over += 1
        flag = "  <<< 超过 3 行"
    print("  %2d  字符%3d  行数%d  最宽行 %4d px%s" % (i + 1, len(t), len(lines), int(mx), flag))

print("最多行数 =", worst, " 超过 3 行的条数 =", over)
print("3 行所需高度 = %d px（lineH = floor(%d*1.4) = %d）" % (3 * int(SIZE * 1.4), SIZE, int(SIZE * 1.4)))
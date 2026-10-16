# -*- coding: utf-8 -*-
"""M18 可读性实测：流程图节点标签在候选字号下的折行与宽度（用真实字体 msyh.ttc）。

判据：标签可用宽度 W（= 方框「无装饰区」在缩放后的宽度）下，
      「节点名」与「来源·规模」两行各自的实际像素宽 ≤ W，且总行数 ≤ max_lines。
用法: python M18_measure_flowtext.py
"""
from __future__ import annotations
import io, json, os
from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
PROJ = os.path.dirname(UI)
SPINE = json.load(io.open(os.path.join(PROJ, "资源组", "剧本", "spine.json"), encoding="utf-8"))

NODE_ACT = {"N01": 1, "N02": 2, "N03": 3, "N04": 4, "N05": 5, "N06": 6, "N07": 7,
            "N08": 8, "N09": 9, "N10": 10, "N11": 11}
BRANCH_SCENE = {"B01": "ot_s01_02c", "B02": "s03_09a"}
ORDER = ["N01", "N02", "N03", "N04", "B01", "N08", "N05", "N06", "B02", "N07", "N09", "N10", "N11"]

acts = {a["act"]: a for a in SPINE["acts"]}
bp = {b["scene_id"]: b for b in SPINE["branch_points"]}

labels = []
for nid in ORDER:
    if nid in NODE_ACT:
        a = acts[NODE_ACT[nid]]
        name = a["name"]
        sub = "%s · %d 场景 / %d 行" % ("/".join(a["source"]), len(a["scenes"]), a["line_count"])
    else:
        b = bp.get(BRANCH_SCENE[nid], {})
        name = "分歧点 " + (b.get("route", "") or BRANCH_SCENE[nid])
        sub = "%d 选项 · %s" % (b.get("option_count", 0), BRANCH_SCENE[nid])
    labels.append((nid, name, sub))

FONT = "C:/Windows/Fonts/msyh.ttc"

def w(f, s):
    return f.getbbox(s)[2] - f.getbbox(s)[0]

print("=" * 100)
print("M18 流程图节点标签宽度实测（字体 msyh.ttc 微软雅黑）")
print("=" * 100)
# 候选：标签可用宽度（方框无装饰区，缩放后）
for avail in (355, 371, 400, 420):
    print("\n--- 标签可用宽度 W = %d px ---" % avail)
    for size in (16, 17, 18, 19, 20, 21, 22):
        f = ImageFont.truetype(FONT, size)
        bad = []
        for nid, name, sub in labels:
            wn, ws = w(f, name), w(f, sub)
            if wn > avail or ws > avail:
                bad.append("%s(name=%d,sub=%d)" % (nid, wn, ws))
        status = "全部单行放得下" if not bad else ("超宽: " + ", ".join(bad))
        print("   size=%2d : %s" % (size, status))

print("\n" + "=" * 100)
print("逐条实际宽度（size=17 / 18 / 20）")
print("=" * 100)
fs = {s: ImageFont.truetype(FONT, s) for s in (17, 18, 20)}
print("%-4s %-24s %-26s %s" % ("节点", "节点名", "来源·规模", "宽度@17 / @18 / @20 (name|sub)"))
for nid, name, sub in labels:
    cells = []
    for s in (17, 18, 20):
        cells.append("%d|%d" % (w(fs[s], name), w(fs[s], sub)))
    print("%-4s %-24s %-26s %s" % (nid, name, sub, "   ".join(cells)))

# 方框缩放与几何核算
print("\n" + "=" * 100)
print("几何核算：方框缩放")
print("=" * 100)
GEO = json.load(io.open(os.path.join(HERE, "M11_生成几何.json"), encoding="utf-8"))
for f_ in GEO["flownode"]:
    sw, sh = f_["size"]
    for s in (0.4785, 0.5):
        print("  %-10s 原 %dx%d -> x%.4f = %dx%d" % (f_["semantic"], sw, sh, s,
                                                     int(round(sw * s)), int(round(sh * s + 0.5))))
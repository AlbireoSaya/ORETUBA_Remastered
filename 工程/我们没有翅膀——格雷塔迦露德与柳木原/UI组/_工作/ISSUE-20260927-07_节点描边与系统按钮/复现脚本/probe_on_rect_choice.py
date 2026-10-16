# -*- coding: utf-8 -*-
"""probe_on_rect_choice.py —— 决定 _on 件用「off 的 rect」还是「on 自身的 rect」做解析化锚点。

判据：验收②要求六件的四角半径（相切一维搜索口径）≈16.0（±0.2）。
两种锚点各跑一遍，比较半径实测值与 50% 交叉矩形的稳定性。
"""
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image                                                    # noqa: E402

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
REPRO7 = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮" / "复现脚本"
BACKUP = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "原形备份"
sys.path.insert(0, str(REPRO7))
import make_node_contour_candidates as CN                                 # noqa: E402

R = 16.0
KINDS = ("section", "select", "frag")


def analytic(a, rect, band_r, radii=(R,) * 4):
    prof, _band = CN.collect_profiles(a, rect, band_r)
    f = CN.shape_fields(a.shape[1], a.shape[0], rect, radii)
    return np.rint(np.clip(CN.synth(prof, f), 0, 255)).astype(np.uint8)


print("kind      state  anchor      rect(x0,x1,y0,y1)                       半径复测 TL/TR/BR/BL        45°")
for k in KINDS:
    aoff = np.asarray(Image.open(BACKUP / ("x_ui_node_%s_off.png" % k)).convert("RGBA")
                      .getchannel("A")).astype(np.float64)
    rect_off = CN.rect_of(aoff)
    for st in ("off", "on"):
        a = np.asarray(Image.open(BACKUP / ("x_ui_node_%s_%s.png" % (k, st))).convert("RGBA")
                       .getchannel("A")).astype(np.float64)
        rect_self = CN.rect_of(a)
        for tag, rect in (("off-rect", rect_off), ("self-rect", rect_self)):
            al = analytic(a, rect, R + 2)
            rm = CN.rect_of(al.astype(np.float64))
            rr, r45 = [], []
            for c in ("TL", "TR", "BR", "BL"):
                Rb, rmsb, n = CN.radius_corner(al.astype(np.float64), rm, c)
                rr.append(Rb if Rb else -1)
                v45 = CN.corner_diag_radius(al.astype(np.float64), rm, c)
                r45.append(v45 if v45 else -1)
            dev = max(abs(rm[i] - rect[i]) for i in range(4))
            print("%-9s %-6s %-11s %-38s %s   %s  rect自移 %.3f"
                  % (k, st, tag, "[" + ", ".join("%8.3f" % v for v in rm) + "]",
                     " ".join("%6.2f" % v for v in rr), " ".join("%6.2f" % v for v in r45), dev))
    print()

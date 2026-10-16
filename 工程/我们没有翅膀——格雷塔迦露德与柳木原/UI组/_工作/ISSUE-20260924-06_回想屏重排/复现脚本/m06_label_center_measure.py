# -*- coding: utf-8 -*-
r"""M06 · **「跳转」按钮 label 墨迹中心** 两端量化（一审 Major 打回的判据脚本）。

■ 一审给的方法（原样照做）
  阈值 `L<120`（暗墨迹）；窗口 `x236..332`、`y = 108 + 205*row + 18 .. +70`（4 块逐个）。
  取窗口内暗像素的**包围盒**，报「引擎中心 y / HTML 中心 y / Δ」。

■ 输入
  引擎：`临时\ui_run_pagescope\runtime\savedata\shot_29_backlog.png`（巡演导出的无指针基线帧）
  HTML：`_工作\ISSUE-20260924-06_回想屏重排\证据\m06_html_backlog.png`（w4_html_config_shots.py 无头截图）

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_label_center_measure.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE))
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))
ENGINE = os.path.join(WT, "临时", "ui_run_pagescope", "runtime", "savedata", "shot_29_backlog.png")
HTML = os.path.join(ISSUE, "证据", "m06_html_backlog.png")

X0, X1 = 236, 332          # 跳转按钮画布横向（块内局部 28..122 ⇒ 画布 236..330，留 2px 余量）
ITEM_H = 205
Y_TOP = 108
ROWS = 4


def ink_box(im, x0, x1, y0, y1, thr=120):
    """窗口内暗像素（L<thr）包围盒；无墨迹返回 None。"""
    g = im.convert("L").crop((x0, y0, x1, y1))
    px = g.load()
    w, h = g.size
    minx = miny = 10 ** 9
    maxx = maxy = -1
    n = 0
    for i in range(w):
        for j in range(h):
            if px[i, j] < thr:
                n += 1
                if i < minx: minx = i
                if i > maxx: maxx = i
                if j < miny: miny = j
                if j > maxy: maxy = j
    if maxx < 0:
        return None
    return (x0 + minx, y0 + miny, x0 + maxx, y0 + maxy, n)


def main():
    from PIL import Image
    for p in (ENGINE, HTML):
        if not os.path.exists(p):
            print("缺图：", p)
            return 2
    eng = Image.open(ENGINE).convert("RGB")
    htm = Image.open(HTML).convert("RGB")

    print("窗口 x%d..%d，逐块 y=%d+%d*r+18..+70，阈值 L<120" % (X0, X1, Y_TOP, ITEM_H))
    print("%-5s | %-26s | %-26s | %s" % ("块", "引擎墨迹包围盒(y0..y1,cx,cy)", "HTML墨迹包围盒(y0..y1,cx,cy)", "中心Δ(HTML-引擎)"))
    dys = []
    dxs = []
    for r in range(ROWS):
        y0 = Y_TOP + ITEM_H * r + 18
        y1 = Y_TOP + ITEM_H * r + 70
        be = ink_box(eng, X0, X1, y0, y1)
        bh = ink_box(htm, X0, X1, y0, y1)
        if be is None or bh is None:
            print("块%d: 引擎=%s HTML=%s" % (r, be, bh))
            continue
        ecy = (be[1] + be[3]) / 2.0
        hcy = (bh[1] + bh[3]) / 2.0
        ecx = (be[0] + be[2]) / 2.0
        hcx = (bh[0] + bh[2]) / 2.0
        dy = hcy - ecy
        dx = hcx - ecx
        dys.append(dy)
        dxs.append(dx)
        print("块%-2d | y%d..%d cx=%.1f cy=%.1f n=%d | y%d..%d cx=%.1f cy=%.1f n=%d | Δy=%+.1f Δx=%+.1f"
              % (r, be[1], be[3], ecx, ecy, be[4], bh[1], bh[3], hcx, hcy, bh[4], dy, dx))
    if dys:
        print("----")
        print("纵向中心 Δ：min=%+.1f max=%+.1f 均值=%+.2f  |Δ|max=%.1f" %
              (min(dys), max(dys), sum(dys) / len(dys), max(abs(d) for d in dys)))
        print("横向中心 Δ：|Δ|max=%.1f" % max(abs(d) for d in dxs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
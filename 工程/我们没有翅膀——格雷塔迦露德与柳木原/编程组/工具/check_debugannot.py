#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
check_debugannot.py —— 【Debug 开发版】屏幕标注的**像素级**机检（编程组 · ISSUE-20261008-05 D1）
================================================================================
用途：把「标注真的画在画面上」这一主张做成**可复算、可失败**的一步——
      不看日志、直接读 run_storytest.py 导出的 PNG 像素。

判据（三件，全部依赖 `ui_debug.tjs` 的实际绘制）：
  ① **顶栏版本标记块**：画布最右 6px × 顶部 40px 的矩形，颜色**精确** 0x00FF66。
     由 `stage.colorRect(W-6, 0, 6, UIDbgBannerH, 0x00ff66, 255)` 画出 ⇒ 无抗锯齿、颜色精确。
     ★ 这是**标注层唯一的签名色**（UI 组素材里没有该纯色满块），**开/关判定以它为准**。
  ② **顶部深色底条**：第 5 行整行像素「三通道均 < 100」占比（`colorRect(...,0x101820,225)`）。
     只作**开启态**的佐证，**不作关闭态判据**——深色 CG / sysicons 压暗浮层同样是深色，会误判。
  ③ **顶栏文字像素**：顶栏区内亮像素（三通道 > 180）数量（`Debug 开发版` 等字样）。

两种期望：
  `--expect on`  ⇒ ① ② ③ 全部成立才 PASS（关掉开关时必须 FAIL）
  `--expect off` ⇒ **①（签名色标记块）不存在** 才 PASS
                    （★ 这同时是**检查器本身能失败**的负控：若检查器恒真，本档必 FAIL）

用法：
  python -X utf8 工具/check_debugannot.py --expect on  <png...>
  python -X utf8 工具/check_debugannot.py --expect off <png...>
  # 也可给目录（取其下所有 storytest PNG 里抽 1 张代表）
"""
import argparse
import os
import sys
import warnings

warnings.simplefilter("ignore", DeprecationWarning)

try:
    from PIL import Image
except Exception as e:                                   # pragma: no cover
    print("[FATAL] 需要 PIL（Pillow）：%s" % e)
    sys.exit(2)

MARK = (0, 255, 102)     # UIDbgColorMark = 0x00ff66
MARK_TOL = 10


def near(px, ref, tol):
    return abs(px[0] - ref[0]) <= tol and abs(px[1] - ref[1]) <= tol and abs(px[2] - ref[2]) <= tol


def analyze(path):
    """返回 %[ w, h, mark_px, dark_frac_row5, bright_px, note ]"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    top = im.crop((0, 0, w, min(40, h)))
    px = list(top.getdata())
    tw = w

    # ① 精确色版本标记块（最右 8px × 顶部 40px 内）
    mark_px = 0
    for yy in range(top.size[1]):
        for xx in range(max(0, tw - 8), tw):
            if near(list(top.getpixel((xx, yy))), MARK, MARK_TOL):
                mark_px += 1

    # ② 第 5 行深色占比
    dark = 0
    row = 5 if top.size[1] > 5 else 0
    for xx in range(tw):
        p = top.getpixel((xx, row))
        if p[0] < 100 and p[1] < 100 and p[2] < 100:
            dark += 1
    dark_frac = dark / float(tw)

    # ③ 顶栏亮像素（文字）
    bright = 0
    for p in px:
        if p[0] > 180 and p[1] > 180 and p[2] > 180:
            bright += 1

    # ④ 面板底条存在性（左上区域 y 60..300 内深色占比，辅助证据，不作判据）
    panel = 0
    bg = im.crop((0, 50, min(1100, w), min(400, h)))
    n = 0
    for p in list(bg.getdata()):
        n += 1
        if p[0] < 60 and p[1] < 70 and p[2] < 80:
            panel += 1
    panel_frac = panel / float(n) if n else 0.0

    return dict(w=w, h=h, mark_px=mark_px, dark_frac=dark_frac, bright_px=bright,
                panel_frac=panel_frac)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", choices=["on", "off"], required=True)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    files = []
    for p in args.paths:
        if os.path.isdir(p):
            for n in sorted(os.listdir(p)):
                if n.lower().endswith(".png"):
                    files.append(os.path.join(p, n))
        else:
            files.append(p)
    if not files:
        print("[FATAL] 没有 PNG 可检")
        sys.exit(2)

    overall = True
    for f in files:
        try:
            a = analyze(f)
        except Exception as e:
            print("[ERR] %s : %s" % (f, e))
            overall = False
            continue
        on = (a["mark_px"] >= 20) and (a["dark_frac"] >= 0.90) and (a["bright_px"] >= 50)
        # ★ 关闭态**只**以签名色标记块为准：深色底条在深色 CG / sysicons 压暗浮层上同样为深
        #   ⇒ 用「顶栏是否深色」判「有没有标注」会把普通深色画面误判成开着。
        off = (a["mark_px"] < 5)
        ok = on if args.expect == "on" else off
        overall = overall and ok
        print("%s  %s  ｜ %dx%d 标记块=%d 顶栏深色占比=%.3f 顶栏亮像素=%d 面板深色占比=%.2f ｜ 期望=%s"
              % ("PASS" if ok else "FAIL", os.path.basename(f), a["w"], a["h"],
                 a["mark_px"], a["dark_frac"], a["bright_px"], a["panel_frac"], args.expect))

    print("★DEBUGANNOT-PNG★ %s ｜ 期望=%s ｜ 检 %d 张" % ("PASS" if overall else "FAIL", args.expect, len(files)))
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()

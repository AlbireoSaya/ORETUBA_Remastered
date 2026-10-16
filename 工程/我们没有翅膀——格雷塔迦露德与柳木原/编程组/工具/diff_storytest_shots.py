#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
diff_storytest_shots.py —— 两组 run_storytest 证据 PNG 的**逐像素对比**（编程组 · ISSUE-20261008-05 D1）
================================================================================
用途：回答「某个叠加层是不是**只在它自己的区域加像素**、没动别处」这类问题——
      不开日志、不比肉眼，直接比像素，并把差异**按纵向分带**归类。

分带（1080 画布）：
  `顶栏(<40)`         —— 顶部固定条带（`ui_debug.tjs` 的 `Debug 开发版` 条）
  `上部带(40..720)`   —— 顶部与对话框之间的区域（标注面板所在）
  `对话框区(>=720)`   —— 对话框底图/正文区（`dlg.mask_bottom` 自 y=730 起）
★ 判读：若某次改动是**纯叠加**，非确定性帧之外应当只有前两带有差异、`对话框区` 为 0。
  但要先跑一次**同配置的两次运行互比**作为噪声基线——本作有两处**运行期非确定性**：
    ① 章节过场卡的存活期由引擎 Timer 驱动（回调实测被拖慢）⇒ 过场卡帧整屏不同；
    ② 对话框光标闪烁相位 ⇒ 对话框区每次约 900 像素的差异。
  这些噪声与改动无关，必须先量出来，再判改动本身。

用法：
  python -X utf8 工具/diff_storytest_shots.py <A目录> <B目录> [--only a.png b.png ...]
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageChops
except Exception as e:                                   # pragma: no cover
    print("[FATAL] 需要 PIL（Pillow）：%s" % e)
    sys.exit(2)

BAND_TOP = 40
BAND_MID = 720


def diff_one(pa, pb):
    ia = Image.open(pa).convert("RGB")
    ib = Image.open(pb).convert("RGB")
    if ia.size != ib.size:
        return dict(size="%dx%d vs %dx%d" % (ia.size + ib.size), bbox="-", n=0, top=0, mid=0, low=0)
    W, H = ia.size
    d = ImageChops.difference(ia, ib)
    da = d.tobytes()
    n = top = mid = low = 0
    for i in range(0, len(da), 3):
        if da[i] or da[i + 1] or da[i + 2]:
            n += 1
            y = (i // 3) // W
            if y < BAND_TOP:
                top += 1
            elif y < BAND_MID:
                mid += 1
            else:
                low += 1
    return dict(size="%dx%d" % (W, H), bbox=str(d.getbbox()), n=n, top=top, mid=mid, low=low)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    na = set(n for n in os.listdir(args.a) if n.lower().endswith(".png"))
    nb = set(n for n in os.listdir(args.b) if n.lower().endswith(".png"))
    names = sorted(na & nb) if args.only is None else list(args.only)
    if args.only is None:
        only_a = sorted(na - nb)
        only_b = sorted(nb - na)
        if only_a or only_b:
            print("[warn] 只在 A 有：%s ｜ 只在 B 有：%s" % (only_a, only_b))
    for n in names:
        pa, pb = os.path.join(args.a, n), os.path.join(args.b, n)
        if not (os.path.isfile(pa) and os.path.isfile(pb)):
            print("SKIP %s（缺件）" % n)
            continue
        r = diff_one(pa, pb)
        print("%-24s %-10s bbox=%-26s 差异=%8d ｜ 顶栏(<%d)=%6d 上部带(%d..%d)=%7d 对话框区(>=%d)=%6d"
              % (n, r["size"], r["bbox"], r["n"], BAND_TOP, r["top"],
                 BAND_TOP, BAND_MID, r["mid"], BAND_MID, r["low"]))
    print("★SHOTDIFF★ 完成（A=%s ｜ B=%s ｜ %d 张）" % (args.a, args.b, len(names)))


if __name__ == "__main__":
    main()

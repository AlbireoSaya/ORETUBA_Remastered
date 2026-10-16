#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
check_eyecatch.py —— 章节过场卡 / Q 版素材自检（ISSUE-20261005-06；**可失败**，进构建验收）
检查项（全部用**盘面实测**，不信任生成器的自我报告）：
  A. 整卡布局：卡贴最左（0..1439 有内容）、右带 1440..1920 被填满（无纯黑列）
  B. 底纹同料同色：右带奶油底的主两色 == 卡面奶油底的主两色（每通道容差 ±2）
  C. 剪开虚线：x=1440±1 列上暗像素占比 ≥ 55%（18/14 间距理论 56%，扣除剪刀缺口）；对照列（x=1000）应为 0
  D. Q 版矩形零越界：映射表里全部矩形满足 x ≥ 1440（不压虚线）、x+w ≤ 1920、y ≥ 0、y+h ≤ 1080
  E. Q 版件齐全：三槽各 N 件、文件都存在、且与映射表一致
  F. 引擎表：story/_eyecatch_chibi.tjs 存在且含 uiEyecatchChibiFill；文件数与映射表一致
用法：
  python -X utf8 工具/check_eyecatch.py --res <资源组> [--assets krkr/game/eyecatch] [--story krkr/game/story]
任一项失败 ⇒ 退出码 1。
"""
import argparse
import glob
import io
import os
import sys


from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
LINE_X = 1440
STRIP_X = 1440
STRIP_W = 480
TEAR_ICON_Y = 70          # 与 eyecatch_compose.TEAR_ICON_Y 保持一致（剪刀图标中心）


def top_colors(im, box, n=3):
    # ★ 用 Image.getcolors（稳定 API），不用 getdata——后者在 Pillow 14 起移除（一审 Minor）
    px = im.crop(box).convert("RGB")
    cols = px.getcolors(1 << 24)                 # [(count, (r,g,b)), ...]
    cols.sort(key=lambda kv: -kv[0])
    tot = sum(k for k, _ in cols)
    return [(rgb, 100.0 * k / tot) for k, rgb in cols[:n]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default=os.path.join(PROJ, "资源组"))
    ap.add_argument("--assets", default=os.path.join(PROJ, "编程组", "krkr", "game", "eyecatch"))
    ap.add_argument("--story", default=os.path.join(PROJ, "编程组", "krkr", "game", "story"))
    ap.add_argument("--card", default="", help="指定一张整卡（缺省取第一张 ec__card_*.png）")
    a = ap.parse_args()
    fails = []
    warns = []

    def chk(name, ok, detail=""):
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("—— " + detail) if detail else ""))
        if not ok:
            fails.append(name)

    # 选一张整卡
    cards = sorted(glob.glob(os.path.join(a.assets, "ec__card_*.png")))
    if a.card:
        cards = [a.card]
    if not cards:
        print("[FAIL] 没有整卡产物（%s）" % a.assets)
        return 1
    card_p = cards[0]
    print("== 检查对象：%s ==" % os.path.basename(card_p))
    im = Image.open(card_p).convert("RGB")
    W, H = im.size
    chk("画布 1920x1080", (W, H) == (1920, 1080), "%dx%d" % (W, H))

    # A. 布局：卡区/右带都有内容
    def col_dark(x):
        n = 0
        for y in range(0, H, 4):
            r, g, b = im.getpixel((x, y))
            if r < 12 and g < 12 and b < 12:
                n += 1
        return n
    chk("A1 卡区无纯黑列", col_dark(700) == 0)
    chk("A2 右带无纯黑列", col_dark(1700) == 0)

    # B. 底纹同料同色：卡面奶油 vs 右带奶油，**主两色按集合比**（棋盘相位不同会让两色的占比次序互换，
    #    逐下标比会把「同料」误判为失败——2026-10-06 自检首跑实测）
    card_c = top_colors(im, (1300, 830, 1420, 990), 4)
    strip_c = top_colors(im, (1500, 830, 1620, 990), 4)
    card_top = sorted([c for c, _ in card_c if sum(c) > 600][:2])
    strip_top = sorted([c for c, _ in strip_c if sum(c) > 600][:2])
    ok_b = len(card_top) >= 2 and len(strip_top) >= 2 and all(
        all(abs(card_top[i][k] - strip_top[i][k]) <= 2 for k in range(3)) for i in range(2))
    chk("B 底纹同料同色（主两色按集合、逐通道 ≤2）", ok_b,
        "卡面 %s vs 右带 %s" % (card_top[:2], strip_top[:2]))

    # C. 剪开虚线
    def dark_ratio(x):
        n = tot = 0
        for y in range(0, H, 2):
            tot += 1
            r, g, b = im.getpixel((x, y))
            if r < 120 and g < 120 and b < 120:
                n += 1
        return n * 1.0 / tot
    r_tear = max(dark_ratio(LINE_X - 1), dark_ratio(LINE_X), dark_ratio(LINE_X + 1))
    r_ref = dark_ratio(1000)
    # 理论占比 = 18/(18+14)=56.25%，再扣剪刀缺口（y28..112 共 84px）⇒ ≈51.9%；阈值取 0.48～0.62
    chk("C1 虚线在 x=%d（暗像素 48%%..62%%）" % LINE_X, 0.48 <= r_tear <= 0.62,
        "实测 %.1f%%（理论 ≈51.9%%，已扣剪刀缺口）" % (r_tear * 100))
    chk("C2 对照列 x=1000 无虚线", r_ref < 0.05, "实测 %.1f%%" % (r_ref * 100))
    # 剪刀（图标区应有暗像素簇：eyecatch_compose 的剪刀画在虚线两侧 ±26px、y≈40..100）
    sc = 0
    for y in range(40, 100, 2):
        for x in range(LINE_X - 26, LINE_X + 27, 2):
            r, g, b = im.getpixel((x, y))
            if r < 130 and g < 130 and b < 130:
                sc += 1
    chk("C3 剪刀图标存在（图标区暗像素 >0）", sc > 0, "暗像素点 %d" % sc)

    # D/E. Q 版矩形与件数
    tsv = os.path.join(PROJ, "编程组", "Q版素材映射.tsv")
    if not os.path.isfile(tsv):
        chk("D Q版映射表存在", False, tsv)
    else:
        rows = []
        with io.open(tsv, encoding="utf-8") as f:
            head = f.readline().rstrip("\n").split("\t")
            for ln in f:
                c = ln.rstrip("\n").split("\t")
                if len(c) >= 8:
                    rows.append(c)
        chk("D0 映射表行数 >0", len(rows) > 0, "%d 行" % len(rows))
        bad_rect = []
        for c in rows:
            idx, src, sub, wh, s1, s2, s3, rects = c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]
            for si, rel in enumerate((s1, s2, s3)):
                # TSV 里是**引擎相对路径**（eyecatch/chibi/...）；盘面路径要剥掉这层前缀再拼 --assets
                rel_fs = rel[len("eyecatch/"):] if rel.startswith("eyecatch/") else rel
                fp = os.path.join(a.assets, rel_fs.replace("/", os.sep))
                if not os.path.isfile(fp):
                    bad_rect.append("c%s 槽%d 缺件 %s" % (idx, si + 1, rel))
            for part in rects.split(" | "):
                x, y, w, h = (int(v) for v in part.split(","))
                if x < LINE_X:
                    bad_rect.append("c%s 越虚线（x=%d）" % (idx, x))
                if x + w > 1920 or y < 0 or y + h > 1080:
                    bad_rect.append("c%s 出画布（%d,%d,%d,%d）" % (idx, x, y, w, h))
        chk("D Q版矩形零越界 + 三槽件齐全", not bad_rect, "；".join(bad_rect[:5]) if bad_rect else "%d 件×3 槽" % len(rows))
        # E. 盘上件数
        for si, tag in enumerate(("s1", "s2", "s3")):
            n = len(glob.glob(os.path.join(a.assets, "chibi", tag, "c*.png")))
            chk("E%d %s 槽件数 = 映射表" % (si + 1, tag), n == len(rows), "盘上 %d / 表 %d" % (n, len(rows)))

    # F. 引擎表
    tjs = os.path.join(a.story, "_eyecatch_chibi.tjs")
    ok_f = os.path.isfile(tjs)
    if ok_f:
        with io.open(tjs, encoding="utf-8") as f:
            txt = f.read()
        ok_f = ("function uiEyecatchChibiFill" in txt) and (txt.count("eyecatch/chibi/") >= 3 * len(rows))
    chk("F 引擎表 _eyecatch_chibi.tjs", ok_f, "含 uiEyecatchChibiFill 且引用 %d 处" % (txt.count("eyecatch/chibi/") if ok_f else -1))

    print()
    if fails:
        print("[FAIL] %d 项未过：%s" % (len(fails), "、".join(fails)))
        return 1
    print("[PASS] 全部检查项通过（A 布局 / B 同料 / C 虚线 / D 矩形 / E 件数 / F 引擎表）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""
make_prologue_review_sheets.py — 序章开场段 · 40 条字幕条的**放大目读印相表**（ISSUE-20260930-07）

产出：`资源组\审查件\序章开场段_字幕条\字幕条_1.png`、`字幕条_2.png`（各 20 条，白底、2× 放大、带编号）
用途：① 中文化时逐条抄录日文原文；② 用户/UI 组目视复核。
（`资源组\审查件\` 已 gitignore，不随镜像同步——需手工拷进主工作区。）

用法：
  python -X utf8 make_prologue_review_sheets.py            # 生成
  python -X utf8 make_prologue_review_sheets.py --check    # 只校验产物存在与张数
"""
from __future__ import annotations

import argparse
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)
OUTDIR = os.path.join(RES, "审查件", "序章开场段_字幕条")


def roots():
    out = [PROJ]
    d = PROJ
    while True:
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            out.append(d)
    out.append(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原")
    seen, res = set(), []
    for r in out:
        if r not in seen:
            seen.add(r)
            res.append(r)
    return res


def product(rel):
    for r in roots():
        c = os.path.join(r, rel)
        if os.path.isfile(c):
            return c
    raise SystemExit("找不到：%s" % rel)


def names_from_list():
    """从 `序章开场段_清单.tsv` 读字幕条的统一名（保持步序）。"""
    p = product(os.path.join("资源组", "审计", "序章开场段_清单.tsv"))
    ns = []
    with io.open(p, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        i_t, i_u = head.index("类型"), head.index("统一名")
        for ln in f:
            c = ln.rstrip("\n").split("\t")
            if len(c) > i_u and c[i_t] == "字幕条":
                ns.append(c[i_u][:-4])
    return ns


def make():
    ns = names_from_list()
    if len(ns) != 40:
        sys.exit("[闸门失败] 字幕条应为 40，实得 %d" % len(ns))
    os.makedirs(OUTDIR, exist_ok=True)
    f = lambda sz: ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", sz)
    written = []
    for part in (0, 1):
        sel = ns[part * 20:(part + 1) * 20]
        W, H = 1600, 20 * 116 + 56
        sh = Image.new("RGB", (W, H), (255, 255, 255))
        dr = ImageDraw.Draw(sh)
        dr.text((10, 12), "序章开场段 · 片头字幕条 放大目读 %d/2（白底 2×；编号＝步序）" % (part + 1),
                font=f(24), fill=(0, 0, 0))
        y = 56
        for k, n in enumerate(sel):
            src = product(os.path.join("资源组", "美术统一", "系统UI", n + ".png"))
            im = Image.open(src).convert("RGBA")
            bg = Image.new("RGB", (im.width, im.height), (255, 255, 255))
            bg.paste(im, (0, 0), im)
            bg = bg.resize((im.width * 2, im.height * 2), Image.LANCZOS)
            dr.text((10, y + 14), n, font=f(20), fill=(190, 0, 0))
            sh.paste(bg, (110, y + 10))
            dr.line([(0, y + 100), (W, y + 100)], fill=(225, 225, 225))
            y += 116
        out = os.path.join(OUTDIR, "字幕条_%d.png" % (part + 1))
        sh.save(out)
        written.append(out)
    print("写出：")
    for w in written:
        print("  ", w, os.path.getsize(w), "B")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        got = [p for p in (os.path.join(OUTDIR, "字幕条_%d.png" % i) for i in (1, 2)) if os.path.isfile(p)]
        if len(got) != 2:
            sys.exit("[--check] 产物不全：%d/2" % len(got))
        if len(names_from_list()) != 40:
            sys.exit("[--check] 清单字幕条数 != 40")
        print("[--check] 产物 2/2 存在；清单 40 条 PASS")
        return
    make()


if __name__ == "__main__":
    main()

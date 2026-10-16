#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
「图片化日文 629 件」人工审查用接触印相表生成器   (ISSUE-20260930-05)
================================================================================
**只读** `美术统一\交付清单.tsv`（取 `图片化日文 == 是` 的 629 行）与交付层 `美术统一_交付\`；
把每 24 件拼成一张带标注（统一名 + 尺寸）的大图，便于**逐张目视**审查「这件图里的文字要不要中文化」。

产物：`资源组\审查件\图片化日文_接触印相\{ui,cg}_NN.png`（系统UI 23 张 + CG背景 4 张，**gitignore**）。
配套的**逐件清单**（含交付路径、子族、是否曲名位图）见 `资源组\审计\图片化日文_审查清单.tsv`；
口径与事实源见 `资源组\03_资源总账_全量现状.md` §5.3（W19 更新块）与 `美术规范.md` §6.5。

> 用户 2026-09-30 裁决：**曲名位图（`mc_bgm*` 58 + `gl_bgm*` 12）不需要中文化**。

用法：python -X utf8 make_picjp_review_sheets.py [--data-root <主工作区>]
"""
from __future__ import annotations

import argparse
import os
import sys

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
CELL_W, CELL_H, PAD, LABEL = 420, 150, 8, 16
COLS, ROWS_PER = 4, 6
PER = COLS * ROWS_PER


def find_main_workspace(cli):
    if cli:
        return os.path.abspath(cli)
    env = os.environ.get("GALGAME_MAIN")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        if os.path.isfile(os.path.join(cur, "工程", GAME, "资源组", "krkr素材库", "资源总账.json")):
            return cur
    raise SystemExit("[FATAL] 未找到主工作区，请用 --data-root 指定")


def assert_in_checkout(path):
    here = os.path.dirname(os.path.abspath(__file__))
    checkout = here
    for _ in range(4):
        if os.path.isdir(os.path.join(checkout, ".git")) or os.path.isfile(os.path.join(checkout, ".git")):
            break
        checkout = os.path.dirname(checkout)
    p = os.path.abspath(path)
    if not (p == checkout or p.startswith(checkout + os.sep)):
        raise SystemExit(f"[FATAL] 产物路径不在本 checkout 内，拒绝写入：{p}")
    return p


def main():
    import csv
    from PIL import Image, ImageDraw

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    res = os.path.join(data, REL_RES)
    here = os.path.dirname(os.path.abspath(__file__))
    out = assert_in_checkout(os.path.join(here, "..", "审查件", "图片化日文_接触印相"))
    os.makedirs(out, exist_ok=True)

    src = next((x for x in (os.path.join(here, "..", "审计", "图片化日文_审查清单.tsv"),
                            os.path.join(res, "审计", "图片化日文_审查清单.tsv"))
                if os.path.isfile(x)), "")
    if src:
        rows = list(csv.DictReader(open(src, encoding="utf-8"), delimiter="\t"))
    else:                                   # 回退：直接从交付清单筛
        rows = [r for r in csv.DictReader(open(os.path.join(res, "美术统一", "交付清单.tsv"),
                                               encoding="utf-8"), delimiter="\t")
                if r.get("图片化日文") == "是"]
        deliv = {r["统一名"]: r["交付相对路径"] for r in
                 csv.DictReader(open(os.path.join(res, "美术统一_交付", "交付清单.tsv"),
                                     encoding="utf-8"), delimiter="\t")}
        rows = [dict(类别=r["类别"], 统一名=r["统一名"], 尺寸=r["尺寸(w,h)"],
                     交付路径=deliv.get(r["统一名"], "")) for r in rows]
    if not rows:
        raise SystemExit("[FATAL] 审查清单为空")

    made = []
    for cat, tag, cell_w in (("系统UI", "ui", CELL_W), ("CG背景", "cg", 560)):
        items = [r for r in rows if r["类别"] == cat]
        for pi in range(0, len(items), PER):
            chunk = items[pi:pi + PER]
            W = COLS * (cell_w + PAD) + PAD
            H = ROWS_PER * (CELL_H + PAD) + PAD
            sheet = Image.new("RGB", (W, H), (250, 250, 250))
            d = ImageDraw.Draw(sheet)
            for k, r in enumerate(chunk):
                cx, cy = k % COLS, k // COLS
                x0 = PAD + cx * (cell_w + PAD)
                y0 = PAD + cy * (CELL_H + PAD)
                p = os.path.join(res, "美术统一_交付", r["交付路径"].replace("/", os.sep))
                try:
                    im = Image.open(p).convert("RGBA")
                except Exception:                                  # noqa: BLE001
                    im = Image.new("RGBA", (100, 30), (255, 0, 0, 255))
                bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                bg.alpha_composite(im)
                im = bg.convert("RGB")
                sc = min(cell_w / im.width, (CELL_H - LABEL) / im.height, 1.0)
                im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                               Image.LANCZOS)
                sheet.paste(im, (x0, y0))
                d.text((x0, y0 + CELL_H - LABEL + 2),
                       "%s  [%s]" % (r["统一名"], r["尺寸"]), fill=(20, 20, 20))
            outp = os.path.join(out, "%s_%02d.png" % (tag, pi // PER + 1))
            sheet.save(outp, optimize=True)
            made.append((os.path.basename(outp), len(chunk)))
    print("共 %d 张接触印相表 → %s" % (len(made), out))
    for n, c in made:
        print("   %-14s %d 件" % (n, c))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""
build_disabled_list.py — 「不得编入成品」停用件清单（ISSUE-20260930-10，用户 2026-09-30 裁决九.1）

用户裁决原文：「**不移除**（弃用件仍留在交付层），**但要记录下哪些文件被弃用，并且不得被编入成品游戏内**。」

产出：`资源组\交接编程组\停用件_禁入成品.tsv`（= `审计\图片化日文_处置清单.tsv` 里 `处置 == 弃用` 的全部件）
列：`序号` / `类别` / `族` / `统一名` / `交付路径` / `字节` / `处置依据`

硬闸门
  G1 行数 == 处置表的「弃用」计数（**497**），且与 `629 − 132` 守恒
  G2 不得含任何 `保留·*` 件
  G3 `--check` 幂等
"""
from __future__ import annotations

import argparse
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)
SRC = os.path.join(RES, "审计", "图片化日文_处置清单.tsv")
OUT = os.path.join(RES, "交接编程组", "停用件_禁入成品.tsv")
HEAD = ["序号", "类别", "族", "统一名", "交付路径", "字节", "处置依据"]


def read_tsv(p):
    rows = [l.rstrip("\n").rstrip("\r").split("\t")
            for l in io.open(p, encoding="utf-8", newline="") if l.strip()]
    return rows[0], rows[1:]


def build():
    h, data = read_tsv(SRC)
    i = {c: h.index(c) for c in ("序号", "类别", "族", "统一名", "交付路径", "字节", "处置依据", "处置")}
    out = [[r[i["序号"]], r[i["类别"]], r[i["族"]], r[i["统一名"]], r[i["交付路径"]],
            r[i["字节"]], r[i["处置依据"]]] for r in data if r[i["处置"]] == "弃用"]
    keep = [r for r in data if r[i["处置"]].startswith("保留")]
    errs = []
    if len(out) != 497:
        errs.append("G1 停用件 %d != 497" % len(out))
    if len(data) != 629 or len(out) + len(keep) != 629:
        errs.append("G1 守恒失败：629 vs %d(弃用)+%d(保留)" % (len(out), len(keep)))
    if any(r[3].startswith("op_") for r in out):
        errs.append("G2 停用件里混入片头字幕条")
    if errs:
        print("[闸门失败]")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    return out


def write(rows):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(HEAD) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows = build()
    if a.check:
        if not os.path.isfile(OUT):
            print("[--check] 产物不存在"); sys.exit(1)
        old = io.open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        write(rows)
        new = io.open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        ok = old == new
        print("[--check] %s" % ("0 改动（幂等）PASS" if ok else "有改动 → 非幂等"))
        sys.exit(0 if ok else 1)
    write(rows)
    print("写出 %s（%d 行）" % (os.path.relpath(OUT, PROJ), len(rows)))
    print("自检：629 = 497（停用·禁入成品）＋ 132（保留）")


if __name__ == "__main__":
    main()

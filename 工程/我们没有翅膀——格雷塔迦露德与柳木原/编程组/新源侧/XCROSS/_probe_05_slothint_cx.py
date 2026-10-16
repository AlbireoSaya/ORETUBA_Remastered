#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_05_slothint_cx.py — 只读：金标 slot_hint × cx 交叉表（检验 slot_hint 是否能定 cx）。

用法: python -X utf8 _probe_05_slothint_cx.py [--out slot_hint_vs_cx.tsv]
"""
import argparse
import collections
import csv
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PSV_TSV = os.path.join(PROJ, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组",
                       "PSV演出", "立绘事件流.tsv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "slot_hint_vs_cx.tsv"))
    a = ap.parse_args()
    tab = collections.Counter()          # (sh, cx)
    byfam = collections.defaultdict(collections.Counter)
    with io.open(PSV_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if not r["scene_id"].startswith("ot_"):
                continue
            if r["cx"].strip() == "" or r["slot_hint"].strip() == "":
                continue
            sh, cx = int(r["slot_hint"]), int(r["cx"])
            tab[(sh, cx)] += 1
            byfam[r["fam"].strip()][cx] += 1
    cxs = sorted(set(c for _, c in tab))
    shs = sorted(set(s for s, _ in tab))
    with io.open(a.out, "w", encoding="utf-8") as f:
        f.write("# 金标 slot_hint × cx（ot 源，行=有 cx 且 slot_hint 非空）\n")
        f.write("\t".join(["slot_hint", "n"] + ["cx=%d" % c for c in cxs]) + "\n")
        for sh in shs:
            n = sum(tab[(sh, c)] for c in cxs)
            f.write("\t".join([str(sh), str(n)]
                              + [str(tab[(sh, c)]) if tab[(sh, c)] else "" for c in cxs]) + "\n")
    print("slot_hint × cx 交叉表 →", a.out)
    print("%-9s %6s  cx 取值数  cx 众数" % ("slot_hint", "n"))
    for sh in shs:
        row = [(tab[(sh, c)], c) for c in cxs if tab[(sh, c)]]
        row.sort(reverse=True)
        print("%-9d %6d  %6d     %s" % (sh, sum(v for v, _ in row), len(row),
              " ".join("%d×%d" % (v, c) for v, c in row[:8])))
    print("\n每 fam 的 cx 众数:")
    for fam in sorted(byfam):
        row = sorted(byfam[fam].items(), key=lambda kv: -kv[1])[:6]
        print("  %-4s %s" % (fam, " ".join("%d×%d" % (v, k) for k, v in row)))


if __name__ == "__main__":
    main()

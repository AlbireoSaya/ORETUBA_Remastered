# -*- coding: utf-8 -*-
r"""分析（二）：核对主代理给的 13/10 是否另有判定基准；并算 B 的疑似孪生候选。"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
CG = os.path.abspath(os.path.join(OUT, ".."))
MANIFEST = os.path.join(CG, "清单.tsv")
CGDIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\CG背景"
REPDIR = os.path.join(CG, "代表图")
GROUPDIR = os.path.join(CG, "组")

UNMENTIONED = [76, 77, 93, 97, 99, 102, 106, 107, 108, 109, 126, 127, 278, 285, 318, 340, 341, 344, 345]
B4 = [91, 182, 225, 228]


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def main():
    rows = list(csv.DictReader(io.open(MANIFEST, encoding="utf-8-sig"), delimiter="\t"))
    by = {int(r["组序号"]): r for r in rows}

    # 每组全部差分的 md5 集合
    diffs = {}
    for i, r in by.items():
        unis = r["统一名列表"].split("、")
        diffs[i] = {u: md5(os.path.join(CGDIR, u)) for u in unis}
    rep = {i: md5(os.path.join(REPDIR, "%03d_%s.png" % (i, by[i]["组名"]))) for i in by}

    print("=== A 的 19 件：不同判定基准下的孪生数 ===")
    bases = {}
    for label, key in (("代表图 md5", None), ("任一差分 md5", None), ("全部差分 md5 集合相同", None)):
        bases[label] = []
    for i in UNMENTIONED:
        t_rep = [j for j in by if j != i and rep[j] == rep[i]]
        t_any = [j for j in by if j != i and set(diffs[j].values()) & set(diffs[i].values())]
        t_set = [j for j in by if j != i and set(diffs[j].values()) == set(diffs[i].values())]
        bases["代表图 md5"].append(bool(t_rep))
        bases["任一差分 md5"].append(bool(t_any))
        bases["全部差分 md5 集合相同"].append(bool(t_set))
        print("  %03d %-10s rep孪生=%-14s 任一差分孪生=%-14s 集合同=%s"
              % (i, by[i]["组名"], ",".join("%03d" % x for x in t_rep) or "无",
                 ",".join("%03d" % x for x in t_any) or "无",
                 ",".join("%03d" % x for x in t_set) or "无"))
    for k, v in bases.items():
        print("  基准[%s]: 有孪生 %d / 无 %d" % (k, sum(v), len(v) - sum(v)))

    print("\n=== B 的 4 件：全差分 md5 与其它组交叉命中（同画异名的最强证据）===")
    for i in B4:
        print("  %03d %s  尺寸=%s  差分%d: %s" % (i, by[i]["组名"], by[i]["代表图尺寸"],
                                                 int(by[i]["差分件数"]), list(diffs[i].keys())))
        for u, h in diffs[i].items():
            hits = [(j, by[j]["组名"], uu) for j in by if j != i for uu, hh in diffs[j].items() if hh == h]
            print("       %-16s %s  -> %s" % (u, h[:10], hits if hits else "无其它组持有同一字节"))

    print("\n=== B 候选：同画异名配对（去/加 e_ 前缀、同号）===")
    name2id = {by[i]["组名"]: i for i in by}
    for i in B4:
        n = by[i]["组名"]
        cands = []
        if n.startswith("e_"):
            alt = n[2:]
        else:
            alt = "e_" + n
        if alt in name2id:
            cands.append((name2id[alt], alt, "去/加 e_ 前缀同号"))
        # 同数字尾号的近邻
        m = re.match(r"^(?:e_)?([a-z]+)(\d+)$", n)
        if m:
            pre, num = m.group(1), m.group(2)
            for j in sorted(by):
                nm = by[j]["组名"]
                if j == i or nm == alt:
                    continue
                if re.match(r"^(?:e_)?%s(\d+)$" % re.escape(pre), nm):
                    cands.append((j, nm, "同族近邻"))
        print("  %03d %-10s 候选: %s" % (i, n, [( "%03d"%c[0], c[1], c[2]) for c in cands[:6]]))

    print("\n=== 同尺寸 967x725 的组（B 中 182/225/228 均为 967x725）===")
    print("  ", [("%03d" % i, by[i]["组名"]) for i in sorted(by) if by[i]["代表图尺寸"] == "967x725"][:40])


if __name__ == "__main__":
    main()
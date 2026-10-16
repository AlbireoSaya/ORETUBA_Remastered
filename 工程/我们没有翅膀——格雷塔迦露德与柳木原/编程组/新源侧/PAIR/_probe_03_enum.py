#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 3：0x1C43C args[2] 与 0x14084(经 0x17514) args[2] 的位置枚举假设对拍金标。
枚举: -1=保持, 0=640(c), 1=336(l), 2=944(r)
只读。"""
import collections
import csv
import os
import sys

sys.dont_write_bytecode = True   # 只读：不得在 PLACE 目录产生 __pycache__
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
PCDIR = os.path.join(PROJ, "SOB0解码")
GOLD = os.path.join(PROJ, "PSV演出", "立绘事件流.tsv")
ARGRE = re.compile(r"args=\[([^\]]*)\]")


def parse_args(ev):
    m = ARGRE.search(ev)
    if not m:
        return None
    body = m.group(1)
    out, cur, depth = [], [], 0
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out if body != "" else []


def au(raw):
    if raw and raw.startswith("N:"):
        try:
            return int(raw[2:])
        except ValueError:
            return None
    return None


def astr(raw):
    if raw and raw.startswith("S:"):
        return raw[2:]
    return None


def vof(ev):
    i = ev.find("V=")
    if i < 0:
        return ""
    j = i + 2
    while j < len(ev) and ev[j] not in " \t":
        j += 1
    return ev[i + 2:j]


nodes = collections.defaultdict(list)
with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        ev = row["evidence"]
        v = vof(ev)
        if v in ("0x1C43C", "0x14084", "0x17514", "0x18B74", "0x186C8", "0x10428", "0x1C5B0"):
            nodes[(row["scene_id"], int(row["seq"]))].append(
                dict(op=row["op"], v=v, args=parse_args(ev) or [], ev=ev))

gold = collections.defaultdict(list)
with open(GOLD, encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["src"] != "ot" or r["cx"] == "":
            continue
        gold[(r["scene_id"], int(r["seq"]))].append(
            (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))


def match_gold(key, name):
    g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")]
    if not name:
        return None
    gg = [x for x in g if x[2].startswith(name[:4])]
    if len(gg) != 1:
        return None
    return gg[0]


st = collections.Counter()
enum_agg = collections.defaultdict(collections.Counter)
for key, ns in sorted(nodes.items()):
    # gather gold once
    for i, nd in enumerate(ns):
        if nd["v"] == "0x1C43C":
            name = astr(nd["args"][4])
            slot = au(nd["args"][5])
            val = au(nd["args"][2])
            src = "1C43C"
        elif nd["v"] == "0x14084":
            name = astr(nd["args"][1])
            slot = au(nd["args"][2])
            st2 = [s for s in ns if s["v"] == "0x17514" and au(s["args"][3]) == slot]
            val = au(st2[0]["args"][2]) if st2 else None
            src = "14084"
        else:
            continue
        g = match_gold(key, name)
        if g is None:
            st[src + "_nomatch"] += 1
            continue
        st[src + "_n"] += 1
        enum_agg[(src, val)][g[0]] += 1

print("== 覆盖率 ==")
for k in sorted(st):
    print("  %-20s %d" % (k, st[k]))
print()
ENUM = {-1: None, 0: 640, 1: 336, 2: 944}
for src in ("1C43C", "14084"):
    print("=== %s：枚举值 × 金标 cx ===" % src)
    for val in sorted([k[1] for k in enum_agg if k[0] == src], key=lambda v: (v is None, v)):
        c = enum_agg[(src, val)]
        tot = sum(c.values())
        pred = ENUM.get(val)
        hit = c[pred] if pred is not None else 0
        print("  args2=%-12s n=%-6d 顶: %s  |  显式枚举命中 %s"
              % (str(val), tot, c.most_common(5), ("%d/%d=%.3f" % (hit, tot, hit / tot)) if pred else "keep(需状态)"))
    print()

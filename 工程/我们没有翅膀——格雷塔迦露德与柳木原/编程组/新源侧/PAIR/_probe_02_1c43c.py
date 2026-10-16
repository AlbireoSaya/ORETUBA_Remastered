#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 2：0x1C43C（CharacterOpen，体量最大）的 args[3] 是否也是位置枚举？
同时给出 0x1C43C / 0x14084 / 0x17514 的 args 全列分布。
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
vdist = collections.Counter()
with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        ev = row["evidence"]
        v = vof(ev)
        a = parse_args(ev)
        if v in ("0x1C43C", "0x14084", "0x17514", "0x186C8"):
            vdist[v] += 1
        if v not in ("0x1C43C", "0x14084", "0x17514", "0x186C8"):
            continue
        nodes[(row["scene_id"], int(row["seq"]))].append(dict(op=row["op"], v=v, args=a, ev=ev))

print("节点总数：", dict(vdist))
print()
for v in ("0x1C43C", "0x14084", "0x17514", "0x186C8"):
    cols = collections.defaultdict(collections.Counter)
    n = 0
    for ns in nodes.values():
        for nd in ns:
            if nd["v"] != v or nd["args"] is None:
                continue
            n += 1
            for i, a in enumerate(nd["args"]):
                cols[i][a] += 1
    print("=== %s  (n=%d) 逐列 top 值 ===" % (v, n))
    for i in sorted(cols):
        top = cols[i].most_common(6)
        print("   args[%d]: %s" % (i, top))
    print()

# 0x1C43C args[3] vs gold
gold = collections.defaultdict(list)
with open(GOLD, encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["src"] != "ot" or r["cx"] == "":
            continue
        gold[(r["scene_id"], int(r["seq"]))].append(
            (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))

pc = collections.Counter()
for key, ns in sorted(nodes.items()):
    opens = [n for n in ns if n["v"] == "0x1C43C"]
    if not opens:
        continue
    g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")]
    if not g:
        continue
    for o in opens:
        name = astr(o["args"][4]) if o["args"] and len(o["args"]) > 4 else None
        if name is None:
            pc[("noName", o["args"])] += 1
            continue
        gg = [x for x in g if x[2].startswith(name[:4])]
        if len(gg) != 1:
            continue
        pc[(au(o["args"][3]) if len(o["args"]) > 3 else None, gg[0][0])] += 1
print("=== 0x1C43C args[3] × gold cx ===")
agg = collections.defaultdict(collections.Counter)
for (val, cx), n in pc.items():
    if val == "noName":
        continue
    agg[val][cx] += n
for val in sorted(agg, key=lambda v: (v is None, v)):
    tot = sum(agg[val].values())
    print("  args3=%-6s n=%-6d top: %s" % (str(val), tot, agg[val].most_common(6)))
print()
print("noName rows:", sum(n for k, n in pc.items() if k == "noName"))

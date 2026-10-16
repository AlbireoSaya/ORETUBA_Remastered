#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索：0x17514（与 CharacterOpen 0x14084 恒相邻）是不是「位置 setter」？
假设：args[2] 是位置枚举  -1=保持当前槽x  0=中央c  1=左l  2=右r
对拍金标 立绘事件流.tsv 的 CharacterOpen 行 cx。
只读。"""
import collections
import csv
import os
import sys

sys.dont_write_bytecode = True   # 只读：不得在 PLACE 目录产生 __pycache__
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
print("WS=", WS)
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
PCDIR = os.path.join(PROJ, "SOB0解码")
GOLD = os.path.join(PROJ, "PSV演出", "立绘事件流.tsv")

ARGRE = re.compile(r"args=\[([^\]]*)\]")


def parse_args(ev):
    m = ARGRE.search(ev)
    if not m:
        return None
    body = m.group(1)
    if body == "":
        return []
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
    return out


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


# ---- load PC (ot) nodes we care about
nodes = collections.defaultdict(list)  # (scene,seq) -> [dict]
with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        ev = row["evidence"]
        v = vof(ev)
        if v not in ("0x14084", "0x17514", "0x18B74", "0x1C43C", "0x186C8", "0x1C5B0", "0x19808"):
            continue
        a = parse_args(ev)
        nodes[(row["scene_id"], int(row["seq"]))].append(
            dict(op=row["op"], v=v, args=a, ev=ev))

# ---- load gold CharacterOpen rows (ot)
gold = collections.defaultdict(list)
with open(GOLD, encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["src"] != "ot":
            continue
        if r["cx"] == "":
            continue
        gold[(r["scene_id"], int(r["seq"]))].append(
            (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))

# ---- join
cnt = collections.Counter()
pair_cnt = collections.Counter()
detail = []
for key, ns in sorted(nodes.items()):
    opens = [n for n in ns if n["v"] == "0x14084"]
    if not opens:
        continue
    g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")]
    if not g:
        continue
    setters = [n for n in ns if n["v"] == "0x17514"]
    for o in opens:
        name = astr(o["args"][1]) if o["args"] and len(o["args"]) > 1 else None
        slot = au(o["args"][2]) if o["args"] and len(o["args"]) > 2 else None
        gg = [x for x in g if name and x[2].startswith(name[:4])]
        if len(gg) != 1:
            cnt["open_no_single_gold"] += 1
            continue
        st2 = [s for s in setters if au(s["args"][3]) == slot]
        val = au(st2[0]["args"][2]) if st2 else None
        cnt["paired"] += 1
        pair_cnt[(val, gg[0][0])] += 1
        detail.append((key[0], key[1], name, slot, val, gg[0][0], gg[0][2], gg[0][1]))

print("open_with_single_gold=", cnt["paired"], "no_single=", cnt["open_no_single_gold"])
print()
print("=== 0x17514 args[2] 值 × 金标 cx 分布（前 40）===")
for (val, cx), n in pair_cnt.most_common(40):
    print("  setter_args2=%-6s gold_cx=%-6d n=%d" % (str(val), cx, n))
print()
print("=== 按 args[2] 值汇总 ===")
agg = collections.defaultdict(collections.Counter)
for (val, cx), n in pair_cnt.items():
    agg[val][cx] += n
for val in sorted(agg, key=lambda v: (v is None, v)):
    tot = sum(agg[val].values())
    print("  args2=%-6s n=%-6d top: %s" % (str(val), tot, agg[val].most_common(6)))

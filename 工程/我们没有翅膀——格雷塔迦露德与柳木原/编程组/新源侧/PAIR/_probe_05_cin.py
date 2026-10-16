#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 5：CIN* 家族 / 0x17514 双节点 / 槽首次使用 vs 复用 的行为。
只读。"""
import collections
import csv
import os
import sys

sys.dont_write_bytecode = True   # 只读：不得在 PLACE 目录产生 __pycache__
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ⚠️ 本探针按「距工作区根 3 层」推 WS、并从旧开发位置（`子代理工作区\ISSUE-20261008-09\PLACE\`，
#    **历史副本，勿用**）import place_dsl ⇒ 只适用于旧位置复跑；入库位置（5 层）会错位。
#    正式判据请用 `pair_place.py`（同树兄弟 `..\PLACE` + 多候选根解析）。本探针不入复跑链，未改常量。
WS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
PCDIR = os.path.join(PROJ, "SOB0解码")
GOLD = os.path.join(PROJ, "PSV演出", "立绘事件流.tsv")
sys.path.insert(0, os.path.join(WS, "子代理工作区", "ISSUE-20261008-09", "PLACE"))
import place_dsl as P  # noqa: E402


def vof(ev):
    i = ev.find("V=")
    j = i + 2
    while j < len(ev) and ev[j] not in " \t":
        j += 1
    return ev[i + 2:j]


nodes = collections.defaultdict(list)
with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        ev = row["evidence"]
        nodes[(row["scene_id"], int(row["seq"]))].append(
            dict(op=row["op"], v=vof(ev), args=P.parse_args_from_evidence(ev) or [], ev=ev))

gold = collections.defaultdict(list)
with open(GOLD, encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["src"] != "ot" or r["cx"] == "":
            continue
        gold[(r["scene_id"], int(r["seq"]))].append(
            (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))

# 0x17514 对：每个 (scene,seq) 里 args[1] 分布
pair = collections.Counter()
two_ = collections.Counter()
for key, ns in nodes.items():
    s = [n for n in ns if n["v"] == "0x17514"]
    pair[collections.Counter(P.arg_uint(n["args"][1]) for n in s if len(n["args"]) > 1).most_common(1)[0][0] if s else "none"] += 1
    if len(s) >= 2:
        two_["len>=2"] += 1
print("0x17514 args[1] (每 key 众数):", dict(pair))
print("key 里 0x17514 个数>=2 :", dict(two_))

# 每个 0x14084 配到的 0x17514 列表
pat = collections.Counter()
for key, ns in nodes.items():
    for i, n in enumerate(ns):
        if n["v"] != "0x14084" or len(n["args"]) < 3:
            continue
        slot = P.arg_uint(n["args"][2])
        s = [x for x in ns if x["v"] == "0x17514" and len(x["args"]) > 3
             and P.arg_uint(x["args"][3]) == slot]
        pat[tuple(P.arg_uint(x["args"][2]) for x in s)] += 1
print("\n每个 0x14084 对应 0x17514 args2 元组 (top20):")
for k, v in pat.most_common(20):
    print("   ", k, v)

# CIN
cin = collections.Counter()
for key, ns in sorted(nodes.items()):
    for n in ns:
        if n["v"] not in ("0x1C43C", "0x14084"):
            continue
        name = P.arg_str(n["args"][4]) if n["v"] == "0x1C43C" else P.arg_str(n["args"][1])
        if not name or not name.startswith("CIN"):
            continue
        g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")
             and x[2].startswith(name[:4])]
        if len(g) != 1:
            cin["nomatch"] += 1
            continue
        cin[g[0][0]] += 1
print("\nCIN 家族 open 的金标 cx 分布:", cin.most_common(15))

# 非 CIN open 的 keep（enum=-1）cx 分布，按 槽是否首次使用
fresh = collections.Counter()
reuse = collections.Counter()
seen_slot = {}
for key in sorted(nodes):
    for n in nodes[key]:
        if n["v"] not in ("0x1C43C", "0x14084"):
            continue
        if n["v"] == "0x1C43C":
            name = P.arg_str(n["args"][4]); slot = P.arg_uint(n["args"][5])
            val = P.arg_uint(n["args"][2])
        else:
            name = P.arg_str(n["args"][1]); slot = P.arg_uint(n["args"][2])
            s = [x for x in nodes[key] if x["v"] == "0x17514" and len(x["args"]) > 3
                 and P.arg_uint(x["args"][3]) == slot]
            val = P.arg_uint(s[0]["args"][2]) if s else None
        if val != 4294967295 or slot is None:
            continue
        g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")
             and name and x[2].startswith(name[:4])]
        if len(g) != 1:
            continue
        k = (key[0], slot)
        d = fresh if k not in seen_slot else reuse
        d["n"] += 1
        d[g[0][0]] += 1
        seen_slot[k] = 1
print("\nkeep(enum=-1) 非CIN：槽首次使用时的 cx 分布:", fresh.most_common(8))
print("keep(enum=-1) 非CIN：槽复用时（有前序）:", reuse.most_common(8))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 7：非 CIN 反例的成因分类。只读。"""
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
        nodes[(row["scene_id"], int(row["seq"]))].append(
            dict(op=row["op"], v=vof(row["evidence"]),
                 args=P.parse_args_from_evidence(row["evidence"]) or [], ev=row["evidence"]))

gold = collections.defaultdict(list)
with open(GOLD, encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["src"] != "ot" or r["cx"] == "":
            continue
        gold[(r["scene_id"], int(r["seq"]))].append(
            (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))

TOKFAM = {"0x18B74": (2, 3), "0x186C8": (1, 2), "0x10428": (5, None)}
ENUM = {0: 960, 1: 504, 2: 1416}


def norm(v):
    return -1 if v == 4294967295 else v


SC = {}
res = []
for key in sorted(nodes):
    ns = nodes[key]
    state = SC.setdefault(key[0], {})
    for nd in ns:
        v, a = nd["v"], nd["args"]
        if v in TOKFAM:
            ci, si = TOKFAM[v]
            ctrl = P.arg_str(a[ci]) if ci < len(a) else None
            slot = P.arg_uint(a[si]) if si is not None and si < len(a) else None
            if slot is None or ctrl is None:
                continue
            ops, unks = P.tokenize_ctrl(ctrl)
            if unks:
                continue
            cur = state.setdefault(slot, {"x": ("num", 960), "y": P.BOTTOM_Y})
            P.apply_ops(ops, cur)
            continue
        if v not in ("0x1C43C", "0x14084"):
            continue
        if v == "0x1C43C":
            name, slot = P.arg_str(a[4]), P.arg_uint(a[5])
            val = norm(P.arg_uint(a[2])) if len(a) > 2 else None
        else:
            name, slot = P.arg_str(a[1]), P.arg_uint(a[2])
            s = [x for x in ns if x["v"] == "0x17514" and len(x["args"]) > 3
                 and P.arg_uint(x["args"][3]) == slot]
            val = norm(P.arg_uint(s[0]["args"][2])) if s else None
        if slot is None:
            continue
        had = slot in state
        cur = state.setdefault(slot, {"x": ("num", 960), "y": P.BOTTOM_Y})
        if val in ENUM:
            cur["x"] = ("num", ENUM[val])
        g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")
             and name and x[2].startswith(name[:4])]
        if len(g) != 1:
            continue
        got = cur["x"]
        res.append(dict(scene=key[0], seq=key[1], name=name, slot=slot, val=val, had=had,
                        pred=(got[1] if got[0] == "num" else None), gold=g[0][0] * 1.5,
                        gcx=g[0][0], v=v, ns=ns))

miss = [r for r in res if r["pred"] != r["gold"] and not (r["name"] or "").startswith("CIN")]
print("非CIN 反例 =", len(miss), " / 样本", len([r for r in res if not (r['name'] or '').startswith('CIN')]))
c = collections.Counter((r["val"], r["had"] and "slot已见" or "slot首用") for r in miss)
print("按 (枚举值, 槽历史):", dict(c))
cs = collections.Counter(r["scene"] for r in miss)
print("\n反例最多的场 (top15):")
for s, n in cs.most_common(15):
    tot = sum(1 for r in res if r["scene"] == s and not (r["name"] or "").startswith("CIN"))
    print("   %-16s miss=%d / open=%d" % (s, n, tot))
print("\n样例 25 条:")
for r in miss[:25]:
    print("   %-16s:%-5d %-8s slot=%s val=%-11s had=%s 我=%-6s 金=%s" %
          (r["scene"], r["seq"], r["name"], r["slot"], str(r["val"]), r["had"],
           str(r["pred"]), str(r["gold"])))
# 对这些反例，看该场该槽此前的显式枚举/token
print("\n-- 反例槽的历史（前 12 条非CIN）--")
for r in miss[:12]:
    print("  === %s slot %s ===" % (r["scene"], r["slot"]))
    for k in sorted(nodes):
        if k[0] != r["scene"] or k[1] > r["seq"]:
            continue
        for nd in nodes[k]:
            if nd["v"] in ("0x1C43C", "0x14084", "0x17514", "0x18B74", "0x186C8"):
                sl = None
                if nd["v"] == "0x1C43C":
                    sl = P.arg_uint(nd["args"][5])
                elif len(nd["args"]) > 3 and nd["v"] == "0x17514":
                    sl = P.arg_uint(nd["args"][3])
                elif nd["v"] in ("0x18B74", "0x186C8"):
                    sl = P.arg_uint(nd["args"][3 if nd["v"] == "0x18B74" else 2])
                elif nd["v"] == "0x14084":
                    sl = P.arg_uint(nd["args"][2])
                if sl == r["slot"]:
                    print("     %-6d %-8s %s" % (k[1], nd["v"], nd["ev"][nd["ev"].find("args="):nd["ev"].find(" ctrl")]))

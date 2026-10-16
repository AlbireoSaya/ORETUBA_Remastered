#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 9：状态重置规则变体（CharacterDelete / 角色易主）对命中率的影响。只读。"""
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


FA = ("0x1C43C", "0x14084", "0x17514", "0x18B74", "0x186C8", "0x10428", "0x1C5B0", "0x19808")
nodes = collections.defaultdict(list)
with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        v = vof(row["evidence"])
        if v in FA:
            nodes[(row["scene_id"], int(row["seq"]))].append(
                dict(op=row["op"], v=v, args=P.parse_args_from_evidence(row["evidence"]) or []))
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


def run(del_reset, change_reset):
    SC = {}
    res = []
    for key in sorted(nodes):
        ns = nodes[key]
        state = SC.setdefault(key[0], {})
        for nd in ns:
            v, a = nd["v"], nd["args"]
            if v == "0x1C5B0":
                if del_reset == "all" or (del_reset == "args0" and P.arg_uint(a[0]) == 0):
                    state.clear()
                continue
            if v == "0x19808":
                continue
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
            if change_reset and name and slot in state and state[slot].get("nm") and \
               state[slot]["nm"][:4] != name[:4]:
                state[slot] = {"x": ("num", 960), "y": P.BOTTOM_Y}
            cur = state.setdefault(slot, {"x": ("num", 960), "y": P.BOTTOM_Y})
            if name:
                cur["nm"] = name
            if val in ENUM:
                cur["x"] = ("num", ENUM[val])
            g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")]
            gg = [x for x in g if name and x[2] == name] or [x for x in g if name and x[2].startswith(name[:4])]
            if len(gg) != 1:
                continue
            got = cur["x"]
            res.append(((got[1] if got[0] == "num" else None), gg[0][0] * 1.5, name or "", val))
    ok = sum(1 for r in res if r[0] == r[1])
    return res, ok


for dr in ("none", "all", "args0"):
    for cr in (False, True):
        res, ok = run(dr, cr)
        byval = collections.defaultdict(lambda: [0, 0])
        for r in res:
            byval[r[3]][1] += 1
            byval[r[3]][0] += (r[0] == r[1])
        miss = [r for r in res if r[0] != r[1]]
        print("del_reset=%-6s change_reset=%-5s n=%-6d hit=%-6d rate=%.4f  keep=%d/%d  miss=%d(CIN%d)"
              % (dr, cr, len(res), ok, ok / len(res), byval[-1][0], byval[-1][1], len(miss),
                 sum(1 for r in miss if r[2].startswith("CIN"))))

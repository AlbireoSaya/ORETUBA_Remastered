#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探索 4：按槽的状态机（route B）。
状态机：槽 s 的 x 初值 = 960(1920空间,=中心)。
  * 0x1C43C / 0x14084(经 0x17514) 的枚举 args2: -1=保持,0=960,1=504,2=1416
  * 0x18B74 / 0x186C8 / 0x10428 的 ctrl token 按 PLACE 的 DSL 施加到槽状态
按 (scene, seq, 文件序) 顺序推进；open 行取施加后的槽状态。
对拍金标 x1920 = cx*1.5。只读。
"""
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

ENUM = {-1: None, 0: 960, 1: 504, 2: 1416}


def norm(val):
    return -1 if val == 4294967295 else val


def enum_of(ns, slot, val):
    val = norm(val)
    if val == -1:
        return None
    x = ENUM.get(val)
    return ("num", x) if x is not None else None


def load():
    nodes = collections.defaultdict(list)
    with open(os.path.join(PCDIR, "解出_ot.tsv"), encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            ev = row["evidence"]
            v = P.vof(ev) if hasattr(P, "vof") else None
            if v is None:
                i = ev.find("V=")
                j = i + 2
                while j < len(ev) and ev[j] not in " \t":
                    j += 1
                v = ev[i + 2:j]
            if v not in ("0x1C43C", "0x14084", "0x17514", "0x18B74", "0x186C8", "0x10428", "0x1C5B0"):
                continue
            nodes[(row["scene_id"], int(row["seq"]))].append(
                dict(op=row["op"], v=v, args=P.parse_args_from_evidence(ev) or [], ev=ev))
    gold = collections.defaultdict(list)
    with open(GOLD, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["src"] != "ot" or r["cx"] == "":
                continue
            gold[(r["scene_id"], int(r["seq"]))].append(
                (int(r["cx"]), r["task_type"], r["ps_name"], r["slot_hint"]))
    return nodes, gold


TOKFAM = {
    "0x18B74": ("ctrl", 2, 3),   # ctrl=args[2], slot=args[3]
    "0x186C8": ("ctrl", 1, 2),
    "0x10428": ("ctrl", 5, None),
}


def main():
    nodes, gold = load()
    st = collections.Counter()
    res = []
    SCENE_STATE = {}
    for key in sorted(nodes):
        ns = nodes[key]
        scene = key[0]
        state = SCENE_STATE.setdefault(scene, {})
        for nd in ns:
            v = nd["v"]
            a = nd["args"]
            if v == "0x1C5B0":
                continue
            if v == "0x17514":
                continue  # 由 0x14084 处消费
            if v == "0x18B74" or v == "0x186C8" or v == "0x10428":
                _, ci, si = TOKFAM[v]
                if ci >= len(a):
                    continue
                ctrl = P.arg_str(a[ci])
                slot = P.arg_uint(a[si]) if si is not None and si < len(a) else None
                if slot is None or ctrl is None:
                    continue
                ops, unks = P.tokenize_ctrl(ctrl)
                if unks:
                    st["tok_unk"] += 1
                    continue
                cur = state.get(slot, {"x": ("num", 960), "y": P.BOTTOM_Y})
                P.apply_ops(ops, cur)
                state[slot] = cur
                continue
            # open families
            if v == "0x1C43C":
                name = P.arg_str(a[4]) if len(a) > 4 else None
                slot = P.arg_uint(a[5]) if len(a) > 5 else None
                val = P.arg_uint(a[2]) if len(a) > 2 else None
            elif v == "0x14084":
                name = P.arg_str(a[1]) if len(a) > 1 else None
                slot = P.arg_uint(a[2]) if len(a) > 2 else None
                s2 = [s for s in ns if s["v"] == "0x17514" and len(s["args"]) > 3
                      and P.arg_uint(s["args"][3]) == slot]
                val = P.arg_uint(s2[0]["args"][2]) if s2 else None
            else:
                continue
            if slot is None:
                st["open_noslot"] += 1
                continue
            cur = state.get(slot, {"x": ("num", 960), "y": P.BOTTOM_Y})
            xv = enum_of(ns, slot, val) if val is not None else None
            if xv is not None:
                cur["x"] = xv
            state[slot] = cur
            # match gold
            g = [x for x in gold.get(key, []) if x[1] in ("CharacterOpen", "CharacterOpenBS")]
            gg = [x for x in g if name and x[2].startswith(name[:4])]
            if len(gg) != 1:
                st[v + "_nomatch"] += 1
                continue
            got = cur["x"]
            pred = got[1] if got and got[0] == "num" else None
            st[v + "_n"] += 1
            res.append((key[0], key[1], v, name, slot, val, pred, gg[0][0] * 1.5, gg[0][0]))
    print("== 状态机 ==")
    for k in sorted(st):
        print("  %-22s %d" % (k, st[k]))
    print()
    ok = sum(1 for r in res if r[6] == r[7])
    print("样本=%d 命中=%d 命中率=%.4f" % (len(res), ok, ok / len(res) if res else 0))
    # by enum val
    agg = collections.defaultdict(lambda: [0, 0])
    for r in res:
        agg[r[5]][1] += 1
        if r[6] == r[7]:
            agg[r[5]][0] += 1
    print("\n-- 按枚举值 --")
    for val in sorted(agg, key=lambda v: (v is None, v)):
        h, n = agg[val]
        print("  args2=%-12s %d/%d = %.4f" % (str(val), h, n, h / n))
    # by fam
    agg2 = collections.defaultdict(lambda: [0, 0])
    for r in res:
        agg2[r[2]][1] += 1
        if r[6] == r[7]:
            agg2[r[2]][0] += 1
    print("\n-- 按族 --")
    for val in sorted(agg2):
        h, n = agg2[val]
        print("  %-10s %d/%d = %.4f" % (val, h, n, h / n))
    miss = [r for r in res if r[6] != r[7]]
    print("\n-- 反例 %d 条（前 25）--" % len(miss))
    for r in miss[:25]:
        print("   %-16s:%-5d %-8s %-8s slot=%s a2=%-11s 我x1920=%-6s 金=%s"
              % (r[0], r[1], r[2], r[3], r[4], str(r[5]), str(r[6]), str(r[7])))


main()

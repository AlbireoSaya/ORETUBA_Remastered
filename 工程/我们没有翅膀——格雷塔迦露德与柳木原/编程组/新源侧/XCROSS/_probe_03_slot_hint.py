#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_03_slot_hint.py — 只读：金标 `slot_hint` 与 PC 槽号（开立族实参位）的对照。

问题：PSV `slot_hint` 与 PC 槽号是否同一量？是否恒等？有无系统性偏移？偏移是否随场变化？

口径：
  * PC 侧：`编程组\\SOB0解码\\解出_ot.tsv`（ot 源）。
    开立族 V∈{0x1C43C(slot=5,name=4), 0x14084(slot=2,name=1), 0x186C8(slot=2)}；
    `name=='0'` 视为删除，不计。族 fam = 角色名前缀小写。
  * 金标：`PSV演出\\立绘事件流.tsv`；键 `(scene_id, seq, fam)` → slot_hint 集（非空）。
  * 配对：(scene,seq,fam) 命中且金标 slot_hint 唯一 → delta = pc_slot − slot_hint。

用法:
  python -X utf8 _probe_03_slot_hint.py [--src ot] [--out slot_hint_vs_arg0.tsv]
"""
import argparse
import collections
import csv
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE = os.path.join(PROJ, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组")
PSV_TSV = os.path.join(BASE, "PSV演出", "立绘事件流.tsv")
PC_TSV = {"ot": os.path.join(BASE, "SOB0解码", "解出_ot.tsv"),
          "otr": os.path.join(BASE, "SOB0解码", "解出_otr.tsv"),
          "otp": os.path.join(BASE, "SOB0解码", "解出_otp.tsv")}
# 开立族: src -> V -> (slot下标, name下标 or None)
OPEN = {
    "ot": {"0x1C43C": (5, 4), "0x14084": (2, 1), "0x186C8": (2, None)},
    "otr": {"0x1C43C": (5, 4), "0x14084": (2, 1), "0x186C8": (2, None)},
    "otp": {"0x1A618": (3, 2), "0x11078": (2, 1), "0x156E8": (3, None)},
}
ARGS_RE = re.compile(r"args=\[(.*)\]\s+ctrl=")


def split_top(s):
    out, cur, d = [], [], 0
    for ch in s:
        if ch == "(":
            d += 1
        elif ch == ")":
            d -= 1
        if ch == "," and d == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse_args(ev):
    m = ARGS_RE.search(ev or "")
    if not m:
        return None
    if m.group(1) == "":
        return []
    a = []
    for p in split_top(m.group(1)):
        if p.startswith("N:"):
            try:
                a.append(("N", int(p[2:])))
            except ValueError:
                a.append(("?", p))
        elif p.startswith("S:"):
            a.append(("S", p[2:]))
        else:
            a.append(("?", p))
    return a


def fam_of(name):
    m = re.match(r"^([A-Za-z]+)", name or "")
    return m.group(1).lower() if m else None


def load_gold(ot_only):
    g = collections.defaultdict(set)
    with io.open(PSV_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["slot_hint"].strip() == "":
                continue
            if ot_only and not r["scene_id"].startswith("ot_"):
                continue
            g[(r["scene_id"], int(r["seq"]), r["fam"].strip())].add(int(r["slot_hint"]))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--out", default=os.path.join(HERE, "slot_hint_vs_arg0.tsv"))
    args = ap.parse_args()

    gold = load_gold(True)
    rows = []
    delta = collections.Counter()
    per_scene = collections.defaultdict(collections.Counter)
    n_open = 0
    n_paired = 0
    unmatched = collections.Counter()

    cur, slot2fam = None, {}
    for r in csv.DictReader(io.open(PC_TSV[args.src], encoding="utf-8"), delimiter="\t"):
        scene = r["scene_id"]
        if scene != cur:
            cur, slot2fam = scene, {}
        seq = int(r["seq"])
        ev = r["evidence"] or ""
        m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
        V = m.group(1) if m else None
        tv = OPEN[args.src]
        if V not in tv:
            continue
        si, ni = tv[V]
        a = parse_args(ev)
        if a is None or si >= len(a):
            continue
        slot = a[si][1]
        name = None
        if ni is not None and ni < len(a) and a[ni][0] == "S":
            name = a[ni][1]
        if name == "0":
            slot2fam[slot] = None
            continue
        fam = fam_of(name) if name else slot2fam.get(slot)
        if name:
            slot2fam[slot] = fam
        n_open += 1
        if fam is None:
            unmatched["no_fam"] += 1
            continue
        sh = gold.get((scene, seq, fam))
        if not sh:
            unmatched["no_gold"] += 1
            continue
        if len(sh) != 1:
            unmatched["gold_multi"] += 1
            continue
        shv = next(iter(sh))
        d = slot - shv
        n_paired += 1
        delta[d] += 1
        per_scene[scene][d] += 1
        rows.append((scene, seq, fam, slot, shv, d))

    per_scene_delta = {}
    for scene, c in per_scene.items():
        per_scene_delta[scene] = dict(c)

    with io.open(args.out, "w", encoding="utf-8") as f:
        f.write("# PSV slot_hint vs PC 槽号（%s 源；键 (scene,seq,fam)，金标 slot_hint 唯一）\n"
                % args.src)
        f.write("# 开立站=%d 可配对=%d 未配对=%s\n"
                % (n_open, n_paired,
                   ", ".join("%s:%d" % (k, v) for k, v in sorted(unmatched.items()))))
        f.write("# delta = PC槽号 − PSV slot_hint 全局分布: %s\n"
                % ", ".join("%d:%d" % (k, v) for k, v in sorted(delta.items())))
        f.write("\tscene_id\tseq\tfam\tpc_slot\tpsv_slot_hint\tdelta\n")
        for row in rows:
            f.write("\t" + "\t".join(str(x) for x in row) + "\n")
        f.write("\n# --- 逐场 delta 分布 ---\n")
        f.write("scene_id\tn_paired\tdelta_dist\n")
        for scene in sorted(per_scene_delta):
            dd = per_scene_delta[scene]
            f.write("%s\t%d\t%s\n" % (scene, sum(dd.values()),
                    ",".join("%d:%d" % (k, v) for k, v in sorted(dd.items()))))
    print("开立站 %d，可配对 %d，未配对 %s" % (n_open, n_paired, dict(unmatched)))
    print("全局 delta(=PC槽号−PSV slot_hint) 分布:", dict(sorted(delta.items())))
    # 逐场：有几种 delta
    mixed = {s: d for s, d in per_scene_delta.items() if len(d) > 1}
    print("场数（可配对）=%d；其中场内 delta 不唯一 =%d" % (len(per_scene_delta), len(mixed)))
    # 按 delta 值统计“整场唯一 delta”的场
    byd = collections.Counter()
    for s, d in per_scene_delta.items():
        if len(d) == 1:
            byd[next(iter(d))] += 1
    print("整场单一 delta 的场分布:", dict(sorted(byd.items())))
    print("→", args.out)


if __name__ == "__main__":
    main()

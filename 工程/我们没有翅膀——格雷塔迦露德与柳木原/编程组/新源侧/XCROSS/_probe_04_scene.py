#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_04_scene.py — 只读：单场 PSV 金标 × PC 事件逐条并排（seq 对齐）。

用法:
  python -X utf8 _probe_04_scene.py --scene ot_s01_04i [--out s01_04i_对照.tsv]
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
PC_TSV = os.path.join(BASE, "SOB0解码", "解出_ot.tsv")
ARGS_RE = re.compile(r"args=\[(.*)\]\s+ctrl=")
VNAME = {"0x1C43C": "Open", "0x14084": "Open*", "0x186C8": "ChrIn",
         "0x18B74": "Anim/Move", "0x1C5B0": "Delete"}
SLOTI = {"0x1C43C": (5, 4), "0x14084": (2, 1), "0x186C8": (2, None), "0x18B74": (3, None),
         "0x1C5B0": (None, None)}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sc = a.scene

    psv = collections.defaultdict(list)
    with io.open(PSV_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["scene_id"] != sc:
                continue
            psv[int(r["seq"])].append(r)
    pc = collections.defaultdict(list)
    with io.open(PC_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["scene_id"] != sc:
                continue
            pc[int(r["seq"])].append(r)

    seqs = sorted(set(psv) | set(pc))
    out = io.StringIO()
    out.write("seq\tPSV(task_type/ps_name/fam/slot_hint/cx/cy/cpri)\tPC(V/role/slot/name/token/args)\n")
    for seq in seqs:
        pl = []
        for r in psv[seq]:
            pl.append("%s/%s/%s/sh=%s/cx=%s/cy=%s/cpri=%s"
                      % (r["task_type"], r["ps_name"], r["fam"], r["slot_hint"] or "-",
                         r["cx"] or "-", r["cy"] or "-", r["cpri"] or "-"))
        cl = []
        for r in pc[seq]:
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", r["arg3"] or "")
            V = m.group(1) if m else None
            if V not in VNAME:
                continue
            ar = parse_args(r["evidence"]) or []
            si, ni = SLOTI[V]
            slot = ar[si][1] if si is not None and si < len(ar) else "-"
            name = ar[ni][1] if ni is not None and ni < len(ar) and ar[ni][0] == "S" else "-"
            ctrl = r["arg1"] or "-"
            cl.append("%s/%s/slot=%s/%s/%s/%s"
                      % (V, VNAME[V], slot, name, ctrl, ",".join(str(x) for _, x in ar)))
        out.write("%d\t%s\t%s\n" % (seq, " ; ".join(pl) or "-", " ; ".join(cl) or "-"))
    text = out.getvalue()
    if a.out:
        io.open(a.out, "w", encoding="utf-8").write(text)
        print("→", a.out)
    else:
        print(text)


if __name__ == "__main__":
    main()

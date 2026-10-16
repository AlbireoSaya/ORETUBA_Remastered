# -*- coding: utf-8 -*-
r"""_accept_compare.py —— 由两份已构建的 `scene_*.tjs` 目录生成**逐场 stageInfo 对照**。

用法：
  python -X utf8 编程组/other语义接入/_accept_compare.py \
      --off  编程组/other语义接入/验收/_stage_off \
      --tier1 编程组/other语义接入/验收/_stage_tier1 \
      --out  编程组/other语义接入/验收/逐场对照.tsv

对照列：scene_id / src / off_{chr,removed,moved,placed} / t1_{...} / d_{...}。
只列**任一计数发生变化**的场景（含 removed/placed/chr/moved 任一 Δ≠0）。
只读；不构建、不改产物。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PRG, "工具"))
sys.dont_write_bytecode = True

RE_ONE = re.compile(r"stageInfo:%\[\s*chr:(-?\d+),\s*se:(-?\d+),\s*removed:(-?\d+),\s*moved:(-?\d+),\s*placed:(-?\d+)")
FIELDS = ("chr", "removed", "moved", "placed")


def read_dir(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("scene_") and fn.endswith(".tjs")):
            continue
        m = RE_ONE.search(io.open(os.path.join(d, fn), encoding="utf-8", errors="replace").read())
        if not m:
            continue
        sid = fn[len("scene_"):-len(".tjs")]
        out[sid] = dict(zip(FIELDS, (int(m.group(1)), int(m.group(3)), int(m.group(4)), int(m.group(5)))))
    return out


def src_of(sid):
    return sid.split("_", 1)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--off", required=True)
    ap.add_argument("--tier1", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    off, t1 = read_dir(a.off), read_dir(a.tier1)
    sids = sorted(set(off) | set(t1))
    header = (["scene_id", "src"]
              + ["off_" + f for f in FIELDS] + ["t1_" + f for f in FIELDS]
              + ["d_" + f for f in FIELDS])
    rows = []
    for sid in sids:
        o = off.get(sid) or {f: 0 for f in FIELDS}
        n = t1.get(sid) or {f: 0 for f in FIELDS}
        if all(o[f] == n[f] for f in FIELDS):
            continue
        rows.append([sid, src_of(sid)]
                    + [o[f] for f in FIELDS] + [n[f] for f in FIELDS]
                    + [n[f] - o[f] for f in FIELDS])
    with io.open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    d0 = 2 + len(FIELDS) + len(FIELDS)          # d_* 起始列
    dr = [r for r in rows if r[d0 + FIELDS.index("removed")] != 0]
    dp = [r for r in rows if r[d0 + FIELDS.index("placed")] != 0]
    dc = [r for r in rows if r[d0 + FIELDS.index("chr")] != 0 or r[d0 + FIELDS.index("moved")] != 0]
    print("对照表 %s ｜ 生效场景 %d（含 chr/removed/moved/placed 任一变化）" % (a.out, len(rows)))
    print("  其中 removed 变化场景 %d ｜ placed 变化场景 %d ｜ chr/moved 变化场景 %d"
          % (len(dr), len(dp), len(dc)))
    for f in FIELDS:
        print("  合计 Δ%s = %d" % (f, sum(r[d0 + FIELDS.index(f)] for r in rows)))


if __name__ == "__main__":
    main()

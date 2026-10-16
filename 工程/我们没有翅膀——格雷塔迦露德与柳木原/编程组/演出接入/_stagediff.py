#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
`_stagediff.py` —— 两套 `scene_*.tjs` 的**逐场演出事件差分**（ISSUE-20261007-11 T5）
================================================================================
只读：只读两套 `story\scene_*.tjs`，不写任何文件（`--tsv <path>` 时写一份逐场表）。

为什么不用文本 diff：`scene_*.tjs` 里 `stage[]` 是**紧凑行**，文本 diff 会把「同一行内多一个
元素」显示成整行重写。本工具按**事件行**切分（`%[ … ]`），做**多重集差分**，给出：
  · `added` / `removed`：事件的增删（精确到 `(seq, op, slot, fam, t, x, y, w, h, z[, dur, dir])`）；
  · `changed_rest`：`stage[]` 以外部分（标题/台词/选择支/背景候选…）是否有任何变化 —— **须为 0**；
  · 逐场明细：新增/删除/受影响场数。
用法：
  python -X utf8 编程组/演出接入/_stagediff.py --a <off 构建 story 目录> --b <on 构建 story 目录> \
      [--tsv <逐场差分表>]
"""
import argparse, glob, io, os, re, sys
from collections import Counter


def split_scene(txt):
    """→ (stage_rows[list[str]], rest[str])：把 `\\tstage:[ … ],` 块单独切出。"""
    m = re.search(r"\n\tstage:\[\n(.*?)\n\t\],\n", txt, re.S)
    if not m:
        return [], txt
    body = m.group(1)
    rows = [x.strip().rstrip(",") for x in re.split(r",\n", body) if x.strip()]
    rest = txt[:m.start()] + "\n<STAGE>" + txt[m.end():]
    return rows, rest


def row_key(s):
    """事件行 → 归一化键（去掉 `%%[ ]` 包装与空白差异）。"""
    return re.sub(r"\s+", "", s.replace("%%[", "").replace("]", ""))


def op_of(key):
    m = re.search(r"op:([^,]+)", key)
    return m.group(1) if m else "?"


def fmt(counter):
    return ",".join("%s:%d" % (o, c) for o, c in sorted(counter.items())) or "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="基线（off）story 目录")
    ap.add_argument("--b", required=True, help="对照（on）story 目录")
    ap.add_argument("--tsv", default="", help="逐场差分 TSV（可选）")
    a = ap.parse_args()
    fa = {os.path.basename(p): p for p in glob.glob(os.path.join(a.a, "scene_*.tjs"))}
    fb = {os.path.basename(p): p for p in glob.glob(os.path.join(a.b, "scene_*.tjs"))}
    print("A=%s（%d 件）｜ B=%s（%d 件）" % (os.path.abspath(a.a), len(fa), os.path.abspath(a.b), len(fb)))
    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))
    if only_a or only_b:
        print("!! 文件集不同：仅 A %d ｜ 仅 B %d" % (len(only_a), len(only_b)))
    tot_add = tot_rem = n_chg_scene = 0
    op_add, op_rem = Counter(), Counter()
    rest_changed = []
    rows_out = ["scene_id\tadded\tremoved\tadd_ops\trem_ops"]
    for name in sorted(set(fa) & set(fb)):
        ta = io.open(fa[name], encoding="utf-8").read()
        tb = io.open(fb[name], encoding="utf-8").read()
        ra, resta = split_scene(ta)
        rb, restb = split_scene(tb)
        if resta != restb:
            rest_changed.append(name)
        ca = Counter(row_key(x) for x in ra)
        cb = Counter(row_key(x) for x in rb)
        add = cb - ca
        rem = ca - cb
        na, nr = sum(add.values()), sum(rem.values())
        if na or nr:
            n_chg_scene += 1
            for k, v in add.items():
                op_add[op_of(k)] += v
            for k, v in rem.items():
                op_rem[op_of(k)] += v
            rows_out.append("%s\t%d\t%d\t%s\t%s"
                            % (name[6:-4], na, nr,
                               fmt(Counter(op_of(k) for k in add.elements())),
                               fmt(Counter(op_of(k) for k in rem.elements()))))
        tot_add += na
        tot_rem += nr
    print("事件差分：added %d ｜ removed %d ｜ 受影响场 %d / %d" % (tot_add, tot_rem, n_chg_scene, len(fa)))
    print("  added 按 op：%s" % dict(op_add))
    print("  removed 按 op：%s" % dict(op_rem))
    print("  stage[] 以外发生变化（须为 0）：%d %s" % (len(rest_changed), rest_changed[:5]))
    if a.tsv:
        with io.open(a.tsv, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(rows_out) + "\n")
        print(" 逐场差分 → %s" % os.path.abspath(a.tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_mut.py — 表感知走查「到达代码区末尾」判据的敏感度扫描（ISSUE-20261008-04 M4 · 一审 B2）。

起因：报告 §1.2 曾断言「任何单个 op 字数改动都会让『走查到达末尾』从 412/412 崩到 0–2/412」，
该断言**过强**（一审实测 47 op × ±1 = 96 个变异中 65 个不崩）。本脚本把 96 个变异逐格跑出，
落盘为证据，并把「牙齿」限定到具体 op。

对每个 op、每个 Δ ∈ {+1, −1}（要求改动后总字数 ≥1）：
  复制正确 VM_WORDS → 改该 op 的字数 → 对 412 个 `.sob` 走查 → 记 endok（完整走到代码区末尾的文件数）。
另记该 op 的正确计数（0 次者为平凡变异）。

用法：
  python -X utf8 xm4_mut.py --all "<SCRIPT>" --tsv <dir>
"""
import os
import sys
import collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402
import xops  # noqa: E402


def endok(files):
    ok = tot = 0
    for p in files:
        try:
            sob = Sob0(p)
        except Exception:
            continue
        tot += 1
        items = xops.decode_items(sob.cells)
        last = items[-1][0] if items else 0
        if last * 4 + 4 >= sob.ss:
            ok += 1
    return ok, tot


def main():
    a = sys.argv[1:]
    root = a[a.index("--all") + 1]
    files = [os.path.join(root, f) for f in sorted(os.listdir(root))
             if f.lower().endswith(".sob")]
    tsvdir = a[a.index("--tsv") + 1] if "--tsv" in a else None

    base = dict(xops.VM_WORDS)
    ok0, tot = endok(files)
    print("== 正确表：endok = %d/%d ==" % (ok0, tot))

    # 正确计数（表感知，用于标注是否为「零次 op」的平凡变异）
    cnt = collections.Counter()
    for p in files:
        try:
            sob = Sob0(p)
        except Exception:
            continue
        cnt.update(xops.scan(sob)["cnt"])

    rows = []
    for op in range(0x2F):
        if op == 0x07:
            continue                      # 0x07 变长，字数不参与本表
        for d in (+1, -1):
            w = base[op] + d
            if w < 1:
                continue
            xops.VM_WORDS.clear()
            xops.VM_WORDS.update(base)
            xops.VM_WORDS[op] = w
            ok, _ = endok(files)
            rows.append((op, base[op], w, d, ok, tot, cnt.get(op, 0)))
    xops.VM_WORDS.clear()
    xops.VM_WORDS.update(base)
    okr, _ = endok(files)

    coll = [r for r in rows if r[4] <= 2]
    noncoll = [r for r in rows if r[4] > 2]
    trivial = [r for r in noncoll if r[6] == 0]
    weak = [r for r in noncoll if r[6] != 0]
    print("== 变异（47 op × ±1 = 96 个；op 0x07 除外）==")
    print("   崩到 ≤2/412 者：%d" % len(coll))
    print("   不崩（>2/412）者：%d  其中 零次 op 的平凡变异 %d、非零次 op 的弱变异 %d"
          % (len(noncoll), len(trivial), len(weak)))
    print("   复原后 endok = %d/%d" % (okr, tot))
    print("\n   -- 弱变异（该 op 全库非 0 次，但 ±1 不崩）--")
    for op, w0, w1, d, ok, t, n in sorted(weak, key=lambda r: r[4]):
        print("     op0x%02X %d->%d : endok=%d/%d（该 op 计数=%d）" % (op, w0, w1, ok, t, n))
    print("\n   -- 崩到 ≤2/412 的变异 --")
    for op, w0, w1, d, ok, t, n in sorted(coll, key=lambda r: r[0]):
        print("     op0x%02X %d->%d : endok=%d/%d（该 op 计数=%d）" % (op, w0, w1, ok, t, n))

    if tsvdir:
        os.makedirs(tsvdir, exist_ok=True)
        with open(os.path.join(tsvdir, "mut_sweep.tsv"), "w", encoding="utf-8", newline="") as f:
            f.write("op\thex\twords_correct\twords_mutated\tdelta\tendok\ttotal\top_count\tclass\n")
            for op, w0, w1, d, ok, t, n in sorted(rows):
                cls = "collapse" if ok <= 2 else ("trivial" if n == 0 else "weak")
                f.write("%d\t0x%02X\t%d\t%d\t%+d\t%d\t%d\t%d\t%s\n"
                        % (op, op, w0, w1, d, ok, t, n, cls))


if __name__ == "__main__":
    main()

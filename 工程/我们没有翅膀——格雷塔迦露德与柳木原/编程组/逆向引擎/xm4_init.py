#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_init.py — `sob_init.dat`（模块登记表）逐条解析 + `attr` 语义核验（ISSUE-20261008-04 M4）。

布局（`SOB0解码\软表解出_说明.md` §六，本脚本复核）：
  u16 count | count × [u8 L][name(L 字节，含尾 NUL)][u32 attr]

本脚本：① 复核「游标恰好到文件尾」；② 列 attr 低 16 位 / 高 16 位分布；
③ 单列 high16∉{0,1} 的条目（旧述 24 条 high16∈{2,3} 未定）；
④ 跨作品对照（`--alt` 第二份 sob_init.dat）。

用法：
  python -X utf8 xm4_init.py --file <sob_init.dat> [--alt <另一个>]
"""
import collections
import os
import struct
import sys


def parse(path):
    d = open(path, "rb").read()
    cnt = struct.unpack_from("<H", d, 0)[0]
    p = 2
    rows = []
    for _ in range(cnt):
        L = d[p]
        p += 1
        name = d[p:p + L]
        p += L
        attr = struct.unpack_from("<I", d, p)[0]
        p += 4
        rows.append((name.rstrip(b"\x00"), attr, L))
    return d, cnt, rows, p


def report(tag, path):
    d, cnt, rows, end = parse(path)
    print("== %s  (%s) ==" % (tag, os.path.basename(path)))
    print("  size=%d  count(u16)=%d  解析后游标=%d  余=%d  恰好到文件尾=%s"
          % (len(d), cnt, end, len(d) - end, end == len(d)))
    lo = collections.Counter(r[1] & 0xFFFF for r in rows)
    hi = collections.Counter(r[1] >> 16 for r in rows)
    print("  attr low16 分布（top10）: %s" % lo.most_common(10))
    print("  attr high16 分布: %s" % dict(hi))
    odd = [(n.decode("cp932", "replace"), hex(a), a & 0xFFFF, a >> 16, L)
           for (n, a, L) in rows if (a >> 16) not in (0, 1)]
    print("  high16 ∉ {0,1} 的条目（%d 条）:" % len(odd))
    for r in odd:
        print("     %-12s attr=%s low16=%d high16=%d L=%d" % r)
    # attr 低 16 位分布全表（前 30 个不同值）
    print("  low16 不同值数=%d  值域=[%d,%d]"
          % (len(lo), min(lo), max(lo)))
    # 非零 high16 的完整列表（含 1？）
    print("  high16 非 0 的条目数=%d（含 1）" % sum(1 for r in rows if r[1] >> 16))
    return rows


def main():
    a = sys.argv[1:]
    p1 = a[a.index("--file") + 1] if "--file" in a else \
        r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀 前奏诗\解包\SCRIPT\sob_init.dat"
    rows = report("主", p1)
    if "--alt" in a:
        p2 = a[a.index("--alt") + 1]
        rows2 = report("对照", p2)
        m1 = {n: a_ for (n, a_, _) in rows}
        m2 = {n: a_ for (n, a_, _) in rows2}
        common = set(m1) & set(m2)
        print("  两件共有模块名 %d 个；attr 相同 %d 个；不同 %d 个"
              % (len(common), sum(1 for n in common if m1[n] == m2[n]),
                 sum(1 for n in common if m1[n] != m2[n])))
        diff = [(n, hex(m1[n]), hex(m2[n])) for n in sorted(common) if m1[n] != m2[n]]
        print("  不同项（前 20）: %s" % diff[:20])
        print("  仅主件有: %s" % sorted(set(m1) - set(m2))[:12])
        print("  仅对照有: %s" % sorted(set(m2) - set(m1))[:12])


if __name__ == "__main__":
    main()

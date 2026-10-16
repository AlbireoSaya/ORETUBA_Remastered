#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""xm4_exc.py — 13 个系统脚本「引用站点精确二分」例外：逐文件定位（ISSUE-20261008-04 M4）。

背景（`SOB0解码\软表解出_说明.md` §二 / `_probe_soft_tables.py` 恒等式 4）：
  「页引用站点 = keys(maps[0]) ∪ keys(maps[4])，两键集不相交」在全库成立，
  **已知例外 13 个系统脚本**（config1 config2 eyecatch func_lib gallery history logo
  movieplay saveload scskip ssskip title title2）——旧产物只登记了原因，**未逐文件定位**。

本脚本给出的**可复跑定位判据**（与 `M4\C类元数据与计数_说明.md` §三 同口径）：

  P = { 代码区 cell 下标 i*4 : cells[i] >> 20 ∈ {0x017,0x018} }        （页引用字站点）
  U = keys(maps[0]) ∪ keys(maps[4])                                      （全部登记键）
  恒等式：U == P
  例外：  U \ P == { k ∈ U : k >= ss }         （ss = 代码区字节长）

即：例外文件里有若干**登记键的偏移落在「串半段」（k ≥ ss）**——它们不是代码站点，
装载期仍被 maps[0]/maps[4] 改写为指针,是模块缓冲串半段内的一片（零填充）数据表。
`P \ U`（**未被登记的页引用字**）在全库恒为 0 —— 故「例外 = 代码区混有页引用字形的数据数组」**不成立**。

本脚本**不做任何 4 对齐过滤**（例外项恰多为非 4 对齐键）；`--tsv` 落盘 `sys_exc_13.tsv`。

用法：
  python -X utf8 xm4_exc.py --all "<SCRIPT>" [--tsv <dir>]
  python -X utf8 xm4_exc.py --file "<SCRIPT>/saveload.sob"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402

SYSEXC = ("config1", "config2", "eyecatch", "func_lib", "gallery", "history",
          "logo", "movieplay", "saveload", "scskip", "ssskip", "title", "title2")


def analyse(sob):
    c = sob.cells
    P = set(i * 4 for i in range(len(c)) if (c[i] >> 20) in (0x017, 0x018))
    K = set(sob.maps[0]) | set(sob.maps[4])
    UP = K - P
    PU = P - K
    ge = set(k for k in K if k >= sob.ss)
    na = set(k for k in K if k % 4)
    return P, K, UP, PU, ge, na


def ranges(keys):
    out = []
    for k in sorted(keys):
        if out and k - out[-1][1] <= 8:
            out[-1][1] = k
        else:
            out.append([k, k])
    return out


def main():
    a = sys.argv[1:]
    files = []
    if "--file" in a:
        files = [a[a.index("--file") + 1]]
    elif "--all" in a:
        root = a[a.index("--all") + 1]
        files = [os.path.join(root, f) for f in sorted(os.listdir(root))
                 if f.lower().endswith(".sob")]
    tsvdir = a[a.index("--tsv") + 1] if "--tsv" in a else None

    print("%-16s %8s %8s %7s %7s %7s %10s %10s"
          % ("file", "ss", "|U|", "|U\\P|", "|P\\U|", "K>=ss", "U\\P==K>=ss", "在13名单"))
    n_hit = 0
    tot_up = 0
    tot_pu = 0
    rows = []
    for p in files:
        try:
            sob = Sob0(p)
        except Exception:
            continue
        P, K, UP, PU, ge, na = analyse(sob)
        stem = os.path.basename(p)[:-4]
        inlist = stem in SYSEXC
        if UP or PU:
            if inlist:
                n_hit += 1
            tot_up += len(UP)
            tot_pu += len(PU)
            print("%-16s %8d %8d %7d %7d %7d %10s %10s"
                  % (os.path.basename(p), sob.ss, len(K), len(UP), len(PU), len(ge),
                     str(UP == ge), str(inlist)))
            rows.append((os.path.basename(p), sob.ss, len(UP), len(ge), len(na),
                         UP == ge, ";".join("0x%X-0x%X" % (x, y) for x, y in ranges(ge))))
    print("\n== 汇总 ==")
    print("  恒等式不成立的文件 = %d（13 名单中 %d 个；另 %d 个非名单文件也违反）"
          % (len(rows), n_hit, len(rows) - n_hit))
    print("  |U\\P| 合计 = %d" % tot_up)
    print("  判据 `U\\P == {k∈U : k≥ss}` 成立的文件 = %d/%d"
          % (sum(1 for r in rows if r[5]), len(rows)))
    print("  `P\\U`（未登记页引用字）合计 = %d  ⇒ '例外=代码区页引用字数据数组' 不成立"
          % tot_pu)

    if tsvdir:
        os.makedirs(tsvdir, exist_ok=True)
        with open(os.path.join(tsvdir, "sys_exc_13.tsv"), "w", encoding="utf-8", newline="") as f:
            f.write("file\tss\tU_minus_P\tkeys_ge_ss\tnonaligned\tU_minus_P_eq_keys_ge_ss\tkey_ranges_ge_ss\n")
            for r in rows:
                f.write("%s\t%d\t%d\t%d\t%d\t%s\t%s\n" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
        print("  [TSV] 已写 %s" % os.path.join(tsvdir, "sys_exc_13.tsv"))


if __name__ == "__main__":
    main()

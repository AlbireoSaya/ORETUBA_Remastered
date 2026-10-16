#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_rule.py — 遮罩 Rule「数值 → RULE### 编号」换算的可判据核验（ISSUE-20261008-04 M4）。

两条互斥假设：
  H1：`:Rule = N` → `RULE%03d` 的 `{N}`（N 直接就是编号）
  H2：`:Rule = N` → `RULE%03d` 的 `{N-1}`（0 保留给内建 "Simple"，1 = RULE000）

判据（可失败）：
  ① 件集合边界：PC 侧遮罩件 `素材提取/UI/rule%03d.png` 与 PSV 侧 `ETC.cpk` 的 `RULE%03d.PNG`
     的实际编号范围（本脚本只读 PC 侧目录与 PSV 清单 txt，不解 cpk）。
  ② 取值边界：PSV 金标 `时间线.tsv` 的 `rule` 列最大值 Nmax。
     · 若 Nmax == 最大件号（=110） ⇒ H1 在边界上要求存在 RULE110/或 Nmax 直接命中；H2 要求 Nmax-1 命中。
     · 若 Nmax == 最大件号 + 1 ⇒ H1 要求存在 **RULE{Nmax}**（超出件集合 ⇒ 伪）；H2 落到最大件号（真）。

用法：
  python -X utf8 xm4_rule.py \
     --pc-ui "<...>/工程/我们没有翅膀/素材提取/UI" \
     --psv-list "<...>/工程/我们没有翅膀PSV/工具/美咲线过程脚本/_cpklist/ETC.cpk.txt" \
     --timeline "<...>/PSV演出/时间线.tsv"
"""
import collections
import csv
import os
import re
import sys


def main():
    a = sys.argv[1:]
    pc = a[a.index("--pc-ui") + 1]
    ps = a[a.index("--psv-list") + 1]
    tl = a[a.index("--timeline") + 1]

    pcn = sorted(int(m.group(1)) for m in
                 (re.match(r"rule(\d+)\.png$", f, re.I) for f in os.listdir(pc)) if m)
    print("== PC 侧遮罩件（%s）==" % os.path.basename(pc))
    print("   件数=%d  编号范围=[%d,%d]" % (len(pcn), pcn[0], pcn[-1]))

    psn = sorted(int(m.group(1)) for m in
                 (re.match(r"RULE(\d+)\.PNG$", l.strip(), re.I) for l in open(ps, encoding="utf-8", errors="replace")) if m)
    print("== PSV ETC.cpk 清单（%s）==" % os.path.basename(ps))
    print("   件数=%d  编号范围=[%d,%d]" % (len(psn), psn[0], psn[-1]))

    vals = collections.Counter()
    with open(tl, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            v = (row.get("rule") or "").strip()
            if v == "":
                continue
            try:
                vals[int(v)] += 1
            except ValueError:
                pass
    ks = sorted(vals)
    print("== PSV 金标时间线 rule 列 ==")
    print("   非空行=%d  不同值=%d  值域=[%d,%d]" % (sum(vals.values()), len(ks), ks[0], ks[-1]))
    print("   0 次数=%d ; 1 次数=%d ; %d 次数=%d ; %d 次数=%d"
          % (vals.get(0, 0), vals.get(1, 0), ks[-1], vals.get(ks[-1], 0),
             ks[-1] - 1, vals.get(ks[-1] - 1, 0)))
    pcmax, psmax, nmax = pcn[-1], psn[-1], ks[-1]
    print("\n== 判定 ==")
    print("   PC 最大件号=%d ; PSV 最大件号=%d ; 金标 rule 最大值 Nmax=%d" % (pcmax, psmax, nmax))
    print("   H1（N→RULE{N}）需存在 RULE%03d ⇒ %s" % (nmax, "存在" if nmax <= psmax else "**不存在 ⇒ H1 伪**"))
    print("   H2（N→RULE{N-1}）落到 RULE%03d ⇒ %s" % (nmax - 1, "存在" if nmax - 1 <= psmax else "不存在"))
    print("   件数关系：PC=%d / PSV=%d ；H2 覆盖 0..%d（0 为内建 Simple）" % (len(pcn), len(psn), psmax))


if __name__ == "__main__":
    main()

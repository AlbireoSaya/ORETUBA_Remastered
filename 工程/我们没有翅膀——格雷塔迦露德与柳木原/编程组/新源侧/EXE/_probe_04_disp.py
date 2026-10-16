#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_04_disp.py — 扫描 .text 中引用给定结构偏移 (disp) 的指令 (只读).

用法: python -X utf8 _probe_04_disp.py 0x1af8 0x1af4 0x1900 ...
口径: 线性 SkipData 反汇编 .text, 命中条件 = op_str 含 `+ 0x<disp>` 或 `[0x<abs va>]`.
      abs VA 形式另按: 若 disp 落在数据区且是全局, 直接给 `--abs 0x503xxx`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns

pe = PE()
t0, t1 = pe.sec_range(".text")

disps = []
for a in sys.argv[1:]:
    if a.startswith("abs:"):
        disps.append(("abs", int(a[4:], 0)))
    else:
        disps.append(("disp", int(a, 0)))

pats = []
for kind, v in disps:
    if kind == "disp":
        pats.append((kind, v, re.compile(r"\+\s*0x%x\b" % v)))
    else:
        pats.append((kind, v, re.compile(r"\[\s*0x%x\b" % v)))

hits = 0
for ins in iter_insns(pe, t0, t1):
    for kind, v, pat in pats:
        if pat.search(ins.op_str):
            print("0x%08X  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
            hits += 1
            break
print("-- hits=%d" % hits)

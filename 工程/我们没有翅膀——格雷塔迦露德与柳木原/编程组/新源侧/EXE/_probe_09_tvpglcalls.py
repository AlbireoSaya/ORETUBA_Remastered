#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_09_tvpglcalls.py — 统计 .text 中对 tvpgl 库函数全局槽的调用 (只读).

tvpgl 库结构体的函数指针在装载器 0x4654C0 内被复制到一批全局槽 (0x503900..0x503D00);
本探针列出每个槽的 call 站点, 用于定位画面 blit/合成路径.

用法: python -X utf8 _probe_09_tvpglcalls.py [lo] [hi]   (默认 0x503900 0x503D00)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns

pe = PE()
t0, t1 = pe.sec_range(".text")
lo = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x503900
hi = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x503D00

pat = re.compile(r"\[0x([0-9a-fA-F]+)\]")
counts = {}
sites = {}
for ins in iter_insns(pe, t0, t1):
    for m in pat.finditer(ins.op_str):
        v = int(m.group(1), 16)
        if lo <= v < hi:
            counts[v] = counts.get(v, 0) + 1
            sites.setdefault(v, []).append((ins.address, ins.mnemonic))

print("== refs to [0x%X,0x%X) ==" % (lo, hi))
for v in sorted(counts):
    lst = sites[v]
    calls = [a for a, mn in lst if mn == "call"]
    print("0x%08X  total=%3d  call=%3d" % (v, counts[v], len(calls)))
    if calls:
        print("     calls:", " ".join("0x%X" % a for a in calls[:30]),
              ("..." if len(calls) > 30 else ""))

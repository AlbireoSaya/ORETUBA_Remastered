#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_11_callgraph.py — 列出调用"落在给定 VA 区间内"的 .text 指令 (只读).

用法: python -X utf8 _probe_11_callgraph.py 0x495600 0x495E00
      python -X utf8 _probe_11_callgraph.py --callers 0x4956C0
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns

pe = PE()
t0, t1 = pe.sec_range(".text")

if "--callers" in sys.argv:
    tgt = int(sys.argv[sys.argv.index("--callers") + 1], 0)
    for ins in iter_insns(pe, t0, t1):
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            try:
                d = int(ins.op_str, 16)
            except ValueError:
                continue
            if d == tgt:
                print("0x%08X  %s 0x%08X" % (ins.address, ins.mnemonic, d))
else:
    lo = int(sys.argv[1], 0)
    hi = int(sys.argv[2], 0)
    for ins in iter_insns(pe, t0, t1):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            try:
                d = int(ins.op_str, 16)
            except ValueError:
                continue
            if lo <= d < hi:
                print("0x%08X  call 0x%08X" % (ins.address, d))

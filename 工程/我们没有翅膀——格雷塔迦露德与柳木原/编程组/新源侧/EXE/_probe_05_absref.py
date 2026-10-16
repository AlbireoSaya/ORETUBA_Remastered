#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_05_absref.py — 找出引用给定绝对 VA (全局变量/字符串) 的 .text 指令 (只读).

用法: python -X utf8 _probe_05_absref.py 0x503E18 0x503E14 ...
输出: 每条 VA 的命中指令 (含反汇编), 并给出所在"函数起点"近似 (向前找 nop 对齐块 + push ebp;mov ebp,esp).
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns, dis, md

pe = PE()
t0, t1 = pe.sec_range(".text")

targets = [int(a, 0) for a in sys.argv[1:]]

# build sorted list of instruction start addresses for function-start heuristic
starts = []
for ins in iter_insns(pe, t0, t1):
    starts.append(ins)


def instr_at(va):
    for i, ins in enumerate(starts):
        if ins.address == va:
            return i
    return None


def func_start(va):
    """向后找最近的一串 >=5 个 0x90 nop (MSVC 对齐填充) 之后的地址, 作为近似函数起点."""
    o = pe.off(va)
    # scan backwards byte-wise for 5+ consecutive nops
    p = o
    while p > pe.off(t0) + 8:
        p -= 1
        if pe.data[p] == 0x90:
            # count run
            q = p
            while q + 1 < o and pe.data[q + 1] == 0x90:
                q += 1
            if q - p + 1 >= 5:
                cand = q + 1
                if cand <= o:
                    return pe.image_base + pe.off_to_rva(cand)
            p = q
    return None


for t in targets:
    print("=" * 60)
    print("ABS 0x%08X  str=%r" % (t, pe.cstr(t, 48)))
    offs = pe.find_imm32(t)
    txt = [(o, r) for (o, r, s) in offs if s == ".text"]
    print("  总 imm32 命中=%d (.text=%d)" % (len(offs), len(txt)))
    for o, r in txt:
        va = pe.image_base + r
        i = instr_at(va)
        if i is None:
            print("   va=0x%08X  (非指令起点, 可能是操作数)" % va)
            continue
        ins = starts[i]
        print("   va=0x%08X  %-7s %s      [func~0x%08X]"
              % (va, ins.mnemonic, ins.op_str, func_start(va) or 0))

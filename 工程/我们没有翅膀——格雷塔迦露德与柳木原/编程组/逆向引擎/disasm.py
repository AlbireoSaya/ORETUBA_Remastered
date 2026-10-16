#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capstone 反汇编工具（x86 32-bit），基于 pe_min.PE 做 RVA<->文件偏移映射。

用法：
  python -X utf8 disasm.py --rva 0x24600 --len 0x300
  python -X utf8 disasm.py --off 0x24600 --len 0x300
  python -X utf8 disasm.py --find-funcs 0x23000 0x25000
  python -X utf8 disasm.py --xref 0x424600          # 找 call/jmp 到该 VA 的位置
"""
import re
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
# skipdata=True：遇无效字节不「停」，而是以 .byte 步进继续 —— 线性扫描必须如此，
# 否则会在第一张数据表处整体截断（旧版 skipdata=False 在 0x418EA1 停，只覆盖 .text 的 8.9%）。
md.skipdata = True


def disasm(pe, off, length, base_va=None):
    code = pe.data[off:off + length]
    rva = pe.off_to_rva(off)
    va = (pe.image_base + rva) if rva is not None else (base_va or 0)
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
    return out


def fmt(ins):
    b = " ".join("%02X" % x for x in ins.bytes)
    op = ins.op_str
    return "0x%08X  %-20s %-8s %s" % (ins.address, b, ins.mnemonic, op)


def cmd_funcs(pe, lo, hi):
    """在文件偏移 [lo,hi) 内找函数序言 push ebp; mov ebp,esp (55 8B EC) 或 55 89 E5。"""
    d = pe.data
    hits = []
    for i in range(lo, min(hi, len(d) - 3)):
        if d[i] == 0x55 and d[i + 1] in (0x8B, 0x89) and d[i + 2] == 0xEC:
            hits.append(i)
        elif d[i] == 0x55 and d[i + 1] == 0x89 and d[i + 2] == 0xE5:
            hits.append(i)
    return hits


def cmd_xref(pe, target_va):
    """扫 .text 找 call/jmp/直接引用 target_va 的指令（E8 rel32 / E9 rel32 / 立即数 32 位）。"""
    d = pe.data
    t = struct.pack("<I", target_va)
    hits = []
    # 立即数出现
    start = 0
    while True:
        p = d.find(t, start)
        if p < 0:
            break
        rva = pe.off_to_rva(p)
        hits.append(("imm32@off", p, rva, d[max(0, p - 8):p + 8].hex()))
        start = p + 1
    # E8/E9 相对位移
    for s in pe.sections:
        if s["name"] != ".text":
            continue
        a = s["rawptr"]
        b = min(len(d), a + s["rawsize"])
        i = a
        while i < b:
            opc = d[i]
            if opc in (0xE8, 0xE9) and i + 5 <= b:
                rel = struct.unpack_from("<i", d, i + 1)[0]
                va = pe.image_base + (i - a + s["vaddr"])
                if va + 5 + rel == target_va:
                    hits.append(("rel@off", i, i - a + s["vaddr"], d[i:i + 5].hex()))
            i += 1
    return hits


def main():
    pe = PE(DUMP_PATH)
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--rva":
        rva = int(args[1], 0)
        ln = int(args[3], 0) if len(args) > 3 else 0x300
        off = pe.rva_to_off(rva)
        for ins in disasm(pe, off, ln):
            print(fmt(ins))
    elif args[0] == "--off":
        off = int(args[1], 0)
        ln = int(args[3], 0) if len(args) > 3 else 0x300
        for ins in disasm(pe, off, ln):
            print(fmt(ins))
    elif args[0] == "--find-funcs":
        lo, hi = int(args[1], 0), int(args[2], 0)
        for off in cmd_funcs(pe, lo, hi):
            rva = pe.off_to_rva(off)
            print("func off=0x%06X rva=0x%06X va=0x%08X" % (off, rva, pe.image_base + rva))
    elif args[0] == "--xref":
        tva = int(args[1], 0)
        for kind, off, rva, hexs in cmd_xref(pe, tva):
            print("%-10s off=0x%06X rva=0x%06X va=0x%08X  bytes=%s"
                  % (kind, off, rva or 0, pe.image_base + (rva or 0), hexs))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全 .text 覆盖分析（R1 修复件）。

- 覆盖口径：**线性扫描 skipdata=True**（遇无效字节以 .byte 步进，不停；旧版 skipdata=False
  会在 0x418EA1 撞数据表即整体停摆，只覆盖 8.9%）。
- 字段枚举：**整节字节模式匹配 + 就地反汇编验证**，与反汇编器「在哪停」无关，无截断。
  口径与 fieldscan.py **完全同源**（同一 OPS、同一 disp32+disp8 规则）。

用法：
  python -X utf8 sweep.py                  # 覆盖计数 + 关键字段枚举
  python -X utf8 sweep.py --disp 0xD4,0xD8  # 指定字段
"""
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

# 与 fieldscan.py 保持逐字一致（同源口径）；**不含 0xFF**（见 fieldscan.py 头注 / T2）
OPS = {0x8B: "mov r,[m]", 0x89: "mov [m],r", 0x8D: "lea", 0x39: "cmp [m],r",
       0x3B: "cmp r,[m]", 0x01: "add [m],r", 0x03: "add r,[m]"}


def linear_count(code, va):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    n = 0
    for _ in md.disasm(code, va):
        n += 1
    return n


def scan(code, va0, disp):
    d32 = struct.pack("<I", disp)
    fits = -128 <= disp <= 127
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = False
    hits = []
    for i in range(len(code) - 6):
        if code[i] not in OPS:
            continue
        m = code[i + 1]
        if (m & 7) == 4:
            continue
        mod = m & 0xC0
        n = None
        if mod == 0x80 and code[i + 2:i + 6] == d32:
            n = 6
        elif mod == 0x40 and fits and code[i + 2] == disp:
            n = 3
        if n is None:
            continue
        ins = next(md.disasm(code[i:i + 16], va0 + i), None)
        if ins is None or len(ins.bytes) != n:
            continue
        if ("0x%x]" % disp) not in ins.op_str:
            continue
        hits.append((va0 + i, ins.mnemonic, ins.op_str))
    return hits


def main():
    pe = PE(DUMP_PATH)
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    print("== .text == vaddr=0x%X rawptr=0x%X rawsize=0x%X"
          % (s["vaddr"], s["rawptr"], s["rawsize"]))
    print("线性扫描(skipdata=True，不截断) 指令数 =", linear_count(code, va0))

    args = sys.argv[1:]
    targets = [0x38, 0x48, 0x58, 0xD4, 0xD8]
    if "--disp" in args:
        targets = [int(x, 0) for x in args[args.index("--disp") + 1].split(",")]
    print("\n== 整节字段枚举（disp32+disp8，含就地验证；口径与 fieldscan.py 同源）==")
    for disp in targets:
        hits = scan(code, va0, disp)
        print("[base+0x%X] %d 处" % (disp, len(hits)))
        for va, mn, ops in hits:
            print("   0x%08X  %-8s %s" % (va, mn, ops))


if __name__ == "__main__":
    main()

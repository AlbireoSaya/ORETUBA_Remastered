#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整节字节级「对象字段访问」扫描（R1/T2/T5 修复件）。

口径（**与 sweep.py 完全一致，同源**）：
  - 只扫**内存操作数** `mov/cmp/add/lea [base+disp]` 的常见 opcode：
    OPS = {8B mov r,[m], 89 mov [m],r, 8D lea, 39 cmp [m],r, 3B cmp r,[m],
           01 add [m],r, 03 add r,[m]}
  - **不含 `0xFF`**（`call/jmp/inc/dec [m]`）——纳入 0xFF 会把间接控制流混进来，
    使 [base+0xD4] 由 51 → 54、[base+0xD8] 由 62 → 65（T2：两工具曾因 OPS 差一个 0xFF 而「打架」）。
  - **同时匹配 disp32（mod=10）与 disp8（mod=01）**：旧版只匹配 disp32，
    对 `[reg+0x38]/[reg+0x48]/[reg+0x58]` 这类小偏移（汇编器用 disp8）**报 0 属工具盲区**（T5）。
  - 每个命中**就地反汇编验证**（capstone 解出的指令须整条覆盖该 disp 且落在该偏移）。

用法：python -X utf8 fieldscan.py [--disp 0xD4,0xD8]
"""
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

# 与 sweep.py 保持逐字一致（同源口径）
OPS = {0x8B: "mov r,[m]", 0x89: "mov [m],r", 0x8D: "lea", 0x39: "cmp [m],r",
       0x3B: "cmp r,[m]", 0x01: "add [m],r", 0x03: "add r,[m]"}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = False


def scan(code, va0, disp):
    """返回 [(va, mnemonic, op_str)]：整节扫描，disp32 与 disp8 两种编码。"""
    d32 = struct.pack("<I", disp)
    fits = -128 <= disp <= 127
    hits = []
    for i in range(len(code) - 6):
        if code[i] not in OPS:
            continue
        m = code[i + 1]
        if (m & 7) == 4:                              # rm=100 → SIB，跳过
            continue
        mod = m & 0xC0
        n = None
        if mod == 0x80 and code[i + 2:i + 6] == d32:  # disp32
            n = 6
        elif mod == 0x40 and fits and code[i + 2] == disp:   # disp8
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
    args = sys.argv[1:]
    targets = [0xD4, 0xD8]
    if "--disp" in args:
        targets = [int(x, 0) for x in args[args.index("--disp") + 1].split(",")]
    for disp in targets:
        hits = scan(code, va0, disp)
        print("== [base+0x%X] 命中 %d 处（整节 0x%X..0x%X，disp32+disp8，无截断）=="
              % (disp, len(hits), va0, va0 + len(code)))
        for va, mn, ops in hits:
            print("   0x%08X  %-8s %s" % (va, mn, ops))
        print()


if __name__ == "__main__":
    main()

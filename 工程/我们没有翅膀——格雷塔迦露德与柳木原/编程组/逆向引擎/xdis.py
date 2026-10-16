#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xdis.py — 逆向引擎辅助：VA 反汇编 / 调用图 / 立即数引用 / 字符串。

口径（写清，避免 R1 类失误）：
  * 目标 exe 默认 ORE_TUBA.EXE（只读，D 盘）；可用 --exe 指定（如 OT_PREDE.EXE 交叉验证）。
  * .text 内 RVA == 文件偏移（因 .text vaddr==rawptr==0x1000）；其余节走 pe_min.rva_to_off。
  * **全节线性反汇编一律 skipdata=True**（不截断）。
  * 传参一律用 **VA**（含 image base 0x400000），与本项目文档一致；也接受 rva: 前缀。

用法：
  python -X utf8 xdis.py --exe ORE   --va 0x424460 --len 0x300
  python -X utf8 xdis.py --exe ORE   --fn 0x424460           # 自动到 ret / 下一个 nop 块
  python -X utf8 xdis.py --exe ORE   --xref 0x424460          # 谁 call/jmp/imm 引用该 VA
  python -X utf8 xdis.py --exe ORE   --str 0x4FC318           # 读 C 串
  python -X utf8 xdis.py --exe ORE   --callers 0x422730       # E8 直接调用者
"""
import struct
import sys

import capstone

from pe_min import PE

EXES = {
    "ORE":  r"D:\Gal\[Navel]我们没有翅膀\ORE_TUBA.EXE",
    "PREDE": r"D:\Gal\壌偨偪偵梼偼側偄乣Prelude乣\OT_PREDE.EXE",
}

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def va_of(pe, va_arg):
    if isinstance(va_arg, str) and va_arg.startswith("rva:"):
        return pe.image_base + int(va_arg[4:], 0)
    return int(va_arg, 0)


def text_sec(pe):
    return [s for s in pe.sections if s["name"] == ".text"][0]


def fmt(ins):
    b = " ".join("%02X" % x for x in ins.bytes)
    return "0x%08X  %-22s %-8s %s" % (ins.address, b, ins.mnemonic, ins.op_str)


def disasm_va(pe, va, length):
    off = pe.rva_to_off(va - pe.image_base)
    if off is None:
        print("!! VA 0x%X 不在任何节" % va)
        return []
    return list(md.disasm(pe.data[off:off + length], va))


def fn_disasm(pe, va, limit=0x4000):
    """从 va 线性反汇编，直到 ret/ret imm（含）后遇到对齐 nop 块，或超 limit。"""
    out = []
    n = 0
    for ins in disasm_va(pe, va, limit):
        out.append(ins)
        n += 1
        if ins.mnemonic in ("ret", "retf") or (ins.mnemonic == "ret" and ins.op_str):
            # 允许 ret imm16
            return out
        if ins.mnemonic == "int3":
            return out
    return out


def all_insns(pe):
    s = text_sec(pe)
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    return list(md.disasm(code, pe.image_base + s["vaddr"]))


def callers(pe, target_va):
    """E8/E9 rel32 直接指向 target 的指令。"""
    s = text_sec(pe)
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    out = []
    i = 0
    while i + 5 <= len(code):
        if code[i] in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", code, i + 1)[0]
            if va0 + i + 5 + rel == target_va:
                out.append((va0 + i, "call" if code[i] == 0xE8 else "jmp"))
        i += 1
    return out


def xref(pe, target_va):
    """立即数 32 位出现 + E8/E9。"""
    out = []
    t = struct.pack("<I", target_va)
    p = 0
    while True:
        p = pe.data.find(t, p)
        if p < 0:
            break
        rva = pe.off_to_rva(p)
        sec = pe.section_of_off(p)
        out.append(("imm32", p, rva, sec["name"] if sec else "?"))
        p += 1
    for va, kind in callers(pe, target_va):
        out.append((kind, pe.rva_to_off(va - pe.image_base), va - pe.image_base, ".text"))
    return out


def cstr(pe, va, n=128):
    off = pe.rva_to_off(va - pe.image_base)
    if off is None:
        return None
    e = pe.data.find(b"\x00", off, off + n)
    return pe.data[off:e if e >= 0 else off + n]


def main():
    a = sys.argv[1:]
    exe = "ORE"
    if "--exe" in a:
        exe = a[a.index("--exe") + 1]
    pe = PE(EXES[exe])
    print("== exe=%s  imagebase=0x%X  size=%d ==" % (exe, pe.image_base, len(pe.data)))
    if "--va" in a:
        va = va_of(pe, a[a.index("--va") + 1])
        ln = int(a[a.index("--len") + 1], 0) if "--len" in a else 0x300
        for ins in disasm_va(pe, va, ln):
            print(fmt(ins))
    elif "--fn" in a:
        va = va_of(pe, a[a.index("--fn") + 1])
        for ins in fn_disasm(pe, va):
            print(fmt(ins))
    elif "--callers" in a:
        t = va_of(pe, a[a.index("--callers") + 1])
        for va, kind in callers(pe, t):
            print("  %-5s 0x%08X" % (kind, va))
    elif "--xref" in a:
        t = va_of(pe, a[a.index("--xref") + 1])
        for kind, off, rva, sec in xref(pe, t):
            print("  %-6s off=0x%06X rva=0x%06X va=0x%08X sec=%s"
                  % (kind, off or 0, rva or 0, pe.image_base + (rva or 0), sec))
    elif "--str" in a:
        va = va_of(pe, a[a.index("--str") + 1])
        print(repr(cstr(pe, va)))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

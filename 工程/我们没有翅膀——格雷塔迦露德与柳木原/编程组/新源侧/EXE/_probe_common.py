#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_common.py — ISSUE-20261008-09 / EXE 模块共用只读探针基座.

纪律:
  * 只读. 目标为模块目录内的副本 work/ORE_TUBA.EXE (由 D 盘原版拷贝, md5 7431b954...).
  * 不写任何文件 (除 stdout).
  * 全部 VA 带 image base 0x400000.
"""
import os
import struct

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(HERE, "work", "ORE_TUBA.EXE")
IMGBASE = 0x400000

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


class PE:
    def __init__(self, path=EXE_PATH):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        assert d[:2] == b"MZ"
        e = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[e:e + 4] == b"PE\0\0"
        coff = e + 4
        (self.machine, self.nsections, self.timestamp, self.ptr_symtab,
         self.nsyms, self.size_opt, self.characteristics) = struct.unpack_from("<HHIIIHH", d, coff)
        opt = coff + 20
        self.entry_rva = struct.unpack_from("<I", d, opt + 16)[0]
        self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        self.size_headers = struct.unpack_from("<I", d, opt + 60)[0]
        nd = min(struct.unpack_from("<I", d, opt + 92)[0], 16)
        self.ddir_off = opt + 96
        self.ddirs = [struct.unpack_from("<II", d, self.ddir_off + 8 * i) for i in range(nd)]
        sec_off = opt + self.size_opt
        self.sections = []
        for i in range(self.nsections):
            o = sec_off + 40 * i
            name = d[o:o + 8].rstrip(b"\0").decode("latin1")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append(dict(name=name, vsize=vsize, vaddr=vaddr,
                                      rawsize=rawsize, rawptr=rawptr))

    def rva_to_off(self, rva):
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                delta = rva - s["vaddr"]
                if delta < s["rawsize"]:
                    return s["rawptr"] + delta
                return None
        if rva < self.size_headers:
            return rva
        return None

    def off_to_rva(self, off):
        for s in self.sections:
            if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
                return s["vaddr"] + (off - s["rawptr"])
        if off < self.size_headers:
            return off
        return None

    def off(self, va):
        return self.rva_to_off(va - self.image_base)

    def section_of_va(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def read_va(self, va, n):
        o = self.off(va)
        if o is None:
            return None
        return self.data[o:o + n]

    def u32(self, va):
        b = self.read_va(va, 4)
        return struct.unpack("<I", b)[0] if b else None

    def cstr(self, va, n=200):
        o = self.off(va)
        if o is None:
            return None
        e = self.data.find(b"\x00", o, o + n)
        return self.data[o:e if e >= 0 else o + n]

    def find_imm32(self, va):
        t = struct.pack("<I", va)
        out = []
        p = 0
        while True:
            p = self.data.find(t, p)
            if p < 0:
                break
            sec = None
            for s in self.sections:
                if s["rawptr"] <= p < s["rawptr"] + s["rawsize"]:
                    sec = s
            out.append((p, self.off_to_rva(p), sec["name"] if sec else "?"))
            p += 1
        return out

    def sec_by_name(self, nm):
        for s in self.sections:
            if s["name"] == nm:
                return s
        return None

    def sec_range(self, nm):
        s = self.sec_by_name(nm)
        if not s:
            return (None, None)
        return (self.image_base + s["vaddr"], self.image_base + s["vaddr"] + s["rawsize"])


def dis(pe, va, length=0x200):
    o = pe.off(va)
    if o is None:
        print("!! VA 0x%X outside sections" % va)
        return []
    return list(md.disasm(pe.data[o:o + length], va))


def fmt(ins):
    return "0x%08X  %-20s %-7s %s" % (ins.address,
                                      " ".join("%02X" % x for x in ins.bytes),
                                      ins.mnemonic, ins.op_str)


def show(pe, va, length=0x120, title=None):
    if title:
        print("---- %s ----" % title)
    for i in dis(pe, va, length):
        print(fmt(i))


def callers(pe, target, span=None):
    """E8/E9 rel32 -> target."""
    s = pe.sections[0] if span is None else span
    va0 = pe.image_base + s["vaddr"]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    out = []
    i = 0
    while i + 5 <= len(code):
        if code[i] in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", code, i + 1)[0]
            if va0 + i + 5 + rel == target:
                out.append((va0 + i, "call" if code[i] == 0xE8 else "jmp"))
        i += 1
    return out


def text_va_range(pe):
    return pe.sec_range(".text")


def iter_insns(pe, start_va, end_va):
    o = pe.off(start_va)
    if o is None:
        return
    n = (end_va - start_va)
    for ins in md.disasm(pe.data[o:o + n], start_va):
        yield ins

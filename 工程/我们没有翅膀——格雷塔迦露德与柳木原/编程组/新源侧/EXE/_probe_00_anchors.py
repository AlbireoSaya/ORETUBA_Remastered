#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_00_anchors.py — 复核任务给出的锚点 (只读).

任务锚点:
  tvpgl.dll 串 0x4FC070 <- 引用 0x4135C8
  %sDS_SPRITE.DLL 串 0x4FC060 <- 0x413656
  ddraw.dll 串 0x4FF350 <- 0x493919
  图形设备管理器起点 0x493900
"""
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from _probe_common import PE, show, fmt, dis

pe = PE()
print("== exe size=%d imagebase=0x%X entry_rva=0x%X ==" % (len(pe.data), pe.image_base, pe.entry_rva))

for va in (0x4FC070, 0x4FC060, 0x4FF350, 0x4FC318, 0x4FC32C, 0x4FC340, 0x4FC354, 0x4FC360):
    s = pe.cstr(va)
    print("str 0x%08X : %r" % (va, s))

print()
for ref_va, label in ((0x4135C8, "tvpgl ref"), (0x413656, "DS_SPRITE ref"), (0x493919, "ddraw ref")):
    print("======== %s @ 0x%08X ========" % (label, ref_va))
    show(pe, ref_va - 0x30, 0x70)

print()
print("======== immediate-32 xref of 0x4FC070 (tvpgl) ========")
for off, rva, sec in pe.find_imm32(0x4FC070):
    print("  off=0x%06X rva=0x%06X va=0x%08X sec=%s" % (off, rva, pe.image_base + rva, sec))

print("======== immediate-32 xref of 0x4FC060 (DS_SPRITE) ========")
for off, rva, sec in pe.find_imm32(0x4FC060):
    print("  off=0x%06X rva=0x%06X va=0x%08X sec=%s" % (off, rva, pe.image_base + rva, sec))

print("======== immediate-32 xref of 0x4FF350 (ddraw) ========")
for off, rva, sec in pe.find_imm32(0x4FF350):
    print("  off=0x%06X rva=0x%06X va=0x%08X sec=%s" % (off, rva, pe.image_base + rva, sec))

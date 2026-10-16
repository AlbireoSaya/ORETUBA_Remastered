#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_02_plugin_api.py — 找出所有 LoadLibraryA/GetProcAddress 调用点及其前后的名字串 (只读).

口径:
  * 扫描 .text 全节 SkipData 线性反汇编, 找 `call dword ptr [0x4ED118]` (LoadLibraryA)
    与 `call dword ptr [0x4ED11C]` (GetProcAddress).
  * 对每个调用点, 往回看最多 12 条指令, 收集 push imm32 且 imm 指向可读 C 串者.
  * 同时记录该调用点所在的"函数"起点 (向前找最近的 ret / nop 对齐块), 便于分组.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, iter_insns, dis, fmt

LOADLIB = 0x4ED118
GETPROC = 0x4ED11C

pe = PE()
t0, t1 = pe.sec_range(".text")
print("== .text VA 0x%08X .. 0x%08X ==" % (t0, t1))

# one linear pass, keeping small backlog
backlog = []
hits = []  # (va, kind, name_str)
for ins in iter_insns(pe, t0, t1):
    if ins.mnemonic == "call" and ins.op_str == "dword ptr [0x4ed118]":
        kind = "LoadLibrary"
    elif ins.mnemonic == "call" and ins.op_str == "dword ptr [0x4ed11c]":
        kind = "GetProcAddress"
    else:
        backlog.append(ins)
        if len(backlog) > 14:
            backlog.pop(0)
        continue
    # collect string pushes in backlog
    names = []
    for b in backlog:
        if b.mnemonic == "push" and b.op_str.startswith("0x"):
            try:
                imm = int(b.op_str, 16)
            except ValueError:
                continue
            s = pe.cstr(imm, 80)
            if s and len(s) >= 2 and all(32 <= c < 127 for c in s):
                names.append((b.address, s.decode("latin1")))
    hits.append((ins.address, kind, names))
    backlog = []

print("\n== %d plugin-loader calls ==" % len(hits))
for va, kind, names in hits:
    nm = " ; ".join("0x%X:%s" % (a, s) for a, s in names)
    print("0x%08X %-16s %s" % (va, kind, nm))

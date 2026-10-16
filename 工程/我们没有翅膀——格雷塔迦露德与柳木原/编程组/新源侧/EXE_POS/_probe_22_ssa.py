#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_22_ssa.py — func_lib/场景 .sob 的「操作数=暂存槽」数据流转储 (只读).

背景(VM handler 逐条反汇编所得, 本次实测):
  * 操作数一律是 **地址/值**(raw 操作数字). 算术与比较指令 **直接读该操作数槽里的值**;
    写指令把结果写到 **操作数所指地址**(maps[4] 条目的 value 即目标偏移).
  * 编译器把「后续指令的操作数槽」当**临时寄存器**: 前一条指令写进后一条的操作数槽,
    该槽在磁盘上是 0, 运行期被改写 ⇒ 打印时标注 `<-w<i>`(第 i 条指令写过它).

op 语义(实测):
  0x08 PUSH: 压入 op0(raw)          | 0x04 CALL: 压返回地址; pc=*op0
  0x0D..0x15 / 0x29..0x2E: *op2 = f(op0,op1)   (op0/op1 raw 值, op2 地址)
  0x1F MOV: *op1 = op0(raw)         | 0x20 MOVD: *op1 = *op0
  0x23 LDSP: *op1 = *(sp-op0)       | 0x28 LEASP: *op1 = sp-op0
  0x22 STSP: *(sp-op1) = op0(raw)   | 0x25 CPSP: *(sp-op1) = *(sp-op0)
  0x05 CALLN: *op2 = op0(op1)       | 0x03 STVAL: *op0 = RETVAL

用法:
  python -X utf8 _probe_22_ssa.py [--file <sob>] --range LO HI
默认 --file = func_lib.sob
"""
import os
import sys
import collections

# ⚠️ 旧开发位置（`子代理工作区\ISSUE-20261008-09\EXE\`）= **历史副本，勿用**；
#    本探针不入复跑链，未改常量（改后仍需 gitignored 输入 `work\*.EXE` 才能跑通 ⇒ 见说明.md §三末）。
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE")
from _probe_12_funclib import Sob, W
from _probe_17_scene_args import walk_linear

FUNCLIB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"

OPN = {0x00: "HALT", 0x01: "RET", 0x02: "RETV", 0x03: "STVAL", 0x04: "CALL", 0x05: "CALLN",
       0x06: "JMP", 0x07: "SWITCH", 0x08: "PUSH", 0x09: "PUSHD", 0x0A: "POP", 0x0B: "ADJSP",
       0x0C: "ADDSP", 0x0D: "ADD", 0x0E: "SUB", 0x0F: "MUL", 0x10: "DIV", 0x11: "MOD",
       0x12: "MODN", 0x13: "AND", 0x14: "OR", 0x15: "XOR", 0x16: "NOT", 0x17: "ISZERO",
       0x18: "SHR", 0x19: "SHL", 0x1A: "INC", 0x1B: "DEC", 0x1C: "INCSP", 0x1D: "DECSP",
       0x1E: "JZ", 0x1F: "MOV", 0x20: "MOVD", 0x21: "MOVI", 0x22: "STSP", 0x23: "LDSP",
       0x24: "STSPD", 0x25: "CPSP", 0x26: "LDSPSP", 0x27: "MOVDD", 0x28: "LEASP",
       0x29: "LT", 0x2A: "LE", 0x2B: "GT", 0x2C: "GE", 0x2D: "EQ", 0x2E: "NE"}

# 值操作数位 ('v') / 地址操作数位 ('a')
ROLE = {
    0x03: "a", 0x04: "a", 0x06: "a", 0x08: "v", 0x0A: "a", 0x0B: "v", 0x0C: "v",
    0x0D: "vva", 0x0E: "vva", 0x0F: "vva", 0x10: "vva", 0x11: "vva", 0x12: "vva",
    0x13: "vva", 0x14: "vva", 0x15: "vva", 0x16: "va", 0x17: "va",
    0x18: "vva", 0x19: "vva", 0x1A: "a", 0x1B: "a", 0x1C: "v", 0x1D: "v",
    0x1E: "va", 0x1F: "va", 0x20: "da", 0x21: "va", 0x22: "vv", 0x23: "va", 0x24: "av",
    0x25: "vv", 0x26: "va", 0x27: "da", 0x28: "va",
    0x29: "vva", 0x2A: "vva", 0x2B: "vva", 0x2C: "vva", 0x2D: "vva", 0x2E: "vva",
}
# 「目标」= 该 op 的第几个操作数是**地址**（写目标）
DEST_K = {
    0x03: 0, 0x05: 2, 0x0A: 0,
    0x0D: 2, 0x0E: 2, 0x0F: 2, 0x10: 2, 0x11: 2, 0x12: 2, 0x13: 2, 0x14: 2, 0x15: 2,
    0x16: 1, 0x17: 1, 0x18: 2, 0x19: 2,
    0x1F: 1, 0x20: 1, 0x21: 1, 0x23: 1, 0x26: 1, 0x27: 1, 0x28: 1,
    0x29: 2, 0x2A: 2, 0x2B: 2, 0x2C: 2, 0x2D: 2, 0x2E: 2,
}


def immascii(v):
    b = bytes([(v >> 0) & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF])
    s = b.rstrip(b"\0")
    if 1 <= len(s) <= 4 and all(32 <= c < 127 for c in s):
        return s.decode("ascii")
    return None


class Dec:
    def __init__(self, sob):
        self.sob = sob
        self.ins = list(walk_linear(sob))
        self.writer = {}

    def addr_id(self, i, k):
        """第 i 条指令第 k 个操作数所指的**地址 id**."""
        pos, op, w, ops = self.ins[i]
        hits = self.sob.site(pos + 4 * (k + 1))
        if hits:
            mi, mv = hits[0]
            if mi == 4:
                return ("OFF", mv)
            if mi == 0:
                return ("VAR", mv)
            if mi == 1:
                return ("NAT", mv)
            return ("M", mv)
        return ("ADDR", ops[k])

    def label(self, i, k):
        pos, op, w, ops = self.ins[i]
        raw = ops[k]
        site = pos + 4 * (k + 1)
        hits = self.sob.site(site)
        if hits:
            mi, mv = hits[0]
            if mi == 0:
                return "VAR#%d" % mv
            if mi == 1:
                return "NAT#%d" % mv
            if mi == 4:
                s = None
                if mv >= self.sob.ss:
                    o = self.sob.cbase + mv
                    e = self.sob.d.find(b"\0", o)
                    if 0 <= e - o <= 80:
                        s = self.sob.d[o:e].decode("latin1")
                return "@0x%X%s" % (mv, (" " + repr(s)) if s else "")
            return "map%d=%d" % (mi, mv)
        a = immascii(raw)
        tag = ""
        wno = self.writer.get(("OFF", site))
        if wno is not None:
            tag = "<-w%d" % wno
        return "%d%s%s" % (raw, (" '" + a + "'") if a else "", tag)


def main():
    a = sys.argv[1:]
    path = a[a.index("--file") + 1] if "--file" in a else FUNCLIB
    sob = Sob(path)
    lo = int(a[a.index("--range") + 1], 0) if "--range" in a else 0
    hi = int(a[a.index("--range") + 2], 0) if "--range" in a else 0x7FFFFFFF
    D = Dec(sob)
    lines = []
    for i, (pos, op, w, ops) in enumerate(D.ins):
        if pos < lo or pos >= hi:
            # 仍要登记 writer（前面指令对后续槽的写入）
            if op in DEST_K and DEST_K[op] < w:
                D.writer[D.addr_id(i, DEST_K[op])] = i
            continue
        if op == 0x07:
            lines.append("  0x%05X  SWITCH n=%d" % (pos, w))
        else:
            role = ROLE.get(op, "")
            parts = []
            for k in range(w):
                rk = role[k] if k < len(role) else " "
                parts.append("%s%s" % (rk + ":" if rk in "vad" else "", D.label(i, k)))
            lines.append("  0x%05X  %-7s %s" % (pos, OPN.get(op, "?"), " , ".join(parts)))
        if op in DEST_K and DEST_K[op] < w:
            D.writer[D.addr_id(i, DEST_K[op])] = i
    print("\n".join(lines))


if __name__ == "__main__":
    main()

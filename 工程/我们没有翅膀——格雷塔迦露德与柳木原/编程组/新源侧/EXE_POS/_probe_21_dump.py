#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_21_dump.py — func_lib.sob 的线性反汇编转储 + 立即数直方图 (只读).

口径: 复用 EXE 模块的 `_probe_12_funclib.Sob`(SOB 容器) 与 `_probe_17_scene_args.walk_linear`
      (表感知线性走查, op 0x07 整段跨过). 本探针只读, 不写文件.

用法:
  python -X utf8 _probe_21_dump.py --range 0x14084 0x14F98      # 线性转储一段
  python -X utf8 _probe_21_dump.py --immhist                    # 全库立即数直方图(位置候选)
  python -X utf8 _probe_21_dump.py --immval 640 944             # 找特定立即数出现站
"""
import os
import sys
import collections

# ⚠️ 旧开发位置（`子代理工作区\ISSUE-20261008-09\EXE\`）= **历史副本，勿用**；
#    本探针不入复跑链，未改常量（改后仍需 gitignored 输入 `work\*.EXE` 才能跑通 ⇒ 见说明.md §三末）。
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE")
from _probe_12_funclib import Sob, W
from _probe_17_scene_args import walk_linear, describe_push

FUNCLIB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"


def asciiz(v):
    b = bytes([(v >> 0) & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF])
    s = b.rstrip(b"\0")
    if 1 <= len(s) <= 4 and all(32 <= c < 127 for c in s):
        return s.decode("ascii")
    return None


def opname(op):
    return {
        0x00: "HALT", 0x01: "RET", 0x02: "RETV", 0x03: "STVAL", 0x04: "CALL",
        0x05: "CALLN", 0x06: "JMP", 0x07: "SWITCH", 0x08: "PUSH", 0x09: "PUSHD",
        0x0A: "POP", 0x0B: "ADJSP", 0x0C: "ADDSP", 0x0D: "ADD", 0x0E: "SUB",
        0x0F: "MUL", 0x10: "DIV", 0x11: "MOD", 0x12: "MODN", 0x13: "AND",
        0x14: "OR", 0x15: "XOR", 0x16: "NOT", 0x17: "ISZERO", 0x18: "SHR",
        0x19: "SHL", 0x1A: "INC", 0x1B: "DEC", 0x1C: "INCSP", 0x1D: "DECSP",
        0x1E: "JZ", 0x1F: "MOV", 0x20: "MOVD", 0x21: "MOVI", 0x22: "STSP",
        0x23: "LDSP", 0x24: "STSPD", 0x25: "CPSP", 0x26: "LDSPSP", 0x27: "MOVDD",
        0x28: "LEASP", 0x29: "LT", 0x2A: "LE", 0x2B: "GT", 0x2C: "GE",
        0x2D: "EQ", 0x2E: "NE",
    }.get(op, "?%02X" % op)


def desc(sob, site, raw):
    hits = sob.site(site)
    if not hits:
        a = asciiz(raw)
        return "imm %d%s" % (raw, (" '%s'" % a) if a else "")
    parts = []
    for mi, mv in hits:
        if mi == 0:
            parts.append("VAR#%d" % mv)
        elif mi == 1:
            parts.append("NAT#%d" % mv)
        elif mi == 3:
            parts.append("V=0x%X" % mv)
        elif mi == 4:
            s = None
            if mv >= sob.ss:
                o = sob.cbase + mv
                e = sob.d.find(b"\0", o)
                if 0 <= e - o <= 80:
                    s = sob.d[o:e].decode("latin1")
            parts.append("MOD=0x%X%s" % (mv, (" " + repr(s)) if s else ""))
        else:
            parts.append("map%d=%d" % (mi, mv))
    return " ".join(parts)


def main():
    a = sys.argv[1:]
    sob = Sob(FUNCLIB)
    if "--info" in a:
        print("ss=0x%X se=0x%X cbase=0x%X maps=%s" %
              (sob.ss, sob.se, sob.cbase, [len(m) for m in sob.maps]))

    if "--range" in a:
        lo = int(a[a.index("--range") + 1], 0)
        hi = int(a[a.index("--range") + 2], 0)
        for pos, op, w, ops in walk_linear(sob):
            if pos < lo:
                continue
            if pos >= hi:
                break
            if op == 0x07:
                print("  0x%05X  [switch table  n=%d]" % (pos, w))
                continue
            txt = []
            for k, o in enumerate(ops):
                txt.append(desc(sob, pos + 4 * (k + 1), o))
            print("  0x%05X  %-7s %s" % (pos, opname(op), " , ".join(txt)))

    if "--immhist" in a:
        lo = int(a[a.index("--immhist") + 1], 0) if len(a) > a.index("--immhist") + 1 and \
            a[a.index("--immhist") + 1].isdigit() else 0
        cnt = collections.Counter()
        where = collections.defaultdict(list)
        for pos, op, w, ops in walk_linear(sob):
            if op == 0x07:
                continue
            for k, o in enumerate(ops):
                site = pos + 4 * (k + 1)
                if sob.site(site):
                    continue
                if o == 0 or o == 0xFFFFFFFF:
                    continue
                if 0x10 <= o <= 0x2000:
                    cnt[o] += 1
                    where[o].append((pos, opname(op), k))
        print("-- imm histogram (0x10..0x2000), top 60 --")
        for v, n in cnt.most_common(60):
            print("   %5d (0x%X) x%-3d  %s" % (v, v, n,
                  " ".join("0x%X" % x[0] for x in where[v][:6])))

    if "--immval" in a:
        vals = set()
        for i, x in enumerate(a):
            if x == "--immval":
                for y in a[i + 1:]:
                    try:
                        vals.add(int(y, 0))
                    except ValueError:
                        break
        hit = collections.defaultdict(list)
        for pos, op, w, ops in walk_linear(sob):
            if op == 0x07:
                continue
            for k, o in enumerate(ops):
                site = pos + 4 * (k + 1)
                if sob.site(site):
                    continue
                if o in vals:
                    hit[o].append((pos, opname(op), k))
        for v in sorted(vals):
            print("imm %d (0x%X): %s" % (v, v,
                  " ".join("0x%X/%s" % (p, nm) for p, nm, k in hit[v][:20])))


if __name__ == "__main__":
    main()

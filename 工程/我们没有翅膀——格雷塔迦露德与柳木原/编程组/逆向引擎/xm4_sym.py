#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_sym.py — 具名符号（maps[2]）与管理器槽 [+0xE0]/[+0xE4]/[+0xE8] 的核验（ISSUE-20261008-04 M4）。

用法：
  # ① maps[2] 在全库的真实占用（旧述「恒空」）+ 3 个站点的定位
  python -X utf8 xm4_sym.py --maps2 "<SCRIPT>"
  # ② 具名符号注册（sub_4228F0 ×3）与名称串
  python -X utf8 xm4_sym.py --symtab
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402


def maps2(root):
    nonempty = []
    hits = []
    for fn in sorted(os.listdir(root)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            sob = Sob0(os.path.join(root, fn))
        except Exception:
            continue
        if sob.maps[2]:
            nonempty.append((os.path.basename(fn), len(sob.maps[2]),
                             {hex(k): hex(v) for k, v in sorted(sob.maps[2].items())}))
        # 走查所有操作数，看哪些落在 maps[2]（表感知需由 xops 提供）
        from xops import decode_items
        for (ci, op, ops) in decode_items(sob.cells):
            if op > 0x2E:
                break
            for p, oc in enumerate(ops):
                if oc * 4 in sob.maps[2]:
                    hits.append((os.path.basename(fn), ci, "0x%02X" % op, p,
                                 hex(sob.cells[oc]), hex(sob.maps[2][oc * 4])))
    print("== maps[2] 非空的文件 ==")
    for r in nonempty:
        print("   %-16s keys=%d  %s" % r)
    print("== 操作数落在 maps[2] 的站点（= 引用具名符号）==")
    for h in hits:
        print("   file=%-16s cell=%-6d op=%-4s pos=%d word=%s -> symbol_index=%s" % h)


def symtab():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pe_min import PE, DUMP_PATH
    pe = PE(DUMP_PATH)
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    calls = []
    for m in re.finditer(rb"\xe8(....)", code, re.S):
        o = m.start()
        rel = int.from_bytes(m.group(1), "little")
        if va0 + o + 5 + rel == 0x4228F0:
            calls.append(va0 + o)
    print("== sub_4228F0（具名符号注册器）调用点 ==")
    print("   %s（共 %d 处）" % ([hex(c) for c in calls], len(calls)))
    for pat in (b"retTgsExp", b"ScriptBootFlg", b"retAppProc"):
        for m in re.finditer(re.escape(pat), pe.data):
            print("   串 %-14r VA=0x%X" % (pat.decode(), pe.image_base + m.start()))


def main():
    a = sys.argv[1:]
    if "--maps2" in a:
        maps2(a[a.index("--maps2") + 1])
    elif "--symtab" in a:
        symtab()


if __name__ == "__main__":
    main()

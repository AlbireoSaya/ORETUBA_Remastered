#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_cand.py — M4 命名候选的**证据合并打印**（只读）。

对给定 handler 下标列表，打印：
  1. handler：VA / 语料引用数 / core(W=0x200) 与扩窗(W=0x1000) 关联 V / 结构特征；
  2. handler 反汇编（首 ~18 条，到 ret）；
  3. 每个 core V：func_lib 窗口内的**首个非空串**（窗口敏感度三档）+ 窗口内 native 序。

用法：python -X utf8 xm4_cand.py 668 669 428 433 729 719 4 40 23 5 65 242 197 209 227 228 229 705 727 432
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capstone                        # noqa: E402
import decode_sob0 as D                # noqa: E402
import xclus                          # noqa: E402
import xvlink                         # noqa: E402
from pe_min import PE, DUMP_PATH      # noqa: E402

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True


def first_string(fl, V, W):
    c, s4 = fl.cells, fl.maps[4]
    for j in range(0, W, 4):
        o = V + j
        if o + 4 > fl.ss:
            break
        if o in s4:
            t = s4[o]
            if fl.ss <= t < fl.se:
                try:
                    x = fl.read_group(t)[0].decode("cp932", "replace")
                except Exception:
                    x = ""
                if x:
                    return x
    return ""


def main():
    hs = [int(x, 0) for x in sys.argv[1:]]
    pe = PE(DUMP_PATH)
    full = xclus.handlers(pe)
    fl = D.Sob0(xvlink.FL_PATH)
    c1, cv, cvf = xvlink.corpus_counts(xvlink.SCRIPT)
    Vs = sorted(V for V in cv if V not in xvlink.SPECIAL_V)
    h2v, vinfo, vcalls = xvlink.build_direct(fl, Vs, 0x200)
    h2v_big = xvlink.build_direct(fl, Vs, 0x1000)[0]
    NM = {V: (d.get("name") or "") for V, d in D.V_NAMING.get("ot", {}).items()}

    for h in hs:
        va = full[h] if h < len(full) else 0
        print("=" * 78)
        print("h%-4d VA=0x%08X  corpus_refs=%d  core(W=0x200)V=%s  big(W=0x1000)V=%d" %
              (h, va, c1.get(h, 0),
               ",".join("0x%X" % V for V in sorted(h2v.get(h, {}))),
               len(h2v_big.get(h, {}))))
        off = pe.rva_to_off(va - pe.image_base)
        k = 0
        for ins in md.disasm(pe.data[off:off + 256], va):
            print("   0x%08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
            k += 1
            if k >= 18 or ins.mnemonic in ("ret", "retf"):
                break
        for V in sorted(h2v.get(h, {})):
            sv = [first_string(fl, V, w) for w in (0x120, 0x200, 0x400)]
            nat = xvlink.walk_win(fl, V, 0x200)[0]
            print("   V=0x%X name=%s nodes=%d 首串(0x120/0x200/0x400)=%s native=%s" %
                  (V, NM.get(V, "-") or "-", cv.get(V, 0),
                   [s for s in sv if s][:3], sorted(set(nat))[:12]))


if __name__ == "__main__":
    main()

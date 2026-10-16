#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xbase.py — 在 exe 的 .rdata/.data 里搜「项长度表」候选：
  tag -> item 长度（含 tag 自身），值来自 decode_sob0.BASE+1（数据侧反推，见文档）。
已知约束（这些 tag 的长度是数据侧实测/推导的最小集）：
  0x00:3 0x01:1 0x03:2 0x04:2 0x05:4 0x06:2 0x08:4 0x0C:2 0x0D:1
  0x13:1 0x14:1 0x17:3 0x1E:3 0x1F:3 0x20:3 0x28:3 0x2C:4 0x2E:1
对 **未知 tag（未列）不约束**。分别在 byte / dword / word 三种元素宽度下搜。

用法：python -X utf8 xbase.py [--max 0x40]
"""
import struct
import sys

from pe_min import PE, DUMP_PATH

KNOWN = {0x00: 3, 0x01: 1, 0x03: 2, 0x04: 2, 0x05: 4, 0x06: 2, 0x08: 4,
         0x0C: 2, 0x0D: 1, 0x13: 1, 0x14: 1, 0x17: 3, 0x1E: 3, 0x1F: 3,
         0x20: 3, 0x28: 3, 0x2C: 4, 0x2E: 1}
# 备选：08 的另一种读法（=1）；两个都试
KNOWN_ALT = dict(KNOWN)
KNOWN_ALT[0x08] = 2


def search(pe, known, width, secnames, tag_max):
    out = []
    for s in pe.sections:
        if s["name"] not in secnames:
            continue
        a, b = s["rawptr"], s["rawptr"] + s["rawsize"]
        for S in range(a, b - tag_max * width - width):
            ok = True
            for tag, L in known.items():
                if width == 1:
                    v = pe.data[S + tag]
                elif width == 2:
                    v = struct.unpack_from("<H", pe.data, S + 2 * tag)[0]
                else:
                    v = struct.unpack_from("<I", pe.data, S + 4 * tag)[0]
                if v != L:
                    ok = False
                    break
            if ok:
                out.append((s["name"], S, pe.off_to_rva(S)))
    return out


def main():
    pe = PE(DUMP_PATH)
    a = sys.argv[1:]
    tmax = int(a[a.index("--max") + 1], 0) if "--max" in a else 0x40
    for label, known in (("BASE(08=4)", KNOWN), ("ALT(08=2)", KNOWN_ALT)):
        for width in (1, 2, 4):
            hits = search(pe, known, width, (".rdata", ".data"), tmax)
            print("[%s width=%d] %d 处" % (label, width, len(hits)))
            for sec, S, rva in hits[:20]:
                va = pe.image_base + rva
                dump = " ".join("%02X" % pe.data[S + i] for i in range(min(0x34, tmax)))
                print("    %s off=0x%X VA=0x%08X : %s" % (sec, S, va, dump))


if __name__ == "__main__":
    main()

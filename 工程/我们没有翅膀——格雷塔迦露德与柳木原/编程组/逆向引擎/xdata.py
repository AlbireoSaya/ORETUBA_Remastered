#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xdata.py — SOB 容器数据侧检视（复用 decode_sob0.Sob0 的解析，但只读、不改）。

用途：把「代码区字流」和 func_lib 的 V 处节点打印出来，给静态反汇编做对照。

用法：
  python -X utf8 xdata.py --file <sob> --info
  python -X utf8 xdata.py --file <sob> --cells 0 40          # 打印 [0,40) 号字
  python -X utf8 xdata.py --file <sob> --around 0x1C8D0      # 打印 V 附近（字/字节）
  python -X utf8 xdata.py --file <sob> --walk 0 200          # 按 BASE 铺项（前 200 项）
  python -X utf8 xdata.py --file <sob> --maps                # 六表规模 + 键/值样点
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "工具"))
from decode_sob0 import Sob0, BASE  # noqa: E402


def main():
    a = sys.argv[1:]
    path = a[a.index("--file") + 1]
    sob = Sob0(path)
    print("file=%s magic=%s size=%d" % (os.path.basename(path), sob.magic, len(sob.d)))
    if "--info" in a or "--maps" in a:
        print("table_end=%d header_end=%d ss=%d se=%d" %
              (sob.table_end, sob.header_end, sob.ss, sob.se))
        for i, m in enumerate(sob.maps):
            vals = sorted(m.values())
            print("  maps[%d] n=%d  key[0..3]=%s val_range=%s" %
                  (i, len(m), [hex(k) for k in list(m)[:3]],
                   (hex(vals[0]), hex(vals[-1])) if vals else None))
    if "--cells" in a:
        lo = int(a[a.index("--cells") + 1], 0)
        hi = int(a[a.index("--cells") + 2], 0)
        for i in range(lo, min(hi, len(sob.cells))):
            print("  cell[%d] byte=0x%X = 0x%08X (%d)" %
                  (i, i * 4, sob.cells[i], sob.cells[i]))
    if "--around" in a:
        v = int(a[a.index("--around") + 1], 0)
        w0 = v // 4
        print("-- around byte 0x%X (cell %d) --" % (v, w0))
        for i in range(max(0, w0 - 8), min(len(sob.cells), w0 + 40)):
            mark = " <== V" if i == w0 else ""
            extra = ""
            site = i * 4
            if site in sob.maps[0]:
                extra += " map0=%d" % sob.maps[0][site]
            if site in sob.maps[1]:
                extra += " map1=%d" % sob.maps[1][site]
            if site in sob.maps[3]:
                extra += " map3=0x%X" % sob.maps[3][site]
            if site in sob.maps[4]:
                extra += " map4=0x%X" % sob.maps[4][site]
            strings = ""
            s = sob.str_at(i)
            if s is not None:
                strings = " str=%r" % s
            print("  cell[%d] byte=0x%X = 0x%08X%s%s%s" %
                  (i, site, sob.cells[i], mark, extra, strings))
    if "--walk" in a:
        lo = int(a[a.index("--walk") + 1], 0)
        hi = int(a[a.index("--walk") + 2], 0)
        i = lo
        n = 0
        while i < min(hi, len(sob.cells)) and n < 400:
            t = sob.cells[i]
            L = BASE.get(t, 1) + 1
            payload = [hex(sob.cells[i + j]) for j in range(1, L)
                       if i + j < len(sob.cells)]
            print("  item@%d tag=0x%X L=%d payload=%s" % (i, t, L, payload))
            i += L
            n += 1
    if "--str" in a:
        v = int(a[a.index("--str") + 1], 0)
        print("  str@0x%X = %r" % (v, sob.read_group(v)))


if __name__ == "__main__":
    main()

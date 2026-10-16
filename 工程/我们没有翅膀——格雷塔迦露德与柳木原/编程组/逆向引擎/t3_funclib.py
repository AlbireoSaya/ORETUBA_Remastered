#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1/T3 验证：V 是 func_lib 代码偏移；解析 func_lib 各 V 处的「描述符」并解出其字符串引用。

用法：python -X utf8 t3_funclib.py
"""
import os
import sys

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
sys.path.insert(0, os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具"))
import decode_sob0 as D  # noqa: E402

FL = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT", "func_lib.sob")


def build_rev(sob):
    """cell 值 -> 串文本（用 maps[4] 站点解串）。"""
    rev = {}
    for site, stroff in sob.maps[4].items():
        wi = site // 4
        if wi >= len(sob.cells):
            continue
        cell = sob.cells[wi]
        if cell in rev:
            continue
        if sob.ss <= stroff < sob.se:
            try:
                rev[cell] = sob.read_group(stroff)[0].decode("cp932", "replace")
            except Exception:
                pass
    return rev


def main():
    fl = D.Sob0(FL)
    print("func_lib: ss=%d se=%d code=[%d,%d)" % (fl.ss, fl.se, fl.header_end, fl.header_end + fl.ss))
    rev = build_rev(fl)
    print("reverse map size:", len(rev))

    V = [0x01C43C, 0x019D58, 0x017514, 0x014084, 0x01A96C, 0x018B74, 0x019808,
         0x01F600, 0x00A5D0, 0x019A68, 0x01FF58, 0x007480, 0x01B69C, 0x0205D0]
    for v in V:
        o = v
        if o + 32 > fl.se:
            print("V=0x%06X out of range" % v)
            continue
        cells = [fl.cells[o // 4 + i] for i in range(8)]
        desc = " ".join(("s=%r" % rev[c]) if c in rev else "0x%X" % c for c in cells)
        print("V=0x%06X off=%d : %s" % (v, o, desc))

    # V 是否是「串引用目标」？检查 V 是否出现在 func_lib 的 maps[0]/maps[4] 值域
    print("\n-- V 与 func_lib 表的关系 --")
    m0v = set(fl.maps[0].values())
    m4v = set(fl.maps[4].values())
    for v in V:
        print("  0x%06X: in maps0.values=%s  in maps4.values=%s" % (v, v in m0v, v in m4v))

    # 被引用最多的串引用字（0x018xxxxx）——可能是命令名/类别名
    print("\n-- func_lib 中重复出现的串引用字 top --")
    import collections
    cnt = collections.Counter()
    for site, stroff in fl.maps[4].items():
        wi = site // 4
        if wi < len(fl.cells) and fl.cells[wi] >> 20 == 0x018:
            cnt[fl.cells[wi]] += 1
    for cell, n in cnt.most_common(15):
        print("  0x%08X x%-5d -> %r" % (cell, n, rev.get(cell)))


if __name__ == "__main__":
    main()

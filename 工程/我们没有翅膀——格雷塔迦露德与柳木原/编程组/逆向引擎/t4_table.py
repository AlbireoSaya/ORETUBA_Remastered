#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4 表：V -> 内嵌字符串（首现，窗口 0x120）+ 类型头 + 内建符号。"""
import os
import sys
import collections

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
sys.path.insert(0, os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具"))
import decode_sob0 as D  # noqa: E402

SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")
WIN = 0x120


def main():
    fl = D.Sob0(os.path.join(SCRIPT, "func_lib.sob"))
    c = collections.Counter()
    for fn in sorted(os.listdir(SCRIPT)):
        if not fn.endswith(".sob") or fn == "func_lib.sob":
            continue
        try:
            s = D.Sob0(os.path.join(SCRIPT, fn))
        except Exception:
            continue
        for _k, V in s.maps[3].items():
            if V < 0x100000:
                c[V] += 1
    rows = []
    for V, n in c.most_common():
        first = None
        for j in range(0, WIN, 4):
            o = V + j
            if o + 4 > fl.ss:
                break
            if o in fl.maps[4]:
                t = fl.maps[4][o]
                if fl.ss <= t < fl.se:
                    x = fl.read_group(t)[0].decode("cp932", "replace")
                    if x and first is None:
                        first = (j, x)
        bu = []
        for j in range(0, WIN, 4):
            o = V + j
            if o in fl.maps[0] and fl.maps[0][o] not in bu:
                bu.append(fl.maps[0][o])
        rows.append((V, n, fl.cells[V // 4], first, bu))
    rows.sort(key=lambda r: -r[1])
    print("%-10s %-7s %-5s %-24s %s" % ("V", "nodes", "head", "first_string(@off)", "builtins"))
    for V, n, h, f, bu in rows:
        print("0x%06X  %-7d 0x%02X  %-24s %s"
              % (V, n, h, (("%s@0x%X" % (f[1], f[0])) if f else "-"), bu[:6]))


if __name__ == "__main__":
    main()

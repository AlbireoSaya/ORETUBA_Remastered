#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4 辅助：对每个真实 V，扫描 func_lib 代码窗口中它引用的内建符号(map0) 与字符串(map4)。
输出 V -> {builtins, strings} 供人工判定语义。"""
import os
import sys
import collections

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
sys.path.insert(0, os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具"))
import decode_sob0 as D  # noqa: E402

SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")


def main():
    fl = D.Sob0(os.path.join(SCRIPT, "func_lib.sob"))
    site0 = set(fl.maps[0])
    site4 = set(fl.maps[4])

    # 全库 V 计数
    counter = collections.Counter()
    for fn in sorted(os.listdir(SCRIPT)):
        if not fn.endswith(".sob") or fn == "func_lib.sob":
            continue
        try:
            s = D.Sob0(os.path.join(SCRIPT, fn))
        except Exception:
            continue
        for _k, V in s.maps[3].items():
            if V < 0x100000:
                counter[V] += 1

    top = counter.most_common(60)
    for V, n in top:
        bu = []
        st = []
        for j in range(0, 0x200, 4):
            o = V + j
            if o + 4 > fl.ss:
                break
            if o in site0:
                bu.append(fl.maps[0][o])
            if o in site4:
                t = fl.maps[4][o]
                if fl.ss <= t < fl.se:
                    try:
                        x = fl.read_group(t)[0].decode("cp932", "replace")
                        if x:
                            st.append(x)
                    except Exception:
                        pass
        if st:
            print("V=0x%06X n=%-6d head=0x%X builtins=%s strings=%s"
                  % (V, n, fl.cells[V // 4] if V // 4 < len(fl.cells) else -1,
                     bu[:8], st[:8]))
    # 全量：列出所有带非空串的 V
    print("\n== 所有窗口内含非空串的 V ==")
    for V, n in counter.most_common():
        st = []
        for j in range(0, 0x200, 4):
            o = V + j
            if o + 4 > fl.ss:
                break
            if o in site4:
                t = fl.maps[4][o]
                if fl.ss <= t < fl.se:
                    try:
                        x = fl.read_group(t)[0].decode("cp932", "replace")
                        if x:
                            st.append(x)
                    except Exception:
                        pass
        if st:
            print("  V=0x%06X n=%-6d strings=%s" % (V, n, st[:8]))


if __name__ == "__main__":
    main()

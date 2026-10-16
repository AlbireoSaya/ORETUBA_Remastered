#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1/T3 决定性证据：命令节点 → map3 项 → func_lib 偏移。

输出：
  1) 全库真实 V（<0x100000）值域 vs func_lib 缓冲尺寸（se）
  2) 若干命令节点的原始 6 字 + 其 map3 项（key=该字偏移, value=V）
  3) 反例（V>=0x100000 的假阳性）计数
"""
import os
import sys
import collections

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
sys.path.insert(0, os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具"))
import decode_sob0 as D  # noqa: E402

SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")


def dump_node(sob, wi):
    c = sob.cells
    print("  RAW6 = [%s]" % ", ".join("0x%X" % c[wi + j] for j in range(6)))
    print("  map3 has key(wi+1)*4=%d ? %s  -> V=0x%X"
          % ((wi + 1) * 4, ((wi + 1) * 4) in sob.maps[3],
             sob.maps[3].get((wi + 1) * 4, -1)))
    print("  map4 has key(wi+5)*4=%d ? %s" % ((wi + 5) * 4, ((wi + 5) * 4) in sob.maps[4]))


def main():
    fl = D.Sob0(os.path.join(SCRIPT, "func_lib.sob"))
    print("func_lib buffer: se=%d (代码区 %d..%d)" % (fl.se, fl.header_end, fl.header_end + fl.ss))

    real = collections.Counter()
    fake = collections.Counter()
    samples = []
    for fn in sorted(os.listdir(SCRIPT)):
        if not fn.endswith(".sob") or fn == "func_lib.sob":
            continue
        try:
            s = D.Sob0(os.path.join(SCRIPT, fn))
        except Exception:
            continue
        # 命令节点（v5 判据：V 位 ∈ maps[3]）
        for i in range(len(s.cells) - 5):
            if not (s.cells[i] == 4 and s.cells[i + 2] == 0x0C and s.cells[i + 4] == 3):
                continue
            if (i + 1) * 4 not in s.maps[3]:
                continue
            v = s.maps[3][(i + 1) * 4]
            if v < 0x100000:
                real[v] += 1
                if fn.startswith("s01_02a") and len(samples) < 3:
                    samples.append((fn, i, v))
            else:
                fake[v] += 1

    print("\n真实 V(命令节点，V<0x100000)：%d 个不同值，总节点 %d" % (len(real), sum(real.values())))
    print("  值域 [0x%X, 0x%X]；max < func_lib.se ? %s"
          % (min(real), max(real), max(real) < fl.se))
    print("  全部 4 对齐：%s" % all(v % 4 == 0 for v in real))
    print("假阳性 V(>=0x100000，页引用字)：%d 个不同值，总节点 %d"
          % (len(fake), sum(fake.values())))
    print("  假阳性 V>>20 分布：", collections.Counter(v >> 20 for v in fake))

    print("\n样本（s01_02a 前 3 个命令节点）：")
    for fn, wi, v in samples:
        s = D.Sob0(os.path.join(SCRIPT, fn))
        print(" %s wi=%d (字节偏移 %d) V=0x%X" % (fn, wi, wi * 4, v))
        dump_node(s, wi)

    # func_lib 内 V 位置首字分布（类型标记）
    typ = collections.Counter(fl.cells[v // 4] for v in real if v // 4 < len(fl.cells))
    print("\nV 处 func_lib 首字(cell) 分布 top8:", [(hex(k), n) for k, n in typ.most_common(8)])


if __name__ == "__main__":
    main()

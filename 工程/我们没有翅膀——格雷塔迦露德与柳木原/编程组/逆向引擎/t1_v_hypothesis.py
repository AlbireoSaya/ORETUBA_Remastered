#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 · 「V 是否指向 func_lib 代码区」的数据侧假设检验（不反汇编）。

复用 decode_sob0.Sob0 的容器视图。读 = 工作区解包目录（只读）；不写盘。

用法：
  python -X utf8 t1_v_hypothesis.py
"""
import collections
import os
import sys

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
TOOL_DIR = os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具")
sys.path.insert(0, TOOL_DIR)
import decode_sob0 as D  # noqa: E402

SRC_OT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")
SRC_OTP = os.path.join(DATA_ROOT, "工程", "我们没有翅膀 前奏诗", "解包", "SCRIPT")


def load(path):
    with open(path, "rb") as f:
        return f.read()


def cmd_nodes_with_V(sob):
    """返回 [(wi, V, k, argwords)]：wi = [04] 所在字索引；V = cells[wi+1]。"""
    emp = sob.empty_offsets()
    c = sob.cells
    out = []
    for i in range(len(c) - 5):
        if (c[i] == 4 and c[i + 2] == 0x0C and c[i + 4] == 3
                and sob.maps[4].get((i + 5) * 4) in emp):
            out.append((i, c[i + 1], c[i + 3]))
    return out


def main():
    files = sorted(f for f in os.listdir(SRC_OT) if f.endswith(".sob"))
    vcounter = collections.Counter()
    tot = 0
    per_file = {}
    for fn in files:
        p = os.path.join(SRC_OT, fn)
        try:
            sob = D.Sob0(p)
        except Exception as e:
            print("[skip] %s : %s" % (fn, e))
            continue
        nodes = cmd_nodes_with_V(sob)
        vcounter.update(V for _w, V, _k in nodes)
        tot += len(nodes)
        per_file[fn] = len(nodes)

    print("== ot 全库命令节点：%d 个（%d 文件）" % (tot, len(files)))
    print("== 不同 V 值：%d 个" % len(vcounter))
    print("== V 值域：min=0x%X (%d)  max=0x%X (%d)"
          % (min(vcounter), min(vcounter), max(vcounter), max(vcounter)))
    print("\n-- 全部 V（按出现次数降序，前 90）--")
    for V, n in vcounter.most_common(90):
        print("  0x%06X  %7d" % (V, n))
    if len(vcounter) > 90:
        print("  ... 其余 %d 个：" % (len(vcounter) - 90))
        for V, n in vcounter.most_common()[90:]:
            print("  0x%06X  %7d" % (V, n))

    # ---- func_lib 结构 ----
    fl_path = os.path.join(SRC_OT, "func_lib.sob")
    fl = D.Sob0(fl_path)
    print("\n== func_lib.sob ==")
    print("  magic=%s ss=%d se=%d header_end=%d" % (fl.magic, fl.ss, fl.se, fl.header_end))
    print("  code region(字节) = [%d, %d)" % (fl.header_end, fl.header_end + fl.ss))
    print("  代码区字数 = %d" % (fl.ss // 4))
    print("  maps 条数 = %s" % ([len(m) for m in fl.maps]))
    print("  文件大小 = %d" % len(fl.d))

    # ---- 假设 A：V 是「全局字号」/「某文件内偏移」 ----
    print("\n== 假设检验 ==")
    vs = sorted(vcounter)
    print("A1 V 是否为 4 的倍数：%d/%d" % (sum(1 for v in vs if v % 4 == 0), len(vs)))
    print("A2 V>>20 分布：", collections.Counter(v >> 20 for v in vs))
    print("A3 V 是否落在 func_lib 代码区字节区间 [%d,%d)：%d/%d"
          % (fl.header_end, fl.header_end + fl.ss,
             sum(1 for v in vs if fl.header_end <= v < fl.header_end + fl.ss), len(vs)))
    print("A4 V 是否落在 [0, func_lib.ss/4) 字号区间（%d）：%d/%d"
          % (fl.ss // 4, sum(1 for v in vs if 0 <= v < fl.ss // 4), len(vs)))
    print("A5 V 是否落在 func_lib maps[0] 的值域 0..%d：%d/%d"
          % (max(fl.maps[0].values()) if fl.maps[0] else 0,
             sum(1 for v in vs if v <= (max(fl.maps[0].values()) if fl.maps[0] else 0)), len(vs)))
    # V 落在 ot 自己的 maps[0] 值域？
    otp0 = os.path.join(SRC_OT, "s01_02a.sob")
    o = D.Sob0(otp0)
    print("A6 对照 ot 样本 s01_02a：maps0 值域 0..%d, maps0 条数=%d, ss=%d"
          % (max(o.maps[0].values()) if o.maps[0] else 0, len(o.maps[0]), o.ss))

    # V 与「页引用字」高 12 位比较
    print("A7 V 高 12 位 vs 已知页号 {0x017,0x018}：",
          collections.Counter(v >> 20 for v in vs).most_common(8))


if __name__ == "__main__":
    main()

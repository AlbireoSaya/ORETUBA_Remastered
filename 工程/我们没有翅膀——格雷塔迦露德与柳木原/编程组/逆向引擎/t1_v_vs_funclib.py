#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1/T3 关系检验：ot 的 V 与 func_lib 内部代码引用目标的关系。"""
import os
import sys
import collections

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
sys.path.insert(0, os.path.join(DATA_ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "编程组", "工具"))
import decode_sob0 as D  # noqa: E402

SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")


def main():
    fl = D.Sob0(os.path.join(SCRIPT, "func_lib.sob"))
    m4code = {v for v in fl.maps[4].values() if v < fl.ss}
    m4str = {v for v in fl.maps[4].values() if fl.ss <= v < fl.se}
    print("func_lib map4: code targets %d, string targets %d" % (len(m4code), len(m4str)))

    # 收集 ot 全库 map3 值（真实 V）
    vals = collections.Counter()
    nfiles = 0
    for fn in sorted(os.listdir(SCRIPT)):
        if not fn.endswith(".sob") or fn == "func_lib.sob":
            continue
        try:
            s = D.Sob0(os.path.join(SCRIPT, fn))
        except Exception:
            continue
        nfiles += 1
        for _k, V in s.maps[3].items():
            if V < 0x100000:
                vals[V] += 1
    print("ot 文件 %d，真实 V 值 %d 个" % (nfiles, len(vals)))
    print("V 落在 func_lib map4 code targets 的：%d/%d"
          % (sum(1 for v in vals if v in m4code), len(vals)))
    print("V 落在 func_lib map4 string targets 的：%d/%d"
          % (sum(1 for v in vals if v in m4str), len(vals)))
    # V 是否等于「某个 map4 code target 的前导」/ 是否 4 对齐
    print("V 4 对齐：%d/%d" % (sum(1 for v in vals if v % 4 == 0), len(vals)))

    # V 与「func_lib 里作为 code target 的偏移」的最近距离分布
    tg = sorted(m4code)
    import bisect
    near = collections.Counter()
    for v in vals:
        i = bisect.bisect_left(tg, v)
        best = None
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(tg):
                d = abs(tg[j] - v)
                if best is None or d < best:
                    best = d
        near["<=4" if best is not None and best <= 4 else
             "<=16" if best is not None and best <= 16 else
             "<=64" if best is not None and best <= 64 else ">64"] += 1
    print("V 到最近 func_lib code target 的距离分布：", dict(near))

    # map0 值域 & 是否 905/915 等出现在 V 描述符
    print("func_lib map0 value range", min(fl.maps[0].values()), max(fl.maps[0].values()))
    m0 = collections.Counter(fl.maps[0].values())
    print("map0 最常见值 top10:", m0.most_common(10))

    # V 描述符前 4 字（类型位）分布
    typ = collections.Counter(fl.cells[v // 4] for v in vals if v % 4 == 0 and v // 4 < len(fl.cells))
    print("V 处首字(cell) 分布 top10:", [(hex(k), n) for k, n in typ.most_common(10)])


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""M18 日志分析：统计 EXIT 相关关键字、OVERLAY 行数、sysicons 呼出/收起、异常。
用法: python M18_analyze_log.py <console_xxx.utf8.log> [...]
"""
import io, sys, re

KEYS = ["EXCEPTION", "An exception occured", "[UI][OVERLAY]", "[UI][SYSICON]",
        "[UI][MOUSE]", "[UI][FLOW][ERR]", "[UI][MISS]", "FATAL", "[UI] quit"]

def analyze(path):
    t = io.open(path, encoding="utf-8", errors="replace").read()
    lines = t.splitlines()
    print("=" * 78)
    print("FILE:", path)
    print("  total lines:", len(lines))
    for k in KEYS:
        n = sum(1 for l in lines if k in l)
        print("  %-24s : %d" % (k, n))
    # OVERLAY 去重后的唯一内容
    ov = [l for l in lines if "[UI][OVERLAY]" in l]
    uniq = sorted(set(ov))
    print("  OVERLAY 唯一行数:", len(uniq))
    for u in uniq[:6]:
        print("      ", u[:150])
    # 退出路径
    for l in lines:
        if "[UI] quit" in l:
            print("  QUIT LINE:", l[:300])
    # sysicons 呼出/收起
    print("  --- SYSICON ---")
    for l in lines:
        if "[UI][SYSICON]" in l:
            print("      ", l[:150])
    # 异常上下文
    exc = [i for i, l in enumerate(lines) if "EXCEPTION" in l or "An exception occured" in l]
    if exc:
        print("  --- EXCEPTION 上下文 ---")
        for i in exc[:8]:
            for j in range(max(0, i - 1), min(len(lines), i + 6)):
                print("      %5d %s" % (j + 1, lines[j][:170]))
            print("      ---")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
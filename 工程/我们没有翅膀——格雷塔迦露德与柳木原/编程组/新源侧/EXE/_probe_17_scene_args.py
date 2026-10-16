#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_17_scene_args.py — 在真实场景脚本里找对目标命令 V 的调用点, 打印其压栈实参 (只读).

口径: 场景 .sob 与 func_lib 同容器布局; maps[3] = func_lib 偏移 (is_lib=0 时 -> [mgr+0xD4]).
      线性表感知走查 (op 0x07 变长跳转表整段跨过); op 0x04 CALL 的操作数若在 maps[3],
      其 value 即被调命令实现体 V.

用法:
  python -X utf8 _probe_17_scene_args.py --file <sob> --target 0x1C43C [--target ..] [--back 12]
  python -X utf8 _probe_17_scene_args.py --scan            # 全 SCRIPT 目录统计各 V 的调用站 + 前邻实参
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_12_funclib import W, Sob

SCRIPTDIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT"


def walk_linear(sob):
    """表感知线性走查, 生成 (pos, op, w, ops). 遇无效 op 停止."""
    i = 0
    n = len(sob.cells)
    while i < n:
        op = sob.cells[i]
        if op > 0x2E:
            return
        if op == 0x07:
            j = i + 2
            while j < n and sob.cells[j] != 0xFFFFFFFF:
                j += 1
            yield (i * 4, op, j - i + 1, [])
            i = j + 1
            continue
        w = W[op]
        yield (i * 4, op, w, sob.cells[i + 1:i + 1 + w])
        i += 1 + w


def describe_push(sob, site):
    """描述一个 [08] 的操作数: maps[0] 变量下标 / maps[4] 模块内 / 立即数."""
    hits = sob.site(site)
    if not hits:
        return "imm %d" % sob.cells[site // 4]
    parts = []
    for mi, mv in hits:
        if mi == 0:
            parts.append("VAR#%d" % mv)
        elif mi == 3:
            parts.append("FUNC_V=0x%X" % mv)
        elif mi == 4:
            s = None
            if mv >= sob.ss:
                o = sob.cbase + mv
                e = sob.d.find(b"\0", o)
                s = sob.d[o:e].decode("latin1") if 0 <= e - o <= 64 else None
            parts.append("MOD=0x%X%s" % (mv, (" %r" % s) if s else ""))
        else:
            parts.append("map%d=%d" % (mi, mv))
    return " ".join(parts)


def calls_of(sob, targets):
    out = []
    seq = list(walk_linear(sob))
    by_pos = {p: k for k, (p, op, w, ops) in enumerate(seq)}
    for k, (pos, op, w, ops) in enumerate(seq):
        if op != 0x04:
            continue
        site = pos + 4
        t = sob.maps[3].get(site)
        if t is None:
            t = sob.maps[4].get(site)
        if t in targets:
            # 收集前面连续的 [08] PUSH 实参
            args = []
            j = k - 1
            while j >= 0 and seq[j][1] == 0x08:
                args.append(describe_push(sob, seq[j][0] + 4))
                j -= 1
            args.reverse()
            out.append((pos, t, args))
    return out


def main():
    a = sys.argv[1:]
    if "--scan" in a:
        targets = set(int(x, 0) for x in a[a.index("--targets") + 1:]) if "--targets" in a else None
        stat = {}
        for fn in sorted(os.listdir(SCRIPTDIR)):
            if not fn.endswith(".sob"):
                continue
            try:
                sob = Sob(os.path.join(SCRIPTDIR, fn))
            except Exception:
                continue
            if len(sob.maps[3]) == 0 and len(sob.maps[4]) == 0:
                continue
            tg = targets if targets else None
            for pos, t, args in calls_of(sob, tg if tg is not None else set(
                    v for v in sob.maps[3].values())):
                stat.setdefault((fn, t), []).append(args)
        print("scan done, %d (file,V) pairs" % len(stat))
        return
    fn = a[a.index("--file") + 1]
    tg = set()
    for i, x in enumerate(a):
        if x == "--target":
            tg.add(int(a[i + 1], 0))
    sob = Sob(fn)
    print("file=%s magic=%s ss=0x%X se=0x%X maps[3]=%d maps[4]=%d"
          % (os.path.basename(fn), sob.magic, sob.ss, sob.se, len(sob.maps[3]), len(sob.maps[4])))
    res = calls_of(sob, tg)
    print("== %d call sites to %s ==" % (len(res), [hex(t) for t in sorted(tg)]))
    for pos, t, args in res:
        print("  @0x%X -> V=0x%X   args=[ %s ]" % (pos, t, " , ".join(args)))


if __name__ == "__main__":
    main()

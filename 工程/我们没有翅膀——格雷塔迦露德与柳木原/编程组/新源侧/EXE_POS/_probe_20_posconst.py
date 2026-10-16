#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_20_posconst.py — 在 PC 侧全部二进制里搜「立绘位置常量表」候选 (只读).

目的: 任务书要求找「k 人排布表」. 本探针做两件事:
  (A) 枚举给定候选常量 (PSV cx 高频词表, 1280 空间 与 800 空间两套) 在各文件里的
      u32 出现位置; 并统计「一张表里同时出现多个人排布值」的窗口.
  (B) 扫描每份二进制, 找「连续 >= N 个 u32 都落在 0..maxpos 且互不相同/单调」的
      窗口 = 位置表候选; 打印窗口字节.

用法:
  python -X utf8 _probe_20_posconst.py            # 默认: 两套词表 + 表扫描
  python -X utf8 _probe_20_posconst.py --only A
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 候选文件 (全部只读) ----
WORK = os.path.join(HERE, "work")
EXE   = os.path.join(WORK, "ORE_TUBA.EXE")
DSSP  = os.path.join(WORK, "DS_SPRITE.DLL")
TVPGL = os.path.join(WORK, "tvpgl.dll")
FUNCLIB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"
USERLIB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\user_var.sob"

# PSV 金标 cx 高频词表 (1280x720 中心系)
POS1280 = [86, 136, 236, 336, 436, 490, 640, 740, 790, 844, 944, 1044, 1144, 1194, 1500]
# 换算到 800 宽 (x / 1.6)
POS800 = [int(round(v / 1.6)) for v in POS1280]

TARGETS = {
    "ORE_TUBA.EXE": EXE,
    "DS_SPRITE.DLL": DSSP,
    "tvpgl.dll": TVPGL,
    "func_lib.sob": FUNCLIB,
    "user_var.sob": USERLIB,
}


def u32_at(d, off):
    return struct.unpack_from("<I", d, off)[0]


def scan_consts(d, vals):
    """返回 {val: [offsets]}"""
    out = {v: [] for v in vals}
    for v in vals:
        t = struct.pack("<I", v)
        p = 0
        while True:
            p = d.find(t, p)
            if p < 0:
                break
            out[v].append(p)
            p += 1
    return out


def find_runs(d, lo=0, hi=1500, minlen=4, aligned=4, maxstep=None):
    """扫 u32 序列, 找连续 >=minlen 个落在 [lo,hi] 的窗口."""
    n = len(d) // aligned
    runs = []
    i = 0
    while i < n:
        v = struct.unpack_from("<I", d, i * aligned)[0]
        if lo <= v <= hi:
            j = i
            seq = []
            while j < n:
                w = struct.unpack_from("<I", d, j * aligned)[0]
                if lo <= w <= hi:
                    seq.append(w)
                    j += 1
                else:
                    break
            if len(seq) >= minlen:
                runs.append((i * aligned, seq))
            i = j
        else:
            i += 1
    return runs


def main():
    a = sys.argv[1:]
    only = None
    if "--only" in a:
        only = a[a.index("--only") + 1]

    for name, path in TARGETS.items():
        if not os.path.exists(path):
            print("!! missing %s" % path)
            continue
        d = open(path, "rb").read()
        print("=" * 78)
        print("## %s  size=0x%X (%d)" % (name, len(d), len(d)))

        if only in (None, "A"):
            print("-- A: PSV cx 词表(1280) 出现点 --")
            c = scan_consts(d, POS1280)
            for v in POS1280:
                offs = c[v]
                print("   %5d x%-4d  %s" % (v, len(offs),
                      " ".join("0x%X" % o for o in offs[:10]) + (" ..." if len(offs) > 10 else "")))
            print("-- A: 800 空间词表 %s --" % POS800)
            c8 = scan_consts(d, POS800)
            for v in POS800:
                offs = c8[v]
                print("   %5d x%-4d  %s" % (v, len(offs),
                      " ".join("0x%X" % o for o in offs[:8]) + (" ..." if len(offs) > 8 else "")))

        if only in (None, "B"):
            print("-- B: 位置窗口扫描 (aligned=4, len>=6, 0..1500) --")
            runs = find_runs(d, 0, 1500, minlen=6, aligned=4)
            for off, seq in runs[:20]:
                print("   @0x%X n=%d  %s" % (off, len(seq), seq[:16]))
            if len(runs) > 20:
                print("   ... 共 %d 个窗口" % len(runs))


if __name__ == "__main__":
    main()

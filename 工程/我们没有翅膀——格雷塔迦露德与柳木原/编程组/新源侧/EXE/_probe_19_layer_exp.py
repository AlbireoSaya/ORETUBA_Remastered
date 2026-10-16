#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_19_layer_exp.py — 为"层序活体差分实验"生成可直接改的字节坐标 (只读).

能力:
  1. `--scene <sob>`        打印该场景立绘开立站的 (文件偏移 / 槽号 / 角色名 / 槽号立即数字节偏移)
  2. `--find-discriminating` 全语料搜"能区分 H2 与 H3 的场景":
       同一处登场窗内, 先开立了较大槽号、后开立较小槽号(且角色不同) —— 此时
       "按槽号绘制(H2)" 与 "按插入序绘制(H3)" 预测的上下层相反.

口径:
  * 命令 V: CharacterOpen `0x1C43C`(带槽号+名字) 与 `0x14084`(带槽号+名字)
  * 开立站识别: `[08]…` 连续压栈 + `[04]` 目标 ∈ {0x1C43C, 0x14084}
    arg[0] = 槽号(立即数), arg[1] = 角色图名(maps[4] 串)
  * 文件偏移 = 容器 code_base + 代码区偏移
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_12_funclib import Sob
from _probe_17_scene_args import calls_of, describe_push, SCRIPTDIR

OPEN_VS = (0x1C43C, 0x14084)


def open_sites(sob):
    """返回 [(call_pos, file_off, slot, name, slot_cell_off, slot_cell_file_off,
              name_tbl_off, name_tbl_file_off)]（按地址序）"""
    seq = []
    for pos, t, args in calls_of(sob, set(OPEN_VS)):
        n = len(args)
        slot = None
        name = None
        slot_cell = None
        name_cell = None
        for i, a in enumerate(args):
            cell = pos - 8 * (n - i) + 4      # 实参值所在单元
            if i == 0 and a.startswith("imm "):
                v = int(a[4:])
                if 0 <= v <= 8:
                    slot = v
                    slot_cell = cell
            if "MOD=" in a:
                s = a.split("'")
                if len(s) >= 2:
                    name = s[1]
                    name_cell = cell
        ntbl = sob.rec_off[4].get(name_cell) if name_cell is not None else None
        seq.append((pos, sob.cbase + pos, slot, name, slot_cell,
                    sob.cbase + slot_cell if slot_cell is not None else None,
                    ntbl, ntbl))
    seq.sort()
    return seq


def main():
    a = sys.argv[1:]
    if "--scene" in a:
        fn = a[a.index("--scene") + 1]
        sob = Sob(fn)
        print("file=%s code_base=0x%X ss=0x%X" % (os.path.basename(fn), sob.cbase, sob.ss))
        print("call_pos  call_file  slot  slot_cell_file  name_tbl_file  name")
        for pos, fo, slot, name, sc, scf, ntbl, ntblfo in open_sites(sob):
            print("  0x%06X  0x%06X   %-4s  0x%-8s    0x%-8s  %s"
                  % (pos, fo, slot,
                     ("%X" % scf) if scf is not None else "-",
                     ("%X" % ntblfo) if ntblfo is not None else "-", name))
        return
    if "--find-discriminating" in a:
        found = []
        for f in sorted(os.listdir(SCRIPTDIR)):
            if not f.endswith(".sob"):
                continue
            try:
                sob = Sob(os.path.join(SCRIPTDIR, f))
            except Exception:
                continue
            if not sob.maps[3]:
                continue
            seq = open_sites(sob)
            for k in range(1, len(seq)):
                p0, o0, s0, n0 = seq[k - 1]
                p1, o1, s1, n1 = seq[k]
                if s0 is None or s1 is None or n0 is None or n1 is None:
                    continue
                if n0 == n1:
                    continue
                if s0 > s1:               # 先开大槽号, 后开小槽号
                    found.append((f, o0, s0, n0, o1, s1, n1))
        print("可区分 H2/H3 的场景站 (前开槽号 > 后开槽号, 角色不同): %d 处" % len(found))
        for f, o0, s0, n0, o1, s1, n1 in found[:60]:
            print("  %-14s  0x%06X slot=%d %-10s  ->  0x%06X slot=%d %s"
                  % (f, o0, s0, n0, o1, s1, n1))
        return
    print(__doc__)


if __name__ == "__main__":
    main()

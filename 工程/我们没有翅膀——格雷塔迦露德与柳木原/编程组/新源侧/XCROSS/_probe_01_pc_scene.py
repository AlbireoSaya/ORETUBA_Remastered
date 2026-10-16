#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_01_pc_scene.py — 只读：直接读 PC 场景 .sob，列出立绘开立/删除/动作站 (槽号/角色名/方向token)。

独立实现（不依赖 SOB0ARGS / EXE 的产物），用于与 `_probe_19_layer_exp.py` 和金标逐条比对。

口径（与 EXE 模块一致，见 00_任务书 §8.6）：
  * 容器：magic(4) | u32 table_size | 6 表(每表 u32 计数 + 8B/项) | u32 ss | u32 se | code
    code_base = 8 + table_size + 8
  * 走查：表感知线性走查，op 0x07 变长跳转表整段跨过（跳变长表）
  * 调用：op 0x04 CALL，操作数站 = 甲站，目标 V 取自 maps[3]（否则 maps[4]）
  * 实参：CALL 前连续的 op 0x08 PUSH；给出顺序 = 逐个 PUSH 逐个记录（第一个 PUSH = 实参号最大的那个，
    即任务书里说的 arg[0] 位——本例中以 `slot=` 形式单独标出）
  * 角色名：maps[4] 命中串（≤64 字节）

用法:
  python -X utf8 _probe_01_pc_scene.py --scene <sob>
  python -X utf8 _probe_01_pc_scene.py --scene <sob> --only-open
"""
import os
import struct
import sys

W = {0x00: 0, 0x01: 0, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x08: 1, 0x09: 1,
     0x0A: 1, 0x0B: 1, 0x0C: 1, 0x0D: 3, 0x0E: 3, 0x0F: 3, 0x10: 3, 0x11: 3, 0x12: 3,
     0x13: 3, 0x14: 3, 0x15: 3, 0x16: 2, 0x17: 2, 0x18: 3, 0x19: 3, 0x1A: 1, 0x1B: 1,
     0x1C: 1, 0x1D: 1, 0x1E: 2, 0x1F: 2, 0x20: 2, 0x21: 2, 0x22: 2, 0x23: 2, 0x24: 2,
     0x25: 2, 0x26: 2, 0x27: 2, 0x28: 2, 0x29: 3, 0x2A: 3, 0x2B: 3, 0x2C: 3, 0x2D: 3, 0x2E: 3}

OPEN_VS = (0x1C43C, 0x14084)          # CharacterOpen / CharacterOpen(候补)
DEL_VS = (0x1C5B0,)                  # CharacterDelete
ANIME_VS = (0x18B74,)                # CharacterAction/Move（带方向 ctrl）
CHRIN_VS = (0x186C8,)                # CharacterOpen(chr_in)


class Sob(object):
    def __init__(self, path):
        self.path = path
        self.d = open(path, "rb").read()
        assert self.d[:4] == b"SOB0", self.d[:4]
        ts = struct.unpack_from("<I", self.d, 4)[0]
        o = 8
        self.maps = []
        for _ in range(6):
            c = struct.unpack_from("<I", self.d, o)[0]
            tbl = {}
            p = o + 4
            for _ in range(c):
                k, v = struct.unpack_from("<II", self.d, p)
                tbl[k] = v
                p += 8
            self.maps.append(tbl)
            o = p
        self.ss = struct.unpack_from("<I", self.d, o)[0]
        self.se = struct.unpack_from("<I", self.d, o + 4)[0]
        self.cbase = o + 8
        self.cells = list(struct.unpack_from("<%dI" % (self.se // 4), self.d, self.cbase))

    def strmod(self, off):
        """maps[4] 命中 → 串（模块内偏移 off）。"""
        if off >= self.ss:
            o = self.cbase + off
            e = self.d.find(b"\0", o)
            if 0 <= e - o <= 64:
                return self.d[o:e].decode("latin1")
        return None


def walk_linear(sob):
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
            yield (i * 4, op, j - i + 1)
            i = j + 1
            continue
        yield (i * 4, op, W[op])
        i += 1 + W[op]


def calls_of(sob, targets):
    seq = list(walk_linear(sob))
    out = []
    for k, (pos, op, w) in enumerate(seq):
        if op != 0x04:
            continue
        site = pos + 4
        t = sob.maps[3].get(site)
        if t is None:
            t = sob.maps[4].get(site)
        if t not in targets:
            continue
        args = []          # 每个元素 = 实参描述
        j = k - 1
        while j >= 0 and seq[j][1] == 0x08:
            sp = seq[j][0] + 4
            v = sob.cells[sp // 4]
            hit = [(mi, sob.maps[mi][sp]) for mi in range(6) if sp in sob.maps[mi]]
            if not hit:
                args.append(("imm", v, None))
            else:
                mi, mv = hit[0]
                if mi == 4:
                    args.append(("mod", mv, sob.strmod(mv)))
                elif mi == 0:
                    args.append(("var", mv, None))
                else:
                    args.append(("map%d" % mi, mv, None))
            j -= 1
        args.reverse()
        out.append((pos, t, args))
    return out


def main():
    a = sys.argv[1:]
    if "--scene" not in a:
        print(__doc__)
        return
    fn = a[a.index("--scene") + 1]
    sob = Sob(fn)
    print("file=%s code_base=0x%X ss=0x%X se=0x%X"
          % (os.path.basename(fn), sob.cbase, sob.ss, sob.se))
    print("call_pos  call_file  V        argc  slot  name       token   args")
    tg = set(OPEN_VS) | set(DEL_VS) | set(ANIME_VS) | set(CHRIN_VS)
    for pos, t, args in calls_of(sob, tg):
        slot = None
        name = None
        tok = None
        for k, (kind, v, s) in enumerate(args):
            if kind == "imm" and k == 0 and 0 <= v <= 8:
                slot = v
            if kind == "mod" and s:
                if name is None:
                    name = s
                else:
                    tok = s
        print("0x%06X  0x%06X  0x%-6X %3d   %-4s  %-9s %-6s  [%s]"
              % (pos, sob.cbase + pos, t, len(args),
                 ("%d" % slot) if slot is not None else "-",
                 name if name else "-",
                 tok if tok else "-",
                 ", ".join(("%s%s" % (k, ":%s" % s if s else (":%d" % v)))
                           for k, v, s in args)))


if __name__ == "__main__":
    main()

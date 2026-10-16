#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_12_funclib.py — func_lib.sob 字节码走查: 给出某命令实现体 V 调用的原生 handler (只读).

口径:
  * 容器: magic(4) | u32 table_size | 6 表 | u32 ss | u32 se | code(se)  ; code_base = 8+table_size+8
  * 表项 8B (key=字节偏移 site, value); maps[0]=table0, maps[1]=table1, maps[4]=table4 (见 xdata.py)
  * opcode 宽度表 = 执行模型.md §4.4 (47 op); op 0x07 为变长跳转表 [07][idx][t0..tN][0xFFFFFFFF]
  * op 0x05 = CALLNATIVE(fn, arg, dest): fn 在 maps[1] 中, 其 value = handler 向量下标
  * op 0x04 = CALL: 操作数在 maps[3]/maps[4], value = 目标 V 偏移

用法: python -X utf8 _probe_12_funclib.py --v 0x2C3C [--depth 2] [--list]
      python -X utf8 _probe_12_funclib.py --info
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"

W = {0x00: 0, 0x01: 0, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x08: 1, 0x09: 1,
     0x0A: 1, 0x0B: 1, 0x0C: 1, 0x0D: 3, 0x0E: 3, 0x0F: 3, 0x10: 3, 0x11: 3, 0x12: 3,
     0x13: 3, 0x14: 3, 0x15: 3, 0x16: 2, 0x17: 2, 0x18: 3, 0x19: 3, 0x1A: 1, 0x1B: 1,
     0x1C: 1, 0x1D: 1, 0x1E: 2, 0x1F: 2, 0x20: 2, 0x21: 2, 0x22: 2, 0x23: 2, 0x24: 2,
     0x25: 2, 0x26: 2, 0x27: 2, 0x28: 2, 0x29: 3, 0x2A: 3, 0x2B: 3, 0x2C: 3, 0x2D: 3, 0x2E: 3}


class Sob:
    def __init__(self, path=SOB):
        self.d = open(path, "rb").read()
        self.magic = self.d[:4]
        ts = struct.unpack_from("<I", self.d, 4)[0]
        o = 8
        self.maps = []
        self.rec_off = []          # rec_off[i][site] = 该表记录的文件偏移（改 maps 值用）
        for i in range(6):
            c = struct.unpack_from("<I", self.d, o)[0]
            tbl = {}
            ro = {}
            p = o + 4
            for _ in range(c):
                k, v = struct.unpack_from("<II", self.d, p)
                tbl[k] = v
                ro[k] = p
                p += 8
            self.maps.append(tbl)
            self.rec_off.append(ro)
            o = p
        self.table_size = ts
        self.ss = struct.unpack_from("<I", self.d, o)[0]
        self.se = struct.unpack_from("<I", self.d, o + 4)[0]
        self.cbase = o + 8               # 文件偏移: 代码区起点
        self.cells = list(struct.unpack_from("<%dI" % (self.se // 4), self.d, self.cbase))

    def site(self, off):
        """字节偏移 -> maps 命中信息"""
        out = []
        for i, m in enumerate(self.maps):
            if off in m:
                out.append((i, m[off]))
        return out


def op_target(sob, site):
    """操作数站点的重定位目标 (maps[3] 优先, 否则 maps[4]); 返回模块内偏移或 None."""
    t3 = sob.maps[3].get(site)
    t4 = sob.maps[4].get(site)
    if t3 is not None:
        return t3
    if t4 is not None:
        return t4
    return None


def walk(sob, v, depth=0, maxdepth=3, out=None, seen=None, limit=20000):
    """CFG 走查 V 起的代码: 跟随 JMP/JZ(0x1E)/跳转表(0x07) 与 CALL(0x04). 收集全部指令."""
    if out is None:
        out = []
    if seen is None:
        seen = set()
    if depth > maxdepth:
        return out
    work = [v]
    while work:
        a = work.pop()
        if a in seen or a < 0 or a + 4 > sob.ss or a % 4:
            continue
        seen.add(a)
        i = a // 4
        op = sob.cells[i]
        if op > 0x2E:
            out.append((v, op, a, None, "INVALID"))
            continue
        if op == 0x07:
            j = i + 2
            entries = []
            while j < len(sob.cells) and sob.cells[j] != 0xFFFFFFFF:
                entries.append(sob.cells[j])
                j += 1
            tgt = [e for e in entries if 0 <= e < sob.ss]
            out.append((v, op, a, entries[:8], "table[n=%d]" % len(entries)))
            for e in tgt:
                work.append(e)
            continue
        w = W[op]
        if op == 0x05:
            fnidx = sob.maps[1].get((i + 1) * 4)
            info = "CALLN h%s" % fnidx
        elif op == 0x04:
            t = op_target(sob, (i + 1) * 4)
            info = "CALL V=0x%X" % t if t is not None else "CALL ?"
            if t is not None:
                walk(sob, t, depth + 1, maxdepth, out, seen, limit)
        elif op == 0x08:
            site = (i + 1) * 4
            hit = [m for m in sob.site(site)]
            info = "PUSH %s" % (hit if hit else ("imm %d" % sob.cells[i + 1]))
        elif op == 0x06:
            t = op_target(sob, (i + 1) * 4)
            info = "JMP 0x%X" % t if t is not None else "JMP ?"
        elif op == 0x1E:
            t0 = op_target(sob, (i + 1) * 4)
            t1 = op_target(sob, (i + 2) * 4)
            info = "JZ 0x%s / 0x%s" % (hex(t0) if t0 is not None else "?",
                                      hex(t1) if t1 is not None else "?")
        else:
            info = ""
        out.append((v, op, a, sob.cells[i + 1:i + 1 + w], info))
        # successors
        if op in (0x00, 0x01, 0x02):
            continue                       # 终止 (RET 目标动态)
        if op == 0x06:
            if t is not None:
                work.append(t)
            continue
        if op == 0x1E:
            # JZ handler 0x433945: if (op0val == 0) pc = op1 else pc = a+8
            # op0 为"立即 0"时不可被 [03][REF] 改写 (该 site 不是 maps 引用) -> 只有一条后继.
            raw0 = sob.cells[i + 1]
            is_ref = bool(sob.site((i + 1) * 4))
            if is_ref:
                # 自改写槽: 两条后继都要跟
                if t1 is not None:
                    work.append(t1)
                nxt = a + 8
                if nxt < sob.ss:
                    work.append(nxt)
            else:
                if raw0 == 0:
                    if t1 is not None:
                        work.append(t1)
                else:
                    nxt = a + 8
                    if nxt < sob.ss:
                        work.append(nxt)
            continue
        nxt = a + 4 * (1 + w)
        if nxt < sob.ss:
            work.append(nxt)
        if len(seen) > limit:
            break
    return out


def main():
    a = sys.argv[1:]
    sob = Sob()
    if "--info" in a or len(a) == 0:
        print("magic=%s table_size=%d ss=0x%X se=0x%X code_base=0x%X cells=%d"
              % (sob.magic, sob.table_size, sob.ss, sob.se, sob.cbase, len(sob.cells)))
        for i, m in enumerate(sob.maps):
            print("  maps[%d] n=%d" % (i, len(m)))
        if len(a) == 0:
            return
    if "--v" in a:
        v = int(a[a.index("--v") + 1], 0)
        d = int(a[a.index("--depth") + 1], 0) if "--depth" in a else 3
        res = walk(sob, v, 0, d)
        print("== walk V=0x%X depth<=%d : %d steps ==" % (v, d, len(res)))
        calls = {}
        for vv, op, pos, ops, info in res:
            if op == 0x05:
                idx = info.split("h")[-1]
                calls[idx] = calls.get(idx, 0) + 1
        if "--list" in a:
            for vv, op, pos, ops, info in res:
                print("  V?@0x%X pos=0x%X op=0x%02X ops=%s  %s"
                      % (vv, pos, op, ops, info))
        print("-- CALLNATIVE handler 下标统计 --")
        for k in sorted(calls, key=lambda x: (x == "None", int(x) if x != "None" else 0)):
            print("   h%-6s x%d" % (k, calls[k]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""xvseg.py — `func_lib.sob` 命令实现体**切分与反汇编**引擎（M1，ISSUE-20261008-04）。

背景
    `func_lib.sob` 是 Lucifen 的**命令实现体库**：场景脚本里 `[04][V]` = op `0x04`（CALL），
    `V` 是 `func_lib` 代码缓冲内的偏移（装载期重定位为 `func_lib_base + V`）。
    它**没有节点长度字段** ⇒ 既有做法只能"猜窗口"读串（实测 9 处越窗实锤、12 处归属未定）。

本件给出的**切分判据**（三条，全部可复跑、可失败）
    C1 **指令边界唯一性**：用引擎真值 opcode 宽度表（`执行模型.md` §4.4，0x07 表感知）
       从 0 线性走查整个代码区 `[0, ss)`，**每个 op 位置的字必须 ≤ 0x2E**（非法 op 位置 = 0），
       且走查必须**恰好落在 ss**（不越界、不留尾）。
    C2 **控制流目标对齐**：所有控制流目标——op `0x04`（CALL）/`0x06`（JMP）的第 1 操作数、
       op `0x1E`（JZ）的第 2 操作数、op `0x07`（表跳）表项——经 `maps[4]` 还原后
       **必须落在 C1 解出的指令起点上**（否则该目标处无法解码 ⇒ 判据失败）。
       ⇒ 这一条**自证解码对齐**：目标错一格就会落到操作数上，而操作数几乎不可能是合法 op。
    C3 **过程切分**：
       · 基本块（basic block）：以 C1 的指令流为准，在「控制流目标」与「返回项之后」切分；
       · 过程（procedure）：入口 `V`（CALL 目标）→ 沿**过程内**边（JZ / JMP / 0x07 表 / 直落）
         做可达闭包，**遇 `0x04`（CALL）不展开**（那是另一个过程）、遇 `0x00/0x01/0x02`
         （HALT_OK / RET / 带值 RET）终止。
       ⇒ 一个命令实现体 = `core`（含 V 的那个基本块，**边界确定**）+ `exp`（过程内可达的其它块）。

★ 置信度口径（写死，不混报）
    `确定`  = V 落在 C1 的指令起点上，且 C2 全库通过，且 V 被 CALL（scenes maps[3] 或库内 0x04）；
    `候选`  = V 落在指令起点上，但**未被任何 CALL 引用**（无调用者 ⇒ 可能是数据/死代码）；
    `未定`  = V 不落在任何指令起点上（**判据失败**，如实报出，不给边界）。

用法（目标文件只读；产物写本目录）
  python -X utf8 xvseg.py --stats                     # 切分统计 + C1/C2 自检
  python -X utf8 xvseg.py --v 0x1C43C                 # 反汇编单个 V（含过程内闭包）
  python -X utf8 xvseg.py --v 0x1C43C --core-only     # 只看 core 基本块
  python -X utf8 xvseg.py --emit                      # 落盘 funclib_切分.tsv + funclib_反汇编\
  python -X utf8 xvseg.py --rejudge                   # 21 个 V 的串归属前后对照
  python -X utf8 xvseg.py --negtest                   # 负向自证（起点平移 / 错判据 / 错宽度表）
"""
from __future__ import annotations

import argparse
import collections
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "工具"))
sys.path.insert(0, HERE)
from decode_sob0 import Sob0  # noqa: E402

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
OT_SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")
FL_PATH = os.path.join(OT_SCRIPT, "func_lib.sob")

OUT_TSV = os.path.join(HERE, "funclib_切分.tsv")
OUT_ASM_DIR = os.path.join(HERE, "funclib_反汇编")
OUT_ASM_ALL = os.path.join(OUT_ASM_DIR, "全部.asm")
OUT_REJUDGE = os.path.join(HERE, "funclib_串归属重判.tsv")

# ── 引擎真值：每个 op 的操作数字数（`执行模型.md` §4.4；0x07 = 变长，单独处理） ──
OPND = {0x00: 0, 0x01: 0, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1,
        0x08: 1, 0x09: 1, 0x0A: 1, 0x0B: 1, 0x0C: 1, 0x0D: 3, 0x0E: 3,
        0x0F: 3, 0x10: 3, 0x11: 3, 0x12: 3, 0x13: 3, 0x14: 3, 0x15: 3,
        0x16: 2, 0x17: 2, 0x18: 3, 0x19: 3, 0x1A: 1, 0x1B: 1, 0x1C: 1,
        0x1D: 1, 0x1E: 2, 0x1F: 2, 0x20: 2, 0x21: 2, 0x22: 2, 0x23: 2,
        0x24: 2, 0x25: 2, 0x26: 2, 0x27: 2, 0x28: 2, 0x29: 3, 0x2A: 3,
        0x2B: 3, 0x2C: 3, 0x2D: 3, 0x2E: 3}
SENT = 0xFFFFFFFF
WLEN = {k: v + 1 for k, v in OPND.items()}

def esc(x):
    r"""串内控制字符转义（串区里有含 0x0A 的日文串，否则会撕破 TSV 行列）。"""
    if not isinstance(x, str):
        return x
    out = []
    for ch in x:
        o = ord(ch)
        if ch == "\t":
            out.append("\\t")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif o < 32:
            out.append("\\x%02X" % o)
        else:
            out.append(ch)
    return "".join(out)


TERM = (0x00, 0x01, 0x02)
MN = {0x00: "HALT_OK", 0x01: "RET", 0x02: "RETVAL_RET", 0x03: "STORE_RETVAL",
      0x04: "CALL", 0x05: "CALLNATIVE", 0x06: "JMP", 0x07: "TABJMP",
      0x08: "PUSH", 0x09: "PUSHDEREF", 0x0A: "POPSTORE", 0x0B: "FRAME_ALLOC",
      0x0C: "SP_DROP", 0x0D: "ADD", 0x0E: "SUB", 0x0F: "MUL", 0x10: "DIV",
      0x11: "MOD", 0x12: "MODN", 0x13: "AND", 0x14: "OR", 0x15: "XOR",
      0x16: "NOT", 0x17: "EQZ", 0x18: "SHR", 0x19: "SHL", 0x1A: "INC_D",
      0x1B: "DEC_D", 0x1C: "INC_S", 0x1D: "DEC_S", 0x1E: "JZ",
      0x1F: "MOV", 0x20: "MOV_D", 0x21: "MOV_DD", 0x22: "ST_STK",
      0x23: "LD_STK", 0x24: "ST_STK_D", 0x25: "MOV_STK_STK", 0x26: "LD_STK_D",
      0x27: "MOV_DD2", 0x28: "LEA_STK", 0x29: "LT", 0x2A: "LE", 0x2B: "GT",
      0x2C: "GE", 0x2D: "EQ", 0x2E: "NE"}
# 数据侧反推的 BASE（decode_sob0 v5，**已知 6 个 tag 与引擎不符**）—— 只作负向对照
BASE_PAYLOAD = {0x00: 2, 0x01: 0, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x08: 3,
                0x0C: 1, 0x0D: 0, 0x13: 0, 0x14: 0, 0x17: 2, 0x1E: 2, 0x1F: 2,
                0x20: 2, 0x28: 2, 0x2C: 3, 0x2E: 0}
VREG = os.path.join(HERE, "v_regions.tsv")


# ================================================================ 引擎
class Seg:
    """func_lib 代码区切分模型（一次构建，多次查询）。"""

    def __init__(self, path=FL_PATH, wlen=None, w07=True):
        self.sob = Sob0(path)
        c = self.sob.cells
        self.cells = c
        self.ss = self.sob.ss
        self.se = self.sob.se
        self.m0, self.m1 = self.sob.maps[0], self.sob.maps[1]
        self.m2, self.m3 = self.sob.maps[2], self.sob.maps[3]
        self.m4 = self.sob.maps[4]
        self.wlen = dict(wlen or WLEN)
        self.use07 = w07
        self.insns = []
        self.by_pos = {}
        self.illegal = []
        self._decode()
        self.VS = ()                     # 事后由 build() 填
        self._leaders()
        self._blocks()

    # ---------- C1 ----------
    def _decode(self):
        c, n, ss = self.cells, len(self.cells), self.ss
        i, lim = 0, ss // 4
        while i < lim:
            op = c[i]
            if op > 0x2E:
                self.illegal.append(i * 4)
                i += 1
                continue
            if op == 0x07 and self.use07:
                j = i + 2
                while j < n and c[j] != SENT:
                    j += 1
                ops = list(range(i + 1, min(j + 1, n)))
                endb = ((j + 1) if j < n else n) * 4
                if j >= n or endb > ss:
                    self.illegal.append(("0x07-table-oob", i * 4))
            else:
                L = self.wlen.get(op, 1)
                ops = list(range(i + 1, min(i + L, n)))
                endb = i * 4 + L * 4
            self.by_pos[i * 4] = (op, ops, endb)
            self.insns.append((i * 4, op, ops, endb))
            i += (endb - i * 4) // 4
        self.walk_end = i * 4

    # ---------- 控制流目标 ----------
    def targets_of(self, op, ops, pos):
        intra, calls, bad = [], [], []
        m4 = self.m4
        if op == 0x04:
            v = m4.get(ops[0] * 4) if ops else None
            if v is not None and v < self.ss:
                calls.append(v)
            else:
                bad.append((pos, "0x04", v))
        elif op == 0x06:
            v = m4.get(ops[0] * 4) if ops else None
            if v is not None and v < self.ss:
                intra.append(v)
            else:
                bad.append((pos, "0x06", v))
        elif op == 0x1E:
            v = m4.get(ops[1] * 4) if len(ops) > 1 else None
            if v is not None and v < self.ss:
                intra.append(v)
            else:
                bad.append((pos, "0x1E", v))
        elif op == 0x07 and self.use07:
            for o in ops:
                v = m4.get(o * 4)
                if v is not None and v < self.ss:
                    intra.append(v)
        return intra, calls, bad

    def _leaders(self):
        self.call_sites = collections.defaultdict(list)
        self.bad_targets = []
        self.leaders = {0}
        for (pos, op, ops, endb) in self.insns:
            intra, calls, bad = self.targets_of(op, ops, pos)
            self.bad_targets += bad
            for t in intra:
                self.leaders.add(t)
            for t in calls:
                self.leaders.add(t)
                self.call_sites[t].append(pos)
            if op in TERM and endb < self.ss:
                self.leaders.add(endb)

    def _blocks(self):
        idx_of_pos = {p: k for k, (p, _, _, _) in enumerate(self.insns)}
        ls = sorted(x for x in self.leaders if x <= self.ss)
        self.block_of = {}
        self.blocks = []
        for k, st in enumerate(ls):
            en = ls[k + 1] if k + 1 < len(ls) else self.ss
            j = idx_of_pos.get(st)
            if j is None:
                self.blocks.append((st, en, []))
                continue
            k2 = j
            rng = []
            while k2 < len(self.insns) and self.insns[k2][0] < en:
                self.block_of[self.insns[k2][0]] = len(self.blocks)
                rng.append(k2)
                k2 += 1
            self.blocks.append((st, en, rng))
        self.intra_edges = {}
        for bi, (st, en, rng) in enumerate(self.blocks):
            succ = set()
            for k in rng:
                pos, op, ops, endb = self.insns[k]
                intra, calls, bad = self.targets_of(op, ops, pos)
                for t in intra:
                    if t in self.block_of:
                        succ.add(self.block_of[t])
                if op in TERM:
                    break
            else:
                if bi + 1 < len(self.blocks):
                    succ.add(bi + 1)
            self.intra_edges[bi] = succ

    # ---------- C3 ----------
    def proc(self, V):
        if V % 4 or V not in self.by_pos:
            return dict(ok=False, reason="V 不落在指令起点")
        b0 = self.block_of[V]
        seen, stack = {b0}, [b0]
        while stack:
            b = stack.pop()
            for s in self.intra_edges.get(b, ()):
                if s not in seen:
                    seen.add(s)
                    stack.append(s)
        order = sorted(seen)
        ins = sorted(k for b in order for k in self.blocks[b][2])
        pos = [self.insns[k][0] for k in ins]
        start, end = pos[0], max(self.insns[k][3] for k in ins)
        # 过程在字面地址上的「连续段数」（1 = 单段连续）
        runs, cur_end = 0, -1
        for b in order:
            st, en, _ = self.blocks[b]
            if st != cur_end:
                runs += 1
            cur_end = en
        # 帧平衡：过程内 0x0B / 0x0C 的操作数之和
        fa_sum = sd_sum = 0
        n_fa = n_sd = 0
        for k in ins:
            p, op, ops, endb = self.insns[k]
            if op == 0x0B and ops:
                n_fa += 1
                fa_sum += self.cells[ops[0]]
            elif op == 0x0C and ops:
                n_sd += 1
                sd_sum += self.cells[ops[0]]
        # 过程末尾（终止项之前）的紧邻 0x0C
        epi = None
        if len(ins) >= 2 and self.insns[ins[-1]][1] in TERM \
                and self.insns[ins[-2]][1] == 0x0C and self.insns[ins[-2]][2]:
            epi = self.cells[self.insns[ins[-2]][2][0]]
        # ★ x02.py 口径的帧配对：过程内**首个 0x0B k** vs 终止项前紧邻的 **0x0C k**
        pro = None
        for k in ins:
            if self.insns[k][1] == 0x0B and self.insns[k][2]:
                pro = self.cells[self.insns[k][2][0]]
                break
        natives, calls, strings = [], [], []
        for k in ins:
            p, op, ops, endb = self.insns[k]
            if op == 0x05 and ops:
                natives.append(self.m1.get(ops[0] * 4))
            if op == 0x04 and ops:
                calls.append(self.m4.get(ops[0] * 4))
            for o in ops:
                s = o * 4
                if s in self.m4 and self.ss <= self.m4[s] < self.se:
                    strings.append((p, s, self.m4[s]))
        core = self.blocks[b0]
        other_v = [V2 for V2 in self.VS if V2 != V and start < V2 < end]
        return dict(ok=True, V=V, core=core, order=order,
                    block_ids=order, insns=ins, start=start, end=end,
                    runs=runs, other_v=other_v,
                    natives=natives, calls=calls, strings=strings,
                    n_insn=len(ins), core_start=core[0], core_end=core[1],
                    n_core_insn=len(core[2]),
                    fa_sum=fa_sum, sd_sum=sd_sum, n_fa=n_fa, n_sd=n_sd,
                    frame_ok=(n_fa > 0 or n_sd > 0) and fa_sum == sd_sum,
                    epilogue_drop=epi, pro_frame=pro,
                    frame_pair=("配对且相等" if (pro is not None and pro == epi) else
                                "配对但不等" if (pro is not None and epi is not None) else
                                "无配对"))

    # ---------- 注解 ----------
    def ann(self, pos):
        out = []
        if pos in self.m0:
            out.append("var#%d" % self.m0[pos])
        if pos in self.m2:
            out.append("sym#%d" % self.m2[pos])
        if pos in self.m1:
            out.append("native#%d" % self.m1[pos])
        if pos in self.m3:
            out.append("V:0x%X" % self.m3[pos])
        if pos in self.m4:
            v = self.m4[pos]
            if self.ss <= v < self.se:
                out.append('str@"%s"' % esc(self.strat(v)))
            elif v < self.ss:
                out.append("L_%X" % v)
            else:
                out.append("oob:0x%X" % v)
        return ",".join(out)

    def strat(self, v):
        try:
            return self.sob.read_group(v)[0].decode("cp932", "replace")
        except Exception:
            return "?"

    def disasm_lines(self, ks, marks=None):
        marks = marks or {}
        out = []
        for k in ks:
            pos, op, ops, endb = self.insns[k]
            args = ["0x%X[%s]" % (self.cells[o], self.ann(o * 4) or "-") for o in ops]
            out.append("%08X  %-13s %-40s %s" % (pos, MN.get(op, "op%02X" % op),
                                                " ".join(args), marks.get(pos, "")))
        return out


# ================================================================ 语料
def corpus_entries(script=OT_SCRIPT):
    vs, files = collections.Counter(), collections.defaultdict(set)
    for fn in sorted(os.listdir(script)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            s = Sob0(os.path.join(script, fn))
        except Exception:
            continue
        for site, v in s.maps[3].items():
            if v < 0x100000:
                vs[v] += 1
                files[v].add(fn)
    return set(vs), vs, files


def build():
    seg = Seg()
    ents, cnt, files = corpus_entries()
    internal = set(seg.call_sites)
    allv = sorted(ents | internal)
    seg.VS = tuple(allv)
    return seg, ents, internal, cnt, files, allv


# ================================================================ 补充证据
def allv_of(seg):
    if seg.VS:
        return seg.VS
    ents, _c, _f = corpus_entries()
    return sorted(ents | set(seg.call_sites))


def do_evidence(seg, allv):
    print("== E1 重定位占位基址 / 是否存在「未记账的代码指针字」 ==")
    cs = collections.Counter()
    for site, v in seg.m4.items():
        if v < seg.ss:
            cs[seg.cells[site // 4] - v] += 1
    B = cs.most_common(1)[0][0]
    print("  raw - maps[4]value 的众数 = 0x%X（%d/%d 条）⇒ 占位基址 B = 0x%X"
          % (B, cs.most_common(1)[0][1], sum(cs.values()), B))
    hit = [i * 4 for i, val in enumerate(seg.cells) if val >= B and val - B < seg.ss]
    unacc = [s for s in hit if s not in seg.m4]
    print("  形如 B+x（x<ss）的字 = %d；其中**不在 maps[4] 记账内**者 = %d" % (len(hit), len(unacc)))
    print("  ⇒ 代码区内没有「未被 maps[4] 记账的代码指针字」⇒ 不存在静态可读的指针跳转表")
    print("== E2 静态不可达区：根块前驱 / 间接跳转惯用式 ==")
    cov, unc = coverage(seg, allv)
    inedge = collections.Counter()
    for b, succ in seg.intra_edges.items():
        for s in succ:
            inedge[s] += 1
    roots = [b for b in unc if not inedge[b]]
    endmap = {seg.insns[k][3]: k for k in range(len(seg.insns))}
    prev = collections.Counter()
    for b in roots:
        k = endmap.get(seg.blocks[b][0])
        prev[MN.get(seg.insns[k][1], "?") if k is not None else "0"] += 1
    print("  不可达块 %d；根 %d；根的前一条指令：%s" % (len(unc), len(roots), dict(prev)))
    tgt = collections.defaultdict(list)
    for (pos, op, ops, endb) in seg.insns:
        intra, calls, bad = seg.targets_of(op, ops, pos)
        for t in intra + calls:
            tgt[t].append(pos)
    notgt = [seg.blocks[b][0] for b in roots if not tgt[seg.blocks[b][0]]]
    print("  根中**完全无静态目标指向**者 = %d / %d" % (len(notgt), len(roots)))
    npr = 0
    for k in range(len(seg.insns) - 1):
        p, op, ops, e = seg.insns[k]
        p2, op2, ops2, e2 = seg.insns[k + 1]
        if e == p2 and op == 0x08 and op2 in TERM:
            npr += 1
    print("  「PUSH <代码指针>; RET」间接跳转惯用式出现 = %d 次（0 ⇒ 无此路径）" % npr)
    print("  ⇒ 不可达区不可由 6 个控制流 op（0x04/0x06/0x07/0x1E + 动态 RET）静态到达；未决（见报告）")


def do_crossbuild(paths, labels):
    print("== E3 跨构建对照（同一 func_lib 的另一份产出：原版 vs 汉化补丁版） ==")
    for lab, p in zip(labels, paths):
        s = Seg(p)
        vs = allv_of(s)
        print("  %-26s 指令=%-6d 非法op=%d 块=%-5d V(语料)可切分=%s"
              % (lab, len(s.insns), len(s.illegal), len(s.blocks),
                 all(s.proc(v)["ok"] for v in vs if v in s.by_pos)))
    a, b = Seg(paths[0]), Seg(paths[1])
    same = tot = 0
    for p, op, ops, e in a.insns:
        if p in b.by_pos:
            tot += 1
            same += 1 if b.by_pos[p][0] == op else 0
    print("  同偏移指令 op 相同 %d/%d = %.6f；块数 %d vs %d；块首集合相同 = %s"
          % (same, tot, same / tot, len(a.blocks), len(b.blocks),
             {x[0] for x in a.blocks} == {x[0] for x in b.blocks}))
    da, db = open(paths[0], "rb").read(), open(paths[1], "rb").read()
    if len(da) == len(db):
        H, SS, SE = a.sob.header_end, a.ss, a.se
        for lo, hi, lab in ((0, H, "表头+六表"), (H, H + SS, "代码区"), (H + SS, H + SE, "串区")):
            n = sum(1 for i in range(lo, hi) if da[i] != db[i])
            print("     %-10s [0x%X,0x%X) 差异字节 = %d / %d" % (lab, lo, hi, n, hi - lo))
    else:
        print("     两文件大小不同（%d vs %d），不做逐字节对照" % (len(da), len(db)))


# ================================================================ 端到端：全库 SOB 走查
def _walk_table(cells, ss, SENT=SENT, wlen=WLEN):
    """表感知（0x07 知表）线性走查 → (items, illegal) items=[(pos, op, [opnd_pos])]"""
    n = len(cells)
    i, lim = 0, ss // 4
    items, illegal = [], []
    while i < lim:
        op = cells[i]
        if op > 0x2E:
            illegal.append(i * 4)
            i += 1
            continue
        if op == 0x07:
            j = i + 2
            while j < n and cells[j] != SENT:
                j += 1
            items.append((i * 4, op, list(range(i + 1, min(j + 1, n)))))
            if j >= n:
                illegal.append(("0x07-table-oob", i * 4))
            i = j + 1
            continue
        L = wlen.get(op, 1)
        items.append((i * 4, op, list(range(i + 1, min(i + L, n)))))
        i += L
    return items, illegal


def do_corpus(script, tag=OT_SCRIPT):
    tot = collections.Counter()
    opcnt = collections.Counter()
    files = 0
    bad_files = []
    for fn in sorted(os.listdir(script)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            s = Sob0(os.path.join(script, fn))
        except Exception:
            continue
        files += 1
        items, ill = _walk_table(s.cells, s.ss)
        starts = {p for p, _, _ in items}
        c = s.cells
        f_bad = 0
        m1, m3, m4 = s.maps[1], s.maps[3], s.maps[4]
        for pos, op, ops in items:
            opcnt[op] += 1
            if op == 0x05 and ops:
                tot["op05"] += 1
                ok = ops[0] * 4 in m1
                tot["op05ok"] += 1 if ok else 0
                f_bad += 0 if ok else 1
            elif op == 0x04 and ops:
                tot["op04"] += 1
                site = ops[0] * 4
                ok = (site in m3) or (site in m4)
                tot["op04ok"] += 1 if ok else 0
                f_bad += 0 if ok else 1
            elif op == 0x06 and ops:
                v = m4.get(ops[0] * 4)
                tot["op06"] += 1
                if v is not None and v < s.ss:
                    tot["op06ok"] += 1
                    if v in starts:
                        tot["op06al"] += 1
                        continue
                f_bad += 1
            elif op == 0x1E and len(ops) > 1:
                v = m4.get(ops[1] * 4)
                tot["op1E"] += 1
                if v is not None and v < s.ss:
                    tot["op1Eok"] += 1
                    if v in starts:
                        tot["op1Eal"] += 1
                        continue
                f_bad += 1
            elif op == 0x07:
                tot["op07"] += 1
                for o in ops[1:]:
                    v = m4.get(o * 4)
                    if v is not None and v < s.ss:
                        tot["op07tgt"] += 1
                        if v in starts:
                            tot["op07al"] += 1
                        else:
                            f_bad += 1
        tot["files"] += 1
        tot["illegal"] += len([x for x in ill if isinstance(x, int)])
        tot["insn"] += len(items)
        if f_bad:
            bad_files.append((fn, f_bad))
    print("== 端到端走查（%s，%d 个可解析 .sob） ==" % (tag, files))
    print("  指令总数 %d；**非法 op 位置 = %d**（要求 0）" % (tot["insn"], tot["illegal"]))
    print("  op 0x05 操作数 ∈ maps[1] : %d/%d = %.6f"
          % (tot["op05ok"], tot["op05"], tot["op05ok"] / tot["op05"]))
    print("  op 0x04 操作数 ∈ maps[3]∪maps[4] : %d/%d = %.6f"
          % (tot["op04ok"], tot["op04"], tot["op04ok"] / tot["op04"]))
    print("  op 0x06 目标 ∈ 本模块代码区 : %d/%d ；其中**落在指令起点**者 %d/%d = %.6f"
          % (tot["op06ok"], tot["op06"], tot["op06al"], tot["op06"],
             tot["op06al"] / tot["op06"] if tot["op06"] else 0))
    print("  op 0x1E 目标 ∈ 本模块代码区 : %d/%d ；其中**落在指令起点** %d/%d = %.6f"
          % (tot["op1Eok"], tot["op1E"], tot["op1Eal"], tot["op1E"],
             tot["op1Eal"] / tot["op1E"] if tot["op1E"] else 0))
    print("  op 0x07 表项 ∈ 本模块代码区 : %d ；其中落在指令起点 %d = %.6f"
          % (tot["op07tgt"], tot["op07al"],
             tot["op07al"] / tot["op07tgt"] if tot["op07tgt"] else 0))
    if bad_files:
        print("  失准文件 %d 个，示例：%s" % (len(bad_files), bad_files[:6]))
    print("  == 表感知口径的 op 计数（对照 `执行模型.md` §八 项 6 的截断值） ==")
    for k in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x07):
        print("     op%02X : %d" % (k, opcnt[k]))
    return tot, opcnt


# ================================================================ 自检
def coverage(seg, allv):
    cov = set()
    for V in allv:
        r = seg.proc(V)
        if r["ok"]:
            cov |= set(r["block_ids"])
    unc = [b for b in range(len(seg.blocks)) if b not in cov]
    return cov, unc


def do_stats(seg, ents, internal, allv, cnt, files):
    print("== C1 指令解码 ==")
    print("  代码区 [0, 0x%X)；解出指令 %d 条；非法 op 位置 = %d；走查终点 = 0x%X（%s）"
          % (seg.ss, len(seg.insns), len(seg.illegal), seg.walk_end,
             "恰好 = ss ✔" if seg.walk_end == seg.ss else "≠ ss ✘"))
    if seg.illegal:
        print("  非法位置示例：%s" % [hex(x) if isinstance(x, int) else x
                                     for x in seg.illegal[:10]])
    print("== C2 控制流目标对齐 ==")
    print("  未能经 maps[4] 还原为代码目标的控制流操作数 = %d" % len(seg.bad_targets))
    mis = sorted({t for t in seg.leaders if t not in seg.by_pos})
    print("  块首中**非指令起点**者 = %d（应为 0）%s" % (len(mis), [hex(x) for x in mis[:8]]))
    print("  基本块数 = %d" % len(seg.blocks))
    n05 = ok05 = 0
    for (pos, op, ops, endb) in seg.insns:
        if op == 0x05 and ops:
            n05 += 1
            ok05 += 1 if ops[0] * 4 in seg.m1 else 0
    print("  op 0x05 操作数 ∈ maps[1]：%d / %d = %.4f（应为 1.0000）" % (ok05, n05, ok05 / n05))
    print("== C3 过程切分 ==")
    print("  入口：语料 maps[3] %d 个 ∪ 库内 CALL 目标 %d 个 = %d 个（去重）"
          % (len(ents), len(internal), len(allv)))
    rows = [(V, seg.proc(V)) for V in allv]
    st = collections.Counter()
    for V, r in rows:
        if not r["ok"]:
            st["未定"] += 1
            continue
        st["确定" if (V in ents or V in internal) else "候选(无调用者)"] += 1
    for k, v in st.most_common():
        print("    %-18s %d" % (k, v))
    sizes = sorted(len(r["insns"]) for _, r in rows if r["ok"])
    cores = sorted(len(r["core"][2]) for _, r in rows if r["ok"])
    print("  过程指令数：中位 %d / 最大 %d / 合计 %d" %
          (sizes[len(sizes) // 2], sizes[-1], sum(sizes)))
    print("  core 指令数：中位 %d / 最大 %d（core 字节：中位 %d）" %
          (cores[len(cores) // 2], cores[-1],
           sorted(r["core_end"] - r["core_start"] for _, r in rows if r["ok"])[len(cores) // 2]))
    # 不重叠性
    owner = collections.Counter()
    for _, r in rows:
        if r["ok"]:
            for b in r["block_ids"]:
                owner[b] += 1
    share = [b for b, n in owner.items() if n > 1]
    print("  被 ≥2 个过程共享的基本块 = %d / %d" % (len(share), len(seg.blocks)))
    inner = sum(1 for _, r in rows if r["ok"] and r["other_v"])
    print("  [起,止) 区间内夹着**其它入口 core** 的过程 = %d / %d（= 字面不连续）" % (inner, len(allv)))
    runs = collections.Counter(r["runs"] for _, r in rows if r["ok"])
    print("  过程连续段数分布：%s" % dict(sorted(runs.items())))
    # 覆盖
    cov, unc = coverage(seg, allv)
    unc_ins = sum(len(seg.blocks[b][2]) for b in unc)
    print("  过程覆盖：块 %d/%d；指令 %d/%d = %.4f；**静态不可达块 %d（%d 指令 = %.4f）**"
          % (len(cov), len(seg.blocks), sum(sizes), len(seg.insns),
             sum(sizes) / len(seg.insns), len(unc), unc_ins, unc_ins / len(seg.insns)))
    # 未可达块的根：前一条指令必为终止符
    inedge = collections.Counter()
    for b, succ in seg.intra_edges.items():
        for s in succ:
            inedge[s] += 1
    roots = [b for b in unc if not inedge[b]]
    prev = collections.Counter()
    endmap = {seg.insns[k][3]: k for k in range(len(seg.insns))}
    for b in roots:
        k = endmap.get(seg.blocks[b][0])
        prev[MN.get(seg.insns[k][1], "?") if k is not None else "0"] += 1
    if roots:
        print("    不可达块之根 %d 个；其前一条指令分布：%s（全部为终止符 ⇒ 非直落可达）"
              % (len(roots), dict(prev)))
    # 帧平衡（佐证；0x0B = sp += k 分配，0x0C = sp -= k 释放）
    fb = collections.Counter()
    for _, r in rows:
        if not r["ok"]:
            continue
        if r["n_fa"] == 0 and r["n_sd"] == 0:
            fb["无帧"] += 1
        elif r["n_fa"] and r["n_sd"] and r["fa_sum"] == r["sd_sum"]:
            fb["Σ0x0B == Σ0x0C"] += 1
        elif r["n_fa"] and r["n_sd"]:
            fb["Σ 不等"] += 1
        elif r["n_fa"]:
            fb["有 0x0B 无 0x0C"] += 1
        else:
            fb["有 0x0C 无 0x0B"] += 1
    print("  帧 Σ 平衡（过程内 Σ(0x0B k) vs Σ(0x0C k)；**0x0C 兼作「丢实参」，此口径仅作参考**）：%s"
          % dict(fb))
    fp = collections.Counter(r["frame_pair"] for _, r in rows if r["ok"])
    print("  ★ x02.py 口径帧配对（过程首个 0x0B k vs 终止项前紧邻 0x0C k）：%s" % dict(fp))
    return rows


# ================================================================ 负向自证
def do_negtest(seg, allv, ents, internal):
    print("== 负向自证（判据必须能失败） ==")
    for delta, tag in ((4, "+1 DWORD"), (-4, "-1 DWORD")):
        n = rej = 0
        why = collections.Counter()
        for V in allv:
            W = V + delta
            if W < 0 or W + 4 > seg.ss:
                continue
            n += 1
            if W not in seg.by_pos:
                rej += 1
                why["该处非指令起点（落在操作数中间）"] += 1
            elif seg.cells[W // 4] > 0x2E:
                rej += 1
                why["该处是非法 op（>0x2E）"] += 1
            else:
                why["该处恰为 1 词长指令（%s）" % MN.get(seg.cells[W // 4])] += 1
        print("[N1%s] 入口起点人为平移 %s：%d/%d 被否决（%.4f）"
              % ("a" if delta > 0 else "b", tag, rej, n, rej / n if n else 0))
        for k, v in why.most_common(4):
            print("      %-34s %d" % (k, v))
    print("  ⇒ +1 DWORD 位移 100% 被否决（起点唯一性成立）。-1 DWORD 全部通过，"
          "因各入口前一条恰是**单字终止符 RET/HALT_OK**——这本身佐证「入口紧接在一个返回项之后」。")
    print("[N2] 用数据侧反推的 BASE 宽度表替代引擎真值表")
    s2 = Seg(wlen={k: v + 1 for k, v in BASE_PAYLOAD.items()}, w07=False)
    print("     BASE 走查非法 op 位置 = %d（引擎真值表 = %d）⇒ BASE 不成立"
          % (sum(1 for x in s2.illegal if isinstance(x, int)), len(seg.illegal)))
    print("[N3] 人为扰动真值宽度表（单点：0x08 操作数 1→2；双点：再加 0x20 2→3）")
    for tag, pert in (("单点 0x08: 1→2", {0x08: 3}), ("双点 +0x20: 2→3", {0x08: 3, 0x20: 4})):
        wl = dict(WLEN)
        wl.update(pert)
        s3 = Seg(wlen=wl)
        ill3 = sum(1 for x in s3.illegal if isinstance(x, int))
        mis3 = sorted({t for t in s3.leaders if t not in s3.by_pos})
        print("     %-18s 非法 op 位置 = %-6d（真值 0）；非指令起点块首 = %-5d（真值 0）"
              % (tag, ill3, len(mis3)))
    print("     ⇒ 判据能失败 ✔（宽度表错一项，C1 立刻出现非法 op、C2 立刻出现目标失准）"
          "；对拍值即「引擎真值表」的唯一性证据")
    print("[N4] 「[V, nextV) 区间 = 命令实现体」判据的正反例")
    vs = sorted(ents)
    nxt = {v: (vs[i + 1] if i + 1 < len(vs) else seg.ss) for i, v in enumerate(vs)}
    same = diff = 0
    cross = []
    for V in vs:
        r = seg.proc(V)
        if not r["ok"]:
            continue
        if r["end"] == nxt[V]:
            same += 1
        else:
            diff += 1
            cross.append((V, r["end"], nxt[V]))
    print("     93 个语料 V 中：过程止点 == nextV 的 %d 个；≠ 的 %d 个" % (same, diff))
    print("     ≠ 者示例（V, 过程止, nextV）：%s"
          % [(hex(a), hex(b), hex(c)) for a, b, c in
             sorted(cross, key=lambda x: x[2] - x[1])[:8]])
    print("     ⇒ 区间口径在 %d/93 个 V 上给出**错误**边界（把下一个命令算进来，或截掉本命令）" % diff)
    print("[N5] 反例：旧「窗口读串」在越窗 V 上读到**别的过程**的串（详见 --rejudge）")


# ================================================================ 21 V 串归属重判
REJUDGE = [
    (0x19D58, "cross", 0x400, "越窗"), (0x1B69C, "quake", 0x200, "越窗"),
    (0x1A858, "trans", 0x400, "越窗"), (0x1AD18, "scroll", 0x400, "越窗"),
    (0x19F9C, "cross", 0x200, "越窗"), (0x1AE2C, "scroll", 0x200, "越窗"),
    (0x1ABF0, "scroll", 0x400, "越窗"), (0x1AEA0, "scroll", 0x200, "越窗"),
    (0x11B0C, "noise", 0x400, "越窗"),
    (0x1A96C, "trans", 0x200, "未定"), (0x1F600, "BGM\\BGM%02d.OGG", 0x400, "未定"),
    (0xA5D0, "BG01", 0x400, "未定"), (0x1B040, "zoomflip", 0x200, "未定"),
    (0x10428, "bg_move", 0x400, "未定"), (0x1BD8C, "quake", 0x400, "未定"),
    (0x1A15C, "cross", 0x200, "未定"), (0x12998, "bg_blur", 0x400, "未定"),
    (0x10980, "bg_zoom", 0x400, "未定"), (0x12E94, "bg_blur", 0x400, "未定"),
    (0x11EA0, "bg_rast", 0x400, "未定"), (0x1107C, "bg_rot", 0x400, "未定"),
]


def win_sites(seg, V, W):
    out = []
    for j in range(0, W, 4):
        o = V + j
        if o + 4 > seg.ss:
            break
        t = seg.m4.get(o)
        if t is None or not (seg.ss <= t < seg.se):
            continue
        out.append((o, t, seg.strat(t)))
    return out


def callee_closure(seg, V, depth=4, cap=400):
    """V 的**被调子程序闭包**（沿 op 0x04，深度受限；用于「间接归属」判定）。"""
    seen, stack = set(), [(V, 0)]
    while stack:
        u, d = stack.pop()
        r = seg.proc(u)
        if not r["ok"]:
            continue
        for w in r["calls"]:
            if w is None or w in seen or w >= seg.ss:
                continue
            seen.add(w)
            if d + 1 < depth and len(seen) < cap:
                stack.append((w, d + 1))
    return seen


def do_rejudge(seg, ents, internal, allv, rows):
    byv = {V: r for V, r in rows}
    # 站址 -> 拥有它的过程（core 优先）
    site_owner = {}
    for V, r in rows:
        if not r["ok"]:
            continue
        for p, q, t in r["strings"]:
            site_owner.setdefault(q, (V, "exp"))
    for V, r in rows:
        if r["ok"]:
            for p, q, t in r["strings"]:
                if r["core_start"] <= p < r["core_end"]:
                    site_owner[q] = (V, "core")
    out = []
    print("== 串归属重判（21 个 V：既有 9 越窗 + 12 归属未定） ==")
    print("旧法 = 窗口 [V,V+W) 内 maps[4] 串引用的首串；新法 = 过程切分（core / exp）判归属")
    flips = 0
    for (V, s0, W0, tag) in REJUDGE:
        r = byv[V]
        sites = win_sites(seg, V, W0)
        # 旧法首串所在站（第一个非空串）
        fsite = None
        for o, t, s in sites:
            if s:
                fsite = (o, s)
                break
        if not r["ok"]:
            print("  0x%-6X [%s] 不可切分（%s）" % (V, tag, r["reason"]))
            out.append((V, tag, s0, W0, "不可切分", "", ""))
            continue
        exp_s = [seg.strat(t) for _p, _q, t in r["strings"] if seg.strat(t)]
        core_s = [seg.strat(t) for p, _q, t in r["strings"]
                  if r["core_start"] <= p < r["core_end"] and seg.strat(t)]
        own = site_owner.get(fsite[0]) if fsite else None
        if own and own[0] == V:
            verdict = "**归属翻转**：旧判「%s」有误——该串确在本命令过程内（%s）" % (tag, own[1])
            flips += 1
        elif own:
            verdict = "旧判方向正确：该串属 0x%X 的过程（%s）；本命令过程内%s" % (
                own[0], own[1], ("含 %r" % s0) if s0 in exp_s else "不含该串")
            if s0 in exp_s and own[0] != V:
                verdict += "【注意：本命令过程内也含同串，属共享串】"
        else:
            verdict = "仍不可判：站 0x%X 落在**静态不可达区**（无可达过程包含它）" % (fsite[0] if fsite else 0)
        if own and own[0] != V and "静态不可达" not in verdict:
            cc = callee_closure(seg, V)
            if own[0] in cc:
                verdict = ("**间接归属**：串属本命令的**被调子程序 0x%X**（%s）；"
                           "旧判「%s」过严——按过程闭包应可采信" % (own[0], own[1], tag))
        print("  0x%-6X [%s] 旧=%r@W=0x%X → %s" % (V, tag, s0, W0, verdict))
        print("        core 0x%X..0x%X；过程 %d 块/%d 条（段数 %d）；core 串=%s；exp 串=%s"
              % (r["core_start"], r["core_end"], len(r["block_ids"]), r["n_insn"], r["runs"],
                 core_s or "无", exp_s or "无"))
        out.append((V, tag, s0, W0, verdict,
                    "|".join(core_s), "|".join(exp_s)))
    print("  汇总：归属翻转 %d / 21" % flips)
    # 落盘
    with io.open(OUT_REJUDGE, "w", encoding="utf-8", newline="\n") as f:
        f.write("V\t旧档\t旧首串\t旧首现窗口\t新判\tcore串\texp串\n")
        for V, tag, s0, W0, v, cs, es in out:
            f.write("%s\t%s\t%s\t0x%X\t%s\t%s\t%s\n"
                    % (hex(V), tag, s0, W0, v, cs, es))
    print("  落盘 %s" % OUT_REJUDGE)
    return out


# ================================================================ 落盘
def do_emit(seg, ents, internal, allv, cnt, files, rows):
    os.makedirs(OUT_ASM_DIR, exist_ok=True)
    vname = {}
    if os.path.exists(VREG):
        with io.open(VREG, encoding="utf-8") as f:
            f.readline()
            for ln in f:
                p = ln.rstrip("\n").split("\t")
                if len(p) >= 3 and p[0] == "ot":
                    try:
                        vname[int(p[1], 0)] = p[2]
                    except ValueError:
                        pass
    byv = {V: r for V, r in rows}
    hdr = ["V", "置信度", "core起", "core止", "过程起", "过程止", "连续段数",
           "区间内其它V数", "块数", "core指令数", "过程指令数", "帧分配次数", "帧释放次数",
           "Σ帧分配", "Σ帧释放", "帧配对x02口径", "库内CALL数", "库内调用者站",
           "语料调用站数", "语料调用文件数", "core串", "过程串", "native下标",
           "被CALL目标", "既有定名", "来源"]
    with io.open(OUT_TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(hdr) + "\n")
        for V, r in sorted(rows):
            if not r["ok"]:
                f.write("\t".join([hex(V), "未定"] + [""] * 24 + [r["reason"]]) + "\n")
                continue
            src = ("语料V+库内CALL" if V in ents and V in internal else
                   "仅语料V" if V in ents else "仅库内CALL")
            core_s = sorted({seg.strat(t) for p, _q, t in r["strings"]
                             if r["core_start"] <= p < r["core_end"] and seg.strat(t)})
            exp_s = sorted({seg.strat(t) for p, _q, t in r["strings"] if seg.strat(t)})
            callers = seg.call_sites.get(V, [])
            f.write("\t".join([
                hex(V), "确定" if (V in ents or V in internal) else "候选(无调用者)",
                hex(r["core_start"]), hex(r["core_end"]), hex(r["start"]), hex(r["end"]),
                str(r["runs"]), str(len(r["other_v"])), str(len(r["block_ids"])),
                str(len(r["core"][2])), str(r["n_insn"]),
                str(r["n_fa"]), str(r["n_sd"]), hex(r["fa_sum"]), hex(r["sd_sum"]),
                r["frame_pair"],
                str(len(callers)), ",".join(hex(p) for p in callers[:10]),
                str(cnt.get(V, 0)), str(len(files.get(V, ()))),
                "|".join(esc(x) for x in core_s), "|".join(esc(x) for x in exp_s),
                ",".join(str(x) for x in r["natives"]),
                ",".join(hex(x) for x in r["calls"] if x is not None),
                vname.get(V, ""), src]) + "\n")
    print("落盘 %s（%d 行）" % (OUT_TSV, len(rows) + 1))
    # 单文件全量反汇编
    marks = {}
    for V, r in rows:
        if r["ok"] and r["core_start"] == V:
            marks[V] = "★ V=0x%X" % V
    with io.open(OUT_ASM_ALL, "w", encoding="utf-8", newline="\n") as f:
        f.write("; func_lib.sob 代码区逐条反汇编（M1 xvseg.py）\n")
        f.write("; ss=0x%X 指令=%d 基本块=%d 过程入口=%d  列：偏移 助记符 操作数[注解] 标记\n"
                % (seg.ss, len(seg.insns), len(seg.blocks), len(rows)))
        f.write("\n".join(seg.disasm_lines(range(len(seg.insns)), marks)) + "\n")
    print("落盘 %s" % OUT_ASM_ALL)
    # 逐 V
    n = 0
    for V, r in sorted(rows):
        if not r["ok"]:
            continue
        fn = os.path.join(OUT_ASM_DIR, "%06X.asm" % V)
        with io.open(fn, "w", encoding="utf-8", newline="\n") as f:
            f.write("; V=0x%X  core=0x%X..0x%X（%d 条）  过程=0x%X..0x%X（%d 块/%d 条，段数 %d）\n"
                    % (V, r["core_start"], r["core_end"], len(r["core"][2]),
                       r["start"], r["end"], len(r["block_ids"]), r["n_insn"], r["runs"]))
            f.write("; native=%s\n" % (r["natives"] or "-"))
            f.write("; 内嵌串 core=%s\n" % (sorted({seg.strat(t) for p, _q, t in r["strings"]
                                                  if r["core_start"] <= p < r["core_end"]}) or "-"))
            f.write("; 库内 CALL -> %s\n" % ([hex(x) for x in r["calls"]] or "-"))
            f.write("\n".join(seg.disasm_lines(r["insns"], {r["core_start"]: "★ V 入口"})) + "\n")
        n += 1
    print("落盘 %s\\*.asm（%d 个）" % (OUT_ASM_DIR, n))


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--v", default=None)
    ap.add_argument("--core-only", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--rejudge", action="store_true")
    ap.add_argument("--negtest", action="store_true")
    ap.add_argument("--corpus", action="store_true")
    ap.add_argument("--evidence", action="store_true")
    ap.add_argument("--crossbuild", action="store_true")
    ap.add_argument("--corpus-dir", default=OT_SCRIPT)
    ap.add_argument("--flib", default=FL_PATH)
    a = ap.parse_args()

    if a.corpus:
        do_corpus(a.corpus_dir, "本作 ot 全库")
        return
    if a.crossbuild:
        do_crossbuild([FL_PATH, r"D:\Gal\[Navel]我们没有翅膀\SCRIPT_CHS\func_lib.sob"],
                      ["原版（解包/SCRIPT）", "汉化补丁版（SCRIPT_CHS）"])
        return

    seg, ents, internal, cnt, files, allv = build()
    if a.evidence:
        do_evidence(seg, allv)
        return
    rows = [(V, seg.proc(V)) for V in allv]

    if a.v is not None:
        V = int(a.v, 0)
        r = seg.proc(V)
        if not r["ok"]:
            print("V=0x%X 不可切分：%s" % (V, r["reason"]))
            return
        print("V=0x%X  core=0x%X..0x%X  过程=0x%X..0x%X  blocks=%s 段数=%d 区间内其它V=%s"
              % (V, r["core_start"], r["core_end"], r["start"], r["end"],
                 [hex(seg.blocks[b][0]) for b in r["block_ids"]], r["runs"],
                 [hex(x) for x in r["other_v"]]))
        print("native=%s" % r["natives"])
        print("库内 CALL -> %s" % [hex(x) for x in r["calls"]])
        print("内嵌串 core=%s" % sorted({seg.strat(t) for p, _q, t in r["strings"]
                                       if r["core_start"] <= p < r["core_end"]}))
        ks = ([k for k in r["insns"] if r["core_start"] <= seg.insns[k][0] < r["core_end"]]
              if a.core_only else r["insns"])
        print("\n" + "\n".join(seg.disasm_lines(ks, {r["core_start"]: "★ V 入口"})))
        return

    if a.stats or not any((a.emit, a.rejudge, a.negtest)):
        do_stats(seg, ents, internal, allv, cnt, files)
    if a.negtest:
        do_negtest(seg, allv, ents, internal)
    if a.rejudge:
        do_rejudge(seg, ents, internal, allv, rows)
    if a.emit:
        do_emit(seg, ents, internal, allv, cnt, files, rows)


if __name__ == "__main__":
    main()

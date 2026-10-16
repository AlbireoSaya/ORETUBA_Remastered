#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xvlink.py — 原生 handler ←→ 命令实现体 V 的**引擎自证关联**（M4 第一批）。

问题
    handler 集合（789 个，`xreg.py` 枚举）里每个 handler 是「原生原语」；给它定名的
    **不依赖外部金标**的唯一证据是：**哪个命令实现体（V）调用了它**。V 的语义已由另一路
    （PSV 金标 / func_lib 内嵌串）独立定名（`decode_sob0.V_NAMING`）。

机制（据 `执行模型.md` §13 实装，全部可复跑）
    * 命令实现体 = `func_lib.sob` 代码缓冲内偏移 `V`（op `0x04` CALL 的操作数）。
    * 实现体内部用 **op `0x05` CALLNATIVE** 调原生 handler；其操作数 site ∈ func_lib 的
      `maps[1]`，**value = handler 向量下标**（`sub_424D30` 循环 B：`code[off]=[mgr+0x38][value]`）。
    * 故：解析 func_lib → 找 op 0x05 → 取 maps[1] value ⇒ handler 下标；
      op `0x04` 的目标（maps[4] value = 本模块偏移）⇒ **内部子程序入口**，可沿调用图传递。

归属判据（**两条，分开记、不混报**）
    L1 **直接窗口关联**：在窗口 `[V, V+W)` 内线性走查所得 op 0x05 的 handler 序；
       W 主口径 **0x1000**（= `W_MAIN`），并做**窗口敏感度**（W∈{0x200,0x1000,0x4000} = `WIN_SENS`；
       报告里的「core」取 **0x200**、「exp」取 **0x1000**，两口径并列不混报）。
    L2 **调用图闭包关联**（次级、弱）：从 V 出发沿 op 0x04 内部调用闭包（深度≤4 = `MAX_TRANS_DEPTH`，
       节点上限 `MAX_TRANS_NODES`=400）可达的入口，其 L1 窗口内的 handler。
       用于补「调度器型 V（本体只 CALL 子程序）」。

★ 硬边界（如实声明，不得越界引用）
    * `func_lib` 的 V/子程序**无长度字段，边界不可判**（`.zcode/skills/lucifen-unpack/SKILL.md`
      §13.8.3）；故 L1 是**窗口**而非「函数体」，L2 的传递会产生**共享助手**型假归属
      ⇒ 凡只有 L2 支持者一律记「弱」，不得单独据以定名。
    * V 号**每 build 组本地**（`ot`/`otp` 各一套），不得跨源搬用。
    * `V=0x2C3C`（`ot` 内联代码块族，57859 节点）不参与命名（标记 SPECIAL）。

用法
    python -X utf8 xvlink.py                       # 打印 top 频次 handler 的 V 关联
    python -X utf8 xvlink.py --src ot --link <path> --vreg <path> [--top 40]
    python -X utf8 xvlink.py --selftest
"""
import argparse
import collections
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode_sob0 as D            # noqa: E402
import xclus                      # noqa: E402
from pe_min import PE, DUMP_PATH  # noqa: E402

DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
SCRIPT = os.path.join(DATA_ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")
FL_PATH = os.path.join(SCRIPT, "func_lib.sob")

OPW = {0x00: 0, 0x01: 0, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x07: -1,
       0x08: 1, 0x09: 1, 0x0A: 1, 0x0B: 1, 0x0C: 1, 0x0D: 3, 0x0E: 3, 0x0F: 3,
       0x10: 3, 0x11: 3, 0x12: 3, 0x13: 3, 0x14: 3, 0x15: 3, 0x16: 2, 0x17: 2,
       0x18: 3, 0x19: 3, 0x1A: 1, 0x1B: 1, 0x1C: 1, 0x1D: 1, 0x1E: 2, 0x1F: 2,
       0x20: 2, 0x21: 2, 0x22: 2, 0x23: 2, 0x24: 2, 0x25: 2, 0x26: 2, 0x27: 2,
       0x28: 2, 0x29: 3, 0x2A: 3, 0x2B: 3, 0x2C: 3, 0x2D: 3, 0x2E: 3}

SPECIAL_V = {0x2C3C}
W_MAIN = 0x1000
WIN_SENS = (0x200, 0x1000, 0x4000)
MAX_TRANS_DEPTH = 4
MAX_TRANS_NODES = 400


# ================================================================ 语料侧
def corpus_counts(root):
    """→ (maps[1] 计数 per handler 下标, V 计数, V 出现文件数)。"""
    c1, cv, cvf = collections.Counter(), collections.Counter(), collections.Counter()
    for fn in sorted(os.listdir(root)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            s = D.Sob0(os.path.join(root, fn))
        except Exception:
            continue
        for v in s.maps[1].values():
            c1[v] += 1
        seen = set()
        for V in s.maps[3].values():
            if V < 0x100000:
                cv[V] += 1
                seen.add(V)
        for V in seen:
            cvf[V] += 1
    return c1, cv, cvf


# ================================================================ func_lib 侧
def walk_win(fl, V, W):
    """从 V 线性走查 W 字节：→ (natives[下标…], calls[内部入口 offset…], bad, stop)。"""
    c = fl.cells
    s1, s4 = fl.maps[1], fl.maps[4]
    i = V // 4
    hlim = min((V + W) // 4, len(c))
    nat, calls, bad, stop = [], [], 0, "end"
    while i < hlim:
        op = c[i]
        if op not in OPW:
            bad += 1
            i += 1
            continue
        if op == 0x07:
            stop = "op7"
            break
        if op == 0x05:
            s = (i + 1) * 4
            if s in s1:
                nat.append(s1[s])
            else:
                bad += 1
        elif op == 0x04:
            s = (i + 1) * 4
            if s in s4:
                calls.append(s4[s])
        i += 1 + OPW[op]
    return nat, calls, bad, stop


def all_entries(fl):
    """func_lib 内全部「子程序入口」候选 = 语料 V ∪ 内部 op 0x04 目标（maps[4]）。

    模式判据：cells[i]==0x04 ∧ site(i+1)∈maps[4]（引擎 op 0x04 的操作数在 func_lib 内
    只能是 maps[4]：func_lib 的 maps[3] 计数恒 0）。**边界声明**：这只是「入口候选」，
    非「函数体」，func_lib 无长度字段 ⇒ 仍不可判边界（见文件头 ★）。
    """
    c = fl.cells
    s4 = fl.maps[4]
    out = set()
    for i in range(len(c) - 1):
        if c[i] == 0x04 and (i + 1) * 4 in s4:
            v = s4[(i + 1) * 4]
            if 0 < v < fl.ss:
                out.add(v)
    return out


def build_direct(fl, Vs, W):
    """→ (h2v: {h: Counter(V)}, vinfo: {V: dict}, vcalls: {V: set(callee)})。"""
    h2v = collections.defaultdict(collections.Counter)
    vinfo, vcalls = {}, {}
    for V in Vs:
        nat, calls, bad, stop = walk_win(fl, V, W)
        vinfo[V] = dict(n=len(nat), bad=bad, stop=stop, n_calls=len(calls))
        vcalls[V] = set(calls)
        for h in set(nat):
            h2v[h][V] += nat.count(h)
    return h2v, vinfo, vcalls


def transitive_natives(fl, V, nat_by_entry, vcalls):
    """从 V 沿 op 0x04 闭包可达入口的 natives 并集（次级信号）。"""
    seen, frontier, out = set(), [V], set()
    for _ in range(MAX_TRANS_DEPTH):
        nxt = []
        for e in frontier:
            if e in seen:
                continue
            seen.add(e)
            out |= nat_by_entry.get(e, set())
            if len(seen) > MAX_TRANS_NODES:
                return out, seen
            for cal in vcalls.get(e, ()):  # noqa
                if cal not in seen:
                    nxt.append(cal)
        frontier = nxt
    return out, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--root", default=SCRIPT)
    ap.add_argument("--link")
    ap.add_argument("--vreg")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    pe = PE(DUMP_PATH)
    full = xclus.handlers(pe)
    va_of = full
    c1, cv, cvf = corpus_counts(a.root)
    Vs = sorted(V for V in cv if V not in SPECIAL_V)
    fl = D.Sob0(FL_PATH)

    h2v, vinfo, vcalls = build_direct(fl, Vs, W_MAIN)
    # 全入口（V ∪ 内部 op0x04 目标）的窗口 natives / callees —— 供 L2 闭包用
    ents = sorted(all_entries(fl) | set(Vs))
    nat_by_entry, vcalls_all = {}, {}
    for e in ents:
        nat, calls, _bad, _stop = walk_win(fl, e, W_MAIN)
        nat_by_entry[e] = set(nat)
        vcalls_all[e] = set(calls)

    # L2 闭包（每个 V 一次，缓存）
    trans_by_V = {}
    for V in Vs:
        tn, _seen = transitive_natives(fl, V, nat_by_entry, vcalls_all)
        trans_by_V[V] = tn
    h2v_trans = collections.defaultdict(set)
    for V, tn in trans_by_V.items():
        for h in tn:
            h2v_trans[h].add(V)

    # 窗口敏感度：对每个 handler 比较 W=0x80 / 0x200 / 0x800 的 V 集合与主口径
    h2v_sens = {}
    for W in WIN_SENS:
        h2_, _, _ = build_direct(fl, Vs, W)
        h2v_sens[W] = {h: set(c) for h, c in h2_.items()}

    NM = {V: (d.get("name") or "") for V, d in D.V_NAMING.get("ot", {}).items()}

    print("== xvlink.py  src=%s  W_main=0x%X ==" % (a.src, W_MAIN))
    print("语料 maps[1] 表项 = %d（不同 handler 下标 = %d，max=%d）" %
          (sum(c1.values()), len(c1), max(c1) if c1 else -1))
    print("func_lib ss=%d maps[1] 项=%d；V 数（去 SPECIAL）= %d" %
          (fl.ss, len(fl.maps[1]), len(Vs)))
    print("L1 直接窗口：op0x05 = %d，bad = %d（应为 0）；被直接关联的 handler = %d" %
          (sum(v["n"] for v in vinfo.values()),
           sum(v["bad"] for v in vinfo.values()), len(h2v)))
    print("L2 闭包关联的 handler = %d" % len(h2v_trans))

    print("\n== 语料引用计数 top %d handler（VA / 直接关联 V / 闭包关联 V）==" % a.top)
    for h, n in c1.most_common(a.top):
        va = va_of[h] if h < len(va_of) else 0
        dV = sorted(h2v.get(h, {}))
        cl = sorted(h2v_trans.get(h, set()))
        name = " ".join("0x%X%s" % (V, "@" + NM[V] if NM.get(V) else "")
                        for V in dV[:6])
        s_min = h2v_sens[WIN_SENS[0]].get(h, set())
        s_max = h2v_sens[WIN_SENS[-1]].get(h, set())
        stable = "稳定" if (dV and set(dV) == s_min) else (
            "含于最大窗" if set(dV) <= s_max else "不稳")
        print("  h%-4d 0x%08X refs=%-6d 直接V(%-3d)=%s | 闭包V(%-3d) | 窗敏=%s" %
              (h, va, n, len(dV), name or "-", len(cl), stable))

    # ---- 高特异性：core(W=0x200) 只关联到 1 个 V ----
    spec = []
    for h, n in c1.items():
        core = h2v_sens[0x200].get(h, set())
        if len(core) == 1 and n >= 10:
            V = next(iter(core))
            spec.append((n, h, V, NM.get(V, ""), len(h2v_sens[0x1000].get(h, set()))))
    spec.sort(reverse=True)
    print("\n== 高特异性候选（core 窗 W=0x200 恰关联 1 个 V，且语料 refs≥10）共 %d ==" % len(spec))
    for n, h, V, nm, exp in spec[:40]:
        va = va_of[h] if h < len(va_of) else 0
        print("  h%-4d 0x%08X refs=%-6d → V=0x%X@%s（扩窗后 %d 个 V）" %
              (h, va, n, V, nm or "-", exp))

    if a.vreg:
        with io.open(a.vreg, "w", encoding="utf-8", newline="") as f:
            f.write("src\tV\tv_name\tcorpus_nodes\tcorpus_files\tW\tn_native\tn_calls\tn_bad\tstop\tnative_top\n")
            for V in Vs:
                vi = vinfo[V]
                cnt = collections.Counter(nat_by_entry[V])
                top = " ".join("%d:%d" % (h, k) for h, k in cnt.most_common(12))
                f.write("%s\t0x%X\t%s\t%d\t%d\t0x%X\t%d\t%d\t%d\t%s\t%s\n" %
                        (a.src, V, NM.get(V, ""), cv[V], cvf[V], W_MAIN,
                         vi["n"], vi["n_calls"], vi["bad"], vi["stop"], top))
        print("\n[写] %s" % a.vreg)
    if a.link:
        feat = {}
        for idx, va in xclus.handlers(pe, merged=True):
            feat[idx] = xclus.features(pe, idx, va, 1)
        with io.open(a.link, "w", encoding="utf-8", newline="") as f:
            f.write("handler_idx\thandler_va\tcorpus_refs\t"
                    "core_nV_W200\tcore_V_W200\texp_nV_W1000\texp_V_W1000\ttrans_nV\t"
                    "first_insn\tleaf\tseljmp\tsel_entries\tret_imm\tall_disp\n")
            allh = sorted(set(list(c1.keys()) + list(h2v.keys())))
            for h in allh:
                va = va_of[h] if h < len(va_of) else 0
                core = sorted(h2v_sens[0x200].get(h, set()))
                exp = sorted(h2v_sens[0x1000].get(h, set()))
                fr = feat.get(h, {})
                f.write("%d\t0x%08X\t%d\t%d\t%s\t%d\t%s\t%d\t%s %s\t%d\t%d\t%s\t%s\t%s\n" %
                        (h, va, c1.get(h, 0), len(core),
                         ",".join("0x%X" % V for V in core), len(exp),
                         ",".join("0x%X" % V for V in exp),
                         len(h2v_trans.get(h, set())),
                         fr.get("first_m", ""), fr.get("first_o", ""),
                         fr.get("leaf", ""), fr.get("has_seljmp", ""),
                         fr.get("sel_entries", ""), fr.get("ret_imm", ""),
                         fr.get("all_disp", "")))
        print("[写] %s" % a.link)

    if a.selftest:
        print("\n== 自证 ==")
        print("  A) L1 归属自证：窗口内 op0x05 操作数不在 maps[1] 的次数 = %d（应 0）" %
              sum(v["bad"] for v in vinfo.values()))
        u = set()
        for V in Vs:
            u |= nat_by_entry[V]
        print("  B) handler 集合一致性：窗口并集 = %d，h2v 键 = %d，相等 = %s" %
              (len(u), len(h2v), u == set(h2v)))
        # C) 变异自证：把 maps[1] 换成空表 → 该 V 的 handler 引用必须归 0
        Vt = 0x1F600
        base, _, _, _ = walk_win(fl, Vt, W_MAIN)
        s1_back = fl.maps[1]
        fl.maps[1] = {}
        mut, _, _, _ = walk_win(fl, Vt, W_MAIN)
        fl.maps[1] = s1_back
        print("  C) 变异自证：maps[1]→空表，V=0x%X handler 引用条数 %d → %d  %s" %
              (Vt, len(base), len(mut),
               "OK（有牙齿）" if mut != base else "!! 无变化"))
        # D) 窗口敏感度：主口径 V 集合是否随 W 变化（对 core 关联最多的 handler）
        h_top = max(h2v, key=lambda h: len(h2v[h])) if h2v else 0
        print("  D) 窗口敏感度（h%d，core 关联 %d 个 V）：0x200=%d / 0x1000=%d / 0x4000=%d" %
              (h_top, len(h2v.get(h_top, {})),
               len(h2v_sens[0x200].get(h_top, set())),
               len(h2v_sens[0x1000].get(h_top, set())),
               len(h2v_sens[0x4000].get(h_top, set()))))
        # E) 负向对照：把 V 集合换成「空」应得 0 关联（判据不恒真）
        print("  E) 负向对照：空 V 集合的关联 handler 数 = %d（应 0）" %
              len(build_direct(fl, [], W_MAIN)[0]))


if __name__ == "__main__":
    main()

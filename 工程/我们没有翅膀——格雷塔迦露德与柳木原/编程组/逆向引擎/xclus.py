#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xclus.py — 789 个原生 handler 的**自动聚类**（判据全部机器可判、可复跑、可失败）。

来源（沿用，不重造）：
  * handler 集合与注册顺序 = `xreg.py` 同款枚举
    （`.text` 内 `68 <handler_VA> 8B CE E8 <rel→0x422730>`，798 个调用点、去重 789 个）。
  * 首指令档 = `xhand.py` 同款 8 类（判据见该文件头）。

本脚本新增（相对 xhand.py）：逐 handler 的**结构特征**与**聚类轴**（见下），
  **不做任何「前 N 句」扫描**；所有判据写死在本文件，逐格可复现。

判据（全部写死；每轴各给「成员数 + 判据」，互不替代）：
  A 首指令 (mnemonic, op_str) 全等（capstone 5.0.7 原样）
  B 形态档（xhand 8 类）
  C 纯 getter：体恰 2 通道指令 `mov r32, dword ptr [r32(+disp)]` + `ret`（无 imm）
  D 纯 setter：体恰 2 通道指令 `mov dword ptr [r32(+disp)], r32` + `ret`
  E 含 `ret imm16`（stdcall 收参 → 直接给出**该原语的参数个数**）
  F 含 selector 分派：`jmp dword ptr [reg*4 + imm]`（表项数 = 表内落在 .text 的 VA 个数）
  G 体含直接 `call`（n_direct_calls）
  H 尾部 `jmp`（末指令是 `jmp`，即尾调用 / trampoline）
  I 触达 app 单例全局（`[0x503248]`）／次全局（`[0x503258]`）／SEH（`fs:[0]`）
  J 触达脚本管理器（`[reg+0x19C8]`）
  K `[ecx+disp]` 偏移族（**逐偏移计数**；仅 base=ecx）
  L 体长（到首个 `ret/retf` 的指令数；600 上限，超限记 no_ret）

用法：
  python -X utf8 xclus.py                    # 打印聚类表 + 各轴类计数
  python -X utf8 xclus.py --tsv <path>       # 另写逐 handler 特征表 TSV
  python -X utf8 xclus.py --summary <path>   # 另写各轴类计数 TSV
  python -X utf8 xclus.py --selftest         # 判据区分力自证（变异打废 → 计数必须变）
"""
import argparse
import collections
import io
import re
import sys

import capstone

from pe_min import PE, DUMP_PATH

CAPSTONE_VER = capstone.__version__
REG_VA = 0x422730
BACK = 64
MAXI = 600                      # 体长上限（指令数）；超出记 no_ret
MAXSHOW = 20                    # 每轴最多打印的类数

APP_SINGLETON = 0x503248
SUB_GLOBAL = 0x503258
MGR_FIELD = 0x19C8

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

# `mov eax, dword ptr [ecx + 0xD4]` / `mov eax, dword ptr [ecx]`
RE_GET = re.compile(r"^(e[a-d]x|e[sd]i|e[bp]x|ecx|edx|esi|edi|ebx|ebp), "
                    r"dword ptr \[(e[a-d]x|e[sd]i|e[bp]x)\]$|"
                    r"^(e[a-d]x|e[sd]i|e[bp]x|ecx|edx|esi|edi|ebx|ebp), "
                    r"dword ptr \[(e[a-d]x|e[sd]i|e[bp]x) \+ (0x[0-9a-f]+|\d+)\]$",
                    re.I)
RE_GET2 = re.compile(r"^(e[a-d]x|e[sd]i|e[bp]x), dword ptr \[(e[a-d]x|e[sd]i|e[bp]x)"
                     r"( \+ (0x[0-9a-f]+|\d+))?\]$", re.I)
RE_SET2 = re.compile(r"^dword ptr \[(e[a-d]x|e[sd]i|e[bp]x)( \+ (0x[0-9a-f]+|\d+))?\], "
                     r"(e[a-d]x|e[sd]i|e[bp]x)$", re.I)
RE_DISP = re.compile(r"\[(e[a-d]x|e[sd]i|e[bp]x)( \+ (0x[0-9a-f]+|\d+))?\]", re.I)
RE_SELJMP = re.compile(r"^dword ptr \[(e[a-d]x|e[sd]i|e[bp]x)\s*\*\s*4 \+ (0x[0-9a-f]+)\]$",
                       re.I)
RE_ARG = re.compile(r"^(e[a-d]x|e[sd]i|e[bp]x|ecx|edx|esi|edi|ebx|ebp), "
                    r"dword ptr \[esp \+ 4\]$", re.I)
RE_SEL_LOAD = re.compile(r"^(e[a-d]x|e[sd]i|e[bp]x), dword ptr \[(e[a-d]x|e[sd]i|e[bp]x|ecx|edx|esi|edi|ebx|ebp)\]$",
                         re.I)
RE_CMP = re.compile(r"^(e[a-d]x|e[sd]i|e[bp]x|ecx|edx|esi|edi|ebx|ebp), (0x[0-9a-f]+|\d+)$", re.I)
RE_CALLREG = re.compile(r"^dword ptr \[0x", re.I)


def _imm(op_str):
    m = re.search(r"0x([0-9a-f]+)", op_str)
    return int(m.group(1), 16) if m else None


def _disp(op_str):
    m = RE_DISP.search(op_str)
    if not m:
        return None
    d = m.group(3)
    return int(d, 16) if d and d.lower().startswith("0x") else (int(d) if d else 0)


def handlers(pe, merged=False):
    """→ [(vec_index, handler_va, n_reg)]：注册顺序 = 向量顺序（前 3 个为 ctor 登记）。"""
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    lo, hi = va0, va0 + len(code)
    seq = []
    for m in re.finditer(rb"\xe8(....)", code, re.S):
        o = m.start()
        rel = int.from_bytes(m.group(1), "little")
        if va0 + o + 5 + rel != REG_VA:
            continue
        for p in range(o - 1, max(-1, o - BACK), -1):
            if code[p] == 0x68 and p + 7 <= o and code[p + 5:p + 7] == b"\x8b\xce":
                h = int.from_bytes(code[p + 1:p + 5], "little")
                if lo <= h < hi:
                    seq.append(h)
                break
    ctor = [0x4221D0, 0x4221B0, 0x4221F0]
    full = ctor + seq                      # 向量下标 0..(3+len(seq)-1)
    if not merged:
        return full
    # 去重（保首个下标）
    seen = {}
    for i, h in enumerate(full):
        seen.setdefault(h, i)
    return [(i, h) for h, i in sorted(seen.items(), key=lambda kv: kv[1])]


def body(pe, va):
    """从 va 反汇编到首个 ret/retf（含），或 MAXI 条。→ (insns, term)。"""
    off = pe.rva_to_off(va - pe.image_base)
    out = []
    for ins in md.disasm(pe.data[off:off + MAXI * 8], va):
        out.append(ins)
        if ins.mnemonic in ("ret", "retf"):
            return out, ins.mnemonic
        if len(out) >= MAXI:
            return out, "no_ret"
    return out, "no_ret"


def table_entries(pe, va, limit=64):
    """跳转表（.text 内 VA 数组）项数；遇非 .text VA 即停。"""
    off = pe.rva_to_off(va - pe.image_base)
    if off is None:
        return 0
    lo = pe.image_base + [s for s in pe.sections if s["name"] == ".text"][0]["vaddr"]
    hi = lo + [s for s in pe.sections if s["name"] == ".text"][0]["rawsize"]
    n = 0
    for i in range(limit):
        v = int.from_bytes(pe.data[off + 4 * i:off + 4 * i + 4], "little")
        if not (lo <= v < hi):
            break
        n += 1
    return n


def features(pe, idx, va, n_reg):
    insns, term = body(pe, va)
    f = dict(vec_index=idx, va="0x%08X" % va, n_reg=n_reg,
             first_m=insns[0].mnemonic if insns else "",
             first_o=insns[0].op_str if insns else "",
             n_insn=len(insns), term=term)
    # C/D 纯 getter/setter（体恰 2 条）
    f["pure_getter"] = 0
    f["getter_disp"] = ""
    f["pure_setter"] = 0
    f["setter_disp"] = ""
    if len(insns) == 2 and insns[1].mnemonic == "ret" and insns[1].op_str == "":
        m = RE_GET2.match(insns[0].op_str)
        if insns[0].mnemonic == "mov" and m:
            f["pure_getter"] = 1
            f["getter_disp"] = hex(_disp(insns[0].op_str) or 0)
        m2 = RE_SET2.match(insns[0].op_str)
        if insns[0].mnemonic == "mov" and m2:
            f["pure_setter"] = 1
            f["setter_disp"] = hex(_disp(insns[0].op_str) or 0)
    # E ret imm（扫描已捕获体内**任意** ret imm16；不止首个 ret）
    f["ret_imm"] = ""
    for ins in insns:
        if ins.mnemonic == "ret" and ins.op_str:
            f["ret_imm"] = ins.op_str
            break
    # F selector 分派（体内任意位置的 indexed jmp）
    f["has_seljmp"] = 0
    f["sel_table"] = ""
    f["sel_entries"] = ""
    f["sel_reg"] = ""
    f["sel_cmp_max"] = ""
    sel_i = -1
    for k, ins in enumerate(insns):
        if ins.mnemonic == "jmp":
            m = RE_SELJMP.match(ins.op_str)
            if m:
                tva = int(m.group(2), 16)
                f["has_seljmp"] = 1
                f["sel_table"] = "0x%X" % tva
                f["sel_entries"] = table_entries(pe, tva)
                f["sel_reg"] = m.group(1).lower()
                sel_i = k
                break
    if sel_i >= 0:
        sreg = f["sel_reg"]
        mx = None
        for ins in insns[:sel_i]:
            if ins.mnemonic == "cmp":
                m = RE_CMP.match(ins.op_str)
                if m and m.group(1).lower() == sreg:
                    v = int(m.group(2), 16) if m.group(2).lower().startswith("0x") \
                        else int(m.group(2))
                    mx = v if mx is None else max(mx, v)
        f["sel_cmp_max"] = ("" if mx is None else str(mx))
    # 取参寄存器（首指令 mov R,[esp+4]）
    f["arg_reg"] = ""
    if insns and insns[0].mnemonic == "mov":
        m = RE_ARG.match(insns[0].op_str)
        if m:
            f["arg_reg"] = m.group(1).lower()
    # G 直接 call / 间接 call（call dword ptr [0x...]）/ H 无条件 jmp
    f["n_direct_calls"] = sum(1 for i in insns if i.mnemonic == "call"
                              and not RE_CALLREG.match(i.op_str))
    f["n_indir_calls"] = sum(1 for i in insns if i.mnemonic == "call"
                             and RE_CALLREG.match(i.op_str))
    f["n_jmps"] = sum(1 for i in insns if i.mnemonic == "jmp")
    f["first_jmp"] = 1 if (insns and insns[0].mnemonic == "jmp") else 0
    f["tail_jmp"] = 1 if (insns and insns[-1].mnemonic == "jmp") else 0
    # 纯存取器（leaf accessor）：无 call、无 jmp、无 selector，止于 ret
    f["leaf"] = 1 if (f["n_direct_calls"] == 0 and f["n_indir_calls"] == 0
                      and f["n_jmps"] == 0 and term in ("ret", "retf")) else 0
    msel = None
    if f["arg_reg"]:
        for ins in insns[:8]:
            if ins.mnemonic == "mov":
                m = RE_SEL_LOAD.match(ins.op_str)
                if m and m.group(2).lower() == f["arg_reg"]:
                    msel = m
                    break
    f["first_sel_load"] = 1 if (msel and f["arg_reg"]) else 0
    # I/J 全局触达
    txt = "\n".join(i.op_str for i in insns)
    f["touch_app"] = 1 if ("0x503248" in txt) else 0
    f["touch_g2"] = 1 if ("0x503258" in txt) else 0
    f["touch_seh"] = 1 if ("fs:[0]" in txt) else 0
    f["touch_mgr"] = 1 if (re.search(r"\[e[a-dx]{2} \+ 0x19c8\]", txt, re.I)) else 0
    # K [ecx+disp] 偏移族
    disps = []
    for ins in insns:
        for m in RE_DISP.finditer(ins.op_str):
            if m.group(1).lower() == "ecx":
                disps.append(_disp(ins.op_str) or 0)
    f["ecx_disp"] = ",".join("0x%X" % d for d in sorted(set(disps)))
    # K2 体内**全部** `[reg(+disp)]` 偏移（基准寄存器忽略）——捕获 app 字段族
    alld = []
    for ins in insns:
        for m in RE_DISP.finditer(ins.op_str):
            alld.append(_disp(ins.op_str) or 0)
    f["all_disp"] = ",".join("0x%X" % d for d in sorted(set(alld)))
    # K3 从取参寄存器读的字段偏移族
    af = []
    if f["arg_reg"]:
        for ins in insns:
            for m in RE_DISP.finditer(ins.op_str):
                if m.group(1).lower() == f["arg_reg"]:
                    af.append(_disp(ins.op_str) or 0)
    f["arg_disp"] = ",".join("0x%X" % d for d in sorted(set(af)))
    return f


FORM_CLASSES = [
    (lambda m, o: m == "mov" and o == "eax, dword ptr [esp + 4]", "1. mov eax,[esp+4]"),
    (lambda m, o: m == "mov" and o == "ecx, dword ptr [esp + 4]", "2. mov ecx,[esp+4]"),
    (lambda m, o: m == "mov" and o == "edx, dword ptr [esp + 4]", "3. mov edx,[esp+4]"),
    (lambda m, o: m == "mov", "4. 其余 mov"),
    (lambda m, o: m == "push", "5. push"),
    (lambda m, o: m == "sub", "6. sub"),
    (lambda m, o: m == "jmp", "7. jmp"),
    (lambda m, o: m == "xor", "8. xor"),
]


def form_class(m, o):
    for pred, name in FORM_CLASSES:
        if pred(m, o):
            return name
    return "9. 其它 %s" % m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv")
    ap.add_argument("--summary")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    pe = PE(DUMP_PATH)
    full = handlers(pe)
    uniq = handlers(pe, merged=True)
    print("== xclus.py  capstone=%s ==" % CAPSTONE_VER)
    print("注册调用点 = %d，向量项 = %d，不同 handler = %d" %
          (len(full) - 3, len(full), len(uniq)))

    rows = []
    for idx, va in uniq:
        n_reg = sum(1 for h in full if h == va)
        rows.append(features(pe, idx, va, n_reg))

    # ---- 各轴类计数 ----
    axes = collections.OrderedDict()
    axes["A 首指令全等"] = collections.Counter(
        "%s %s" % (r["first_m"], r["first_o"]) for r in rows)
    axes["B 形态档"] = collections.Counter(form_class(r["first_m"], r["first_o"]) for r in rows)
    axes["C 纯 getter"] = collections.Counter(
        ("是" if r["pure_getter"] else "否") for r in rows)
    axes["C2 getter 偏移族"] = collections.Counter(
        r["getter_disp"] for r in rows if r["pure_getter"])
    axes["D 纯 setter"] = collections.Counter(
        ("是" if r["pure_setter"] else "否") for r in rows)
    axes["D2 setter 偏移族"] = collections.Counter(
        r["setter_disp"] for r in rows if r["pure_setter"])
    axes["E ret imm"] = collections.Counter(
        (r["ret_imm"] if r["ret_imm"] else "(无 ret imm)") for r in rows)
    axes["F selector 分派"] = collections.Counter(("有" if r["has_seljmp"] else "无") for r in rows)
    axes["F2 selector 表项数"] = collections.Counter(
        str(r["sel_entries"]) for r in rows if r["has_seljmp"])
    axes["F3 selector cmp 上界"] = collections.Counter(
        (r["sel_cmp_max"] or "(无 cmp 上界)") for r in rows if r["has_seljmp"])
    axes["G 直接 call 数"] = collections.Counter(
        ("0" if r["n_direct_calls"] == 0 else ("1" if r["n_direct_calls"] == 1 else "2+"))
        for r in rows)
    axes["G2 间接 call 数"] = collections.Counter(
        ("0" if r["n_indir_calls"] == 0 else ("1" if r["n_indir_calls"] == 1 else "2+"))
        for r in rows)
    axes["H 首指令 jmp（thunk）"] = collections.Counter(r["first_jmp"] for r in rows)
    axes["H2 体内无条件 jmp"] = collections.Counter(r["n_jmps"] > 0 for r in rows)
    axes["H3 纯存取器 leaf"] = collections.Counter(
        ("是" if r["leaf"] else "否") for r in rows)
    axes["H4 首指令取 selector"] = collections.Counter(r["first_sel_load"] for r in rows)
    axes["I app 单例 [0x503248]"] = collections.Counter(r["touch_app"] for r in rows)
    axes["I2 次全局 [0x503258]"] = collections.Counter(r["touch_g2"] for r in rows)
    axes["I3 SEH fs:[0]"] = collections.Counter(r["touch_seh"] for r in rows)
    axes["J 管理器 [reg+0x19C8]"] = collections.Counter(r["touch_mgr"] for r in rows)
    # K' 逐偏移：每个 `[reg+disp]` 偏移被多少 handler 触达
    kc = collections.Counter()
    for r in rows:
        for d in (r["all_disp"] or "").split(","):
            if d:
                kc[d] += 1
    axes["K2 逐偏移触达 handler 数（top）"] = kc
    axes["K3 [ecx+disp] 偏移族"] = collections.Counter(r["ecx_disp"] for r in rows)
    axes["L 体长（指令数）"] = collections.Counter(_blen(r["n_insn"]) for r in rows)

    total = len(rows)
    print("\n== 聚类轴（每轴合计应 = %d）==" % total)
    for name, cnt in axes.items():
        print("\n-- %s --" % name)
        shown = cnt.most_common(MAXSHOW)
        s = sum(v for _, v in shown)
        for k, v in shown:
            print("   %-46s %4d (%.1f%%)" % (str(k), v, 100.0 * v / total))
        if s < total:
            print("   （其余 %d 类共 %d 项，已截断）" % (len(cnt) - len(shown), total - s))

    # 组合：leaf 存取器 ∧ 取 [esp+4]
    thin = [r for r in rows if r["leaf"]]
    print("\n== 组合 ==")
    print("  纯 getter（体恰 2 条 mov+ret）            = %d (%.1f%%)" %
          (sum(1 for r in rows if r["pure_getter"]), 100.0 * sum(1 for r in rows if r["pure_getter"]) / total))
    print("  纯 setter（体恰 2 条 mov+ret）            = %d" % sum(1 for r in rows if r["pure_setter"]))
    print("  leaf 存取器（无 call/jmp，止于 ret）       = %d (%.1f%%)" %
          (len(thin), 100.0 * len(thin) / total))
    print("  selector 分派（indexed jmp）              = %d (%.1f%%)" %
          (sum(1 for r in rows if r["has_seljmp"]),
           100.0 * sum(1 for r in rows if r["has_seljmp"]) / total))
    print("  首指令取 arg ∧ 紧接取 selector            = %d" %
          sum(1 for r in rows if r["first_sel_load"]))

    if a.tsv:
        cols = ["vec_index", "va", "n_reg", "first_m", "first_o", "n_insn", "term",
                "pure_getter", "getter_disp", "pure_setter", "setter_disp", "ret_imm",
                "has_seljmp", "sel_table", "sel_entries", "sel_reg", "sel_cmp_max",
                "arg_reg", "first_sel_load", "n_direct_calls", "n_indir_calls", "n_jmps",
                "first_jmp", "tail_jmp", "leaf", "touch_app", "touch_g2", "touch_seh",
                "touch_mgr", "ecx_disp", "all_disp", "arg_disp"]
        with io.open(a.tsv, "w", encoding="utf-8", newline="") as f:
            f.write("\t".join(cols) + "\n")
            for r in rows:
                f.write("\t".join(str(r[c]) for c in cols) + "\n")
        print("\n[写] %s（%d 行）" % (a.tsv, len(rows)))
    if a.summary:
        with io.open(a.summary, "w", encoding="utf-8", newline="") as f:
            f.write("axis\tclass\tcount\n")
            for name, cnt in axes.items():
                for k, v in cnt.most_common():
                    f.write("%s\t%s\t%d\n" % (name, str(k).replace("\t", " "), v))
        print("[写] %s" % a.summary)

    if a.selftest:
        # ---- 判据区分力自证：对每个关键轴做「变异打废」，计数必须变 ----
        print("\n== 自证（变异打废；判据有牙齿 = 计数随判据变化）==")
        # ① selector 检测：放松为「任意 jmp」→ 必须变多
        strict_sel = sum(1 for r in rows if r["has_seljmp"])
        loose_sel = sum(1 for r in rows if r["n_jmps"] > 0)
        print("  selector（严格 indexed jmp）            = %d" % strict_sel)
        print("  selector（放松为「体内含任意 jmp」）      = %d  %s" %
              (loose_sel, "OK" if loose_sel != strict_sel else "!! 无区分力"))
        # ② leaf：放松为「无直接 call」→ 必须变多
        leaf_strict = sum(1 for r in rows if r["leaf"])
        leaf_loose = sum(1 for r in rows if r["n_direct_calls"] == 0 and r["n_jmps"] == 0)
        print("  leaf（严格：无 call∧无 jmp∧止于 ret）    = %d" % leaf_strict)
        print("  leaf（放松为「无 call∧无 jmp」）          = %d  %s" %
              (leaf_loose, "OK" if leaf_loose != leaf_strict else "!! 无区分力"))
        # ③ 取参档：严格 [esp+4] 对 8 类之 1/2/3
        strict_arg = sum(1 for r in rows if r["arg_reg"])
        print("  首指令严格取 [esp+4]（eax|ecx|edx）       = %d" % strict_arg)
        print("  （全 789 中首指令为 mov 者 = %d，两者不等即判据有牙齿）" %
              sum(1 for r in rows if r["first_m"] == "mov"))
        # ④ 负向对照：把 handler 集合换成「全部 .text 线性扫描的 call 目标」不该发生；
        #    改为核对「去重前 798 / 去重后 789」恒等式
        print("  注册调用点 %d − 去重 %d = 重复登记 %d（期望 9）" %
              (len(full) - 3, len(uniq), (len(full) - 3) - len(uniq)))


def _blen(n):
    if n <= 1:
        return "1"
    if n == 2:
        return "2"
    if n <= 5:
        return "3-5"
    if n <= 10:
        return "6-10"
    if n <= 30:
        return "11-30"
    if n <= 100:
        return "31-100"
    return "101-600"


if __name__ == "__main__":
    main()

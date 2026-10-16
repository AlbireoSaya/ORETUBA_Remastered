#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_frame_args.py —— 只读探针：从 func_lib 反汇编读出每个目标 V「实际读取了哪些栈偏移」，
按 frame 口径换算成 node_args 位号。

口径（写死，可复现）
--------------------
引擎事实（`逆向引擎\执行模型.md` §4.4 + 本次直读 handler）：
  * 调用点形态  `[08][argN-1] … [08][arg0] [04][V]`：CALL 把返回地址 push 进操作数栈，
    故 **V 入口时 sp 指向返回地址之上**；`arg_i` 位于 `sp_entry - 8 - 4i`
    （arg_0 = 最后 push 的实参，见 `SOB0解码\说明.md` node_args：`node_args[i] = cells[node-1-2i]`）。
  * `FRAME_ALLOC k`（op 0x0B）= `sp += k`：为局部量腾出 k 字节；局部量在 `sp-4 … sp-k`。
  * `SP_DROP k`（op 0x0C）= `sp -= k`：丢 k 字节（**既用于丢实参，也用于函数尾声丢局部量**）。
  * `CALL`（op 0x04）**净栈变化 = 0**：push 返回地址 +4，被 callee 的 `RET`（op 0x01）pop。
    （线性清单里看不到 callee 的 RET；若把 CALL 记 +4 会整体错位 —— 本脚本按净 0 处理，
     并用 M3 已独立验证的 4 条时长位作阳性对照，见 `--selftest`。）
  * `CALLNATIVE`（op 0x05）不消费 VM 操作数栈（实参由其后的 `SP_DROP` 丢）。

换算（**任务书给的规则**）：
  在「相对 V 入口累计净栈偏移 d」处读 `LD_STK X` ⇒ 该字地址 = `sp_entry + d - X`。
  令其 = `arg_i` 地址（`sp_entry - 8 - 4i`）⇒ **X = d + 8 + 4i**，
  即 **i = (X - d - 8) / 4**（d = 该点相对入口的净栈偏移，含 FRAME_ALLOC 与已 push 的实参）。
  * `d` 由**基本块级抽象解释**求出（沿控制流传播；合并点若 d 不唯一 ⇒ 记 `d歧义`，如实上报）。
  * 当 d = 0 且 body 无 FRAME_ALLOC 时，本条退化为任务书写的 `node_args[i] 位于 +8+4i`。
  * **`FRAME_ALLOC k` 变体**：若 body 有 `FRAME_ALLOC k`，则「未 push 时」的实参位落在
    `X = k + 8 + 4i`（脚本直接算 i，不依赖这一等价式）。

分类（写死）
  * `实参`  ：0 <= i < argc
  * `局部`  ：i < 0（落在 FRAME_ALLOC 出来的局部区，或更深的调用者帧 —— 由偏移量判定）
  * `越界`  ：i >= argc（**读到 argc 之外 ⇒ 任务书要求必须明确写出**）
  * `非4字节格`：X - d - 8 不是 4 的倍数（换算不成立）

复跑（只读）：
  python -X utf8 _probe_frame_args.py --emit      # 出 效果族参数位_帧读.tsv
  python -X utf8 _probe_frame_args.py --selftest  # 用 M3 已证 4 条位作阳性对照
"""
import argparse
import glob
import os
import re
import sys
from collections import defaultdict

G = r"E:/ZCode Workspace/Galgame"
ENG = G + "/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/逆向引擎"
ASMDIR = ENG + "/funclib_反汇编"
TSVDIR = G + "/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/SOB0解码"

# ---- 目标 V（任务书点名；V 号 ot 本地口径）-----------------------------------
# name 只是「既有定名」标签，取 资源组\演出\Lucifen命令族标签.tsv（ot）+ M3 + TIME_FAMILY，
# **不作为本轮的判定结论**，只作阅读锚点。
TARGETS = [
    ("0x1B888", "Flash"),
    ("0x1B69C", "EffectQuake"),
    ("0x19D58", "EffectQuakeEnd(候选)"),
    ("0x1C330", "EffectQuakeEnd(候选)"),
    ("0x1BD8C", "EffectQuake(候选)"),
    ("0x1B040", "InOut_Act"),
    ("0x1AEA0", "scroll/InOut_Act第二载体"),
    ("0x1A96C", "InOut(现名rule_in)"),
    ("0x19F9C", "FadeOut(fadeend载体)"),
    ("0x7480", "Window"),
    ("0x10150", "bg_move"),
    ("0xFDF4", "bg_zoom"),
    ("0x10980", "bg_zanime/bg_zoom"),
    ("0x12998", "dash/bg_blur"),
    ("0x12E94", "mdash/bg_blur"),
    ("0x13300", "bg_blur"),
    ("0x1107C", "bg_rot"),
    ("0x2A150", "cross"),
    ("0x1AD18", "EyeCatch/EyeCatchEnd"),
    ("0x10428", "SpriteMove/bg_anime"),
]

# 净栈偏移 d 的传递（字节）
STACK_DELTA = {
    "PUSH": 4, "PUSHDEREF": 4,
    "POPSTORE": -4,
    "CALL": 0, "CALLNATIVE": 0,
}
TERMINAL = {"RET", "HALT_OK"}
JUMPS = {"JZ", "JMP", "TABJMP"}
# 读/写栈偏移的助记符 -> (offset_operand_index, kind)
STKACCESS = {
    "LD_STK": (0, "读"),
    "LD_STK_D": (0, "读*"),
    "LEA_STK": (0, "取址"),
    "ST_STK": (1, "写"),
    "ST_STK_D": (1, "写"),
    "MOV_STK_STK": (0, "读"),
}

LINE_RE = re.compile(r"^([0-9A-Fa-f]{8})\s+(\S+)\s*(.*)$")
ANN_RE = re.compile(r"\[(.*?)\]$")
L_RE = re.compile(r"^L_([0-9A-Fa-f]+)$")


def asm_path(v):
    return os.path.join(ASMDIR, "%06X.asm" % int(v, 16))


def parse_asm(path):
    """-> (header_dict, [ {off, op, operands:[raw], anns:[str]} ])"""
    ins = []
    header = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if ln.startswith(";"):
                if "过程=" in ln:
                    m = re.search(r"core=(0x[0-9A-Fa-f]+)\.\.(0x[0-9A-Fa-f]+)", ln)
                    if m:
                        header["core"] = (int(m.group(1), 16), int(m.group(2), 16))
                    m2 = re.search(r"过程=(0x[0-9A-Fa-f]+)\.\.(0x[0-9A-Fa-f]+)", ln)
                    if m2:
                        header["proc"] = (int(m2.group(1), 16), int(m2.group(2), 16))
                continue
            m = LINE_RE.match(ln)
            if not m:
                continue
            off = int(m.group(1), 16)
            op = m.group(2)
            rest = m.group(3).strip()
            toks = rest.split() if rest else []
            raw, anns = [], []
            for t in toks:
                am = ANN_RE.search(t)
                if am:
                    raw.append(t[:t.index("[")])
                    anns.append(am.group(1))
                else:
                    raw.append(t)
                    anns.append("-")
            ins.append({"off": off, "op": op, "raw": raw, "ann": anns})
    return header, ins


def to_int(s):
    try:
        return int(s, 16) if s.lower().startswith("0x") else int(s)
    except Exception:
        return None


def jump_targets(ins):
    out = []
    for a in ins["ann"]:
        m = L_RE.match(a)
        if m:
            out.append(int(m.group(1), 16))
    return out


def dataflow(ins_list, entry):
    """抽象解释：每个指令偏移处的净栈偏移 d 集合。返回 {off: set(d)}"""
    by = {i["off"]: i for i in ins_list}
    order = sorted(by)
    # fallthrough 目标
    def next_off(off):
        idx = order.index(off)
        return order[idx + 1] if idx + 1 < len(order) else None

    state = defaultdict(set)
    state[entry].add(0)
    work = [entry]
    seen = set()
    while work:
        off = work.pop()
        if off in seen:
            continue
        seen.add(off)
        cur = by.get(off)
        if cur is None:
            continue
        ds = state[off]
        if cur["op"] in TERMINAL:
            continue
        succ_d = set()
        for d in ds:
            nd = d + STACK_DELTA.get(cur["op"], 0)
            if cur["op"] == "FRAME_ALLOC":
                v = to_int(cur["raw"][0]) if cur["raw"] else None
                nd = d + (v if v else 0)
            elif cur["op"] == "SP_DROP":
                v = to_int(cur["raw"][0]) if cur["raw"] else None
                nd = d - (v if v else 0)
            succ_d.add(nd)
        succs = []
        if cur["op"] in JUMPS:
            succs.extend(jump_targets(cur))
            if cur["op"] == "JZ":
                n = next_off(off)
                if n is not None:
                    succs.append(n)
        else:
            n = next_off(off)
            if n is not None:
                succs.append(n)
        for s in succs:
            before = len(state[s])
            state[s] |= succ_d
            if len(state[s]) != before:
                work.append(s)
    return state


def analyse(v, argc):
    p = asm_path(v)
    if not os.path.exists(p):
        return None
    header, ins_list = parse_asm(p)
    if not ins_list:
        return None
    entry = int(v, 16)
    st = dataflow(ins_list, entry)
    rows = []
    frame_alloc = None
    for i in ins_list:
        if i["op"] == "FRAME_ALLOC":
            frame_alloc = to_int(i["raw"][0])
    for i in ins_list:
        acc = STKACCESS.get(i["op"])
        if not acc:
            continue
        oi, kind = acc
        if oi >= len(i["raw"]):
            continue
        X = to_int(i["raw"][oi])
        if X is None:
            continue
        ds = st.get(i["off"], set())
        for d in (sorted(ds) if ds else [None]):
            row = {"V": v, "off": i["off"], "op": i["op"], "kind": kind,
                   "X": X, "d": d, "frame_alloc": frame_alloc}
            if d is None:
                row["i"] = None
                row["cls"] = "d未知"
            else:
                num = X - d - 8
                if num % 4 != 0:
                    row["i"] = None
                    row["cls"] = "非4字节格"
                else:
                    ii = num // 4
                    row["i"] = ii
                    if argc is not None and 0 <= ii < argc:
                        row["cls"] = "实参"
                    elif ii < 0:
                        row["cls"] = "局部"
                    else:
                        row["cls"] = "越界"
            rows.append(row)
    return {"header": header, "entry": entry, "frame_alloc": frame_alloc,
            "n_ins": len(ins_list), "rows": rows}


# ---- argc：从 解出_*.tsv 的 evidence 读（括号感知顶层逗号切分，不 strip）------
def parse_args_evidence(ev):
    """从 evidence 串取 args=[…] 顶层逗号切分（**不用非贪婪正则**：串实参可含 ] 与 ,）。"""
    k = ev.find("args=[")
    if k < 0:
        return None
    s = k + 6
    j = ev.find(" ctrl=", s)
    body = ev[s:j] if j >= 0 else ev[s:]
    out, depth, cur = [], 0, []
    for ch in body:
        if ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def load_argc(tsv):
    """{(src,V): {argc: n}}"""
    res = defaultdict(lambda: defaultdict(int))
    with open(tsv, "r", encoding="utf-8", errors="replace") as f:
        head = f.readline().rstrip("\n").split("\t")
        ci = {c: n for n, c in enumerate(head)}
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) <= ci.get("evidence", 8):
                continue
            ev = p[ci["evidence"]]
            m = re.search(r"V=(0x[0-9A-Fa-f]+)", ev)
            m2 = re.search(r"argc=(\d+)", ev)
            if not m or not m2:
                continue
            src = p[ci["scene_id"]].split("_")[0]
            res[(src, m.group(1))][int(m2.group(1))] += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    argc = load_argc(os.path.join(TSVDIR, "解出_ot.tsv"))
    # **全库 argc（含系统脚本）优先** —— 用项目自带解码器扫 412 文件；
    # 剧情语料口径缺 cross(0x2A150) 等系统脚本命令，只用它会误判「越界」。
    try:
        import _probe_corpus_argc as _CA
        _cor, _nf, _bad = _CA.scan(_CA.SCRIPTDIR)
        for v, r in _cor.items():
            argc[("ot", v)] = dict(r["argc"])
        print("[argc 来源] 全库 412 文件（项目解码器；文件 %d 跳过 %d）优先" % (_nf, _bad))
    except Exception as e:
        print("[argc 来源] 剧情语料（全库扫描不可用：%s）" % e)
    argc_tr = load_argc(os.path.join(TSVDIR, "解出_otr.tsv"))
    argc_tp = load_argc(os.path.join(TSVDIR, "解出_otp.tsv"))
    for k, v in argc_tr.items():
        for kk, vv in v.items():
            argc[k][kk] += vv
    for k, v in argc_tp.items():
        for kk, vv in v.items():
            argc[k][kk] += vv

    out = []
    print("== 帧读探针（ot 口径；V 号 ot 本地）==")
    print("%-9s %-24s %-6s %-5s %-6s %-7s %-6s %s" %
          ("V", "name(既有)", "argc", "读位", "frame", "净偏d", "分类", "备注"))
    for v, name in TARGETS:
        ac = argc.get(("ot", v), {})
        acs = sorted(ac.items())
        argv = acs[0][0] if acs else None
        amap = ",".join("%d×%d" % (k, n) for k, n in acs) or "-"
        r = analyse(v, argv)
        if r is None:
            print("%-9s %-24s %-6s  %s" % (v, name, amap, "!! 反汇编缺失"))
            continue
        reads = {}
        for row in r["rows"]:
            if row["cls"] in ("实参", "越界", "非4字节格"):
                reads.setdefault((row["i"], row["cls"]), []).append(row)
            else:
                reads.setdefault((row["i"], row["cls"]), []).append(row)
        # 打印实参/越界/异常，局部只汇总
        for (ii, cls), rs in sorted(reads.items(), key=lambda kv: (kv[0][0] is None, kv[0][0] or 0)):
            if cls == "局部":
                continue
            Xs = sorted(set(x["X"] for x in rs))
            ds = sorted(set(str(x["d"]) for x in rs))
            ops = sorted(set(x["op"] for x in rs))
            print("%-9s %-24s %-6s %-5s %-6s %-7s %-6s %s" % (
                v, name, amap,
                ("-%d" % -ii) if (ii is not None and ii < 0) else (str(ii) if ii is not None else "?"),
                ("%s" % r["frame_alloc"]) if r["frame_alloc"] is not None else "-",
                ",".join(ds), cls,
                "X=%s op=%s n=%d" % (",".join("0x%X" % x for x in Xs), "/".join(ops), len(rs))))
            out.append({"V": v, "name": name, "argc": amap, "pos": ii, "cls": cls,
                        "X": ",".join("0x%X" % x for x in Xs), "d": ",".join(ds),
                        "op": "/".join(ops), "n": len(rs),
                        "frame_alloc": r["frame_alloc"], "off": ",".join("0x%X" % x["off"] for x in rs)})
        nloc = sum(1 for row in r["rows"] if row["cls"] == "局部")
        print("%-9s %-24s %-6s  [局部槽读 %d 次，略]" % (v, name, amap, nloc))

    if a.emit:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "效果族参数位_帧读.tsv")
        cols = ["V", "name", "argc", "pos", "cls", "X", "d", "op", "n", "frame_alloc", "off"]
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("\t".join(cols) + "\n")
            for row in out:
                f.write("\t".join("-" if row[c] is None else str(row[c]) for c in cols) + "\n")
        print("-> %s （%d 行）" % (p, len(out)))

    if a.selftest:
        print("\n== 阳性对照：M3（ISSUE-20261008-04）已独立验证的 4 条实参位 ==")
        # (V, 期望位, 依据)
        golden = [("0x1B69C", 5, "EffectQuake pos5=ms (M3 §2.1)"),
                  ("0x1B040", 3, "InOut_Act pos3=ms (M3 §2.2)"),
                  ("0x1AEA0", 2, "InOut_Act第二载体 pos2=ms (M3 §2.3)"),
                  ("0x1A96C", 2, "InOut/rule_in pos2=ms (M3 §2.4)")]
        ok = True
        for v, want, why in golden:
            ac = argc.get(("ot", v), {})
            argv = sorted(ac.items())[0][0] if ac else None
            r = analyse(v, argv)
            pos = sorted(set(x["i"] for x in r["rows"] if x["cls"] == "实参"))
            hit = want in pos
            ok = ok and hit
            print("  %-9s argc=%s  实参位=%s  期望含 pos%d -> %s   [%s]" %
                  (v, argv, pos, want, "PASS" if hit else "FAIL", why))
        print("SELFTEST = %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

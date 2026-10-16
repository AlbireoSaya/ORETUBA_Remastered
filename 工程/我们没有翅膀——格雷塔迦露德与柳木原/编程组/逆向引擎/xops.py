#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xops.py — 表感知（table-aware）全 op 计数与操作数命中率重算。

Issue ISSUE-20261008-04（M4）。背景：旧走查（xwalk.py / xverify.py / xverify.check）
遇 `op 0x07`（变长跳转表）即 `break` ⇒ 计数与「操作数命中率」均为**截断口径**。
本脚本把 `0x07` 当**变长指令**正确跨过（表内联于 idx 字之后，尾部哨兵 `0xFFFFFFFF`），
重算 **全部 47 个 op** 的：① 出现次数；② 每个操作数位的 6 表归属分布；
③ 对「语义声明的期望集合」的操作数命中率。

口径（与 `执行模型.md` §4.4 逐字同表）：
  op 操作数字数（不含 op）由各 handler 反汇编读出；总字数 = 1 + 操作数字数。
  `0x07`：`[07][idx][t0..tN][0xFFFFFFFF]`，idx 占 1 字，表项 N+1 个，哨兵 1 字。

用法：
  python -X utf8 xops.py --all "<SCRIPT>"            # 汇总 + 逐 op 表（table-aware）
  python -X utf8 xops.py --all "<SCRIPT>" --trunc    # 旧口径（遇 0x07 即停）对照
  python -X utf8 xops.py --all "<SCRIPT>" --tsv <dir># 落 TSV（op_counts / operand_membership / validation）
  python -X utf8 xops.py --file <sob> --dump07       # 单文件：0x07 站点与表
"""
import os
import sys
import collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402

# 总字数 = 1 + 操作数字数（即「含 op 自身」；与 x02.py/xwalk.py 的 VM_LEN 同表）
VM_WORDS = {0x00: 1, 0x01: 1, 0x02: 2, 0x03: 2, 0x04: 2, 0x05: 4, 0x06: 2,
            0x08: 2, 0x09: 2, 0x0A: 2, 0x0B: 2, 0x0C: 2, 0x0D: 4,
            0x0E: 4, 0x0F: 4, 0x10: 4, 0x11: 4, 0x12: 4, 0x13: 4, 0x14: 4,
            0x15: 4, 0x16: 3, 0x17: 3, 0x18: 4, 0x19: 4, 0x1A: 2, 0x1B: 2,
            0x1C: 2, 0x1D: 2, 0x1E: 3, 0x1F: 3, 0x20: 3, 0x21: 3, 0x22: 3,
            0x23: 3, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 4,
            0x2A: 4, 0x2B: 4, 0x2C: 4, 0x2D: 4, 0x2E: 4}
SENTINEL = 0xFFFFFFFF
ALL_OPS = list(range(0x2F))


def decode_items(cells, trunc07=False):
    """线性走查 → item 列表 [(cell_index, op, [operand_cell_indices])]。

    table-aware：`0x07` 的表从 idx 字之后直到尾部哨兵（含哨兵）**整体作为操作数**；
    trunc07=True：遇第一个 `0x07` 即停（复现旧口径）。
    """
    items = []
    i, n = 0, len(cells)
    while i < n:
        t = cells[i]
        if t > 0x2E:
            items.append((i, t, []))          # 非法 op（数据侧）
            break
        if t == 0x07:
            if trunc07:
                break
            j = i + 2
            while j < n and cells[j] != SENTINEL:
                j += 1
            if j < n:
                items.append((i, t, list(range(i + 1, j + 1))))   # idx + 表项 + 哨兵
                i = j + 1
            else:                                                  # 无哨兵（异常）
                items.append((i, t, list(range(i + 1, n))))
                i = n
            continue
        W = VM_WORDS.get(t, 1)
        items.append((i, t, list(range(i + 1, min(i + W, n)))))
        i += W
    return items


def membership(sob, cell_index):
    """操作数字所在字节偏移命中的 map 集合（可能多张）。"""
    site = cell_index * 4
    hits = []
    for k, m in enumerate(sob.maps):
        if site in m:
            hits.append(k)
    return hits


# 各 op 操作数位的「语义期望集合」——**由 handler 反汇编逐条读出**（本文件 §反汇编结论，
# 与 `执行模型.md` §4.4 的记号有若干出入，出处以本处为准并已在报告登记订正）。
# 记号：R = 引用字/地址(maps[0]|maps[3]|maps[4])；C = 代码指针(maps[3]|maps[4])；
#       H = 原生 handler 下标(maps[1])；I = 立即数（不在任何表）；
#       V = 值类（既可为立即数、也可为引用字，两者皆合法）
REF = ("R",)
CODE = ("C",)
HAND = ("H",)
IMM = ("I",)
VAL = ("V",)
# op -> [(pos, 期望集合), ...]；pos 0 = 第 1 操作数
SPEC = {
    0x02: [(0, IMM)],                       # RETVAL = *op（立即数返回码）
    0x03: [(0, REF)],                       # *op = RETVAL（dest 槽）
    0x04: [(0, CODE)],                      # CALL *op（V = func_lib 代码指针）
    0x05: [(0, HAND), (1, IMM), (2, REF)],  # dest = handler(立即数实参)
    0x06: [(0, CODE)],                      # JMP
    0x08: [(0, VAL)],                       # PUSH 操作数字（值/指针皆可）
    0x09: [(0, REF)],                       # push(**op)
    0x0A: [(0, REF)],                       # *op = pop
    0x0B: [(0, IMM)],                       # sp += imm（帧分配）
    0x0C: [(0, IMM)],                       # sp -= imm（ADDSP）
    0x0D: [(0, IMM), (1, IMM), (2, REF)],
    0x0E: [(0, IMM), (1, IMM), (2, REF)],
    0x0F: [(0, IMM), (1, IMM), (2, REF)],
    0x10: [(0, IMM), (1, IMM), (2, REF)],
    0x11: [(0, IMM), (1, IMM), (2, REF)],
    0x12: [(0, IMM), (1, IMM), (2, REF)],
    0x13: [(0, IMM), (1, IMM), (2, REF)],
    0x14: [(0, IMM), (1, IMM), (2, REF)],
    0x15: [(0, IMM), (1, IMM), (2, REF)],
    0x16: [(0, IMM), (1, REF)],             # *op1 = ~op0
    0x17: [(0, IMM), (1, REF)],             # *op1 = (op0==0)
    0x18: [(0, IMM), (1, IMM), (2, REF)],
    0x19: [(0, IMM), (1, IMM), (2, REF)],
    0x1A: [(0, REF)],                       # ++(*(*op))
    0x1B: [(0, REF)],                       # --(*(*op))
    0x1C: [(0, IMM)],                       # ++(*(sp-imm))
    0x1D: [(0, IMM)],                       # --(*(sp-imm))
    0x1E: [(0, IMM), (1, CODE)],            # if(op0==0) pc=op1（op0 直接比较，不解引用）
    0x1F: [(0, VAL), (1, REF)],             # *op1 = op0
    0x20: [(0, REF), (1, REF)],             # *op1 = *op0
    0x21: [(0, VAL), (1, REF)],             # **op1 = op0
    0x22: [(0, VAL), (1, IMM)],             # *(sp-op1) = op0
    0x23: [(0, IMM), (1, REF)],             # *op1 = *(sp-op0)
    0x24: [(0, REF), (1, IMM)],             # *(sp-op1) = *op0
    0x25: [(0, IMM), (1, IMM)],             # *(sp-op1) = *(sp-op0)
    0x26: [(0, IMM), (1, REF)],             # *op1 = *(*(sp-op0))
    0x27: [(0, REF), (1, REF)],             # *op1 = **op0
    0x28: [(0, IMM), (1, REF)],             # *op1 = sp - op0（取栈槽地址）
    0x29: [(0, IMM), (1, IMM), (2, REF)],
    0x2A: [(0, IMM), (1, IMM), (2, REF)],
    0x2B: [(0, IMM), (1, IMM), (2, REF)],
    0x2C: [(0, IMM), (1, IMM), (2, REF)],
    0x2D: [(0, IMM), (1, IMM), (2, REF)],
    0x2E: [(0, IMM), (1, IMM), (2, REF)],
}


def hit(expect, hits):
    """hits = 该操作数命中 map 的编号集合。"""
    e = expect[0]
    if e == "I":
        return len(hits) == 0
    if e == "V":
        return True                      # 值类：ref/imm 皆合法（不构成可失败判据）
    if e == "H":
        return 1 in hits
    if e == "C":
        return (3 in hits) or (4 in hits)
    return (0 in hits) or (3 in hits) or (4 in hits)


def scan(sob, trunc07=False):
    cells = sob.cells
    items = decode_items(cells, trunc07=trunc07)
    cnt = collections.Counter()
    mem = collections.defaultdict(collections.Counter)   # (op,pos) -> Counter(mapidx/'none')
    val = collections.defaultdict(lambda: [0, 0])        # (op,pos) -> [hit,n]
    o07 = []
    claims = collections.Counter()                        # 旧文档具体断言的分子/分母
    for (ci, op, ops) in items:
        if op > 0x2E:
            break
        cnt[op] += 1
        if op == 0x07:
            o07.append((ci, len(ops) - 1))     # ops = idx + 表项 + 哨兵 ⇒ 表长 = len-1
            for p, oc in enumerate(ops):
                hits = membership(sob, oc)
                mem[(op, p)]["none" if not hits else ",".join(map(str, hits))] += 1
            continue
        for p, oc in enumerate(ops):
            hits = membership(sob, oc)
            mem[(op, p)]["none" if not hits else ",".join(map(str, hits))] += 1
        for (p, expect) in SPEC.get(op, []):
            if p < len(ops):
                hits = membership(sob, ops[p])
                val[(op, p)][1] += 1
                if hit(expect, hits):
                    val[(op, p)][0] += 1
        # --- 旧文档具体断言 ---
        if op == 0x05 and len(ops) >= 1:                  # 操作数0 ∈ maps[1] 且 value<801
            site = ops[0] * 4
            claims["op05_fn_n"] += 1
            if site in sob.maps[1] and sob.maps[1][site] < 801:
                claims["op05_fn_ok"] += 1
        if op == 0x04 and len(ops) >= 1:                  # 操作数0 ∈ maps[3]∪maps[4]
            site = ops[0] * 4
            claims["op04_n"] += 1
            if (site in sob.maps[3]) or (site in sob.maps[4]):
                claims["op04_ok"] += 1
        if op == 0x05 and len(ops) >= 3:                  # 第3操作数(dest) ∈ maps[0/3/4]
            site = ops[2] * 4
            claims["op05_dest_n"] += 1
            if (site in sob.maps[0]) or (site in sob.maps[3]) or (site in sob.maps[4]):
                claims["op05_dest_ok"] += 1
        if op == 0x08 and len(ops) >= 1:                  # 旧述「arg 是 maps[0/3/4] 引用字」
            site = ops[0] * 4
            claims["op08_n"] += 1
            if (site in sob.maps[0]) or (site in sob.maps[3]) or (site in sob.maps[4]):
                claims["op08_ok"] += 1
        if op == 0x04 and len(ops) >= 1:                  # 细分 maps[3] vs maps[4]
            site = ops[0] * 4
            if site in sob.maps[3]:
                claims["op04_map3"] += 1
            if site in sob.maps[4]:
                claims["op04_map4"] += 1
    last = items[-1][0] if items else 0
    return dict(cnt=cnt, mem=mem, val=val, o07=o07, claims=claims,
                bad=(items[-1][1] > 0x2E) if items else False,
                end_ok=(last * 4 + 4 >= sob.ss), last=last, ss=sob.ss,
                n_items=len([1 for (_, o, _) in items if o <= 0x2E]))


def main():
    a = sys.argv[1:]
    trunc = "--trunc" in a
    files = []
    if "--file" in a:
        files = [a[a.index("--file") + 1]]
    elif "--all" in a:
        root = a[a.index("--all") + 1]
        files = [os.path.join(root, f) for f in sorted(os.listdir(root))
                 if f.lower().endswith(".sob")]
    tsvdir = a[a.index("--tsv") + 1] if "--tsv" in a else None

    cnt = collections.Counter()
    mem = collections.defaultdict(collections.Counter)
    val = collections.defaultdict(lambda: [0, 0])
    claims = collections.Counter()
    o07_total = 0
    bad_files = []
    end_ok_n = 0
    nf = 0
    skip1 = 0
    for p in files:
        try:
            sob = Sob0(p)
        except Exception:
            skip1 += 1
            continue
        r = scan(sob, trunc07=trunc)
        nf += 1
        cnt.update(r["cnt"])
        claims.update(r["claims"])
        for k, c in r["mem"].items():
            mem[k].update(c)
        for k, v in r["val"].items():
            val[k][0] += v[0]
            val[k][1] += v[1]
        o07_total += len(r["o07"])
        if r["bad"]:
            bad_files.append((os.path.basename(p), r["last"], r["ss"]))
        if r["end_ok"]:
            end_ok_n += 1

    print("== %s 口径 ==" % ("TRUNC（遇 0x07 即停）" if trunc else "TABLE-AWARE（正确跨过 0x07）"))
    print("  files=%d（跳过非容器 %d）  op 0x07 站点=%d  完整走到代码区末尾=%d/%d"
          % (nf, skip1, o07_total, end_ok_n, nf))
    print("  撞上非法 op(>0x2E) 而提前停的文件=%d" % len(bad_files))
    for b in bad_files[:20]:
        print("     %-22s last_cell=%d ss=%d" % b)
    print("\n  op   count     operand-validation（表感知口径）")
    tot_tokens = sum(cnt.values())
    print("  %-4s %9s" % ("op", "count"))
    for op in ALL_OPS:
        c = cnt.get(op, 0)
        vs = []
        for (p, expect) in SPEC.get(op, []):
            h, n = val.get((op, p), [0, 0])
            if n:
                e = expect[0]
                ename = {"R": "maps[0/3/4]", "C": "maps[3/4]",
                         "H": "maps[1]", "I": "non-map", "V": "value"}[e]
                vs.append("pos%d∈%s %d/%d=%.4f" % (p, ename, h, n, h / n))
        print("  0x%02X %9d  %s" % (op, c, "  |  ".join(vs) if vs else "-"))
    print("\n  合计 token 数（含操作数/表项）=%d" % tot_tokens)

    print("\n  == 旧文档「100.0000%」类具体断言重算 ==")
    def cf(name, ok, n, old_ok=None, old_n=None):
        r = ("%.4f" % (ok / n)) if n else "-"
        old = ("  旧述 %d/%d=%.4f" % (old_ok, old_n, old_ok / old_n)) if old_n else ""
        flag = ""
        if old_n is not None:
            flag = "  <- 数字变动" if (ok != old_ok or n != old_n) else "  (数字不变)"
        print("   %-44s %d/%d=%s%s%s" % (name, ok, n, r, old, flag))
    cf("C1 op0x05 操作数0∈maps[1] 且 value<801",
       claims["op05_fn_ok"], claims["op05_fn_n"], 62245, 62245)
    cf("C2 op0x04 操作数0∈maps[3]∪maps[4]",
       claims["op04_ok"], claims["op04_n"], 113166, 113166)
    cf("C3 op0x05 第3操作数(dest)∈maps[0/3/4]",
       claims["op05_dest_ok"], claims["op05_dest_n"], 62245, 62245)
    cf("C4 op0x08 操作数∈maps[0/3/4]（旧述『arg 是引用字』）",
       claims["op08_ok"], claims["op08_n"])
    print("   C2 细分：op0x04 操作数0∈maps[3] = %d ；∈maps[4] = %d（和 = %d）"
          % (claims["op04_map3"], claims["op04_map4"],
             claims["op04_map3"] + claims["op04_map4"]))
    print("   C4：op0x08 操作数 引用字=%d / 立即数=%d（立即数=未被任何表登记）"
          % (claims["op08_ok"], claims["op08_n"] - claims["op08_ok"]))

    if tsvdir:
        os.makedirs(tsvdir, exist_ok=True)
        with open(os.path.join(tsvdir, "op_counts%s.tsv" % ("_trunc" if trunc else "")),
                  "w", encoding="utf-8", newline="") as f:
            f.write("op\thex\tcount\n")
            for op in ALL_OPS:
                f.write("%d\t0x%02X\t%d\n" % (op, op, cnt.get(op, 0)))
        with open(os.path.join(tsvdir, "op_operand_membership%s.tsv" % ("_trunc" if trunc else "")),
                  "w", encoding="utf-8", newline="") as f:
            f.write("op\thex\tpos\tn\tmap0\tmap1\tmap2\tmap3\tmap4\tmap5\tnone\tmulti\n")
            for op in ALL_OPS:
                for p in range(0, max(1, VM_WORDS.get(op, 1) - 1) if op != 0x07 else 8):
                    c = mem.get((op, p))
                    if not c:
                        continue
                    n = sum(c.values())
                    g = lambda k: c.get(str(k), 0)
                    multi = sum(v for k, v in c.items()
                                if k != "none" and "," in k)
                    f.write("%d\t0x%02X\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"
                            % (op, op, p, n, g(0), g(1), g(2), g(3), g(4), g(5),
                               c.get("none", 0), multi))
        with open(os.path.join(tsvdir, "op_validation%s.tsv" % ("_trunc" if trunc else "")),
                  "w", encoding="utf-8", newline="") as f:
            f.write("op\thex\tpos\texpect\thit\tn\trate\tnote\n")
            note = {0x02: "immediate retval", 0x03: "REF=RETVAL", 0x04: "CALL V(func_lib)",
                    0x05: "CALLNATIVE fn/arg/dest", 0x06: "JMP", 0x08: "PUSH",
                    0x0B: "frame alloc", 0x0C: "ADDSP", 0x1E: "JZ",
                    0x28: "stack-slot addr"}
            for op in ALL_OPS:
                for (p, expect) in SPEC.get(op, []):
                    h, n = val.get((op, p), [0, 0])
                    f.write("%d\t0x%02X\t%d\t%s\t%d\t%d\t%s\t%s\n"
                            % (op, op, p, expect[0], h, n,
                               ("%.4f" % (h / n)) if n else "-",
                               note.get(op, "")))


if __name__ == "__main__":
    main()

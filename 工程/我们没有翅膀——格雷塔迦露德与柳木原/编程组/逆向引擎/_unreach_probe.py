# -*- coding: utf-8 -*-
"""_unreach_probe.py —— 静态不可达区「初查」只读探针（ISSUE-20261008-06 C1 · 任务③）。

复用 `xvseg.py` 的切分/可达引擎（不重写），对**多个作品**各自的 `func_lib.sob`：
  1. 按**该作品自己的语料**（`<SCRIPT>/*.sob` 的 `maps[3]` ∪ 库内 CALL 目标）做可达闭包；
  2. 量化静态不可达区（块 / 指令 / 占比 / 根数）；
  3. 判「不可达区是否自洽成完整过程」——从不可达根在**不可达集合内**做闭包，
     看能否覆盖全部不可达块（支持 H1：库内未被调用的命令实现体）；
  4. 跨作品：ot 不可达过程的内嵌串 / 字节是否在 otp/AS 的 func_lib 中复现（H1 的跨作线索）。

只读：不写任何游戏文件、不改 xvseg；中断/异常如实打印。
"""
from __future__ import annotations
import io, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xvseg  # noqa: E402

DR = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
WORKS = [
    ("ot  (本作)",    os.path.join(DR, "工程", "我们没有翅膀", "解包", "SCRIPT", "func_lib.sob"),
                      os.path.join(DR, "工程", "我们没有翅膀", "解包", "SCRIPT")),
    ("otp (前奏诗)",  os.path.join(DR, "工程", "我们没有翅膀 前奏诗", "解包", "SCRIPT", "func_lib.sob"),
                      os.path.join(DR, "工程", "我们没有翅膀 前奏诗", "解包", "SCRIPT")),
    ("ota (After Story)", os.path.join(DR, "工程", "我们没有翅膀 After Story", "语料", "原文", "func_lib.sob"),
                      os.path.join(DR, "工程", "我们没有翅膀 After Story", "语料", "原文")),
    ("otr (R版SCRIPT)", os.path.join(DR, "工程", "我们没有翅膀R", "语料", "R版SCRIPT", "func_lib.sob"),
                      os.path.join(DR, "工程", "我们没有翅膀R", "语料", "R版SCRIPT")),
]


def explore(name, flib, script):
    print("=" * 78)
    print("[%s]\n  func_lib = %s\n  corpus   = %s" % (name, flib, script))
    if not os.path.isfile(flib):
        print("  缺文件，跳过"); return None
    seg = xvseg.Seg(flib)
    ents, cnt, files = xvseg.corpus_entries(script)
    internal = set(seg.call_sites)
    allv = sorted(ents | internal)
    seg.VS = tuple(allv)
    cov, unc = xvseg.coverage(seg, allv)
    nin = len(seg.insns)
    nblk = len(seg.blocks)
    # 指令数：块内指令 = insns 落 [st,en)
    pos_list = [p for (p, _o, _a, _e) in seg.insns]
    import bisect
    def blk_instrs(b):
        st, en = seg.blocks[b][0], seg.blocks[b][1]
        return bisect.bisect_left(pos_list, en) - bisect.bisect_left(pos_list, st)
    unc_i = sum(blk_instrs(b) for b in unc)
    print("  代码区 [0,0x%X)  %d B；指令 %d；非法 op %d；走查终点 0x%X (ss=0x%X)"
          % (seg.ss, seg.ss, nin, len(seg.illegal), seg.walk_end, seg.ss))
    print("  基本块 %d；可达 %d（指令 %d）；**不可达 %d 块 / %d 指令 = %.4f**"
          % (nblk, len(cov), nin - unc_i, len(unc), unc_i, unc_i / max(nin, 1)))
    print("  语料 maps[3] V = %d；库内 CALL 目标 = %d；入口并集 = %d（交 %d）"
          % (len(ents), len(internal), len(allv), len(ents & internal)))

    # ── 3. 不可达区自洽性：从「不可达根」在不可达集合内闭包 ──
    uncset = set(unc)
    inedge = collections.Counter()
    for b, succ in seg.intra_edges.items():
        for s in succ:
            inedge[s] += 1
    roots = [b for b in unc if inedge[b] == 0]
    reached = set()
    stack = list(roots)
    while stack:
        b = stack.pop()
        if b in reached:
            continue
        reached.add(b)
        for s in seg.intra_edges.get(b, ()):
            if s in uncset and s not in reached:
                stack.append(s)
    orphan = [b for b in unc if b not in reached]
    print("  不可达根 %d 个（无任何入边）；从根在**不可达集合内**闭包可达 %d / %d 块；"
          "孤立（连不可达根都到不了）%d 块" % (len(roots), len(reached), len(unc), len(orphan)))
    # 根的闭包是否「自洽完整过程」：闭包内是否有终止项、是否有指向闭包外的边
    good = bad = 0
    for r in roots:
        cl, st = set(), [r]
        while st:
            b = st.pop()
            if b in cl:
                continue
            cl.add(b)
            for s in seg.intra_edges.get(b, ()):
                if s in uncset:
                    st.append(s)
        has_term = False
        exits = 0
        for b in cl:
            st0, en0, rng = seg.blocks[b]
            if rng and seg.insns[rng[-1]][1] in xvseg.TERM:
                has_term = True
            for s in seg.intra_edges.get(b, ()):
                if s not in cl:
                    exits += 1
        if has_term and exits == 0:
            good += 1
        else:
            bad += 1
    print("  根闭包「自洽完整过程」判据（含终止项 ∧ 无跨闭包出边）：成立 %d / %d；不成立 %d"
          % (good, len(roots), bad))
    return dict(seg=seg, unc=unc, roots=roots, allv=allv, ents=ents)


def main():
    res = {}
    for name, flib, script in WORKS:
        res[name] = explore(name, flib, script)

    # ── 4. 跨作品对照（H1 的决定性初查）────────────────────────────────────────
    #   对 ot 的每个「不可达根」，取其首块前 16B 作签名，在 otp 代码区里搜；
    #   命中即映射到 otp 的块，判该处**在 otp 里是否可达**：
    #     · 若大量 ot-不可达块在 otp 里**可达**（otp 有命令调用它）
    #       ⇒ 支持 H1「库内未被本作调用」；
    #     · 若命中处**在 otp 里也不可达**（两作都不调用）
    #       ⇒ 更支持「本作外也无人调用」（H1 的弱化 / 或 H2）。
    print("=" * 78)
    print("== 跨作品对照（H1 决定·只读） ==")
    ot = res.get("ot  (本作)")
    otp = res.get("otp (前奏诗)")
    if ot and otp:
        a, b = ot["seg"], otp["seg"]
        ab = open(WORKS[0][1], "rb").read()
        bb = open(WORKS[1][1], "rb").read()
        ah, bh = a.sob.header_end, b.sob.header_end
        b_pos = [p for (p, _o, _a, _e) in b.insns]
        import bisect as _bis
        # otp: pos -> block id, and 可达集合
        bcov, bunc = xvseg.coverage(b, otp["allv"])
        bpos2blk = {}
        for bi, (st, en, rng) in enumerate(b.blocks):
            for k in rng:
                bpos2blk[b.insns[k][0]] = bi
        b_by_pos = set(b_pos)
        found = 0
        found_reach = 0
        for r in ot["roots"]:
            st = a.blocks[r][0]
            sig = ab[ah + st: ah + st + 16]
            if len(sig) < 16:
                continue
            off = bb.find(sig, bh)
            if off < 0:
                continue
            found += 1
            rel = off - bh
            # rel 是否落在 otp 的某个指令起点（块首）？
            blk = bpos2blk.get(rel)
            if blk is None:
                # 找覆盖 rel 的块（取起点 ≤ rel 的最近块）
                j = _bis.bisect_right(b_pos, rel) - 1
                if j >= 0:
                    blk = bpos2blk.get(b_pos[j])
            if blk is not None and blk in bcov:
                found_reach += 1
        print("  ot 不可达根 94 个：16B 签名在 otp 代码区命中 %d 个；其中在 otp 内**可达**（被 otp 调用）%d 个"
              % (found, found_reach))
        # 反向：ot 可达根（120 个入口）签名在 otp 命中率（作阳性对照）
        ot_pos2blk = {}
        for bi, (st, en, rng) in enumerate(a.blocks):
            for k in rng:
                ot_pos2blk[a.insns[k][0]] = bi
        ot_cov, ot_unc = xvseg.coverage(a, ot["allv"])
        ent_blocks = sorted({ot_pos2blk[V] for V in ot["allv"] if V in ot_pos2blk})
        pf = pf_reach = 0
        for blk in ent_blocks:
            st = a.blocks[blk][0]
            sig = ab[ah + st: ah + st + 16]
            if len(sig) < 16:
                continue
            off = bb.find(sig, bh)
            if off < 0:
                continue
            pf += 1
            rel = off - bh
            j = _bis.bisect_right(b_pos, rel) - 1
            b2 = bpos2blk.get(b_pos[j]) if j >= 0 else None
            if b2 is not None and b2 in bcov:
                pf_reach += 1
        print("  【阳性对照】ot 已采纳入口 %d 个：签名在 otp 命中 %d；其中 otp 内可达 %d"
              % (len(ent_blocks), pf, pf_reach))

    print("=" * 78)
    print("== 跨作品：最长公共前缀 & 不可达块签名跨作命中（原始口径，仅供参考） ==")
    if ot:
        a = ot["seg"]
        ab = open(WORKS[0][1], "rb").read()
        ah = a.sob.header_end
        for name, flib, _s in WORKS:
            if name.startswith("ot  ") or not os.path.isfile(flib):
                continue
            bb = open(flib, "rb").read()
            n = min(len(ab), len(bb)); k = 0
            while k < n and ab[k] == bb[k]:
                k += 1
            print("  ot vs %-20s 文件 %d vs %d B；最长公共前缀 %d B" % (name, len(ab), len(bb), k))


if __name__ == "__main__":
    main()

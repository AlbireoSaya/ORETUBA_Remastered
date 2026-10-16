# -*- coding: utf-8 -*-
r"""_analyse_cases.py — 12 条反例逐条证据：PC 同槽时序 + PSV 明文（按槽时间对齐）。只读。"""
from __future__ import annotations
import collections, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE); PROJ = os.path.dirname(PRG)
sys.path.insert(0, os.path.join(PRG, "工具")); sys.path.insert(0, os.path.join(PROJ, "资源组", "工具"))
sys.dont_write_bytecode = True
import decode_sob0 as D, _research_slot as RS, _emit_other_family as EF

CASES = [
    ("ot_s01_10b", 0, "_", 300), ("ot_s02_02a", 1, "[", 500),
    ("ot_s02_03e", 0, "r", 500), ("ot_s02_03g", 1, "c_", 300),
    ("ot_s02_03g4", 1, ">2 <> c", 300), ("ot_s02_09a", 0, "<> <6", 300),
    ("ot_s02_09b", 1, "_", 300), ("ot_s02_09b", 1, "_", 100),
    ("ot_s03_03b", 0, "_l", 500), ("ot_s03_03e", 0, "l_", 300),
    ("otp_p04_01b", 0, "$ _ _", 300), ("otr_s03c_04b", 0, "$ $", 100),
]

RE_TASK = re.compile(r'^\s*\[Task(\d+)\]\s*$')
RE_CHARA = re.compile(r'^\s*\[Chara(\d+)\]\s*$')
RE_ST = re.compile(r'<<\s*(st_[^>\s]+)\s*>>', re.I)
RE_IN = re.compile(r'^\s*//\s*chr_in\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')
RE_CHR = re.compile(r'^\s*//\s*chr\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')
RE_ANIME = re.compile(r'^\s*//\s*chr_anime\s+(\d+)\s*,\s*"([^"]*)"')


def main():
    ledger = D.Ledger(D.LEDGER)
    nodes, assigns = [], []
    for src in EF.SRCS:
        n, a = EF.collect_pc2(src, ledger); nodes += n; assigns += a
    asg = collections.defaultdict(list)
    for x in assigns:
        asg[(x["scene_id"], x["slot"])].append(x)
    for v in asg.values():
        v.sort(key=lambda z: z["code"])
    smap = RS.load_scene_map()
    psv_dir = RS.PSV_SCRIPT_DIR

    for (sid, slot, ctrl, ms) in CASES:
        print("=" * 100)
        print("CASE %s slot=%s ctrl=%r ms=%s" % (sid, slot, ctrl, ms))
        ev = [x for x in nodes if x["scene_id"] == sid and x["slot"] == slot
              and x["ctrl"] == ctrl and x["ms"] == ms]
        if not ev:
            print("  (无对应控制串节点)")
            continue
        x0 = ev[0]
        code, evseq = x0["code"], x0["seq"]
        print("  PC event: %s V=0x%X code=%d seq=%s" % (x0["slot_src"], x0["V"], code, evseq))
        print("  PC 同 seq 全部控制串节点:",
              [(z["slot_src"], z["slot"], z["ctrl"], z["ms"]) for z in nodes
               if z["scene_id"] == sid and z["seq"] == evseq])
        for s in range(0, 6):
            seqs = [a for a in asg.get((sid, s), []) if a["code"] < code]
            if seqs:
                a = seqs[-1]
                print("    PC slot%d 事件前最近分配: code=%d %s %s -> %s" % (s, a["code"], a["kind"], a["name"], a["fam"]))
        # PSV
        script = smap.get(sid)
        if not script:
            print("  (无 PSV 脚本映射)"); continue
        p = os.path.join(psv_dir, script)
        if not os.path.isfile(p):
            print("  (PSV 脚本文件缺失: %s)" % script); continue
        lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        # 找该 chr_anime 宏（匹配 slot/ctrl/ms）
        ti = None
        for i, l in enumerate(lines):
            m = RE_ANIME.match(l)
            if not m or int(m.group(1)) != slot or m.group(2) != ctrl:
                continue
            # 取该宏后第一条 chr_anime 之前的行；ms 从宏行尾解析
            mm = re.search(r'"?\s*,\s*(\d+)\s*$', l)
            if mm and int(mm.group(1)) != ms:
                continue
            j = i
            while j < len(lines) and not RE_TASK.match(lines[j]):
                j += 1
            ti = j if j < len(lines) else None
            print("  PSV 宏在第 %d 行: %s (task=%s)" % (i, l.strip(),
                  RE_TASK.match(lines[j]).group(1) if ti is not None else "?"))
            break
        if ti is None:
            # ms 未匹配到：退化为 (slot,ctrl)
            for i, l in enumerate(lines):
                m = RE_ANIME.match(l)
                if m and int(m.group(1)) == slot and m.group(2) == ctrl:
                    j = i
                    while j < len(lines) and not RE_TASK.match(lines[j]):
                        j += 1
                    ti = j if j < len(lines) else None
                    print("  PSV 宏(仅 slot/ctrl 匹配, ms 未对上) 第 %d 行: %s" % (i, l.strip()))
                    break
        if ti is None:
            print("  (PSV 明文未找到该 chr_anime 宏)")
            continue
        # 宏之前各槽最近 chr_in/chr
        for s in range(0, 6):
            last_in = last_chr = None
            for k in range(0, ti):
                mi = RE_IN.match(lines[k])
                if mi and int(mi.group(1)) == s:
                    last_in = (k, mi.group(2))
                mc = RE_CHR.match(lines[k])
                if mc and int(mc.group(1)) == s:
                    last_chr = (k, mc.group(2))
            if last_in or last_chr:
                print("    PSV slot%d 宏前: chr_in=%s chr=%s" % (s, last_in, last_chr))
        # task 块
        lo, hi = ti, min(len(lines), ti + 26)
        print("  --- PSV task 块 + 前 10 行 ---")
        for k in range(max(0, ti - 10), hi):
            if lines[k].strip():
                print("    %5d| %s" % (k, lines[k].rstrip()))
        # 该 task 内 [CharaN] -> st
        end = next((k for k in range(ti + 1, len(lines)) if RE_TASK.match(lines[k])), len(lines))
        cur = None
        for k in range(ti, end):
            mc = RE_CHARA.match(lines[k])
            if mc:
                cur = mc.group(1); continue
            ms2 = RE_ST.search(lines[k])
            if ms2 and cur is not None:
                print("  PSV task [Chara%s] -> %s" % (cur, ms2.group(1)))


if __name__ == "__main__":
    main()

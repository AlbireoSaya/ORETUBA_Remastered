# -*- coding: utf-8 -*-
r"""_validate_psv2.py — 改进的 PSV 宏→Task 配对（栈式，一次 Task 弹一个宏），复核 12 条反例并重算广义命中。

旧配对（_research_slot.parse_psv_macros）：一个宏 → 其后**第一个** [TaskN]。
  缺陷：多条 `//chr_anime` 叠在同一 Task 之前时，全都指向同一个 Task（取 [Chara<slot>] 兜底会错）。
本脚本：按行序走，遇宏入队，遇 [TaskN] 出队一个宏配对（顺序一一对应）。
只读；不改他人脚本。
"""
from __future__ import annotations
import collections, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE); PROJ = os.path.dirname(PRG)
sys.path.insert(0, os.path.join(PRG, "工具")); sys.path.insert(0, os.path.join(PROJ, "资源组", "工具"))
sys.dont_write_bytecode = True
import decode_sob0 as D, _research_slot as RS, _emit_other_family as EF

RE_TASK = re.compile(r'^\s*\[Task(\d+)\]\s*$')
RE_CHARA = re.compile(r'^\s*\[Chara(\d+)\]\s*$')
RE_ST = re.compile(r'<<\s*(st_[^>\s]+)\s*>>', re.I)
RE_ANIME = re.compile(r'^\s*//\s*chr_anime\s+([^,]+),\s*"([^"]*)"\s*(?:,\s*([0-9]+))?')
RE_IN = re.compile(r'^\s*//\s*chr_in\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')
RE_CHR = re.compile(r'^\s*//\s*chr\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')

CASES = [
    ("ot_s01_10b", 0, "_", 300), ("ot_s02_02a", 1, "[", 500),
    ("ot_s02_03e", 0, "r", 500), ("ot_s02_03g", 1, "c_", 300),
    ("ot_s02_03g4", 1, ">2 <> c", 300), ("ot_s02_09a", 0, "<> <6", 300),
    ("ot_s02_09b", 1, "_", 300), ("ot_s02_09b", 1, "_", 100),
    ("ot_s03_03b", 0, "_l", 500), ("ot_s03_03e", 0, "l_", 300),
    ("otp_p04_01b", 0, "$ _ _", 300), ("otr_s03c_04b", 0, "$ $", 100),
]


def parse_ordered():
    """栈式配对：返回 [dict(scene,sid,slot,ctrl,ms,task,st,fam,task_line)]，另附每场 source 注释时间线。"""
    smap = RS.load_scene_map()
    psv_dir = RS.PSV_SCRIPT_DIR
    out = []
    src_comments = {}   # scene -> list[(line, kind, slot, name)]
    for sid, script in smap.items():
        p = os.path.join(psv_dir, script)
        if not os.path.isfile(p):
            continue
        lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        comments = []
        for i, l in enumerate(lines):
            mi = RE_IN.match(l)
            if mi:
                comments.append((i, "chr_in", int(mi.group(1)), mi.group(2)))
            mc = RE_CHR.match(l)
            if mc:
                comments.append((i, "chr", int(mc.group(1)), mc.group(2)))
        src_comments[sid] = comments
        pending = []
        for i, l in enumerate(lines):
            ma = RE_ANIME.match(l)
            if ma:
                try:
                    slot = int(ma.group(1).strip())
                except ValueError:
                    continue
                pending.append((i, slot, ma.group(2), int(ma.group(3)) if ma.group(3) else None))
                continue
            mt = RE_TASK.match(l)
            if mt and pending:
                mi_, slot, ctrl, ms = pending.pop(0)
                # 该 Task 块内 [Chara<slot>] → st
                end = next((k for k in range(i + 1, len(lines)) if RE_TASK.match(lines[k])), len(lines))
                charas, cur = {}, None
                for k in range(i, end):
                    mcc = RE_CHARA.match(lines[k])
                    if mcc:
                        cur = int(mcc.group(1)); continue
                    ms2 = RE_ST.search(lines[k])
                    if ms2 and cur is not None and cur not in charas:
                        charas[cur] = ms2.group(1)
                st = charas.get(slot)
                if st is None and len(charas) == 1:
                    st = next(iter(charas.values()))
                out.append(dict(scene_id=sid, slot=slot, ctrl=ctrl, ms=ms, task=int(mt.group(1)),
                                st=st, fam=RS.fam_of_token(st) if st else None, macro_line=mi_, task_line=i))
    return out, src_comments


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

    def fam_at(sc, slot, code):
        best = None
        for x in asg.get((sc, slot), []):
            if x["code"] >= code:
                break
            if x["slot"] == slot and x["fam"]:
                best = x
        return best

    psv2, src_comments = parse_ordered()
    by_key = collections.defaultdict(list)
    for x in psv2:
        by_key[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)

    print("=== 12 条反例：改进配对后复核 ===")
    for (sid, slot, ctrl, ms) in CASES:
        ev = [x for x in nodes if x["scene_id"] == sid and x["slot"] == slot
              and x["ctrl"] == ctrl and x["ms"] == ms]
        pc = fam_at(sid, slot, ev[0]["code"]) if ev else None
        pcf = pc["fam"] if pc else None
        # 源注释最近 chr_in/chr
        evline = ev[0]["code"] if ev else 0
        sc = src_comments.get(sid, [])
        sfi = last = None
        for (ln, kind, s, nm) in sc:
            if s == slot and kind == "chr_in":
                sfi = nm
        srcf = RS.fam_of_token(sfi) if sfi else None
        ents = by_key.get((sid, slot, ctrl, ms), [])
        newfams = sorted({e["fam"] for e in ents if e["fam"]})
        newtasks = [(e["task"], e["st"], e["fam"]) for e in ents]
        print("  %-13s slot%s ctrl=%-14r ms=%-4s | PC=%-4s (src注释 chr_in=%s->%s) | 新配对 PSV=%s %s"
              % (sid, slot, ctrl, ms, pcf, sfi, srcf, newfams, newtasks))

    # 广义：全部 PC 节点（去重 key）与新配对 PSV 比
    print("=== 广义（PC 控制串节点 vs 新配对 PSV，按 (scene,slot,ctrl,ms)）===")
    hit = miss = noGold = ambig = 0
    mism = []
    for x in nodes:
        if x["slot"] is None or not x["ctrl"] or x["ms"] is None:
            continue
        ents = by_key.get((x["scene_id"], x["slot"], x["ctrl"], x["ms"]))
        if not ents:
            noGold += 1; continue
        fams = {e["fam"] for e in ents if e["fam"]}
        if len(fams) != 1:
            ambig += 1; continue
        f = fams.pop()
        pc = fam_at(x["scene_id"], x["slot"], x["code"])
        pcf = pc["fam"] if pc else None
        if pcf == f:
            hit += 1
        else:
            miss += 1
            mism.append((x, pcf, f, ents))
    tot = hit + miss + ambig + noGold
    print("节点 %d ｜ 命中 %d ｜ 未命中 %d ｜ 无金标 %d ｜ 金标歧义 %d"
          % (tot, hit, miss, noGold, ambig))
    print("命中率(可比 %d) = %.4f" % (hit + miss, hit / max(1, hit + miss)))
    print("--- 未命中 %d ---" % len(mism))
    for x, pcf, f, ents in mism:
        print("  %-13s slot%s ctrl=%-14r ms=%-5s | PC=%-4s PSV=%-4s tasks=%s"
              % (x["scene_id"], x["slot"], x["ctrl"], x["ms"], pcf, f,
                 [(e["task"], e["st"]) for e in ents]))


if __name__ == "__main__":
    main()

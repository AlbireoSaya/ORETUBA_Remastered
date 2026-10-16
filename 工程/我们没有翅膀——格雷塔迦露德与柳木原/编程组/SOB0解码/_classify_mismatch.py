# -*- coding: utf-8 -*-
r"""_classify_mismatch.py — 对 PC/PSV 键级不一致的 16 条，逐条给出判定证据。只读。"""
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
RE_IN = re.compile(r'^\s*//\s*chr_in\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')
RE_CHR = re.compile(r'^\s*//\s*chr\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')
RE_BODYCHR = re.compile(r'^\s*//\s*chr\s+(\d+)\s*,\s*([A-Za-z0-9_]+)')


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

    def famat(sc, slot, code):
        best = None
        for x in asg.get((sc, slot), []):
            if x["code"] >= code:
                break
            if x["slot"] == slot and x["fam"]:
                best = x
        return best

    psv = EF.parse_psv_ordered()
    smap = RS.load_scene_map()
    psv_dir = RS.PSV_SCRIPT_DIR
    # 复用键级统计找 mismatch
    by_key = collections.defaultdict(list)
    for x in psv:
        by_key[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)
    nk = collections.defaultdict(list)
    for x in nodes:
        if x["slot"] is None or not x["ctrl"] or x["ms"] is None:
            continue
        nk[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)

    mism = []
    for k, xs in sorted(nk.items()):
        pfams = {(famat(k[0], k[1], x["code"]) or {}).get("fam") for x in xs}
        pfams.discard(None)
        ents = by_key.get(k, [])
        vfams = {e["fam"] for e in ents if e["fam"]}
        if len(pfams) == 1 and len(vfams) == 1 and pfams != vfams:
            mism.append((k, pfams.pop(), vfams.pop(), xs[0], ents))

    for (k, pf, vf, x, ents) in mism:
        sid, slot, ctrl, ms = k
        fa = famat(sid, slot, x["code"])
        print("=" * 96)
        print("%s slot=%s ctrl=%r ms=%s | PC=%s(%s/%s@%d)  PSVtask=%s"
              % (sid, slot, ctrl, ms, pf, fa["name"], fa["kind"], fa["code"],
                 [(e["task"], e["st"]) for e in ents]))
        script = smap.get(sid)
        if not script:
            print("  (无 PSV 映射)"); continue
        p = os.path.join(psv_dir, script)
        if not os.path.isfile(p):
            print("  (PSV 缺失)"); continue
        lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        mline = ents[0]["macro_line"]
        # 宏前该槽最近 chr_in / chr
        l_in = l_chr = None
        for q in range(0, mline):
            mi = RE_IN.match(lines[q])
            if mi and int(mi.group(1)) == slot:
                l_in = (q, mi.group(2))
            mc = RE_CHR.match(lines[q])
            if mc and int(mc.group(1)) == slot:
                l_chr = (q, mc.group(2))
        srcf = RS.fam_of_token(l_chr[1]) if l_chr else (RS.fam_of_token(l_in[1]) if l_in else None)
        print("  宏(%dL):%s" % (mline, lines[mline].strip()))
        print("  宏前该槽源注释: chr_in=%s chr=%s -> 源fam=%s" % (l_in, l_chr, srcf))
        # port task 块
        ti = ents[0]["task_line"]
        end = next((q for q in range(ti + 1, len(lines)) if RE_TASK.match(lines[q])), len(lines))
        cur = None
        for q in range(ti, end):
            mc = RE_CHARA.match(lines[q])
            if mc:
                cur = mc.group(1)
                continue
            ms2 = RE_ST.search(lines[q])
            if ms2 and cur is not None:
                print("  port task [Chara%s] -> %s" % (cur, ms2.group(1)))
            mb = RE_BODYCHR.match(lines[q])
            if mb and "chr_anime" not in lines[q]:
                print("  port task 内源注: %s" % lines[q].strip())


if __name__ == "__main__":
    main()

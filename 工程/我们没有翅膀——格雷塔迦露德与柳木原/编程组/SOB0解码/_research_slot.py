# -*- coding: utf-8 -*-
r"""_research_slot.py — 「控制串(fam) 族身份」研究（只读数据，不接入构建）。

回答：
  A) 解码器能否落 slot（chr_anime 节点 slot 位）？
  B) 旧表 op=other 能否与解码器节点 join 上（(scene,seq) / (scene,ctrl) 两键）？未命中原因分布？
  C) slot → fam 能否建成（PC 同场 chr 事件 + PSV 金标）？命中/反例/冲突？
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE)
PROJ = os.path.dirname(PRG)
sys.path.insert(0, os.path.join(PRG, "工具"))
sys.path.insert(0, os.path.join(PROJ, "资源组", "工具"))
sys.dont_write_bytecode = True
import decode_sob0 as D          # noqa: E402
import _staging_common as SC     # noqa: E402

PSV_SCRIPT_DIR = os.path.join(D.DATA_ROOT, "工程", "我们没有翅膀PSV", "脚本解包")
OLD_TABLE_DIR = os.path.join(PROJ, "资源组", "演出")
SRCS = ("ot", "otp", "otr")

# chr_anime 控制串节点：argc=4，实参序 [flag, ms, ctrl, slot]（slot=args[3]）
CHR_ANIME = {"ot": {0x18B74}, "otr": {0x18B74}, "otp": {0x15BAC}}
# l<2/r>2 家族（chr_open）
CHR_OPEN = {"ot": {0x186C8}, "otr": {0x186C8}, "otp": {0x156E8}}
# 槽位分配节点：(V, argc, name_idx, slot_idx)
CHR_IN = {"ot": (0x1C43C, 6, 4, 5), "otr": (0x1C43C, 6, 4, 5), "otp": (0x1A618, 4, 2, 3)}
CHR_DIFF = {"ot": (0x14084, 3, 1, 2), "otr": (0x14084, 3, 1, 2), "otp": (0x11078, 3, 1, 2)}

RE_MACRO = re.compile(r'^\s*//\s*chr_anime\s+([^,]+),\s*"([^"]*)"\s*(?:,\s*([0-9]+))?')
RE_TASK = re.compile(r'^\s*\[Task(\d+)\]\s*$')
RE_CHARA = re.compile(r'^\s*\[Chara(\d+)\]\s*$')
RE_ST = re.compile(r'<<\s*(st_[^>\s]+)\s*>>', re.I)


def fam_of_token(tok):
    if not tok:
        return None
    t = re.sub(r"^st_", "", tok.strip(), flags=re.I)
    f = SC.family_of(t)
    return f if (f and len(f) >= 2) else None


def parse_task_charas(lines, start, slot):
    """[Task] 块内 → 目标 sprite 的 st_ 名。

    规则：优先 `[Chara<slot>]`；该块只有一个 `[CharaN]` 时取它（PSV 端常把单 sprite 任务
    折叠成 `[Chara0]`）；多 sprite 且无 `[Chara<slot>]` ⇒ 未定（None，不猜）。
    """
    end = next((k for k in range(start + 1, len(lines)) if RE_TASK.match(lines[k])), len(lines))
    charas = {}          # N -> st 名
    cur = None
    for k in range(start, end):
        mc = RE_CHARA.match(lines[k])
        if mc:
            cur = int(mc.group(1))
            continue
        ms = RE_ST.search(lines[k])
        if ms and cur is not None and cur not in charas:
            charas[cur] = ms.group(1)
    if slot in charas:
        return charas[slot]
    if len(charas) == 1:
        return next(iter(charas.values()))
    return None


def parse_psv_macros():
    smap, tl = load_scene_map(), load_timeline()
    out = []
    for sid, script in smap.items():
        p = os.path.join(PSV_SCRIPT_DIR, script)
        if not os.path.isfile(p):
            continue
        try:
            lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        except OSError:
            continue
        n = len(lines)
        macro_of = collections.defaultdict(list)
        for i, l in enumerate(lines):
            mm = RE_MACRO.match(l)
            if not mm:
                continue
            try:
                slot = int(mm.group(1).strip())
            except ValueError:
                continue
            j = i
            while j < n and not RE_TASK.match(lines[j]):
                j += 1
            if j >= n:
                continue
            macro_of[j].append((slot, mm.group(2), int(mm.group(3)) if mm.group(3) else None))
        for j, lst in macro_of.items():
            tn = int(RE_TASK.match(lines[j]).group(1))
            row = tl.get((sid, tn))
            for k, (slot, ctrl, ms) in enumerate(lst):
                st = parse_task_charas(lines, j, slot)
                out.append(dict(scene_id=sid, script=script, task=tn, k=k, slot=slot, ctrl=ctrl,
                                ms=ms, st=st, fam=fam_of_token(st) if st else None,
                                psv_type=row.get("type") if row else None,
                                psv_time=row.get("time") if row else None,
                                psv_x=row.get("cx") if row else None,
                                psv_seq=row.get("seq") if row else None))
    return out


def collect_pc(src, ledger):
    spec = D.SOURCES[src]
    scene_path = os.path.join(D.SCENE_DIR, spec["scene"])
    anim, assigns = [], []
    with io.open(scene_path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            script = o["script"]
            if spec["prefix"] and not script.lower().startswith(spec["prefix"]):
                continue
            p = os.path.join(spec["dir"], script + spec["ext"])
            if not os.path.isfile(p):
                continue
            try:
                sob = D.Sob0(p)
            except ValueError:
                continue
            rows, info = D.extract_scene(src, o, sob, sob.slots(), None, ledger)
            for nd in info["nodes"]:
                V, args = nd["V"], nd["args"]
                if V in CHR_ANIME[src] and len(args) == 4:
                    anim.append(dict(src=src, scene_id=o["scene_id"], script=script,
                                     code=nd["code"], seq=nd["seq"], V=V,
                                     ctrl=args[2][1] if args[2][0] == "S" else None,
                                     ms=args[1][1] if args[1][0] in ("N", "A", "I") else None,
                                     slot=args[3][1] if args[3][0] in ("N", "A", "I") else None,
                                     flag=args[0][1] if args[0][0] in ("N", "A", "I") else None,
                                     fam_kind="chr_anime"))
                for tbl, kind in ((CHR_IN, "chr_in"), (CHR_DIFF, "chr_diff")):
                    if src in tbl and V == tbl[src][0] and len(args) == tbl[src][1]:
                        _v, _ac, ni, si = tbl[src]
                        if args[ni][0] == "S" and args[si][0] in ("N", "A", "I"):
                            nm = args[ni][1]
                            assigns.append(dict(src=src, scene_id=o["scene_id"], code=nd["code"],
                                                kind=kind, name=nm, slot=args[si][1],
                                                fam=fam_of_token(nm)))
                        break
    return anim, assigns


def load_timeline():
    m = {}
    with io.open(D.PSV_TIMELINE, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            try:
                m[(r["scene_id"], int(r["task"]))] = r
            except (ValueError, KeyError):
                continue
    return m


def load_scene_map():
    m = {}
    with io.open(D.PSV_MAP, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            m[r["scene_id"]] = r["script"]
    return m


def load_old():
    out = []
    for src in SRCS:
        p = os.path.join(OLD_TABLE_DIR, "演出_%s.tsv" % src)
        if not os.path.isfile(p):
            continue
        with io.open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r.get("op") == "other":
                    out.append(dict(src=src, scene_id=r["scene_id"], seq=int(r["seq"]),
                                    ctrl=r.get("arg1", ""), target=r.get("target", "")))
    return out


def is_ctrl(s):
    return bool(s) and ((s.encode("cp932", "replace") in D.CTRL_BYTES) or D.COORD_RE.match(s))


def analyse(anim, assigns, psv, old):
    st = {}
    anim_by_scene = collections.defaultdict(list)
    anim_by_seq = collections.defaultdict(list)
    anim_by_ctrl = collections.defaultdict(list)
    for x in anim:
        anim_by_scene[x["scene_id"]].append(x)
        anim_by_seq[(x["scene_id"], x["seq"])].append(x)
        if x["ctrl"]:
            anim_by_ctrl[(x["scene_id"], x["ctrl"])].append(x)
    assign_by_scene = collections.defaultdict(list)
    for x in assigns:
        assign_by_scene[x["scene_id"]].append(x)
    for v in assign_by_scene.values():
        v.sort(key=lambda z: z["code"])
    psv_by_key = collections.defaultdict(list)
    for x in psv:
        psv_by_key[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)

    st["anim_total"] = len(anim)
    st["anim_with_slot"] = sum(1 for x in anim if x["slot"] is not None)
    st["anim_with_ctrl"] = sum(1 for x in anim if x["ctrl"])
    st["assign_total"] = len(assigns)
    st["assign_with_fam"] = sum(1 for x in assigns if x["fam"])

    j = collections.Counter()
    jmiss = collections.Counter()
    jmiss_by_src = collections.defaultdict(collections.Counter)
    join_rows = []
    old_ctrl = old        # 旧表 op=other 整类即「控制串行」（与任务口径一致）
    for r in old_ctrl:
        sc, sq, c = r["scene_id"], r["seq"], r["ctrl"]
        a_seq = anim_by_seq.get((sc, sq), [])
        a_ctrl = anim_by_ctrl.get((sc, c), []) if c else []
        if a_seq:
            j["keyA_hit"] += 1
            if any(x["ctrl"] == c for x in a_seq):
                j["keyA_ctrl_eq"] += 1
        if a_ctrl:
            j["keyB_hit"] += 1
        j["total"] += 1
        if not a_seq:
            if sc not in anim_by_scene:
                jmiss["scene_no_anim"] += 1
                jmiss_by_src[r["src"]]["scene_no_anim"] += 1
            elif not a_ctrl:
                jmiss["seq_miss_and_ctrl_miss"] += 1
                jmiss_by_src[r["src"]]["seq_miss_and_ctrl_miss"] += 1
            else:
                jmiss["seq_miss_ctrl_ok"] += 1
                jmiss_by_src[r["src"]]["seq_miss_ctrl_ok"] += 1
        pick = None
        key = None
        if a_seq and len(a_seq) == 1 and a_seq[0]["ctrl"] == c:
            pick, key = a_seq[0], "seq"
        elif a_ctrl and len(a_ctrl) == 1:
            pick, key = a_ctrl[0], "ctrl"
        if pick:
            join_rows.append(dict(old=r, anim=pick, key=key))
    st["join"] = dict(j)
    st["join_miss"] = dict(jmiss)
    st["join_miss_by_src"] = {k: dict(v) for k, v in jmiss_by_src.items()}
    st["join_rows"] = join_rows

    def fam_at(scene, slot, code):
        best = None
        for x in assign_by_scene.get(scene, []):
            if x["code"] >= code:
                break
            if x["slot"] == slot and x["fam"]:
                best = x
        return best

    def fams_static(scene, slot):
        return sorted({x["fam"] for x in assign_by_scene.get(scene, [])
                       if x["slot"] == slot and x["fam"]})

    mrows, conflicts = [], collections.Counter()
    resolved = 0
    for x in anim:
        if x["slot"] is None:
            continue
        fa = fam_at(x["scene_id"], x["slot"], x["code"])
        fs = fams_static(x["scene_id"], x["slot"])
        if len(fs) > 1:
            conflicts["pc_multi_fam_slot"] += 1
        if fa:
            resolved += 1
        mrows.append(dict(src=x["src"], scene_id=x["scene_id"], slot=x["slot"],
                          fam_pc=(fa["fam"] if fa else ""),
                          fam_pc_src=(fa["name"] if fa else ""),
                          fam_pc_kind=(fa["kind"] if fa else ""),
                          fams_static="|".join(fs), n_static=len(fs)))
    st["pc_resolved"] = resolved
    st["pc_unresolved"] = sum(1 for x in anim if x["slot"] is not None) - resolved
    st["pc_conflicts"] = dict(conflicts)
    glob = collections.defaultdict(collections.Counter)
    for x in mrows:
        if x["fam_pc"]:
            glob[x["slot"]][x["fam_pc"]] += 1
    st["global_slot_fam"] = {k: dict(v.most_common(8)) for k, v in sorted(glob.items())}

    cand = []
    for jr in join_rows:
        an = jr["anim"]
        if an["slot"] is None or not an["ctrl"]:
            continue
        gold = psv_by_key.get((an["scene_id"], an["slot"], an["ctrl"], an["ms"]))
        if not gold:
            continue
        fam_gold = {g["fam"] for g in gold if g["fam"]}
        if len(fam_gold) != 1:
            continue
        fa = fam_at(an["scene_id"], an["slot"], an["code"])
        cand.append(dict(old=jr["old"], an=an, key=jr["key"], fam_pc=(fa["fam"] if fa else ""),
                         fam_src=(fa["name"] if fa else ""), kind=(fa["kind"] if fa else ""),
                         fam_gold=fam_gold.pop(), gold=gold[0]))
    random.seed(20261007)
    sample = random.sample(cand, min(len(cand), 60))
    st["cand"] = len(cand)
    st["sample_n"] = len(sample)
    st["sample_hit"] = sum(1 for s in sample if s["fam_pc"] and s["fam_pc"] == s["fam_gold"])
    st["sample_resolved"] = sum(1 for s in sample if s["fam_pc"])
    st["sample"] = sample
    st["mrows"] = mrows
    st["psv"] = psv

    # ---- E. 广义验证：全部 PC 控制串节点 vs PSV 金标（不依赖旧表可 join 性）----
    broad = []
    for x in anim:
        if x["slot"] is None or not x["ctrl"]:
            continue
        gold = psv_by_key.get((x["scene_id"], x["slot"], x["ctrl"], x["ms"]))
        if not gold:
            continue
        fams = {g["fam"] for g in gold if g["fam"]}
        if len(fams) != 1:
            continue
        fa = fam_at(x["scene_id"], x["slot"], x["code"])
        broad.append(dict(an=x, fam_pc=(fa["fam"] if fa else ""),
                          fam_src=(fa["name"] if fa else ""),
                          kind=(fa["kind"] if fa else ""), fam_gold=fams.pop(),
                          psv_type=gold[0]["psv_type"], psv_name=gold[0]["st"],
                          psv_task=gold[0]["task"]))
    st["broad"] = broad
    st["broad_n"] = len(broad)
    st["broad_resolved"] = sum(1 for x in broad if x["fam_pc"])
    st["broad_hit"] = sum(1 for x in broad if x["fam_pc"] and x["fam_pc"] == x["fam_gold"])
    return st


def _w(path, header, rows):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if r.get(c) is None else str(r.get(c, ""))
                              for c in header) + "\n")


def emit(st, anim, assigns, psv, old):
    out_dir = OLD_TABLE_DIR
    # ---------- ② join 对照（逐条旧表 op=other 行）----------
    join_idx = {}
    for jr in st["join_rows"]:
        r = jr["old"]
        join_idx[(r["src"], r["scene_id"], r["seq"], r["ctrl"])] = jr
    anim_scenes = {x["scene_id"] for x in anim}
    anim_ctrl = {(x["scene_id"], x["ctrl"]) for x in anim if x["ctrl"]}
    # fam map（PC 侧：事件处最近一次分配）
    assign_by_scene = collections.defaultdict(list)
    for x in assigns:
        assign_by_scene[x["scene_id"]].append(x)
    for v in assign_by_scene.values():
        v.sort(key=lambda z: z["code"])

    def fam_at(scene, slot, code):
        best = None
        for x in assign_by_scene.get(scene, []):
            if x["code"] >= code:
                break
            if x["slot"] == slot and x["fam"]:
                best = x
        return best

    rows = []
    for r in old:
        jr = join_idx.get((r["src"], r["scene_id"], r["seq"], r["ctrl"]))
        an = jr["anim"] if jr else None
        fa = fam_at(an["scene_id"], an["slot"], an["code"]) if (an and an["slot"] is not None) else None
        if an:
            verdict = "joined"
        elif r["scene_id"] not in anim_scenes:
            verdict = "miss_scene_no_node"      # 该场无 chr_anime/chr_open 命令节点（含 otr 未解场）
        elif (r["scene_id"], r["ctrl"]) not in anim_ctrl:
            verdict = "miss_ctrl_absent"        # 该场无此控制串节点（多为非控制串 ascii 令牌）
        else:
            verdict = "miss_seq_mismatch"       # 场内有同名节点，但 seq 对不上
        rows.append(dict(src=r["src"], scene_id=r["scene_id"], seq=r["seq"], ctrl=r["ctrl"],
                         join_key=(jr["key"] if jr else ""),
                         anim_V=("0x%X" % an["V"]) if an else "",
                         anim_ms=(an["ms"] if an else ""),
                         anim_slot=(an["slot"] if an else ""),
                         fam_pc=(fa["fam"] if fa else ""),
                         fam_src=(fa["name"] if fa else ""),
                         fam_kind=(fa["kind"] if fa else ""),
                         verdict=verdict))
    _w(os.path.join(out_dir, "join对照_旧表vs解码.tsv"),
       ["src", "scene_id", "seq", "ctrl", "join_key", "anim_V", "anim_ms", "anim_slot",
        "fam_pc", "fam_src", "fam_kind", "verdict"], rows)

    # ---------- ③ slot→fam 映射表（含冲突）----------
    psv_by_sc_slot = collections.defaultdict(set)
    for x in psv:
        if x["fam"]:
            psv_by_sc_slot[(x["scene_id"], x["slot"])].add(x["fam"])
    anim_by_sc_slot = collections.defaultdict(list)
    for x in anim:
        anim_by_sc_slot[(x["scene_id"], x["slot"])].append(x)
    mrows = []
    for (sid, slot), xs in sorted(anim_by_sc_slot.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        src = xs[0]["src"]
        a = sorted(assign_by_scene.get(sid, []), key=lambda z: z["code"])
        a = [x for x in a if x["slot"] == slot]
        fams = []
        for x in a:
            if x["fam"] and x["fam"] not in fams:
                fams.append(x["fam"])
        first = a[0] if a else None
        last = None
        for x in a:
            if x["fam"]:
                last = x
        # 末个 chr_anime 事件处的最近分配
        lastx = max(xs, key=lambda z: z["code"])
        fa = fam_at(sid, slot, lastx["code"])
        ps = sorted(psv_by_sc_slot.get((sid, slot), set()))
        agree = ""
        if fa and ps:
            agree = "1" if fa["fam"] in ps else "0"
        mrows.append(dict(src=src, scene_id=sid, slot=slot, n_chr_anime=len(xs),
                          n_assign=len(a), fam_pc_first=(first["fam"] if first and first["fam"] else ""),
                          fam_pc_last=(last["fam"] if last else ""),
                          fam_pc_at_last_event=(fa["fam"] if fa else ""),
                          fam_pc_set="|".join(fams), n_fam_pc=len(fams),
                          fam_psv_set="|".join(ps), n_fam_psv=len(ps),
                          conflict_pc=("1" if len(fams) > 1 else "0"),
                          psv_agree=agree,
                          evidence=";".join("%s=%s" % (x["kind"], x["name"]) for x in a[:4])))
    _w(os.path.join(out_dir, "slot族映射.tsv"),
       ["src", "scene_id", "slot", "n_chr_anime", "n_assign", "fam_pc_first", "fam_pc_last",
        "fam_pc_at_last_event", "fam_pc_set", "n_fam_pc", "fam_psv_set", "n_fam_psv",
        "conflict_pc", "psv_agree", "evidence"], mrows)

    # ---------- ④ 抽样对照（逐条 PSV 金标）----------
    srows = []
    for s in st["sample"]:
        an = s["an"]
        srows.append(dict(src=an["src"], scene_id=an["scene_id"], seq=an["seq"],
                          ctrl=an["ctrl"], ms=an["ms"], slot=an["slot"],
                          fam_pc=s["fam_pc"], fam_src=s["fam_src"], fam_kind=s["kind"],
                          fam_psv=s["fam_gold"], psv_task=s["gold"]["task"],
                          psv_st=s["gold"]["st"], psv_type=s["gold"]["psv_type"],
                          match=("1" if (s["fam_pc"] and s["fam_pc"] == s["fam_gold"]) else "0")))
    _w(os.path.join(out_dir, "slot归属_抽样对照.tsv"),
       ["src", "scene_id", "seq", "ctrl", "ms", "slot", "fam_pc", "fam_src", "fam_kind",
        "fam_psv", "psv_task", "psv_st", "psv_type", "match"], srows)

    # ---------- ④b 广义对照（全部可比控制串节点）----------
    brows = []
    for x in st["broad"]:
        an = x["an"]
        brows.append(dict(src=an["src"], scene_id=an["scene_id"], seq=an["seq"], ctrl=an["ctrl"],
                          ms=an["ms"], slot=an["slot"], fam_pc=x["fam_pc"], fam_src=x["fam_src"],
                          fam_kind=x["kind"], fam_psv=x["fam_gold"], psv_task=x["psv_task"],
                          psv_st=x["psv_name"], psv_type=x["psv_type"],
                          match=("1" if (x["fam_pc"] and x["fam_pc"] == x["fam_gold"]) else "0")))
    _w(os.path.join(out_dir, "slot归属_广义对照.tsv"),
       ["src", "scene_id", "seq", "ctrl", "ms", "slot", "fam_pc", "fam_src", "fam_kind",
        "fam_psv", "psv_task", "psv_st", "psv_type", "match"], brows)
    return dict(join=len(rows), map_rows=len(mrows), sample=len(srows), broad=len(brows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args()
    ledger = D.Ledger(D.LEDGER)
    anim, assigns = [], []
    for src in SRCS:
        an, asg = collect_pc(src, ledger)
        anim += an
        assigns += asg
    psv = parse_psv_macros()
    old = load_old()
    st = analyse(anim, assigns, psv, old)

    print("=== A. slot 覆盖 ===")
    print("控制串节点 %d ｜ 有 slot %d ｜ 有 ctrl %d"
          % (st["anim_total"], st["anim_with_slot"], st["anim_with_ctrl"]))
    print("slot 分配节点 %d ｜ 有 fam %d" % (st["assign_total"], st["assign_with_fam"]))
    print("=== B. join（旧表 op=other 控制串行 %d）===" % st["join"]["total"])
    print("keyA(seq)命中 %d ｜ 其中 ctrl 相等 %d ｜ keyB(ctrl)命中 %d"
          % (st["join"]["keyA_hit"], st["join"]["keyA_ctrl_eq"], st["join"]["keyB_hit"]))
    print("seq 未命中原因:", st["join_miss"])
    print("=== C. slot→fam（PC 侧）===")
    print("可解析 %d ｜ 不可解析 %d ｜ 冲突(slot 多族) %s"
          % (st["pc_resolved"], st["pc_unresolved"], st["pc_conflicts"]))
    print("全局 slot→fam:", json.dumps(st["global_slot_fam"], ensure_ascii=False))
    print("=== D. 抽样对照 PSV ===")
    print("候选 %d ｜ 抽样 %d ｜ PC 可解析 %d ｜ 命中 %d"
          % (st["cand"], st["sample_n"], st["sample_resolved"], st["sample_hit"]))
    print("=== E. 广义验证（全部控制串节点 vs PSV）===")
    print("可比对 %d ｜ PC 可解析 %d ｜ 命中 %d"
          % (st["broad_n"], st["broad_resolved"], st["broad_hit"]))
    bmiss = [x for x in st["broad"] if not (x["fam_pc"] and x["fam_pc"] == x["fam_gold"])]
    print("--- 广义未命中 %d 条 ---" % len(bmiss))
    for x in bmiss:
        an = x["an"]
        print("  %-14s slot=%s ctrl=%-14r ms=%s | PC=%-5s(%s/%s) PSV=%-5s %s(%s) task=%s"
              % (an["scene_id"], an["slot"], an["ctrl"], an["ms"], x["fam_pc"] or "-",
                 x["fam_src"] or "-", x["kind"] or "-", x["fam_gold"], x["psv_name"],
                 x["psv_type"], x["psv_task"]))
    # 未 join 的旧表行：ctrl 是否根本不是控制串
    seqset = {(x["scene_id"], x["seq"]) for x in anim}
    cset = {(x["scene_id"], x["ctrl"]) for x in anim if x["ctrl"]}
    missrows = [r for r in old if (r["scene_id"], r["seq"]) not in seqset]
    n_notctrl = sum(1 for r in missrows if not is_ctrl(r["ctrl"])
                    and (r["scene_id"], r["ctrl"]) not in cset)
    print("未 join（按 seq）旧表行 %d ｜ 其中 ctrl 非控制串/场内有同名节点者除外后 = %d"
          % (len(missrows), n_notctrl))
    if a.emit:
        info = emit(st, anim, assigns, psv, old)
        print("已落盘:", info)
    # 冲突分布 by 源
    cc = collections.Counter()
    for x in st["mrows"]:
        if x["n_static"] > 1:
            cc[x["src"]] += 1
    print("多族 slot（static 冲突）by src:", dict(cc))
    print("--- 抽样逐条（前 20）---")
    for i, s in enumerate(st["sample"][:20]):
        an = s["an"]
        print(" %2d %-14s seq=%-4s ctrl=%-8r slot=%s ms=%-5s | PC=%-5s(%s/%s) PSV=%-5s %s"
              % (i, s["old"]["scene_id"], s["old"]["seq"], an["ctrl"], an["slot"], an["ms"],
                 s["fam_pc"] or "-", s["fam_src"] or "-", s["kind"] or "-",
                 s["fam_gold"], s["gold"]["psv_type"]))
    miss = [s for s in st["sample"] if not (s["fam_pc"] and s["fam_pc"] == s["fam_gold"])]
    print("--- 抽样未命中 %d 条 ---" % len(miss))
    for s in miss[:10]:
        an = s["an"]
        print("  %-14s slot=%s ctrl=%-8r ms=%s PC=%r(%s) PSV=%s %s(%s)"
              % (s["old"]["scene_id"], an["slot"], an["ctrl"], an["ms"], s["fam_pc"],
                 s["fam_src"], s["fam_gold"], s["gold"]["st"], s["gold"]["psv_type"]))


if __name__ == "__main__":
    main()

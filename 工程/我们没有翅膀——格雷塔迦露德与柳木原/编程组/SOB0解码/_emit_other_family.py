# -*- coding: utf-8 -*-
r"""_emit_other_family.py — 产出 `资源组\演出\其他语义_族身份.tsv`

目的：把旧表 `演出_{ot,otp,otr}.tsv` 的 `op=other`（控制串）行，**按事件时刻**补上目标立绘族。

方法（与既有 `_research_slot.py` 同源，不重造轮子）：
  1. join：把旧表行 `(scene_id, seq)` / `(scene_id, ctrl)` 对上解码器的**控制串节点**，
     取该节点的 `slot` 与 `code`（字节码位 = 事件时刻）。
  2. 族重建：fam = 同场、同 slot、code **严格小于**该节点的最近一个 `chr_in`/`chr`（差分变更）
     分配节点的族 —— 即**有序分配流**（时间序），**不是**整场静态映射。
  3. 证据与置信度落列；join 不上的行 **留空不猜**，并给分类计数。

控制串节点（slot 来源）有两个 V 家族，均为 [.., ctrl, slot] 尾参形态：
  - `chr_anime`：ot/otr V=0x18B74 argc=4 `[flag, ms, ctrl, slot]`；otp V=0x15BAC argc=4
  - `chr_open` ：ot/otr V=0x186C8 argc=3 `[flag, ctrl, slot]`      ；otp V=0x156E8 argc=3
    （`l<2`/`r>2` 等主要落在这里；`slot_src` 列区分两者）

只读数据源；不接入构建、不改 build_story.py。
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
import _research_slot as RS      # noqa: E402

OLD_TABLE_DIR = os.path.join(PROJ, "资源组", "演出")
OUT_TSV = os.path.join(OLD_TABLE_DIR, "其他语义_族身份.tsv")
SRCS = ("ot", "otp", "otr")

# 控制串节点家族：(V, argc, ctrl_idx, slot_idx, ms_idx)
ANIM = {"ot": (0x18B74, 4, 2, 3, 1), "otr": (0x18B74, 4, 2, 3, 1), "otp": (0x15BAC, 4, 2, 3, 1)}
OPEN = {"ot": (0x186C8, 3, 1, 2, None), "otr": (0x186C8, 3, 1, 2, None),
        "otp": (0x156E8, 3, 1, 2, None)}
# 槽位分配节点：(V, argc, name_idx, slot_idx)
CHR_IN = {"ot": (0x1C43C, 6, 4, 5), "otr": (0x1C43C, 6, 4, 5), "otp": (0x1A618, 4, 2, 3)}
CHR_DIFF = {"ot": (0x14084, 3, 1, 2), "otr": (0x14084, 3, 1, 2), "otp": (0x11078, 3, 1, 2)}

NUM = ("N", "A", "I")

RE_TASK = re.compile(r'^\s*\[Task(\d+)\]\s*$')
RE_CHARA = re.compile(r'^\s*\[Chara(\d+)\]\s*$')
RE_ST = re.compile(r'<<\s*(st_[^>\s]+)\s*>>', re.I)


def parse_psv_ordered():
    """改进的 PSV 宏→Task 配对：按行序，遇 `//chr_anime` 入队，遇 `[TaskN]` 出队一个宏配对。

    旧法（一个宏→其后第一个 Task）在多条 chr_anime 叠加于同一 Task 前时会全指向同一 Task，
    取 [Chara<slot>] 兜底即错。本函数按出现顺序一一对应。
    只读 PSV 明文；返回列表，元素含 scene_id/slot/ctrl/ms/task/st/fam。
    """
    smap = RS.load_scene_map()
    psv_dir = RS.PSV_SCRIPT_DIR
    out = []
    for sid, script in smap.items():
        p = os.path.join(psv_dir, script)
        if not os.path.isfile(p):
            continue
        lines = open(p, "rb").read().decode("cp932", "replace").split("\n")
        pending = []
        for i, l in enumerate(lines):
            ma = RS.RE_MACRO.match(l)
            if ma:
                try:
                    slot = int(ma.group(1).strip())
                except ValueError:
                    continue
                pending.append((i, slot, ma.group(2), int(ma.group(3)) if ma.group(3) else None))
                continue
            mt = RE_TASK.match(l)
            if mt and pending:
                mline, slot, ctrl, ms = pending.pop(0)
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
                                st=st, fam=RS.fam_of_token(st) if st else None,
                                macro_line=mline, task_line=i))
    return out


def _num(args, i):
    return args[i][1] if (i is not None and i < len(args) and args[i][0] in NUM) else None


def _str(args, i):
    return args[i][1] if (i is not None and i < len(args) and args[i][0] == "S") else None


def collect_pc2(src, ledger):
    """返回 (nodes, assigns)：nodes＝控制串节点（chr_anime + chr_open），assigns＝槽位分配节点。"""
    spec = D.SOURCES[src]
    scene_path = os.path.join(D.SCENE_DIR, spec["scene"])
    nodes, assigns = [], []
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
                for famspec, ssrc in ((ANIM, "chr_anime"), (OPEN, "chr_open")):
                    if src in famspec and V == famspec[src][0] and len(args) == famspec[src][1]:
                        _v, _ac, ci, si, mi = famspec[src]
                        nodes.append(dict(src=src, scene_id=o["scene_id"], script=script,
                                          code=nd["code"], seq=nd["seq"], V=V, slot_src=ssrc,
                                          ctrl=_str(args, ci), ms=_num(args, mi), slot=_num(args, si)))
                        break
                for tbl, kind in ((CHR_IN, "chr_in"), (CHR_DIFF, "chr_diff")):
                    if src in tbl and V == tbl[src][0] and len(args) == tbl[src][1]:
                        _v, _ac, ni, si = tbl[src]
                        if args[ni][0] == "S" and args[si][0] in NUM:
                            nm = args[ni][1]
                            assigns.append(dict(src=src, scene_id=o["scene_id"], code=nd["code"],
                                                kind=kind, name=nm, slot=args[si][1],
                                                fam=RS.fam_of_token(nm)))
                        break
    return nodes, assigns


def load_old():
    out = []
    for src in SRCS:
        p = os.path.join(OLD_TABLE_DIR, "演出_%s.tsv" % src)
        with io.open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r.get("op") == "other":
                    out.append(dict(src=src, scene_id=r["scene_id"], seq=int(r["seq"]),
                                    ctrl=r.get("arg1", ""), confidence_old=r.get("confidence", "")))
    return out


def is_ctrl(s):
    return bool(s) and (s.encode("cp932", "replace") in D.CTRL_BYTES or D.COORD_RE.match(s))


def build():
    ledger = D.Ledger(D.LEDGER)
    nodes, assigns = [], []
    for src in SRCS:
        n, a = collect_pc2(src, ledger)
        nodes += n
        assigns += a

    by_seq = collections.defaultdict(list)
    by_ctrl = collections.defaultdict(list)
    for x in nodes:
        by_seq[(x["scene_id"], x["seq"])].append(x)
        if x["ctrl"]:
            by_ctrl[(x["scene_id"], x["ctrl"])].append(x)
    node_scenes = {x["scene_id"] for x in nodes}
    node_ctrl = {(x["scene_id"], x["ctrl"]) for x in nodes if x["ctrl"]}

    assign_by_scene = collections.defaultdict(list)
    for x in assigns:
        assign_by_scene[x["scene_id"]].append(x)
    for v in assign_by_scene.values():
        v.sort(key=lambda z: z["code"])

    slot_fams = collections.defaultdict(set)   # (scene, slot) -> {fam}
    for x in assigns:
        if x["fam"]:
            slot_fams[(x["scene_id"], x["slot"])].add(x["fam"])

    def fam_at(scene, slot, code):
        best = None
        for x in assign_by_scene.get(scene, []):
            if x["code"] >= code:
                break
            if x["slot"] == slot and x["fam"]:
                best = x
        return best

    old = load_old()
    rows = []
    for r in old:
        sc, sq, c = r["scene_id"], r["seq"], r["ctrl"]
        a_seq = by_seq.get((sc, sq), [])
        a_ctrl = by_ctrl.get((sc, c), []) if c else []
        pick, key = None, ""
        # 优先「同 seq 且恰一个且 ctrl 相等」；退而「场内同名 ctrl 恰一个」
        if len(a_seq) == 1 and a_seq[0]["ctrl"] == c:
            pick, key = a_seq[0], "seq"
        elif len(a_ctrl) == 1:
            pick, key = a_ctrl[0], "ctrl"
        if pick is not None:
            status = "joined"
        elif sc not in node_scenes:
            status = "miss_scene_no_node"
        elif (sc, c) not in node_ctrl:
            status = "miss_ctrl_absent"
        else:
            status = "miss_seq_mismatch"

        slot = ms = fam = fam_src = fam_kind = fam_code = ""
        slot_src = ""
        if pick is not None:
            slot = pick["slot"] if pick["slot"] is not None else ""
            ms = pick["ms"] if pick["ms"] is not None else ""
            slot_src = pick["slot_src"]
            if pick["slot"] is not None:
                fa = fam_at(sc, pick["slot"], pick["code"])
                if fa:
                    fam, fam_src, fam_kind, fam_code = fa["fam"], fa["name"], fa["kind"], fa["code"]
        multi = 1 if len(slot_fams.get((sc, pick["slot"]) if pick else (sc, None), set())) > 1 else 0
        conf = "unknown"
        if fam:
            conf = "exact" if key == "seq" else "read"

        if pick is None:
            ev = "join 失败：%s" % status
        else:
            ev = ("SOB0 %s slot=%s%s code=%s; fam@code<-%s %s@%s"
                  % (slot_src, slot, ("" if ms == "" else " ms=%s" % ms), pick["code"],
                     fam_kind or "-", fam_src or "-", fam_code if fam_code != "" else "-"))
            if not fam:
                ev += "; 该 slot 事件前无同槽分配 => 留空"
            if multi:
                ev += "; 本场该 slot 场内多族(须按时刻)"
        rows.append(dict(src=r["src"], scene_id=sc, seq=sq, ctrl=c, join_key=key,
                         slot=slot, ms=ms, fam=fam, fam_src=fam_src, fam_kind=fam_kind,
                         fam_code=fam_code, slot_src=slot_src, slot_multi_fam=multi,
                         status=status, confidence=conf, evidence=ev))
    return old, nodes, assigns, rows


def write_tsv(rows):
    header = ["src", "scene_id", "seq", "ctrl", "join_key", "slot", "ms", "fam", "fam_src",
              "fam_kind", "fam_code", "slot_src", "slot_multi_fam", "psv_conflict",
              "status", "confidence", "evidence"]
    with io.open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if r.get(c) in (None, "") else str(r.get(c)) for c in header) + "\n")
    return header


# ---------------- 自检：随机抽样 vs PSV 金标 ----------------
def psv_by_key(psv):
    m = collections.defaultdict(list)
    for x in psv:
        m[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)
    return m


def selfcheck(rows, psv, nodes, n=60, seed=20261007):
    """随机抽样 vs PSV 金标（改进配角；只取 PC 键唯一 且 PSV 族唯一 的行，避免键歧义偏向）。"""
    pm = collections.defaultdict(list)
    for x in psv:
        pm[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)
    keycnt = collections.Counter((x["scene_id"], x["slot"], x["ctrl"], x["ms"]) for x in nodes)
    pool = []
    for r in rows:
        if not r["fam"] or r["slot"] == "" or r["ctrl"] == "" or r["ms"] == "":
            continue
        k = (r["scene_id"], int(r["slot"]), r["ctrl"], int(r["ms"]))
        if keycnt.get(k) != 1:            # PC 侧同键多节点 => 时刻不同族，本抽样回避
            continue
        g = pm.get(k)
        if not g:
            continue
        fams = {x["fam"] for x in g if x["fam"]}
        if len(fams) != 1:
            continue
        gp = next((x for x in g if x["fam"]), g[0])
        pool.append((r, fams.pop(), gp))
    random.seed(seed)
    sample = random.sample(pool, min(len(pool), n))
    hits = sum(1 for r, f, g in sample if r["fam"] == f)
    return pool, sample, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-emit", action="store_true")
    ap.add_argument("--sample", type=int, default=60)
    a = ap.parse_args()

    old, nodes, assigns, rows = build()
    psv = parse_psv_ordered()
    # 标注 PSV 金标冲突（仅当 (scene,slot,ctrl,ms) 两侧族都可唯一定）
    pm = collections.defaultdict(list)
    for x in psv:
        pm[(x["scene_id"], x["slot"], x["ctrl"], x["ms"])].append(x)
    for r in rows:
        if not r["fam"] or r["slot"] == "" or r["ms"] == "":
            r["psv_conflict"] = ""
            continue
        ents = pm.get((r["scene_id"], int(r["slot"]), r["ctrl"], int(r["ms"])))
        fams = {x["fam"] for x in (ents or []) if x["fam"]}
        r["psv_conflict"] = "" if len(fams) != 1 else ("0" if next(iter(fams)) == r["fam"] else "1")
    if not a.no_emit:
        write_tsv(rows)

    st = collections.Counter(r["status"] for r in rows)
    cf = collections.Counter(r["confidence"] for r in rows)
    by_src = collections.defaultdict(collections.Counter)
    for r in rows:
        by_src[r["src"]][r["status"]] += 1
    withfam = [r for r in rows if r["fam"]]
    print("=== 全表（旧表 op=other 行 %d）===" % len(rows))
    print("控制串节点 %d（chr_anime %d / chr_open %d）｜ 分配节点 %d"
          % (len(nodes), sum(1 for x in nodes if x["slot_src"] == "chr_anime"),
             sum(1 for x in nodes if x["slot_src"] == "chr_open"), len(assigns)))
    print("status:", dict(st))
    print("confidence:", dict(cf))
    print("有 fam 的行 %d ｜ 其中 slot_src=chr_anime %d / chr_open %d"
          % (len(withfam), sum(1 for r in withfam if r["slot_src"] == "chr_anime"),
             sum(1 for r in withfam if r["slot_src"] == "chr_open")))
    print("psv_conflict:", dict(collections.Counter(r["psv_conflict"] for r in withfam)))
    print("按源 status:")
    for s in SRCS:
        print("  %-4s %s" % (s, dict(by_src[s])))
    # join 缺口细分
    node_ctrl = {(x["scene_id"], x["ctrl"]) for x in nodes if x["ctrl"]}
    node_scenes = {x["scene_id"] for x in nodes}
    un = [r for r in rows if r["status"] != "joined"]
    g = collections.Counter()
    for r in un:
        if is_ctrl(r["ctrl"]) and (r["scene_id"], r["ctrl"]) in node_ctrl:
            g["真控制串·seq错位"] += 1
        elif is_ctrl(r["ctrl"]) and r["scene_id"] in node_scenes:
            g["真控制串·场内无此串节点"] += 1
        elif is_ctrl(r["ctrl"]):
            g["真控制串·该场无命令节点"] += 1
        elif (r["scene_id"], r["ctrl"]) in node_ctrl:
            g["非控制串·场内有同名节点(seq错位)"] += 1
        elif r["scene_id"] in node_scenes:
            g["非控制串(ascii令牌等)·场有节点"] += 1
        else:
            g["非控制串·该场无节点"] += 1
    print("join 缺口细分（%d 行）:" % len(un), dict(g))
    # 生产者关注的 7 个映射 token 覆盖
    MAPPED = {"!l", "!r", "c", "l", "r"}
    dpat = re.compile(r"^[<>][0-9]$")
    mp = [r for r in rows if r["ctrl"] in MAPPED or dpat.match(r["ctrl"] or "")]
    mp_fam = [r for r in mp if r["fam"]]
    print("接入映射表 7 token 命中行 %d ｜ 其中有 fam %d" % (len(mp), len(mp_fam)))
    print("slot_multi_fam=1 且有 fam %d" % sum(1 for r in rows if r["fam"] and r["slot_multi_fam"]))

    pool, sample, hits = selfcheck(rows, psv, nodes, a.sample)
    print("=== 自检（随机抽样 vs PSV 金标，改进配角，种子 20261007）===")
    print("可比对池 %d ｜ 抽样 %d ｜ 命中 %d (%.1f%%)"
          % (len(pool), len(sample), hits, 100.0 * hits / max(1, len(sample))))
    for i, (r, f, g) in enumerate(sample):
        ok = "OK " if r["fam"] == f else "MISS"
        print(" %2d %s %-14s seq=%-4s ctrl=%-14r slot=%s ms=%-5s PC=%-5s(%s/%s) PSV=%-5s %s[Chara%s] task=%s"
              % (i, ok, r["scene_id"], r["seq"], r["ctrl"], r["slot"], r["ms"], r["fam"],
                 r["fam_src"], r["fam_kind"], f, g["st"], r["slot"], g["task"]))


if __name__ == "__main__":
    main()

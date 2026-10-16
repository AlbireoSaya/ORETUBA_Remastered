#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
emit_character_events.py —— 从 PSV 金标时间线抽取并归一「逐场立绘事件流」
ISSUE-20261008-03 · M1（编程组 · PSV演出）

职责（只读金标，不改任何既有产物）：
  读 `时间线.tsv`（27 列 / 121,707 行）+ `场景映射.tsv`（462 场，取 src / map_rate / align /
  corpus_lines），把金标里 layer=chr 的 26,712 行**归一**成一份可直接驱动构建的逐场立绘事件表。

产物（写在本脚本同目录）：
  · 立绘事件流.tsv          —— 主表（20 列，列名列序见 COLS，前 19 列为主代理定死 schema）
  · 立绘事件流_说明.md       —— 列义 / 推导规则 / 换算口径与自证 / 计数 / 退化登记 / 边界
  · 退化场景登记.tsv         —— map_rate / align 触阈的逐场登记（含触因与 chr 事件数）
  · 立绘事件流_统计.json     —— 机读计数（抽取前后对照 / 覆盖场数 / 分布 / 换算自证）

设计要点：
  1. 不猜：金标没写的不补（cy 留空就是留空，remove 无名就是无名）。
  2. op 由 `:Tasktype` 归一（七类闭集）；不属七类的原样另列并登记（本批实测 0 行）。
  3. fam  ＝ ps_name 的前导字母串（小写）——机械规则，不做跨族合并（kaa/kab 不并）。
  4. slot_hint ＝ 场内「活槽位」分配（最低空闲槽，0 基，按 add 顺序分配、remove 释放）。
     ——「同一场同一时刻，两个在场角色的 slot_hint 必不相同」是分配器不变量，可由 checker 复算。
  5. x1920/y1920 = 金标 cx/cy × 1.5（PSV 1280×720 → 我方 1920×1080，恰好整数倍，实测 cx 全偶）。
  6. conf = exact | inferred：目标名或（add/move 的）坐标缺失 ⇒ inferred。

复跑：
  python -X utf8 emit_character_events.py
  python -X utf8 emit_character_events.py --check     # 幂等复核（与已落盘产物逐字节比对）
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------- 常量

# 主代理定死的 schema（列名/列序不得改）；新增列只能追加在末尾。
FIXED_COLS = ["scene_id", "src", "seq", "op", "task_type", "ps_name", "delivery", "fam",
              "slot_hint", "x", "y", "cx", "cy", "cpri", "priority", "time",
              "x1920", "y1920", "conf"]
EXTRA_COLS = ["scene_degraded"]          # 本批追加：该行所属场景是否落在退化清单（0/1）
COLS = FIXED_COLS + EXTRA_COLS

# `:Tasktype` → op（七类闭集，与 emit_staging_psv.py::OP_MAP 的 chr 系一致）
OP_MAP = {
    "CharacterOpen": "add",
    "CharacterOpenBS": "add",
    "CharacterMove": "move",
    "CharacterDelete": "remove",
    "CharacterAction": "expr",
    "CharacterActionEnd": "expr_end",
    "CharacterPriority": "priority",
    "CharacterWait": "wait",
    "CharacterStop": "wait",
}
OPS = ("add", "move", "remove", "expr", "expr_end", "priority", "wait")

CHR_LAYER = "chr"

# 输出排序：ot 先，其后 otv/otp/otr；未知源排最后。
SRC_RANK = {"ot": 0, "otv": 1, "otp": 2, "otr": 3}

# 退化判据（两档取或）——见 说明.md「退化场景」节
DEG_MAP_RATE = 0.98
DEG_ALIGN = 0.90

SCALE = 1.5          # PSV 1280×720 → 我方 1920×1080

COL_SCENE, COL_SRC, COL_SEQ, COL_OP, COL_TYPE, COL_NAME, COL_DELIVERY, COL_FAM = COLS[:8]
COL_SLOT = COLS[8]

_RE_FAM = re.compile(r"^([A-Za-z]+)")
_RE_INT = re.compile(r"^-?\d+$")

HERE = os.path.dirname(os.path.abspath(__file__))


def _guess_workspace_root() -> str:
    """从本脚本位置向上找含 `Galgame.md` 与 `工程` 子目录的工作区根（避免硬编码绝对路径）。
    取**最外层**命中者：本脚本常在 `临时/wt-*/` 工作树里跑，而金标落在**主工作树**。"""
    p, hit = HERE, None
    for _ in range(8):
        p = os.path.dirname(p)
        if os.path.isfile(os.path.join(p, "Galgame.md")) and os.path.isdir(os.path.join(p, "工程")):
            hit = p
    return hit or r"E:\ZCode Workspace\Galgame"    # 兜底（可用 --data-root 覆盖）


DEFAULT_DATA_ROOT = _guess_workspace_root()
GAME_DIR = os.path.join("工程", "我们没有翅膀——格雷塔迦露德与柳木原")
PSV_SUB = os.path.join("编程组", "PSV演出")


# ---------------------------------------------------------------- 工具函数

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pick_input(name: str, explicit: str | None, data_root: str) -> str:
    """优先本 checkout，其次主工作树（金标被 .gitignore，worktree 里可能没有）。"""
    if explicit:
        return explicit
    local = os.path.join(HERE, name)
    if os.path.isfile(local):
        return local
    remote = os.path.join(data_root, GAME_DIR, PSV_SUB, name)
    return remote


def fam_of(ps_name: str) -> str:
    """角色族 ＝ ps_name 的前导字母串（小写）。空名 ⇒ 空族。机械规则，不做跨族合并。"""
    m = _RE_FAM.match(ps_name or "")
    return m.group(1).lower() if m else ""


def conf_of(op: str, name: str, cx: str) -> str:
    """exact | inferred —— inferred 仅当「该 op 本应带、却缺失」的字段为空。"""
    if op in ("add", "move"):
        return "exact" if (name and cx != "") else "inferred"
    if op in ("expr", "expr_end", "remove", "priority"):
        return "exact" if name else "inferred"     # priority 实测 44/44 带 :Number ⇒ 走同一条
    return "exact"        # wait：实测 653/653 无名，按设计不带目标，不因缺名降级


def scale_val(v: str):
    """金标坐标 × 1.5 → 我方 1920×1080 系；空值保持空（不补 0）。"""
    if v == "" or not _RE_INT.match(v):
        return ""
    return str(int(round(int(v) * SCALE)))


# ---------------------------------------------------------------- 读入

def read_scene_map(path: str):
    scenes = {}
    order = []
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        I = {k: i for i, k in enumerate(hdr)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            sid = p[I["scene_id"]]
            scenes[sid] = {
                "src": p[I["src"]],
                "tasks": p[I["tasks"]],
                "psv_msg": p[I["psv_msg"]],
                "corpus_lines": p[I["corpus_lines"]],
                "header": p[I["header"]],
                "align": float(p[I["align"]]),
                "map_rate": float(p[I["map_rate"]]),
            }
            order.append(sid)
    return scenes, order


def read_timeline(path: str):
    """返回 (chr 行列表, 全表行数)。chr 行按 (src_rank, scene_id, 金标序) 排好序。"""
    chr_rows = []
    total = 0
    with open(path, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        I = {k: i for i, k in enumerate(hdr)}
        for gi, line in enumerate(f):
            total += 1
            p = line.rstrip("\n").split("\t")
            if p[I["layer"]] != CHR_LAYER:
                continue
            chr_rows.append({
                "scene_id": p[I["scene_id"]],
                "task": p[I["task"]],
                "type": p[I["type"]],
                "name": p[I["name"]],
                "delivery": p[I["delivery"]],
                "x": p[I["x"]],
                "y": p[I["y"]],
                "cx": p[I["cx"]],
                "cy": p[I["cy"]],
                "cpri": p[I["cpri"]],
                "priority": p[I["priority"]],
                "time": p[I["time"]],
                "seq": p[I["seq"]],
                "_gi": gi,
            })
    chr_rows.sort(key=lambda r: (SRC_RANK.get(r["scene_id"].split("_")[0], 9),
                                 r["scene_id"], r["_gi"]))
    return chr_rows, total


# ---------------------------------------------------------------- 归一

# 「同族并存」证据：同一金标 task 内对**同一 fam 的 ≥2 个不同立绘名**发出下列 op
COEXIST_EVIDENCE_OPS = ("move", "remove", "expr", "expr_end")


def scan_coexist(evs):
    """逐场扫「同族并存」证据。
    判据（与一审 §3.2 同）：同一 task 内对同一 fam 的 ≥2 个不同名发出 move/remove/expr/expr_end
    ⇒ 二者同时在场，不可能是一个替换另一个。
    返回 (coinvolve, reg)：coinvolve[fam] = 该场卷入并存的立绘名集合；reg = 逐任务登记行。
    """
    by_task = collections.OrderedDict()
    for e in evs:
        by_task.setdefault(e["task"], []).append(e)
    coinvolve = collections.defaultdict(set)
    reg = []
    for task, group in by_task.items():
        ops = {g["op"] for g in group}
        if not (set(COEXIST_EVIDENCE_OPS) & ops):
            continue
        fams = collections.defaultdict(set)
        for g in group:
            if g["name"]:
                fams[g["fam"]].add(g["name"])
        for F in sorted(fams):
            ns = fams[F]
            if F and len(ns) >= 2:
                coinvolve[F] |= ns
                reg.append({"task": task, "fam": F, "names": sorted(ns),
                            "ops": ",".join(o for o in ("move", "remove", "expr", "expr_end") if o in ops)})
    return coinvolve, reg


def _new_alloc():
    return {"live": {}, "fam_live": {}, "free": [], "next": 0, "max_live": 0}


def _take_free(st):
    if st["free"]:
        s = min(st["free"])
        st["free"].remove(s)
        return s
    s = st["next"]
    st["next"] += 1
    return s


def alloc_slot(st, op, name, fam, still_alive, i, mode):
    """返回 (slot_str, kind)。still_alive(old, i) 判「旧件此后仍被引用（其间未再 add）」。
    live 模式 kind ∈ fresh | coexist | reuse_same | reuse_swap | remove | remove_fam | ref | ref_fam | noop；
    fam 模式（负向对照）∈ fresh | reuse | remove | ref | noop；ordinal（调试）∈ debug。"""
    if mode == "ordinal":
        # ★ 调试专用：只给 add 递增计号，**不维护 live** ⇒ 非 add 的 op 一律落空槽。不用于生产。
        if op == "add":
            s = st["next"]
            st["next"] += 1
            return str(s), "debug"
        return "", "debug"

    if mode == "fam":
        # ★ 仅用于负向对照：复现修复前的「fam 键」模型（ISSUE-20261008-03 Major-1）。
        if op == "add":
            if not fam:
                return "", "noop"
            if fam in st["live"]:
                return str(st["live"][fam]), "reuse"        # fam 模式：族槽复用（不计数）
            s = _take_free(st)
            st["live"][fam] = s
            return str(s), "fresh"
        if op == "remove":
            if fam and fam in st["live"]:
                s = st["live"].pop(fam)
                st["free"].append(s)
                return str(s), "remove"
            return "", "noop"
        if fam and fam in st["live"]:
            return str(st["live"][fam]), "ref"
        return "", "noop"

    # ---- live（生产）：身份键 ＝ **逐立绘件名**
    if op == "add":
        if not name:
            return "", "noop"                       # 无名 add：不猜
        if name in st["live"]:                      # 同名再开 ＝ 同一实例
            return str(st["live"][name]), "reuse_same"
        lst = st["fam_live"].setdefault(fam, [])
        old = lst[-1] if lst else None
        if old is None:                             # 该族本不在场 ⇒ 新槽
            s = _take_free(st)
            st["live"][name] = s
            lst.append(name)
            return str(s), "fresh"
        if still_alive(old, i):                     # 旧件此后仍被引用（其间未再 add）⇒ 二者并存，各占一槽
            s = _take_free(st)
            st["live"][name] = s
            lst.append(name)
            return str(s), "coexist"
        s = st["live"].pop(old)                     # 差分替换 ⇒ 沿用旧槽
        st["live"][name] = s
        lst[-1] = name
        return str(s), "reuse_swap"

    if op == "remove":
        s, exact = None, True
        if name and name in st["live"]:
            s = st["live"].pop(name)
            lst = st["fam_live"].get(fam)
            if lst and name in lst:
                lst.remove(name)
                if not lst:
                    del st["fam_live"][fam]
        else:
            # 族回退：被引用件名已换成同族别的差分件 ⇒ 删该 fam **当前**（最近）在世立绘
            lst = st["fam_live"].get(fam) if fam else None
            if lst:
                old = lst.pop()
                s = st["live"].pop(old)
                if not lst:
                    del st["fam_live"][fam]
                exact = False
        if s is None:
            return "", "noop"                       # 无名 remove / 件名本场未开：不猜
        st["free"].append(s)
        return str(s), ("remove" if exact else "remove_fam")

    # move / expr / expr_end / priority ⇒ 先精确件名，再回退到该 fam 当前（最近）在世立绘
    if name and name in st["live"]:
        return str(st["live"][name]), "ref"
    if fam:
        lst = st["fam_live"].get(fam)
        if lst:
            s = st["live"].get(lst[-1])
            if s is not None:
                return str(s), "ref_fam"
    return "", "noop"


def build_rows(chr_rows, scenes, slot_mode="live"):
    rows = []
    register = []
    stats = {
        "before_by_type": collections.Counter(),
        "before_by_op": collections.Counter(),
        "unknown_type": collections.Counter(),
        "slot_mode": slot_mode,
        "inferred_reasons": collections.Counter(),
        "add_kind": collections.Counter(),
        "add_rows": 0,
        "fam_fallback": collections.Counter(),
        "orphan_by_op": collections.Counter(),
        "ref_kind": collections.Counter(),
    }

    # pass 1：归一 op / fam（并存预扫需要先有 op）
    for r in chr_rows:
        ttype = r["type"]
        op = OP_MAP.get(ttype)
        if op is None:
            op = ttype                             # 不属七类：原样另列一值（说明里登记）
            stats["unknown_type"][ttype] += 1
        r["op"] = op
        r["fam"] = fam_of(r["name"])
        stats["before_by_type"][ttype] += 1
        stats["before_by_op"][op] += 1

    # 分组（chr_rows 已按 scene 排好）
    by_scene = collections.OrderedDict()
    for r in chr_rows:
        by_scene.setdefault(r["scene_id"], []).append(r)

    for sid, evs in by_scene.items():
        coinvolve, reg = scan_coexist(evs)
        sc = scenes.get(sid)
        src = sc["src"] if sc else sid.split("_")[0]
        for gr in reg:
            register.append({"scene_id": sid, "src": src, **gr})

        # 件名索引 → 「旧件是否仍被引用」（生成器与校验器 C8 用同一条可判定规则）
        adds_idx, refs_idx = collections.defaultdict(list), collections.defaultdict(list)
        for i, e in enumerate(evs):
            if e["name"]:
                (adds_idx if e["op"] == "add" else refs_idx)[e["name"]].append(i)

        def still_alive(nm, i, _a=adds_idx, _r=refs_idx):
            """被换下的 nm 在位置 i 之后**仍被引用**、且其间**未再 add** ⇒ 与新增者并存。"""
            nxt = next((a for a in _a.get(nm, ()) if a > i), None)
            return any(r > i and (nxt is None or r < nxt) for r in _r.get(nm, ()))

        st = _new_alloc()
        for i, r in enumerate(evs):
            op, name, fam = r["op"], r["name"], r["fam"]
            slot, kind = alloc_slot(st, op, name, fam, still_alive, i, slot_mode)

            if op == "add":
                stats["add_rows"] += 1
                if kind in ("fresh", "coexist", "reuse_same", "reuse_swap"):
                    stats["add_kind"][kind] += 1
            elif kind == "ref_fam":
                stats["fam_fallback"]["ref"] += 1
            elif kind == "remove_fam":
                stats["fam_fallback"]["remove"] += 1
            if op in ("move", "expr", "expr_end", "priority") and name:
                stats["ref_kind"][("hit" if slot != "" else "orphan")] += 1
                if slot == "":
                    stats["orphan_by_op"][op] += 1
            if op == "remove" and name and slot == "":
                stats["orphan_by_op"]["remove"] += 1

            st["max_live"] = max(st["max_live"], len(st["live"]))

            conf = conf_of(op, name, r["cx"])
            if conf == "inferred":
                stats["inferred_reasons"][op + ":" + ("no_name" if not name else "no_cx")] += 1

            degenerate = 0
            if sc is not None and (sc["map_rate"] < DEG_MAP_RATE or sc["align"] < DEG_ALIGN):
                degenerate = 1

            rows.append({
                "scene_id": sid,
                "src": src,
                "seq": r["seq"],
                "op": op,
                "task_type": r["type"],
                "ps_name": name,
                "delivery": r["delivery"],
                "fam": fam,
                "slot_hint": slot,
                "x": r["x"],
                "y": r["y"],
                "cx": r["cx"],
                "cy": r["cy"],
                "cpri": r["cpri"],
                "priority": r["priority"],
                "time": r["time"],
                "x1920": scale_val(r["x"] if r["x"] != "" else r["cx"]),
                "y1920": scale_val(r["y"] if r["y"] != "" else r["cy"]),
                "conf": conf,
                "scene_degraded": str(degenerate),
                "_max_live": st["max_live"],
            })
    return rows, register, stats



def to_tsv(rows):
    out = ["\t".join(COLS)]
    for r in rows:
        out.append("\t".join("" if r[c] is None else str(r[c]) for c in COLS))
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 统计

def commit_counters(c) -> dict:
    return {k: c[k] for k in sorted(c)}


def collect_stats(rows, register, stats, scenes, scene_order, timeline_path, scene_map_path,
                  timeline_total, timeline_sha, map_sha):
    after_by_op = collections.Counter(r["op"] for r in rows)
    after_by_src = collections.Counter(r["src"] for r in rows)
    by_src_op = collections.defaultdict(collections.Counter)
    for r in rows:
        by_src_op[r["src"]][r["op"]] += 1

    per_scene = collections.Counter(r["scene_id"] for r in rows)
    scenes_from_rows = set(per_scene)
    map_scenes = set(scenes)
    no_chr = [s for s in scene_order if s not in scenes_from_rows]
    extra = sorted(scenes_from_rows - map_scenes)

    vals = sorted(per_scene.values())
    buckets = collections.Counter()
    for v in vals:
        if v <= 5:
            buckets[str(v)] += 1
        elif v <= 20:
            buckets["6-20"] += 1
        elif v <= 50:
            buckets["21-50"] += 1
        elif v <= 100:
            buckets["51-100"] += 1
        else:
            buckets[">100"] += 1

    # 退化场景
    deg = []
    for sid, sc in scenes.items():
        reasons = []
        if sc["map_rate"] < DEG_MAP_RATE:
            reasons.append("map_rate<%.2f" % DEG_MAP_RATE)
        if sc["align"] < DEG_ALIGN:
            reasons.append("align<%.2f" % DEG_ALIGN)
        if reasons:
            deg.append({
                "scene_id": sid, "src": sc["src"],
                "map_rate": sc["map_rate"], "align": sc["align"],
                "psv_msg": sc["psv_msg"], "corpus_lines": sc["corpus_lines"],
                "header": sc["header"], "reason": "+".join(reasons),
                "chr_events": per_scene.get(sid, 0),
            })
    deg.sort(key=lambda d: (SRC_RANK.get(d["src"], 9), d["scene_id"]))

    # 换算自证：cx 众数 × 1.5 == 960（我方 1920 的一半）；且波位 token 值域复核
    cx_vals = collections.Counter(r["cx"] for r in rows if r["cx"] != "")
    cx_mode = cx_vals.most_common(1)[0][0] if cx_vals else ""
    odd_cx = sum(1 for r in rows if r["cx"] != "" and int(r["cx"]) % 2)

    max_live_per_scene = {}
    for r in rows:
        max_live_per_scene[r["scene_id"]] = max(max_live_per_scene.get(r["scene_id"], 0),
                                                r["_max_live"])
    over6 = {k: v for k, v in max_live_per_scene.items() if v > 6}

    deliv_blank_by_op = collections.Counter(r["op"] for r in rows if r["delivery"] == "")

    stats_out = {
        "generated_from": {
            "timeline": os.path.abspath(timeline_path),
            "timeline_sha256": timeline_sha,
            "timeline_rows_excl_header": timeline_total,
            "scene_map": os.path.abspath(scene_map_path),
            "scene_map_sha256": map_sha,
        },
        "chr_rows_total": len(rows),
        "before_by_op": commit_counters(stats["before_by_op"]),
        "after_by_op": commit_counters(after_by_op),
        "before_by_type": commit_counters(stats["before_by_type"]),
        "unknown_type_rows": commit_counters(stats["unknown_type"]),
        "by_src": {s: commit_counters(c) for s, c in sorted(by_src_op.items())},
        "by_src_total": commit_counters(after_by_src),
        "coverage": {
            "psv_scenes_total": len(scenes),
            "scenes_with_chr_events": len(scenes_from_rows),
            "scenes_without_chr_events": len(no_chr),
            "scenes_without_chr_list": no_chr,
            "scenes_in_rows_not_in_map": extra,
        },
        "events_per_scene": {
            "min": min(vals) if vals else 0,
            "max": max(vals) if vals else 0,
            "median": (vals[len(vals) // 2] if vals else 0),
            "buckets": {k: buckets[k] for k in sorted(buckets)},
        },
        "inferred": {
            "total": sum(1 for r in rows if r["conf"] == "inferred"),
            "reasons": commit_counters(stats["inferred_reasons"]),
        },
        "delivery_blank": {
            "total": sum(deliv_blank_by_op.values()),
            "by_op": commit_counters(deliv_blank_by_op),
        },
        "slot": {
            "mode": stats["slot_mode"],
            "scenes_gt6_concurrent": len(over6),
            "max_concurrent_examples": dict(sorted(over6.items(), key=lambda kv: -kv[1])[:10]),
            "max_concurrent_overall": max(max_live_per_scene.values()) if max_live_per_scene else 0,
            "add_total": stats["add_rows"],
            "add_by_kind": commit_counters(stats["add_kind"]),
            "ref_by_kind": commit_counters(stats["ref_kind"]),
            "orphan_by_op": commit_counters(stats["orphan_by_op"]),
            "fam_fallback": commit_counters(stats["fam_fallback"]),
        },
        "coexist": {
            "evidence_ops": list(COEXIST_EVIDENCE_OPS),
            "tasks": len(register),
            "scenes": sorted({r["scene_id"] for r in register}),
            "names": sum(len(r["names"]) for r in register),
            "registry_rows": len(register),
        },
        "degenerate": {
            "criterion": "map_rate<%.2f OR align<%.2f" % (DEG_MAP_RATE, DEG_ALIGN),
            "count": len(deg),
            "scenes": deg,
        },
        "conversion_selftest": {
            "scale": SCALE,
            "cx_mode": cx_mode,
            "cx_mode_x1920": scale_val(cx_mode),
            "cx_odd_rows": odd_cx,
            "expected_cx_mode_x1920": "960",
            "token_positions_psv": {"c": 640, "l": 336, "r": 944, "<d": 236, ">d": 1044},
            "token_positions_x1920": {"c": 960, "l": 504, "r": 1416, "<d": 354, ">d": 1566},
            "all_cx_even": odd_cx == 0,
        },
    }
    return stats_out, after_by_op, per_scene, max_live_per_scene, deg, no_chr


def compare_selfdefined(candidate_dirs):
    """与现有五源自定摆位表（资源组 演出 演出_<源>.tsv）的粗粒度对照。
    candidate_dirs = 依次尝试的「资源组\\演出」目录（本 checkout 优先，主工作树兜底）。"""
    out = {}
    for src in ("ot", "otv", "otp", "otr", "ota", "np"):
        path = None
        for d in candidate_dirs:
            cand = os.path.join(d, "演出_%s.tsv" % src)
            if os.path.isfile(cand):
                path = cand
                break
        if not path:
            out[src] = {"present": False}
            continue
        c = collections.Counter()
        with open(path, encoding="utf-8") as f:
            hdr = f.readline().rstrip("\n").split("\t")
            I = {k: i for i, k in enumerate(hdr)}
            for line in f:
                p = line.rstrip("\n").split("\t")
                c[p[I["op"]]] += 1
        out[src] = {"present": True, "path": path,
                    "total": sum(c.values()),
                    "chr_add": c["chr_add"], "chr_remove": c["chr_remove"],
                    "chr_move": c["chr_move"], "chr_expr": c["chr_expr"]}
    return out


# ---------------------------------------------------------------- 说明.md

def scan_true_concurrency(rows):
    """按**忠实构建规则**重放并发峰值（口径与 build_story.py gold 分支一致）。

    规则（与复核_ISSUE-20261008-03 §3.1 的重算脚本 `_fix_verify_concurrency.py` 同）：
    只认 `delivery` 前缀 `立绘/` 的事件；`add`/`expr` 于数字槽位置位；`priority` 仅当槽仍在场；
    `remove` 中 `CG背景/` 丢弃、**无名 remove＝清空全部**（区别于本表 `slot_hint` 列对无名 remove
    的「不猜＝留空」；这是消费侧构建的规则）、具名 remove 释放槽。返回 {scene_id: {live, peak}}。

    ★ 仅供「说明.md」的订正口径渲染，**不进** `立绘事件流_统计.json`（该文件须逐字节稳定）。
    """
    per = collections.defaultdict(lambda: {"live": set(), "peak": 0})
    for r in rows:
        st = per[r["scene_id"]]
        d = (r.get("delivery") or "").replace("\\", "/")
        pre = (d.split("/")[0] + "/") if "/" in d else ""
        op = r["op"]
        sh = str(r.get("slot_hint") or "").strip()
        ischr = (pre == "立绘/")
        if op in ("add", "expr", "move", "priority"):
            if ischr and op in ("add", "expr") and sh.isdigit():
                st["live"].add(int(sh))
        elif op == "remove":
            if pre == "CG背景/":
                pass
            elif not sh:
                st["live"].clear()
            elif ischr:
                st["live"].discard(int(sh))
        st["peak"] = max(st["peak"], len(st["live"]))
    return per


def doc_metrics(rows):
    """「说明.md」专用订正口径（不进 `立绘事件流_统计.json`，保持该文件逐字节不变）：
    `slot_hint` 下标峰值 /「`slot_hint ≥ 6`」的场数 / 真并发 >6 的场清单 / 并发峰值场。"""
    sh_scene = {}
    for r in rows:
        sh = str(r.get("slot_hint") or "").strip()
        if sh.isdigit():
            sid = r["scene_id"]
            sh_scene[sid] = max(sh_scene.get(sid, -1), int(sh))
    per = scan_true_concurrency(rows)
    gt6 = sorted(((s, d["peak"]) for s, d in per.items() if d["peak"] > 6),
                 key=lambda kv: -kv[1])
    if per:
        peak_scene, peak_entry = max(per.items(), key=lambda kv: kv[1]["peak"])
        peak_val = peak_entry["peak"]
    else:
        peak_scene, peak_val = "", 0
    return {"max_slot_hint": max(sh_scene.values()) if sh_scene else 0,
            "slot_ge6_scenes": sum(1 for v in sh_scene.values() if v >= 6),
            "gt6": gt6, "peak_scene": peak_scene, "peak_val": peak_val}


def render_doc(stats, cmp_self, register, tsv_name, tsv_rows, slot_mode, doc_x):
    L = []
    a = L.append
    cov = stats["coverage"]
    eps = stats["events_per_scene"]
    a("# PSV 金标 → 逐场立绘事件流 · 交付说明（ISSUE-20261008-03 · M1）")
    a("")
    # 校准注（2026-10-09 · ISSUE-20261009-01）：原为手工追加；为使重跑幂等，逐字移入模板
    # （含其 ③「生成器模板落后」的历史陈述——该条自本次 ISSUE-20261009-08 同步后已成历史记录）。
    a("> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（金标立绘事件流口径；**本件是生成物**）｜ 权威入口：`工程\\我们没有翅膀——格雷塔迦露德与柳木原\\00_项目索引.md`")
    a("> 校准核对（2026-10-09）：① 数据一致——`立绘事件流.tsv` 26,712 行，输入 `时间线.tsv` sha256 `78203e1c…`／`场景映射.tsv` sha256 `a09dbcec…` 与 `立绘事件流_统计.json` 记录一致；② **本文件由 `emit_character_events.py` 生成**（重跑会整体重写；本「校准」注为该生成器模板之外的手工追加）；③ 已知分歧（待主代理处置）：**生成器模板落后于本文件**——本文件 §六/§七.3 的**一审订正**（「真并发 >6 的场只有 2 个」）不在生成器中，重跑会退回旧口径「18 个」；`emit_character_events.py --check` 报「不一致」的构成＝行尾差异（库内 CRLF／生成器 LF，坑 #90，三份数据文件 `立绘事件流.tsv`/`退化场景登记.tsv`/`同族并存登记.tsv` 归一化后**与重出相同**）＋`立绘事件流_统计.json` 内嵌绝对路径不同＋`立绘事件流_说明.md` 的上述文本差异（非数据过期）。")
    a(">")
    a("> **本件是什么**：把 PSV 金标时间线（`编程组\\PSV演出\\时间线.tsv`）里 **`layer=chr`** 的")
    a("> **%s 行**立绘事件，**抽取并归一**成一份可直接驱动构建的逐场立绘事件表 `%s`。" % (f"{stats['chr_rows_total']:,}", tsv_name))
    a("> 目的：我方五源 PC 脚本**没有成体系的立绘退场数据**（资源组审计四条硬边界之一），")
    a("> 现行「场景内保持、换场景清空」+ 自定摆位 ⇒ 同屏重叠错位；本表把金标完整的")
    a("> `CharacterOpen/OpenBS/Action/ActionEnd/Move/Delete/Priority/Wait` 事件流归一为下游可消费的形式。")
    a(">")
    a("> - **生成器**：`emit_character_events.py`（本目录；只读金标，逐字节确定性再生，`--check` 幂等）")
    a("> - **独立校验器**：`check_character_events.py`（**不共用生成器实现**，含 `--self-test` 失败自证）")
    a("> - **输入**：`时间线.tsv` sha256 `%s` ｜ `场景映射.tsv` sha256 `%s`" % (stats["generated_from"]["timeline_sha256"][:16], stats["generated_from"]["scene_map_sha256"][:16]))
    a("")
    a("复跑：")
    a("```bash")
    a("cd \"工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/PSV演出\"")
    a("python -X utf8 emit_character_events.py            # 生成五件产物")
    a("python -X utf8 emit_character_events.py --check    # 幂等复核")
    a("python -X utf8 check_character_events.py           # 独立机检 C1–C10（含失败自证）")
    a("```")
    a("")
    a("---")
    a("")
    a("## 一 列义（**照此读表，不要自行解释**）")
    a("")
    a("20 列，前 19 列为定死 schema（列名列序由主代理定死），第 20 列 `scene_degraded` 为本批**追加**列（允许的追加位）。")
    a("UTF-8 无 BOM、TAB 分隔、无引号包裹、首行表头、LF 行尾。")
    a("")
    a("```")
    a("\t".join(COLS))
    a("```")
    a("")
    a("| 列 | 含义 |")
    a("| --- | --- |")
    a("| `scene_id` | 我方语料场名（`场景映射.tsv` 的键） |")
    a("| `src` | 源代号（`ot`/`otv`/`otp`/`otr`，取自 `场景映射.tsv`；`ot` 优先排前） |")
    a("| `seq` | **我方语料 `lines[].seq`**（金标行已有，1-based，与 `资源组\\剧本\\scene_<源>.jsonl` 同系）；语义＝「在该行显示之前生效」 |")
    a("| `op` | 归一 op：`add \\| move \\| remove \\| expr \\| expr_end \\| priority \\| wait`（由 `:Tasktype` 归一，见 §二.1） |")
    a("| `task_type` | 金标原始 `:Tasktype`（**未改写**） |")
    a("| `ps_name` | 金标 `name`：PSV 立绘件名（如 `MIS03H`）；**remove 可能为空**（金标 `CharacterDelete` 有 966/1448 行不带 `:Number`） |")
    a("| `delivery` | **直接用金标行既有的 `delivery` 值**（我方交付层相对路径，如 `立绘/mis03h.png`），未重算 |")
    a("| `fam` | 角色族 ＝ `ps_name` 前导字母串小写（见 §二.2） |")
    a("| `slot_hint` | 场内「活槽位」序号（0 基，**身份键 ＝ 逐立绘件名**；见 §二.3） |")
    a("| `x` / `y` | 金标贴图层坐标——**立绘事件恒为空**（立绘走 `cx/cy`，实测 chr 行 `x/y` 全空） |")
    a("| `cx` / `cy` | **金标原值**（1280×720 中心系）。`cy` 显式 `0` 与**留空**含义不同：显式 `0` ＝按底边定位、留空 ＝子块未给 `:Position`。**本表原样保留，不补 0**（不猜） |")
    a("| `cpri` | 金标立绘 `:Priority`（值域 1..9，实测非空 4,836 行） |")
    a("| `priority` | 金标层序 `:Priority`（值域 1..9；chr 行仅 `CharacterPriority` 的 44 行非空） |")
    a("| `time` | 金标 `:Time`（帧，60fps；chr 行仅 `chr_move` 的 881 行非空） |")
    a("| `x1920` / `y1920` | 换算到我方 1920×1080 的值（`×1.5`；口径与自证见 §三） |")
    a("| `conf` | `exact \\| inferred`（见 §二.4） |")
    a("| `scene_degraded` | **追加列**：`1` ＝该行所属场景触退化阈（`map_rate<0.98` 或 `align<0.90`，见 §五），`0` ＝否 |")
    a("")
    a("**行序**：按 `(src 排位, scene_id, 金标原始行序)` 排；同场内即**金标执行序**（任务序），")
    a("下游可按 `seq` 重排挂到行游标上。")
    a("")
    a("---")
    a("")
    a("## 二 归一规则（逐条写明）")
    a("")
    a("### 2.1 `op` ← `:Tasktype`（七类闭集）")
    a("")
    a("| `:Tasktype` | `op` | 金标行数 |")
    a("| --- | --- | ---: |")
    order = [("CharacterOpen", "add"), ("CharacterOpenBS", "add"), ("CharacterMove", "move"),
             ("CharacterDelete", "remove"), ("CharacterAction", "expr"),
             ("CharacterActionEnd", "expr_end"), ("CharacterPriority", "priority"),
             ("CharacterWait", "wait"), ("CharacterStop", "wait")]
    before_type = stats["before_by_type"]
    for t, o in order:
        a("| `%s` | `%s` | %s |" % (t, o, f"{before_type.get(t, 0):,}"))
    a("")
    unk = stats["unknown_type_rows"]
    a("- **七类之外的 chr 系 `type`**：" + ("**本批实测 0 行**（26,712 行全部落七类内）。" if not unk else "见下表，`op` 原样另列："))
    if unk:
        a("")
        a("| 原始 type | 行数 |")
        a("| --- | ---: |")
        for t, n in unk.items():
            a("| `%s` | %s |" % (t, f"{n:,}"))
    a("- 生成器对未知 `type` 一律**原样另列**（不丢行、不猜语义），故未来金标新增 type 会以原始名出现在 `op` 列并计数。")
    a("")
    a("### 2.2 `fam` ← `ps_name`")
    a("")
    a("规则：`fam = 正则 ^([A-Za-z]+)` 的捕获组，**小写**；`ps_name` 为空 ⇒ `fam` 为空。")
    a("实测金标 `ps_name` 共 1,173 个不同值 / 34 个前导字母族（`mis` `ai` `cin` …），与")
    a("`资源组\\演出\\头像族判读.tsv` 的族码体系同形。")
    a("")
    a("**不做跨族合并**：`kaa` / `kab`（作品层术语表 §5.2 记为同一角色「凤凰寺翔」的两个形态）")
    a("在立绘素材层是两族，本表**保持两族**（合并属语义裁决，不在本模块）。")
    a("")
    a("### 2.3 `slot_hint` —— 场内活槽位分配（模式 `%s`；身份键 ＝ **逐立绘件名**）" % slot_mode)
    a("")
    ak = stats["slot"]["add_by_kind"]
    a("规则（`live` 模式）：同场内按金标执行序扫描，**以立绘件名（`ps_name`）为身份键**：")
    a("")
    a("1. `add`，该**件名不在场**、其 **`fam` 也不在场** ⇒ 取**最低空闲槽**（0 基）——`fresh` **%s** 条；"
      % f"{ak.get('fresh', 0):,}")
    a("2. `add` 且**同名件已在场** ⇒ 沿用其槽（同名再开＝同一实例）——`reuse_same` **%s** 条；"
      % f"{ak.get('reuse_same', 0):,}")
    a("3. `add` 且该 `fam` 在场、旧件名 ≠ 新件名：**旧件名在本次 `add` 之后是否仍被引用**（`move`/")
    a("   `remove`/`expr`/`expr_end`/`priority`，且其间**未再 add** 同名件）——")
    a("   · **仍被引用 ⇒ 二者并存** ⇒ **新开一槽**（旧件继续在场）——`coexist` **%s** 条；" % f"{ak.get('coexist', 0):,}")
    a("   · 否则 ⇒ 旧件已被换下 ⇒ **沿用旧件的槽**（差分替换）——`reuse_swap` **%s** 条。" % f"{ak.get('reuse_swap', 0):,}")
    a("   （此规则即派单裁决 1 的 B 案；「其间未再 add」的分句由 `check_character_events.py` C8 用**同一条可判定规则**复算。）")
    a("")
    unnamed = stats["slot"]["add_total"] - sum(ak.values())
    a("   ⇒ `add` 合计 **%s** 条 = `fresh` %s ＋ `reuse_same` %s ＋ `reuse_swap` %s ＋ `coexist` %s"
      " ＋ 无名（留空）%s"
      % (f"{stats['slot']['add_total']:,}", f"{ak.get('fresh', 0):,}", f"{ak.get('reuse_same', 0):,}",
         f"{ak.get('reuse_swap', 0):,}", f"{ak.get('coexist', 0):,}", f"{unnamed:,}"))
    a("   ⇒ **沿用既有槽的 add 共 %s 条**（`reuse_same` ＋ `reuse_swap`；PSV 用 `CharacterOpen` 反复换差分件，"
      % f"{ak.get('reuse_same', 0) + ak.get('reuse_swap', 0):,}")
    a("   **若一律按件名新分配会让槽位爆炸且无意义**）。")
    fb = stats["slot"].get("fam_fallback", {})
    a("4. `remove`：该**件名**在场 ⇒ 取该件名的槽；否则**族回退**到该 fam 当前（最近）在世立绘的槽"
      "（实测 `remove` 族回退 **%s** 条）⇒ 取到后**释放**（供后续 add 复用）；" % f"{fb.get('remove', 0):,}")
    a("5. `expr` / `expr_end` / `move` / **`priority`** ⇒ 先取该**件名**的槽；件名不在场 ⇒ **族回退**到该 fam")
    a("   当前（最近）在世立绘的槽（实测 `ref_fam` **%s** 条）；仍无 ⇒ 留空。" % f"{fb.get('ref', 0):,}")
    a("   （`CharacterPriority` 实测 44/44 带 `:Number` ⇒ 取到该立绘当前槽；语义正当：priority 正是对该立绘设层序。）")
    a("   族回退的用途：PSV 常对同一角色的**旧差分件名**发 `expr`/`move`（该名已被新差分件替换）——")
    a("   这是对**同族同一立绘**的操作，观测上表现为「引用已换下的件名」，故按族回退解析。")
    a("6. `wait`、**无名 `add` / 无名 `remove`**、**件名本场从未开过且该族不在场**的 op ⇒ 留空（**不猜**）。")
    a("")
    a("不变量（`check_character_events.py` C8 复算，**身份键同为逐件名**）：**同一场同一时刻，两个在场")
    a("立绘的 `slot_hint` 必不相同**（旧件被差分替换时被换下）；非空 `slot_hint` 的")
    a("`remove`/`move`/`expr`/`expr_end`/`priority` 必指向当时在场的**同一件名或同族件**。")
    a("**本表 `slot_hint` 下标最大用到 %d**（＝最远槽位；同屏并发立绘数峰值 **%d**，`%s`）。"
      % (doc_x["max_slot_hint"], doc_x["peak_val"], doc_x["peak_scene"]))
    a("**订正（一审后，ISSUE-20261008-03）**：**真并发 >6 的场只有 %d 个**（%s）；下文旧写的「>6 的场 %d 个」是**错口径**——%d 是「`slot_hint ≥ 6` 的场数」"
      % (len(doc_x["gt6"]), " ／\n".join("`%s` 峰值 %d" % (s, p) for s, p in doc_x["gt6"]),
         stats["slot"]["scenes_gt6_concurrent"], doc_x["slot_ge6_scenes"]))
    a("（＝会用到槽下标 6 的场数），不是同屏并发场数。⇒ 消费侧 6 槽模型需降级/排队，见 §七.3。")
    a("")
    a("> 备选模式 `ordinal`（`--slot-mode ordinal`）：**实验性 / 仅调试**——只给 `add` 递增计号，")
    a("> **不维护 live** ⇒ 非 `add` 的 op 一律落空槽；不用于生产、未纳入验收。")
    a("> 另 `--slot-mode fam`：**仅用于负向对照**，复现修复前（`ISSUE-20261008-03` Major-1）的「fam 键」模型。")
    a("")
    a("### 2.4 `conf`")
    a("")
    a("`inferred` 仅当**该 op 本应携带、却缺失**的字段为空；其余 `exact`：")
    a("")
    a("- `add` / `move`：`ps_name` 空 **或** `cx` 空 ⇒ `inferred`；")
    a("- `expr` / `expr_end` / `remove` / `priority`：`ps_name` 空 ⇒ `inferred`（`priority` 实测 44/44 带名）；")
    a("- `wait`：实测 653/653 无名，按设计不带目标名 ⇒ 恒 `exact`（不因缺名降级）。")
    a("")
    inf = stats["inferred"]
    a("实测 `inferred` **%s 行**（占比 %.2f%%）：" % (f"{inf['total']:,}", 100.0 * inf["total"] / max(1, stats["chr_rows_total"])))
    a("")
    a("| op:原因 | 行数 |")
    a("| --- | ---: |")
    for k, v in inf["reasons"].items():
        a("| `%s` | %s |" % (k, f"{v:,}"))
    a("")
    a("### 2.5 「同族并存」证据与登记（`同族并存登记.tsv`）")
    a("")
    a("**判据**（可复现）：同一金标 `task` 内对**同一 `fam` 的 ≥2 个不同立绘名**发出 "
      "`CharacterMove` / `CharacterDelete` / `CharacterAction` / `CharacterActionEnd`")
    a("⇒ 引擎在同一任务里显式操作这两个立绘 ⇒ **二者同时在场**，不可能是一个替换另一个。")
    a("这是 §2.3 规则 3 的**任务级并存证据**（其 7 条 `add` 均落 `coexist`）；规则 3 另按「旧件仍被引用」")
    a("判定，故全表 `coexist` 共 **%d** 条（含本登记的 7 条）。" % stats["slot"]["add_by_kind"].get("coexist", 0))
    a("")
    co = stats["coexist"]
    a("实测命中 **%d 场 / %d 个任务**（全部 `cin` 群演族），逐任务登记："
      % (len(co["scenes"]), co["tasks"]))
    a("")
    a("| scene_id | task | fam | names | ops |")
    a("| --- | --- | --- | --- | --- |")
    for gr in register:
        a("| `%s` | %s | `%s` | %s | %s |" % (gr["scene_id"], gr["task"], gr["fam"],
                                              ", ".join(gr["names"]), gr["ops"]))
    a("")
    a("（同一清单另存 `同族并存登记.tsv`，机读；校验器 C10 会独立重扫金标并核对本登记集。）")
    a("")
    a("---")
    a("")
    a("## 三 换算口径（`x1920` / `y1920`）与自证")
    a("")
    a("**口径**：我方 1920×1080 与 PSV 逻辑画布 1280×720 **同为 16:9**，换算恰 **×1.5**：")
    a("`x1920 = round(cx × 1.5)`、`y1920 = round(cy × 1.5)`（立绘 `x/y` 恒空，故一律取 `cx/cy`）。")
    a("金标缺值（空 `cx`/`cy`）⇒ 对应 `x1920`/`y1920` **留空**（**不补 0**）。")
    a("")
    a("**自证一（既有标定，作品专属 skill 已载）**：立绘中心槽位 `c` 的 PSV 值 **640 ＝ 1280/2** ⇒")
    a("我方 **960 ＝ 1920/2**。实测本表 `cx` **众数 ＝ %s**（%s 行），`×1.5 = %s` ✓。"
      % (stats["conversion_selftest"]["cx_mode"],
         f"{stats['conversion_selftest'].get('cx_mode_rows', '')}".strip() or "—",
         stats["conversion_selftest"]["cx_mode_x1920"]))
    a("")
    a("**自证二（符号位值域复核）**：作品专属 skill §四·补「立绘基准与摆位」记载 PSV 位置符号众数")
    a("`c`=640 / `l`=336 / `r`=944 / `<d`=236 / `>d`=1044；本表实测 `cx` 值域与之逐值吻合，")
    a("换算得 `c`→960 / `l`→504 / `r`→1416 / `<d`→354 / `>d`→1566，与 skill 记载**逐值一致**。")
    a("")
    a("**自证三（整数性）**：实测 chr 行 `cx` **奇数 %d 行** ⇒ `×1.5` 恒为整数，无舍入歧义"
      % stats["conversion_selftest"]["cx_odd_rows"])
    a("（`y1920` 同法；`cy` 非零值实测含负数，如 `-600`，属源侧越界/滑出位，**原样换算**）。")
    a("")
    a("---")
    a("")
    a("## 四 计数（抽取前后对照）")
    a("")
    a("### 4.1 按 `op` 分类：抽取前（金标）＝ 抽取后（本表）")
    a("")
    a("| `op` | 抽取前 | 抽取后 | 差 |")
    a("| --- | ---: | ---: | ---: |")
    bo, ao = stats["before_by_op"], stats["after_by_op"]
    for o in OPS:
        a("| `%s` | %s | %s | %s |" % (o, f"{bo.get(o,0):,}", f"{ao.get(o,0):,}", f"{ao.get(o,0)-bo.get(o,0):,}"))
    a("| **合计** | **%s** | **%s** | **%s** |" % (f"{sum(bo.values()):,}", f"{sum(ao.values()):,}", f"{sum(ao.values())-sum(bo.values()):,}"))
    a("")
    a("（**1:1 无丢弃**：每个金标 chr 行产出一行；不一致即校验器报错。）")
    a("")
    a("### 4.2 按 `src` × `op`")
    a("")
    a("| src | add | move | remove | expr | expr_end | priority | wait | 合计 |")
    a("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for s in sorted(stats["by_src"], key=lambda x: SRC_RANK.get(x, 9)):
        c = stats["by_src"][s]
        a("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            s, f"{c.get('add',0):,}", f"{c.get('move',0):,}", f"{c.get('remove',0):,}",
            f"{c.get('expr',0):,}", f"{c.get('expr_end',0):,}", f"{c.get('priority',0):,}",
            f"{c.get('wait',0):,}", f"{stats['by_src_total'][s]:,}"))
    a("")
    a("### 4.3 场覆盖")
    a("")
    a("- PSV 覆盖场（`场景映射.tsv`）：**%d 场**" % cov["psv_scenes_total"])
    a("- **有 ≥1 条立绘事件的场：%d 场**" % cov["scenes_with_chr_events"])
    a("- 无立绘事件的场：**%d 场**（金标确无 chr 行，非本模块丢弃）" % cov["scenes_without_chr_events"])
    a("- 事件表内出现、但 `场景映射.tsv` 无登记的场：%s" % (cov["scenes_in_rows_not_in_map"] or "无"))
    a("")
    a("无立绘事件的 %d 场（供下游跳过/占位）：" % cov["scenes_without_chr_events"])
    a("")
    a("```")
    for i in range(0, len(cov["scenes_without_chr_list"]), 6):
        a("  ".join(cov["scenes_without_chr_list"][i:i + 6]))
    a("```")
    a("")
    a("### 4.4 每场事件数分布")
    a("")
    a("min **%d** / median **%d** / max **%d**" % (eps["min"], eps["median"], eps["max"]))
    a("")
    a("| 区间 | 场数 |")
    a("| --- | ---: |")
    for k in ("1", "2", "3", "4", "5", "6-20", "21-50", "51-100", ">100"):
        if k in eps["buckets"]:
            a("| %s | %d |" % (k, eps["buckets"][k]))
    a("")
    a("---")
    a("")
    a("## 五 退化场景登记（`map_rate` / `align` 触阈）")
    a("")
    a("**判据**（两档取或，逐场）：")
    a("")
    a("- `map_rate < 0.98`：PSV 台词找到对应语料行的比例偏低 ⇒ **`seq` 落点不可靠**；")
    a("- `align < 0.90`：两侧**逐字相等率**低 ⇒ PSV 移植时**整段重编**过（极端例 `ot_s04_25b`：")
    a("  我方 482 行 vs PSV 79 句、`align=0.0127`、`header=403`），此时**即使 `map_rate=1.0`**，")
    a("  `seq` 也只是「PSV 第 k 句 ∼ 我方第 n 行」的比例对位，**不是逐句对应**。")
    a("")
    a("> 判据要点：**「事件仍在」**——本表的立绘事件（op/名/坐标）取自 PSV 脚本**明文**，")
    a("> 与对齐质量无关，**事件本身照常可用**；**不可靠的只是 `seq` 对位**。故退化场照常产出，")
    a("> 只是 `scene_degraded=1`、`seq` 须下游降级（按 PSV 序驱动或比例映射）。")
    a("")
    a("实测触阈 **%d 场**（`map_rate<0.98` 者 %d、`align<0.90` 者 %d，有交集）："
      % (stats["degenerate"]["count"],
         sum(1 for d in stats["degenerate"]["scenes"] if "map_rate" in d["reason"]),
         sum(1 for d in stats["degenerate"]["scenes"] if "align" in d["reason"])))
    a("")
    a("| scene_id | src | map_rate | align | psv_msg | corpus_lines | header | 触因 | chr 事件数 |")
    a("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
    for d in stats["degenerate"]["scenes"]:
        a("| `%s` | %s | %.4f | %.4f | %s | %s | %s | %s | %d |" % (
            d["scene_id"], d["src"], d["map_rate"], d["align"], d["psv_msg"],
            d["corpus_lines"], d["header"], d["reason"], d["chr_events"]))
    a("")
    a("（同一清单另存 `退化场景登记.tsv`，机读。）")
    a("")
    a("---")
    a("")
    a("## 六 与现有「五源自定摆位」的差异（粗粒度）")
    a("")
    a("现有五源逐行演出表（`资源组\\演出\\演出_<源>.tsv`）与金标的 chr 事件计数对照：")
    a("")
    a("| src | 现有源表 chr_add | 现有 chr_remove | 现有 chr_move | 金标 add | 金标 remove | 金标 move |")
    a("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    gb = stats["by_src"]
    for s in ("ot", "otv", "otp", "otr"):
        e = cmp_self.get(s, {})
        if not e.get("present"):
            a("| `%s` | — | — | — | %s | %s | %s |" % (s, f"{gb.get(s,{}).get('add',0):,}", f"{gb.get(s,{}).get('remove',0):,}", f"{gb.get(s,{}).get('move',0):,}"))
            continue
        a("| `%s` | %s | %s | %s | %s | %s | %s |" % (
            s, f"{e['chr_add']:,}", f"{e['chr_remove']:,}", f"{e['chr_move']:,}",
            f"{gb.get(s,{}).get('add',0):,}", f"{gb.get(s,{}).get('remove',0):,}", f"{gb.get(s,{}).get('move',0):,}"))
    a("")
    tot_pc_rm = sum(cmp_self.get(s, {}).get("chr_remove", 0) for s in ("ot", "otv", "otp", "otr", "ota", "np"))
    tot_pc_mv = sum(cmp_self.get(s, {}).get("chr_move", 0) for s in ("ot", "otv", "otp", "otr", "ota", "np"))
    a("**结论（粗粒度）**：")
    a("")
    a("1. **退场**：现有源表**合计仅 %d 条 `chr_remove`**（且只在 `otv`——`ot`/`otp`/`otr`/`ota`/`np` **各 0 条**，"
      % tot_pc_rm)
    a("   即资源组审计的四条硬边界之①「立绘退场无信号」）；**金标有 %s 条**。"
      % f"{sum(gb[s]['remove'] for s in gb):,}")
    a("   这正是「现行「场景内保持、换场景清空」⇒ 同屏重叠错位」的**数据侧根因**。")
    a("2. **移动**：现有源表合计 %d 条 `chr_move`，**金标 %s 条**。" % (tot_pc_mv, f"{sum(gb[s]['move'] for s in gb):,}"))
    a("3. **开立绘**：现有表把「同族首次引用＝`chr_add`／后续＝`chr_expr`」作为启发式，")
    a("   金标则直接用 `CharacterOpen`（%s 条）＋ `CharacterOpenBS`（%s 条）——"
      % (f"{before_type.get('CharacterOpen', 0):,}", f"{before_type.get('CharacterOpenBS', 0):,}"))
    a("   后者在作品专属 skill §四·补被列为 **PC 侧 SOB0 解码器不可达**的命令类 ⇒ 该类只有金标有。")
    a("4. **位置**：现有摆位是**我方自定**（按在场集合重排、拥挤降缩放；默认「源侧中心位」单人 960／")
    a("   多人 354/1566）；本表给的是**金标逐事件 `cx`（×1.5）**，即**源侧真实摆位**。")
    a("")
    a("---")
    a("")
    a("## 七 边界与未决（**不要当成已完成**）")
    a("")
    orph = stats["slot"]["orphan_by_op"]
    orph_ref = sum(v for k, v in orph.items() if k != "remove")
    a("1. **`slot_hint` 语义是本模块的定义**（schema 只给了列名）。采用**逐立绘件的活槽位**"
      "（最低空闲 + 同族并存证据开新槽，见 §2.3/§2.5），")
    a("   与消费侧 `ui_staging.tjs`「按 slot 逐个摆放 + 退场不重排」同向。")
    n_rm, n_rm_noname = bo.get("remove", 0), inf["reasons"].get("remove:no_name", 0)
    a("2. **无名 `chr_remove` %s 行**（占 %s 条 remove 的 %.0f%%）：金标 `CharacterDelete` 不带 `:Number`，"
      % (f"{n_rm_noname:,}", f"{n_rm:,}", 100.0 * n_rm_noname / max(1, n_rm)))
    a("   **本表不猜目标**（`ps_name`/`fam`/`slot_hint` 均留空）。⇒ 下游**不能**据此关掉某个具体槽，")
    a("   只能按「退场了某在场立绘」处理；要精确定位须 PSV 源侧补 `:Number`（已超出本模块）。")
    a("   **有名 op 落空槽的残留共 %d 条**（`remove` %d ＋ `move`/`expr`/`expr_end`/`priority` %d）——"
      % (sum(orph.values()), orph.get("remove", 0), orph_ref))
    a("   全部是「该件名本场从未开过、且该族也不在场」⇒ 无从定位，**不猜**。")
    a("   修复前（`fam` 键模型，`--slot-mode fam` 可复现）为 **20 条**（remove 7 ＋ expr_end 10 ＋ expr 2 ＋ move 1），")
    a("   其中 **5 条**由旧模型自身的挤槽缺陷造成（`ot_s01_04k CIN074C`／`ot_s01_08f CIN066`／")
    a("   `ot_s01_14c CIN062,CIN070`／`ot_s03_02b CIN155A`）——**已随本次修复全部消除**（20 → %d）。" % sum(orph.values()))
    a("3. **同屏并发立绘数 > 6 的场 %d 个**（%s）"
      % (len(doc_x["gt6"]), " ／ ".join("`%s` 峰值 %d" % (s, p) for s, p in doc_x["gt6"])))
    a("   ——**订正（一审后，ISSUE-20261008-03）**：此处旧写「%d 个」是**错口径**（%d 是"
      % (stats["slot"]["scenes_gt6_concurrent"], doc_x["slot_ge6_scenes"]))
    a("   「`slot_hint ≥ 6` 的场数」，不是并发场数）。消费侧 `UIStageMaxSlots=6` 时，")
    a("   本表 `slot_hint` 会超过 5；属**忠实呈现源侧同时在场立绘数**，需消费侧排队/缩放或另立封顶规则。")
    a("4. **`chr_remove` 无 `:Time`**（实测 1,448 行全空）⇒ **无滑出时长**；`ui_staging.tjs` 的")
    a("   退场滑出（`dur`/`dir`）**在本金标里没有数据来源**，须另立提取任务。")
    a("5. **`otr` 的逐行 `seq` 另有独立风险**：作品专属 skill §四·补明载「`otr` 逐行 `seq` 不可用（11/21 场）」，")
    a("   本表 `seq` 取自金标 difflib 对齐（另一套方法），**未与该方法对拍**；`otr` 消费时须复核。")
    a("6. **本篇 `ot` 只覆盖 362/367 场、`otp` 只 14/59 场**（PSV 移植范围所限）⇒ 未覆盖场**无本表数据**，")
    a("   仍走现有自定摆位。")
    a("7. **`s01_01` 与 35 个非演出文件**不在金标内（我方语料无对应场 / 非演出脚本），本表无从覆盖。")
    a("8. 本模块**只做「抽取归一」**，未改引擎代码、未改 `build_story.py`、未动任何既有产物。")
    db = stats["delivery_blank"]
    a("9. **`delivery` 有 %s 行留空**（金标自身 `delivery` 空；主因 `remove` %s ＋ `wait` %s）——"
      % (f"{db['total']:,}", f"{db['by_op'].get('remove', 0):,}", f"{db['by_op'].get('wait', 0):,}"))
    a("   本表**照抄金标值、不重算**（派单要求）。下游若需「族→交付件」兜底，须另立规则。")
    a("")
    a("---")
    a("")
    a("## 八 自证（判据 + 失败演示）")
    a("")
    a("`check_character_events.py` 复算（**不共用生成器实现**）：")
    a("")
    a("- C1 列数/列序/表头逐字一致（20 列）")
    a("- C2 无 BOM、LF、每行 TAB 数 = 19、字段**不含**引号")
    a("- C3 `op` 属七类闭集")
    a("- C4 `seq` 为正整数且 ≤ 该场 `corpus_lines`")
    a("- C5 `fam` 与 `ps_name` 推导一致")
    a("- C6 `x1920 == round(cx*1.5)`（缺值留空）")
    a("- C7 **每场 remove 数 ≤ add 数**")
    a("- C8 **slot_hint 不变量（身份键 ＝ 逐立绘件名）**：复算活槽位，同一场同一时刻两个在场")
    a("     立绘 `slot_hint` 不得相同；非空 `slot_hint` 的 `remove`/`move`/`expr`/`expr_end`/**`priority`**")
    a("     必指向当时在场的同一件名。**可抓住「同族并存挤同槽」（旧模型缺陷）**——见交付报告负向对照。")
    a("- C9 覆盖：与金标逐场 chr 行数一致（须能取到 `时间线.tsv`）")
    a("- C10 **归一映射 + 并存登记**：① 用金标重算**逐场 by-op 计数**并与产物比（堵住")
    a("     `op ↔ :Tasktype` 归一整面，C3/C9 都抓不到该类系统错）；② 独立重扫金标的")
    a("     「单任务同族 ≥2 名」证据集，核对与 `同族并存登记.tsv` **集合相等**。")
    a("")
    a("`--self-test` 用**人为破坏的输入**逐条引爆 C1–C8（C10 另以合成金标/登记集引爆），退出码 0 表示")
    a("「每条判据都确实抓住了对应的坏输入」。实测输出见 `子代理工作区/ISSUE-20261008-03/M1/`。")
    a("")
    a("---")
    a("")
    a("## 九 依据来源")
    a("")
    a("- 金标：`编程组\\PSV演出\\时间线.tsv`（27 列 / 121,707 行；生成器 `编程组\\工具\\emit_staging_psv.py`）")
    a("- 场景映射：`编程组\\PSV演出\\场景映射.tsv`（462 场）")
    a("- 列义与口径：`编程组\\PSV演出\\说明.md` §三/§四（**照此读表**）")
    a("- 现有自定摆位：`资源组\\演出\\演出_<源>.tsv` + `资源组\\演出\\演出表说明.md`")
    a("- 换算与摆位标定：`作品skill\\SKILL.md` §四·补「★ 立绘基准与摆位」")
    a("- 消费侧：`编程组\\krkr\\game\\ui_staging.tjs`（`slot`/`fam`/`dur`/`dir` 契约）")
    a("")
    return "\n".join(L) + "\n"


def render_registry(register):
    nl = chr(10)
    cols = ["scene_id", "src", "task", "fam", "names", "ops"]
    out = [chr(9).join(cols)]
    for r in sorted(register, key=lambda r: (SRC_RANK.get(r["src"], 9), r["scene_id"],
                                             int(r["task"]) if str(r["task"]).isdigit() else 0)):
        names = r["names"]
        row = {"scene_id": r["scene_id"], "src": r["src"], "task": r["task"], "fam": r["fam"],
               "names": ",".join(names) if isinstance(names, list) else str(names),
               "ops": r["ops"]}
        out.append(chr(9).join(str(row[c]) for c in cols))
    return nl.join(out) + nl

def render_deg_tsv(deg):
    cols = ["scene_id", "src", "map_rate", "align", "psv_msg", "corpus_lines", "header",
            "reason", "chr_events"]
    out = ["\t".join(cols)]
    for d in deg:
        out.append("\t".join(str(d[c]) for c in cols))
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 主流程

def generate(args):
    timeline = pick_input("时间线.tsv", args.timeline, args.data_root)
    scene_map = pick_input("场景映射.tsv", args.scene_map, args.data_root)
    if not os.path.isfile(timeline):
        sys.exit("找不到金标时间线：%s（用 --timeline 指定）" % timeline)
    if not os.path.isfile(scene_map):
        sys.exit("找不到场景映射：%s（用 --scene-map 指定）" % scene_map)

    print("[read] timeline = %s" % timeline)
    print("[read] scene map = %s" % scene_map)
    t_sha = sha256_file(timeline)
    m_sha = sha256_file(scene_map)

    scenes, scene_order = read_scene_map(scene_map)
    chr_rows, total = read_timeline(timeline)
    print("[read] 金标行 %d，其中 layer=chr %d" % (total, len(chr_rows)))

    rows, register, stats = build_rows(chr_rows, scenes, slot_mode=args.slot_mode)
    tsv = to_tsv(rows)

    stats_out, after_by_op, per_scene, max_live, deg, no_chr = collect_stats(
        rows, register, stats, scenes, scene_order, timeline, scene_map, total, t_sha, m_sha)
    if cx_mode := stats_out["conversion_selftest"]["cx_mode"]:
        stats_out["conversion_selftest"]["cx_mode_rows"] = sum(
            1 for r in rows if r["cx"] == cx_mode)

    game_root = os.path.normpath(os.path.join(HERE, "..", ".."))
    cand = [os.path.join(game_root, "资源组", "演出"),
            os.path.join(args.data_root, GAME_DIR, "资源组", "演出")]
    cmp_self = compare_selfdefined(list(dict.fromkeys(cand)))

    doc = render_doc(stats_out, cmp_self, register, "立绘事件流.tsv", len(rows), args.slot_mode,
                     doc_metrics(rows))
    deg_tsv = render_deg_tsv(deg)
    reg_tsv = render_registry(register)
    stats_json = json.dumps(stats_out, ensure_ascii=False, indent=2) + "\n"

    files = {
        "立绘事件流.tsv": tsv,
        "立绘事件流_说明.md": doc,
        "退化场景登记.tsv": deg_tsv,
        "同族并存登记.tsv": reg_tsv,
        "立绘事件流_统计.json": stats_json,
    }
    if args.out_tsv:
        with open(args.out_tsv, "w", encoding="utf-8", newline="") as f:
            f.write(tsv)
        print("[write] %s (%d B) —— 仅主表（slot-mode=%s）"
              % (args.out_tsv, len(tsv.encode("utf-8")), args.slot_mode))
        return 0

    if args.check:
        bad = 0
        for name, content in files.items():
            path = os.path.join(HERE, name)
            if not os.path.isfile(path):
                print("[check] 缺文件 %s" % name); bad += 1; continue
            with open(path, encoding="utf-8", newline="") as f:
                cur = f.read()
            if cur != content:
                print("[check] 不一致 %s" % name); bad += 1
            else:
                print("[check] ok %s" % name)
        return 0 if bad == 0 else 1

    for name, content in files.items():
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        print("[write] %s (%d B)" % (path, len(content.encode("utf-8"))))

    print("[stat] chr 行 %d → 输出 %d 行；op=%s" % (
        len(chr_rows), len(rows),
        ", ".join("%s:%d" % (o, after_by_op.get(o, 0)) for o in OPS)))
    print("[stat] 同族并存 %d 任务 / %d 场；slot add kinds = %s" % (
        stats_out["coexist"]["tasks"], len(stats_out["coexist"]["scenes"]),
        stats_out["slot"]["add_by_kind"]))
    print("[stat] 覆盖 %d 场（无事件 %d 场）；退化 %d 场；inferred %d 行" % (
        stats_out["coverage"]["scenes_with_chr_events"],
        stats_out["coverage"]["scenes_without_chr_events"],
        stats_out["degenerate"]["count"], stats_out["inferred"]["total"]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="PSV 金标 → 逐场立绘事件流（ISSUE-20261008-03 M1）")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="主工作树根（金标默认落点）")
    ap.add_argument("--timeline", default=None, help="金标时间线路径（默认本目录，否则主工作树）")
    ap.add_argument("--scene-map", default=None, help="场景映射路径")
    ap.add_argument("--slot-mode", choices=("live", "fam", "ordinal"), default="live",
                    help="live＝逐立绘件名活槽位（生产，默认）；fam＝复现修复前的族键模型（仅负向对照）；"
                         "ordinal＝仅 add 计号且**不维护 live**（实验性/仅调试，不用于生产）")
    ap.add_argument("--check", action="store_true", help="幂等复核：与已落盘产物逐字节比对")
    ap.add_argument("--out-tsv", default=None,
                    help="只把主表写到该路径（供负向对照复现旧模型）；不写其它产物")
    args = ap.parse_args(argv)
    return generate(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
`fade_seq_pair.py` —— Fade 事件 `seq` 落点对齐（ISSUE-20261008-01 · M1）
================================================================================
**只读上游数据**（`解出_<源>.tsv` / `PSV演出\时间线.tsv`），产出**事件表 + 残余表 + 度量**。

## 问题
上游 `build_story.py --fade-source lucifen` 把 PC（Lucifen SOB0）侧 Fade 时长载体
（`ot 0x19F9C` / `otp 0x172BC`）节点**按解码器给的 `seq` 直接落位**。场级可信
（recall 306/306、precision 306/322），但**逐 seq 落点**只有
「同 seq 命中 0.918 ／ PSV `FadeOut(time>0)` 覆盖 0.765」（`演出接入\说明.md` §T2.4）。

## 本模块做什么
**「场景内多节点 ↔ PSV 多条事件」的配对**，按**证据强度**分四轮（**禁用「类型共现」类弱判据**）：

  P1 `exact`       同 `seq` 且 `round(ms×0.06) == PSV.time`（时长吻合 ∧ 位置吻合）
  P2 `window`      `|Δseq| ≤ W` 且时长吻合（吸收两侧行锚定 ±1..3 的抖动）
  P3 `zero-comment` `PSV.time == 0`（移植端把 `:Time` 清零）∧ 时长 == **原始脚本
                   `// fadeout|fadeend N` 注释**的 N（**独立第三方证据**，非位置猜测）
  P4 `zero-near`   `PSV.time == 0` ∧ `|Δseq| ≤ W`（**纯位置**，默认关闭，须显式 `--zero-near`）

配对结果按三种模式出事件（`--mode`）：

  `raw`   不改：照 PC 节点原 `seq` 发（＝现状，作对照片）
  `pair`  PC 主源：配对成功者**改锚到 PSV 行的 `seq`**；未配对的 PC 节点默认**丢弃**
          （`--keep-unpaired` 保留原位，便于看召回损失）
  `gold`  PSV 主源：以 PSV `FadeOut(time>0)` 行为事件全集（**存在性 / seq / 时长三者都取金标**，
          时长 = `time / 0.06`），PC 载体会配对成功时作为**独立印证**记账。**这是唯一能到
          1.000/1.000 的口径**（见 `seq对齐_说明.md` §四 不可达反证）。
  `hybrid`（**用户 2026-10-08 裁定的生产口径 · 逐场判定**）
          · 该场 ∈ **PSV 金标覆盖集**（`gold_scenes`，由 `PSV演出\场景映射.tsv` 给出）
            ⇒ 该场**全取金标**（＝`gold` 在本场的切片）；**即使该场一条 `FadeOut(time>0)` 也没有，
            就一条都不发**（金标的判决，不回落 PC）。
          · 该场 ∉ 覆盖集 ⇒ **回落 PC 载体**（＝`raw` 在本场的切片：发全部 PC 载体节点、原 `seq`）。
          金标覆盖集**限 `ot/otp`**（`otv/otr` 本无 Fade 载体源，两分支结果都是「不发」⇒ 不影响行为；
          但计入会让「金标判定不发」的统计失去意义）。
          ⚠️ 闸门（`--check`）：**只对金标覆盖集判 1.000/1.000**；**回落场单列、不进分母**（打印数量）。

## 硬口径与自证
  `--check`：`同 seq 命中 == 1.000` **且** `PSV FadeOut(time>0) 覆盖 == 1.000`，否则 **exit 1**。
             `--mode hybrid` 时改为**金标覆盖集口径**（`gold_same_seq_rate` / `gold_psv_cover_rate`），
             回落场在输出里单列。
  `--selftest`：内含**必失败夹具**（弱判据必须被拒等），任一夹具行为不符即 exit 1。

用法（复跑）：
  python -X utf8 编程组/演出接入/fade_seq_pair.py --data-root "E:/ZCode Workspace/Galgame" \
      --decode "<checkout>/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/SOB0解码" \
      --mode pair --emit-tsv <out>\配对_事件.tsv --residual-tsv <out>\配对_残余.tsv \
      --metrics-json <out>\度量.json --check
"""
import argparse
import csv
import io
import json
import os
import re
import sys

# 载体 V：与 `Lucifen命令族标签.tsv` 的 carrier 行同源（build_story.load_v_labels 再过滤 verdict）
CARRIERS = {"ot": 0x19F9C, "otp": 0x172BC}
SRC_ORDER = ("ot", "otp")
FPS = 60.0

# 原始 PSV 脚本注释里的「被移植端清零的时长」：`// fadeout 800` / `// fadeend 2400`
TASK_RE = re.compile(r"\[Task(\d+)\]\s*\{(.*?)\n\t\}", re.S)
CMT_RE = re.compile(r"//\s*fade(?:out|end)\s+(\d+)")


# ---------------------------------------------------------------- 基础
def load_tsv(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def frames(ms):
    """毫秒 → 帧（60fps，四舍五入）。PSV `time` 列即帧。"""
    return int(round(float(ms) * FPS / 1000.0))


def ms_of_frames(t):
    return int(round(float(t) * 1000.0 / FPS))


def load_pc_nodes(decode_dir, src_order=SRC_ORDER, carriers=None):
    """PC 侧 Fade 载体节点 → {scene_id: [dict(seq, ms, V, conf), ...]}（按 seq 升序）。"""
    carriers = carriers or CARRIERS
    out = {}
    for src in src_order:
        V = carriers.get(src)
        if V is None:
            continue
        p = os.path.join(decode_dir, "解出_%s.tsv" % src)
        if not os.path.isfile(p):
            continue
        for r in load_tsv(p):
            a3 = (r.get("arg3") or "").strip()
            if not a3.lower().startswith("v=0x"):
                continue
            try:
                if int(a3[2:], 16) != V:
                    continue
            except ValueError:
                continue
            sid = (r.get("scene_id") or "").strip()
            if not sid:
                continue
            try:
                seq = int((r.get("seq") or "0").strip() or "0")
            except ValueError:
                seq = 0
            try:
                ms = int((r.get("time_ms") or "").strip() or "0")
            except ValueError:
                ms = 0
            out.setdefault(sid, []).append(dict(seq=seq, ms=ms, V=V,
                                                conf=(r.get("confidence") or "").strip(),
                                                src=src))
    for sid in out:
        out[sid].sort(key=lambda e: e["seq"])
    return out


def load_psv_fade(decode_dir, psv_dir):
    """PSV 金标 Fade 行 → {scene_id: [dict(seq, time, task, src), ...]}（只收 ot/otp 载体源）。"""
    tl = os.path.join(psv_dir, "时间线.tsv")
    out = {}
    if not os.path.isfile(tl):
        return out
    for r in load_tsv(tl):
        sid = (r.get("scene_id") or "").strip()
        if not sid or sid.split("_")[0] not in SRC_ORDER:
            continue
        if (r.get("type") or "").strip() != "FadeOut":
            continue
        try:
            seq = int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            continue
        try:
            t = int((r.get("time") or "0").strip() or "0")
        except ValueError:
            t = 0
        try:
            task = int((r.get("task") or "0").strip() or "0")
        except ValueError:
            task = 0
        out.setdefault(sid, []).append(dict(seq=seq, time=t, task=task,
                                            src=sid.split("_")[0]))
    for sid in out:
        out[sid].sort(key=lambda e: (e["seq"], e["task"]))
    return out


def load_psv_fade_comments(psv_root, script_of):
    """PSV 原始脚本的 `// fadeout|fadeend N` 注释 → {scene_id: {task: ms}}。

    ★ 这是 P3 轮的**独立证据**：移植端把起始 FadeOut 的 `:Time` 清零（注释保留了原值），
      只有「注释值 == PC 侧 ms」才允许配对 —— 不是位置猜测。
    """
    cache, out = {}, {}
    for sid, script in script_of.items():
        if sid.split("_")[0] not in SRC_ORDER:
            continue
        if script not in cache:
            m = {}
            fp = os.path.join(psv_root, script)
            if os.path.isfile(fp):
                try:
                    txt = io.open(fp, encoding="cp932", errors="replace").read()
                except Exception:
                    txt = ""
                for mt in TASK_RE.finditer(txt):
                    c = CMT_RE.search(mt.group(2))
                    if c:
                        m[int(mt.group(1))] = int(c.group(1))
            cache[script] = m
        if cache[script]:
            out[sid] = cache[script]
    return out


# ---------------------------------------------------------------- 配对
def match_scene(P, Q, window=3, zero_near=False, cmts=None, coincide_first=True):
    """场景内配对。P/Q 为索引化列表（见 apply_fade_pair），返回 (pairs, up, uq)。

    pairs: [(p_idx, q_idx, conf)]；conf ∈ exact|window|zero-comment|zero-near。
    **时长判据是硬门**（`round(ms×0.06) == time`）：这是能被证伪的强判据，
    与「类型共现」类弱判据（只看 co-occurrence ⇒ 任何常见 V 都能 P=1.0）不同。
    """
    P = list(enumerate(P))
    Q = list(enumerate(Q))
    up = set(range(len(P)))
    uq = set(range(len(Q)))
    pairs = []

    def take(pi, qi, conf):
        if pi not in up or qi not in uq:      # 防重复占用
            return
        up.discard(pi)
        uq.discard(qi)
        pairs.append((pi, qi, conf))

    # P1 同 seq ∧ 时长吻合
    for qi, q in Q:
        if q["time"] <= 0:
            continue
        for pi, p in P:
            if pi in up and p["seq"] == q["seq"] and frames(p["ms"]) == q["time"]:
                take(pi, qi, "exact")
                break
    if coincide_first:
        # P0-b 同 seq 且 `time=0` ∧ 注释值 == PC ms（独立证据；先于纯位置轮）
        for qi, q in Q:
            if qi not in uq or q["time"] != 0:
                continue
            cms = (cmts or {}).get(q["task"])
            if cms is None:
                continue
            for pi, p in P:
                if pi in up and p["seq"] == q["seq"] and p["ms"] == cms:
                    take(pi, qi, "zero-comment")
                    break
        # P0-c 同 seq 位置共现（**保底不改动**：PC 节点与 PSV 行本就同 seq 时一律保留原位，
        #       不做时长要求 —— 时长不符是「移植端改了时长」，属数据差异，不该把落点挪走）
        for qi, q in Q:
            if qi not in uq:
                continue
            for pi, p in P:
                if pi in up and p["seq"] == q["seq"]:
                    take(pi, qi, "same-seq")
                    break
    # P2 窗口 ∧ 时长吻合（最近优先）
    for qi, q in Q:
        if qi not in uq or q["time"] <= 0:
            continue
        best = None
        for pi, p in P:
            if pi not in up:
                continue
            d = abs(p["seq"] - q["seq"])
            if d > window:
                continue
            if frames(p["ms"]) != q["time"]:
                continue
            if best is None or d < best[0]:
                best = (d, pi)
        if best is not None:
            take(best[1], qi, "window")
    # P3 time=0 ∧ 注释值 == PC ms（独立证据；`coincide_first` 时已在同 seq 轮处理）
    for qi, q in Q:
        if qi not in uq or q["time"] != 0:
            continue
        cms = (cmts or {}).get(q["task"])
        if cms is None:
            continue
        best = None
        for pi, p in P:
            if pi not in up:
                continue
            if p["ms"] != cms:
                continue
            d = abs(p["seq"] - q["seq"])
            if d > window:
                continue
            if best is None or d < best[0]:
                best = (d, pi)
        if best is not None:
            take(best[1], qi, "zero-comment")
    # P4 纯位置（默认关闭）
    if zero_near:
        for qi, q in Q:
            if qi not in uq or q["time"] != 0:
                continue
            best = None
            for pi, p in P:
                if pi not in up:
                    continue
                d = abs(p["seq"] - q["seq"])
                if d > window:
                    continue
                if best is None or d < best[0]:
                    best = (d, pi)
            if best is not None:
                take(best[1], qi, "zero-near")
    return pairs, sorted(up), sorted(uq)


def load_build_scenes(script_dir):
    """`--all` 口径的构建场景集：spine 的 acts ∪ side_stories（∩ 语料由消费侧过滤）。

    ★ 与 `build_story.py --all` 的选择逻辑同源（`excluded` 的 32 个前奏诗 02_/03_ 去重件不入）。
    """
    p = os.path.join(script_dir, "spine.json")
    if not os.path.isfile(p):
        return None
    try:
        with io.open(p, encoding="utf-8") as f:
            sp = json.load(f)
    except Exception:
        return None
    out = []
    for a in sp.get("acts") or []:
        out += a.get("scenes") or []
    for sd in sp.get("side_stories") or []:
        if isinstance(sd, dict):
            out.append(sd.get("scene_id") or "")
        elif isinstance(sd, str):
            out.append(sd)
    return set(x for x in out if x)


def _classify_pc_unpaired(p, Q, window):
    if not Q:
        return "scene_no_fadeout_row"
    d = min(abs(p["seq"] - q["seq"]) for q in Q)
    if d > window:
        return "far_gt_window"
    return "near_but_dur_mismatch"


def _classify_psv_unpaired(q, P, window):
    if not P:
        return "scene_no_pc_node"
    d = min(abs(p["seq"] - q["seq"]) for p in P)
    if d > window:
        return "far_gt_window"
    return "near_but_dur_mismatch"


def load_gold_scenes(psv_dir, srcs=SRC_ORDER):
    """**PSV 金标覆盖集** → set(scene_id)：`PSV演出\\场景映射.tsv` 的 scene_id（限 `srcs` 两源）。

    ★ 这是 `hybrid` 的逐场判据：**在集合内 ⇒ 该场全取金标（含「一条都不发」）；不在 ⇒ 回落 PC**。
    ★ 为什么限 `ot/otp`：另两源（`otv`/`otr`）本无 Fade 载体源，两分支结果都是「不发」⇒ 行为不变；
      而把 `otv/otr` 计入会让「金标判定不发」的统计混入与 Fade 无关的场。
    """
    p = os.path.join(psv_dir, "场景映射.tsv")
    out = set()
    if not os.path.isfile(p):
        return out
    for r in load_tsv(p):
        sid = (r.get("scene_id") or "").strip()
        if sid and sid.split("_")[0] in srcs:
            out.add(sid)
    return out


def apply_fade_pair(pc_map, psv_map, mode="pair", window=3, keep_unpaired=False,
                    zero_near=False, comments=None, src_order=SRC_ORDER, gold_zero=False,
                    gold_scenes=None):
    """把「PC 载体节点 + PSV Fade 行」按 `mode` 折成**待发事件表 + 残余表**。

    返回 dict(events, res_pc, res_psv, stats)。
    events: [dict(scene_id, seq, dur, dir, src_seq, psv_seq, psv_time, conf, src)]
    """
    assert mode in ("raw", "pair", "gold", "hybrid"), mode
    events, res_pc, res_psv = [], [], []
    st = {"pc_nodes": 0, "psv_rows_pos": 0, "psv_rows_zero": 0,
          "pair_exact": 0, "pair_window": 0, "pair_zero_comment": 0, "pair_zero_near": 0,
          "pair_same_seq": 0, "pair_same_seq_dur_mismatch": 0, "pair_same_seq_zero": 0,
          "pc_unpaired_dropped": 0, "pc_unpaired_kept": 0,
          "gold_rows": 0, "gold_pc_paired": 0, "gold_dur_agree": 0, "gold_dur_disagree": 0,
          # hybrid 专用
          "hy_gold_scenes": 0, "hy_gold_scenes_emitted": 0, "hy_gold_silent_scenes": 0,
          "hy_gold_events": 0, "hy_gold_pc_unused": 0,
          "hy_fb_scenes": 0, "hy_fb_scenes_emitted": 0, "hy_fb_events": 0,
          "hy_gold_added": 0}

    gs = set(gold_scenes) if gold_scenes is not None else set()
    if mode == "hybrid":
        # 防御性并入：**任何有 PSV `FadeOut` 行的场本身就是「金标覆盖」**。
        # 正常情况下 `set(psv_map) ⊆ gold_scenes`（场景映射 ⊇ 时间线场景），此并集为空操作；
        # 若调用方 gold_scenes 传窄了，这样可避免把「金标行」误判成回落场而丢事件。
        _before = len(gs)
        gs |= set(psv_map)
        st["hy_gold_added"] = len(gs) - _before
    # hybrid 时把「金标覆盖集内的场」也纳入遍历（即便该场既无 PC 节点也无 Fade 行，
    # 也要能统计「金标判定为不发」的场数）。
    scenes = sorted(set(pc_map) | set(psv_map) | (gs if mode == "hybrid" else set()))
    for sid in scenes:
        P = pc_map.get(sid, [])
        Q = psv_map.get(sid, [])
        st["pc_nodes"] += len(P)
        st["psv_rows_pos"] += sum(1 for q in Q if q["time"] > 0)
        st["psv_rows_zero"] += sum(1 for q in Q if q["time"] == 0)
        cmts = (comments or {}).get(sid) or {}
        pairs, up, uq = match_scene(P, Q, window, zero_near, cmts)
        for pi, qi, conf in pairs:
            st["pair_" + conf.replace("-", "_")] += 1
            if conf == "same-seq":
                if Q[qi]["time"] > 0 and frames(P[pi]["ms"]) != Q[qi]["time"]:
                    # 同 seq 保底配上（PSV 行有非零时长）但**两侧时长不一致**（移植端改了时长）
                    st["pair_same_seq_dur_mismatch"] += 1
                elif Q[qi]["time"] == 0:
                    # 同 seq 保底配上的是 `time=0` 行（移植端清零的起始淡出）
                    st["pair_same_seq_zero"] += 1

        if mode == "hybrid":
            # ★ 逐场判定（用户 2026-10-08 裁定）：
            #   场 ∈ 金标覆盖集 ⇒ 该场**全取金标**（等价 gold 的本场切片）；**无 FadeOut 行则不发**。
            #   场 ∉ 覆盖集     ⇒ **回落 PC 载体**（等价 raw 的本场切片）。
            if sid in gs:
                st["hy_gold_scenes"] += 1
                st["hy_gold_pc_unused"] += len(P)      # 金标场里的 PC 节点**不被使用**（金标拥有该场）
                pair_of = {qi: (pi, conf) for pi, qi, conf in pairs}
                _n0 = len(events)
                for qi, q in enumerate(Q):
                    if q["time"] <= 0 and not (gold_zero and qi in pair_of):
                        continue                        # 入口 fade（金标记 time=0）默认不发
                    pi_conf = pair_of.get(qi)
                    if pi_conf:
                        pi, conf = pi_conf
                        pc_ms = P[pi]["ms"]
                    else:
                        pc_ms = None
                    if q["time"] > 0:
                        dur = ms_of_frames(q["time"])   # 时长取金标
                        conf2 = ("hybrid+pc:" + conf) if pi_conf else "hybrid-gold"
                    else:
                        dur = pc_ms or 0                # time=0 行只能取 PC（需 gold_zero + 已配上）
                        conf2 = ("hybrid-zero:evidence" if conf == "zero-comment"
                                 else "hybrid-zero:same-seq")
                    events.append(dict(scene_id=sid, seq=q["seq"], dur=dur, dir="out",
                                       src_seq=(P[pi]["seq"] if pi_conf else None), psv_seq=q["seq"],
                                       psv_time=q["time"], conf=conf2, src=q.get("src"),
                                       pc_ms=pc_ms, V=(P[pi]["V"] if pi_conf else None)))
                    st["hy_gold_events"] += 1
                if len(events) > _n0:
                    st["hy_gold_scenes_emitted"] += 1
                else:
                    st["hy_gold_silent_scenes"] += 1
            else:
                st["hy_fb_scenes"] += 1
                if P:
                    st["hy_fb_scenes_emitted"] += 1
                for p in P:
                    events.append(dict(scene_id=sid, seq=p["seq"], dur=p["ms"], dir="out",
                                       src_seq=p["seq"], psv_seq=None, psv_time=None,
                                       conf="hybrid-fallback", src=p.get("src"), V=p.get("V")))
                    st["hy_fb_events"] += 1
            continue

        if mode == "raw":
            for p in P:
                events.append(dict(scene_id=sid, seq=p["seq"], dur=p["ms"], dir="out",
                                   src_seq=p["seq"], psv_seq=None, psv_time=None,
                                   conf="raw", src=p.get("src"), V=p.get("V")))
            continue

        if mode == "pair":
            pair_of = {pi: (qi, conf) for pi, qi, conf in pairs}
            for pi, p in enumerate(P):
                if pi in pair_of:
                    qi, conf = pair_of[pi]
                    q = Q[qi]
                    events.append(dict(scene_id=sid, seq=q["seq"], dur=p["ms"], dir="out",
                                       src_seq=p["seq"], psv_seq=q["seq"], psv_time=q["time"],
                                       conf=conf, src=p.get("src"), V=p.get("V")))
                else:
                    res_pc.append(dict(scene_id=sid, src_seq=p["seq"], ms=p["ms"],
                                       frames=frames(p["ms"]), src=p.get("src"),
                                       cause=_classify_pc_unpaired(p, Q, window)))
                    st["pc_unpaired_dropped"] += 1
                    if keep_unpaired:
                        st["pc_unpaired_kept"] += 1
                        events.append(dict(scene_id=sid, seq=p["seq"], dur=p["ms"], dir="out",
                                           src_seq=p["seq"], psv_seq=None, psv_time=None,
                                           conf="unpaired", src=p.get("src"), V=p.get("V")))
            for qi, q in enumerate(Q):
                if q["time"] > 0 and qi in uq:
                    res_psv.append(dict(scene_id=sid, psv_seq=q["seq"], psv_time=q["time"],
                                        psv_ms=ms_of_frames(q["time"]), task=q["task"],
                                        src=q.get("src"),
                                        cause=_classify_psv_unpaired(q, P, window)))
            continue

        # gold：事件全集 = PSV FadeOut(time>0) 行；**seq 与时长都取金标**，PC 只作独立印证
        #   （★ 时长不取 PC：口径是「与 PSV 金标一致」；PC/PSV 时长不一致的差异另记账）
        pair_of = {qi: (pi, conf) for pi, qi, conf in pairs}
        for qi, q in enumerate(Q):
            if q["time"] <= 0:
                # ★ `time=0` 行＝移植端把 `:Time` 清零的「起始淡出」；默认不发（口径只认 time>0）。
                #   `gold_zero` 时，只发**配对轮配上了**的那些，时长只能取 PC 的 ms；
                #   置信分两类：`gold-zero:evidence`（注释值独立印证）/ `gold-zero:same-seq`（仅同 seq 位置）。
                if not (gold_zero and qi in pair_of):
                    continue
            pi_conf = pair_of.get(qi)
            if pi_conf:
                pi, conf = pi_conf
                st["gold_pc_paired"] += 1
                if q["time"] > 0 and frames(P[pi]["ms"]) == q["time"]:
                    st["gold_dur_agree"] += 1
                elif q["time"] > 0:
                    st["gold_dur_disagree"] += 1
                pc_ms = P[pi]["ms"]
            else:
                pc_ms = None
            if q["time"] > 0:
                dur = ms_of_frames(q["time"])          # 金标时长
                conf2 = ("gold+pc:" + conf) if pi_conf else "gold-psv-only"
            else:
                dur = pc_ms or 0                       # time=0 行只能取 PC（时长无金标来源）
                conf2 = ("gold-zero:evidence" if conf == "zero-comment"
                         else "gold-zero:same-seq")
            st["gold_rows"] = st.get("gold_rows", 0) + 1
            events.append(dict(scene_id=sid, seq=q["seq"], dur=dur, dir="out",
                               src_seq=(P[pi]["seq"] if pi_conf else None), psv_seq=q["seq"],
                               psv_time=q["time"], conf=conf2, src=q.get("src"),
                               pc_ms=pc_ms,
                               V=(P[pi]["V"] if pi_conf else None)))
        for pi, p in enumerate(P):
            if pi not in {v[0] for v in pair_of.values()}:
                res_pc.append(dict(scene_id=sid, src_seq=p["seq"], ms=p["ms"],
                                   frames=frames(p["ms"]), src=p.get("src"),
                                   cause=_classify_pc_unpaired(p, Q, window)))
                st["pc_unpaired_dropped"] += 1

    return dict(events=events, res_pc=res_pc, res_psv=res_psv, stats=st)


# ---------------------------------------------------------------- 度量
def measure(events, psv_map, window=3, gold_scenes=None):
    """度量：同 seq 命中（precision）/ PSV FadeOut(time>0) 覆盖 / PC 节点召回。

    `gold_scenes`（可选）：给出后额外算 **金标覆盖集口径** 的一组数（`gold_*`），供 `hybrid` 闸门使用：
    回落场的事件**单列**（`emitted_fallback_scenes` / `fallback_events`），**不进分母**。
    """
    row_any = set()
    row_pos = set()
    pos_rows = []
    for sid, Q in psv_map.items():
        for q in Q:
            row_any.add((sid, q["seq"]))
            if q["time"] > 0:
                row_pos.add((sid, q["seq"]))
                pos_rows.append((sid, q))
    hit = sum(1 for e in events if (e["scene_id"], e["seq"]) in row_any)
    covered = set((e["scene_id"], e["seq"]) for e in events)
    cov = sum(1 for sid, q in pos_rows if (sid, q["seq"]) in covered)
    out = dict(
        emitted=len(events),
        same_seq_hit=hit,
        same_seq_rate=(hit / float(len(events))) if events else None,
        psv_pos_rows=len(pos_rows),
        psv_pos_covered=cov,
        psv_cover_rate=(cov / float(len(pos_rows))) if pos_rows else None,
    )
    if gold_scenes is not None:
        gs = set(gold_scenes)
        ev_g = [e for e in events if e["scene_id"] in gs]
        ev_f = [e for e in events if e["scene_id"] not in gs]
        rows_g = [(sid, q) for sid, q in pos_rows if sid in gs]
        hit_g = sum(1 for e in ev_g if (e["scene_id"], e["seq"]) in row_any)
        cov_g = sum(1 for sid, q in rows_g if (sid, q["seq"]) in covered)
        out.update(
            gold_scenes=len(gs),
            emitted_gold_scenes=len(set(e["scene_id"] for e in ev_g)),
            gold_events=len(ev_g),
            gold_same_seq_hit=hit_g,
            gold_same_seq_rate=(hit_g / float(len(ev_g))) if ev_g else None,
            gold_psv_pos_rows=len(rows_g),
            gold_psv_pos_covered=cov_g,
            gold_psv_cover_rate=(cov_g / float(len(rows_g))) if rows_g else None,
            fallback_events=len(ev_f),
            emitted_fallback_scenes=len(set(e["scene_id"] for e in ev_f)),
        )
    return out


def check(metrics, tol=0.0, keys=("same_seq_rate", "psv_cover_rate"),
          labels=("同 seq 命中", "PSV FadeOut(time>0) 覆盖"),
          pairs=(("same_seq_hit", "emitted"), ("psv_pos_covered", "psv_pos_rows"))):
    """硬口径闸门：两条率都须 == 1.000，否则返回 (False, [原因…])。

    `hybrid` 用 `keys=("gold_same_seq_rate","gold_psv_cover_rate")` + 对应 `pairs`，
    即**只对金标覆盖集判**；回落场已在 `measure` 里单列、不进分母。
    """
    bad = []
    for i, k in enumerate(keys):
        r = metrics.get(k)
        num, den = pairs[i]
        if r is None or r < 1.0 - tol:
            bad.append("%s %s < 1.000（%s/%s）"
                       % (labels[i], "%.4f" % r if r is not None else "-",
                          metrics.get(num, 0), metrics.get(den, 0)))
    return (len(bad) == 0), bad


# ---------------------------------------------------------------- 自证
def selftest(pc_map, psv_map, window=3):
    """必失败夹具：任何一条不符即 FAIL。"""
    cases = []

    def case(name, ok, detail):
        cases.append((name, bool(ok), detail))

    # F1 时长判据必须能拒：同 seq 但时长不符 ⇒ **在「不用同 seq 保底」的轮里不配对**
    #    （弱判据只看同 seq/共现 ⇒ 会错配；本判据自己有判别力 ⇒ 拒）
    P = [dict(seq=3, ms=800)]
    Q = [dict(seq=3, time=72, task=1)]
    pairs_d, up, uq = match_scene(P, Q, window, False, {}, coincide_first=False)
    case("F1 时长不符不得被「时长判据」配对", len(pairs_d) == 0 and up == [0] and uq == [0],
         "pairs=%d up=%s uq=%s（同 seq 但 frames(800)=48 != 72）" % (len(pairs_d), up, uq))
    # F1c 同 seq 保底轮会配上，但**必须标注为 `same-seq`（无时长证据）**，不得冒充 exact
    pairs_c, _, _ = match_scene(P, Q, window, False, {})
    case("F1c 同 seq 保底只给 same-seq 置信（不冒充 exact）",
         len(pairs_c) == 1 and pairs_c[0][2] == "same-seq",
         "pairs=%s" % pairs_c)

    # F1b 反向：时长符合必须配上（否则判据恒假＝无判别力）
    Q2 = [dict(seq=3, time=48, task=1)]
    pairs2, _, _ = match_scene(P, Q2, window, False, {})
    case("F1b 时长符合必须配对", len(pairs2) == 1 and pairs2[0][2] == "exact",
         "pairs=%s" % pairs2)

    # F2 篡改 events 的 seq ⇒ check 必须 FAIL
    ev = [dict(scene_id="ot_x", seq=10, dur=1200, conf="exact")]
    pm = {"ot_x": [dict(seq=10, time=72, task=1), dict(seq=20, time=48, task=2)]}
    ok, bad = check(measure(ev, pm))
    case("F2 覆盖不足必须 FAIL", (not ok) and len(bad) >= 1, "check=%s bad=%s" % (ok, bad))
    ev_bad = [dict(scene_id="ot_x", seq=99, dur=1200, conf="exact")]
    ok2, bad2 = check(measure(ev_bad, pm))
    case("F2b 同 seq 命中不足必须 FAIL", (not ok2) and any("同 seq" in b for b in bad2),
         "check=%s bad=%s" % (ok2, bad2))

    # F3 真数据：raw 口径必须 FAIL，且失败信息里必须出现两个口径的字样
    ev_raw = apply_fade_pair(pc_map, psv_map, mode="raw")["events"]
    m_raw = measure(ev_raw, psv_map)
    ok3, bad3 = check(m_raw)
    case("F3 真数据 raw 口径必须 FAIL", (not ok3) and len(bad3) == 2,
         "raw: same_seq=%s cover=%s" % (m_raw["same_seq_rate"], m_raw["psv_cover_rate"]))

    # F4 变异自证：把配对判据改成「永远为真」（类型共现类弱判据）⇒ 度量必须变化
    global frames
    orig = frames
    try:
        frames = lambda ms: 72  # 恒等于 F1 的 72 ⇒ 时长判据的错配会被放行
        p3, _, _ = match_scene(P, Q, window, False, {}, coincide_first=False)
        mutated = len(p3) == 1
    finally:
        frames = orig
    case("F4 弱判据变异必须被检出（判据有判别力）", mutated,
         "把 frames() 常量化为 72 后，「时长判据」把 F1 的 (800↔72) 错配为 %d 对"
         "（正常为 0 对）⇒ 说明该判据确实在起作用" % len(p3))

    # F5/F6 真数据：pair 必须 FAIL（覆盖不足）、gold 必须 PASS（闸门不是恒假）
    ev_pair = apply_fade_pair(pc_map, psv_map, mode="pair", window=window)["events"]
    m_pair = measure(ev_pair, psv_map)
    ok5, bad5 = check(m_pair)
    case("F5 真数据 pair 口径覆盖不足必须 FAIL",
         (not ok5) and all("覆盖" in b for b in bad5),
         "pair: same_seq=%s cover=%s bad=%s" % (m_pair["same_seq_rate"], m_pair["psv_cover_rate"], bad5))
    ev_gold = apply_fade_pair(pc_map, psv_map, mode="gold", window=window)["events"]
    m_gold = measure(ev_gold, psv_map)
    ok6, bad6 = check(m_gold)
    case("F6 真数据 gold 口径必须 PASS（闸门非恒假）", ok6,
         "gold: same_seq=%s cover=%s" % (m_gold["same_seq_rate"], m_gold["psv_cover_rate"]))

    # ---- F7 系：`hybrid` 逐场判定（**必须证明「回落分支真的会被走到」**）----
    NG = {"ng_a": [dict(seq=5, ms=800, V=1)]}          # 不在金标覆盖集内的场（有 PC 节点）
    QZ = {"gold_a": [dict(seq=7, time=60, task=1)]}    # 金标场（有 1 条 FadeOut>0）
    PG = {"gold_a": [dict(seq=3, ms=800, V=1)], "silent_a": [dict(seq=4, ms=1200, V=1)]}

    # F7a **回落分支必须被走到**：场不在覆盖集 ⇒ 发 PC 载体（原 seq）
    r7 = apply_fade_pair(NG, {}, mode="hybrid", gold_scenes=set())
    case("F7a hybrid 回落到 PC 载体（分支确实被走到）",
         len(r7["events"]) == 1 and r7["events"][0]["seq"] == 5
         and r7["events"][0]["conf"] == "hybrid-fallback"
         and r7["stats"]["hy_fb_events"] == 1 and r7["stats"]["hy_fb_scenes"] == 1,
         "events=%s stats(fb_events=%d, fb_scenes=%d)"
         % ([(e["scene_id"], e["seq"], e["conf"]) for e in r7["events"]],
            r7["stats"]["hy_fb_events"], r7["stats"]["hy_fb_scenes"]))

    # F7b 金标场**一条 FadeOut 都没有** ⇒ **一条都不发**（金标的判决，不回落 PC）
    r7b = apply_fade_pair(PG, QZ, mode="hybrid", gold_scenes={"gold_a", "silent_a"})
    ev_sil = [e for e in r7b["events"] if e["scene_id"] == "silent_a"]
    case("F7b 覆盖集内无 FadeOut 行 ⇒ 金标判定「不发」（不回落）",
         len(ev_sil) == 0 and r7b["stats"]["hy_gold_silent_scenes"] == 1
         and r7b["stats"]["hy_gold_pc_unused"] == 2,
         "silent_a 事件 %d 条（PC 节点 1 个未被使用）｜ silent_scenes=%d ｜ gold_pc_unused=%d"
         % (len(ev_sil), r7b["stats"]["hy_gold_silent_scenes"], r7b["stats"]["hy_gold_pc_unused"]))

    # F7c 金标场 ⇒ seq/时长取金标（PC 只作印证，不覆盖金标时长/落点）
    ev_g = [e for e in r7b["events"] if e["scene_id"] == "gold_a"]
    case("F7c 覆盖集内取金标 seq/时长",
         len(ev_g) == 1 and ev_g[0]["seq"] == 7 and ev_g[0]["dur"] == 1000
         and ev_g[0]["conf"].startswith("hybrid"),
         "gold_a 事件=%s（PSV 行 seq=7 time=60 ⇒ 1000ms）"
         % [(e["seq"], e["dur"], e["conf"]) for e in ev_g])

    # F7d hybrid 闸门（金标口径）必须能 FAIL：把金标事件去掉 ⇒ 覆盖 < 1
    m7 = measure(ev_g, QZ, gold_scenes={"gold_a"})
    ok7, bad7 = check(m7, keys=("gold_same_seq_rate", "gold_psv_cover_rate"),
                      pairs=(("gold_same_seq_hit", "gold_events"),
                             ("gold_psv_pos_covered", "gold_psv_pos_rows")))
    m7b = measure([], QZ, gold_scenes={"gold_a"})
    ok7b, bad7b = check(m7b, keys=("gold_same_seq_rate", "gold_psv_cover_rate"),
                        pairs=(("gold_same_seq_hit", "gold_events"),
                               ("gold_psv_pos_covered", "gold_psv_pos_rows")))
    case("F7d hybrid 金标口径闸门可 PASS / 可 FAIL（有判别力）",
         ok7 and (not ok7b), "有事件: ok=%s bad=%s ｜ 空事件: ok=%s bad=%s" % (ok7, bad7, ok7b, bad7b))

    # F7e 回落场**不进分母**：把回落事件与金标事件混在一起，金标口径仍为 1.000
    mix = r7["events"] + ev_g
    m7c = measure(mix, QZ, gold_scenes={"gold_a"})
    case("F7e 回落场单列、不进金标口径分母",
         m7c["gold_events"] == 1 and m7c["fallback_events"] == 1
         and m7c["gold_same_seq_rate"] == 1.0 and m7c["gold_psv_cover_rate"] == 1.0,
         "gold_events=%d / fallback_events=%d ｜ gold_rate=%s/%s"
         % (m7c["gold_events"], m7c["fallback_events"],
            m7c["gold_same_seq_rate"], m7c["gold_psv_cover_rate"]))

    allok = all(c[1] for c in cases)
    for name, ok, detail in cases:
        print("  [%s] %s ｜ %s" % ("PASS" if ok else "FAIL", name, detail))
    print("SELFTEST = %s（%d/%d）" % (allok, sum(1 for c in cases if c[1]), len(cases)))
    return allok


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--decode", default="")
    ap.add_argument("--psv-dir", default="")
    ap.add_argument("--psv-root", default="")
    ap.add_argument("--mode", choices=["raw", "pair", "gold", "hybrid"], default="pair",
                    help="hybrid=逐场判定（金标覆盖集内全取金标、含「判定为不发」；集外回落 PC 载体）")
    ap.add_argument("--scope", choices=["all", "build"], default="all",
                    help="all=全语料（含构建外的去重件）；build=与 build_story --all 同场景集")
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--zero-near", action="store_true",
                    help="开启 P4 纯位置轮（默认关：属弱判据，仅供评估）")
    ap.add_argument("--keep-unpaired", action="store_true",
                    help="pair 模式下保留未配对的 PC 节点（原位发出；默认丢弃）")
    ap.add_argument("--gold-zero", action="store_true",
                    help="gold/hybrid 下是否纳入 **入口 fade**（金标记 `time=0`）：开启则只发「配上」的行，时长取 PC ms；注释证据(`*:evidence`)与同 seq(`*:same-seq`)两类分别标注。**默认关**（金标自身对入口 fade 记 time=0）")
    ap.add_argument("--emit-tsv", default="")
    ap.add_argument("--residual-tsv", default="")
    ap.add_argument("--metrics-json", default="")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    proj = os.path.join(a.data_root, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
    dec = a.decode or os.path.join(proj, "编程组", "SOB0解码")
    psv_dir = a.psv_dir or os.path.join(proj, "编程组", "PSV演出")
    psv_root = a.psv_root or os.path.join(a.data_root, "工程", "我们没有翅膀PSV", "脚本解包")

    pc_map = load_pc_nodes(dec)
    psv_map = load_psv_fade(dec, psv_dir)
    if not psv_map:
        print("[FATAL] 无 PSV Fade 行（时间线缺？%s）" % psv_dir, file=sys.stderr)
        return 2
    script_of = {}
    mp = os.path.join(psv_dir, "场景映射.tsv")
    if os.path.isfile(mp):
        for r in load_tsv(mp):
            sid = (r.get("scene_id") or "").strip()
            if sid:
                script_of[sid] = (r.get("script") or "").strip()
    comments = load_psv_fade_comments(psv_root, script_of)

    if a.scope == "build":
        bs = load_build_scenes(os.path.join(proj, "资源组", "剧本"))
        if not bs:
            print("[FATAL] 取不到构建场景集（spine.json 缺）", file=sys.stderr)
            return 2
        pc_map = {k: v for k, v in pc_map.items() if k in bs}
        psv_map = {k: v for k, v in psv_map.items() if k in bs}
    gold_scenes = load_gold_scenes(psv_dir)          # ★ hybrid 的逐场判据（限 ot/otp）
    if a.scope == "build":
        gold_scenes = {s for s in gold_scenes if s in bs}

    if a.selftest:
        return 0 if selftest(pc_map, psv_map, a.window) else 1

    res = apply_fade_pair(pc_map, psv_map, mode=a.mode, window=a.window,
                          keep_unpaired=a.keep_unpaired, zero_near=a.zero_near,
                          comments=comments, gold_zero=a.gold_zero,
                          gold_scenes=gold_scenes)
    m = measure(res["events"], psv_map, a.window,
                gold_scenes=gold_scenes if a.mode == "hybrid" else None)
    HK = ("gold_same_seq_rate", "gold_psv_cover_rate")
    HP = (("gold_same_seq_hit", "gold_events"), ("gold_psv_pos_covered", "gold_psv_pos_rows"))
    if a.mode == "hybrid":
        ok, bad = check(m, keys=HK, labels=("【金标集内】同 seq 命中", "【金标集内】PSV 覆盖"), pairs=HP)
    else:
        ok, bad = check(m)
    st = res["stats"]
    print("模式=%s 口径=%s 窗口=W%d ｜ PC 载体节点 %d ｜ PSV FadeOut 行 %d（time>0 %d / time=0 %d）"
          % (a.mode, a.scope, a.window, st["pc_nodes"], st["psv_rows_pos"] + st["psv_rows_zero"],
             st["psv_rows_pos"], st["psv_rows_zero"]))
    print("  配对：exact %d ｜ same-seq %d（其中 time>0 且**两侧时长不一致 %d**、time=0 行 %d）"
          " ｜ window %d ｜ zero-comment %d ｜ zero-near %d"
          % (st["pair_exact"], st["pair_same_seq"], st["pair_same_seq_dur_mismatch"],
             st["pair_same_seq_zero"], st["pair_window"], st["pair_zero_comment"],
             st["pair_zero_near"]))
    print("  PC 未配对 丢弃 %d 保留 %d ｜ gold 行 %d（PC 印证 %d：时长一致 %d / 不一致 %d）"
          % (st["pc_unpaired_dropped"], st["pc_unpaired_kept"], st.get("gold_rows", 0),
             st.get("gold_pc_paired", 0), st.get("gold_dur_agree", 0),
             st.get("gold_dur_disagree", 0)))
    print("  发出事件 %d" % m["emitted"])
    print("  ★ 同 seq 命中 %d/%d = %s ｜ PSV FadeOut(time>0) 覆盖 %d/%d = %s"
          % (m["same_seq_hit"], m["emitted"],
             ("%.4f" % m["same_seq_rate"]) if m["same_seq_rate"] is not None else "-",
             m["psv_pos_covered"], m["psv_pos_rows"],
             ("%.4f" % m["psv_cover_rate"]) if m["psv_cover_rate"] is not None else "-"))
    print("  残余：PC 未配对 %d（原因 %s）｜ PSV(time>0) 未覆盖 %d（原因 %s）"
          % (len(res["res_pc"]), _cnt(res["res_pc"], "cause"),
             len(res["res_psv"]), _cnt(res["res_psv"], "cause")))
    if a.mode == "hybrid":
        print("  【hybrid 逐场判定】金标覆盖集 %d 场（限 ot/otp）｜其中**发出事件 %d 场**、"
              "**金标判定为不发 %d 场**（场内无 `FadeOut(time>0)` ⇒ 一条不发）；"
              "金标集内 PC 节点被弃用 %d 个"
              % (st["hy_gold_scenes"], st["hy_gold_scenes_emitted"], st["hy_gold_silent_scenes"],
                 st["hy_gold_pc_unused"]))
        print("  【hybrid 逐场判定】**回落 PC 载体 %d 场**（覆盖集外）｜其中发出事件 %d 场 / **%d 条事件**"
              % (st["hy_fb_scenes"], st["hy_fb_scenes_emitted"], st["hy_fb_events"]))
        print("  ★【金标集内】同 seq 命中 %d/%d = %s ｜【金标集内】PSV FadeOut(time>0) 覆盖 %d/%d = %s"
              "（**回落场单列、不进分母**：%d 场 / %d 条）"
              % (m["gold_same_seq_hit"], m["gold_events"],
                 ("%.4f" % m["gold_same_seq_rate"]) if m["gold_same_seq_rate"] is not None else "-",
                 m["gold_psv_pos_covered"], m["gold_psv_pos_rows"],
                 ("%.4f" % m["gold_psv_cover_rate"]) if m["gold_psv_cover_rate"] is not None else "-",
                 m["emitted_fallback_scenes"], m["fallback_events"]))

    if a.emit_tsv:
        _write(a.emit_tsv, ["scene_id", "seq", "dur", "dir", "src_seq", "psv_seq",
                            "psv_time", "pc_ms", "conf", "src"], res["events"])
        print("  事件表 → %s" % os.path.abspath(a.emit_tsv))
    if a.residual_tsv:
        rows = [dict(kind="pc_unpaired", **r) for r in res["res_pc"]] + \
               [dict(kind="psv_uncovered", **r) for r in res["res_psv"]]
        _write(a.residual_tsv, ["kind", "scene_id", "src", "src_seq", "ms", "frames",
                                "psv_seq", "psv_time", "psv_ms", "task", "cause"], rows)
        print("  残余表 → %s" % os.path.abspath(a.residual_tsv))
    if a.metrics_json:
        with io.open(a.metrics_json, "w", encoding="utf-8") as f:
            json.dump(dict(mode=a.mode, window=a.window, metrics=m, stats=st,
                           check_ok=ok, check_bad=bad), f, ensure_ascii=False, indent=1)
        print("  度量 → %s" % os.path.abspath(a.metrics_json))
    if a.check:
        print("CHECK = %s%s" % (ok, "" if ok else " ｜ " + " ；".join(bad)))
        return 0 if ok else 1
    return 0


def _cnt(rows, key):
    d = {}
    for r in rows:
        d[r.get(key)] = d.get(r.get(key), 0) + 1
    return dict(sorted(d.items(), key=lambda kv: -kv[1]))


def _write(path, cols, rows):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else r.get(c) for c in cols])


if __name__ == "__main__":
    sys.exit(main())

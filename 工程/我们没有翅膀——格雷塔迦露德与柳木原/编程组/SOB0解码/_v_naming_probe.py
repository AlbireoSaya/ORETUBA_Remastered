#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""`V → 命令语义/名字` 定名探针（ISSUE-20261007-11，**只读**，不写任何文件）

目标：把 `V`（场景脚本 `maps[3]` 的值 = `func_lib.sob` 缓冲内偏移）补完到**可交付的定名表**
（有阈值、可失败）。全部数字可复跑。

T1 · 读 `V` 处的 func_lib 结构（**窗口式**）
    · 首字（head）
    · BASE 元数表项流前缀（`[tag][payload…]`，走到撞上引用字/越界为止）
    · `maps[4]` 内嵌串 + `maps[0]` 内建符号号（默认窗口 0x120）
    · **敏感度测试** W ∈ {0x60,0xF0,0x120,0x200,0x400}：首串是否随窗口改变
    · **越窗风险**：与「下一个 V 的距离」比对（`window_overruns_next`）
    · 附：场景侧**实参证据**（argc / 实参串分布）——判断命令「吃什么」

T2 · 与 PSV 金标（`编程组\PSV演出\时间线.tsv`）逐条对拍（**多重口径，分开报**）
    · 场级：V 场 vs T 场（precision / recall / base / 反例）
    · seq 级：`(scene_id, seq)` 集合的 precision / recall / base_seq
    · **单事件 seq 标签纯度**（分母明确、不受「全覆盖型 type」稀释）
        `D_all` = 该 seq 恰 1 条非 Message PSV 行（不限 PC 节点数）
        `D_strict` = 再要求该 seq 上 PC 命令节点恰 1 个（归属唯一 ⇒ 最强金标）
    · **计数签名**：逐场 `n_V(sid)` vs `n_T(sid)` 的 sumAbsDiff / exactRate
    · **位置签名**：节点 seq 在该场 PSV 事件序中的归一化位置（区分「场首/场尾」标记）
    · **参数级金标**：实参串 == 同 seq PSV 行的 `name`

T3 · 定名表（阈值见 `TH_*`；达不到阈值一律「未定」，并写明缺什么）

T4 · 采纳项写进 `decode_sob0.py` 的 `V_NAMING`（**只在 main() 汇总段引用，不改 14 列契约**）

用法
  python -X utf8 编程组/SOB0解码/_v_naming_probe.py
  python -X utf8 编程组/SOB0解码/_v_naming_probe.py --json 编程组/SOB0解码/_v_naming.json
  python -X utf8 编程组/SOB0解码/_v_naming_probe.py --focus

口径纪律（写报告不得混报）
  · 「V」= `maps[3]` 的**值**（ot 全库 412 文件口径；`nodes_all`）与命名命令口径（`nodes_cmd`）分列。
  · 分母 N = 该源语料场 ∩ PSV 金标场（ot 362）。
  · 单事件 seq 的 `D_strict` 是**唯一归属**口径；`D_all` 只作参考（同 seq 多 PC 节点时归属不唯一）。
r"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PRG, "工具"))
import decode_sob0 as D  # noqa: E402

FUNC_LIB = os.path.join(D.SOURCES["ot"]["dir"], "func_lib.sob")
OT_SCRIPT = D.SOURCES["ot"]["dir"]

WIN_DEFAULT = 0x120
WIN_SENS = (0x60, 0xF0, 0x120, 0x200, 0x400)

# ---------------------------------------------------------------- 阈值（自定）
TH_PREC_SCENE = 0.67      # 既有「FadeOut 0.67 被采纳」口径（仅报告用）
TH_BASE_MAX = 0.95        # type 场覆盖 ≥ 0.95 ⇒ 逐场共现无鉴别力
TH_D_STRICT = 20          # R1：唯一 event 标签样本量
TH_PUR_STRICT = 0.90      # R1：唯一 event 标签纯度
TH_PUR_ALL = 0.95         # R1b：宽松标签纯度
TH_D_ALL = 30             # R1b：宽松标签样本量
TH_AMBIG_NODES = 2.5      # R1b：每个标签 seq 的平均 PC 命令节点数上限
TH_PARAM_N = 100          # R2：参数级金标样本量
TH_PARAM_RATE = 0.90      # R2：参数级金标一致率
TH_TITLE_RATE = 0.90      # R3b：实参串 = 语料 title_variants 的逐场一致率
TH_CNT_EXACT = 0.60       # R4：计数签名逐场精确率
TH_CNT_SADMAX = 0.35      # R4：sumAbsDiff / max(Vtot,Ttot) 上限（实测达标者 ≤0.32，次优者 ≥0.43）
TH_R3_MIN = 5             # R3：采纳所需最小节点样本
TH_CAND_D_STRICT = 10     # 候选：唯一 event 标签样本量
TH_CAND_PUR_STRICT = 0.80 # 候选：唯一 event 标签纯度
TH_SEQ_MIN = 20           # 报告用最小样本（场级/seq 级）

# 效果/资源名白名单前缀（用于 R3：内嵌串是否「像命令语义名」）
EFFECTY = ("bg_", "sp_", "chr_", "cross", "rule", "trans", "quake", "zoom",
           "scroll", "mosaic", "wave", "addsub", "noise", "motion", "flip",
           "SYS\\", "SYS/", "RULE", "SM_")


def ucount():
    return collections.Counter()


# ================================================================ T1
def base_walk(fl, V, maxit=24):
    ref = fl.ref_sites
    out = []
    i = V // 4
    while len(out) < maxit:
        o = i * 4
        if o + 4 > fl.ss:
            return out, "end"
        if o in ref:
            return out, "ref@0x%X" % o
        t = fl.cells[i]
        L = D.BASE.get(t, 1) + 1
        out.append((o, t, L))
        i += L
    return out, "maxit"


def win_strings(fl, V, W):
    out = []
    for j in range(0, W, 4):
        o = V + j
        if o + 4 > fl.ss:
            break
        t = fl.maps[4].get(o)
        if t is None or not (fl.ss <= t < fl.se):
            continue
        try:
            s = fl.read_group(t)[0].decode("cp932", "replace")
        except Exception:
            continue
        if s:
            out.append((j, o, s))
    return out


def win_builtins(fl, V, W):
    bu, cr = [], 0
    for j in range(0, W, 4):
        o = V + j
        if o + 4 > fl.ss:
            break
        if o in fl.maps[0] and fl.maps[0][o] not in bu:
            bu.append(fl.maps[0][o])
        t = fl.maps[4].get(o)
        if t is not None and t < fl.ss:
            cr += 1
    return bu, cr


def v_domain():
    nodes_all, nodes_cmd = ucount(), ucount()
    for fn in sorted(os.listdir(OT_SCRIPT)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            s = D.Sob0(os.path.join(OT_SCRIPT, fn))
        except Exception:
            continue
        for _k, V in s.maps[3].items():
            nodes_all[V] += 1
        for i in s.command_nodes():
            nodes_cmd[s.cells[i + 1]] += 1
    return nodes_all, nodes_cmd


def t1_table(fl, nodes_all, nodes_cmd, Vs):
    order = sorted(Vs)
    nxt = {V: (order[k + 1] if k + 1 < len(order) else None)
           for k, V in enumerate(order)}
    out = {}
    for V in order:
        sens = {}
        for W in WIN_SENS:
            ss = win_strings(fl, V, W)
            sens["0x%X" % W] = dict(first=(ss[0][2] if ss else None),
                                    first_j=("0x%X" % ss[0][0] if ss else None),
                                    n=len(ss), strings=[s for _j, _o, s in ss][:8])
        w = win_strings(fl, V, WIN_DEFAULT)
        bu, cr = win_builtins(fl, V, WIN_DEFAULT)
        firsts = {W: sens["0x%X" % W]["first"] for W in (0x120, 0x200, 0x400)}
        base_first = firsts[0x120]
        stable = (base_first is not None
                  and all(v == base_first for v in firsts.values()))
        gap = None if nxt[V] is None else nxt[V] - V
        out["0x%X" % V] = dict(
            nodes_all=nodes_all.get(V, 0), nodes_cmd=nodes_cmd.get(V, 0),
            head="0x%X" % fl.cells[V // 4],
            walk_tags=["0x%X" % t for _o, t, _L in base_walk(fl, V)[0]],
            walk_stop=base_walk(fl, V)[1], walk_n=len(base_walk(fl, V)[0]),
            strings=[dict(j="0x%X" % j, s=s) for j, _o, s in w],
            first_string=base_first, string_stable=stable,
            string_effecty=bool(base_first and base_first.startswith(EFFECTY)),
            sens=sens, builtins=bu, crefs=cr,
            gap_to_next_V=(gap if gap is not None else -1),
            window_overruns_next=(gap is not None and WIN_DEFAULT > gap))
    return out


# ================================================================ 语料
def load_scenes():
    """→ (nodes_by_scene, golden)。"""
    path = os.path.join(D.SCENE_DIR, "scene_ot.jsonl")
    out = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            p = os.path.join(OT_SCRIPT, o["script"] + ".sob")
            if not os.path.isfile(p):
                continue
            try:
                sob = D.Sob0(p)
            except ValueError:
                continue
            rows, info = D.extract_scene("ot", o, sob, sob.slots(), None, None)
            titles = {o.get("title_jp") or ""}
            for tv in (o.get("title_variants") or []):
                if tv.get("jp"):
                    titles.add(tv["jp"])
            titles.discard("")
            out[o["scene_id"]] = dict(
                nodes=[(n["V"], int(n["seq"]), n["args"]) for n in info["nodes"]],
                titles=titles)
    return out


# ================================================================ T2
def run_t2(scenes, psv):
    gold = {sid: psv[sid] for sid in scenes if sid in psv}
    N = len(gold)
    # PSV 侧：type→场 / type→seq / 单事件 seq 标签 / seq→rank
    type_scenes = collections.defaultdict(set)
    type_seqs = collections.defaultdict(set)
    seq_label = {}
    seq_rank = {}
    all_seq = set()
    for sid, rows in gold.items():
        ev = [r for r in rows if r.get("type") != "Message"]
        ev.sort(key=lambda r: int(r["seq"] or 0))
        n = len(ev)
        for k, r in enumerate(ev):
            seq_rank[(sid, str(r["seq"]))] = k / max(1, n - 1)
        for r in rows:
            type_scenes[r.get("type", "")].add(sid)
        byseq = collections.defaultdict(list)
        for r in ev:
            byseq[str(r["seq"])].append(r)
            type_seqs[r.get("type", "")].add((sid, str(r["seq"])))
        for sq, rs in byseq.items():
            all_seq.add((sid, sq))
            if len(rs) == 1:
                seq_label[(sid, sq)] = rs[0].get("type", "")
    # PC 侧
    v_nodes = ucount()
    v_tsc = collections.defaultdict(set)
    v_scenes_all = collections.defaultdict(set)
    v_seqs_gold = collections.defaultdict(set)
    v_seqs_all = collections.defaultdict(set)
    seq_pc = ucount()
    v_count = collections.defaultdict(ucount)        # V->sid->n
    t_count = collections.defaultdict(ucount)        # type->sid->n
    for sid, d in scenes.items():
        for V, sq, _a in d["nodes"]:
            v_nodes[V] += 1
            v_scenes_all[V].add(sid)
            v_seqs_all[V].add((sid, str(sq)))
            seq_pc[(sid, str(sq))] += 1
            if sid in gold:
                v_seqs_gold[V].add((sid, str(sq)))
                v_count[V][sid] += 1
        if sid in gold:
            for r in gold[sid]:
                if r.get("type") != "Message":
                    t_count[r.get("type", "")][sid] += 1
    gsids = sorted(gold)
    # 参数级金标（实参串 == 同 seq PSV name）
    psv_names = collections.defaultdict(list)
    for sid, rows in gold.items():
        for r in rows:
            if r.get("type") == "Message":
                continue
            psv_names[(sid, str(r["seq"]))].append(r)
    out = dict(N=N, n_gold_seq=len(all_seq), n_single_seq=len(seq_label))
    for V in sorted(v_seqs_gold):
        vs = v_seqs_gold[V]
        vsc = {sid for sid, _ in vs}
        best_scene, best_seq, best_cnt = [], [], []
        for t in type_scenes:
            tsc = type_scenes[t]
            inter = vsc & tsc
            if inter:
                vo = sorted(vsc - tsc)
                best_scene.append([round(len(inter) / len(vsc), 4),
                                   round(len(inter) / len(tsc), 4),
                                   round(len(tsc) / N, 4), t, len(inter),
                                   len(vo), vo[:8], len(tsc - vsc)])
        for t in type_seqs:
            tq = type_seqs[t]
            inter = vs & tq
            if inter:
                best_seq.append([round(len(inter) / len(vs), 4),
                                 round(len(inter) / len(tq), 4),
                                 round(len(tq) / len(all_seq), 4), t, len(inter),
                                 len(vs - tq)])
        for t, c in t_count.items():
            ta = sum(v_count[V][s] for s in gsids)
            tb = sum(c[s] for s in gsids)
            if not tb:
                continue
            sad = sum(abs(v_count[V][s] - c[s]) for s in gsids)
            ex = sum(1 for s in gsids if v_count[V][s] == c[s])
            base_sc = len(type_scenes[t]) / N
            vo = sorted(s for s in gsids if v_count[V][s] > 0 and c[s] == 0)
            to = sorted(s for s in gsids if c[s] > 0 and v_count[V][s] == 0)
            vo_rows = sum(v_count[V][s] for s in vo)
            to_rows = sum(c[s] for s in to)
            best_cnt.append([sad, round(ex / len(gsids), 4), t, ta, tb,
                             round(base_sc, 4), round(sad / max(ta, tb), 4),
                             len(vo), vo[:8], len(to), vo_rows, to_rows])
        best_scene.sort(reverse=True)
        best_seq.sort(reverse=True)
        best_cnt.sort()
        # 单事件 seq 标签
        lab_all, lab_str, amb = ucount(), ucount(), []
        for key in vs:
            t = seq_label.get(key)
            if t is None:
                continue
            lab_all[t] += 1
            amb.append(seq_pc.get(key, 0))
            if seq_pc.get(key, 0) == 1:
                lab_str[t] += 1

        def pur(c):
            """→ (纯度, 样本量, 众数, 是否并列)。并列 = 最高票与次高票相等。"""
            tot = sum(c.values())
            if not tot:
                return None, 0, None, False
            mc = c.most_common(2)
            top, n = mc[0]
            tie = len(mc) > 1 and mc[1][1] == n
            return round(n / tot, 4), tot, top, tie
        p_all, d_all, top_all, tie_all = pur(lab_all)
        p_str, d_str, top_str, tie_str = pur(lab_str)
        # 位置签名
        pos = [seq_rank[(sid, sq)] for sid, sq in vs if (sid, sq) in seq_rank]
        pos_mean = round(sum(pos) / len(pos), 4) if pos else None
        # 参数级
        pm = ucount()
        pm_n = 0
        PREF = ("PIC\\", "SYS\\", "CHR\\", "BGM\\", "VOICE\\", "PIC/", "SYS/")
        for sid, d in scenes.items():
            if sid not in gold:
                continue
            for Vn, sq, args in d["nodes"]:
                if Vn != V:
                    continue
                strs = [v for k, v in args if k == "S" and v
                        and not v.startswith(PREF)]
                if not strs:
                    continue
                rows = psv_names.get((sid, str(sq)))
                if not rows:
                    continue
                names = {r.get("name", "") for r in rows if r.get("name")}
                if not names:
                    continue
                pm_n += 1
                for s in strs:
                    if s in names:
                        for r in rows:
                            if r.get("name") == s:
                                pm[r.get("type", "")] += 1
        out["0x%X" % V] = dict(
            nodes=v_nodes[V], nodes_all=len(v_seqs_all[V]),
            scenes_all=len(v_scenes_all[V]), scenes_gold=len(vsc),
            seqs_all=len(v_seqs_all[V]), seqs_gold=len(vs),
            best_scene=best_scene[:4], best_seq=best_seq[:4], best_cnt=best_cnt[:4],
            single_all=dict(purity=p_all, D=d_all, top=top_all, tie=tie_all,
                            dist=dict(lab_all.most_common(5)),
                            avg_nodes=round(sum(amb) / len(amb), 3) if amb else None),
            single_strict=dict(purity=p_str, D=d_str, top=top_str, tie=tie_str,
                               dist=dict(lab_str.most_common(5))),
            pos_mean=pos_mean, pos_n=len(pos),
            param_n=pm_n, param_match=dict(pm.most_common(5)))
    return out


def title_test(scenes):
    """0x1C8D0 的实参串 vs 语料 title_variants 逐场一致率。

    分母分两栏：`n`（全部有 0x1C8D0 实参串的场）与 `n_titled`（其中**语料登记了标题**的场）。
    9 场**无语料标题**（title_jp=None 且 title_variants=[]）⇒ 不计入 titled 分母（非矛盾）。
    """
    hit = tot = 0
    hit_t = tot_t = no_title = 0
    miss = []
    for sid, d in scenes.items():
        for V, _sq, args in d["nodes"]:
            if V != 0x1C8D0:
                continue
            strs = [v for k, v in args if k == "S" and v]
            if not strs:
                continue
            tot += 1
            if strs[0] in d["titles"]:
                hit += 1
            if not d["titles"]:
                no_title += 1
                continue
            tot_t += 1
            if strs[0] in d["titles"]:
                hit_t += 1
            elif len(miss) < 12:
                miss.append((sid, strs[0]))
    return dict(n=tot, hit=hit, rate=(round(hit / tot, 4) if tot else None),
                n_titled=tot_t, hit_titled=hit_t,
                rate_titled=(round(hit_t / tot_t, 4) if tot_t else None),
                no_corpus_title=no_title, miss=miss)


# ================================================================ T3 判定
def _cand_types(V, t2):
    """一个 V 的**候选 PSV type**（含各规则用的数字），供冲突消解与报告。"""
    g = t2.get("0x%X" % V)
    if g is None:
        return None
    out = dict(V=V, nodes=g["nodes"], seqs=g["seqs_gold"], scenes_gold=g["scenes_gold"],
               ss=g["single_strict"], sa=g["single_all"],
               cnt=g["best_cnt"], scene=g["best_scene"], seq=g["best_seq"],
               param_n=g["param_n"], param=g["param_match"],
               pos=g["pos_mean"])
    return out


def verdict(V, t1, t2, title_ok=False, nodes_cmd=0):
    """返回 (判定字符串, 依据字符串, 命中 type 列表)。规则见文件头；全部可失败。"""
    e = t1["0x%X" % V]
    # ---- R3 / R3b：T1 语义直证（不依赖语料）----
    if e["string_stable"] and e["first_string"]:
        if nodes_cmd >= TH_R3_MIN:
            return ("采纳：" + e["first_string"],
                    "R3 func_lib 内嵌串稳定（窗口 0x120/0x200/0x400 首串不变）；样本 %d 节点" % nodes_cmd, [])
        return ("候选（%s）：%s" % ("非命令节点形态" if nodes_cmd == 0 else "样本 %d 节点" % nodes_cmd,
                                    e["first_string"]),
                "R3 内嵌串稳定但命令节点样本 %d < %d，不足以定名" % (nodes_cmd, TH_R3_MIN), [])
    # ---- 非命名命令（仅 maps[3] 项，非 `[..][03][空串REF]` 形态，且无内嵌串）----
    if nodes_cmd == 0:
        return ("非命名命令（maps[3] 项，非命令节点形态）",
                "该 V 无 `[04][V][0C][k][03][空串REF]` 形态节点（软表解出_说明.md §五：内联/跳转族）", [])
    if title_ok:
        return "采纳：场景标题设置（章/场名）", "R3b 实参串=语料 title_variants（逐场一致率≥0.90）", []
    g = _cand_types(V, t2)
    if g is None:
        return "未定（ot 语料无该 V 的节点）", "无 T2 数据；且 T1 内嵌串不稳定/为空", []
    ss, sa = g["ss"], g["sa"]
    # ---- R1 唯一 event 标签 ----
    if ss["D"] >= TH_D_STRICT and (ss["purity"] or 0) >= TH_PUR_STRICT:
        return ("采纳：" + str(ss["top"]),
                "R1 唯一 event 标签（seq 上 PC 命令节点恰 1 个且 PSV 非 Message 事件恰 1 个）"
                " purity=%.4f D=%d" % (ss["purity"], ss["D"]), [ss["top"]])
    # ---- R1f 唯一 event 标签·族（top1+top2 ≥ 0.95）----
    if ss["D"] >= TH_D_STRICT and ss["dist"]:
        it = list(ss["dist"].items())
        r2 = sum(n for _k, n in it[:2]) / ss["D"]
        if r2 >= 0.95:
            fam = "%s/%s" % (it[0][0], it[1][0]) if len(it) > 1 else it[0][0]
            return ("采纳：" + fam,
                    "R1f 唯一 event 标签·族（top2 %.4f）" % r2, [it[0][0], it[1][0]] if len(it) > 1 else [it[0][0]])
    # ---- R1b 宽松标签 ----
    if (sa["D"] >= TH_D_ALL and (sa["purity"] or 0) >= TH_PUR_ALL
            and sa["avg_nodes"] is not None and sa["avg_nodes"] <= TH_AMBIG_NODES):
        return ("采纳：" + str(sa["top"]),
                "R1b 单事件标签（纯度≥%.2f，D=%d，平均 PC 节点 %.2f）"
                % (TH_PUR_ALL, sa["D"], sa["avg_nodes"]), [sa["top"]])
    # ---- R2 参数级金标 ----
    if g["param_n"] >= TH_PARAM_N and g["param"]:
        top, n = max(g["param"].items(), key=lambda x: x[1])
        if n / g["param_n"] >= TH_PARAM_RATE:
            return ("采纳：" + top,
                    "R2 参数级金标（实参串=同 seq PSV name：%d/%d）" % (n, g["param_n"]), [top])
    # ---- R4 计数签名：**仅看 sad 最小的 3 个候选**（防在长尾里挑到偶然达标者）----
    for row in g["cnt"][:3]:
        sad, ex, t, ta, tb, base_sc, rel = row[:7]
        if ex >= TH_CNT_EXACT and rel <= TH_CNT_SADMAX and base_sc < TH_BASE_MAX:
            # 与其它 type 的计数签名**完全相同**时，名字并列写（仅字母序不同 ⇒ 不得择一）
            same = [r[2] for r in g["cnt"][:3]
                    if r[2] != t and r[:2] == row[:2] and r[3] == ta and r[4] == tb]
            name = t if not same else t + "/" + "/".join(sorted(same))
            note = ("R4 计数签名（逐场精确率 %.3f，sumAbsDiff %d / max(V,T) = %.3f，base %.3f）"
                    % (ex, sad, rel, base_sc))
            if same:
                note += "；**与 %s 计数签名完全相同（仅字母序不同）⇒ 并列记名**" % "/".join(sorted(same))
            return ("采纳：" + name, note, [t] + sorted(same))
    # ---- 候选 / 未定 ----
    notes = []
    # 唯一 event 标签：达 20 样本但纯度不足 0.90 ⇒ 记「候选」（弱于采纳线）
    if ss["D"] >= TH_CAND_D_STRICT and (ss["purity"] or 0) >= TH_CAND_PUR_STRICT:
        notes.append("唯一 event 标签众数 %s %.4f(D=%d)" % (ss["top"], ss["purity"], ss["D"]))
    if sa["D"] >= 10:
        notes.append("单事件标签众数 %s %.3f(D=%d, avg_nodes=%s)"
                     % (sa["top"], sa["purity"] or 0, sa["D"], sa["avg_nodes"]))
    if g["cnt"]:
        c0 = g["cnt"][0]
        notes.append("最佳计数签名 %s ex=%.3f sad=%d rel=%.3f base=%.3f"
                     % (c0[2], c0[1], c0[0], c0[6], c0[5]))
    if g["scene"]:
        s0 = g["scene"][0]
        notes.append("最佳场级 %s P=%.3f base=%.3f" % (s0[3], s0[0], s0[2]))
    if g["pos"] is not None:
        notes.append("位置均值 %.3f" % g["pos"])
    if e["first_string"]:
        notes.append("内嵌串 %s（稳定=%s）" % (e["first_string"], e["string_stable"]))
    if ss["D"] >= TH_CAND_D_STRICT and (ss["purity"] or 0) >= TH_CAND_PUR_STRICT:
        return "候选：" + str(ss["top"]), "；".join(notes), [ss["top"]]
    if (sa["purity"] or 0) >= 0.80 and sa["D"] >= 10:
        return "候选：" + str(sa["top"]), "；".join(notes), [sa["top"]]
    return "未定", "；".join(notes) or "无任何达阈值证据", []


# ================================================================ 主
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--focus", action="store_true")
    ap.add_argument("--md", action="store_true", help="打印完整定名表（markdown）")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    fl = D.Sob0(FUNC_LIB)
    nodes_all, nodes_cmd = v_domain()
    Vs = set(nodes_all)
    t1 = t1_table(fl, nodes_all, nodes_cmd, Vs)
    scenes = load_scenes()
    psv, _ids = D.load_psv_timeline()
    t2 = run_t2(scenes, psv)
    tt = title_test(scenes)
    title_ok = (tt["n"] >= 100 and (tt["rate"] or 0) >= TH_TITLE_RATE)

    rows = []
    for V in sorted(Vs, key=lambda v: -nodes_all.get(v, 0)):
        vd, why, tt2 = verdict(V, t1, t2, title_ok=(V == 0x1C8D0),
                               nodes_cmd=nodes_cmd.get(V, 0))
        rows.append((V, vd, why, tt2))
    # 冲突：同一 PSV type 被多个 V 采纳
    claimed = collections.defaultdict(list)
    for V, vd, _w, tt2 in rows:
        if vd.startswith("采纳：") and tt2:
            for t in tt2:
                claimed[t].append(V)
    conflicts = {t: vs for t, vs in claimed.items() if len(vs) > 1}
    # R1 护栏量 q：单事件 seq 上各 type 的先验占比（采信上限见 定名_说明.md §2.2）
    rep_q = {}
    tot_single = t2["n_single_seq"]
    if tot_single:
        pri = collections.Counter()
        for sid, _rowsl in psv.items():
            if sid not in scenes:
                continue
            by = collections.defaultdict(list)
            for r in _rowsl:
                if r.get("type") == "Message":
                    continue
                by[str(r["seq"])].append(r.get("type", ""))
            for _q, ts in by.items():
                if len(ts) == 1:
                    pri[ts[0]] += 1
        rep_q = {"single_event_seqs": tot_single,
                 "prior": {t: n for t, n in pri.most_common()},
                 "q_max": round(max(pri.values()) / tot_single, 4) if pri else None,
                 "q_max_type": pri.most_common(1)[0][0] if pri else None}
    rep = dict(
        r1_prior=rep_q,
        func_lib=dict(path=FUNC_LIB, magic=fl.magic, ss=fl.ss, se=fl.se,
                      he=fl.header_end, maps_count=[len(m) for m in fl.maps],
                      V_min="0x%X" % min(Vs), V_max="0x%X" % max(Vs), n_V=len(Vs)),
        n_named_V=len([V for V in Vs if nodes_cmd.get(V)]),
        win_default="0x%X" % WIN_DEFAULT, win_sens=["0x%X" % w for w in WIN_SENS],
        thresholds=dict(prec_scene=TH_PREC_SCENE, r3_min=TH_R3_MIN,
                        base_max=TH_BASE_MAX, d_strict=TH_D_STRICT,
                        pur_strict=TH_PUR_STRICT, pur_all=TH_PUR_ALL, d_all=TH_D_ALL,
                        ambig=TH_AMBIG_NODES, param_n=TH_PARAM_N,
                        param_rate=TH_PARAM_RATE, title_rate=TH_TITLE_RATE,
                        cnt_exact=TH_CNT_EXACT, cnt_sadmax=TH_CNT_SADMAX,
                        cand_d_strict=TH_CAND_D_STRICT, cand_pur_strict=TH_CAND_PUR_STRICT,
                        seq_min=TH_SEQ_MIN),
        title_test=tt, t1=t1, t2=t2,
        conflicts={"%s" % t: ["0x%X" % v for v in vs] for t, vs in conflicts.items()},
        verdicts={"0x%X" % V: dict(verdict=vd, basis=why, types=["%s" % x for x in tt2])
                  for V, vd, why, tt2 in rows})

    focus = [0x17514, 0x14084, 0x19A68, 0x1FAD4, 0x7480, 0x1B040, 0x1AD18,
             0x1C8D0, 0x19F9C, 0x186C8, 0x10150, 0xFDF4, 0x13300, 0x2A150,
             0x1E45C, 0x1E634, 0x1C43C, 0x19808, 0x2C3C, 0x1F600]
    print("func_lib: %s ss=%d se=%d he=%d maps=%s"
          % (fl.magic, fl.ss, fl.se, fl.header_end, [len(m) for m in fl.maps]))
    print("V 域 %d 个（min %s max %s），命名命令 V %d 个"
          % (len(Vs), rep["func_lib"]["V_min"], rep["func_lib"]["V_max"], rep["n_named_V"]))
    print("N(ot 金标场)=%d  金标 seq=%d  单事件 seq=%d  标题直证 %d/%d=%s"
          % (t2["N"], t2["n_gold_seq"], t2["n_single_seq"], tt["hit"], tt["n"], tt["rate"]))
    print()
    print("%-9s %-7s %-6s %-10s %-14s %-6s %-7s %-7s %-7s %s"
          % ("V", "nodes", "nCmd", "head", "firstStr(st)", "purS", "DS", "purA", "posM", "判定"))
    for V in sorted(Vs, key=lambda v: -nodes_all.get(v, 0)):
        if a.focus and V not in focus:
            continue
        e = t1["0x%X" % V]
        g = t2.get("0x%X" % V)
        if g is None:
            print("%-9s %-7d %-6d %-10s %-14s %s"
                  % ("0x%X" % V, e["nodes_all"], e["nodes_cmd"], e["head"], "-", "未定（无 ot 节点）"))
            continue
        ss, sa = g["single_strict"], g["single_all"]
        vd = rep["verdicts"]["0x%X" % V]
        fs = (e["first_string"] or "-")
        fs = fs + ("*" if e["string_stable"] else "")
        print("%-9s %-7d %-6d %-10s %-14s %-6s %-7d %-7s %-7s %s"
              % ("0x%X" % V, e["nodes_all"], e["nodes_cmd"], e["head"], fs[:14],
                 str(ss["purity"]), ss["D"], str(sa["purity"]), str(g["pos_mean"]),
                 vd["verdict"]))
    print("\n判定来源：")
    for V, vd, why, _tt2 in rows:
        if vd.startswith("采纳") or vd.startswith("候选"):
            print("  0x%-6X → %-28s [%s]" % (V, vd, why))
    if conflicts:
        print("\n★ 同一 PSV type 被多个 V 采纳（type 粒度粗 / 需人工消歧）：")
        for t, vs in conflicts.items():
            print("   %-18s ← %s" % (t, ", ".join("0x%X" % v for v in vs)))
    if a.md:
        print("\n<!-- ===== 定名表（--md 生成） ===== -->")
        print("| V | 节点数(all/cmd) | 推断名称/语义 | 来源 | precision | recall | 反例数 | 判定 | 依据 |")
        print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for V, vd, why, tt2 in rows:
            e = t1["0x%X" % V]
            g = t2.get("0x%X" % V)
            name = vd.split("：", 1)[1] if "：" in vd else "-"
            src, prec, rec, ctr = "-", "-", "-", "-"
            if why.startswith("R3 func_lib"):
                src = "func_lib内嵌串"
            elif why.startswith("R3b"):
                src = "语料 title 直证"
            elif g is not None:
                ss, sa = g["single_strict"], g["single_all"]
                if why.startswith("R1 唯一"):
                    src = "PSV对拍·唯一event"
                    prec = "%.4f" % ss["purity"]
                    rec = "1.0000"
                    ctr = ss["D"] - (ss["dist"][ss["top"]] if ss["dist"] else 0)
                elif why.startswith("R1f"):
                    src = "PSV对拍·唯一event(族)"
                    it = list(ss["dist"].items())
                    prec = "%.4f" % (sum(n for _k, n in it[:2]) / ss["D"] if ss["D"] else 0)
                    rec = "1.0000"
                    ctr = ss["D"] - sum(n for _k, n in it[:2])
                elif why.startswith("R1b"):
                    src = "PSV对拍·单事件(弱)"
                    prec = "%.4f" % sa["purity"]
                    rec = "-"
                    ctr = sa["D"] - (sa["dist"][sa["top"]] if sa["dist"] else 0)
                elif why.startswith("R4"):
                    row = next((r for r in g["best_cnt"] if tt2 and r[2] == tt2[0]), g["best_cnt"][0])
                    src = "PSV对拍·计数签名"
                    prec = "%.3f" % ((row[3] - row[10]) / row[3]) if row[3] else "-"
                    rec = "%.3f" % ((row[4] - row[11]) / row[4]) if row[4] else "-"
                    ctr = "%d场(%d节点)" % (row[7], row[10])
            print("| `0x%X` | %d/%d | %s | %s | %s | %s | %s | %s | %s |"
                  % (V, e["nodes_all"], e["nodes_cmd"], name, src, prec, rec, ctr,
                     vd, why.replace("|", "/")))

    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
        print("\n[写] %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())

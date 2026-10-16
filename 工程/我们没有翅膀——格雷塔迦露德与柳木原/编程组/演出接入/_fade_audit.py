#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
`_fade_audit.py` —— Fade 事件源（Lucifen 载体）对 PSV 金标的**只读**对拍（ISSUE-20261007-11 T2）
================================================================================
只读：除 `--json <path>` 显式指定的机读结果外，不写任何文件。

对拍口径（**分开报，不混用**；与 `SOB0解码\落地_说明.md` §T2 同口径，便于逐数字复核）：
  · **载体场（全语料）** ＝ 该源出现过 Fade 载体 V 的场（不分是否有 PSV 金标）。
  · **载体场（金标）**   ＝ 上者 ∩ PSV 金标场。
  · **T 场** ＝ PSV 该 `type` 出现的场（金标场口径）。
  · **precision（全语料口径）** ＝ |载体场 ∩ T场| / |载体场|  ← 与落地文档的 0.950 同式
  · **precision（金标口径）**   ＝ |载体场 ∩ T场| / |载体场 ∩ 金标场|
  · **recall** ＝ |载体场 ∩ T场| / |T场|
  · **反例** ＝ 载体场 \ T场（逐场列出）；**notime>0 口径**另给（落地文档的「16 场」即此口径）。
  · **帧吻合**：`round(time_ms × 0.06)` ∈ 同 seq PSV 该 type 的 `time` 集合的比率。
  · **方向判据**：同一批载体节点分别对 `FadeOut.time` / `FadeIn.time` 算帧吻合，**高者为真实 dir**
    （本批 ot：FadeOut 0.718 / FadeIn 0.000 ⇒ `dir="out"`；FadeIn 在金标里恒 `time=0`，是瞬时复位）。

用法：
  python -X utf8 编程组/演出接入/_fade_audit.py --data-root "E:/ZCode Workspace/Galgame" \
      --decode "<checkout>/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/SOB0解码" \
      --json "<checkout>/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出接入/_fade_audit.json"
"""
import argparse, csv, io, json, os, sys


def load_tsv(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _dist(vals):
    d = {}
    for v in vals:
        d[str(v)] = d.get(str(v), 0) + 1
    return dict(sorted(d.items(), key=lambda kv: -kv[1]))


def audit_src(src, decode_dir, tl_rows_all):
    # 1) 命令族标签表（**只认 verdict=采纳 且 carrier 非空**）→ 载体 V
    lab_p = os.path.normpath(os.path.join(decode_dir, "..", "..", "资源组", "演出",
                                          "Lucifen命令族标签.tsv"))
    carriers = {}
    if os.path.isfile(lab_p):
        for r in load_tsv(lab_p):
            if (r.get("verdict") or "").strip() != "采纳":
                continue
            if (r.get("src") or "").strip() != src:
                continue
            if not (r.get("carrier") or "").strip():
                continue
            carriers[int((r.get("V") or "0x0"), 16)] = (r.get("carrier") or "").strip()
    # 2) 载体节点（解码产物）
    dec_p = os.path.join(decode_dir, "解出_%s.tsv" % src)
    nodes = []
    if os.path.isfile(dec_p):
        for r in load_tsv(dec_p):
            a3 = (r.get("arg3") or "").strip()
            if not a3.startswith("V=0x"):
                continue
            V = int(a3[2:], 16)
            if V not in carriers:
                continue
            nodes.append(dict(scene_id=(r.get("scene_id") or "").strip(),
                              seq=(r.get("seq") or "0").strip() or "0",   # ★ 统一按字符串键
                              ms=int((r.get("time_ms") or "").strip() or "0"),
                              V=V, conf=(r.get("confidence") or "").strip()))
    # 3) PSV 侧（scene_id / seq 统一按字符串键）
    tl = [r for r in tl_rows_all if (r.get("scene_id") or "").startswith(src + "_")]
    gold_scenes = set(r["scene_id"] for r in tl)
    ttype_scenes, ttype_seq_time = {}, {}          # type -> {scenes}, (sid,seq) -> {type:set(time)}
    for r in tl:
        t = (r.get("type") or "").strip()
        k = (r["scene_id"], (r.get("seq") or "").strip())
        tv = int((r.get("time") or "0").strip() or "0")
        ttype_scenes.setdefault(t, set()).add(r["scene_id"])
        ttype_seq_time.setdefault(k, {}).setdefault(t, set()).add(tv)
    pc_scenes = set(n["scene_id"] for n in nodes)
    pc_seq = {}
    for n in nodes:
        pc_seq.setdefault((n["scene_id"], n["seq"]), 0)
        pc_seq[(n["scene_id"], n["seq"])] += 1

    def metric(tname, require_time_pos=False):
        if require_time_pos:
            S = set(sid for (sid, sq), tt in ttype_seq_time.items()
                    if any(v > 0 for v in tt.get(tname, set())))
        else:
            S = ttype_scenes.get(tname) or set()
        Tgold = S & gold_scenes
        hit_all = pc_scenes & S
        return dict(
            type=tname, time_pos=require_time_pos,
            t_scenes=len(Tgold),
            hit=len(hit_all),
            precision_all=(len(hit_all) / float(len(pc_scenes))) if pc_scenes else None,
            precision_gold=(len(pc_scenes & gold_scenes & S) / float(len(pc_scenes & gold_scenes)))
                           if (pc_scenes & gold_scenes) else None,
            recall=(len(hit_all) / float(len(Tgold))) if Tgold else None,
            gold_base=(len(Tgold) / float(len(gold_scenes))) if gold_scenes else None,
            counterexamples=sorted(pc_scenes - S),
        )

    def frame_agree(tname):
        ok = tot = 0
        for n in nodes:
            ts = (ttype_seq_time.get((n["scene_id"], n["seq"])) or {}).get(tname)
            if not ts:
                continue
            tot += 1
            if round(n["ms"] * 0.06) in ts:
                ok += 1
        return dict(type=tname, matched=ok, total=tot,
                    rate=(ok / float(tot)) if tot else None)

    return dict(
        src=src, carriers={"0x%X" % V: nm for V, nm in carriers.items()},
        label_table=lab_p,
        nodes=len(nodes), scenes_pc=len(pc_scenes), scenes_pc_in_gold=len(pc_scenes & gold_scenes),
        gold_scenes=len(gold_scenes),
        node_seq_with_psv_row=sum(1 for n in nodes
                                  if ttype_seq_time.get((n["scene_id"], n["seq"]))),
        ms_dist=_dist([n["ms"] for n in nodes]), conf_dist=_dist([n["conf"] for n in nodes]),
        per_scene_node_dist=_dist([sum(1 for m in nodes if m["scene_id"] == s) for s in pc_scenes]),
        metrics=[metric("FadeOut"), metric("FadeIn"), metric("FadeOut", True), metric("FadeIn", True)],
        frame_agree=[frame_agree("FadeOut"), frame_agree("FadeIn")],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--decode", default="",
                    help="解出_*.tsv 所在目录（默认 <data-root>\\工程\\我们没有翅膀——格雷塔迦露德与柳木原\\编程组\\SOB0解码）")
    ap.add_argument("--json", default="", help="机读结果落盘（只写此文件）")
    a = ap.parse_args()
    proj = os.path.join(a.data_root, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
    dec = a.decode or os.path.join(proj, "编程组", "SOB0解码")
    tl_p = os.path.join(proj, "编程组", "PSV演出", "时间线.tsv")
    tl = load_tsv(tl_p)
    print("时间线 = %s（%d 行）" % (tl_p, len(tl)))
    out = {}
    for src in ("ot", "otp"):
        d = audit_src(src, dec, tl)
        out[src] = d
        print("\n=== [%s] Fade 载体 %s ===" % (src, d["carriers"]))
        print("  载体节点 %d ｜ 载体场 %d（其中金标场 %d）｜ 金标场总数 %d ｜ 节点 seq 有 PSV 行 %d/%d"
              % (d["nodes"], d["scenes_pc"], d["scenes_pc_in_gold"], d["gold_scenes"],
                 d["node_seq_with_psv_row"], d["nodes"]))
        print("  每场节点数：%s" % d["per_scene_node_dist"])
        print("  ms 分布：%s" % d["ms_dist"])
        print("  置信度：%s" % d["conf_dist"])
        for m in d["metrics"]:
            print("  [场级 %-8s time>0=%-5s] T场 %d 命中 %d ｜ precision(全语料) %s ｜ precision(金标) %s"
                  " ｜ recall %s ｜ base %s ｜ 反例 %d 场"
                  % (m["type"], m["time_pos"], m["t_scenes"], m["hit"],
                     ("%.3f" % m["precision_all"]) if m["precision_all"] is not None else "-",
                     ("%.3f" % m["precision_gold"]) if m["precision_gold"] is not None else "-",
                     ("%.3f" % m["recall"]) if m["recall"] is not None else "-",
                     ("%.3f" % m["gold_base"]) if m["gold_base"] is not None else "-",
                     len(m["counterexamples"])))
        for f in d["frame_agree"]:
            print("  [帧吻合 %-8s] %d/%d = %s"
                  % (f["type"], f["matched"], f["total"],
                     ("%.3f" % f["rate"]) if f["rate"] is not None else "-"))
        ce = [m for m in d["metrics"] if m["type"] == "FadeOut" and m["time_pos"]][0]["counterexamples"]
        print("  反例清单（FadeOut time>0 口径，%d 场）：" % len(ce))
        for i in range(0, len(ce), 6):
            print("     " + " ".join(ce[i:i + 6]))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with io.open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("\n机读结果 → %s" % os.path.abspath(a.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())

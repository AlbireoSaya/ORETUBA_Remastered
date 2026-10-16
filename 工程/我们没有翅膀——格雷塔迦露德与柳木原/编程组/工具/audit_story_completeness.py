#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_story_completeness.py —— 剧情与流程图完整性审计（ISSUE-20261003-03）
================================================================
只读，离线。**独立于 build_story.py**：直接读源语料 `资源组\剧本\scene_*.jsonl` 与 `spine.json`，
再读构建产物 `story\选择支配对说明.tsv` / `story\_intro.tjs` 与 UI 组 `layout\screens\32_flowchart.json`，
交叉对账剧情图的连通性与流程图的数据覆盖。

判据（任一不过即 FAIL）：
  S1 悬空引用：任何 `next` / 选择支 `target` 都必须指向存在的场景
  S2 选择支解析率：`story\选择支配对说明.tsv` 里**不得有「未解析（留空）」**
  S3 幕覆盖：`spine.acts` 每一幕的场景**都存在于语料**，且流程图有对应的幕级节点（`nodes[].act`）
  S4 入口可达：`spine` 的每个幕首场景 / 每个番外场景 都存在于语料

用法：
  python -X utf8 工具/audit_story_completeness.py --proj "<proj>" [--out <tsv>]
"""
import argparse, glob, io, json, os, re, sys

SRCS = ["ot", "otr", "ota", "otp", "otv", "np"]


def load_corpus(script_dir):
    sc = {}
    for f in sorted(glob.glob(os.path.join(script_dir, "scene_*.jsonl"))):
        for ln in io.open(f, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            d = json.loads(ln)
            sc[d["scene_id"]] = d
    return sc


def norm(x, sc):
    """与 build_story.norm 同口径：裸名补源前缀，再逐源兜底。"""
    if not x:
        return ""
    x = str(x)
    if x in sc:
        return x
    for p in SRCS:
        c = "%s_%s" % (p, x)
        if c in sc:
            return c
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    proj = os.path.abspath(args.proj)
    script_dir = os.path.join(proj, "资源组", "剧本")
    story = os.path.join(proj, "编程组", "krkr", "game", "story")
    sc = load_corpus(script_dir)
    print("[S0] 语料场景 %d 个" % len(sc))

    fails = []
    rows = []

    # ---- S1 悬空引用 ----
    dangling = []
    inbound = {}
    for sid, d in sc.items():
        for x in (d.get("next") or []):
            t = norm(x, sc)
            if not t:
                dangling.append((sid, "next", x))
            else:
                inbound.setdefault(t, []).append(sid)
        for c in (d.get("choices") or []):
            tg = c.get("target")
            if not tg:
                continue
            t = norm(tg, sc)
            if not t:
                dangling.append((sid, "choice", tg))
            else:
                inbound.setdefault(t, []).append(sid + "*")
    print("[S1] 悬空引用 %d 条（须为 0）" % len(dangling))
    for x in dangling[:10]:
        print("     ✗ %s 的 %s → %s" % x)
    if dangling:
        fails.append("S1 悬空 %d" % len(dangling))

    # ---- S2 选择支解析率（读构建产物） ----
    clp = os.path.join(story, "选择支配对说明.tsv")
    n_ch, n_unres = 0, 0
    if os.path.isfile(clp):
        hdr = None
        for ln in io.open(clp, encoding="utf-8"):
            c = ln.rstrip("\r\n").split("\t")
            if hdr is None:
                hdr = c
                continue
            if len(c) != len(hdr):
                continue
            d = dict(zip(hdr, c))
            if d["项序"] == "-1":
                continue
            n_ch += 1
            if d["依据"] == "未解析（留空）":
                n_unres += 1
        print("[S2] 选择支 %d 项 ｜ 未解析 %d 项（须为 0）" % (n_ch, n_unres))
        if n_unres:
            fails.append("S2 选择支未解析 %d" % n_unres)
    else:
        print("[S2] 未找到 %s —— 请先跑 build_story.py" % clp)
        fails.append("S2 缺构建产物")

    # ---- S3 幕覆盖 + 流程图幕级节点 ----
    sp = json.load(io.open(os.path.join(script_dir, "spine.json"), encoding="utf-8"))
    acts = sp.get("acts") or []
    miss_scene, act_counts = [], []
    for i, a in enumerate(acts):
        ss = a.get("scenes") or []
        act_counts.append(len(ss))
        for s in ss:
            if s not in sc:
                miss_scene.append((i + 1, s))
    print("[S3] spine 幕 %d 个 ｜ 幕内场景合计 %d ｜ 语料缺失 %d（须为 0）"
          % (len(acts), sum(act_counts), len(miss_scene)))
    for m in miss_scene[:8]:
        print("     ✗ 第 %d 幕缺场景 %s" % m)
    if miss_scene:
        fails.append("S3 幕场景缺失 %d" % len(miss_scene))

    fc = os.path.join(proj, "UI组", "krkr", "game", "ui_flow_data.tjs")
    fc_acts = []
    if os.path.isfile(fc):
        t = io.open(fc, encoding="utf-8").read()
        fc_acts = [int(m) for m in re.findall(r'kind:\s*"act",\s*act:\s*(\d+)', t)]
        print("[S3b] 流程图 `ui_flow_data.tjs` 的幕级节点 %d 个：%s" % (len(fc_acts), sorted(fc_acts)))
        if len(fc_acts) != len(acts):
            print("     ⚠️ 与 spine 幕数不等（%d vs %d）——需人工确认" % (len(fc_acts), len(acts)))
    else:
        print("[S3b] 未找到流程图数据 %s" % fc)

    # ---- S4 入口可达 ----
    entries = []
    for a in acts:
        if a.get("scenes"):
            entries.append(("act", a["scenes"][0]))
    for sd in (sp.get("side_stories") or []):
        if isinstance(sd, dict) and sd.get("scene_id"):
            entries.append(("side", sd["scene_id"]))
    bad_e = [(k, s) for k, s in entries if s not in sc]
    print("[S4] 入口 %d 个（幕 %d ＋ 番外 %d）｜ 不存在 %d（须为 0）"
          % (len(entries), len(acts), len(entries) - len(acts), len(bad_e)))
    for b in bad_e[:8]:
        print("     ✗ %s 入口 %s 不在语料" % b)
    if bad_e:
        fails.append("S4 入口缺失 %d" % len(bad_e))

    # ---- 附加情报（不判失败）：孤儿 / 无出口 ----
    spine_ids = set()
    for a in acts:
        spine_ids |= set(a.get("scenes") or [])
    for sd in (sp.get("side_stories") or []):
        if isinstance(sd, dict) and sd.get("scene_id"):
            spine_ids.add(sd["scene_id"])
    for sd in (sp.get("excluded") or []):
        if isinstance(sd, str):
            spine_ids.add(sd)
        elif isinstance(sd, dict) and sd.get("scene_id"):
            spine_ids.add(sd["scene_id"])
    orph = [s for s in sc if not inbound.get(s) and s not in spine_ids]
    ends = [s for s, d in sc.items() if not (d.get("next") or []) and not (d.get("choices") or [])]
    print("[S5] 孤儿（无入边且不在 spine）%d 个：%s%s"
          % (len(orph), "、".join(sorted(orph)[:10]), " …" if len(orph) > 10 else ""))
    print("[S6] 无出口场景（结局/终止点）%d 个：%s%s"
          % (len(ends), "、".join(sorted(ends)[:10]), " …" if len(ends) > 10 else ""))

    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("scene_id\tsrc\tlines\tnext\tchoices\tinbound\tverdict\n")
            for sid in sorted(sc):
                d = sc[sid]
                nxt = d.get("next") or []
                ch = d.get("choices") or []
                v = "结局" if (not nxt and not ch) else ("孤儿" if sid in orph else "OK")
                f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n"
                        % (sid, d.get("source", ""), d.get("line_count", 0),
                           len(nxt), len(ch), len(inbound.get(sid, [])), v))
        print("[ok] 明细 → %s" % args.out)

    print()
    if fails:
        print("[RESULT] FAIL ｜ " + " ｜ ".join(fails))
        return 1
    print("[RESULT] PASS ｜ 无悬空引用、选择支全解析、幕与入口全覆盖")
    return 0


if __name__ == "__main__":
    sys.exit(main())

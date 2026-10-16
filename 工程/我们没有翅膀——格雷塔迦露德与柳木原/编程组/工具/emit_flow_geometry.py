#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
emit_flow_geometry.py —— 把 UI 组已交的「全量节点几何」导成游戏内可读的 TJS（ISSUE-20261003-09）
================================================================================
* 只读 `UI组\_工作\ISSUE-20260928-02_第2步\全量布局.json`（**不修改、不复制该文件**）；
* 产出 `编程组\krkr\game\story\_flowgeom.tjs`（构建产物，随 story 目录一起进成品）：
    UIFlowGeomNodes = [ [x,y,w,h,kindCode], ... ]   // 全量 712 节点
    UIFlowGeomLinks = [ [x1,y1,x2,y2], ... ]        // 折线（**由真实边推导**；真实边为空时退回同 lane 代理）
    UIFlowGeomEdges = [ [i,j], ... ]                // **真实边**：节点下标对（剧本 next/choices 推导）

  真实边的推导（ISSUE-20261003-10）：读 `资源组\剧本\spine.json` 与 `scene_*.jsonl`，
  对每个场景取其 `next[]` 与 `choices[].target`，归一化到语料 scene_id，再映射到节点下标。
  归一化与 `build_story.py::norm` 同口径（裸名加源前缀，逐源兜底）。
"""
import argparse, glob, io, json, os

KIND = {"section": 0, "select": 1, "branch": 2, "frag": 3}
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
    for s in SRCS:
        c = "%s_%s" % (s, x)
        if c in sc:
            return c
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    proj = os.path.abspath(a.proj)
    src = os.path.join(proj, "UI组", "_工作", "ISSUE-20260928-02_第2步", "全量布局.json")
    if not os.path.isfile(src):
        print("[FATAL] 找不到几何源：%s" % src)
        return 2
    o = json.load(io.open(src, encoding="utf-8"))
    nodes = o["nodes"]
    if not nodes:
        # 一审次要-6：空节点表会让下面的 min()/max() 抛 ValueError（报错不干净）
        print("[FATAL] 几何源里 nodes 为空：%s" % src)
        return 2

    # ---- 真实边：剧本 next/choices → 节点下标对 ----
    script_dir = os.path.join(proj, "资源组", "剧本")
    corpus = load_corpus(script_dir)
    # ★ ISSUE-20261004-12：旧扁平几何同样**跟随构建集**（spine.json 的 acts+side_stories）——
    #   D15/D30 去重件（前奏诗 02/03 邂逅 32 场、PSV 美咲线 P03 4 场）不建节点、不连边。
    #   本文件只是分页几何缺位时的兜底，但两套生成器的节点集必须一致。
    _spine = json.load(io.open(os.path.join(script_dir, "spine.json"), encoding="utf-8"))
    buildset = set()
    for _a in _spine.get("acts") or []:
        for _s in _a.get("scenes") or []:
            buildset.add(_s)
    for _sd in _spine.get("side_stories") or []:
        buildset.add((_sd.get("scene_id") or "") if isinstance(_sd, dict) else _sd)
    buildset.discard("")
    # ★ 过滤必须在**建立任何下标之前**：直接丢弃构建集之外的节点，后面所有下标自然连续
    _before = len(nodes)
    nodes = [n for n in nodes
             if (not norm(n.get("id"), corpus)) or (norm(n.get("id"), corpus) in buildset)]
    if _before != len(nodes):
        print("[dedup] 按构建集剔除 %d 个节点（D15/D30 去重件，不入主干也不入流程图）" % (_before - len(nodes)))
    # 节点 id（UI 侧无前缀，如 s00_00）→ 语料 scene_id → 节点下标
    nid_of, idx_of = {}, {}
    for i, n in enumerate(nodes):
        sid = norm(n.get("id"), corpus)
        nid_of[i] = sid
        if sid and sid not in idx_of:
            idx_of[sid] = i
    edges, seen = [], set()
    for sid, d in corpus.items():
        if sid not in buildset:
            continue
        na = idx_of.get(sid)          # ⚠️ 不能叫 `a`：那会覆盖 argparse 的命名空间
        if na is None:
            continue
        tgt = [norm(x, corpus) for x in (d.get("next") or [])]
        tgt += [norm(c.get("target"), corpus) for c in (d.get("choices") or [])]
        for t2 in tgt:
            if t2 not in buildset:
                continue
            b = idx_of.get(t2)
            if b is None or na == b:
                continue
            k = (na, b)
            if k not in seen:
                seen.add(k)
                edges.append([na, b])

    def seg(p, q):
        """折线端点：**源节点底边中点 → 目标节点中心**。
        只给 4 个数（与既定格式和 `ui_flowfull.tjs` 的读取一致：`[x1,y1,x2,y2]`，
        由渲染器再折成 `[x1,y1, x2,y1, x2,y2]` 的 L 形）。"""
        return [int(p["x"] + p["w"] / 2), int(p["y"] + p["h"]),
                int(q["x"] + q["w"] / 2), int(q["y"] + q["h"] / 2)]

    links = [seg(nodes[a], nodes[b]) for a, b in edges]

    # ---- 兜底：真实边为空时，退回「同 lane 相邻相连」（仅保证有东西可画）----
    if not links:
        bylane = {}
        for n in nodes:
            bylane.setdefault(("" + str(n.get("lane"))), []).append(n)
        for _ln, arr in bylane.items():
            arr.sort(key=lambda n: (n.get("y") or 0, n.get("x") or 0))
            for i in range(1, len(arr)):
                p, q = arr[i - 1], arr[i]
                links.append([int(p["x"]), int(p["y"]), int(q["x"]), int(q["y"])])
        print("[warn] 真实边为空 ⇒ 退回同 lane 相邻代理（%d 条）" % len(links))

    out = a.out or os.path.join(proj, "编程组", "krkr", "game", "story", "_flowgeom.tjs")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("// 生成物（emit_flow_geometry.py）——勿手改：全量节点几何（源自 UI 组 全量布局.json）\n")
        f.write("UIFlowGeomNodes = [")
        f.write(",".join("[%d,%d,%d,%d,%d]" % (int(n["x"]), int(n["y"]), int(n["w"]), int(n["h"]),
                                               KIND.get(n.get("kind"), 9)) for n in nodes))
        f.write("];\n")
        f.write("UIFlowGeomLinks = [")
        f.write(",".join("[%d,%d,%d,%d]" % tuple(l) for l in links))
        f.write("];\n")
        # ★ 节点标题（供运行期自绘的 `drawText` 用）：与 UIFlowGeomNodes **同序同长**，
        #   取语料 `title_cn`（缺则 `title_jp`，再缺则场景 id）。空串表示该节点无标题。
        titles = []
        for i in range(len(nodes)):
            sid = nid_of.get(i, "")
            d = corpus.get(sid) or {}
            ti = (d.get("title_cn") or d.get("title_jp") or sid or "")
            titles.append(ti)
        f.write("UIFlowGeomTitles = [")
        f.write(",".join(json.dumps(x, ensure_ascii=False) for x in titles))
        f.write("];")
        f.write("\n")
        f.write("UIFlowGeomEdges = [")
        f.write(",".join("[%d,%d]" % tuple(e) for e in edges))
        f.write("];\n")
        # ★ 场景 id（与 Nodes 同序同长）：点选节点「进入该场景」用（动作 flow_scene_enter）。
        #   取归一化后的**语料 scene id**（如 ot_s01_19a），正是 `uiStoryStart()` 的入口键。
        f.write("UIFlowGeomIds = [")
        f.write(",".join(json.dumps(nid_of.get(i, ""), ensure_ascii=False) for i in range(len(nodes))))
        f.write("];\n")
        # ★ 节点类别码（与 Nodes 同序同长）：0 section / 1 select / 2 branch / 3 frag
        f.write("UIFlowGeomKinds = [")
        f.write(",".join("%d" % KIND.get(n.get("kind"), 9) for n in nodes))
        f.write("];\n")
        # ★ 内容包围盒 [x0,y0,x1,y1]（画布坐标）：视图平移/缩放的夹取依据。
        #   只用 x/y/w/h，跟 UI 组 geometry 一致；**不用** 1920×1080 画布（画布远小于内容）。
        bx0 = min(int(n["x"]) for n in nodes)
        by0 = min(int(n["y"]) for n in nodes)
        bx1 = max(int(n["x"]) + int(n["w"]) for n in nodes)
        by1 = max(int(n["y"]) + int(n["h"]) for n in nodes)
        f.write("UIFlowGeomBBox = [%d,%d,%d,%d];\n" % (bx0, by0, bx1, by1))
        f.write("UIFlowGeomViewport = [%d,%d,%d,%d];\n" % (
            int((o.get("viewport") or {}).get("x", 0)), int((o.get("viewport") or {}).get("y", 0)),
            int((o.get("viewport") or {}).get("w", 1920)), int((o.get("viewport") or {}).get("h", 1080))))
        f.write("UIFlowGeomCanvas = [%d,%d];\n" % (
            int((o.get("canvas") or {}).get("w", 1920)), int((o.get("canvas") or {}).get("h", 1080))))
        print("     包围盒 [%d,%d,%d,%d]（%dx%d）" % (bx0, by0, bx1, by1, bx1 - bx0, by1 - by0))
    _nt = len([x for x in titles if x])
    print("[ok] 节点 %d ｜ **真实边 %d 条** ｜ 折线 %d 条 ｜ **有标题 %d** ｜ → %s"
          % (len(nodes), len(edges), len(links), _nt, out))
    if edges:
        _iso = [i for i in range(len(nodes)) if nid_of.get(i, "") == ""]
        print("     UI 节点里归一不到语料的：%d 个" % len(_iso))
        print("     语料里没有几何节点的场景：%d 个（＝按 D15/D30 剔除的去重件，预期 %d）"
              % (len(corpus) - len(idx_of), len(_spine.get("excluded") or [])))
    print("     kind 分布：", {k: sum(1 for n in nodes if n.get("kind") == k) for k in KIND})
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

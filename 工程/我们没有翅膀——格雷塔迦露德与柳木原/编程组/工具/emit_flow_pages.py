#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
emit_flow_pages.py —— 流程图「分页」几何生成器（ISSUE-20261004-03）
================================================================================
为什么要重排：UI 组的 `全量布局.json`（`--preset full`）把 **6 部作品 19 条道拍平进同一
坐标系且未加每部偏移** ⇒ 48 个坐标格各挤了 2–5 个不同作品的场景（同格叠字）。
原作《交汇协奏曲》/《月影魅像》（Applique 同一套 `scnchart`）是**一条路线一页**：
`scnchart_ui.tjs` 的 `table.count == routes.count`；页内 y 沿脊柱累加、分叉沿垂直方向对称铺开
（`y = vert*(vnumer*2-(vdenom-1))\2`）、汇合用 `vclose` 拉回。

本生成器 = 把用户已裁决的 **9 页口径**（`流程图分页方案.md`）落成几何：
  · 每页独立坐标，页内重排原点 ⇒ **同坐标叠字归零**（硬断言：同层两节点矩形不得相交）
  · 分叉并排：k 个后继按 `(j-(k-1)/2) × SPREAD(k)` 对称铺开（k=2 → ±0.75 列；k≥3 → 1 列步进）
  · 汇合对齐：多父节点回到**最近公共祖先**的列（＝分叉的发散点）—— 即原作 `vclose` 的等价物
  · 组件（弱连通块）纵向堆叠；`4:0` 涅布追加篇由用户裁决**固定排在 A 页最后**
  · 跨页边 → 锚点表（源页出锚 / 目标页入锚），由渲染器画标记

输入（**只读**）：
  · `UI组\_工作\ISSUE-20260928-02_第2步\全量布局.json`（19 道的节点 / 类别 / 视口）
  · `资源组\剧本\scene_*.jsonl`（真实边 `next[]`+`choices[].target`、标题）
     `资源组\剧本\spine.json`（仅作分组计数参考，不参与版式）

输出：`编程组\krkr\game\story\_flowpages.tjs`（构建产物，随 story 目录进成品）
  UIFlowPageNames     = ["渡来明日香", ...]                         // 9 页名
  UIFlowPageCodes     = ["A","B",...]                              // 页代号（锚点标记用）
  UIFlowPageTable     = [ %[ nodes, links, titles, ids, kinds, bbox, anchors_in, anchors_out,
                            node_entries, node_count, link_count ], ... ]
  UIFlowGeomViewport / UIFlowGeomCanvas                             // 与旧版同名（渲染器已读）
  ⚠️ `UIFlowGeomNodes/Links/Titles/Ids/Kinds/BBox` **不在这里赋值** —— 它们由渲染器按
     「当前页」从 `UIFlowPageTable` 里**绑定**（`uiFlowFullSelectPage`），保证渲染器只认一个当前页。

用法：
  python -X utf8 工具\emit_flow_pages.py --proj "<工程目录>" --out "<krkr\game\story>"
  python -X utf8 工具\emit_flow_pages.py --proj "<工程目录>" --stats-only    # 只打印版式体检
"""
import argparse
import glob
import io
import json
import math
import os
import sys
from collections import defaultdict, deque

KIND = {"section": 0, "select": 1, "branch": 2, "frag": 3}
SRCS = ["ot", "otr", "ota", "otp", "otv", "np"]

# ── 版式参数（与 UI 组既有节点尺寸/行距一致；列宽 = 节点宽 + 间隙）────────────────
NODE_W = 296
NODE_H = 65
STEP_Y = 150          # 行距（与原版一致）
SPREAD_COL = 340      # 一「列」的横向步进 = 296 + 44 间隙
COMP_GAP = 260        # 组件之间的纵向空档
HUB_MIN_OUT = 8       # 出度 ≥ 此值的节点按「菜单枢纽」处理（不铺开，走总线）
# 分叉铺开步进（单位＝列）：
#   k=2 → ±0.75 列（362 px 间距）；k≥3 → ±(k-1)/2 列，相邻固定 1 列（340 px）
def spread_unit(k):
    if k <= 2:
        return 1.5
    return 1.0


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


# ── 九页口径（用户裁决；`流程图分页方案.md` §二/§三）────────────────────────────
PAGES = [
    ("A", "渡来明日香", ["0:0", "0:1", "0:5", "4:0"]),
    ("B", "玉泉日和子", ["0:2"]),
    ("C", "凤鸣", ["0:3"]),
    ("D", "大路线（真相·最终章）", ["0:4", "3:1"]),
    ("E", "香田亚衣（R 版）", ["1:0"]),
    ("F", "林田美咲（PSV）", ["2:0"]),
    ("G", "后日谈·对决羽田小鹰志", ["3:0"]),
    ("I", "AfterStory 番外", ["3:2"]),
    ("J", "前奏诗·短篇集", ["5:0", "5:1", "5:2", "5:3", "5:4", "5:5", "5:6"]),
]
# 节点标题为空的补名（数据事实：这两个 np 节点语料里没有标题）
# ⚠️ 顺序很关键：**先查本表，再取语料标题**。曾把语料标题的兜底写成 `title or sid`，
#    结果 `sid` 先填上了 ⇒ 本表**永远命中不到**（实测：`np_start_oretuba` 直接以 id 显示）。
TITLE_FIX = {
    # ★ 用**中文译名**（与 `Galgame.md` 索引 / `作品skill\SKILL.md:57` 的「涅布＊普拉斯」一致）。
    #   一审 Minor-3：原写「涅布＊プラス」是**源代号写法**，与作品层中文译名不一致 ⇒ 统一为中文。
    "np_start_oretuba": "涅布＊普拉斯 追加篇",
    "np_end_oretuba": "追加篇 闭幕",
}
# 页签条用的短名（9 个页签挤在 1235 px 里，全名会互相压字；全名仍保留在 UIFlowPageNames 里）
PAGE_SHORT = {
    "A": "明日香", "B": "日和子", "C": "凤鸣", "D": "大路线",
    "E": "亚衣", "F": "美咲", "G": "小鹰志", "I": "番外", "J": "前奏诗",
}


# ══════════════════════════════════════════════════════════════════════
# 图算法
# ══════════════════════════════════════════════════════════════════════
def components(nodes, succ, pred):
    """弱连通块；返回按「块内最小源序」排序的 list[list[node]]。"""
    adj = defaultdict(set)
    for a in nodes:
        for b in succ.get(a, ()):
            if b in nodes:
                adj[a].add(b)
                adj[b].add(a)
    seen = set()
    out = []
    for a in nodes:
        if a in seen:
            continue
        comp, st = [], [a]
        seen.add(a)
        while st:
            x = st.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    st.append(y)
        out.append(sorted(comp))
    return out


def levels_of(comp, succ, pred):
    """最长路层级（块内）。返回 {node: level}。块内无入边者为根（level 0）。"""
    cs = set(comp)
    indeg = {}
    for n in comp:
        indeg[n] = sum(1 for p in pred.get(n, ()) if p in cs)
    lev = {}
    dq = deque()
    for n in comp:
        if indeg[n] == 0:
            lev[n] = 0
            dq.append(n)
    order = []
    while dq:
        a = dq.popleft()
        order.append(a)
        for b in succ.get(a, ()):
            if b not in cs:
                continue
            lev[b] = max(lev.get(b, 0), lev[a] + 1)
            indeg[b] -= 1
            if indeg[b] == 0:
                dq.append(b)
    # 环保护：DAG 之外若还有剩余（本作语料无环，留兜底），按 0 级挂上
    for n in comp:
        if n not in lev:
            lev[n] = 0
    return lev, order


def _is_hub(children):
    """出度 ≥ HUB_MIN_OUT ⇒ 按「菜单枢纽」处理（不左右铺开，走左侧总线）。
    实测本作只有 1 个：`np_start_oretuba`（出度 26，涅布篇的章节枢纽，设计如此）。"""
    return len(children) >= HUB_MIN_OUT


def deepest_common_ancestor(ps, pred, lev):
    """多父节点的「最近公共祖先」：取父集合祖先集的交里 level 最大者。
    祖先集**含自身** ⇒ 单父时自然返回该父（继承其列）。找不到（含自身成环）时返回 None。"""
    cs = None
    for p in ps:
        anc = set()
        st = [p]
        while st:
            x = st.pop()
            if x in anc:
                continue
            anc.add(x)
            st.extend(pred.get(x, ()))
        cs = anc if cs is None else (cs & anc)
        if not cs:
            return None
    return max(cs, key=lambda n: (lev.get(n, 0), -n))


# ══════════════════════════════════════════════════════════════════════
# 版式
# ══════════════════════════════════════════════════════════════════════
def layout_page(order, succ, pred, report, is_np):
    """order = 本页节点的源序 list。返回 (xy, edges, _)。
    xy: {node: (x, y)}；x/y 皆为**画布坐标**（页内已重排原点：x0=0, y0=0）。"""
    nodes = list(order)
    nset = set(nodes)
    osucc = {n: [b for b in succ.get(n, ()) if b in nset] for n in nodes}
    opred = {n: [a for a in pred.get(n, ()) if a in nset] for n in nodes}
    rank = {n: i for i, n in enumerate(nodes)}      # 源序（决定同层/子序的稳定次序）

    comps = components(nodes, osucc, opred)
    # 用户裁决：`4:0` 涅布追加篇**整块排到最后**（该块节点的语料 id 以 `np_` 开头）
    comps.sort(key=lambda c: (1 if all(is_np(n) for n in c) else 0, min(rank[n] for n in c)))

    xy = {}
    y_cursor = 0
    centered = []
    st = report.setdefault("rule", dict(fan_nodes=0, fan_children=0, merge_nodes=0, merge_aligned=0,
                                        merge_no_lca=0, hubs=0, shifted=0))
    for comp in comps:
        lev, topo = levels_of(comp, osucc, opred)
        # ★ 前置条件硬校验（一审 Minor-1）：`levels_of` 的环兜底会把环内节点 `lev=0`
        #   但**不放进 `topo`** ⇒ 后面读 `col[n]` 会 KeyError 崩溃（不是静默错，但报错很难懂）。
        #   本作语料实测 **9 页 0 环**；这里把「无环」这条前置条件钉成断言，将来出现脏数据会立刻炸出来。
        if len(topo) != len(comp):
            print("[FATAL] 页内图有环（成分 %d 个节点，拓扑序只排出 %d 个）——本生成器**只支持 DAG**，"
                  "请先修数据或扩展版式算法。" % (len(comp), len(topo)))
            return None
        col = {}
        # 子序 = 源序（等价于脚本 `next[]` 的顺序：语料按该序排布行）
        for n in topo:
            ps = opred[n]
            if len(ps) >= 2:
                # ★ 汇合对齐：多父节点回到「最近公共祖先」的列（＝分叉的发散点，原作 `vclose` 的等价物）
                a = deepest_common_ancestor(ps, opred, lev)
                if a is None:
                    col[n] = 0.0
                    st["merge_no_lca"] += 1
                else:
                    col[n] = col.get(a, 0.0)
                    st["merge_aligned"] += 1
                st["merge_nodes"] += 1
            elif len(ps) == 1:
                p = ps[0]
                ch = sorted(osucc[p], key=lambda z: rank[z])
                if _is_hub(osucc[p]):
                    col[n] = col[p]                    # 枢纽：子节点不铺开（走总线）
                elif len(ch) == 1:
                    col[n] = col[p]
                else:
                    j = ch.index(n)
                    k = len(ch)
                    st["fan_children"] += 1
                    if j == 0:
                        st["fan_nodes"] += 1
                    col[n] = col[p] + (j - (k - 1) / 2.0) * spread_unit(k)
            else:
                col[n] = 0.0
        st["hubs"] += sum(1 for n in comp if _is_hub(osucc[n]))
        # 同层去冲突：按 col 排序后逐个推挤（保证同层任意两节点矩形不相交）
        bylev = defaultdict(list)
        for n in comp:
            bylev[lev[n]].append(n)
        min_sep = NODE_W + 24
        for L, arr in bylev.items():
            arr.sort(key=lambda n: (col[n], rank[n]))
            for i in range(1, len(arr)):
                need = col[arr[i - 1]] * SPREAD_COL + min_sep
                if col[arr[i]] * SPREAD_COL < need:
                    col[arr[i]] = need / SPREAD_COL
                    st["shifted"] += 1
        # ★ 整块居中：块内 col 的极差中心放到 0（页内 x 原点），避免长块整体偏到一侧
        cs = [col[n] for n in comp]
        mid = (min(cs) + max(cs)) / 2.0
        for n in comp:
            col[n] -= mid
        m = max(lev.values()) if lev else 0
        for n in comp:
            xy[n] = (col[n] * SPREAD_COL, y_cursor + lev[n] * STEP_Y)
        y_cursor += (m + 1) * STEP_Y + COMP_GAP
        centered.append((comp, lev, col, m))
        report["comps"].append(dict(size=len(comp), levels=m + 1,
                                    first_rank=min(rank[n] for n in comp)))

    edges = []
    for a in nodes:
        for b in osucc[a]:
            edges.append((a, b))
    return xy, edges


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--stats-only", action="store_true")
    ap.add_argument("--page", default="", help="只体检某页（A/B/...）")
    a = ap.parse_args()
    proj = os.path.abspath(a.proj)
    src = os.path.join(proj, "UI组", "_工作", "ISSUE-20260928-02_第2步", "全量布局.json")
    if not os.path.isfile(src):
        print("[FATAL] 找不到几何源：%s" % src)
        return 2
    lay = json.load(io.open(src, encoding="utf-8"))
    unodes = lay["nodes"]
    lanes = lay["lanes"]
    if not unodes:
        print("[FATAL] 几何源里 nodes 为空：%s" % src)
        return 2

    corpus = load_corpus(os.path.join(proj, "资源组", "剧本"))
    # ★ ISSUE-20261004-12：流程图节点集**跟随构建集**（spine.json 的 acts + side_stories）。
    #   语料里被 D15 / D30 判为去重件的场景（前奏诗 02/03 邂逅 32 场、PSV 美咲线 P03 4 场）
    #   **不建节点**——否则流程图会出现点不进去的死节点，且同一段美咲短篇会在 J/F 两页各出现一次。
    #   判定来源与 build_story --all 完全一致（spine 的 acts[].scenes + side_stories[].scene_id）。
    _spine = json.load(io.open(os.path.join(proj, "资源组", "剧本", "spine.json"), encoding="utf-8"))
    buildset = set()
    for _a in _spine.get("acts") or []:
        for _s in _a.get("scenes") or []:
            buildset.add(_s)
    for _sd in _spine.get("side_stories") or []:
        if isinstance(_sd, dict):
            buildset.add(_sd.get("scene_id") or "")
        else:
            buildset.add(_sd)
    buildset.discard("")
    sid_of, byid = {}, {}
    for i, n in enumerate(unodes):
        sid = norm(n.get("id"), corpus)
        sid_of[i] = sid
        if sid and sid not in byid:
            byid[sid] = i
    excluded_nodes = {i for i, s in sid_of.items() if s and s not in buildset}
    if excluded_nodes:
        print("[dedup] 按构建集剔除 %d 个节点（D15/D30 去重件，不入主干也不入流程图）" % len(excluded_nodes))
    # 全局节点索引（UI 数组下标）作为内部节点键
    # 道 → 该道的节点索引序列（保序）；★ 剔除构建集之外的节点，空「道」整条丢弃（D15/D30）
    lane_nodes = {}
    dropped_lanes = []
    for L in lanes:
        seq = []
        for nid in L["nodes"]:
            for i, n in enumerate(unodes):
                if n["id"] == nid:
                    if i not in excluded_nodes:
                        seq.append(i)
                    break
        if seq:
            lane_nodes[L["key"]] = seq
        else:
            dropped_lanes.append(L["key"])
    if dropped_lanes:
        print("[dedup] 空「道」整条丢弃（其场景全部为去重件）：%s" % dropped_lanes)

    # 真实边（全局）；★ 起点/终点任一在构建集之外（D15/D30 去重件）的边一并丢弃
    gsucc, gpred = defaultdict(list), defaultdict(list)
    for sid, d in corpus.items():
        if sid not in buildset:
            continue
        i = byid.get(sid)
        if i is None:
            continue
        tg = [norm(x, corpus) for x in (d.get("next") or [])]
        tg += [norm(c.get("target"), corpus) for c in (d.get("choices") or [])]
        for t in tg:
            if t not in buildset:
                continue
            j = byid.get(t)
            if j is None or j == i:
                continue
            if j not in gsucc[i]:
                gsucc[i].append(j)
            if i not in gpred[j]:
                gpred[j].append(i)

    # 页归属
    lane2page = {}
    for pi, (_code, _nm, keys) in enumerate(PAGES):
        for k in keys:
            lane2page[k] = pi
    unmapped = [k for k in lane_nodes if k not in lane2page]
    if unmapped:
        print("[FATAL] 有「道」没分到页：%s" % unmapped)
        return 2

    report = dict(pages=[], comps=[])
    page_tables = []
    total = 0
    for pi, (code, name, keys) in enumerate(PAGES):
        order, seen = [], set()
        for k in keys:
            for i in lane_nodes.get(k, []):
                if i not in seen:
                    seen.add(i)
                    order.append(i)
        if not order:
            print("[FATAL] 页 %s 无节点" % code)
            return 2
        # 页内图
        nset = set(order)
        osucc = {n: [b for b in gsucc.get(n, ()) if b in nset] for n in order}
        opred = {n: [a for a in gpred.get(n, ()) if a in nset] for n in order}
        r = layout_page(order, osucc, opred, report,
                        lambda n: (sid_of[n] or "").startswith("np_"))
        if r is None:
            return 2                      # 页内图有环（见 layout_page 的前置条件校验）
        xy, edges = r

        # ── 体检：同层同坐标 ────────────────────────────────────────
        cell = {}
        dup = 0
        for n in order:
            x, y = xy[n]
            key = (round(x), round(y))
            if key in cell:
                dup += 1
            cell[key] = n
        # 同层最小水平间距
        byy = defaultdict(list)
        for n in order:
            byy[round(xy[n][1])].append(xy[n][0])
        mindx = 10 ** 9
        for y, xs in byy.items():
            xs.sort()
            for i in range(1, len(xs)):
                mindx = min(mindx, xs[i] - xs[i - 1])

        # ── 输出记录 ───────────────────────────────────────────────
        uidx = {n: i for i, n in enumerate(order)}
        nodes_out, links_out, titles_out, ids_out, kinds_out = [], [], [], [], []
        for n in order:
            u = unodes[n]
            x, y = xy[n]
            nodes_out.append([int(round(x)), int(round(y)), int(u["w"]), int(u["h"]),
                              KIND.get(u.get("kind"), 9)])
            t = (corpus.get(sid_of[n]) or {})
            # ★ 顺序：**补名表 → 语料标题 → 空串**。**绝不用场景 id 兜底**
            #   （语料里 22 个节点无标题，用 id 兜底会让节点上显示 "ot_s01_04n" 这种机器串）。
            ti = TITLE_FIX.get(sid_of[n], "")
            if not ti:
                ti = t.get("title_cn") or t.get("title_jp") or ""
            titles_out.append(ti)
            ids_out.append(sid_of[n])
            kinds_out.append(KIND.get(u.get("kind"), 9))

        # 连线：折线点列（扁平 [x1,y1,x2,y2,...]）——同列直线；异列走「贝塞尔展平」
        def nrect(n):
            x, y = xy[n]
            u = unodes[n]
            return (x, y, x + u["w"], y + u["h"])

        def poly(a, b):
            """父底边中点 → 子顶边中点。同列直线；异列用三次贝塞尔（先竖、后横、末端竖直入）"""
            ax, ay, ax2, ay2 = nrect(a)
            bx, by, bx2, by2 = nrect(b)
            x1, y1 = (ax + ax2) / 2.0, ay2                    # 父底边中点
            x2, y2 = (bx + bx2) / 2.0, by                     # 子顶边中点
            if abs(x1 - x2) < 1.5:
                return [x1, y1, x2, y2]
            # 异列：从父底边中点出发，折到父侧边，再竖直下到子顶边（原作 `_pathLinkV*` 同法）
            sx = ax2 if x2 > x1 else ax                       # 父的侧边
            pts = [x1, y1, sx, y1]
            k = 10
            # 贝塞尔展平：起点 (sx,y1) → 控制点 (x2,y1) → 控制点 (x2,y1) → 终点 (x2,y2)
            c1x, c1y = x2, y1
            c2x, c2y = x2, y1
            ex, ey = x2, y2
            px, py = sx, y1
            for i in range(1, k + 1):
                t = i / float(k)
                mt = 1.0 - t
                X = mt**3 * px + 3 * mt**2 * t * c1x + 3 * mt * t**2 * c2x + t**3 * ex
                Y = mt**3 * py + 3 * mt**2 * t * c1y + 3 * mt * t**2 * c2y + t**3 * ey
                pts += [X, Y]
            return pts

        nlinks = 0
        hub_bus = 0
        for a_, b_ in edges:
            if _is_hub(osucc[a_]):
                # 枢纽：走左侧总线 —— 父底边中点 → 总线 x → 子左沿
                hub_bus += 1
                ax, ay, ax2, ay2 = nrect(a_)
                bx, by, bx2, by2 = nrect(b_)
                hx = (ax + ax2) / 2.0
                busx = ax - 60
                links_out.append([hx, ay2, busx, ay2, busx, by + NODE_H / 2.0, bx, by + NODE_H / 2.0])
            else:
                links_out.append([int(round(v)) for v in poly(a_, b_)])
            nlinks += 1

        bbox = [min(round(xy[n][0]) for n in order), min(round(xy[n][1]) for n in order),
                max(round(xy[n][0]) + unodes[n]["w"] for n in order),
                max(round(xy[n][1]) + unodes[n]["h"] for n in order)]
        # 跨页锚点
        ain, aout = [], []
        pages_of = {}
        for pj, (_c, _n, ks) in enumerate(PAGES):
            for k in ks:
                pages_of[k] = pj
        # 节点 → 页
        nodepage = {}
        for pj, (_c, _n, ks) in enumerate(PAGES):
            for k in ks:
                for n in lane_nodes.get(k, []):
                    nodepage[n] = pj
        for n in order:
            for b in gsucc.get(n, ()):
                pb = nodepage.get(b, -1)
                if pb >= 0 and pb != pi:
                    aout.append([uidx[n], pb, PAGES[pb][0], uidx.get(b, -1)])
        for n in order:
            for p_ in gpred.get(n, ()):
                pp = nodepage.get(p_, -1)
                if pp >= 0 and pp != pi:
                    ain.append([uidx[n], pp, PAGES[pp][0]])

        page_tables.append(dict(code=code, name=name, nodes=nodes_out, links=links_out,
                                titles=titles_out, ids=ids_out, kinds=kinds_out, bbox=bbox,
                                anchors_in=ain, anchors_out=aout,
                                entries=[uidx[n] for n in order
                                         if not [p for p in opred[n]]],
                                ))
        report["pages"].append(dict(code=code, name=name, n=len(order), links=nlinks,
                                    dup_coord=dup, min_dx=(None if mindx > 10 ** 8 else mindx),
                                    bbox=bbox, anchors_out=len(aout), anchors_in=len(ain),
                                    hub_edges=hub_bus,
                                    entries=[sid_of[n] for n in order if not opred[n]]))
        total += len(order)

    # ── 打印体检 ────────────────────────────────────────────────────
    print("=" * 78)
    print("分页版式体检（%d 页 / 合计 %d 节点 = 构建集场景；语料 %d 场，按 D15/D30 剔除 %d 场）"
          % (len(page_tables), total, len(corpus), len(excluded_nodes)))
    print("=" * 78)
    bad = 0
    for p in report["pages"]:
        flag = ""
        if p["dup_coord"]:
            flag += " ★同坐标=%d" % p["dup_coord"]
            bad += 1
        if p["min_dx"] is not None and p["min_dx"] < NODE_W:
            flag += " ★同层最小间距=%d" % p["min_dx"]
            bad += 1
        print("  %-2s %-22s 节点 %-4d 连线 %-4d 同坐标 %-3d 同层最小间距 %-5s "
              "锚出 %-2d 锚入 %-2d%s" % (
                  p["code"], p["name"], p["n"], p["links"], p["dup_coord"],
                  p["min_dx"], p["anchors_out"], p["anchors_in"], flag))
        print("      包围盒 %s（%d×%d） 入口 %s" % (
            p["bbox"], p["bbox"][2] - p["bbox"][0], p["bbox"][3] - p["bbox"][1],
            p["entries"][:4]))
    _empty = []
    for p in page_tables:
        for t2, i2 in zip(p["titles"], p["ids"]):
            if not t2:
                _empty.append(i2)
    print("节点标题：%d/%d 有字 ｜ 无字（语料无标题，**不拿 id 兜底**）：%d 个 %s"
          % (total - len(_empty), total, len(_empty), _empty[:6]))
    n_anchor = sum(p["anchors_out"] for p in report["pages"])
    print("-" * 78)
    st = report.get("rule", {})
    print("版式规则计数：并排分叉 %d 个（铺开子节点 %d 个）｜ 汇合节点 %d 个（对齐到最近公共祖先 %d、"
          "找不到 LCA %d）｜ 菜单枢纽 %d 个 ｜ 去冲突推挤 %d 次"
          % (st.get("fan_nodes", 0), st.get("fan_children", 0), st.get("merge_nodes", 0),
             st.get("merge_aligned", 0), st.get("merge_no_lca", 0), st.get("hubs", 0),
             st.get("shifted", 0)))
    print("跨页锚点合计（出）：%d  （方案定稿 12）" % n_anchor)
    print("重排后同坐标节点合计：%d  ；有问题的页数：%d" % (
        sum(p["dup_coord"] for p in report["pages"]), bad))
    if a.stats_only:
        return 0 if bad == 0 else 3

    # ★★ 默认输出**跟脚本自身位置走**，不跟 `--proj` 走。
    #   踩过的坑（`会话交接_20261004-01.md` 坑 46）：`--proj` 指的是**工程目录**，
    #   而并行会话里 `--proj` 常指向**主工作树** ⇒ 依它拼输出会把几何写进主工作树、
    #   本 checkout 反而没有。凡"构建产物"，落点必须由 `--out` 决定（`build_story.py` 已如此）。
    out = a.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "krkr", "game", "story", "_flowpages.tjs")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("// 生成物（emit_flow_pages.py）——勿手改：流程图**分页**几何（ISSUE-20261004-03）\n")
        f.write("// 来源：UI组\\_工作\\ISSUE-20260928-02_第2步\\全量布局.json + 资源组\\剧本\\scene_*.jsonl\n")
        f.write("UIFlowPageCodes = [%s];\n" % ",".join(json.dumps(p["code"]) for p in page_tables))
        f.write("UIFlowPageNames = [%s];\n" % ",".join(
            json.dumps(p["name"], ensure_ascii=False) for p in page_tables))
        f.write("UIFlowPageShort = [%s];\n" % ",".join(
            json.dumps(PAGE_SHORT.get(p["code"], p["name"]), ensure_ascii=False) for p in page_tables))
        f.write("UIFlowGeomViewport = [%d,%d,%d,%d];\n" % (
            int((lay.get("viewport") or {}).get("x", 60)), int((lay.get("viewport") or {}).get("y", 190)),
            int((lay.get("viewport") or {}).get("w", 1235)), int((lay.get("viewport") or {}).get("h", 827))))
        f.write("UIFlowGeomCanvas = [%d,%d];\n" % (
            int((lay.get("canvas") or {}).get("w", 1920)), int((lay.get("canvas") or {}).get("h", 1080))))
        f.write("UIFlowPageTable = [\n")
        for _pi, p in enumerate(page_tables):
            # ⚠️ 页与页之间必须是 **逗号**（数组元素分隔）——写成 `;` 会让整个文件语法错误
            #    （实测：引擎报「几何装载失败：语法有误」）。首元素前不加分隔符。
            if _pi > 0:
                f.write(",\n")
            f.write("%%[code:%s,name:%s,\n" % (json.dumps(p["code"]),
                                               json.dumps(p["name"], ensure_ascii=False)))
            f.write("  nodes:[%s],\n" % ",".join("[%d,%d,%d,%d,%d]" % tuple(v) for v in p["nodes"]))
            f.write("  links:[%s],\n" % ",".join("[" + ",".join("%.1f" % v for v in l) + "]"
                                                for l in p["links"]))
            f.write("  titles:[%s],\n" % ",".join(json.dumps(t, ensure_ascii=False) for t in p["titles"]))
            f.write("  ids:[%s],\n" % ",".join(json.dumps(t, ensure_ascii=False) for t in p["ids"]))
            f.write("  kinds:[%s],\n" % ",".join("%d" % k for k in p["kinds"]))
            f.write("  bbox:[%d,%d,%d,%d],\n" % tuple(p["bbox"]))
            f.write("  entries:[%s],\n" % ",".join("%d" % e for e in p["entries"]))
            f.write("  anchors_in:[%s],\n" % ",".join("[%d,%d,%s]" % (v[0], v[1], json.dumps(v[2]))
                                                      for v in p["anchors_in"]))
            # ⚠️ 最后一项**不能带尾逗号**：TJS2 的 `%[…, ]` 字典字面量不接受尾逗号
            #    （实测：引擎报「几何装载失败：语法有误」）。
            f.write("  anchors_out:[%s]\n" % ",".join(
                "[%d,%d,%s,%d]" % (v[0], v[1], json.dumps(v[2]), v[3]) for v in p["anchors_out"]))
            f.write("]")            # ★ 本页字典**收尾**：只写 `]`（**不能带 `;`**——那会把数组字面量
                                    #   截断成 `[…];, %[…]`，引擎报「语法有误」；实测踩到）
        f.write("\n];\n")
        f.write("UIFlowPageBBox = [%s];\n" % ",".join(
            "[%d,%d,%d,%d]" % tuple(p["bbox"]) for p in page_tables))
        _st = report.get("rule", {})
        f.write("UIFlowPageRule = %%[fan_nodes:%d, fan_children:%d, merge_nodes:%d, merge_aligned:%d, "
                "merge_no_lca:%d, hubs:%d, shifted:%d];\n" % (
                    _st.get("fan_nodes", 0), _st.get("fan_children", 0), _st.get("merge_nodes", 0),
                    _st.get("merge_aligned", 0), _st.get("merge_no_lca", 0), _st.get("hubs", 0),
                    _st.get("shifted", 0)))
    sz = os.path.getsize(out)
    print("[ok] → %s（%.1f KB）" % (out, sz / 1024.0))
    return 0 if bad == 0 else 3


if __name__ == "__main__":
    sys.exit(main())

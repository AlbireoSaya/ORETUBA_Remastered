# -*- coding: utf-8 -*-
r"""test_flow_links.py —— 流程图**连线数据**闸门（七条断言 + 四条自证）

Issue `ISSUE-20260927-05`（第 1 步 · 模块 E1 建）→ `ISSUE-20260928-02`（第 2 步 · E1 增补 state 断言）
接口 = `_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md` §三（v1.2）
     ＋ `_工作\ISSUE-20260928-02_第2步\接口冻结.md` §一.2（**本文件新增的 state 断言**）

■ 它守什么（**七条断言**）
  ① 每点 `x∈[0,1920] y∈[0,1080]`
  ② 相邻点**只有一维变化**（正交折线）
  ③ 首点＝源节点锚点、末点＝目标节点顶边中点
     —— 契约原文写「首点＝源节点底边中点」；但 §三 表里 VL（侧出）的首点定义是
        `[ex, sy-32]`＝源节点**朝目标那一侧的边中点**，与底边中点不同 ⇒ 本闸门按形态分别认锚：
        直线 / VZ 认「底边中点」，VL 认「左/右侧边中点」。末点一律认「目标顶边中点」。
  ④ `arrow ⇒ 末段长度 ≥ 2.0×w`
  ⑤ `pts` 无重复相邻点
  ⑥ **`state` 与色/宽/箭头逐条自洽**（冻结 §一.2，取代第 1 步的 `kind`）：
     · `state` ∈ {`normal`,`visited`,`noroute`}（缺省语义＝`normal`，但**生成器一律显式写出**）
     · `color` == `palette.json` 里 `edge_<state>` 的值（★ 全部断言里唯一的「色值溯源」关）
     · `w` / `arrow` == 冻结表：normal 4/true、visited 4/true、**noroute 3/false**
     · **`kind` 键不得再出现**（第 2 步已废弃该字段 ⇒ 防回退）
     · 三档色**两两不同**；三档的 palette 键**必须都存在**（即便本屏只用到 `normal`）
  ⑦ **新族端点保护**：番外独立层 `fc.frag<G>.*`（冻结 §二）**不产连线** ⇒
     断言没有任何 `links` 的首/末点落在独立层节点锚点上
     （若今后要让它作端点，须同步本文件的 `node_slots()` 与契约）

■ 四条自证
  ⑧ **异参复跑**：同一条生成器命令换 `--section/--lanes` ⇒ 产出**不同**的节点集合
     （证明生成器没有样例硬编码；走 `--dry-run`，**不落盘**）
  ⑨ **变异自证 A**：在内存里把一条边的一个点挪 1px ⇒ 断言必须失败（证明闸门不是恒真）
  ⑩ **变异自证 B**：在内存里把一条边的 `state` 改成 `noroute`、**却保留原 `w`/`arrow`/`color`**
     ⇒ 断言必须失败（证明 ⑥ 的「state ↔ 色宽箭头自洽」真的在管，不是只看 `state` 取值合法）
  ⑪ **变异自证 C**：在内存里加一条**端点落在独立层节点锚点上**的边 ⇒ 断言 ⑦ 必须报出
     （证明「独立层不产连线」不是空话；仅当屏内有 `fc.frag<G>.*` 时可构造）

■ 用法
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python 工具\test_flow_links.py                       # 默认查 layout/screens/32_flowchart.json
    python 工具\test_flow_links.py --screen <某屏.json>    # 查任意预设产出（如 states/frag 变体）
    # EXIT=0 才算通过；失败逐条打印
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCR = os.path.join(UI, "layout", "screens", "32_flowchart.json")
ROOT = os.path.join(UI, "layout", "_root.json")
PAL = os.path.join(UI, "layout", "palette.json")
GEN = os.path.join(HERE, "gen_flow_layout.py")

NODE_W, NODE_H = 296, 65
BRANCH_W, BRANCH_H = 65, 65
BRANCH_OFFSET_X = (NODE_W - BRANCH_W) // 2      # 生成器把分支底座居中于 296 宽槽位（+115）
VL_LATERAL = NODE_W // 2
ARROW_BACK_FACTOR = 2.0

# ★ 冻结 §一.2 的硬表（**本文件的镜像**；生成器侧在 `gen_flow_layout.EDGE_STATES`）
#   改表必须两处同改，且 `layout\_schema.md` §links 表同步。
EDGE_STATES = {
    "normal":  ("edge_normal",  4, True),
    "visited": ("edge_visited", 4, True),
    "noroute": ("edge_noroute", 3, False),
}

# 番外独立层节点 id 前缀形态：fc.frag<G>.<NNNN>（G=1..6）——**不产连线**（冻结 §二）
FRAG_ID_PREFIX = "fc.frag"

FAILS: list[str] = []


def fail(msg):
    FAILS.append(msg)
    return msg


def load(path=SCR):
    scr = json.load(io.open(path, encoding="utf-8"))
    canvas = json.load(io.open(ROOT, encoding="utf-8"))["canvas"]
    pal = json.load(io.open(PAL, encoding="utf-8"))["colors"]
    return scr, canvas, pal


def node_slots(elements):
    """屏内所有**主干节点槽位** `[(slot_x, slot_y, id)]`，以及**独立层节点槽位**（另列）。

    · `fc.node.*`（296×65 image）：左上角即槽位左上角
    · `fc.branch.*`（65×65 image）：底座居中于 296 宽槽位 ⇒ slot_x = x - 115（与生成器同口径）
    · `fc.frag<G>.<NNNN>`（296×65 image，冻结 §二）：**独立层节点**，本轮**不作连线端点** ⇒ 另列，
      由断言 ⑦ 保证「没有任何 links 的端点落在它上面」。
    """
    main, frag = [], []
    for e in elements:
        i = e.get("id", "")
        if e.get("kind") != "image":
            continue
        if i.startswith("fc.node.") and e.get("w") == NODE_W and e.get("h") == NODE_H:
            main.append((e["x"], e["y"], i))
        elif i.startswith("fc.branch.") and e.get("w") == BRANCH_W and e.get("h") == BRANCH_H:
            main.append((e["x"] - BRANCH_OFFSET_X, e["y"], i))
        elif (i.startswith(FRAG_ID_PREFIX) and e.get("w") == NODE_W
              and e.get("h") == NODE_H and "." in i):
            frag.append((e["x"], e["y"], i))
    return main, frag


def anchor_bottom_keys(nodes):
    return [(x + NODE_W // 2, y + NODE_H) for (x, y, _i) in nodes]


def palette_map(pal):
    """palette.json → {键: 0xAARRGGBB 整数}（只收能解析成色值的键）。"""
    out = {}
    for k, v in pal.items():
        val = v.get("value") if isinstance(v, dict) else None
        if isinstance(val, str) and val.startswith("#") and len(val) == 7:
            out[k] = 0xFF000000 | int(val[1:], 16)
        elif isinstance(val, int) and not isinstance(val, bool):
            out[k] = 0xFF000000 | (val & 0xFFFFFF)
    return out


def run_checks(nodes, frag_nodes, links, cw, ch, palmap):
    """六条契约断言 ＋ 冻结 §一.2 的四条。把失败写进模块级 FAILS；调用方先清空。"""
    if not links:
        fail("屏内一条连线都没有（links 为空）—— 生成器没产边或键被丢弃")
        return len(FAILS)

    # ★ 三档色键必须都存在（即便本屏只用到 normal）——色板回归的第一道网
    for st, (ckey, _w, _a) in EDGE_STATES.items():
        if ckey not in palmap:
            fail("palette.json 缺色键 %s（state=%s 的配色来源；禁止直写色值）" % (ckey, st))
    cols_seen = {}
    for st, (ckey, _w, _a) in EDGE_STATES.items():
        if ckey in palmap:
            cols_seen.setdefault(palmap[ckey], []).append(st)
    for c, sts in cols_seen.items():
        if len(sts) > 1:
            fail("三档连线色**不互异**：0x%08X 同时被 %s 使用（状态不可辨）" % (c, sts))

    anchor_bottom = {(x + NODE_W // 2, y + NODE_H): i for (x, y, i) in nodes}
    anchor_top = {(x + NODE_W // 2, y): i for (x, y, i) in nodes}
    # VL 的侧出锚点：契约 §三 表 `[ex, sy-32]`；sy = 槽位底边 = y+65 ⇒ sy-32 = y+33
    side_y = NODE_H - NODE_H // 2
    anchor_side = {}
    for (x, y, i) in nodes:
        anchor_side[(x, y + side_y)] = i
        anchor_side[(x + NODE_W, y + side_y)] = i
    # 独立层节点锚点（只用于断言 ⑦）
    frag_anchors = set()
    for (x, y, _i) in frag_nodes:
        frag_anchors.add((x + NODE_W // 2, y))
        frag_anchors.add((x + NODE_W // 2, y + NODE_H))
        frag_anchors.add((x, y + side_y))
        frag_anchors.add((x + NODE_W, y + side_y))

    state_hist = {k: 0 for k in EDGE_STATES}
    for lk in links:
        lid = lk.get("id", "?")
        pts = lk.get("pts")
        w = lk.get("w")
        if not isinstance(pts, list) or len(pts) < 2:
            fail("%s：pts 非法或点数 <2：%r" % (lid, pts))
            continue
        # ① 画布内
        for p in pts:
            if not (isinstance(p, list) and len(p) == 2):
                fail("%s：点不是 [x,y]：%r" % (lid, p))
                break
            if not (0 <= p[0] <= cw and 0 <= p[1] <= ch):
                fail("%s：点 %r 越出画布 [0,%d]×[0,%d]" % (lid, p, cw, ch))
        # ② 正交（相邻点只有一维变化）
        for k in range(len(pts) - 1):
            dx = pts[k + 1][0] - pts[k][0]
            dy = pts[k + 1][1] - pts[k][1]
            if (dx == 0) == (dy == 0):
                fail("%s：第 %d→%d 段非正交（dx=%s dy=%s）（两点重合或斜向）"
                     % (lid, k, k + 1, dx, dy))
        # ⑤ 无重复相邻点（与 ② 同源，独立报出以便分辨）
        for k in range(len(pts) - 1):
            if pts[k] == pts[k + 1]:
                fail("%s：第 %d,%d 点是重复的相邻点 %r" % (lid, k, k + 1, pts[k]))
        first, last = tuple(pts[0]), tuple(pts[-1])
        # ③ 首末锚点
        if last not in anchor_top:
            fail("%s：末点 %r 不是任何节点的顶边中点（%s）"
                 % (lid, last, ("最近候选 " + str(sorted(anchor_top)[0])) if anchor_top else "无节点"))
        if first not in anchor_bottom and first not in anchor_side:
            fail("%s：首点 %r 既不是任何节点的底边中点、也不是任何节点的左/右侧边中点" % (lid, first))
        # ★ ⑥ / 冻结 §一.2：state ↔ 色/宽/箭头**逐条自洽**（两端不做配色判断 ⇒ 数据必须自洽）
        st = lk.get("state")
        if "kind" in lk:
            fail("%s：仍带已废弃的 `kind` 键（%r）—— 第 2 步已由 `state` 取代（冻结 §一.2）"
                 % (lid, lk.get("kind")))
        if st is None:
            fail("%s：缺 `state` 键（冻结 §一.2 要求生成器一律显式写出；缺省语义虽为 normal，"
                 "但缺键无法与「写错档」区分）" % lid)
        elif st not in EDGE_STATES:
            fail("%s：state=%r 非法（只允许 %s）" % (lid, st, list(EDGE_STATES)))
        else:
            state_hist[st] += 1
            ckey, ew, ea = EDGE_STATES[st]
            if ckey in palmap and lk.get("color") != palmap[ckey]:
                fail("%s：state=%s 的 color=0x%08X ≠ palette.%s=0x%08X（禁止直写 / 写错档）"
                     % (lid, st, lk.get("color") or 0, ckey, palmap[ckey]))
            if w != ew:
                fail("%s：state=%s 的 w=%r ≠ 冻结表 %d" % (lid, st, w, ew))
            if bool(lk.get("arrow")) != ea:
                fail("%s：state=%s 的 arrow=%r ≠ 冻结表 %s（noroute **不画箭头**）"
                     % (lid, st, lk.get("arrow"), ea))
        if not isinstance(w, int) or w <= 0:
            fail("%s：w 非法：%r（契约要求正整数）" % (lid, w))
            continue
        # ④ 箭头末段长
        if lk.get("arrow"):
            seg = abs(pts[-1][0] - pts[-2][0]) + abs(pts[-1][1] - pts[-2][1])
            if seg < ARROW_BACK_FACTOR * w:
                fail("%s：arrow 末段长 %s < %.1f×w（w=%s）" % (lid, seg, ARROW_BACK_FACTOR, w))
        # ⑦ 独立层节点不得作端点（冻结 §二：独立层不产连线）
        for tag, p in (("首点", first), ("末点", last)):
            if p in frag_anchors:
                fail("%s：%s %r 落在**番外独立层节点**锚点上 —— 独立层不产连线（冻结 §二）；"
                     "若确需让它作端点，须同步本文件的 `node_slots()` 与契约" % (lid, tag, p))
    return len(FAILS)


def dry_run_node_ids(*extra):
    """跑生成器 --dry-run，取 `NODE_IDS:` 行（**不落盘**）。"""
    cmd = [sys.executable, GEN, "--dry-run"] + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=UI)
    if r.returncode != 0:
        raise RuntimeError("生成器 --dry-run 失败（rc=%d）：%s" % (r.returncode, r.stderr[-500:]))
    for line in r.stdout.splitlines():
        if line.startswith("NODE_IDS:"):
            body = line[len("NODE_IDS:"):].strip()
            return [x for x in body.split(",") if x]
    raise RuntimeError("--dry-run 输出里没有 NODE_IDS 行")


def main():
    ap = argparse.ArgumentParser(description="流程图连线数据闸门（七条断言：契约 §三 6 条 + 冻结 §一.2 1 条 ｜ 四条自证）")
    ap.add_argument("--screen", default=SCR,
                    help="待检屏文件（默认 layout/screens/32_flowchart.json；"
                         "可指向任意预设产出，如 --out 落下的 states/frag 变体）")
    args = ap.parse_args()

    print("=" * 78)
    print("test_flow_links.py · 流程图连线数据闸门（七条断言：契约 §三 6 条 + 冻结 §一.2 1 条 ｜ 四条自证）")
    print("  屏文件：%s" % args.screen)
    print("=" * 78)
    scr, canvas, pal = load(args.screen)
    cw, ch = canvas["width"], canvas["height"]
    nodes, frag_nodes = node_slots(scr.get("elements") or [])
    links = scr.get("links") or []
    palmap = palette_map(pal)
    print("  节点 %d 个（主干；独立层节点 %d 个）｜ 连线 %d 条 ｜ 画布 %d×%d ｜ 色板键 %d 个（可解析色值）"
          % (len(nodes), len(frag_nodes), len(links), cw, ch, len(palmap)))
    print("  flags_default = %s" % (scr.get("flags_default") or {}))

    FAILS.clear()
    n = run_checks(nodes, frag_nodes, links, cw, ch, palmap)
    core_fails = list(FAILS)
    hist = {}
    for lk in links:
        hist[lk.get("state")] = hist.get(lk.get("state"), 0) + 1
    print("\n【①–⑦ 断言（契约 §三 6 条 ＋ 冻结 §一.2 的 state↔色宽箭头 ＋ 独立层不产连线）】（%d 条连线）" % len(links))
    print("  state 分布：%s" % ("，".join("%s %d" % (k, v) for k, v in sorted(hist.items())) or "(无)"))
    if n == 0:
        print("  七条断言全部通过 ✓")
    else:
        print("  **%d 处失败**：" % n)
        for m in core_fails:
            print("    ✗ %s" % m)

    extra_fails = []

    # ── ⑧ 异参复跑：节点集合必须变 ────────────────────────────────
    print("\n【⑧ 异参复跑（证明无样例硬编码；--dry-run 不落盘）】")
    a = dry_run_node_ids()
    b = dry_run_node_ids("--section", "5", "--lanes", "0", "--from", "0", "--limit", "40", "--step-y", "150")
    same = set(a) == set(b)
    if not a or not b:
        extra_fails.append("⑧ 异参复跑：有一侧节点集合为空")
        print("  ✗ 有一侧为空（默认 %d 个 / 异参 %d 个）" % (len(a), len(b)))
    elif same:
        extra_fails.append("⑧ 异参复跑：换 --section/--lanes 后节点集合竟完全相同 ⇒ 疑似样例硬编码")
        print("  ✗ 节点集合相同（%d 个：%s…）" % (len(a), a[:3]))
    else:
        print("  ✓ 默认 %d 个（%s…） ≠ 异参 %d 个（%s…）；交集 %d 个"
              % (len(a), a[:3], len(b), b[:3], len(set(a) & set(b))))

    # ── ⑨ 变异自证 A：挪 1px 必须被抓住 ─────────────────────────────
    print("\n【⑨ 变异自证 A（内存里挪 1px，不落盘）】")
    if not links:
        extra_fails.append("⑨ 变异自证 A：没有连线可变异")
        print("  ✗ 没有连线可变异")
    else:
        mut = json.loads(json.dumps(links, ensure_ascii=False))
        bottoms = set(anchor_bottom_keys(nodes))
        target = None
        for lk in mut:
            if tuple(lk["pts"][0]) in bottoms:
                target = lk
                break
        if target is None:
            target = mut[0]
        before = list(target["pts"][0])
        target["pts"][0] = [before[0], before[1] + 1]
        FAILS.clear()
        nm = run_checks(nodes, frag_nodes, mut, cw, ch, palmap)
        mut_fails = list(FAILS)
        if nm == 0:
            extra_fails.append("⑨ 变异自证 A 失败：把 %s 的首点挪 1px 后七条断言仍全过 ⇒ 闸门恒真"
                               % target.get("id"))
            print("  ✗ 变异后仍全过（闸门恒真！）")
        else:
            hit = [m for m in mut_fails if str(target.get("id")) in m]
            print("  ✓ 把 %s 的首点 %s 挪到 %s ⇒ 报出 %d 处失败" % (target.get("id"), before,
                                                                    target["pts"][0], nm))
            print("      命中该变异的断言：%s" % (hit[0][:110] if hit else "(其它断言先报出)"))

    # ── ⑩ 变异自证 B：state 与色/宽/箭头脱钩必须被抓住 ──────────────
    print("\n【⑩ 变异自证 B（内存里把 state 改成 noroute、却保留原 color/w/arrow，不落盘）】")
    if not links:
        extra_fails.append("⑩ 变异自证 B：没有连线可变异")
        print("  ✗ 没有连线可变异")
    else:
        mut2 = json.loads(json.dumps(links, ensure_ascii=False))
        # 找一条**原本不是 noroute** 的边（noroute 改 noroute 是恒等变异、抓不住任何东西）
        t2 = None
        for lk in mut2:
            if lk.get("state") != "noroute":
                t2 = lk
                break
        if t2 is None:
            print("  － 屏内全部边都已是 noroute ⇒ 本自证不可构造（跳过，不记失败）")
        else:
            old = (t2.get("state"), t2.get("w"), t2.get("arrow"))
            t2["state"] = "noroute"          # 只改状态、**故意不动** w/arrow/color
            FAILS.clear()
            nm2 = run_checks(nodes, frag_nodes, mut2, cw, ch, palmap)
            f2 = list(FAILS)
            if nm2 == 0:
                extra_fails.append("⑩ 变异自证 B 失败：%s 的 state 改成 noroute 而 w/arrow/color 未跟改，"
                                   "七条断言仍全过 ⇒ 「state ↔ 色宽箭头自洽」没在管" % t2.get("id"))
                print("  ✗ 变异后仍全过（⑥ 的耦合检查恒真！）")
            else:
                hit2 = [m for m in f2 if str(t2.get("id")) in m]
                print("  ✓ 把 %s 由 %s 改成 noroute（w/arrow/color 保持原值）⇒ 报出 %d 处失败"
                      % (t2.get("id"), old[0], nm2))
                print("      命中该变异的断言：%s" % (hit2[0][:110] if hit2 else "(其它断言先报出)"))

    # ── ⑪ 变异自证 C：独立层节点**不得作端点**必须被抓住 ────────────
    print("\n【⑪ 变异自证 C（内存里加一条端点落在独立层节点锚点上的边，不落盘）】")
    if not frag_nodes:
        print("  － 本屏无番外独立层节点（`fc.frag<G>.*`）⇒ 本自证不可构造（跳过，不记失败）")
    elif not links:
        extra_fails.append("⑪ 变异自证 C：没有连线可作对照")
        print("  ✗ 没有连线可作对照")
    else:
        fx, fy, fid = frag_nodes[0]
        sxa, sya = fx + NODE_W // 2, fy + NODE_H          # 独立层节点 1 的底边中点
        # 尾巴接到一条**合法的主干顶边中点**上，并保证折线正交、无重复点
        # ⇒ 唯一该被抓的就是「首点落在独立层节点锚点」（断言 ⑦；③ 亦会同报）
        tgt = None
        for lk in links:
            lx, ly = lk["pts"][-1]
            if ly != sya and lx != sxa:
                tgt = (lx, ly)
                break
        if tgt is None:
            print("  － 找不到可作尾巴的主干顶边锚点（构造不出正交折线）⇒ 跳过，不记失败")
        else:
            mut3 = json.loads(json.dumps(links, ensure_ascii=False))
            mut3.append({"id": "fc.link.SYNTHETIC", "state": "normal",
                         "pts": [[sxa, sya], [tgt[0], sya], [tgt[0], tgt[1]]],
                         "w": EDGE_STATES["normal"][1],
                         "color": palmap.get(EDGE_STATES["normal"][0], 0),
                         "arrow": EDGE_STATES["normal"][2]})
            FAILS.clear()
            nm3 = run_checks(nodes, frag_nodes, mut3, cw, ch, palmap)
            f3 = list(FAILS)
            hit3 = [m for m in f3 if "fc.link.SYNTHETIC" in m and "番外独立层节点" in m]
            if not hit3:
                extra_fails.append("⑪ 变异自证 C 失败：端点落在独立层节点锚点上的边未被断言 ⑦ 报出 ⇒ 该断言恒真")
                print("  ✗ 断言 ⑦ 未报出（恒真！）；该变异共报出 %d 处失败：%s" % (nm3, f3[:2]))
            else:
                print("  ✓ 注入 fc.link.SYNTHETIC（首点＝%s 的底边中点 (%d,%d)；折线正交、末点为合法主干顶边中点）"
                      "⇒ 报出 %d 处失败" % (fid, sxa, sya, nm3))
                print("      断言 ⑦ 命中：%s" % hit3[0][:110])
                print("      （注：断言 ③「首点须是主干节点锚点」也会同时报出 —— ⑦ 的价值在于把冻结 §二 的"
                      "「独立层不产连线」显式化：若今后把 frag 族加进 `node_slots()`，③ 会静默放宽而 ⑦ 仍会报）")

    print("\n" + "-" * 78)
    allf = core_fails + extra_fails
    if allf:
        print("结果：**不通过**（退出码 1）—— 断言失败 %d 处 + 自证失败 %d 处"
              % (len(core_fails), len(extra_fails)))
        for m in allf:
            print("  ✗ %s" % m)
        return 1
    print("结果：**全部通过**（七条断言 + 四条自证）（退出码 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

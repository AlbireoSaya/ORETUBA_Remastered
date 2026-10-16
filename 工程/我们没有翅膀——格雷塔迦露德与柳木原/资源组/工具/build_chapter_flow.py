#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_chapter_flow.py —— 《我们没有翅膀——格雷塔迦露德与柳木原》全系列「章节级」剧情流程图生成器

产物（均在 资源组\\ 下，只读输入、幂等、可复跑）：
  1. 资源组\\08_全系列章节流程图.md    （章节级流程图：Mermaid 分层图 + 逐路线播放顺序表 + 分岔点表 + 影响清单）
  2. 资源组\\08_全系列章节流程图.html  （自包含可交互页面，无任何外部依赖）

数据源（只读）：
  资源组\\05_章节总表.tsv   —— 712 章（一脚本 = 一章）

**顺序口径（本版核心修正）**：
  lane 不再按 `05_章节总表.tsv` 的 `章节序号`（逐源 DFS 前序，会跨路线穿插）排列，
  而是**直接复用 `07_路线脉络.md` 的路线定义与播放顺序算法**（`build_chapter_docs.py` 的
  `build_routes()` / `play_order()`）——即「沿 `next[i]` 走该路线的分岐臂」的
  **分支感知展开**（分支点在前、各臂相邻、汇合点在后）。
  由此保证 **08 的每条 lane 与 07 的对应节逐章顺序完全一致**（同一函数、同一成员集合）。

**「臂」口径（与 07 §0.1 对齐）**：
  `next` 的第 i 项一律记作「臂 i」；**只有该章「选项数 = `next` 项数」时才可称「选项 i → 臂 i」**。
  全系列 50 个含选项章节中 32 章满足、18 章不满足（详见 §〇 与 `KEY_CHOICE` 断言）。

**共享章节口径（与 07 对齐）**：同一章被多条路线播放时，在每条路线中**均完整列出**并标 `〔共用〕`。
故 lane 条目合计 814，**去重后唯一章节数 = 712**（＝ `05_章节总表.tsv` 的 712 行）。

只读声明：本脚本不写任何语料、不改 TSV、不改既有文档；只写上面两份产物。
"""
import csv
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))          # 资源组\工具
RG = os.path.dirname(HERE)                                  # 资源组
TSV = os.path.join(RG, "05_章节总表.tsv")
OUT_MD = os.path.join(RG, "08_全系列章节流程图.md")
OUT_HTML = os.path.join(RG, "08_全系列章节流程图.html")
DOC07 = os.path.join(RG, "07_路线脉络.md")

# 复用 07 的路线定义与播放顺序算法（同一函数 => 顺序口径必然一致）
sys.path.insert(0, HERE)
import build_chapter_docs as B  # noqa: E402

SEP = "；"          # next 分隔符（全角分号）
NO_NEXT = "（无）"   # next 占位符

# ── 按 07 的路线结构分组（组名 = 用户可读的展示名）─────────────────────
SECTIONS = [
    ("本篇（2009）· 序文 · 三条平行线 · 大路线", [1, 2, 3, 4, 5, 6]),
    ("R 版亚衣线（2011）", [7]),
    ("PSV 美咲线（2014）", [8]),
    ("After Story（2010 FD）", [9, 10, 11]),
    ("涅布＊プラス 明日香篇（2012）", [12]),
    ("前奏诗（Prelude · 2008）", [13, 14, 15, 16, 17, 18, 19]),
]

WORK_POS = {
    "otp": "全系列最早（2008 先行作）：框架剧＋四角色短篇＋邂逅原型",
    "ot": "正传本体：序文 → 三条平行人格线 → 大路线真相",
    "otr": "R 版（2011）：亚衣线扩至 55 章，隼人线内分支",
    "otv": "PSV（2014）：美咲线，承鹰志线 Bad End 的同期分支",
    "ota": "后日谈合集：对决四篇＋各线 after＋最终统合线",
    "np": "涅布（2012）：毕业后 2 月的子篇目菜单式短篇集",
}

# ── 07 §0.1「分岐点 × 臂」表：7 个关键分岐点 / 16 行（逐字对齐 07）─────
# 字段：(分岐点, 该章选项数, 选项文本（中文）, 走的臂, 该臂入口, 该臂走向, 归属路线)
# 该表用于 §〇.2 与 HTML「分岔点」视图；生成时对 TSV 做断言（选项数、臂目标一致）。
KEY_CHOICE = [
    ("s01_14g", 0, "（无选项文本，脚本级分岐）", 1, "s01_14g1",
     "`s01_14g1 → s01_14h → s01_17a → s01_18a`（京 END）→ `s01_19a`", "(2)山科京"),
    ("s01_14g", 0, "（无选项文本，脚本级分岐）", 2, "s01_14g2",
     "死路（`next=[]`）", "(6)鹰志线 Bad End 支"),
    ("s01_14g", 0, "（无选项文本，脚本级分岐）", 3, "s01_14i",
     "`s01_14i → s01_14j1 → s01_14k → s01_14l → s01_15a → s01_15b → s01_16a`（明日香 END）", "(1)渡来明日香"),
    ("s01_14i", 0, "（无选项文本，脚本级分岐）", 1, "s01_14j1",
     "`s01_14j1 → s01_14k → s01_14l → s01_15a → s01_15b → s01_16a`", "(1)渡来明日香"),
    ("s01_14i", 0, "（无选项文本，脚本级分岐）", 2, "s01_14j2",
     "死路（`next=[]`）", "(6)鹰志线 Bad End 支"),
    ("s03_08b", 0, "（无选项文本，脚本级分岐）", 1, "s03_08c1",
     "`s03_08c1` → `s03_09a1` → `s03_09b` → （鸣线主链，全文见 (4) 章表）→ `s03_22a`", "(4)凤鸣"),
    ("s03_08b", 0, "（无选项文本，脚本级分岐）", 2, "s03_08c2",
     "`s03_08c2` → `s03_09a2` → **跨源** `s03c_01a`（R 版亚衣线）", "(7)香田亚衣"),
    ("s04_05i", 2, "不带来救赎 / 带来救赎", 1, "s04_06j1",
     "`s04_06j1` → `s04_06k` → `s01_05a` / `s02_10a`", "(1)(3)"),
    ("s04_05i", 2, "不带来救赎 / 带来救赎", 2, "s04_06j2",
     "`s04_06j2` → `s04_07a` → （s04 主链 45 章，全文见 (5) 章表）→ `s04_28b` → `s04_29a`（真 END）",
     "(5)大路线（真相）"),
    ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 1, "s03_16a",
     "`s03_16a` → `s03_17a` → `s03_18a` → `s03_19a` → `s03_20a` → `s03_21a` → `s03_21b` → `s03_21c` → `s03_22a`（鸣解缆）",
     "(4)凤鸣"),
    ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 2, "s04_06k",
     "`s04_06k` → `s01_05a` / `s02_10a`", "(1)(3)"),
    ("s04_06j1", 0, "（无选项文本，脚本级分岐）", 3, "s04_06l",
     "终点（`next=[]`）", "(5)大路线（真相）"),
    ("s04_06k", 0, "（无选项文本，脚本级分岐）", 1, "s01_05a",
     "`s01_05a` → `s01_05b` → `s01_06a` → （s01 主链，全文见 (1) 章表）→ `s01_16a`", "(1)渡来明日香"),
    ("s04_06k", 0, "（无选项文本，脚本级分岐）", 2, "s02_10a",
     "`s02_10a` → `s02_10b` → `s02_10c` → （s02 主链，全文见 (3) 章表）→ `s02_16a`", "(3)玉泉日和子"),
    ("24_4e", 3, "隼人 / 迦楼罗 / 小鹰志", 1, "24_5a", "`24_5a → 24_5b`（G-END）", "(10)最终统合线"),
    ("24_4e", 3, "隼人 / 迦楼罗 / 小鹰志", 2, "24_5c", "`24_5c`（B-END，终点）", "(10)最终统合线"),
]

# 分岔点的展示名（07 §0.1 用带源前缀的写法；TSV 的 script 无前缀）
POINT_LABEL = {"24_4e": "ota_24_4e"}

# 「选项数 ≠ next 项数」的 18 章（实测，见 §〇.1）
UNPAIRED = [
    ("s01_12b", 2, 3), ("s01_13b", 2, 3), ("11_3d0", 4, 3), ("12_4c0", 3, 2),
    ("24_1b", 3, 1), ("24_2b", 3, 1), ("24_2c", 3, 1), ("24_2d", 3, 1),
    ("24_3b", 3, 1), ("24_3c", 3, 1), ("24_3d", 3, 1), ("24_3e", 3, 1),
    ("24_4b", 3, 1), ("24_4c", 3, 1), ("24_4d", 3, 1), ("24_4e", 3, 2),
    ("24_5a", 3, 1), ("start_oretuba", 34, 26),
]

# 18 件「影响后续剧情」的逐条说明（均据 TSV 的 next / 选项 / 依据列写就，不含臆测）
IMPACT_NOTE = {
    "s03_08b": "隼人线**分岐前共享段终点**（前 40 章共通）。两臂：`s03_08c1` 续走隼人／凤鸣线并最终汇入 s04 大路线；`s03_08c2` 跨源转入 R 版亚衣线 `s03c_01a`。**改此章＝决定隼人线走凤鸣还是亚衣。**",
    "s04_05i": "大路线选择支（选项「不带来救赎／带来救赎」）。臂 1 → `s04_06j1`＝不救赎，走向各线回环与 `s04_06l`（不完全统合）；臂 2 → `s04_06j2`＝救赎，直达真 END `s04_29a`。**改此章＝决定大路线是否收束到真结局。**",
    "s04_06j1": "大路线三臂：`s03_16a`（回 s03 隼人线）、`s04_06k`（回环到 s01／s02）、`s04_06l`（自循环＝不完全统合）。**是 s04 向三条人格线回环的核心节点。**",
    "s04_06k": "两臂分别回 `s01_05a`（鹰志线）与 `s02_10a`（鹫介线）。**是把大路线重新接回 s01／s02 的两条跨路线边。**",
    "s01_09c0": "鹰志线选择支，三选项点名**渡来／山科／针生**三人，分别指向 `s01_09c1／c2／c3`。**改此章＝改鹰志线人际支线走向。**",
    "s01_09d": "鹰志线**共通线伏笔**：提到 WING QUEST（「ウイングクエストって知ってるか」），**后于 s04 大路线回收**。",
    "s01_14g": "鹰志线**分岐前共享段终点**（前 67 章共通，占该线 59%）。三臂：`s01_14g1`→京 END 线；`s01_14g2`→鹰志线 Bad End（终至 `s01_14j2`）；`s01_14i`→明日香 END 线。**改此章＝决定鹰志线走京／明日香／坏结局。**",
    "s01_14i": "鹰志线两臂：`s01_14j1`（→`s01_16a` 明日香 END）与 `s01_14j2`（Bad End，**同时是 PSV 美咲线 `M01_01` 的接入点**）。**改此章＝决定是否落入 Bad End 并开启美咲线。**",
    "s02_10c": "鹫介线选择支，三选项点名**纪奈子／英里子**，分别指向 `s02_10d1／d2／d3`。**改此章＝改鹫介线人际支线走向。**",
    "s04_25b": "大路线**真相伏笔**：提到 伊丹さん（「伊丹さんが何でも言うこと聞くと言ったとき…」），**指向被封印的长兄人格**。",
    "s03_09a2": "隼人线 `s03_09a` 的 (C) 变体，**全系列唯一跨源边** `s03_09a2 → s03c_01a`，即 **R 版亚衣线的正式入口**（`s03_09a1` 则续鸣线）。**改此章＝开关亚衣线。**",
    "11_3d0": "After Story 对决羽田鹰志篇选择支，4 选项点名**京／渡来／山科／针生**，指向 3 臂 `11_3d1／d2／d3`（**选项数 ≠ 臂数，配对未确证**）。**改此章＝改后日谈分支。**",
    "24_4e": "AS 最终统合线**分岐前共享段终点**（前 17 章共通）。两臂：`24_5a`→`24_5b`（G-END，小鸠救助成功）；`24_5c`（B-END，失败 GAME OVER）。**改此章＝决定 G-END／B-END。**",
    "02_03g": "前奏诗「邂逅·鹫介」原型的选择支（选项「是／不是／说不好」→ `02_03g1／g2／g3`）。**target 已填但 `pairing_verified=false`（配对未确证）；该场景 D15 已排除，不入主干。**",
    "03_03b": "前奏诗「邂逅·隼人」原型的选择支（「配合／掐断小丫头的节奏」→ `03_03c1／c2`）。**target 已填但 `pairing_verified=false`。**",
    "03_03i": "前奏诗「邂逅·隼人」原型的选择支（「说不定真有／那不可能吧」→ `03_03j1／j2`）。**target 已填但 `pairing_verified=false`。**",
    "a05_a0": "涅布「S／M 比」选择支，4 臂：`a05_b0／c0`→`a06_c0`；`a05_d0／e0` 为 `next=[]` 自循环（**后继未确证**，见 `章节提取说明` §6.2-6）。",
    "start_oretuba": "涅布**子篇目菜单根脚本**：34 选项／26 臂（`a01_*`–`a06_*`），**决定进入哪个子篇**。`pairing_verified=true`，并点名 小鸠／针生。",
}

# 跨作品衔接（依据：TSV next 边 / 章节提取说明 §3.3；无 next 边者注明来源）
LINKAGE = [
    ("本篇 s03_09a2", "R版亚衣线 s03c_01a", "TSV next 边（**跨源**）", "隼人线 (C) 变体分岔入亚衣线；全系列唯一跨源边"),
    ("前奏诗（全源）", "本篇 / 全系列", "时序（无 next 边）", "2008 先行作；框架剧＋四短篇＋邂逅原型"),
    ("本篇 s01_14j2", "PSV美咲线 M01_01", "既有文档（无 next 边）", "01_剧情流程图 §4.4：M01_01 注释「S01_14J2 的继续」"),
    ("本篇 s04_29a（真 END）", "AfterStory 24_1a", "时序（无 next 边）", "AS 24_1a「仮統合の崩壊」承接 s04 假统合"),
    ("AfterStory（全源）", "涅布明日香篇 start_oretuba", "时序（无 next 边）", "毕业后 2 月，菜单式短篇集"),
    ("AfterStory 11_6a/12_5a/13_5b", "AS おれつば剧场 51_1/52_1/53_1", "TSV next 边（跨路线）", "对决四篇收束后接剧场番外"),
]

# 总览图（跨作品，仅作品级节点；实线＝TSV next 边，虚线＝时序/文档衔接）
OVERVIEW_MERMAID = """flowchart TD
    PRE["前奏诗 Prelude（2008）<br/>buru01-04 框架剧 · p01-p04 四短篇 · 02/03 邂逅原型"]:::work
    S00["本篇 序文 s00_00"]:::work
    S01["s01 鹰志线（114 章）<br/>明日香 END / 京 END / Bad End"]:::work
    S02["s02 鹫介线（83 章）<br/>日和子 END"]:::work
    S03["s03 隼人线（95 章）<br/>凤鸣 END"]:::work
    S04["s04 大路线（74 章）<br/>真相 · 真 END"]:::work
    OTR["R版亚衣线 s03c（55 章）<br/>亚衣 END"]:::work
    OTV["PSV 美咲线（31 章）<br/>美咲 END"]:::work
    OTA["After Story（172 章）<br/>11/12/13/14 对决四篇 · 24 最终统合线 G/B-END"]:::work
    NP["涅布＊プラス 明日香篇（28 章）<br/>子篇目菜单式短篇集"]:::work

    PRE -.->|时序（2008 先行）| S00
    S00 --> S01
    S01 --> S02
    S02 --> S03
    S03 --> S04
    S01 -->|"s01_19a → s03_24"| S03
    S02 -->|"s02_17a → s03_24"| S03
    S03 -->|"s03_09a2 → s03c_01a"| OTR
    S04 -->|"s04_06k → s01_05a"| S01
    S04 -->|"s04_06k → s02_10a"| S02
    S04 -->|"s04_06j1 → s03_16a"| S03
    S01 -.->|"s01_14j2 接入（文档）"| OTV
    S04 -.->|时序| OTA
    OTA -.->|时序| NP
    classDef work fill:#1c232e,stroke:#4ea3ff,color:#dde4ee;
"""

CLASS_DEFS = """    classDef norm fill:#1c232e,stroke:#2b3543,color:#dde4ee;
    classDef imp fill:#3a1620,stroke:#ff6b6b,color:#ffd7d7,stroke-width:2px;
    classDef branch fill:#3a2f14,stroke:#ffb347,color:#ffe9c2;
    classDef end fill:#12331f,stroke:#4ade80,color:#d6ffe4;
    classDef sys fill:#1a2330,stroke:#4ea3ff,color:#cfe6ff;
    classDef side fill:#241a30,stroke:#b07cff,color:#e9dcff;
    classDef cross fill:#111820,stroke:#5d6b7d,color:#8fa0b6,stroke-dasharray:4 3;
"""


# ─────────────────────────── 读取与建模 ───────────────────────────

def split_next(cell):
    cell = (cell or "").strip()
    if not cell or cell == NO_NEXT:
        return []
    return [t.strip() for t in cell.split(SEP) if t.strip() and t.strip() != NO_NEXT]


def split_choices(cell):
    cell = (cell or "").strip()
    if not cell:
        return []
    return [t.strip() for t in cell.split(" / ") if t.strip()]


def mlabel(s):
    """Mermaid 标签安全化。"""
    s = (s or "").replace('"', "'").replace("\n", " ")
    s = s.replace("[", "（").replace("]", "）")
    return s


def esc_md(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


def node_class(n):
    if n["impact"]:
        return "imp"
    if n["role"].startswith("结局") or n["next_kind"] == "end":
        return "end"
    if n["next_kind"] == "branch":
        return "branch"
    if n["role"] in ("系统", "框架"):
        return "sys"
    if n["role"] in ("番外", "短剧情", "其他"):
        return "side"
    return "norm"


def short_title(n, width=26):
    t = n["cn"] or n["jp"] or "（无标题）"
    if len(t) > width:
        t = t[: width - 1] + "…"
    return t


def build():
    rows, by = B.load()
    for r in rows:
        r["_sid"] = r["源代号"] + "_" + r["script"]

    routes = B.build_routes(rows, by)
    seqs = [B.play_order(by, rt["members"]) for rt in routes]

    nodes = {}
    order = []
    for r in rows:
        script = r["script"].strip()
        assert script and script not in nodes, "duplicate script: %s" % script
        nodes[script] = {
            "script": script,
            "src": r["源代号"].strip(),
            "work": r["作品来源"].strip(),
            "seq": int(r["章节序号"]),
            "jp": r["章节标题(日文)"].strip(),
            "cn": r["章节标题(中文)"].strip(),
            "phase": r["phase"].strip(),
            "route": r["route"].strip(),
            "kind": r["source_kind"].strip(),
            "lines": int(r["行数"] or 0),
            "next": split_next(r["next"]),
            "next_kind": r["next_kind"].strip(),
            "choiceN": int(r["选项数"] or 0),
            "choices": split_choices(r["选项文本(中文)"]),
            "date": r["游戏日期"].strip(),
            "cast": r["登场人物"].strip(),
            "role": r["章节作用"].strip(),
            "impact": r["是否影响后续剧情"].strip(),
            "spine": r["spine归属"].strip(),
            "remark": r["备注"].strip(),
        }
        order.append(script)

    # 边
    edges = []
    for s in order:
        for t in nodes[s]["next"]:
            assert t in nodes, "dangling next target %s -> %s" % (s, t)
            edges.append((s, t))

    # 路线归属（07 口径；同一章可属多条路线）
    route_of = {s: [] for s in order}
    for rt, seq in zip(routes, seqs):
        for s in seq:
            route_of[s].append(rt["rid"])

    # 每条 lane：节点序（07 的播放顺序）+ 共用标记（07 口径：在更早路线出现过）
    lanes = []
    seen = set()
    for rt, seq in zip(routes, seqs):
        items = [{"id": s, "shared": s in seen} for s in seq]
        lanes.append({
            "rid": rt["rid"], "title": rt["title"], "kind": rt["kind"], "src": rt["src"],
            "note": rt["note"], "path": B.ROUTE_PATH.get(rt["rid"], "待判定"),
            "nodes": items,
        })
        seen.update(seq)

    # 分岔点 / 臂
    key_choice = {}
    for (a, n, b, c, entry, dest, e) in KEY_CHOICE:
        assert a in nodes, a
        assert nodes[a]["choiceN"] == n, ("KEY_CHOICE 选项数不符", a, nodes[a]["choiceN"], n)
        assert nodes[a]["next"][c - 1] == entry, ("KEY_CHOICE 臂目标不符", a, c, entry)
        key_choice[(a, c)] = e

    arms = {}   # script -> [ {i, target, routeLabel, crossRoute, crossSrc, choice} ]
    for s in order:
        n = nodes[s]
        if len(n["next"]) < 2:
            continue
        lst = []
        for i, t in enumerate(n["next"], 1):
            rt_list = route_of.get(t, [])
            if (s, i) in key_choice:
                rl = key_choice[(s, i)]
            else:
                rl = "／".join("(%d)%s" % (r, routes[r - 1]["title"]) for r in rt_list) or "（未裁决）"
            lst.append({
                "i": i, "target": t, "routeLabel": rl,
                "crossRoute": bool(rt_list) and not any(
                    t in set(seqs[r - 1]) and s in set(seqs[r - 1]) for r in rt_list),
                "crossSrc": nodes[t]["src"] != n["src"],
                "choice": n["choices"][i - 1] if (n["choiceN"] == len(n["next"]) and i - 1 < len(n["choices"])) else None,
            })
        arms[s] = lst

    # 跨路线边（u,v 同属某 lane 但 v 不在该 lane）
    cross_edges = []
    for lane in lanes:
        mem = set(x["id"] for x in lane["nodes"])
        for s in [x["id"] for x in lane["nodes"]]:
            for t in nodes[s]["next"]:
                if t not in mem:
                    cross_edges.append({
                        "lane": lane["rid"], "u": s, "v": t,
                        "crossSrc": nodes[t]["src"] != nodes[s]["src"],
                        "vRoutes": route_of.get(t, []),
                    })

    impact = [s for s in order if nodes[s]["impact"]]
    assert len(impact) == 18, "impact count %d" % len(impact)

    # 分岐点总数（next 项数 ≥ 2）
    branch_all = [s for s in order if len(nodes[s]["next"]) >= 2]
    assert len(branch_all) == 65, "branch count %d" % len(branch_all)

    uniq = set()
    for lane in lanes:
        for x in lane["nodes"]:
            uniq.add(x["id"])
    assert len(uniq) == len(order) == 712, ("unique mismatch", len(uniq), len(order))

    return {
        "rows": rows, "by": by, "nodes": nodes, "order": order, "edges": edges,
        "routes": routes, "seqs": seqs, "lanes": lanes, "arms": arms,
        "cross_edges": cross_edges, "impact": impact, "branch_all": branch_all,
        "route_of": route_of,
    }


# ─────────────────────────── Markdown ───────────────────────────

def gen_md(D):
    nodes = D["nodes"]
    order = D["order"]
    edges = D["edges"]
    lanes = D["lanes"]
    arms = D["arms"]
    impact = D["impact"]
    cross_edges = D["cross_edges"]
    routes = D["routes"]

    L = []
    A = L.append
    A("# 《我们没有翅膀——格雷塔迦露德与柳木原》· 全系列**章节级**剧情流程图")
    A("")
    A("> 模块 `ISSUE-20260920-17` ｜ 构建器 `资源组\\工具\\build_chapter_flow.py`（只读语料、幂等、可复跑）")
    A("> 数据源 `资源组\\05_章节总表.tsv`（712 章） ｜ 本图 **712 个章节节点**（lane 条目合计 %d）、**%d 条 `next` 边**"
      % (sum(len(l["nodes"]) for l in lanes), len(edges)))
    A("")
    A("**与 `07_路线脉络.md` 的关系（口径声明）**")
    A("")
    A("- 本文件是**图视图**（Mermaid 关系图 ＋ 逐路线播放顺序表 ＋ 分岔点表），`07_路线脉络.md` 是**逐章列表视图**。")
    A("- **两者顺序口径完全一致**：lane 划分与 lane 内章节顺序**直接复用 07 的路线定义与播放顺序算法**")
    A("  （`build_chapter_docs.py` 的 `build_routes()`／`play_order()`，即「沿 `next[i]` 走该路线的分岐臂」的")
    A("  分支感知展开：**分支点在前、各臂相邻、汇合点在后**），**不是** `05_章节总表.tsv` 的 `章节序号`")
    A("  （那是逐源 DFS 前序，会跨路线穿插，**不等于播放顺序**）。")
    A("- **数据源同为 `资源组\\05_章节总表.tsv`**；本文件不改动 07/06/05 中的任何内容。")
    A("- 顺序一致性由 `资源组\\工具\\verify_chapter_flow.py` 逐 lane 自动比对（见 §十一）。")
    A("")
    A("---")
    A("")
    A("## 〇、图例、口径与读图说明")
    A("")
    A("### 〇.1 `next` 与「臂」的口径（与 07 §0.1 一致）")
    A("")
    A("| 记号 | 含义 |")
    A("| --- | --- |")
    A("| **节点** | **一个章节**（一脚本 = 一章；`script` 全局唯一，共 712 个） |")
    A("| 实线箭头 `-->` | 章节 `next` 边（**`next` 第 i 项 = 臂 i**） |")
    A("| 虚线箭头 `-.->` | **跨路线**边，指向另一条路线的桩节点（`X_<script>`，桩非章节节点） |")
    A("| **★** 前缀 + 红框 | **`是否影响后续剧情` 非空** 的章节（共 18 件，逐条说明见 §八） |")
    A("| 橙框 | **分岔点**（`next` 项数 ≥ 2，即 N 臂） |")
    A("| 绿框 | 结局 / `next` 为空（终点）的章节 |")
    A("| 蓝框 / 紫框 | 系统·框架章节 / 番外·短剧情·其他章节 |")
    A("")
    A("**「选项 i → `next[i]`」不是通则（本版修正）**：")
    A("`next` 的第 i 项一律记作**「臂 i」**；**只有当该章「选项数 = `next` 项数」时，才可称「选项 i → 臂 i」**。")
    A("")
    A("- 全系列 **50 个含选项章节**中，**32 章**满足「选项数 = `next` 项数」")
    A("  （如 `s01_02c` 2 选项 2 臂、`s01_09c0` 3 选项 3 臂、`s02_10c` 3 选项 3 臂）；")
    A("- 另 **18 章不满足**，即选项与臂**不能一一对应**：")
    A("")
    A("| 章节 | 选项数 | `next` 项数（臂数） | 说明 |")
    A("| --- | ---: | ---: | --- |")
    for s, n, k in UNPAIRED:
        A("| `%s` | %d | %d | 选项数 %s 臂数，配对未确证 |" % (s, n, k, ">" if n > k else "<"))
    A("")
    A("故本文件与 07 一致，**一律按「臂」表述，不臆称「选第 N 项」**。")
    A("")
    A("**关键分岔点的选项数为 0 —— 属脚本级分岐（由前置 flag 决定），不存在「选第几项」**：")
    A("`s01_14g`、`s01_14i`、`s03_08b`、`s04_06j1`、`s04_06k` 等**选项数 = 0**，")
    A("其 `next` 却有多项（2–3 臂）；此类分岔由脚本内的前置 flag 决定走向，**没有选项文本、没有「第几项」**。")
    A("（全系列「`next` 项数 ≥ 2 而选项数 = 0」的分岔点共 27 个。）")
    A("")
    A("### 〇.2 关键分岔点 × 臂（与 `07_路线脉络.md` §0.1 逐条一致）")
    A("")
    A("| 分岔点 | 该章选项数 | 选项文本（中文） | 走的臂 | 该臂入口 | 该臂走向 | 归属路线 |")
    A("| --- | ---: | --- | ---: | --- | --- | --- |")
    for (a, n, b, c, entry, dest, e) in KEY_CHOICE:
        A("| `%s` | %d | %s | %d | `%s` | %s | %s |"
          % (POINT_LABEL.get(a, a), n, esc_md(b), c, entry, dest, e))
    A("")
    A("### 〇.3 读图说明")
    A("")
    A("1. **每张图 = 07 的一条路线（lane）**，lane 顺序与 07 §零 的路线编号 1–19 完全一致。")
    A("2. **lane 内节点顺序 = 沿 `next[i]` 走该路线分岐臂的播放顺序**：分岔点在前、各臂相邻、汇合点在后；")
    A("   收敛分支的两臂之间不会插入无关章节。")
    A("3. **跨路线边**（含全系列唯一**跨源**边 `s03_09a2 → s03c_01a`，以及 `s04_06k → s01_05a`／`s02_10a` 等）")
    A("   **全部保留**，在图上以虚线 + 桩节点表示，并在 lane 末尾「跨路线边」小表与 §九 汇总中显式标注。")
    A("4. **共享章节**：同一章被多条路线播放时，在每条路线中**均完整列出**并标 `〔共用〕`（07 口径）。")
    A("   故 lane 条目合计 **814**，**去重后唯一章节数 = 712**（＝ `05_章节总表.tsv` 的 712 行）。")
    A("5. **节点标签用中文标题**（与 07 的 `《中文》〔日文〕` 对齐）；日文原名以**副标签**给出")
    A("   （md：逐路线播放顺序表的「章节」列与 Mermaid 之外的分岔点表；HTML：节点副标签 + 悬停 + 详情面板）。")
    A("")
    A("### 〇.4 路线总账（与 07 §零 一致）")
    A("")
    A("| # | 路线 | 定位 | 脚本来源 | 列出章数 | 其中独占 | 其中共用 |")
    A("| ---: | --- | --- | --- | ---: | ---: | ---: |")
    for lane in lanes:
        n = len(lane["nodes"])
        sh = sum(1 for x in lane["nodes"] if x["shared"])
        A("| %d | %s | %s | `%s` | %d | %d | %d |"
          % (lane["rid"], esc_md(lane["title"]), esc_md(lane["kind"]), lane["src"], n, n - sh, sh))
    A("| — | **合计（列出行数）** | — | — | **%d** | **712** | **%d** |"
      % (sum(len(l["nodes"]) for l in lanes), sum(len(l["nodes"]) for l in lanes) - 712))
    A("")
    A("---")
    A("")
    A("## 一、跨作品总览")
    A("")
    A("```mermaid")
    A(OVERVIEW_MERMAID.rstrip())
    A("```")
    A("")
    A("> 实线＝TSV 中真实存在的 `next` 边；虚线＝时序或既有文档记载、**TSV 中无对应 `next` 边**的衔接（见 §九）。")
    A("")
    A("| 作品 | 源代号 | 章数 | 主线定位 |")
    A("| --- | --- | ---: | --- |")
    for src in ("otp", "ot", "otr", "otv", "ota", "np"):
        cnt = sum(1 for s in order if nodes[s]["src"] == src)
        A("| %s | `%s` | %d | %s |" % (B.SRC_NAME[src], src, cnt, WORK_POS.get(src, "")))
    A("")
    A("---")
    A("")

    # 逐路线
    cn_no = "二三四五六七八九十"
    for si, (sec_title, rids) in enumerate(SECTIONS):
        A("## %s、%s" % (cn_no[si], sec_title))
        A("")
        cnt = sum(len(lanes[r - 1]["nodes"]) for r in rids)
        A("**合计 %d 章（lane 条目）**。本组含 07 路线 %s。"
          % (cnt, "、".join("(%d)%s" % (r, lanes[r - 1]["title"]) for r in rids)))
        A("")
        for r in rids:
            lane = lanes[r - 1]
            lst = [x["id"] for x in lane["nodes"]]
            mem = set(lst)
            shn = sum(1 for x in lane["nodes"] if x["shared"])
            A("### (%d) %s · `%s`（列出 %d 章：独占 %d ＋ 共用 %d）"
              % (lane["rid"], esc_md(lane["title"]), lane["src"], len(lst), len(lst) - shn, shn))
            A("")
            A("- **定位**：%s" % lane["note"])
            A("- **选择支路径（本线走的臂）**：%s" % lane["path"])
            A("- **顺序依据**：沿 `next[i]` 走该路线分岐臂（与 `07_路线脉络.md` §(%d) 逐章一致）" % lane["rid"])
            A("")
            # Mermaid 图（节点声明顺序 = 播放顺序）
            A("```mermaid")
            A("flowchart TD")
            A(CLASS_DEFS.rstrip())
            for s in lst:
                n = nodes[s]
                star = "★ " if n["impact"] else ""
                share = "〔共用〕" if s in mem and nodes[s] and any(
                    x["id"] == s and x["shared"] for x in lane["nodes"]) else ""
                lbl = "%s%s · %s%s" % (star, s, mlabel(short_title(n)), share)
                A('    n_%s["%s"]:::%s' % (s, lbl, node_class(n)))
            stubs = []
            for s in lst:
                n = nodes[s]
                for i, t in enumerate(n["next"], 1):
                    if t in mem:
                        if len(n["next"]) > 1:
                            A('    n_%s -->|"臂 %d"| n_%s' % (s, i, t))
                        else:
                            A("    n_%s --> n_%s" % (s, t))
                    else:
                        stub = "X_" + t
                        if stub not in stubs:
                            stubs.append(stub)
                            tl = "／".join("(%d)%s" % (rr, routes[rr - 1]["title"])
                                           for rr in D["route_of"].get(t, [])) or "（未裁决）"
                            A('    %s["↷ %s（转 %s）"]:::cross' % (stub, t, mlabel(tl)))
                        arm = ("臂 %d " % i) if len(n["next"]) > 1 else ""
                        A('    n_%s -.->|"%s跨路线"| %s' % (s, arm, stub))
            A("```")
            A("")
            # 逐路线播放顺序表（顺序口径的可读视图）
            A("**播放顺序（与 `07_路线脉络.md` §(%d) 逐章一致）**" % lane["rid"])
            A("")
            A("| 序 | script | 章节《中文》〔日文〕 | 选项数 | 臂数 | 备注 |")
            A("| ---: | --- | --- | ---: | ---: | --- |")
            for k, s in enumerate(lst, 1):
                n = nodes[s]
                jp = n["jp"] or "（无标题）"
                cn = n["cn"] or "（无标题）"
                body = "《%s》" % esc_md(cn)
                if jp != cn:
                    body += "〔%s〕" % esc_md(jp)
                note = []
                x = next((y for y in lane["nodes"] if y["id"] == s), None)
                if x and x["shared"]:
                    note.append("〔共用〕")
                if n["impact"]:
                    note.append("★影响后续剧情")
                if len(n["next"]) >= 2:
                    note.append("分岔点（%d 臂）" % len(n["next"]))
                elif n["next_kind"] == "end":
                    note.append("终点")
                A("| %d | `%s` | %s | %d | %d | %s |"
                  % (k, s, body, n["choiceN"], len(n["next"]), " ".join(note)))
            A("")
            # 本 lane 的分岔点与臂
            br = [s for s in lst if len(nodes[s]["next"]) >= 2]
            if br:
                A("**本 lane 分岔点（%d 个）与各臂**" % len(br))
                A("")
                A("| 分岔点 | 标题 | 选项数 | 臂 | 该臂入口 | 该臂归属路线 | 跨路线 |")
                A("| --- | --- | ---: | ---: | --- | --- | :---: |")
                for s in br:
                    n = nodes[s]
                    for a in arms[s]:
                        A("| `%s` | %s | %d | %d | `%s` | %s | %s |"
                          % (s, esc_md(short_title(n, 30)), n["choiceN"], a["i"], a["target"],
                             a["routeLabel"],
                             ("跨源" if a["crossSrc"] else ("跨路线" if a["crossRoute"] else ""))))
                A("")
            # 本 lane 的跨路线边
            ce = [c for c in cross_edges if c["lane"] == lane["rid"]]
            if ce:
                A("**本 lane 跨路线边（%d 条，图上以虚线 + 桩节点显式标注）**" % len(ce))
                A("")
                A("| 源章节 | 目标章节 | 目标归属路线 | 类型 |")
                A("| --- | --- | --- | --- |")
                for c in ce:
                    tl = "／".join("(%d)%s" % (rr, routes[rr - 1]["title"]) for rr in c["vRoutes"]) or "（未裁决）"
                    A("| `%s` | `%s` | %s | %s |" % (c["u"], c["v"], tl, "**跨源**" if c["crossSrc"] else "跨路线"))
                A("")

    # §八
    A("---")
    A("")
    A("## 八、18 件「影响后续剧情」逐条说明")
    A("")
    A("以下 18 章在 `05_章节总表.tsv` 的 `是否影响后续剧情` 列非空，图上均以 **★ 前缀 + 红框** 显式标注。")
    A("")
    for i, s in enumerate(impact, 1):
        n = nodes[s]
        rts = D["route_of"].get(s, [])
        A("### %d. `%s`（%s · %s）" % (i, s, n["work"], n["route"] or "（未裁决）"))
        A("")
        A("- **标题**：%s%s" % (n["cn"] or "（无中文标题）", ("／" + n["jp"]) if n["jp"] and n["jp"] != n["cn"] else ""))
        A("- **章节作用**：%s ｜ **phase**：%s ｜ **选项数**：%d ｜ **臂数**：%d"
          % (n["role"], n["phase"] or "（空）", n["choiceN"], len(n["next"])))
        A("- **出现于路线**：%s" % ("、".join("(%d)%s" % (r, routes[r - 1]["title"]) for r in rts) or "（未裁决）"))
        A("- **各臂**：%s" % (" ；".join("臂 %d → `%s`" % (i2, t) for i2, t in enumerate(n["next"], 1))
                              if n["next"] else "（无后继，`end`）"))
        A("- **影响说明**：%s" % IMPACT_NOTE.get(s, "（说明待补）"))
        A("")
    A("**合计：%d 件。**" % len(impact))
    A("")

    # §九
    A("---")
    A("")
    A("## 九、跨作品衔接与跨路线 / 跨源边")
    A("")
    A("### 9.1 跨作品衔接")
    A("")
    A("| 上游 | 下游 | 依据类型 | 说明 |")
    A("| --- | --- | --- | --- |")
    for a, b, t, d in LINKAGE:
        A("| %s | %s | %s | %s |" % (a, b, t, d))
    A("")
    A("### 9.2 全部跨路线边（含跨源）")
    A("")
    A("**共 %d 条**（按 07 的路线口径统计；其中**跨源** %d 条），图上均以虚线 + 桩节点显式标注。"
      % (len(cross_edges), sum(1 for c in cross_edges if c["crossSrc"])))
    A("")
    A("| # | 所属 lane | 源章节 | 目标章节 | 目标归属路线 | 类型 |")
    A("| ---: | --- | --- | --- | --- | --- |")
    for i, c in enumerate(cross_edges, 1):
        lane = lanes[c["lane"] - 1]
        tl = "／".join("(%d)%s" % (rr, routes[rr - 1]["title"]) for rr in c["vRoutes"]) or "（未裁决）"
        A("| %d | (%d)%s | `%s` | `%s` | %s | %s |"
          % (i, c["lane"], esc_md(lane["title"]), c["u"], c["v"], tl,
             "**跨源**" if c["crossSrc"] else "跨路线"))
    A("")
    A("> **全系列唯一跨源边**：`s03_09a2 → s03c_01a`（`ot` → `otr`，R 版亚衣线正式入口）。")
    A("> 其余为同源跨路线边（`s01→s02`／`s02→s03`／`s03→s04`／`s04→s01,s02,s03` 等），")
    A("> 与 `章节提取说明.md` §3.3 的 13 条跨源/跨路线边口径一致（本表按 07 的 lane 口径展开）。")
    A("")

    # §十
    A("---")
    A("")
    A("## 十、待判定与已知缺口（不臆断）")
    A("")
    A("| # | 项 | 现状 | 缺什么 |")
    A("| ---: | --- | --- | --- |")
    A("| 1 | 实机「章节」是否把无标题续章片段并入上一章 | 本图按「一脚本 = 一章」＝ 712 章 | 实机逐章跳转录屏（`章节提取说明` §2、§6.2-1） |")
    A("| 2 | `choices[].target` 的选项↔目标配对 | 仅 `np` 34 条 `pairing_verified=true`；`otp` 7 条 target 非空但 false；其余 115 条 null；50 章中 18 章选项数 ≠ 臂数 | TOB0/SOB0/BGI 分支语义未逆向 |")
    A("| 3 | 前奏诗在剧情内的时序 | 按 `otp` 自身 `next` 链排列 | 语料内无「相对正传」的时点声明 |")
    A("| 4 | 伏笔穷举清单 | 本表只登记 2 条已逐字核实者（`s01_09d`／`s04_25b`） | 需人工通读全语料 |")
    A("| 5 | `ota` 22_*/23_* 线路归属 | `route=null`（D13 待裁决），07 归入 (11)AfterStory 番外 | D13 用户裁决 |")
    A("| 6 | `np` 的 `a05_d0`/`a05_e0` 后继 | `next=[]` 但语义上非终点 | 源侧复核 |")
    A("| 7 | `ota_24_5a` 三条选项源值均为 `ヨージ` | 疑源提取缺陷，如实保留 | 源侧复核 |")
    A("")
    A("---")
    A("")
    A("## 十一、顺序一致性校验（与 07 对账）")
    A("")
    A("```bash")
    A('cd "E:/ZCode Workspace/Galgame"')
    A('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/verify_chapter_flow.py"')
    A("```")
    A("")
    A("校验内容：节点守恒（712）、逐 lane 顺序与 07 一致（不一致数 = 0）、分岔点与臂与 07 §0.1 一致、")
    A("18 件影响后续剧情标注齐全、HTML 自包含、md 与 html 同源一致、生成器幂等。")
    A("")
    A("---")
    A("")
    A("## 附：复现命令（幂等）")
    A("")
    A("```bash")
    A('cd "E:/ZCode Workspace/Galgame"')
    A('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_chapter_flow.py"')
    A("```")
    A("")
    return "\n".join(L) + "\n"


# ─────────────────────────── HTML ───────────────────────────

def gen_html(D):
    nodes = D["nodes"]
    order = D["order"]
    lanes = D["lanes"]
    routes = D["routes"]
    data = {
        "meta": {
            "total": len(order),
            "listed": sum(len(l["nodes"]) for l in lanes),
            "edges": len(D["edges"]),
            "cross": len(D["cross_edges"]),
            "crossSrc": sum(1 for c in D["cross_edges"] if c["crossSrc"]),
            "impact": len(D["impact"]),
            "branch": len(D["branch_all"]),
            "unpaired": len(UNPAIRED),
            "paired": 32,
            "choiceChapters": 50,
        },
        "sections": [
            {"title": t, "lanes": [
                {"rid": lanes[r - 1]["rid"], "title": lanes[r - 1]["title"],
                 "kind": lanes[r - 1]["kind"], "src": lanes[r - 1]["src"],
                 "note": lanes[r - 1]["note"], "path": lanes[r - 1]["path"],
                 "nodes": lanes[r - 1]["nodes"]}
                for r in rids]}
            for (t, rids) in SECTIONS
        ],
        "routes": [{"rid": rt["rid"], "title": rt["title"], "src": rt["src"]} for rt in routes],
        "nodes": {s: {k: nodes[s][k] for k in (
            "script", "src", "work", "seq", "jp", "cn", "phase", "route", "kind",
            "lines", "next", "next_kind", "choiceN", "choices", "date", "cast",
            "role", "impact", "spine", "remark")} for s in order},
        "arms": D["arms"],
        "crossEdges": D["cross_edges"],
        "impactList": D["impact"],
        "impactNote": IMPACT_NOTE,
        "linkage": LINKAGE,
        "workPos": WORK_POS,
        "keyChoice": [{"point": POINT_LABEL.get(a, a), "choiceN": n, "choices": b, "arm": c,
                       "entry": e, "dest": d, "route": f} for (a, n, b, c, e, d, f) in KEY_CHOICE],
        "unpaired": [{"script": s, "choiceN": n, "arms": k} for (s, n, k) in UNPAIRED],
        "srcName": B.SRC_NAME,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return HTML_TEMPLATE.replace("__PAYLOAD__", payload)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>我们没有翅膀——格雷塔迦露德与柳木原 · 全系列章节流程图</title>
<style>
:root{
  --bg:#0e1116;--bg2:#151a22;--bg3:#1c232e;--line:#2b3543;
  --fg:#dde4ee;--fg2:#8fa0b6;--fg3:#5d6b7d;
  --imp:#ff6b6b;--branch:#ffb347;--end:#4ade80;--sys:#4ea3ff;--side:#b07cff;
  --accent:#ffd166;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);
  font-family:"Microsoft YaHei","微软雅黑","PingFang SC","Hiragino Sans GB",sans-serif;
  font-size:14px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
header{padding:22px 28px 14px;border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,#171d27 0%,#0e1116 100%)}
h1{font-size:21px;font-weight:600}
h1 .sub{color:var(--fg2);font-size:13px;font-weight:400;margin-left:8px}
.meta{margin-top:7px;color:var(--fg3);font-size:12.5px}
.meta b{color:var(--fg2);font-weight:500}
nav{display:flex;gap:2px;padding:0 28px;border-bottom:1px solid var(--line);
  background:var(--bg2);position:sticky;top:0;z-index:50;overflow-x:auto}
nav button{background:none;border:none;border-bottom:2px solid transparent;color:var(--fg2);
  padding:12px 16px;font-size:13.5px;cursor:pointer;font-family:inherit;white-space:nowrap}
nav button:hover{color:var(--fg);background:#1a212b}
nav button.on{color:var(--accent);border-bottom-color:var(--accent);background:#1a212b}
main{padding:22px 28px 90px;max-width:1620px}
section{display:none}
section.on{display:block}
h2{font-size:16px;margin:20px 0 10px;padding-left:10px;border-left:3px solid var(--accent)}
h2:first-child{margin-top:0}
h3{font-size:14px;margin:16px 0 8px;color:var(--accent)}
p{margin:7px 0;color:var(--fg2)}
.note{background:#1a212b;border:1px solid var(--line);border-left:3px solid var(--branch);
  padding:10px 14px;border-radius:4px;margin:10px 0;font-size:13px;color:var(--fg2)}
.note b{color:var(--fg)}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 16px}
.legend span{font-size:12.5px;padding:3px 10px;border-radius:20px;border:1px solid var(--line);background:var(--bg2)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
.tools{display:flex;gap:10px;align-items:center;margin:12px 0;flex-wrap:wrap}
.tools input{background:#0b0f14;border:1px solid var(--line);color:var(--fg);
  padding:7px 12px;border-radius:5px;font-family:inherit;font-size:13px;min-width:260px}
.tools .cnt{color:var(--fg3);font-size:12.5px}
.lane{background:var(--bg2);border:1px solid var(--line);border-radius:7px;margin:14px 0;overflow:hidden}
.lane>h3{margin:0;padding:11px 15px;background:var(--bg3);border-bottom:1px solid var(--line);
  color:var(--fg);font-size:13.5px}
.lane>h3 b{color:var(--accent)}
.lane .laneinfo{padding:10px 16px 0;font-size:12.5px;color:var(--fg2)}
.lane .laneinfo .k{color:var(--fg3)}
.lanebody{padding:10px 16px 18px}
.flow{position:relative;padding-left:6px}
.node{position:relative;display:flex;align-items:flex-start;gap:10px;
  border:1px solid var(--line);background:var(--bg3);border-radius:6px;
  padding:8px 11px;margin:0 0 0 20px;cursor:pointer;transition:.12s}
.node:hover{border-color:var(--accent);transform:translateX(2px)}
.node::before{content:"";position:absolute;left:-14px;top:50%;width:14px;height:1px;background:var(--line)}
.node.first::before{display:none}
.conn{height:16px;margin-left:20px;border-left:2px solid var(--line);position:relative}
.conn::after{content:"";position:absolute;left:-5px;bottom:0;border:4px solid transparent;border-top-color:var(--line)}
.node .seq{color:var(--fg3);font-size:11.5px;min-width:44px;padding-top:2px}
.node .body{flex:1;min-width:0}
.node .scr{font-family:Consolas,Menlo,monospace;font-size:12.5px;color:#9fd3ff}
.node .ttl{color:var(--fg);font-size:13px;margin-top:1px}
.node .jp{color:var(--fg3);font-size:11.5px;margin-top:1px}
.badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}
.bdg{font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);color:var(--fg2)}
.bdg.imp{color:#ffd7d7;border-color:var(--imp);background:#3a1620}
.bdg.br{color:#ffe9c2;border-color:var(--branch);background:#3a2f14}
.bdg.en{color:#d6ffe4;border-color:var(--end);background:#12331f}
.bdg.sy{color:#cfe6ff;border-color:var(--sys);background:#1a2330}
.bdg.sd{color:#e9dcff;border-color:var(--side);background:#241a30}
.bdg.sh{color:#cfe6ff;border-color:#3f6b8f;background:#16222e}
.node.imp{border-color:var(--imp);background:#2a1219}
.node.end{border-color:#2c5a3d}
.node.br{border-color:#6b5320}
.arms{margin:6px 0 0 20px;border-left:2px dashed #3a4657;padding-left:12px}
.arm{font-size:12.5px;color:var(--fg2);margin:3px 0}
.arm .o{color:var(--branch)}
.arm .rt{color:#c9a4ff}
.arm a{font-family:Consolas,Menlo,monospace;color:#9fd3ff}
.arm .warn{color:var(--fg3);font-size:11.5px}
.crossbox{margin:6px 0 0 20px;font-size:12.5px;color:var(--side)}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:12.5px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--bg3);color:var(--fg2);font-weight:500}
td code,.mono{font-family:Consolas,Menlo,monospace;color:#9fd3ff}
tr:hover td{background:#161c25}
.impcard{background:var(--bg2);border:1px solid var(--line);border-left:3px solid var(--imp);
  border-radius:6px;padding:12px 15px;margin:10px 0}
.impcard h4{font-size:13.5px;color:var(--fg);margin-bottom:5px}
.impcard .l{color:var(--fg2);font-size:12.8px;margin:3px 0}
.impcard .l b{color:var(--fg3);font-weight:500;margin-right:5px}
#detail{position:fixed;top:0;right:0;width:430px;max-width:92vw;height:100%;
  background:#12171f;border-left:1px solid var(--line);transform:translateX(100%);
  transition:.22s;z-index:200;overflow-y:auto;padding:20px 20px 60px;box-shadow:-14px 0 40px rgba(0,0,0,.5)}
#detail.on{transform:none}
#detail h3{color:var(--accent);margin-top:0}
#detail .close{position:absolute;top:14px;right:16px;cursor:pointer;color:var(--fg2);font-size:20px;line-height:1}
#detail dl{margin-top:10px}
#detail dt{color:var(--fg3);font-size:12px;margin-top:9px}
#detail dd{color:var(--fg);font-size:13px;word-break:break-word}
#detail .k{font-family:Consolas,Menlo,monospace;color:#9fd3ff}
#scrim{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;z-index:190}
#scrim.on{display:block}
mark{background:#5a4a12;color:#ffe9c2;border-radius:2px}
</style>
</head>
<body>
<header>
  <h1>我们没有翅膀——格雷塔迦露德与柳木原<span class="sub">全系列章节流程图（章节级 · 图视图）</span></h1>
  <div class="meta">模块 <b>ISSUE-20260920-17</b> ｜ 数据源 <b>05_章节总表.tsv</b> ｜ 顺序口径 <b>与 07_路线脉络.md 一致（沿 next[i] 的分岐臂）</b> ｜ 章节节点 <b id="m-total"></b> ｜ lane 条目 <b id="m-listed"></b> ｜ next 边 <b id="m-edges"></b> ｜ 跨路线边 <b id="m-cross"></b> ｜ 影响后续剧情 <b id="m-impact"></b></div>
</header>
<nav id="nav"></nav>
<main id="main"></main>
<div id="scrim"></div>
<aside id="detail"><span class="close" onclick="closeDetail()">×</span><div id="detailBody"></div></aside>
<script>
const DATA = __PAYLOAD__;
const N = DATA.nodes;
const M = DATA.meta;
const BADGE = {
  imp:['★ 影响后续剧情','imp'],
  end:['● 结局/终点','en'],
  branch:['◇ 分岔点','br'],
  sys:['◈ 系统/框架','sy'],
  side:['◇ 番外/短剧情','sd']
};
function clsOf(n){
  if(n.impact) return 'imp';
  if(n.role.startsWith('结局')||n.next_kind==='end') return 'end';
  if(n.next.length>=2) return 'branch';
  if(n.role==='系统'||n.role==='框架') return 'sys';
  if(n.role==='番外'||n.role==='短剧情'||n.role==='其他') return 'side';
  return 'norm';
}
function titleOf(n){return n.cn||n.jp||'（无标题）';}
function jpOf(n){return n.jp||'';}
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function routeName(rid){const r=DATA.routes.find(x=>x.rid===rid);return r?('('+r.rid+')'+r.title):('('+rid+')');}

/* ── 导航 ── */
const TABS = [{id:'overview',label:'总览与口径'}]
  .concat(DATA.sections.map((s,i)=>({id:'sec'+i,label:s.title.split('（')[0].replace('· ','')})))
  .concat([{id:'branch',label:'分岔点 × 臂'},{id:'impact',label:'影响后续剧情 18'},
           {id:'cross',label:'跨路线 / 跨源边'},{id:'check',label:'与 07 对账'}]);
const nav=document.getElementById('nav');
TABS.forEach((t)=>{
  const b=document.createElement('button');
  b.textContent=t.label; b.dataset.tab=t.id;
  b.onclick=()=>show(t.id);
  nav.appendChild(b);
});
function show(id){
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.tab===id));
  document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id==='tab-'+id));
  window.scrollTo({top:0});
}
const main=document.getElementById('main');
function sec(id){
  const s=document.createElement('section'); s.id='tab-'+id; main.appendChild(s); return s;
}

/* ── 总览与口径 ── */
(function(){
  const s=sec('overview');
  s.innerHTML =
    '<h2>总览 · 六作品 / 712 章 · 19 条路线</h2>'+
    '<div class="legend">'+
      '<span><i class="dot" style="background:#ff6b6b"></i>★ 影响后续剧情</span>'+
      '<span><i class="dot" style="background:#ffb347"></i>◇ 分岔点</span>'+
      '<span><i class="dot" style="background:#4ade80"></i>● 结局/终点</span>'+
      '<span><i class="dot" style="background:#4ea3ff"></i>◈ 系统/框架</span>'+
      '<span><i class="dot" style="background:#b07cff"></i>◇ 番外/短剧情</span>'+
    '</div>'+
    '<div class="note"><b>与 07_路线脉络.md 的关系</b>：本页是<b>图视图</b>，07 是<b>逐章列表视图</b>；'+
      '两者<b>顺序口径完全一致</b>——lane 划分与 lane 内章节顺序<b>直接复用 07 的路线定义与播放顺序算法</b>'+
      '（沿 <code>next[i]</code> 走该路线的分岐臂：<b>分岔点在前、各臂相邻、汇合点在后</b>），'+
      '而不是 TSV 的 <code>章节序号</code>（逐源 DFS 前序，会跨路线穿插）。数据源同为 <b>05_章节总表.tsv</b>。</div>'+
    '<div class="note"><b>「臂」口径（修正）</b>：<code>next</code> 的第 i 项一律记作「<b>臂 i</b>」；'+
      '<b>只有当该章「选项数 = next 项数」时，才可称「选项 i → 臂 i」</b>。'+
      '全系列 '+M.choiceChapters+' 个含选项章节中 <b>'+M.paired+' 章</b>满足、<b>'+M.unpaired+' 章不满足</b>（见「分岔点 × 臂」页）。'+
      '关键分岔点 <code>s01_14g</code>／<code>s01_14i</code>／<code>s03_08b</code>／<code>s04_06j1</code>／<code>s04_06k</code> 的<b>选项数 = 0</b>，'+
      '属<b>脚本级分岐（由前置 flag 决定）</b>，不存在「选第几项」。</div>'+
    '<div class="note">节点标签用<b>中文标题</b>（主标签），日文原名以<b>副标签</b>给出；点击任一节点可查看标题、作用、选项、各臂与是否影响后续剧情。'+
      '共享章节在每条路线中均完整列出并标 <b>〔共用〕</b>（与 07 一致）：lane 条目合计 <b>'+M.listed+'</b>，去重后唯一章节数 <b>'+M.total+'</b>。</div>'+
    '<table><thead><tr><th>组</th><th>路线（lane）</th><th>列出章数</th></tr></thead><tbody>'+
    DATA.sections.map((x,i)=>'<tr><td>'+esc(x.title)+'</td><td>'+
        x.lanes.map(l=>'<a href="#" onclick="goLane('+l.rid+');return false">('+l.rid+')'+esc(l.title)+' ('+l.nodes.length+')</a>').join(' ｜ ')+
        '</td><td>'+x.lanes.reduce((a,l)=>a+l.nodes.length,0)+'</td></tr>').join('')+
    '</tbody></table>'+
    '<h3>跨作品衔接</h3><div class="note">实线＝TSV 中真实存在的 next 边；虚线＝时序/文档衔接（TSV 无 next 边）。'+
      '<table><thead><tr><th>上游</th><th>下游</th><th>依据类型</th><th>说明</th></tr></thead><tbody>'+
    DATA.linkage.map(r=>'<tr><td>'+esc(r[0])+'</td><td>'+esc(r[1])+'</td><td>'+esc(r[2])+'</td><td>'+esc(r[3])+'</td></tr>').join('')+
    '</tbody></table></div>';
})();

/* ── 逐组 / 逐路线 ── */
DATA.sections.forEach((sx,si)=>{
  const s=sec('sec'+si);
  const head=document.createElement('div');
  head.innerHTML='<h2>'+esc(sx.title)+'</h2><div class="note">本组含 '+sx.lanes.length+' 条路线，合计 <b>'+
    sx.lanes.reduce((a,l)=>a+l.nodes.length,0)+'</b> 章（lane 条目）。lane 内顺序＝沿 next[i] 的分岐臂播放顺序，与 07 对应节逐章一致。</div>'+
    '<div class="tools"><input placeholder="搜索 脚本名 / 中文标题 / 日文标题 …" oninput="filterLane(this)"><span class="cnt"></span></div>';
  s.appendChild(head);
  sx.lanes.forEach(l=>{
    const box=document.createElement('div'); box.className='lane';
    box.dataset.lane='lane-'+l.rid;
    const shn=l.nodes.filter(x=>x.shared).length;
    const h=document.createElement('h3');
    h.innerHTML='('+l.rid+') '+esc(l.title)+' · <b>'+l.nodes.length+'</b> 章（独占 '+(l.nodes.length-shn)+' ＋ 共用 '+shn+'）'+
      ' <span class="mono" style="color:#5d6b7d">'+esc(l.src)+'</span>';
    box.appendChild(h);
    const info=document.createElement('div'); info.className='laneinfo';
    info.innerHTML='<div><span class="k">定位</span> '+esc(l.note)+'</div>'+
      '<div><span class="k">选择支路径（本线走的臂）</span> '+esc(l.path).replace(/`/g,'')+'</div>';
    box.appendChild(info);
    const body=document.createElement('div'); body.className='lanebody';
    const flow=document.createElement('div'); flow.className='flow';
    l.nodes.forEach((item,i)=>{
      const id=item.id, n=N[id];
      if(i>0){const c=document.createElement('div');c.className='conn';flow.appendChild(c);}
      const d=document.createElement('div');
      d.className='node '+(i===0?'first ':'')+clsOf(n);
      d.dataset.script=id;
      d.dataset.lane='lane-'+l.rid;
      d.dataset.q=(id+' '+titleOf(n)+' '+jpOf(n)).toLowerCase();
      let badges='<div class="badges">';
      const cl=clsOf(n);
      if(BADGE[cl]) badges+='<span class="bdg '+BADGE[cl][1]+'">'+BADGE[cl][0]+'</span>';
      if(item.shared) badges+='<span class="bdg sh">〔共用〕</span>';
      if(n.choiceN>0) badges+='<span class="bdg">选项 '+n.choiceN+'</span>';
      if(n.next.length>1) badges+='<span class="bdg">'+n.next.length+' 臂</span>';
      badges+='</div>';
      let arms='';
      if(n.next.length>1){
        const A=DATA.arms[id]||[];
        arms='<div class="arms">';
        A.forEach(a=>{
          let opt;
          if(a.choice!=null) opt='<span class="o">选项 '+a.i+'：'+esc(a.choice)+'</span> → ';
          else if(n.choiceN===0) opt='<span class="warn">臂 '+a.i+'（脚本级分岐，无选项文本）</span> → ';
          else opt='<span class="warn">臂 '+a.i+'（选项数 '+n.choiceN+' ≠ 臂数 '+n.next.length+'，配对未确证）</span> → ';
          arms+='<div class="arm">'+opt+'<a href="#" onclick="jump(\''+a.target+'\',\''+l.rid+'\');return false">'+a.target+'</a> '+
            (N[a.target]?esc(titleOf(N[a.target])):'')+
            ' <span class="rt">［'+esc(a.routeLabel)+(a.crossSrc?' · 跨源':(a.crossRoute?' · 跨路线':''))+'］</span></div>';
        });
        arms+='</div>';
      }
      const xt=DATA.crossEdges.filter(c=>c.u===id&&c.lane===l.rid);
      let crossbox='';
      if(xt.length){
        crossbox='<div class="crossbox">↷ 跨'+(xt.some(c=>c.crossSrc)?'源':'路线')+'边（本图以虚线 + 桩节点显式标注）：'+
          xt.map(c=>'<a href="#" onclick="jump(\''+c.v+'\','+((c.vRoutes[0])||0)+');return false">'+c.v+'</a>（'+esc(N[c.v].route||'未裁决')+'）').join('，')+'</div>';
      }
      const inc=DATA.crossEdges.filter(c=>c.v===id&&c.lane!==l.rid);
      let inbox='';
      if(inc.length){
        inbox='<div class="crossbox">↳ 入口（自其他路线汇入）：'+
          inc.map(c=>'<a href="#" onclick="jump(\''+c.u+'\','+c.lane+');return false">'+c.u+'</a>（'+routeName(c.lane)+'）').join('，')+'</div>';
      }
      d.innerHTML='<div class="seq">序 '+i+'</div><div class="body"><div class="scr">'+id+'</div>'+
        '<div class="ttl">《'+esc(titleOf(n))+'》</div>'+
        (jpOf(n)&&jpOf(n)!==titleOf(n)?'<div class="jp">〔'+esc(jpOf(n))+'〕</div>':'')+
        badges+'</div>';
      d.title=id+' 《'+titleOf(n)+'》'+(jpOf(n)?'〔'+jpOf(n)+'〕':'');
      d.onclick=(e)=>{ if(e.target.tagName!=='A') openDetail(id,l.rid); };
      flow.appendChild(d);
      if(arms){const w=document.createElement('div');w.innerHTML=arms;flow.appendChild(w.firstChild);}
      if(crossbox){const w=document.createElement('div');w.innerHTML=crossbox;flow.appendChild(w.firstChild);}
      if(inbox){const w=document.createElement('div');w.innerHTML=inbox;flow.appendChild(w.firstChild);}
    });
    body.appendChild(flow);
    box.appendChild(body);
    s.appendChild(box);
  });
});

/* ── 分岔点 × 臂 ── */
(function(){
  const s=sec('branch');
  const byPt={};
  DATA.keyChoice.forEach(r=>{(byPt[r.point]=byPt[r.point]||[]).push(r);});
  s.innerHTML='<h2>分岔点 × 臂（与 07 §0.1 逐条一致）</h2>'+
    '<div class="note"><b>「选项 i → next[i]」的配对可信度</b>：仅当该章<b>选项数 = next 项数</b>时成立——'+
    '全系列 '+M.choiceChapters+' 个含选项章节中 <b>'+M.paired+' 章</b>满足，另 <b>'+M.unpaired+' 章不满足</b>。'+
    '故一律以「臂」表述；<b>未确证处不臆称「选第 N 项」</b>。分岔点若无选项文本，则为<b>脚本级分岐（由前置 flag 决定）</b>。</div>'+
    '<h3>1. 07 §0.1 的 7 个关键分岔点 / '+DATA.keyChoice.length+' 行</h3>'+
    '<table><thead><tr><th>分岔点</th><th>该章选项数</th><th>选项文本（中文）</th><th>走的臂</th><th>该臂入口</th><th>该臂走向</th><th>归属路线</th></tr></thead><tbody>'+
    DATA.keyChoice.map(r=>'<tr><td><code>'+r.point+'</code></td><td>'+r.choiceN+'</td><td>'+esc(r.choices)+'</td><td>'+r.arm+
      '</td><td><code>'+r.entry+'</code></td><td>'+esc(r.dest).replace(/`/g,'')+'</td><td>'+esc(r.route)+'</td></tr>').join('')+
    '</tbody></table>'+
    '<h3>2. 「选项数 ≠ next 项数」的 '+M.unpaired+' 章（不能称「选项 i → 臂 i」）</h3>'+
    '<table><thead><tr><th>章节</th><th>选项数</th><th>next 项数（臂数）</th></tr></thead><tbody>'+
    DATA.unpaired.map(r=>'<tr><td><code>'+r.script+'</code></td><td>'+r.choiceN+'</td><td>'+r.arms+'</td></tr>').join('')+
    '</tbody></table>'+
    '<div class="note">图上「<b>分岔点</b>」= <code>next</code> 项数 ≥ 2 的章节，全系列共 <b>'+M.branch+'</b> 个；'+
    '其中<b>选项数 = 0</b> 者 '+27+' 个，属脚本级分岐（无选项文本、无「第几项」）。</div>';
})();

/* ── 影响清单 ── */
(function(){
  const s=sec('impact');
  s.innerHTML='<h2>18 件「影响后续剧情」章节</h2><div class="note">以下章节在 05_章节总表.tsv 的「是否影响后续剧情」列非空，图上均以 <b>★ 前缀 + 红框</b> 显式标注。</div>'+
    DATA.impactList.map((id,i)=>{
      const n=N[id];
      const A=DATA.arms[id]||[];
      return '<div class="impcard"><h4>'+(i+1)+'. <span class="mono">'+id+'</span> · 《'+esc(titleOf(n))+'》 <span style="color:#5d6b7d;font-size:12px">（'+esc(n.work)+' · '+esc(n.route||'未裁决')+'）</span></h4>'+
        '<div class="l"><b>章节作用</b>'+esc(n.role)+' ｜ <b>phase</b>'+esc(n.phase||'（空）')+' ｜ <b>选项数</b>'+n.choiceN+' ｜ <b>臂数</b>'+n.next.length+'</div>'+
        '<div class="l"><b>各臂</b>'+(n.next.length?n.next.map((t,k)=>'<a href="#" onclick="jump(\''+t+'\',0);return false"><code>臂 '+(k+1)+' → '+t+'</code></a>').join(' ；'):'（无后继，end）')+'</div>'+
        '<div class="l"><b>影响说明</b>'+esc(DATA.impactNote[id]||'（待补）').replace(/\*\*/g,'')+'</div></div>';
    }).join('')+
    '<div class="note">合计 <b>'+DATA.impactList.length+'</b> 件。</div>';
})();

/* ── 跨路线 / 跨源边 ── */
(function(){
  const s=sec('cross');
  s.innerHTML='<h2>跨路线 / 跨源边（'+DATA.crossEdges.length+' 条）</h2>'+
    '<div class="note">按 07 的路线口径统计；其中<b>跨源</b> '+M.crossSrc+' 条（全系列唯一跨源边：<code>s03_09a2 → s03c_01a</code>，'+
    '<code>ot</code> → <code>otr</code>，R 版亚衣线正式入口）。图上均以<b>虚线 + 桩节点</b>显式标注。</div>'+
    '<table><thead><tr><th>#</th><th>所属 lane</th><th>源章节</th><th>目标章节</th><th>目标归属路线</th><th>类型</th></tr></thead><tbody>'+
    DATA.crossEdges.map((c,i)=>'<tr><td>'+(i+1)+'</td><td>'+routeName(c.lane)+'</td>'+
      '<td><a href="#" onclick="jump(\''+c.u+'\','+c.lane+');return false"><code>'+c.u+'</code></a></td>'+
      '<td><a href="#" onclick="jump(\''+c.v+'\','+((c.vRoutes[0])||0)+');return false"><code>'+c.v+'</code></a></td>'+
      '<td>'+(c.vRoutes.length?c.vRoutes.map(routeName).join('／'):'（未裁决）')+'</td>'+
      '<td>'+(c.crossSrc?'<b style="color:#b07cff">跨源</b>':'跨路线')+'</td></tr>').join('')+
    '</tbody></table>';
})();

/* ── 与 07 对账 ── */
(function(){
  const s=sec('check');
  s.innerHTML='<h2>与 07_路线脉络.md 对账</h2>'+
    '<div class="note"><b>顺序口径</b>：本页 lane 划分与 lane 内章节顺序<b>直接复用 07 的路线定义与播放顺序算法</b>'+
    '（<code>build_chapter_docs.py</code> 的 <code>build_routes()</code> / <code>play_order()</code>），'+
    '即「沿 <code>next[i]</code> 走该路线的分岐臂」的分支感知展开——<b>分岔点在前、各臂相邻、汇合点在后</b>；'+
    '不是 TSV 的 <code>章节序号</code>（逐源 DFS 前序，会跨路线穿插）。</div>'+
    '<table><thead><tr><th>项</th><th>数值</th></tr></thead><tbody>'+
    '<tr><td>章节节点（去重唯一）</td><td><b>'+M.total+'</b>（＝ 05_章节总表.tsv 的 712 行）</td></tr>'+
    '<tr><td>lane 条目（含共用重复）</td><td>'+M.listed+'（＝ 712 ＋ 102 条共用重复）</td></tr>'+
    '<tr><td>next 边</td><td>'+M.edges+'</td></tr>'+
    '<tr><td>路线（lane）数</td><td>'+DATA.routes.length+'（与 07 §零 的 19 条一致）</td></tr>'+
    '<tr><td>分岔点（next 项数 ≥ 2）</td><td>'+M.branch+'</td></tr>'+
    '<tr><td>跨路线边 / 其中跨源</td><td>'+M.cross+' / '+M.crossSrc+'</td></tr>'+
    '<tr><td>影响后续剧情</td><td>'+M.impact+'</td></tr>'+
    '<tr><td>含选项章节 / 选项数=臂数 / 不满足</td><td>'+M.choiceChapters+' / '+M.paired+' / '+M.unpaired+'</td></tr>'+
    '</tbody></table>'+
    '<div class="note">逐 lane 顺序比对由 <code>资源组\\工具\\verify_chapter_flow.py</code> 自动执行（不一致数应为 0）。</div>';
})();

/* ── 交互 ── */
function jump(id,rid){
  const sel='.node[data-script="'+id+'"]'+(rid?('[data-lane="lane-'+rid+'"]'):'');
  let el=document.querySelector(sel)||document.querySelector('.node[data-script="'+id+'"]');
  if(!el) return;
  let p=el.closest('section'); if(p) show(p.id.slice(4));
  el.scrollIntoView({behavior:'smooth',block:'center'});
  el.style.outline='2px solid var(--accent)';
  setTimeout(()=>el.style.outline='',1400);
}
function goLane(rid){
  const el=document.querySelector('.lane[data-lane="lane-'+rid+'"]');
  if(!el) return;
  let p=el.closest('section'); if(p) show(p.id.slice(4));
  setTimeout(()=>el.scrollIntoView({behavior:'smooth',block:'start'}),40);
}
function filterLane(inp){
  const q=inp.value.trim().toLowerCase();
  const box=inp.closest('section');
  let hit=0,all=0;
  box.querySelectorAll('.node').forEach(d=>{
    all++;
    const ok=!q||d.dataset.q.indexOf(q)>=0;
    d.style.display=ok?'':'none';
    if(ok)hit++;
  });
  box.querySelector('.cnt').textContent=q?('命中 '+hit+' / '+all):'';
}
function openDetail(id,rid){
  const n=N[id];
  const b=document.getElementById('detailBody');
  const cl=clsOf(n);
  const bl=(BADGE[cl]?'<span class="bdg '+BADGE[cl][1]+'">'+BADGE[cl][0]+'</span> ':'');
  const A=DATA.arms[id]||[];
  let laneSeq='';
  if(rid){
    const lane=DATA.sections.flatMap(x=>x.lanes).find(l=>l.rid===rid);
    if(lane){const i=lane.nodes.findIndex(x=>x.id===id); laneSeq='('+rid+')'+lane.title+' 第 '+(i+1)+' / '+lane.nodes.length+' 章';}
  }
  const inc=DATA.crossEdges.filter(c=>c.v===id);
  b.innerHTML='<h3>《'+esc(titleOf(n))+'》</h3>'+
    '<div style="margin-bottom:6px">'+bl+'<span class="bdg">TSV 章节序号 #'+n.seq+'</span></div>'+
    '<div class="k" style="font-size:14px">'+id+'</div>'+
    '<dl>'+
    '<dt>本路线播放序</dt><dd>'+esc(laneSeq||'（不在该路线）')+'</dd>'+
    '<dt>作品 / 源代号</dt><dd>'+esc(n.work)+' / '+esc(n.src)+'</dd>'+
    '<dt>TSV route</dt><dd>'+esc(n.route||'（未裁决）')+'</dd>'+
    '<dt>中文标题</dt><dd>《'+esc(n.cn||'（无标题）')+'》</dd>'+
    '<dt>日文原名</dt><dd>〔'+esc(n.jp||'（无标题）')+'〕</dd>'+
    '<dt>章节作用</dt><dd>'+esc(n.role)+'</dd>'+
    '<dt>phase</dt><dd>'+esc(n.phase||'（空）')+'</dd>'+
    '<dt>next（'+n.next.length+' 臂）</dt><dd>'+(n.next.length?n.next.map((t,k)=>{
        const a=A[k];
        return '<div>臂 '+(k+1)+' → <a href="#" onclick="jump(\''+t+'\','+((a&&a.targetRoutes&&a.targetRoutes[0])||0)+');return false"><code>'+t+'</code></a>'+
          (N[t]?(' 《'+esc(titleOf(N[t]))+'》'):'')+(a?(' <span style="color:#c9a4ff">［'+esc(a.routeLabel)+'］</span>'):'')+'</div>';
      }).join(''):'（无，end）')+'</dd>'+
    '<dt>选项数</dt><dd>'+n.choiceN+(n.choiceN!==n.next.length&&n.next.length>1?(' <span style="color:#ffb347">（选项数 ≠ 臂数 '+n.next.length+'，配对未确证）</span>'):'')+'</dd>'+
    '<dt>选项文本</dt><dd>'+(n.choices.length?n.choices.map((c,i)=>'<div>选项 '+(i+1)+'：'+esc(c)+((n.choiceN===n.next.length&&n.next[i])?(' → <code>'+n.next[i]+'</code>'):'')+'</div>').join(''):'（无选项文本'+(n.next.length>1?'，脚本级分岐（由前置 flag 决定）':'')+'）')+'</dd>'+
    '<dt>是否影响后续剧情</dt><dd>'+(n.impact?('<span style="color:#ff6b6b">'+esc(n.impact)+'</span>'):'否')+'</dd>'+
    '<dt>入口（自其他路线汇入）</dt><dd>'+(inc.length?inc.map(c=>'<a href="#" onclick="jump(\''+c.u+'\','+c.lane+');return false"><code>'+c.u+'</code></a>（'+routeName(c.lane)+'）').join('，'):'（无）')+'</dd>'+
    '<dt>游戏日期</dt><dd>'+esc(n.date||'（无显式日期）')+'</dd>'+
    '<dt>行数 / 登场人物</dt><dd>'+n.lines+' 行 ｜ '+esc(n.cast||'（无）')+'</dd>'+
    '<dt>spine 归属</dt><dd>'+esc(n.spine||'（无）')+'</dd>'+
    '<dt>备注</dt><dd>'+esc(n.remark||'（无）')+'</dd>'+
    '</dl>';
  document.getElementById('detail').classList.add('on');
  document.getElementById('scrim').classList.add('on');
}
function closeDetail(){
  document.getElementById('detail').classList.remove('on');
  document.getElementById('scrim').classList.remove('on');
}
document.getElementById('scrim').onclick=closeDetail;
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetail();});

document.getElementById('m-total').textContent=M.total;
document.getElementById('m-listed').textContent=M.listed;
document.getElementById('m-edges').textContent=M.edges;
document.getElementById('m-cross').textContent=M.cross;
document.getElementById('m-impact').textContent=M.impact;
show('overview');
</script>
</body>
</html>
"""


def main():
    D = build()
    md = gen_md(D)
    html = gen_html(D)

    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    print("[OK] 章节节点 %d（去重）｜ lane 条目 %d ｜ next 边 %d ｜ 路线 %d ｜ 分岔点 %d ｜ 跨路线边 %d ｜ 影响后续剧情 %d"
          % (len(D["order"]), sum(len(l["nodes"]) for l in D["lanes"]), len(D["edges"]),
             len(D["lanes"]), len(D["branch_all"]), len(D["cross_edges"]), len(D["impact"])))
    print("[OK] %s (%d bytes)" % (OUT_MD, os.path.getsize(OUT_MD)))
    print("[OK] %s (%d bytes)" % (OUT_HTML, os.path.getsize(OUT_HTML)))


if __name__ == "__main__":
    main()
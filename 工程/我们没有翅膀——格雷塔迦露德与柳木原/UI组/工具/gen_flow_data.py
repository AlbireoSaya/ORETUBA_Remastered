# -*- coding: utf-8 -*-
r"""gen_flow_data.py —— M4 流程图 / 番外(Fragment) / 章节选择 的数据生成器
=========================================================================
Issue : ISSUE-20260919-11（UI 美术组 · M4）
职责  : 把**资源组只读产物**转成两侧（krkr / HTML）共用的流程图数据文件，
        保证「幕名 / 番外组名 / 条数 / 结局」全部有据可查、**不得手写剧情**。

单一数据源（只读，主工作树绝对路径）
-----------------------------------
  A 资源组\剧本\spine.json
      · acts[11]          -> 幕名 / 来源 / 场景数 / 行数 / 说明（幕名唯一权威）
      · side_stories[53]  -> 番外 6 组的组名与条数（**只取组名与条数，不取剧情**）
      · branch_points[50] -> 关键分歧点（选项数 / 选项文本）
      · excluded[32]      -> 排除清单条数
      · reconciliation    -> 场景总数 / 选项总数对账
  B 资源组\01_剧情流程图.md  §五 结局矩阵（Markdown 表，程序化解析）
  C 资源组\剧本\主线编排方案.md  §二 分幕表（交叉核对 acts 的幕名与场景数）

产物（写权限内）
---------------
  1) 复刻\flow_data.js           -> window.UI_FLOW_DATA = { … };
  2) krkr\game\ui_flow_data.tjs  -> var UIFlowData = %[ … ];

**几何不写进数据文件**：节点盒 / 连线的 x/y/w/h 一律由
`layout/screens/32_flowchart.json` 声明（→ UILayoutData），数据文件只描述
「拓扑 + 文本 + 三态判定规则」。这样 krkr 侧与 HTML 侧同读同一份布局数据，
1:1 由结构保证。

★ 第 3 批（ISSUE-20260928-02 · 2026-09-28）· **旧元素寻址字段已删除**
------------------------------------------------------------------
  `nodes[].el` / `branches[].el` / `edges[].els` / `buses[].el` / `links[].el` /
  `layout.wrap_elements` / `layout.bypass_elements` —— 这六个字段的值是 **M18 期屏版式**的
  元素 id（`flow.n01`/`flow.seq01`/`flow.bus_c`/`flow.cv1_a`…），那批元素**早已不在屏数据里**
  ⇒ 字段**没有任何消费者**（krkr 侧按它们寻址的函数已整批删除；实测证据：每轮巡演日志打
  `滚动就绪：视口 0–0 ｜ 滚动元素 0 件`）⇒ 属「按旧 id 静默空转」的隐患源。**本批一并删除**，
  并在**两个产物**的文件头同步写入退场说明（`RETIRED_NOTE_LINES`，改这里即改两处头注）。
  现行寻址：屏上元素一律按 `fc.node.*` / `fc.entry.*` / `fc.frag<G>.*`
  （生成器 `工具\\gen_flow_layout.py`）。
  ⚠️ 另订正一处**静默回退**隐患（缺口 G-5）：`BOX_PNG` 原指向 4 个**已不存在**的 M18 期素材
  （`ui/x_gen_flownode_*.png`），而盘上 `ui_flow_data.tjs` 的 `box_png` 早已手工改成存在的
  `ui/x_ui_*` 件 —— 跑一次生成器就会把 `box_png` 静默回退成缺图引用。本批已把盘上真值回写生成器。

复跑
----
    cd "工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\工具"
    python gen_flow_data.py            # 两个产物一起写（★ 会覆盖 复刻/flow_data.js）

依赖：仅标准库。
"""

from __future__ import annotations

import io
import json
import os
import re
import sys

# ── 路径（工作区铁律 1：只写 UI组\ 内；资源组只读） ────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))            # …\UI组\工具
UI = os.path.dirname(HERE)                                   # …\UI组
PROJ = os.path.dirname(UI)                                   # …\我们没有翅膀——格雷塔迦露德与柳木原
RES = os.path.join(PROJ, "资源组")

SPINE = os.path.join(RES, "剧本", "spine.json")
FLOW_MD = os.path.join(RES, "01_剧情流程图.md")
MAIN_MD = os.path.join(RES, "剧本", "主线编排方案.md")

OUT_JS = os.path.join(UI, "复刻", "flow_data.js")
OUT_TJS = os.path.join(UI, "krkr", "game", "ui_flow_data.tjs")

# ── 流程图拓扑（人工编排；每个节点/边都对应上面数据源里的既有事实） ────
#   id 命名：N01..N11 = spine.json acts[0..10]（幕 1..11），B01/B02 = 关键分歧点。
#   * B01 = branch_points 里 ot_s01_02c（s01 鹰志线，2 选项）—— 唯一有明确
#     选项文本的 ot 线分歧（spine.json branch_points[0]；主线编排方案.md §6.2 ot 段）。
#   * B02 = s03_09a「世间种种（Ｃ）」→ next=['s03c_01a']（亚衣线入口；
#     主线编排方案.md §二 第 6/7 幕说明、§六 6.2 更正项 W10b）。
#   边：acts 之间的叙事顺序取自 主线编排方案.md §三「主线顺序」；
#   幕 2（前奏诗·系统脚本）明文「无剧情时序，不排入叙事顺序」→ 只挂 N01 作旁支。
NODE_ACT = [
    # (node_id, act_no)  —— act_no 对应 spine.json acts[].act
    ("N01", 1), ("N02", 2), ("N03", 3), ("N04", 4), ("N05", 5), ("N06", 6),
    ("N07", 7), ("N08", 8), ("N09", 9), ("N10", 10), ("N11", 11),
]

EDGES = [
    # (edge_id, from, to, 依据)
    ("E01", "N01", "N02", "幕 2 为前奏诗系统脚本，挂在幕 1 之后作旁支（主线编排方案.md §二 第 2 幕说明：无剧情时序）"),
    ("E02", "N01", "N03", "主线顺序 1 → 3（主线编排方案.md §三）"),
    ("E03", "N03", "N04", "主线顺序 3 → 4（主线编排方案.md §三）"),
    ("E04", "N03", "N05", "主线顺序 3 → 5（s01/s02/s03 为同一时间带的平行线，§二 第 4/5 幕说明）"),
    ("E05", "N03", "N06", "主线顺序 3 → 6（主线编排方案.md §三）"),
    ("E06", "N04", "B01", "s01 线内分歧点 ot_s01_02c（spine.json branch_points[0]）"),
    ("E07", "B01", "N08", "PSV 美咲线承 s01 鹰志线 Bad End（S01_14J2）的同期分支（§二 第 8 幕说明）"),
    ("E08", "N06", "B02", "s03 线内分歧点 s03_09a（主线编排方案.md §二 第 6 幕说明）"),
    ("E09", "B02", "N07", "亚衣线入口 s03_09a2 → next=['s03c_01a']（W10b 实测更正，§二 第 7 幕说明）"),
    ("E10", "N04", "N09", "s04 收束全线（§二 第 9 幕说明：唯一真结局）"),
    ("E11", "N08", "N09", "s04 收束全线（含 PSV 美咲线）"),
    ("E12", "N05", "N09", "s04 收束全线"),
    ("E13", "N06", "N09", "s04 收束全线"),
    ("E14", "N07", "N09", "s04 收束全线（含亚衣线）"),
    ("E15", "N09", "N10", "After Story 在 s04 之后（24_1a 明示接「仮統合」；§二 第 10 幕说明）"),
    ("E16", "N10", "N11", "涅布＊プラス 明日香篇在 AS 之后（毕业后 2 月；§二 第 11 幕说明）"),
]

# ── M18（2026-09-20）：流程图改为「一屏看全」的 2 列 × 7 行网格 ────────
#   背景：M14 的「纵向长图 + 视口滚动」一屏只见约 3 个节点、共 4 页，用户要的是
#   「一眼看全」。主代理 2026-09-20 授权本屏对节点方框使用
#   `nine:{l:0,t:0,r:0,b:0}`（_schema.md §六 明文允许的「整图等比缩放」语义），
#   于是 13 个节点可以缩到 0.4785× 后放进 **2 列 × 7 行** 的单屏网格。
#   几何推导与可读性实测见 32_flowchart.json 的屏 note 与 _工作\M18_报告.md。
#
#   屏上元素的拓扑表达（单屏下的简化，**信息损失如实登记**）：
#     ① 同列相邻节点 → 纵向连接条 flow.seq01…seq11（其中与真实边重合者登记为该边的元素）
#     ② 跨列续接   → 三段折线 flow.wrap_a/b/c（N05 → N06；**不对应任何真实边**，只表阅读顺序）
#     ③ 真实边 E02（N01→N03，同列跨一行）→ 左侧旁路 flow.e02_a/b/c
#     ④ 五线汇入 s04 → 列间空隙中线 x=960 的汇流总线 flow.bus_c + 四条短横条 flow.cv1_a…cv4_a
#        + 引入段 flow.cv_n09（N07→N09 与 N09 同列相邻，由 flow.seq09 表达，不进总线）
#     ⑤ **E04（N03→N05）与 E05（N03→N06）在 2×7 网格里无屏上元素**（els 为空数组）——
#        要横跨 3–5 行，画出来会与总线/续接线大量交叠；bus_a 的 el 同样置空串。
#        拓扑本身完整保留在本文件的 EDGES / BUSES 里（供编程组与数据对账）。
FLOW_ORDER = ["N01", "N02", "N03", "N04", "B01", "N08", "N05", "N06", "B02", "N07",
              "N09", "N10", "N11"]

# 网格：(列, 行)。**列优先**填充（先填满第 1 列再填第 2 列），列内自上而下 = FLOW_ORDER。
GRID_COLS = 2
GRID_ROWS = 7
FLOW_GRID = {
    "N01": (0, 0), "N02": (0, 1), "N03": (0, 2), "N04": (0, 3),
    "B01": (0, 4), "N08": (0, 5), "N05": (0, 6),
    "N06": (1, 0), "B02": (1, 1), "N07": (1, 2), "N09": (1, 3),
    "N10": (1, 4), "N11": (1, 5),
}

# 同列相邻节点之间的纵向连接条 —— ★ 第 3 批：只留**拓扑**（from/to/edge），
#   元素 id（`flow.seq01`…）**已退休**（旧屏元素，早已不在屏数据里 ⇒ 见文件头「旧寻址退场」）。
LINKS = [
    ("N01", "N02", "E01"),
    ("N02", "N03", ""),    # 无对应边：阅读顺序相邻
    ("N03", "N04", "E03"),
    ("N04", "B01", "E06"),
    ("B01", "N08", "E07"),
    ("N08", "N05", ""),    # 无对应边：s01 与 s02 的平行关系
    ("N06", "B02", "E08"),
    ("B02", "N07", "E09"),
    ("N07", "N09", "E14"),
    ("N09", "N10", "E15"),
    ("N10", "N11", "E16"),
]

# ── ★ 第 3 批（2026-09-28）：旧元素寻址常量**整批退休** ──────────────────
#   被删的常量与字段（值都是旧屏版式的元素 id，`flow.n01`/`flow.seq01`/`flow.bus_c`/`flow.cv1_a`…）：
#     · `WRAP_ELEMENTS` / `BYPASS_ELEMENTS`（曾进 `layout.wrap_elements` / `layout.bypass_elements`）
#     · `EDGE_ELEMENT`（曾进 `edges[].els`）
#     · `NODE_ELEMENT_PREFIX`（曾进 `nodes[].el` / `branches[].el`）
#   理由：那批元素**早已不在屏数据里**（现行屏是 `工具\gen_flow_layout.py` 产的
#   `fc.node.<NNNN>` 族）⇒ 这六个字段**没有任何消费者**（krkr 侧按它们寻址的函数已整批删除；
#   实测证据：每轮巡演日志打 `滚动就绪：视口 0–0 ｜ 滚动元素 0 件`）⇒ 属「按旧 id 静默空转」的隐患源。
#   现行寻址：屏上元素一律按 `fc.node.*` / `fc.entry.*` / `fc.frag<G>.*`（编号规则见该生成器）。

# ── 节点方框类型（用户 2026-09-20 定义四种方框语义）──────────────────
#   判定依据：spine.json acts[].note（逐幕载明的结局）＋ 资源组\01_剧情流程图.md §五 结局矩阵
#   normal    = 一般剧情 / badend = BAD END / important = 重要章节 / goodend = GOOD END
#   ★ 第 3 批订正：`BOX_PNG` 原指向 **4 个已不存在的 M18 期素材**
#     （`ui/x_gen_flownode_{1_normal,2_badend,3_important,4_goodend}.png`，盘上实测**均缺**），
#     盘上 `ui_flow_data.tjs` 的 `box_png` 早已**手工改成存在的 `ui/x_ui_*` 件**；
#     生成器不同步 ⇒ 跑一次就把 `box_png` 静默回退成缺图引用。本批把盘上真值**回写生成器**。
#     注：`box_png`/`box`/`box_cn`/`box_legend` 是 M18 期**图例语义**，现行屏不再渲染它们
#     （渲染是 `fc.node.<NNNN>` 三件套）⇒ 这些字段是**遗迹字段、零消费者**，只为历史对照保留。
BOX_PNG = {
    "normal":    "ui/x_ui_node_section_off.png",
    "badend":    "ui/x_ui_node_select_off.png",
    "important": "ui/x_ui_node_frag_off.png",
    "goodend":   "ui/x_ui_label_off.png",
}
BOX_CN = {
    "normal":    "一般剧情",
    "badend":    "BAD END / 普通结局",
    "important": "重要章节（影响后续剧情发展）",
    "goodend":   "GOOD END（包括女主角非坏结局的结尾）",
}
NODE_BOX = {
    "N01": ("normal",
            "acts[0].note：火烈鸟三人＋ＡＤさん主持的剧场框架，包裹四个角色短篇；"
            "§五 结局矩阵无其结局 → 开篇铺垫，一般剧情"),
    "N02": ("normal",
            "acts[1].note：引擎初始化/回想/制作人员/标题画面，**无剧情时序**，"
            "不排入叙事顺序；§五 无其结局 → 一般剧情"),
    "N03": ("normal",
            "acts[2].note：s00「序文 ～俺たちに翼はない～」，全篇开篇（1 场景 / 2 槽）；"
            "§五 无其结局 → 一般剧情"),
    "N04": ("goodend",
            "acts[3].note：含明日香 END（s01_16a）与京 END（s01_18a）；"
            "§五 结局矩阵两行均为女主角非坏结局 → GOOD END"),
    "N05": ("goodend",
            "acts[4].note：日和子 END（s02_16a）；§五 结局矩阵 → GOOD END"),
    "N06": ("goodend",
            "acts[5].note：鸣 END（s03_22a）；§五 结局矩阵 → GOOD END"),
    "N07": ("goodend",
            "acts[6].note：亚衣 END（s03c_20a「エピローグ～隼人君と亜衣～」）；"
            "§五 结局矩阵 → GOOD END"),
    "N08": ("goodend",
            "acts[7].note：美咲 END（M09_01 / M09_02）；§五 结局矩阵 → GOOD END。"
            "（备选判定：本线入口为 s01 鹰志编 Bad End「S01_14J2」，"
            "若按「入口结局定档」则应标 badend —— 见 M14 报告「备选判定」）"),
    "N09": ("goodend",
            "acts[8].note：真 END（s04_28b → s04_29a），**收束全线的唯一真结局**；"
            "§五 结局矩阵 → GOOD END"),
    "N10": ("badend",
            "acts[9].note：24 最终统合线含 24_5c「Ｂ－ＥＮＤ：俺の涙よ誰かに届け」"
            "（失败，GAME OVER）；§五 结局矩阵 → BAD END。"
            "（该幕同时含 24_5b「Ｇ－ＥＮＤ」——见 M14 报告「备选判定」）"),
    "N11": ("normal",
            "acts[10].note：子篇目菜单式短篇集（start_oretuba 为菜单脚本，34 条选择支挂其下）；"
            "§五 结局矩阵未列其结局 → 一般剧情"),
    "B01": ("important",
            "spine.json branch_points[0] ot_s01_02c：s01 鹰志线内 2 选项关键分歧点，"
            "决定后续（其 Bad End 分支即 PSV 美咲线入口）→ 重要章节"),
    "B02": ("important",
            "s03_09a 的 (N)/(C) 两变体：s03_09a1 继续鸣线 / s03_09a2 → next=['s03c_01a'] "
            "分叉亚衣线（W10b 实测，主线编排方案.md §二 第 6/7 幕说明）→ 重要章节"),
}
# 方框图例（屏上图例行的顺序：一般剧情 / BAD END / 重要章节 / GOOD END）
BOX_LEGEND = [
    {"type": "normal",    "png": BOX_PNG["normal"],    "cn": BOX_CN["normal"]},
    {"type": "badend",    "png": BOX_PNG["badend"],    "cn": BOX_CN["badend"]},
    {"type": "important", "png": BOX_PNG["important"], "cn": BOX_CN["important"]},
    {"type": "goodend",   "png": BOX_PNG["goodend"],   "cn": BOX_CN["goodend"]},
]

# 汇流总线（不属于任何单条边的纵线；几何在 32_flowchart.json 声明）
#   M18：单屏 2×7 网格下，列间空隙（x=852…1068）的中线 x=960 就是天然的汇流通道，
#        故 bus_b 用当时那条 `flow.bus_c` 表达（远端四源 N04/N08/N05/N06 各一条短横条接入，
#        N07 与 N09 同列相邻、其边由当时的 `flow.seq09` 表达，不进总线）。
#        bus_a（N03 之后三条平行线的汇流）在网格里仍无对应元素 —— 拓扑保留在 sources 里。
#   ★ 第 3 批（2026-09-28）：`BUSES[].el` 字段**已删除**（旧屏元素 id，早已不在屏数据里）；
#     只保留 `id` / `sources` / `note`（拓扑与语义信息）。上面这些旧元素名只作**历史注释**。
BUSES = [
    {"id": "BUS_C1C2", "sources": ["N03"],
     "note": "N03 之后三条平行线（s01/s02/s03）共用的汇流纵线。"
             "**M18：2×7 网格仍无法表达 ⇒ 无屏上元素**（`el` 字段已按第 3 批删除）"},
    {"id": "BUS_C2C3", "sources": ["N04", "N05", "N06", "N07", "N08"],
     "note": "五条线（s01/s02/s03/亚衣/PSV）汇入 s04 的汇流纵线；"
             "M18 画在**列间空隙的中线 x=960**，远端四源各用短横条接入，另一条引入段接到 N09 左边界；"
             "N07→N09 与 N09 同列相邻，故不进总线（`el` 字段已按第 3 批删除）"},
]

# 节点状态判定（写明依据，供报告引用）
RULES = {
    "visited": "节点已到达（当前进度中该幕/分歧点已被走过）",
    "available": "节点未到达，但其任一入边的源节点已到达（= 可前往）",
    "locked": "节点未到达且所有入边的源节点均未到达（= 未解锁）",
    "current": "当前所在节点，单独用 @palette.node_current 外框标记",
    "priority": "已到达 > 可前往 > 未解锁（三态互斥，判定顺序固定）",
    "root": "无入边的节点（N01）恒为可前往（起始节点）",
    "progress_source": "已到达集合由 ui_state.tjs 的持久化机制保存（跨启动读回），键名 flow_visited",
    "edge": "连线颜色按**源节点是否已到达**判定：源与目标均已读=node_visited / 源已读（可通行）=node_available / 源未读=node_locked；"
            "汇流总线取「任一源节点已读」即 node_available，否则 node_locked",
    "layout": "**M18（2026-09-20）版式**：流程图改**单屏 2 列 × 7 行网格总览**（13 个节点全部一屏可见、"
              "无需滚动）。节点方框为 M11 交来的 1152×217–234 横条 PNG，经主代理授权用 "
              "`nine:{l:0,t:0,r:0,b:0}`（_schema.md §六 允许的「整图等比缩放」语义）缩到 **0.4785×**"
              "（552×104–112）。列优先填充，列内自上而下 = FLOW_ORDER。"
              "由此 E04/E05 两条跨行边在网格里无屏上元素，属**已知信息损失**"
              "（拓扑保留在 edges/buses 里）；相比 M14 多表达了真实边 E02（左侧旁路）。"
              "★ 第 3 批（2026-09-28）：M18 期元素 id（`flow.*`）的**寻址字段已整批删除**"
              "（`nodes[].el`/`edges[].els`/`buses[].el`/`links[].el`/`layout.wrap_elements`/"
              "`layout.bypass_elements`）—— 现行屏元素按 `fc.node.<NNNN>` 寻址。"
              "几何推导与可读性实测见 32_flowchart.json 的屏 note 与 _工作\\M18_报告.md。",
}


# ── ★ 第 3 批（2026-09-28）· 旧元素寻址退场说明（逐行写进**两个产物**的文件头）────
#   生成器与产物**两处同步**：改这里即改两个文件的头注（不再手工补头注、跑一次就被抹）。
RETIRED_NOTE_LINES = [
    "",
    "★★ 第 3 批（ISSUE-20260928-02 · 2026-09-28）· 旧元素寻址字段**已删除** ★★",
    "------------------------------------------------------------------",
    "  下列六个字段**已从本文件与生成器一并删除**（不再是「保留待检」）：",
    "    `nodes[].el` / `branches[].el`（值 `flow.n01`…/`flow.b01`…）",
    "    `edges[].els`（值 `flow.seq*` / `flow.cv*` / `flow.bus_c` 数组）",
    "    `buses[].el`（值 `flow.bus_c`）",
    "    `links[].el`（值 `flow.seq01`…）",
    "    `layout.wrap_elements` / `layout.bypass_elements`（值 `flow.wrap_*` / `flow.e02_*`）",
    "  理由：这些值是 **M18 期屏版式**的元素 id，那批元素**早已不在屏数据里**",
    "  （现行屏是 `layout/screens/32_flowchart.json` 的 `fc.node.<NNNN>` 族，由",
    "  `工具\\gen_flow_layout.py` 产出）⇒ 六个字段**没有任何消费者**：",
    "    · krkr 侧按它们寻址的函数（`uiFlowSyncFlowchart` / `uiFlowBuildScroll` /",
    "      `uiFlowScrollToCursor` / `uiFlowPage` / `uiFlowDrawMarkers`）已**整批删除**；",
    "    · 退场前的实测证据：每轮巡演日志都打 `滚动就绪：视口 0–0 ｜ 滚动元素 0 件`",
    "      （按旧 id 取不到任何元素 ⇒ 那一整套三态色环/滚动/标记框全是空转）。",
    "  ⇒ 现保留的只有**拓扑与语义**（`nodes`/`edges`/`links`/`buses`/`branches`/`fragments`",
    "    的 id 与 from/to/basis/sources 等），**不得**再据任何字段索引屏上元素 ——",
    "    屏上元素一律按 `fc.node.*` / `fc.entry.*` / `fc.frag<G>.*`；",
    "    机器可读的退场标记见数据顶层 `retired_addressing` / `retired_addressing_note`。",
    "  ⚠️ 缺口登记（G-5）：本文件属「**生成器产出后手工维护**」——生成器的 `BOX_PNG` 曾指向",
    "     4 个已不存在的 M18 期素材（`ui/x_gen_flownode_*.png`），盘上 `box_png` 已手工改成",
    "     存在的 `ui/x_ui_*` 件；本批已把盘上真值**回写生成器**（`BOX_PNG`），此后可安全重跑。",
]


# ── 读取资源组产物（只读） ────────────────────────────────────────────
def load_spine():
    with io.open(SPINE, encoding="utf-8") as f:
        return json.load(f)


def parse_ending_matrix(path):
    """解析 01_剧情流程图.md 的 §五 结局矩阵（Markdown 表）。"""
    lines = io.open(path, encoding="utf-8").read().split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("## 五") and "结局矩阵" in ln:
            start = i
            break
    if start is None:
        return [], "未找到 §五 结局矩阵"
    rows = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if s.startswith("## "):
            break
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if set(cells[0]) <= set("-: ") or cells[0] == "结局":
            continue
        rows.append({
            "ending": cells[0].replace("**", ""),
            "script": cells[1].strip("`"),
            "name_jp": cells[2],
            "meaning": cells[3],
        })
    return rows, "§五 结局矩阵 %d 行" % len(rows)


def parse_act_table(path):
    """解析 主线编排方案.md §二 分幕表，用于与 spine.json acts 交叉核对。"""
    txt = io.open(path, encoding="utf-8").read()
    m = re.search(r"## 二、分幕表(.*?)## 三、", txt, re.S)
    if not m:
        return {}
    out = {}
    for ln in m.group(1).split("\n"):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        out[int(cells[0])] = {"name": cells[1], "source": cells[2],
                              "scenes": int(cells[3]), "lines": int(cells[4])}
    return out


# ── 组装数据 ─────────────────────────────────────────────────────────
def build():
    spine = load_spine()
    endings, end_note = parse_ending_matrix(FLOW_MD)
    act_table = parse_act_table(MAIN_MD)

    acts_raw = {a["act"]: a for a in spine["acts"]}

    # 幕 -> 节点
    acts = []
    nodes = []
    for nid, no in NODE_ACT:
        a = acts_raw.get(no)
        if a is None:
            raise SystemExit("[FAIL] spine.json 缺 act %d" % no)
        # 交叉核对（主线编排方案.md §二 分幕表）
        t = act_table.get(no)
        xcheck = ""
        if t is not None:
            if t["name"] != a["name"]:
                xcheck = "幕名不一致：spine=%s / 分幕表=%s" % (a["name"], t["name"])
            elif t["scenes"] != len(a["scenes"]):
                xcheck = "场景数不一致：spine=%d / 分幕表=%d" % (len(a["scenes"]), t["scenes"])
            else:
                xcheck = "与分幕表一致"
        acts.append({
            "act": no, "node": nid, "name": a["name"],
            "source": "/".join(a["source"]), "scenes": len(a["scenes"]),
            "lines": a["line_count"], "note": a["note"], "basis": a["basis"],
            "cross_check": xcheck,
        })
        btype, breason = NODE_BOX[nid]
        nodes.append({
            "id": nid, "kind": "act", "act": no, "label": a["name"],
            "sub": "%s · %d 场景 / %d 行" % ("/".join(a["source"]), len(a["scenes"]), a["line_count"]),
            # ★ 第 3 批：`el`（旧元素 id `flow.n01`…）**已删除** —— 旧 id 静默空转隐患源。
            #   现行寻址一律按屏数据 `fc.node.<NNNN>`（`工具/gen_flow_layout.py` 产出）。
            # M14：节点方框类型（四种方框 PNG 之一）+ 判定依据
            "box": btype, "box_cn": BOX_CN[btype], "box_png": BOX_PNG[btype],
            "box_reason": breason,
        })

    # 关键分歧点（只取 spine.json 已有事实）
    bp_by_scene = {b["scene_id"]: b for b in spine["branch_points"]}
    branch_defs = [
        ("B01", "ot_s01_02c", "E06", "E07",
         "s01 鹰志线内分歧点：国家 / 阿斯嘉公主 二选一（spine.json branch_points[0]）"),
        ("B02", "s03_09a", "E08", "E09",
         "s03 隼人线内分歧点：世间万象（Ｎ）继续鸣线 / 世间种种（Ｃ）分叉到亚衣线 s03c（主线编排方案.md §二 第 6 幕说明，W10b 实测）"),
    ]
    branches = []
    for bid, scene, ein, eout, note in branch_defs:
        b = bp_by_scene.get(scene, {})
        btype, breason = NODE_BOX[bid]
        branches.append({
            "id": bid, "scene": scene, "kind": "branch",
            "route": b.get("route", ""), "options": b.get("option_count", 0),
            "choices": [c.get("text_cn", "") for c in b.get("choices", [])],
            "label": "分歧点 " + (b.get("route", "") or scene),
            "sub": "%d 选项 · %s" % (b.get("option_count", 0), scene),
            # ★ 第 3 批：`el`（旧元素 id `flow.b01`/`flow.b02`）**已删除** —— 旧 id 静默空转隐患源
            "note": note,
            "box": btype, "box_cn": BOX_CN[btype], "box_png": BOX_PNG[btype],
            "box_reason": breason,
        })
        nodes.append(branches[-1])

    # M18：网格坐标（列/行）。`row` 保留为 FLOW_ORDER 的序号（旧字段，兼容既有消费方）。
    row_of = {}
    for i, nid in enumerate(FLOW_ORDER):
        row_of[nid] = i
    for n in nodes:
        n["row"] = row_of.get(n["id"], len(FLOW_ORDER) + nodes.index(n))
        gc, gr = FLOW_GRID.get(n["id"], (0, 0))
        n["grid_col"] = gc
        n["grid_row"] = gr

    # 边
    #   ★ 第 3 批：`els`（旧元素 id 数组）**已删除** —— 只留拓扑 `id`/`from`/`to`/`basis`。
    edges = []
    for eid, f, t, basis in EDGES:
        edges.append({"id": eid, "from": f, "to": t, "basis": basis})

    # 相邻行的纵向连接条 —— ★ 第 3 批：只留**拓扑**（from/to/edge）；`el` 字段已删除。
    links = [{"from": a, "to": b, "edge": e} for a, b, e in LINKS]

    # 番外（Fragment）：**只取组名与条数**；不取剧情
    #   （M4 任务书：Fragment 为空壳框架，内容字段留空待后续填充）
    groups = []
    seen = []
    for s in spine["side_stories"]:
        g = s["group"]
        if g not in seen:
            seen.append(g)
            groups.append({"name": g, "count": 0})
        groups[seen.index(g)]["count"] += 1

    # M14：Fragment 屏**本期上屏的前 40 条**（40 = M11 底图实测格子数 5×8）。
    #   标题逐条取自 spine.json side_stories[].title_cn / title_jp，**不得手写**。
    frag_cells = []
    for i, s in enumerate(spine["side_stories"][:40]):
        frag_cells.append({
            "index": i, "row": i // 5, "col": i % 5,
            "scene_id": s["scene_id"], "group": s["group"],
            "title_cn": s["title_cn"], "title_jp": s["title_jp"],
            "source": "/".join(s["source"]) if isinstance(s.get("source"), list) else s.get("source", ""),
            "script": s.get("script", ""),
        })

    rec = spine["reconciliation"]

    return {
        # ★ 第 3 批：机器可读的退场标记（值 = **已删除**的字段名；解释见产物文件头）
        "retired_addressing": ["nodes[].el", "edges[].els", "buses[].el",
                               "links[].el", "layout.wrap_elements", "layout.bypass_elements"],
        "retired_addressing_note": (
            "★ 第 3 批（ISSUE-20260928-02 · 2026-09-28）：上述六个**旧元素寻址字段已删除**"
            "（不只是「保留待检」）——它们的值是 M18 期屏版式的元素 id（`flow.n01`/`flow.seq01`/"
            "`flow.bus_c`/`flow.cv1_a`…），那批元素**早已不在屏数据里** ⇒ 这六个字段没有任何消费者"
            "（krkr 侧按它们寻址的函数已整批删除；实测证据：每轮巡演日志打 "
            "`滚动就绪：视口 0–0 ｜ 滚动元素 0 件`）。现行寻址：`fc.node.<NNNN>` / `fc.entry.*` / "
            "`fc.frag<G>.*`（生成器 `工具\\gen_flow_layout.py`）。"),
        "generated_from": {
            "spine": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/剧本/spine.json",
            "flow_md": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/01_剧情流程图.md",
            "main_md": "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/剧本/主线编排方案.md",
        },
        "counts": {
            "acts": len(spine["acts"]), "scenes_total": rec["source_scene_total"],
            "acts_scenes": rec["acts_total"], "excluded": rec["excluded_total"],
            "side_stories": rec["side_total"], "side_groups": len(groups),
            "branch_points": len(spine["branch_points"]),
            "choices_in_spine": rec["choices_total_in_spine"],
            "endings": len(endings),
        },
        "rules": RULES,
        "acts": acts,
        "nodes": nodes,
        "edges": edges,
        "links": links,
        "buses": BUSES,
        "branches": branches,
        "box_legend": BOX_LEGEND,
        "layout": {
            "version": "M18-2026-09-20",
            "mode": "single-screen-grid",
            "cols": GRID_COLS,
            "rows": GRID_ROWS,
            "row_order": FLOW_ORDER,
            "grid": FLOW_GRID,
            # ★ 第 3 批：`wrap_elements` / `bypass_elements`（旧元素 id 数组）**已删除**。
            "note": "M18 单屏网格版式：13 个节点按 grid（列优先）排进 2 列 × 7 行，全部一屏可见、"
                    "无需滚动。方框由 1152×217–234 等比缩到 0.4785×（552×104–112，用 "
                    "nine:{l:0,t:0,r:0,b:0} 表达整图缩放）。同列相邻节点用纵向连接条（links）；"
                    "跨列用当时的三段折线；E02 用当时左侧旁路；"
                    "五线汇入 s04 用列间空隙中线 x=960 的汇流总线 + 四条短横条。"
                    "E04/E05 在网格中无屏上元素 —— 拓扑保留在 edges/buses 里，属已知信息损失。"
                    "★ 第 3 批（2026-09-28）：M18 期元素 id（`flow.*`）的**寻址字段整批删除**，"
                    "上面提到的连线元素名只作历史背景；现行屏元素一律按 `fc.node.*` / `fc.entry.*` / "
                    "`fc.frag<G>.*`（`工具\\gen_flow_layout.py` 产出）寻址。",
        },
        "endings": endings,
        "ending_note": end_note,
        "fragments": {
            "total": len(spine["side_stories"]),
            "group_count": len(groups),
            "groups": groups,
            "onscreen": len(frag_cells),
            "cells": frag_cells,
            "note": "番外（Fragment）：spine.json side_stories[] 共 53 条 / 6 组。"
                    "M11 交来的 Fragment 底图实测为 **5 列 × 8 行 = 40 格**，"
                    "故本期**只上屏前 40 条**（cells，标题逐条取自 spine.json，不得手写）；"
                    "余 13 条的呈现方式（第 2 页 / 滚动 / 另开屏）待定，见 M14 报告。",
        },
        "note": "幕名/番外组名/结局一律取自资源组产物（见 generated_from），M4/M14 不得自造。",
    }


# ── 输出 ─────────────────────────────────────────────────────────────
def tjs_literal(node, indent=0):
    pad = "  " * indent
    if isinstance(node, dict):
        if not node:
            return "%[]"
        items = []
        for k, v in node.items():
            key = k if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)) else '"%s"' % k
            items.append("%s  %s: %s" % (pad, key, tjs_literal(v, indent + 1)))
        return "%[\n" + ",\n".join(items) + "\n" + pad + "]"
    if isinstance(node, list):
        return "[" + ", ".join(tjs_literal(v, indent) for v in node) + "]"
    if isinstance(node, bool):
        return "true" if node else "false"
    if node is None:
        return "void"
    if isinstance(node, str):
        return '"%s"' % node.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return str(node)


def main():
    data = build()

    with io.open(OUT_JS, "w", encoding="utf-8", newline="\n") as f:
        f.write("// ============================================================\n")
        f.write("// flow_data.js —— 【自动生成，禁止手改】\n")
        f.write("// 生成器：UI组/工具/gen_flow_data.py\n")
        f.write("// 数据源：资源组\\剧本\\spine.json + 资源组\\01_剧情流程图.md（§五 结局矩阵）\n")
        f.write("//         + 资源组\\剧本\\主线编排方案.md（§二 分幕表，交叉核对）\n")
        f.write("// 幕名 / 番外组名 / 结局一律取自上述资源组产物，不得自造。\n")
        f.write("// 几何不在本文件：节点盒与连线的 x/y/w/h 由 layout/screens/32_flowchart.json\n")
        f.write("// 声明（→ ui_layout.js / ui_layout.tjs），两侧同读同一份布局数据。\n")
        f.write(("// " + RETIRED_NOTE_LINES[0]).rstrip() + "\n")
        for _ln in RETIRED_NOTE_LINES[1:]:
            f.write(("// " + _ln).rstrip() + "\n")
        f.write("// ============================================================\n")
        f.write("window.UI_FLOW_DATA = ")
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
        f.write(";\n")

    with io.open(OUT_TJS, "w", encoding="utf-8", newline="\n") as f:
        f.write("// ============================================================\n")
        f.write("// ui_flow_data.tjs —— 【自动生成，禁止手改】\n")
        f.write("// 生成器：UI组/工具/gen_flow_data.py\n")
        f.write("// 数据源：资源组\\剧本\\spine.json + 资源组\\01_剧情流程图.md（§五 结局矩阵）\n")
        f.write("//         + 资源组\\剧本\\主线编排方案.md（§二 分幕表，交叉核对）\n")
        f.write("// 幕名 / 番外组名 / 结局一律取自上述资源组产物，不得自造。\n")
        f.write("// 几何不在本文件：节点盒与连线的 x/y/w/h 由 layout/screens/32_flowchart.json\n")
        f.write("// 声明（→ UILayoutData），两侧同读同一份布局数据。\n")
        f.write("// 本文件是**数据文件**（与 ui_layout.tjs 同性质），不含任何绘制逻辑。\n")
        for _ln in RETIRED_NOTE_LINES:
            f.write(("// " + _ln).rstrip() + "\n")
        f.write("// ============================================================\n")
        f.write("var UIFlowData = " + tjs_literal(data) + ";\n")

    c = data["counts"]
    print("[OK] gen_flow_data.py 完成")
    print("     幕 %d ｜ 场景总数 %d（主干 %d / 排除 %d）｜ 番外 %d 条 / %d 组 ｜ 分歧点 %d ｜ 选项总数 %d ｜ 结局 %d"
          % (c["acts"], c["scenes_total"], c["acts_scenes"], c["excluded"],
             c["side_stories"], c["side_groups"], c["branch_points"],
             c["choices_in_spine"], c["endings"]))
    print("     节点 %d（幕 %d + 分歧点 %d）｜ 边 %d"
          % (len(data["nodes"]), len(data["acts"]), len(data["branches"]), len(data["edges"])))
    print("     幕名交叉核对（主线编排方案.md §二）：")
    bad = 0
    for a in data["acts"]:
        print("       %2d 幕 %-34s %s" % (a["act"], a["name"], a["cross_check"]))
        if a["cross_check"] != "与分幕表一致":
            bad += 1
    print("     结局矩阵解析：%s" % data["ending_note"])
    print("     输出：%s" % os.path.relpath(OUT_JS, UI))
    print("           %s" % os.path.relpath(OUT_TJS, UI))
    if bad:
        print("[WARN] %d 幕与分幕表不一致，请主代理裁决" % bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
# -*- coding: utf-8 -*-
r"""gen_flow_layout.py —— 剧情流程图屏生成器（`layout/screens/32_flowchart.json`）

Issue `ISSUE-20260927-05`（流程图系统第 1 步 · 模块 E1）→ **第 2 步 `ISSUE-20260928-02`（模块 E1：运行态数据 / 番外独立层 / 全量几何）**
接口 = `_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md`（v1.2，仍有效）
     ＋ `_工作\ISSUE-20260928-02_第2步\接口冻结.md`（本轮唯一接口；本文件只做增补，不改前者口径）
参照 = `_工作\ISSUE-20260927-05_流程图实现\侦察_参照作布局算法.md`

■ 职责（单一数据源 → 屏数据）
    资源组\08_全系列章节流程图.html 的 `const DATA`（712 节点 / 760 边 / 6 段 19 道）
    ＋ 资源组\剧本\spine.json（side_stories[].entry_suggestion）
        → layout\screens\32_flowchart.json（元素 + 顶层 `links`）
    三处产物（ui_layout.json / ui_layout.tjs / ui_layout.js）由 `工具\gen_layout.py` 转出，**本脚本不碰**。

■ 产出的图内容层（契约 §一：**只替换/新增这一批**）
    fc.node.<NNNN>（+`_tx`/`_hit`）｜ fc.branch.<NNNN> ｜ fc.label.<NNNN>（+`_tx`）｜ fc.entry.<NNNN>
    顶层 `links[]`（生成器算好 `pts` 正交折线；两端只负责描线 + 画箭头）

■ 契约 §一 列出的既有静态元素**原样透传**（id 与几何一字不改）
    它们以「逐字提取自改造前 32_flowchart.json 的 JSON 快照」形式内嵌在本文件（`STATIC_ELEMENTS_JSON`），
    这是本工程生成器的一贯写法（同 `工具\m34_build_screens.py` 把元素写在代码里）——
    若从磁盘现值读，第二次运行会把**自己产出的图内容层**当成静态元素，不可幂等。

■ 番外组名中文化（ISSUE-20260927-06）
    `spine.json` 的 `side_stories[].group` 是我方自建的**组名元数据**，6 组中 3 组残留日文 token。
    spine.json 属资源组数据、本模块**只读不改** ⇒ 中文化映射落在本文件（常量 `GROUP_CN_MAP`
    ＋ 函数 `group_cn()`），**只映射需要改的组，其余组原样透传**；逐条来源注记写在
    `GROUP_CN_MAP` 上方注释。映射结果写进 `fc.label.*_tx` 的 `sample`（**两端绘制与量测的都是
    `sample`**：`krkr/game/ui_theme.tjs` 的 `uiThemeRenderText`／`复刻/replica.js`），故一处改、两端生效。

■ 只读、不改的输入
    · 08_全系列章节流程图.html（正则取 `const DATA = ` … `\nconst N = `，**不解析 DOM**）
    · 剧本\spine.json（只取 side_stories[].entry_suggestion / group / script）
    · layout\palette.json（连线色**只从色板解析**，禁止直写色值）
    · layout\_root.json（画布 1920×1080）

■ 用法
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python 工具\gen_flow_layout.py                     # 产样例屏（默认 = 预设 screen1 = 交付样例）
    python 工具\gen_flow_layout.py --preset screen2     # 含 frag 番外节点的第二交付样例
    python 工具\gen_flow_layout.py --preset ref150      # 参照作口径变体（**不是交付样例**）
    python 工具\gen_flow_layout.py --preset states      # ★ 运行态演示：节点五态 + 连线三档同屏
    python 工具\gen_flow_layout.py --preset frag        # ★ 番外独立层演示：主干 + 第 1 组独立层
    python 工具\gen_flow_layout.py --preset full        # ★ 全量几何数据（**不产元素**，落 _工作\...\全量布局.json）
    python 工具\gen_flow_layout.py --section 0 --lanes 0,1 --from 100 --limit 9 --step-y 95
    python 工具\gen_flow_layout.py --dry-run            # 只打印统计/包围盒/节点 id 集，**不落盘**
    python 工具\gen_flow_layout.py --text-fit-report    # 文字容量实测（uiThemeLayoutText 复刻）

■ ★ 第 2 步（ISSUE-20260928-02 · 接口冻结 §一/§二/§五）——本脚本新增的四处能力
    ① **连线 `state` 取代 `kind`**（冻结 §一.2）：取值 `normal`/`visited`/`noroute`；生成器按 `state`
       解析出 `color`（palette 键 `edge_normal`/`edge_visited`/`edge_noroute`）、`w`（4/4/3）、
       `arrow`（true/true/false）后写进 JSON ⇒ **两端不做任何配色判断**。缺省 `normal`（＝旧样例外观）。
    ② **节点 `flow_state` + 叠加件**（冻结 §一.1）：`fc.node.<NNNN>` 可选 `flow_state`；
       **不写该字段时外观与文件内容一律不变**（交付样例 screen1/screen2/ref150 都不写）。
       叠加件只在 `--preset states` 里演示：`_dim`（locked，★ ISSUE-20260928-03 由 `rect` 改 **`image`**，
       按节点种类派生的压暗件、几何与 `nine` 与底图件逐字段一致、强度由 `opacity` 控）／
       `_new`（new）／`_read`（visited，★ ISSUE-20260928-03 新增「已读绿对勾」，用户裁决「丙方案」）；
       `current` 由两端程序化画环 ⇒ 不产元素（**本轮裁决：current 只留金环、不加对勾**）。
    ③ **番外独立层**（冻结 §二）：屏级 `flags_default.fc_layer="main"`；
       ★ **第 3 批更正**：层旗标由**图内容层独家持有**（`fc.node.*`/`fc.branch.*`/`fc.label.*`/
       `fc.entry.*`/`fc.frag*`），**外壳件（视口/迷你地图/滚条/页签/标题牌/关闭/付箋/回放/进入本章）不写
       `vis_flag`/`vis_when`** —— 外壳是两种层共用的舞台（随层隐藏会让组名与网格画在无底图的透明/黑画面上）。
       新族 `fc.frag<G>.<NNNN>`/`_tx`/`_hit`（G=1..6，来自 `spine.json` 的 `side_stories[].group` 分组）
       按网格排布、**不产连线**；每组顶栏 = 组名 `fc.frag<G>_title` ＋ **按组**返回键
       `fc.frag<G>_back`/`_back_tx`（「返回主干」）/`_back_hit`；入口热区 `fc.entry.<NNNN>_hit`
       （`action:"flow_layer"`, `layer:` 目标层）。★ 交付样例 `screen1` 产**全部 6 组**独立层（进出闭环）；
       `--preset frag` 保留「只第 1 组」的最小档（供单层口径断言）。
       ★★ **裁决 4（第 4 批 · 2026-09-28 主代理）：入口热区 `fc.entry.<NNNN>_hit` 只在「该组的独立层
       确实在本档产出」时才产** —— 未产出则**不产该热区**（入口 image / 组名标签仍在，作**纯占位**、
       不可点），并在**生成器输出**打印「哪个档、哪几组因此不产热区」。落盘前**无条件**卡一道：
       「存在 `fc.entry.*_hit` ⇒ 其 `layer` 必在本档 `produced_layers` 内」（对所有档统一生效）。
       依据：非全量演示档（screen2/ref150/states 无独立层、frag 只有第 1 组）若照产 6 个热区，
       点一下会切到**未产出的层** ⇒ 屏面变空且回不来（HTML 实测 `E3_screen1_entry点击后.png`）。
    ④ **`--preset full`**（冻结 §五）：产 `_工作\ISSUE-20260928-02_第2步\全量布局.json`
       （逐节点 `{id,group,lane,kind,x,y,w,h,flow_state}` + 每 lane 的 `step_y` 与内容 bbox +
       全局 bbox + 视口参数），**绝不产 627×3 个 elements** —— 元素化渲染交编程组。

■ 参数默认值（★ 与契约 §8.2 的关系，见报告「需裁决」）
    --vert-x 375       ＝契约 §8.2 参照作口径（select 450 亦为参照值，本轮不区分）
    --step-y 150       ＝契约 §8.2 参照作口径（**默认值，§九 裁决 1 明令不得改成 95**）
    --step-y 95        **样例屏**由命令显式传（`python 工具\gen_flow_layout.py --step-y 95`），算术证据：
        本作唯一可用的两条短跨道边是
          VL 源 `s01_14g`(lane0 idx100) → `s01_14g1`(lane1 idx101)   Δ=1 行
          VZ 源 `s01_18a`(lane1 idx104) → `s01_19a`(lane0 idx108)     Δ=4 行
        要让「lane0 的 idx100 与 idx108」同时落进一屏（1235×827），行数需 ≥ 9 行 ⇒
        9 行需 `8*step_y + 65 <= 827` ⇒ `step_y <= 95`。step=150 时一屏只有 6 行，
        idx100 与 idx108 相差 8 行 ⇒ **两条边不可能同屏**（已穷举 12 条跨道边，仅此两条 Δ<=5）。
      ⇒ 生成器默认值取样例窗口参数；`--step-y 150` 可随时复现契约 §8.2 口径。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)                                # …\<作品>\UI组
GAME_ROOT = os.path.dirname(UI)                           # …\<作品>
LAYOUT = os.path.join(UI, "layout")
SCREENS = os.path.join(LAYOUT, "screens")
DEFAULT_OUT = os.path.join(SCREENS, "32_flowchart.json")

DATA_HTML = os.path.join(GAME_ROOT, "资源组", "08_全系列章节流程图.html")
SPINE_JSON = os.path.join(GAME_ROOT, "资源组", "剧本", "spine.json")
PALETTE = os.path.join(LAYOUT, "palette.json")
ROOT_JSON = os.path.join(LAYOUT, "_root.json")

# ── 几何 / 契约常量（契约 §二、§三、§四）────────────────────────────────
NODE_W, NODE_H = 296, 65
NODE_NINE = {
    "section": {"l": 14, "t": 0, "r": 16, "b": 0},   # 源 236×65（契约 §二.2）
    "select":  {"l": 14, "t": 0, "r": 13, "b": 0},   # 源 263×65
    "frag":    {"l": 14, "t": 0, "r": 15, "b": 0},   # 源 228×65
}
NODE_ASSET = {
    "section": ("ui/x_ui_node_section_off.png", "ui/x_ui_node_section_on.png"),
    "select":  ("ui/x_ui_node_select_off.png",  "ui/x_ui_node_select_on.png"),
    "frag":    ("ui/x_ui_node_frag_off.png",    "ui/x_ui_node_frag_on.png"),
}
NODE_ASSET_SOURCE = ("AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；"
                     "坐标取自《交汇协奏曲》PSB 容器（M34 复刻件，实测尺寸与 nine 见契约 §二.2）")

# ★★ 修正轮（2026-09-27 · 用户裁决 V2「缩字号」）★★
#   根因：上一轮把「竖向容量」判在**元素高 65** 上，但三类底图的**可见实体面**只有 48–49px
#   （逐行平均 alpha>200 的行区间：section/frag = rows 8..55（48 行）、select = 8..56（49 行））。
#   23px 时两行墨迹跨度 = block_top + lineH + (size-1) = 13+23+22 = 58 > 49 ⇒ 实机上第一行被画到底板外
#   （vision 实测上溢 7–8px、「切头」）。⇒ 改用 **19px / 行距 1.0 / 盒宽 240**（用户看的就是这组参数）。
TEXT_SIZE = 19                 # 字号（V2 裁决）
TEXT_LINE_SPACING = 1.0        # ★ 显式行距（**元素级** `line_spacing` 字段；全局基线是 fonts.line_spacing.body = 1.4，必须覆盖）
TEXT_W = 240                   # 文字盒宽（底图仍 296，文字盒收窄并按节点水平居中：x = x_node + 28）
                               # 横向依据（判据C）：可见实体面宽度实测 ≈282px（section：源列 7..228 经 nine ×1.291 映射到 296 空间的 7..288）
                               # ⇒ 行墨迹 ≤ 263 即左右各留 ≥9px。19px 下每行可容 12 字（228），
                               # 禁则强行并入最多 +1 字 ⇒ 上限 240 内可达 13 字 = 247（留 16px）。
TEXT_MAX_LINES = 2
TEXT_INK = "@palette.psv_ink"
# 可见实体面（逐行平均 alpha>200 的行区间；--text-fit-report 会在有 PIL 时**重新实测**并核对下面这组值）
PLATE_ROWS = {"section": (8, 55), "select": (8, 56), "frag": (8, 55)}
PLATE_MARGIN_MIN = 5           # 判据A/B：实体面上/下沿与首/末行墨迹之间至少留 5px

# ══════════════════════════════════════════════════════════════════════
# ★★ 第 9 批（2026-09-28 · vision 复核后的数据侧最后一处修复）★★
#   **「已读对勾」不变量**：节点标题**首行墨迹左缘 ≥ x_node + 30**。
#   由来（vision 实测）：已读对勾 = 节点内左上角 `(x+10, y+12)` 的 **20×20** 件 ⇒ 其右缘在
#   节点相对 **+30**；而标题文字盒左缘 = `x_node + 28`（盒宽 240 居中）⇒ 标题**居中**渲染时
#   首行墨迹左缘 = `28 + (240 − w0)/2`。两线一叠就压住首字左边（现状：全量 712 条里有 **12 条**
#   首行墨迹 < +29、最小 **+20.50**（`62_1b` 单行 255px）。成因＝**字符串末尾是行首禁则字符**
#   （如 `）`）⇒ `ui_theme_wrap` 把它强行并入本行 ⇒ 单行 247–255px（> 盒宽 240）。
#   ⇒ 本表在**自然断点**处插**硬换行** `\n`（引擎 `uiThemeWrap` 按 `\n` 分段，生成器的
#     `ui_theme_wrap` 同式，已核）：两行墨迹都 ≤ 230px ⇒ 左缘 ≥ +33，给对勾留 ≥4px 余量。
TITLE_CHECK_GAP = 34           # 首行墨迹左缘须 ≥ x_node + 34（＝对勾右缘 +30 **再留 ≥4px 余量**）
#   ★ 第 10 批收紧：原值 30 只保证「零重叠」，仍留 0px 紧贴的边界簇（8 条实测 +30.00/+32.00）。
#     用户 2026-09-28 看完实机对照图后裁决「留 ≥4px」⇒ 提到 34，把那 8 条一并硬断行锁定
#     （收紧后全量复算：最紧 **+34.00**＝`s01_02b`，712 条**全部 ≥ +34**）。
TITLE_BREAK_MAX_LINE = 230     # 硬断行后**两行墨迹**都须 ≤ 本值（左缘 ≥ 28+(240−230)/2 = +33）
# 断点理由（逐条；断点优先级＝A 全角开括号/引号/波浪之前 ＞ B 句读标点之后 ＞ C 空格处）：
#   A 类（语义边界，优先）：`（` 前的「题名＋括注」结构 —— 括注独占第二行，最自然；
#   B 类：断在 `、` 之后（该字符是行首禁则 ⇒ 引擎本来也只能断它之后，这里只是**显式化**)；
#   C 类：拉丁词界（空格）。
#   表内每条的「旧值」是**加表之前**该标题的折行结果（`--title-check-report` 可复跑复核）。
TITLE_HARD_BREAK = {
    # ── A 类：全角「（」前（题名 ＋ 括注两行）────────────────────────────
    # 62_1b　旧单行 255px（**首行**左缘 +20.50，全量最小）：断在「（」前 ⇒ 122 / 133（**首行**左缘 +87.0）
    "62_1b": ("无论何时·棱镜", "（性的意义上）"),
    # s03_03k 旧单行 247（+24.50）⇒ 「临别时的恶作剧」133 /「（硬汉风味）」114（+81.5）
    "s03_03k": ("临别时的恶作剧", "（硬汉风味）"),
    # s03_06d2 旧单行 247（+24.50）⇒ 190 /「（Ｃ）」57（+53.0；括注仅 3 字，第二行必然短）
    "s03_06d2": ("交错之箭的颜色与去向", "（Ｃ）"),
    # s03_06d1 同上（Ｎ 版）⇒ 190 / 57（+53.0）
    "s03_06d1": ("交错之箭的颜色与去向", "（Ｎ）"),
    # s01_12a 旧单行 247（+24.50）⇒ 「公主之墙」76 /「（明日香大人的墙）」171（+62.5）
    "s01_12a": ("公主之墙", "（明日香大人的墙）"),
    # s03_03l1 旧单行 247（+24.50）⇒ 190 /「（Ｎ）」57（+53.0）
    "s03_03l1": ("笨蛋们开着面包车来了", "（Ｎ）"),
    # 12_3a0 旧单行 247（+24.50）⇒ 「约定的放学后」114 /「（Ｔａｋｅ２）」133（+81.5）
    "12_3a0": ("约定的放学后", "（Ｔａｋｅ２）"),
    # s02_05g 旧单行 247（+24.50）⇒ 「那一定是试炼」114 /「（的一种愿望）」133（+81.5）
    "s02_05g": ("那一定是试炼", "（的一种愿望）"),
    # ── A 类：全角波浪「～」前（副题分界）────────────────────────────────
    # 02_02a 旧单行 247（+24.50）⇒ 「“序章」57 /「～亚历山大的众人～”」190（+53.0）
    #   备选「“序章～亚历山大的众人」209 /「～”」38 更不均衡 ⇒ 取前者（波浪即副题分界）
    "02_02a": ("“序章", "～亚历山大的众人～”"),
    # 02_01a 旧单行 247（+24.50）⇒ 「“邂逅」57 /「～对抗：千岁鹫介～”」190（+53.0）
    "02_01a": ("“邂逅", "～对抗：千岁鹫介～”"),
    # ── B 类：断在「、」之后（该字符行首禁则 ⇒ 引擎本来的断点，此处显式化）──────
    # s01_08f 旧两行但首行 240px（左缘 +28.00）⇒ 「ＩＮ ＴＨＥ ＲＯＯＭ、」202 /「ＡＴ ＮＩＧＨＴ」139（+47.0）
    "s01_08f": ("ＩＮ ＴＨＥ ＲＯＯＭ、", "ＡＴ ＮＩＧＨＴ"),
    # ── C 类：拉丁词界（空格）──────────────────────────────────────────
    # s03_03i 旧两行但首行 240px（左缘 +28.00）⇒ 「ＵＮＤＥＲ ＴＨＥ 」164 /「ＳＭＯＫＩＮＧ ＳＫＹ」196（+50.0）
    "s03_03i": ("ＵＮＤＥＲ ＴＨＥ ", "ＳＭＯＫＩＮＧ ＳＫＹ"),
    # ══════════════════════════════════════════════════════════════════
    # ★ 第 10 批（`ISSUE-20260928-04` · 用户 2026-09-28 看完**实机对照图**后裁决）：
    #   **「零间隙边界簇」8 条一并补硬断行**。
    #   这 8 条**满足**原不变量（首行墨迹左缘 ≥ +30 ⇒ 与对勾零重叠），但余量只有 0–2px：
    #   `42_3`/`42_4`/`s01_09c4`/`s02_10b`/`s04_03f1`/`s04_03f2`/`s04_03f3` 恰 **+30.00**（首行 236px）、
    #   `s03_17a` **+32.00**（232px）。其中 **4 条本来就是「236px 长行 + 2–3 字尾巴」的难看折行**
    #   （`42_4` 次行 38、`s04_03f1` 57、`s04_03f3` 38），**`42_4` 还把 `ＦＡＬＣＯＮ` 从中间切断**
    #   （引擎按**字符**折行、不认识拉丁词界）⇒ 补硬断行同时把这些折行修平衡。
    #   ★ 断点规则与既有表一致：**「（」前**（开括号＝第二行领起，同 A 类）；
    #     **「·」「，」之后**（行尾分隔符；「，」属行首禁则 ⇒ 引擎只能断在其后）。
    #   ★ **其中 2 条在交付样例里**（`42_3`→`fc.frag4.0008_tx`、`42_4`→`fc.frag4.0009_tx`）
    #     ⇒ 本批对交付样例的**有意变更恰 2 处**（且仅这两个 `sample` 字段），
    #     已在 `m06_delivered_sample_ledger.py` 的「基线总账」里登记。
    # ── A 类：「（」前（题名 ＋ 括注两行）────────────────────────────────
    # 42_3 旧单行 236px（左缘 +30.00＝零间隙）⇒ 「格兰·玛尼耶」103 /「（ＥＡＧＬＥ）」133（**首行**左缘 +96.5）
    "42_3": ("格兰·玛尼耶", "（ＥＡＧＬＥ）"),
    # 42_4 旧首行 236px 且次行仅「ＯＮ）」38px（**拉丁词 ＦＡＬＣＯＮ 被切断**）⇒ 122 /「（ＦＡＬＣＯＮ）」152（+72.0）
    "42_4": ("格兰玛·露尼耶", "（ＦＡＬＣＯＮ）"),
    # ── B 类：断在「·」之后（副题分隔符作行尾）──────────────────────────
    # s01_09c4 旧单行 236px（+30.00）⇒ 「第一届·」65 /「明天在哪里干活会议」171（+62.5）
    "s01_09c4": ("第一届·", "明天在哪里干活会议"),
    # s02_10b 旧单行 236px（+30.00）⇒ 「实录·」46 /「变态中年是怎样炼成的」190（+53.0）
    "s02_10b": ("实录·", "变态中年是怎样炼成的"),
    # s04_03f1 旧两行 236/57（+30.00，次行仅 3 字）⇒「多元世界的真相·」141 /「泡沫、细胞与污垢」152（+72.0）
    "s04_03f1": ("多元世界的真相·", "泡沫、细胞与污垢"),
    # s04_03f2 旧单行 236px（+30.00）⇒ 「多元世界的真相·」141 /「声音与怀念」95（+100.5）
    "s04_03f2": ("多元世界的真相·", "声音与怀念"),
    # s04_03f3 旧两行 236/38（+30.00，次行仅 2 字）⇒ 「多元世界的真相·」141 /「爬行于右下之物」133（**首行**左缘 +77.5）
    "s04_03f3": ("多元世界的真相·", "爬行于右下之物"),
    # ── B 类：断在「，」之后（行首禁则 ⇒ 引擎本来的断点，此处显式化）────────
    # s03_17a 旧两行 232/76（+32.00）⇒ 「——那一天，」118 /「我连妈妈的脸都看不了」190（+53.0）
    "s03_17a": ("——那一天，", "我连妈妈的脸都看不了"),
}


def title_sample(nid, v):
    """节点标题的**最终上屏文本**：`cn`（为空回落 `script`）＋ 按 `TITLE_HARD_BREAK` 插硬换行。

    ★ 表内每条的**拼接必须逐字等于**原文本（`assert` 守住）—— 源语料一改，本表即被查出过期，
    不会静默错切（这也是「表 → 数据」单向、可复核的关键）。
    """
    base = v.get("cn") or v.get("script") or nid
    parts = TITLE_HARD_BREAK.get(nid)
    if not parts:
        return base
    joined = "".join(parts)
    if joined != base:
        raise SystemExit("[FAIL] TITLE_HARD_BREAK[%s] 拼接（%r）≠ 源文本（%r）⇒ 表已过期，请复核"
                         % (nid, joined, base))
    return "\n".join(parts)

BRANCH_ASSET = "ui/x_ui_branch_s.png"     # 契约 §四：65×65（源 64×65 → 用 nine）
BRANCH_W, BRANCH_H = 65, 65
BRANCH_NINE = {"l": 16, "t": 16, "r": 16, "b": 16}
BRANCH_OFFSET_X = (NODE_W - BRANCH_W) // 2   # 65×65 底座居中于 296 宽槽位 = +115

LABEL_ASSET = "ui/x_ui_label_off.png"     # 契约 §四：333×38（源 355×60 → 零九宫格整图缩放，沿用旧 fc.label 先例）
LABEL_W, LABEL_H = 333, 38
LABEL_NINE = {"l": 0, "t": 0, "r": 0, "b": 0}
LABEL_TEXT_SIZE = 16                      # 长组名（19 字）在 333 内 1 行放得下的上限（实测 19×16=304）

ENTRY_ASSET = "ui/x_ui_fusen_off.png"     # 契约 §四写 `_on`，但实测 `_on`=108×60 ≠ 契约同时写明的 86×48…
ENTRY_W, ENTRY_H = 86, 48                 # ⇒ 取 `_off`（实测恰 86×48）以同时满足「尺寸」与「1:1 无缩放异常」
ENTRY_NINE = {"l": 0, "t": 0, "r": 0, "b": 0}
ENTRY_COL_W = max(ENTRY_W, LABEL_W)   # 入口列宽 = 组名标签宽（333）
ENTRY_COL_GAP = 16                    # 入口列与道带的间距
ENTRY_SOURCE = ("占位件（非最终美术）：M34 PSB 复刻付箋件 x_ui_fusen_off.png（86×48，实测 alpha bbox 4,7,82,40）；"
                "真「番外入口」图标见 26 件生图任务书 FC-4，尚未生成")

LINK_W = 4                        # 契约 §三：参照作 normal 成品宽 5×0.75=3.75 → 取整 4
LINK_COLOR_KEY = "edge_normal"    # 色板键（修正轮：**深蓝 #266080** = 参照作 noroute/query 色，用户 2026-09-27 裁决；禁止直写色值）
LINK_ARROW = True
ARROW_BACK_FACTOR = 2.0           # 末段长 ≥ 2.0×w
VL_LATERAL = NODE_W // 2          # ±148

# ══════════════════════════════════════════════════════════════════════
# ★ ISSUE-20260928-02 第 2 步（接口冻结 `_工作\ISSUE-20260928-02_第2步\接口冻结.md`）
# ══════════════════════════════════════════════════════════════════════

# ── A · 运行态：节点 `flow_state`（冻结 §一.1；★ ISSUE-20260928-03 修正 `_dim` 口径）──
#   取值（冻结，不得自造）：locked / available / visited / current / new
#   ★ `fc.node.<NNNN>` 上**只作数据**；缺省（不写该字段）＝ available（交付样例不写 ⇒ 外观不变）
#   叠加件（全部走既有机制，不新造绘制能力）：
#     locked  → `_dim`（**image**，按节点种类派生的压暗素材 / 几何与 `nine` **与该节点底图件逐字段一致** /
#                      强度由元素 opacity 控（110）/ z=节点z+1）—— ★ ISSUE-20260928-03 修正，见下
#     new     → `_new`（image ui/x_ui_new.png / 50×17 / 位置优先 (x, y−12)，越出图表视口或画布则回落 (x+6, y+8) / z=节点z+6）
#     visited → `_read`（image ui/x_ui_read_check.png / 20×20 / 1:1 无 nine / 节点可见实体面左上角内缘 (x+10, y+12) / z=节点z+6）
#               ★ ISSUE-20260928-03 新增（用户 2026-09-28 裁决「丙方案」）；`current`（当前所在）**不加**对勾（只留金环）
#     current → **两端程序化画环**（krkr layerExDraw / HTML canvas），⇒ **不产元素**
#     available → 无叠加
FLOW_STATES = ("locked", "available", "visited", "current", "new")
FLOW_STATE_DEFAULT = "available"        # 缺省语义（不写 flow_state 即此值）
NODE_STATE_FLAG = "fc.state."           # 逐节点叠加件的 flag 名前缀：fc.state.<NNNN>
# ★★ ISSUE-20260928-03 · ① 修「未解锁压暗件方角」缺陷：`_dim` 由 `rect` 改 `image` ★★
#   根因（已实测）：节点底图的**可见实体面四角是 r=16 圆弧、弧外透明**，而原实现是
#   `kind:"rect"` 的**方角矩形**（x+6, y+8, 284×48, #000000, opacity 110）⇒ 矩形四角压在背景上，
#   locked 节点每个角露出约 **55px 暗方角**（实测方角处显示色 (8,10,13) vs 同型 available 节点 (15,18,24)）。
#   修法（主代理 2026-09-28 已定）：`_dim` 改 `kind:"image"`，引用**按节点种类派生的压暗素材**；
#   **几何与 `nine` 与该节点的底图件逐字段一致**（沿用 `asset` 的 x/y/w/h/nine）；强度仍由元素
#   `opacity` 控（**保持 110**）；`z` / `vis_flag:"fc.state.<NNNN>"` / `vis_when:"locked"` 一律不变。
#   ⇒ **通用教训**：运行态叠层的**强度**由元素 `opacity` 控、**形状**由素材 alpha 控
#     （方角 / 圆角必须由素材决定，不得用元素矩形去"近似"带透明角的底图）。
DIM_OPA = 110                           # 强度旋钮（元素 opacity），与修正前一致
DIM_OFF_X, DIM_OFF_Y, DIM_W, DIM_H = 6, 8, 284, 48   # 节点**可见实体面**（不是元素矩形 296×65）
# 逐种类压暗素材（★ 件名冻结，由素材组产出；源尺寸＝对应节点底图源尺寸 ⇒ nine 与底图件完全相同）
DIM_ASSET_BY_KIND = {
    "section": "ui/x_ui_node_section_dim.png",   # 236×65 ＝ `x_ui_node_section_off.png` 源尺寸
    "select":  "ui/x_ui_node_select_dim.png",    # 263×65 ＝ `x_ui_node_select_off.png` 源尺寸
    "frag":    "ui/x_ui_node_frag_dim.png",      # 228×65 ＝ `x_ui_node_frag_off.png` 源尺寸
}
DIM_SRC_SIZE = {"section": (236, 65), "select": (263, 65), "frag": (228, 65)}
NEW_ASSET = "ui/x_ui_new.png"           # E4 产出（冻结 §三，50×17）；**接线＝E1**
NEW_W, NEW_H = 50, 17
NEW_PREF = (0, -12)                     # 参照作落点 (node.x, node.y−12)
NEW_FALLBACK = (DIM_OFF_X, DIM_OFF_Y)   # 越出图表视口/画布时的回落 (node.x+6, node.y+8)
DIM_Z_OFF, NEW_Z_OFF = 1, 6             # 冻结 §一.1
# ★★ ISSUE-20260928-03 · ② 新增「已读」绿对勾 `_read`（用户 2026-09-28 裁决「丙方案」）★★
#   落点：节点**可见实体面**（x+6, y+8, 284×48）的**左上角内缘** —— x_node+10, y_node+12
#   （距实体面左/上沿各留 4px；机检①「完全落在可见实体面内」、②「与 `_new` 不共存」、
#   ③「不越出图表视口与画布」三条都在 `build()` 里落盘前断言）。
READ_ASSET = "ui/x_ui_read_check.png"        # 绿对勾，20×20（1:1、**无 nine**）；素材组产出
READ_ALT_ASSET = "ui/x_ui_read_check_alt.png"  # 备选件（素材组一并产出；**本轮不接线**，仅登记备选）
READ_W, READ_H = 20, 20
READ_OFF = (10, 12)                     # 节点可见实体面左上角内缘：(node.x+10, node.y+12)
READ_Z_OFF = 6                          # 与 `_new` 同档（z = 节点 z + 6）
#   ★ 为什么 `current`（当前所在）**不加**对勾：本轮裁决「current 只留金环」（两端程序化画的
#     `@palette.node_current` #D8A83C 圆角描边）——「已读对勾」表达的是**已读**，当前节点另有金环标识，
#     两枚叠加会互相干扰；且当前节点必然已读 ⇒ 对勾信息冗余。登记为口径（不是缺口）。

# ── A · 运行态：连线 `state`（冻结 §一.2；**取代** 第 1 步的 `kind`）──
#   色/宽/箭头**由生成器解析后写进 `color`/`w`/`arrow`**，两端不做任何配色判断。
#   normal 缺省＝交付样例现值（外观不变）；noroute 无箭头 ⇒ 末段不补三角。
EDGE_STATES = {
    "normal":  ("edge_normal",  4, True),
    "visited": ("edge_visited", 4, True),
    "noroute": ("edge_noroute", 3, False),
}
EDGE_STATE_DEFAULT = "normal"
EDGE_STATE_ORDER = ("normal", "visited", "noroute")

# ── B · 番外独立层（冻结 §二）────────────────────────────────────────
#   屏级 flag `fc_layer`（初值 "main"）：**图内容层**件 `vis_when:"main"`，独立层件 `vis_when:"frag<G>"`。
#   ★★ 第 3 批更正（2026-09-28 · 主代理）：冻结书 §二 原写「现有 117 件**全部**加
#     `vis_flag:"fc_layer"` + `vis_when:"main"`」**作废** —— **外壳件不参与层旗标**。
#     理由（实测）：外壳件（视口 / 迷你地图 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 / 付箋 /
#     回放窗与回放键 / 进入本章 / 右栏详情）是**两种层共用的舞台**，只有「图内容」随层切换；
#     把外壳件也挂 `vis_when:"main"` ⇒ 切到第 G 组独立层时外壳被**一并隐藏**，
#     深墨色组名与网格被画到没有底图的透明/黑画面上（HTML 实测证据 `E3_frag_frag1.png`：几乎不可读）。
#     ⇒ 层旗标由**图内容层独家持有**（见 `LAYER_OWNED_PREFIXES`）；外壳件不写 vis_flag/vis_when。
LAYER_FLAG = "fc_layer"
# 图内容层（**唯一**参与层旗标的族）：只有这些前缀的元素写 `vis_flag`/`vis_when`。
#   落盘前自检（`build()` 末尾）按本表双向卡：外壳件带旗标 ⇒ 拒；图内容件缺旗标 ⇒ 拒。
LAYER_OWNED_PREFIXES = ("fc.node.", "fc.branch.", "fc.label.", "fc.entry.", "fc.frag")
LAYER_MAIN = "main"
FRAG_LAYER_FMT = "frag%d"               # vis_when 取值
FRAG_ID_FMT = "fc.frag%d.%04d"          # 元素族 id：fc.frag<G>.<NNNN>（+`_tx`/`_hit`）
FRAG_ASSET = NODE_ASSET["frag"]         # 冻结 §二：image 296×65 用 ui/x_ui_node_frag_off|on.png
FRAG_COLS = 3                           # ★ 参照作 5 个/行；我方视口 1235 宽下 5×296+4×79=1796 放不下 ⇒ 改 3
FRAG_STEP_X = NODE_W + 79               # 375（冻结 §二：296+79）
FRAG_STEP_Y = 192
FRAG_LEAD_Y = 90                        # 行首（第一行）纵向偏移：origin + 90
FRAG_ORIGIN = (6, 6)                    # 原点 = 图表视口左上 + (6, 6)
FRAG_VIEW_ROWS = 4                      # 视口内可容行数（计算值见 frag_grid_rows()）
FRAG_TITLE_SIZE = 24                    # 组名字号（★ 第 5 批：**不动** —— 修法只加底托，不改文字色/字号）
FRAG_TITLE_H = 44                       # 顶栏带高（网格行首 = 视口顶 +(6,6)；行首另有 FRAG_LEAD_Y 纵向偏移）
# ★★ 第 5 批（2026-09-28 收口）· 独立层组名不可读修复：**顶栏 = 标签底板 ＋ 文字** ★★
#   与主图 `fc.label.<NNNN>`（image 底板 + **同矩形** `_tx`，`align:"center"`）**同惯例**。
#   起因（HTML 组实测）：组名墨色 `@palette.psv_ink`（#16223A）原**直接画在近黑舞台**上 ——
#   `fc.dim`（`@palette.backdrop` #000000 / opacity 60）＋ `fc.scroll`（#5A6A8A / opacity 40）
#   合成 ≈ **(14,17,22)** ⇒ WCAG 相对亮度比仅 **1.19:1**，判**不可读**；同层返回键 6.56:1 达标
#   （它自带亮色按钮底图）。根因＝「组名用了主图标签的墨色，但独立层没有主图那块标签底板」。
#   ⇒ 第 5 批先**复用**主图标签底板（`x_ui_label_off.png`，零九宫格整图缩放）。
# ★★ 第 7 批（2026-09-28 · vision 复测加严后换件）：**改为专用硬边件** `ui/x_ui_fragtitle_bg.png` ★★
#   第 5 批的复用件（355×60）**四边都是宽渐隐带** ⇒ 拉到 420×38 后真不透明只有 rows 7..30 / cols 13..406，
#   而文字框与底板同框 ⇒ 首末字压在左右渐隐带、笔画上下沿压在上下渐隐带 ⇒ HTML 侧实测
#   **字形核心像素 5 分位对比度 1.04:1**（中位 12.98 达标，但 13%–25% 的核心笔画落在暗底上；
#   证据图 `_工作\ISSUE-20260928-02_HTML\证据\E3_title_frag1_title_未达标像素标注.png`）。
#   ⇒ 素材组产出**专用件 444×52**（硬边、霜白浅蓝底板、**不透明核心覆盖整张**）；
#     元素与素材**等尺寸 ⇒ 1:1、不加 `nine`**（也正因此不再有渐隐带吃掉笔画的问题）。
FRAG_TITLE_BG_ASSET = "ui/x_ui_fragtitle_bg.png"   # ★ 第 7 批专用件（444×52，硬边；素材组产出）
FRAG_TITLE_BG_H = 52                    # ＝ 素材高（1:1）；顶栏带 44 居中 ⇒ y = 带顶 + 3 + (44−52)//2
FRAG_TITLE_BG_W = 444                   # ＝ 素材宽（1:1）＝ 最长组名墨迹 396 + 2×24（两侧各 24px 实边距）
FRAG_TITLE_BG_PAD = 12                  # **要求的最小**文字两侧内边距（自证：最长墨迹 + 2×PAD ≤ 底板宽）
#   落盘前自检（`build()` 内）：实测最长组名墨迹 + 2×PAD > 本值 ⇒ **拒绝落盘**（提示加宽，不静默溢出）
#   ★ **当前余量 24px（非零）**：396 + 2×12 = 420 ≤ 444 ⇒ 余量 444−420 = **24px**，
#     等价于「最长组名两侧各 **24px** 实边距」（比第 5 批的 12px 更宽裕；第 5 批那条「余量恰好为零」的
#     说明已随换件作废）。任何 +1px 的组名变化仍受本闸门保护（越界即拒绝落盘并提示加宽）。
#   ★ 纵向：文字（24px）在 52 高板内 `valign:middle` ⇒ 行盒顶 = (52−24)//2 = 14 ⇒ 上下各留 **14px**（≥10px ✓），
#     且**行盒墨迹行与第 5 批完全一致**（206..229）—— 板换大只加边，不动文字位置。
FRAGBACK_ASSET = ("ui/x_ui_jumpfc_off.png", "ui/x_ui_jumpfc_over.png", "ui/x_ui_jumpfc_on.png")
FRAGBACK_W, FRAGBACK_H = 328, 61        # 同 `fc.jump`（同素材 157×61，同 nine）
FRAGBACK_NINE = {"l": 39, "t": 15, "r": 39, "b": 15}
FRAGBACK_GAP = 6                        # 距视口右/上缘
# ★ 第 3 批：返回键**按组**（`fc.frag<G>_back` / `_back_tx` / `_back_hit`）——
#   `vis_when` 只能取一个值 ⇒ 一个返回键无法同时服务 6 层，故按组拆（主代理 2026-09-28 第 3 批 item 3）。
#   文案「返回主干」，**字体/字号取该屏既有按键文字口径**＝`fc.jump_tx`（size 27 / bold / @palette.node_locked /
#   align:center / valign:middle / wrap:false / max_lines:1）。
FRAGBACK_TEXT = "返回主干"
FRAGBACK_TEXT_FONT = {"size": 27, "bold": True, "color": "@palette.node_locked",
                      "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}

# ── 全量（冻结 §五）：**只交几何与数据，不交元素** ─────────────────────
FULL_OUT = os.path.join(UI, "_工作", "ISSUE-20260928-02_第2步", "全量布局.json")
FULL_STEP_Y = 150                       # 契约 §8.2 参照作口径（全量数据的默认行距）

# 被替换/新增的图内容层（契约 §一 第 2 条）——**除这些之外的元素一律原样透传**
REPLACED_EXACT = {"fc.label", "fc.label_tx", "fc.branch", "fc.newmark"}
REPLACED_PREFIX = ("fc.n_section", "fc.n_select", "fc.n_extra")

# 契约 §一 明确点名「必须原样透传」的既有静态元素（逐条断言其存在）
PASSTHROUGH_REQUIRED = [
    "fc.dim", "fc.scroll", "fc.p_title", "fc.p_text", "fc.p_player", "fc.p_message", "fc.smallmap",
    "fc.scr_rail", "fc.scr_up", "fc.scr_knob", "fc.scr_dn", "fc.zoom_rail", "fc.zoom_knob",
    "fc.zoom_minus", "fc.zoom_plus", "fc.shift_rail", "fc.shift_knob", "fc.shift_lf", "fc.shift_rg",
    "fc.mtab1", "fc.mtab2", "fc.mtab3", "fc.mtab4", "fc.titleplate", "fc.sysbar", "fc.close",
    "fc.fusen_edit", "fc.fusen_reset", "fc.pbkick", "fc.jump", "fc.jump_hit",
    # ★ 裁决 6（2026-09-27 收尾轮）：`fc.sep`（旧样板的固定坐标章分隔线）**不再透传** ——
    #   新布局节点自 y=190 起排，它横穿第二行节点；章分隔线应由生成器在**段边界**处产出
    #   （本轮样例只有一段 ⇒ 本屏不产；全量图出段边界时再按 R2 的 1233×2 程序化产出）。
]

SCREEN_ID = "flowchart"
SCREEN_TITLE_CN = "剧情流程图"
SCREEN_OWNER = "M34"
SCREEN_NOTE = (
    "★ 本屏由 `工具\\gen_flow_layout.py`（ISSUE-20260927-05）**从真实剧情数据生成**，禁止手工摆版。\n"
    "· 数据源：`资源组\\08_全系列章节流程图.html` 的 `const DATA`（712 节点 / 760 边 / 6 段 19 道）"
    "＋ `资源组\\剧本\\spine.json`（side_stories 番外入口）。\n"
    "· 接口契约：`_工作\\ISSUE-20260927-05_流程图实现\\边与节点数据契约.md`（v1.1）——"
    "节点 296×65（素材 <296 宽者用 nine 横向拉伸）；文字 19px / **行距 1.0** / 文字盒 240（居中 x_node+28）/ 最多 2 行 / wrap；"
    "连线为**顶层键 `links`**（不走 elements 管道），`pts` 为生成器算好的正交折线，两端只描线 + 画箭头。\n"
    "· §一 列出的既有静态元素（视口 / 迷你地图 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 / 付箋 / 回放 / 进入本章）"
    "**原样透传**，id 与几何一字未改；被替换的只有旧图内容层 "
    "`fc.n_section*`/`fc.n_select*`/`fc.n_extra*`/`fc.label*`/`fc.branch`/`fc.newmark`（旧 `fc.mini1..8` 保留原样）。\n"
    "· ★ 收尾轮裁决（2026-09-27）：`fc.sep`（旧样板的固定坐标章分隔线）**不再透传**（它横穿新布局第二行节点）；章分隔线应由生成器在**段边界**处产出，本屏样例只有一段 ⇒ 不产。\n"
    "· ★ 文字（修正轮 V2 裁决）：字号 **19px**、**行距 1.0**（元素级 `line_spacing`，覆盖全局基线 1.4）、文字盒 **240 宽**（`x = x_node + 28` 水平居中）、`valign:「middle」` 垂直居中、最多 2 行、wrap。\n"
    "· ★ 竖向判据的由来（**不是元素高 65**）：三类底图的**可见实体面**（逐行平均 alpha>200）只有 **rows 8..55 ＝ 48px**（select 8..56 ＝ 49px）；上一轮按元素高判竖向容量 ⇒ 23px 两行的墨迹跨度 58px 越出实体面、实机第一行「切头」（vision 实测上溢 7–8px）。⇒ 判据改为**对准实体面**：\n"
    "    A 首行上留 = 首行墨迹顶 − 实体面上沿 ≥ **5px**；B 末行下留 = 实体面下沿 − 末行墨迹底 ≥ **5px**；C 任一行横向墨迹 ≤ **263px**（可见实体面宽实测 ≈282 ⇒ 左右各留 ≥9px）；D 712/712 **零截断**。\n"
    "    **712 条实测最小值：上留 5px / 下留 5px / 最宽行 255px / 截断 0**（`--text-fit-report` 可复跑）。19px 是这四条判据下的**字号上限**（两行需 `2×lineH ≤ 39 ⇒ lineH ≤ 19`，而 `lineH ≥ size`）。\n"
    "    ⚠ 上一轮「按元素高 65 判」的结论（含 f=23 那组参数）在新判据下全部作废。\n"
    "· ★ 连线色（修正轮）：`@palette.edge_normal` = **#266080**（深蓝，参照作 noroute/query 色 ⇒ 0xFF266080；用户 2026-09-27 裁决——原冰蓝 #65B1D4 与 select 节底色 #5FABD2 的 ΔE76 仅 3.2、几乎同色）；`pts` 为整数像素（§三 末）。\n"
    "· ★ 本屏所有**产出元素**整体落在图表视口内（x∈[60,1295]、y∈[190,1017]）：番外入口列整列摆在视口一侧，道带在剩余宽度里居中（§九 裁决 5）。\n"
    "· ★ 具名预设（无参 = `screen1` = **本交付样例**；禁手工摆版）：\n"
    "    `python 工具\\gen_flow_layout.py`（= `--preset screen1`）→ 屏1；`--preset screen2` → 含 frag 的屏2；`--preset ref150` = **参照作口径变体、不是交付样例**（跑它会把本屏换成变体）；"
    "`--preset states` = **运行态演示**（节点五态 + 连线三档同屏）；`--preset frag` = **番外独立层演示**（主干 + 第 1 组独立层）。\n"
    "    （五个预设的规模与 md5 金标见 `工具\\gen_flow_layout.py` 的 `PRESET_TABLE`、`--help` 与 `layout\\_schema.md` 的金标表。）\n"
    "· ★ 入口列落点次序（可判读）：① 按 `entry_suggestion` 关键词锚到**已落盘节点**所在行；② 该行已被上一组占用 ⇒ **下移整数个行距**直到空行；③ 下移后「标记+标签」放不下视口 ⇒ **回落**到入口列自上而下的第一个空行；④ 标签默认在标记**下方**，下方放不下则转**上方**。（`entry_after` 全为 null、无原作证据 ⇒ 落点属占位。）\n"
    "· ★ 番外组名中文化（ISSUE-20260927-06）：左栏组名标签的文案 = 经 `GROUP_CN_MAP`／`group_cn()` "
    "处理后的 `spine.json` `side_stories[].group`（写进 `fc.label.*_tx` 的 `sample`，两端据此绘制）。"
    "映射表**只收需要改的 3 组**：`おっぱい系列`→`胸部系列`（援引通用层 术语表.md:171 «おっぱい» 叙述者轨「胸部」"
    "＋ §4.1 第 2 条轨判定：组名不在引号内 ⇒ 非台词轨）、`おれつば剧场`→`没翅剧场`（同语料 title_cn 5/5）、"
    "`おまけ`→`附赠`（两层术语表均未收录，按通用层 SKILL.md §四 文体通则新定）；其余 3 组不含日文 ⇒ **原样透传**，"
    "`各线 after` 的 `after` 是英文按既有裁决保留。逐条依据与反向证据见 `工具\\gen_flow_layout.py` 的 "
    "`GROUP_CN_MAP` 上方注释；**`spine.json` 本模块只读、未被改动**（其 `title_cn` 与 `DATA.nodes[].cn` 的**混轨计数**与**两处已同屏并列**的完整口径，见 `作品skill\术语表.md` 的 `おっぱい` 行与工程记录未决项）。\n"
    "· ★ 已知排版现象（**不是缺陷**）：19px 下每行可容 **12 字**（228px）⇒ **11–12 字标题变单行**；孤字只出现在 **≥13 字**标题上（13 字 = 247px，需靠禁则并字成 1 行，或折成 12+1）。\n"
    "· 素材与材质沿用 M34 的《交汇协奏曲》PSB 复刻件（`ui/x_ui_*.png`），无雪花要素（用户 2026-09-21 裁定）。\n"
    "· **番外入口标记为占位件**（`x_ui_fusen_off.png` 充当，真 FC-4 图标未生成）。\n"
    "· ★ 第 2 步（ISSUE-20260928-02 · 接口冻结 §一/§二）——本屏数据面新增三件事：\n"
    "    ① **连线 `state` 取代 `kind`**：取值 `normal`/`visited`/`noroute`；生成器按 `state` 解析出 "
    "`color`（`@palette.edge_normal`/`edge_visited`/`edge_noroute`）、`w`（4/4/**3**）、`arrow`（true/true/**false**）后写进 JSON，"
    "**两端不做任何配色判断**。缺省 `normal` ＝ 交付样例外观（深蓝 #266080 / w4 / 有箭头）。\n"
    "    ② **节点 `flow_state` 可选字段**：`fc.node.<NNNN>` 支持 `locked`/`available`/`visited`/`current`/`new`；"
    "**本交付样例不写该字段 ⇒ 外观与文件内容一律不变**；只有 `--preset states` 演示（`_dim` 压暗件 / `_new` 角标件；"
    "`current` 由两端程序化画环 ⇒ **不产元素**）。\n"
    "    ③ **番外独立层**（屏级 flag `fc_layer`，初值 `main`）：★ **第 3 批更正 —— 外壳件不参与层旗标**："
    "层旗标由**图内容层独家持有**（`fc.node.*`（含 `_tx`/`_hit`/`_dim`/`_new`）/ `fc.branch.*` / `fc.label.*` / `fc.entry.*` / `fc.frag*`）；"
    "视口 / 迷你地图 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 / 付箋 / 回放 / 进入本章 / 右栏详情等**外壳件不写 `vis_flag`/`vis_when`** —— "
    "它们是**两种层共用的舞台**，随层隐藏会让组名与网格画在无底图的透明/黑画面上（实测 `E3_frag_frag1.png`）。\n"
    "    独立层新族 `fc.frag<G>.<NNNN>`/`_tx`/`_hit`（G=1..6，来自 `spine.json` `side_stories[].group` 的 6 组），"
    "网格**每行 3 个**、横向步进 375、纵向步进 192、行首纵向偏移 90、原点＝图表视口左上 +(6,6)；"
    "文字口径与主干节点**完全一致**（19px / 元素级 `line_spacing` 1.0 / 盒宽 240 / `max_lines` 2 / `x=x_node+28` / `valign:middle`），"
    "并**同样跑四条文字判据**；**独立层不产连线**。每组顶栏 = 组名标题 `fc.frag<G>_title`（组名＝`group_cn()`）＋ "
    "**按组**的返回键 `fc.frag<G>_back`/`_back_tx`（文案「返回主干」，字体/字号取该屏既有按键文字口径＝`fc.jump_tx` 的 27px/bold）"
    "/`_back_hit`（`action:\"flow_layer\"`, `layer:\"main\"`）；入口热区 `fc.entry.<NNNN>_hit`"
    "（`action:\"flow_layer\"`, `layer:\"frag<G>\"`，矩形＝入口件矩形）。\n"
    "    ④ ★ **交付样例含 6 组独立层**（第 3 批）：无参 `screen1` 产出 **G1–G5 全格 ＋ G6 视口可容的 12 格**（超出者在 "
    "`--frag-report` 列明）⇒ 「点入口 → 进该组独立层 → 点该组返回键 → 回主干」在**交付样例上闭环**（此前只有入口热区、没有独立层元素，"
    "点一下屏面变空且**回不来**：HTML 实测 1,510,027 差异像素、全黑）。\n"
    "    ⑤ ★ **裁决 4（第 4 批 · 2026-09-28）——入口热区只在「该组的独立层确实在本档产出」时才产**："
    "`fc.entry.<NNNN>_hit` 的 `layer` 必须指向**本档已产出**的层；该组独立层未产出（如非全量演示档）⇒ "
    "**不产该热区**，入口 image 与组名标签**仍在**（主干层可见的**纯占位**、不可点）。"
    "落盘前**无条件**自检「存在 `fc.entry.*_hit` ⇒ 其 `layer` ∈ 本档产出层」，违反即拒绝落盘。"
    "本交付样例 `screen1` 产全部 6 组 ⇒ **6/6 组有入口热区**（无占位缺口）。\n"
    "    ★ **偏离登记（冻结 §二 已授权）**：参照作番外独立层是 **5 个/行**（其视口更宽）；我方 1235px 视口下 "
    "5×296+4×79=1796 放不下 ⇒ 改 **3 个/行**。视口高 827 下该网格最多容 **4 行（12 格）**，"
    "组内超出者**本轮不产**（纵滚/横移属编程组，冻结 §五）。\n"
    "    ★★ 第 5 批追加（2026-09-28 收口）· **独立层组名加「标签底板」**（真缺陷修复）★★\n"
    "    · 起因（HTML 组实测）：`fc.frag<G>_title` 的组名墨色 `@palette.psv_ink`（#16223A）原**直接画在近黑舞台上**"
    "——`fc.dim`（`@palette.backdrop` #000000 / opacity 60）＋`fc.scroll`（#5A6A8A / opacity 40）合成 ≈ **(14,17,22)**，"
    "WCAG 相对亮度比仅 **1.19:1**，判**不可读**；同层返回键 6.56:1 达标（自带亮色按钮底图）。\n"
    "    · 根因：组名用了**主图标签的墨色**，但独立层**没有主图那块标签底板**。\n"
    "    · 修法（照主图既有惯例、**不新造素材**）：每组加一块标签底板 **`fc.frag<G>_title_bg`**"
    "（`kind:\"image\"`、素材复用 `ui/x_ui_label_off.png`、**零九宫格整图缩放**口径同 `fc.label.<NNNN>`、"
    "`vis_flag:\"fc_layer\"`＋`vis_when:\"frag<G>\"`、**`z = fc.frag<G>_title 的 z − 1` = 24**）；"
    "标题文字件改为**与底板同一矩形**（`align:center`/`valign:middle`，与 `fc.label.<N>_tx` 落在 `fc.label.<N>` 上的口径一致），"
    "**文字色与字号未动**。纵向取顶栏带居中（带 y..y+44 ⇒ 底板 y+3..y+41），文字中心仍 218（与加底托前一致）。\n"
    "    · 本机复算：底板核心实色 **(228,238,250)**（alpha≥250 众数）⇒ 对墨色 #16223A 的对比度 **≈13.5:1**（≥4.5:1）；"
    "底板 **420×38**、最长组名墨迹 396px（`番外·群像（新年行军 / 格兰玛尼耶）`@24px）⇒ 两侧各 ≥12px 余量（落盘前自检，溢出即拒）。\n"
    "    · ⚠ **本段（第 5 批）的「复用 `x_ui_label_off.png` / 420×38」已被第 7 批换件取代 —— 见下方第 7 批段。**\n"
    "    ★★ 第 7 批追加（2026-09-28 · vision 复测加严后）· **组名底托换专用硬边件** ★★\n"
    "    · 起因（HTML 组加严复测）：第 5 批复用的 `ui/x_ui_label_off.png`（355×60）**四边都是宽渐隐带**，"
    "零九宫格整张拉到 420×38 后**真不透明区只有 rows 7..30 / cols 13..406**，而文字框与底板同框 ⇒ "
    "首末字压在左右渐隐带、笔画上下沿压在上下渐隐带 ⇒ **字形核心像素 5 分位对比度仅 1.04:1**"
    "（中位 12.98:1 达标，但 13%–25% 的核心笔画落在暗底上；证据图 "
    "`_工作\\ISSUE-20260928-02_HTML\\证据\\E3_title_frag1_title_未达标像素标注.png`）。\n"
    "    · 修法：底板换**专用件** `ui/x_ui_fragtitle_bg.png` —— **444×52、硬边、霜白浅蓝底板、不透明核心覆盖整张**"
    "（素材组产出，件名与尺寸冻结）；元素与素材**等尺寸 ⇒ 1:1、不加 `nine`**（零九宫格缩放这条路同时退场）。\n"
    "    · 几何：**`x = 66`（与网格原点/番外入口列同左沿，保持原左沿不动）、`y = 192`**（＝顶栏带 196..240 的垂直居中："
    "带顶 + (44−52)//2）⇒ **24px 文字行盒墨迹行仍为 206..229、文字中心仍 218**（与第 5 批逐像素同位）；"
    "板上/下各留 **14px**（≥10px）、最长组名两侧实边距 **24px**（444−396 = 48 ⇒ 每侧 24px，比第 5 批的 12px 更宽裕）。\n"
    "    · 自检（落盘前，越界即拒）：① 组名墨迹 + 2×`FRAG_TITLE_BG_PAD`(12) ≤ **444** ⇒ 当前 **420 ≤ 444，余量 24px**"
    "（**第 5 批那条「余量恰好为零」的说明随换件作废**）；② 文字在板内上下各留 ≥10px（当前 14px）。\n"
    "    ★★ 同批第二项 · **`@palette.edge_noroute` 调暗 `#6A6A7A` → `#5A5A68`** ★★\n"
    "    · 起因（vision 实测）：最不重要的那一档 `noroute` 在引擎深底 (39,45,59) 上 **2.59:1**，"
    "**反而比 `normal` 深蓝的 2.01:1 更亮** ⇒ 语义层级与亮度层级相反。\n"
    "    · 落点：**只改 `layout/palette.json` 的该键值**（+ note 说明）；线宽 `w=3`、无箭头、`state` 分档一律不变。"
    "**交付样例 `screen1` 连线全 `normal`** ⇒ 本项**不改动屏幕数据**（`edge_noroute` 仅被 `--preset states` 的 noroute 边引用，"
    "该演示档的 md5 随之变化，属预期）。\n"
    "    ★★ 第 8 批追加（2026-09-28 · `ISSUE-20260928-03`）· **两处运行态修正** ★★\n"
    "    ① **修「未解锁压暗件方角」真缺陷** —— `fc.node.<NNNN>_dim` 由 `kind:\"rect\"` 改 **`kind:\"image\"`**。\n"
    "     · 根因（已实测）：节点底图的**可见实体面四角是 r=16 圆弧、弧外透明**，而原实现是方角 `rect`"
    "（`x+6, y+8, 284×48`、`#000000`、`opacity 110`）⇒ 矩形四角压在背景上，locked 节点**每个角露出约 55px 暗方角**"
    "（实测方角处显示色 **(8,10,13)** vs 同型 available 节点 **(15,18,24)**）。\n"
    "     · 修法：`_dim` 引用**按节点种类派生的压暗素材**（section→`ui/x_ui_node_section_dim.png` 236×65 ／ "
    "select→`ui/x_ui_node_select_dim.png` 263×65 ／ frag→`ui/x_ui_node_frag_dim.png` 228×65，件名冻结、素材组产出）；"
    "**几何与 `nine` 与该节点的底图件逐字段一致**（沿用 `asset` 的 x/y/w/h/nine）；"
    "**强度仍由元素 `opacity` 控（保持 110）**；`z`（＝节点 z+1）／ `vis_flag:\"fc.state.<NNNN>\"` ／ `vis_when:\"locked\"` 不变。\n"
    "     · **通用教训（写进 `_schema.md` 的 `fc_layer` 节）**：运行态叠层的**强度**由元素 `opacity` 控、"
    "**形状**由素材 alpha 控 —— 方角 / 圆角必须由**素材**决定，**不得**用元素矩形去「近似」带透明角的底图。\n"
    "    ② **新增「已读」绿对勾 `fc.node.<NNNN>_read`**（用户的 2026-09-28 裁决「**丙方案**」）：\n"
    "     · 件：`kind:\"image\"`、`asset:\"ui/x_ui_read_check.png\"`、**20×20（1:1、无 `nine`）**、`opacity 255`；"
    "`vis_flag:\"fc.state.<NNNN>\"`＋`vis_when:\"visited\"`；`z`＝节点 z+**6**（与 `_new` 同档）。\n"
    "     · 位置＝节点**可见实体面**（`x+6, y+8, 284×48`）的**左上角内缘** ⇒ **`x_node+10, y_node+12`**"
    "（距实体面左/上沿各 4px；右下余 264×24）。落盘前**三条机检**：① 完全落在可见实体面内；"
    "② 与 `_new` 角标**不共存于同一节点**（`new` 与 `visited` 语义互斥）；③ 不越出图表视口与画布。\n"
    "     · **为什么不用「甲 / 乙案」**：甲＝节点左侧竖条 —— 对节点面（284×48）是 **2.88:1** 的极端长宽比、"
    "竖条细而高，在网格里读作分隔线而非状态；乙＝字色弱化 —— 可见实体面上对比度由 **10.46:1 → 1.67:1** 过淡，"
    "且与「未解锁压暗」语义混淆。\n"
    "     · **`current`（当前所在）本轮不加对勾**：只留两端程序化画的 `@palette.node_current` 金环"
    "（两枚叠加互相干扰，且当前节点必然已读 ⇒ 对勾信息冗余）。\n"
    "     · 备选件 `ui/x_ui_read_check_alt.png`（素材组一并产出）**本轮不接线**，仅登记备选。\n"
    "     · **本批数据面影响**：只有 `--preset states` 产这两族（其余四档不写 `flow_state`）；"
    "`states` 元素数 **123 → 126**（`_dim` 仍 3 件、`_new` 仍 2 件、**新增 `_read` 3 件**）。\n"
    "    ★★ 第 9 批追加（2026-09-28 · vision 复核后的**数据侧最后一处修复**）· **「已读对勾」不变量** ★★\n"
    "     · 起因（vision 实测）：第 8 批的绿对勾占节点相对 **+10..+30**（20×20），而节点标题文字盒左缘 = `x_node+28`"
    "、**居中**渲染 ⇒ 首行墨迹左缘 = `28 + (240 − w0)/2`。全量复算 **12 条**标题的首行墨迹左缘 **< +29**"
    "（最小 **+20.50**＝`62_1b`「无论何时·棱镜（性的意义上）」单行 **255px**）⇒ **对勾会压住首字左边**"
    "（现在没露出来只是因为 `states` 的 3 个 `visited` 恰好都排在短标题节点上；而这 12 条里 `fc.frag6.0007_tx`"
    "**就在交付样例里**，一旦它成为已读即必然重叠）。\n"
    "     · 成因：字符串**末尾是行首禁则字符**（如 `）`）⇒ `ui_theme_wrap` 把它强行并入本行 ⇒ 单行 247–255px（> 盒宽 240）。\n"
    "     · **① 新增落盘前自检（真不变量）**：对**所有含文字节点**（主干 ＋ 独立层）复算"
    "「**首行墨迹左缘 ≥ x_node + 30**」（等价：首行墨迹 ≤ 236px），违反即**拒绝落盘**并逐条打印"
    "（节点 id / 标题 / 首行宽 / 左缘 / 行数）。当前实测：712 条**违规 0**，最紧 **+30.00**（`s04_03f1`）。\n"
    "     · **② 修掉那 12 条**：新增常量表 **`TITLE_HARD_BREAK`**（12 条，每条注明断点与理由），"
    "在自然断点处插**硬换行** `\\n`（引擎 `uiThemeWrap` 与生成器 `ui_theme_wrap` 都是按 `\\n` 分段，两端一致）；"
    "断点优先级＝**A 全角开括号/引号/波浪之前**（`（`「”」「～」前，题名＋括注两行最自然）＞ "
    "**B 句读标点之后**（`、` 是行首禁则 ⇒ 引擎本来也只能断它之后，此处只是显式化）＞ "
    "**C 拉丁词界（空格）**；表内每条**拼接必须逐字等于**源文本（`title_sample()` 内 `assert` 守住，源语料一改即报过期）。"
    "断后**两行墨迹都 ≤ 230px**（实测最大 202），给对勾留 ≥4px 余量。\n"
    "     · **本批对交付样例的唯一外观变更**：**`fc.frag6.0007_tx`**（script `62_1b`）—— 旧「无论何时·棱镜（性的意义上）」"
    "**单行 255px（左缘 +20.50，压对勾）** ⇒ 新「无论何时·棱镜」＋硬换行＋「（性的意义上）」（**122 / 133px，左缘 +87**）。"
    "其余 11 条**均不在交付样例的四档里**（分布见 `--title-check-report` 与 `PRESET_TABLE`）；"
    "`screen2`/`ref150`/`states`/`frag` 的 **content-sha256 逐字不变**（元素内容未动）。\n"
    "     · 机检：`--title-check-report`（不变量实测与违规清单）／`--selfcheck-title-break`（**变异自证**："
    "删一条硬断行必越线、表清空须 ≥ 表内条数 ⇒ 非恒真）／`m03` 的「底托」节同批复算。\n"
    "    ★★ 第 10 批追加（2026-09-28 · `ISSUE-20260928-04` · **用户看完实机对照图后裁决**）· **不变量收紧 +30 ⇒ +34** ★★\n"
    "     · **起因**：第 9 批只保证「与对勾零重叠」（≥+30）⇒ 仍有 **8 条**标题余量只有 **0–2px**"
    "（`42_3`/`42_4`/`s01_09c4`/`s02_10b`/`s04_03f1`/`s04_03f2`/`s04_03f3` 恰 **+30.00**（首行 236px）、"
    "`s03_17a` **+32.00**（232px））。其中 **4 条本来就是「236px 长行 + 2–3 字尾巴」的难看折行**，"
    "**`42_4` 还把 `ＦＡＬＣＯＮ` 从中间切断**（引擎按**字符**折行、不认拉丁词界）。\n"
    "     · **实机对照**（`run_autotour.bat frag4` 两变体帧，证据在"
    "`_工作\\ISSUE-20260928-03_标题边界簇\\证据\\对照_长标题与已读对勾_实机.png`）：现状 `42_3` 间隙 **1px**、"
    "`42_4` **5px**（且 `（ＦＡＬＣ/ＯＮ）` 断词）；补硬断行后 **65px / 55px** 且两行均衡。\n"
    "     · **处置（用户裁决）**：把这 **8 条一并补进 `TITLE_HARD_BREAK`**（断点＝「（」前、「·」「，」后，"
    "与既有 A/B 类规则一致），并把 `TITLE_CHECK_GAP` **由 30 收紧到 34**（＝对勾右缘 +30 再留 **≥4px**）"
    "⇒ 等价判据变为**首行墨迹 ≤ 228px**。收紧后全量复算：**最紧 +34.00**（`s01_02b`）、712 条**全部 ≥ +34**、"
    "两行条数 101 → **105**、全量最宽行 236.0 → **228.0px**、**截断 0**。\n"
    "     · **本批对交付样例的有意变更恰 2 处**（该 8 条里只有 2 条在交付样例里）："
    "**`fc.frag4.0008_tx`**（script `42_3`）与 **`fc.frag4.0009_tx`**（`42_4`）的 `sample` 各插一个硬换行；"
    "元素数 289 不变、连线 13 条几何全同（已在 `m06_delivered_sample_ledger.py` 的基线总账登记）。\n"
)



# ══════════════════════════════════════════════════════════════════════
# 静态元素快照 —— 逐字提取自改造前的 layout/screens/32_flowchart.json
#   （§一 要求「原样透传、id 与几何一字不改」；内嵌以保证生成器幂等）
# ══════════════════════════════════════════════════════════════════════
STATIC_ELEMENTS_JSON = r"""[
 {
  "id": "fc.dim",
  "kind": "rect",
  "z": 1,
  "visible_default": true,
  "x": 0,
  "y": 0,
  "w": 1920,
  "h": 1080,
  "color": "@palette.backdrop",
  "opacity": 60,
  "note": "全屏压暗遮罩"
 },
 {
  "id": "fc.mtab1",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_ftab_on.png",
  "x": 34,
  "y": 33,
  "w": 179,
  "h": 44,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "模式页签 1「序章」（PSB `modetabs/1` x34 y33 w179 h44）（素材 103×44 ≠ 设计 179×44 → nine {'l': 25, 't': 11, 'r': 25, 'b': 11}）",
  "nine": {
   "l": 25,
   "t": 11,
   "r": 25,
   "b": 11
  }
 },
 {
  "id": "fc.mtab1_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 34,
  "y": 33,
  "w": 179,
  "h": 44,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "序章",
  "note": "页签名（引擎绘制）"
 },
 {
  "id": "fc.mtab1_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 34,
  "y": 33,
  "w": 179,
  "h": 44,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "页签热区"
 },
 {
  "id": "fc.mtab2",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_ftab_off.png",
  "x": 304,
  "y": 33,
  "w": 157,
  "h": 44,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "模式页签 2「本篇」（PSB `modetabs/2` x304 y33 w157 h44）（素材 79×34 ≠ 设计 157×44 → nine {'l': 19, 't': 8, 'r': 19, 'b': 8}）",
  "nine": {
   "l": 19,
   "t": 8,
   "r": 19,
   "b": 8
  }
 },
 {
  "id": "fc.mtab2_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 304,
  "y": 33,
  "w": 157,
  "h": 44,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "本篇",
  "note": "页签名（引擎绘制）"
 },
 {
  "id": "fc.mtab2_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 304,
  "y": 33,
  "w": 157,
  "h": 44,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "页签热区"
 },
 {
  "id": "fc.mtab3",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_ftab_off.png",
  "x": 559,
  "y": 33,
  "w": 236,
  "h": 44,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "模式页签 3「After Story」（PSB `modetabs/3` x559 y33 w236 h44）（素材 79×34 ≠ 设计 236×44 → nine {'l': 19, 't': 8, 'r': 19, 'b': 8}）",
  "nine": {
   "l": 19,
   "t": 8,
   "r": 19,
   "b": 8
  }
 },
 {
  "id": "fc.mtab3_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 559,
  "y": 33,
  "w": 236,
  "h": 44,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "After Story",
  "note": "页签名（引擎绘制）"
 },
 {
  "id": "fc.mtab3_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 559,
  "y": 33,
  "w": 236,
  "h": 44,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "页签热区"
 },
 {
  "id": "fc.mtab4",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_ftab_off.png",
  "x": 859,
  "y": 33,
  "w": 193,
  "h": 44,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "模式页签 4「Fragment」（PSB `modetabs/1` x859 y33 w193 h44）（素材 79×34 ≠ 设计 193×44 → nine {'l': 19, 't': 8, 'r': 19, 'b': 8}）",
  "nine": {
   "l": 19,
   "t": 8,
   "r": 19,
   "b": 8
  }
 },
 {
  "id": "fc.mtab4_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 859,
  "y": 33,
  "w": 193,
  "h": 44,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "Fragment",
  "note": "页签名（引擎绘制）"
 },
 {
  "id": "fc.mtab4_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 859,
  "y": 33,
  "w": 193,
  "h": 44,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "页签热区"
 },
 {
  "id": "fc.titleplate",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_dress_top.png",
  "x": 58,
  "y": 93,
  "w": 385,
  "h": 68,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "标题牌（PSB `フローチャート/Flowchart` x58 y93 w385 h68）（素材 1946×122 ≠ 设计 385×68 → nine {'l': 0, 't': 0, 'r': 0, 'b': 0}）",
  "nine": {
   "l": 0,
   "t": 0,
   "r": 0,
   "b": 0
  }
 },
 {
  "id": "fc.title",
  "kind": "text",
  "z": 11,
  "visible_default": true,
  "x": 58,
  "y": 93,
  "w": 385,
  "h": 68,
  "font": {
   "size": 27,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "剧情流程图",
  "note": "屏标题（引擎绘制）"
 },
 {
  "id": "fc.scroll",
  "kind": "rect",
  "z": 5,
  "visible_default": true,
  "x": 60,
  "y": 190,
  "w": 1235,
  "h": 827,
  "color": "@palette.panel_edge",
  "opacity": 40,
  "note": "流程图滚动视口底（PSB `#rects/scroll` x60 y190 w1235 h827；程序化 rect）"
 },
 {
  "id": "fc.p_title",
  "kind": "rect",
  "z": 6,
  "visible_default": true,
  "x": 1416,
  "y": 214,
  "w": 443,
  "h": 73,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「标题」视口底（PSB `#rects/title` x1416 y214 w443 h73；程序化 rect）"
 },
 {
  "id": "fc.p_title_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1428,
  "y": 224,
  "w": 419,
  "h": 40,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "标题",
  "note": "「标题」标签（引擎绘制）"
 },
 {
  "id": "fc.p_text",
  "kind": "rect",
  "z": 6,
  "visible_default": true,
  "x": 1425,
  "y": 309,
  "w": 422,
  "h": 171,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「说明」视口底（PSB `#rects/text` x1425 y309 w422 h171；程序化 rect）"
 },
 {
  "id": "fc.p_text_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1437,
  "y": 319,
  "w": 398,
  "h": 40,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "说明",
  "note": "「说明」标签（引擎绘制）"
 },
 {
  "id": "fc.pbk_panel",
  "kind": "image",
  "z": 5,
  "visible_default": false,
  "asset": "ui/x_ui_replay_panel.png",
  "x": 1422,
  "y": 493,
  "w": 426,
  "h": 241,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py` 程序化合成）：`ui/x_ui_replay_panel.png` 426×241（浅底＋蓝边，来源＝既有面板件合成；参照作 `res58_フローチャート__シーン再生.png` 426×241、`UI布局规格.md:467`）。",
  "note": "★ 第 2 步补接线（2026-09-28 · ISSUE-20260928-02）：**场景回放窗底板**（参照作 `シーン再生` 426×241 @1422,493）。它比既有 `fc.p_player`（1423,495,424,237）四周各大 1–2px ⇒ **z 取 `fc.p_player`(z=6) − 1 = 5**，作其底板（同 z 时本件声明在前 ⇒ 亦不会反压）。`visible_default:false` 与 `fc.p_player` 的「**M34 互斥态分组：与 minimap 重叠、默认隐藏**」口径一致 —— 可见性由运行期 `ctx.forceShow` 抬起（`ui_widget.tjs:1499` 的 forceShow 优先于 `ui_screens.tjs:284` 的 `visible_default===false`，故**不是死件**；`vis_flag/vis_when` 为与本屏其余主干件同款的层归属声明，在该件上属**惰性**守卫）。426×241 与素材等尺寸 ⇒ **1:1、无 nine**。"
 },
 {
  "id": "fc.p_player",
  "kind": "rect",
  "z": 6,
  "visible_default": false,
  "x": 1423,
  "y": 495,
  "w": 424,
  "h": 237,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「场景回放」视口底（PSB `#rects/player` x1423 y495 w424 h237；程序化 rect）　★ M34 互斥态分组：与 minimap 重叠，默认隐藏。"
 },
 {
  "id": "fc.p_player_tx",
  "kind": "text",
  "z": 25,
  "visible_default": false,
  "x": 1435,
  "y": 505,
  "w": 400,
  "h": 40,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "场景回放",
  "note": "「场景回放」标签（引擎绘制）　★ M34 互斥态分组：与 minimap 重叠，默认隐藏。"
 },
 {
  "id": "fc.p_message",
  "kind": "rect",
  "z": 6,
  "visible_default": true,
  "x": 1425,
  "y": 750,
  "w": 422,
  "h": 171,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「台词」视口底（PSB `#rects/message` x1425 y750 w422 h171；程序化 rect）"
 },
 {
  "id": "fc.p_message_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1437,
  "y": 760,
  "w": 398,
  "h": 40,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "台词",
  "note": "「台词」标签（引擎绘制）"
 },
 {
  "id": "fc.smallmap",
  "kind": "rect",
  "z": 5,
  "visible_default": true,
  "x": 1416,
  "y": 190,
  "w": 443,
  "h": 829,
  "color": "@palette.panel_edge",
  "opacity": 40,
  "note": "缩略总览（minimap）底（PSB `#rects/smallmap` x1416 y190 w443 h829）"
 },
 {
  "id": "fc.mini1",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1450,
  "y": 240,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini2",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1650,
  "y": 240,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini3",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1450,
  "y": 390,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini4",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1650,
  "y": 390,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini5",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1450,
  "y": 540,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini6",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1650,
  "y": 540,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini7",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1450,
  "y": 690,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mini8",
  "kind": "rect",
  "z": 20,
  "visible_default": true,
  "x": 1650,
  "y": 690,
  "w": 150,
  "h": 70,
  "color": "@palette.node_available",
  "opacity": 180,
  "note": "缩略图节点块（程序化 rect）"
 },
 {
  "id": "fc.mapview",
  "kind": "rect",
  "z": 21,
  "visible_default": true,
  "x": 1440,
  "y": 225,
  "w": 380,
  "h": 300,
  "color": "@palette.accent",
  "opacity": 60,
  "note": "缩略图可视区框（程序化 rect）"
 },
 {
  "id": "fc.scr_up",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_scroll_up_off.png",
  "x": 1321,
  "y": 190,
  "w": 31,
  "h": 31,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_scroll_up_{off,over,on}.png` 31×31 ×3（参照作序号 10/22/26）。原为单态占位件 `ui/x_ui_arrow_up.png`（29×31）。",
  "note": "滚动上（PSB `ボタン/上` x1321 y190 w31 h31）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_scroll_up_{off,over,on}.png`（`asset`=`_off`），**删 nine{7,7,7,7}** —— 新件 31×31 **与元素 31×31 等尺寸 ⇒ 1:1、无拉伸**。★ 本批已知外观变化：静止态由 `arrow_up` 单态换成 `scroll_up` 常态件。★ **`action` 保持空串**：纵滚行为属编程组（冻结 §五）。",
  "state_assets": {
   "normal": "ui/x_ui_scroll_up_off.png",
   "hover": "ui/x_ui_scroll_up_over.png",
   "pressed": "ui/x_ui_scroll_up_on.png"
  }
 },
 {
  "id": "fc.scr_knob",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_scroll_knob.png",
  "x": 1321,
  "y": 556,
  "w": 31,
  "h": 73,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "滚动滑块（PSB `ボタン/滑块` x1321 y556 w31 h73）（素材 18×71 ≠ 设计 31×73 → nine {'l': 4, 't': 17, 'r': 4, 'b': 17}）",
  "nine": {
   "l": 4,
   "t": 17,
   "r": 4,
   "b": 17
  }
 },
 {
  "id": "fc.scr_dn",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_scroll_dn_off.png",
  "x": 1321,
  "y": 987,
  "w": 31,
  "h": 30,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_scroll_dn_{off,over,on}.png` 31×30 ×3（参照作序号 9/21/25）。原为单态占位件 `ui/x_ui_arrow_down.png`（29×31）。",
  "note": "滚动下（PSB `ボタン/下` x1321 y987 w31 h30）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_scroll_dn_{off,over,on}.png`（`asset`=`_off`），**删 nine{7,7,7,7}** —— 新件 31×30 **与元素 31×30 等尺寸 ⇒ 1:1、无拉伸**。★ 本批已知外观变化：静止态由 `arrow_down` 单态换成 `scroll_dn` 常态件。★ **`action` 保持空串**：纵滚行为属编程组。",
  "state_assets": {
   "normal": "ui/x_ui_scroll_dn_off.png",
   "hover": "ui/x_ui_scroll_dn_over.png",
   "pressed": "ui/x_ui_scroll_dn_on.png"
  }
 },
 {
  "id": "fc.scr_rail",
  "kind": "rect",
  "z": 19,
  "visible_default": true,
  "x": 1321,
  "y": 221,
  "w": 31,
  "h": 766,
  "color": "@palette.letterbox",
  "opacity": 140,
  "note": "滚动条轨（PSB `フローチャート/スクロールバー` 31×767）"
 },
 {
  "id": "fc.zoom_rail",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_zoom_rail.png",
  "x": 1047,
  "y": 112,
  "w": 270,
  "h": 31,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "缩放条轨（PSB `zoom/rail` x1047 y112 w270 h31）（素材 123×31 ≠ 设计 270×31 → nine {'l': 30, 't': 7, 'r': 30, 'b': 7}）",
  "nine": {
   "l": 30,
   "t": 7,
   "r": 30,
   "b": 7
  }
 },
 {
  "id": "fc.zoom_knob",
  "kind": "image",
  "z": 21,
  "visible_default": true,
  "asset": "ui/x_ui_zoom_knob.png",
  "x": 1174,
  "y": 112,
  "w": 40,
  "h": 31,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "缩放条滑块（PSB `zoom/slider` x1174 y112 w40 h31）（素材 29×16 ≠ 设计 40×31 → nine {'l': 7, 't': 4, 'r': 7, 'b': 4}）",
  "nine": {
   "l": 7,
   "t": 4,
   "r": 7,
   "b": 4
  }
 },
 {
  "id": "fc.zoom_minus",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_zoomout_off.png",
  "x": 1006,
  "y": 112,
  "w": 29,
  "h": 29,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_zoomout_{off,over,on}.png` **均为 29×29**（★ 第 5 批订正 · 2026-09-28 盘上复核实测：本字段原写「29×29 / 29×29 / 41×41」与素材不符，已改成现况；参照作序号 1/2/15）。原为单态占位件 `ui/x_ui_arrow_left.png`（29×31）。",
  "note": "缩放「－」（PSB `zoom/オフ/－`）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_zoomout_{off,over,on}.png`（`asset`=`_off`），**删 nine{0,0,0,0}**。★ **本批唯一的几何变更**：`29×8 @(1006,123)` → **`29×29 @(1006,112)`**（x 不变、y −11、h +21）。理由：旧 `29×8` 是参照作**细减号字形盒**（`版式规范 §1.1` 抄自 PSB），新素材是 **29×29 圆形键**（与 `fc.zoom_plus` 同规格）⇒ 按 1:1 落地并**与 `fc.zoom_plus`(1321,112,29×29) 及 `fc.zoom_rail`(y112,h31) 同带对齐**；旧 29×8 盒放 29×29 的键只能竖向压扁（3.6× 非等比），那是素材组明令要消除的类缺陷。★ 本批已知外观变化：静止态由 `arrow_left` 单态换成 `zoomout` 常态件，且矩形随之取正。★★ 第 5 批订正（2026-09-28 · 盘上复核）：三态（`off`/`over`/`on`）**均为 29×29**（原写「按下态 `_on`(41×41) 会被缩到 29×29」是**过期描述**）⇒ 三态与元素 29×29 **等尺寸 ⇒ 按下不放大**；原设计的「**按下放大**」**登记为缺口 G-2**（`state_assets` **无逐态几何** —— 只换位图、不改元素矩形；若要真放大，需机制扩展（按 state 改矩形）或复制成对元素）。★ **`action` 保持空串**：缩放行为属编程组。",
  "state_assets": {
   "normal": "ui/x_ui_zoomout_off.png",
   "hover": "ui/x_ui_zoomout_over.png",
   "pressed": "ui/x_ui_zoomout_on.png"
  }
 },
 {
  "id": "fc.zoom_plus",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_zoomin_off.png",
  "x": 1321,
  "y": 112,
  "w": 29,
  "h": 29,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_zoomin_{off,over,on}.png` **均为 29×29**（★ 第 5 批订正 · 2026-09-28 盘上复核实测：本字段原写「29×29 / 29×29 / 41×41」与素材不符，已改成现况；参照作序号 4/5/33）。原为单态占位件 `ui/x_ui_arrow_right.png`（29×31）。",
  "note": "缩放「＋」（PSB `zoom/オフ/＋` x1321 y112 w29 h29）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_zoomin_{off,over,on}.png`（`asset`=`_off`），**删 nine{0,0,0,0}** —— 新件 29×29 **与元素 29×29 等尺寸 ⇒ 1:1、无拉伸**，几何未动。★ 本批已知外观变化：静止态由 `arrow_right` 单态换成 `zoomin` 常态件。★★ 第 5 批订正（2026-09-28 · 盘上复核）：三态（`off`/`over`/`on`）**均为 29×29**（原写「按下态 `_on`(41×41) 被缩到 29×29」是**过期描述**）⇒ 按下不放大；原设计的「**按下放大**」**登记为缺口 G-2**（`state_assets` **无逐态几何** —— 只换位图、不改元素矩形；要真放大需机制扩展或复制成对元素）。★ **`action` 保持空串**：缩放行为属编程组。",
  "state_assets": {
   "normal": "ui/x_ui_zoomin_off.png",
   "hover": "ui/x_ui_zoomin_over.png",
   "pressed": "ui/x_ui_zoomin_on.png"
  }
 },
 {
  "id": "fc.shift_rail",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_shift_rail.png",
  "x": 130,
  "y": 1018,
  "w": 1094,
  "h": 25,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "平移条轨（PSB `shift/rail` x130 y1018 w1094 h25）（素材 80×25 ≠ 设计 1094×25 → nine {'l': 20, 't': 6, 'r': 20, 'b': 6}）",
  "nine": {
   "l": 20,
   "t": 6,
   "r": 20,
   "b": 6
  }
 },
 {
  "id": "fc.shift_knob",
  "kind": "image",
  "z": 21,
  "visible_default": true,
  "asset": "ui/x_ui_shift_knob.png",
  "x": 466,
  "y": 1018,
  "w": 73,
  "h": 25,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "平移条滑块（PSB `shift/slider` x466 y1018 w73 h25）（素材 16×25 ≠ 设计 73×25 → nine {'l': 4, 't': 6, 'r': 4, 'b': 6}）",
  "nine": {
   "l": 4,
   "t": 6,
   "r": 4,
   "b": 6
  }
 },
 {
  "id": "fc.shift_lf",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_shift_lf_off.png",
  "x": 100,
  "y": 1018,
  "w": 31,
  "h": 25,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_shift_lf_{off,over,on}.png` 31×25 ×3（参照作序号 7/19/23）。原为单态占位件 `ui/x_ui_arrow_left.png`（29×31）。",
  "note": "平移「左」（PSB `shift/ボタン/オフ/左` x100 y1018 w31 h25）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_shift_lf_{off,over,on}.png`（`asset`=`_off`），**删 nine{7,7,7,7}** —— 新件 31×25 **与元素 31×25 等尺寸 ⇒ 1:1、无拉伸**，几何未动。★ 本批已知外观变化：静止态由 `arrow_left` 单态换成 `shift_lf` 常态件。★ **`action` 保持空串**：横移行为属编程组。",
  "state_assets": {
   "normal": "ui/x_ui_shift_lf_off.png",
   "hover": "ui/x_ui_shift_lf_over.png",
   "pressed": "ui/x_ui_shift_lf_on.png"
  }
 },
 {
  "id": "fc.shift_rg",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_shift_rg_off.png",
  "x": 1224,
  "y": 1018,
  "w": 30,
  "h": 25,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py`）：`ui/x_ui_shift_rg_{off,over,on}.png` 30×25 ×3（参照作序号 8/18/24）。原为单态占位件 `ui/x_ui_arrow_right.png`（29×31）。",
  "note": "平移「右」（PSB `shift/ボタン/オフ/右` x1224 y1018 w30 h25）★ 第 2 步补接线（2026-09-28）：换真三态 `x_ui_shift_rg_{off,over,on}.png`（`asset`=`_off`），**删 nine{7,7,7,7}** —— 新件 30×25 **与元素 30×25 等尺寸 ⇒ 1:1、无拉伸**，几何未动。★ 本批已知外观变化：静止态由 `arrow_right` 单态换成 `shift_rg` 常态件。★ **`action` 保持空串**：横移行为属编程组。",
  "state_assets": {
   "normal": "ui/x_ui_shift_rg_off.png",
   "hover": "ui/x_ui_shift_rg_over.png",
   "pressed": "ui/x_ui_shift_rg_on.png"
  }
 },
 {
  "id": "fc.jump",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_jumpfc_off.png",
  "x": 1474,
  "y": 943,
  "w": 328,
  "h": 61,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "「读取剧情」键（PSB `ボタン/オフ/シナリオを読み込む` x1474 y943 w328 h61）（素材 157×61 ≠ 设计 328×61 → nine {'l': 39, 't': 15, 'r': 39, 'b': 15}）★ M43（2026-09-23，用户裁定）：本键现承担「进入本章」（动作 `flow_enter`，热区见 fc.jump_hit、文案见 fc.jump_tx）。",
  "nine": {
   "l": 39,
   "t": 15,
   "r": 39,
   "b": 15
  }
 },
 {
  "id": "fc.jump_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1474,
  "y": 943,
  "w": 328,
  "h": 61,
  "font": {
   "size": 27,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "进入本章",
  "note": "按钮文字（引擎绘制）★ M43（2026-09-23，用户裁定）：文案由「读取剧情」改为「进入本章」。原 PSB 标签是 `ボタン/オフ/シナリオを読み込む`（= 读取剧情）；`chapter` 屏删除后，「进入剧情」的能力由本键承担，故按用户裁定改名。动作名 = `flow_enter`（见 fc.jump_hit）。"
 },
 {
  "id": "fc.jump_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 1474,
  "y": 943,
  "w": 328,
  "h": 61,
  "action": "flow_enter",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "「进入本章」热区（PSB 原按钮 `ボタン/#rect` 的 1:1 复刻位）。★ M43（2026-09-23，用户裁定）：接上新动作 `flow_enter` —— 取当前光标节点 UIFlowCursor：未解锁 → 只提示解锁条件、不进剧情；已解锁 → 标记该节点已读 + 置当前节点 + 存状态，然后重置对话框并进入 dialog 屏（与原 `chapter` 屏的 `chapter_enter` 同口径，该屏已删除）。两端实现：krkr `ui_flow.tjs::uiFlowEnterCurrent()` ／ HTML `replica.js::flowEnter()`。"
 },
 {
  "id": "fc.fusen_edit",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_fusen_off.png",
  "x": 499,
  "y": 99,
  "w": 145,
  "h": 48,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "「编辑备注」键（PSB `fusen/オフ/编辑备注` x499 y99 w145 h48）（素材 86×48 ≠ 设计 145×48 → nine {'l': 21, 't': 12, 'r': 21, 'b': 12}）★ 第 2 步（2026-09-28 · ISSUE-20260928-02 · 接口冻结 §三 · **E1 接线**）：三态件**已存在**（`x_ui_fusen_{off,over,on}.png` ＝ 86×48 / 86×48 / 108×60）⇒ 补 `state_assets{normal,hover,pressed}`（**不产新件**）；`_on` 物理尺寸 108×60 经同一 nine 落到 145×48。",
  "nine": {
   "l": 21,
   "t": 12,
   "r": 21,
   "b": 12
  },
  "state_assets": {
   "normal": "ui/x_ui_fusen_off.png",
   "hover": "ui/x_ui_fusen_over.png",
   "pressed": "ui/x_ui_fusen_on.png"
  }
 },
 {
  "id": "fc.fusen_edit_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 499,
  "y": 99,
  "w": 145,
  "h": 48,
  "font": {
   "size": 20,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "编辑备注",
  "note": "按钮文字（引擎绘制）"
 },
 {
  "id": "fc.fusen_edit_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 499,
  "y": 99,
  "w": 145,
  "h": 48,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "「编辑备注」热区"
 },
 {
  "id": "fc.fusen_reset",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_fusen_off.png",
  "x": 679,
  "y": 99,
  "w": 145,
  "h": 48,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "「备注初始化」键（PSB `fusen/オフ/备注初始化` x679 y99 w145 h48）（素材 86×48 ≠ 设计 145×48 → nine {'l': 21, 't': 12, 'r': 21, 'b': 12}）★ 第 2 步（2026-09-28 · ISSUE-20260928-02 · 接口冻结 §三 · **E1 接线**）：同 `fc.fusen_edit`，补三态 `state_assets`（**不产新件**）。",
  "nine": {
   "l": 21,
   "t": 12,
   "r": 21,
   "b": 12
  },
  "state_assets": {
   "normal": "ui/x_ui_fusen_off.png",
   "hover": "ui/x_ui_fusen_over.png",
   "pressed": "ui/x_ui_fusen_on.png"
  }
 },
 {
  "id": "fc.fusen_reset_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 679,
  "y": 99,
  "w": 145,
  "h": 48,
  "font": {
   "size": 20,
   "bold": true,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "备注初始化",
  "note": "按钮文字（引擎绘制）"
 },
 {
  "id": "fc.fusen_reset_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 679,
  "y": 99,
  "w": 145,
  "h": 48,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "「备注初始化」热区"
 },
 {
  "id": "fc.pbkick",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_pbkick_off.png",
  "x": 1576,
  "y": 555,
  "w": 119,
  "h": 119,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py` 程序化合成）：`ui/x_ui_pbkick_{off,over,on}.png` 119×119 ×3（参照作 `res39/50/54/57/67/69`：off 圆环内 ▶、on 内 ■）。原素材为旧占位件 `ui/x_ui_branch_l.png`（分支底座，语义不符），已由本批替换。",
  "note": "场景回放键（PSB `pbkick/@pbkick:n:off` x1576 y555 w119 h119）★ 第 2 步补接线（2026-09-28 · ISSUE-20260928-02 · 冻结 §三 · **主代理裁决 2026-09-28「接」**）：静止态素材由**旧占位件** `x_ui_branch_l.png` 换成真三态件 `x_ui_pbkick_{off,over,on}.png`（`asset` = `_off`，另补 `state_assets{normal,hover,pressed}`）；**同时删除 `nine{29,29,29,29}`** —— 旧 nine 继承自 `branch_l`（118×119），新件 119×119 **与元素 119×119 等尺寸 ⇒ 1:1、无拉伸**，留着 nine 属埋雷（素材组实测其九宫格边界列/行步进 0.70/0.00）。★ **本批已知外观变化**：本件静止态由「分支底座占位图」变为「真回放键图形」（＝本次要修的缺口）。",
  "state_assets": {
   "normal": "ui/x_ui_pbkick_off.png",
   "hover": "ui/x_ui_pbkick_over.png",
   "pressed": "ui/x_ui_pbkick_on.png"
  }
 },
 {
  "id": "fc.pbkick_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 1573,
  "y": 552,
  "w": 125,
  "h": 125,
  "action": "",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "场景回放热区"
 },
 {
  "id": "fc.close",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_close_off.png",
  "x": 1843,
  "y": 177,
  "w": 26,
  "h": 26,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "关闭键（PSB `close/off` x1843 y177 w26 h26）（素材 24×26 ≠ 设计 26×26 → nine {'l': 6, 't': 6, 'r': 6, 'b': 6}） ★ M35b：接收原热区 `fc.close_hit` 的三态图（热区矩形是 PSB 的交互区，比美术大得多，由热区画会拉伸涂抹）——美术在 1:1/九宫格口径下画，与热区用 state_group「flowchart.close」联动。",
  "nine": {
   "l": 6,
   "t": 6,
   "r": 6,
   "b": 6
  },
  "state_assets": {
   "normal": "ui/x_ui_close_off.png",
   "hover": "ui/x_ui_close_over.png",
   "pressed": "ui/x_ui_close_on.png"
  },
  "state_group": "flowchart.close"
 },
 {
  "id": "fc.close_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 1830,
  "y": 159,
  "w": 56,
  "h": 56,
  "action": "close",
  "label": "",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "关闭热区（PSB `close/#rect`） ★ M35b：**退回纯热区**（不再持有美术，避免按热区矩形拉伸绘制）；三态图改由同矩形的 image `fc.close` 绘制，两者 state_group「flowchart.close」联动。",
  "state_group": "flowchart.close"
 },
 {
  "id": "fc.sysbar",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "asset": "ui/x_ui_sysbar.png",
  "x": 1227,
  "y": 32,
  "w": 648,
  "h": 41,
  "opacity": 255,
  "source": "AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；坐标取自《交汇协奏曲》PSB 容器",
  "note": "系统共通条（PSB `システム共通` x1227 y32 w648 h41）（素材 1946×292 ≠ 设计 648×41 → nine {'l': 0, 't': 0, 'r': 0, 'b': 0}）",
  "nine": {
   "l": 0,
   "t": 0,
   "r": 0,
   "b": 0
  }
 }
]"""


def load_static_elements():
    return json.loads(STATIC_ELEMENTS_JSON)


# ══════════════════════════════════════════════════════════════════════
# 输入读取
# ══════════════════════════════════════════════════════════════════════
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data(path=DATA_HTML):
    """从 08_全系列章节流程图.html 取内嵌 `const DATA = {…}`（单行 JSON）。

    ★ 契约：正则取 `const DATA = ` 与 `\\nconst N = ` 之间、去尾分号后 json.loads；**不解析 DOM**。
    """
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    i = s.index("const DATA = ")
    j = s.index("\nconst N = ", i)
    body = s[i + len("const DATA = "):j].strip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def load_spine(path=SPINE_JSON):
    return load_json(path)


def load_canvas():
    return load_json(ROOT_JSON)["canvas"]


def load_palette_colors():
    """palette.json 的 colors 段（键 → 值）。"""
    return load_json(PALETTE)["colors"]


def resolve_palette_int(key):
    """色板键 → 0xAARRGGBB 整数（禁止直写色值）。"""
    cols = load_palette_colors()
    if key not in cols:
        raise SystemExit("[FAIL] palette.json 缺色键 %s（色值禁止直写）" % key)
    hexv = str(cols[key]["value"]).lstrip("#")
    return 0xFF000000 | int(hexv, 16)


def load_link_color(key=LINK_COLOR_KEY):
    """连线色：只从 palette.json 解析成 0xAARRGGBB 整数（禁止直写色值）。

    ★ 第 2 步起按 `state` 逐条解析（键 ∈ edge_normal / edge_visited / edge_noroute）。
    """
    return resolve_palette_int(key)


def edge_style(state):
    """连线 `state` → (palette 键, w, arrow)。冻结 §一.2 的硬表，两端不做判断。"""
    if state not in EDGE_STATES:
        raise SystemExit("[FAIL] 非法 links[].state：%r（只允许 %s）" % (state, list(EDGE_STATES)))
    return EDGE_STATES[state]


# ══════════════════════════════════════════════════════════════════════
# 节点类型映射（契约 §二 kind ∈ section|select|frag；§四 branch 只出底座）
# ══════════════════════════════════════════════════════════════════════
def node_kind(v):
    r"""DATA 节点 → 显示种类。

    · DATA.kind == "branch"                       → branch（只出分支底座，不出节点框）
    · DATA.phase == ""（53 件，与 spine.side_stories 数量一致）→ frag（番外）
    · 多臂 / next_kind=="branch" / choiceN>0      → select（有分歧）
    · 其余                                        → section
    依据：`_工作\ISSUE-20260927-04_流程图\侦察_数据与现状.md` §1.2（kind 4 值）＋ §一.1（side_stories 53）。
    """
    if v.get("kind") == "branch":
        return "branch"
    if v.get("phase", None) == "":
        return "frag"
    if len(v.get("next") or []) > 1 or v.get("next_kind") == "branch" or int(v.get("choiceN") or 0) > 0:
        return "select"
    return "section"


# ══════════════════════════════════════════════════════════════════════
# 连线路由（契约 §三 —— 生成器算好 pts，两端只描线）
# ══════════════════════════════════════════════════════════════════════
def route_pts(a, b, kind_a):
    """a/b = 节点槽位 dict(x,y)；kind_a = 源节点显示种类。返回 (形态, pts)。

    sx = ax+148（源节点中线 x）｜sy = ay+65（源节点底边）｜tx = bx+148｜ty = by（目标顶边）
    padding=0（无端点内缩）；直线 / VZ（Z 形）/ VL（侧出）三形态与参照作解包实现同构。
    """
    sx, sy = a["x"] + NODE_W // 2, a["y"] + NODE_H
    tx, ty = b["x"] + NODE_W // 2, b["y"]
    if tx == sx:
        return "line", [[sx, sy], [tx, ty]]
    if kind_a not in ("select", "branch"):
        my = (sy + ty) // 2                      # 契约写 (sy+ty)/2；取整以保证两端像素可比
        return "vz", [[sx, sy], [sx, my], [tx, my], [tx, ty]]
    ex = sx + VL_LATERAL if tx > sx else sx - VL_LATERAL
    return "vl", [[ex, sy - NODE_H // 2], [tx, sy - NODE_H // 2], [tx, ty]]


def dedupe_pts(pts):
    """去掉相邻重复点（门 ⑤：pts 无重复相邻点）。零长段删除不影响末段方向。"""
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return out


# ══════════════════════════════════════════════════════════════════════
# 文字容量（复刻 krkr\game\ui_theme.tjs::uiThemeLayoutText / uiThemeWrap）
# ══════════════════════════════════════════════════════════════════════
NOHEAD = "、。，．！？：；）」』】》〉”’!?,.:;)]}"      # ui_theme.tjs:33（不允许出现在行首）
NOTAIL = "（「『【《〈“‘([{"                           # ui_theme.tjs:35（不允许出现在行尾）


def width_fn(size=TEXT_SIZE):
    """返回 width_of(str)->float。优先用 PIL + 系统字体（与引擎 fallback_faces[0] 同族）实测。"""
    try:
        from PIL import ImageFont
        faces = ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"]
        for p in faces:
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                return (lambda s: float(f.getlength(s))), "PIL:%s@%d" % (os.path.basename(p), size)
    except Exception:
        pass

    def approx(s):
        w = 0.0
        for ch in s:
            w += size * (1.0 if ord(ch) >= 0x2E80 else 0.5)
        return w
    return approx, "class-width(近似: CJK=size, ASCII=0.5size)"


def ui_theme_wrap(text, maxW, maxLines, wof):
    """逐字复刻 uiThemeWrap（ui_theme.tjs:314-364）。返回 (lines, truncated)。"""
    out = []
    truncated = False
    for para in ("%s" % text).split("\n"):
        if para == "":
            out.append("")
            continue
        line = ""
        for ch in para:
            cand = line + ch
            if wof(cand) <= maxW or line == "":
                line = cand
                continue
            if ch in NOHEAD:            # 行首禁则：强行并入本行
                line = cand
                continue
            carry = ""
            if line and line[-1] in NOTAIL:   # 行尾禁则：末字挪到下一行
                carry = line[-1]
                line = line[:-1]
            out.append(line)
            line = carry + ch
        if line != "" or para == "":
            out.append(line)
    if maxLines and maxLines > 0 and len(out) > maxLines:
        truncated = True
        while len(out) > maxLines:
            out.pop()
    return out, truncated


def line_height(size=TEXT_SIZE, spacing=1.4):
    """ui_theme.tjs:237 —— lineH = max(size, floor(size×spacing))；spacing 缺省 = fonts.line_spacing.body = 1.4。"""
    lh = int(size * spacing)
    return max(size, lh)


def measure_plate(kind):
    """实测某类节点底图的**可见实体面**（逐行平均 alpha>200 的行区间）。

    返回 (top, bottom)；无 PIL / 文件缺失时回落到记录值 PLATE_ROWS[kind]。
    口径：`_off`（normal，默认态）那张；实测值见 PLATE_ROWS 注释。
    """
    asset = NODE_ASSET.get(kind, ("", ""))[0].split("/")[-1]
    path = os.path.join(UI, "krkr", "assets", "ui", asset) if asset else ""
    try:
        from PIL import Image
        import numpy as np
        if path and os.path.exists(path):
            im = Image.open(path).convert("RGBA")
            a = np.array(im.getchannel("A"), dtype=float)
            rows = a.mean(axis=1)
            solid = [i for i, v in enumerate(rows) if v > 200]
            if solid:
                return (solid[0], solid[-1])
    except Exception:
        pass
    return PLATE_ROWS.get(kind, PLATE_ROWS["section"])


def check_text_criteria(data_nodes, size=None, spacing=None, box_w=None, max_lines=None):
    r"""★ 修正轮四判据（逐条实测；判据 A/B **对准可见实体面**，不是元素高）。

      plate          = 该 kind 底图的可见实体面行区间（section/frag 8..55、select 8..56；取**最紧**的 (8,55)）
      lineH          = max(size, floor(size × spacing))          （引擎 ui_theme.tjs:237 同式）
      块顶           = floor((元素高 − 行数×lineH) / 2)             （valign:"middle"，同 uiThemeLayoutText）
      首行墨迹顶     = 块顶
      末行墨迹底     = 块顶 + (行数−1)×lineH + (size−1)
      A 首行上留 = 首行墨迹顶 − plate 上沿 ≥ 5px
      B 末行下留 = plate 下沿 − 末行墨迹底 ≥ 5px
      C 任一行横向墨迹宽 ≤ 263px（可见实体面宽实测 ≈282 ⇒ 左右各留 ≥9px）
      D 712/712 零截断（max_lines=2）

    返回 dict（min_top, min_bottom, max_ink, widest, trunc, n_two, plate, fails[]）。

    ★ 第 9 批：文本取 `title_sample()`（**已应用 `TITLE_HARD_BREAK` 硬换行**），且按 `\n` **分段**
    各自折行（与引擎 `uiThemeWrap` 同式）—— 否则判据算的不是真正上屏的那几行。
    """
    size = TEXT_SIZE if size is None else size
    spacing = TEXT_LINE_SPACING if spacing is None else spacing
    box_w = TEXT_W if box_w is None else box_w
    max_lines = TEXT_MAX_LINES if max_lines is None else max_lines
    wof, src = width_fn(size)
    lineH = line_height(size, spacing)
    # 最紧实体面：上沿取各类最大、下沿取各类最小（select 更宽松，不能替 section/frag 背书）
    tops = [v[0] for v in PLATE_ROWS.values()]
    bots = [v[1] for v in PLATE_ROWS.values()]
    plate = (max(tops), min(bots))
    min_top = min_bottom = 10 ** 9
    max_ink = 0.0
    widest = ("", "")
    trunc = 0
    n_two = 0
    for k, v in data_nodes.items():
        t = title_sample(k, v)
        lines = []
        for seg in t.split("\n"):
            seg_lines, tr = ui_theme_wrap(seg, box_w, max_lines, wof)
            if tr:
                trunc += 1
            lines.extend(seg_lines)
        n = len(lines)
        if n == max_lines:
            n_two += 1
        bt = (NODE_H - n * lineH) // 2
        ib = bt + (n - 1) * lineH + (size - 1)
        min_top = min(min_top, bt - plate[0])
        min_bottom = min(min_bottom, plate[1] - ib)
        for l in lines:
            wd = wof(l)
            if wd > max_ink:
                max_ink = wd
                widest = (k, t)
    fails = []
    if min_top < PLATE_MARGIN_MIN:
        fails.append("判据A：首行上留最小 %dpx < %dpx" % (min_top, PLATE_MARGIN_MIN))
    if min_bottom < PLATE_MARGIN_MIN:
        fails.append("判据B：末行下留最小 %dpx < %dpx" % (min_bottom, PLATE_MARGIN_MIN))
    if max_ink > 263:
        fails.append("判据C：最宽行墨迹 %.1fpx > 263px（%s「%s」）" % (max_ink, widest[0], widest[1]))
    if trunc:
        fails.append("判据D：截断 %d 条 > 0" % trunc)
    return {"size": size, "spacing": spacing, "box_w": box_w, "lineH": lineH, "plate": plate,
            "min_top": min_top, "min_bottom": min_bottom, "max_ink": max_ink, "widest": widest,
            "trunc": trunc, "n_two": n_two, "src": src, "fails": fails}


# ══════════════════════════════════════════════════════════════════════
# ★ 第 9 批：「已读对勾」不变量（首行墨迹左缘 ≥ x_node + 30）
# ══════════════════════════════════════════════════════════════════════
def assert_break_table_keys():
    r"""★ 第 10 批补的守卫（一审指出）：`TITLE_HARD_BREAK` 的键集**必须 ⊆ 源语料键集**。

    原先幻影 id（源里没有该节点的条目）不被任何判据检出、只会被静默忽略 ⇒ 「表已过期」有覆盖空档。
    ⚠ 必须用**全量**语料比：`check_title_first_line` 会被 `m03` 以**独立层子集**调用，
    故守卫**不能**放在那里（第 10 批首版就犯过这个错，被 `m03` 当场抓出来）。
    """
    nodes = load_data()["nodes"]
    unknown = [k for k in TITLE_HARD_BREAK if k not in nodes]
    if unknown:
        raise SystemExit("[FAIL] TITLE_HARD_BREAK 里有**源语料中不存在的 id**：%s ⇒ 表已过期"
                         "（幻影 id 只会被静默忽略，故此处硬拦）" % unknown)


def check_title_first_line(data_nodes, hard=None, size=None, box_w=None, max_lines=None):
    r"""逐条复算**首行墨迹左缘**：`(NODE_W − box_w)/2 + (box_w − w0)/2`，须 ≥ `TITLE_CHECK_GAP`（第 10 批起为 **34**；第 9 批曾为 30）。

    `hard` 可传入**替代表**（变异自证用：传 `{}` 即「去掉全部硬断行」）。
    返回 (violations, stat)：violations = [(nid, title_repr, w0, left, lines)]；
    stat = (min_left, min_left_id, n_checked, n_two, max_line_ink)。
    """
    hard = TITLE_HARD_BREAK if hard is None else hard
    size = TEXT_SIZE if size is None else size
    box_w = TEXT_W if box_w is None else box_w
    max_lines = TEXT_MAX_LINES if max_lines is None else max_lines
    wof, _src = width_fn(size)
    off = (NODE_W - box_w) // 2
    viol, min_left, min_id, n_two, max_ink = [], 10 ** 9, "", 0, 0.0
    for nid, v in data_nodes.items():
        base = v.get("cn") or v.get("script") or nid
        parts = hard.get(nid)
        t = "\n".join(parts) if parts else base
        lines = []
        for seg in t.split("\n"):
            seg_lines, _tr = ui_theme_wrap(seg, box_w, max_lines, wof)
            lines.extend(seg_lines)
        if len(lines) == max_lines:
            n_two += 1
        w0 = wof(lines[0]) if lines else 0.0
        left = off + (box_w - w0) / 2.0
        max_ink = max(max_ink, max((wof(l) for l in lines), default=0.0))
        if left < min_left:
            min_left, min_id = left, nid
        if left < TITLE_CHECK_GAP:
            viol.append((nid, t.replace("\n", "⏎"), w0, left, len(lines)))
    return viol, (min_left, min_id, len(data_nodes), n_two, max_ink)


def title_check_report(nodes):
    assert_break_table_keys()
    r"""`--title-check-report`：不变量实测（逐条列违规 + 最紧一条），只读不落盘。"""
    data = nodes if isinstance(nodes, dict) else load_data()["nodes"]
    viol, (min_left, min_id, n, n_two, max_ink) = check_title_first_line(data)
    print("=" * 78)
    print("gen_flow_layout.py · --title-check-report（第 9/10 批「已读对勾」不变量：+30 ⇒ +34 收紧）")
    print("  不变量：**首行墨迹左缘 ≥ x_node + %d**（对勾 20×20 @(x+10,y+12) ⇒ 右缘 +30）"
          "；等价判据：首行墨迹 ≤ %dpx" % (TITLE_CHECK_GAP, TEXT_W - 2 * (TITLE_CHECK_GAP - (NODE_W - TEXT_W) // 2)))
    print("  文字盒宽 %d（左缘 x_node+%d，居中）｜ 断行表 `TITLE_HARD_BREAK` %d 条（目标两行 ≤ %dpx）"
          % (TEXT_W, (NODE_W - TEXT_W) // 2, len(TITLE_HARD_BREAK), TITLE_BREAK_MAX_LINE))
    print("  复算 %d 条：**最紧** 首行左缘 %+.2f（%s）｜ 两行条数 %d ｜ 全量最宽行 %.1fpx"
          % (n, min_left, min_id, n_two, max_ink))
    print("  违规（左缘 < +%d）：**%d 条**" % (TITLE_CHECK_GAP, len(viol)))
    for nid, t, w0, left, ln in viol:
        print("      ✗ %-10s 首行 %.1fpx 左缘 %+.2f（%d 行）｜「%s」" % (nid, w0, left, ln, t))
    print("=" * 78)
    return 0 if not viol else 1


def selfcheck_title_break():
    assert_break_table_keys()
    r"""**变异自证**（内存构造，不落盘）：证明「首行左缘 ≥ +30」这条自检**非恒真**。

    · 正向：用真表跑 ⇒ 违规 0（现状成立）；
    · 变异：把 `TITLE_HARD_BREAK` 换成**去掉指定一条**（默认 `62_1b`，即全量最紧的那条）
      ⇒ 该条必然越线、自检必须失败；
    · 反向对照：把表换成 `{}`（全去掉）⇒ 违规条数必须 ≥ 12（与 vision 全量复算的 12 条一致）。
    """
    import copy
    data = load_data()["nodes"]
    ok = True
    viol_real, (min_left, min_id, n, _n2, _mi) = check_title_first_line(data)
    print("=" * 78)
    print("交付自检 · 变异自证（第 9 批「首行墨迹左缘 ≥ +%d」不变量，不落盘）" % TITLE_CHECK_GAP)
    print("  ① 真表：违规 **%d 条**（最紧 %+.2f＝%s）%s"
          % (len(viol_real), min_left, min_id, "✓" if not viol_real else " ✗ 不符合预期"))
    ok = ok and (not viol_real)
    mut = copy.deepcopy(TITLE_HARD_BREAK)
    drop = "62_1b" if "62_1b" in mut else sorted(mut)[0]
    planted = mut.pop(drop)
    viol_mut, (ml2, mi2, _n, _n2, _mi) = check_title_first_line(data, hard=mut)
    hit = [v for v in viol_mut if v[0] == drop]
    print("  ② 变异（删去 %s 的硬断行 %r）：违规 **%d 条**，其中 %s %s ｜ 最紧 %+.2f（%s）"
          % (drop, "⏎".join(planted), len(viol_mut), drop,
             "**已越线** ✓" if hit else "**未越线** ✗（自检可能恒真）", ml2, mi2))
    if not hit:
        ok = False
    viol_none, _st3 = check_title_first_line(data, hard={})
    print("  ③ 反向对照（表清空）：违规 **%d 条**%s（表内 %d 条全部退回 +20~+32）"
          % (len(viol_none), " ✓" if len(viol_none) >= len(TITLE_HARD_BREAK) else " ✗ 少于表内条数",
             len(TITLE_HARD_BREAK)))
    if len(viol_none) < len(TITLE_HARD_BREAK):
        ok = False
    print("  自证结果：%s" % ("**按预期** ✓（真表 0 违规；删一条必越线；清空表 ≥ 表内条数 ⇒ 非恒真）"
                             if ok else "**不符合预期** ✗"))
    return 0 if ok else 1


def text_fit_report(nodes, data_nodes):
    r"""文字容量与**竖向**四判据实测（修正轮 · 判据对准「可见实体面」）。

    根因：上一轮把竖向容量判在**元素高 65** 上；三类底图的**可见实体面**（逐行平均 alpha>200）
    只有 48–49px（section/frag rows 8..55、select 8..56）⇒ 23px 两行墨迹跨度 58px 越出实体面，
    实机表现为第一行「切头」（vision 实测上溢 7–8px）。本轮判据：

      ① A 首行上留 = 首行墨迹顶 − 实体面上沿 ≥ 5px
      ② B 末行下留 = 实体面下沿 − 末行墨迹底 ≥ 5px
      ③ C 任一行横向墨迹宽 ≤ 263px（可见实体面宽实测 ≈282 ⇒ 左右各留 ≥9px）
      ④ D 712/712 零截断（max_lines=2）
    """
    tc = check_text_criteria(data_nodes)
    print("=" * 78)
    print("文字四判据实测（复刻 krkr\\game\\ui_theme.tjs::uiThemeLayoutText；含行首/行尾禁则）")
    print("  当前取值：字号 %d ｜ **行距 %s**（元素级 `line_spacing`）｜ 文字盒宽 %d ｜ max_lines %d ｜ 元素高 %d"
          % (tc["size"], tc["spacing"], tc["box_w"], TEXT_MAX_LINES, NODE_H))
    print("  lineH = max(size, floor(size×spacing)) = %d ｜ 字宽来源：%s" % (tc["lineH"], tc["src"]))
    print("=" * 78)

    print("\n【可见实体面实测（逐行平均 alpha>200；`_off` 常态件）】")
    for kind in ("section", "select", "frag"):
        t, b = measure_plate(kind)
        print("  %-8s rows %d..%d（高 %d）｜记录值 %s%s"
              % (kind, t, b, b - t + 1, PLATE_ROWS[kind],
                 "" if (t, b) == PLATE_ROWS[kind] else "  ← 与记录值不同，需复核"))
    print("  取**最紧**的 (上沿 max, 下沿 min) = %s 作四判据基准（select 更宽松，不能替 section/frag 背书）"
          % (tc["plate"],))

    print("\n【四判据 · 全量 712 条实测】")
    print("  ① 首行上留最小 = **%dpx**（要求 ≥%d）%s"
          % (tc["min_top"], PLATE_MARGIN_MIN, "✓" if tc["min_top"] >= PLATE_MARGIN_MIN else "✗"))
    print("  ② 末行下留最小 = **%dpx**（要求 ≥%d）%s"
          % (tc["min_bottom"], PLATE_MARGIN_MIN, "✓" if tc["min_bottom"] >= PLATE_MARGIN_MIN else "✗"))
    print("  ③ 最宽行墨迹   = **%.1fpx**（要求 ≤263）%s%s"
          % (tc["max_ink"], "✓" if tc["max_ink"] <= 263 else "✗",
             "  最宽：%s「%s」" % tc["widest"] if tc["widest"][0] else ""))
    print("  ④ 截断         = **%d 条**（要求 0）%s ｜ 两行标题 %d 条 / 单行 %d 条"
          % (tc["trunc"], "✓" if tc["trunc"] == 0 else "✗", tc["n_two"], len(data_nodes) - tc["n_two"]))
    if tc["fails"]:
        print("  ⇒ **不达标**：" + "；".join(tc["fails"]))
    else:
        print("  ⇒ **四判据全绿**")

    print("\n【字号上限推导（新竖向判据下）】")
    print("  两行时 块顶 = floor((%d − 2×lineH)/2) ≥ plate 上沿 + %d = %d ⇒ 2×lineH ≤ %d ⇒ lineH ≤ %.1f"
          % (NODE_H, PLATE_MARGIN_MIN, tc["plate"][0] + PLATE_MARGIN_MIN,
             NODE_H - 2 * (tc["plate"][0] + PLATE_MARGIN_MIN), (NODE_H - 2 * (tc["plate"][0] + PLATE_MARGIN_MIN)) / 2.0))
    print("  且 lineH = max(size, floor(size×spacing)) ≥ size ⇒ **字号上限 = 19**（用户 V2 裁决的 19px 恰为上限解）")
    print("  穷举对照（行距 1.0；带 plate 判据）：")
    for f in range(16, 23):
        c = check_text_criteria(data_nodes, size=f, spacing=1.0, box_w=TEXT_W)
        print("    f=%2d ⇒ 上留 %2dpx 下留 %2dpx 最宽 %5.1fpx 截断 %d  %s"
              % (f, c["min_top"], c["min_bottom"], c["max_ink"], c["trunc"],
                 "✓ 全绿" if not c["fails"] else "✗ " + "；".join(c["fails"])))
    print("  （旧备选档 f=21/w=251、f=22/w=240 在**新竖向判据下 A/B 全不达标**，已作废。）")

    print("\n【三档（引擎侧折行结果，供 E3 做两端渲染比对）】")

    def pick(n):
        c = [k for k, v in data_nodes.items() if len(v["cn"]) == n]
        c.sort(key=lambda k: (data_nodes[k]["seq"] if isinstance(data_nodes[k]["seq"], int) else 0, k))
        return c[0] if c else None

    wof, _ = width_fn(tc["size"])
    for lab, n in (("最长 21 字", 21), ("p90 13 字", 13), ("11 字", 11), ("p50 8 字", 8)):
        k = pick(n)
        if k is None:
            continue
        t = data_nodes[k]["cn"]
        lines, tr = ui_theme_wrap(t, tc["box_w"], TEXT_MAX_LINES, wof)
        print("  %-10s %-12s 行数=%d 每行字数=%-9s 墨迹=%s 截断=%s"
              % (lab, k, len(lines), str([len(l) for l in lines]),
                 [round(wof(l), 1) for l in lines], tr))
        print("             %s" % t)

    print("\n【Top-10 长标题】")
    top = sorted(data_nodes.items(), key=lambda kv: (-len(kv[1]["cn"]), kv[0]))[:10]
    for k, v in top:
        lines, tr = ui_theme_wrap(v["cn"], tc["box_w"], TEXT_MAX_LINES, wof)
        print("  %-12s %2d 字 行数=%d 每行字数=%-9s 截断=%s 最宽=%.0f"
              % (k, len(v["cn"]), len(lines), str([len(l) for l in lines]), tr,
                 max(round(wof(l), 1) for l in lines)))

    print("\n【已知排版现象（不是缺陷）】")
    print("  %dpx 下每行可容 12 字（228px）⇒ **11–12 字标题变单行**；孤字只出现在 ≥13 字标题上"
          "（13 字 = 247px 需靠禁则并字，或折成 12+1）。" % tc["size"])
    return 0 if not tc["fails"] else 1


# ══════════════════════════════════════════════════════════════════════
# 番外组名中文化映射（ISSUE-20260927-06）
# ══════════════════════════════════════════════════════════════════════
# 背景：`资源组\剧本\spine.json` 的 `side_stories[].group` 是我方自建的**组名元数据**
#   （组名由本工程拼装，非原作字段；该字段**只有日文/中文混写、没有 `group_cn`**），
#   其中 6 组里有 3 组残留日文 token。spine.json 是资源组的数据、**本模块只读不改**，
#   故中文化映射落在这里：**只映射需要改的组，其余组原样透传**（未命中即原文返回）。
# 落点：映射结果写进 `fc.label.*_tx` 的 `sample` —— 引擎与 HTML 两端绘制/量测的都是
#   `sample`（`krkr/game/ui_theme.tjs` 的 `uiThemeRenderText`：`txt = el.sample`；
#   `复刻/replica.js`：`inner.textContent = String(e.sample)`），故改此处两端同时生效。
#
# 逐条来源注记（键 = spine.json 现组名原文；值 = (中文组名, 依据)）：
#   ① `おっぱい` → **胸部** —— **援引既有条目，本次不新增、不改表**。
#      依据：通用层 `术语表.md` **:171** `おっぱい`｜台词轨「奶子」／叙述者轨「胸部」（双轨成对登记）。
#      轨判定依通用层同文件 **§4.1 第 2 条**：「出现在 `【说话人】「…」` 引号内＝台词轨；其余＝叙述者轨」
#      —— 组名标签不在引号内 ⇒ **叙述者轨** ⇒ 胸部。
#      ⚠ 同语料反向证据：`side_stories[6].title_cn`（`俺たちのおっぱいよ永遠に`）作「我们的奶子啊直到永远」
#      （＝台词轨用词），与本条 1:1 并存 ⇒ 属**资源组数据内部不一致**，已随交付上报（本模块不改 spine.json）。
#   ② `おれつば劇場` → **没翅剧场** —— **同语料既有译法**（两层术语表均未收录，已 grep 复核 0 命中）。
#      依据：`spine.json` `side_stories[28..32].title_cn` **5/5** 作「没翅剧场～…～」；
#      同工程文档同形：`资源组\07_路线脉络.md:865,894-897`、`资源组\08_全系列章节流程图.md:2799,2828-2831`。
#      简称来源：作品中文名「我们没有翅膀」⇒「没翅」。
#   ③ `おまけ` → **附赠** —— **本次新定**（两层术语表均未收录，已 grep 复核 0 命中）。
#      通用层 `SKILL.md` §四 文体通则下择优：优先级「原意 > 语气 > 自然中文 > 原作风味 > 原句形式」，
#      `おまけ`＝白送的赠品/添头 ⇒ 「附赠」直取原意且**是自然中文的独立名词**；候选对比——
#      · 「特典」：日语借词，且日语 `特典` ＝随购买附送的优惠/赠品（`初回特典`），语义**窄于** `おまけ`，
#        亦违反 §四「读起来像中文写的」；
#      · 「额外」：形容词性，作 `番外·额外（成人向）` 这类**独立标签**不成立；
#      · 「附加」：动/区别词性（`附加条件`／`附加费`），作独立名词标签偏书面、生硬；
#        ⚠ 但同语料 `side_stories[46].title_cn`（`日和子おまけＨ（後）`）作「日和子附加Ｈ（后）」⇒
#        **唯一一处既有中文渲染是「附加」**，与本条形成「一致性 vs 自然中文」的取舍点，
#        已随交付上报（若主代理裁定从既有渲染，把本行值改成「附加」即可，映射表为唯一落点）。
#   ※ 其余 3 组（`番外·苍女X日`／`番外·各线 after`／`番外·群像（新年行军 / 格兰玛尼耶）`）**不含日文**
#     ⇒ 不入表、原样透传；其中 `各线 after` 的 `after` 是**英文**，按本工程既有裁决（英文题字保留原样）不动。
GROUP_CN_MAP = {
    "番外·阿雷克桑德平安夜（おっぱい系列）": (
        "番外·阿雷克桑德平安夜（胸部系列）",
        "援引通用层 术语表.md:171（おっぱい＝叙述者轨「胸部」）＋ §4.1 第 2 条轨判定（组名不在引号内）"),
    "番外·おれつば剧场": (
        "番外·没翅剧场",
        "同语料既有译法：spine.json title_cn 5/5（side_stories[28..32]）＋ 资源组\\07_路线脉络.md:865,894-897"),
    "番外·おまけ（成人向）": (
        "番外·附赠（成人向）",
        "本次新定（两层术语表均未收录）；通用层 SKILL.md §四 文体通则择优（附赠＞特典/额外/附加）"),
}

# 日文假名（平假名 + 片假名 + 半角片假名）；用于**映射后残留日文的自警**（不阻断生成）
KANA_RE = re.compile(r"[\u3041-\u309f\u30a0-\u30ff\uff66-\uff9f]")


def group_cn(group):
    """组名中文化：返回 (中文组名, 依据)。未命中映射 ⇒ (原文, "")，即**原样透传**。"""
    hit = GROUP_CN_MAP.get(group)
    if hit is None:
        return group, ""
    return hit[0], hit[1]


def group_kana_residue(spine):
    """映射后仍含日文假名的组名清单（自警用；正常应为空）。"""
    out = []
    for group, _rows in entry_groups(spine):
        cn, _src = group_cn(group)
        if KANA_RE.search(cn):
            out.append((group, cn))
    return out


# ══════════════════════════════════════════════════════════════════════
# 番外入口锚点（契约 §四：落点依据 = spine.json side_stories[].entry_suggestion）
# ══════════════════════════════════════════════════════════════════════
# 关键词 → 锚点脚本前缀；None = 无定位锚（改为挂在本组自己的番外链首）
ANCHOR_RULES = (
    ("21 与 24 之间", "21_"),
    ("AS 主线之后", "24_"),
    ("各对应角色线之后", None),
    ("任意时点可选", None),
)


def entry_groups(spine):
    """按 spine.json 首次出现顺序返回 [(group, [rows])]。"""
    order, by = [], {}
    for row in spine.get("side_stories", []):
        g = row.get("group") or "(无组)"
        if g not in by:
            by[g] = []
            order.append(g)
        by[g].append(row)
    return [(g, by[g]) for g in order]


def entry_anchor_prefix(suggestion, rows):
    for kw, pref in ANCHOR_RULES:
        if kw in (suggestion or ""):
            if pref:
                return pref
            return (rows[0]["script"].split("_")[0] + "_") if rows else None
    return (rows[0]["script"].split("_")[0] + "_") if rows else None


# ══════════════════════════════════════════════════════════════════════
# 番外独立层网格（冻结 §二）
# ══════════════════════════════════════════════════════════════════════
def frag_grid_rows(vp_y, vp_h):
    """图表视口内可容的独立层网格**行数**。

    y(row) = 视口顶 + FRAG_ORIGIN[1] + FRAG_LEAD_Y + row×FRAG_STEP_Y，格高 ＝ NODE_H。
    实测（视口 y190 h827）：行基线 286 / 478 / 670 / 862 落得下，1054 越出 ⇒ **4 行**。
    """
    n = 0
    while True:
        y = vp_y + FRAG_ORIGIN[1] + FRAG_LEAD_Y + n * FRAG_STEP_Y
        if y + NODE_H > vp_y + vp_h:
            return n
        n += 1


def frag_grid_cols(vp_x, vp_w):
    """图表视口内可容的独立层网格**列数**（冻结把列数收敛为 3 的依据）。"""
    n = 0
    while True:
        x = vp_x + FRAG_ORIGIN[0] + n * FRAG_STEP_X
        if x + NODE_W > vp_x + vp_w:
            return n
        n += 1


def frag_capacity_report():
    r"""★ 未产格清单（主代理 2026-09-28 裁决 5）：独立层视口**只容 4 行 × 3 列 = 12 格**，
    组内超出者本轮**不产**（纵滚 / 横移属编程组）。本函数把 6 个组的「可容格数 / 产出格数 /
    未产格清单」一次打全 —— 只读、只打印，**不写任何文件**（`--frag-report`）。
    """
    spine = load_spine()
    static = load_static_elements()
    vp = next(e for e in static if e["id"] == "fc.scroll")
    vpx, vpy, vpw, vph = vp["x"], vp["y"], vp["w"], vp["h"]
    cols, rows = FRAG_COLS, frag_grid_rows(vpy, vph)
    cap = cols * rows
    print("=" * 78)
    print("gen_flow_layout.py · --frag-report（冻结 §二 番外独立层的**视口容量与未产格清单**）")
    print("  视口 fc.scroll = (%d,%d,%d,%d) ｜ 网格 %d 列 × %d 行 = **可容 %d 格**"
          % (vpx, vpy, vpw, vph, cols, rows, cap))
    print("  网格口径：横向步进 %d、纵向步进 %d、行首纵向偏移 %d、原点 = 视口左上 +(%d,%d)"
          % (FRAG_STEP_X, FRAG_STEP_Y, FRAG_LEAD_Y, FRAG_ORIGIN[0], FRAG_ORIGIN[1]))
    print("  偏离登记：参照作 5 个/行（其视口更宽）；我方视口 %d 宽下 5×%d+4×79=1796 放不下 ⇒ 改 %d 个/行"
          % (vpw, NODE_W, cols))
    print("-" * 78)
    print("  %-3s %-34s %4s %6s %6s  %s" % ("G", "组名（group_cn）", "章数", "可容", "产出", "未产格清单（script）"))
    tot_drop = 0
    for gi, (group, grows) in enumerate(entry_groups(spine), 1):
        gcn, _src = group_cn(group)
        made = grows[:cap]
        drop = [r.get("script") or r.get("scene_id") for r in grows[cap:]]
        tot_drop += len(drop)
        print("  %-3d %-34s %4d %6d %6d  %s"
              % (gi, gcn, len(grows), cap, len(made),
                 ("—（全部落格）" if not drop else "%d 条：%s" % (len(drop), ", ".join(drop)))))
    print("-" * 78)
    print("  合计未产 %d 格（跨 %d 组）；这些格**本轮不产元素**——需纵滚/横移才能呈现，"
          "属**编程组**（冻结 §五）。换组/换上限：`--frag-groups 1,3,5` / `--frag-limit n`"
          "（★ 第 3 批：交付样例 `screen1` 默认产**全部 6 组**，故屏上已含下表的「产出」格；"
          "超出 12 格的组按裁决 5 只产前 12 格）。"
          % (tot_drop, sum(1 for _g, rs in entry_groups(spine) if len(rs) > cap)))
    print("  ★ 独立层节点**运行态未定义**（不写 `flow_state`、不产 `_dim`/`_new`）—— 主代理 2026-09-28 裁决 4 登记为缺口。")
    print("  ★ 裁决 4（第 4 批 · 入口热区只在独立层产出时才产）：`fc.entry.<NNNN>_hit` **仅当该组的独立层"
          "在本档产出**时才产 —— 未产出则该入口为**纯占位**（image/组名标签仍在、不可点），"
          "避免点进去切到**未产层** ⇒ 屏面变空且回不来（HTML 实测 `E3_screen1_entry点击后.png`）。"
          "上表「产出」列即该组是否产独立层（`>=1` 格 ⇒ 产 ⇒ 有热区）。"
          "交付样例 `screen1`（默认产**全部 6 组**）⇒ **6/6 组有热区**；`frag` 只产第 1 组 ⇒ 只有 1 个热区；"
          "`screen2`/`ref150`/`states` 不产独立层 ⇒ **0 个热区**（6 个入口全为占位）。")
    return 0


# ══════════════════════════════════════════════════════════════════════
# 主构建
# ══════════════════════════════════════════════════════════════════════
def build(section, lanes_sel, froms, limit, step_y, vert_x, x0, y0, with_entries, cull=True,
          entry_side="left", x0_locked=False, node_states=None, link_states=None,
          frag_groups=None, frag_limit=None):
    r"""产 (screen, stats)。

    第 2 步新增参数（冻结 §一/§二）：
      · `node_states`：节点 `flow_state` 演示序列（**循环套用到 `order` 的每个节点**）；
        缺省 `None` ⇒ **不写 `flow_state` 字段**（＝交付样例，文件内容与外观均不变）。
        仅 `--preset states` 传入；`current` 不产元素（两端程序化画环）。
      · `link_states`：连线 `state` 演示序列（**循环套用到产出的每条边**）；缺省 `None` ⇒ 全部 `normal`。
      · `frag_groups`：番外独立层组号**列表**（每个 1..6，`spine.json` `side_stories` 首次出现序）；
        `None`/空 ⇒ 不产独立层。★ 第 3 批：由单值 `frag_group` 扩为**列表** ——
        交付样例 `screen1` 产**全部 6 组**（每组各有自己的顶栏组名与**按组**返回键）⇒
        「点入口 → 进该组独立层 → 点返回键 → 回主干」在交付样例上闭环。
      · `frag_limit`：**每组**独立层最多产多少格（默认＝视口可容行数 × 每行 3）。
    """
    data = load_data()
    spine = load_spine()
    nodes = data["nodes"]
    sections = data["sections"]
    canvas = load_canvas()
    cw, ch = canvas["width"], canvas["height"]

    static = load_static_elements()
    static_ids = [e["id"] for e in static]
    for need in PASSTHROUGH_REQUIRED:
        if need not in static_ids:
            raise SystemExit("[FAIL] 静态元素快照缺 §一 点名的元素：%s" % need)
    vp = next(e for e in static if e["id"] == "fc.scroll")
    # ★ 冻结 §二 铁律：**一元素只允许一对 `vis_flag`** ⇒ 静态件快照里不得已带 vis_flag
    _dup = [e["id"] for e in static if "vis_flag" in e or "vis_when" in e]
    if _dup:
        raise SystemExit("[FAIL] 静态元素快照已带 vis_flag/vis_when（一元素只允许一对）：%s" % _dup)
    # ★★ 更正（2026-09-28 第 3 批 · 主代理 · 冻结书 §二 原写的「现有 117 件全部加 vis_flag/vis_when」作废）：
    #   **外壳件不参与层旗标** —— 静态件快照（视口 / 迷你地图 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 /
    #   付箋 / 回放窗与回放键 / 进入本章 / 右栏详情）**一律不写 `vis_flag`/`vis_when`**，
    #   于是它们在**任何层**都照常绘制（外壳是两种层共用的舞台）。
    #   旗标只由**图内容层**持有（见 `LAYER_OWNED_PREFIXES`），由 `build()` 末尾自检双向卡住。
    #   依据：外壳件随层隐藏会让深墨色组名/网格画到无底图的透明/黑画面上（实测证据 `E3_frag_frag1.png`）。

    if section < 0 or section >= len(sections):
        raise SystemExit("[FAIL] --section 越界：%d（共 %d 段）" % (section, len(sections)))
    sec = sections[section]
    lane_all = sec["lanes"]
    if lanes_sel is None:
        lanes_sel = list(range(len(lane_all)))
    for li in lanes_sel:
        if li < 0 or li >= len(lane_all):
            raise SystemExit("[FAIL] --lanes 越界：%d（本段共 %d 道）" % (li, len(lane_all)))

    D = len(lanes_sel)
    placed = {}      # id -> dict(lane, lane_pos, idx, x, y)
    order = []

    # ── 道带中心：若产入口列，则把入口列整列摆进视口、道带在**剩余宽度**里居中 ──
    #   依据：§九 裁决 5「样例屏所有产出元素必须落在 x∈[60,1295]、y∈[190,1017]」。
    #   组名标签 333 宽 > 视口两侧任一侧的空隙（282）⇒ 只能整列让位，不能塞在道带旁边。
    vpx, vpy, vpw, vph = vp["x"], vp["y"], vp["w"], vp["h"]
    if with_entries and not x0_locked:
        if entry_side == "right":
            x0 = (vpx + (vpx + vpw - ENTRY_COL_W - ENTRY_COL_GAP)) / 2.0
        else:
            x0 = ((vpx + ENTRY_COL_W + ENTRY_COL_GAP) + (vpx + vpw)) / 2.0
    elif not x0_locked:
        x0 = vpx + vpw / 2.0

    def inside(x, y, w, h):
        """是否**完整落进流程图视口**（fc.scroll，1235×827）。

        裁到视口而不是画布：视口外的节点若照画，会压到右栏（迷你地图 / 缩放 / 平移条）上。
        参照作同款语义（`scnchart_ui.tjs:2111-2117`：pos 出界的 item 不创建 layer）。
        """
        return (vp["x"] <= x and x + w <= vp["x"] + vp["w"]
                and vp["y"] <= y and y + h <= vp["y"] + vp["h"])

    for p, li in enumerate(lanes_sel):
        cx = x0 + (p - (D - 1) / 2.0) * vert_x
        slot_x = int(round(cx - NODE_W / 2.0))
        frm = froms[p]
        entries = lane_all[li]["nodes"]
        for idx in range(frm, min(frm + limit, len(entries))):
            nid = entries[idx]["id"]
            if nid in placed:
                continue
            y = y0 + (idx - frm) * step_y
            if cull and not inside(slot_x, y, NODE_W, NODE_H):
                continue          # 视口外的节点不建元素（参照作同款：pos 出界不创建 layer）
                # ★ `--no-cull` 关闭本裁剪：只为**全量规模核算**用（产出的元素会落到画布外，
                #   不能当交付屏；连线仍受「点在画布内」约束，会大量丢弃）。
            placed[nid] = {"lane": li, "lane_pos": p, "idx": idx, "x": slot_x, "y": y}
            order.append(nid)

    # ── 图内容层元素 ────────────────────────────────────────────────
    gen = []
    empty_fallback = 0
    for n, nid in enumerate(order, 1):
        info, v = placed[nid], nodes[nid]
        k = node_kind(v)
        tag = "%04d" % n
        where = "DATA.sections[%d].lanes[%d] nodes[%d]" % (section, info["lane"], info["idx"])
        base_note = ("· script=%s · %s · spine=%s" % (nid, where, v.get("spine") or "-"))
        if k == "branch":
            gen.append({
                "id": "fc.branch." + tag, "kind": "image", "z": 20, "visible_default": True,
                "asset": BRANCH_ASSET, "x": info["x"] + BRANCH_OFFSET_X, "y": info["y"],
                "w": BRANCH_W, "h": BRANCH_H, "opacity": 255, "nine": dict(BRANCH_NINE),
                "source": NODE_ASSET_SOURCE,
                "note": "分支底座（DATA.kind=branch 的节点只出底座、不出节点框，契约 §四）%s"
                        "· 65×65 居中于 296 宽槽位（+%d）· 本轮统一取 65×65 件（119×119 大件无数据依据区分，未用）"
                        % (base_note, BRANCH_OFFSET_X),
            })
            continue
        off, on = NODE_ASSET[k]
        # ★ 冻结 §一.1：`flow_state` 只作数据、**缺省不写**（不写 ⇒ available ⇒ 外观不变）
        st = None
        if node_states:
            st = node_states[(n - 1) % len(node_states)]
            if st not in FLOW_STATES:
                raise SystemExit("[FAIL] 非法 flow_state：%r（只允许 %s）" % (st, list(FLOW_STATES)))
        node_el = {
            "id": "fc.node." + tag, "kind": "image", "z": 20, "visible_default": True,
            "asset": off, "x": info["x"], "y": info["y"], "w": NODE_W, "h": NODE_H,
            "opacity": 255, "nine": dict(NODE_NINE[k]),
            "state_assets": {"normal": off, "hover": on, "pressed": on},
            "source": NODE_ASSET_SOURCE,
            "note": "流程图节点（kind=%s）%s· 素材 %s（源尺寸≠296 ⇒ nine 横向拉伸，契约 §二.2）"
                    "· state_assets 三态图；**不带 state_group**（本屏无配对待联动的热区，"
                    "能过闸门的最简写法，见报告）%s"
                    % (k, base_note, off.split("/")[-1],
                       "" if st is None else
                       "· ★ 运行态样例 `flow_state=%s`（冻结 §一.1；**只作数据**，"
                       "叠加件见同 tag 的 `_dim`/`_new`，`current` 由两端程序化画环 ⇒ 不产元素）" % st),
        }
        if st is not None:
            node_el["flow_state"] = st
        gen.append(node_el)
        # 文案：cn 为空时回落 script 名（§九 裁决 7，与参照作「tag 名兜底」同构）
        title = v.get("cn") or ""
        fallback = False
        if not title:
            title = v.get("script") or nid
            fallback = True
            empty_fallback += 1
        # ★ 第 9 批：按 `TITLE_HARD_BREAK` 在自然断点插硬换行（`sample` 里就是带 `\n` 的最终文本）
        title_broken = (nid in TITLE_HARD_BREAK)
        title = title_sample(nid, v)
        tx_x = info["x"] + (NODE_W - TEXT_W) // 2      # 文字盒收窄并水平居中
        gen.append({
            "id": "fc.node.%s_tx" % tag, "kind": "text", "z": 25, "visible_default": True,
            "x": tx_x, "y": info["y"], "w": TEXT_W, "h": NODE_H,
            "font": {"size": TEXT_SIZE, "bold": True, "color": TEXT_INK},
            "line_spacing": TEXT_LINE_SPACING,   # ★ 元素级行距（覆盖全局 fonts.line_spacing.body = 1.4）
            "align": "center", "valign": "middle", "wrap": True, "max_lines": TEXT_MAX_LINES,
            "sample": title,
            "note": "节点标签（引擎绘制，不烘焙进图）· 文案 = DATA.nodes[].cn%s · "
                    "字号 %d / **行距 %s**（元素级 `line_spacing`，两端都读：krkr uiThemeElementSpacing / HTML lineSpacing()）"
                    "/ 文字盒宽 %d（居中于 296 宽节点：x_node+%d）/ 最多 %d 行 / wrap "
                    "（四判据：上留≥%dpx、下留≥%dpx＝对准**可见实体面** rows %s、行墨迹≤263px、712/712 零截断）%s"
                    % ("（**cn 为空 ⇒ 回落 script 名，§九 裁决 7**）" if fallback else "（jp 不上屏）",
                       TEXT_SIZE, TEXT_LINE_SPACING, TEXT_W, (NODE_W - TEXT_W) // 2, TEXT_MAX_LINES,
                       PLATE_MARGIN_MIN, PLATE_MARGIN_MIN, PLATE_ROWS["section"],
                       "" if not title_broken else
                       "· ★ **第 9 批：按 `TITLE_HARD_BREAK` 在自然断点插硬换行**（原文「%s」→ 两行「%s」/「%s」）"
                       "—— 保证**首行墨迹左缘 ≥ x_node+%d**（已读对勾 20×20 @(x+10,y+12) 右缘 +30 不压首字）"
                       % ("".join(TITLE_HARD_BREAK[nid]), TITLE_HARD_BREAK[nid][0], TITLE_HARD_BREAK[nid][1],
                          TITLE_CHECK_GAP)),
        })
        gen.append({
            "id": "fc.node.%s_hit" % tag, "kind": "hit", "z": 95, "visible_default": True,
            "x": info["x"], "y": info["y"], "w": NODE_W, "h": NODE_H,
            "action": "", "label": "",
            "note": "节点热区%s· action 本轮**留空**（点节点＝标记已读 + 定位属编程组，契约 §二）"
                    % base_note,
        })
        # ── 运行态叠加件（冻结 §一.1；**只在演示预设里出现**，`st is None` ⇒ 不产）──
        if st == "locked":
            # ★ ISSUE-20260928-03 修正：压暗件改 `kind:"image"`，引用**按节点种类**派生的压暗素材；
            #   几何与 `nine` **与该节点底图件逐字段一致**（dst＝node 底图件，不是"可见实体面矩形"）。
            #   起因：原 `kind:"rect"`（方角 284×48）压在**四角 r=16 圆弧、弧外透明**的底图上，
            #   locked 节点每角露出约 55px 暗方角（实测 (8,10,13) vs 同型 available (15,18,24)）。
            #   保留：`opacity` 控强度（110）、`z`＝节点 z+1、flag 对不变。
            gen.append({
                "id": "fc.node.%s_dim" % tag, "kind": "image", "z": 20 + DIM_Z_OFF,
                "visible_default": True,
                "asset": DIM_ASSET_BY_KIND[k],
                "x": info["x"], "y": info["y"], "w": NODE_W, "h": NODE_H,
                "opacity": DIM_OPA, "nine": dict(NODE_NINE[k]),
                "source": "素材组产出（★ ISSUE-20260928-03 冻结件名 `%s`，源 %d×%d ＝ 该节点底图源尺寸）"
                          % (DIM_ASSET_BY_KIND[k], DIM_SRC_SIZE[k][0], DIM_SRC_SIZE[k][1]),
                "vis_flag": NODE_STATE_FLAG + tag, "vis_when": "locked",
                "note": "★ 运行态·未解锁（`locked`）压暗叠层%s· ★ ISSUE-20260928-03 **修正**："
                        "`kind:\"image\"`（原 `kind:\"rect\"` 方角矩形），素材 `%s`、"
                        "几何与 `nine` **与同 tag 节点底图件逐字段一致**（%d×%d / nine %s）；"
                        "**强度**由元素 `opacity` 控（%d）、**形状**由素材 alpha 控；z＝节点 z+%d。"
                        "**根因（已实测）**：节点可见实体面四角是 **r=16 圆弧、弧外透明**，方角矩形四角"
                        "压在背景上 ⇒ locked 节点每角露出约 55px 暗方角（实测方角处 (8,10,13) vs 同型 "
                        "available 节点 (15,18,24)）。**不得**改成改节点元素 opacity（冻结 §四.4：会与既有 opacity 闸门互相干扰）"
                        % (base_note, DIM_ASSET_BY_KIND[k].split("/")[-1], NODE_W, NODE_H,
                           NODE_NINE[k], DIM_OPA, DIM_Z_OFF),
            })
        elif st == "new":
            # NEW 角标：位置优先照参照作 (x, y−12)；越出图表视口或画布 ⇒ 回落 (x+6, y+8)
            nx, ny = info["x"] + NEW_PREF[0], info["y"] + NEW_PREF[1]
            fell = False
            if not inside(nx, ny, NEW_W, NEW_H) or not (0 <= nx and nx + NEW_W <= cw
                                                        and 0 <= ny and ny + NEW_H <= ch):
                nx, ny = info["x"] + NEW_FALLBACK[0], info["y"] + NEW_FALLBACK[1]
                fell = True
            gen.append({
                "id": "fc.node.%s_new" % tag, "kind": "image", "z": 20 + NEW_Z_OFF,
                "visible_default": True,
                "asset": NEW_ASSET, "x": nx, "y": ny, "w": NEW_W, "h": NEW_H, "opacity": 255,
                "vis_flag": NODE_STATE_FLAG + tag, "vis_when": "new",
                "source": "E4 产出（冻结 §三）：NEW 角标 %d×%d，底色 #A50000（参照件 "
                          "`res12_blocks__fragment__NEW.png` 实测），白字 `NEW`；参照 FC-4-2 的 100×34 是它的 2× 母版"
                          % (NEW_W, NEW_H),
                "note": "★ 运行态·已解锁未读（`new`）NEW 角标%s· 冻结 §一.1：位置**优先照参照作** "
                        "`(node.x, node.y−12)`＝(%d, %d)，%s；z＝节点 z+%d。1:1 无 nine（素材物理尺寸＝%d×%d）"
                        % (base_note, info["x"] + NEW_PREF[0], info["y"] + NEW_PREF[1],
                           "**越出图表视口 ⇒ 已回落 `(node.x+6, node.y+8)`**" if fell
                           else "本节点未越界、按参照作落点",
                           NEW_Z_OFF, NEW_W, NEW_H),
            })
        elif st == "visited":
            # ★ ISSUE-20260928-03 新增：已读绿对勾（用户 2026-09-28 裁决「丙方案」）
            rx, ry = info["x"] + READ_OFF[0], info["y"] + READ_OFF[1]
            # 机检①：**完全落在节点可见实体面**（x+6, y+8, 284×48）内
            _px0, _py0 = info["x"] + DIM_OFF_X, info["y"] + DIM_OFF_Y
            if not (_px0 <= rx and rx + READ_W <= _px0 + DIM_W
                    and _py0 <= ry and ry + READ_H <= _py0 + DIM_H):
                raise SystemExit("[FAIL] %s 的 `_read` 落点 (%d,%d,%d×%d) **越出节点可见实体面**"
                                 "（%d,%d,%d×%d）" % ("fc.node.%s" % tag, rx, ry, READ_W, READ_H,
                                                      _px0, _py0, DIM_W, DIM_H))
            # 机检③：不越出图表视口与画布
            if not inside(rx, ry, READ_W, READ_H) or not (0 <= rx and rx + READ_W <= cw
                                                          and 0 <= ry and ry + READ_H <= ch):
                raise SystemExit("[FAIL] %s 的 `_read` 落点 (%d,%d,%d×%d) 越出图表视口或画布"
                                 % ("fc.node.%s" % tag, rx, ry, READ_W, READ_H))
            gen.append({
                "id": "fc.node.%s_read" % tag, "kind": "image", "z": 20 + READ_Z_OFF,
                "visible_default": True,
                "asset": READ_ASSET, "x": rx, "y": ry, "w": READ_W, "h": READ_H, "opacity": 255,
                "vis_flag": NODE_STATE_FLAG + tag, "vis_when": "visited",
                "source": "素材组产出（★ ISSUE-20260928-03 冻结件名）：绿对勾 %d×%d（1:1、无 nine）；"
                          "备选件 `%s` 一并产出但**本轮不接线**（仅登记备选）"
                          % (READ_W, READ_H, READ_ALT_ASSET.split("/")[-1]),
                "note": "★ 运行态·已读（`visited`）绿对勾叠加件%s· **ISSUE-20260928-03 新增**："
                        "**用户 2026-09-28 裁决「丙方案」**（① 完全落在可见实体面内、② 与 `_new` 不共存、"
                        "③ 不越出视口/画布 —— 三条均为落盘前机检）。"
                        "落点＝节点**可见实体面**（x+%d, y+%d, %d×%d）的**左上角内缘** ⇒ (%d, %d) "
                        "（距实体面左/上沿各 %dpx；实体面右下余 %dpx×%dpx）；尺寸 %d×%d（1:1、**无 `nine`**）；"
                        "`z`＝节点 z+%d（与 `_new` 同档）；`vis_flag:\"fc.state.%s\"`＋`vis_when:\"visited\"`；`opacity` 255。"
                        "**为什么不用「甲 / 乙案」**：甲＝节点左侧竖条 —— 对节点面（284×48）为 **2.88:1** 的极端长宽比，"
                        "竖条细而高、在网格里读作分隔线而非状态；乙＝字色弱化（把标题墨色压暗）—— "
                        "可见实体面上对比度由 **10.46:1 → 1.67:1** 过淡、且与「未解锁压暗」语义混淆。"
                        "**`current`（当前所在）本轮不加对勾**：只留两端程序化画的 `@palette.node_current` 金环"
                        "（两枚叠加互相干扰，且当前节点必然已读 ⇒ 对勾信息冗余）。"
                        % (base_note, DIM_OFF_X, DIM_OFF_Y, DIM_W, DIM_H, READ_OFF[0], READ_OFF[1],
                           READ_OFF[0] - DIM_OFF_X, DIM_W - (READ_OFF[0] - DIM_OFF_X) - READ_W,
                           DIM_H - (READ_OFF[1] - DIM_OFF_Y) - READ_H, READ_W, READ_H, READ_Z_OFF, tag),
            })
        # st ∈ {available} ⇒ 无叠加（冻结 §一.1 表）；
        # st == "current" ⇒ **不产元素**（两端程序化画环；本轮裁决「current 只留金环、不加对勾」）

    # ── ★ ISSUE-20260928-03 落盘前机检（② `_read` 与 `_new` **不共存于同一节点**）──
    #   `new`（已解锁未读）与 `visited`（已读）**语义互斥** ⇒ 同一节点不可能同时产 `_new` 与 `_read`；
    #   落盘前无条件卡一道，防「状态机被改坏 / 逐节点状态表串位」导致两枚角标叠在同一角。
    _gen_ids = {e["id"] for e in gen}
    _coexist = sorted(i[:-5] for i in _gen_ids
                      if i.endswith("_read") and (i[:-5] + "_new") in _gen_ids)
    if _coexist:
        raise SystemExit("[FAIL] `_read`（visited）与 `_new`（new）**共存于同一节点**（语义互斥）：%s"
                         % _coexist)
    # 机检（附）：凡产 `_read` 的节点其 `flow_state` 必为 `visited`；凡 `locked` 必产 `_dim`、必不产 `_read`
    _st_by_tag = {"%04d" % n: (node_states[(n - 1) % len(node_states)] if node_states else None)
                  for n, _nid in enumerate(order, 1)} if node_states else {}
    for _tag, _stv in _st_by_tag.items():
        _has_read = ("fc.node.%s_read" % _tag) in _gen_ids
        _has_dim = ("fc.node.%s_dim" % _tag) in _gen_ids
        if _has_read and _stv != "visited":
            raise SystemExit("[FAIL] fc.node.%s 产了 `_read` 但 flow_state=%r ≠ visited" % (_tag, _stv))
        if _stv == "locked" and not _has_dim:
            raise SystemExit("[FAIL] fc.node.%s 为 locked 但无 `_dim`" % _tag)
        if _stv == "locked" and _has_read:
            raise SystemExit("[FAIL] fc.node.%s 为 locked 却产了 `_read`" % _tag)
        if _stv == "current" and (_has_read or _has_dim):
            raise SystemExit("[FAIL] fc.node.%s 为 current（只留金环、不加对勾）却产了叠加件" % _tag)

    # ── 边（顶层 links）─────────────────────────────────────────────
    # ★ 冻结 §一.2：`state` **取代** 第 1 步的 `kind`；色/宽/箭头由生成器按 state 解析后写进
    #   `color`/`w`/`arrow`（两端不做任何配色判断）。缺省 normal ＝ 旧样例外观（不改色宽箭头）。
    links, forms = [], {"line": 0, "vz": 0, "vl": 0}
    edge_counts = {k: 0 for k in EDGE_STATES}
    drop_not_placed = drop_outside = drop_degenerate = 0
    for nid in order:
        a = placed[nid]
        ka = node_kind(nodes[nid])
        for t in nodes[nid].get("next") or []:
            b = placed.get(t)
            if b is None:
                drop_not_placed += 1
                continue
            form, pts = route_pts(a, b, ka)
            pts = dedupe_pts(pts)
            # §三 末「取整」：半像素端点会让两端抗锯齿各自铺 4–6px ⇒ 所有点取整
            pts = [[int(round(p[0])), int(round(p[1]))] for p in pts]
            assert all(isinstance(c, int) for p in pts for c in p), "pts 必须为整数"
            if len(pts) < 2:
                drop_degenerate += 1   # 路由退化（两端槽位重合）⇒ 无可见线段
                continue
            if not all(0 <= p[0] <= cw and 0 <= p[1] <= ch for p in pts):
                drop_outside += 1   # 路由点越出画布 ⇒ 不产（门 ① 要求每点在画布内；参照作同款离屏不画）
                continue
            st = EDGE_STATE_DEFAULT
            if link_states:
                st = link_states[len(links) % len(link_states)]
            ckey, lw, arrow = edge_style(st)
            links.append({
                "id": "fc.link.%04d" % (len(links) + 1),
                "state": st,
                "pts": pts,
                "w": lw,
                "color": resolve_palette_int(ckey),
                "arrow": arrow,
            })
            edge_counts[st] += 1
            forms[form] += 1

    # ── 番外入口标记 + 关联标签（契约 §四）──────────────────────────
    entry_stats = []
    # ★ 裁决 4（第 4 批 · 2026-09-28 主代理）：入口热区 `fc.entry.<NNNN>_hit` **只在该组的独立层
    #   确实在本档产出时**才产 —— 否则热区指向**未产出的层** ⇒ 点一下屏面变空且回不来
    #   （HTML 实测 `_工作\ISSUE-20260928-02_HTML\证据\E3_screen1_entry点击后.png`）。
    #   未产出时**入口 image / 组名标签仍在**（主干层可见的纯占位），只是**不可点**。
    entry_hit_skipped = []
    if with_entries:
        # 入口列**整列摆进视口**（§九 裁决 5）：左贴视口左缘 / 右贴视口右缘；
        # 组名标签 333 宽 > 视口两侧空隙（各 282）⇒ 不能塞在道带旁边，只能整列占一条竖带。
        if entry_side == "right":
            col_x = vp["x"] + vp["w"] - ENTRY_COL_W
        else:
            col_x = vp["x"]
        entry_x = col_x + (ENTRY_COL_W - ENTRY_W) // 2     # 标记在列内居中
        label_x = col_x                                    # 组名标签左对齐列首
        used_y = set()

        def anchor_node(prefix):
            for nid in reversed(order):
                if nodes[nid]["script"].startswith(prefix):
                    return nid
            return None

        fb = 0
        vp_bottom = vp["y"] + vp["h"]
        for gi, (group, rows) in enumerate(entry_groups(spine), 1):
            sugg = rows[0].get("entry_suggestion") or ""
            gcn, gsrc = group_cn(group)                 # 组名中文化（未命中 ⇒ 原样透传，gsrc=""）
            gsrc_eq = ("；原文组名 = 「%s」（%s）" % (group, gsrc)) if gsrc else ""
            pref = entry_anchor_prefix(sugg, rows)
            an = anchor_node(pref) if pref else None
            ey = None
            basis = ""
            if an is not None:
                base = placed[an]["y"]
                k = 0
                while (base + k * step_y) in used_y:
                    k += 1
                cand = base + k * step_y
                if cand + ENTRY_H + 4 + LABEL_H <= vp_bottom:      # 标记+标签都要落进视口
                    ey = cand
                    basis = ("锚点 = 已落盘节点 %s（script 前缀 %s，依 entry_suggestion 关键词）%s"
                             % (an, pref, "" if k == 0 else "；同行已被上一组占用 ⇒ 下移 %d 行" % k))
            if ey is None:
                while (y0 + fb * step_y) in used_y:
                    fb += 1
                ey = y0 + fb * step_y
                fb += 1
                basis = ("锚点 %s 未在本屏落盘（或该行已被占用且下移后放不下）⇒ **回落**入口列次行"
                         "（本屏 --section %d 未选该锚点所在段/道）；entry_after 全为 null（无原作证据）"
                         % (pref or "无定位锚（任意时点可用）", section))
            used_y.add(ey)
            # ★ 裁决 4：本组独立层是否**在本档产出**（`frag_groups` 是该档实际产出的组号列表）。
            #   未产出 ⇒ 不产入口热区（入口件降级为纯占位）。
            skip_hit = not (frag_groups and gi in frag_groups)
            if skip_hit:
                entry_hit_skipped.append(gi)
                img_note_suffix = ("· ★ 裁决 4：本组独立层**未在本档产出**（`frag_groups` 不含 %d）⇒ "
                                   "本入口为**纯占位**、**不产 `fc.entry.%04d_hit` 热区**"
                                   "（否则点进去屏面变空且回不来）" % (gi, gi))
            else:
                img_note_suffix = ""
            # 组名标签：优先放标记**下方**；下方放不下则转到**上方**（§九 裁决 5：元素必须全在视口内）
            lbl_y = ey + ENTRY_H + 4
            if lbl_y + LABEL_H > vp_bottom:
                lbl_y = ey - LABEL_H - 4
            gen.append({
                "id": "fc.entry.%04d" % gi, "kind": "image", "z": 21, "visible_default": True,
                "asset": ENTRY_ASSET, "x": entry_x, "y": ey, "w": ENTRY_W, "h": ENTRY_H,
                "opacity": 255, "nine": dict(ENTRY_NINE),
                "vis_flag": LAYER_FLAG, "vis_when": LAYER_MAIN,
                "source": ENTRY_SOURCE,
                "note": "番外入口标记（**占位，非最终美术**）· 组=%s（%d 章）· entry_suggestion=「%s」· %s%s%s"
                        % (gcn, len(rows), sugg, basis, gsrc_eq, img_note_suffix),
            })
            # ★ 冻结 §二：入口热区 `fc.entry.<NNNN>_hit`（矩形＝入口 image 件矩形）
            #   ★ 裁决 4：**仅在该组独立层确实产出时**才产（见上方 `skip_hit`）。
            if not skip_hit:
                gen.append({
                    "id": "fc.entry.%04d_hit" % gi, "kind": "hit", "z": 95, "visible_default": True,
                    "x": entry_x, "y": ey, "w": ENTRY_W, "h": ENTRY_H,
                    "action": "flow_layer", "layer": FRAG_LAYER_FMT % gi,
                    "label": "",
                    "vis_flag": LAYER_FLAG, "vis_when": LAYER_MAIN,
                    "note": "★ 番外入口热区（冻结 §二）：`action:\"flow_layer\"` + `layer:\"%s\"` —— "
                            "把屏级 flag `%s` 置为 `%s` 并重绘/重算命中（进入第 %d 组番外独立层）。"
                            "矩形＝入口 image 件矩形 %d×%d @(%d,%d)；`fc.entry`/`fc.label` 保持 `vis_when:\"main\"`。"
                            "★ 裁决 4：**仅当本组独立层在本档产出**时才产本热区。"
                            % (FRAG_LAYER_FMT % gi, LAYER_FLAG, FRAG_LAYER_FMT % gi, gi,
                               ENTRY_W, ENTRY_H, entry_x, ey),
                })
            gen.append({
                "id": "fc.label.%04d" % gi, "kind": "image", "z": 20, "visible_default": True,
                "asset": LABEL_ASSET, "x": label_x, "y": lbl_y, "w": LABEL_W, "h": LABEL_H,
                "opacity": 255, "nine": dict(LABEL_NINE),
                "source": NODE_ASSET_SOURCE,
                "note": "关联标签底板（番外组名）· 置于入口标记%s %dpx" % (
                    "下方" if lbl_y > ey else "上方", ENTRY_H + 4),
            })
            gen.append({
                "id": "fc.label.%04d_tx" % gi, "kind": "text", "z": 25, "visible_default": True,
                "x": label_x, "y": lbl_y, "w": LABEL_W, "h": LABEL_H,
                "font": {"size": LABEL_TEXT_SIZE, "bold": True, "color": TEXT_INK},
                "align": "center", "valign": "middle", "wrap": True, "max_lines": 1,
                "sample": gcn,
                "note": "关联标签文字（引擎绘制）· 文案 = 组名中文化（`GROUP_CN_MAP`／`group_cn`）后的 "
                        "spine.json side_stories[].group%s"
                        % (gsrc_eq or "（本组不在映射表内 ⇒ 原样透传）"),
            })
            entry_stats.append((group, gcn, ey))

    # ★ 冻结 §二：**图内容层产出件**（node / branch / label / entry …）全部 `vis_flag:"fc_layer"` + `vis_when:"main"`。
    #   已带 vis_flag 的（运行态叠加件 `_dim`/`_new`，vis_flag=fc.state.<NNNN>）**不覆盖**
    #   —— 「一元素只允许一对 vis_flag」是硬约束（`_schema.md` §四 M47 条）。
    #   ★ 第 3 批：外壳件（`static`）**不在本循环里** ⇒ 一律不带层旗标（两态共用舞台）。
    for e in gen:
        if "vis_flag" not in e:
            e["vis_flag"] = LAYER_FLAG
            e["vis_when"] = LAYER_MAIN

    # ── 番外独立层（冻结 §二；★ 第 3 批扩为**多组**）────────────────
    #   交付样例 `screen1` 传 [1..6] ⇒ 6 组各自的网格/顶栏/按组返回键都进屏，
    #   入口热区 `fc.entry.<NNNN>_hit`（layer=frag<G>）与返回键（layer=main）成对 ⇒ 进出闭环。
    frag_stats = []
    if frag_groups:
        all_groups = entry_groups(spine)
        # 网格原点＝图表视口左上 +(6,6)；行首（第一行）再纵向偏移 90（6 组共用同一网格几何，
        # 只是互斥显示 ⇒ 空间上叠在一起，靠 vis_when 区分）
        ox = vpx + FRAG_ORIGIN[0]
        oy = vpy + FRAG_ORIGIN[1] + FRAG_LEAD_Y
        grid_rows = frag_grid_rows(vpy, vph)
        grid_cols = frag_grid_cols(vpx, vpw)
        if FRAG_COLS > grid_cols:
            raise SystemExit("[FAIL] 独立层列数 %d 超出视口可容列数 %d（视口宽 %d、横步 %d、格宽 %d）"
                             % (FRAG_COLS, grid_cols, vpw, FRAG_STEP_X, NODE_W))
        cap = FRAG_COLS * grid_rows if frag_limit is None else min(frag_limit, FRAG_COLS * grid_rows)
        fb_x = vpx + vpw - FRAGBACK_W - FRAGBACK_GAP
        fb_y = vpy + FRAGBACK_GAP
        # ★ 第 5 批：组名墨迹实测器（与文字四判据**同一把尺** ＝ `width_fn`，PIL 取 `msyhbd.ttc`）；
        #   用于（a）逐组把墨迹宽写进 note、（b）**落盘前自检**「墨迹 + 2×PAD ≤ 底板宽」，
        #   避免组名长过底板时静默溢出（本批最长 396px，底板 420）。
        _wof_title, _wof_title_src = width_fn(FRAG_TITLE_SIZE)
        _title_w_max = 0.0
        seen_groups = set()
        for frag_group in frag_groups:
            if not (1 <= frag_group <= len(all_groups)):
                raise SystemExit("[FAIL] --frag-groups 越界：%d（spine.side_stories 共 %d 组）"
                                 % (frag_group, len(all_groups)))
            if frag_group in seen_groups:
                raise SystemExit("[FAIL] --frag-groups 有重复组号：%d" % frag_group)
            seen_groups.add(frag_group)
            group, grows = all_groups[frag_group - 1]
            gcn, gsrc = group_cn(group)
            layer = FRAG_LAYER_FMT % frag_group
            made, dropped = [], []
            for i, row in enumerate(grows, 1):
                col, rr = (i - 1) % FRAG_COLS, (i - 1) // FRAG_COLS
                cx_, cy_ = ox + col * FRAG_STEP_X, oy + rr * FRAG_STEP_Y
                if len(made) >= cap or not inside(cx_, cy_, NODE_W, NODE_H):
                    dropped.append((i, row.get("script")))
                    continue
                made.append((i, row, cx_, cy_))
            for i, row, cx_, cy_ in made:
                script = row.get("script") or ""
                dv = nodes.get(script)
                title = (dv or {}).get("cn") or row.get("title_cn") or script or row.get("scene_id")
                # ★ 第 9 批：独立层节点标题**同样**应用 `TITLE_HARD_BREAK`（按 script 取表；
                #   与主干节点同一张表、同一判据 ⇒ 换到独立层也不会压住对勾）
                if dv is not None:
                    title = title_sample(script, dv)
                src_kind = "DATA.nodes[%s].cn" % script if (dv or {}).get("cn") else (
                    "spine.side_stories[].title_cn" if row.get("title_cn") else "script 名兜底")
                base_note = ("· script=%s · spine.side_stories 组 %d（%s）· 组内序 %d/%d"
                             % (script, frag_group, group, i, len(grows)))
                off, on = FRAG_ASSET
                gen.append({
                    "id": FRAG_ID_FMT % (frag_group, i), "kind": "image", "z": 20,
                    "visible_default": True,
                    "asset": off, "x": cx_, "y": cy_, "w": NODE_W, "h": NODE_H,
                    "opacity": 255, "nine": dict(NODE_NINE["frag"]),
                    "state_assets": {"normal": off, "hover": on, "pressed": on},
                    "source": NODE_ASSET_SOURCE,
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "★ 番外独立层节点（冻结 §二）%s· 素材 %s（源 228×65 ≠ 296 ⇒ nine 横向拉伸，"
                            "与主干 frag 节点同件同 nine）· state_assets 三态图、不带 state_group"
                            "· **运行态未定义**（裁决 4：不写 `flow_state`、不产 `_dim`/`_new`）"
                            % (base_note, off.split("/")[-1]),
                })
                gen.append({
                    "id": (FRAG_ID_FMT % (frag_group, i)) + "_tx", "kind": "text", "z": 25,
                    "visible_default": True,
                    "x": cx_ + (NODE_W - TEXT_W) // 2, "y": cy_, "w": TEXT_W, "h": NODE_H,
                    "font": {"size": TEXT_SIZE, "bold": True, "color": TEXT_INK},
                    "line_spacing": TEXT_LINE_SPACING,
                    "align": "center", "valign": "middle", "wrap": True, "max_lines": TEXT_MAX_LINES,
                    "sample": title,
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "番外独立层节点标签（引擎绘制）· 文案＝%s%s· **文字口径与主干节点完全一致**："
                            "字号 %d / 行距 %s（元素级 `line_spacing`）/ 文字盒宽 %d（居中：x_node+%d）/ "
                            "最多 %d 行 / wrap / valign:middle（同样跑四条文字判据）"
                            % (src_kind, "（**cn 缺失 ⇒ 回落标题/脚本名**）" if src_kind != "DATA.nodes[%s].cn" % script else "",
                               TEXT_SIZE, TEXT_LINE_SPACING, TEXT_W, (NODE_W - TEXT_W) // 2, TEXT_MAX_LINES),
                })
                gen.append({
                    "id": (FRAG_ID_FMT % (frag_group, i)) + "_hit", "kind": "hit", "z": 95,
                    "visible_default": True,
                    "x": cx_, "y": cy_, "w": NODE_W, "h": NODE_H,
                    "action": "", "label": "",
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "番外独立层节点热区%s· action 本轮**留空**（与主干节点同口径：点节点＝标记已读+定位属编程组）"
                            % base_note,
                })
            # ── 每组顶栏（独立层内）：**标签底板 + 组名标题**（同 `fc.label.*` 惯例）+ **按组**返回主干键 ──
            #   ★ 第 5 批：底板 `fc.frag<G>_title_bg`（z = 标题 z − 1 = 24），与标题、返回键**同组同 vis_when**；
            #     标题矩形 = 底板矩形（`align:"center"` / `valign:"middle"`，与 `fc.label.<N>_tx` 同口径）；
            #     纵向取顶栏带居中（带 y..y+44，底板高 52 ⇒ y = 带顶 + (44−52)//2 = 带顶 − 4 = 192）。
            #   ★ 第 7 批：底板换**专用硬边件** `ui/x_ui_fragtitle_bg.png`（444×52，1:1、无 `nine`）。
            _title_bg_y = vpy + FRAG_ORIGIN[1] + (FRAG_TITLE_H - FRAG_TITLE_BG_H) // 2
            _tw = _wof_title(gcn)
            _title_w_max = max(_title_w_max, _tw)
            if _tw + 2 * FRAG_TITLE_BG_PAD > FRAG_TITLE_BG_W:
                raise SystemExit("[FAIL] 第 %d 组组名墨迹 %.1fpx + 两侧内边距 %d×2 > 底板宽 %d（会溢出底板）；"
                                 "请加宽 FRAG_TITLE_BG_W（组名＝「%s」）"
                                 % (frag_group, _tw, FRAG_TITLE_BG_PAD, FRAG_TITLE_BG_W, gcn))
            # ★ 第 7 批纵向上限自证：24px 文字在 52 高板内上下各留 = (52−24)//2 = 14px（要求 ≥10px）
            _title_v_pad = (FRAG_TITLE_BG_H - FRAG_TITLE_SIZE) // 2
            if _title_v_pad < 10:
                raise SystemExit("[FAIL] 组名文字在底板内上下仅 %dpx（要求 ≥10px）；请加高 FRAG_TITLE_BG_H"
                                 % _title_v_pad)
            gen.append({
                "id": "fc.frag%d_title_bg" % frag_group, "kind": "image", "z": 24,
                "visible_default": True,
                "asset": FRAG_TITLE_BG_ASSET, "x": ox, "y": _title_bg_y,
                "w": FRAG_TITLE_BG_W, "h": FRAG_TITLE_BG_H,
                "opacity": 255,
                "source": "专用件（第 7 批 · vision 复测加严后由**素材组产出**，件名与尺寸冻结）："
                          "`krkr/assets/ui/x_ui_fragtitle_bg.png` 444×52、硬边、霜白浅蓝底板、"
                          "**不透明核心覆盖整张**（取代第 5 批复用的 `x_ui_label_off.png`——后者四边为宽渐隐带，"
                          "拉伸后真不透明区仅 rows 7..30 / cols 13..406，会让首末字与笔画上下沿落在暗底上）",
                "vis_flag": LAYER_FLAG, "vis_when": layer,
                "note": "★ 番外独立层第 %d 组**组名标签底板**（第 5 批新增，第 7 批**换专用件**）· "
                        "素材 `ui/x_ui_fragtitle_bg.png` **444×52 硬边件**，与元素**等尺寸 ⇒ 1:1、无 `nine`** · "
                        "矩形 %d×%d @(%d,%d) = 标题文字件的同一矩形（`align:center`/`valign:middle`）；"
                        "`z = fc.frag<G>_title 的 z − 1` = 24（底板在文字之下）· 三件（底板/标题/返回键）"
                        "同组同 `vis_when:\"frag%d\"`。**为什么换件**：第 5 批复用的 `x_ui_label_off.png`（355×60）"
                        "**四边宽渐隐带**，拉到 420×38 后文字框与底板同框 ⇒ 首末字压在左右渐隐带、笔画上下沿压在上下渐隐带"
                        "⇒ HTML 侧实测**字形核心像素 5 分位对比度仅 1.04:1**（中位 12.98 达标）；专用件不透明核心覆盖整张 ⇒ 消除该类。"
                        "★ 纵向：24px 文字在 52 高板内上下各留 **%dpx**（≥10px）；组名两侧实边距 ≥ **%dpx**"
                        % (frag_group, FRAG_TITLE_BG_W, FRAG_TITLE_BG_H, ox, _title_bg_y, frag_group,
                           _title_v_pad, (FRAG_TITLE_BG_W - _tw) // 2),
            })
            gen.append({
                "id": "fc.frag%d_title" % frag_group, "kind": "text", "z": 25, "visible_default": True,
                "x": ox, "y": _title_bg_y, "w": FRAG_TITLE_BG_W, "h": FRAG_TITLE_BG_H,
                "font": {"size": FRAG_TITLE_SIZE, "bold": True, "color": TEXT_INK},
                "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
                "sample": gcn,
                "vis_flag": LAYER_FLAG, "vis_when": layer,
                "note": "★ 番外独立层顶栏标题（冻结 §二）· 文案＝生成器 `group_cn()` 结果＝「%s」（原文组名「%s」%s）"
                        "· 位置＝图表视口左上 +(6,6) 的顶栏带内、网格左上（网格行首另有 %dpx 纵向偏移）；"
                        "★ 第 5 批：矩形改与**标签底板** `fc.frag<G>_title_bg` 同一矩形（%d×%d @(%d,%d)，"
                        "`align:center`/`valign:middle`，与 `fc.label.<N>_tx` 落在 `fc.label.<N>` 上的口径一致）"
                        "—— **文字色（`@palette.psv_ink`）与字号（%d）未动**，只补底板解决「墨色画在近黑舞台上」⇒ 不可读"
                        "· 本组墨迹实测 %.1fpx ≤ 底板 %d − 2×%d=%.0f（落盘前自检）"
                        % (gcn, group, "；依据见 `GROUP_CN_MAP`" if gsrc else "（不在映射表内 ⇒ 原样透传）",
                           FRAG_LEAD_Y, FRAG_TITLE_BG_W, FRAG_TITLE_BG_H, ox, _title_bg_y,
                           FRAG_TITLE_SIZE, _tw, FRAG_TITLE_BG_W, FRAG_TITLE_BG_PAD,
                           FRAG_TITLE_BG_W - 2 * FRAG_TITLE_BG_PAD),
            })
            gen.append({
                "id": "fc.frag%d_back" % frag_group, "kind": "image", "z": 20, "visible_default": True,
                "asset": FRAGBACK_ASSET[0], "x": fb_x, "y": fb_y, "w": FRAGBACK_W, "h": FRAGBACK_H,
                "opacity": 255, "nine": dict(FRAGBACK_NINE),
                "state_assets": {"normal": FRAGBACK_ASSET[0], "hover": FRAGBACK_ASSET[1],
                                 "pressed": FRAGBACK_ASSET[2]},
                "source": "M34 PSB 复刻件（同 `fc.jump`：`x_ui_jumpfc_off/over/on.png` 157×61 / 157×61 / 204×79，"
                          "冻结 §二 指定三态复用）",
                "vis_flag": LAYER_FLAG, "vis_when": layer,
                "note": "★ 番外独立层第 %d 组「返回主干」键（冻结 §二；**按组**：`vis_when` 只能取一个值，"
                        "一个返回键无法同时服务 6 层，故按组拆——主代理 2026-09-28 第 3 批）"
                        "· 三态复用 `ui/x_ui_jumpfc_{off,over,on}.png`（与 `fc.jump` 同件同 nine %s，"
                        "故三件不同物理尺寸也能落到同一 %d×%d 矩形）" % (frag_group, FRAGBACK_NINE, FRAGBACK_W, FRAGBACK_H),
            })
            gen.append({
                "id": "fc.frag%d_back_tx" % frag_group, "kind": "text", "z": 25, "visible_default": True,
                "x": fb_x, "y": fb_y, "w": FRAGBACK_W, "h": FRAGBACK_H,
                "font": dict(FRAGBACK_TEXT_FONT),
                "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
                "sample": FRAGBACK_TEXT,
                "vis_flag": LAYER_FLAG, "vis_when": layer,
                "note": "番外独立层第 %d 组「返回主干」键文字（引擎绘制）· 文案＝「%s」· "
                        "字体/字号取本屏**既有按键文字口径**＝ `fc.jump_tx`（size %d / bold / @palette.node_locked / "
                        "align:center / valign:middle / wrap:false / max_lines:1）；文字框＝按钮件矩形"
                        % (frag_group, FRAGBACK_TEXT, FRAGBACK_TEXT_FONT["size"]),
            })
            gen.append({
                "id": "fc.frag%d_back_hit" % frag_group, "kind": "hit", "z": 95, "visible_default": True,
                "x": fb_x, "y": fb_y, "w": FRAGBACK_W, "h": FRAGBACK_H,
                "action": "flow_layer", "layer": LAYER_MAIN, "label": "",
                "vis_flag": LAYER_FLAG, "vis_when": layer,
                "note": "★ 番外独立层第 %d 组「返回主干」热区（冻结 §二；按组）：`action:\"flow_layer\"` + "
                        "`layer:\"main\"` —— 把屏级 flag `%s` 置回 `main` 并重绘/重算命中。"
                        "矩形＝`fc.frag%d_back` 件矩形。" % (frag_group, LAYER_FLAG, frag_group),
            })
            frag_stats.append({
                "group": frag_group, "group_name": group, "group_cn": gcn,
                "rows_total": len(grows), "produced": len(made),
                "dropped": [s for _i, s in dropped],
                "grid": {"cols": FRAG_COLS, "step_x": FRAG_STEP_X, "step_y": FRAG_STEP_Y,
                         "lead_y": FRAG_LEAD_Y, "origin": (ox, oy), "rows_fit": grid_rows, "cap": cap},
                "back_key": "fc.frag%d_back" % frag_group,
                "title_bg_key": "fc.frag%d_title_bg" % frag_group,
                "title_ink_w": _tw,
            })
        # ★ 第 5/7 批落盘前自检（**底托口径**）：最长组名墨迹必须装进底板（含两侧要求的**最小**内边距）
        if _title_w_max + 2 * FRAG_TITLE_BG_PAD > FRAG_TITLE_BG_W:
            raise SystemExit("[FAIL] 最长组名墨迹 %.1fpx + 2×%d > 底板宽 %d（会溢出底板）；"
                             "请加宽 FRAG_TITLE_BG_W" % (_title_w_max, FRAG_TITLE_BG_PAD, FRAG_TITLE_BG_W))
        print("  ★ 第 5/7 批·组名底托自检：%d 组底板 **%d×%d（1:1、无 nine）**（资产 %s）｜ 最长组名墨迹 %.1fpx"
              "（尺＝%s）⇒ 自检余量 %.1fpx（要求 ≥%d×2=%d ✓）／两侧**实边距各 %.1fpx**；"
              "文字在板内上下各留 %dpx（要求 ≥10 ✓）"
              % (len(frag_stats), FRAG_TITLE_BG_W, FRAG_TITLE_BG_H, FRAG_TITLE_BG_ASSET.split("/")[-1],
                 _title_w_max, _wof_title_src,
                 FRAG_TITLE_BG_W - _title_w_max - 2 * FRAG_TITLE_BG_PAD, FRAG_TITLE_BG_PAD,
                 2 * FRAG_TITLE_BG_PAD, (FRAG_TITLE_BG_W - _title_w_max) / 2.0,
                 (FRAG_TITLE_BG_H - FRAG_TITLE_SIZE) // 2))

    vx, vy, vw, vh = vp["x"], vp["y"], vp["w"], vp["h"]
    n_in_vp = sum(1 for n in order
                  if placed[n]["x"] >= vx and placed[n]["x"] + NODE_W <= vx + vw
                  and placed[n]["y"] >= vy and placed[n]["y"] + NODE_H <= vy + vh)
    # ★ §九 裁决 5 自证：**本屏全部产出元素**（图内容层）必须整体落在图表视口内
    outside = [e["id"] for e in gen
               if not (vx <= e["x"] and e["x"] + e["w"] <= vx + vw
                       and vy <= e["y"] and e["y"] + e["h"] <= vy + vh)]
    max_right = max([e["x"] + e["w"] for e in gen] or [0])
    max_bottom = max([e["y"] + e["h"] for e in gen] or [0])
    kinds = {"section": 0, "select": 0, "frag": 0, "branch": 0}
    for nid in order:
        kinds[node_kind(nodes[nid])] += 1

    elements = [json.loads(json.dumps(e, ensure_ascii=False)) for e in static] + gen
    # ── ★ 落盘前自检（第 3 批 · 主代理 item 1）：层旗标**只由图内容层持有**，双向卡 ──
    #   ① 外壳件（任何非图内容层 id）带 `vis_flag`/`vis_when` ⇒ 拒绝（会在独立层被误隐藏）；
    #   ② 图内容层件缺 `vis_flag` ⇒ 拒绝（会漏声明层归属，切换时行为未定义）。
    shell_flagged = [e["id"] for e in elements
                     if not e["id"].startswith(LAYER_OWNED_PREFIXES) and ("vis_flag" in e or "vis_when" in e)]
    if shell_flagged:
        raise SystemExit("[FAIL] 外壳件带层旗标（本批更正：外壳不参与层旗标，两态共用舞台）：%s"
                         % shell_flagged)
    content_unflagged = [e["id"] for e in elements
                         if e["id"].startswith(LAYER_OWNED_PREFIXES) and "vis_flag" not in e]
    if content_unflagged:
        raise SystemExit("[FAIL] 图内容层件缺 vis_flag/vis_when（层归属未声明）：%s" % content_unflagged)
    # ★ 冻结 §二：屏级 `flags_default` 新增 `{"fc_layer":"main"}`；演示预设另外登记逐节点运行态 flag
    flags_default = {LAYER_FLAG: LAYER_MAIN}
    if node_states:
        for i, nid in enumerate(order, 1):
            flags_default[NODE_STATE_FLAG + ("%04d" % i)] = node_states[(i - 1) % len(node_states)]
    # ★ 第 3 批自证：`fc_layer` 的 vis_when 取值集 = {"main"} ∪ {本屏实际产出的独立层}
    layer_vals = sorted({e.get("vis_when") for e in elements if e.get("vis_flag") == LAYER_FLAG})
    want_layers = sorted([LAYER_MAIN] + [FRAG_LAYER_FMT % g for g in (frag_groups or [])])
    if layer_vals != want_layers:
        raise SystemExit("[FAIL] fc_layer 的 vis_when 取值集 %s ≠ 期望 %s" % (layer_vals, want_layers))
    # ★ 第 3 批自证（**进出闭环**，两条互补的硬判据）：
    #   a) **每个已产出的独立层**都必须「进得去、回得来」——有对应入口热区（layer=frag<G>）
    #      且有**按组**返回键 `fc.frag<G>_back_hit`（action=flow_layer / layer=main）。
    #   b) ★ **裁决 4（第 4 批 · 2026-09-28）**：**任何入口热区都必须指向本档已产出的层**
    #      —— 由 `build()` 的 `skip_hit` 保证（未产出的组**根本不产热区**），此处再**无条件**卡一道：
    #      「存在 `fc.entry.*_hit` ⇒ 其 `layer` 必在本档 `produced_layers` 内」。
    #      这是对所有档（含非全量演示档）统一生效的判据，取代第 3 批「按全量档 / 非全量档分叉」的写法。
    produced_layers = [FRAG_LAYER_FMT % g for g in (frag_groups or [])]
    entry_layers = [e.get("layer") for e in gen
                    if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")]
    for lg in produced_layers:
        if lg not in entry_layers:
            raise SystemExit("[FAIL] 独立层 %s 已产出但**无入口热区**（去不了）" % lg)
        back = "fc.%s_back_hit" % lg
        if not any(x["id"] == back for x in gen):
            raise SystemExit("[FAIL] 独立层 %s 有入口但无返回键 %s（进得去回不来）" % (lg, back))
    dangling = [e["id"] for e in gen
                if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")
                and e.get("layer") not in produced_layers]
    if dangling:
        raise SystemExit("[FAIL] 入口热区指向**未产出**的独立层（裁决 4：点进去屏面为空且回不来）：%s"
                         % dangling)
    screen = {
        "id": SCREEN_ID,
        "title_cn": SCREEN_TITLE_CN,
        "owner": SCREEN_OWNER,
        "note": SCREEN_NOTE,
        "flags_default": flags_default,
        "elements": elements,
        "links": links,
    }
    stats = {
        "section": section, "section_title": sec["title"],
        "lanes": lanes_sel, "step_y": step_y, "vert_x": vert_x,
        "x0_eff": x0, "y0_eff": y0, "entry_side": (entry_side if with_entries else "-"),
        "froms": froms, "limit": limit,
        "nodes_placed": len(order), "gen_elements": len(gen), "static_elements": len(static),
        "empty_cn_fallback": empty_fallback,
        "kinds": kinds,
        "links": len(links), "forms": forms,
        "edge_states": edge_counts,
        "node_states": list(node_states) if node_states else [],
        "frags": frag_stats,
        "layer_vis_when": layer_vals,
        "flags_default": flags_default,
        "drop_not_placed": drop_not_placed, "drop_outside_canvas": drop_outside,
        "drop_degenerate": drop_degenerate,
        "entries": entry_stats,
        # ★ 裁决 4：因该组独立层未在本档产出而**不产入口热区**的组号（入口件降级为纯占位）。
        "entry_hit_skipped": entry_hit_skipped,
        "entry_hits": [e.get("layer") for e in gen
                       if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")],
        "bbox_nodes": bbox([(placed[n]["x"], placed[n]["y"], NODE_W, NODE_H) for n in order]),
        "bbox_links": link_bbox(links),
        "node_ids": order,
        "placed_raw": placed,
        "nodes_in_viewport": n_in_vp,
        "elements_outside_viewport": outside,
        "gen_max_right": max_right, "gen_max_bottom": max_bottom,
        "viewport_ok": (not outside),
        "viewport": (vp["x"], vp["y"], vp["w"], vp["h"]),
        "canvas": (cw, ch),
    }
    return screen, stats


def bbox(rects):
    if not rects:
        return None
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1, y1)


def link_bbox(links):
    """连线包围盒（pts 的极值；不含线宽 / 箭头外扩）。"""
    xs = [p[0] for l in links for p in l["pts"]]
    ys = [p[1] for l in links for p in l["pts"]]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
# 具名预设 · 交付样例金标（★ 收尾轮 ⑪：无参调用必须复现交付样例）
# ══════════════════════════════════════════════════════════════════════
# 病根（本工程反复出过的一类缺陷）：生成器的**默认参数**与**盘上交付产物**不一致 ⇒
#   谁跑一次无参就把交付物静默回退成别的样子（`build_backlog`/`build_config`/`build_music`/`build_dress`
#   一路被登记为「重跑会抹」）。本生成器不留这个坑：把交付样例那组参数**设为默认值**，
#   并在落盘前用**金标摘要**自检 —— 默认产出 ≠ 交付样例 ⇒ 拒绝落盘并报错。
PRESETS = {
    # ── 交付样例 · 屏1（默认；`python 工具/gen_flow_layout.py` 就是这个）──
    #   ★ 第 3 批：`frag_groups` 由 None 改为 **[1..6]** —— 交付样例产**全部 6 组**独立层
    #   （每组各有顶栏组名与按组返回键）⇒「点入口 → 进该组独立层 → 点返回键 → 回主干」闭环。
    "screen1": {
        "note": "交付样例·屏1（三种路由形态；section 11 / select 2；**不写 flow_state、连线全 normal** ⇒ 外观不变；"
                "★ 第 3 批：含**全部 6 组**番外独立层（入口→独立层→返回键闭环））",
        "section": 0, "lanes": "0,1", "frm": "100", "limit": 9,
        "step_y": 95, "vert_x": 375, "entry_side": "left", "entries": True,
        "node_states": None, "link_states": None, "frag_groups": [1, 2, 3, 4, 5, 6],
    },
    # ── 交付样例 · 屏2（含 frag 番外节点）──
    "screen2": {
        "note": "交付样例·屏2（含 frag 番外节点；section 4 / select 5 / frag 9；本段数据无跨道边 ⇒ 只有直线；"
                "**不写 flow_state、连线全 normal** ⇒ 外观不变）",
        "section": 3, "lanes": "1,2", "frm": "0", "limit": 9,
        "step_y": 95, "vert_x": 375, "entry_side": "left", "entries": True,
        "node_states": None, "link_states": None, "frag_groups": None,
    },
    # ── 参照作口径变体（**不是交付样例**）──
    "ref150": {
        "note": "★ 参照作口径变体（step_y=150）——**不是交付样例**；跑它会把 32_flowchart.json 换成变体"
                "（11 节点 / VZ 0：该行距下一屏只有 6 行，VZ 边被视口裁掉、根本没进屏数据）",
        "section": 0, "lanes": "0,1", "frm": "100", "limit": 9,
        "step_y": 150, "vert_x": 375, "entry_side": "left", "entries": True,
        "node_states": None, "link_states": None, "frag_groups": None,
    },
    # ── ★ 第 2 步 · A 运行态演示（冻结 §一）：节点五态 + 连线三档同屏（**不是交付样例**）──
    "states": {
        "note": "★ 运行态演示（冻结 §一）——**不是交付样例**：节点 `flow_state` 按 "
                "[locked→`_dim` 压暗件（★ ISSUE-20260928-03 改 image，按种类取件） / available / "
                "visited→`_read` 已读绿对勾（★ ISSUE-20260928-03 新增） / current→不产元素（两端程序化画环，只留金环、不加对勾） / "
                "new→`_new` 角标件] 循环演示；连线 `state` 按 [normal / visited / noroute] 循环 ⇒ **三档同屏**",
        "section": 0, "lanes": "0,1", "frm": "100", "limit": 9,
        "step_y": 95, "vert_x": 375, "entry_side": "left", "entries": True,
        "node_states": ["locked", "available", "visited", "current", "new"],
        "link_states": ["normal", "visited", "noroute"],
        "frag_groups": None,
    },
    # ── ★ 第 2 步 · B 番外独立层演示（冻结 §二）：主干 + **仅第 1 组**独立层（**不是交付样例**）──
    #   ★ 第 3 批：交付样例 screen1 已含全部 6 组；本预设保留「**只第 1 组**」的最小档，
    #   供守门断言 `fc_layer` 取值集恰为 [frag1, main]（单层口径的干净夹具）。
    "frag": {
        "note": "★ 番外独立层演示（冻结 §二）——**不是交付样例**：主干（同 screen1 参数）+ spine 第 1 组"
                "（`番外·阿雷克桑德平安夜（おっぱい系列）`）独立层；屏级 flag `fc_layer` 初值 `main`"
                "（跑它时屏文件仍是主干视图；把 flag 改成 `frag1` 即切该组独立层）",
        "section": 0, "lanes": "0,1", "frm": "100", "limit": 9,
        "step_y": 95, "vert_x": 375, "entry_side": "left", "entries": True,
        "node_states": None, "link_states": None, "frag_groups": [1],
    },
    # ── ★ 第 2 步 · D 全量（冻结 §五）：**只交几何与数据、不产元素**，落 _工作 下 JSON ──
    "full": {
        "note": "★ 全量几何数据（冻结 §五）——**只交数据、不产 elements**；元素化渲染交编程组。"
                "产出 `_工作\\ISSUE-20260928-02_第2步\\全量布局.json`，**不写屏文件**",
        "section": None, "lanes": None, "frm": None, "limit": None,
        "step_y": FULL_STEP_Y, "vert_x": 375, "entry_side": "left", "entries": False,
        "node_states": None, "link_states": None, "frag_groups": None,
    },
}
DEFAULT_PRESET = "screen1"

# ★ 金标：预设 → (整文件 md5, **去 note 后的内容 sha256**)
#   · 整文件 md5：落盘前自检的**主判据**（无参/具名预设且写默认屏文件时）
#   · 内容 sha256：把「屏级 note + 每个元素的 note」剥掉后规范化序列化的摘要 ⇒ **对措辞编辑免疫**，
#     用来证明「本次变的是 note 还是内容」。`--refresh-golden` 会同时重钉两者。
#   ★ 第 2 步起为**五**个预设（screen1 / screen2 / ref150 / states / frag）；`full` 不产屏文件、无金标。
GOLDEN = {
    "screen1": ("801d447520a8b5967e3a99fda5aec187", "69300239ed66b9767fc047a0eea655c3f8b4e163ed881f71745063d4674c31a3"),
    "screen2": ("37fe3902823381b66c4da94b1cb1fdda", "91d5cab9c97b9b77bb8dbd8e7859cdcac608c9054728268a70ec084f1b38b0af"),
    "ref150": ("012af841e2471a2690402cf659e548db", "297ad56f2dc00425a97b63469413044e90cc166d530c38299520a87fa26b2d6f"),
    "states": ("e0a407098e5ed31305529202932f2530", "96e34141b8803b51ef46d4f0dd204cb42fd9a16baed9237cf34ee5a89a1efbf0"),
    "frag": ("b8aa2703b28543cc75be605e3a26241d", "ac7c119a7f4389bac942f03f2c47e53c36463bbac3ad18a41b34df3ed3f2ef14"),
}
GOLDEN_ORDER = ("screen1", "screen2", "ref150", "states", "frag")

PRESET_TABLE = """预设名 → 命令行 → 产出规模 → md5（金标，实跑真值）
  screen1（**默认**，无参即此）  python 工具/gen_flow_layout.py
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95 ｜ 13 节点（section 11/select 2）｜ 13 连线（直线 11/VZ 1/VL 1，全 normal）
      289 元素（**总**）＝ 外壳 **61** ＋ 图内容层 **228**
      ├ 外壳 61：`fc.` 图内容层前缀之外的一切（视口/迷你地图/滚条/页签/标题牌/关闭/付箋/回放/进入本章/右栏详情）—— **不带层旗标**
      └ 图内容层 228 ＝ 主干 **63**（`fc.node.*` 39 ＋ `fc.label.*` 12 ＋ `fc.entry.*` 12；`fc.branch.*` 0）
        ＋ 独立层节点 **135**（6 组共 45 格 ×3〔image/text/hit〕）
        ＋ 每组顶栏 **30**（6 组 × 5：`_title`／**`_title_bg`（组名底托，第 5 批）**／`_back`／`_back_tx`／`_back_hit`）
        （⇒ 63 ＋ 135 ＋ 30 ＝ 228 ✓；★ 注意「组名底托 6 件」**是顶栏 30 的子集，不得另加**——
         上一版把它另列并写成「主干 124」，124 是**第 2 批时的旧总元素数**，被误标成主干，已订正）
      ★ 第 3 批：交付样例含**全部 6 组**番外独立层（G1 7/7、G2 7/7、G3 4/4、G4 10/10、G5 5/5、G6 12/20）⇒ 入口→独立层→按组返回键闭环
      ★ 第 4 批（裁决 4）：本档 6 组入口**均已产独立层** ⇒ **6/6 组有入口热区**（无占位缺口）
      ★ 第 5 批：每组顶栏加**组名标签底板** `fc.frag<G>_title_bg`（+6 件 ⇒ 283 → 289；修「组名对比度 1.19:1 不可读」）
      ★ 第 7 批：组名底托**换专用件** `x_ui_fragtitle_bg.png`（444×52、硬边、1:1 无 nine）⇒ 元素数不变（289）、几何与素材变
      ★ 第 8 批（`ISSUE-20260928-03`）：**元素内容逐字不变**（content-sha256 与第 7 批同值）——md5 变因**仅屏 note 措辞**
      ★ 第 9 批：**唯一一处文字变更** —— `fc.frag6.0007_tx`（script `62_1b`）按 `TITLE_HARD_BREAK` 断成两行（旧单行 255px/左缘 +20.50 ⇒ 新 122/133px、左缘 +87）⇒ 元素数不变（**289**）、该 `sample` 与屏 note 变
      md5 = 801d447520a8b5967e3a99fda5aec187 ｜ content-sha256 = 69300239ed66b9767fc047a0eea655c3f8b4e163ed881f71745063d4674c31a3
      ★ 第 10 批：**两行条数 101 → 105**；`fc.frag4.0008_tx`（script `42_3`）与 `fc.frag4.0009_tx`（`42_4`）的
        `sample` 各插一个硬换行（断在「（」前）—— **本批对交付样例的有意变更恰此 2 处**（md5 与 content-sha 都因此变）
  screen2                        python 工具/gen_flow_layout.py --preset screen2
      段[3] AfterStory 道 1,2 from 0 limit 9 step_y 95 ｜ 18 节点（section 4/select 5/frag 9）｜ 14 连线（直线 14，全 normal）｜ 133 元素
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 139 → 133，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因**共用静态件 `fc.zoom_minus/plus` 的 `source` 订正**（见下）
      ★ 第 7 批：**content-sha256 逐字不变**（无底托、连线全 normal）⇒ 只有屏 note 措辞变（本批追加两段）
      ★ 第 8 批：**content-sha256 逐字不变**（元素内容未动）⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = 37fe3902823381b66c4da94b1cb1fdda ｜ content-sha256 = 91d5cab9c97b9b77bb8dbd8e7859cdcac608c9054728268a70ec084f1b38b0af
      ★ 第 10 批：**content-sha256 逐字不变**（本档无表内标题）⇒ md5 变因**仅屏 note 共用**
  ref150（**不是交付样例**）      python 工具/gen_flow_layout.py --preset ref150
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 150 ｜ 11 节点（section 9/select 2）｜ 10 连线（直线 9/VL 1，无 VZ，全 normal）｜ 112 元素
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 118 → 112，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因同上（`source` 订正）
      ★ 第 7 批：同上（**content-sha256 逐字不变**）
      ★ 第 8 批：**content-sha256 逐字不变** ⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = 012af841e2471a2690402cf659e548db ｜ content-sha256 = 297ad56f2dc00425a97b63469413044e90cc166d530c38299520a87fa26b2d6f
      ★ 第 10 批：**content-sha256 逐字不变**（本档无表内标题）⇒ md5 变因**仅屏 note 共用**
  states（**不是交付样例**）      python 工具/gen_flow_layout.py --preset states
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95 ｜ 13 节点（与 screen1 同一批）｜ 13 连线（**normal 5 / visited 4 / noroute 4 —— 三档同屏**）｜ 126 元素
      （节点 flow_state 循环 locked→available→visited→current→new：`_dim` 3 件（**image，按种类取件**）、
        `_new` 2 件、`_read` 3 件（已读绿对勾）；`current` **不产元素**，两端程序化画环、**只留金环、不加对勾**）
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 129 → 123，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因同上（`source` 订正）
      ★ 第 7 批：`edge_noroute` 调暗 #6A6A7A → #5A5A68 ⇒ **本档 noroute 边的 `color` 内嵌值变**（元素数不变 123）
      ★ 第 8 批（`ISSUE-20260928-03`）：① `_dim` 由 `rect` 改 **`image`**（按节点种类取压暗件、与底图件同几何同 nine）
        —— 修「方角 55px 暗方角」真缺陷；② 新增 `_read` 3 件（visited）。⇒ **123 → 126 元素**
        （3 个 locked：node 0001＝**select**、0006/0011＝section ⇒ 本档同时演示 select 与 section 两种压暗件）
      md5 = e0a407098e5ed31305529202932f2530 ｜ content-sha256 = 96e34141b8803b51ef46d4f0dd204cb42fd9a16baed9237cf34ee5a89a1efbf0
      ★ 第 10 批：**content-sha256 逐字不变**（本档无 `fc.frag*`，不含表内标题）⇒ md5 变因**仅屏 note 共用**
  frag（**不是交付样例**）        python 工具/gen_flow_layout.py --preset frag
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95（主干同 screen1）＋ spine **第 1 组**番外独立层 7/7 格
      13 节点 ｜ 13 连线（全 normal；**独立层不产连线**）｜ 145 元素（＝第 4 批 144 ＋ **1 件组名底托**）
      ★ 第 4 批（裁决 4）：本档只产**第 1 组**独立层 ⇒ 仅 **1 个入口热区**（`layer:frag1`），其余 5 组入口为纯占位
      ★ 第 7 批：底托换件（同上）⇒ 元素数不变（145）、几何与素材变
      ★ 第 8 批：**content-sha256 逐字不变** ⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = b8aa2703b28543cc75be605e3a26241d ｜ content-sha256 = ac7c119a7f4389bac942f03f2c47e53c36463bbac3ad18a41b34df3ed3f2ef14
      ★ 第 10 批：**content-sha256 逐字不变**（`frag` 档展示的组内无表内标题）⇒ md5 变因**仅屏 note 共用**
  full（**不是交付样例**；只交数据）  python 工具/gen_flow_layout.py --preset full
      6 段 / 19 道 / 712 lane 节点（section 579 / select 77 / frag 53 / branch 3）｜ **不产 elements**
      → _工作\\ISSUE-20260928-02_第2步\\全量布局.json（元素化渲染交编程组）
  文字参数（五预设共用）：字号 19px / 行距 1.0（元素级 line_spacing）/ 文字盒 240 / max_lines 2；
  四判据实测最小值：上留 5px、下留 5px、最宽行 255px、截断 0。
  番外组名（五预设共用）：经 `GROUP_CN_MAP` 中文化的 6 个组名（ISSUE-20260927-06）——映射 3 组、透传 3 组。
  连线（五预设共用口径）：`state` ∈ normal(#266080 / w4 / 有箭头) ｜ visited(#3580A8 / w4 / 有箭头) ｜ noroute(**#5A5A68** / w3 / **无箭头**)。
  ★ **裁决 4（第 4 批 · 2026-09-28 主代理）：入口热区 `fc.entry.<NNNN>_hit` 只在该组独立层确实产出时才产。**
    · `screen1` 产全部 6 组 ⇒ **6/6 入口热区**；`frag` 只产第 1 组 ⇒ **1**；`screen2`/`ref150`/`states` 不产独立层 ⇒ **0**。
    · 未产出 ⇒ 入口 image / 组名标签**仍在**（主干层可见的**纯占位**、不可点），元素数各档相应减少（−6 / −5）。
    · 落盘前**无条件**自检「存在 `fc.entry.*_hit` ⇒ 其 `layer` ∈ 本档产出层」，违反即拒绝落盘。
    · 生成器每次跑打印一行可判读说明（哪个档、哪几组因此不产热区）；`--frag-report` 与屏 `note` 同口径。
  ★ **第 5 批重钉（2026-09-28 收口 · 主代理）——两件事：**
    ① **独立层组名加「标签底板」**（真缺陷修复）：每组新增 `fc.frag<G>_title_bg`（image，素材复用主图标签
       `ui/x_ui_label_off.png`、**零九宫格整图缩放**口径同 `fc.label.<NNNN>`、**420×38 @(66,199)**、
       `z=24`＝标题 z−1、与标题/返回键**同组同 `vis_when`**）；标题文字件改为**与底板同矩形**
       （`align:center`/`valign:middle`，同 `fc.label.<N>_tx` 惯例）—— **文字色与字号未动**。
       起因：组名墨色 `@palette.psv_ink`(#16223A) 原直接画在近黑舞台（`fc.dim`＋`fc.scroll` 合成 ≈(14,17,22)）
       上，**对比度仅 1.19:1 ⇒ 不可读**；加底托后 **≈13.5:1**（底板核心实色 (228,238,250)，WCAG 相对亮度比）。
       落盘前自检：最长组名墨迹 396px + 2×12 ≤ 420，违者拒绝落盘。
    ② **静态件 `fc.zoom_minus`/`fc.zoom_plus` 的过期描述订正**：`source`/`note` 原写按下态 `_on` 为 **41×41**，
       实测三态**均为 29×29**（⇒ 按下不放大），已改为现况并补「『按下放大』登记为缺口 G-2」。
  ★ **第 7 批（2026-09-28 · 小修两处）：**
    ① **组名底托换专用硬边件**：`fc.frag<G>_title_bg` 的 `asset` → `ui/x_ui_fragtitle_bg.png`（444×52、硬边、**不透明核心覆盖整张**，1:1、**无 `nine`**）；
       几何 **444×52 @(66,192)**（`y` 使文字墨迹行仍 206..229、文字中心仍 218，与第 5 批同位）；落盘自检 **余量 24px**（396+24=420 ≤ 444）、文字上下各留 **14px**。
       起因：复用件（355×60，四边宽渐隐带）拉到 420×38 后**字形核心像素 5 分位对比度仅 1.04:1**（HTML 实测）。
    ② **`@palette.edge_noroute` 调暗 `#6A6A7A` → `#5A5A68`**（只改 palette 一个键）：原值在引擎深底上 2.59:1、**比 normal 的 2.01:1 更亮** ⇒ 层级反了。
       **交付样例 `screen1` 连线全 normal ⇒ 其屏幕数据不含该值**（`screen1` 的 content-sha 变化只来自底托几何/素材与 note；`states` 变因 noroute 边内嵌色值）。
  ★ **第 7 批重钉（2026-09-28）**：上表前五行为现行值。上一批（第 5 批）值
    `aa4be586…`／`c56ce544…`／`d4cd5447…`／`fb4d6e19…`／`8841c6a8…` 与更早各批所有值**全部作废**
    （`screen2`/`ref150` 的 **content-sha256 逐字不变** ⇒ 证明只有 note 措辞变）。
  ★ **第 5 批重钉（2026-09-28）**：上表前五行为现行值。上一批（第 4 批）值
    `42247f41…`／`d9c7214e…`／`6cfa4c4f…`／`2f26fa4c…`／`a4162286…` 与更早各批所有值**全部作废**
    （`screen2`/`ref150`/`states` 三档元素数不变，md5/`content-sha256` 变因仅 **`source` 订正**）。
  （五个屏预设都写同一个屏文件 layout/screens/32_flowchart.json；跑完非 screen1 的预设后，请再跑一次无参回到交付样例。）
  ★ **第 8 批（2026-09-28 · `ISSUE-20260928-03` · 节点运行态两处修正）**：上表前五行为现行值。
    上一批（第 7 批）值 `4c8f01c0…`／`51f58498…`／`e9df490e…`／`21ecd73e…`／`7f30a924…` 与更早各批全部值**作废**。
    ① **修「未解锁压暗件方角」真缺陷**：`_dim` 由 `kind:"rect"`（方角 284×48）改 **`kind:"image"`** ——
       按节点种类取压暗件（section/select/frag 三族，件名冻结）、**几何与 `nine` 与该节点底图件逐字段一致**、
       **强度仍由元素 `opacity` 控（110）**。根因：节点可见实体面四角是 r=16 圆弧、弧外透明，方角矩形四角压在
       背景上 ⇒ locked 节点每角露出约 55px 暗方角（实测 (8,10,13) vs 同型 available (15,18,24)）。
    ② **新增「已读」绿对勾 `_read`**（用户 2026-09-28 裁决「丙方案」）：image 20×20（1:1 无 nine）、
       节点可见实体面左上角内缘 `(x+10, y+12)`、`z`＝节点 z+6（与 `_new` 同档）、`vis_when:"visited"`；
       **`current` 不加对勾**（只留金环）。备选件 `x_ui_read_check_alt.png` 不接线。
    ⇒ **只有 `states` 预设含运行态** ⇒ 其元素数 **123 → 126**（＋3 `_read`）；其余四档**元素内容不变**
      （`screen1` md5/`content-sha256` 变因**仅屏 note 措辞**——本批口径追加到屏 note；逐档 content-sha256 见实跑）。
  ★ **第 9 批（2026-09-28 · vision 复核后的数据侧最后一处修复）**：上表前五行为现行值。
    上一批（第 8 批）值 `0527ae97…`／`2f76c5fd…`／`ac24df59…`／`bbac0fd5…`／`f8fb0ab6…` 与更早各批全部值**作废**
    （★ 注意：`screen2`/`ref150`/`states`/`frag` 的 md5 与第 8 批**同值** ⇒ 本批未动这四档的元素内容与 note，
     只有 `screen1` 变）。
    ① **新增「已读对勾」不变量（落盘前自检）**：所有含文字节点的**首行墨迹左缘 ≥ x_node + 30**〔★ 第 10 批已收紧为 **+34**，见下〕
       （＝对勾 20×20 @(x+10,y+12) 的右缘 +30；等价「首行墨迹 ≤ 236px」）—— 违反即**拒绝落盘**并逐条打印。
       实测 712 条 **违规 0**、最紧 **+30.00**（`s04_03f1`）。
    ② **新增常量表 `TITLE_HARD_BREAK`（第 9 批 12 条；★ 第 10 批 +8 ＝ 20 条）**：在自然断点插硬换行，修掉全量 12 条「首行墨迹 < +29」的标题
       （成因＝末尾行首禁则字符被 `ui_theme_wrap` 强行并入本行 ⇒ 单行 247–255px）；
       断点优先级 A 全角开括号/引号/波浪之前 ＞ B 句读标点之后 ＞ C 拉丁空格；断后两行 **≤ 230px**（实测最大 202）。
       ⇒ **`screen1` 的外观变更＝`fc.frag6.0007_tx`（62_1b）**；其余 11 条不在交付样例的四档里。
    ③ 机检：`--title-check-report`（不变量实测 + 违规清单）／`--selfcheck-title-break`（变异自证：删一条必越线、
       表清空 ≥ **表内条数** ⇒ 非恒真）；四判据 A/B/C/D 改后**仍全绿**（两行 2×19=38 ≤ 39）。
  ★ **第 10 批（2026-09-28 · `ISSUE-20260928-04` · 用户看完实机对照图后裁决）—— 上表前五行为现行值**：
    · **不变量 `TITLE_CHECK_GAP` 由 30 收紧为 34**（＝对勾右缘 +30 再留 **≥4px**）⇒ 等价判据**首行墨迹 ≤ 228px**；
    · **`TITLE_HARD_BREAK` 追加 8 条**「零间隙边界簇」（`42_3`/`42_4`/`s01_09c4`/`s02_10b`/`s04_03f1`/
      `s04_03f2`/`s04_03f3`/`s03_17a`；断点＝「（」前、「·」「，」后）—— 原余量仅 0–2px，其中 4 条本就是
      「236px 长行 + 2–3 字尾巴」的难看折行（`42_4` 还把 `ＦＡＬＣＯＮ` 从中切断）；
    · 收紧后全量：**最紧 +34.00（`s01_02b`）／两行 105／最宽行 228.0px／截断 0／违规 0**；
    · **`screen1` 再变 2 处**＝`fc.frag4.0008_tx`（`42_3`）与 `fc.frag4.0009_tx`（`42_4`）的 `sample` 各插硬换行
      ⇒ 该档**累计文字变更 3 处**（62_1b／42_3／42_4）。★ **更正第 9 批那句话**：「其余 11 条不在四档」
      只对第 9 批那 12 条成立 —— 第 10 批新增的 8 条里 **有 2 条在交付样例里**（上句那两件）；
    · 另补**幻影 id 守卫**（表内 id 必须 ⊆ 源语料键集，否则拒绝落盘 —— 一审指出的空档）；
    · 交付样例的「有意变更总账」落在 `_工作/ISSUE-20260928-02_第2步/复现脚本/m06_delivered_sample_ledger.py`，
      且 **`m01` 第 10 批起直接消费该总账** ⇒ `run_all` 在**未提交窗口**内也能全绿（不再只能事后验）。
  （`--refresh-golden` 只重钉上表五组的 `GOLDEN` 字面量，**本表要手改**——冻结 §七 明写。）
"""


def content_sha256(screen):
    r"""去 note 后的内容摘要（屏级 note + 所有元素 note 剥掉，键排序、紧凑分隔符）。"""
    d = json.loads(json.dumps(screen, ensure_ascii=False))
    d.pop("note", None)
    for e in d.get("elements", []):
        e.pop("note", None)
    blob = json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def serialize_screen(screen):
    return (json.dumps(screen, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def parse_list(s, n, name):
    if s is None:
        return [0] * n
    parts = [p.strip() for p in str(s).split(",") if p.strip() != ""]
    vals = [int(p) for p in parts]
    if len(vals) == 1:
        return vals * n
    if len(vals) != n:
        raise SystemExit("[FAIL] --%s 给了 %d 项，但 --lanes 有 %d 道" % (name, len(vals), n))
    return vals


def run_once(section, sel, frm, limit, step_y, vert_x, x0, y0, no_entries, entry_side, preset_name,
             node_states=None, link_states=None, frag_groups=None, frag_limit=None):
    """按一组参数产出 (screen, stats)，并加上「预设注记」。

    ★ 三条路径（无参/具名预设、`--refresh-golden`、`--selfcheck-delivered`）共用本函数 ⇒
    金标摘要一定在**与落盘完全相同的字节**上计算（否则 refresh 会钉到「无注记版」的 md5，
    无参跑就会永远自检失败）。
    """
    data = load_data()
    if sel is None:
        sel = list(range(len(data["sections"][section]["lanes"])))
    froms = parse_list(frm, len(sel), "from")
    static = load_static_elements()
    vp = next(e for e in static if e["id"] == "fc.scroll")
    x0v = x0 if x0 is not None else vp["x"] + vp["w"] / 2.0
    y0v = y0 if y0 is not None else vp["y"]
    screen, st = build(section, sel, froms, limit, step_y, vert_x, x0v, y0v,
                       not no_entries, cull=True, entry_side=entry_side, x0_locked=(x0 is not None),
                       node_states=node_states, link_states=link_states,
                       frag_groups=frag_groups, frag_limit=frag_limit)
    decorate_preset_note(screen, preset_name, st)
    return screen, st


def preset_run(name):
    """按具名预设跑一次（参数一律取自 PRESETS[name]）。"""
    p = PRESETS[name]
    return run_once(p["section"], parse_lanes(p["lanes"], load_data(), p["section"]),
                    p["frm"], p["limit"], p["step_y"], p["vert_x"], None, None,
                    False, p["entry_side"], name,
                    node_states=p.get("node_states"), link_states=p.get("link_states"),
                    frag_groups=p.get("frag_groups"))


def decorate_preset_note(screen, preset_name, st):
    """屏 note 末尾追加「本文件由预设 X 产出 + 参数 + 回到交付样例的办法」。"""
    extra = ""
    if st.get("node_states"):
        extra += ("；节点 flow_state 循环 %s（叠加件 `_dim`（locked，image）／`_new`（new）／"
                  "`_read`（visited，已读绿对勾）；`current` 不产元素 ⇒ 只留金环、不加对勾）"
                  % st["node_states"])
    if st.get("edge_states") and len([k for k, n in st["edge_states"].items() if n]) > 1:
        extra += "；连线 state 分布 %s" % {k: n for k, n in st["edge_states"].items() if n}
    if st.get("frags"):
        f = st["frags"]
        extra += ("；番外独立层 **%d 组**：%s（每组一顶栏标题 + 一按组返回键 `fc.frag<G>_back[_hit/_tx]`；"
                  "网格 %d 列 × 步进 %d/%d、行首偏移 %d、原点 %s；**独立层不产连线**；"
                  "超出视口的格不产，纵滚/横移属编程组）"
                  % (len(f),
                     "／".join("组%d「%s」%d/%d 格%s" % (x["group"], x["group_cn"], x["produced"], x["rows_total"],
                                                    "" if not x["dropped"] else "（未产 %d）" % len(x["dropped"]))
                              for x in f),
                     f[0]["grid"]["cols"], f[0]["grid"]["step_x"], f[0]["grid"]["step_y"],
                     f[0]["grid"]["lead_y"], f[0]["grid"]["origin"]))
    # ★ 裁决 4（第 4 批）：本档哪些组的入口**因独立层未产出而不产热区**（该档口径随屏 note 落盘）
    _skip = st.get("entry_hit_skipped") or []
    if _skip:
        extra += ("；★ 裁决 4：本档有 **%d 组**未产独立层 ⇒ 对应 `fc.entry.*` 为**纯占位**、"
                  "**不产 `fc.entry.*_hit` 热区**（点不进任何层）：组 %s" % (len(_skip), _skip))
    else:
        extra += "；★ 裁决 4：本档入口组均已产独立层 ⇒ 入口热区齐备（无占位缺口）"
    screen["note"] = (
        screen["note"]
        + "\n· ★ 本文件由**预设 %s** 产出（%s）；参数：段[%d] 道 %s from %s limit %d "
          "step_y %d vert_x %d entry_side=%s%s。改回交付样例＝跑一次无参 `python 工具\\gen_flow_layout.py`。"
        % (preset_name, PRESETS[preset_name]["note"], st["section"], st["lanes"],
           st["froms"], st["limit"], st["step_y"], st["vert_x"], st["entry_side"], extra))


def selfcheck_delivered():
    r"""反向自证（内存构造，**不落盘**）：把默认预设的 step_y 改成 150 ⇒ 交付自检必须拦下，且盘上 md5 不变。

    ★ 变异对象 = **默认参数本身**（不是传一个显式开关）：这正是「重跑即静默回退」缺陷的形态。
    """
    import copy
    ok = True
    before = hashlib.md5(open(DEFAULT_OUT, "rb").read()).hexdigest() if os.path.exists(DEFAULT_OUT) else "(无)"
    print("=" * 78)
    print("交付自检 · 反向自证（内存里把默认预设的 step_y 改成 150，不落盘）")
    print("  运行前 32_flowchart.json md5 = %s" % before)
    MUTATED_STEP_Y = 150
    saved = copy.deepcopy(PRESETS["screen1"])
    try:
        PRESETS["screen1"]["step_y"] = MUTATED_STEP_Y
        # ★ 变异 = 默认参数本身被改成 150（不是传显式开关）：这正是「重跑即静默回退」的形态
        mut_lanes = [int(x) for x in saved["lanes"].split(",") if x.strip() != ""]
        screen, st = run_once(saved["section"], mut_lanes, saved["frm"], saved["limit"],
                              MUTATED_STEP_Y, saved["vert_x"], None, None, False,
                              saved["entry_side"], "screen1")
        blob = serialize_screen(screen)
        got = hashlib.md5(blob).hexdigest()
        want = GOLDEN["screen1"][0]
        if got == want:
            print("  ✗ 变异后仍与金标一致（自检恒真！）；got=%s want=%s" % (got, want))
            ok = False
        else:
            print("  ✓ 变异后摘要 %s ≠ 金标 %s ⇒ 落盘前自检会拒绝" % (got, want))
        if st["nodes_placed"] != 13 or st["forms"]["vz"] != 1:
            print("  ✓ 变异确实改了产出规模（节点 %d、VZ %d）" % (st["nodes_placed"], st["forms"]["vz"]))
    finally:
        PRESETS["screen1"].clear()
        PRESETS["screen1"].update(saved)
    after = hashlib.md5(open(DEFAULT_OUT, "rb").read()).hexdigest() if os.path.exists(DEFAULT_OUT) else "(无)"
    if after != before:
        print("  ✗ 自证把盘上文件改了！%s → %s" % (before, after))
        ok = False
    else:
        print("  ✓ 盘上 32_flowchart.json md5 未变（%s）" % after)
    print("  自证结果：%s" % ("按预期 ✓" if ok else "**不符合预期** ✗"))
    return 0 if ok else 1


def refresh_golden(rows):
    """把实跑得到的五组 (md5, content-sha) 回填进本文件的 GOLDEN 字面量。"""
    text = open(os.path.abspath(__file__), encoding="utf-8").read()
    for name, md5v, shav in rows:
        pat = r'("%s": \()("[^"]*", "[^"]*")(\))' % name
        text = re.sub(pat, lambda m: m.group(1) + '"%s", "%s"' % (md5v, shav) + m.group(3), text)
    with open(os.path.abspath(__file__), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[golden] 已重钉 %d 组金标：" % len(rows))
    for name, md5v, shav in rows:
        print("  %-8s md5=%s  content-sha256=%s" % (name, md5v, shav[:16] + "…"))


def emit_full_layout(step_y=FULL_STEP_Y, vert_x=375, out=FULL_OUT, dry_run=False):
    r"""★ 冻结 §五：**只交几何与数据、不交元素** —— 全量布局数据。

    产出 `_工作\ISSUE-20260928-02_第2步\全量布局.json`：
      · 逐节点 `{id, group, lane, kind, x, y, w, h, flow_state}`
      · 每 lane 的 `step_y` 与内容 bbox（＋道名/段名/首行 y/槽位 x/节点 id 序）
      · 全局内容 bbox ＋ 视口/画布参数
    **绝不产 `elements`**：全量 627 节点 ≈ 1,881 个元素（另加番外 53×3）——逐元素渲染的层预算
    未验证、纵滚/横移机制属编程组 ⇒ 元素化渲染交编程组（冻结 §五）。

    口径与 `build()` 完全同源：`lane` 内节点沿主轴推进（`y = 视口顶 + lane 内序号 × step_y`）、
    道与道之间横向档距 `vert_x` 并**按段居中**；**跨 lane 的共享节点只出现一次**
    （取其首次出现的 lane，契约 §8.4 第 2 条）；`kind=="branch"` 的节点几何为**分支底座 65×65**
    （居中于 296 宽槽位），与 `build()` 的产出件几何逐字一致。
    """
    data = load_data()
    nodes, sections = data["nodes"], data["sections"]
    canvas = load_canvas()
    static = load_static_elements()
    vp = next(e for e in static if e["id"] == "fc.scroll")
    vpx, vpy, vpw, vph = vp["x"], vp["y"], vp["w"], vp["h"]
    x0 = vpx + vpw / 2.0

    seen, out_nodes, lanes_out = set(), [], []
    dup_entries = 0
    for si, sec in enumerate(sections):
        lane_list = sec["lanes"]
        D = len(lane_list)
        for li, lane in enumerate(lane_list):
            cx = x0 + (li - (D - 1) / 2.0) * vert_x
            slot_x = int(round(cx - NODE_W / 2.0))
            ids, rects = [], []
            for idx, ent in enumerate(lane["nodes"]):
                nid = ent["id"]
                if nid in seen:
                    dup_entries += 1        # 跨 lane 共享节点：只取首次出现的 lane（契约 §8.4 第 2 条）
                    continue
                seen.add(nid)
                v = nodes.get(nid)
                if v is None:
                    raise SystemExit("[FAIL] 全量布局：lane 引用了 DATA.nodes 里不存在的 id：%s" % nid)
                k = node_kind(v)
                y = vpy + idx * step_y
                if k == "branch":
                    ex, ey, ew, eh = slot_x + BRANCH_OFFSET_X, y, BRANCH_W, BRANCH_H
                else:
                    ex, ey, ew, eh = slot_x, y, NODE_W, NODE_H
                ids.append(nid)
                rects.append((ex, ey, ew, eh))
                out_nodes.append({
                    "id": nid, "group": sec["title"], "lane": "%d:%d" % (si, li), "kind": k,
                    "x": ex, "y": ey, "w": ew, "h": eh, "flow_state": FLOW_STATE_DEFAULT,
                })
            lanes_out.append({
                "key": "%d:%d" % (si, li), "section": si, "section_title": sec["title"],
                "lane": li, "lane_title": lane.get("title") or "",
                "x": slot_x, "y0": vpy, "step_y": step_y,
                "nodes_total": len(lane["nodes"]), "nodes_emitted": len(ids),
                "bbox": bbox(rects), "nodes": ids,
            })
    by_kind = {k: 0 for k in ("section", "select", "frag", "branch")}
    for n in out_nodes:
        by_kind[n["kind"]] += 1
    trunk = by_kind["section"] + by_kind["select"]
    est_trunk = trunk * 3 + by_kind["branch"] * 1        # branch 只出 1 件底座（不出节点框）
    est_all = est_trunk + by_kind["frag"] * 3
    meta = {
        "generated_by": "工具\\gen_flow_layout.py --preset full（**生成物，禁止手改**）",
        "issue": "ISSUE-20260928-02（第 2 步 · 模块 E1 数据层）",
        "interface": "_工作\\ISSUE-20260928-02_第2步\\接口冻结.md §五",
        "sources": ["资源组\\08_全系列章节流程图.html 的 `const DATA`（**不解析 DOM**）",
                    "资源组\\剧本\\spine.json（仅用于分组计数）",
                    "layout\\_root.json（画布）／layout\\screens\\32_flowchart.json 快照（视口 fc.scroll）"],
        "reason_no_elements": (
            "**本文件只交几何与数据，不交 `elements`**（冻结 §五）：`fc.node.*` 每节点 3 个元素"
            "（image/text/hit）⇒ 全量 627 节点 ≈ 1,881 个元素（另加番外 53×3）；逐元素渲染全量的"
            "**层预算未验证**，且纵滚/横移机制是否属 UI 组能力未定 ⇒ **元素化 / 纵滚 / 横移 / 迷你地图 / 缩放交编程组**。"),
        "element_estimate": {
            "冻结原文": "627 节点 ≈ 1,881 个元素（＝627×3）；另加番外 53×3",
            "实测_主干节点（kind ∈ section|select）": trunk,
            "实测_branch 节点（只出 1 件底座）": by_kind["branch"],
            "实测_番外节点（kind == frag）": by_kind["frag"],
            "按本轮口径元素化估算_主干": est_trunk,
            "按本轮口径元素化估算_合计含番外": est_all,
            "差异说明": (
                "**冻结的 627 未能在数据里复现**：实测主干（section+select）＝%d，差 %d。"
                "可试的口径都对不上 —— 712（全部 lane 节点）− 53（frag）＝659；再减 3（branch）= 656（本行口径）；"
                "`spine.json` 的 `excluded` 虽为 32 条，但那是**场景级**排除、其 32 个 `scene_id` **逐条 grep 均不在 "
                "`DATA.nodes` 里**，无法在节点级扣除（「712−53−32＝627」属算术巧合，未确证）。"
                "⇒ **以实测为准**，627 / 1,881 的来路上报主代理裁决；本轮估算按实测主干 %d ⇒ %d 元素（含番外 %d）。"
                % (trunk, trunk - 627, trunk, est_trunk, est_all)),
        },
        "known_gaps": [
            "**G-1 独立层节点的运行态未定义**（主代理 2026-09-28 裁决 4）：冻结 §二 只定义 `fc.frag<G>.*`"
            " 的 image/text/hit 三件套，未提 `flow_state` ⇒ 本轮**独立层不写 `flow_state`、不产 `_dim`/`_new`**；"
            "主干节点的五态叠加机制（冻结 §一.1）已就绪，独立层要接只需同规则补。",
            "**G-2 `state_assets` 无逐态几何**：`state_assets` 只换位图、不改元素矩形 ⇒ 素材组为缩放键设计的"
            "「按下态 41×41 放大」（`x_ui_zoom{out,in}_on`）在本机制下**只能被缩到元素 29×29**，"
            "「按下变大」的观感无法呈现。要真放大需两端按 `state` 改矩形（机制扩展）或复制成对元素（数据 +2 件/键）。",
            "**G-3 独立层视口只容 12 格**（主代理 2026-09-28 裁决 5）：网格 3 列 × 4 行；组内超出者本轮不产"
            "（`--frag-report` 打全 6 组清单：现仅第 6 组 `番外·附赠（成人向）` 20 章溢出，**未产 8 格**）。"
            "纵滚 / 横移 / 迷你地图 / 缩放交编程组（冻结 §五）。",
            "**G-4 主干节点 / 连线的运行态数据只有「声明」**：`flow_state` 与连线 `state` 的**运行期取值**"
            "（哪些已读、哪些已走、哪些不可前往）由编程组持有并写 `fc.state.<NNNN>` flag；本轮只交付"
            "「字段 + 叠加件 + 解析后的 color/w/arrow」这套数据面。",
        ],
        "field_notes": {
            "id": "DATA.nodes 的键＝脚本名（如 `s01_01a`、`22_1a`）",
            "group": "所属**段**标题（DATA.sections[].title）",
            "lane": "所属**道**键 `\"<段下标>:<道下标>\"`（与 lanes[].key 对应）",
            "kind": "`section` / `select` / `frag`（番外，53 条）/ `branch`（只出 65×65 底座）",
            "x,y,w,h": "**实际渲染几何**（branch 为底座 65×65 居中于 296 宽槽位后的矩形；其余 296×65）",
            "flow_state": "运行态字段的**声明默认值**（冻结 §一.1 缺省＝`available`）；真实运行态由编程组持有",
            "主干 / 番外": "主干 = `kind != \"frag\"`；番外 = `kind == \"frag\"`（%d 条）" % by_kind["frag"],
        },
        "step_y": step_y, "vert_x": vert_x,
        "step_y_note": "主轴行距＝入参（默认 %d ＝契约 §8.2 参照作口径）；每 lane 的 `step_y` 逐条登记在 `lanes[]`"
                       % step_y,
        "lane_x_range": [min(l["x"] for l in lanes_out), max(l["x"] for l in lanes_out)],
        "lane_x_note": ("道与道按 `vert_x` 排开并**按段居中于图表视口水平中心**（与 `build()` 同口径）："
                        "19 道 × %d 档距必然大量落在画布外 —— **横向平移/纵滚属编程组**（冻结 §五）；"
                        "`lanes[].x` 是道带槽位左上 x（可为负），节点 `x` 即由它派生"
                        "（branch 另加 +%d 居中偏移）" % (vert_x, BRANCH_OFFSET_X)),
    }
    doc = {
        "meta": meta,
        "viewport": {"x": vpx, "y": vpy, "w": vpw, "h": vph, "element": "fc.scroll"},
        "canvas": {"w": canvas["width"], "h": canvas["height"]},
        "x0": x0,
        "bbox": bbox([(n["x"], n["y"], n["w"], n["h"]) for n in out_nodes]),
        "counts": {
            "lane_entries": sum(l["nodes_total"] for l in lanes_out),
            "nodes": len(out_nodes),
            "by_kind": by_kind,
            "duplicate_lane_entries_dropped": dup_entries,
            "lanes": len(lanes_out),
            "sections": len(sections),
        },
        "lanes": lanes_out,
        "nodes": out_nodes,
    }
    blob = (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    print("=" * 78)
    print("gen_flow_layout.py · --preset full（冻结 §五：**只交数据、不产 elements**）")
    print("  段 %d ｜ 道 %d ｜ lane 条目 %d ｜ 节点 %d（section %d / select %d / frag %d / branch %d）｜ 跨道共享去重 %d"
          % (len(sections), len(lanes_out), doc["counts"]["lane_entries"], len(out_nodes),
             by_kind["section"], by_kind["select"], by_kind["frag"], by_kind["branch"], dup_entries))
    print("  行距 step_y %d ｜ 横向档距 vert_x %d ｜ 视口 %s ｜ 全局内容 bbox %s"
          % (step_y, vert_x, (vpx, vpy, vpw, vph), doc["bbox"]))
    print("  元素化估算：主干 %d（＝%d×3 ＋ branch %d×1）｜ 含番外合计 %d（冻结原文 627 节点 / 1,881 元素：实测主干 %d，差 %d）"
          % (est_trunk, trunk, by_kind["branch"], est_all, trunk, trunk - 627))
    if dry_run:
        print("  [dry-run] 未落盘（--dry-run）")
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as f:
        f.write(blob)
    print("  → %s（%d 字节，md5=%s；**无 `elements` 键**：%s）"
          % (os.path.abspath(out), len(blob), hashlib.md5(blob).hexdigest(),
             "elements" not in doc))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="剧情流程图屏生成器（ISSUE-20260927-05）",
        epilog=PRESET_TABLE,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", default=DEFAULT_PRESET, choices=tuple(PRESETS.keys()),
                    help="具名预设（默认 %s = 交付样例·屏1；见下方预设表）" % DEFAULT_PRESET)
    ap.add_argument("--section", type=int, default=None, help="DATA.sections 下标（默认取预设）")
    ap.add_argument("--lanes", default=None, help="道下标，逗号分隔；传 all 表示全道（默认取预设）")
    ap.add_argument("--from", dest="frm", default=None, help="每道起始条目下标，单值或逗号分隔（默认取预设）")
    ap.add_argument("--limit", type=int, default=None, help="每道最多取多少条目（默认取预设）")
    ap.add_argument("--step-y", type=int, default=None,
                    help="主轴行距 px。**默认 95 = 预设 screen1 = 交付样例**；"
                         "参照作口径 150 走 `--preset ref150` 或显式 `--step-y 150`"
                         "（**会产出变体、把屏换掉**，见预设表）")
    ap.add_argument("--vert-x", type=int, default=None, help="横向道档距 px（默认 375 = 契约 §8.2 参照作口径）")
    ap.add_argument("--x0", type=float, default=None, help="道带中心 x（默认 = 视口中心；给入口列时按剩余宽度居中）")
    ap.add_argument("--y0", type=int, default=None, help="首行 y（默认 = fc.scroll 视口顶 190）")
    ap.add_argument("--entry-side", default=None, choices=("left", "right"), help="入口列摆哪一侧（默认 left）")
    ap.add_argument("--no-entries", action="store_true", help="不产番外入口标记 / 组名标签")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出路径（默认 layout/screens/32_flowchart.json）")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计与节点 id 集，不落盘")
    ap.add_argument("--no-cull", action="store_true",
                    help="不做视口裁剪（**只用于全量规模核算**；产出不可当交付屏，须与 --dry-run 同用）")
    ap.add_argument("--text-fit-report", action="store_true", help="只做文字容量实测并退出")
    ap.add_argument("--refresh-golden", action="store_true",
                    help="用实跑结果重钉**五组**金标（改过 note 或参数后由主代理执行）")
    ap.add_argument("--selfcheck-delivered", action="store_true",
                    help="反向自证：把默认预设的 step_y 改成 150 ⇒ 交付自检必须拦下且盘上 md5 不变")
    ap.add_argument("--title-check-report", action="store_true",
                    help="★ 第 9 批：只打印「首行墨迹左缘 ≥ x_node+30（已读对勾不变量）」实测与违规清单，不落盘")
    ap.add_argument("--selfcheck-title-break", action="store_true",
                    help="★ 第 9 批：该不变量的**变异自证**（删一条硬断行必越线 / 清空表须 ≥ 表内条数）")
    ap.add_argument("--frag-groups", default=None,
                    help="番外独立层组号**列表**（逗号分隔，每个 1..6；★ 第 3 批：由单值扩为列表。"
                         "仅对非 full 预设生效，默认取预设 = screen1 为 1,2,3,4,5,6；frag 为 1）")
    ap.add_argument("--frag-group", type=int, default=None,
                    help="（旧名，等价 `--frag-groups <G>`；保留兼容）")
    ap.add_argument("--frag-limit", type=int, default=None,
                    help="**每组**独立层最多产多少格（默认＝视口可容行数 × 每行 3 = 12）")
    ap.add_argument("--frag-report", action="store_true",
                    help="只打印 6 个番外组的独立层容量与**未产格清单**（主代理裁决 5），不落盘")
    ap.add_argument("--full-out", default=FULL_OUT,
                    help="--preset full 的输出路径（默认 _工作\\ISSUE-20260928-02_第2步\\全量布局.json）")
    args = ap.parse_args()

    if args.selfcheck_delivered:
        return selfcheck_delivered()

    if args.selfcheck_title_break:
        return selfcheck_title_break()

    if args.title_check_report:
        return title_check_report(load_data()["nodes"])

    if args.frag_report:
        return frag_capacity_report()

    if args.text_fit_report:
        return text_fit_report(None, load_data()["nodes"])

    if args.preset == "full":
        return emit_full_layout(args.step_y if args.step_y is not None else FULL_STEP_Y,
                                args.vert_x if args.vert_x is not None else 375,
                                args.full_out, args.dry_run)

    if args.refresh_golden:
        rows = []
        for name in GOLDEN_ORDER:
            scr, _st = preset_run(name)
            blob = serialize_screen(scr)
            rows.append((name, hashlib.md5(blob).hexdigest(), content_sha256(scr)))
        refresh_golden(rows)
        return 0

    # ── 预设 → 显式参数覆盖 ──
    p = PRESETS[args.preset]
    section = p["section"] if args.section is None else args.section
    lanes_s = p["lanes"] if args.lanes is None else args.lanes
    frm = p["frm"] if args.frm is None else args.frm
    limit = p["limit"] if args.limit is None else args.limit
    step_y = p["step_y"] if args.step_y is None else args.step_y
    vert_x = p["vert_x"] if args.vert_x is None else args.vert_x
    entry_side = p["entry_side"] if args.entry_side is None else args.entry_side
    with_entries = p["entries"] and not args.no_entries
    node_states = p.get("node_states")
    link_states = p.get("link_states")
    # ★ 第 3 批：`frag_groups` 为**列表**；旧单值开关 `--frag-group G` 等价 `--frag-groups G`
    frag_groups = p.get("frag_groups")
    if args.frag_groups is not None:
        frag_groups = [int(x) for x in str(args.frag_groups).split(",") if x.strip() != ""]
    elif args.frag_group is not None:
        frag_groups = [args.frag_group]

    data = load_data()
    sel = None if str(lanes_s).strip().lower() == "all" else [int(x) for x in str(lanes_s).split(",") if x.strip() != ""]
    n_lanes = len(data["sections"][section]["lanes"]) if sel is None else len(sel)
    froms = parse_list(frm, n_lanes, "from")

    static = load_static_elements()
    vp = next(e for e in static if e["id"] == "fc.scroll")
    x0 = args.x0 if args.x0 is not None else vp["x"] + vp["w"] / 2.0
    y0 = args.y0 if args.y0 is not None else vp["y"]

    screen, st = run_once(section, sel, frm, limit, step_y, vert_x, args.x0,
                          args.y0, args.no_entries, entry_side, args.preset,
                          node_states=node_states, link_states=link_states,
                          frag_groups=frag_groups, frag_limit=args.frag_limit)

    print("=" * 78)
    print("gen_flow_layout.py · 流程图屏生成（ISSUE-20260927-05）")
    print("  预设 = %s（%s）" % (args.preset, p["note"]))
    print("  段[%d] %s ｜ 道 %s ｜ from %s ｜ limit %d ｜ step_y %d ｜ vert_x %d ｜ x0 %.1f ｜ y0 %d"
          % (st["section"], st["section_title"], st["lanes"], froms, limit,
             st["step_y"], st["vert_x"], st["x0_eff"], st["y0_eff"]))
    print("  入口列 = %s 侧（整列摆进视口；道带在剩余宽度里居中）" % st["entry_side"])
    print("  节点落盘 %d（%s）｜ 图内容层元素 %d（静态透传 %d）｜ cn 为空回落 script 名 %d"
          % (st["nodes_placed"],
             " / ".join("%s %d" % (k, st["kinds"][k]) for k in ("section", "select", "frag", "branch")),
             st["gen_elements"], st["static_elements"], st["empty_cn_fallback"]))
    print("  连线 %d 条（直线 %d / VZ %d / VL %d）｜ 未落盘目标丢弃 %d ｜ 越出画布丢弃 %d"
          % (st["links"], st["forms"]["line"], st["forms"]["vz"], st["forms"]["vl"],
             st["drop_not_placed"], st["drop_outside_canvas"]))
    print("  退化丢弃 %d" % st["drop_degenerate"])
    b = st["bbox_nodes"]
    print("  节点包围盒 %s（宽 %d 高 %d）" % (b, b[2] - b[0] if b else 0, b[3] - b[1] if b else 0))
    bl = st["bbox_links"]
    if bl:
        print("  连线包围盒 %s（宽 %d 高 %d）" % (bl, bl[2] - bl[0], bl[3] - bl[1]))
    print("  番外入口标记 %d 个，y = %s" % (len(st["entries"]), [e[2] for e in st["entries"]]))
    if with_entries:
        _kr = group_kana_residue(load_spine())
        print("  组名中文化：映射 %d/%d 组%s"
              % (len(GROUP_CN_MAP), len(st["entries"]),
                 "；★ 残留日文假名 %d 组：%s" % (len(_kr), [c for _g, c in _kr]) if _kr
                 else "；★ 组名标签已无日文假名 ✓"))
    print("  视口 %s 内**完整落入**的真实节点：%d 个" % (st["viewport"], st["nodes_in_viewport"]))
    print("  ★ 产出元素视口内自证：%s（x+w 最大 %d ≤ %d ｜ y+h 最大 %d ≤ %d）%s"
          % ("全部落在视口内 ✓" if st["viewport_ok"] else "**越界 %d 件**：%s"
             % (len(st["elements_outside_viewport"]), st["elements_outside_viewport"][:6]),
             st["gen_max_right"], vp["x"] + vp["w"], st["gen_max_bottom"], vp["y"] + vp["h"],
             "" if st["viewport_ok"] else " ⇒ **拒绝落盘**（§九 裁决 5）"))
    print("  屏级 flags_default：%s%s"
          % (st["flags_default"],
             "（含逐节点运行态 flag，仅演示预设）" if st["node_states"] else ""))
    print("  ★ 连线 state 分布（冻结 §一.2：色/宽/箭头由生成器解析后写进 JSON）：%s"
          % " ｜ ".join("%s %d 条（%s w%d arrow=%s）"
                       % (k, v, EDGE_STATES[k][0], EDGE_STATES[k][1], EDGE_STATES[k][2])
                       for k, v in st["edge_states"].items()))
    if st["node_states"]:
        _cnt = {}
        for i in range(st["nodes_placed"]):
            s_ = st["node_states"][i % len(st["node_states"])]
            _cnt[s_] = _cnt.get(s_, 0) + 1
        print("  ★ 节点 flow_state 演示（循环 %s）：%s ｜ 叠加件 `_dim` %d 件（image，按种类取件）、`_new` %d 件、"
              "`_read` %d 件（已读绿对勾）；`current`/`available` **不产元素**"
              "（`current` 由两端程序化画环、**只留金环、不加对勾**）"
              % (st["node_states"], _cnt,
                 sum(1 for e in screen["elements"] if e["id"].endswith("_dim")),
                 sum(1 for e in screen["elements"] if e["id"].endswith("_new")),
                 sum(1 for e in screen["elements"] if e["id"].endswith("_read"))))
    if st["frags"]:
        f0 = st["frags"][0]
        print("  ★ 番外独立层（冻结 §二）：**%d 组**（层旗标取值集 %s）｜ 网格 %d 列 × 步进 %d/%d、"
              "行首偏移 %d、原点 %s、可容 %d 行"
              % (len(st["frags"]), st["layer_vis_when"], f0["grid"]["cols"], f0["grid"]["step_x"],
                 f0["grid"]["step_y"], f0["grid"]["lead_y"], f0["grid"]["origin"], f0["grid"]["rows_fit"]))
        for f in st["frags"]:
            print("     组 %d「%s」产出 %d/%d 格（%s）；**不产连线**；按组返回键 %s；未产格 %s"
                  % (f["group"], f["group_cn"], f["produced"], f["rows_total"],
                     "全部落在 %d 行网格内" % f["grid"]["rows_fit"], f["back_key"],
                     f["dropped"] if f["dropped"] else "无"))
    else:
        print("  ★ 番外独立层：**本预设不产**（层旗标取值集 %s ⇒ 只有主干层）" % st["layer_vis_when"])
    # ★ 裁决 4（第 4 批）可判读说明：哪个档、哪几组**因独立层未产出而不产入口热区**
    _skip_g = st.get("entry_hit_skipped") or []
    _hit_layers = st.get("entry_hits") or []
    if _skip_g:
        print("  ★ 裁决 4（入口热区只在「该组独立层确实产出」时才产）：本档＝预设 **%s** ⇒ "
              "**%d/%d 组**未产独立层，对应入口 image/组名标签**保留为纯占位、不产 `fc.entry.*_hit`**：组 %s"
              "（否则点一下切到未产层 ⇒ 屏面变空且回不来）。已产热区 %d 个 → %s"
              % (args.preset, len(_skip_g), len(st["entries"]), _skip_g,
                 len(_hit_layers), _hit_layers or "无"))
    else:
        print("  ★ 裁决 4（入口热区只在「该组独立层确实产出」时才产）：本档＝预设 **%s** ⇒ "
              "全部 %d 组入口**均已产独立层** ⇒ 入口热区 **%d/%d 组**齐备（无占位缺口）：%s"
              % (args.preset, len(st["entries"]), len(_hit_layers), len(st["entries"]), _hit_layers))
    # ★ 第 3 批机检自证（落盘前打印）：外壳件**无**层旗标 / 图内容层**有**层旗标（计数 + 清单）
    _shell = [e["id"] for e in screen["elements"] if not e["id"].startswith(LAYER_OWNED_PREFIXES)]
    _shell_flag = [e["id"] for e in screen["elements"]
                   if not e["id"].startswith(LAYER_OWNED_PREFIXES) and "vis_flag" in e]
    print("  ★ 层旗标归属自证（第 3 批）：外壳件 %d 件，其中带 vis_flag 的 **%d 件**%s；"
          "图内容层件 %d 件全部带 vis_flag ✓"
          % (len(_shell), len(_shell_flag), "（✓ 外壳不参与层旗标）" if not _shell_flag else " ← **违规**",
             len(screen["elements"]) - len(_shell)))
    if args.dry_run:
        per = {}
        for nid, info in st["placed_raw"].items():
            d = per.setdefault(info["lane"], [10 ** 9, -1, 0])
            d[0] = min(d[0], info["y"])
            d[1] = max(d[1], info["y"])
            d[2] += 1
        print("PER_LANE: " + ";".join("lane%d n=%d y=%d..%d h=%d" % (k, v[2], v[0], v[1], v[1] - v[0] + NODE_H)
                                      for k, v in sorted(per.items())))
        print("NODE_IDS: %s" % ",".join(st["node_ids"]))
        print("LINK_FORMS: line=%d,vz=%d,vl=%d" % (st["forms"]["line"], st["forms"]["vz"], st["forms"]["vl"]))
        print("[dry-run] 未落盘（--dry-run）")
        return 0

    if not st["viewport_ok"]:
        print("[FAIL] 产出元素越出图表视口（§九 裁决 5）；调 --vert-x / --lanes / --entry-side 后重试")
        return 1

    # ── ★ 落盘前「文字四判据」自检（修正轮 ②：对准**可见实体面**，不达标即拒绝落盘）──
    tc = check_text_criteria(load_data()["nodes"])
    print("  ★ 文字四判据（f=%d / 行距 %s / 盒宽 %d / plate rows %d..%d）："
          "上留最小 %dpx ｜ 下留最小 %dpx ｜ 最宽行 %.1fpx（%s）｜ 截断 %d"
          % (tc["size"], tc["spacing"], tc["box_w"], tc["plate"][0], tc["plate"][1],
             tc["min_top"], tc["min_bottom"], tc["max_ink"], tc["widest"][0], tc["trunc"]))
    if tc["fails"]:
        print("    ✗ " + "；".join(tc["fails"]))
        print("    ⇒ **拒绝落盘**：文字四判据必须全绿（V2 缩字号裁决）；先修参数再落盘。")
        return 1
    print("    ✓ 四判据全绿（A/B ≥%dpx、C ≤263px、D 零截断）" % PLATE_MARGIN_MIN)

    # ── ★ 第 9 批落盘前自检：**「已读对勾」不变量**（首行墨迹左缘 ≥ x_node+30）──
    assert_break_table_keys()          # ★ 幻影 id 守卫（落盘前，用全量语料）
    viol, (tl_min, tl_min_id, tl_n, tl_two, tl_max) = check_title_first_line(load_data()["nodes"])
    print("  ★ 第 9 批·「已读对勾」不变量（首行墨迹左缘 ≥ x_node+%d，即首行墨迹 ≤ %dpx）："
          "复算 %d 条 ｜ 最紧 %+.2f（%s）｜ 两行条数 %d ｜ 全量最宽行 %.1fpx（目标两行 ≤ %dpx）"
          % (TITLE_CHECK_GAP, TEXT_W - 2 * (TITLE_CHECK_GAP - (NODE_W - TEXT_W) // 2),
             tl_n, tl_min, tl_min_id, tl_two, tl_max, TITLE_BREAK_MAX_LINE))
    if viol:
        print("    ✗ 违规 %d 条（对勾 20×20 @(x+10,y+12) ⇒ 右缘 +30，会压住首字左边）：" % len(viol))
        for nid, t, w0, left, ln in viol:
            print("        %-10s 首行 %.1fpx 左缘 %+.2f（%d 行）｜「%s」" % (nid, w0, left, ln, t))
        print("    ⇒ **拒绝落盘**：给这些标题在 `TITLE_HARD_BREAK` 里补自然断点（断在禁则字符前的括号/波浪，"
              "否则取中点附近且第二行不以禁则字符开头），使两行墨迹 ≤ %dpx。" % TITLE_BREAK_MAX_LINE)
        return 1
    print("    ✓ 不变量全绿（%d 条全部 ≥ +%d；断行表 %d 条）"
          % (tl_n, TITLE_CHECK_GAP, len(TITLE_HARD_BREAK)))

    # ── ★ 落盘前「交付样例」自检（收尾轮 ⑪.4）──
    blob = serialize_screen(screen)
    md5v = hashlib.md5(blob).hexdigest()
    shav = content_sha256(screen)
    writing_default_out = (os.path.abspath(args.out) == os.path.abspath(DEFAULT_OUT))
    g_md5, g_sha = GOLDEN.get(args.preset, ("?", "?"))
    if writing_default_out:
        if md5v != g_md5:
            print("  ✗ 落盘前自检：预设 %s 产出 md5=%s ≠ 金标 %s" % (args.preset, md5v, g_md5))
            print("    内容摘要 content-sha256=%s（金标 %s）%s"
                  % (shav, g_sha, "——**仅 note 措辞变化**（内容未动）" if shav == g_sha else "，内容也变了"))
            print("    ⇒ **拒绝落盘**：默认/具名预设产出必须等于交付样例；"
                  "若这是有意的改动，请先核对再跑 `--refresh-golden` 重钉金标。")
            return 1
        print("  ✓ 落盘前自检：预设 %s 产出 md5=%s == 金标；content-sha256=%s"
              % (args.preset, md5v, shav[:16] + "…"))
    else:
        print("  （--out 非默认屏文件 ⇒ 不做交付金标自检；md5=%s）" % md5v)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(blob)
    print("  → %s（%d 元素 / %d 边，md5=%s）"
          % (os.path.abspath(args.out), len(screen["elements"]), len(screen["links"]), md5v))
    if writing_default_out and args.preset != DEFAULT_PRESET:
        print("  ⚠ 当前屏文件已被预设 %s 覆盖（**非交付样例**）；跑一次无参 `python 工具/gen_flow_layout.py` 回到交付样例。"
              % args.preset)
    return 0


def parse_lanes(spec, data, section):
    if str(spec).strip().lower() == "all":
        return None
    return [int(x) for x in str(spec).split(",") if x.strip() != ""]


if __name__ == "__main__":
    sys.exit(main())

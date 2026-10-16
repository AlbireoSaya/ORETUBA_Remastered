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
    fc.node.<NNNN>（+`_tx`/`_hit`）｜ fc.branch.<NNNN> ｜ fc.entry.<NNNN>（+`_hit`，**第 12 批改形制**）
    ｜ fc.label.<NNNN>_tx（**第 12 批起只剩文字件**：底板 `fc.label.<NNNN>` 已删）
    顶层 `links[]`（生成器算好 `pts` 正交折线；两端只负责描线 + 画箭头）

■ 契约 §一 列出的既有静态元素**原样透传**（id 与几何一字不改）
    它们以「逐字提取自改造前 32_flowchart.json 的 JSON 快照」形式内嵌在本文件（`STATIC_ELEMENTS_JSON`），
    这是本工程生成器的一贯写法（同 `工具\m34_build_screens.py` 把元素写在代码里）——
    若从磁盘现值读，第二次运行会把**自己产出的图内容层**当成静态元素，不可幂等。
    ★ **例外（逐批登记的快照改动）**：快照本身会被后续批次**有意图**地改动，改动**逐条记在各元素的
      `note` 与下方「批次日志」里**（本批＝`ISSUE-20260929-04` 第 12 批：新增 `fc.bg`、
      删 `fc.sysbar`、改 `fc.zoom_knob`/`fc.p_title`/`fc.p_title_tx`）。

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
       `fc.entry.*`/`fc.frag*`），**外壳件（视口/滚条/**模式入口 `fc.mode_*`**/标题牌/关闭/进入本章/右栏四段）不写
       `vis_flag`/`vis_when`** —— 外壳是两种层共用的舞台（随层隐藏会让组名与网格画在无底图的透明/黑画面上）。
       （★ 第 13 批：旧文里的「页签 / 付箋」两族**已全部删除**（`fc.mtab*` 12 件 / `fc.fusen_*` 6 件），
       位置由**两枚模式入口** `fc.mode_*` 6 件接手；素材文件一律保留不删。）
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

# ══════════════════════════════════════════════════════════════════════
# ★★ 第 12 批（`ISSUE-20260929-04` · 用户 2026-09-29 追加裁决）★★
#   ① **组名标签底板 `fc.label.<NNNN>`（image）已删** —— 用户裁定「`fc.label.000x` 与 `fc.entry.000x`
#      一律删去，统一为**和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状、只是底色换成淡黄**；
#      文字方案不动」。⇒ `build()` **不再产 `fc.label.<NNNN>` image**，
#      只保留文字件 `fc.label.<NNNN>_tx`（文案/字号/对齐/颜色一律不动，仅矩形改为与新入口块**同矩形**）。
#   ② **入口块 `fc.entry.<NNNN>` 改形制**：86×48 付箋占位件 → **296×65 淡黄节点形块**
#      （新素材 `ui/x_ui_entry_frag_{off,on}.png`，**由 `ui/x_ui_node_select_{off,on}.png` 派生**：
#       alpha 逐字节同源、仅换色相；`nine` 与 `fc.node.*` select 族**完全一致**）。
#   ③ 旧件一律保留不删：`ui/x_ui_label_off.png`（标签底板，本批已无引用）、
#      `ui/x_ui_fusen_off.png`（占位件退役为 `fc.entry.*` 的历史）。
#      ★ 第 13 批订正：旧文「**仍被 `fc.fusen_edit`/`fc.fusen_reset` 使用**」**已作废** ——
#        该批删了 `fc.fusen_edit`/`fc.fusen_reset` 两键 ⇒ `x_ui_fusen_{off,over,on}.png`（及 `x_ui_ftab_*`）
#        自本批起**零功能引用**（仅素材库保留，不删）。
# ══════════════════════════════════════════════════════════════════════
LABEL_ASSET = "ui/x_ui_label_off.png"     # ★ 已退役（组名标签底板元素本批已删；素材文件保留不删）
LABEL_W, LABEL_H = 333, 38                # ★ 已退役（旧底板几何）；`LABEL_W` 仍被 `ENTRY_COL_W` 引用
LABEL_NINE = {"l": 0, "t": 0, "r": 0, "b": 0}   # ★ 已退役（旧底板的零九宫格整图缩放口径）
LABEL_TEXT_SIZE = 16                      # 组名文字字号（**保留使用**；`fc.label.<NNNN>_tx` 的 font.size）

# ── 番外入口块（第 12 批改形制：节点形 296×65）────────────────────────────
ENTRY_W, ENTRY_H = 296, 65                # ★ 第 12 批：296×65（＝与 `fc.node.*` 同形制；原 86×48 付箋已退役）
#   ★ nine **与 `fc.node.*`（select 族）完全一致**（源素材 263×65 ≠ 296 ⇒ 横向九宫格拉伸）
ENTRY_NINE = {"l": 14, "t": 0, "r": 13, "b": 0}
ENTRY_ASSET = "ui/x_ui_entry_frag_off.png"      # normal：淡黄节点形块（离线/常态）
ENTRY_ASSET_ON = "ui/x_ui_entry_frag_on.png"    # hover：亮态（淡黄 → 提亮）
ENTRY_ASSET_SOURCE = (
    "素材组产出（ISSUE-20260929-04 · 冻结 §A）：`ui/x_ui_entry_frag_{off,on}.png` **263×65 RGBA** —— "
    "由章节素材 `ui/x_ui_node_select_{off,on}.png` **派生**（alpha 逐字节同源、仅换色相为淡黄 ≈ `#FFFF99` 族）；"
    "旧占位件 `ui/x_ui_fusen_off.png`（86×48 付箋）**退役为该件的历史、文件保留不删**。"
)

# ══════════════════════════════════════════════════════════════════════
# ★ ISSUE-20260929-05 第 13 批（2026-09-29 · 模式入口收敛 + 删备注/对话框提示）
#   · 用户 2026-09-29 指令（流程图页第 ② 条）：删 4 个模式页签 `fc.mtabx`（序章/本篇/After Story/Fragment）
#     ＋其 text；在原页签位置用**两枚文字入口**取代 —— **「本篇集合」**（序章/本篇/After Story 并入）与
#     **「番外故事」**（原 Fragment）；要求 ①排版整齐、间距相等 ②高度 60px 左右 ③白字＋黑描边＋白淡光、
#     微软雅黑 Regular ④常规/悬停/点击三态、三态一眼可辨。
#   · 用户裁决（AskUserQuestion 2026-09-29）：动作**拟用名** `flow_mode_main` / `flow_mode_frag`
#     （**命中即派发**，切集/筛选行为留编程组，与 `flow_replay_toggle` 同口径）；
#     **按下态＝半透明冰蓝实底胶囊（≈ `@palette.accent`）＋1px 亮边**，且整体**下沉 1px**。
#   · 几何（接口冻结 §B，逐字）：两枚同矩形 **180×60**、y=25（60 高居中于旧页签带中线 55 ⇒ 占 25..85，
#     与下方标题牌 y93 留 8px）；x=**34** / **254**（等宽 180、间距 40 ⇒ 满足「间距相等」）。
#     `_glow`（底光图 z10）/ `_hit`（热区 z95）**同矩形**。
#     ★ **E5 订正（用户 2026-09-29 裁决「两个模式入口的文字下移 8px」）**：文字件 `_tx`（z20）的 `y`
#       **25 → 33**（`x/w/h` 不变）⇒ 三件**不再逐字段同矩形**：`_glow`/`_hit` 仍 y25，`_tx` 为
#       **y = MODE_ENTRY_Y + MODE_ENTRY_TX_DY**。依据＝vision 实测墨迹恒为 y31..63（中心 47）、
#       而元素框中心 55 ⇒ 偏高 8px（按下态冰蓝胶囊上沿 y≈36 会横穿字头 5px）。下移后墨迹
#       y≈39..71、中心 55 与框同心。先例＝`ISSUE-20260928-03` 列表标签/`item_buttons` 各 `y+6`。
#   · 三态口径：三态**全靠 `_glow` 底光图承载**（同一枚柔和白淡光的弱/强/实底三档）；
#     `_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**。
#     ⚠ 用户原话「文字下移 1px」**无法实现**（不支持文字逐态位移、`state_group` 只配对图片层）
#       ⇒ 以「**底沉 1px**」等价表达；如需文字本体位移须加「逐态位移」新接口（新裁决）。已写进交接文档。
#     ★ 注意区分：**E5 的「文字下移 8px」是静止态的版面订正**（改 `_tx.y` 这一个数据字段），
#       与上面这条「逐态位移无法实现」是**两件事** —— 后者说的是「按下时文字相对底图再沉 1px」不可做。
#   · 它们**不是图内容层**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ 外壳件、**不写 `vis_flag`/`vis_when`**
#     （主干层与 6 个番外独立层的共用舞台）。
# ══════════════════════════════════════════════════════════════════════
MODE_ENTRY_W, MODE_ENTRY_H = 180, 60
MODE_ENTRY_Y = 25
# ★ E5 订正：文字件 `_tx` 相对 `_glow`/`_hit` 的**纵向偏移**（用户 2026-09-29 裁决「文字下移 8px」）。
#   实测原墨迹 y31..63（中心 47）vs 元素框 y25..85（中心 55）⇒ 偏高 8px；`+8` 后墨迹居中。
MODE_ENTRY_TX_DY = 8
MODE_ENTRY_X = {"mode_main": 34, "mode_frag": 254}
MODE_ENTRY_ORDER = ("mode_main", "mode_frag")
MODE_ENTRY_ACTIONS = {"mode_main": "flow_mode_main", "mode_frag": "flow_mode_frag"}
MODE_ENTRY_SAMPLES = {"mode_main": "本篇集合", "mode_frag": "番外故事"}
MODE_ENTRY_SUFFIXES = ("glow", "tx", "hit")
MODE_ENTRY_IDS = tuple("fc.%s_%s" % (g, s)
                       for g in MODE_ENTRY_ORDER for s in MODE_ENTRY_SUFFIXES)
# 素材（★ E1 实际产出 3 件，两入口共用同一套 —— 冻结 §D 允许按形状一致性复用、优先省件数）
MODE_ASSET_TRI = {
    "normal": "ui/x_ui_modetab_off.png",
    "hover": "ui/x_ui_modetab_over.png",
    "pressed": "ui/x_ui_modetab_press.png",
}
#   ★ 本批**已删**的两族（勿再按旧描述理解；素材文件一律保留不删）：
#     `fc.mtab1..4`（＋`_tx`/`_hit`，共 12 件）—— 4 个模式页签；`fc.fusen_edit`/`fc.fusen_reset`
#     （＋`_tx`/`_hit`，共 6 件）—— 备注功能键。⇒ 素材 `x_ui_ftab_{on,off,over}.png` 与
#     `x_ui_fusen_{off,over,on}.png` **自本批起零功能引用**（仅素材库保留）。


def _rect_overlap(a, b):
    """两矩形相交（半开区间口径与 `uiWidgetRect` 一致：贴边不算重叠）。"""
    return (a[0] < b[0] + b[2] and b[0] < a[0] + a[2]
            and a[1] < b[1] + b[3] and b[1] < a[1] + a[3])


def mode_entry_rects(elements):
    """两枚模式入口的三件矩形（逐组；缺件记 None）。纯函数，供自检与变异自证共用。"""
    out = {}
    for g in MODE_ENTRY_ORDER:
        rs = []
        for s in MODE_ENTRY_SUFFIXES:
            e = next((x for x in elements if x["id"] == "fc.%s_%s" % (g, s)), None)
            rs.append(None if e is None else (e["x"], e["y"], e["w"], e["h"]))
        out[g] = rs
    return out


def mode_entry_violations(elements, cw, ch):
    r"""★ 第 13 批**落盘前自检**（纯函数 ⇒ 可做变异自证）：两枚模式入口的几何不变量。

    判据（把用户指令②「排版整齐、间距相等、高度 60px 左右」变成可机检的形式）：
      ① `_glow` 与 `_hit` **逐字段同矩形**（底光与热区必须同框）；`_tx` 的 `x/w/h` 与它们相同、
         `y` 必须恰好 `= _glow.y + MODE_ENTRY_TX_DY`（**E5 订正**：文字下移 8px，用户 2026-09-29 裁决
         —— 原墨迹 y31..63/中心 47 vs 框中心 55 ⇒ 偏高 8px；三件**不再逐字段同框**是**有意**的，
         但「同 x/w/h + 固定 y 偏移」仍是硬不变量，防「顺手把文字挪歪」）；
      ② 组间**等宽等高且 y 相同**（「排版整齐」；比较用 `_glow` 矩形 —— 两枚 `_glow` 恒同 y=25），
         间距 ≥ 0（「间距相等」由 `MODE_ENTRY_X` 定值保证，此处卡「不重叠」）；
      ③ 每件**完整落在画布内**；
      ④ **两枚入口彼此零重叠**；
      ⑤ 与**任何相邻元素**零重叠 —— 逐件比对同屏全部元素，**排除满幅层**（`w≥画布宽 且 h≥画布高`，
         即 `fc.bg`/`fc.dim` 这类画布底）与本族自身。满幅层是「画布底」不是「邻居」，
         把它算进来会让判据恒真（它必然覆盖全屏）。

    返回违规描述列表（空 = 通过）。
    """
    msgs = []
    rects = mode_entry_rects(elements)
    fam = set(MODE_ENTRY_IDS)
    for g in MODE_ENTRY_ORDER:
        rs = rects[g]
        miss = [MODE_ENTRY_SUFFIXES[i] for i, r in enumerate(rs) if r is None]
        if miss:
            msgs.append("模式入口 %s 缺件：%s" % (g, miss))
            continue
        # ★ E5 订正：三件不再逐字段同矩形 —— `_glow`/`_hit` 同框；`_tx` 同 x/w/h 且 y = glow.y + 8。
        r_glow, r_tx, r_hit = rs
        if r_glow != r_hit:
            msgs.append("模式入口 %s 的 `_glow`/`_hit` **不同矩形**：%s vs %s（底光与热区必须同框）"
                        % (g, r_glow, r_hit))
        want_tx = (r_glow[0], r_glow[1] + MODE_ENTRY_TX_DY, r_glow[2], r_glow[3])
        if r_tx != want_tx:
            msgs.append("模式入口 %s 的 `_tx` 矩形 %s ≠ 期望 %s（＝ `_glow` 同 x/w/h、`y + %d`；"
                        "E5 文字下移口径）" % (g, r_tx, want_tx, MODE_ENTRY_TX_DY))
        for s, r in zip(MODE_ENTRY_SUFFIXES, rs):
            if not (0 <= r[0] and r[0] + r[2] <= cw and 0 <= r[1] and r[1] + r[3] <= ch):
                msgs.append("模式入口 fc.%s_%s 矩形 %s **越出画布** %d×%d" % (g, s, r, cw, ch))
    ok = [g for g in MODE_ENTRY_ORDER if rects[g][0] is not None]
    if len(ok) == 2:
        a, b = rects[ok[0]][0], rects[ok[1]][0]
        if (a[2], a[3]) != (b[2], b[3]):
            msgs.append("两枚模式入口**不等宽等高**（「排版整齐」不成立）：%s vs %s"
                        % ((a[2], a[3]), (b[2], b[3])))
        if a[1] != b[1]:
            msgs.append("两枚模式入口 **y 不同**（不在同一水平带）：%d vs %d" % (a[1], b[1]))
        if _rect_overlap(a, b):
            msgs.append("两枚模式入口**彼此重叠**：%s vs %s（间距应 ≥ 0）" % (a, b))
        for e in elements:
            if e["id"] in fam:
                continue
            r = (e["x"], e["y"], e["w"], e["h"])
            if r[2] >= cw and r[3] >= ch:
                continue        # 满幅层（画布底，不是邻居）
            for g in MODE_ENTRY_ORDER:
                # ★ E5 订正：把 `_tx`（y 已下移 8px、下沿较低）**一并**纳入邻居重叠检查
                #   —— 只查 `_glow` 会漏掉「文字压住下方件」这一类（glow 25..85 vs tx 33..93）。
                for s, r_g in zip(MODE_ENTRY_SUFFIXES, rects[g]):
                    if _rect_overlap(r_g, r):
                        msgs.append("模式入口 fc.%s_%s %s 与相邻件 `%s` %s **重叠**"
                                    % (g, s, r_g, e["id"], r))
    return msgs


def mode_entry_report(elements, cw, ch):
    """可判读的自检打印行（间隙实测；`fc.titleplate` 等邻居统一给出）。"""
    rects = mode_entry_rects(elements)
    a, b = rects["mode_main"][0], rects["mode_frag"][0]
    gap = b[0] - (a[0] + a[2])
    atx = rects["mode_main"][1]
    lines = ["两枚模式入口 %d×%d：`_glow`/`_hit` @y%d（main %s ／ frag %s）｜`_tx` @y%d（main %s，"
             "＝ `_glow.y + %d`；E5 文字下移 8px）⇒ **块间隙 %dpx**（等宽等高、同 y ⇒ 排版整齐）；"
             "间距相等由 `MODE_ENTRY_X` 定值（%d / %d）保证"
             % (a[2], a[3], a[1], a[:2], b[:2], atx[1], atx[:2], MODE_ENTRY_TX_DY, gap,
                MODE_ENTRY_X["mode_main"], MODE_ENTRY_X["mode_frag"])]
    for e in elements:
        if e["id"] in MODE_ENTRY_IDS:
            continue
        r = (e["x"], e["y"], e["w"], e["h"])
        if r[2] >= cw and r[3] >= ch:
            continue
        # 只报「与入口带同高或更近」的邻居间隙，避免刷屏
        if e["id"] not in ("fc.titleplate", "fc.close", "fc.scroll", "fc.smallmap"):
            continue
        # ★ E5：间隙对 `_glow` 与 `_tx` **各报一次**（tx 下沿更低 ⇒ 与下方件的间隙以 tx 为准）
        dy = r[1] - (a[1] + a[3])
        dy_tx = r[1] - (atx[1] + atx[3])
        dx = r[0] - (a[0] + a[2])
        lines.append("  · 邻居 `%s` %s：竖直间隙 %+dpx（`_glow` 口径）／ %+dpx（`_tx` 口径）"
                     "／ 水平间隙 %+dpx ⇒ **零重叠**"
                     % (e["id"], r, dy, dy_tx, dx))
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# ★★ ISSUE-20260930-02 第 15 批：**章节详情**（说明槽截断 ＋ 详情浮层 ＋ 加号按钮）
#   · 接口冻结：`_工作\ISSUE-20260930-02_章节详情\接口冻结.md` §三（元素逐字段）／§四（动作）／
#     §六（验收）。（**注**：冻结书 §一.3/§三.1 记的「398 → 344」是**落盘前的早期稿**；
#      用户 2026-09-30 最终裁定**说明槽宽 = 300**，M4 几何定标亦复核为 300 ⇒ 本批按 **300** 落盘。）
#   · 8 件新元素全在**同一屏**（不新开屏、不复用 `gal_shell`）：右栏 2 件（加号按钮 + 其热区）
#     ＋ 详情浮层 6 件（压暗 / 压暗热区 / 面板底 / 面板热区 / 标题 / 正文）。
#   · 浮层族用**屏级 flag `fc_intro`**（`"closed"` / `"open"`）+ `vis_flag`/`vis_when` 控显隐。
#     它与 `fc_replay` 同性质：**不是层旗标**（不参与 `fc_layer` 切层）⇒ 也是**外壳件**、
#     同样列入具名豁免集 `STATIC_FLAG_EXEMPT`（理由见该常量处）。
# ══════════════════════════════════════════════════════════════════════
INTRO_FLAG = "fc_intro"
INTRO_OPEN = "open"
INTRO_CLOSED = "closed"
INTRO_OVERLAY_IDS = (
    "fc.intro_scrim", "fc.intro_scrim_hit", "fc.intro_bg",
    "fc.intro_panel_hit", "fc.intro_title_tx", "fc.intro_text_tx",
)
INTRO_OVERLAY_Z = (200, 235)          # 浮层**基座 6 件** z 区间（闭区间；冻结 §三.2「浮层组 200–235」）
# ★★ 第 15 批 · 第 2 轮（2026-09-30 · 用户裁定 5「加一枚小 ×」）：**关闭件 2 件**。
#   它们是浮层族的一部分（同挂 `vis_flag:"fc_intro"`），但 z **必须高于面板热区** `fc.intro_panel_hit`
#   （230）—— 否则点关闭会被面板的「空动作＝吞点击」吃掉（冻结 §三.2 明写「z 236/237」）。
#   ⇒ 单独成组（区间 200–235 之外），由 `intro_overlay_violations()` 另加**专条断言**：
#     ① 两件 z 高于 `fc.intro_panel_hit`；② 高于本屏所有非浮层**点击候选**；③ 完整在画布内。
#   ⚠ 「浮层族」= `INTRO_FLOAT_IDS`（8 件）—— 非浮层点击候选集要**排除全族**，否则 236/237
#     会被当成「既有热区」而让基座 6 件的「压过全部热区」判据假失败。
INTRO_CLOSE_IDS = ("fc.intro_close", "fc.intro_close_hit")
INTRO_CLOSE_Z = {"fc.intro_close": 236, "fc.intro_close_hit": 237}
INTRO_FLOAT_IDS = INTRO_OVERLAY_IDS + INTRO_CLOSE_IDS
PLUS_ID = "fc.p_plus"                 # 加号按钮（三态 image）
PLUS_HIT_ID = "fc.p_plus_hit"         # 加号按钮热区（`action:"flow_intro_open"`）
PLUS_PANEL_ID = "fc.p_text"           # 按钮必须**完整落在**该面板内
PLUS_TEXT_ID = "fc.p_text_tx"         # 按钮必须与该文字槽**零重叠**
INTRO_BG_ID = "fc.intro_bg"           # 浮层面板底（九宫格件）
INTRO_TEXT_IDS = ("fc.intro_title_tx", "fc.intro_text_tx")
#   ★ 关闭件：与既有 `fc.close` **同用法**（`asset` + `state_assets{normal,over,pressed}` 三态、
#     `state_group` 与热区配对）。⚠ 元素**必须带 `nine`** —— 素材 `x_ui_close_off.png` 实为 **24×26**
#     （`fc.close` 的 26×26 也是靠 `nine{6,6,6,6}` 撑住），而 `工具/verify_ui.py` 的 [2] 判据是
#     「`kind=image` 且**无** `nine` ⇒ w/h 必须等于 PNG 实尺寸」⇒ 不写 `nine` 会**假失败**。
INTRO_CLOSE_NINE = {"l": 6, "t": 6, "r": 6, "b": 6}   # 与 `fc.close` 逐字相同


def _z_num(e):
    r"""取元素的**引擎口径 z**（与 `krkr/game/ui_widget.tjs::uiWidgetDrawScreen` /
    `uiWidgetNum` 的数值比较一致）：缺省 0；`int`/`float` 原样；**字符串按数值解释**
    （TJS2 的 `<`/`<=` 在 string↔number 之间做数值强制转换 ⇒ `"250"` 与 250 同序）。
    非数值字符串 / 其它类型 ⇒ 0（与「缺省」同档）。

    ★ 第 15 批 · 第 2 轮（一审建议项 · 判据对齐引擎）：旧写法 `max(z for kind=="hit")` 有**两个
    窄口径漏洞**（一审用反例实测）—— ① `z` 写成**字符串** `"250"` 时 `isinstance(z,int)` 为假 ⇒
    被 `continue` 跳过；② 把元素 `kind` 换成 `"list"` 就脱离了 `kind=="hit"` 过滤。而引擎侧的
    命中候选是 `kind ∈ {list, hit}` 且 z **数值**比较 ⇒ 两种写法都能骗过旧断言（浮层实际被压住）。
    本函数 + 调用处的 `kind in ("hit","list")` 把口径对齐引擎。
    """
    v = e.get("z", 0)
    if v is None:
        return 0
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return 0
        return int(f) if f.is_integer() else f
    return 0


def intro_overlay_violations(elements, cw, ch):
    r"""★★ 第 15 批**落盘前自检**（纯函数 ⇒ 可做变异自证）：章节详情浮层的几何不变量。

    判据（把冻结书 §六 三条论文化成可机检形式）：
      ① `fc.p_plus` 与 `fc.p_text_tx` **零重叠**，且按钮**完整落在**面板 `fc.p_text` 内
         （另卡：`fc.p_plus_hit` 与 `fc.p_plus` **同框** —— 热区与按钮必须同矩形）；
      ② **点击可达性（z 序）**：浮层族（`INTRO_FLOAT_IDS`，8 件）的 `z` 必须**高于本屏所有
         **非浮层**的**点击候选**（`kind ∈ {list, hit}` —— **不是只 `hit`**；`z` 按引擎口径
         **数值化**，见 `_z_num()`）⇒ 浮层打开时其余热区**不可达**。其中
         · 基座 6 件（`INTRO_OVERLAY_IDS`）另受**区间**约束 `INTRO_OVERLAY_Z`（200–235）；
         · 关闭件 2 件（`INTRO_CLOSE_IDS`）须**逐件等于** `INTRO_CLOSE_Z`（236/237），
           且 **`fc.intro_close_hit` 的 z 必须 > `fc.intro_panel_hit` 的 z**
           （否则点关闭被面板的「空动作＝吞点击」吃掉 —— 用户裁定 5 的硬前提）；
      ③ 浮层族（8 件）几何**完整落在画布内**，且 `fc.intro_title_tx`/`fc.intro_text_tx`
         **完整落在** `fc.intro_bg` 内。

    返回违规描述列表（空 = 通过）。
    """
    msgs = []
    by = {e["id"]: e for e in elements}

    def rect(eid):
        e = by.get(eid)
        return None if e is None else (e["x"], e["y"], e["w"], e["h"])

    need = list(INTRO_FLOAT_IDS) + [PLUS_ID, PLUS_HIT_ID, PLUS_PANEL_ID, PLUS_TEXT_ID]
    miss = [i for i in need if i not in by]
    if miss:
        return ["章节详情浮层自检缺件：%s" % miss]

    # ── ① 加号按钮：与文字零重叠 + 完整落在面板内 + 热区同框 ──
    rp, rt, rpanel = rect(PLUS_ID), rect(PLUS_TEXT_ID), rect(PLUS_PANEL_ID)
    if _rect_overlap(rp, rt):
        msgs.append("`%s` %s 与 `%s` %s **重叠**（冻结 §三.1 要求文字槽与按钮**零重叠**、留 22px 间隙）"
                    % (PLUS_ID, rp, PLUS_TEXT_ID, rt))
    if not (rp[0] >= rpanel[0] and rp[0] + rp[2] <= rpanel[0] + rpanel[2]
            and rp[1] >= rpanel[1] and rp[1] + rp[3] <= rpanel[1] + rpanel[3]):
        msgs.append("`%s` %s **未完整落在**面板 `%s` %s 内（冻结 §三.1「按钮在说明框内右上角」）"
                    % (PLUS_ID, rp, PLUS_PANEL_ID, rpanel))
    if rect(PLUS_HIT_ID) != rp:
        msgs.append("`%s` 矩形 %s ≠ `%s` %s（热区与按钮必须同框）"
                    % (PLUS_HIT_ID, rect(PLUS_HIT_ID), PLUS_ID, rp))

    # ── ② 浮层族 z：数值化后高于本屏所有非浮层**点击候选**（kind ∈ {list,hit}）──
    #   ★ 判据对齐引擎：候选集 = `kind in ("hit","list")`（`uiScreenClick` 只在这两种 kind 里取最高 z），
    #     z 走 `_z_num()`（字符串按数值解释）。
    other_cand_z = [_z_num(e) for e in elements
                    if e.get("kind") in ("hit", "list") and e["id"] not in INTRO_FLOAT_IDS]
    max_hit_z = max(other_cand_z) if other_cand_z else 0
    for i in INTRO_OVERLAY_IDS:
        z = _z_num(by[i])
        if not (INTRO_OVERLAY_Z[0] <= z <= INTRO_OVERLAY_Z[1]):
            msgs.append("浮层件 `%s` 的 z=%r 不在浮层组区间 %d–%d"
                        % (i, by[i].get("z"), INTRO_OVERLAY_Z[0], INTRO_OVERLAY_Z[1]))
        elif z <= max_hit_z:
            msgs.append("浮层件 `%s` 的 z=%s ≤ 本屏既有热区最高 z=%s ⇒ 浮层打开时其余热区仍可能可达"
                        % (i, z, max_hit_z))
    # 关闭件：区间外，但**逐件钉死 z** + 高于全部非浮层点击候选
    for i in INTRO_CLOSE_IDS:
        z = _z_num(by[i])
        if z != INTRO_CLOSE_Z[i]:
            msgs.append("关闭件 `%s` 的 z=%r ≠ 冻结值 %d（用户裁定 5；z 序硬约束）"
                        % (i, by[i].get("z"), INTRO_CLOSE_Z[i]))
        if z <= max_hit_z:
            msgs.append("关闭件 `%s` 的 z=%s ≤ 本屏既有热区最高 z=%s ⇒ 浮层打开时其余热区仍可能可达"
                        % (i, z, max_hit_z))
    # ★★ 用户裁定 5 的**硬前提**（第 2 轮新增断言）：关闭热区必须压在面板热区之上。
    z_close_hit = _z_num(by["fc.intro_close_hit"])
    z_panel = _z_num(by["fc.intro_panel_hit"])
    if z_close_hit <= z_panel:
        msgs.append("关闭热区 `fc.intro_close_hit` 的 z=%s **未高于**面板热区 `fc.intro_panel_hit` 的 z=%s"
                    " ⇒ 点关闭会被面板的「空动作＝吞点击」吃掉（用户裁定 5 的硬前提）"
                    % (z_close_hit, z_panel))

    # ── ③ 浮层族：完整落在画布内 + 两个 `_tx` 完整落在 `fc.intro_bg` 内 ──
    for i in INTRO_FLOAT_IDS:
        r = rect(i)
        if not (0 <= r[0] and r[0] + r[2] <= cw and 0 <= r[1] and r[1] + r[3] <= ch):
            msgs.append("浮层件 `%s` %s **越出画布** %d×%d" % (i, r, cw, ch))
    rbg = rect(INTRO_BG_ID)
    for i in INTRO_TEXT_IDS:
        r = rect(i)
        if not (r[0] >= rbg[0] and r[0] + r[2] <= rbg[0] + rbg[2]
                and r[1] >= rbg[1] and r[1] + r[3] <= rbg[1] + rbg[3]):
            msgs.append("浮层件 `%s` %s **未完整落在** `%s` %s 内" % (i, r, INTRO_BG_ID, rbg))
    return msgs


def intro_overlay_report(elements, cw, ch):
    """可判读的自检打印行（间隙 / z 序 / 面板包含关系实测）。"""
    by = {e["id"]: e for e in elements}
    rp = (by[PLUS_ID]["x"], by[PLUS_ID]["y"], by[PLUS_ID]["w"], by[PLUS_ID]["h"])
    rt = (by[PLUS_TEXT_ID]["x"], by[PLUS_TEXT_ID]["y"], by[PLUS_TEXT_ID]["w"], by[PLUS_TEXT_ID]["h"])
    rpanel = (by[PLUS_PANEL_ID]["x"], by[PLUS_PANEL_ID]["y"], by[PLUS_PANEL_ID]["w"], by[PLUS_PANEL_ID]["h"])
    rbg = (by[INTRO_BG_ID]["x"], by[INTRO_BG_ID]["y"], by[INTRO_BG_ID]["w"], by[INTRO_BG_ID]["h"])
    gap = rp[0] - (rt[0] + rt[2])
    other_cand_z = [_z_num(e) for e in elements
                    if e.get("kind") in ("hit", "list") and e["id"] not in INTRO_FLOAT_IDS]
    zs = sorted(_z_num(by[i]) for i in INTRO_OVERLAY_IDS)
    zc = [_z_num(by[i]) for i in INTRO_CLOSE_IDS]
    z_panel = _z_num(by["fc.intro_panel_hit"])
    return "\n".join([
        "加号按钮 `%s` %s：右缘 %d ＝ 面板 `%s` 右缘 %d；上缘 %d ＝ 槽顶 +%d ⇒ **完整在面板内**；"
        "与文字槽 `%s` %s 水平间隙 **%dpx**（要求零重叠）"
        % (PLUS_ID, rp, rp[0] + rp[2], PLUS_PANEL_ID, rpanel[0] + rpanel[2],
           rp[1], rp[1] - rpanel[1], PLUS_TEXT_ID, rt, gap),
        "浮层基座 6 件 z=%s（区间 %d–%d）；关闭件 2 件 z=%s（**逐件钉死 %s**，"
        "且 `fc.intro_close_hit` z=%s > 面板热区 `fc.intro_panel_hit` z=%s ✓）；"
        "本屏非浮层**点击候选**（kind ∈ {hit,list}）最高 z=%s ⇒ **浮层压过全部热区**"
        % (zs, INTRO_OVERLAY_Z[0], INTRO_OVERLAY_Z[1], zc, INTRO_CLOSE_Z,
           _z_num(by["fc.intro_close_hit"]), z_panel,
           max(other_cand_z) if other_cand_z else 0),
        "浮层面板 `%s` %s（九宫格 4/4/4/4）；两个 `_tx` 完整落在面板内 ⇒ **几何闭包成立**"
        % (INTRO_BG_ID, rbg),
    ])


ENTRY_COL_W = max(ENTRY_W, LABEL_W)   # 入口列**保留宽** = 333（原组名标签宽）
                                      # ★ 本批入口块虽改 296 宽，仍**沿用 333 列宽** ⇒ 道带位置与上一批**逐字相同**
                                      #   （左栏节点/连线几何零变化，只换入口列自身的形制）
ENTRY_COL_GAP = 16                    # 入口列与道带的间距
# ★ 第 12 批：入口块落点 = 锚定行 + 本偏移。它**沿用原「入口标记(48) → 组名标签(+4 间隙)」的行位**
#   （＝原 `fc.label.<NNNN>` 标签的 y）⇒ 交付样例入口块 y ＝ 190+52 / 285+52 / … = **242/337/432/527/622/717**
#   （行距 95 不变；块高 65 < 95 ⇒ 相邻块零重叠）。
ENTRY_BLOCK_DY = 52

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
#     理由（实测）：外壳件（视口 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 / 付箋 / 进入本章 /
#     右栏四段〔大播放窗 `fc.play_win`＋`fc.play_view` / 标题 / 说明 / 台词〕）是**两种层共用的舞台**，
#     只有「图内容」随层切换；把外壳件也挂 `vis_when:"main"` ⇒ 切到第 G 组独立层时外壳被**一并隐藏**，
#     深墨色组名与网格被画到没有底图的透明/黑画面上（HTML 实测证据 `E3_frag_frag1.png`：几乎不可读）。
#     ⇒ 层旗标由**图内容层独家持有**（见 `LAYER_OWNED_PREFIXES`）；外壳件**不写** vis_flag/vis_when。
#     ★ ISSUE-20260929-02（2026-09-29 · 冻结 §B.6）：本批新增的**播放键/暂停键同位置互斥**需要 flag
#       ⇒ 外壳件禁令新增**具名豁免集** `STATIC_FLAG_EXEMPT`（只此两件，豁免理由见该常量处）。
#     ★ 同批退场（**本批已删的元素**，勿再按旧描述理解）：迷你地图组（`fc.mini1..8` ＋ `fc.mapview`）
#       ＋ 场景回放组的 `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx`（素材文件一律保留）。
LAYER_FLAG = "fc_layer"
# 图内容层（**唯一**参与层旗标的族）：只有这些前缀的元素写 `vis_flag`/`vis_when`。
#   落盘前自检（`build()` 末尾）按本表双向卡：外壳件带旗标 ⇒ 拒；图内容件缺旗标 ⇒ 拒。
LAYER_OWNED_PREFIXES = ("fc.node.", "fc.branch.", "fc.label.", "fc.entry.", "fc.frag")
LAYER_MAIN = "main"

# ── C · 播放/暂停互斥（ISSUE-20260929-02 · 冻结 §B.5 / §B.6）───────────────
#   屏级 flag `fc_replay`（初值 `"play"`）：**播放键 `fc.pbkick`（`vis_when:"play"`）／暂停键
#   `fc.pbkick_pause`（`vis_when:"pause"`）同位置互斥** —— `layout/_schema.md` §四 **铁律一**：
#   只在状态上互斥的重叠件必须靠 `vis_flag`，**不得靠 z 排序**（两键都在大播放窗中央、同一矩形）。
REPLAY_FLAG = "fc_replay"
REPLAY_PLAY = "play"
REPLAY_PAUSE = "pause"
# ★ 冻结 §B.6：**唯一**被允许带 `vis_flag`/`vis_when` 的**外壳件**（具名豁免集；两处自检都认它）。
#   豁免理由（必须留痕）：`fc_replay` **不是层旗标**（≠ `LAYER_FLAG`），其初值 `"play"` 在**任何层**
#   都成立 ⇒ 播放键在主干层与 6 个独立层里**恒可见**；「切层丢外壳」这条禁令要防的风险**不存在**
#   （这两个键本就不该随层隐藏）。⇒ 除本集之外，外壳件带旗标**仍然严格拒绝**（`_dup` 与
#   `shell_flagged` 两处自检的反向自证能力**保留**；可把本集临时置空跑一次验之）。
#   ★★ 第 15 批（`ISSUE-20260930-02`）**新增 6 件**：详情浮层族 `fc.intro_*` 与 `fc.pbkick` 同性质 ——
#     它们挂的是屏级 flag **`fc_intro`**（`"closed"`/`"open"`），**不是层旗标**（不参与 `fc_layer`
#     切层），初值在**任何层**都成立 ⇒ 浮层开合与「主干/番外独立层」切换互不干扰。⇒ 同列豁免集。
#     （加号按钮 `fc.p_plus`/`fc.p_plus_hit` **不带** `vis_flag`，故不在本集。）
STATIC_FLAG_EXEMPT = {"fc.pbkick", "fc.pbkick_pause",
                      "fc.intro_scrim", "fc.intro_scrim_hit", "fc.intro_bg",
                      "fc.intro_panel_hit", "fc.intro_title_tx", "fc.intro_text_tx",
                      # ★ 第 15 批 · 第 2 轮（用户裁定 5）：浮层**关闭件 2 件**（同挂 `fc_intro`）。
                      "fc.intro_close", "fc.intro_close_hit"}
FRAG_LAYER_FMT = "frag%d"               # vis_when 取值
FRAG_ID_FMT = "fc.frag%d.%04d"          # 元素族 id：fc.frag<G>.<NNNN>（+`_tx`/`_hit`）
FRAG_ASSET = NODE_ASSET["frag"]         # 冻结 §二：image 296×65 用 ui/x_ui_node_frag_off|on.png
FRAG_COLS = 3                           # ★ 参照作 5 个/行；我方视口 1235 宽下 5×296+4×79=1796 放不下 ⇒ 改 3
FRAG_STEP_X = NODE_W + 79               # 375（冻结 §二：296+79）
FRAG_STEP_Y = 192
FRAG_LEAD_Y = 90                        # 行首（第一行）纵向偏移：origin + 90
FRAG_ORIGIN = (6, 6)                    # 原点 = 图表视口左上 + (6, 6)
# ★★ ISSUE-20260930-06（2026-09-30 · 用户裁定 5）：独立层改**纵向流水**、**组内全量产出** ★★
#   · 行数 = ceil(章数 / FRAG_COLS)，**不再由视口派生**（见 `frag_rows()`）；`cap` 与「视口派生的行上限」一并取消。
#   · 裁剪口径放宽：独立层元素只要求 **x 完整落视口 且 y ≥ 视口顶**（**允许纵向溢出**）—— 见 `frag_layer_rect_ok()`。
#     这是**有意偏离** §九 裁决 5（「全部产出元素完整落视口」），依据＝用户 2026-09-30 裁定 5
#     「番外独立层改纵向流水、组内全部产出」＋「纵滚归编程组」；**主干节点判据一字未改**。
FRAG_VIEW_ROWS = 4                      # ★ **纯文档常量：不参与任何裁剪/派生逻辑**。视口 fc.scroll（高 827）在
                                        #   **旧口径**下可容 4 行（＝ 12 格）；此值只作历史对照保留，
                                        #   现行行数一律用 `frag_rows(n)` 派生 ⇒ **不得**再据它设任何上限
FRAG_TITLE_SIZE = 24                    # 组名字号（★ 第 5 批：**不动** —— 修法只加底托，不改文字色/字号）
FRAG_TITLE_H = 44                       # 顶栏带高（网格行首 = 视口顶 +(6,6)；行首另有 FRAG_LEAD_Y 纵向偏移）
# ★★ 第 5 批（2026-09-28 收口）· 独立层组名不可读修复：**顶栏 = 标签底板 ＋ 文字** ★★
#   与主图 `fc.label.<NNNN>`（image 底板 + **同矩形** `_tx`，`align:"center"`）**同惯例**。
#   ★ **第 12 批订正（`ISSUE-20260929-04`）**：主图的组名底板 `fc.label.<NNNN>` **已被用户裁定删除**
#     （改为「淡黄入口块 + 其上的组名文字」）⇒ 「与主图同惯例」这句里的**主图那一侧已不存在**；
#     **独立层顶栏仍保留底板**（`fc.frag<G>_title_bg`，444×52 硬边件）—— 它在**独立层**上是必要的：
#     组名墨色 @palette.psv_ink 画在独立层舞台上仍需一块亮底（第 5/7 批的对比度修复）。
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

# 契约 §一 明确点名、**逐条断言其存在**的元素清单。
#   ★ 语义（本批订正）：这**不只是**「既有透传件」——凡**本批新增且必须常驻**的静态件也点名在此
#     （断言存在 ＝ 防「被静默删掉」；与 `STATIC_FLAG_EXEMPT` 的「过期检测」同一种保护思路）。
#   ★ 第 12 批（`ISSUE-20260929-04`）：① **移除 `fc.sysbar`**（该元素已按用户 2026-09-29 裁定删除，
#     再断言存在会直接 `SystemExit`）；② **新增点名 `fc.bg`**（满幅背景件，本批新增，
#     列入理由＝它是本屏最底层、全屏唯一的底图，被误删则整屏裸露/变黑而**其它判据全绿**——
#     必须有一条「它还在」的断言把它钉住；它不是「透传件」而是**新增点名件**，语义已在带注释）。
PASSTHROUGH_REQUIRED = [
    # ★ ISSUE-20260929-02（2026-09-29 · 右栏大改 · 冻结 §B.1/§B.2/§B.3）：
    #   · **删** `fc.p_player`（回放组内容底，已随该批退场）；
    #   · **保留** `fc.p_title`/`fc.p_text`/`fc.p_message`/`fc.smallmap`/`fc.pbkick`（该批改了 y/字体/flag）；
    #   · **新增点名** `fc.play_win`/`fc.play_view`/`fc.pbkick_pause`/`fc.pbkick_hit`
    #     （后两件与 `fc.pbkick` 一并列入点名 ⇒「播放键 + 暂停键 + 共同热区」三件均受本清单保护）。
    # ★ ISSUE-20260929-04 第 12 批：新增点名 `fc.bg`（满幅背景）；移除 `fc.sysbar`（元素已删）。
    "fc.bg",
    "fc.dim", "fc.scroll", "fc.p_title", "fc.p_text", "fc.p_message", "fc.smallmap",
    "fc.play_win", "fc.play_view", "fc.pbkick_pause", "fc.pbkick_hit",
    "fc.scr_rail", "fc.scr_up", "fc.scr_knob", "fc.scr_dn", "fc.zoom_rail", "fc.zoom_knob",
    "fc.zoom_minus", "fc.zoom_plus", "fc.shift_rail", "fc.shift_knob", "fc.shift_lf", "fc.shift_rg",
    # ★ ISSUE-20260929-05 第 13 批（2026-09-29 · 模式入口收敛）：**删** 4 个模式页签 `fc.mtab1..4`
    #   （用户 2026-09-29 裁定「删掉 4 个 `fc.mtabx` 和对应 text」⇒ 元素已删，再断言存在即 `SystemExit`）；
    #   同时**删** `fc.fusen_edit` / `fc.fusen_reset`（用户裁定「不再需要备注功能」）。
    #   ★ 旧文「`fc.mtab1..4` / `fc.fusen_edit`/`fc.fusen_reset` 在本清单内」**已作废**。
    "fc.titleplate", "fc.close",
    # ★ ISSUE-20260929-05 第 13 批：`fc.sysbar` 已在第 12 批移除（素材保留不删）。
    # ★ 第 13 批 **新增点名** 6 件 `fc.mode_*`（两枚模式入口各 3 件）。列入理由（与 `fc.bg` 同一思路）：
    #   它们是本屏上方**唯一的模式入口**（原 4 页签位置的替代品），被误删则入口区整体消失，
    #   而**其它判据全绿**（节点/连线/右栏不受影响）⇒ 必须有一条「它还在」的断言把这一族钉住。
    #   它们不是「透传件」而是**新增点名件**，语义同 `fc.bg`。
    "fc.mode_main_glow", "fc.mode_main_tx", "fc.mode_main_hit",
    "fc.mode_frag_glow", "fc.mode_frag_tx", "fc.mode_frag_hit",
    "fc.pbkick", "fc.jump", "fc.jump_hit",
    # ★★ ISSUE-20260930-02 第 15 批 **新增点名** 10 件（章节详情：加号按钮 2 件 ＋ 浮层 8 件）。
    #   列入理由（与 `fc.bg`/`fc.mode_*` 同一思路 ——「防被静默删掉」）：① 加号按钮 `fc.p_plus`/
    #   `fc.p_plus_hit` 是本批唯一的入口件（被误删则「说明」框右上角空掉、浮层无路可开，而其它的
    #   元素/连线/右栏判据**全绿**）；② 浮层 8 件 `fc.intro_*` 是**同一屏的整组浮层**（被误删则
    #   详情功能整组消失，同样无其它判据可察）。它们不是「透传件」而是**新增点名件**。
    #   ★ 第 2 轮（用户裁定 5）：浮层族由 6 件增为 **8 件**（＋关闭按钮 `fc.intro_close` ＋其热区
    #     `fc.intro_close_hit`）—— 关闭件被误删则浮层**只能靠点外部关闭**（观感上像缺件）。
    "fc.p_plus", "fc.p_plus_hit",
    "fc.intro_scrim", "fc.intro_scrim_hit", "fc.intro_bg",
    "fc.intro_panel_hit", "fc.intro_title_tx", "fc.intro_text_tx",
    "fc.intro_close", "fc.intro_close_hit",
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
    "· §一 列出的既有静态元素（视口 / 缩放平移滚条 / **模式入口 `fc.mode_*`** / 标题牌 / 关闭 / 进入本章 / 右栏四段）"
    "**原样透传**，id 与几何一字未改；被替换的只有旧图内容层 "
    "`fc.n_section*`/`fc.n_select*`/`fc.n_extra*`/`fc.label*`/`fc.branch`/`fc.newmark`。"
    "（★ ISSUE-20260929-02 第 11 批：迷你地图组 `fc.mini1..8`/`fc.mapview` 与场景回放组 "
    "`fc.pbk_panel`/`fc.p_player`/`fc.p_player_tx` **本批已删** ⇒ 本句旧文「旧 `fc.mini1..8` 保留原样」**已作废**）。\n"
    "    ★ **第 13 批订正**：本句原文列的「**页签 / 付箋**」两族（`fc.mtab1..4`（＋`_tx`/`_hit`）与 "
    "`fc.fusen_edit`/`fc.fusen_reset`（＋`_tx`/`_hit`））**本批已删**，位置由**两枚模式入口** `fc.mode_*`（6 件）接手 ⇒ "
    "旧文「页签 / 付箋 原样透传」**已作废**（详见下方第 13 批段；素材文件一律保留不删）。\n"
    "· ★ 收尾轮裁决（2026-09-27）：`fc.sep`（旧样板的固定坐标章分隔线）**不再透传**（它横穿新布局第二行节点）；章分隔线应由生成器在**段边界**处产出，本屏样例只有一段 ⇒ 不产。\n"
    "· ★ 文字（修正轮 V2 裁决）：字号 **19px**、**行距 1.0**（元素级 `line_spacing`，覆盖全局基线 1.4）、文字盒 **240 宽**（`x = x_node + 28` 水平居中）、`valign:「middle」` 垂直居中、最多 2 行、wrap。\n"
    "· ★ 竖向判据的由来（**不是元素高 65**）：三类底图的**可见实体面**（逐行平均 alpha>200）只有 **rows 8..55 ＝ 48px**（select 8..56 ＝ 49px）；上一轮按元素高判竖向容量 ⇒ 23px 两行的墨迹跨度 58px 越出实体面、实机第一行「切头」（vision 实测上溢 7–8px）。⇒ 判据改为**对准实体面**：\n"
    "    A 首行上留 = 首行墨迹顶 − 实体面上沿 ≥ **5px**；B 末行下留 = 实体面下沿 − 末行墨迹底 ≥ **5px**；C 任一行横向墨迹 ≤ **263px**（可见实体面宽实测 ≈282 ⇒ 左右各留 ≥9px）；D 712/712 **零截断**。\n"
    "    **712 条实测最小值：上留 5px / 下留 5px / 最宽行 228.0px / 截断 0**（`--text-fit-report` 可复跑）。19px 是这四条判据下的**字号上限**（两行需 `2×lineH ≤ 39 ⇒ lineH ≤ 19`，而 `lineH ≥ size`）。\n"
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
    "· ★ **番外入口（第 12 批改形制）**：`fc.entry.<NNNN>` 为**淡黄节点形块** 296×65"
    "（素材 `ui/x_ui_entry_frag_{off,on}.png`，由 `ui/x_ui_node_select_{off,on}.png` 派生、alpha 逐字节同源）；"
    "其**职能＝「进入该 xx 番外章节」**（热区 `fc.entry.<NNNN>_hit` 的 `action:\"flow_layer\"` + `layer:\"frag<G>\"`）。"
    "⚠ **旧文「番外入口标记为占位件（`x_ui_fusen_off.png` 充当，真 FC-4 图标未生成）」已作废**"
    "（该付箋件退役为本件的历史；**文件保留不删**）。"
    "★ **第 13 批订正**：旧文括注「仍被 `fc.fusen_edit`/`fc.fusen_reset` 使用」**亦已作废** —— "
    "该批删了这两键 ⇒ `x_ui_fusen_{off,over,on}.png` 现**零功能引用**。\n"
    "· ★ 第 2 步（ISSUE-20260928-02 · 接口冻结 §一/§二）——本屏数据面新增三件事：\n"
    "    ① **连线 `state` 取代 `kind`**：取值 `normal`/`visited`/`noroute`；生成器按 `state` 解析出 "
    "`color`（`@palette.edge_normal`/`edge_visited`/`edge_noroute`）、`w`（4/4/**3**）、`arrow`（true/true/**false**）后写进 JSON，"
    "**两端不做任何配色判断**。缺省 `normal` ＝ 交付样例外观（深蓝 #266080 / w4 / 有箭头）。\n"
    "    ② **节点 `flow_state` 可选字段**：`fc.node.<NNNN>` 支持 `locked`/`available`/`visited`/`current`/`new`；"
    "**本交付样例不写该字段 ⇒ 外观与文件内容一律不变**；只有 `--preset states` 演示（`_dim` 压暗件 / `_new` 角标件；"
    "`current` 由两端程序化画环 ⇒ **不产元素**）。\n"
    "    ③ **番外独立层**（屏级 flag `fc_layer`，初值 `main`）：★ **第 3 批更正 —— 外壳件不参与层旗标**："
    "层旗标由**图内容层独家持有**（`fc.node.*`（含 `_tx`/`_hit`/`_dim`/`_new`）/ `fc.branch.*` / `fc.label.*` / `fc.entry.*` / `fc.frag*`）；"
    "视口 / 缩放平移滚条 / **模式入口 `fc.mode_*`** / 标题牌 / 关闭 / 进入本章 / 右栏四段等**外壳件不写 `vis_flag`/`vis_when`**"
    "（★ ISSUE-20260929-02 唯一豁免：播放/暂停键 `fc.pbkick`/`fc.pbkick_pause`，见下方第 11 批段与 `STATIC_FLAG_EXEMPT`）—— "
    "它们是**两种层共用的舞台**，随层隐藏会让组名与网格画在无底图的透明/黑画面上（实测 `E3_frag_frag1.png`）。"
    "（★ 第 13 批：本句原列的「页签 / 付箋」两族已删、位置由 `fc.mode_*` 接手 ⇒ 旧文**已作废**。）\n"
    "    独立层新族 `fc.frag<G>.<NNNN>`/`_tx`/`_hit`（G=1..6，来自 `spine.json` `side_stories[].group` 的 6 组），"
    "网格**每行 3 个**、横向步进 375、纵向步进 192、行首纵向偏移 90、原点＝图表视口左上 +(6,6)；"
    "文字口径与主干节点**完全一致**（19px / 元素级 `line_spacing` 1.0 / 盒宽 240 / `max_lines` 2 / `x=x_node+28` / `valign:middle`），"
    "并**同样跑四条文字判据**；**独立层不产连线**。每组顶栏 = 组名标题 `fc.frag<G>_title`（组名＝`group_cn()`）＋ "
    "**按组**的返回键 `fc.frag<G>_back`/`_back_tx`（文案「返回主干」，字体/字号取该屏既有按键文字口径＝`fc.jump_tx` 的 27px/bold）"
    "/`_back_hit`（`action:\"flow_layer\"`, `layer:\"main\"`）；入口热区 `fc.entry.<NNNN>_hit`"
    "（`action:\"flow_layer\"`, `layer:\"frag<G>\"`，矩形＝入口件矩形）。\n"
    "    ④ ★ **交付样例含 6 组独立层**（第 3 批）：无参 `screen1` 产出 **6 组全部章节点**"
    "（G1 7/7、G2 7/7、G3 4/4、G4 10/10、G5 5/5、**G6 20/20**）"
    "⇒ 「点入口 → 进该组独立层 → 点该组返回键 → 回主干」在**交付样例上闭环**（此前只有入口热区、没有独立层元素，"
    "点一下屏面变空且**回不来**：HTML 实测 1,510,027 差异像素、全黑）。\n"
    "    ⑤ ★ **裁决 4（第 4 批 · 2026-09-28）——入口热区只在「该组的独立层确实在本档产出」时才产**："
    "`fc.entry.<NNNN>_hit` 的 `layer` 必须指向**本档已产出**的层；该组独立层未产出（如非全量演示档）⇒ "
    "**不产该热区**，入口 image 与组名标签**仍在**（主干层可见的**纯占位**、不可点）。"
    "落盘前**无条件**自检「存在 `fc.entry.*_hit` ⇒ 其 `layer` ∈ 本档产出层」，违反即拒绝落盘。"
    "本交付样例 `screen1` 产全部 6 组 ⇒ **6/6 组有入口热区**（无占位缺口）。\n"
    "    ★ **偏离登记（冻结 §二 已授权）**：参照作番外独立层是 **5 个/行**（其视口更宽）；我方 1235px 视口下 "
    "5×296+4×79=1796 放不下 ⇒ 改 **3 个/行**。\n"
    "    ★★ **2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）：独立层改「纵向流水、组内全量产出」（关闭缺口 G-3）** ★★\n"
    "    · 行数 ＝ `ceil(章数/3)`（**不再由视口派生、不设上限**）；几何不变（列 x 66/441/816、行 y = 286 + row×192、纵步 192、行首偏移 90）。\n"
    "    · **裁剪口径（本批唯一的判据放松 —— 有意偏离 §九 裁决 5）**：独立层元素改判「`x` 完整落视口 **且** `y ≥ 视口顶 190`」"
    "⇒ **允许纵向溢出**（下沿可超视口底 1017、可超画布 1080）；`x` 判据保留是因为 3 列右沿 1112 < 视口右沿 1295（x 方向本就零冲突）。"
    "**主干节点判据一字未改**（仍要求完整落视口）；`--no-cull` 语义不变（只关主干那条）。\n"
    "    · 依据 ＝ 用户 2026-09-30 裁定 5「番外独立层改纵向流水、**组内全部产出**」＋裁定 3「右侧滑标＝纵滚（**逻辑归编程组**）」；"
    "⇒ 第 6 组 20 章由旧口径「只产前 12 格」改为**全产 20 格**（第 5–7 行 y = 1054 / 1246 / 1438，末行下沿 1503）。\n"
    "    · 层固定件（`fc.frag<G>_title_bg` / `_title` / `_back`/`_back_tx`/`_back_hit`）**位置不变、不随滚**；**可滚对象＝节点行**。"
    "**未滚到位时 y > 1017 的行不可见＝预期，不得据此报「缺件」。**\n"
    "    · HTML 侧：若宿主对画布 `overflow:hidden`，**y > 1080 的节点需纵滚才可见**（`复刻/replica.js` 与 `krkr/game/ui_flow*.tjs` "
    "按 `vis_when`/几何数据驱动，**本批零改动**）；呈现由编程组的独立层纵滚承担。\n"
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
    "（节点 id / 标题 / 首行宽 / 左缘 / 行数）。当前实测：712 条**违规 0**，最紧 **+34.00**（`s01_02b`）。\n"
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
    "    ★★ 第 11 批（2026-09-29 · `ISSUE-20260929-02` · 用户 6 条指令 · 右栏「章节详情」大改）★★\n"
    "    · 本批**只动右栏**（**用户指令 1–4**）；左栏图表区（`fc.scroll` / 节点 / 连线 / 番外独立层 / 视口 / 滚条 / 页签 / 标题牌 / 关闭 / 付箋 / `fc.jump`）**一字不改**。\n"
    "    · **冻结 §B.1 删元素 12 件**（**只删元素，素材一个不删**）：迷你地图组 `fc.mini1..8` ＋ `fc.mapview`；"
    "场景回放组 `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx`。素材 `ui/x_ui_replay_panel.png` 等**保留在库**。\n"
    "    · **冻结 §B.2 新增 3 件**（**用户指令 2 / 3**）："
    "`fc.play_win`（**大播放窗底板**，`ui/x_ui_playwin_bg.png` 380×300、1:1 无 nine、z6、`(1448,214)`）／"
    "`fc.play_view`（**画面层**，`asset:null` ＋ `dynamic:\"flow_scene_frames\"`、`(1454,220,368,288)`、z7；"
    "**未填充时两端须画占位底色**，不得跳过；窗 380×300 ≈1.267:1 ⇒ 16:9 画面需 **contain 居中适配、上下留边**）／"
    "`fc.pbkick_pause`（**暂停键**，三态 `ui/x_ui_pbkick_pause_{off,over,on}.png` 119×119、"
    "`vis_flag:\"fc_replay\"` ＋ `vis_when:\"pause\"`、z20）。\n"
    "    · **冻结 §B.3 改 8 件**（**用户指令 1 / 3 / 4**）：三槽底 `y`（标题 214→**536** / 说明 309→**631** / 台词 750→**824**，"
    "**`x`/`w`/`h` 一律不动**）★ **本节几何已被第 3 轮改排作废**（现值见下方「第 3 轮」段与逐件 `note`）；三个 `_tx` 改**白字 ＋ 黑描边 2px**（`@palette.text_primary` ＋ "
    "`outline:true` / `outline_color:\"#000000\"` / `outline_width:2`，写法照 `layout/screens/10_dialog.json` 的 `dlg.text`，"
    "`shadow` **保持 false**，字号 **24** / `bold` **不动**），其中「说明 / 台词」两件**扩槽**为 "
    "`(1437,y,398,159)` / `valign:\"top\"` / `wrap:true` / `max_lines:4`（标题**不扩**，仍 `h40`/`middle`/`max_lines:1`）"
    "★ **该 `h159` 与 `y` 亦被第 3 轮作废（现 `h138`、`y` 见下）；`max_lines` 仍为 4**—— ★ **第 2 轮裁决（2026-09-29）**：`max_lines` **5 → 4**。依据：行盒 ＝ `floor(24 × 全局 `line_spacing.body` 1.4)` ＝ **33px**"
    "（`krkr/game/ui_theme.tjs:237-238` 的 `uiThemeElementSpacing`/`Math.floor(size × spacing)` ＋ `layout/_root.json:66` 的 `line_spacing.body=1.4`；"
    "元素级 `line_spacing` 优先，本批**不加**该字段 ⇒ 走全局基线）⇒ 槽高 **159** 时 4 行（4 行 132 ≤ 159 ✓；5 行 165 ✗）"
    "★ **第 3 轮改为槽高 138 ⇒ 138 ÷ 33 ＝ 4.18 ⇒ 仍 4 行**（132 ≤ 138 ✓）；"
    "`fc.pbkick` 移到**大播放窗中央** `(1578,304)` 并增 `vis_flag:\"fc_replay\"` ＋ `vis_when:\"play\"`；"
    "`fc.pbkick_hit` 随之 `(1575,301,125,125)` 且 `action` **空串 → `flow_replay_toggle`**。\n"
    "    · **冻结 §B.5 屏级 flag**：`flags_default` 新增 **`\"fc_replay\": \"play\"`**（与 `fc_layer` 并列）；"
    "取值 `play`（显示播放键）／`pause`（显示暂停键），**二者互斥、同位置、同一时刻只有一个可见**"
    "（铁律一：靠 `vis_flag`，**不得靠 z 排序**）。\n"
    "    · **冻结 §B.6 生成器自检的唯一放宽（留痕）**：`STATIC_FLAG_EXEMPT = {\"fc.pbkick\", \"fc.pbkick_pause\"}` —— "
    "`fc_replay` **不是层旗标**，其初值 `\"play\"` 在**任何层**都成立 ⇒ 播放键恒可见，"
    "「切层丢外壳」这条禁令要防的风险**不存在**；两处自检（载入处 `_dup` / 落盘前 `shell_flagged`）认该集，"
    "**集外仍严格拒绝**（反向自证能力保留）。\n"
    "    · **右栏四段**（冻结 §B.4；栏底 `fc.smallmap`（1416,190,443×829）**保留不动**）："
    "**★ 第 3 轮（vision 复审后）改排为「窗与三槽分离、三槽彼此紧凑」——本句为现行值**："
    "① 大播放窗 `214–514`（`(1448,214,380,300)` 不动）② 标题 `534–607`（`y 536→534`）③ 说明 `617–767`（`y 631→617`、`h 171→150`）"
    "④ 台词 `777–927`（`y 824→777`、`h 171→150`）；"
    "**段间**：窗底 514 → 标题 534 ＝ **20**；标题底 607 → 说明 617 ＝ **10**；说明底 767 → 台词 777 ＝ **10**；"
    "**台词底 927 → 按钮 `fc.jump` 上沿 943 ＝ 16px（无重叠）**；栏底 1019 − 按钮下沿 1004 ＝ **15px**。"
    "两个 `_tx`：说明 `(1437,623,398,138)`、台词 `(1437,783,398,138)`（均 `y = 槽顶 + 6`，落在槽内）。"
    "大播放窗居中于 443 栏宽 ⇒ `x = 1416 + ceil((443 − 380)/2) = 1416 + 32 = 1448`（`fc.play_win` 本批未动）。\n"
    "    · **本批计数订正**：元素总数 **289 → 280**（−12 ＋3）、静态件（外壳）**61 → 52**；图内容层 **228 不变**。"
    "上文各批段里的「289 / 外壳 61 / 外壳件 61」是**那几批当时的读数**；"
    "★ **第 12 批再订正：280 → 274**（见下方第 12 批段；「图内容层 228」亦随之作废；该批读数 222 "
    "**现已再被第 16 批的 246 取代** ⇒ 现值见下方第 16 批段）。\n"
    "    · **语义边界（不得声称已生效）**：`flow_replay_toggle` = **命中即派发**；画面的**时序 / 帧序列**与 "
    "`fc.play_view` 的填充**接线留编程组**（与 `bgm_playpause` ／ `replay_play:<行号>` 同口径）。\n"
    "    ★★ **第 3 轮（2026-09-29 · vision 实机复审后 · 主代理已亲自复核）—— 两处真缺陷修复** ★★\n"
    "    · **① 右栏台词槽压住「进入本章」按钮（本批引进的排版失误，已修）**："
    "第 11 批首版把台词槽放到 `y824 h171` ⇒ 槽下沿 **995**，与 `fc.jump`/`fc.jump_tx`/`fc.jump_hit` `(1474,943,328,61)` 的上沿 **943** "
    "**竖直重叠 52px**（vision 实测按钮可见区 x1482..1800 / y953..996 落在槽内）。\n"
    "      修法：三个文字槽高度 **171 → 150**，重排为「窗与三槽分离、三槽彼此紧凑」——"
    "`fc.p_title` `y 536→534`（h73 不变）／`fc.p_title_tx` `y 546→544`（仍 `y=槽顶+10`）／"
    "`fc.p_text` `y 631→617`、`h 171→150`／`fc.p_text_tx` `y 637→623`、`h 159→138`／"
    "`fc.p_message` `y 824→777`、`h 171→150`／`fc.p_message_tx` `y 830→783`、`h 159→138`；"
    "`fc.play_win`/`fc.play_view`/`fc.pbkick`/`fc.pbkick_pause`/`fc.pbkick_hit`/`fc.jump*` **一字不改**。\n"
    "      ⇒ **改后**：段间 **20 / 10 / 10**；**台词底 927 → 按钮上沿 943 ＝ 16px（无重叠）**；按钮下沿 1004 → 栏底 1019 ＝ 15px。\n"
    "      ⇒ **容量不变（`max_lines` 仍 4，双口径都过）**：**krkr** 行盒 `floor(24 × 1.4) = 33` ⇒ 138 ÷ 33 ＝ 4.18 ⇒ 4 行（4×33＝132 ≤ 138 ✓）；"
    "**HTML** 行盒 `24 × 1.4 = 33.6`（保守取整 34）⇒ 4×34＝136 ≤ 138 ✓（余 2px）。\n"
    "    · **② 动态层「占位标签」横向溢出屏幕（结构性缺陷，已修 · 两端同判据）**："
    "`krkr/game/ui_widget.tjs::uiWidgetDrawPlaceholder` 原只按高度决定画不画第二行、**横向无任何约束** ⇒ "
    "`fc.play_view` 的第二行 `dynamic:flow_scene_frames`（25 字符、全局 body 字号）墨迹实测 **x1456..1918**，"
    "戳出窗右沿 1822、越过栏右沿 1859、贴到屏宽 1919 被切断；`复刻/replica.js` 的 `markDynamicEmpty` 靠 CSS 自然换行，两端**行数与断点分叉**。\n"
    "      修法：**每一行都必须完整落在元素矩形 `r` 内**，装不下就**截断并追加 `…`**，两端都**不换行**；"
    "宽度预算 ＝ 元素可用内容宽（krkr 无内边距 ⇒ `r.w`；HTML 扣左右内边距），度量各用**本端自己的**度量"
    "（krkr `ui_theme.tjs::uiThemeEllipsize` 用 `Font.getTextWidth`；HTML 离屏 span + `getBoundingClientRect`）。\n"
    "      该机制是**所有动态层共用**的 ⇒ 新增动态层自动受益（含今后 122×73 这类小盒；小盒另受「框高不足两行只画首行」的既有规则约束）。\n"
    "    · **本轮的机检**：`--text-fit-report` / `--title-check-report` / `--selfcheck-title-break` 全绿（与右栏无关的判据不受影响）；"
    "占位标签的横向钳位由**实机巡演导出的 PNG 像素实测**复核（`_工作\\ISSUE-20260929-02_右栏大改\\证据\\缺陷2_占位钳位.md`）。\n"
    "    ★★ 第 12 批（2026-09-29 · `ISSUE-20260929-04` · 流程图页四件收尾 · 用户 2026-09-29 追加裁决）★★\n"
    "    · **① 新增满幅背景 `fc.bg`**（用户指令 4′「给流程图页面加一个背景图，就选 `bg72.png`」）："
    "`kind:\"image\"`、`(0,0,1920×1080)`、素材 `ui/x_bg_flowchart.png`（`美术统一_超分\\CG背景\\bg72.png` 2560×1440 → **0.75× LANCZOS** 降采样，**不调色/不裁切/不加字**）、"
    "**`z:0`**（在 `fc.dim` z1 之下）、`visible_default:true`、**无 `nine`**（1:1）；它**是外壳件**（不写层旗标 ⇒ 主干与 6 个独立层共用的舞台）。\n"
    "    · **② `fc.sysbar` 已删**（用户 2026-09-29 裁定「`fc.sysbar` 删掉元素」）：该件是 `sysbar` 屏删除后**留在本屏的遗留装饰条**（无文字、无点击）；"
    "**素材 `ui/x_ui_sysbar.png` 保留不删**。\n"
    "    · **③ `fc.zoom_knob` 换件并删 `nine`**（用户指令 1「滑标应该是一个指针形状，而不是现在的两个不明物体形状」）："
    "`asset` → `ui/x_ui_zoom_handle.png`（**40×31 单一竖圆角胶囊手柄**）、**删 `nine`**"
    "（旧件 `x_ui_zoom_knob.png` 29×16、内含**横胶囊＋圆点两个图形**，九宫格各自拉伸 ⇒ 实机上是「两坨」）；"
    "`(1174,112,40×31)` / `z:21` / `opacity:255` **不变**；旧件退役、**文件保留不删**。\n"
    "    · **④ `fc.p_title` / `fc.p_title_tx` 三槽对齐**（用户指令 4「宽度和下面两个 `fc.p_text_tx` 和 `fc.p_message_tx` 统一」）："
    "`fc.p_title` `x/w` **1416/443 → 1425/422**、`fc.p_title_tx` `x/w` **1428/419 → 1437/398** ⇒ 与 `fc.p_text`/`fc.p_message` 及其 `_tx` 的 `x/w` **逐字相同**（口径 A）；"
    "`y`/`h`/`z`/`font` 一律不改，另两槽底一字不改。\n"
    "    · **⑤ 番外入口统一为「淡黄节点形块」＋ 组名底板退役**（用户追加裁决：「`fc.label.000x` 与 `fc.entry.000x` 一律删去，"
    "统一为**和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状，只是底色换成淡黄（≈ `#FFFF99`）**；文字方案不动」）：\n"
    "      · `fc.entry.<NNNN>`（0001–0006）**改形制**：86×48 付箋 → **296×65 淡黄节点形块**"
    "（素材 `ui/x_ui_entry_frag_{off,on}.png`，**由 `x_ui_node_select_{off,on}.png` 派生**：alpha 逐字节同源、仅换色相）、"
    "`nine{l14,t0,r13,b0}`（与 `fc.node.*` **完全一致**）、`z:20`、`state_assets{normal,hover}`；"
    "**职能＝「进入该 xx 番外章节」**＝热区 `fc.entry.<NNNN>_hit` 的 `action:\"flow_layer\"` + `layer:\"frag<G>\"`（＝用户说的 `fc_layer - fragx`，**action/layer 一字未改**）。\n"
    "      · `fc.label.<NNNN>`（**底板 image 333×38**）**已删**（**只删元素**；素材 `ui/x_ui_label_off.png` 保留不删）。\n"
    "      · `fc.label.<NNNN>_tx` **保留**（**文字方案未动**：16px / bold / `@palette.psv_ink` / `align:center` / `valign:middle`），"
    "矩形改为与入口块**同矩形** `(60, y, 296×65)`，`y` ＝ **242/337/432/527/622/717**（＝原 `fc.label.<NNNN>` 的行位；行距 95 不变 ⇒ 相邻块高 65 < 95，零重叠）。\n"
    "      · **文字容量实测**（本工程铁律：判容量用**真实语料 ＋ 引擎折行算法**，不得凭目测）：6 条组名在 16px / 盒宽 296 下"
    "经 `ui_theme_wrap` 复刻复算**全部单行**（最长「番外·群像（新年行军 / 格兰玛尼耶）」**265.0px** ≤ 盒宽 296，"
    "且 ≤ 入口块**可见实体面**带宽 **280px**）⇒ **维持 `wrap:true` + `max_lines:1`，不新增字段**。\n"
    "    · **本批计数订正（第 12 批当时读数）**：`screen1` 元素 **280 → 274**（总）＝ 外壳 52 ＋ 图内容层 222；"
    "五档各 **−6**（**274 / 118 / 97 / 111 / 130**）。"
    "⚠ **该组读数已被第 13 批取代、并再被第 15/16 批取代**（见下方第 15/16 批段；**第 16 批现行值 296 / 116 / 95 / 109 / 128**；"
    "第 13 批读数 262 / 106 / 85 / 99 / 118、第 15 批读数 272 / 116 / 95 / 109 / 128 与第 15 批首轮读数 270 / 114 / 93 / 107 / 126 **均已作废**）。\n"
    "    · **左栏图表区未改**：入口块右缘 **356** ≪ 最左节点槽 **516** ⇒ 与节点道带**零重叠**；道带位置因 `ENTRY_COL_W` 仍取 **333** 而**逐字不变**（节点/连线几何零变化）。\n"
    "    · **机检**：`m06_delivered_sample_ledger.py`（基线总账追认 **1 增 / 7 删 / 字段改动**，**含 `nine` 的删与增**）、"
    "`m03_shell_and_delivery_loop.py`（基坑口径改为 `fc.bg` ＋ `fc.dim` ＋ `fc.scroll`；`states` 元素数 111 —— ★ 第 13 批已改 **99**）、"
    "`m02_states_frag_variants.py`（右栏 z 序补 `fc.bg`（z=0）为最低位）、`m01_screen1_appearance_diff.py`（消费同一总账）。\n"
    "· ★★ **第 13 批（`ISSUE-20260929-05` · 模式入口收敛 ＋ 删备注功能与对话框提示）** ★★\n"
    "    · 用户 2026-09-29 指令：**流程图页** ① 删 4 个 `fc.mtabx` 与其 text；② 在原位置用**两枚文字入口**取代 ——"
    "**「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）；③ 删 `fc.fusen_edit`/`fc.fusen_reset`"
    "（＋`_tx`/`_hit`，**不再需要备注功能**）。**对话框页**：删除 `dlg.hint`（不需要操作提示）。\n"
    "    · **删 19 件 / 加 6 件**（**只删元素、素材一个不删**）：\n"
    "      — 删 `fc.mtab1..4`＋`_tx`＋`_hit`（**12 件**，4 个模式页签）与 `fc.fusen_edit`/`fc.fusen_reset`＋`_tx`＋`_hit`"
    "（**6 件**，备注功能键）＝ 本屏 **18 件**；另 `layout/screens/10_dialog.json` 删 `dlg.hint`（**1 件**，该屏手工维护）。\n"
    "      — 加 **6 件** `fc.mode_main_glow`/`_tx`/`_hit` ＋ `fc.mode_frag_glow`/`_tx`/`_hit`：**180×60**、"
    "**`_glow`/`_hit` @y25** ／ **`_tx` @y33**（★ **E5 订正**：用户 2026-09-29 裁决「两个模式入口的文字下移 8px」"
    "—— 实测原墨迹 y31..63/中心 47 vs 框中心 55 ⇒ 偏高 8px；下移后墨迹 y≈39..71、中心 55）、"
    "x=**34**／**254**（等宽 180、间距 40）、z=**10/20/95**、`state_group`＝`mode_main`/`mode_frag`、"
    "`action`＝**`flow_mode_main`/`flow_mode_frag`**（**拟用名**：命中即派发，切集/筛选留编程组，已登记进 "
    "`layout\\_schema.md` §六 动作表）；`state_assets` 三态指向素材组产出的 **`ui/x_ui_modetab_{off,over,press}.png`**"
    "（**180×60 ×3，两入口共用同一套** —— 冻结 §D 允许按形状一致性复用、优先省件数）；文字 30px / `bold:false`"
    "（引擎默认字体族首位即**微软雅黑 Regular**）＋ 白字 ＋ 黑描边 2px。\n"
    "    · **三态口径**：三态**全靠 `_glow` 底光图承载**（同一枚柔和白淡光的弱/强/实底三档；`_press`＝半透明冰蓝实底胶囊＋1px 亮边）；"
    "`_tx` 文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**。"
    "⚠ 用户原话「**文字下移 1px**」**无法实现**（不支持文字逐态位移、`state_group` 只配对图片层）⇒ 以「**底沉 1px**」等价表达；"
    "如需文字本体位移须加新接口（新裁决）。已写进 `UI组交接编程组.md` 与元素 `note`。\n"
    "    · **落盘前自检（本批新增 · 真不变量）**：两枚模式入口（各 3 件）**同 x/w/h**（**`_glow`/`_hit` 逐字段同框；"
    "`_tx` 的 `y = _glow.y + 8`**，★ E5 口径）、**完整落在画布内**、"
    "**彼此零重叠**、且**与任何相邻元素零重叠**（满幅层 `fc.bg`/`fc.dim` 视作画布底、不计入邻居）——"
    "违反即**拒绝落盘**；`--selfcheck-mode-entries` 是它的**变异自证**（重叠／越出画布／压住 `fc.titleplate` 三条变异各须被检出）。"
    "实测：与 `fc.titleplate` 竖直间隙 **8.0px**、与 `fc.close` 92px、与 `fc.scroll` 105px、与右栏 `fc.smallmap` ≥990px。\n"
    "    · **动作表**：`_schema.md` §六 新增 `flow_mode_main`/`flow_mode_frag` 两行（拟用名 + 语义边界）。\n"
    "    · **元素数（第 13 批收口时）**：`screen1` 总 **262 件**（＝ 外壳 40 ＋ 图内容层 222，由 274 −12 得到）；`dialog` **10 → 9**（−1；⚠ 冻结 §E 记的「18 → 17」为**绝对值笔误**，增量 −1 正确）；"
    "**17 屏合计 1404 → 1391**。五档各 **−12**：**262 / 106 / 85 / 99 / 118**；外壳 **52 → 40**（逐件：删 12 ＋ 6、增 6），图内容层 222 逐字不变。\n"
    "    · **闸门同步**：`m06`（基线总账：18 删 / 6 增 / 新件载荷字段追认）、`m03`（`states` 元素数 **111 → 99**）、"
    "`m02`（**`fc.fusen_edit`/`fc.fusen_reset` 两件移出「九宫格件」名单**，改由**三段新断言**接手："
    "六件 `fc.mode_*` 三态素材在库且 1:1 无 `nine`／`fc.mode_*_hit` 的 `action` 非空且**在 §六 动作表内**／"
    "同 `state_group` 的 `_glow` 与 `_hit` 配对且三态齐 ⇒ **只增不减覆盖**；另有**反向断言**「18 件均不在屏数据里」）、"
    "`m01`（消费同一总账）。\n"
    "    · **死引用排查（必做，实测）**：`krkr/game/*.tjs`（含巡演步骤 `UIScrTourSteps`）／`复刻/*.js`／`复刻/*.html` "
    "对 19 件**没有任何「按 id 取值后解引用」**（仅 3 处为屏数据定义/注释）；巡演按屏与 `action` 选点、"
    "`_selftest_states.html` 对 flowchart 是**数据驱动遍历**（无硬编码计数）⇒ **删元素零悬空引用**。\n"
    "· ★★ **第 15 批（`ISSUE-20260930-02` · 章节详情：说明槽截断 ＋ 详情浮层 ＋ 加号按钮）** ★★\n"
    "    · 用户 2026-09-30 裁定：① 加号按钮**新做**一枚 44×44 三态小徽章（风格/配色对齐 `fc.pbkick`）；\n"
    "② 浮层内容＝**章节标题 ＋ 简介全文**（白字黑描边）；③ 加号位置＝**「说明」框内右上角**、文字槽相应**收窄**；\n"
    "④ 字号**不下调**（维持 24px），**超出边框即省略为省略号 `……`**（不得用 `...`）。\n"
    "    · **加 10 件**（**只加元素；素材新出 3 件** `ui/x_ui_plusbtn_{off,over,press}.png` 44×44 RGBA；\n"
    "关闭件**零新素材**、复用既有 `x_ui_close_*`）：\n"
    "      ① 右栏 2 件：`fc.p_plus`（image，三态 44×44 @1803,**618**、z27、`state_group:\"p_plus\"`、1:1 无 `nine`）\n"
    "＋ `fc.p_plus_hit`（hit，同矩形、z96、`action:\"flow_intro_open\"`、同 `state_group`）；\n"
    "      ② 详情浮层 **8 件**（`vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`）：`fc.intro_scrim`（rect 满幅 `#000000`×150、z200）\n"
    "／`fc.intro_scrim_hit`（hit 满幅、z210、`action:\"flow_intro_close\"`）／`fc.intro_bg`（image `ui/x_ui_gal_cell_on.png`\n"
    "**1240×400 @340,340**、**`nine{l:4,t:4,r:4,b:4}`**、z220）／`fc.intro_panel_hit`（hit 同面板、z230、**空 `action` 吞点击**）\n"
    "／`fc.intro_title_tx`（text **1140×44 @372,372**、24px **bold**、白字黑描边、`max_lines:1`、z235）\n"
    "／`fc.intro_text_tx`（text **1176×276 @372,432**、24px 常规、白字黑描边、`max_lines:6`、z235）\n"
    "／**`fc.intro_close`（image 26×26 @1530,364、`ui/x_ui_close_*` 三态、`nine{6,6,6,6}`、`state_group:\"intro_close\"`、z236）\n"
    "／`fc.intro_close_hit`（hit 46×46 @1520,354、`action:\"flow_intro_close\"`、同 `state_group`、z237）**。\n"
    "    · **说明槽收窄**：`fc.p_text_tx` 的 `w` **398 → 300**（其余字段一字不改）—— 终值取 **300**（非冻结书初稿 344）：\n"
    "M4 几何定标（真实语料 1199 条）实测 300 档最大墨迹 **336px ≤ 354px 上限**（344 档 384px ✗）。\n"
    "    · **屏级 flag**：`flags_default` **追加 `\"fc_intro\": \"closed\"`**（进屏默认关闭浮层）；既有 `fc_layer`/`fc_replay` 不动。\n"
    "    · **动作**：`flow_intro_open`（`fc.p_plus_hit`）/`flow_intro_close`（`fc.intro_scrim_hit` **＋** `fc.intro_close_hit`，两条关闭路径共用语义）\n"
    "—— **纯 flag 翻转、两端本批实现**（与 `flow_replay_toggle` 同口径）；**简介全文与标题的取数（按 `场景id`）留编程组**。已登记进 `layout\\_schema.md` §六 动作表。\n"
    "    · **超框省略号**（冻结 §五）：折行超 `max_lines` ⇒ 保留前 N 行、末行逐字回退接 `……`（两个 U+2026）；\n"
    "连 `……` 都放不下 ⇒ 该行不画；**纯渲染、不参与布局**。三处同判据（krkr `ui_theme.tjs` ／ HTML `replica.js`\n"
    "／ Python `gen_flow_layout.apply_ellipsis`），由 `工具/test_text_ellipsis.py` 冻结期望表交叉闸门守住；\n"
    "**引擎侧**另有巡演步 `kind:\"wrapellip\"` 直调 `uiThemeWrap` 打 `★WRAPELLIP★` 判词（第 2 轮补上，见 `ui_screens.tjs`）。\n"
    "    · **新增落盘前自检**（冻结 §六 · 真不变量）：① `fc.p_plus` 与 `fc.p_text_tx` **零重叠**且按钮完整在面板 `fc.p_text` 内；\n"
    "② 浮层族（**8 件**）z **高于本屏所有非浮层点击候选**（`kind ∈ {hit,list}`、z 按引擎口径**数值化**）——\n"
    "其中基座 6 件受区间 **200–235** 约束、关闭件 2 件**逐件钉死 236/237** 且 **`fc.intro_close_hit.z > fc.intro_panel_hit.z`**；\n"
    "③ 浮层族几何完整在画布内、两个 `_tx` 完整在 `fc.intro_bg` 内。\n"
    "违反即**拒绝落盘**；`--selfcheck-intro-overlay` 是它的**变异自证**（**九条**变异各须被检出，\n"
    "含「z 写成字符串」「kind 换成 list」两条口径对齐引擎的负向对照）。\n"
    "    · **元素数（第 15 批收口读数 —— ⚠ 其中 `screen1` 的计数已被第 16 批取代，见下）**：`screen1` 旧读数 **272**（总）＝ 外壳 **50** ＋ 图内容层 222（＝ 262 ＋10，10 件全为外壳件）；\n"
    "第 15 批五档读数 **272 / 116 / 95 / 109 / 128**；**17 屏合计 1391 → 1401**。"
    "（⚠ 本句里的「272」「图内容层 222」是**第 15 批的历史留痕**，第 16 批现行值见下方第 16 批段。）\n"
    "      ★ **第 2 轮计数变更（用户裁定 5/6/7）**：浮层族 6 → **8 件**（＋ `fc.intro_close`/`fc.intro_close_hit`）\n"
    "⇒ 第 15 批的「＋8」订正为「**＋10**」、外壳 48 → **50**；浮层面板 1240×652 → **1240×400**、\n"
    "标题槽 → 1140×44 @372,372、正文槽 → 1176×276 @372,432；加号按钮 y 625 → **618**；\n"
    "加号素材外圈环改**按目标尺寸 1:1 直绘**（off 环色 (146,159,183)@α255，对齐 pbkick）。\n"
    "· ★★ **第 16 批（`ISSUE-20260930-06` · 2026-09-30 · 番外独立层改纵向流水）** ★★\n"
    "    · 用户裁定 5：独立层改纵向流水、**组内全量产出** ⇒ 第 6 组由旧口径的 12 格全产为 **G6 20/20**"
    "（新增 8 个节点 × 3 件〔image/text/hit〕＝ **＋24 件**，全部落在图内容层；**素材零新增**）。\n"
    "    · **现行元素数（第 16 批）**：`screen1` **296 元素**（总）＝ 外壳 **50** ＋ 图内容层 **246**"
    "（＝ 主干 **57**〔`fc.node.*` 39 ＋ `fc.label.*_tx` 6 ＋ `fc.entry.*` 12〕＋ 独立层节点 **159**〔53 格×3〕＋ 每组顶栏 **30**）；\n"
    "五档 **296 / 116 / 95 / 109 / 128**（仅 `screen1` 因本轮 ＋24）；**17 屏合计现行 1428**（第 16 批 1401 → 1422；★ **D-01 2026-10-01**〔`ISSUE-20261001-11`〕：`title` 屏 18→24 ⇒ ＋6）"
    "（★ 中间值 **1425** ＝「flowchart 单项 +24」未减 config 的 −3，**只作历史留痕**；"
    "冻结 §7.1 勘误 4 定第 16 批终值 **1422**；`flowchart` **296** 与 `config` **467** 两个单项值不变）；**外壳 50 逐字不变**。\n"
    "    · 裁剪口径放宽（**有意偏离** §九 裁决 5）、层固定件不随滚、HTML `overflow:hidden` 时需纵滚 —— 见上方独立层段；"
    "需纵滚的行 y = 1054 / 1246 / 1438（末行下沿 1503）。\n"
    "    · ★★ **冻结 §7.2 可见性契约（2026-09-30 · 一审后返修 · vision 打回的直修项）** ★★\n"
    "      起因：G6 第 5 行节点盒 y1054–1119 **无底部裁剪**，只有物理屏 y1080 切断 ⇒ 画面底部 y1062–1080 露出半截"
    "节点与文字字头（实测 7280 px），且落在底部横移条（y1018–1043）之下、压在主面板外背景上。\n"
    "      修法：独立层中**元素盒下沿 `y + h > 视口底 1017` 的行**，其**全部三件**（`image`/`_tx`/`_hit`）一律写 "
    "**`visible_default: false`** ⇒ **数据完整产出、默认不画**；**纵滚实现时置真**（属编程组）——与 config 屏既有"
    "「`visible_default:false` ＝ 预留下但默认不画」**同源用法，不新造机制**。**只加字段、不减元素**（仍 296）。\n"
    "      ⇒ **产出 53 格 ＝ 数据完整；默认可见 12 格（4 行）；其余 8 格需纵滚置真**"
    "（该「12 格 / 8 格」以**唯一有溢出的第 6 组**为准；全屏默认可见 ＝ G1–G5 共 33 格 ＋ G6 前 4 行 12 格 ＝ 45 格）。"
    "`--frag-report` 另报「默认可见格数 / 需纵滚置真格数」，「产出」列仍按**元素存在**计。"
    "落盘前**双向**自检：溢出却默认可画 / 未溢出却默认不画 ⇒ 均拒绝落盘。\n"
    "    · **一句话印证**：三处产物（`layout/ui_layout.json`／`krkr/game/ui_layout.tjs`／`复刻/ui_layout.js`）与\n"
    "五档金标由 `--refresh-golden` 重钉后一致（见 `PRESET_TABLE` 末的「第 16 批重钉」）。\n"
)



# ══════════════════════════════════════════════════════════════════════
# 静态元素快照 —— 逐字提取自改造前的 layout/screens/32_flowchart.json
#   （§一 要求「原样透传、id 与几何一字不改」；内嵌以保证生成器幂等）
# ══════════════════════════════════════════════════════════════════════
STATIC_ELEMENTS_JSON = r"""[
 {
  "id": "fc.bg",
  "kind": "image",
  "z": 0,
  "visible_default": true,
  "asset": "ui/x_bg_flowchart.png",
  "x": 0,
  "y": 0,
  "w": 1920,
  "h": 1080,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-04 · 冻结 §A）：`krkr/assets/ui/x_bg_flowchart.png` **1920×1080 RGB**（无 alpha）—— 由 资源组\\美术统一_超分\\CG背景\\bg72.png（2560×1440）**0.75× LANCZOS 降采样**得到，**不做任何调色/裁切/加字**。",
  "note": "★ ISSUE-20260929-04 **新增**（2026-09-29 · 用户指令 4′「能不能给流程图页面加一个背景图，就选 bg72.png」）：流程图屏**满幅背景**。\n· `z=0` ⇒ 在 `fc.dim`（全屏压暗遮罩，`z=1`）**之下**；用户 2026-09-29 裁决「**满幅铺底 ＋ 保留现有 `fc.dim` 压暗 60（opacity 值）**」。\n· **1:1**：素材 1920×1080 与元素**等尺寸 ⇒ 不带 `nine`**（整图铺满）。\n· 它是**外壳件**（id 不属图内容层前缀 `LAYER_OWNED_PREFIXES`）⇒ **不写 `vis_flag`/`vis_when`**：主干层与 6 个番外独立层**共用的舞台**（切层时不隐藏）。\n· 源件与倍率：`美术统一_超分\\CG背景\\bg72.png` 2560×1440 → **0.75×**（＝1920/2560）LANCZOS 降采样（该目录被 `.gitignore` 排除 ⇒ 中间物不落库，只落降采样成品）。\n· 旧文（本批之前）「右栏详情／缩略总览(minimap)／回放窗」等描述与本案无关；`fc.bg` 是**新增纯背景件**，不复用任何旧 id。"
 },
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
  "id": "fc.mode_main_glow",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_modetab_off.png",
  "x": 34,
  "y": 25,
  "w": 180,
  "h": 60,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-05 · E1）：`ui/x_ui_modetab_{off,over,press}.png` **180×60 RGBA ×3**（同一枚柔和白淡光的弱/强/实底三档）；**两个模式入口共用同一套 3 张**（形状一致，冻结 §D 允许复用、优先省件数）。",
  "note": "模式入口「本篇集合」的**底光图**（三态承载者）。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_main`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。",
  "state_assets": {
   "normal": "ui/x_ui_modetab_off.png",
   "hover": "ui/x_ui_modetab_over.png",
   "pressed": "ui/x_ui_modetab_press.png"
  },
  "state_group": "mode_main"
 },
 {
  "id": "fc.mode_main_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 34,
  "y": 33,
  "w": 180,
  "h": 60,
  "font": {
   "size": 30,
   "bold": false,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "本篇集合",
  "note": "★ **E5 订正（用户 2026-09-29 裁决 · 「两个模式入口的文字下移 8px」）**：本件 `y` **25 → 33**（`x/w/h` 与 `font`/`align`/`valign`/`wrap`/`max_lines`/`sample` **一字未动**）。依据：vision 实测两枚文字**墨迹恒为 y31..63（中心 47）**，而元素框 `y25..85` 的中心是 **55** ⇒ **偏高 8px**，且按下态冰蓝胶囊上沿（`y≈36`）会横穿字头 5px。下移后墨迹 **y≈39..71、中心 55 与框同心**（判据：|墨迹中心 − 框中心| ≤ 2px）。★ **`_glow`/`_hit` 仍是 `y25`**（底光与热区不动）；偏移的唯一来源是常量 `MODE_ENTRY_TX_DY = 8`。★ 先例＝`ISSUE-20260928-03` 给列表标签与 `item_buttons` 各 `y+6` 把墨迹压到底中（同一口径）。\n· 模式入口「本篇集合」的**文字**（引擎绘制，30px / `bold:false` ⇒ 引擎默认字体族首位即**微软雅黑 Regular**（`layout\\_root.json` 的 `fonts.fallback_faces[0]`）；白字 ＋ 黑描边 2px ＋ 白淡光由底层 `_glow` 图给）。文字**不参与换态**（schema 不支持文字带 `state_assets`）。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_main`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。"
 },
 {
  "id": "fc.mode_main_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 34,
  "y": 25,
  "w": 180,
  "h": 60,
  "action": "flow_mode_main",
  "label": "",
  "state_group": "mode_main",
  "font": {
   "size": 30,
   "bold": false,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "模式入口「本篇集合」的**热区**（与底光图/文字同矩形 180×60，z95 最高 ⇒ 指针落在按钮任意位置都由它胜出，再经 `state_group:\"mode_main\"` 联动底层 `_glow` 换三态）。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_main`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。"
 },
 {
  "id": "fc.mode_frag_glow",
  "kind": "image",
  "z": 10,
  "visible_default": true,
  "asset": "ui/x_ui_modetab_off.png",
  "x": 254,
  "y": 25,
  "w": 180,
  "h": 60,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-05 · E1）：`ui/x_ui_modetab_{off,over,press}.png` **180×60 RGBA ×3**（同一枚柔和白淡光的弱/强/实底三档）；**两个模式入口共用同一套 3 张**（形状一致，冻结 §D 允许复用、优先省件数）。",
  "note": "模式入口「番外故事」的**底光图**（三态承载者，与 `fc.mode_main_glow` 共用同一套 3 张素材）。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_frag`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。",
  "state_assets": {
   "normal": "ui/x_ui_modetab_off.png",
   "hover": "ui/x_ui_modetab_over.png",
   "pressed": "ui/x_ui_modetab_press.png"
  },
  "state_group": "mode_frag"
 },
 {
  "id": "fc.mode_frag_tx",
  "kind": "text",
  "z": 20,
  "visible_default": true,
  "x": 254,
  "y": 33,
  "w": 180,
  "h": 60,
  "font": {
   "size": 30,
   "bold": false,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "center",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "番外故事",
  "note": "★ **E5 订正（用户 2026-09-29 裁决 · 「两个模式入口的文字下移 8px」）**：本件 `y` **25 → 33**（口径与 `fc.mode_main_tx` 逐字段相同：`x/w/h`/`font`/`align`/`valign`/`wrap`/`max_lines`/`sample` 一字未动）。依据与判据见 `fc.mode_main_tx` 的 note（墨迹原 y31..63/中心 47 vs 框中心 55 ⇒ 下移 8px 后 y≈39..71、中心 55）。★ **`_glow`/`_hit` 仍是 `y25`**。\n· 模式入口「番外故事」的**文字**（引擎绘制；口径与 `fc.mode_main_tx` 逐字段相同，仅 `sample` 不同）。文字**不参与换态**。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_frag`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。"
 },
 {
  "id": "fc.mode_frag_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 254,
  "y": 25,
  "w": 180,
  "h": 60,
  "action": "flow_mode_frag",
  "label": "",
  "state_group": "mode_frag",
  "font": {
   "size": 30,
   "bold": false,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "模式入口「番外故事」的**热区**（同矩形 180×60 / z95；`state_group:\"mode_frag\"` 与同组 `_glow` 联动）。★ ISSUE-20260929-05 **本批新增**（2026-09-29 · 用户指令：流程图页第 ② 条）——**模式入口**：删 4 个 `fc.mtabx` 页签（序章/本篇/After Story/Fragment）后，在原「剧情流程图」按钮**上方**用**两枚文字入口**取代，只保留 **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。几何 `(x,25,180×60)`：60 高居中于旧页签带中线 55（占 25..85，与下方标题牌 y93 留 8px）；左沿沿用原「序章」页签 x34；两块等宽 180、间距 40（34+180+40=254）⇒ 满足「排版整齐、间距相等、高度 60px 左右」。\n· **三态口径（必读）**：`_off/_over/_press` 是**同一枚柔和白淡光**的弱/强/实底三档，三态**全靠这枚底光图**承载；`fc.mode_*_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**（悬停＝该按钮整体发亮）。\n· ⚠ **限制（不声称已实现）**：用户原话含「文字下移 1px」，但 schema 不支持文字逐态位移、`state_group` 只配对图片层 ⇒ **以「底沉 1px」等价表达「按进去」**（`_press` 图＝半透明冰蓝实底胶囊＋1px 亮边，且整体比 `_off/_over` 的底框下沉 1px）。**如需文字本体位移，须给引擎加「逐态位移」新接口（新裁决）**。\n· **动作** `flow_mode_frag`：**拟用名**（用户 2026-09-29 裁决）——**命中即派发**，切集/筛选行为**留编程组**（与 `flow_replay_toggle` 同口径）；已登记进 `layout\\_schema.md` §六 动作表。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（主干层与 6 个番外独立层的**共用舞台**，切层时照常绘制）。\n· **落盘前自检**：两枚入口**全部落进画布**、**彼此零重叠**、且与 `fc.titleplate` 等相邻件零重叠（实测统一间隙 8.0px / 与右栏 ≥990px）—— 见 `build()` 末尾的本批自检。"
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
  "x": 1425,
  "y": 534,
  "w": 422,
  "h": 73,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「标题」槽底（程序化 rect；`x1425 w422 h73` —— ★ 第 12 批起 `x/w` 取 PSB `#rects/text` 的取值，与说明/台词槽**逐字相同**）\n★ ISSUE-20260929-04 第 12 批（2026-09-29 · **用户指令 4**「`fc.p_title` 的宽度应该和下面两个 `fc.p_text_tx` 和 `fc.p_message_tx` 统一」）：`x` **1416 → 1425**、`w` **443 → 422**（口径 A「三槽底对齐」⇒ 与 `fc.p_text`/`fc.p_message` 的 `x/w` **逐字相同**；只动这一件，另两槽底一字不改）；`y`(534)/`h`(73)/`z`(6)/`color`/`opacity` 不变。旧值 **x1416 / w443 已作废**（那是 PSB `#rects/title` 的原值，本批按用户裁决让位给「三槽一致」）。\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 4**）：右栏重排为「① 大播放窗 ② 标题 ③ 说明 ④ 台词」四段 ⇒ 本件 `y` **214 → 536**。★ **第 3 轮（2026-09-29 · vision 复审后）**：四段改排「窗与三槽分离、三槽彼此紧凑」⇒ 本件 `y` **536 → 534**（第 2 段 y 区间 **534–607**；段间＝窗底 514 → 槽顶 534 ＝ **20px**）。起因：改前台词槽下沿 **995** 与「进入本章」按钮（`fc.jump`）上沿 **943** **竖直重叠 52px**（vision 实测按钮可见区 y953..996 落在槽内）——那是该批把台词槽从 PSB 的 `y750` 移到 `y824` 引进的，该轮收口。改前的「y214 / y536」两值均已作废。"
 },
 {
  "id": "fc.p_title_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1437,
  "y": 544,
  "w": 398,
  "h": 40,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "标题",
  "note": "「标题」标签（引擎绘制）\n★ ISSUE-20260929-04 第 12 批（2026-09-29 · **用户指令 4**）：随 `fc.p_title` 的三槽对齐 ⇒ `x` **1428 → 1437**、`w` **419 → 398**（与 `fc.p_text_tx`/`fc.p_message_tx` 的 `x/w` **逐字相同**）；`y`(544)/`h`(40)/`align`(left)/`valign`(middle)/`wrap`(false)/`max_lines`(1)/`font`（白字黑描边 2px）**一律不变**。旧值 **x1428 / w419 已作废**。\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 1 / 4**）：① `font.color` `@palette.node_locked` → **`@palette.text_primary`**（白字）并增 `outline:true` / `outline_color:\"#000000\"` / `outline_width:2`（黑描边 2px；写法照 `layout\\screens\\10_dialog.json` 的 `dlg.text`，`shadow` **保持 `false`**）；② `y` **224 → 546**（`_tx` 比槽顶 +10）。字号 **24** / `bold:true` **未动**；本槽**不扩**：`h40` / `valign:\"middle\"` / `wrap:false` / `max_lines:1`。\n★ **第 3 轮（2026-09-29 · vision 复审后）**：随 `fc.p_title` 的 `y 536 → 534` 同步上移 ⇒ `y` **546 → 544**（**仍 `y = 槽顶 + 10`**，槽内 544–584 完整落在 `fc.p_title` 的 534–607 内）。改前的「y224 / y546」两值均已作废。"
 },
 {
  "id": "fc.p_text",
  "kind": "rect",
  "z": 6,
  "visible_default": true,
  "x": 1425,
  "y": 617,
  "w": 422,
  "h": 150,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「说明」槽底（程序化 rect；`x1425 w422` 沿用 PSB `#rects/text`）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 4**）：四段重排 ⇒ 本件 `y` **309 → 631**。`x`/`w` 沿 PSB 原样。\n★ **第 3 轮（2026-09-29 · vision 复审后）**：三槽高度 **171 → 150** 并重排为「三槽彼此紧凑」⇒ 本件 `y` **631 → 617**、`h` **171 → 150**（第 3 段 y 区间 **617–767**；段间＝标题底 607 → 说明槽顶 617 ＝ **10px**）。改前的「y309 / y631」及 `h171` 均已作废。"
 },
 {
  "id": "fc.p_text_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1437,
  "y": 623,
  "w": 300,
  "h": 138,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "left",
  "valign": "top",
  "wrap": true,
  "max_lines": 4,
  "sample": "说明",
  "note": "「说明」标签（引擎绘制）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 1 / 4**）：① 同 `fc.p_title_tx` —— 白字 `@palette.text_primary` + 黑描边 2px（`outline:true` / `outline_color:\"#000000\"` / `outline_width:2`，写法照 `10_dialog.json` 的 `dlg.text`；`shadow` 保持 `false`）；② 多行内容槽：`(1437,319,398,40)` → **`(1437,637,398,159)`**、`valign` `middle` → **`top`**、`wrap` `false` → **`true`**；`x`/`w` 未动；字号 24 / `bold:true` **未动**。\n★ **第 3 轮（2026-09-29 · vision 复审后）—— 几何与容量双口径核算**：随三槽收高 ⇒ **`y` 637 → 623、`h` 159 → 138**（槽内 623–761 落在 `fc.p_text` 的 617–767 内）。\n  · **`max_lines` 仍写 4**（不变）。按 **138** 盒高重算：**krkr 口径** 行盒 ＝ `floor(24 × 全局 `line_spacing.body` 1.4)` ＝ **33px**（`krkr/game/ui_theme.tjs` 的 `uiThemeApplyFont`：`lineH = Math.floor(size × uiThemeElementSpacing(el))`，元素级 `line_spacing` 未写 ⇒ 走全局；`layout/_root.json` 的 `fonts.line_spacing.body = 1.4`）⇒ 138 ÷ 33 ＝ **4.18 ⇒ 4 行**；4 行块高 **132 ≤ 138 ✓**、5 行 **165 > 138 ✗**。\n  · **HTML 口径** 行盒 ＝ `font.size × line_spacing` ＝ 24 × 1.4 ＝ **33.6px**（`复刻/replica.js` 的 `buildText`：`var lh = size * lineSpacing(...)`，不取整）；按**保守取整口径** `Math.round(24 × 1.4) = 34` 算 ⇒ 4 × 34 ＝ **136 ≤ 138 ✓**（**余 2px**）。\n  ⇒ 双口径都过「4 行块高 ≤ 盒高」，故 `max_lines` **仍为 4**。**不加**元素级 `line_spacing`（保持全局基线 1.4）。改前的「319/637/159 与 159 ÷ 33 ＝ 4.82」整套算式**已作废**。\n★★ **ISSUE-20260930-02 第 15 批（2026-09-30）**：`w` **398 → 300**（**x 1437 / y 623 / h 138 不变**；其余字段一字不改）。起因＝用户裁定在「说明」框内**右上角新增一枚加号按钮** `fc.p_plus`（44×44 @1803,625）⇒ 文字槽**相应收窄**让位。**为何是 300 而不是冻结书初稿的 344**：引擎折行的**行首禁则**会把禁则字符**强行并入本行** ⇒ **行墨迹可以超过槽宽**（本工程既有记载：240px 盒内可达 247px）；M4 几何定标（`复现脚本/m57_intro_fit.py`，真实语料 1199 条）逐档实测「槽宽 + 最大超宽」：300px 档最大墨迹 **336.0px** ≤ 可用上限 **354px** ✓（344 档 384px ✗）；可用上限 ＝ 文字左沿 1437 → 按钮左沿 1803 共 366px、取 12px 安全间隙 ⇒ 354px。故终定 **300**，文字右缘 1737 与按钮左沿 1803 留 **66px**。★ **超框即省略号**（冻结书 §五）：末行尾部接 `……`（两个 U+2026）、纯渲染不参与布局 —— 契约条款见 `layout\\_schema.md` §六 与 `流程图系统_版式规范.md`。"
 },
 {
  "id": "fc.p_message",
  "kind": "rect",
  "z": 6,
  "visible_default": true,
  "x": 1425,
  "y": 777,
  "w": 422,
  "h": 150,
  "color": "@palette.panel_edge",
  "opacity": 35,
  "note": "右栏「台词」槽底（程序化 rect；`x1425 w422` 沿用 PSB `#rects/message`）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 4**）：四段重排 ⇒ 本件 `y` **750 → 824**。`x`/`w` 沿 PSB 原样。\n★ **第 3 轮（2026-09-29 · vision 复审后 · 本轮的起因件）**：三槽收高并重排 ⇒ 本件 `y` **824 → 777**、`h` **171 → 150**（第 4 段 y 区间 **777–927**；段间＝说明槽底 767 → 台词槽顶 777 ＝ **10px**）。\n  · **改前的真缺陷（已修）**：`y824 h171` ⇒ 槽下沿 **995**，与「进入本章」按钮 `fc.jump`/`fc.jump_tx`/`fc.jump_hit` 的 `(1474,943,328,61)` 上沿 **943** **竖直重叠 52px**（vision 实测按钮可见区 x1482..1800 / y953..996 落在槽内）。\n  · **改后**：本槽下沿 **927** → 按钮上沿 **943** ＝ **16px 间隙（无重叠）**；按钮下沿 1004 → 栏底 `fc.smallmap`（1416,190,443×829）下沿 1019 ＝ **余 15px**。\n  · 改前的「y750 / y824」两值均已作废。"
 },
 {
  "id": "fc.p_message_tx",
  "kind": "text",
  "z": 25,
  "visible_default": true,
  "x": 1437,
  "y": 783,
  "w": 398,
  "h": 138,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "left",
  "valign": "top",
  "wrap": true,
  "max_lines": 4,
  "sample": "台词",
  "note": "「台词」标签（引擎绘制）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 1 / 4**）：① 同 `fc.p_title_tx` —— 白字 `@palette.text_primary` + 黑描边 2px（`outline:true` / `outline_color:\"#000000\"` / `outline_width:2`，写法照 `10_dialog.json` 的 `dlg.text`；`shadow` 保持 `false`）；② 多行内容槽：`(1437,760,398,40)` → **`(1437,830,398,159)`**、`valign` `middle` → **`top`**、`wrap` `false` → **`true`**；`x`/`w` 未动；字号 24 / `bold:true` **未动**。\n★ **第 3 轮（2026-09-29 · vision 复审后）—— 几何与容量双口径核算**：随三槽收高 ⇒ **`y` 830 → 783、`h` 159 → 138**（槽内 783–921 落在 `fc.p_message` 的 777–927 内）。\n  · **`max_lines` 仍写 4**（不变）。按 **138** 盒高重算：**krkr 口径** 行盒 ＝ `floor(24 × 全局 `line_spacing.body` 1.4)` ＝ **33px** ⇒ 138 ÷ 33 ＝ **4.18 ⇒ 4 行**；4 行块高 **132 ≤ 138 ✓**、5 行 **165 > 138 ✗**。\n  · **HTML 口径** 行盒 ＝ 24 × 1.4 ＝ **33.6px**（保守取整 `Math.round(24 × 1.4) = 34`）⇒ 4 × 34 ＝ **136 ≤ 138 ✓**（**余 2px**）。\n  ⇒ 双口径都过，故 `max_lines` **仍为 4**；**不加**元素级 `line_spacing`。改前的「760/830/159 与 159 ÷ 33 ＝ 4.82」整套算式**已作废**。"
 },
 {
  "id": "fc.play_win",
  "kind": "image",
  "z": 6,
  "visible_default": true,
  "asset": "ui/x_ui_playwin_bg.png",
  "x": 1448,
  "y": 214,
  "w": 380,
  "h": 300,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-02 · 冻结 §A · 程序化合成，照 `ui/x_ui_replay_panel.png` 同一配方：霜白竖向渐变 + 2px 细蓝边 + 外沿柔光 + 上沿内侧白高光带）：`ui/x_ui_playwin_bg.png` **380×300**（盘面上**不烘焙任何文字**）。旧回放窗底板 `ui/x_ui_replay_panel.png`（426×241）的**元素**已随本批退场，**素材文件保留**（冻结 §E：只删元素、不删图）。",
  "note": "★ ISSUE-20260929-02 **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 2**）：**大播放窗底板**。\n· **取代**（本批已退场）：8 张缩略图 `fc.mini1..8` + 缩略图可视区框 `fc.mapview`（迷你地图组）＋ 场景回放组的 `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx`（回放窗底板元素）。\n· 用途：运行期由编程组在该窗内**按顺序播放该章节的游戏内画面**（画面层＝ `fc.play_view`，`dynamic:\"flow_scene_frames\"`）。\n· 几何 `1448,214,380,300`：**与旧 `fc.mapview` 同尺寸（380×300）**，在 443 宽的栏底 `fc.smallmap`（1416,190,443×829）内**居中** ⇒ `x = 1416 + ceil((443 − 380)/2) = 1416 + 32 = 1448`（左留 32 / 右留 31）；`y=214` ＝ 四段第 1 段顶（栏内上边距 24）。\n· `z=6`（与三个槽底同档、在 `fc.smallmap` z5 之上；画面层 `fc.play_view` z7）。380×300 与素材**等尺寸 ⇒ 1:1、不加 `nine`**。\n· 旧描述「右栏详情 / 迷你地图 / 回放窗底板」等一律作废（本件是新族，不复用旧 id）。"
 },
 {
  "id": "fc.play_view",
  "kind": "image",
  "z": 7,
  "visible_default": true,
  "asset": null,
  "dynamic": "flow_scene_frames",
  "x": 1454,
  "y": 220,
  "w": 368,
  "h": 288,
  "opacity": 255,
  "note": "★ ISSUE-20260929-02 **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 2**）：**大播放窗的画面层**。\n· `asset:null` + `dynamic:\"flow_scene_frames\"` ⇒ 运行期由编程组按顺序填入该章节的游戏内画面；**未填充时两端必须画占位底色**（`layout\\_schema.md` §四 `dynamic` 条，**不得跳过**；写法照 `10_dialog.json` 的 `dlg.content`）。\n· 几何＝底板内缩 6px：`(1448+6, 214+6, 380−12, 300−12)` = **`(1454,220,368,288)`**；`z=7` ＝ `fc.play_win` z6 + 1。\n· ★ **窗为 380×300（≈1.267:1），16:9 画面需 `contain` 居中适配、上下留边**（**不拉伸、不裁切**；画面时序/帧序列接线留编程组）。"
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
  "asset": "ui/x_ui_zoom_handle.png",
  "x": 1174,
  "y": 112,
  "w": 40,
  "h": 31,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-04 · 冻结 §A）：`krkr/assets/ui/x_ui_zoom_handle.png` **40×31 RGBA** —— 单一**竖圆角胶囊手柄**（条宽 12 / 条高 27 / 圆角 6 / 画布居中：左右各 14、上下各 2；霜白竖向渐变 `#F7FBFF`→`#DEEBFA` + 冰蓝 1.5px 描边 + 外沿柔光，真 alpha；配方照 `ui/x_ui_shift_knob.png` 同族）。旧件 `ui/x_ui_zoom_knob.png`（29×16）**已退役、文件保留不删**。",
  "note": "缩放条滑块（PSB `zoom/slider` x1174 y112 w40 h31）\n★ ISSUE-20260929-04（2026-09-29 · **用户指令 1**「`fc.zoom_knob` 作为滑块，应该是一个指针形状，而不是现在的两个不明物体形状」）：\n· `asset` **`ui/x_ui_zoom_knob.png` → `ui/x_ui_zoom_handle.png`**，并**删 `nine`**。\n· **旧件为何是「两个不明物体」**：`x_ui_zoom_knob.png` 实测 **29×16**、可见 bbox (0,0)-(28,10)、α>8 像素仅 **159** —— 里面是**横胶囊（轨道片）＋圆点（滑标）两个图形**（AI 拆件把 `FC-3-4 缩放条滑块`那整张图里的轨道片与滑标圆点一起切入）；旧 `nine{'l':7,'t':4,'r':7,'b':4}` 把这两坨各自拉伸 ⟹ 实机上就是「两坨」。\n· **新件与元素等尺寸（40×31）⇒ 1:1、无 `nine`**（旧 `nine{'l':7,'t':4,'r':7,'b':4}` 系为旧素材的九宫格拉伸而设，**已作废**）。\n· `x/y/w/h`＝**(1174,112,40×31)**、`z:21`、`opacity:255` **一律不变**。\n· 旧描述「（素材 29×16 ≠ 设计 40×31 → nine {'l': 7, 't': 4, 'r': 7, 'b': 4}）」为**改前**值，已作废。"
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
  "id": "fc.pbkick",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "vis_flag": "fc_replay",
  "vis_when": "play",
  "asset": "ui/x_ui_pbkick_off.png",
  "x": 1578,
  "y": 304,
  "w": 119,
  "h": 119,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260928-02 · C 组 · `m55_make_flow_assets.py` 程序化合成）：`ui/x_ui_pbkick_{off,over,on}.png` 119×119 ×3（参照作 `res39/50/54/57/67/69`：off 圆环内 ▶、on 内 ■）。原素材为旧占位件 `ui/x_ui_branch_l.png`（分支底座，语义不符），已由本批替换。",
  "note": "**播放键**（大播放窗 380×300 中央的「播放」键；PSB 原字段名 `pbkick` 保留为 id）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 3**）：\n· ① 移到**大播放窗中央**：`(1576,555)` → **`(1578,304)`**（件中心 (1637.5,363.5) ＝ 窗中心；窗内水平居中）。\n· ② **与暂停键 `fc.pbkick_pause` 同位置、靠 `vis_flag:\"fc_replay\"` 互斥**：本件 `vis_when:\"play\"`、暂停键 `vis_when:\"pause\"`（屏级 flag 初值 `play` ⇒ 初始显示本件）；**同一时刻只有一个可见**（`layout\\_schema.md` §四 **铁律一**：只在状态上互斥的重叠件必须靠 flag，**不得靠 z 排序**）。\n· ③ 素材三态 `ui/x_ui_pbkick_{off,over,on}.png` 119×119 **不变**（1:1、无 `nine`）；`visible_default` **保持 `true`**（判定语义的前置条件，写 `false` 即死件）。\n· ④ 视觉与命中由 `fc.pbkick_hit`（共同热区）派发 **`flow_replay_toggle`** 承担。\n· ⑤ 本件是**外壳件**、且是本批**唯一获批带 `vis_flag` 的外壳件**（具名豁免集 `STATIC_FLAG_EXEMPT`）：`fc_replay` **不是层旗标**，其初值 `\"play\"` 在**任何层**都成立 ⇒ 播放键恒可见，「切层丢外壳」这条禁令要防的风险**不存在**（冻结 §B.6）。\n★ 旧 note 的「x1576 y555 / 场景回放键」为**改前**值，已作废。",
  "state_assets": {
   "normal": "ui/x_ui_pbkick_off.png",
   "hover": "ui/x_ui_pbkick_over.png",
   "pressed": "ui/x_ui_pbkick_on.png"
  }
 },
 {
  "id": "fc.pbkick_pause",
  "kind": "image",
  "z": 20,
  "visible_default": true,
  "vis_flag": "fc_replay",
  "vis_when": "pause",
  "asset": "ui/x_ui_pbkick_pause_off.png",
  "x": 1578,
  "y": 304,
  "w": 119,
  "h": 119,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260929-02 · 冻结 §A.1「派生版」）：复用 `m55_make_flow_assets.py` 的 `pbkick_base(state)` **只替换字形掩膜**（两条圆角竖条 ‖，高 54 / 圆角 2 / 条宽 16 间隙 16）⇒ 盘面（外发光 + 盘体 + 环）与**同态播放键逐像素相同**：`ui/x_ui_pbkick_pause_{off,over,on}.png` 119×119 ×3（PNG-32 真 alpha）。另出的 AI 版暂停键落 `_工作\\ISSUE-20260929-02_右栏大改\\暂停键_AI版\\`、**不接线**，等用户二选一。",
  "note": "★ ISSUE-20260929-02 **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 3**）：**暂停键**（用户说的「停止键（竖着的两条线）」按术语对齐 ＝ **暂停 ⏸**）。\n· 与 `fc.pbkick`（播放键）**同位置、互斥显示**：本件 `vis_when:\"pause\"`、播放键 `vis_when:\"play\"`（同一对屏级 flag **`fc_replay`**）⇒ **同一时刻只有一个可见**（铁律一：靠 flag，不靠 z）。\n· 几何与播放键**逐字段相同**：`(1578,304,119,119)`、`z=20`。\n· 三态素材 `ui/x_ui_pbkick_pause_{off,over,on}.png` **119×119 ＝ 元素等尺寸 ⇒ 1:1、无 `nine`**；`visible_default:true`（铁律：靠 flag 控显隐的元素写 `false` 会成死件）。\n· 本件是**外壳件**、与播放键同在豁免集 `STATIC_FLAG_EXEMPT`（理由见冻结 §B.6）。\n· 命中与派发走**共同热区** `fc.pbkick_hit`（两键同位置 ⇒ 一条热区即够）。",
  "state_assets": {
   "normal": "ui/x_ui_pbkick_pause_off.png",
   "hover": "ui/x_ui_pbkick_pause_over.png",
   "pressed": "ui/x_ui_pbkick_pause_on.png"
  }
 },
 {
  "id": "fc.pbkick_hit",
  "kind": "hit",
  "z": 95,
  "visible_default": true,
  "x": 1575,
  "y": 301,
  "w": 125,
  "h": 125,
  "action": "flow_replay_toggle",
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
  "note": "播放/暂停键的**共同热区**（覆盖两键同一位置，外边各扩 3px）\n★ ISSUE-20260929-02（2026-09-29 · **用户指令 3** · 冻结 §B.5）：\n· ① 随播放键移到**大播放窗中央**：`(1573,552,125,125)` → **`(1575,301,125,125)`**（件中心 (1637.5,363.5) ＝ 窗中心）。\n· ② `action` 由**空串** → **`\"flow_replay_toggle\"`**：语义＝「播放/暂停切换」，**命中即派发**；**播放本身（画面时序、帧序列）接线留编程组**（与 `bgm_playpause` ／ `replay_play:<行号>` 同口径，**不得声称已生效**）。该动作名登记进 `layout\\_schema.md` §六 动作表与 `UI组\\UI组交接编程组.md`（由主代理/E3 落实）。\n· ③ 两键**同位置互斥** ⇒ **一条热区即够**（勿按可见键拆成两条；两态都不会漏掉命中）。\n· `z=95`（高于两键 z20）。旧 note 的「场景回放热区 / 无 action」已作废。"
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
  "id": "fc.p_plus",
  "kind": "image",
  "z": 27,
  "visible_default": true,
  "asset": "ui/x_ui_plusbtn_off.png",
  "x": 1803,
  "y": 618,
  "w": 44,
  "h": 44,
  "opacity": 255,
  "source": "素材组产出（ISSUE-20260930-02 第 15 批 · `_工作\\ISSUE-20260930-02_章节详情\\复现脚本\\m56_make_plusbtn_assets.py`）：`ui/x_ui_plusbtn_{off,over,press}.png` **44×44 RGBA ×3**（真 alpha、四角 α=0；风格/配色对齐 `fc.pbkick`：近白盘 ＋ **外圈环按目标尺寸 1:1 直绘、取 pbkick off 环色 (146,159,183)@α255**（over/press 按族规用 ACCENT 环）＋ **族内字形色 `#A7CBF1`「+」（按下态转白）**；`over` 整体提亮、`press` 实底并整体下沉 1px）。",
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.1）：**「说明」槽内右上角的加号按钮**（用户裁定 1「加号按钮怎么做」→ 新做一枚 44×44 三态小徽章）。\n· 几何 `(1803,618,44×44)`：**右缘 1847 ＝ 面板 `fc.p_text`（1425,617,422×150）右缘 1847**；**上缘 618**（★ 第 2 轮订正：由 625 上移到 618 —— 用户裁定 7「垂直对齐到首行行盒中心」；依据见冻结书 §三.1 注：按**墨迹中心** 633 对齐会把按钮顶出面板上缘 617 ⇒ 取排版学正解＝对齐首行**行盒**中心 `639.5 − 22 = 617.5 → 618`，实移 7px；按钮 y 区间 618–662 **完整落在**面板 617–767 内）。与文字槽 `fc.p_text_tx`（右缘 1737）留 **66px** ⇒ **零重叠**（由 `intro_overlay_violations()` 落盘前断言）。\n· **三态**：`asset`＝`state_assets.normal`＝`ui/x_ui_plusbtn_off.png`；`state_assets{normal,over,pressed}` 三态齐、**与元素等尺寸 44×44 ⇒ 1:1、无 `nine`**；`state_group:\"p_plus\"`（与同组热区 `fc.p_plus_hit` 配对，指针落在热区即点亮本件三态）。\n· `z=27`（在右栏三 `_tx` 的 z25 之上、热区 z96 之下）。\n· 命中与派发走 `fc.p_plus_hit`（同矩形）⇒ 动作 **`flow_intro_open`**。\n· 本件是**外壳件**（前缀不在 `LAYER_OWNED_PREFIXES` 内）⇒ **不写 `vis_flag`/`vis_when`**（常驻右栏）。",
  "state_assets": {
   "normal": "ui/x_ui_plusbtn_off.png",
   "hover": "ui/x_ui_plusbtn_over.png",
   "pressed": "ui/x_ui_plusbtn_press.png"
  },
  "state_group": "p_plus"
 },
 {
  "id": "fc.p_plus_hit",
  "kind": "hit",
  "z": 96,
  "visible_default": true,
  "x": 1803,
  "y": 618,
  "w": 44,
  "h": 44,
  "action": "flow_intro_open",
  "label": "",
  "state_group": "p_plus",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.1）：加号按钮 `fc.p_plus` 的**热区**（与按钮**同矩形** 44×44 @1803,618）。\n· `action:\"flow_intro_open\"`（★ 冻结 §四：**两端本批实现** —— 命中即把屏级 flag `fc_intro` 置 `\"open\"` 显示详情浮层，纯 flag 翻转、与 `flow_replay_toggle` 同口径；**简介全文与标题的取数留编程组**）。\n· `state_group:\"p_plus\"` 与同组按钮配对（悬停/按下点亮按钮三态）。\n· `z=96`：本屏非浮层热区中最高（既有节点/入口/关闭/进入本章/播放键/模式入口皆 z=95）⇒ 按钮与文字槽虽有 66px 间隙，指针落点仍由本热区胜出。\n· ★ 第 2 轮：y 625 → **618**（随按钮上移，仍同矩形）。"
 },
 {
  "id": "fc.intro_scrim",
  "kind": "rect",
  "z": 200,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 0,
  "y": 0,
  "w": 1920,
  "h": 1080,
  "color": "#000000",
  "opacity": 150,
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：详情浮层的**整屏压暗淡幕**。\n· 满幅 `(0,0,1920×1080)`、`color:#000000`、`opacity:150`、`z=200`（浮层组最低 ⇒ 压在一切既有元素之上、在面板之下）。\n· `vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"` ⇒ **仅当屏级 flag `fc_intro==\"open\"` 时可见**（初值 `\"closed\"` ⇒ 进屏不显示）。\n· 它是**外壳件**且带非层旗标 ⇒ 列入具名豁免集 `STATIC_FLAG_EXEMPT`（理由同 `fc.pbkick`：`fc_intro` 不参与 `fc_layer` 切层）。"
 },
 {
  "id": "fc.intro_scrim_hit",
  "kind": "hit",
  "z": 210,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 0,
  "y": 0,
  "w": 1920,
  "h": 1080,
  "action": "flow_intro_close",
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
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：压暗淡幕的**热区**（满幅 `1920×1080`）。\n· `action:\"flow_intro_close\"`（★ 冻结 §四：**两端本批实现** —— 命中即把 `fc_intro` 置回 `\"closed\"`，＝**点浮层之外回主页**，纯 flag 翻转）。\n· `z=210`：本件低于面板热区 `fc.intro_panel_hit`（z230）⇒ 点面板内由面板热区（**空动作 = 吞掉点击**）胜出、**不关闭**；点面板外由本件胜出 ⇒ 关闭。"
 },
 {
  "id": "fc.intro_bg",
  "kind": "image",
  "z": 220,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "asset": "ui/x_ui_gal_cell_on.png",
  "x": 340,
  "y": 340,
  "w": 1240,
  "h": 400,
  "opacity": 255,
  "source": "既有素材（M34 PSB 复刻件，**本批不新出**）：`ui/x_ui_gal_cell_on.png` 291×166 RGBA —— 观览/展厅单元底（「详情面板」底材，冻结 §三.2 指定复用）。",
  "nine": {
   "l": 4,
   "t": 4,
   "r": 4,
   "b": 4
  },
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：详情浮层的**面板底**。\n· 几何 `(340,340,1240×400)` —— ★ **第 2 轮订正（用户裁定 6「浮层尺寸改 1240×400」）**：由 1240×652 @340,214 改为 **1240×400 @340,340**（**版面中心**：右缘 1580 = 左缘 340 + 1240、下缘 740；中心 (960,540) = 画布中心）。起因＝vision 实测正文仅占面板 ~1.5%、观感像未完成。素材 `ui/x_ui_gal_cell_on.png`（**291×166 RGBA**，既有件，不新出）。\n· **`nine:{l:4,t:4,r:4,b:4}`**：源件实测结构 ＝ **方角**、外侧 **2px 硬边 `#7AB0E8`（＝ `palette.accent`）** ＋ 内侧 **2px 渐变过渡**、内部纯色 **`#324862` α≈248** ⇒ 取 4 可把「硬边 ＋ 渐变」**全部 1:1 保真**，九宫格拉大**不使边框变形**。\n· `z=220`（在压暗 200 之上、两个 `_tx` z235 与关闭件 z236/237 之下）。\n· `vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 },
 {
  "id": "fc.intro_panel_hit",
  "kind": "hit",
  "z": 230,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 340,
  "y": 340,
  "w": 1240,
  "h": 400,
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
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：面板的**热区**（与 `fc.intro_bg` 同矩形 `(340,340,1240×400)`）。\n· **`action:\"\"`（空动作）＝吞掉点击** ⇒ 点面板内**不关闭**浮层（`z=230` 高于压暗热区 z210 ⇒ 面板区域内由本件胜出）。\n· ★ 第 2 轮：几何随 `fc.intro_bg` 由 1240×652 @340,214 改为 **1240×400 @340,340**；**`z=230` 不动**——它是「关闭件 z 必须高于它」这条**新断言**（用户裁定 5 的硬前提）的基准件。\n· `vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 },
 {
  "id": "fc.intro_title_tx",
  "kind": "text",
  "z": 235,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 372,
  "y": 372,
  "w": 1140,
  "h": 44,
  "font": {
   "size": 24,
   "bold": true,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "left",
  "valign": "middle",
  "wrap": false,
  "max_lines": 1,
  "sample": "章节标题",
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：详情浮层的**章节标题**（一行）。\n· 几何 `(372,372,1140×44)` —— ★ **第 2 轮订正（用户裁定 6）**：由 `1176×44 @372,246` 改为 `1140×44 @372,372`（面板 340,340,1240×400 内缩：左/上各 32px；**宽由 1176 收到 1140 给关闭件让位** ⇒ 右缘 1512 与关闭件左沿 1530 留 **18px**）；`sample:\"章节标题\"`（**占位**，运行期由编程组按 `场景id` 取数填充 —— 冻结 §四「简介全文与标题的取数留编程组」）。\n· 24px / **`bold:true`**（与右栏「标题」一致）/ `@palette.text_primary`（白字）＋ **黑描边 2px**（`outline:true`/`#000000`/宽 2，写法照 `10_dialog.json` 的 `dlg.text`）；`align:left`/`valign:middle`/`wrap:false`/`max_lines:1`。\n· 冻结 §七 待确认 1：浮层**正文**的字重取 `bold:false`（正文更耐读），**标题**取 `bold:true`；若用户要求与右栏统一加粗，改一处字段即可。\n· `z=235`；`vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 },
 {
  "id": "fc.intro_text_tx",
  "kind": "text",
  "z": 235,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 372,
  "y": 432,
  "w": 1176,
  "h": 276,
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.text_primary",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0,
   "outline": true,
   "outline_color": "#000000",
   "outline_width": 2
  },
  "align": "left",
  "valign": "top",
  "wrap": true,
  "max_lines": 6,
  "sample": "章节简介全文",
  "note": "★★ ISSUE-20260930-02 第 15 批 **新增**（2026-09-30 · 冻结书 §三.2）：详情浮层的**简介全文**（多行）。\n· 几何 `(372,432,1176×276)` —— ★ **第 2 轮订正（用户裁定 6）**：由 `1176×528 @372,306` 改为 `1176×276 @372,432`（标题之下：y 432 ＝ 标题底 416 + 16px；**面板底 740 − 32 留白 = 708** ⇒ h 276；右/下各内缩 32px ⇒ 右缘 1548、下缘 708，均完整落在面板 340,340,1240×400 内）；`sample:\"章节简介全文\"`（**占位**，运行期由编程组按 `场景id` 取数填充）。\n· 24px / **`bold:false`**（段落可读性，见 §七 待确认 1）/ 白字 ＋ **黑描边 2px**；`align:left`/`valign:top`/`wrap:true`/**`max_lines:6`**。\n· **容量依据（M4 实测，真实语料 1199 条）**：1176px × 6 行 ⇒ 自然折行最大 **3 行**、**截断 0 条** ⇒ 该槽确实能看全文（最长 132 字）。6 行 × 行盒 33px ＝ 198 ≤ 276（余 78px）。\n· **超框即省略号**（冻结书 §五）：若日后语料变长导致超 6 行，末行接 `……`（纯渲染、不参与布局）。\n· `z=235`；`vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 },
 {
  "id": "fc.intro_close",
  "kind": "image",
  "z": 236,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "asset": "ui/x_ui_close_off.png",
  "x": 1530,
  "y": 364,
  "w": 26,
  "h": 26,
  "opacity": 255,
  "source": "既有素材（**零新素材**，用户裁定 5「复用既有 `x_ui_close_*`」）：`ui/x_ui_close_off.png` / `_over.png` / `_on.png` —— 与 `fc.close` **同一套三态图**（本屏标题牌右侧关闭键的素材），本批不新出、不改动。",
  "nine": {
   "l": 6,
   "t": 6,
   "r": 6,
   "b": 6
  },
  "note": "★★ ISSUE-20260930-02 第 15 批 · **第 2 轮新增**（2026-09-30 · 用户裁定 5「加一枚小 ×」：复用既有 `x_ui_close_*`、**零新素材**）＋ 冻结书 §三.2：详情浮层**右上角的关闭按钮**。\n· 几何 `(1530,364,26×26)`：右缘 **1556**（＝ 面板右缘 1580 − 24 内缩）、上缘 **364**（＝ 面板上缘 340 + 24），完整落在面板内；与标题槽 `fc.intro_title_tx`（右缘 1512）留 **18px**。\n· **三态与 `fc.close` 同用法**：`asset`＝`state_assets.normal`＝`ui/x_ui_close_off.png`；`state_assets{normal,over,pressed}` → `_off`/`_over`/`_on`；`state_group:\"intro_close\"`（与同组热区 `fc.intro_close_hit` 配对，指针落在热区即点亮本件三态）。\n· ⚠ **必须带 `nine{l:6,t:6,r:6,b:6}`（与 `fc.close` 逐字相同）**：素材 `x_ui_close_off.png` 实为 **24×26**（`_over` 30×32 / `_on` 36×38），而 `工具/verify_ui.py` 的 [2] 判据是「`kind=image` 且**无** `nine` ⇒ w/h 必须**等于** PNG 实尺寸」⇒ 不写 `nine` 会假失败。★ **这一处与冻结书 §三.2 表内「无 `nine`」不一致，已在交付报告中上报主代理**（该表同段又写「与 `fc.close` 同用法」，而 `fc.close` 正带 `nine{6,6,6,6}`；`fc.close` 的 26×26 也是靠它撑住的）。\n· **`z=236`**：**必须高于** `fc.intro_panel_hit`（z230），否则点击会被面板的「空动作＝吞点击」吃掉（冻结 §三.2 硬约束）。\n· `vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 },
 {
  "id": "fc.intro_close_hit",
  "kind": "hit",
  "z": 237,
  "visible_default": true,
  "vis_flag": "fc_intro",
  "vis_when": "open",
  "x": 1520,
  "y": 354,
  "w": 46,
  "h": 46,
  "action": "flow_intro_close",
  "label": "",
  "state_group": "intro_close",
  "font": {
   "size": 24,
   "bold": false,
   "color": "@palette.node_locked",
   "shadow": false,
   "shadow_color": "@palette.shadow",
   "shadow_ofs": 0
  },
  "align": "center",
  "note": "★★ ISSUE-20260930-02 第 15 批 · **第 2 轮新增**（2026-09-30 · 用户裁定 5 ＋ 冻结书 §三.2）：关闭按钮 `fc.intro_close` 的**热区**（图标外扩 10px 便于点按 ⇒ 26+2×10 = 46×46 @1520,354；热区中心 (1543,377) ＝ 图标中心）。\n· `action:\"flow_intro_close\"` —— 与遮罩热区 `fc.intro_scrim_hit` **同一动作** ⇒ 两条关闭路径（点 × ／ 点浮层之外）**共用语义**，纯 flag 翻转。\n· `state_group:\"intro_close\"` 与同组按钮配对（悬停/按下点亮三态）。\n· **`z=237`**：**必须高于** `fc.intro_panel_hit`（z230）—— 否则点关闭会被面板热区吞掉（**这是本件存在的唯一前提**，由 `intro_overlay_violations()` 的专条断言 ＋ `--selfcheck-intro-overlay` 变异 G 守住）。本件也是本屏**最高 z 的点击候选**。\n· `vis_flag:\"fc_intro\"` ＋ `vis_when:\"open\"`；**外壳件** ⇒ 列入 `STATIC_FLAG_EXEMPT`。"
 }
]"""


# ══════════════════════════════════════════════════════════════════════
# ★ ISSUE-20260929-04 第 12 批：「系统共通条 `fc.sysbar`」**元素已删**（素材保留）
#   用户 2026-09-29 裁定：**删掉该元素**（`fc.sysbar` 是 `sysbar` 屏删除后留在流程图屏上的
#   遗留装饰条：无文字、无点击 —— `_hit` 不存在）。本次**只删元素**，素材
#   `krkr/assets/ui/x_ui_sysbar.png`（1946×292）**保留不删**（工程口径「旧素材一件不删」；
#   它同时被已删除的 `sysbar` 屏引用过，留作历史/复原依据）。
#   ⇒ 它已从本快照移除（不再出现在 `PASSTHROUGH_REQUIRED` 里）；原文描述
#   「系统共通条（PSB `システム共通` x1227 y32 w648 h41）（素材 1946×292 ≠ 设计 648×41 → nine 全零）」
#   **已作废**（该件不再产出）。
# ══════════════════════════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════════════════════════
# 超框省略号（ISSUE-20260930-02 · 第 15 批 · 冻结书 §五）—— **Python 侧唯一实现**
#   冻结书 §五 原文（逐字照此实现）：
#     1. 折行后若行数 > max_lines ⇒ **保留前 max_lines 行**，并在**最后一行尾部**追加 `……`；
#     2. 追加前先从末行**逐字回退**，直到 `宽度(末行 + "……") ≤ maxW`（预算规则与既有
#        `uiThemeEllipsize` 一致）；
#     3. 若连 `……` 本身都放不下（`maxW - 宽度("……") ≤ 0`）⇒ 与 `uiThemeEllipsize` 同口径：
#        **该行不画**（宁可少一行，也不许溢出）；
#     4. **纯渲染**，不参与布局（不改变行盒数量/位置，故既有排版判据不变）。
#   ★ 三处实现必须同判据：① 引擎 `krkr/game/ui_theme.tjs`；② HTML `复刻/replica.js`；
#     ③ 本函数（供 M4 全量语料实测）。本批把原先分叉的两份 Python 折算（`工具/test_text_ellipsis.py`
#     的内联 port 与 `_工作/ISSUE-20260930-02_章节详情/复现脚本/m57_intro_fit.py::ellipsize`）
#     **归并到这一个函数**（两处改为调用本函数，删除各自内联实现）。
#   ⚠ **不动 `ui_theme_wrap` 本体**：它被标题硬断行等既有逻辑复用，改它会让金标漂移。本函数是
#     **后处理**（吃折行结果、吐省略号收尾的折行结果），与折行算法解耦。
# ══════════════════════════════════════════════════════════════════════
ELLIPSIS_DOTS = "……"          # 两个 U+2026（冻结书 §一 裁定 4：**不得用 "..."**）


def apply_ellipsis(lines, maxW, maxLines, wof, dots=ELLIPSIS_DOTS):
    r"""超框省略号收尾（冻结书 §五 · 语义逐字）。返回 `(lines2, ellipsized, notes)`。

    · `lines`   —— **已折好**的行列表（调用方用各自口径折行，如 `ui_theme_wrap(text, maxW, 0, wof)`）；
    · `maxW`    —— 单行预算（该槽的可用宽度）；
    · `maxLines`—— 行数上限；`lines` 不超过它 ⇒ **原样返回、不动一行**；
    · `wof`     —— 字宽度量函数 `wof(str) -> float`；
    · `dots`    —— 省略号串（默认两个 U+2026）。
    · `notes`   —— 人读的规则说明（供 M4 报告与自检打印；无副作用）。

    逐字回退的判据 `while last and wof(last) + dw > maxW: last = last[:-1]` 与
    `uiThemeEllipsize` 同预算口径（末行 + `……` 的墨迹宽 ≤ maxW）。
    """
    notes = []
    if not (maxLines and maxLines > 0 and len(lines) > maxLines):
        return list(lines), False, notes
    kept = list(lines[:maxLines])
    dw = wof(dots)
    if maxW - dw <= 0:                       # ③ 连 `……` 都放不下 ⇒ 该行不画
        kept = kept[:-1]
        notes.append("连「%s」都放不下（maxW - 宽度 = %d - %.1f ≤ 0）⇒ 该行不画"
                     "（与 uiThemeEllipsize 同口径）" % (dots, maxW, dw))
        return kept, True, notes
    last = kept[-1]
    cut = 0
    while last and wof(last) + dw > maxW:    # ② 逐字回退
        last = last[:-1]
        cut += 1
    kept[-1] = last + dots
    notes.append("末行回退 %d 字后接「%s」（末行宽 %.1f ≤ %d）" % (cut, dots, wof(kept[-1]), maxW))
    return kept, True, notes


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


def selfcheck_mode_entries():
    r"""★ 第 13 批**变异自证**（内存构造，不落盘）：证明模式入口几何自检**非恒真**。

    做法：拿**盘上真实静态快照**（含 6 件 `fc.mode_*` 与 `fc.titleplate` 等邻居）跑四条对照：
      ① 正向：真数据 ⇒ 违规 0（现状成立）；
      ② 变异 A：把 `fc.mode_frag_*` 左移到 x=100（与 main 的 34..214 重叠）⇒ 必须报「彼此重叠」；
      ③ 变异 B：把 `fc.mode_main_*` 的 y 挪到 1080-60+10（出画布）⇒ 必须报「越出画布」；
      ④ 变异 C：把两枚入口挪到标题牌带上（y=93）⇒ 必须报「与相邻件 `fc.titleplate` 重叠」；
      ⑤ 变异 D（★ **E5 新增**）：把 `fc.mode_main_tx` 的 `y` 从 33 改回 25（＝取消文字下移 8px）
         ⇒ 必须报「`_tx` 矩形 ≠ 期望 …」—— 证明 **E5 新立的「`_tx` 固定下移 8px」判据非恒真**
         （否则「顺手把文字挪回/挪歪」无人拦）。
    四条变异各命中一条判据 ⇒ 「自检能失败」有实测证据（不是只写在注释里）。
    """
    import copy
    canvas = load_canvas()
    cw, ch = canvas["width"], canvas["height"]
    els = load_static_elements()
    ok = True
    v0 = mode_entry_violations(els, cw, ch)
    print("=" * 78)
    print("交付自检 · 变异自证（第 13 批「模式入口：画布内 + 与相邻件零重叠」，不落盘）")
    print("  ① 真数据：违规 **%d 条**%s" % (len(v0), " ✓" if not v0 else " ✗ " + str(v0)))
    ok = ok and (not v0)

    def _mut(tag, fn, want):
        nonlocal ok
        m = copy.deepcopy(els)
        fn(m)
        v = mode_entry_violations(m, cw, ch)
        hit = [x for x in v if want in x]
        print("  ② 变异 %s：违规 **%d 条**，其中命中「%s」**%d 条**%s"
              % (tag, len(v), want, len(hit), " ✓" if hit else " ✗ **未检出**（判据恒真）"))
        if not hit:
            ok = False

    def _move(g, dx=0, dy=0):
        def f(m):
            for s in MODE_ENTRY_SUFFIXES:
                e = next(x for x in m if x["id"] == "fc.%s_%s" % (g, s))
                e["x"] += dx
                e["y"] += dy
        return f

    def _move_tx_back(m):
        """★ E5 变异 D：把两件 `_tx` 的 y 变回 25（＝取消「文字下移 8px」）⇒ 必须被 `_tx` 判据抓住。"""
        for g in MODE_ENTRY_ORDER:
            e = next(x for x in m if x["id"] == "fc.%s_tx" % g)
            e["y"] = MODE_ENTRY_Y

    _mut("A（frag 组左移 ⇒ 与 main 重叠）", _move("mode_frag", dx=-154), "彼此重叠")
    _mut("B（main 组下移出画布）", _move("mode_main", dy=ch - MODE_ENTRY_Y - MODE_ENTRY_H + 10), "越出画布")
    _mut("C（两枚都挪到标题牌带上）",
         lambda m: (_move("mode_main", dy=93 - MODE_ENTRY_Y)(m),
                    _move("mode_frag", dx=-40, dy=93 - MODE_ENTRY_Y)(m)),
         "`fc.titleplate`")
    # ★ E5 新增：证明「`_tx` 固定下移 8px」这条新判据**非恒真**（把文字挪回 y25 必须被检出）。
    _mut("D（把 `_tx` 的文字下移取消 ⇒ 挪回 y25）", _move_tx_back, "`_tx` 矩形")
    print("  自证结果：%s" % ("**按预期** ✓（真数据 0 违规；四条变异各被对应判据检出 ⇒ 非恒真）"
                             if ok else "**不符合预期** ✗"))
    return 0 if ok else 1


def selfcheck_intro_overlay():
    r"""★★ 第 15 批**变异自证**（内存构造，不落盘）：证明章节详情浮层几何自检**非恒真**。

    做法：拿**盘上真实静态快照**（含 8 件新件与 `fc.p_text`/`fc.p_text_tx` 等邻居）跑七条对照：
      ① 正向：真数据 ⇒ 违规 0（现状成立）；
      ② 变异 A：把 `fc.p_plus` 左移进文字区（与 `fc.p_text_tx` 重叠）⇒ 必须报「重叠」；
      ③ 变异 B：把**非浮层**热区 `fc.p_plus_hit` 抬到 z=240（高于浮层组）⇒ 必须报「≤ 本屏既有热区最高 z」；
      ④ 变异 C：把 `fc.intro_scrim_hit` 的 z 调到 100（**在热区之上、但不在浮层区间 200–235**）⇒ 必须报「不在浮层组区间」；
      ⑤ 变异 D：把 `fc.intro_text_tx` 下移出面板（`fc.intro_bg`）⇒ 必须报「未完整落在 `fc.intro_bg` 内」；
      ⑥ 变异 E：把 `fc.p_plus` 右移出说明面板（`fc.p_text`）⇒ 必须报「未完整落在…`fc.p_text` 内」；
      ⑦ 变异 F：把 `fc.p_plus_hit` 与按钮拆到不同矩形 ⇒ 必须报「热区与按钮必须同框」。
      ★★ 第 2 轮追加三条（用户裁定 5 的硬前提 ＋ 一审建议项「判据对齐引擎」）：
      ⑧ 变异 G：把 `fc.intro_close_hit` 的 z 降到 230（＝面板热区同一档）⇒ 必须报
         「未高于面板热区」；
      ⑨ 变异 H：把**非浮层**热区 `fc.p_plus_hit` 的 z 写成**字符串** `"250"` ⇒ 必须被检出
         （旧判据 `isinstance(z,int)` 会静默跳过 ⇒ 假绿；现按 `_z_num()` 数值化后必报）；
      ⑩ 变异 I：把 `fc.p_plus_hit` 的 `kind` 换成 `"list"`（引擎同样把它当点击候选）⇒ 必须被检出
         （旧判据只筛 `kind=="hit"` ⇒ 假绿；现按 `kind ∈ {hit,list}` 判）。

    九条变异各命中一条判据 ⇒ 「自检能失败」有实测证据（不是只写在注释里）。
    """
    import copy
    canvas = load_canvas()
    cw, ch = canvas["width"], canvas["height"]
    els = load_static_elements()
    ok = True
    v0 = intro_overlay_violations(els, cw, ch)
    print("=" * 78)
    print("交付自检 · 变异自证（第 15 批「章节详情：加号按钮 + 详情浮层」，不落盘）")
    print("  ① 真数据：违规 **%d 条**%s" % (len(v0), " ✓" if not v0 else " ✗ " + str(v0)))
    ok = ok and (not v0)

    def _mut(tag, fn, want):
        nonlocal ok
        m = copy.deepcopy(els)
        fn(m)
        v = intro_overlay_violations(m, cw, ch)
        hit = [x for x in v if want in x]
        print("  ② 变异 %s：违规 **%d 条**，其中命中「%s」**%d 条**%s"
              % (tag, len(v), want, len(hit), " ✓" if hit else " ✗ **未检出**（判据恒真）"))
        if not hit:
            ok = False

    def _set(eid, **kw):
        def f(m):
            e = next(x for x in m if x["id"] == eid)
            e.update(kw)
        return f

    # A：把按钮挪进文字区（x 落到文字槽 1437..1737 内）⇒ 与文字重叠（仍在面板内 ⇒ 触发重叠 + 热区不同框）
    _mut("A（`fc.p_plus` 挪进文字区 ⇒ 与 `fc.p_text_tx` 重叠）",
         _set(PLUS_ID, x=1500), "重叠")
    # B：把**非浮层**热区 `fc.p_plus_hit` 抬到 z=240（高于浮层组 200–235）⇒ 浮层不再压过全部热区。
    #    ★ 这条针对「别的批给某个非浮层 hit 加了高 z」这一类回归；与之互补的「浮层自身出区间」由
    #      变异 C 覆盖 —— 两条判据一内一外（区间内 z 序 / 区间本身），单向变异各只命中一条，**有意**。
    _mut("B（非浮层热区 `fc.p_plus_hit` 抬到 z=240 高于浮层）",
         _set(PLUS_HIT_ID, z=240), "≤ 本屏既有热区最高 z")
    # C：浮层热区 z=100 在热区之上、但不在浮层区间 200–235
    _mut("C（`fc.intro_scrim_hit` z=100 ∉ 200–235）",
         _set("fc.intro_scrim_hit", z=100), "不在浮层组区间")
    # D：正文下移出面板
    _mut("D（`fc.intro_text_tx` 下移出 `fc.intro_bg`）",
         _set("fc.intro_text_tx", y=1000), "`fc.intro_bg`")
    # E：按钮右移出说明面板
    _mut("E（`fc.p_plus` 右移出 `fc.p_text`）",
         _set(PLUS_ID, x=1900), "面板 `fc.p_text`")
    # F：拆散「热区与按钮同框」
    _mut("F（`fc.p_plus_hit` 与按钮不同框）",
         _set(PLUS_HIT_ID, y=700), "热区与按钮必须同框")
    # G（★ 第 2 轮 · 用户裁定 5 的硬前提）：关闭热区 z 降到面板热区同一档 ⇒ 点关闭会被面板吞掉。
    _mut("G（`fc.intro_close_hit` z 降到 230 ＝ 面板热区档）",
         _set("fc.intro_close_hit", z=230), "未高于")
    # H（★ 第 2 轮 · 一审建议项）：z 写成**字符串** —— 旧判据 `isinstance(z,int)` 会静默跳过。
    _mut("H（非浮层热区 `fc.p_plus_hit` 的 z 写成字符串 \"250\"）",
         _set(PLUS_HIT_ID, z="250"), "≤ 本屏既有热区最高 z")
    # I（★ 第 2 轮 · 一审建议项）：kind 换成 list（引擎同样把它当点击候选）**且** z 抬到 240
    #   —— 旧判据只筛 `kind=="hit"` ⇒ 该件被排除在「既有热区最高 z」之外 ⇒ 假绿。
    _mut("I（非浮层 `fc.p_plus_hit` 换 kind=\"list\" 且 z=240）",
         _set(PLUS_HIT_ID, kind="list", z=240), "≤ 本屏既有热区最高 z")
    print("  自证结果：%s" % ("**按预期** ✓（真数据 0 违规；九条变异各被对应判据检出 ⇒ 非恒真）"
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
def frag_rows(n):
    """独立层第 G 组的网格**行数**（★ 2026-09-30 · `ISSUE-20260930-06` 新口径）。

    行数 = ceil(n / FRAG_COLS)（n ＝ 该组章数）；**不设上限、不由视口派生**。
    几何不变：列 x ＝ 视口左 + FRAG_ORIGIN[0] + col×FRAG_STEP_X（**66 / 441 / 816**）；
    行 y ＝ 视口顶 + FRAG_ORIGIN[1] + FRAG_LEAD_Y + row×FRAG_STEP_Y（**286 / 478 / …**），格高 ＝ NODE_H。

    旧口径（`frag_grid_rows()`：「视口内可容 4 行 × 3 列 ＝ 12 格，组内超出者不产」）**已作废**
    —— 用户 2026-09-30 裁定 5「番外独立层改纵向流水、**组内全部产出**」（关闭缺口 G-3）。
    末行下沿可超出视口下沿（1017）、甚至画布（1080）：由**编程组的独立层纵滚**呈现；
    **未滚到位时该行不可见＝预期**，不得据此报「缺件」。
    """
    return (n + FRAG_COLS - 1) // FRAG_COLS


def frag_grid_cols(vp_x, vp_w):
    """图表视口内可容的独立层网格**列数**（冻结把列数收敛为 3 的依据；x 方向仍要求完整落视口）。"""
    n = 0
    while True:
        x = vp_x + FRAG_ORIGIN[0] + n * FRAG_STEP_X
        if x + NODE_W > vp_x + vp_w:
            return n
        n += 1


def frag_layer_rect_ok(x, y, w, h, vp):
    """★ 独立层元素的裁剪判据（**本批唯一的判据放松**）：`x` 完整落视口 **且** `y ≥ 视口顶`。

    ＝ **允许纵向溢出**（下沿可 > 视口底 1017、可 > 画布 1080）。**这是有意偏离** §九 裁决 5
    （「本屏全部产出元素必须整体落在图表视口内」），依据＝用户 2026-09-30 裁定 5
    「番外独立层改纵向流水、**组内全部产出**」＋ 裁定 3「右侧滑标＝纵滚（逻辑归编程组）」。
    `x` 判据**保留**是因为 3 列右沿 1112 < 视口右沿 1295（x 方向本就零冲突，侦察已逐矩形验证）。
    **主干节点不走本函数**（仍用 `inside()` 的「完整落视口」）；`--no-cull` 语义不变（只关主干那条）。
    """
    return (vp["x"] <= x and x + w <= vp["x"] + vp["w"] and y >= vp["y"])


def frag_capacity_report():
    r"""★ 番外独立层「组内全量产出」总账（`--frag-report`；只读、只打印，**不写任何文件**）。

    ★ 2026-09-30 改口径（`ISSUE-20260930-06`，用户裁定 5）：逐组报
    `章数 / rows / 可容(=rows×3) / 产出 / 未产` ⇒ **未产必须逐组为 0**；并报
    **虚拟内容高度**（首行 y → 末行下沿）与**需纵滚的行清单**（下沿 > 视口底的行）。
    旧口径（「独立层视口只容 4 行 × 3 列 ＝ 12 格，组内超出者本轮不产」）**已作废**。
    ★ **冻结 §7.2 追加（一审后返修）**：另报**默认可见格数 / 需纵滚置真格数** ——
    溢出行的三件写 `visible_default:false`（**数据完整、默认不画**）；「产出」列仍按**元素存在**计。
    """
    spine = load_spine()
    static = load_static_elements()
    vp = next(e for e in static if e["id"] == "fc.scroll")
    vpx, vpy, vpw, vph = vp["x"], vp["y"], vp["w"], vp["h"]
    oy = vpy + FRAG_ORIGIN[1] + FRAG_LEAD_Y
    vp_bottom = vpy + vph
    print("=" * 78)
    print("gen_flow_layout.py · --frag-report（★ 2026-09-30 纵向流水口径：**组内全量产出**）")
    print("  视口 fc.scroll = (%d,%d,%d,%d) ｜ 网格 %d 列（**行数按章数派生、不设上限**）"
          % (vpx, vpy, vpw, vph, FRAG_COLS))
    print("  几何：列 x = %d / %d / %d ｜ 行 y = %d + row×%d（行首 y = %d = 视口顶 +(%d,%d) + %d）"
          % (vpx + FRAG_ORIGIN[0], vpx + FRAG_ORIGIN[0] + FRAG_STEP_X,
             vpx + FRAG_ORIGIN[0] + 2 * FRAG_STEP_X, oy, FRAG_STEP_Y,
             oy, FRAG_ORIGIN[0], FRAG_ORIGIN[1], FRAG_LEAD_Y))
    print("  裁剪口径（**有意偏离** §九 裁决 5）：独立层元素只要求「x 完整落视口 且 y ≥ %d」"
          " ⇒ **允许纵向溢出**（视口底 %d / 画布 1080 均可越过；纵滚属编程组）" % (vpy, vp_bottom))
    print("  偏离登记：参照作 5 个/行（其视口更宽）；我方视口 %d 宽下 5×%d+4×79=1796 放不下 ⇒ 改 %d 个/行"
          % (vpw, NODE_W, FRAG_COLS))
    print("  ★ 冻结 §7.2 可见性契约：溢出视口底（y+h > %d）的行的**三件**一律 `visible_default:false`"
          "（**数据完整、默认不画**；纵滚到位时由编程组置真）——「产出」列按**元素存在**计，不受本契约影响"
          % vp_bottom)
    print("-" * 78)
    print("  %-3s %-34s %4s %5s %6s %6s %6s %6s %6s  %s"
          % ("G", "组名（group_cn）", "章数", "rows", "可容", "产出", "未产",
             "默认可见", "纵滚置真", "需纵滚的行（row y 下沿）"))
    tot_made = tot_n = tot_drop = tot_vis = tot_scr = 0
    max_rows = 0
    for gi, (group, grows) in enumerate(entry_groups(spine), 1):
        gcn, _src = group_cn(group)
        n = len(grows)
        rows = frag_rows(n)
        max_rows = max(max_rows, rows)
        cap = rows * FRAG_COLS
        made = grows[:cap]
        drop = [r.get("script") or r.get("scene_id") for r in grows[cap:]]
        # 可见性（冻结 §7.2）：按**格**（＝组内序 k 的所在行）判，与元素 `visible_default` 同算式
        n_vis = sum(1 for _k in range(len(made))
                    if (oy + (_k // FRAG_COLS) * FRAG_STEP_Y + NODE_H) <= vp_bottom)
        n_scr = len(made) - n_vis
        tot_made += len(made)
        tot_n += n
        tot_drop += len(drop)
        tot_vis += n_vis
        tot_scr += n_scr
        scr_rows = []
        for r_ in range(rows):
            y = oy + r_ * FRAG_STEP_Y
            if y + NODE_H > vp_bottom:
                scr_rows.append("row%d y=%d 下沿=%d" % (r_, y, y + NODE_H))
        print("  %-3d %-34s %4d %5d %6d %6d %6d %6d %6d  %s"
              % (gi, gcn, n, rows, cap, len(made), len(drop), n_vis, n_scr,
                 ("—（全在视口内）" if not scr_rows else "；".join(scr_rows))))
        if drop:
            print("        ✗ 未产 %d 条：%s" % (len(drop), ", ".join(drop)))
    print("-" * 78)
    print("  ⇒ 合计 章数 %d ／ 产出 %d ／ **未产 %d**（纵向流水口径下未产必须逐组为 0）%s"
          % (tot_n, tot_made, tot_drop, " ✓" if tot_drop == 0 else " ← **违规**"))
    print("  ⇒ 可见性（冻结 §7.2）：**产出 %d 格（数据完整）／ 默认可见 %d 格 ／ 需纵滚置真 %d 格**"
          % (tot_made, tot_vis, tot_scr))
    print("  虚拟内容高度：首行 y = %d → 末行下沿 = %d（最大组 rows=%d）＝ 内容高 %d px；"
          "视口可视带仅 %d…%d ⇒ 越过部分由纵滚呈现"
          % (oy, oy + (max_rows - 1) * FRAG_STEP_Y + NODE_H, max_rows,
             (max_rows - 1) * FRAG_STEP_Y + NODE_H, vpy, vp_bottom))
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
      · `frag_limit`：**每组**独立层最多产多少格（★ 2026-09-30 新口径：默认＝**全量**
        ＝ `ceil(章数/3) × 3`；显式给值时仍 `min(frag_limit, rows×3)`）。
    """
    data = load_data()
    spine = load_spine()
    nodes = data["nodes"]
    sections = data["sections"]
    canvas = load_canvas()
    cw, ch = canvas["width"], canvas["height"]

    # ★ 第 11 批收口：生成前先断言 `PRESET_TABLE` ↔ `GOLDEN` 逐组一致（一审阻断项 1 的根治；
    #   `--refresh-golden` 期间自动跳过、并在刷新之后补断一次）
    assert_preset_table_sync()
    static = load_static_elements()
    static_ids = [e["id"] for e in static]
    for need in PASSTHROUGH_REQUIRED:
        if need not in static_ids:
            raise SystemExit("[FAIL] 静态元素快照缺 §一 点名的元素：%s" % need)
    vp = next(e for e in static if e["id"] == "fc.scroll")
    # ★ 冻结 §二 铁律：**一元素只允许一对 `vis_flag`** ⇒ 静态件快照里不得已带 vis_flag
    #   ★★ ISSUE-20260929-02（冻结 §B.6）**具名豁免集**：`STATIC_FLAG_EXEMPT` 里的外壳件**允许**带旗标 ——
    #     `fc_replay` 不是层旗标（≠ `LAYER_FLAG`），其初值 `"play"` 在**任何层**都成立 ⇒ 播放键恒可见；
    #     「切层丢外壳」这条禁令要防的风险**不存在**。**集外仍严格拒绝**（反向自证能力保留）。
    _dup = [e["id"] for e in static
            if ("vis_flag" in e or "vis_when" in e) and e["id"] not in STATIC_FLAG_EXEMPT]
    if _dup:
        raise SystemExit("[FAIL] 静态元素快照已带 vis_flag/vis_when（一元素只允许一对；"
                         "外壳件仅豁免集 %s 例外）：%s" % (sorted(STATIC_FLAG_EXEMPT), _dup))
    # ★★ 更正（2026-09-28 第 3 批 · 主代理 · 冻结书 §二 原写的「现有 117 件全部加 vis_flag/vis_when」作废）：
    #   **外壳件不参与层旗标** —— 静态件快照（视口 / 缩放平移滚条 / 页签 / 标题牌 / 关闭 / 付箋 /
    #   进入本章 / 右栏四段〔大播放窗 / 标题 / 说明 / 台词〕）**一律不写 `vis_flag`/`vis_when`**
    #   （★ ISSUE-20260929-02 起唯一例外 = 豁免集 `STATIC_FLAG_EXEMPT` 的播放/暂停键），
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

        裁到视口而不是画布：视口外的节点若照画，会压到右栏（大播放窗 380×300 / 缩放 / 平移条）上。
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
    entry_rects = []          # ★ 第 12 批：入口块矩形（落盘前「视口内 + 零重叠」自检用）
    if with_entries:
        # 入口列**整列摆进视口**（§九 裁决 5）：左贴视口左缘 / 右贴视口右缘；
        # 入口列**保留宽 333**（原组名标签宽，见 `ENTRY_COL_W`）⇒ 道带位置与上一批逐字相同。
        if entry_side == "right":
            col_x = vp["x"] + vp["w"] - ENTRY_COL_W
        else:
            col_x = vp["x"]
        # ★ 第 12 批：入口块（296×65）与组名文字件（`fc.label.<NNNN>_tx`）**同左沿、同矩形** ——
        #   文字直接落在淡黄入口块上（不再有独立的标签底板）。块在 333 列宽内**左对齐列首**。
        entry_x = col_x
        label_x = col_x
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

            def row_ok(r):
                """该行是否可作入口块落点：**最坏情况**（块落在本行、不 +52）也必须完整落进视口。"""
                return r >= vp["y"] and r + ENTRY_H <= vp_bottom

            if an is not None:
                base = placed[an]["y"]
                k = 0
                while (base + k * step_y) in used_y:
                    k += 1
                cand = base + k * step_y
                # ★ 第 12 批：入口块 **65 高**（原付箋 48）⇒ 行可用判据按块高算（见 `row_ok`）。
                if row_ok(cand):
                    ey = cand
                    basis = ("锚点 = 已落盘节点 %s（script 前缀 %s，依 entry_suggestion 关键词）%s"
                             % (an, pref, "" if k == 0 else "；同行已被上一组占用 ⇒ 下移 %d 行" % k))
            if ey is None:
                while (y0 + fb * step_y) in used_y or not row_ok(y0 + fb * step_y):
                    fb += 1
                    if y0 + fb * step_y > vp_bottom:
                        raise SystemExit("[FAIL] 入口列放不下：第 %d 组既无可用锚点行、"
                                         "也无可用回落行（视口 y∈[%d,%d]、入口块高 %d、行距 %d）"
                                         % (gi, vp["y"], vp_bottom, ENTRY_H, step_y))
                ey = y0 + fb * step_y
                fb += 1
                basis = ("锚点 %s 未在本屏落盘（或该行已被占用且下移后放不下）⇒ **回落**入口列次行"
                         "（本屏 --section %d 未选该锚点所在段/道）；entry_after 全为 null（无原作证据）"
                         % (pref or "无定位锚（任意时点可用）", section))
            used_y.add(ey)
            # ★ 第 12 批：入口块顶 ＝ 锚定行 + `ENTRY_BLOCK_DY`（沿用原「入口标记 → 组名标签」的行位）
            #   ⇒ 交付样例 242/337/432/527/622/717（＝原 `fc.label.<NNNN>` 标签的 y）。
            #   **行距小于 52+65 的档**（如 `--preset ref150` 的 step_y=150）末行会越出视口 ⇒
            #   此时**回落到本行**（块高 65 < 行距 150 ⇒ 仍不压上一块）；普通档（95）不受影响。
            eyb = ey + ENTRY_BLOCK_DY
            if eyb + ENTRY_H > vp_bottom:
                basis += "；★ 第 12 批：+%d 落点（%d）会越出视口下沿 %d ⇒ 入口块**回落到本行** y=%d" % (
                    ENTRY_BLOCK_DY, eyb + ENTRY_H, vp_bottom, ey)
                eyb = ey
            if not row_ok(eyb):
                raise SystemExit("[FAIL] 入口块 %d 落点 (%d,%d,%d×%d) 越出图表视口 %s"
                                 % (gi, entry_x, eyb, ENTRY_W, ENTRY_H, (vp["x"], vp["y"], vp["w"], vp["h"])))
            entry_rects.append((entry_x, eyb, ENTRY_W, ENTRY_H))
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
            # ★ 第 12 批：入口块 = **与章节节点同形制的淡黄块**（296×65、nine 与 `fc.node.*` select 族
            #   完全一致）；组名文字件 `fc.label.<NNNN>_tx` **落在同一矩形**（不再有独立标签底板）。
            gen.append({
                "id": "fc.entry.%04d" % gi, "kind": "image", "z": 20, "visible_default": True,
                "asset": ENTRY_ASSET, "x": entry_x, "y": eyb, "w": ENTRY_W, "h": ENTRY_H,
                "opacity": 255, "nine": dict(ENTRY_NINE),
                "state_assets": {"normal": ENTRY_ASSET, "hover": ENTRY_ASSET_ON},
                "vis_flag": LAYER_FLAG, "vis_when": LAYER_MAIN,
                "source": ENTRY_ASSET_SOURCE,
                "note": "★ 番外入口块（**第 12 批改形制**：淡黄节点形 296×65）· 组=%s（%d 章）"
                        "· entry_suggestion=「%s」· %s%s%s\n"
                        "· **用户 2026-09-29 追加裁决**：`fc.label.<NNNN>` 底板与旧 `fc.entry.<NNNN>` 付箋"
                        "「**一律删去，统一为和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状，"
                        "只是底色换成淡黄（≈ `#FFFF99`）**；文字方案不动」⇒ "
                        "① 底板 `x_ui_label_off.png` 元素的角色由本件承担（**删元素、素材保留**）；"
                        "② 本件素材 `ui/x_ui_entry_frag_{off,on}.png` **由 `x_ui_node_select_{off,on}.png` 派生**"
                        "（alpha 逐字节同源、仅换色相）；③ 旧占位件 `ui/x_ui_fusen_off.png`（86×48 付箋）"
                        "退役为本件的历史（**文件保留不删**；★ **第 13 批订正**：旧文括注「仍被 "
                        "`fc.fusen_edit`/`fc.fusen_reset` 使用」**已作废** —— 该批删了这两键 ⇒ 该素材现**零功能引用**）。\n"
                        "· **职能 =「进入该 xx 番外章节」**：由同一矩形的热区 `fc.entry.%04d_hit` 承担"
                        "（`action:\"flow_layer\"` + `layer:\"frag%d\"` ＝ 用户说的 `fc_layer - fragx`）。\n"
                        "· 几何 `(60, %d, 296×65)`：`nine %s` 与 `fc.node.*` 完全一致（源 263×65 横向拉伸）；"
                        "`z:20`（在组名文字 z25 之下）· `state_assets{normal,hover}` 两态（`_off`/`_on`）。\n"
                        "· ★ 本文件由 `ISSUE-20260929-04` 第 12 批产出（用户指令 2 的追加裁决）。"
                        % (gcn, len(rows), sugg, basis, gsrc_eq, img_note_suffix,
                           gi, gi, eyb, ENTRY_NINE),
            })
            # ★ 冻结 §二：入口热区 `fc.entry.<NNNN>_hit`（矩形＝入口 image 件矩形）
            #   ★ 裁决 4：**仅在该组独立层确实产出时**才产（见上方 `skip_hit`）。
            if not skip_hit:
                gen.append({
                    "id": "fc.entry.%04d_hit" % gi, "kind": "hit", "z": 95, "visible_default": True,
                    "x": entry_x, "y": eyb, "w": ENTRY_W, "h": ENTRY_H,
                    "action": "flow_layer", "layer": FRAG_LAYER_FMT % gi,
                    "label": "",
                    "vis_flag": LAYER_FLAG, "vis_when": LAYER_MAIN,
                    "note": "★ 番外入口热区（冻结 §二）：`action:\"flow_layer\"` + `layer:\"%s\"` —— "
                            "把屏级 flag `%s` 置为 `%s` 并重绘/重算命中（进入第 %d 组番外独立层）；"
                            "＝**用户说的 `fc_layer - fragx`**（`fc.entry.<NNNN>` 的职能就是「进入该 xx 番外章节」）。"
                            "矩形＝入口块 `fc.entry.%04d` 的同一矩形 %d×%d @(%d,%d)；`fc.entry`/`fc.label` 保持 `vis_when:\"main\"`。"
                            "★ 裁决 4：**仅当本组独立层在本档产出**时才产本热区。"
                            "★ 第 12 批：`action`/`layer` **一字未改**，只有矩形随入口块改形制而变（86×48 → 296×65）。"
                            % (FRAG_LAYER_FMT % gi, LAYER_FLAG, FRAG_LAYER_FMT % gi, gi, gi,
                               ENTRY_W, ENTRY_H, entry_x, eyb),
                })
            # ★★ 第 12 批：**`fc.label.<NNNN>` 底板（image）已删**（用户 2026-09-29 追加裁决）——
            #   底板让位于同矩形的**淡黄入口块 `fc.entry.<NNNN>`**（「和章节素材一样的形状、底色换淡黄」）。
            #   **只保留文字件** `fc.label.<NNNN>_tx`；素材 `ui/x_ui_label_off.png` **保留不删**（只删元素）。
            gen.append({
                "id": "fc.label.%04d_tx" % gi, "kind": "text", "z": 25, "visible_default": True,
                "x": label_x, "y": eyb, "w": ENTRY_W, "h": ENTRY_H,
                "font": {"size": LABEL_TEXT_SIZE, "bold": True, "color": TEXT_INK},
                "align": "center", "valign": "middle", "wrap": True, "max_lines": 1,
                "sample": gcn,
                "vis_flag": LAYER_FLAG, "vis_when": LAYER_MAIN,
                "note": "★ 番外组名文字（引擎绘制）——**第 12 批：底板 `fc.label.<NNNN>` 已删、文字留在原地**\n"
                        "· 文案 = 组名中文化（`GROUP_CN_MAP`／`group_cn`）后的 `spine.json` "
                        "side_stories[].group%s（**文字方案未动**：字号 %d / bold / `@palette.psv_ink` 一律不变）。\n"
                        "· **矩形改为与新入口块 `fc.entry.%04d` 同矩形**（`(60, %d, 296×65)`，`align:center`/`valign:middle`）"
                        "—— 文字直接落在淡黄入口块上；旧底板 `fc.label.<NNNN>`（image 333×38，y＝入口标记 +52）"
                        "**已删**（用户 2026-09-29 裁定；`ui/x_ui_label_off.png` 素材保留不删）。\n"
                        "· **容量实测（本工程铁律：判容量用真实语料 + 引擎折行算法）**：6 条组名在 16px / 盒宽 %d 下"
                        "经 `ui_theme_wrap` 复刻复算 ⇒ **全部单行**（最长＝「番外·群像（新年行军 / 格兰玛尼耶）」**265.0px** ≤ 盒宽 %d；"
                        "且 ≤ 入口块可见实体面带宽 **280px**）⇒ **维持 `wrap:true` + `max_lines:1`，未新增字段**。"
                        "证据 `_工作\\ISSUE-20260929-04_流程图件\\证据\\E2_文字容量实测.md`。\n"
                        "· ★ 第 12 批 `ISSUE-20260929-04`（用户 2026-09-29 追加裁决）。"
                        % (gsrc_eq or "（本组不在映射表内 ⇒ 原样透传）", LABEL_TEXT_SIZE,
                           gi, eyb, ENTRY_W, ENTRY_W),
            })
            entry_stats.append((group, gcn, eyb))

    # ── ★ 第 12 批落盘前自检（新增块与邻居的相交复核）────────────────────
    #   本工程教训：**重排前先清点邻居**。入口块由 86×48 付箋放大成 296×65 且左沿移到 60 ⇒
    #   必须证明 ① 每块**完整落在图表视口内**；② **相邻块零重叠**（行距 ≥ 块高即可，但要机器说）。
    if entry_rects:
        _outside = [r for r in entry_rects
                    if not (vp["x"] <= r[0] and r[0] + r[2] <= vp["x"] + vp["w"]
                            and vp["y"] <= r[1] and r[1] + r[3] <= vp["y"] + vp["h"])]
        if _outside:
            raise SystemExit("[FAIL] 入口块越出图表视口：%s（视口 %s）"
                             % (_outside, (vp["x"], vp["y"], vp["w"], vp["h"])))
        _ov = []
        for _a in range(len(entry_rects)):
            for _b in range(_a + 1, len(entry_rects)):
                A, B = entry_rects[_a], entry_rects[_b]
                if (A[0] < B[0] + B[2] and B[0] < A[0] + A[2]
                        and A[1] < B[1] + B[3] and B[1] < A[1] + A[3]):
                    _ov.append((A, B))
        if _ov:
            raise SystemExit("[FAIL] 入口块彼此重叠 %d 对：%s" % (len(_ov), _ov))
        # 与**最左节点槽**的横向间隙自证（左栏图表区未被挤压 ⇒ 入口列与道带零重叠）
        _min_node_x = min([info["x"] for info in placed.values()] or [vp["x"]])
        print("  ★ 第 12 批落盘前自检：入口块 %d 件全部落进视口 ✓、彼此零重叠 ✓；"
              "入口块右缘 %d → 最左节点槽 %d（**横向间隙 %+d px** ⇒ 与节点道带零重叠）"
              % (len(entry_rects), entry_rects[0][0] + ENTRY_W, _min_node_x,
                 _min_node_x - (entry_rects[0][0] + ENTRY_W)))

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
        grid_cols = frag_grid_cols(vpx, vpw)
        if FRAG_COLS > grid_cols:
            raise SystemExit("[FAIL] 独立层列数 %d 超出视口可容列数 %d（视口宽 %d、横步 %d、格宽 %d）"
                             % (FRAG_COLS, grid_cols, vpw, FRAG_STEP_X, NODE_W))
        # ★ 2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）**新口径**：行数按**章数**派生
        #   （`rows = ceil(n/3)`，逐组在下方循环内算）⇒ **取消 `cap` 与视口派生的行上限**；
        #   `--frag-limit` 语义保留：显式给值时仍 `min(frag_limit, rows×3)`；不给值＝全量。
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
            # ★ 行数 = ceil(章数/3)；`--frag-limit` 显式给值时仍 `min(frag_limit, rows×3)`（缺省＝全量）。
            rows = frag_rows(len(grows))
            cap = rows * FRAG_COLS if frag_limit is None else min(frag_limit, rows * FRAG_COLS)
            made, dropped = [], []
            for i, row in enumerate(grows, 1):
                col, rr = (i - 1) % FRAG_COLS, (i - 1) // FRAG_COLS
                cx_, cy_ = ox + col * FRAG_STEP_X, oy + rr * FRAG_STEP_Y
                # ★ 裁剪判据（本批**唯一**的放松）：`x` 完整落视口 **且** `y ≥ 视口顶` ⇒ **允许纵向溢出**。
                #   主干节点仍走 `inside()`（完整落视口）；`--no-cull` 语义不变（只关主干那条）。
                if len(made) >= cap or not frag_layer_rect_ok(cx_, cy_, NODE_W, NODE_H, vp):
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
                # ★★ 冻结 §7.2（2026-09-30 一审后返修 · vision 打回的直修项）：**溢出行的可见性契约** ★★
                #   元素盒下沿 `y + h > 视口底`（＝ vpy+vph ＝ 1017）的行 ⇒ **全部三件一律
                #   `visible_default: false`**（语义＝**数据完整产出、默认不画**；纵滚实现时由编程组置真）。
                #   与 config 屏既有的「`visible_default:false` ＝ 预留下但默认不画」**同源用法，不新造机制**。
                #   起因：G6 第 5 行盒 y1054–1119 会露出半截（y1062–1080 实测 7280 px 残片，压在主面板外背景上）。
                #   ⚠ **只改 `visible_default`，不动几何、不减元素**（`--frag-report` 的「产出」按**元素存在**计）。
                vd = (cy_ + NODE_H) <= (vpy + vph)
                ov_note = ("" if vd else
                           "· ★ **溢出视口底（y+h=%d > %d）⇒ `visible_default:false`**"
                           "（数据完整产出、默认不画；纵滚到位时由编程组置真 —— 冻结 §7.2）"
                           % (cy_ + NODE_H, vpy + vph))
                off, on = FRAG_ASSET
                gen.append({
                    "id": FRAG_ID_FMT % (frag_group, i), "kind": "image", "z": 20,
                    "visible_default": vd,
                    "asset": off, "x": cx_, "y": cy_, "w": NODE_W, "h": NODE_H,
                    "opacity": 255, "nine": dict(NODE_NINE["frag"]),
                    "state_assets": {"normal": off, "hover": on, "pressed": on},
                    "source": NODE_ASSET_SOURCE,
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "★ 番外独立层节点（冻结 §二）%s· 素材 %s（源 228×65 ≠ 296 ⇒ nine 横向拉伸，"
                            "与主干 frag 节点同件同 nine）· state_assets 三态图、不带 state_group"
                            "· **运行态未定义**（裁决 4：不写 `flow_state`、不产 `_dim`/`_new`）%s"
                            % (base_note, off.split("/")[-1], ov_note),
                })
                gen.append({
                    "id": (FRAG_ID_FMT % (frag_group, i)) + "_tx", "kind": "text", "z": 25,
                    "visible_default": vd,
                    "x": cx_ + (NODE_W - TEXT_W) // 2, "y": cy_, "w": TEXT_W, "h": NODE_H,
                    "font": {"size": TEXT_SIZE, "bold": True, "color": TEXT_INK},
                    "line_spacing": TEXT_LINE_SPACING,
                    "align": "center", "valign": "middle", "wrap": True, "max_lines": TEXT_MAX_LINES,
                    "sample": title,
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "番外独立层节点标签（引擎绘制）· 文案＝%s%s· **文字口径与主干节点完全一致**："
                            "字号 %d / 行距 %s（元素级 `line_spacing`）/ 文字盒宽 %d（居中：x_node+%d）/ "
                            "最多 %d 行 / wrap / valign:middle（同样跑四条文字判据）%s"
                            % (src_kind, "（**cn 缺失 ⇒ 回落标题/脚本名**）" if src_kind != "DATA.nodes[%s].cn" % script else "",
                               TEXT_SIZE, TEXT_LINE_SPACING, TEXT_W, (NODE_W - TEXT_W) // 2, TEXT_MAX_LINES,
                               ov_note),
                })
                gen.append({
                    "id": (FRAG_ID_FMT % (frag_group, i)) + "_hit", "kind": "hit", "z": 95,
                    "visible_default": vd,
                    "x": cx_, "y": cy_, "w": NODE_W, "h": NODE_H,
                    "action": "", "label": "",
                    "vis_flag": LAYER_FLAG, "vis_when": layer,
                    "note": "番外独立层节点热区%s· action 本轮**留空**（与主干节点同口径：点节点＝标记已读+定位属编程组）%s"
                            % (base_note, ov_note),
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
                         "lead_y": FRAG_LEAD_Y, "origin": (ox, oy), "rows": rows, "cap": cap,
                         "content_bottom": oy + (rows - 1) * FRAG_STEP_Y + NODE_H,
                         "needs_scroll": (oy + (rows - 1) * FRAG_STEP_Y + NODE_H) > (vpy + vph)},
                "back_key": "fc.frag%d_back" % frag_group,
                "title_bg_key": "fc.frag%d_title_bg" % frag_group,
                "title_ink_w": _tw,
                # ★ 冻结 §7.2：可见性统计（产出格数按**元素存在**计，与此两列无关）
                "cells_visible": sum(1 for _i, _r, _cx, _cy in made
                                     if (_cy + NODE_H) <= (vpy + vph)),
                "cells_scroll": sum(1 for _i, _r, _cx, _cy in made
                                    if (_cy + NODE_H) > (vpy + vph)),
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
    # ★ §九 裁决 5 自证：**本屏全部产出元素**（图内容层）必须整体落在图表视口内。
    #   ★★ 2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）**唯一豁免**：**独立层元素**
    #     （`vis_flag=="fc_layer"` 且 `vis_when` 以 `frag` 开头）改判据为
    #     「`x` 完整落视口 **且** `y ≥ 视口顶`」⇒ **允许纵向溢出**（见 `frag_layer_rect_ok()`）。
    #     **这是有意偏离** §九 裁决 5（依据与登记见 `FRAG_VIEW_ROWS` 上方注释与本函数注释）；
    #     主干节点与外壳件判据**一字未改**。`--no-cull` 语义不变。
    def _frag_layer_el(e):
        return e.get("vis_flag") == LAYER_FLAG and str(e.get("vis_when", "")).startswith("frag")

    outside = []
    for e in gen:
        if _frag_layer_el(e):
            if not frag_layer_rect_ok(e["x"], e["y"], e["w"], e["h"], vp):
                outside.append(e["id"])
        elif not (vx <= e["x"] and e["x"] + e["w"] <= vx + vw
                  and vy <= e["y"] and e["y"] + e["h"] <= vy + vh):
            outside.append(e["id"])
    max_right = max([e["x"] + e["w"] for e in gen] or [0])
    max_bottom = max([e["y"] + e["h"] for e in gen] or [0])
    # ★ 第 16 批：纵向下沿**分开报** —— 主干/外壳仍受「完整落视口」约束，独立层允许溢出。
    _frag_gen = [e for e in gen if _frag_layer_el(e)]
    _trunk_gen = [e for e in gen if not _frag_layer_el(e)]
    max_bottom_trunk = max([e["y"] + e["h"] for e in _trunk_gen] or [0])
    max_bottom_frag = max([e["y"] + e["h"] for e in _frag_gen] or [0])
    # ── ★★ 冻结 §7.2 落盘前自检：**溢出行的可见性契约**（违反即拒绝落盘）──
    #   「独立层元素盒下沿 y+h > 视口底 ⇒ `visible_default` 必须为 False；否则必须为 True」
    #   双向卡：**溢出却默认可画**（＝本轮 vision 缺陷本体）与**未溢出却默认不画**（＝误藏）都拒绝。
    _vd_bad = []
    for e in _frag_gen:
        _should_vis = (e["y"] + e["h"]) <= (vpy + vph)
        if bool(e.get("visible_default", True)) != _should_vis:
            _vd_bad.append((e["id"], e["y"] + e["h"], e.get("visible_default")))
    if _vd_bad:
        raise SystemExit("[FAIL] 冻结 §7.2 可见性契约被违反（溢出行的三件必须 `visible_default:false`、"
                         "未溢出者必须 `true`）：%s" % _vd_bad)
    print("  ★ 冻结 §7.2·独立层可见性契约自检：独立层元素 %d 件 ⇒ 溢出视口底（y+h > %d）者 "
          "**%d 件全部 `visible_default:false`**（数据完整、默认不画；纵滚到位时由编程组置真）✓；"
          "未溢出者 %d 件 `true` ✓"
          % (len(_frag_gen), vpy + vph,
             sum(1 for e in _frag_gen if (e["y"] + e["h"]) > (vpy + vph)),
             sum(1 for e in _frag_gen if (e["y"] + e["h"]) <= (vpy + vph))))
    kinds = {"section": 0, "select": 0, "frag": 0, "branch": 0}
    for nid in order:
        kinds[node_kind(nodes[nid])] += 1

    elements = [json.loads(json.dumps(e, ensure_ascii=False)) for e in static] + gen
    # ── ★ 落盘前自检（第 3 批 · 主代理 item 1）：层旗标**只由图内容层持有**，双向卡 ──
    #   ① 外壳件（任何非图内容层 id）带 `vis_flag`/`vis_when` ⇒ 拒绝（会在独立层被误隐藏）；
    #   ② 图内容层件缺 `vis_flag` ⇒ 拒绝（会漏声明层归属，切换时行为未定义）。
    #   ★★ ISSUE-20260929-02（冻结 §B.6）：① 新增**具名豁免集** `STATIC_FLAG_EXEMPT`（播放/暂停键）——
    #     `fc_replay` **不是层旗标**，其初值 `"play"` 在**任何层**都成立 ⇒ 播放键恒可见，
    #     「切层丢外壳」这条禁令要防的风险**不存在**；**集外仍严格拒绝**（反向自证能力保留：
    #     把豁免集临时置空跑一次，本判据必须如旧报错）。
    shell_flagged = [e["id"] for e in elements
                     if not e["id"].startswith(LAYER_OWNED_PREFIXES)
                     and ("vis_flag" in e or "vis_when" in e)
                     and e["id"] not in STATIC_FLAG_EXEMPT]
    if shell_flagged:
        raise SystemExit("[FAIL] 外壳件带层旗标（本批更正：外壳不参与层旗标，两态共用舞台；"
                         "豁免集 %s 除外，理由见冻结 §B.6）：%s"
                         % (sorted(STATIC_FLAG_EXEMPT), shell_flagged))
    content_unflagged = [e["id"] for e in elements
                         if e["id"].startswith(LAYER_OWNED_PREFIXES) and "vis_flag" not in e]
    if content_unflagged:
        raise SystemExit("[FAIL] 图内容层件缺 vis_flag/vis_when（层归属未声明）：%s" % content_unflagged)
    # ★ 冻结 §二：屏级 `flags_default` 新增 `{"fc_layer":"main"}`；演示预设另外登记逐节点运行态 flag
    # ★ 冻结 §B.5（ISSUE-20260929-02）：再新增 `{"fc_replay":"play"}` —— 播放键 `fc.pbkick`
    #   （`vis_when:"play"`）与暂停键 `fc.pbkick_pause`（`vis_when:"pause"`）**同位置互斥**，
    #   初值 `play` ⇒ 进屏显示播放键（与 `review` 侧的 flag 机制同款，不新增机制）。
    flags_default = {LAYER_FLAG: LAYER_MAIN, REPLAY_FLAG: REPLAY_PLAY}
    # ★★ 第 15 批（`ISSUE-20260930-02` · 冻结 §三.2/§四）：再新增 **`fc_intro`（初值 `"closed"`）** ——
    #   章节详情浮层 6 件靠 `vis_flag:"fc_intro"` + `vis_when:"open"` 显隐 ⇒ **进屏默认关闭浮层**。
    #   与 `fc_layer`/`fc_replay` 并列，既有两键**不动**（冻结 §三.2）。动作 `flow_intro_open`/
    #   `flow_intro_close` 为**纯 flag 翻转**、两端本批实现（见 `layout/_schema.md` §六 动作表）。
    flags_default[INTRO_FLAG] = INTRO_CLOSED
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
    # ── ★ ISSUE-20260929-05 第 13 批落盘前自检（模式入口：画布内 + 与相邻件零重叠）──
    #   本工程教训：**重排前先清点邻居**（第 12 批入口块自检的同一条）。两枚模式入口取代原 4 页签、
    #   位置在「剧情流程图」按钮上方 ⇒ 必须机器说清「落进画布、彼此不重叠、不压任何相邻件」。
    #   判据见 `mode_entry_violations()`；`--selfcheck-mode-entries` 是它的**变异自证**（自检要能失败）。
    _mv = mode_entry_violations(elements, cw, ch)
    if _mv:
        raise SystemExit("[FAIL] 模式入口自检不通过（用户指令②「排版整齐、间距相等」）：\n  - "
                         + "\n  - ".join(_mv))
    print("  ★ 第 13 批落盘前自检（模式入口）：\n    " + mode_entry_report(elements, cw, ch).replace("\n", "\n    "))
    # ── ★★ ISSUE-20260930-02 第 15 批落盘前自检（章节详情：加号按钮 + 详情浮层）──
    #   冻结 §六 三条：① 按钮与文字零重叠且完整落在面板内；② 浮层组 z 高于本屏所有非浮层 hit；
    #   ③ 浮层组几何在画布内、两个 `_tx` 完整在 `fc.intro_bg` 内。
    #   判据见 `intro_overlay_violations()`；`--selfcheck-intro-overlay` 是它的**变异自证**（自检要能失败）。
    _iv = intro_overlay_violations(elements, cw, ch)
    if _iv:
        raise SystemExit("[FAIL] 章节详情浮层自检不通过（冻结 §六）：\n  - " + "\n  - ".join(_iv))
    print("  ★ 第 15 批落盘前自检（章节详情：加号按钮 + 详情浮层）：\n    "
          + intro_overlay_report(elements, cw, ch).replace("\n", "\n    "))
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
        "gen_max_bottom_trunk": max_bottom_trunk, "gen_max_bottom_frag": max_bottom_frag,
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
    "screen1": ("1c6496e7b3efff589c4fd09c613e3ef3", "99b15674e782dc66b05b2ebd6807fbe370546afda6adffa90cf11190e7799884"),
    "screen2": ("3cd4e92d91d197d2847e30442124860c", "ce17b7955cfd69f1af95b8526b650a0b979db4b2c75a9ac6882e7c18e22e642b"),
    "ref150": ("43a5b40ab3bea83d57cbd053c895a535", "15e50f1c4a8aadd410319173d41ab7f746c883656961f3a3970a91f6262f2c80"),
    "states": ("74392cc9b5d3f632cc693afa95b24a89", "97fb4fd8a87537614b05f690969338f776ab6dda9208bd88467650737237d5fe"),
    "frag": ("4ed7585a16ea700343328a962a9eb95a", "b581b226459b48a2bac0687765b375b91bab51c0e3e55d74a0a9c7145afc2cd3"),
}
GOLDEN_ORDER = ("screen1", "screen2", "ref150", "states", "frag")
# ★ 第 11 批收口：`--refresh-golden` 进行中置 True ⇒ `assert_preset_table_sync()` 延后到刷新之后
#   （刷新那一刻表本来就该是旧的）。见 `refresh_golden` / `assert_preset_table_sync` 的 docstring。
_REFRESHING = False

# ★ 第 11 批第 3 轮（二审 B1）：`PRESET_TABLE` / `SCREEN_NOTE` 里除了 md5/sha，还有**人读的散文数字**。
#   本批实测踩到过「同一张表里 `255px` 与 `228.0px` 并存」的自相矛盾（第 1 轮只治了 md5/sha 两列）
#   ⇒ 除 md5/sha 逐组比对外，再断言：① 现行口径的字符串**必须逐源在**；② 已作废的字符串**任一源都不得出现**。
#   ⚠ **必须逐源判**（第 3 轮齿检查拓出的漏洞）：起初把两处并成一个 blob 判「必须在」，
#      结果「只从 `PRESET_TABLE` 里删掉现行串」**不会被抓到**（`SCREEN_NOTE` 里那份顶住了）。
#   **维护规则**：以后任何一次「口径数字变了」，都要把旧串登记进 `RETIRED_TABLE_SNIPPETS`
#   （否则这条防线的判别力会随批次衰减）。
REQUIRED_PRESET_TABLE_SNIPPETS = (
    "最宽行 228.0px",
    "最紧 **+34.00**（`s01_02b`）",
    # ★ 第 16 批（`ISSUE-20260930-06` · 独立层纵向流水）：现行元素数口径（口径变了却不改本表 ⇒ 本条即报警）
    "296 元素",
    "图内容层 **246**",
    "外壳 **50**",
    "独立层节点 **159**",
    "G6 20/20",
    # ★ 冻结 §7.2（一审后返修）：溢出行的可见性契约（口径变了却不改本表 ⇒ 本条即报警）
    "默认可见 12 格（4 行）",
    "其余 8 格需纵滚置真",
)
REQUIRED_SCREEN_NOTE_SNIPPETS = (
    "最宽行 228.0px",
    "最紧 **+34.00**（`s01_02b`）",
    # ★ 第 16 批：现行元素数口径（同上，**逐源判**）
    "296 元素",
    "图内容层 **246**",
    "外壳 **50**",
    "独立层节点 **159**",
    "G6 20/20",
    # ★ 冻结 §7.2（一审后返修）：同上，**逐源判**
    "默认可见 12 格（4 行）",
    "其余 8 格需纵滚置真",
    # ★ D-01（2026-10-01 · ISSUE-20261001-11）：17 屏合计 1422 → **1428**（`title` 屏 +6）
    #   ⚠ **只登记 SCREEN_NOTE** —— `PRESET_TABLE` 不含该句（本闸门按源逐条判）
    "17 屏合计现行 1428",
)
RETIRED_TABLE_SNIPPETS = (
    "四判据实测最小值：上留 5px、下留 5px、最宽行 255px、截断 0。",
    "实测 712 条 **违规 0**、最紧 **+30.00**（`s04_03f1`）。",
    "(443−380)//2",
    "(443-380)//2",
    # ★ 第 12 批：第 11 批的现行元素数口径（已被 274/222 取代；旧串不得再作现值出现）
    "280 元素（**总**）＝ 外壳 **52** ＋ 图内容层 **228**",
    "（⇒ 63 ＋ 135 ＋ 30 ＝ 228 ✓",
    # ★★ 第 13 批：第 12 批的现行元素数口径（已被 262/40/222 取代 ⇒ 旧串一律不得再作现值出现）
    #   ⚠ 注意本清单是**整串**匹配（`in`）⇒ 也把旧的行首整句登记进来，避免「274 元素（**总**）＝ 外壳 **52**」残留。
    "274 元素",
    "274 元素（**总**）＝ 外壳 **52** ＋ 图内容层 **222**",
    "外壳 **52** ＋ 图内容层 **222**",
    # ★★ 第 15 批：第 13 批的现行元素数口径（已被 270/48/222 取代 ⇒ 旧串一律不得再作现值出现）
    "262 元素",
    "外壳 **40**",
    "262 元素（**总**）＝ 外壳 **40** ＋ 图内容层 **222**",
    # ★★ 第 15 批 · 第 2 轮（用户裁定 5/6/7）：第 15 批首轮的现行元素数口径
    #   （已被 272/50/222 取代 —— 浮层族 6 → 8 件 ⇒ 外壳 48 → 50；首轮读数一律不得再作现值出现）
    "270 元素",
    "270 元素（**总**）＝ 外壳 **48** ＋ 图内容层 **222**",
    "外壳 **48**",
    # ★★ 第 16 批（`ISSUE-20260930-06` · 独立层纵向流水）：第 15 批的现行元素数口径
    #   （已被 296 / 50 / 246 取代 —— 第 6 组 12 → 20 格 ⇒ 图内容层 222 → 246；旧串一律不得再作现值出现）
    "272 元素",
    "图内容层 **222**",
    "独立层节点 **135**",
    "G6 12/20",
    # ★ D-01（2026-10-01）：第 16 批的 17 屏合计口径（已被「现行 1428」取代 ⇒ 旧串不得再作现值出现）
    "**17 屏合计 1401 → 1422**",
)

PRESET_TABLE = """预设名 → 命令行 → 产出规模 → md5（金标，实跑真值）
  screen1（**默认**，无参即此）  python 工具/gen_flow_layout.py
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95 ｜ 13 节点（section 11/select 2）｜ 13 连线（直线 11/VZ 1/VL 1，全 normal）
      296 元素（**总**）＝ 外壳 **50** ＋ 图内容层 **246**
      ├ 外壳 50：`fc.` 图内容层前缀之外的一切（**满幅背景 `fc.bg`（第 12 批新增）** / 视口/滚条/**模式入口 `fc.mode_*`（第 13 批新增，6 件）** / 标题牌/关闭/进入本章/右栏四段
        〔大播放窗 `fc.play_win`＋`fc.play_view` ／ 标题 `fc.p_title`＋`_tx` ／ 说明 `fc.p_text`＋`_tx` ／
        台词 `fc.p_message`＋`_tx`〕／ **章节详情 10 件（第 15 批新增：加号按钮 2 件 ＋ 浮层 8 件
        〔基座 6 ＋ 关闭件 `fc.intro_close`/`fc.intro_close_hit` 2〕）**）
        —— **除豁免集 `fc.pbkick`/`fc.pbkick_pause` ＋ `fc.intro_*`（8 件）外不带层旗标**
        （★ 第 12 批：`fc.sysbar` 已删 ⇒ 外壳 52 − 1 ＋ 1（`fc.bg`）；★ **第 13 批：52 → 40** ——
         删 12 件 `fc.mtab*` ＋ 6 件 `fc.fusen_*`、增 6 件 `fc.mode_*` ⇒ 52 − 12 = 40；**旧读数「外壳 52」已作废**；
         ★ **第 15 批：40 → 48** —— 增 8 件章节详情件（加号按钮 2 ＋ 浮层 6），全部为外壳件 ⇒ 40 ＋ 8 = 48；
         ★ **第 15 批 · 第 2 轮：48 → 50** —— 浮层再增关闭件 2 件（用户裁定 5）⇒ 48 ＋ 2 = 50）
      └ 图内容层 246 ＝ 主干 **57**（`fc.node.*` 39 ＋ **`fc.label.*_tx` 6** ＋ `fc.entry.*` 12；`fc.branch.*` 0）
        ＋ 独立层节点 **159**（6 组共 53 格 ×3〔image/text/hit〕；★ 第 16 批：G6 由 12 格全产为 20 格 ⇒ 45 → 53 格）
        ＋ 每组顶栏 **30**（6 组 × 5：`_title`／**`_title_bg`（组名底托，第 5 批）**／`_back`／`_back_tx`／`_back_hit`）
        （⇒ 57 ＋ 159 ＋ 30 ＝ 246 ✓；★ 注意「组名底托 6 件」**是顶栏 30 的子集，不得另加**——
         上一版把它另列并写成「主干 124」，124 是**第 2 批时的旧总元素数**，被误标成主干，已订正）
        （★ 第 12 批：主干 63 → **57** —— **6 件 `fc.label.<NNNN>` 底板已删**，文字件 `_tx` 6 件保留；
          ⇒ 280 − 6 − 1（`fc.sysbar`）＋ 1（`fc.bg`）＝ 274 ⇒ ★ **第 13 批：274 − 12 ＝ 262**
          ⇒ ★ **第 15 批：262 ＋ 10 ＝ 272** ⇒ ★★ **第 16 批：272 ＋ 24 ＝ 296**）
      ★★ 第 16 批（`ISSUE-20260930-06` · 2026-09-30 · **番外独立层改纵向流水**）：**加 24 件**（G6 的 13–20 格 × 3
        ＝ 8 节点；用户裁定 5「组内全部产出」，关闭缺口 G-3）⇒ `screen1` **272 → 296**（五档仅 screen1 变：
        **296 / 116 / 95 / 109 / 128**；17 屏合计 **1401 → 1422**（★ D-01：`title` 18→24 ⇒ **现行 1428**）〔★ 中间值 1425 ＝ 未减 config 的 −3，**只作历史留痕**〕）；**外壳 50 逐字不变**、图内容层 **222 → 246**；
        裁剪口径放宽（x 完整落视口 且 y ≥ 视口顶 ⇒ **允许纵向溢出**，**有意偏离** §九 裁决 5）、
        层固定件不随滚、HTML `overflow:hidden` 需纵滚 —— 详见屏 note 第 16 批段与 `layout\\_schema.md` 第 16 批块。
      ★★ 第 13 批（`ISSUE-20260929-05` · 模式入口收敛 ＋ 删备注功能与对话框提示）：**删 18 件 / 加 6 件**
        ⇒ `screen1` 274 → **262**（五档各 **−12**：**262 / 106 / 85 / 99 / 118**；`dialog` 10 → 9；
        17 屏合计 **1404 → 1391**）。删：`fc.mtab1..4`＋`_tx`＋`_hit`（12）＋`fc.fusen_edit`/`fc.fusen_reset`＋`_tx`＋`_hit`（6）；
        加：`fc.mode_main_glow`/`_tx`/`_hit` ＋ `fc.mode_frag_glow`/`_tx`/`_hit`（180×60、`_glow`/`_hit` @y25、
        **`_tx` @y33（E5 文字下移 8px）**、x 34/254、
        z 10/20/95、`state_group` `mode_main`/`mode_frag`、`action` `flow_mode_main`/`flow_mode_frag`、
        三态素材 `ui/x_ui_modetab_{off,over,press}.png`（两入口共用））。**素材一个不删**。
        详见屏 note 第 13 批段与 `PRESET_TABLE` 末的「第 13 批重钉」。
      ★★ 第 15 批（`ISSUE-20260930-02` · 章节详情：说明槽截断 ＋ 详情浮层 ＋ 加号按钮）：
        **加 10 件**（第 1 轮 8 件；**第 2 轮再增关闭件 2 件**）
        （加号按钮 `fc.p_plus`/`fc.p_plus_hit` ＋ 浮层基座 `fc.intro_scrim`/`_scrim_hit`/`_bg`/`_panel_hit`/`_title_tx`/`_text_tx`
        ＋ **关闭件 `fc.intro_close`/`fc.intro_close_hit`（第 2 轮 · 用户裁定 5）**）
        ⇒ `screen1` 262 → **272**（五档各 **＋10**：**272 / 116 / 95 / 109 / 128**；17 屏合计 **1391 → 1401**）；
        `fc.p_text_tx.w` **398 → 300**（说明槽收窄让位加号按钮；终值取 300 见 M4 几何定标）；
        屏级 flag 追加 **`fc_intro:"closed"`**；动作 **`flow_intro_open`/`flow_intro_close`**（纯 flag 翻转、两端已实现，
        见 `layout\\_schema.md` §六）；**素材新出 3 件** `ui/x_ui_plusbtn_{off,over,press}.png`（44×44 RGBA ×3；
        关闭件**零新素材**，复用既有 `x_ui_close_*`）。
        ★★ **第 2 轮（2026-09-30 · 用户裁定 5/6/7）**：再加 2 件关闭件（外壳 48 → **50**）；
        浮层面板 **1240×652 → 1240×400**（@340,340，版面中心）、标题槽 **1176×44 @372,246 → 1140×44 @372,372**、
        正文槽 **1176×528 @372,306 → 1176×276 @372,432**；加号按钮及热区 y **625 → 618**（对齐首行行盒中心）；
        `fc.intro_close` z236（`nine{6,6,6,6}`，同 `fc.close` 用法）/ `fc.intro_close_hit` z237（**须高于面板热区 230**，
        落盘前自检专条断言 ＋ 变异自证 G）；加号素材外圈环改**按目标尺寸 1:1 直绘**（off 环色 (146,159,183)@α255）。
        详见屏 note 第 15 批段与 `layout\\_schema.md` 第 15 批块。\n      ★ 第 3 批：交付样例含**全部 6 组**番外独立层（G1 7/7、G2 7/7、G3 4/4、G4 10/10、G5 5/5、G6 **20/20**〔★ 第 16 批：G6 由 12 → 20 格〕）⇒ 入口→独立层→按组返回键闭环
      ★ 第 4 批（裁决 4）：本档 6 组入口**均已产独立层** ⇒ **6/6 组有入口热区**（无占位缺口）
      ★ 第 5 批：每组顶栏加**组名标签底板** `fc.frag<G>_title_bg`（+6 件 ⇒ 283 → 289；修「组名对比度 1.19:1 不可读」）
      ★ 第 7 批：组名底托**换专用件** `x_ui_fragtitle_bg.png`（444×52、硬边、1:1 无 nine）⇒ 元素数不变（289）、几何与素材变
      ★ 第 8 批（`ISSUE-20260928-03`）：**元素内容逐字不变**（content-sha256 与第 7 批同值）——md5 变因**仅屏 note 措辞**
      ★ 第 9 批：**唯一一处文字变更** —— `fc.frag6.0007_tx`（script `62_1b`）按 `TITLE_HARD_BREAK` 断成两行（旧单行 255px/左缘 +20.50 ⇒ 新 122/133px、左缘 +87）⇒ 元素数不变（**289**）、该 `sample` 与屏 note 变
      md5 = 1c6496e7b3efff589c4fd09c613e3ef3 ｜ content-sha256 = 99b15674e782dc66b05b2ebd6807fbe370546afda6adffa90cf11190e7799884
      ★ 第 10 批：**两行条数 101 → 105**；`fc.frag4.0008_tx`（script `42_3`）与 `fc.frag4.0009_tx`（`42_4`）的
        `sample` 各插一个硬换行（断在「（」前）—— **本批对交付样例的有意变更恰此 2 处**（md5 与 content-sha 都因此变）
      ★ 第 11 批（`ISSUE-20260929-02` · 右栏大改 · 用户指令 1–4）：**元素 289 → 280**（删 12 ＋ 增 3）、
        **外壳 61 → 52**；图内容层 **228 不变**（★ **第 12 批再订正 → 222**）；屏级新增 flag `fc_replay:"play"`；三个 `_tx` 改白字＋黑描边；
        新增 `fc.play_win`/`fc.play_view`/`fc.pbkick_pause`，`fc.pbkick`/`fc.pbkick_hit` 移到大播放窗中央
        （`md5` 与 `content-sha256` 都因此变；详见屏 note 第 11 批段）
      ★ **第 11 批·第 2 轮（2026-09-29 · 主代理裁决）**：「说明/台词」两件 `max_lines` **5 → 4**
        （槽高 159 ÷ 行盒 33px ＝ 4.82；行盒 ＝ `floor(24 × 全局 line_spacing.body 1.4)`）⇒
        **五档 md5 与 content-sha256 再变一次**（元素数不变：280/124/103/117/136）；实跑真值见下方各行
      ★ **第 11 批·第 3 轮（2026-09-29 · vision 实机复审后 · 主代理已亲自复核）**：**两处真缺陷修复**
        —— ① 右栏台词槽（`y824 h171` ⇒ 下沿 995）与「进入本章」按钮（上沿 943）**竖直重叠 52px** ⇒
        三槽高度 **171 → 150**、四段重排为「窗与三槽分离、三槽彼此紧凑」（`y` 534/617/777，两个 `_tx` `h 159→138`；
        **台词底 927 → 按钮 943 ＝ 16px 无重叠**）；`max_lines` **仍 4**（krkr 138÷33＝4.18；HTML 4×34＝136 ≤ 138）；
        ② 动态层占位标签**横向不受矩形约束**（`fc.play_view` 第二行墨迹 x1456..1918 戳出窗/栏/屏）⇒
        两端改为**逐行按元素宽截断并追加 `…`**（krkr `ui_widget.tjs` ＋ `ui_theme.tjs::uiThemeEllipsize`；
        HTML `复刻/replica.js` 离屏 span 度量）。
        ⇒ **元素数不变（280/124/103/117/136）**，但六件右栏件的 `y`/`h` 变 ⇒ **五档 md5 与 content-sha256 全部再变**（实跑真值见下）
        （★ **第 12 批**：五档各 **−6** ⇒ **274 / 118 / 97 / 111 / 130**，见下方「第 12 批重钉」；
         ★ **第 13 批**：五档各再 **−12** ⇒ **262 / 106 / 85 / 99 / 118**，见下方「第 13 批重钉」）
  screen2                        python 工具/gen_flow_layout.py --preset screen2
      段[3] AfterStory 道 1,2 from 0 limit 9 step_y 95 ｜ 18 节点（section 4/select 5/frag 9）｜ 14 连线（直线 14，全 normal）｜ **116 元素**（★ 第 16 批现行；第 13 批读数 106、第 15 批 ＋10 见重钉块）
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 139 → 133，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因**共用静态件 `fc.zoom_minus/plus` 的 `source` 订正**（见下）
      ★ 第 7 批：**content-sha256 逐字不变**（无底托、连线全 normal）⇒ 只有屏 note 措辞变（本批追加两段）
      ★ 第 8 批：**content-sha256 逐字不变**（元素内容未动）⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = 3cd4e92d91d197d2847e30442124860c ｜ content-sha256 = ce17b7955cfd69f1af95b8526b650a0b979db4b2c75a9ac6882e7c18e22e642b
      ★ 第 10 批：**content-sha256 逐字不变**（本档无表内标题）⇒ md5 变因**仅屏 note 共用**
      ★ 第 11 批：元素 **133 → 124**（右栏 −12 ＋3）⇒ md5 与 content-sha256 **都变**
      ★ 第 12 批：元素 **124 → 118**（−6 = 6 件 `fc.label.<NNNN>` 底板）⇒ md5 与 content-sha256 **都变**
      ★ 第 13 批：元素 **118 → 106**（−12 = 12 件 `fc.mtab*`；6 件 `fc.fusen_*` 删、6 件 `fc.mode_*` 增相抵）⇒ md5 与 content-sha256 **都变**
  ref150（**不是交付样例**）      python 工具/gen_flow_layout.py --preset ref150
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 150 ｜ 11 节点（section 9/select 2）｜ 10 连线（直线 9/VL 1，无 VZ，全 normal）｜ **95 元素**（★ 第 16 批现行；第 13 批读数 85、第 15 批 ＋10 见重钉块）
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 118 → 112，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因同上（`source` 订正）
      ★ 第 7 批：同上（**content-sha256 逐字不变**）
      ★ 第 8 批：**content-sha256 逐字不变** ⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = 43a5b40ab3bea83d57cbd053c895a535 ｜ content-sha256 = 15e50f1c4a8aadd410319173d41ab7f746c883656961f3a3970a91f6262f2c80
      ★ 第 10 批：**content-sha256 逐字不变**（本档无表内标题）⇒ md5 变因**仅屏 note 共用**
      ★ 第 11 批：元素 **112 → 103**（右栏 −12 ＋3）⇒ md5 与 content-sha256 **都变**
      ★ 第 12 批：元素 **103 → 97**（−6 = 6 件 `fc.label.<NNNN>` 底板）⇒ md5 与 content-sha256 **都变**
      ★ 第 13 批：元素 **97 → 85**（−12 = 12 件 `fc.mtab*`；`fc.fusen_*` 6 删 / `fc.mode_*` 6 增相抵）⇒ md5 与 content-sha256 **都变**
  states（**不是交付样例**）      python 工具/gen_flow_layout.py --preset states
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95 ｜ 13 节点（与 screen1 同一批）｜ 13 连线（**normal 5 / visited 4 / noroute 4 —— 三档同屏**）｜ **109 元素**（★ 第 16 批现行；第 13 批读数 99、第 15 批 ＋10 见重钉块）
      （节点 flow_state 循环 locked→available→visited→current→new：`_dim` 3 件（**image，按种类取件**）、
        `_new` 2 件、`_read` 3 件（已读绿对勾）；`current` **不产元素**，两端程序化画环、**只留金环、不加对勾**）
      ★ 第 4 批（裁决 4）：本档**不产独立层** ⇒ 6 个入口为**纯占位**、**0 个入口热区**（第 3 批 129 → 123，−6）
      ★ 第 5 批：元素数不变；md5/`content-sha256` 变因同上（`source` 订正）
      ★ 第 7 批：`edge_noroute` 调暗 #6A6A7A → #5A5A68 ⇒ **本档 noroute 边的 `color` 内嵌值变**（元素数不变 123）
      ★ 第 8 批（`ISSUE-20260928-03`）：① `_dim` 由 `rect` 改 **`image`**（按节点种类取压暗件、与底图件同几何同 nine）
        —— 修「方角 55px 暗方角」真缺陷；② 新增 `_read` 3 件（visited）。⇒ **123 → 126 元素**
        （3 个 locked：node 0001＝**select**、0006/0011＝section ⇒ 本档同时演示 select 与 section 两种压暗件）
      md5 = 74392cc9b5d3f632cc693afa95b24a89 ｜ content-sha256 = 97fb4fd8a87537614b05f690969338f776ab6dda9208bd88467650737237d5fe
      ★ 第 10 批：**content-sha256 逐字不变**（本档无 `fc.frag*`，不含表内标题）⇒ md5 变因**仅屏 note 共用**
      ★ 第 11 批：元素 **126 → 117**（右栏 −12 ＋3；含 `_dim` 3 / `_new` 2 / `_read` 3）⇒ md5 与 content-sha256 **都变**
      ★ 第 12 批：元素 **117 → 111**（−6 = 6 件 `fc.label.<NNNN>` 底板；含 `_dim` 3 / `_new` 2 / `_read` 3）⇒ md5 与 content-sha256 **都变**
      ★ 第 13 批：元素 **111 → 99**（−12 = 12 件 `fc.mtab*`；`fc.fusen_*` 6 删 / `fc.mode_*` 6 增相抵；含 `_dim` 3 / `_new` 2 / `_read` 3）⇒ md5 与 content-sha256 **都变**
  frag（**不是交付样例**）        python 工具/gen_flow_layout.py --preset frag
      段[0] 本篇 道 0,1 from 100 limit 9 step_y 95（主干同 screen1）＋ spine **第 1 组**番外独立层 7/7 格
      13 节点 ｜ 13 连线（全 normal；**独立层不产连线**）｜ **128 元素**（★ 第 16 批现行；第 13 批读数 118、第 15 批 ＋10 见重钉块 ／ 第 4 批 144 ＋ **1 件组名底托**；★ 第 11 批 −12 ＋3；★ 第 12 批 −6；★ 第 13 批 −12）
      ★ 第 4 批（裁决 4）：本档只产**第 1 组**独立层 ⇒ 仅 **1 个入口热区**（`layer:frag1`），其余 5 组入口为纯占位
      ★ 第 7 批：底托换件（同上）⇒ 元素数不变（145）、几何与素材变
      ★ 第 8 批：**content-sha256 逐字不变** ⇒ 只有屏 note 措辞变
      ★ 第 9 批：**content-sha256 逐字不变**（本档无表内标题；元素内容未动）⇒ 只有屏 note 措辞变
      md5 = 4ed7585a16ea700343328a962a9eb95a ｜ content-sha256 = b581b226459b48a2bac0687765b375b91bab51c0e3e55d74a0a9c7145afc2cd3
      ★ 第 10 批：**content-sha256 逐字不变**（`frag` 档展示的组内无表内标题）⇒ md5 变因**仅屏 note 共用**
      ★ 第 11 批：元素 **145 → 136**（右栏 −12 ＋3）⇒ md5 与 content-sha256 **都变**
      ★ 第 12 批：元素 **136 → 130**（−6 = 6 件 `fc.label.<NNNN>` 底板）⇒ md5 与 content-sha256 **都变**
      ★ 第 13 批：元素 **130 → 118**（−12 = 12 件 `fc.mtab*`；`fc.fusen_*` 6 删 / `fc.mode_*` 6 增相抵）⇒ md5 与 content-sha256 **都变**
  full（**不是交付样例**；只交数据）  python 工具/gen_flow_layout.py --preset full
      6 段 / 19 道 / 712 lane 节点（section 579 / select 77 / frag 53 / branch 3）｜ **不产 elements**
      → _工作\\ISSUE-20260928-02_第2步\\全量布局.json（元素化渲染交编程组）
  文字参数（五预设共用）：字号 19px / 行距 1.0（元素级 line_spacing）/ 文字盒 240 / max_lines 2；
  四判据实测最小值：上留 5px、下留 5px、最宽行 228.0px、截断 0。
  番外组名（五预设共用）：经 `GROUP_CN_MAP` 中文化的 6 个组名（ISSUE-20260927-06）——映射 3 组、透传 3 组。
  连线（五预设共用口径）：`state` ∈ normal(#266080 / w4 / 有箭头) ｜ visited(#3580A8 / w4 / 有箭头) ｜ noroute(**#5A5A68** / w3 / **无箭头**)。
  ★ **裁决 4（第 4 批 · 2026-09-28 主代理）：入口热区 `fc.entry.<NNNN>_hit` 只在该组独立层确实产出时才产。**
    · `screen1` 产全部 6 组 ⇒ **6/6 入口热区**；`frag` 只产第 1 组 ⇒ **1**；`screen2`/`ref150`/`states` 不产独立层 ⇒ **0**。
    · 未产出 ⇒ 入口 image / 组名文字件（`fc.label.<NNNN>_tx`；**第 12 批起底板已删**）**仍在**
      （主干层可见的**纯占位**、不可点），元素数各档相应减少（−6 / −5；**第 12 批另各 −6 ＝ 6 件 `fc.label.<NNNN>` 底板**）。
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
       实测 712 条 **违规 0**、最紧 **+34.00**（`s01_02b`）。
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
  ★ **第 11 批重钉（2026-09-29 · `ISSUE-20260929-02` · 右栏「章节详情」大改 · 用户 6 条指令）**：
    上表**前五行**为现行值；本批之前各批的全部 md5 / content-sha256 值**一律作废**。
    · **本批只动右栏**（**用户指令 1–4**；左栏图表区一字不改）：**删元素 12 件**（`fc.mini1..8` /
      `fc.mapview` / `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx`；**只删元素，素材一个不删**）
      ＋ **新增 3 件**（`fc.play_win` / `fc.play_view` / `fc.pbkick_pause`）
      ＋ **改 8 件**（三槽底 `y`、三个 `_tx` 的白字＋黑描边与「说明/台词」扩槽、
      `fc.pbkick` 与 `fc.pbkick_hit` 移到大播放窗中央且后者 `action=flow_replay_toggle`）。
      ★ **第 2 轮裁决（2026-09-29）**：「说明/台词」两件的 `max_lines` 由 **5 改 4**
      —— 槽净高 159 ÷ 行盒 **33px**（＝ `floor(24 × 全局 line_spacing.body 1.4)`，
      `krkr/game/ui_theme.tjs:237-238` ＋ `layout/_root.json:66`）＝ 4.82 ⇒ **4 行**（4 行 132 ✓ / 5 行 165 越槽底 6px ✗）；
      **不加**元素级 `line_spacing`（保持全局基线）。该轮**同时**推翻正文里第 11 批首版的「24×1.3＝31.2 ⇒ 5」算法（错）。
    · 屏级 `flags_default` 新增 **`fc_replay:"play"`**（播放/暂停键同位置互斥：`play`＝播放键 / `pause`＝暂停键）。
    · **元素数**：`screen1` 289 → **280**、`screen2` 133 → **124**、`ref150` 112 → **103**、
      `states` 126 → **117**、`frag` 145 → **136**（每档 −12 ＋3；五档共用同一静态件快照 ⇒
      **五档的 md5 与 content-sha256 全变**，与以往「只有 note 措辞变」的批次不同）。
    · **生成器自检的唯一放宽（留痕）**：`STATIC_FLAG_EXEMPT = {"fc.pbkick", "fc.pbkick_pause"}` ——
      `fc_replay` 不是层旗标、初值 `"play"` 在**任何层**都成立 ⇒ 播放键恒可见；两处自检认该集，
      **集外仍严格拒绝**（把该集临时置空跑一次，判据必须如旧报错）。
    · ★ **交付样例基线总账需同步（属 E3/主代理范围，未在本脚本）**：
      `_工作\\ISSUE-20260928-02_第2步\\复现脚本\\m06_delivered_sample_ledger.py` 的 `DECLARED`
      必须追认本批的增删改，否则 `run_all` 必 FAIL。
  ★ **第 11 批·第 3 轮重钉（2026-09-29 · vision 实机复审后的两处真缺陷修复）**：上表**前五行**为现行值；
    上一条（第 11 批首轮 / 第 2 轮）的全部 md5 / content-sha256 值**一律作废**。
    ① **右栏台词槽与「进入本章」按钮重叠 52px**（本批引进）⇒ 三槽 `h 171→150`、四段重排
      （`fc.p_title y534` / `_tx y544` · `fc.p_text y617 h150` / `_tx y623 h138` ·
      `fc.p_message y777 h150` / `_tx y783 h138`）；**台词底 927 → `fc.jump` 上沿 943 ＝ 16px 无重叠**；
      `max_lines` **仍 4**（krkr `floor(24×1.4)=33` ⇒ 138÷33＝4.18；HTML 保守 4×34＝136 ≤ 138，余 2px）。
    ② **动态层占位标签横向溢出**（`fc.play_view` 第二行墨迹 x1456..1918，戳出窗 1822 / 栏 1859 / 屏 1919）⇒
      两端**逐行按元素可用宽截断并追加 `…`**（不换行）；krkr 度量 `Font.getTextWidth`，HTML 离屏 span。
    · **元素数不变**（280 / 124 / 103 / 117 / 136）——但右栏六件的 `y`/`h` 变 ⇒ **五档 md5 与 content-sha256 全变**。
    · **本轮的基线总账需同步（属本模块范围，已办）**：`m06_delivered_sample_ledger.py` 的 `DECLARED`
      已按新值追认 `fc.p_title`/`fc.p_title_tx`/`fc.p_text`/`fc.p_text_tx`/`fc.p_message`/`fc.p_message_tx` 的 `y`/`h`
      （否则 `run_all` 必 FAIL）。
  ★ **第 12 批重钉（2026-09-29 · `ISSUE-20260929-04` · 流程图页四件收尾 · 用户 2026-09-29 追加裁决）**：
    上表**前五行**为现行值；本批之前各批的全部 md5 / content-sha256 值**一律作废**。本批五件事：
    ① **新增满幅背景 `fc.bg`**（**用户指令 4′**）：`kind:"image"`、`(0,0,1920×1080)`、素材
      `ui/x_bg_flowchart.png`（`美术统一_超分\\CG背景\\bg72.png` 2560×1440 → **0.75× LANCZOS** 降采样；
      该目录被 `.gitignore` 排除 ⇒ 只落降采样成品）、**`z:0`**（在 `fc.dim` z1 之下）、**无 `nine`**（1:1）、
      外壳件（不写层旗标，两态共用舞台）。
    ② **删 `fc.sysbar`**（用户裁定）：`sysbar` 屏删除后留在本屏的**遗留装饰条**（无文字、无点击）；
      **素材 `ui/x_ui_sysbar.png` 保留不删**。
    ③ **`fc.zoom_knob` 换件删 `nine`**（**用户指令 1**）：`asset` → `ui/x_ui_zoom_handle.png`
      （**40×31 单一竖圆角胶囊手柄**）、**删 `nine`**（旧件 29×16 内含**横胶囊＋圆点两个图形** ⇒ 实机上是「两坨」）；
      `(1174,112,40×31)` / `z:21` / `opacity:255` 不变；旧件 `x_ui_zoom_knob.png` 退役、**文件保留不删**。
    ④ **`fc.p_title` / `fc.p_title_tx` 三槽对齐**（**用户指令 4**）：`fc.p_title` `x/w` **1416/443 → 1425/422**、
      `fc.p_title_tx` `x/w` **1428/419 → 1437/398** ⇒ 与 `fc.p_text`/`fc.p_message` 及其 `_tx` 的 `x/w` **逐字相同**（口径 A）。
    ⑤ **番外入口统一为「淡黄节点形块」＋ 组名底板退役**（用户追加裁决：「`fc.label.000x` 与 `fc.entry.000x`
      一律删去，统一为**和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状，只是底色换成淡黄**；文字方案不动」）：
      · `fc.entry.<NNNN>` **改形制**：86×48 付箋 → **296×65 淡黄节点形块**（素材 `ui/x_ui_entry_frag_{off,on}.png`
        **由 `x_ui_node_select_{off,on}.png` 派生**、alpha 逐字节同源）、`nine{l14,t0,r13,b0}`（与 `fc.node.*` **完全一致**）、
        `z:20`、`state_assets{normal,hover}`；**职能＝「进入该 xx 番外章节」**＝热区 `action:"flow_layer"` + `layer:"frag<G>"`
        （＝用户说的 `fc_layer - fragx`，**action/layer 一字未改**）。
      · `fc.label.<NNNN>`（**底板 image 333×38**）**已删**（**只删元素**；素材 `ui/x_ui_label_off.png` 保留不删）；
        `fc.label.<NNNN>_tx` **保留**（**文字方案未动**），矩形改与入口块**同矩形** `(60, y, 296×65)`，
        `y` ＝ **242/337/432/527/622/717**（＝原 `fc.label.<NNNN>` 的行位；行距 95 不变）。
      · **文字容量实测**（真实语料 ＋ 引擎折行算法）：6 条组名在 16px / 盒宽 296 下**全部单行**
        （最长「番外·群像（新年行军 / 格兰玛尼耶）」**265.0px** ≤ 296，且 ≤ 入口块可见实体面带宽 280）⇒
        **维持 `wrap:true` + `max_lines:1`，不新增字段**。
    · **元素数**：**`screen1` 280 → 274**、`screen2` 124 → **118**、`ref150` 103 → **97**、
      `states` 117 → **111**、`frag` 136 → **130**（每档 −6 ＝ 6 件 `fc.label.<NNNN>` 底板；`fc.sysbar` 与 `fc.bg` 相抵
      ⇒ 外壳 **52 不变**）⇒ **五档的 md5 与 content-sha256 全变**。
    · **左栏图表区未改**：入口块右缘 356 ≪ 最左节点槽 516 ⇒ 与节点道带零重叠（横向间隙 **+160px**，
      生成器落盘前自检打印）；道带位置因 `ENTRY_COL_W` 仍取 333 而**逐字不变**（节点/连线几何零变化）。
    · **落盘前自检（新增 · 真不变量）**：入口块**全部落进图表视口**且**彼此零重叠**，违反即拒绝落盘
      （本工程教训：重排前先清点邻居）。★ 行距较大的档（`ref150` step_y=150、`screen2` 的个别锚点行）
      其 **+52 落点会越出视口下沿** ⇒ 入口块**回落到本行**（块高 65 < 行距 ⇒ 仍不压上一块）；
      实测 `ref150` 入口 y ＝ **242/392/542/692/842/940**、`screen2` ＝ **242/337/950/432/527/622**。
    · **闸门同步（本模块范围）**：`m06` 总账追认 1 增 / 7 删 / 字段改动（**含 `nine` 的删与增**，
      后者由 `m06` ⑦ 的 `nine` 专项变异自证证明「确实参与比对」）；`m03` 基坑口径改
      `fc.bg`＋`fc.dim`＋`fc.scroll`、`states` 元素数 111；`m02` 右栏 z 序补 `fc.bg`（z=0）为**最低位**
      （`fc.bg` < `fc.dim` < 栏底 …）。
  ★★ **第 13 批重钉（2026-09-29 · `ISSUE-20260929-05` · 模式入口收敛 ＋ 删备注功能与对话框提示）** ★★
    上表**前五行**为现行值；本批之前各批的全部 md5 / content-sha256 值（含第 12 批的
    `1b0c2ba6…`／`7a37f9ef…`／`d013257e…`／`41db5009…`／`899ee92b…`）**一律作废**。本批四件事：
    ① **删 4 个模式页签**（用户指令①②）：`fc.mtab1..4` ＋ `_tx` ＋ `_hit` = **12 件**（文案 序章／本篇／
      After Story／Fragment）；原 4 页签位置（`y33..77`）**不再有页签带**。
    ② **加两枚文字入口**（用户指令②）：`fc.mode_main_glow`/`_tx`/`_hit` ＋ `fc.mode_frag_glow`/`_tx`/`_hit`
      = **6 件** —— **「本篇集合」/「番外故事」**。几何（接口冻结 §B ＋ **E5 订正**）：两枚 **180×60**
      〔`_glow`/`_hit` **@y25**；**`_tx` @y33** ＝ ★ **E5 文字下移 8px**，用户 2026-09-29 裁决〕
      （`_glow`/`_hit` 60 高居中于旧页签带中线 55 ⇒ 占 25..85，与下方标题牌 y93 留 8px；
       `_tx` 下移 8px ⇒ 占 33..93，与标题牌**贴边 0px**、半开区间 ⇒ 零重叠）、x = **34 / 254**（等宽 180、
      **间距 40**）、三件 z = **10 / 20 / 95**；`state_group` = `mode_main` / `mode_frag`；
      `action` = **`flow_mode_main` / `flow_mode_frag`**（**拟用名**：命中即派发，切集/筛选留编程组，
      已登记进 `layout/_schema.md` §六 动作表）；三态素材 `ui/x_ui_modetab_{off,over,press}.png`
      （**180×60 ×3，两入口共用同一套**）；文字 30px / `bold:false` ⇒ 引擎默认字体族首位即**微软雅黑 Regular**，
      白字 ＋ 黑描边 2px ＋ 但**「白淡光」由底层 `_glow` 图给**。
      ★ **E5 订正（用户 2026-09-29 裁决「两个模式入口的文字下移 8px」）**：两件 `_tx` 的 `y`
      **25 → 33**（`_glow`/`_hit` **仍 25**）；实测原墨迹 y31..63/中心 47 vs 框中心 55 ⇒ 下移后
      墨迹 y≈39..71、中心 55 与框同心。**五档金标与 `content-sha256` 因此全变**（`y` 是被绘制的载荷字段）。
    ③ **删备注功能键**（用户指令③）：`fc.fusen_edit`/`fc.fusen_reset` ＋ `_tx` ＋ `_hit` = **6 件**
      （用户点名 4 件，另两个 `_hit` 若不删会留下指向空动作的死热区 ⇒ 一并删；与冻结 §A 同口径）。
      另 `layout/screens/10_dialog.json`（**手工维护**）删 `dlg.hint` = **1 件**（用户「对话框页」指令）。
    ④ **删 19 件 / 加 6 件 ⇒ 净 −12 件**（**只删元素，素材一个不删**）：
      `screen1` **274 → 262**、`screen2` **118 → 106**、`ref150` **97 → 85**、`states` **111 → 99**、
      `frag` **130 → 118**；外壳 **52 → 40**（−18 ＋6）、图内容层 **222 不变**；`dialog` **10 → 9**（冻结 §E 记「18 → 17」为绝对值笔误）；
      **17 屏合计 1404 → 1391**。⇒ **五档的 md5 与 content-sha256 全变**（见上表五行 `md5 = …`）。
    · **三态口径（勿误解）**：三态**全靠 `_glow` 底光图承载**（同一枚柔和白淡光的弱/强/实底三档；
      `_press` ＝ 半透明冰蓝实底胶囊 ＋ 1px 亮边，且**整体比 `_off/_over` 的底框下沉 1px**）；
      `_tx` 的文字由**引擎绘制**、schema 不支持文字带 `state_assets` ⇒ **文字不参与换态**。
      ⚠ 用户原话「**文字下移 1px**」**无法实现**（不支持文字逐态位移、`state_group` 只配对图片层）
      ⇒ 以「**底沉 1px**」等价表达；如需文字本体位移须给引擎加「逐态位移」新接口（**新裁决**）。已写进交接文档。
    · **落盘前自检（新增 · 真不变量）**：两枚模式入口各 3 件**同矩形**、**完整落在画布内**、**彼此零重叠**、
      且**与任何相邻元素零重叠**（满幅层 `fc.bg`/`fc.dim` 视作画布底、不计入邻居）——违反即**拒绝落盘**；
      实测与 `fc.titleplate` 竖直间隙 **8.0px**、与 `fc.close` **92px**、与 `fc.scroll` **105px**、与右栏 ≥**990px**。
      `--selfcheck-mode-entries` 是其**变异自证**（重叠／越出画布／压住 `fc.titleplate` 三条变异各须被检出）。
    · **闸门同步**：`m06` 总账（**18 删 / 6 增 / 新件载荷字段追认**：`state_group`/`state_assets`/`action`
      —— 并把 `state_group` **补进 `APPEARANCE_FIELDS`**，此前它不在清单里）、
      `m03`（`states` 元素数 **111 → 99**，`_read` 仍 3 件）、
      `m02`（两件 `fc.fusen_*` **移出**「九宫格件」名单 ⇒ 由**等强度的三段新断言**接手：
      ① 六件 `fc.mode_*` 的三态素材在库且与元素 **1:1／无 `nine`**；② `fc.mode_*_hit` 的 `action` **非空**
      且**能在 `_schema.md` §六 动作表里查到**；③ 同 `state_group` 的 `_glow` 与 `_hit` **配对**且三态齐；
      另加**反向断言**「18 件旧件**均不在屏数据里**」⇒ **只增不减覆盖**）、`m01`（消费同一总账）。
    · **死引用排查（实测）**：`krkr/game/*.tjs`（含巡演 `UIScrTourSteps`）／`复刻/*.js`／`复刻/*.html`
      对 19 件**零「按 id 取值后解引用」**（仅 `ui_dialog.tjs:190`、`replica.js:3442/5529` 三处为屏数据定义/注释）；
      巡演按屏与 `action` 选点、`_selftest_states.html` 对 flowchart 是**数据驱动遍历**（无硬编码计数）
      ⇒ **删元素零悬空引用**（见 `_工作/ISSUE-20260929-05_模式入口/证据/E2_自检报告.md`）。
  ★★ **第 15 批重钉（2026-09-30 · `ISSUE-20260930-02` · 章节详情 · 用户裁定 5/6/7）** ★★
    ⚠ **本节所述五组值为第 15 批当时的现行值，已被下方「第 16 批重钉」取代**（上面各档行首的 md5/content-sha256
    已由 `--refresh-golden` 刷为第 16 批真值；本节的散文计数只作历史留痕，**不得再当现值引用**）。
    本批之前各批的全部 md5 / content-sha256 值（含第 13 批的
    `7fa46f2f…`／`642cf515…`／`5655e08a…`／`d84014c5…`／`a1b92d6b…`）**一律作废**。本批三件事：
    ① **浮层尺寸 1240×652 → 1240×400**（用户裁定 6）：`fc.intro_bg`/`fc.intro_panel_hit` 几何
      **@340,340、w1240 h400**（版面中心：右缘 1580、下缘 740、中心 (960,540)）——
      起因＝vision 实测正文仅占面板 ~1.5%、观感像未完成；`fc.intro_title_tx` **1176×44 @372,246
      → 1140×44 @372,372**（宽收 36px 给关闭件让位；右缘 1512 与关闭件左沿 1530 留 18px）；
      `fc.intro_text_tx` **1176×528 @372,306 → 1176×276 @372,432**（y ＝ 标题底 416 + 16；
      面板底 740 − 32 留白 = 708 ⇒ h 276；6 行 ×33 = 198 ≤ 276）。
    ② **新增关闭件 2 件**（用户裁定 5「加一枚小 ×」·**零新素材**，复用既有 `x_ui_close_*`）：
      `fc.intro_close`（image **26×26 @1530,364**、`state_assets{normal:_off,hover:_over,pressed:_on}`、
      `state_group:"intro_close"`、**`nine{6,6,6,6}`（同 `fc.close`）**、**z236**）
      ＋ `fc.intro_close_hit`（hit **46×46 @1520,354**、`action:"flow_intro_close"`、同 `state_group`、**z237**）。
      ⇒ 浮层族 6 → **8 件**、外壳 **48 → 50**、`screen1` **270 → 272**（五档各 **＋10**：
      **272 / 116 / 95 / 109 / 128**；17 屏合计 **1391 → 1401**）。**z 序硬约束**：关闭件 z 必须**高于**
      面板热区 `fc.intro_panel_hit`（230），否则点关闭被面板的「空动作＝吞点击」吃掉 ⇒ 新增
      落盘前自检**专条断言**（`fc.intro_close_hit.z > fc.intro_panel_hit.z`）＋ `--selfcheck-intro-overlay`
      **变异 G**（把 z 降到 230 必须被检出）。⚠ 两件均列入 `STATIC_FLAG_EXEMPT` 与 `PASSTHROUGH_REQUIRED`。
    ③ **加号按钮 y 625 → 618**（用户裁定 7「垂直对齐到首行行盒中心」）：`fc.p_plus`/`fc.p_plus_hit`
      同移（仍同矩形 44×44 @1803,618；y 区间 618–662 完整落在面板 617–767 内）。
      **不宜取 613 之类**（会顶出面板上缘 617）；加号素材外圈环改**按目标尺寸 1:1 直绘**。
    ⇒ **五档的 md5 与 content-sha256 全变**（几何与元素集合都变；content-sha 也该变）。
    · **判据口径对齐引擎（第 2 轮 · 一审建议项）**：浮层自检的「既有热区最高 z」由
      `kind=="hit"` ＋ `isinstance(z,int)` 改为 **`kind ∈ {hit,list}` ＋ `_z_num()` 数值化**
      （引擎 `uiScreenClick` 的候选即这两种 kind、z 按数值比较）⇒ 补两条负向对照（变异 H「z 写字符串」、
      变异 I「kind 换 list」），自证由 6 条扩为 **9 条**。
    · **引擎侧证据**（第 2 轮补齐）：巡演新增 `kind:"wrapellip"` 步直调 `uiThemeWrap` 打 `★WRAPELLIP★`
      （长文本 ⇒ 4 行 + 末行 `……` + 末行宽 ≤ maxW；短文本 ⇒ <4 行且无 `……`；极窄 maxW ⇒ 3 行且无 `……`），
      另一条 `★WRAPELLIP-REJECT★` 负向对照。
  ★★ **第 16 批重钉（`ISSUE-20260930-06` · 2026-09-30 · 番外独立层改纵向流水）** ★★
    上面各档行首的 `md5` / `content-sha256` 已由 `--refresh-golden` 实跑重钉为**本批真值**
    （五组：screen1 / screen2 / ref150 / states / frag）。本批**只动 `screen1` 的元素集合**；
    其余四档元素集合不变，两个摘要因**屏 note 措辞共用**而变化（可用内容 sha 判「是措辞还是内容」）。
    ① **行数 = ceil(章数/3)、不设上限**；`cap` 与视口派生的行上限一并取消；`--frag-limit` 语义保留（缺省＝全量）。
    ② **裁剪口径放宽**（本批唯一的判据放松）：独立层元素改判「`x` 完整落视口 **且** `y ≥ 视口顶`」⇒ **允许纵向溢出**；
       **有意偏离** §九 裁决 5；主干节点判据**一字未改**。
    ③ `screen1` **272 → 296**（＋24 ＝ G6 的 13–20 格 × 3）、图内容层 **222 → 246**、独立层节点 **135 → 159**、
       **外壳 50 不变**；五档 **296 / 116 / 95 / 109 / 128**；17 屏合计 **1401 → 1422**（★ D-01：`title` 18→24 ⇒ **现行 1428**）
       〔★ 中间值 1425（＝ flowchart 单项 +24、**未减 config 的 −3**）**只作历史留痕**；冻结 §7.1 勘误 4 定终值 **1422**〕。
       **素材零新增**（1359 件 / 100,604,112 B 不变）。
    ④ **G6 20/20**；需纵滚的行 y = 1054 / 1246 / 1438（末行下沿 1503）。
    ⑤ 层固定件（`fc.frag<G>_title_bg` / `_title` / `_back*`）**位置不变、不随滚**；可滚对象＝节点行。
    ⑥ HTML 侧若对画布 `overflow:hidden`，**y > 1080 的节点需纵滚才可见**（不改 JS；呈现归编程组）。
    ⑦ **冻结 §7.2 可见性契约（一审后返修）**：元素盒下沿 `y + h > 视口底 1017` 的行，其**三件**一律
       `visible_default:false`（**数据完整产出、默认不画**；纵滚到位时由编程组置真 —— 与 config 屏既有
       「`visible_default:false` ＝ 预留下但默认不画」**同源，不新造机制**）。**只加字段、不加元素**（仍 296）。
       ⇒ **产出 53 格 ＝ 数据完整；默认可见 12 格（4 行）；其余 8 格需纵滚置真**（★ 口径以**唯一有溢出的第 6 组**为准；
       全屏默认可见 ＝ G1–G5 共 33 格 ＋ G6 前 4 行 12 格 ＝ **45 格**，其余 8 格置真）。
       落盘前**双向**自检：溢出却默认可画 / 未溢出却默认不画 ⇒ 均拒绝落盘。
    ⑧ 闸门同步：`m02` 的 `check_frag()` 改 `rows=ceil(n/3)` 口径 ＋ **变异自证**（节点数 −1、几何 +1px 各须被检出），
       并对 `screen1` 的 G6 溢出格断言 `visible_default:false` ＋ **变异自证**（把一格改回 `true` 必须被检出）；
       `m06` 的 `DECLARED_NEW_IDS` 追认 G6 的 13–20 格 ×3 ＝ 24 件新增几何 ＋ 断言其 `visible_default:false`
       （变异自证同上）；`layout\\_schema.md` 金标表与 `layout\\screens\\_index.json` 金标行随之重钉。
  （`--refresh-golden` 只重钉上表五组的 `GOLDEN` 字面量，**本表要改**——散文数字由
   `assert_preset_table_sync()` 的两向断言守住，见该函数。）
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
    """把实跑得到的五组 (md5, content-sha) 回填进本文件的 GOLDEN 字面量。

    ★ 第 11 批收口（一审阻断项 1）：**同时回填 `PRESET_TABLE` 里那 5 行 `md5 = …` /
    `content-sha256 = …`** —— 该表是 `--help` 的判读依据、一直是**手写**的，此前没有任何闸门
    覆盖它；第 3 轮重钉后它静默留着第 1/2 轮的中途值（一审实测：`GOLDEN` 的五个新值一个都不在表里）。
    ⇒ 一把梭进刷新流程（行序即 `GOLDEN_ORDER`），并由 `assert_preset_table_sync()` 在刷完后自证。
    """
    text = open(os.path.abspath(__file__), encoding="utf-8").read()
    for name, md5v, shav in rows:
        pat = r'("%s": \()("[^"]*", "[^"]*")(\))' % name
        text = re.sub(pat, lambda m: m.group(1) + '"%s", "%s"' % (md5v, shav) + m.group(3), text)
    # ── 同步 `PRESET_TABLE`（有序；行序 == 传入 rows 顺序 == GOLDEN_ORDER）──────────
    md5s, shas = [r[1] for r in rows], [r[2] for r in rows]

    def _sync(tbl):
        """在**任一份表文本**上按序替换 md5 / content-sha256 字面量 → (新文本, md5 处数, sha 处数)。

        ⚠ **必须对两份都做**：① 写回磁盘的那份；② **本进程内存里的 `PRESET_TABLE` 全局** ——
        否则 `--refresh-golden` 末尾那次自证（`assert_preset_table_sync`）读到的还是**旧的**内存值，
        会自相矛盾地报 FAIL（本批第 3 轮实测踩到：刷新其实成功、退出码却是 1）。
        """
        it_m, it_s = iter(md5s), iter(shas)

        def _m(m):
            try:
                return "md5 = " + next(it_m)
            except StopIteration:
                return m.group(0)

        def _s(m):
            try:
                return "content-sha256 = " + next(it_s)
            except StopIteration:
                return m.group(0)

        t, nm = re.subn(r"md5 = [0-9a-f]{32}", _m, tbl)
        t, ns = re.subn(r"content-sha256 = [0-9a-f]{64}", _s, t)
        return t, nm, ns

    global PRESET_TABLE
    text, n_m, n_s = _sync(text)
    PRESET_TABLE, n_m2, n_s2 = _sync(PRESET_TABLE)
    assert (n_m, n_s) == (n_m2, n_s2), \
        "内存表与磁盘表的同步处数不一致（%s vs %s）" % ((n_m, n_s), (n_m2, n_s2))
    # ★★ 第 12 批修复（真缺陷 · 由本批实测暴露）：**内存里的 `GOLDEN` 也必须一起更新**。
    #   上面那条 ⚠ 注释只治了 `PRESET_TABLE` 的内存副本，**漏了 `GOLDEN`** ⇒ `--refresh-golden`
    #   末尾那次 `assert_preset_table_sync()` 拿「内存 GOLDEN（旧值）」比「内存 PRESET_TABLE（新值）」
    #   ⇒ **必然 FAIL、退出码 1**（文件其实已正确写盘）。本批实测复现：
    #   `python 工具\gen_flow_layout.py --refresh-golden` 打印「已重钉 5 组金标」后立刻报
    #   `[FAIL] PRESET_TABLE 与 GOLDEN **不一致**（5/5 组）：… 表 1b0c2ba6… ≠ 金标 a84a1876…`。
    #   修法＝`GOLDEN.update(...)`：让「内存态 == 磁盘态」，自证才有意义（否则它只是恒假的噪声）。
    GOLDEN.update({name: (md5v, shav) for name, md5v, shav in rows})
    with open(os.path.abspath(__file__), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[golden] 已重钉 %d 组金标（GOLDEN %d 行）；PRESET_TABLE 同步 md5 %d 处 / content-sha256 %d 处"
          % (len(rows), len(rows), n_m, n_s))
    for name, md5v, shav in rows:
        print("  %-8s md5=%s  content-sha256=%s" % (name, md5v, shav[:16] + "…"))


def assert_preset_table_sync():
    r"""★ 第 11 批收口（一审阻断项 1）：**`PRESET_TABLE` 与 `GOLDEN` 必须逐组一致**。

    为什么要有这条：`PRESET_TABLE` 是 `python 工具\gen_flow_layout.py --help` 的 `epilog`，
    是**人读金标的唯一入口**；它**手写**、且**此前无任何闸门**（`复现脚本\` 与 `工具\` 全库无引用）
    ⇒ 本批第 3 轮重钉后它静默留着第 1/2 轮的中途 md5，一审把它抓了出来。
    判别力：唯一合法的改动路径是 `--refresh-golden`（它现在**自动**同步该表）⇒ 本条能变红的情形
    只有「有人手改了 `GOLDEN` 却忘了改表」—— 正是本批踩到的那个坑。`_REFRESHING` 期间跳过
    （那一刻表本来就该旧），刷新**之后**再断言一次，所以刷新路径本身也被自证覆盖。
    """
    if _REFRESHING:
        print("[golden] （--refresh-golden 进行中：PRESET_TABLE 一致性断言延后到刷新之后）")
        return
    md5s = re.findall(r"md5 = ([0-9a-f]{32})", PRESET_TABLE)
    shas = re.findall(r"content-sha256 = ([0-9a-f]{64})", PRESET_TABLE)
    want = [(GOLDEN[n][0], GOLDEN[n][1]) for n in GOLDEN_ORDER]
    if len(md5s) != len(want) or len(shas) != len(want):
        raise SystemExit("[FAIL] PRESET_TABLE 内 `md5 =` / `content-sha256 =` 行数 %d / %d ≠ 预设数 %d"
                         "（表被改坏或漏行）" % (len(md5s), len(shas), len(want)))
    bad = [(GOLDEN_ORDER[i], md5s[i], shas[i], want[i]) for i in range(len(want))
           if (md5s[i], shas[i]) != want[i]]
    if bad:
        raise SystemExit(
            "[FAIL] PRESET_TABLE 与 GOLDEN **不一致**（%d/%d 组）：%s\n"
            "       ⇒ 跑 `python 工具\\gen_flow_layout.py --refresh-golden` 自动同步该表（**勿手改**）"
            % (len(bad), len(want),
               "；".join("%s：表 %s/%s ≠ 金标 %s/%s" % (n, m[:12], s[:12], wm[:12], ws[:12])
                         for n, m, s, (wm, ws) in bad)))
    # ── ★ 第 3 轮（二审 B1）：散文数字的两向断言（现行串必须**逐源**在 / 作废串任一源都不得在）──
    #   实测踩到过「同一张表里 `255px` 与 `228.0px` 并存」——第 1 轮只治了 md5/sha 那两列。
    #   ⚠ **逐源判**：并成一个 blob 判「必须在」时，「只从表里删掉现行串」不会被抓到（见常量处注释）。
    for src_name, src_text, want_snips in (
            ("PRESET_TABLE", PRESET_TABLE, REQUIRED_PRESET_TABLE_SNIPPETS),
            ("SCREEN_NOTE", SCREEN_NOTE, REQUIRED_SCREEN_NOTE_SNIPPETS)):
        missing = [t for t in want_snips if t not in src_text]
        if missing:
            raise SystemExit("[FAIL] `%s` 缺**现行口径**字符串（口径变了却没同步）：%s"
                             % (src_name, missing))
    retired = [t for t in RETIRED_TABLE_SNIPPETS if t in (PRESET_TABLE + SCREEN_NOTE)]
    if retired:
        raise SystemExit("[FAIL] `PRESET_TABLE`/`SCREEN_NOTE` 里仍留着**已作废**的数字串：%s\n"
                         "       ⇒ 订正为现行值；若该串是「历史留痕」而非现值断言，请改写措辞"
                         "（如「旧单行 255px」）以免与本断言冲突" % retired)
    print("[golden] PRESET_TABLE 与 GOLDEN 五组逐组一致 ✓；散文数字：现行串（表 %d / 屏 note %d）逐源在、"
          "作废串 %d 项不在 ✓"
          % (len(REQUIRED_PRESET_TABLE_SNIPPETS), len(REQUIRED_SCREEN_NOTE_SNIPPETS),
             len(RETIRED_TABLE_SNIPPETS)))


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
            "**层预算未验证**，且纵滚/横移机制是否属 UI 组能力未定 ⇒ "
            "**元素化 / 纵滚 / 横移 / 大播放窗内画面填充（`fc.play_view`）/ 缩放交编程组**。"),
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
            "**G-3 独立层「组内全量产出」已关闭**（★ 2026-09-30 · `ISSUE-20260930-06` · 用户裁定 5）：独立层自"
            "**2026-09-30 起改「纵向流水」** —— 行数 = ceil(章数/3)、**不设上限**，第 6 组 20 章由旧口径的 12 格"
            "全产为 **20 格**（`--frag-report` 逐组「未产 = 0」）。旧条目「网格 3 列 × 4 行、组内超出者不产」"
            "**已作废**。**裁剪口径亦随之放宽**（独立层元素只要求 x 完整落视口 且 y ≥ 视口顶 ⇒ 允许纵向溢出，"
            "**有意偏离** §九 裁决 5）；y > 视口底 1017/画布 1080 的行**由编程组的独立层纵滚呈现**"
            "（未滚到位时不可见＝预期，不得据此报缺件）。纵滚 / 横移 / 大播放窗内画面填充（`fc.play_view`）/ 缩放"
            "仍交编程组（冻结 §五）。",
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
    ap.add_argument("--selfcheck-mode-entries", action="store_true",
                    help="★ 第 13 批：模式入口几何自检的**变异自证**"
                         "（重叠/越出画布/压住邻居 三条变异各须被检出 ⇒ 自检能失败）")
    ap.add_argument("--selfcheck-intro-overlay", action="store_true",
                    help="★ 第 15 批：章节详情浮层几何自检的**变异自证**"
                         "（按钮与文字重叠 / 浮层 z 越界 / 文字出面板 / 热区不同框 / 关闭件 z 未高于面板热区 / "
                         "z 写成字符串 / kind 换成 list 等**九条**变异各须被检出）")
    ap.add_argument("--frag-groups", default=None,
                    help="番外独立层组号**列表**（逗号分隔，每个 1..6；★ 第 3 批：由单值扩为列表。"
                         "仅对非 full 预设生效，默认取预设 = screen1 为 1,2,3,4,5,6；frag 为 1）")
    ap.add_argument("--frag-group", type=int, default=None,
                    help="（旧名，等价 `--frag-groups <G>`；保留兼容）")
    ap.add_argument("--frag-limit", type=int, default=None,
                    help="**每组**独立层最多产多少格（★ 2026-09-30：默认＝**全量**＝ceil(章数/3)×3；"
                         "显式给值仍 min(给值, rows×3)）")
    ap.add_argument("--frag-report", action="store_true",
                    help="★ 2026-09-30 纵向流水口径：逐组报 章数/rows/可容/产出/未产（未产须为 0）"
                         "＋虚拟内容高度＋需纵滚的行清单；不落盘")
    ap.add_argument("--full-out", default=FULL_OUT,
                    help="--preset full 的输出路径（默认 _工作\\ISSUE-20260928-02_第2步\\全量布局.json）")
    args = ap.parse_args()

    if args.selfcheck_delivered:
        return selfcheck_delivered()

    if args.selfcheck_title_break:
        return selfcheck_title_break()

    if args.selfcheck_mode_entries:
        return selfcheck_mode_entries()

    if args.selfcheck_intro_overlay:
        return selfcheck_intro_overlay()

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
        global _REFRESHING
        rows = []
        _REFRESHING = True
        try:
            for name in GOLDEN_ORDER:
                scr, _st = preset_run(name)
                blob = serialize_screen(scr)
                rows.append((name, hashlib.md5(blob).hexdigest(), content_sha256(scr)))
        finally:
            _REFRESHING = False
        refresh_golden(rows)
        # ★ 刷新**之后**自证一次：`GOLDEN` 与 `PRESET_TABLE` 必须逐组一致（本批一审阻断项 1 的根治）
        assert_preset_table_sync()
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
    print("  ★ 产出元素视口内自证：%s（x+w 最大 %d ≤ %d ｜ **主干/外壳** y+h 最大 %d ≤ %d ｜ "
          "**独立层** y+h 最大 %d〔**允许 > %d**：有意偏离 §九 裁决 5，纵滚归编程组〕）%s"
          % ("全部落在视口内 ✓" if st["viewport_ok"] else "**越界 %d 件**：%s"
             % (len(st["elements_outside_viewport"]), st["elements_outside_viewport"][:6]),
             st["gen_max_right"], vp["x"] + vp["w"],
             st["gen_max_bottom_trunk"], vp["y"] + vp["h"],
             st["gen_max_bottom_frag"], vp["y"] + vp["h"],
             "" if st["viewport_ok"] else " ⇒ **拒绝落盘**（§九 裁决 5；独立层按豁免判据）"))
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
        print("  ★ 番外独立层（★ 2026-09-30 纵向流水口径）：**%d 组**（层旗标取值集 %s）｜ 网格 %d 列 × 步进 %d/%d、"
              "行首偏移 %d、原点 %s、**行数按章数派生（ceil(章数/3)，不设上限）**"
              % (len(st["frags"]), st["layer_vis_when"], f0["grid"]["cols"], f0["grid"]["step_x"],
                 f0["grid"]["step_y"], f0["grid"]["lead_y"], f0["grid"]["origin"]))
        for f in st["frags"]:
            g = f["grid"]
            print("     组 %d「%s」产出 %d/%d 格（rows=%d、内容下沿 %d、默认可见 %d 格 / 纵滚置真 %d 格%s）；"
                  "**不产连线**；按组返回键 %s；未产格 %s"
                  % (f["group"], f["group_cn"], f["produced"], f["rows_total"], g["rows"],
                     g["content_bottom"], f["cells_visible"], f["cells_scroll"],
                     " ⇒ **需纵滚**" if g["needs_scroll"] else "（在视口内）",
                     f["back_key"], f["dropped"] if f["dropped"] else "无"))
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
    # ★ ISSUE-20260929-02（冻结 §B.6）：带旗标的外壳件分「豁免集内（合法）」与「集外（违规）」两类，
    #   判据与 `build()` 的两处自检**同一份豁免集**（本打印是自证，不是第二套判据）。
    _shell_flag_ok = [i for i in _shell_flag if i in STATIC_FLAG_EXEMPT]
    _shell_flag_bad = [i for i in _shell_flag if i not in STATIC_FLAG_EXEMPT]
    _ok_note = ("（豁免集：%s —— `fc_replay` 非层旗标、初值 `play` 在任何层都成立 ⇒ 播放键恒可见）"
                % ", ".join(_shell_flag_ok)) if _shell_flag_ok else "（无豁免件）"
    print("  ★ 层旗标归属自证（第 3 批 ＋ ISSUE-20260929-02 冻结 §B.6 豁免集）：外壳件 %d 件，"
          "其中带 vis_flag 的 **%d 件** ＝ 豁免集内 %d 件%s ＋ 集外违规 **%d 件**%s；"
          "图内容层件 %d 件全部带 vis_flag ✓"
          % (len(_shell), len(_shell_flag), len(_shell_flag_ok), _ok_note,
             len(_shell_flag_bad), " ← **违规**" if _shell_flag_bad else "（✓ 集外零违规）",
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

# -*- coding: utf-8 -*-
r"""m06_delivered_sample_ledger.py —— ★ 交付样例「基线总账」（固定引用，不随 `HEAD` 漂移）

**这个闸门存在的理由**（一次真实事故，见 `工程记录\2026-09-28_对于流程图未解锁压暗件与已读标记的修改.md` §风险 10）：

`m01` 原先用 `git HEAD` 当对照。`:HEAD` 是**随提交粒度漂移**的靶子 —— 本批把生成器不变量与重生成的
产物**一并提交**后，HEAD 自己就含全部变更 ⇒ 相对 HEAD 的差异恒为 0 ⇒ 判据**再无证据可产**。
更糟的是靶子可能**坏掉**：本批初版提交 `98b43dd` 里那份 `layout/screens/32_flowchart.json` 实测是
**`--preset states` 的产出**（126 元素、含 `_dim`/`_read`/`_new`、无 `fc.frag*`；md5 `bbac0fd5…`），
而交付样例应为 **289 元素**；同批的 `layout\ui_layout.json`、`krkr\game\ui_layout.tjs`、
`复刻\ui_layout.js` 也是 states 派生（`ui_layout.tjs` 因此被削掉 3861 行）。

⇒ 本脚本把对照**钉死在固定引用 `BASE_REF`**（本批开工时的交付基线），于是本表成为
「**交付样例自基线以来的有意变更总账**」：

  · 新批有**意图**改动 ⇒ **追加**一条到 `DECLARED`（写清 old → new 与理由）；
  · 任何**未被追认**的差异 ⇒ **判失败**（含元素增删、字段漂移、连线几何变化、屏级字段变化）；
  · 声明了的条目**必须真的变了且等于声明的 new 值**（防表里留假条目 = 防豁免失效）。

**与 `m01` 的分工**：`m06` 管「**盘上现值 vs 固定基线**」（内容是否被偷偷改过）；
`m01` 管「**盘上 vs `HEAD`**」＋**基线健全性硬失败**（＝「提交进去的那份是不是交付样例」）。

**幂等**：只读（`git show` ＋ 读盘）；**不写任何产物、不动屏文件**。

★★ **已登记的覆盖缺口（E5 一轮 · S6 · 2026-09-29，只登记不改逻辑）**
本总账的对照对象**只有一屏**：`SCREEN_REL = "layout/screens/32_flowchart.json"`（下一行）。
⇒ **它只管「流程图屏有没有被偷偷改过」**；`layout/screens/_index.json` 列出的**其余 16 屏**
（含本批删了 1 件、且**手工维护、无生成器**的 `10_dialog.json`）**没有任何基线等值闸门**：
本批 `dlg.hint` 的删除**只由**「独立 diff」与 `verify_ui [3]`（三产物同值）兜住 ——
即「删得对不对」有人看，「相对基线少没少别的东西」**没人看**。
· 现状**不是缺陷**（各屏各有其闸门：`test_gen_sync` 管生成器同步、`verify_ui` 管引用/尺寸/三产物一致），
  但**性质不同**：那些是「与生成器/产物比」，**没有一个是「与交付基线逐字段比」**。
· **扩到全部 17 屏属后续议题**（需要为每屏各钉一份固定基线 + 一张有意变更总账，
  `10_dialog.json` 这类手工屏还要逐条登记历史改动）；本轮**不动**，只把缺口写在文件头，避免被当成「已覆盖」。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/m06_delivered_sample_ledger.py"
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
SCREEN_REL = "layout/screens/32_flowchart.json"
SCREEN = os.path.join(UI, SCREEN_REL)
GEN = os.path.join(UI, "工具", "gen_flow_layout.py")

# ══════════════════════════════════════════════════════════════════════
# ★ 固定基线：**本批开工时的 `main`（交付基线）** `ef68dcf`
#   · 对该屏文件，`ef68dcf` 与 `82e94ab`（`ISSUE-20260928-02` 第 2 批的交付提交）同值：md5 `4c8f01c0…`
#   · 选它而不是 `HEAD`：见文件头「理由」。它是 `main` 的既有历史，**合并后仍可达**。
#   · 若日后要换基线（例如再交付一批后重钉），改这一个常量 + 同步 `DECLARED` 即可。
# ══════════════════════════════════════════════════════════════════════
BASE_REF = "ef68dcf"
BASE_REF_MD5_EXPECT = "4c8f01c0c119c3df2da5b0adfe86e05e"   # 该文件在基线处的 md5（健全性佐证）

# 影响观感 / 行为的字段 —— 与 `m01` 保持**同一份清单**（两边不一致会漏判）
#   ★ 第 12 批（`ISSUE-20260929-04`）· E5 补全：**加入 `vis_flag` / `vis_when` / `layer` / `dynamic`**。
#     一审实测（本批字段补全 S3）：原清单**不含**这 4 个字段 ⇒ `vis_flag`/`vis_when`/`layer`/`dynamic`
#     的漂移**没有任何基线等值闸门**（上一批 `fc.pbkick` 新增 `vis_flag:"fc_replay"`/`vis_when:"play"`
#     正是这样被放过的；本批「`_hit.layer` 一字未改」这条不变量同样没有闸门）。
#     `layer` 是 `_hit` 的层跳转目标（`action:"flow_layer"` 用），`dynamic` 是运行期填充层的名字，
#     `vis_flag`/`vis_when` 是显隐谓词 —— 四者都**改变观感/行为**，本就该进本清单。
#   ★ 单一来源：`m01` 不再自带副本，改为 `from m06 import APPEARANCE_FIELDS`（见其 `load_ledger`）
#     ⇒ 此后**只改这一处**，不会两边漂移。
#   ★★ 第 13 批（`ISSUE-20260929-05`）· E2 补全：**加入 `state_group`**。
#     一审口径同 S3：它是**载荷字段**（决定「同组图片层一起换三态」的配对键）——本批新增的
#     6 件 `fc.mode_*` 全靠它把 `_hit`（z95）与 `_glow`（z10）绑成一对；而原先它**不在清单里**
#     ⇒ 该字段的漂移没有任何基线等值闸门（`fc.close`/`fc.close_hit` 的 `flowchart.close` 一直是裸奔的）。
#     本批补入；同时由 `m02` 的**三段新断言**做正向核对（三态素材在库且 1:1／`_hit.action` 非空且入动作表／
#     同组 `_glow`+`_hit` 配对且三态齐）—— 清单等值 + 正向断言**两道**都有。
APPEARANCE_FIELDS = [
    "kind", "x", "y", "w", "h", "asset", "z", "color", "opacity", "font", "align", "valign",
    "wrap", "max_lines", "sample", "nine", "state_assets", "state_group", "action", "label",
    "visible_default", "line_spacing",
    "vis_flag", "vis_when", "layer", "dynamic",
]
# ── 屏级字段里**允许**变化的白名单（不参与渲染判据）
SCREEN_FIELD_ALLOW = ("note",)

# ══════════════════════════════════════════════════════════════════════
# ★ 第 12 批（`ISSUE-20260929-04`）常量：入口块的 (旧 y, 新 y) 与落点偏移
#   · 旧 y ＝ 原入口标记行（锚定行本身：190/285/380/475/570/665）
#   · 新 y ＝ **原 `fc.label.<NNNN>` 标签的行位** ＝ 旧 y + 52
#     （52 ＝ 原「入口标记 48 高 + 4px 间隙」；对应生成器 `ENTRY_BLOCK_DY`）
#   ⇒ 交付样例入口块 y ＝ **242 / 337 / 432 / 527 / 622 / 717**（行距 95 不变）
# ══════════════════════════════════════════════════════════════════════
ENTRY_BLOCK_DY_12 = 52
ENTRY_Y_PAIRS_12 = {1: (190, 242), 2: (285, 337), 3: (380, 432),
                    4: (475, 527), 5: (570, 622), 6: (665, 717)}

# ══════════════════════════════════════════════════════════════════════
# ★★ 2026-09-30（`ISSUE-20260930-06` · 用户裁定 5）：**番外独立层改纵向流水** ★★
#   第 6 组由旧口径的 12 格全产为 **20 格** ⇒ 新增 8 节点 × 3 件（image/text/hit）＝ **24 件**
#   （相对基线 `ef68dcf`）。「几何追认」＝把逐格几何**钉在盘面值**上（`DECLARED_NEW_IDS` 只记
#   「这是新增的」，记不住它长在哪）；另加**反向断言**「G6 必须全量 20 格」（防回退到 12 格上限）。
#   几何常量**独立写出**（与生成器同值、不 import）⇒ 判据非恒真。
#   ⚠ `BASE_REF` **不得改**（改它等于拿会漂移的靶子当基线 —— 本脚本存在的理由）。
# ══════════════════════════════════════════════════════════════════════
FRAG_COLS_M06 = 3
FRAG_STEP_X_M06 = 375
FRAG_STEP_Y_M06 = 192
FRAG_LEAD_Y_M06 = 90
FRAG_ORIGIN_M06 = (6, 6)
FRAG_NODE_W_M06, FRAG_NODE_H_M06 = 296, 65
FRAG_TEXT_W_M06 = 240
FRAG_G6 = 6
FRAG_NEW_CELLS_6 = tuple(range(13, 21))      # 本批新增的 G6 第 13–20 格

# ══════════════════════════════════════════════════════════════════════
# ★★ 有意变更总账（相对 `BASE_REF`）—— **新批只追加，不改写历史条目**
#   结构：元素 id → { 字段: (改前值, 改后值, 理由) }
# ══════════════════════════════════════════════════════════════════════
DECLARED = {
    # ── `ISSUE-20260928-03` 第 9 批：vision 必改③（「已读对勾」不变量）──────────────
    #   元素 `fc.frag6.0007_tx`（script `62_1b`，番外第 6 组 0007 格）：
    #   旧单行 255px（首行墨迹左缘 +20.50 < 对勾右缘 +30 ⇒ 对勾压住首字左边）
    #   ⇒ 按 `TITLE_HARD_BREAK` 在「（」前插硬换行，两行 122 / 133px（左缘 +87）。
    #   生成器侧不变量与自证见 `工具/gen_flow_layout.py` 的 `TITLE_CHECK_GAP` /
    #   `--title-check-report` / `--selfcheck-title-break`。
    "fc.frag6.0007_tx": {
        "sample": (
            "无论何时·棱镜（性的意义上）",
            "无论何时·棱镜\n（性的意义上）",
            "第 9 批：「已读对勾」不变量（首行墨迹左缘 ≥ x_node+30）—— 单行 255px → 两行 122/133px",
        ),
    },
    # ── `ISSUE-20260928-04` 第 10 批：不变量收紧 +30 ⇒ +34（用户看完实机对照图后裁决）──
    #   起因：「零间隙边界簇」8 条满足 ≥+30 但余量只有 0–2px（4 条本来就是「236px 长行 + 2–3 字尾巴」的
    #   难看折行，其中 `42_4` 还把 `ＦＡＬＣＯＮ` 从中间切断）。该 8 条里**只有 2 条在交付样例里**：
    #   下面这两件各插一个硬换行（断点＝「（」前）。其余 6 条不在交付样例四档 ⇒ 不在本总账内。
    #   生成器侧见 `TITLE_CHECK_GAP = 34`、`TITLE_HARD_BREAK` 第 10 批 8 条、`--title-check-report`。
    "fc.frag4.0008_tx": {
        "sample": (
            "格兰·玛尼耶（ＥＡＧＬＥ）",
            "格兰·玛尼耶\n（ＥＡＧＬＥ）",
            "第 10 批：零间隙边界簇（旧 236px / 左缘 +30.00 ⇒ 间隙 0px）按硬断行表断在「（」前；"
            "103 / 133px（左缘 +81.5）。实机对照：间隙 1px → 65px",
        ),
    },
    "fc.frag4.0009_tx": {
        "sample": (
            "格兰玛·露尼耶（ＦＡＬＣＯＮ）",
            "格兰玛·露尼耶\n（ＦＡＬＣＯＮ）",
            "第 10 批：同上；旧首行 236px 且次行仅「ＯＮ）」38px（**拉丁词 ＦＡＬＣＯＮ 被切断**）"
            "⇒ 122 / 152px（左缘 +72.0）。实机对照：间隙 5px → 55px",
        ),
    },
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260929-02` 第 11 批：**流程图右栏「章节详情」大改**（用户 2026-09-29 六条指令）
    #   · 用户裁决（AskUserQuestion）：①暂停键两版都出（派生为主）②迷你地图组与场景回放组都退场
    #     ③大播放窗 380×300 居中。
    #   · 接口冻结书：`_工作\ISSUE-20260929-02_右栏大改\接口冻结.md`（id/几何/素材名/动作名/flag 名）。
    #   · `fc_replay`（屏级 flag）与新增 3 件的旗标**不在此表**——它们不改像素，见 `m01` ①b 与 `m03` ①。
    #   · 白字 + 黑描边取 M38 既有机制（`outline`/`outline_color`/`outline_width`），写法照
    #     `10_dialog.json` 的 `dlg.text`（`@palette.text_primary` + `#000000` + 宽 2）。
    #   · 两个多行槽的 `max_lines`：`lineH = floor(24 × 全局 line_spacing.body 1.4) = 33px`
    #     （`krkr/game/ui_theme.tjs:237`）⇒ 槽高 **159** 时容 **4** 行（132px）。
    #   · ★ 第 3 轮（2026-09-29 · vision 实机复审后 · 主代理已亲自复核）：
    #     ① 台词槽 `y824 h171`（下沿 **995**）与「进入本章」按钮 `fc.jump`（上沿 **943**）
    #        **竖直重叠 52px**（本批引进的排版失误）⇒ 三槽 `h 171→150`、四段重排为
    #        「窗与三槽分离、三槽彼此紧凑」（`y` 534/617/777；两个 `_tx` `h 159→138`）；
    #        改后台词底 **927** → 按钮上沿 943 ＝ **16px，无重叠**；按钮下沿 1004 → 栏底 1019 ＝ 15px。
    #     ② 动态层占位标签横向溢出（`fc.play_view` 第二行墨迹 x1456..1918）⇒ **两端**修
    #        （`ui_widget.tjs` / `replica.js`），**不改本屏元素** ⇒ 不在本表。
    #     · **容量仍 4**：krkr `138 ÷ 33 ＝ 4.18`（132 ≤ 138）；HTML 行盒 `24 × 1.4 ＝ 33.6`（保守取整 34）
    #       ⇒ 4×34 ＝ 136 ≤ 138（余 2px）。
    "fc.p_title": {
        "y": (214, 534,
              "第 11 批：右栏四段重排（用户指令 4）自上而下＝大播放窗/标题/说明/台词。"
              "★ 第 3 轮改排为「窗与三槽分离、三槽彼此紧凑」⇒ y 536→534"
              "（段间＝窗底 514 → 槽顶 534 ＝ 20px）。x/w/h 沿用 PSB 原样"),
        # ★ 第 12 批（`ISSUE-20260929-04` · 用户指令 4）：三槽底对齐 ⇒ x/w 改（另两槽底不动）
        "x": (1416, 1425, "第 12 批：**用户指令 4**「宽度和下面两个 `fc.p_text_tx` 和 `fc.p_message_tx` 统一」"
                          "⇒ 与 `fc.p_text`/`fc.p_message` 的 `x` **逐字相同**（口径 A「三槽底对齐」）"),
        "w": (443, 422, "第 12 批：同上（443 → 422）；旧值 **x1416/w443 是 PSB `#rects/title` 原值，已作废**"),
    },
    "fc.p_title_tx": {
        "y": (224, 544,
              "第 11 批 + 第 3 轮：随标题槽上移 ⇒ 544（**仍为 `y = 槽顶 + 10`**；一行标题，不扩槽）"),
        # ★ 第 12 批（`ISSUE-20260929-04` · 用户指令 4）：随三槽底对齐 ⇒ x/w 改
        "x": (1428, 1437, "第 12 批：随 `fc.p_title` 三槽对齐 ⇒ 与两个 `_tx` 的 `x` **逐字相同**"),
        "w": (419, 398, "第 12 批：同上（419 → 398）；`y/h/align/valign/wrap/max_lines/font` 一律不变"),
        "font": (
            {"size": 24, "bold": True, "color": "@palette.node_locked", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            {"size": 24, "bold": True, "color": "@palette.text_primary", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0,
             "outline": True, "outline_color": "#000000", "outline_width": 2},
            "第 11 批：**用户指令 1**「白字 + 黑描边」—— 字色 `@palette.node_locked`(#4A4A56) → "
            "`@palette.text_primary`(#FFFFFF)，加 M38 描边（黑 `#000000`、宽 2，照 `dlg.text`）；"
            "字号/粗体不动",
        ),
    },
    "fc.p_text": {
        "y": (309, 617,
              "第 11 批 + 第 3 轮：「说明」槽重排 ⇒ y **617**（第 3 轮由 631 上移）；"
              "h **171→150** 属第 3 轮（段间＝标题底 607 → 槽顶 617 ＝ 10px）；x/w 不动"),
        "h": (171, 150, "第 3 轮：三槽收高 171→150（窗与三槽分离、三槽彼此紧凑）"),
    },
    "fc.p_text_tx": {
        # ★ 第 15 批（`ISSUE-20260930-02`）：「说明」槽收窄让位加号按钮 `fc.p_plus`（398 → 300）。
        #   终值取 300（非冻结书初稿 344）：M4 几何定标（真实语料 1199 条）实测 300 档最大墨迹
        #   336px ≤ 354px 可用上限（344 档 384px ✗）。y/h/font/max_lines 等**一字未改**。
        "w": (398, 300,
              "第 15 批：**用户裁定 3**「加号位置＝说明框内右上角，文字槽相应收窄」⇒ `w` 398 → **300**；"
              "x 1437 / y 623 / h 138 / font / align / valign / wrap / max_lines **一律不变**。"
              "该槽超框时末行接 `……`（冻结 §五，纯渲染）"),
        "y": (319, 623, "第 11 批：`y = 槽顶 + 6`（多行内容槽内缩 6px）；第 3 轮随槽顶 617 上移 ⇒ 623"),
        "h": (40, 138, "第 11 批：一行标签 → 多行内容槽；第 3 轮随槽高 150 收为 **138**（槽顶 +6 起排 ⇒ 623..761）"),
        "valign": ("middle", "top", "第 11 批：多行内容自槽顶起排（原单行标签垂直居中）"),
        "wrap": (False, True, "第 11 批：说明是多行内容，须折行（原单行 `wrap:false`）"),
        "max_lines": (1, 4, "第 11 批：容量 4 行；第 3 轮按 138 盒高复核 **仍 4**（krkr 138÷33＝4.18；HTML 4×34＝136 ≤ 138）"),
        "font": (
            {"size": 24, "bold": True, "color": "@palette.node_locked", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            {"size": 24, "bold": True, "color": "@palette.text_primary", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0,
             "outline": True, "outline_color": "#000000", "outline_width": 2},
            "第 11 批：**用户指令 1**「白字 + 黑描边」（同上，黑描边宽 2）",
        ),
    },
    "fc.p_message": {
        "y": (750, 777,
              "第 11 批 + 第 3 轮：「台词」槽重排 ⇒ y **777**（第 3 轮由 824 上移，修"
              "「槽下沿 995 与 fc.jump 上沿 943 竖直重叠 52px」）；h **171→150**（第 3 轮）；x/w 不动"),
        "h": (171, 150, "第 3 轮：三槽收高 171→150 ⇒ 槽下沿 **927**，与按钮上沿 943 留 **16px**（无重叠）"),
    },
    "fc.p_message_tx": {
        "y": (760, 783, "第 11 批：`y = 槽顶 + 6`（同说明槽口径）；第 3 轮随槽顶 777 上移 ⇒ 783"),
        "h": (40, 138, "第 11 批：一行标签 → 多行内容槽；第 3 轮随槽高 150 收为 **138**（783..921 落在槽 777..927 内）"),
        "valign": ("middle", "top", "第 11 批：多行内容自槽顶起排"),
        "wrap": (False, True, "第 11 批：台词是多行内容，须折行"),
        "max_lines": (1, 4, "第 11 批：容量 4 行；第 3 轮按 138 盒高复核 **仍 4**（同说明槽，行盒 33px / HTML 34px）"),
        "font": (
            {"size": 24, "bold": True, "color": "@palette.node_locked", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            {"size": 24, "bold": True, "color": "@palette.text_primary", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0,
             "outline": True, "outline_color": "#000000", "outline_width": 2},
            "第 11 批：**用户指令 1**「白字 + 黑描边」（同上，黑描边宽 2）",
        ),
    },
    "fc.pbkick": {
        "x": (1576, 1578, "第 11 批：移到**大播放窗中央**（窗 380×300@(1448,214) ⇒ 水平居中 x=1578）"),
        "y": (555, 304, "第 11 批：同上，垂直居中 y=304（件中心 (1637.5,363.5) ＝ 窗中心）"),
        # ★ E5 补全（`ISSUE-20260929-04` · S3）：`vis_flag`/`vis_when` 原先**不在** `APPEARANCE_FIELDS`
        #   ⇒ 这一对（上一批引入）一直没有基线等值闸门。补入清单后本项**新暴露**，追认如下。
        #   注意：`fc.pbkick_pause`（同字段值 `"pause"`）是**新增元素**，走 `DECLARED_NEW_IDS`，不在本表。
        "vis_flag": (None, "fc_replay",
                     "第 11 批：**用户指令 1+3** —— 播放键/暂停键『同位置互斥显示』走**既有** "
                     "`vis_flag`+`vis_when` 机制（`layout/_schema.md` §四 铁律一：不得靠 z 排序、"
                     "不得运行期手藏）；屏级 flag `fc_replay` 初值 `\"play\"`。基线该件无此字段（恒可见）"),
        "vis_when": (None, "play",
                     "第 11 批：同上 —— `fc_replay == \"play\"` 时播放键可见（暂停键同字段值 `\"pause\"`，"
                     "靠屏级 flag 互斥）；两键显隐由 `uiScreenElementVisible` 谓词自动同步"),
    },
    "fc.pbkick_hit": {
        "x": (1573, 1575, "第 11 批：热区随播放键同轴移动（119×119 外扩 6px ⇒ 125×125）"),
        "y": (552, 301, "第 11 批：同上"),
        "action": ("", "flow_replay_toggle",
                   "第 11 批：**用户指令 3** —— 播放/暂停共用一条热区，动作＝「播放/暂停切换」"
                   "（**拟用名**；命中即派发，画面时序接线留编程组，本批不声称已生效）"),
    },
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260929-04` 第 12 批：**流程图页四件收尾 + 番外入口统一形制**
    #   · 用户 4 条指令 + 1 条追问（原话见 `_工作\ISSUE-20260929-04_流程图件\接口冻结.md` §0）
    #     ＋ **2026-09-29 追加裁决**（本批真正的形状变更来源）：
    #     「`fc.label.000x` 与 `fc.entry.000x` **一律删去**，统一为**和章节素材
    #      `ui/x_ui_node_select_off(和on).png` 一样的形状、只是底色换成淡黄**；文字方案不动」。
    #   · `fc.bg`（新增）／`fc.sysbar` 与 6 件 `fc.label.<NNNN>` 底板（删除）见下方
    #     `DECLARED_NEW_IDS` / `DECLARED_REMOVED_IDS`。
    #   · 下面三族是本批的**字段变更**（`nine` 的**删**与**加**都在 `APPEARANCE_FIELDS` 里
    #     ⇒ 由 `m06` ② 与 `m01` ③ 同一份清单机检 ⇒ **不需要另立断言**；见交付报告的说明）。
    # ══════════════════════════════════════════════════════════════════════
    # ① 入口块 `fc.entry.<NNNN>`：86×48 付箋 → **296×65 淡黄节点形块**（与 `fc.node.*` 同形制）
    **{
        "fc.entry.%04d" % _g: {
            "x": (183, 60,
                  "第 12 批：入口块左沿取**入口列列首**（60）＝ 与组名文字件 `_tx` **同矩形**；"
                  "旧值 183 是「86 宽付箋在原 333 列宽内居中」的落点，已作废"),
            "y": (_oy, _ny,
                  "第 12 批：落点 ＝ 锚定行 + %d（＝原「入口标记(48) + 4px 间隙」，即**原 `fc.label.<NNNN>` "
                  "标签的行位**）；行距 95 不变 ⇒ 交付样例 **242/337/432/527/622/717**" % ENTRY_BLOCK_DY_12),
            "w": (86, 296, "第 12 批：296 ＝ 与章节节点（`fc.node.*`）同形制；原付箋 86 宽已作废"),
            "h": (48, 65, "第 12 批：65 ＝ 与章节节点同形制；原付箋 48 高已作废"),
            "asset": ("ui/x_ui_fusen_off.png", "ui/x_ui_entry_frag_off.png",
                      "第 12 批：**用户追加裁决** —— 淡黄节点形块（素材 `x_ui_entry_frag_off.png` 由 "
                      "`x_ui_node_select_off.png` **派生**：alpha 逐字节同源、仅换色相）；"
                      "旧占位件 `x_ui_fusen_off.png`（86×48 付箋）退役、**文件保留不删**。"
                      "★ 第 13 批订正：旧文括注「（仍被 `fc.fusen_edit`/`fc.fusen_reset` 使用）」**已作废** —— "
                      "该批删了这两键 ⇒ 该素材现**零功能引用**"),
            "z": (21, 20, "第 12 批：z **20**（在组名文字件 z25 之下，文字才压得住块面）；原 21 已作废"),
            "nine": ({"l": 0, "t": 0, "r": 0, "b": 0}, {"l": 14, "t": 0, "r": 13, "b": 0},
                     "第 12 批：**新增 `nine{l14,t0,r13,b0}`** —— 与 `fc.node.*`（select 族）**完全一致**"
                     "（源 263×65 ≠ 296 ⇒ 横向九宫格拉伸）；旧「全零 nine ＝ 整图拉伸」已作废"),
            "state_assets": (None, {"normal": "ui/x_ui_entry_frag_off.png",
                                   "hover": "ui/x_ui_entry_frag_on.png"},
                             "第 12 批：**新增两态**（`_off` 常态 / `_on` 悬停）；旧为单态 `asset`"),
        } for _g, (_oy, _ny) in ENTRY_Y_PAIRS_12.items()
    },
    # ② 入口热区：矩形随入口块变（**`action`/`layer` 一字未改** ⇒ 不在表内）
    **{
        "fc.entry.%04d_hit" % _g: {
            "x": (183, 60, "第 12 批：矩形＝入口块同一矩形（左沿 60）"),
            "y": (_oy, _ny, "第 12 批：矩形＝入口块同一矩形（y 同入口块）"),
            "w": (86, 296, "第 12 批：矩形＝入口块同一矩形（296）"),
            "h": (48, 65, "第 12 批：矩形＝入口块同一矩形（65）"),
        } for _g, (_oy, _ny) in ENTRY_Y_PAIRS_12.items()
    },
    # ③ 组名文字件 `fc.label.<NNNN>_tx`：**保留**（文字方案不动），矩形改为与入口块同矩形
    **{
        "fc.label.%04d_tx" % _g: {
            "w": (333, 296, "第 12 批：矩形改为与入口块**同矩形**（296）—— 文字直接落在淡黄块上；"
                            "`align/valign/font`（16px/bold/@palette.psv_ink）**一律不动**"),
            "h": (38, 65, "第 12 批：同上（65；`valign:middle` ⇒ 文字在块内垂直居中，墨迹行居中于可见实体面）"),
        } for _g in range(1, 7)
    },
    # ④ `fc.zoom_knob`：换件 + **删 `nine`**（用户指令 1「滑标应是一个指针形状」）
    "fc.zoom_knob": {
        "asset": ("ui/x_ui_zoom_knob.png", "ui/x_ui_zoom_handle.png",
                  "第 12 批：**用户指令 1** —— 旧件 29×16、内含**横胶囊＋圆点两个图形**"
                  "（AI 拆件误切），九宫格各自拉伸 ⇒ 实机上是「两坨」；新件 40×31 **单一竖圆角胶囊手柄**"
                  "（与元素**等尺寸 ⇒ 1:1**）；旧件退役、**文件保留不删**"),
        "nine": ({"l": 7, "t": 4, "r": 7, "b": 4}, None,
                 "第 12 批：**删 `nine`** —— 新件与元素矩形等尺寸（40×31）⇒ 1:1、无需九宫格；"
                 "旧 nine 系为旧素材的拉伸而设，已作废。`x/y/w/h`(1174,112,40×31) / `z:21` / `opacity:255` 不变"),
    },
    # ⑤ `fc.p_title` / `fc.p_title_tx`：三槽对齐（用户指令 4「宽度和下面两个 `_tx` 统一」）
    #   ⚠ 这两件的 `y`（与 `_tx` 的 `font`）**在第 11 批条目里**（见上方 `"fc.p_title"` / `"fc.p_title_tx"`）
    #     —— Python 字典字面量**同名键后者覆盖前者**，故**不得**在此另开同名键；新增项已并入上方两条。
}
# 有意**新增**的元素 id（相对基线）——第 11 批 3 件（右栏大改；用户裁决「两组旧元素都退场」）
DECLARED_NEW_IDS = {
    "fc.play_win": "第 11 批：**大播放窗底板** 380×300@(1448,214)，素材 `ui/x_ui_playwin_bg.png`"
                   "（程序化合成，照 `x_ui_replay_panel` 同配方）；用户指令 2+4",
    "fc.play_view": "第 11 批：**大播放窗画面层** 368×288@(1454,220)（四周内缩 6px）——"
                    "`asset:null` + `dynamic:\"flow_scene_frames\"`，运行期由编程组按顺序填充"
                    "该章节的游戏内画面；未填充时两端画占位底色；用户指令 2",
    "fc.pbkick_pause": "第 11 批：**暂停键** 119×119@(1578,304)（与播放键同位置、同 z），"
                       "三态素材 `ui/x_ui_pbkick_pause_{off,over,on}.png`（由播放键三态派生，"
                       "盘面逐像素同源）；靠屏级 flag `fc_replay` 与播放键互斥；用户指令 3",
    # ── `ISSUE-20260929-04` 第 12 批：**满幅背景**（用户指令 4′「给流程图页面加一个背景图」）
    "fc.bg": "第 12 批：**满幅背景** `(0,0,1920×1080)`、素材 `ui/x_bg_flowchart.png`"
             "（`美术统一_超分\\CG背景\\bg72.png` 2560×1440 → **0.75× LANCZOS** 降采样、不调色/不裁切/不加字）、"
             "**`z:0`**（在 `fc.dim` z1 之下）、`visible_default:true`、**无 `nine`**（1:1）；"
             "它是**外壳件**（不写层旗标 ⇒ 主干与 6 个独立层共用的舞台）；用户 2026-09-29 指令 4′",
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260929-05` 第 13 批：**模式入口收敛**（两枚文字入口取代 4 个模式页签）
    #   · 接口冻结：`_工作\ISSUE-20260929-05_模式入口\接口冻结.md` §B（id / 几何 / 字段逐字）。
    #   · 用户 2026-09-29 指令（流程图页 ②）：删 4 个 `fc.mtabx` 与其 text；在原位置用**两枚文字入口**
    #     取代 —— **「本篇集合」**（序章/本篇/After Story 并入）与 **「番外故事」**（原 Fragment）。
    #   · 用户裁决（AskUserQuestion）：动作**拟用名** `flow_mode_main`/`flow_mode_frag`（命中即派发，
    #     切集/筛选留编程组）；**按下态＝半透明冰蓝实底胶囊＋1px 亮边、整体下沉 1px**。
    #   · 每入口 3 件、**逐件载荷字段在此追认**（`state_group`/`state_assets`/`action` 三者都是
    #     `APPEARANCE_FIELDS` 的载荷字段；本批已把 `state_group` **补进清单** ⇒ 未来漂移受闸门管）：
    #       ① `_glow`（image）：`asset`＝`state_assets.normal`＝`ui/x_ui_modetab_off.png`；
    #          `state_assets{normal,over,pressed}` 三态齐、**两入口共用同一套 3 张**（E1 实际产出；
    #          冻结 §D 允许按形状一致性复用、优先省件数）；**1:1 ⇒ 无 `nine`**；`state_group`＝`mode_main`/`mode_frag`。
    #       ② `_tx`（text）：`sample`＝「本篇集合」/「番外故事」；font `size 30`/`bold:false`/
    #          `@palette.text_primary` + `outline:true`+`#000000`+宽 2/`shadow:false`。**文字不参与换态**。
    #       ③ `_hit`（hit）：`action`＝`flow_mode_main`/`flow_mode_frag`；`state_group` 与同组 `_glow` 相同。
    #     · 三态**全靠 `_glow` 底光图承载**；⚠ **「文字下移 1px」无法实现**（不支持文字逐态位移、
    #       `state_group` 只配对图片层）⇒ 以「**底沉 1px**」等价表达（已写进交接文档）。
    **{
        "fc.mode_%s_%s" % (_g, _s): (
            "第 13 批：**模式入口**（%s）%s —— 180×60 @(%d,%d)%s、z=%s、"
            "`state_group`＝`%s`%s；**外壳件**（不写层旗标）。"
            "用户 2026-09-29 指令（流程图页 ②）＋AskUserQuestion 裁决；接口冻结 §B。"
            % ("「本篇集合」" if _g == "main" else "「番外故事」",
               {"glow": "底光图（三态承载者）", "tx": "文字（引擎绘制、不参与换态）",
                "hit": "热区（z95，指针落任意位置即胜出）"}[_s],
               34 if _g == "main" else 254,
               {"glow": 25, "tx": 33, "hit": 25}[_s],
               "（★ E5：文字件 `_tx` 下移 8px ⇒ y33；`_glow`/`_hit` 仍 y25）" if _s == "tx" else "",
               {"glow": 10, "tx": 20, "hit": 95}[_s],
               "mode_main" if _g == "main" else "mode_frag",
               "" if _s != "hit" else "、`action`＝`flow_mode_%s`" % _g))
        for _g in ("main", "frag") for _s in ("glow", "tx", "hit")
    },
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260930-02` 第 15 批：**章节详情**（说明槽截断 ＋ 详情浮层 ＋ 加号按钮）
    #   · 接口冻结：`_工作\ISSUE-20260930-02_章节详情\接口冻结.md` §三/§四/§六。
    #   · 用户 2026-09-30 裁定 4 条（加号新做 / 浮层内容 / 加号位置 / 不下调字号即超框省略号）。
    #   · 每件载荷字段（几何/z/state_group±state_assets/vis_flag±vis_when/nine）见元素 `note` 与
    #     `layout\_schema.md` 第 15 批块；生成器侧另有三条落盘前自检（`intro_overlay_violations()`
    #     ＋ `--selfcheck-intro-overlay` 变异自证）。
    # ══════════════════════════════════════════════════════════════════════
    "fc.p_plus": "第 15 批：**加号按钮**（「说明」框内右上角）44×44 @(1803,**618**)、`z:27`、"
                 "三态素材 `ui/x_ui_plusbtn_{off,over,press}.png`（44×44 RGBA，风格/配色对齐 `fc.pbkick`："
                 "族内字形色 `#A7CBF1`、按下转白；★ 第 2 轮：**外圈环按目标尺寸 1:1 直绘**、off 环色"
                 "(146,159,183)@α255 与 pbkick 逐值相等）、`state_group:\"p_plus\"`、**1:1 无 `nine`**；"
                 "右缘 1847 ＝ 面板 `fc.p_text` 右缘、上缘 **618**（第 2 轮：625 → 618，"
                 "对齐首行行盒中心）；与文字槽留 66px 间隙",
    "fc.p_plus_hit": "第 15 批：加号按钮**热区**（同矩形 44×44 @1803,**618**；第 2 轮 y 625→618）、"
                     "`z:96`（本屏非浮层热区最高）、"
                     "`action:\"flow_intro_open\"`（纯 flag 翻转：`fc_intro` → `\"open\"`；两端本批实现）、"
                     "`state_group:\"p_plus\"`",
    "fc.intro_scrim": "第 15 批：详情浮层**整屏压暗淡幕** 满幅 `#000000`×opacity150 @z200、"
                      "`vis_flag:\"fc_intro\"`/`vis_when:\"open\"`（外壳件 ⇒ 豁免集）",
    "fc.intro_scrim_hit": "第 15 批：压暗热区 满幅 @z210、`action:\"flow_intro_close\"`"
                          "（命中外侧即回 `\"closed\"`＝点浮层外回主页）",
    "fc.intro_bg": "第 15 批：浮层**面板底** `ui/x_ui_gal_cell_on.png` **1240×400 @(340,340)**"
                   "（第 2 轮：用户裁定 6「浮层改 1240×400」⇒ 由 1240×652 @340,214 改为版面中心）、"
                   "**`nine{l:4,t:4,r:4,b:4}`**（源件 291×166：2px 硬边 #7AB0E8 ＋ 2px 渐变 ⇒ 取 4 保真）、@z220",
    "fc.intro_panel_hit": "第 15 批：面板热区（同 `fc.intro_bg` 矩形 **1240×400 @340,340** @z230）、"
                          "**空 `action`＝吞掉点击**（点面板内不关闭）",
    "fc.intro_title_tx": "第 15 批：浮层**章节标题** **1140×44 @(372,372)**、24px **bold**、白字＋黑描边 2px、"
                         "`max_lines:1`、@z235；`sample:\"章节标题\"` 为占位（取数留编程组）。"
                         "★ 第 2 轮：宽 1176 → 1140（给关闭件让位）、y 246 → 372",
    "fc.intro_text_tx": "第 15 批：浮层**简介全文** **1176×276 @(372,432)**、24px 常规、白字＋黑描边 2px、"
                        "`max_lines:6`（M4 实测：1199 条真实语料自然折行最大 3 行 ⇒ **截断 0**）、@z235。"
                        "★ 第 2 轮：y 306 → 432、h 528 → 276（面板底 740 − 32 留白 = 708）",
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260930-02` 第 15 批 · **第 2 轮**（用户裁定 5：「浮层关闭控件＝加一枚小「×」，复用既有
    #   `x_ui_close_*`，零新素材」＋「保留点浮层之外也关」）—— **新增关闭件 2 件**
    # ══════════════════════════════════════════════════════════════════════
    "fc.intro_close": "第 15 批·第 2 轮：浮层**右上角关闭按钮** `ui/x_ui_close_off.png` **26×26 @(1530,364)**、"
                      "`state_assets{normal:_off,hover:_over,pressed:_on}`（与 `fc.close` 同用法）、"
                      "`state_group:\"intro_close\"`、**`nine{6,6,6,6}`（同 `fc.close`；素材实为 24×26，"
                      "`verify_ui[2]` 要求「无 nine ⇒ w/h＝PNG 实尺寸」）**、**z236**（必须高于面板热区 230）",
    "fc.intro_close_hit": "第 15 批·第 2 轮：关闭按钮**热区**（图标外扩 10px ⇒ **46×46 @1520,354**）、"
                          "`action:\"flow_intro_close\"`（与遮罩热区**同一动作**）、`state_group:\"intro_close\"`、"
                          "**z237**（本屏最高点击候选；**必须高于 `fc.intro_panel_hit` 的 230** —— "
                          "落盘前自检专条断言 ＋ 变异自证 G）",
    # ══════════════════════════════════════════════════════════════════════
    # ── `ISSUE-20260930-06` 第 16 批（2026-09-30）：**番外独立层改纵向流水**（用户裁定 5）
    #   ⇒ 第 6 组由图 12 格全产为 **20 格** ⇒ 新增 8 节点 × 3 件（image/text/hit）＝ **24 件**。
    #   「几何追认」＝逐件把几何钉在盘面值（另由 `check_new_frag_cells()` 反向核对；
    #   `col=(i-1)%3`、`row=(i-1)//3`，x=66+col×375、y=286+row×192；`_tx` 为 x+28/240 宽、`_hit` 同底图）。
    #   素材**零新增**（复用 `ui/x_ui_node_frag_off.png` 等既有件）。
    # ══════════════════════════════════════════════════════════════════════
    **{("fc.frag%d.%04d%s" % (FRAG_G6, _i, _s)): (
        "第 16 批：**番外独立层纵向流水**（`ISSUE-20260930-06` · 用户裁定 5「组内全部产出」）—— "
        "第 6 组由旧口径 12 格全产为 20 格 ⇒ 新增第 %d 格 %s；几何 ＝ `col=(%d-1)%%3=%d`、`row=(%d-1)//3=%d` "
        "⇒ `(x,y) = (66+%d×375, 286+%d×192) = (%d,%d)`%s；`vis_flag:\"fc_layer\"`/`vis_when:\"frag6\"`；"
        "`w/h = 296×65`；素材零新增（与主干 frag 节点同件同 nine）；"
        "★ **冻结 §7.2：`visible_default:false`**（本件是**溢出件**：下沿 %d > 视口底 1017 ⇒ "
        "数据完整产出、**默认不画**；纵滚到位时由编程组置真）"
        % (_i, {"": "底图件", "_tx": "文字件（`x=x_node+28`、盒宽 240）", "_hit": "热区"}[_s],
           _i, (_i - 1) % 3, _i, (_i - 1) // 3, (_i - 1) % 3, (_i - 1) // 3,
           66 + ((_i - 1) % 3) * 375, 286 + ((_i - 1) // 3) * 192,
           "" if _s != "_tx" else "、文字件 `(x,y) = (%d,%d)`"
           % (66 + ((_i - 1) % 3) * 375 + 28, 286 + ((_i - 1) // 3) * 192),
           286 + ((_i - 1) // 3) * 192 + 65))
       for _i in FRAG_NEW_CELLS_6 for _s in ("", "_tx", "_hit")},
}
# 有意**删除**的元素 id（相对基线）——第 11 批 12 件（**只删元素，素材一个不删**）
DECLARED_REMOVED_IDS = {
    **{("fc.mini%d" % _n): "第 11 批：**用户指令 2**「我不需要小略缩图」—— 8 张迷你缩略图块退场，"
                           "由大播放窗统一承担" for _n in range(1, 9)},
    "fc.mapview": "第 11 批：缩略图可视区框退场（其 380×300 被沿用为大播放窗的**尺寸基准**）；用户指令 2",
    "fc.pbk_panel": "第 11 批：旧「场景回放窗底板」元素退场（→ `fc.play_win`）；"
                    "**素材 `ui/x_ui_replay_panel.png` 保留不删**（工程口径「旧素材一件不删」）",
    "fc.p_player": "第 11 批：旧回放组内容底退场（→ `fc.play_view`）",
    "fc.p_player_tx": "第 11 批：旧「场景回放」占位标签退场（新排版不再需要该标签）",
    # ── `ISSUE-20260929-04` 第 12 批：**删 7 件元素**（6 件组名底板 + 1 件系统条；**素材一个不删**）
    #   ① 6 件 `fc.label.<NNNN>`：用户 2026-09-29 追加裁决「`fc.label.000x` 与 `fc.entry.000x` 一律删去，
    #      统一为和章节素材 `ui/x_ui_node_select_off(和on).png` 一样的形状、底色换淡黄；文字方案不动」
    #      ⇒ **底板**让位给同矩形的淡黄入口块 `fc.entry.<NNNN>`；**文字件 `_tx` 保留**（不在本表）。
    #      素材 `ui/x_ui_label_off.png` **保留不删**（工程口径「旧素材一件不删」）。
    #   ② `fc.sysbar`：`sysbar` 屏删除后**留在本屏的遗留装饰条**（无文字、无点击）；用户裁定删元素。
    #      素材 `ui/x_ui_sysbar.png`（1946×292）**保留不删**。
    **{("fc.label.%04d" % _g): "第 12 批：**组名标签底板退役**（用户追加裁决）—— 让位给同矩形的淡黄入口块 "
                              "`fc.entry.%04d`；**只删元素**，素材 `ui/x_ui_label_off.png` 保留不删；"
                              "文字件 `fc.label.%04d_tx` **仍在**（不在本表）" % (_g, _g)
       for _g in range(1, 7)},
    "fc.sysbar": "第 12 批：**遗留装饰条退役**（用户 2026-09-29 裁定「`fc.sysbar` 删掉元素」）—— "
                 "它原是 `sysbar` 屏删除后留在流程图屏上的装饰条（无文字、无点击、无 `_hit`）；"
                 "**素材 `ui/x_ui_sysbar.png` 保留不删**",
    # ── `ISSUE-20260929-05` 第 13 批：**删 18 件元素**（12 模式页签 ＋ 6 备注键；**素材一个不删**）
    #   ① 12 件 `fc.mtab1..4` ＋ `_tx` ＋ `_hit`：**4 个模式页签**（序章／本篇／After Story／Fragment）——
    #      用户 2026-09-29 指令（流程图页 ①）「删掉 4 个 `fc.mtabx` 和对应 text」。
    #      素材 `ui/x_ui_ftab_{on,off,over}.png` **保留不删**（现零功能引用）。
    #   ② 6 件 `fc.fusen_edit`/`fc.fusen_reset` ＋ `_tx` ＋ `_hit`：**备注功能键** —— 用户指令（流程图页 ③）
    #      「不再需要备注功能」；用户点名 4 件，另两个 `_hit` 若不删会留下**指向空动作的死热区** ⇒ 一并删。
    #      素材 `ui/x_ui_fusen_{off,over,on}.png` **保留不删**（现零功能引用）。
    **{("fc.mtab%d%s" % (_n, _s)): (
        "第 13 批：**模式页签退役**（用户 2026-09-29 指令①「删掉 4 个 `fc.mtabx` 和对应 text」）—— "
        "序号 %d（%s）；位置由**两枚模式入口** `fc.mode_*` 接手；**只删元素**，"
        "素材 `ui/x_ui_ftab_{on,off,over}.png` 保留不删（现零功能引用）"
        % (_n, {1: "序章", 2: "本篇", 3: "After Story", 4: "Fragment"}[_n] if _s == "" else
           ("页签名（引擎绘制）" if _s == "_tx" else "页签热区（`action` 全为空串，从未接线）")))
       for _n in (1, 2, 3, 4) for _s in ("", "_tx", "_hit")},
    **{("fc.fusen_%s%s" % (_k, _s)): (
        "第 13 批：**备注功能键退役**（用户 2026-09-29 指令③「不再需要备注功能」）—— "
        "键「%s」%s；**只删元素**，素材 `ui/x_ui_fusen_{off,over,on}.png` 保留不删（现零功能引用）"
        % ("编辑备注" if _k == "edit" else "备注初始化",
           {"": "（image，三态接线）", "_tx": "（按钮文字，引擎绘制）",
            "_hit": "（热区，`action` 为空串 ⇒ 不删会留下指空动作的死热区）"}[_s]))
       for _k in ("edit", "reset") for _s in ("", "_tx", "_hit")},
}
# ★★ 有意变更的**屏级**字段（相对基线）—— 结构：字段名 → (old, new, 理由)
#   与 `SCREEN_FIELD_ALLOW`（纯白名单，如 `note`）分工：这里的是**载荷字段**，必须逐条追认。
DECLARED_SCREEN = {
    "flags_default": (
        {"fc_layer": "main"},
        {"fc_layer": "main", "fc_replay": "play", "fc_intro": "closed"},
        "第 11 批：右栏新增「播放键/暂停键」一对 ⇒ 新增屏级 flag **`fc_replay`**（初值 `\"play\"` ⇒"
        "进屏默认显示播放键）；★ 第 15 批：章节详情浮层 ⇒ 再新增 **`fc_intro`**（初值 `\"closed\"` ⇒"
        "进屏默认关闭浮层，6 件 `fc.intro_*` 靠 `vis_when:\"open\"` 显隐）；`flags_default` 是**载荷字段**，"
        "故逐条追认（不是白名单）",
    ),
}
# 有意变化的连线（相对基线）——本批无；结构：边序号 → (字段, old, new, 理由)
DECLARED_LINKS = {}

FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("      ✗ %s" % msg)


def ok(msg):
    print("      ✓ %s" % msg)


def brief(v, n=52):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n - 1] + "…"


# ★ 第 11 批第 4 轮（合并验证时实测）：**盘面 md5 必须按 LF 规范化后再比**。
#   金标（`GOLDEN` / `PRESET_TABLE` / `layout\_schema.md` 金标表）按定义是 **LF 规范化值**
#   （`_schema.md` 金标表明载：「LF 规范化值；盘面 CRLF 因 `core.autocrlf=true`，字节 md5 …」）。
#   而**新检出的 worktree 是 CRLF** ⇒ 直接对盘面字节取 md5 会得到另一个值（同一份内容：
#   LF `a84a1876…` vs CRLF `a7a47fb0…`）⇒ 在 CRLF 检出面上**假失败**，还会给出误导性提示
#   （「多半是上一次跑了别的预设」），诱导人无谓地重跑生成器。
#   （`git show <rev>:` 取到的是 git 存储形态＝LF，故基线侧本来就没有这个问题。）

def lf_bytes(b):
    """把盘面字节按 **LF 规范化**（`core.autocrlf=true` 下检出面可能是 CRLF）——见上方注。"""
    return b.replace(b"\r\n", b"\n")

def git_show(ref, path_rel):
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                         capture_output=True, text=True).stdout.strip()
    rel = os.path.relpath(path_rel, top).replace("\\", "/")
    r = subprocess.run(["git", "show", "%s:%s" % (ref, rel)], cwd=top,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] git show %s:%s 失败：%s" % (ref, rel, r.stderr[-300:]))
    return r.stdout


def looks_like_screen1(doc):
    r"""交付样例 `screen1` 的两条识别特征（与 `m01` 同式）：含 `fc.frag*` 族、`flags_default` 无逐节点运行态键。"""
    fl = doc.get("flags_default") or {}
    if any(str(k).startswith("fc.state.") for k in fl):
        return False, "flags_default 含逐节点运行态键 `fc.state.*`（那是 `states` 档的特征）"
    if not any(e["id"].startswith("fc.frag") for e in doc.get("elements", [])):
        return False, "屏内没有 `fc.frag*` 族（screen1 应含 6 组独立层）"
    return True, ""


def diff_fields(om, nm):
    """逐元素逐字段比对 `APPEARANCE_FIELDS`。纯函数（供变异自证调用）⇒ 判据非恒真。"""
    out = []
    for i in sorted(set(om) & set(nm)):
        for f in APPEARANCE_FIELDS:
            if om[i].get(f) != nm[i].get(f):
                out.append((i, f, om[i].get(f), nm[i].get(f)))
    return out


def judge(diffs):
    """把字段差异分成（声明内命中, 未声明, 值不符）。纯函数。"""
    hit, undeclared, mismatch = [], [], []
    for i, f, a, b in diffs:
        d = DECLARED.get(i, {}).get(f)
        if d is None:
            undeclared.append((i, f, a, b))
        elif d[0] != a or d[1] != b:
            mismatch.append((i, f, a, b, d))
        else:
            hit.append((i, f, a, b))
    return hit, undeclared, mismatch


# ══════════════════════════════════════════════════════════════════════
# ★ 第 13 批（`ISSUE-20260929-05`）：**新增件的载荷字段逐条追认**
#   背景：`DECLARED_NEW_IDS` 只记「这个 id 是新增的」——**记不住它带什么载荷**。
#   本批新增的 6 件 `fc.mode_*` 全靠 `state_group` 把 `_hit`（z95）与 `_glow`（z10）绑成一对换三态，
#   载荷写错（组名不同 / 三态缺件 / action 漏写）在**其它判据上全绿**（元素在、几何对、素材在库）。
#   ⇒ 单列一节把「接口冻结 §B 的载荷」逐条钉在盘面值上；并附**变异自证**（改坏一处必须被检出）。
#   判据（逐件）：① 几何/`z`/`kind` 与冻结一致；② `_glow` 的 `state_assets` 三态齐、`normal == asset`、
#   **三张素材在库且与元素等尺寸（1:1、无 `nine`）**；③ `_glow`/`_hit` 的 `state_group` **同组**且等于冻结值；
#   ④ `_hit.action` 非空且等于冻结的拟用名；⑤ `_tx.sample` 等于冻结文案；
#   ⑥ `_glow`/`_hit` **逐字段同矩形**；`_tx` **同 `x/w/h`、`y == _glow.y + MODE_ENTRY_TX_DY`**。
#      ★ **E5 一轮订正（用户 2026-09-29 裁决「文字下移 8px」）**：原先判「三件逐字段同矩形」，
#      本轮起 `_tx.y` **25 → 33**（实测原墨迹 y31..63/中心 47 vs 框中心 55 ⇒ 偏高 8px）⇒
#      「同框」口径改为「`_glow`/`_hit` 同框 + `_tx` 同 x/w/h 且固定 y 偏移」——
#      **判据没有放松**（偏移是定值，任何歪斜仍被检出），只把这条**有意的**偏移写进判据。
#   纯函数，供变异自证复用。
# ══════════════════════════════════════════════════════════════════════
MODE_ASSET_TRI = {"normal": "ui/x_ui_modetab_off.png",
                  "hover": "ui/x_ui_modetab_over.png",
                  "pressed": "ui/x_ui_modetab_press.png"}
MODE_ENTRY_TX_DY = 8        # ★ E5：文字件相对底光/热区的纵向偏移（与生成器同名常量同值）
MODE_NEW_SPEC = {
    "fc.mode_main_glow": dict(kind="image", x=34, y=25, w=180, h=60, z=10, sg="mode_main"),
    "fc.mode_main_tx": dict(kind="text", x=34, y=33, w=180, h=60, z=20, sg=None, sample="本篇集合"),
    "fc.mode_main_hit": dict(kind="hit", x=34, y=25, w=180, h=60, z=95, sg="mode_main",
                             action="flow_mode_main"),
    "fc.mode_frag_glow": dict(kind="image", x=254, y=25, w=180, h=60, z=10, sg="mode_frag"),
    "fc.mode_frag_tx": dict(kind="text", x=254, y=33, w=180, h=60, z=20, sg=None, sample="番外故事"),
    "fc.mode_frag_hit": dict(kind="hit", x=254, y=25, w=180, h=60, z=95, sg="mode_frag",
                             action="flow_mode_frag"),
}


def new_mode_payload_fails(by):
    """逐条核对 6 件 `fc.mode_*` 的冻结载荷；返回失败描述列表（空 = 通过）。纯函数。"""
    from PIL import Image as _Im
    out = []
    assets_dir = os.path.join(UI, "krkr", "assets", "ui")
    for eid, spec in sorted(MODE_NEW_SPEC.items()):
        e = by.get(eid)
        if e is None:
            out.append("缺新增件 `%s`" % eid)
            continue
        got = (e.get("x"), e.get("y"), e.get("w"), e.get("h"))
        want = (spec["x"], spec["y"], spec["w"], spec["h"])
        if got != want:
            out.append("%s 几何 %s ≠ 冻结 %s" % (eid, got, want))
        if e.get("z") != spec["z"]:
            out.append("%s z=%s ≠ 冻结 %s" % (eid, e.get("z"), spec["z"]))
        if e.get("kind") != spec["kind"]:
            out.append("%s kind=%r ≠ 冻结 %r" % (eid, e.get("kind"), spec["kind"]))
        if spec["sg"] is not None and e.get("state_group") != spec["sg"]:
            out.append("%s state_group=%r ≠ 冻结 %r（换三态的配对键）"
                       % (eid, e.get("state_group"), spec["sg"]))
        if "sample" in spec and e.get("sample") != spec["sample"]:
            out.append("%s sample=%r ≠ 冻结 %r" % (eid, e.get("sample"), spec["sample"]))
        if "action" in spec:
            if not str(e.get("action") or "").strip():
                out.append("%s 的 action 为空串（本批要求非空：命中即派发）" % eid)
            elif e.get("action") != spec["action"]:
                out.append("%s action=%r ≠ 冻结 %r" % (eid, e.get("action"), spec["action"]))
        if spec["kind"] == "image":
            sa = e.get("state_assets") or {}
            if sorted(sa) != ["hover", "normal", "pressed"]:
                out.append("%s 的 state_assets 键不是 normal/hover/pressed：%s" % (eid, sorted(sa)))
                continue
            if sa.get("normal") != e.get("asset"):
                out.append("%s 的 state_assets.normal=%r ≠ asset=%r"
                           % (eid, sa.get("normal"), e.get("asset")))
            if "nine" in e:
                out.append("%s 不应带 `nine`（1:1 件）" % eid)
            for k in ("normal", "hover", "pressed"):
                v = sa.get(k)
                p = os.path.join(assets_dir, os.path.basename(v or ""))
                if not os.path.exists(p):
                    out.append("%s 的 %s 素材缺文件：%s" % (eid, k, v))
                else:
                    sz = _Im.open(p).size
                    if sz != (spec["w"], spec["h"]):
                        out.append("%s 的 %s 素材 %s ≠ 元素 %s（应 1:1）"
                                   % (eid, k, sz, (spec["w"], spec["h"])))
    # 三件几何口径（★ E5：`_glow`/`_hit` 同框；`_tx` 同 x/w/h 且 y = glow.y + 8）+ 同组配对 + 两入口等宽等高
    for g in ("main", "frag"):
        trio = ["fc.mode_%s_%s" % (g, s) for s in ("glow", "tx", "hit")]
        rs = [(by[i].get("x"), by[i].get("y"), by[i].get("w"), by[i].get("h"))
              for i in trio if i in by]
        if len(rs) == 3 and rs[0] != rs[2]:
            out.append("%s 的 `_glow`/`_hit` 不同矩形：%s vs %s（底光与热区必须同框）"
                       % (g, rs[0], rs[2]))
        elif len(rs) == 3:
            want_tx = (rs[0][0], rs[0][1] + MODE_ENTRY_TX_DY, rs[0][2], rs[0][3])
            if rs[1] != want_tx:
                out.append("%s 的 `_tx` 矩形 %s ≠ 期望 %s（同 x/w/h、`y = _glow.y + %d`；E5 文字下移口径）"
                           % (g, rs[1], want_tx, MODE_ENTRY_TX_DY))
        gl, ht = by.get(trio[0]), by.get(trio[2])
        if gl is not None and ht is not None and gl.get("state_group") != ht.get("state_group"):
            out.append("%s 的 `_glow`(%r) 与 `_hit`(%r) 不同 `state_group` ⇒ 不会联动换态"
                       % (g, gl.get("state_group"), ht.get("state_group")))
    for a, b in (("main", "frag"),):
        ea, eb = by.get("fc.mode_%s_glow" % a), by.get("fc.mode_%s_glow" % b)
        if ea and eb and (ea.get("w"), ea.get("h")) != (eb.get("w"), eb.get("h")):
            out.append("两入口不等宽等高（「排版整齐」不成立）")
    return out


def check_new_mode_payload(doc):
    """打印 + 断言（含变异自证：把一处 `state_group` 改坏必须被检出）。"""
    print("\n【⑧ ★ 第 13 批：新增件 `fc.mode_*` 的**载荷字段逐条追认**（几何/z/state_group/state_assets/action/sample）】")
    by = {e["id"]: e for e in doc["elements"]}
    bads = new_mode_payload_fails(by)
    print("      6 件逐条核对（含三态素材在库且 1:1、同组配对、`_glow`/`_hit` 同框且 `_tx` 下移 8px、"
          "两入口等宽等高）⇒ 失败 **%d 处**%s"
          % (len(bads), " ✓" if not bads else ""))
    for b in bads:
        fail("新增件载荷：" + b)
    # 变异自证：改坏 `fc.mode_frag_hit.state_group` ⇒ 必须报「不同 state_group」
    if "fc.mode_frag_hit" in by:
        mut = json.loads(json.dumps(doc))
        for e in mut["elements"]:
            if e["id"] == "fc.mode_frag_hit":
                e["state_group"] = "mode_main"
        mut_bads = new_mode_payload_fails({e["id"]: e for e in mut["elements"]})
        hit = [x for x in mut_bads if "不同 `state_group`" in x or "state_group=" in x]
        print("      变异自证：把 `fc.mode_frag_hit.state_group` 改成 `mode_main` ⇒ 失败 **%d 处**"
              "（其中命中 `state_group` **%d 处**）%s"
              % (len(mut_bads), len(hit), " ✓ 判据非恒真" if hit else " ✗ **判据恒真**"))
        if not hit:
            fail("新增件载荷判据**恒真**：改坏 `state_group` 未被检出")


# ══════════════════════════════════════════════════════════════════════
# ★ 第 16 批（`ISSUE-20260930-06`）：**新增 8 节点的几何追认**（纯函数 + 正向核对 + 变异自证）
#   为什么单列：`DECLARED_NEW_IDS` 只记「这个 id 是新增的」——**记不住它落在网格哪一格**。
#   本批新增的 24 件（G6 的 13–20 格 ×3）全部在**视口之外**（y 1054/1246/1438 > 视口底 1017），
#   几何写错（列/行错位、落到非 3 列网格、漏 `vis_when`）在**其它判据上全绿**（元素在、素材在、条数对）。
# ══════════════════════════════════════════════════════════════════════
def frag_cell_rect_m06(g, i, vp):
    """第 g 组第 i 格的底图件矩形 (x, y, w, h)（照生成器几何独立复算）。"""
    col, row = (i - 1) % FRAG_COLS_M06, (i - 1) // FRAG_COLS_M06
    return (vp["x"] + FRAG_ORIGIN_M06[0] + col * FRAG_STEP_X_M06,
            vp["y"] + FRAG_ORIGIN_M06[1] + FRAG_LEAD_Y_M06 + row * FRAG_STEP_Y_M06,
            FRAG_NODE_W_M06, FRAG_NODE_H_M06)


def new_frag_cell_fails(by):
    """逐件核对本批新增的 G6 13–20 格 ×3 ＝ 24 件；返回失败描述列表（空 ＝ 通过）。纯函数。

    ★ 冻结 §7.2（2026-09-30 一审后返修）：这 24 件**全部是溢出件**（下沿 1119/1311/1503 > 视口底 1017）
    ⇒ 其 `visible_default` **必须为 `False`**（数据完整产出、默认不画；纵滚到位时由编程组置真）。
    本函数把该字段一并钉死（`DECLARED_NEW_IDS` 只记「新增」，记不住可见性）。
    """
    out = []
    vp = by.get("fc.scroll")
    if vp is None:
        return ["缺 `fc.scroll`（独立层网格原点无从判定）"]
    vb = vp["y"] + vp["h"]
    for i in FRAG_NEW_CELLS_6:
        x, y, w, h = frag_cell_rect_m06(FRAG_G6, i, vp)
        trio = [("fc.frag%d.%04d" % (FRAG_G6, i), (x, y, w, h), "image"),
                ("fc.frag%d.%04d_tx" % (FRAG_G6, i), (x + 28, y, FRAG_TEXT_W_M06, h), "text"),
                ("fc.frag%d.%04d_hit" % (FRAG_G6, i), (x, y, w, h), "hit")]
        for eid, want, kind in trio:
            e = by.get(eid)
            if e is None:
                out.append("缺本批新增件 `%s`" % eid)
                continue
            got = (e.get("x"), e.get("y"), e.get("w"), e.get("h"))
            if got != want:
                out.append("%s 几何 %s ≠ 网格追认 %s" % (eid, got, want))
            if e.get("kind") != kind:
                out.append("%s kind=%r ≠ %r" % (eid, e.get("kind"), kind))
            if e.get("vis_flag") != "fc_layer" or e.get("vis_when") != "frag%d" % FRAG_G6:
                out.append("%s 的 flag 对不合法：%s/%s"
                           % (eid, e.get("vis_flag"), e.get("vis_when")))
            # ★ 冻结 §7.2：溢出件必须 `visible_default:false`（y+h > 视口底）
            if (want[1] + want[3]) > vb and e.get("visible_default") is not False:
                out.append("%s 是溢出件（下沿 %d > 视口底 %d）⇒ `visible_default` 应为 **False**，实为 %r"
                           % (eid, want[1] + want[3], vb, e.get("visible_default")))
    # 反向：G6 必须**全量 20 格**（纵向流水口径 ⇒ 不得回退到 12 格上限）
    n6 = len([e for e in by if re.match(r"^fc\.frag%d\.\d{4}$" % FRAG_G6, e)])
    if n6 != 20:
        out.append("G6 独立层节点数 **%d** ≠ 20（纵向流水应组内全量产出；旧 12 格上限不得回归）" % n6)
    # 反向（冻结 §7.2）：G6 前 4 行（12 格）必须**仍默认可画**（不得被「一律置 false」蒙过）
    n_ov_false = len([e for e in by.values()
                      if re.match(r"^fc\.frag%d\.\d{4}(?:_tx|_hit)?$" % FRAG_G6, e["id"])
                      and e.get("visible_default") is False])
    if n_ov_false != 24:
        out.append("G6 带 `visible_default:false` 的件数 **%d** ≠ 24（8 溢出格 ×3；"
                   "溢出却默认可画 / 未溢出却默认不画 均属违规）" % n_ov_false)
    return out


def check_new_frag_cells(doc):
    """打印 + 断言（含变异自证：删掉本批新增的一格 / 把溢出件改回默认可画 ⇒ 必须被检出）。"""
    print("\n【⑨ ★ 第 16 批：番外独立层**纵向流水** —— 新增 G6 13–20 格 ×3 的几何追认"
          "＋冻结 §7.2 可见性（溢出件 `visible_default:false`）】")
    by = {e["id"]: e for e in doc["elements"]}
    bads = new_frag_cell_fails(by)
    n6 = len([e for e in by if re.match(r"^fc\.frag%d\.\d{4}$" % FRAG_G6, e)])
    n_false = len([e for e in by.values()
                   if re.match(r"^fc\.frag%d\.\d{4}(?:_tx|_hit)?$" % FRAG_G6, e["id"])
                   and e.get("visible_default") is False])
    print("      G6 节点 **%d/20** 格；`visible_default:false` **%d 件**（预期 24；全部为溢出件）；"
          "逐件核对 24 件（几何/kind/vis_flag+vis_when/可见性）⇒ 失败 **%d 处**%s"
          % (n6, n_false, len(bads), " ✓" if not bads else ""))
    for b in bads:
        fail("新增独立层格：" + b)
    # 变异自证：删掉 `fc.frag6.0020` 三件 ⇒ 必须报「缺新增件」＋「节点数 ≠ 20」
    drop = "fc.frag6.0020"
    mut = json.loads(json.dumps(doc))
    mut["elements"] = [e for e in mut["elements"]
                       if e["id"] not in (drop, drop + "_tx", drop + "_hit")]
    mut_bads = new_frag_cell_fails({e["id"]: e for e in mut["elements"]})
    hit = [x for x in mut_bads if "缺本批新增件" in x or "≠ 20" in x]
    print("      变异自证：删 `%s` ×3 件 ⇒ 失败 **%d 处**（其中「缺件/节点数」**%d 处**）%s"
          % (drop, len(mut_bads), len(hit), " ✓ 判据非恒真" if hit else " ✗ **判据恒真**"))
    if not hit:
        fail("新增独立层格判据**恒真**：删掉 `%s` 三件未被检出" % drop)
    # 变异自证（★ 冻结 §7.2）：把溢出件的 `visible_default` 改回 `true` ⇒ 必须被检出
    mut2 = json.loads(json.dumps(doc))
    for e in mut2["elements"]:
        if re.match(r"^fc\.frag%d\.\d{4}(?:_tx|_hit)?$" % FRAG_G6, e["id"]) \
                and e.get("visible_default") is False:
            e["visible_default"] = True
    mut2_bads = new_frag_cell_fails({e["id"]: e for e in mut2["elements"]})
    hit2 = [x for x in mut2_bads if "应为 **False**" in x or "≠ 24" in x]
    print("      变异自证（冻结 §7.2）：把 24 件溢出件的 `visible_default` 改回 `true` ⇒ 失败 **%d 处**"
          "（其中「应为 False/件数」**%d 处**）%s"
          % (len(mut2_bads), len(hit2), " ✓ 判据非恒真" if hit2 else " ✗ **判据恒真**"))
    if not hit2:
        fail("冻结 §7.2 判据**恒真**：把溢出件改回默认可画未被检出")


def mutate_selfcheck(om):
    r"""★ 变异自证：在内存副本注入**必属未声明**的字段变异，判据必须检出 ⇒ 证明判据非恒真。

    ★ 第 12 批（`ISSUE-20260929-04`）追加第二支：**单独注入一次 `nine` 的删除**。
      起因：本批的字段改动里最不显眼的一处是「`fc.zoom_knob` **删 `nine`**」与
      「`fc.entry.*` **加 `nine`**」—— 而 `nine` **本来就在 `APPEARANCE_FIELDS` 里**
      （m06 ② 与 m01 ③ 共用该清单）⇒ 这一处**已被机检住**，无需另立断言。
      但「在清单里」只是声明，必须**证明它真的参与比对**：故注入一次 `nine` 删除并断言被检出
      （参数化证据，不是读清单）。
    """
    print("\n【⑦ 变异自证（证明 ①–③ 非恒真；含 `nine` 专项）】")
    tgt = None
    for i in sorted(om):
        if i.startswith("fc.") and om[i].get("kind") == "image" and (i not in DECLARED):
            tgt = i
            break
    if tgt is None:
        fail("变异自证无法选靶（找不到未被声明的 image 元素）")
        return
    mut = json.loads(json.dumps(om))
    mut[tgt]["x"] = (mut[tgt].get("x") or 0) + 1
    mut[tgt]["asset"] = "__mut__.png"
    _hit, undeclared, _mm = judge(diff_fields(om, mut))
    tagged = [u for u in undeclared if u[0] == tgt]
    okk = len(tagged) >= 2
    print("      注入 `%s` 的 `x` +1px、`asset`→`__mut__.png` ⇒ 判据报未声明差异 **%d 处**"
          "（其中本元素 %d 处）%s" % (tgt, len(undeclared), len(tagged), "✓ 判据非恒真" if okk else "✗ **判据恒真**"))
    if not okk:
        fail("变异自证失败：注入 2 处字段变异后判据未全部检出（①/③ 恒真、无判别力）")

    # ── ★ 第 12 批第二支：`nine` 专项（证明「删/加 `nine`」确实被字段比对照到）──────
    ntg = None
    for i in sorted(om):
        if om[i].get("kind") == "image" and "nine" in om[i] and (i not in DECLARED):
            ntg = i
            break
    if ntg is None:
        fail("`nine` 专项变异自证无法选靶（找不到「带 nine 且未声明」的 image 元素）")
        return
    mut_n = json.loads(json.dumps(om))
    del mut_n[ntg]["nine"]
    _hn, und_n, _mn = judge(diff_fields(om, mut_n))
    hit_n = [u for u in und_n if u[0] == ntg and u[1] == "nine"]
    print("      `nine` 专项：删 `%s.nine`（%s → 无）⇒ 判据报未声明差异 **%d 处**（其中本元素 `nine` %d 处）%s"
          % (ntg, brief(om[ntg].get("nine")), len(und_n), len(hit_n),
             "✓ `nine` 确实参与比对" if hit_n else "✗ **`nine` 未被比对**"))
    if not hit_n:
        fail("`nine` 的删除**未被检出** ⇒ `APPEARANCE_FIELDS` 的 `nine` 未真正参与比对"
             "（本批 `fc.zoom_knob` 删 nine / `fc.entry.*` 加 nine 就失去机检）")


def main():
    print("=" * 78)
    print("m06 · 交付样例「基线总账」（固定引用 `%s` ↔ 盘上现值）—— 「有意」与「意外」分开列" % BASE_REF)
    print("=" * 78)

    base_raw = git_show(BASE_REF, SCREEN)
    base_md5 = hashlib.md5(base_raw.encode("utf-8")).hexdigest()
    old = json.loads(base_raw)
    disk_raw = open(SCREEN, encoding="utf-8", newline="").read()
    new = json.loads(disk_raw)
    disk_md5 = hashlib.md5(lf_bytes(disk_raw.encode("utf-8"))).hexdigest()

    # ── ⓪ 基线与现值两侧的健全性（任一侧不健康 ⇒ 本脚本的结论无意义 ⇒ 硬失败）──────
    print("\n【⓪ 两侧健全性】")
    bok, bwhy = looks_like_screen1(old)
    if bok:
        ok("基线 `%s` 是 screen1 变体（md5 %s%s）" % (
            BASE_REF, base_md5[:12],
            "＝预期 ✓" if base_md5 == BASE_REF_MD5_EXPECT else "，⚠ 与登记的 %s 不同" % BASE_REF_MD5_EXPECT[:12]))
    else:
        fail("基线不健全：`%s` 的该文件**不是 screen1 变体**（%s）⇒ 请修正 `BASE_REF` 常量" % (BASE_REF, bwhy))
    nok, nwhy = looks_like_screen1(new)
    spec = importlib.util.spec_from_file_location("_gfl", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    g_md5, g_csha = mod.GOLDEN["screen1"]
    if nok and disk_md5 == g_md5:
        ok("盘上现值是交付样例 `screen1`（md5 %s ＝ 金标 ✓）" % disk_md5[:12])
    elif nok:
        fail("盘上现值虽含 `fc.frag*` 族，但 md5 %s ≠ 金标 `screen1` %s ⇒ 盘上不是交付样例"
             "（多半是上一次跑了别的预设没还原；跑一次无参 `python 工具/gen_flow_layout.py`）"
             % (disk_md5[:12], g_md5[:12]))
    else:
        fail("盘上现值**不是 screen1 变体**（%s）⇒ 跑一次无参 `python 工具/gen_flow_layout.py` 还原"
             "（**切勿把这种状态提交**：本批事故就是这样发生的）" % nwhy)

    om = {e["id"]: e for e in old["elements"]}
    nm = {e["id"]: e for e in new["elements"]}
    print("      元素数：基线 %d → 现值 %d ｜ 连线 %d → %d"
          % (len(om), len(nm), len(old.get("links", [])), len(new.get("links", []))))

    # ── ① 元素增删（必须全部被追认）────────────────────────────────────
    print("\n【① 元素增删】")
    added = sorted(set(nm) - set(om))
    removed = sorted(set(om) - set(nm))
    bad_add = [i for i in added if i not in DECLARED_NEW_IDS]
    bad_rm = [i for i in removed if i not in DECLARED_REMOVED_IDS]
    print("      新增 %d 件 / 删除 %d 件" % (len(added), len(removed)))
    if added:
        print("        新增：%s" % (added if len(added) <= 12 else added[:12] + ["…共 %d" % len(added)]))
    if removed:
        print("        删除：%s" % (removed if len(removed) <= 12 else removed[:12] + ["…共 %d" % len(removed)]))
    for i in bad_add:
        fail("未追认的新增元素 `%s`（kind=%s）" % (i, nm[i].get("kind")))
    for i in bad_rm:
        fail("未追认的删除元素 `%s`" % i)
    stale_ids = [i for i in DECLARED_NEW_IDS if i not in added]
    for i in stale_ids:
        fail("总账过期：`DECLARED_NEW_IDS` 声明新增 `%s`，但相对基线并未新增 ⇒ 删除该条目" % i)
    stale_rm = [i for i in DECLARED_REMOVED_IDS if i not in removed]
    for i in stale_rm:
        fail("总账过期：`DECLARED_REMOVED_IDS` 声明删除 `%s`，但相对基线仍存在 ⇒ 删除该条目" % i)
    if not added and not removed and not FAILS:
        ok("元素集合与基线一致（无增无删）")

    # ── ② 外观/行为字段（差额必须逐条落在总账里，且值必须与账一致）──────────
    print("\n【② 影响外观/行为的 %d 个字段】" % len(APPEARANCE_FIELDS))
    diffs = diff_fields(om, nm)
    hit, undeclared, mismatch = judge(diffs)
    print("      声明内差异 %d 处 ／ 未声明差异 %d 处 ／ 值不符 %d 处" % (len(hit), len(undeclared), len(mismatch)))
    for i, f, a, b in hit:
        print("        账内  %-18s %-10s %s → %s" % (i, f, brief(a), brief(b)))
    for i, f, a, b in undeclared:
        fail("未追认的字段变更 %s.%s：%s → %s" % (i, f, brief(a), brief(b)))
    for i, f, a, b, d in mismatch:
        fail("总账值不符 %s.%s：账记 %s → %s，实际 %s → %s"
             % (i, f, brief(d[0]), brief(d[1]), brief(a), brief(b)))
    # 总账过期（声明了却没变）
    for i in sorted(DECLARED):
        for f, d in sorted(DECLARED[i].items()):
            if i not in om or i not in nm:
                continue
            if om[i].get(f) == nm[i].get(f):
                fail("总账过期：`%s.%s` 声明为「有意变更」但实际与基线相同 ⇒ 删除或订正该条" % (i, f))
            elif (i, f, om[i].get(f), nm[i].get(f)) not in hit:
                pass    # 值不符已在上面报过

    # ── ③ 连线（条数 / pts / 色宽箭头 / 状态）────────────────────────────
    print("\n【③ 连线】")
    ol, nl = old.get("links", []), new.get("links", [])
    if len(ol) != len(nl):
        fail("连线条数变了：%d → %d" % (len(ol), len(nl)))
    else:
        geo_old = [(k["color"], k["w"], bool(k["arrow"]), k.get("state")) for k in ol]
        geo_new = [(k["color"], k["w"], bool(k["arrow"]), k.get("state")) for k in nl]
        chg = [k for k in range(len(ol)) if geo_old[k] != geo_new[k]]
        pts_chg = [k for k in range(len(ol)) if ol[k]["pts"] != nl[k]["pts"]]
        print("      (color,w,arrow,state) 变化 %d 处 ｜ `pts` 变化 %d 处" % (len(chg), len(pts_chg)))
        for k in chg:
            fail("未追认的连线变更 #%d：%s → %s" % (k, geo_old[k], geo_new[k]))
        for k in pts_chg:
            fail("未追认的连线路径变更 #%d（`pts` 逐点比）" % k)
        if not chg and not pts_chg:
            ok("连线条数、`pts`、`color`/`w`/`arrow`/`state` 与基线一致")
    keys_old = sorted({k for lk in ol for k in lk})
    keys_new = sorted({k for lk in nl for k in lk})
    if keys_old != keys_new:
        print("      键集：基线 %s → 现值 %s（`kind`→`state` 属第 2 批已并入，不应再变）" % (keys_old, keys_new))

    # ── ④ 屏级字段（白名单里的非判据字段 + `DECLARED_SCREEN` 里逐条追认的载荷字段）────
    print("\n【④ 屏级字段】")
    sc = [k for k in set(old) & set(new) if old[k] != new[k] and k not in ("elements", "links")]
    bad_sc = [k for k in sc
              if k not in SCREEN_FIELD_ALLOW and k not in DECLARED_SCREEN]
    print("      变化：%s（白名单 %s；逐条追认表 %s）"
          % (sc or "无", list(SCREEN_FIELD_ALLOW), sorted(DECLARED_SCREEN)))
    for k in sc:
        if k in SCREEN_FIELD_ALLOW:
            continue
        d = DECLARED_SCREEN.get(k)
        if d is None:
            continue
        o, n, why = d
        if old[k] == o and new[k] == n:
            print("      账内  %-16s %s → %s" % (k, brief(o), brief(n)))
            print("            └ %s" % why)
        else:
            fail("总账值不符（屏级）`%s`：账记 %s → %s，实际 %s → %s"
                 % (k, brief(o), brief(n), brief(old[k]), brief(new[k])))
    for k in bad_sc:
        fail("未追认的屏级字段变更 `%s`" % k)
    # ★ 总账过期（声明了却没变）—— 防「空壳豁免」
    for k, d in sorted(DECLARED_SCREEN.items()):
        if k not in old or k not in new:
            fail("总账过期：`DECLARED_SCREEN` 声明 `%s`，但该键在基线或现值中不存在 ⇒ 删除该条" % k)
        elif old[k] == new[k]:
            fail("总账过期：屏级 `%s` 声明为「有意变更」但两侧相同 ⇒ 删除该条" % k)
    kadd, krm = sorted(set(new) - set(old)), sorted(set(old) - set(new))
    if kadd or krm:
        fail("屏级键集变化：新增 %s / 删除 %s" % (kadd, krm))

    mutate_selfcheck(om)
    check_new_mode_payload(new)
    # ★ 第 16 批（`ISSUE-20260930-06`）：番外独立层纵向流水 ⇒ 新增 G6 13–20 格 ×3 的**几何追认**（含变异自证）
    check_new_frag_cells(new)

    print("\n" + "-" * 78)
    if FAILS:
        print("结果：**不通过**（退出码 1）—— %d 处" % len(FAILS))
        return 1
    print("结果：**通过**（退出码 0）—— 相对基线 `%s`：元素集合一致、未追认差异 **0 处**、"
          "总账 %d 条全部命中且值相符、连线与屏级字段均在允许范围"
          % (BASE_REF, sum(len(v) for v in DECLARED.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

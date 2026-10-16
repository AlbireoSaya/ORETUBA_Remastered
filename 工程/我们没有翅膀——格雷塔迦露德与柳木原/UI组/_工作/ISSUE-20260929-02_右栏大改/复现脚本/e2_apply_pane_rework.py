# -*- coding: utf-8 -*-
# ★★ 一次性脚本 · 已应用 · **不得重跑**（★ 第 3 轮补注）　　　　　　　　　　　　　　　　　　　　　　#
#   本脚本把「第 1 轮」的右栏改造应用到生成器的静态元素快照上，**已经跑过并已被第 3 轮改排取代**。
#   它内嵌的是**第 1 轮几何**（`y` 536/631/824、`h` 159、`max_lines 5`），且自带守卫
#   （`--dry` 实测会报 `[FAIL] 待删件 fc.mini1 不在快照里（脚本已跑过？）`）⇒ **重跑无害但无意义**。
#   历史留痕用途，勿据此判断现值；**现值一律以屏数据 / `工具\gen_flow_layout.py` 为准**。

r"""e2_apply_pane_rework.py —— ISSUE-20260929-02 · 模块 E2（生成器）· 右栏大改：**静态元素快照**改造

只做一件事：把冻结书 §B.1（删 12 件）/ §B.2（新增 3 件）/ §B.3（改动 8 件）落到
`工具\gen_flow_layout.py` 内嵌的 `STATIC_ELEMENTS_JSON` 字面量上。

口径：
  · 快照是 `json.dumps(obj, indent=1, ensure_ascii=False)` 的逐字产物（已实测**往返字节相同**）
    ⇒ 用 json 读改写；**未点名元素一个字节不动**（键序原样保留，可用 `git diff` 复核）。
  · **只删元素，不删素材**（`ui/x_ui_replay_panel.png` 等一律保留）。
  · 散文（docstring / SCREEN_NOTE / PASSTHROUGH_REQUIRED / PRESET_TABLE / 两处自检）不在本脚本，
    由主编辑另行落实 —— 本脚本只碰 `STATIC_ELEMENTS_JSON` 字面量。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260929-02_右栏大改/复现脚本/e2_apply_pane_rework.py"          # 应用
    python "_工作/ISSUE-20260929-02_右栏大改/复现脚本/e2_apply_pane_rework.py" --dry   # 只报告
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
GEN = os.path.join(UI, "工具", "gen_flow_layout.py")

DELETE = ["fc.mini%d" % i for i in range(1, 9)] + ["fc.mapview", "fc.pbk_panel",
                                                   "fc.p_player", "fc.p_player_tx"]

ISSUE = "ISSUE-20260929-02"

PLAYWIN_SOURCE = (
    "素材组产出（ISSUE-20260929-02 · 冻结 §A · 程序化合成，照 `ui/x_ui_replay_panel.png` 同一配方："
    "霜白竖向渐变 + 2px 细蓝边 + 外沿柔光 + 上沿内侧白高光带）：`ui/x_ui_playwin_bg.png` **380×300**"
    "（盘面上**不烘焙任何文字**）。旧回放窗底板 `ui/x_ui_replay_panel.png`（426×241）的**元素**已随本批退场，"
    "**素材文件保留**（冻结 §E：只删元素、不删图）。"
)
PAUSE_SOURCE = (
    "素材组产出（ISSUE-20260929-02 · 冻结 §A.1「派生版」）：复用 `m55_make_flow_assets.py` 的 "
    "`pbkick_base(state)` **只替换字形掩膜**（两条圆角竖条 ‖，高 54 / 圆角 2 / 条宽 16 间隙 16）"
    "⇒ 盘面（外发光 + 盘体 + 环）与**同态播放键逐像素相同**：`ui/x_ui_pbkick_pause_{off,over,on}.png` "
    "119×119 ×3（PNG-32 真 alpha）。另出的 AI 版暂停键落 "
    "`_工作\\ISSUE-20260929-02_右栏大改\\暂停键_AI版\\`、**不接线**，等用户二选一。"
)

NOTE_TITLE = (
    "右栏「标题」槽底（程序化 rect；`x1416 w443 h73` 沿用 PSB `#rects/title`）\n"
    "★ {0}（2026-09-29 · **用户指令 4**）：右栏重排为「① 大播放窗 ② 标题 ③ 说明 ④ 台词」四段 ⇒ "
    "本件 `y` **214 → 536**（第 2 段 y 区间 536–609）。`x`/`w`/`h` **一律不动**（冻结 §B.4：横向三槽底不动）。"
    "旧 note 的「y214」为**改前**位置，已作废。"
).format(ISSUE)

NOTE_TITLE_TX = (
    "「标题」标签（引擎绘制）\n"
    "★ {0}（2026-09-29 · **用户指令 1 / 4**）：① `font.color` `@palette.node_locked` → "
    "**`@palette.text_primary`**（白字）并增 `outline:true` / `outline_color:\"#000000\"` / "
    "`outline_width:2`（黑描边 2px；写法照 `layout\\screens\\10_dialog.json` 的 `dlg.text`，"
    "`shadow` **保持 `false`**）；② 随第 2 段下移 ⇒ `y` **224 → 546**（`_tx` 比槽底 +10）。"
    "字号 **24** / `bold:true` **未动**（用户只要求改颜色与描边）；本槽**不扩**："
    "`h40` / `valign:\"middle\"` / `wrap:false` / `max_lines:1`（标题一行 443 宽）。"
).format(ISSUE)

NOTE_TEXT = (
    "右栏「说明」槽底（程序化 rect；`x1425 w422 h171` 沿用 PSB `#rects/text`）\n"
    "★ {0}（2026-09-29 · **用户指令 4**）：四段重排 ⇒ 本件 `y` **309 → 631**（第 3 段 631–802）。"
    "`x`/`w`/`h` 不动。旧 note 的「y309」为**改前**位置，已作废。"
).format(ISSUE)

NOTE_TEXT_TX = (
    "「说明」标签（引擎绘制）\n"
    "★ {0}（2026-09-29 · **用户指令 1 / 4**）：① 同 `fc.p_title_tx` —— 白字 "
    "`@palette.text_primary` + 黑描边 2px（`outline:true` / `outline_color:\"#000000\"` / "
    "`outline_width:2`，写法照 `10_dialog.json` 的 `dlg.text`；`shadow` 保持 `false`）；"
    "② 随第 3 段下移并**扩槽**：`(1437,319,398,40)` → **`(1437,637,398,159)`**、"
    "`valign` `middle` → **`top`**、`wrap` `false` → **`true`**、`max_lines` `1` → **`4`**"
    "（**第 2 轮主代理裁决（2026-09-29）**：槽净高 **159** ÷ 行盒 **33px**"
    "（＝ `floor(24 × 全局 line_spacing.body 1.4)`，见 `krkr/game/ui_theme.tjs:237-238` ＋ "
    "`layout/_root.json:66`）＝ **4.82 ⇒ `max_lines` 4**（4 行 132 ≤ 159 ✓；**5 行 165 越槽底 6px ✗**）；"
    "**不加**元素级 `line_spacing` —— 保持全局基线）。`x`/`w` 未动；字号 24 / `bold:true` **未动**。"
).format(ISSUE)

NOTE_MESSAGE = (
    "右栏「台词」槽底（程序化 rect；`x1425 w422 h171` 沿用 PSB `#rects/message`）\n"
    "★ {0}（2026-09-29 · **用户指令 4**）：四段重排 ⇒ 本件 `y` **750 → 824**（第 4 段 824–995）。"
    "`x`/`w`/`h` 不动。旧 note 的「y750」为**改前**位置，已作废。"
).format(ISSUE)

NOTE_MESSAGE_TX = (
    "「台词」标签（引擎绘制）\n"
    "★ {0}（2026-09-29 · **用户指令 1 / 4**）：① 同 `fc.p_title_tx` —— 白字 "
    "`@palette.text_primary` + 黑描边 2px（`outline:true` / `outline_color:\"#000000\"` / "
    "`outline_width:2`，写法照 `10_dialog.json` 的 `dlg.text`；`shadow` 保持 `false`）；"
    "② 随第 4 段下移并**扩槽**：`(1437,760,398,40)` → **`(1437,830,398,159)`**、"
    "`valign` `middle` → **`top`**、`wrap` `false` → **`true`**、`max_lines` `1` → **`4`**"
    "（同 `fc.p_text_tx` 的 **4 行**推导：槽净高 159 ÷ 行盒 33px ＝ 4.82 ⇒ 4；**5 行 165 越槽底 6px**）。"
    "`x`/`w` 未动；字号 24 / `bold:true` **未动**。"
).format(ISSUE)

NOTE_PLAYWIN = (
    "★ {0} **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 2**）：**大播放窗底板**。\n"
    "· **取代**（本批已退场）：8 张缩略图 `fc.mini1..8` + 缩略图可视区框 `fc.mapview`（迷你地图组）"
    "＋ 场景回放组的 `fc.pbk_panel` / `fc.p_player` / `fc.p_player_tx`（回放窗底板元素）。\n"
    "· 用途：运行期由编程组在该窗内**按顺序播放该章节的游戏内画面**（画面层＝ `fc.play_view`，"
    "`dynamic:\"flow_scene_frames\"`）。\n"
    "· 几何 `1448,214,380,300`：**与旧 `fc.mapview` 同尺寸（380×300）**，"
    "在 443 宽的栏底 `fc.smallmap`（1416,190,443×829）内**居中** ⇒ `x = 1416 + ceil((443 − 380)/2) = 1416 + 32 = 1448`"
    "（左留 32 / 右留 31）；`y=214` ＝ 四段第 1 段顶（栏内上边距 24）。\n"
    "· `z=6`（与三个槽底同档、在 `fc.smallmap` z5 之上；画面层 `fc.play_view` z7）。"
    "380×300 与素材**等尺寸 ⇒ 1:1、不加 `nine`**。\n"
    "· 旧描述「右栏详情 / 迷你地图 / 回放窗底板」等一律作废（本件是新族，不复用旧 id）。"
).format(ISSUE)

NOTE_PLAYVIEW = (
    "★ {0} **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 2**）：**大播放窗的画面层**。\n"
    "· `asset:null` + `dynamic:\"flow_scene_frames\"` ⇒ 运行期由编程组按顺序填入该章节的游戏内画面；"
    "**未填充时两端必须画占位底色**（`layout\\_schema.md` §四 `dynamic` 条，**不得跳过**；"
    "写法照 `10_dialog.json` 的 `dlg.content`）。\n"
    "· 几何＝底板内缩 6px：`(1448+6, 214+6, 380−12, 300−12)` = **`(1454,220,368,288)`**；"
    "`z=7` ＝ `fc.play_win` z6 + 1。\n"
    "· ★ **窗为 380×300（≈1.267:1），16:9 画面需 `contain` 居中适配、上下留边**"
    "（**不拉伸、不裁切**；画面时序/帧序列接线留编程组）。"
).format(ISSUE)

NOTE_PBKICK = (
    "**播放键**（大播放窗 380×300 中央的「播放」键；PSB 原字段名 `pbkick` 保留为 id）\n"
    "★ {0}（2026-09-29 · **用户指令 3**）：\n"
    "· ① 移到**大播放窗中央**：`(1576,555)` → **`(1578,304)`**"
    "（件中心 (1637.5,363.5) ＝ 窗中心；窗内水平居中）。\n"
    "· ② **与暂停键 `fc.pbkick_pause` 同位置、靠 `vis_flag:\"fc_replay\"` 互斥**：本件 "
    "`vis_when:\"play\"`、暂停键 `vis_when:\"pause\"`（屏级 flag 初值 `play` ⇒ 初始显示本件）；"
    "**同一时刻只有一个可见**（`layout\\_schema.md` §四 **铁律一**：只在状态上互斥的重叠件必须靠 flag，"
    "**不得靠 z 排序**）。\n"
    "· ③ 素材三态 `ui/x_ui_pbkick_{{off,over,on}}.png` 119×119 **不变**（1:1、无 `nine`）；"
    "`visible_default` **保持 `true`**（判定语义的前置条件，写 `false` 即死件）。\n"
    "· ④ 视觉与命中由 `fc.pbkick_hit`（共同热区）派发 **`flow_replay_toggle`** 承担。\n"
    "· ⑤ 本件是**外壳件**、且是本批**唯一获批带 `vis_flag` 的外壳件**（具名豁免集 "
    "`STATIC_FLAG_EXEMPT`）：`fc_replay` **不是层旗标**，其初值 `\"play\"` 在**任何层**都成立 ⇒ "
    "播放键恒可见，「切层丢外壳」这条禁令要防的风险**不存在**（冻结 §B.6）。\n"
    "★ 旧 note 的「x1576 y555 / 场景回放键」为**改前**值，已作废。"
).format(ISSUE)

NOTE_PAUSE = (
    "★ {0} **新增**（2026-09-29 · 冻结 §B.2 · **用户指令 3**）：**暂停键**"
    "（用户说的「停止键（竖着的两条线）」按术语对齐 ＝ **暂停 ⏸**）。\n"
    "· 与 `fc.pbkick`（播放键）**同位置、互斥显示**：本件 `vis_when:\"pause\"`、播放键 `vis_when:\"play\"`"
    "（同一对屏级 flag **`fc_replay`**）⇒ **同一时刻只有一个可见**（铁律一：靠 flag，不靠 z）。\n"
    "· 几何与播放键**逐字段相同**：`(1578,304,119,119)`、`z=20`。\n"
    "· 三态素材 `ui/x_ui_pbkick_pause_{{off,over,on}}.png` **119×119 ＝ 元素等尺寸 ⇒ 1:1、无 `nine`**；"
    "`visible_default:true`（铁律：靠 flag 控显隐的元素写 `false` 会成死件）。\n"
    "· 本件是**外壳件**、与播放键同在豁免集 `STATIC_FLAG_EXEMPT`（理由见冻结 §B.6）。\n"
    "· 命中与派发走**共同热区** `fc.pbkick_hit`（两键同位置 ⇒ 一条热区即够）。"
).format(ISSUE)

NOTE_PBKICK_HIT = (
    "播放/暂停键的**共同热区**（覆盖两键同一位置，外边各扩 3px）\n"
    "★ {0}（2026-09-29 · **用户指令 3** · 冻结 §B.5）：\n"
    "· ① 随播放键移到**大播放窗中央**：`(1573,552,125,125)` → **`(1575,301,125,125)`**"
    "（件中心 (1637.5,363.5) ＝ 窗中心）。\n"
    "· ② `action` 由**空串** → **`\"flow_replay_toggle\"`**：语义＝「播放/暂停切换」，**命中即派发**；"
    "**播放本身（画面时序、帧序列）接线留编程组**（与 `bgm_playpause` ／ `replay_play:<行号>` 同口径，"
    "**不得声称已生效**）。该动作名登记进 `layout\\_schema.md` §六 动作表与 "
    "`UI组\\UI组交接编程组.md`（由主代理/E3 落实）。\n"
    "· ③ 两键**同位置互斥** ⇒ **一条热区即够**（勿按可见键拆成两条；两态都不会漏掉命中）。\n"
    "· `z=95`（高于两键 z20）。旧 note 的「场景回放热区 / 无 action」已作废。"
).format(ISSUE)

NEW_WIN = {
    "id": "fc.play_win",
    "kind": "image",
    "z": 6,
    "visible_default": True,
    "asset": "ui/x_ui_playwin_bg.png",
    "x": 1448,
    "y": 214,
    "w": 380,
    "h": 300,
    "opacity": 255,
    "source": PLAYWIN_SOURCE,
    "note": NOTE_PLAYWIN,
}
NEW_VIEW = {
    "id": "fc.play_view",
    "kind": "image",
    "z": 7,
    "visible_default": True,
    "asset": None,
    "dynamic": "flow_scene_frames",
    "x": 1454,
    "y": 220,
    "w": 368,
    "h": 288,
    "opacity": 255,
    "note": NOTE_PLAYVIEW,
}
NEW_PAUSE = {
    "id": "fc.pbkick_pause",
    "kind": "image",
    "z": 20,
    "visible_default": True,
    "vis_flag": "fc_replay",
    "vis_when": "pause",
    "asset": "ui/x_ui_pbkick_pause_off.png",
    "x": 1578,
    "y": 304,
    "w": 119,
    "h": 119,
    "opacity": 255,
    "source": PAUSE_SOURCE,
    "note": NOTE_PAUSE,
    "state_assets": {
        "normal": "ui/x_ui_pbkick_pause_off.png",
        "hover": "ui/x_ui_pbkick_pause_over.png",
        "pressed": "ui/x_ui_pbkick_pause_on.png",
    },
}

# font 键序与 `10_dialog.json` 的 `dlg.text` 逐键同序（size/bold/color/shadow/shadow_color/
# shadow_ofs/outline/outline_color/outline_width）
WHITE_FONT = {
    "size": 24,
    "bold": True,
    "color": "@palette.text_primary",
    "shadow": False,
    "shadow_color": "@palette.shadow",
    "shadow_ofs": 0,
    "outline": True,
    "outline_color": "#000000",
    "outline_width": 2,
}

# 新键的插入锚（键序：插在锚键之后）—— 只对 `fc.pbkick` 需要
INSERT_KEY_AFTER = {"fc.pbkick": {"visible_default": ["vis_flag", "vis_when"]}}

UPDATES = {
    "fc.p_title": {"y": 536, "note": NOTE_TITLE},
    "fc.p_title_tx": {"y": 546, "font": dict(WHITE_FONT), "note": NOTE_TITLE_TX},
    "fc.p_text": {"y": 631, "note": NOTE_TEXT},
    "fc.p_text_tx": {"x": 1437, "y": 637, "w": 398, "h": 159, "valign": "top",
                     "wrap": True, "max_lines": 4, "font": dict(WHITE_FONT),
                     "note": NOTE_TEXT_TX},
    "fc.p_message": {"y": 824, "note": NOTE_MESSAGE},
    "fc.p_message_tx": {"x": 1437, "y": 830, "w": 398, "h": 159, "valign": "top",
                        "wrap": True, "max_lines": 4, "font": dict(WHITE_FONT),
                        "note": NOTE_MESSAGE_TX},
    "fc.pbkick": {"x": 1578, "y": 304, "vis_flag": "fc_replay", "vis_when": "play",
                  "note": NOTE_PBKICK},
    "fc.pbkick_hit": {"x": 1575, "y": 301, "action": "flow_replay_toggle",
                      "note": NOTE_PBKICK_HIT},
}

INSERT_AFTER = {"fc.p_message_tx": [NEW_WIN, NEW_VIEW], "fc.pbkick": [NEW_PAUSE]}


def apply_update(e, upd):
    """保留原键序；`INSERT_KEY_AFTER` 指定的新键插到锚键之后，其余新键追加到末尾（note 前）。"""
    ins = INSERT_KEY_AFTER.get(e["id"], {})
    new = {}
    for k, v in e.items():
        new[k] = upd.get(k, v)
        for nk in ins.get(k, []):
            if nk in upd:
                new[nk] = upd[nk]
    rest = [k for k in upd if k not in new and k != "note"]
    for k in rest:
        new[k] = upd[k]
    if "note" in upd and "note" not in new:      # 兜底：note 总是最后
        new["note"] = upd["note"]
    return new


def main(dry=False):
    src = io.open(GEN, encoding="utf-8").read()
    m = re.search(r'STATIC_ELEMENTS_JSON = r"""(.*?)"""', src, re.S)
    if not m:
        raise SystemExit("[FAIL] 未在 %s 找到 STATIC_ELEMENTS_JSON 字面量" % GEN)
    old_text = m.group(1)
    els = json.loads(old_text)
    ids_before = [e["id"] for e in els]
    print("改前：静态件 %d 件" % len(els))

    for i in DELETE:
        if i not in ids_before:
            raise SystemExit("[FAIL] 待删件 %s 不在快照里（脚本已跑过？）" % i)
    for i in [e["id"] for v in INSERT_AFTER.values() for e in v]:
        if i in ids_before:
            raise SystemExit("[FAIL] 待新增件 %s 已存在（脚本已跑过？）" % i)

    # ── B.1 删除 12 件（**素材一个不删**）──
    els = [e for e in els if e["id"] not in DELETE]
    print("B.1 删除 %d 件（只删元素、不删素材）：%s" % (len(DELETE), ", ".join(DELETE)))

    # ── B.3 改动 8 件 ──
    out = []
    for e in els:
        upd = UPDATES.get(e["id"])
        if upd:
            before = {k: e.get(k) for k in upd}
            e2 = apply_update(e, upd)
            print("B.3 改 %-16s %s ⇒ %s"
                  % (e["id"], json.dumps(before, ensure_ascii=False),
                     json.dumps({k: e2.get(k) for k in upd}, ensure_ascii=False)))
            out.append(e2)
        else:
            out.append(e)
    els = out

    # ── B.2 新增 3 件（插在锚点之后）──
    for anchor, news in INSERT_AFTER.items():
        pos = [i for i, e in enumerate(els) if e["id"] == anchor]
        if not pos:
            raise SystemExit("[FAIL] 锚点 %s 不在快照里" % anchor)
        at = pos[0] + 1
        els[at:at] = [json.loads(json.dumps(n, ensure_ascii=False)) for n in news]
        print("B.2 新增 %d 件（插在 %s 之后）：%s"
              % (len(news), anchor, ", ".join(n["id"] for n in news)))

    new_text = json.dumps(els, indent=1, ensure_ascii=False)
    ids_after = [e["id"] for e in els]
    print("改后：静态件 %d 件 ＝ %d − %d ＋ %d"
          % (len(els), len(ids_before), len(DELETE),
             len(ids_after) - (len(ids_before) - len(DELETE))))
    print("改后 id：%s" % ", ".join(ids_after))
    if dry:
        print("[dry] 未写文件；新快照 %d 字节" % len(new_text.encode("utf-8")))
        return 0
    src2 = src[:m.start(1)] + new_text + src[m.end(1):]
    with io.open(GEN, "w", encoding="utf-8", newline="\n") as f:
        f.write(src2)
    print("→ 已写回 %s（快照 %d → %d 字节）"
          % (GEN, len(old_text.encode("utf-8")), len(new_text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(dry="--dry" in sys.argv))

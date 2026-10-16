# -*- coding: utf-8 -*-
r"""M51 · BGM 鉴赏页 · **一次性脚手架**：产出 `layout\screens\28_music.json`

Issue : ISSUE-20260924-08（鉴赏模式四页重构 · **M3 = BGM 页**）
契约  : `_工作\ISSUE-20260924-08_鉴赏模式\方案.md`（接口冻结书）
参考件: `工程\交汇协奏曲\解包\gallery\结构清单.md` §2.2（BGM 页 **34 条**）+ `layers_75.json`（矩形实测）

■■ 为什么是一次性脚手架（不保留为常驻生成器）
  先例：M47 的 `_工作\M47_设置屏重设\复现脚本\m47_build_config.py`、
        M49 的 `_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_build_backlog.py`。
  本屏是**结构性重绘**（30 件静态行 → 1 个二维网格 list + 逐项按钮 + 音量滑块 + 翻页），
  且 `28_music.json` 原先挂在 `test_gen_sync.py` 的 `GENERATORS`（`m34_build_screens.build_music`）
  ⇒ 回写生成器收益 < 两真相源互踩的风险；**退休生成器 + 本脚本一次性产出 + 此后手工维护**。

■■ 运行
    python _工作\ISSUE-20260924-08_鉴赏模式\M3_BGM\m51_build_music.py
  幂等：同输入重跑逐字节一致（无随机、无时间戳）。
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # <UI组>
# ★ 两段式落盘（任务书 D 条纪律）：
#   `28_music.json` 原先挂在 `test_gen_sync.py` 的 `GENERATORS`（`m34_build_screens.build_music`），
#   **未退休前不得直接改该文件**（否则 test_gen_sync 必报 UNSYNC/LOSS）。
#   ⇒ 本脚本默认只写**草稿** `28_music.draft.json`；主代理裁决「退休生成器」后加 `--install` 落盘。
OUT_DRAFT = os.path.join(HERE, "28_music.draft.json")
OUT_REAL = os.path.join(UI, "layout", "screens", "28_music.json")
OUT = OUT_REAL if "--install" in sys.argv else OUT_DRAFT
CAND = os.path.join(HERE, "m51_bgm_candidates.tsv")

# ──────────────────────────────────────────────────────────── 几何（**唯一出处**）
#   参考作实测（`layers_75.json`，基准 1920×1080）：
#     Sound/pos/#0|#1|#2/0…9 → 列步进 527/526、行步进 60、行矩形 481×59、每页 30 槽（3×10）
#     卡体 `Sound/item/オフ` (205,217,452,37)；行内播放键 `Sound/item/play` (171,214,29,40)
#     播放控制 `Sound/ボタン/#pos/*` (x,831,59,59)，x = 609/702/793/885/975/1062/1153/1234
#     音量 `volume/バー` (718,915,488,14)、`volume/オン|オフ` (945,907,29,29)
#     频谱 `Sound/#speana` (781,966,359,48)
#   ★ 一个 `gap` 同时用于两轴（M1 的 `uiWidgetListItemRect`）⇒ 取 gap=1（行步进 60 − 行高 59）
#     并令 `item_w = 527 − 1 = 526` ⇒ 列步进 527 ✓；行矩形 481→526 只是块变宽，
#     **卡体仍在块内 (34,10)-(486,47) ⇒ 卡体绝对位置 205/732/1259，与参考作 205/732/1258 对齐**。
COLS, ROWS = 3, 10
ITEM_W, ITEM_H, GAP = 526, 59, 1
LIST_X, LIST_Y = 171, 207
LIST_W = COLS * ITEM_W + (COLS - 1) * GAP          # 1580
LIST_H = ROWS * ITEM_H + (ROWS - 1) * GAP          # 599
PAGE_SIZE = COLS * ROWS                            # 30

PB_X = {"none": 609, "one": 702, "all": 793, "rnd": 885,
        "prev": 975, "playpause": 1062, "stop": 1153, "next": 1234}
PB_CN = {"none": "无循环", "one": "单曲循环", "all": "全曲循环", "rnd": "随机",
         "prev": "上一曲", "playpause": "播放/暂停", "stop": "停止", "next": "下一曲"}
# 动作名：`bgm_play:%row%` 是**主代理已冻结**的；其余 7 个是**拟用同族名**（待确认，见 note）。
PB_ACT = {"none": "bgm_mode_none", "one": "bgm_mode_one", "all": "bgm_mode_all",
          "rnd": "bgm_mode_rnd", "prev": "bgm_prev", "playpause": "bgm_playpause",
          "stop": "bgm_stop", "next": "bgm_next"}

FONT_BTN = {"size": 24, "bold": False, "color": "@palette.node_locked", "shadow": False,
            "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_LIST = {"size": 22, "bold": True, "color": "@palette.node_locked", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0}
FONT_PGTX = {"size": 24, "bold": True, "color": "@palette.text_menu", "shadow": False,
             "shadow_color": "@palette.shadow", "shadow_ofs": 0}

SRC_REF = ("AI 生图（gpt-image-2.5-1k）→ 工具\\lyai-image-api\\ui_gen.py + ui_slice.py；"
           "坐标取自《交汇协奏曲》PSB 容器")
SRC_M51 = "工具\\m51_make_bgm_assets.py（程序化生成，冰蓝霜白族；坐标取自《交汇协奏曲》PSB 容器）"


def load_tracks():
    """曲目（按剧本首次引用顺序；**曲名未知 ⇒ 用「序号 + 文件名标识」占位，不编造**）"""
    rows = []
    with open(CAND, encoding="utf-8") as f:
        head = f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            rows.append(p)
    labels = []
    for i, p in enumerate(rows, 1):
        stem = p[2].split("/")[-1].rsplit(".", 1)[0]
        labels.append("%02d　%s" % (i, stem))
    return rows, labels


def main():
    rows, labels = load_tracks()
    n = len(labels)
    pages = (n + PAGE_SIZE - 1) // PAGE_SIZE
    els = []

    def add(e):
        els.append(e)

    # ── ① 全屏压暗（与 26_backlog / 27_gallery / 37_dress 同口径：系统屏是透明浮层）
    add({"id": "mu.dim", "kind": "rect", "z": 1, "visible_default": True,
         "x": 0, "y": 0, "w": 1920, "h": 1080,
         "color": "@palette.backdrop", "opacity": 70, "note": "全屏压暗遮罩"})

    # ── ② 曲目列表：**一个二维网格 list**（`orientation:"h"` + `max_cols`×`max_rows`）
    add({
        "id": "mu.list", "kind": "list", "z": 20, "visible_default": True,
        "orientation": "h",
        "x": LIST_X, "y": LIST_Y, "w": LIST_W, "h": LIST_H,
        "item_w": ITEM_W, "item_h": ITEM_H, "gap": GAP,
        "max_cols": COLS, "max_rows": ROWS,
        "scroll": {"mode": "page", "page_size": PAGE_SIZE},
        "labels": labels,
        "actions": [""] * n,
        "font": FONT_LIST, "align": "left",
        "highlight": {"kind": "rect", "color": "@palette.highlight",
                      "opacity": "@palette.highlight_opa"},
        "highlight_font_color": "@palette.text_primary",
        "item_frame": {
            "asset": "ui/x_ui_bgm_row_off.png",
            "state_assets": {"normal": "ui/x_ui_bgm_row_off.png",
                             "hover": "ui/x_ui_bgm_row_over.png",
                             "pressed": "ui/x_ui_bgm_row_on.png"},
            "opacity": 255},
        "item_text": {"x": 40, "y": 0, "w": 434, "h": ITEM_H, "wrap": False,
                      "max_lines": 1, "align": "left", "valign": "middle"},
        "item_buttons": [{
            "key": "play", "x": 0, "y": 7, "w": 29, "h": 40,
            "asset": "ui/x_ui_bgm_play_off.png",
            "state_assets": {"normal": "ui/x_ui_bgm_play_off.png",
                             "hover": "ui/x_ui_bgm_play_over.png",
                             "pressed": "ui/x_ui_bgm_play_on.png"},
            "action": "bgm_play:%row%",
            "label": "",
            "note": ("行内「播放」键（`item_buttons` 逐项子命中）。块内局部 0,7,29×40 —— "
                     "对应 PSB `Sound/item/play` (171,214,29,40)（块起点 171 ⇒ 局部 0,7）。"
                     "三态件 `ui/x_ui_bgm_play_{off,over,on}.png`（29×40，1:1 无 nine）。"
                     "动作 `bgm_play:%row%`（**主代理冻结**；`%row%` = 全局项序号，含分页偏移，"
                     "由 `uiWidgetListHit` 给出）。**本轮语义 = 命中 → 派发 → 焦点高亮可见**："
                     "引擎无音频代码（M47 已登记）⇒ 音频接线留给编程组，不得声称已生效。")}],
        "source": SRC_M51,
        "note": (
            "曲目列表（**一个二维网格 `list`**）。\n"
            "★ 几何：3 列 × 10 行 = **30 槽/页**，与参考作 `Sound/pos/#0|#1|#2` 逐格一致"
            "（列步进 527/526、行步进 60、行矩形 481×59）。`item_w=526`+`gap=1` ⇒ 列步进 527；"
            "`item_h=59`+`gap=1` ⇒ 行步进 60；外框 `w=@W@`（3×526+2×1）、`h=@H@`（10×59+9×1）。"
            "块内卡体 (34,10)-(486,47) ⇒ 卡体绝对位置 205/732/1259，对齐参考作 205/732/1258（1px 差）。\n"
            "★ **机制**：M1（ISSUE-20260924-08）为 `orientation:\"h\"` 实现 `max_cols`×`max_rows` "
            "网格（`uiWidgetListSpan` / `uiWidgetListPage` / `uiWidgetListItemRect` 折行 = "
            "`col = i % cols`、`row = floor(i / cols)`，与 HTML `buildList` 同公式）⇒ "
            "**一个 list 排 3×10**，翻页沿用既有 `scroll.page_size`（30）。"
            "`%row%` = `pg.first + i`（**全局项序号，含分页偏移**）⇒ 冻结的 `bgm_play:%row%` 原样成立。\n"
            "★ **折行顺序 = 行优先**（M1 落盘口径）⇒ 第 1 行 = 第 1..3 首、第 2 行 = 第 4..6 首……"
            "参考作 `pos` 编号是**列优先**（`#0/0..9` 一整列）⇒ **有意差异**（已登记；M1 未提供列优先开关）。\n"
            "★ 逐项三态 `item_frame.state_assets`（M46 机制）＝悬停/按下**只换被指到的那一行**的图；"
            "选中态 = `highlight` 块 + `highlight_font_color`，由既有 **focus** 驱动"
            "（`uiScreenClick` 命中列表即写 `UIScrFocus[list]`，见 ui_screens.tjs）⇒ "
            "点行/点播放键都会把该行点亮（**「播放中/选中」的本轮可见形态**）。\n"
            "★ 曲目数据：**@N@ 首**（来源 `m51_bgm_candidates.tsv`，按剧本首次引用顺序）⇒ "
            "**@P@ 页**（30 + @L@）。曲名语料内查无（见 `m51_bgm_report.txt` §④）⇒ "
            "`labels` 用「序号 + 文件名标识」**占位、不编造**，待真实曲名到位后替换。\n"
            "★ `actions[]` 全空串：整行点击**待编程组定义**（不臆造动作名）；"
            "注意空串在 `uiScreenClick` 会回落 `open_sysmenu`（展开快捷条）—— 既有行为，非本屏引入。"
        ).replace("@W@", str(LIST_W)).replace("@H@", str(LIST_H)).replace("@N@", str(n))
         .replace("@P@", str(pages)).replace("@L@", str(n - PAGE_SIZE * (pages - 1))), "source": SRC_M51})

    # ── ③ 翻页（参考作 BGM 页**无**页码键 ⇒ 取 CG 页页码键几何，与 M2 的 `gal.pg_*` 同形同尺寸）
    for key, x, act, cn, glyph in (("prev", 790, "gallery_page_prev", "上一页", "pgprev"),
                                   ("next", 1074, "gallery_page_next", "下一页", "pgnext")):
        grp = "mu.pg" + key
        add({"id": "mu.pg_%s" % key, "kind": "image", "z": 30, "visible_default": True,
             "asset": "ui/x_ui_bgm_%s_off.png" % glyph,
             "state_assets": {"normal": "ui/x_ui_bgm_%s_off.png" % glyph,
                              "hover": "ui/x_ui_bgm_%s_over.png" % glyph,
                              "pressed": "ui/x_ui_bgm_%s_on.png" % glyph},
             "state_group": grp,
             "x": x, "y": 939, "w": 56, "h": 56, "opacity": 255,
             "source": SRC_M51,
             "note": ("翻页键「%s」（56×56 圆角方盘，1:1 无 nine）。几何与 M2 的 `gal.pg_prev/next` "
                      "同源（790/1074, y939, 56×56）—— 参考作 BGM 页无页码键，取 CG 页页码键位置以统一四页。"
                      "三态件 `ui/x_ui_bgm_%s_{off,over,on}.png`。" % (cn, glyph))})
        add({"id": "mu.pg_%s_hit" % key, "kind": "hit", "z": 32, "visible_default": True,
             "x": x - 7, "y": 931, "w": 70, "h": 72,
             "action": act, "label": "", "font": FONT_BTN, "align": "center",
             "state_group": grp,
             "note": ("翻页热区（**带 `state_group`**：与同组 image 一起换三态 ⇒ 按下态可达；"
                      "M2 的 `gal.pg_*` 未挂组、其 `_on` 件不可达，本条为**改良**）。"
                      "动作 `%s`（冻结书 §5 冻结名）。" % act)})
    add({"id": "mu.pg_tx", "kind": "text", "z": 31, "visible_default": True,
         "x": 858, "y": 939, "w": 204, "h": 56, "font": FONT_PGTX,
         "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
         "sample": "1 / %d" % pages,
         "note": "页码指示（引擎绘制，与 M2 的 `gal.pg_tx` 同几何；实际页码由编程组/机制写入）"})

    # ── ④ 播放控制 8 键（PSB `Sound/ボタン/#pos/*` 59×59 @y831）
    for key, x in PB_X.items():
        grp = "mu.pb_" + key
        add({"id": "mu.pb_%s" % key, "kind": "image", "z": 20, "visible_default": True,
             "asset": "ui/x_ui_bgm_pb_%s_off.png" % key,
             "state_assets": {"normal": "ui/x_ui_bgm_pb_%s_off.png" % key,
                              "hover": "ui/x_ui_bgm_pb_%s_over.png" % key,
                              "pressed": "ui/x_ui_bgm_pb_%s_on.png" % key},
             "state_group": grp, "x": x, "y": 831, "w": 59, "h": 59, "opacity": 255,
             "source": SRC_M51,
             "note": ("播放控制「%s」（PSB `Sound/ボタン/#pos/%s` x%d y831 59×59）。"
                      "三态件 `ui/x_ui_bgm_pb_%s_{off,over,on}.png`（59×59，1:1 无 nine）—— "
                      "参考作该条是**整张图标条三态位图**（647×47/653×53），我方改**逐键出件**"
                      "（与 M37 药丸/徽章同路线：逐键可独立换态，不必整条一起亮）。"
                      "**字形为纯图形、不含文字**：参考作图标条里 `1`/`ALL`/`RND` 是烘焙拉丁字，"
                      "本工程铁律禁止文字烘焙 ⇒ 改画「循环弧+单点／循环弧+三点／交叉箭头」等图形。"
                      % (PB_CN[key], key, x, key))})
        add({"id": "mu.pb_%s_hit" % key, "kind": "hit", "z": 95, "visible_default": True,
             "x": x, "y": 831, "w": 59, "h": 59,
             "action": PB_ACT[key], "label": "", "font": FONT_BTN, "align": "center",
             "state_group": grp,
             "note": ("「%s」热区。动作名 `%s` = **拟用**（与已冻结的 `bgm_play:%%row%%` 同 `bgm_` 族；"
                      "**待主代理/M1 确认**）。若否决 ⇒ 改空串，但空串会回落 `open_sysmenu`（展开快捷条）"
                      "—— 那是既有行为，非本屏引入。" % (PB_CN[key], PB_ACT[key]))})

    # ── ⑤ 音量（PSB `Sound/volume/バー` 488×14 + `volume/オン|オフ` 29×29）
    add({"id": "mu.vol", "kind": "slider", "z": 22, "visible_default": True,
         "x": 718, "y": 907, "w": 488, "h": 29,
         "min": 0, "max": 100, "step": 5, "value": 80,
         "setting": "vol_bgm",
         "rail": {"asset": "ui/x_ui_bgm_rail.png"},
         "handle": {"asset": "ui/x_ui_bgm_knob.png",
                    "state_assets": {"normal": "ui/x_ui_bgm_knob.png",
                                     "hover": "ui/x_ui_bgm_knob_over.png"}},
         "source": SRC_M51,
         "note": ("BGM 音量滑块（PSB `Sound/volume/バー` (718,915,488,14) + "
                  "`volume/オン|オフ` (945,907,29,29)）。元素框 (718,907,488,29)：轨道 488×14 "
                  "以垂直中心线为轴（y = 907+7.5 ≈ 915 ✓ 与参考作同位），手柄 29×29（1:1，不随框裁剪）。"
                  "`setting=\"vol_bgm\"` = **既有设置键**（`ui_settings.tjs::UISettingDef`，默认 80）。"
                  "手柄两态件 `ui/x_ui_bgm_knob{,_over}.png` 对应参考作 `volume/オフ`（素圆）/`オン`（带 ♪）。"
                  "★ **音量类只存值**：引擎无音频代码（M47 已登记）⇒ 值写入设置仓，**实际音量由编程组接线**，"
                  "不得声称已生效。")})
    add({"id": "mu.vol_hit", "kind": "hit", "z": 95, "visible_default": True,
         "x": 714, "y": 898, "w": 496, "h": 33,
         "action": "", "label": "", "font": FONT_BTN, "align": "center",
         "slider": "mu.vol",
         "note": ("音量滑块的**拖动热区**（方案 §3.2：hit 带 `slider=\"mu.vol\"` ⇒ 按下即绑定拖动、"
                  "悬停期间按 x 持续更新、抬起/换屏解绑）。★ **不带 `state_group`**（滑块不入悬停候选并集，"
                  "M47 口径）；手柄两态由 `ctx.hoverSlider`/`dragSlider` 驱动。"
                  "几何 (714,898,496,33)：覆盖轨道与手柄中段（y 898..931；轨道 907..936、手柄 907..936，"
                  "**拖动手感锚点在中心线 y≈921.5，已覆盖**）—— 上沿留 9px、下沿止于 **931** ⇒ "
                  "**与页码键热区（y 931 起）零重叠**（初版取 898..936 与 `mu.pg_*_hit` 叠了 5px，"
                  "草稿自检 ⑦ 抓到后收紧）。")})

    # ── ⑥ 频谱装饰（PSB `Sound/#speana` (781,966,359,48)，opacity 153）
    add({"id": "mu.speana", "kind": "image", "z": 20, "visible_default": True,
         "asset": "ui/x_ui_speana.png",
         "x": 781, "y": 966, "w": 359, "h": 48, "opacity": 153,
         "nine": {"l": 18, "t": 16, "r": 18, "b": 16},
         "source": SRC_REF,
         "note": ("频谱条占位（PSB `Sound/#speana` (781,966,359,48)，opacity 153）。"
                  "★ **纯装饰**：引擎无音频代码 ⇒ 频谱不接线（参考作该件亦是无贴图矩形占位）。")})

    doc = {
        "id": "music",
        "title_cn": "音乐鉴赏",
        "owner": "M3",
        # ★ 附加层 id = **屏 id**（不是文件名）：M1 的 `UIScrGalleryShellId = "gal_shell"`
        #   （ui_screens.tjs:1572）⇒ 必须写 `gal_shell`；写文件名 `39_gal_shell` 会被
        #   `★M08TAB-REJECT★ 未挂鉴赏外壳` 挡下。与 M2 的 `27_gallery.json` 同值。
        "attach": "gal_shell",
        "note": (
            "**M3 重绘（2026-09-24 · ISSUE-20260924-08）**：按参考作《交汇协奏曲》"
            "`extra.pimg`(idx75) 的 **BGM 鉴赏页 34 条**结构重做，弃用 M34 的旧方案"
            "（旧版 = 4 枚页签 + 30 件**静态**曲目行 + 7 键播放控制；静态行翻页即散，"
            "正是用户「必须标准化」所指的缺陷）。\n"
            "★ **页签 = 切屏**（主代理 2026-09-24 裁决）：本屏**不画**页签条 / 大标题 / 返回键 —— "
            "共享外壳由 M1 的浮层屏 `39_gal_shell.json` 提供，本屏 `attach` 它"
            "（与 M2 的 `27_gallery.json` 同口径）。本屏元素**一律不带页 flag**（不需要 `flags_default`）。\n"
            "★ **不铺底图**：与 `26_backlog` / `27_gallery` / `37_dress` 同口径 —— 系统屏是透明浮层，"
            "只留一层薄压暗（`mu.dim`），画面透出下层剧情背景；可读性由**行内卡体**"
            "（`x_ui_bgm_row_*`，α 235–252）承担（同 26_backlog 的 `x_ui_msgblock.png`）。\n"
            "★ **文字一律引擎绘制**（铁律：禁止把文字烘焙进图）。参考作 `Sound/曲名/オフ・オンマウス` "
            "与 `Sound/曲名/オン` 是**整张 1344×564 的曲名位图**（含 30 个曲名、白/青两态），"
            "我方**不照抄**：曲名改为逐行 `item_text` 由引擎绘制。\n"
            "★ 素材：`ui/x_ui_bgm_*.png`（**42 件新件**，`工具\\m51_make_bgm_assets.py` 程序化生成、"
            "冰蓝霜白族、真 alpha）；旧 `x_ui_music_list*.png` / `x_ui_track_*.png` / `x_ui_pb_*.png` / "
            "`x_ui_speana.png` **一件不删**（`x_ui_tab_off/on.png` 另被 23_save/24_load 共用，更不可删）。\n"
            "★ 曲目数据与收录口径见 `_工作\\ISSUE-20260924-08_鉴赏模式\\M3_BGM\\m51_bgm_report.txt`。\n"
            "★ 首版由 `_工作\\ISSUE-20260924-08_鉴赏模式\\M3_BGM\\m51_build_music.py` **一次性**产出；"
            "此后本文件手工维护（生成器 `m34_build_screens.build_music` 已退休，见 `test_gen_sync.py` 的 `NO_GEN`）。"),
        "elements": els,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("写出 %s" % OUT)
    print("  元素 %d 件（list 1 ／ image %d ／ hit %d ／ text 1 ／ rect 1 ／ slider 1）"
          % (len(els), sum(1 for e in els if e["kind"] == "image"),
             sum(1 for e in els if e["kind"] == "hit")))
    print("  曲目 %d 首 / %d 页（每页 %d 槽，网格 %d×%d）" % (n, pages, PAGE_SIZE, COLS, ROWS))
    print("  列表外框 (%d,%d) %d×%d ；卡体绝对 x = %s"
          % (LIST_X, LIST_Y, LIST_W, LIST_H,
             "/".join(str(LIST_X + c * (ITEM_W + GAP) + 34) for c in range(COLS))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
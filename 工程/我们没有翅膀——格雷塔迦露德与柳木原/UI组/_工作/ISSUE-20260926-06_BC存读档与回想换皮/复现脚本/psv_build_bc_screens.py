# -*- coding: utf-8 -*-
r"""psv_build_bc_screens.py —— B 组 PSV 换皮：23 存档 / 24 读档 / 26 通话记录 重排（**一次性脚手架**）

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮 · B 组）｜ 依据 `PSV换皮_素材与文字处置清单.md` §一 + §七。

★★ **本脚本是一次性脚手架，产物已入库；此后三屏手工维护，不要重跑本脚本** ——
   重跑会覆盖此后对这三屏的任何手工修改。生成器登记（`工具\test_gen_sync.py`）里
   23/24 的现状见该文件的 `ACK_UNSYNC["23_save.json"]` / `ACK_UNSYNC["24_load.json"]`；
   26 早已是 `NO_GEN`（`m34_build_screens.build_backlog()` 已退休），不存在「重跑即抹」。

■ 素材（拆件脚本见 `工具\psv_split_sldata.py` / `工具\psv_make_backlog_row.py`）
  · `x_ui_psv_save_bg.png` / `x_ui_psv_load_bg.png`：PSV 整屏霜面（1920×1080，1:1）。
  · `x_ui_psv_slot_norm/hover/warn.png`：槽框三态 415×122（蓝=常态 / 灰=禁用 / 暗红=覆盖警告）。
  · `x_ui_psv_slot_thumbwin.png`：缩略窗 122×73（与槽框内嵌窗同源同像素，见拆件脚本自证②）。
  · `x_ui_psv_sl_nodata.png`：空槽窗内标签 61×19。
  · `x_ui_psv_backlog_bg.png`：26 整屏底（1920×1080）；`x_ui_psv_bklog_row.png`：行板 1526×188。

■ 12 槽版式（**全部数字可复算**）
  · 槽框 415×122（= 源件 831×245 × 0.5，派单口径）；列距 = 行距 = **44**；
    左右边距 **64**（= PSV 题字左边距 64@1× × 2，见清单 §一 题字 (64,61)-(236,149)）；
    4 列 × 415 + 3 × 44 = 1792 ⇒ 边距 (1920−1792)/2 = **64** ✓ 左右对称。
  · 纵向：题字下沿 149、页码键上沿 939（两者实测，见下）⇒ 可用 790；
    3 行 × 122 + 2 × 44 = 454 ⇒ **在 149..939 内垂直居中**：y0 = (149+939)/2 − 454/2 = **317**；
    行 y = 317 / 483 / 649（下沿 771）。**为什么居中而不是铺满**：行距必须与列距一致（44），
    否则网格两轴节奏不同；铺满（行距 212）会让横竖留白失衡。
  · 列 x = 64 / 523 / 982 / 1441（右沿 1856，右边距 64 ✓）。
  · 行优先编号：槽 1–4 = 第 1 行、5–8 = 第 2 行、9–12 = 第 3 行。
  · 槽内：缩略窗在件内 (33,25)（= 源 (70,54) − 槽框源原点 (4,4)，再 ÷2）；文字区在件内 x+170..x+402
    （宽 232、右边距 13）：槽号 y+10 高 30（字号 22）、信息 y+44 高 75（字号 18、行距 1.4 → 行高 25、
    最多 3 行 = 75，恰为上限）。
  · ⚠️ 无「第 N 号 / 日期」文字烘焙进图：一律**引擎绘制**（本工程铁律）⇒ 槽号/信息仍是 `text`。

■ 槽三态怎么接（**新机制？不，是既有屏级 flag 机制**）
  用户裁决的三态（蓝=常态／灰=禁用（空槽等）／暗红=覆盖警告）在数据层的落点 = **12 个屏级 flag**
  `sv_s1..sv_s12`（`flags_default` 全 `"on"`）+ 每槽三件槽框图各带 `vis_flag:"sv_sN"` +
  `vis_when:"on"|"off"|"warn"`（取值严格相等 ⇒ 同一时刻只显一件，与 21 确认框选板同款）。
  · 默认 `"on"`（蓝）：PSV 观感不变；`"off"`（灰）额外显 `sv.nodataN`（窗内 `NO DATA`）。
  · **谁来写**：存档数据在编程组手里（本作尚无存档系统）⇒ 本轮只**冻结接口**：进屏后
    `uiScreenFlagSet("sv_sN", "on"|"off"|"warn")`（屏栈 reset 会按 `flags_default` 重置 ⇒ 必须在进屏后写）。
  · 靠 flag 控显隐的元素一律 `visible_default:true`（`_schema.md` §四铁律）。

■ 保持不动的部分（**本轮明确不碰，见报告「未决点」**）
  · 页脚条 y988..1032（PSV 烘焙中文页脚）为**待定区**（用户双路对比裁决中）⇒ `sv.edit` /
    `sv.del/mod/mov/cpy`（+ `_tx`）与 `sv.hit_back` **一个数与一个字节都没动**。
  · 页码键 `sv.pg01..10`（+ `_tx` / `_hit`）：**保留现有页码件**（派单允许二选一），仅整体左移 56px
    （x120→64，与槽网格左沿对齐 ⇒ 满足「几何对齐」）；0.5 倍率下 PSV 数字件只有 18–27px 高，
    塞进 53×53 页码键要么再放大（破坏统一倍率）要么留大片空框，故不采用。
  · 其余 `sv.sys_*`（3 组）、`sv.help`(+`_tx`) 几何不动。
  · 顶部页签 `sv.tab_a`/`sv.tab_b`（+`_tx`/`_hit`）**整体 x + 315**（25→340、211→526）：
    原位置 25..392 会压在 PSV 题字 SAVE/LOAD（实测 (64,61)-(236,149)）上 —— 题字按用户裁决保留原样，
    故让位的是页签；新位置在题字右侧、系统按钮左侧，互不重叠。
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
SCR = os.path.join(UI, "layout", "screens")

# ── 12 槽版式（全部由本文件头注的算式推出）────────────────────────────────
COLS_X = [64, 523, 982, 1441]
ROWS_Y = [317, 483, 649]
SLOT_W, SLOT_H = 415, 122
WIN_REL = (33, 25, 122, 73)          # 缩略窗（件内相对槽框左上）
NODATA_W, NODATA_H = 61, 19
NUM_REL = (170, 10, 232, 30)         # 槽号（件内）
INFO_REL = (170, 44, 232, 75)        # 信息（件内）
NUM_FONT = {"size": 22, "bold": True, "color": "@palette.node_locked",
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
INFO_FONT = {"size": 18, "bold": True, "color": "@palette.node_locked",
             "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
PAGE_DX = -56                        # 页码键整体左移（x120 → 64，对齐槽网格左沿）
TAB_DX = 315                         # 页签让位（25→340 / 211→526）

# ── 26 通话记录版式 ─────────────────────────────────────────────────────
BL_BOARD = (157, 146, 1604, 788)     # PSV 内容板（画布口径；源 (157,150)-(1761,938) 再减 4px 上偏）
BL_PAD = 12                          # 板内缩
BL_GAP = 4                           # 行间距
BL_ROWS = 4
BL_ITEM_H = 188                      # 4×188 + 3×4 = 764 = 788 − 2×12 ✓
BL_LIST_X = BL_BOARD[0] + BL_PAD     # 169
BL_LIST_Y = BL_BOARD[1] + BL_PAD     # 158
BL_LIST_W = 1526                     # 右沿 1695（滚动条槽 1712 之前留 17px）
ROW_ASSET = "ui/x_ui_psv_bklog_row.png"
ROW_OPACITY = 150        # 行带不透明度（实测：与板同调的带只能做极轻明度差；见 note 中实测 Δ）
SCROLL_CX = (1712 + 1734) / 2.0      # 滚动条槽中心 1723
TRACK_TOP, TRACK_BOT = 227, 876      # 槽纵向（源 231..880 减 4px 上偏）


def img(eid, z, asset, x, y, w, h, note, **kw):
    d = {"id": eid, "kind": "image", "z": z, "visible_default": True, "asset": asset,
         "x": x, "y": y, "w": w, "h": h, "opacity": 255, "note": note}
    d.update(kw)
    return d


def slot_rect(i):
    """槽 i（1..12）→ (x, y)，行优先。"""
    return COLS_X[(i - 1) % 4], ROWS_Y[(i - 1) // 4]


BG_NOTE = ("PSV 整屏霜面底图（1920×1080，1:1、无 nine）：%s。英文题字 SAVE/LOAD 在图内烘焙 —— "
           "用户裁决「英文题字保留原样」（`PSV换皮_素材与文字处置清单.md` §七）。"
           "z=2（在 `sv.dim` 之上、槽面板之下）；本件不透明满屏 ⇒ `sv.dim` 实机不可见（保留不删，"
           "零风险且不影响既有点击可达豁免表）。页脚条 y988..1032 为待定区 ⇒ 本轮不动该条带。")

DIM_NOTE = ("全屏压暗遮罩。**PSV 换皮后位于 `sv.bg`（z=2，不透明满屏）之下 ⇒ 实机不可见**；"
            "保留而非删除的理由：不动既有元素与豁免表（save/load 的 `sv.hit_back` 豁免条目）零风险，"
            "移除动作留给主代理一并处理。")

TAB_NOTE = ("页签名（引擎绘制）。**PSV 换皮：整体 x + %d**（原 25/211 → 340/526）——"
            "原位置会压在 PSV 题字 SAVE/LOAD（实测 (64,61)-(236,149)，用户裁决保留题字不改）上；"
            "新位置在题字右侧、`sv.sys_*` 按钮左侧，互不重叠。action 一律未改（`open_save`/`open_load`）。"
            % TAB_DX)


SLOT_FRAME_NOTE = (
    "槽位 %d 槽框·%s（PSV 件 415×122 = 源 831×245 × 0.5；拆件见 `工具\\psv_split_sldata.py`）。"
    "三态由**屏级 flag `%s`** 选件（`vis_when` 取值严格相等 ⇒ 同一时刻只显一件，与 21 确认框选板同款机制）："
    "`on`=常态蓝 / `off`=禁用灰 / `warn`=覆盖警告暗红。默认 `on`（屏级 `flags_default`）；"
    "存档数据接入后由调用方在**进屏之后** `uiScreenFlagSet(\"%s\", \"on\"|\"off\"|\"warn\")`"
    "（屏栈 reset 会按 `flags_default` 重置）。**为什么三态各一件而不是一件换图**：元素级 `state_assets` "
    "只有 normal/hover/pressed（悬停/按下语义），表达不了「空槽 / 覆盖警告」；而 `vis_flag` 一对只能带一个值 "
    "⇒ 三态必须各占一件。靠 flag 控显隐的元素 `visible_default` 一律 true（`_schema.md` §四铁律）。")


def guard_m34_shape(fn, old):
    """一次性脚手架的**单向保护**：已是换皮后形态就拒绝重跑（否则会把新件再展开一遍 ⇒ id 重复）。

    本脚本按「M34 旧形 → PSV 形」的单向映射工作（12 件槽框 → 36 件三态、加底图等），
    对自身的产出**不幂等**。要重做请先 `git checkout` 该文件回旧形再跑。
    """
    ids = [e.get("id") for e in old["elements"]]
    if ("sv.bg" in ids) or ("bl.bg" in ids):
        raise SystemExit("!! %s 已是 PSV 换皮后的形态（含 sv.bg/bl.bg）——本脚本是一次性脚手架、"
                         "对自身产出不幂等。要重做请先 `git checkout -- layout/screens/%s` 回 M34 旧形。" % (fn, fn))
    if any(i and (i.endswith("_off") or i.endswith("_warn") or i.startswith("sv.nodata")) for i in ids):
        raise SystemExit("!! %s 含换皮新增 id（*_off/*_warn/sv.nodata*）⇒ 已改造过，拒绝重跑" % fn)


def build_saveload(mode):
    """mode: "save" | "load" → (文件名, 新屏对象)。"""
    fn = "23_save.json" if mode == "save" else "24_load.json"
    old = json.load(io.open(os.path.join(SCR, fn), encoding="utf-8"))
    guard_m34_shape(fn, old)
    bg_asset = "ui/x_ui_psv_%s_bg.png" % ("save" if mode == "save" else "load")
    els = [img("sv.bg", 2, bg_asset, 0, 0, 1920, 1080, BG_NOTE % bg_asset,
               source="PSV系统UI参考\\AI中文化\\2x\\otv_%s_bg_cn.png（1920×1088 PSV 屏区版，"
                      "上下各去 4px → 1920×1080；入库件 krkr\\assets\\ui\\x_ui_psv_%s_bg.png，"
                      "由 工具\\m53_psv_ui_assets.py 入库）"
                      % ("save" if mode == "save" else "load", "save" if mode == "save" else "load"))]
    flags = {}
    for n in range(1, 13):
        flags["sv_s%d" % n] = "on"

    for e in old["elements"]:
        eid = e.get("id", "")
        if eid == "sv.dim":
            e = dict(e)
            e["note"] = DIM_NOTE
            els.append(e)
            continue
        if eid.startswith("sv.tab_"):
            e = dict(e)
            e["x"] = e["x"] + TAB_DX
            e["note"] = (("页签文字（引擎绘制）。" if eid.endswith("_tx") else "") + TAB_NOTE)
            els.append(e)
            continue
        if eid.startswith("sv.pg"):
            e = dict(e)
            e["x"] = e["x"] + PAGE_DX
            if eid.endswith("_tx"):
                e["note"] = ("页码文字（引擎绘制）。**PSV 换皮：与页码键一同左移 %dpx**（120→64），"
                             "使页码行与 12 槽网格左沿对齐（派单「几何对齐」）；"
                             "页码件与几何尺寸保持原状（派单允许「保留现有页码件」）。" % (-PAGE_DX))
            elif eid.endswith("_hit"):
                e["note"] = ("页码热区。PSV 换皮：随键左移 %dpx；`action` 未改（`page_N`），"
                             "与键、文字三层几何一致、可点。" % (-PAGE_DX))
            else:
                e["note"] = ("页码键底（保留现有件，派单允许二选一）。PSV 换皮：与文字/热区一同左移 %dpx。"
                             "**为什么不用 PSV 数字件**：拆件倍率为整图统一 0.5 ⇒ 数字件只有 18–27px 高，"
                             "塞进 53×53 键要么再放大（破坏统一倍率）要么留大片空框；且「10」需两枚字形拼接、"
                             "页号属文字（铁律：引擎绘制）。" % (-PAGE_DX))
            els.append(e)
            continue

        m = re.match(r"sv\.(slot|thumb|num|info|hit)(\d+)$", eid)
        if not m:
            els.append(e)
            continue
        kind, n = m.group(1), int(m.group(2))
        x, y = slot_rect(n)
        f = "sv_s%d" % n
        if kind == "slot":
            for suf, asset, when, zh in (
                    ("", "ui/x_ui_psv_slot_norm.png", "on", "常态（蓝 #7070A8）"),
                    ("_off", "ui/x_ui_psv_slot_hover.png", "off", "禁用（灰 #484050）——空槽等"),
                    ("_warn", "ui/x_ui_psv_slot_warn.png", "warn", "覆盖警告（暗红 #782040）")):
                els.append(img("sv.slot%d%s" % (n, suf), 20, asset, x, y, SLOT_W, SLOT_H,
                               SLOT_FRAME_NOTE % (n, zh, f, f),
                               vis_flag=f, vis_when=when,
                               source="PSV系统UI参考\\超分2x\\otv_sl_data.png（槽框雪碧图，三态）"))
        elif kind == "thumb":
            wx, wy, ww, wh = WIN_REL
            els.append(img("sv.thumb%d" % n, 21, "ui/x_ui_psv_slot_thumbwin.png",
                           x + wx, y + wy, ww, wh,
                           "槽位 %d 缩略窗（PSV 件 122×73）。**与槽框内嵌窗同源同像素**"
                           "（拆件脚本自证②：本件逐字节等于 `slot_norm` 的窗位 (33,25)-(155,98)）"
                           "⇒ 叠画零变化；保留本元素的用途 = 给缩略图提供**定位与绘制槽位**"
                           "（编程组接 `dynamic:slot_thumb` 时用它的矩形），与本工程既有 `sv.thumb*` 角色一致。"
                           % n, source="PSV系统UI参考\\超分2x\\otv_sl_data.png（缩略窗）"))
            els.append(img("sv.nodata%d" % n, 23, "ui/x_ui_psv_sl_nodata.png",
                           x + wx + (ww - NODATA_W) // 2, y + wy + (wh - NODATA_H) // 2,
                           NODATA_W, NODATA_H,
                           "槽位 %d 空槽标签 `NO DATA`（PSV 件 61×19，窗内居中）。"
                           "**仅当该槽为 `off`（空槽/禁用）时显示**：`vis_flag:%s` + `vis_when:\"off\"`。" % (n, f),
                           vis_flag=f, vis_when="off",
                           source="PSV系统UI参考\\超分2x\\otv_sl_data.png（NO DATA）"))
        elif kind == "num":
            nx, ny, nw, nh = NUM_REL
            e = dict(e)
            e.update(x=x + nx, y=y + ny, w=nw, h=nh, font=dict(NUM_FONT))
            e["note"] = ("槽位号「第 %d 号」（引擎绘制，字号 22）。PSV 换皮：随槽位重排到槽框文字区上段"
                         "（件内 x+170 y+10 232×30）。" % n)
            els.append(e)
        elif kind == "info":
            ix, iy, iw, ih = INFO_REL
            e = dict(e)
            e.update(x=x + ix, y=y + iy, w=iw, h=ih, font=dict(INFO_FONT))
            e["note"] = ("槽位信息（日期 + 章节；引擎绘制，字号 18、行距 1.4 ⇒ 行高 25、最多 3 行 = 75 = 框高）。"
                         "PSV 换皮：重排到槽框文字区下段（件内 x+170 y+44 232×75）。框宽 232 比旧 217 略宽，"
                         "同字号下所需行数只减不增 ⇒ 容量不降。")
            els.append(e)
        elif kind == "hit":
            e = dict(e)
            e.update(x=x, y=y, w=SLOT_W, h=SLOT_H)
            e["note"] = ("槽位 %d 热区（`action=slot_%d`，未改）。PSV 换皮：随槽框重排为 415×122，"
                         "与槽框/缩略窗/文字同矩形域；z=95 高于槽面板 ⇒ 悬停面与点击面一致。" % (n, n))
            els.append(e)

    note = ("**PSV 换皮（2026-09-26，ISSUE-20260926-06 · B 组）· %s**。用户裁决见 "
            "`PSV换皮_素材与文字处置清单.md` §七。\n"
            "★ **底图**：`%s`（PSV 整屏霜面 1920×1080，1:1）——英文题字 %s **保持原样**（用户裁决）。\n"
            "★ **12 槽重排为 4 列 × 3 行**：槽框 415×122（= PSV 源件 831×245 × 0.5）；"
            "列距 = 行距 = 44；左右边距 64（= PSV 题字左边距）；纵向在题字下沿 149 与页码键上沿 939 之间"
            "**居中**（y0 = (149+939)/2 − 454/2 = 317）⇒ 行 y = 317/483/649、列 x = 64/523/982/1441。\n"
            "★ **槽三态**（用户裁决：蓝=常态／灰=禁用（空槽等）／暗红=覆盖警告）："
            "由 12 个屏级 flag `sv_s1..sv_s12`（`flags_default` 全 `\"on\"`）选件，每槽三件槽框各带 "
            "`vis_when:on|off|warn`；空槽额外显示 `sv.nodataN`（窗内 `NO DATA`）。"
            "**接口冻结**：编程组进屏后 `uiScreenFlagSet(\"sv_sN\", \"on\"|\"off\"|\"warn\")`"
            "（屏栈 reset 按 `flags_default` 重置 ⇒ 必须进屏后写）。\n"
            "★ **44 个 text 全部保留引擎绘制**（槽号/信息/页码/页签/编辑键/系统键/说明），"
            "其中 24 个（`sv.num*`/`sv.info*`）随新槽几何重排；**文字一个都没有烘焙进图**。\n"
            "★ **action 全部未改**：`slot_1..12`、`page_1..10`、`open_save`/`open_load`、`close` 原样。\n"
            "★ **不动的部分**：页脚条 y988..1032（PSV 烘焙中文页脚）为**待定区**（用户双路对比中）⇒ "
            "`sv.edit`/`sv.del|mod|mov|cpy`(+`_tx`)/`sv.hit_back` 未动；页码键保留现有件、仅整体左移 56px "
            "与槽网格左沿对齐；`sv.sys_*` 与 `sv.help` 几何未动。\n"
            "★ 退场登记：`工具\\test_gen_sync.py` 的 `ACK_UNSYNC[\"%s\"]`（生成器 "
            "`m34_build_screens.build_saveload_%s()` 仍在 `__main__` 接线里 ⇒ **重跑会把本屏改回旧形"
            "（并抹掉 flags_default / 全部 vis_flag）**，不得重跑）。"
            % ("存档" if mode == "save" else "读档", bg_asset, "SAVE" if mode == "save" else "LOAD",
               fn, mode))

    out = {"id": old["id"], "title_cn": old["title_cn"], "owner": "M34 / PSV-B组",
           "flags_default": flags, "note": note, "elements": els}
    return fn, out


def build_backlog():
    fn = "26_backlog.json"
    old = json.load(io.open(os.path.join(SCR, fn), encoding="utf-8"))
    guard_m34_shape(fn, old)
    els = [img("bl.bg", 2, "ui/x_ui_psv_backlog_bg.png", 0, 0, 1920, 1080,
               "PSV 通话记录整屏底图（1920×1080：题字 BACKLOG + 高光内容板 + 右缘滚动条槽；1:1）。"
               "用户裁决「英文题字 BACKLOG 保留原样」。z=2（`bl.dim` z=1 之上、列表之下）"
               "⇒ `bl.dim` 实机不可见（保留不删）。页脚 y988..1032 的日语两项为**待定区**（用户双路对比中），"
               "本轮不动该条带。",
               source="PSV系统UI参考\\超分2x\\otv_bklog.png（按屏区 y0..1088 裁 1920×1080）")]
    BOARD_X, BOARD_Y, BOARD_W, BOARD_H = BL_BOARD
    for e in old["elements"]:
        eid = e.get("id", "")
        if eid == "bl.dim":
            e = dict(e)
            e["note"] = DIM_NOTE.replace("sv.bg", "bl.bg")
            els.append(e)
            continue
        if eid == "bl.list":
            e = json.loads(json.dumps(e, ensure_ascii=False))
            e["x"], e["y"], e["w"] = BL_LIST_X, BL_LIST_Y, BL_LIST_W
            e["item_h"], e["gap"], e["max_rows"] = BL_ITEM_H, BL_GAP, BL_ROWS
            e["item_frame"] = {"asset": ROW_ASSET, "opacity": ROW_OPACITY}
            e["item_text"] = {"x": 219, "y": 10, "w": 1291, "h": 168, "wrap": True,
                              "max_lines": 4, "align": "left", "valign": "top"}
            e["note"] = ("回想消息块列表。**PSV 换皮（2026-09-26，ISSUE-20260926-06 · B 组）**：\n"
                         "★ **版式按 PSV 内容板重排**（板实测 x157..1761 × y146..934，画布口径 1604×788）："
                         "板内缩 12 ⇒ 列表 x=169 y=158，宽 1526（右沿 1695，止于滚动条槽 1712 之前 17px）；"
                         "4 行 `item_h=188`、`gap=4` ⇒ 4×188+3×4 = 764 = 788−2×12 **恰好填满板内可用高度**。\n"
                         "★ **`item_frame` 换 PSV 自家像素**：`ui/x_ui_psv_bklog_row.png`（1526×188，1:1 无 nine）"
                         "= 从**同一张底图**的板内取的一条 1526×188 行板（取件框 (169,450)、"
                         "带内平均亮度 213.7 = 板内 4 行区平均 ⇒ 最「平」的带，不含雪晶），"
                         "以 `opacity=150` 半透明叠在板上（**上下各 32px α 余弦羽化，见取件脚本 docstring**）⇒ 只做**行带明度差**，不引入第二个面板："
                         "PSV 的通话记录屏**没有逐行底板**（板是整块、无行分隔），"
                         "「每行一块板」只能这样解决；取同图同倍率像素可保证与板同色同纹。"
                         "取件脚本 `工具\\psv_make_backlog_row.py`（幂等、判据可复算）。\n"
                         "★ **文本区** `item_text`：块内 (219,10) 1291×168，字号 30 / 行距 1.4 ⇒ 行高 42 / 最多 4 行"
                         "（= 168）。框宽 1117→**1291 更宽** ⇒ 同字号下所需行数只减不增 ⇒ 旧「4 行 0 截断」"
                         "实测结论**仍然成立且更宽松**（M06 容量实测见其 note）。\n"
                         "★ **逐块按钮**（跳转 94×29 @(28,26) / 重新播放 44×44 @(154,18)）几何未改："
                         "两块都在新块高 188 内、且在 4 行文本区左侧栏内。\n"
                         "★ **旧件 `x_ui_msgblock.png` 不再被引用**（按工程惯例**保留不删**）。")
            els.append(e)
            continue
        if eid == "bl.close":
            e = dict(e)
            e["note"] = (e.get("note", "") + " ★ PSV 换皮：**几何未动**（在板上方、题字带右端，无 PSV 对应件；"
                         "板内不许放关闭键，底图该处是雪晶装饰带）。").strip()
            els.append(e)
            continue
        if eid in ("bl.up", "bl.down", "bl.slider"):
            cx = round(SCROLL_CX - e["w"] / 2.0)
            if eid == "bl.up":
                e["y"] = TRACK_TOP
            elif eid == "bl.down":
                e["y"] = TRACK_BOT - e["h"]
            else:
                e["y"] = TRACK_TOP + (TRACK_BOT - TRACK_TOP - e["h"]) // 2
            e["x"] = cx
            e["source"] = e.get("source", "")
            e["note"] = (e.get("note", "") + " ★ PSV 换皮：**x 对齐 PSV 滚动条槽**（槽实测 x1712..1734，中心 1723；"
                         "y 对齐槽纵向 227..876：上箭头贴顶、下箭头贴底、滑块居中）。"
                         "我方件宽 31 vs 槽宽 22 ⇒ 左右各溢出约 4.5px，仍在槽内居中。").strip()
            els.append(e)
            continue
        if eid in ("bl.up_hit", "bl.slider_hit", "bl.down_hit"):
            src = {"bl.up_hit": "bl.up", "bl.slider_hit": "bl.slider", "bl.down_hit": "bl.down"}[eid]
            tgt = [x for x in els if x.get("id") == src][0]
            e = dict(e)
            e["x"], e["y"], e["w"], e["h"] = 1696, tgt["y"] - 6, 76, tgt["h"] + 12
            e["note"] = (e.get("note", "") + " ★ PSV 换皮：随件重排（x=1696、宽 76 —— **左沿 1696 > 列表右沿 1695**，"
                         "刻意不压列表矩形，避免新增点击可达性重叠；右沿 1772 略出板缘 1761，属不可见热区）。").strip()
            els.append(e)
            continue
        if eid == "bl.close_hit":
            els.append(e)
            continue
        els.append(e)

    note = ("**PSV 换皮（2026-09-26，ISSUE-20260926-06 · B 组）· 26 通话记录**。用户裁决见 "
            "`PSV换皮_素材与文字处置清单.md` §七。\n"
            "★ 底图换 `ui/x_ui_psv_backlog_bg.png`（PSV 整屏：题字 BACKLOG + 高光内容板 1604×788 + "
            "右缘滚动条槽；1:1；题字按用户裁决保留原样）。\n"
            "★ `bl.list` 按**板内可用高度**重排：x169 y158 w1526、4 行 × `item_h188` + `gap4` = 764 "
            "（= 板高 788 − 上下各 12 内缩）；`item_text` 1291×168（更宽 ⇒ 所需行数只减不增）。\n"
            "★ `item_frame` = `ui/x_ui_psv_bklog_row.png`（从底图板内取的 1526×188 行板，1:1、"
            "`opacity=110`）—— PSV 板无逐行底板，「每行一块」以同图同倍率像素半透明叠加解决。\n"
            "★ `bl.close` 几何未动；`bl.up/slider/down` x 对齐滚动条槽中心 1723、y 对齐槽纵向 227..876；"
            "4 个 hit 随件重排（左沿 1696 不压列表矩形）。\n"
            "★ 页脚日语两项（y988..1032）为**待定区**（用户双路对比中），本轮不动该条带。\n"
            "★ 本屏无 `item_buttons` 之外的机制改动；`backlog_jump:%row%` / `backlog_replay:%row%` 原样。")
    out = {"id": old["id"], "title_cn": old["title_cn"], "owner": "M34 / PSV-B组",
           "note": note, "elements": els}
    return fn, out


def main():
    applied = []
    for mode in ("save", "load"):
        fn, out = build_saveload(mode)
        applied.append((fn, out))
    fn, out = build_backlog()
    applied.append((fn, out))

    for fn, out in applied:
        p = os.path.join(SCR, fn)
        with io.open(p, "w", encoding="utf-8", newline="\r\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("  写出 %-18s 元素 %3d 件%s" % (fn, len(out["elements"]),
                                          "（flags_default %d 键）" % len(out["flags_default"])
                                          if "flags_default" in out else ""))
    print("[OK] 三屏已写出")
    return 0


if __name__ == "__main__":
    sys.exit(main())

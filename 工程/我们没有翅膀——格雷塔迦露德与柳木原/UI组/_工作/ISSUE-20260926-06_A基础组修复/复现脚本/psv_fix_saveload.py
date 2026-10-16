# -*- coding: utf-8 -*-
r"""psv_fix_saveload.py —— 23 存档 / 24 读档 修复轮数据侧（页码徽章数字 + 页签选中态）

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）· **A 基础组修复轮**（本轮派单缺陷 ④）。
素材侧配套（**先跑它们再跑本脚本**）：
  · `工具\psv_fix_save_badge.py` —— 抹掉底图里烘焙的「/10」（23/24 两张 PSV 霜页底图）
  · `工具\psv_fix_tab_state.py`  —— 派生选中态页签件 `x_ui_psv_tab_sel.png`

■ 缺陷 ④-1【中】右上页码徽章只显示「/10」（底图烘焙缺前导数字；屏内无该数字元素 ⇒ 永久残缺）
  修法（两步）：
   ① **底图补底**（已由 `psv_fix_save_badge.py` 完成）：抹掉烘焙「/10」，还出干净霜面；
   ② **引擎绘「N / 10」**（本脚本）：新增屏级字段 **`page_flag: "sv_page"`** ＋ `flags_default.sv_page = "1"`
      ＋ **10 件互斥文本** `sv.pgnum_01..10`（`vis_flag:"sv_page"` / `vis_when:"1".."10"`，样文 `1 / 10`..`10 / 10`）。
  几何：徽章牌 x≈1643..1920 / y≈56..150；烘焙「/10」实测 x1765..1842 / y82..134（右缘 1843）
   ⇒ 文本 `x1663 y68 w180 h80`、`align:"right"`（**字符串右缘 = 1843**，与烘焙件同位）＋ 整框纵向中心 = 108
   （= 烘焙字形纵向中心）⇒「1 / 10」与「10 / 10」右缘对齐、数字向左生长，与 PSV 原设计同向。
  字号 `66`：由烘焙字形**数字高 ≈48px** ÷ 本作字体「数字高/字号 ≈0.73」反推（≈66）。
  字体：白字 `@palette.text_primary` ＋ 2px 描边 `#3E63B8`（沿用同屏 `22_loading` 的
  `ld.text` 既有口径：PSV 冰蓝描边；直写色值属该口径要求，非配色自由发挥）。
  ★ **语义与「勿冲突」**：`sv_page` 与底部页码键 `sv.pg01..10`（`action: page_1..10`）**同语义**——
     都是「当前页号（1 基，共 10 页）」。底部键负责**翻页**，`sv_page` 负责**把当前页号喂给徽章**，
     二者取值域一致（"1".."10"）⇒ 不会互相覆盖。
  ⚠️ **未决点（本脚本写不进、须编程组）**：krkr 侧只有 `gallery_page_prev/next`（鉴赏外壳那条路径）
     会写 `page_flag`（`ui_screens.tjs: uiScreenPageFlagOf` + `uiScreenFlagSet`），而 **`page_1..10` 在
     `krkr\game\*.tjs` 里没有处理器**（整个存读档翻页在演示运行期未实现）。本轮**受禁改 tjs 约束**，
     只做数据侧声明 ⇒ 徽章默认显示 `flags_default` 的「1 / 10」；要让它在翻页后跟随，需编程组按
     既有机理补一行 `uiScreenFlagSet("sv_page", ""+页号)`（数据侧已就绪，勿再改本屏）。

■ 缺陷 ④-轻【轻】页签选中态过弱（选中/未选中带体仅差 ≤3/255）
  修法（**不动机制**：不加 flag、不改 action/几何/文字/热区，只换「选中态」图）：
  · 23 存档：`sv.tab_a`（存档）→ `ui/x_ui_psv_tab_sel.png`（新派生件），`sv.tab_b` 保持 `x_ui_tab_off.png`；
  · 24 读档：`sv.tab_a` → `x_ui_tab_off.png`、`sv.tab_b`（读档）→ `ui/x_ui_psv_tab_sel.png`。
    ★ **原状是两屏都 `tab_a = x_ui_tab_on.png`** ⇒ 读档屏高亮的是**存档**页签（同一缺陷的语义面）——
      本轮一并订正：**当前页签才用选中件**。对比度实测：带体内逐像素差 中位 4 → **94**（`psv_fix_tab_state.py` 输出）。
  · 共享件 `x_ui_tab_on/off.png` **未改**（`28_music.json` 也在用 ⇒ 改它会动别的屏）。

**幂等**：读盘 → 按固定值改 → 写回（重复运行逐字节相同）。
用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_A基础组修复\复现脚本\psv_fix_saveload.py [--check]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCR = os.path.join(UI, "layout", "screens")

PAGES = 10                                   # 总页数（底部 `sv.pg01..10`）⇒ 徽章「N / 10」
PAGE_FLAG = "sv_page"                        # ★ 屏级 `page_flag` 名（与 `page_1..10` 同语义）
# 徽章数字文本几何（屏坐标）：右缘 1843 = 烘焙「/10」右缘；纵向中心 108 = 烘焙字形中心
NUM_BOX = (1663, 68, 180, 80)
NUM_FONT = {"size": 66, "bold": True, "color": "@palette.text_primary",
            "outline": True, "outline_color": "#3E63B8", "outline_width": 2,
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}
TAB_SEL = "ui/x_ui_psv_tab_sel.png"
TAB_OFF = "ui/x_ui_tab_off.png"
TAB_SRC_PSV = ("PSV系统UI参考\\AI中文化\\2x（PSV 霜页体系）｜选中态件由 工具\\psv_fix_tab_state.py "
               "确定性重着色派生：RGB' = (R×0.55, G×0.68, B×0.92)（6bit）/ alpha 逐像素原样")

TAB_NOTE_SEL = (
    "页签底（**当前页签**）。★ 修复轮（ISSUE-20260926-06_A基础组修复 · 缺陷 ④-轻）："
    "原选中/未选中带体仅差 ≤3/255（实测逐像素中位 4）⇒ 选中态改用派生件 "
    "`ui/x_ui_psv_tab_sel.png`（由 `x_ui_tab_on.png` 确定性重着色：RGB×(0.55/0.68/0.92)、alpha 原样；"
    "实测带体内两态差 中位 4 → 94）。**机制未动**（无 flag、无 action/几何/文字/热区变更）；"
    "共享件 `x_ui_tab_on/off.png` 未改（28_music 也在用）。")
TAB_NOTE_OFF = (
    "页签底（**非当前页签**）。★ 修复轮：本屏的当前页签改用派生件 `ui/x_ui_psv_tab_sel.png`，"
    "本件仅用于**非当前**页签；共享件 `x_ui_tab_on/off.png` 未改（28_music 也在用）。")

FIX_NOTE = """★ **修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复，vision 判不达标后重做）**：
  · **④-1【中】右上页码徽章「/10」残缺 → 已修**：底图烘焙的「/10」由 `工具\\psv_fix_save_badge.py`
    **程序化抹除**（补底矩形 x1763..1845 / y80..140，上下锚行线性补底 + 下沿 4 行混合带 ⇒ 与上下霜面
    逐点连续，实测上沿 4.3 / 下沿 1.0 / 线性段 1.3 / 字形核心残差 ≤1.7，全部 ≤ 阈值）；屏内**新增引擎绘
    「N / 10」**：屏级 `page_flag:"sv_page"` + `flags_default.sv_page:"1"` + 10 件互斥文本
    `sv.pgnum_01..10`（`vis_when:"1".."10"`，右缘 1843 = 烘焙件右缘、字号 66 ≈ 烘焙数字高 48px）。
    ⚠️ **未决点**：`page_1..10` 在 `krkr\\game\\*.tjs` 无处理器（演示运行期未实现存读档翻页），
    受禁改 tjs 约束本轮只做数据侧声明 ⇒ 徽章显示 `flags_default` 的「1 / 10」；驱动方须编程组按
    既有机理补 `uiScreenFlagSet("sv_page", ""+页号)`（数据侧已就绪）。
  · **④-轻【轻】页签选中态过弱 → 已修**：选中态改件 `ui/x_ui_psv_tab_sel.png`（重着色派生，实测带体内
    两态差 中位 4 → 94）；**并把「当前页签」订正到本屏对应的页签**（原状两屏都高亮存档页签：
    读档屏高亮错误 —— 属同一缺陷的语义面）。机制未动、共享件未改。
"""

SCREENS = {"23_save.json": "a", "24_load.json": "b"}     # 屏 → 本屏「当前页签」的元素后缀


def fix(fn, cur, dry):
    p = os.path.join(SCR, fn)
    d = json.load(io.open(p, encoding="utf-8"))
    els = d["elements"]
    sel_suffix = cur                                  # "a" = 本屏当前页签是 sv.tab_a

    # ── ④-1：屏级 page_flag + flags_default ──
    d["flags_default"][PAGE_FLAG] = "1"
    d["page_flag"] = PAGE_FLAG
    # 10 件互斥页码文本（屏级 flag 驱动；右缘 1843 对齐烘焙件）
    x, y, w, h = NUM_BOX
    existing = {e["id"] for e in els}
    new = []
    for i in range(1, PAGES + 1):
        eid = "sv.pgnum_%02d" % i
        if eid in existing:
            continue
        new.append({
            "id": eid, "kind": "text", "z": 30, "visible_default": True,
            "x": x, "y": y, "w": w, "h": h,
            "text": "%d / %d" % (i, PAGES), "align": "right", "valign": "middle",
            "wrap": False, "max_lines": 1, "font": dict(NUM_FONT),
            "sample": "%d / %d" % (i, PAGES),
            "vis_flag": PAGE_FLAG, "vis_when": str(i),
            "note": ("页码徽章数字（引擎绘制）第 %d / %d 页。★ 修复轮（缺陷 ④-1）：底图烘焙的「/10」已由 "
                     "工具\\psv_fix_save_badge.py 抹除，本件以 `align:right` 让字符串**右缘恒在 x1843**"
                     "（= 原烘焙「/10」右缘）⇒ 数字向左生长，与 PSV 版式同向；字号 66 ≈ 烘焙数字高 48px。"
                     "`vis_flag` = 屏级 `page_flag`（%s）——与底部 `sv.pg01..10` 的 `page_1..10` **同语义**："
                     "1 基页号／共 %d 页；底部键翻页、本件只显示当前页号。" % (i, PAGES, PAGE_FLAG, PAGES)),
        })
    if new:
        els.extend(new)

    # ── ④-轻：当前页签用选中件，另一页签用未选中件 ──
    for e in els:
        if e["id"] == "sv.tab_%s" % sel_suffix:
            e["asset"] = TAB_SEL
            e["source"] = TAB_SRC_PSV
            e["note"] = TAB_NOTE_SEL
        elif e["id"] == "sv.tab_%s" % ("b" if sel_suffix == "a" else "a"):
            e["asset"] = TAB_OFF
            e["source"] = TAB_SRC_PSV
            e["note"] = TAB_NOTE_OFF

    if "修复轮（2026-09-26 · ISSUE-20260926-06_A基础组修复" not in d["note"]:
        d["note"] = d["note"].rstrip() + "\n" + FIX_NOTE
    d["note"] = d["note"].replace(
        "★ **action 全部未改**",
        "★ **修复轮追加**：本屏新增屏级 `page_flag:\"sv_page\"` 与 10 件徽章页码文本 `sv.pgnum_01..10`、"
        "当前页签换件 `ui/x_ui_psv_tab_sel.png`（详见文末「修复轮」段）；`sv.tab_*` 的 `action` 仍未改。\n"
        "★ **action 全部未改**")

    if dry:
        return "%s（dry）：将新增 %d 件页码文本、page_flag=%s、当前页签=%s" % (
            fn, len(new), PAGE_FLAG, "sv.tab_" + sel_suffix)
    with io.open(p, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return "%s：元素 %d 件（新增页码文本 %d 件）｜page_flag=%s ｜当前页签 sv.tab_%s" % (
        fn, len(els), len(new), PAGE_FLAG, sel_suffix)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报将改什么，不落盘")
    a = ap.parse_args()
    print("=" * 92)
    print("23/24 修复轮：页码徽章引擎数字 + 页签选中态%s" % ("（--check 不落盘）" if a.check else ""))
    print("=" * 92)
    for fn, cur in SCREENS.items():
        print("  " + fix(fn, cur, a.check))
    print("结果：%s" % ("仅比对" if a.check else "已落盘"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

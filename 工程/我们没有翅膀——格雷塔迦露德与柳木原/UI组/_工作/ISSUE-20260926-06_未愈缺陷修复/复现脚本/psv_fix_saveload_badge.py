# -*- coding: utf-8 -*-
r"""psv_fix_saveload_badge.py —— 23/24 页码徽章缺陷修复（数据侧）：前导页数字贴回烘焙「/10」左槽 + 系统键行上移让位

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）· **未愈缺陷修复轮**（派单缺陷 ① 与 ② 的数据侧）。
素材侧：`工具\psv_fix_save_badge.py`（**删除上一轮的抹字补丁、恢复 PSV 原图**——见该文件头部的完整依据）。

■ 缺陷 ①：页码数字压住「退出游戏」
  上一轮把徽章数字放到 `sv.pgnum_*` 的 `(1663, 68, 180, 80)`：右缘 1843（= 烘焙件右缘），
  与 `sv.sys_end` 按钮 `(1670, 44, 210, 50)` 矩形**相交 173×26 = 4498 px²**（`sv.sys_end_hit`
  `(1662,36,226,66)` 相交更大）⇒ 数字压在按钮与按钮文字上。

■ 缺陷 ②的备选（已定）：保留烘焙「/10」，只补**前导页数字**
  素材侧结论：同族像素拷贝在本徽章带**不对齐**（gal_shell dy=+4 徽章带 |Δ| 均值 9.05 / p95 32 /
  71% 像素 >4；徽章带外 3.36 / 6.33 / 6.12）⇒ 按派单「|Δ|≤2 才整带拷贝」口径不可用；
  而 PSV 原图徽章内 x1690..1757 / y84..132 本就是**干净霜面**（原设计即「烘焙 /10 ＋ 引擎绘前导数字」）。
  ⇒ 删除补丁、保留烘焙「/10」，`sv.pgnum_01..10` 改为只绘**前导页数字**并贴到「／」左槽。

■ 本脚本改什么（两屏同款）
  ① `sv.pgnum_01..10`：`sample`/`text` 由 `"N / 10"` → `"N"`；几何 → `(1676, 83, 84, 48)`
     （右缘 1760 = 烘焙「／」左沿 1763 − 3px；纵向盒 83..130 与烘焙数字带 84..131 同带）；
     字号 66 → **68**（见下「字号/基线推导」）；`align:right` / 描边色 / 描边宽一律沿用。
  ② `sv.sys_game|title|end` 三按钮行（各含 `_tx` / `_hit`，共 9 件）**上移 22px**：
     `y 44→22`（按钮与文字）、`y 36→14`（热区）⇒ 与页签行（`sv.tab_*` y24）顶端基本对齐，并让出徽章数字带。
     按钮尺寸 / 九宫格 / `source` / action **一律未改**。
  ③ 屏级 `page_flag:"sv_page"`、`flags_default.sv_page:"1"` **保留**（机制未动）。

■ 字号/基线推导（可复核；依据 = 引擎自身排版式 + 字体实际 ink 度量）
  · 引擎排版（`krkr\game\ui_theme.tjs:uiThemeLayoutText`）：`lineH = max(size, floor(size*1.4))`（body 行距 1.4，
    见 `layout\ui_layout.json:fonts.line_spacing.body`）；`valign:"middle"` ⇒ `y_text = el.y + floor((el.h − lineH)/2)`；
    文本按 `drawText(x, y_text)` 画（y_text = 行框顶 = 字体 ascent 顶）。
  · **烘焙字形实测（白芯口径，radix = `Q8(otv_save_bg_cn)`，逐像素等于 PSV 原图）**：
    「1」白芯 y87..123（**高 37×16**）、「0」白芯 y87..123（高 37×36）、「10」白芯 x1798..1845（宽 48）、
    「／」白芯 x1763..1788 / y88..127（高 40）。⇒ 数字白芯高 37、数字带中心 y105。
  · 引擎字体 = `fonts.fallback_faces[0]`「微软雅黑 Bold」（msyhbd）——用 FreeType 量其 **ink 比例**：
    「1」白芯高/字号 = 0.765（`yoff 14..50` @size48）、「／」高/字号 = 0.875。
  · 令白芯高 == 37 ⇒ `size = 37/0.765 = 48.4` ⇒ 取 **48**（实测白芯高 37 ✓、「／」42 vs 烘焙 40，差 2px）。
  · 令白芯 == y87..123 ⇒ `y_text + 14 = 87` ⇒ `y_text = 73`；取 `el.h = 48` ⇒ `lineH = floor(48*1.4) = 67`
    ⇒ `floor((48−67)/2) = −10` ⇒ `el.y = 73 + 10 = **83**`。
  · 水平：`align:"right"`、盒右缘 `1759`（= 烘焙「／」白芯左沿 1762 − 3px；烘焙「／」与「10」之间实测也是
    3–4px 间隙）⇒ 盒 `(1699, 83, 60, 48)`（宽 60 ≥「10」白芯宽 53 ✓）。
  · 对照上一轮：上一轮取 size 66（按「烘焙数字高 48」反推）⇒ 其白芯高 = 0.765×66 ≈ 50，**比烘焙 37 高 35%**；
    本轮的 37 与烘焙白芯逐像素同带。
  ⚠️ 未决点：上式为「引擎排版式 + 系统字体实际 ink 度量（FreeType）」推演，**未做实机像素复验**
     （派单禁跑巡演/浏览器）⇒ 若实机 ink 偏移 >2px，只需按同一式微调 `NUM_BOX` 的 y 与 `NUM_SIZE`。

■ 幂等
  读盘 → 置固定值 → 写回（`ensure_ascii=False, indent=1`，与盘上现有格式一致）⇒ 重复运行逐字节相同。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_未愈缺陷修复\复现脚本\psv_fix_saveload_badge.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCR = os.path.join(UI, "layout", "screens")
EVID = os.path.join(UI, "_工作", "ISSUE-20260926-06_未愈缺陷修复", "取证")

# ── 目标几何（数值依据见文件头「字号/基线推导」；改这里即可整体再定标） ──────────
NUM_SIZE = 48                         # 字号：按烘焙字形**白芯高 37px**（「／」40px）与微软雅黑
                                      #   「数字白芯高/字号 = 0.765」反推 ⇒ 47–48；取 48（白芯 37、／ 42）
NUM_BOX = (1699, 83, 60, 48)          # 前导页数字盒：右缘 1759 = 烘焙「／」白芯左沿 1762 − 3px；
                                      #   y=83 使 y_text = 83 + floor((48 − floor(48*1.4))/2) = 73
                                      #   ⇒ 白芯 87..123 = 烘焙「1」白芯 87..123（逐像素同带）
SYS_SHIFT = -22                       # 系统键行整体上移
BAKED_DIGITS = (1798, 87, 1845, 123)  # 烘焙「10」白芯实测包围盒（x0,y0,x1,y1 含）
BAKED_SLASH = (1763, 88, 1788, 127)   # 烘焙「／」白芯实测包围盒
NUM_BOX_X = (NUM_BOX[0], NUM_BOX[1], NUM_BOX[0] + NUM_BOX[2], NUM_BOX[1] + NUM_BOX[3])

NUM_NOTE = (
    "页码徽章前导页数字（引擎绘制）第 %d / 10 页。"
    "★ **未愈缺陷修复轮（2026-09-26）**：上一轮把本件写成「N / 10」右缘 1843 ⇒ 与 `sv.sys_*` 三按钮行"
    "**矩形相交 4498 px²**（数字压在「退出游戏」按钮上）。本轮改为**只绘前导页数字**、几何贴回烘焙「／」左槽："
    "`sample` 由「N / 10」→「N」、盒 `(1663,68,180,80)` → `" + repr(NUM_BOX) + "`、字号 66 → " + str(NUM_SIZE) + "、"
    "`align:right` 与描边口径沿用（`outline` 2px `#3E63B8`）。**底图烘焙的「/10」不再抹除**"
    "（`工具\\psv_fix_save_badge.py` 已改为 **删除上一轮的抹字补丁、恢复 PSV 原图**——同族像素拷贝在徽章带"
    "实测 |Δ| 均值 9.05 > 2 不达标；而 PSV 原图徽章内 x1690..1757 本就是留给引擎绘前导数字的**干净霜面**）。"
    "⇒ 徽章显示为「**N**（引擎）+ **／10**（烘焙原图）」，与 PSV 原设计（PSV 原作同样只烘焙「／」与总数、"
    "前导数字由引擎绘）同构。"
    "`vis_flag` = 屏级 `page_flag`（`sv_page`）——与底部 `sv.pg01..10` 的 `page_1..10` **同语义**："
    "1 基页号／共 10 页；底部键翻页、本件只显示当前页号。"
    "⚠️ 未决点①：`page_1..10` 在 `krkr\\game\\*.tjs` 无处理器（演示运行期未实现存读档翻页），"
    "受禁改 tjs 约束本轮只做数据侧声明 ⇒ 徽章显示 `flags_default` 的「1」；"
    "驱动方须编程组按既有机理补 `uiScreenFlagSet(\"sv_page\", \"\"+页号)`（数据侧已就绪）。"
    "⚠️ 未决点②（样式，留主代理/vision）：**烘焙「10」与「／」实测无深色描边**（其四周即霜面 "
    "RGB≈(176–192, 184–208, 240–248)），而本件按项目口径带 2px `#3E63B8` 描边 ⇒ 前导数字会有一圈"
    "烘焙件没有的深蓝晕。若要完全同质，可把本件 `outline` 置 false（纯白字）——本轮按派单「描边沿用现状」未改。"
)


SYS_NOTE_SUFFIX = "；★ **未愈缺陷修复轮（2026-09-26）**：y 44→22（热区 36→14），共 3 件按钮/3 件文字/3 件热区整体上移 22px" \
                  "——让出徽章前导数字带（y83..131）使二者矩形相交 = 0，并与页签行（y24）顶端对齐；尺寸/九宫格/action 未改。"
SYS_HIT_SUFFIX = "；★ 未愈缺陷修复轮（2026-09-26）：随按钮行上移 22px（y36→14）"


def add_once(note, suffix):
    """幂等追加：先把重复段折叠成一段（清掉历史累加），已含则原样返回。"""
    note = note or ""
    if suffix:
        while suffix + suffix in note:
            note = note.replace(suffix + suffix, suffix)
    return note if (not suffix or suffix in note) else note + suffix

ROUND_NOTE = """★ **未愈缺陷修复轮（2026-09-26 · ISSUE-20260926-06，两处未愈缺陷逐条修）**：
  · **① 页码数字压住「退出游戏」→ 已修**：`sv.pgnum_*` 与 `sv.sys_*` 的矩形相交由 15116 px² 降到 **0**——
    数字盒改 `(1699, 83, 60, 48)`（贴烘焙「／」左槽、右缘 1759 = 烘焙「／」白芯左沿 1762 − 3px），
    `sv.sys_*` 三按钮行（含 `_tx`/`_hit`，9 件）**上移 22px**（按钮/文字 y44→22、热区 y36→14，与页签行 y24 顶端对齐）。
    自证：逐对相交面积核算（`复现脚本\\psv_fix_saveload_badge.py` 输出，改前 15116 → 改后 0 px²）
    + 1:1 合成图（`取证\\合成_右上角_1to1_对照_*.png`）。
  · **② 抹字补丁可见 → 已修（采派单备选）**：`工具\\psv_fix_save_badge.py` 由「抹字」改为「**删除补丁、恢复 PSV 原图**」。
    依据：同族像素拷贝在**徽章带**实测不对齐（`x_ui_psv_gal_shell.png` dy=+4：徽章带 |Δ| 均值 9.05 / p95 32 /
    n>4 = 71%，而徽章带外 3.36 / 6.33 / 6.12 —— 差异只集中在徽章内，ALBUM 屏徽章自带另一套装饰）
    ⇒ 派单「|Δ|≤2 才整带拷贝」不满足；而 PSV 原图徽章内（「／」左槽 x1690..1762 / y87..123）本就是**干净霜面**
    （原设计即「烘焙 /10 ＋ 引擎绘前导数字」）⇒ 保留烘焙「/10」、只补前导数字。
    自证：盘上件与 `Q8(otv_*_bg_cn 去上下各 4px)` **逐像素相同（max|Δ| = 0）**；掩码（旧补丁矩形
    x1763..1845 / y80..140）外逐像素与改前相同；补区 stdev 13.42 → 20.28 = 原图同区 20.28（差 0.00%）；
    跨边台阶「脚本引入 = 0.00」；装饰结构量 = 原图；10× 改前/改后对照见 `取证\\zoom_badge_10x_*.png`。
  · 屏内像素文字（`sv.num*`/`sv.info*`）与其余几何/action **未动**。
"""


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def intersect_area(a, b):
    """a/b = (x0,y0,x1,y1)（右下开区间）⇒ 相交面积（px²）。"""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def collide_report(screen, path, label="改后"):
    """打印「页码文本矩形 ×（三按钮矩形 + 标题矩形 + 热区）」相交矩阵，返回总相交面积。"""
    els = {e["id"]: e for e in screen["elements"]}
    nums = [els["sv.pgnum_%02d" % i] for i in range(1, 11) if ("sv.pgnum_%02d" % i) in els]
    others = [els[k] for k in ("sv.sys_game", "sv.sys_game_tx", "sv.sys_game_hit",
                               "sv.sys_title", "sv.sys_title_tx", "sv.sys_title_hit",
                               "sv.sys_end", "sv.sys_end_tx", "sv.sys_end_hit") if k in els]
    tot = 0
    print("  相交核算 · %s（%s；10 件页码文本 × 9 件系统键/标题矩形/热区）" % (os.path.basename(path), label))
    for n in nums:
        rn = rect(n)
        hits = [(o["id"], intersect_area(rn, rect(o))) for o in others]
        bad = [(i, a) for i, a in hits if a > 0]
        tot += sum(a for _, a in bad)
        if n["id"] == "sv.pgnum_01":
            print("     %s 盒 %s" % (n["id"], rn))
            for i, a in hits:
                print("        × %-16s = %d px²%s" % (i, a, "" if a == 0 else "   ← 相交！"))
        elif bad:
            print("     %s 相交 %s" % (n["id"], bad))
    print("     合计相交面积 = %d px² %s" % (tot, "✓（=0）" if tot == 0 else "✗"))
    # 烘焙图形碰撞（信息项）：数字盒与烘焙「10」/「／」的关系
    print("     信息：数字盒 %s ｜ 烘焙「／」%s ｜ 烘焙「10」%s ⇒ 与「10」相交 %d px²、与「／」右侧间隙 3px"
          % (NUM_BOX_X, BAKED_SLASH, BAKED_DIGITS,
             intersect_area(NUM_BOX_X, (BAKED_DIGITS[0], BAKED_DIGITS[1], BAKED_DIGITS[2] + 1, BAKED_DIGITS[3] + 1))))
    return tot


def pre_fix_report(scr):
    """改前口径（上一轮几何）的相交核算——用于「15116 px² → 0」的对照。

    ★ 注意：本脚本已把 `sv.sys_*` 的 y 改成新值，故改前的按钮/热区矩形**必须按上一轮基准 y 重建**
      （按钮/文字 y=44 h=50；热区 y=36 h=66），不能用盘上现值。
    """
    els = {e["id"]: e for e in scr["elements"]}
    old_num = (1663, 68, 1843, 148)                    # 上一轮 sv.pgnum_* 几何
    tot = 0
    for base in ("sv.sys_game", "sv.sys_title", "sv.sys_end"):
        for suf, oy, oh in (("", 44, 50), ("_tx", 44, 50), ("_hit", 36, 66)):
            e = els[base + suf]
            old_sys = (e["x"], oy, e["x"] + e["w"], oy + oh)
            a = intersect_area(old_num, old_sys)
            if a:
                print("     改前：页码盒 %s × %-16s %s = %d px²" % (old_num, base + suf, old_sys, a))
            tot += a
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只核算相交与格式，不写盘")
    a = ap.parse_args()

    print("=" * 110)
    print("23/24 页码徽章缺陷修复（数据侧）：前导页数字贴回烘焙「/10」左槽 ＋ 系统键行上移 22px")
    print("  NUM_BOX=%s  NUM_SIZE=%d  烘焙「／」%s  烘焙「10」%s" % (NUM_BOX, NUM_SIZE, BAKED_SLASH, BAKED_DIGITS))
    print("=" * 110)

    total = 0
    for fn in ("23_save.json", "24_load.json"):
        p = os.path.join(SCR, fn)
        before = open(p, "rb").read()
        scr = load(p)
        pre = pre_fix_report(scr)

        # ① 前导页数字
        for i in range(1, 11):
            eid = "sv.pgnum_%02d" % i
            e = next((x for x in scr["elements"] if x["id"] == eid), None)
            assert e is not None, "%s 缺 %s" % (fn, eid)
            e["x"], e["y"], e["w"], e["h"] = NUM_BOX
            e["sample"] = str(i)
            if "text" in e:
                e["text"] = str(i)
            e["font"]["size"] = NUM_SIZE
            e["align"] = "right"
            e["valign"] = "middle"
            e["note"] = NUM_NOTE % i

        # ② 系统键行整体上移（只加位移量一次：从「基准 y」推目标值，避免重复调用时累加）
        for base, base_y in (("sv.sys_game", 44), ("sv.sys_title", 44), ("sv.sys_end", 44)):
            for suf, by in (("", base_y), ("_tx", base_y), ("_hit", base_y - 8)):
                eid = base + suf
                e = next((x for x in scr["elements"] if x["id"] == eid), None)
                assert e is not None, "%s 缺 %s" % (fn, eid)
                e["y"] = by + SYS_SHIFT
                if suf == "_hit":
                    e["note"] = add_once(e.get("note", ""), SYS_HIT_SUFFIX)
                else:
                    e["note"] = add_once(e.get("note", ""), SYS_NOTE_SUFFIX)

        # ③ 屏级说明：去重（上一轮把同一段写了两遍）+ 追记本轮
        if fn == "23_save.json":
            dup = ("★ **修复轮追加**：本屏新增屏级 `page_flag:\"sv_page\"` 与 10 件徽章页码文本 "
                   "`sv.pgnum_01..10`、当前页签换件 `ui/x_ui_psv_tab_sel.png`（详见文末「修复轮」段）；"
                   "`sv.tab_*` 的 `action` 仍未改。\n")
            if scr["note"].count(dup) == 2:
                scr["note"] = scr["note"].replace(dup + dup, dup)
        if "★ **未愈缺陷修复轮（2026-09-26" not in scr["note"]:
            scr["note"] = scr["note"].rstrip("\n") + "\n" + ROUND_NOTE

        post = collide_report(scr, p)
        total += post
        print("     改前合计相交 = %d px² → 改后 %d px²" % (pre, post))
        if not a.check:
            save(p, scr)
            after = open(p, "rb").read()
            print("     落盘 %s（%d → %d 字节）md5=%s" %
                  (fn, len(before), len(after), hashlib.md5(after).hexdigest()[:12]))
    print("-" * 110)
    print("合计相交面积 = %d px²（口径：右下开区间矩形；>0 即未通过）" % total)
    print("结果：%s" % ("仅核算（--check）" if a.check else "已落盘（重跑逐字节相同、幂等）"))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

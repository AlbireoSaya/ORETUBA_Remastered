# -*- coding: utf-8 -*-
r"""M06 · 回想（backlog）屏重排 · 数据侧一次性构建（`layout\screens\26_backlog.json`）

Issue : ISSUE-20260924-06（回想屏重排 · 数据 + 素材模块）
契约  : `_工作\ISSUE-20260924-06_回想屏重排\方案.md`（**接口冻结书**）

■■ 本脚本做什么（只改 `26_backlog.json` 一个文件）
  ① `bl.list.max_rows 3 → 4`（用户指令①「渲染 4 行」）；
  ② `bl.list.item_h 240 → 205`、`gap 0`（**算式**见下）；
  ③ **新增 `item_text`**：块内文本区局部矩形 + 折行/行数（机制侧据此排版，见「契约增补」）；
  ④ **新增 `item_buttons`**：逐块「跳转」「重新播放」两个按钮（块内局部矩形 + 三态图 + 动作）；
  ⑤ **删除**跨 3 块的静态按钮 `bl.jump` / `bl.jump_tx` / `bl.jump_hit` / `bl.spk` / `bl.spk_hit`
     —— 它们被逐项按钮取代（列表分页滚动时静态元素不随块走，见冻结书 §0 结论）；
  ⑥ `bl.list.item_frame.nine` 的 `t/b 0 → 34`（块高压缩后 `t=b=0` 会把整卡纵向压扁，见下）；
  ⑦ `labels` 补到 4 条（占位用；真实台词运行期灌入）。
  **保留不动**：`bl.dim`、`bl.close` / `bl.close_hit`、`bl.up` / `bl.up_hit`、
                `bl.slider` / `bl.slider_hit`、`bl.down` / `bl.down_hit`（滚动列与关闭键）。

■■ 几何算式（全部可由冻结书 §1 的不等式推出）
  · 栈顶 y=108（PSB `#rects/frame` 的 top）、4 块 + 3 个 gap 必须落在**栈底 ≤ 940** 内：
        4 × item_h + 3 × gap ≤ 940 − 108 = **832**
    取 `gap = 0`（沿用现状）、`item_h = 205` ⇒ `4 × 205 + 0 = 820 ≤ 832` ✓
    ⇒ 栈底 = 108 + 820 = **928**，距上限 940 留 12 px 余量；距下滚键顶（y=952）24 px。
    （item_h=208 也满足不等式但栈底正好压到 940，无余量；205 留出余量且行高整齐。）
  · **文本区**（`item_text`，块内局部坐标）：x=**219**、y=19、w=**1117**、h=173。
    ★ **+13px 形体修正（本轮实测得出的关键一条）**：块底板素材是
      **1350×241 的卡体 + 四边各 12.5px 柔光/外发光**（源 1375×266），而引擎把**整张画布**
      画进元素矩形 ⇒ 画面上**可见卡体恒内缩 12.5px**（`证据\m06_nine_grid_study.py` 形体实测）。
      PSB 的坐标（文本 206 / JUMP 15 / スピーカー 141）是照「卡体 = 元素矩形」写的，
      直接照抄会让每个元素都离可见卡缘近 12.5px（实测观感：按钮贴住卡缘）。
      故按 **+13px（取整）** 修正：文本 x 206→**219**、跳转 x 15→**28**、重播 x 141→**154**。
    - 左界 219 = 卡体左缘 12.5 + PSB 的 206；右界 1336 = 219 + 1117 ≈ 卡体右缘 1336.5。
    - h=173：卡体上缘 12.5 / 下缘 192.5 ⇒ 19..192 全在卡体之内。
      **纵向加不了这 12.5**：4 行 × 行距 42 = 168，而卡体高只有 180 ⇒ 上留 6.5 / 下留 5.5，
      已是 item_h=205 下的极限（要补齐竖向修正得把 item_h 抬到 230，而 4×230 = 920 > 832 不允许）。
      行距 = floor(font.size 30 × line_spacing.body 1.4) = 42（元素未写 line_spacing ⇒ 回落 body，
      见 `krkr\game\ui_theme.tjs:144` 与 `layout\ui_layout.json.fonts.line_spacing.body`）。
  · **按钮**（块内局部坐标，均在左栏内、不越 x=1610 滚动列左界，也不压文本区 x≥219）：
    - 跳转   ：x 28,  y 26, 94×29  —— x = PSB `JUMP`（223−208=15）+ 13；
    - 重新播放：x 154, y 18, 44×44 —— x = PSB `スピーカー`（349−208=141）+ 13；
    - y 取「与文本区第一行（19..61，中心 ≈40）垂直居中对齐」：跳转 26+14.5=40.5、
      重播 18+22=40。两端 y 因此都随块内文本首行走，而非沿用 PSB 的 33/30（那是 240 块高的位置）。

■■ 素材侧联动（`工具\m49_make_backlog_assets.py` 同步交付）
  · 重新播放键由 25×27 / 37×40 重做为 **`ui/x_ui_spk2_{off,over,on}.png` 44×44**（用户点名「太小」）；
    **旧件 `x_ui_spk_*` 保留不删**（冻结书 §3）。44×44 为 **1:1 件（无 nine）**
    ⇒ `item_buttons[].w/h` 必须 = 44×44。
  · 跳转键沿用既有 `ui/x_ui_jump_{off,over,on}.png`（素材 52×29 / 74×41），
    绘制尺寸仍 94×29 ⇒ nine `{l:13, t:7, r:13, b:7}`（**原样照抄现状，未改尺寸**）。
  · `x_ui_msgblock.png`（1375×266）九宫格 `t=b=0 → 34`：实测竖向细节区 = 柔光 13 + 圆角 20 = 33 px
    ⇒ t=b ≥ 33 即整段 1:1 绘制；取 34 留 1 px 余量。t=b=0 在 item_h=205 下圆角纵向被压 23%
    （逐像素差 max=244、7.87% 像素 |Δ|>8，见证据脚本输出）。

■■ ★ 契约增补（**冻结书 §1/§2 未列，须机制侧认领**，已在交付报告「需裁决点」列明）
  1. `item_text`（块内文本区矩形 + wrap/max_lines/align/valign）：冻结书只定义了 `item_buttons`，
     未定义「每块的台词画在哪」。既有 `list` 的标签路径（`uiWidgetDrawList`）是**单行、不折行、
     不截断**，真实台词最长 132 字（实测）必然溢出 ⇒ 机制侧必须按 `item_text` 折行绘制。
     字段口径与 `item_buttons` 完全同族：**块内局部坐标**、缺省=沿用旧的「项内居中单行」行为。
  2. `item_buttons[].label` / `font`（跳转键的「跳转」二字由**引擎绘制**）：
     本工程铁律禁止把文字烘焙进图（`M34_UI复刻总纲.md` §七），故按钮文字必须随块走 ⇒
     逐项按钮须支持可选 `label` + `font`（绘制口径同既有 `hit.label`：居中、单行、valign=middle）。

■■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_build_backlog.py --dry-run   # 只打印 diff，不写盘
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_build_backlog.py            # 落盘
  ★ 本脚本是**一次性脚手架**：落盘后 `layout\screens\26_backlog.json` 才是真相源，
    此后手工维护（生成器侧处置见屏幕 note 与交付报告）。
"""
from __future__ import annotations

import difflib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # <UI组>
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")

ITEM_H, GAP, MAX_ROWS = 205, 0, 4
FRAME_W = 1349
TEXT = {"x": 219, "y": 19, "w": 1117, "h": 173,
        "wrap": True, "max_lines": 4, "align": "left", "valign": "top"}
BTN_JUMP = {"key": "jump", "x": 28, "y": 26, "w": 94, "h": 29,
            "asset": "ui/x_ui_jump_off.png", "nine": {"l": 13, "t": 7, "r": 13, "b": 7},
            "state_assets": {"normal": "ui/x_ui_jump_off.png", "hover": "ui/x_ui_jump_over.png",
                             "pressed": "ui/x_ui_jump_on.png"},
            "action": "backlog_jump:%row%", "label": "跳转",
            "font": {"size": 20, "bold": True, "color": "@palette.node_locked", "shadow": False,
                     "shadow_color": "@palette.shadow", "shadow_ofs": 0},
            "align": "center",
            "note": "跳转键：块内局部矩形（x28 = PSB `バックログ/オフ/JUMP` 的 223−208=15，+13 形体修正；"
                    "y26 = 与文本区首行中心(≈40)垂直居中）。文字「跳转」由引擎绘制（`label`+`font`，"
                    "本工程铁律禁止文字烘焙进图）。矩形 94×29 与素材 nine 同现状、未改尺寸。"}
BTN_REPLAY = {"key": "replay", "x": 154, "y": 18, "w": 44, "h": 44,
              "asset": "ui/x_ui_spk2_off.png",
              "state_assets": {"normal": "ui/x_ui_spk2_off.png", "hover": "ui/x_ui_spk2_over.png",
                               "pressed": "ui/x_ui_spk2_on.png"},
              "action": "backlog_replay:%row%",
              "note": "重新播放键（用户点名「太小」⇒ 由 25×27/37×40 重做为 44×44 新件，旧件保留不删）。"
                      "块内局部矩形 x154 = PSB `スピーカー` 的 349−208=141，+13 形体修正；y18 = 与首行中心(≈40)对齐。"
                      "**1:1 件、无 nine** ⇒ w/h 必须 = 素材 44×44。"}

LABELS = [
    "这里是回想文本区（占位文案，真实台词运行期灌入）。",
    "每块 205 高、块间无间隙；可见 4 块，超出部分由右侧滑块翻页滚动。",
    "每块左栏两个按钮：跳转 94×29（x28,y26）、重新播放 44×44（x154,y18）。",
    "文本区块内局部 219,19 1117×173，字号 30 / 行距 42 / 最多 4 行（实测语料最多 4 行、0 截断）。",
]

NEW_NOTE = (
    "回想消息块列表。**本轮（ISSUE-20260924-06，用户指令：渲染 4 行 + 重新排版 + 每块加「跳转」"
    "「重新播放」）改为每屏 4 块、逐块两个按钮**：\n"
    "★ 几何：`item_h=205`、`gap=0` ⇒ 4 块 = 820 ≤ 832（栈顶 y=108、栈底 928 ≤ 940，依据冻结书 §1 的不等式）。\n"
    "★ 文本区 `item_text`：块内局部 (219,19) 1117×173，字号 30 / 行距 42 ⇒ 4 行；"
    "左右界 219/1336 = 块底板**可见卡体**左右缘（卡体恒内缩 12.5px，故 PSB 的 206 与 15/141 各 +13）。容量实测：6 个 scene_*.jsonl 共 96680 条非空台词，"
    "按引擎 `uiThemeWrap`（含行首/行尾禁则）折行后**最多 4 行、超限 0 条**（证据见 "
    "`_工作\\ISSUE-20260924-06_回想屏重排\\证据\\m06_capacity_report.txt`）。\n"
    "★ 逐块按钮 `item_buttons`（**块内局部坐标**）：跳转 (28,26) 94×29 → `backlog_jump:%row%`；"
    "重新播放 (154,18) 44×44 → `backlog_replay:%row%`。两者 x 沿用 PSB、y 与文本首行居中；"
    "均在左栏内、不越 x=1610 滚动列左界。\n"
    "★ 块底板九宫格 `t/b 0→34`：源图 1375×266 的竖向细节区 = 柔光 13 + 圆角 20 = 33px，"
    "`t=b=0` 在 205 块高下圆角纵向被压 23%（实测逐像素差 max=244 / 7.87% 像素 |Δ|>8），补 34 后 0% 形变"
    "（证据 `证据\\m06_msgblock_nine_compare.png`）。\n"
    "★ **跨 3 块的静态按钮已删除**（`bl.jump` / `bl.jump_tx` / `bl.jump_hit` / `bl.spk` / `bl.spk_hit`）："
    "列表分页滚动时静态元素不随块走，逐块按钮只能走「逐项渲染 + 逐项子命中」（冻结书 §0 结论）。"
    "滚动列（`bl.up/down/slider` 及各自 `_hit`）、`bl.close*`、`bl.dim` 均保持原样。\n"
    "★ 重新播放键素材：**新件** `ui/x_ui_spk2_{off,over,on}.png`（44×44，程序化生成，"
    "`工具\\m49_make_backlog_assets.py`）；旧件 `ui/x_ui_spk_*.png` **保留不删**（冻结书 §3）。\n"
    "★ `backlog_replay` / `backlog_jump` 本轮为**接口冻结/占位**：引擎尚无音频代码，"
    "命中→派发→日志可见，音频接线留给编程组（不得声称已生效）。"
)

DROP = ("bl.jump", "bl.jump_tx", "bl.jump_hit", "bl.spk", "bl.spk_hit")


def build(cur):
    d = json.loads(json.dumps(cur, ensure_ascii=False))       # 深拷贝
    out = []
    for e in d["elements"]:
        if e.get("id") in DROP:
            continue
        if e.get("id") == "bl.list":
            e["item_h"] = ITEM_H
            e["gap"] = GAP
            e["max_rows"] = MAX_ROWS
            e["labels"] = list(LABELS)
            e["actions"] = [""] * MAX_ROWS
            e["item_frame"]["nine"] = {"l": 60, "t": 34, "r": 60, "b": 34}
            e["item_text"] = dict(TEXT)
            e["item_buttons"] = [dict(BTN_JUMP), dict(BTN_REPLAY)]
            e["note"] = NEW_NOTE
        out.append(e)
    d["elements"] = out
    return d


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def main():
    raw = io.open(SCREEN, encoding="utf-8").read()
    cur = json.loads(raw)
    new = dump(build(cur))
    dry = "--dry-run" in sys.argv
    print("=" * 100)
    print("M06 · 回想屏数据重排（%s）" % ("dry-run：只打印 diff，不写盘" if dry else "落盘"))
    print("  目标 %s" % os.path.relpath(SCREEN, UI).replace("\\", "/"))
    print("  元素数 %d → %d（删除 %s）"
          % (len(cur["elements"]), len(json.loads(new)["elements"]), " / ".join(DROP)))
    d2 = json.loads(new)
    lst = [e for e in d2["elements"] if e.get("id") == "bl.list"][0]
    print("  item_h 240→%d ｜ gap 0 ｜ max_rows 3→%d ｜ nine t/b 0→34 ｜ 新增 item_text + item_buttons[%d]"
          % (ITEM_H, MAX_ROWS, len(lst["item_buttons"])))
    print("  4×item_h + 3×gap = %d ≤ 832 ✓（栈底 %d ≤ 940）" % (4 * ITEM_H + 3 * GAP, 108 + 4 * ITEM_H + 3 * GAP))
    print("=" * 100)
    diff = list(difflib.unified_diff(raw.splitlines(True), new.splitlines(True),
                                    "26_backlog.json(现状)", "26_backlog.json(重排后)", n=2))
    sys.stdout.write("".join(diff))
    if dry:
        print("\n（dry-run：磁盘未改动）")
        return 0
    io.open(SCREEN, "w", encoding="utf-8", newline="\n").write(new)
    print("\n已写入 %s（%d B → %d B）" % (os.path.relpath(SCREEN, UI), len(raw.encode("utf-8")),
                                        len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())

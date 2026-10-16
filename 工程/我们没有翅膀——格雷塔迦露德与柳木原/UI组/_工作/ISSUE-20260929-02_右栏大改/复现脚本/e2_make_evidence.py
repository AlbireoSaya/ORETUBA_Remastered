# -*- coding: utf-8 -*-
r"""e2_make_evidence.py —— ISSUE-20260929-02 · E2：产出三份证据（前/后对照、改后清单 TSV、金标新旧）

输入（均为只读）：
  · 改前快照：`_工作\ISSUE-20260929-02_右栏大改\备份_gen_flow_layout_改前.py`（改动前的生成器整份备份）
  · 改后屏数据：`layout\screens\32_flowchart.json`（落盘后的交付样例 screen1）
输出（写进 `_工作\ISSUE-20260929-02_右栏大改\证据\`）：
  · 生成器改动_前.md ／ 生成器改动_后.md ／ 右栏元素_改后清单.tsv
"""
from __future__ import annotations

import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE_DIR))
EVID = os.path.join(ISSUE_DIR, "证据")
BEFORE_PY = os.path.join(ISSUE_DIR, "备份_gen_flow_layout_改前.py")
SCREEN = os.path.join(UI, "layout", "screens", "32_flowchart.json")

DELETED = ["fc.mini%d" % i for i in range(1, 9)] + ["fc.mapview", "fc.pbk_panel",
                                                   "fc.p_player", "fc.p_player_tx"]
ADDED = ["fc.play_win", "fc.play_view", "fc.pbkick_pause"]
CHANGED = ["fc.p_title", "fc.p_title_tx", "fc.p_text", "fc.p_text_tx",
           "fc.p_message", "fc.p_message_tx", "fc.pbkick", "fc.pbkick_hit"]
RIGHT_IDS = ["fc.p_title", "fc.p_title_tx", "fc.p_text", "fc.p_text_tx", "fc.pbk_panel",
             "fc.p_player", "fc.p_player_tx", "fc.p_message", "fc.p_message_tx",
             "fc.smallmap", "fc.mapview"] + ["fc.mini%d" % i for i in range(1, 9)] \
            + ["fc.pbkick", "fc.pbkick_hit", "fc.play_win", "fc.play_view", "fc.pbkick_pause"]
FIELDS = ["kind", "z", "x", "y", "w", "h", "visible_default", "vis_flag", "vis_when",
          "asset", "dynamic", "nine", "state_assets", "opacity", "color", "font",
          "align", "valign", "wrap", "max_lines", "sample", "action", "label",
          "line_spacing", "source"]


def snap_from_py(path):
    s = io.open(path, encoding="utf-8").read()
    m = re.search(r'STATIC_ELEMENTS_JSON = r"""(.*?)"""', s, re.S)
    return {e["id"]: e for e in json.loads(m.group(1))}


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, str):
        s = v.replace("\n", "⏎")
        return s if len(s) <= 200 else s[:197] + "…"
    return json.dumps(v, ensure_ascii=False)


def short(v):
    return fmt(v)


def row(before, after, ids):
    out = []
    for i in ids:
        b, a = before.get(i), after.get(i)
        out.append("| `%s` | %s | %s | %s | %s | %s | %s | %s |"
                   % (i, b["kind"] if b else "—", a["kind"] if a else "—",
                      "%s,%s,%s,%s" % (b["x"], b["y"], b["w"], b["h"]) if b else "—",
                      "%s,%s,%s,%s" % (a["x"], a["y"], a["w"], a["h"]) if a else "—",
                      short((b.get("font") or {}).get("color")) if b else "—",
                      short((a.get("font") or {}).get("color")) if a else "—",
                      ("%s/%s" % (b.get("vis_flag") or "—", b.get("vis_when") or "—")) if b else "—",
                      ))
    return out


def main():
    before = snap_from_py(BEFORE_PY)
    after = {e["id"]: e for e in json.load(io.open(SCREEN, encoding="utf-8"))["elements"]}
    os.makedirs(EVID, exist_ok=True)

    # ── ①/② 生成器改动_前.md / _后.md ──
    for tag, src in (("前", before), ("后", after)):
        L = []
        L.append("# 生成器改动_%s · ISSUE-20260929-02 · 模块 E2（`工具/gen_flow_layout.py`）\n" % tag)
        L.append("> 口径：**只统计右栏相关 id**（%d 件）—— 12 件删除 ＋ 8 件改动 ＋ 3 件新增 ＋ 1 件保留未动"
                 "（`fc.smallmap`）。\n" % len(RIGHT_IDS))
        L.append("> %s = %s。\n" % ("改前快照来源" if tag == "前" else "改后来源",
                                    "`_工作/ISSUE-20260929-02_右栏大改/备份_gen_flow_layout_改前.py`（整份备份）"
                                    if tag == "前" else "`layout/screens/32_flowchart.json`（落盘后的交付样例 screen1）"))
        L.append("\n## 一、逐件字段（右栏相关 %d 件）\n" % len(RIGHT_IDS))
        L.append("| id | kind | z | x | y | w | h | font.color | outline | vis_flag | vis_when | visible_default | action | valign/wrap/max_lines | asset / state_assets |")
        L.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |")
        for i in RIGHT_IDS:
            e = src.get(i)
            if not e:
                L.append("| `%s` | （本档不存在） | | | | | | | | | | | | |" % i)
                continue
            f = e.get("font") or {}
            outl = ("%s/%s/%s" % (f.get("outline"), f.get("outline_color"), f.get("outline_width"))
                    if f.get("outline") is not None else "—")
            ass = e.get("asset")
            if e.get("state_assets"):
                ass = "%s ＋ state_assets{%s}" % (ass, ",".join(
                    "%s=%s" % (k, v.split("/")[-1]) for k, v in sorted(e["state_assets"].items())))
            if e.get("dynamic"):
                ass = "asset:null ＋ dynamic:%s" % e["dynamic"]
            L.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                     % (i, e.get("kind"), e.get("z"), e.get("x"), e.get("y"), e.get("w"), e.get("h"),
                        fmt(f.get("color")), outl, fmt(e.get("vis_flag")), fmt(e.get("vis_when")),
                        e.get("visible_default"), fmt(e.get("action")) or "—",
                        ("%s/%s/%s" % (e.get("valign"), e.get("wrap"), e.get("max_lines"))
                         if e.get("kind") == "text" else "—"),
                        fmt(ass)))
        L.append("\n## 二、%s右栏四段布局（冻结 §B.4）\n" % ("改" if tag == "前" else "现"))
        L.append("| 段 | 件 | y 范围 | 说明 |")
        L.append("| --- | --- | --- | --- |")
        segs = ([("（改前无四段，各件按 PSB 原位）", "", "", "")] if tag == "前" else
                [("① 大播放窗", "`fc.play_win`(z6) ＋ `fc.play_view`(z7)", "214 – 514",
                  "380×300 居中于 443 栏宽 ⇒ x=1448；画面层内缩 6px＝368×288"),
                 ("② 标题", "`fc.p_title`(z6) ＋ `fc.p_title_tx`(z25)", "536 – 609",
                  "底 443×73 @1416；文字 419×40 @1428,546（valign:middle、不扩槽）"),
                 ("③ 说明", "`fc.p_text`(z6) ＋ `fc.p_text_tx`(z25)", "631 – 802",
                  "底 422×171 @1425；文字 398×159 @1437,637（top/wrap/**max_lines 4**——第 2 轮裁决：159÷33≈4.82）"),
                 ("④ 台词", "`fc.p_message`(z6) ＋ `fc.p_message_tx`(z25)", "824 – 995",
                  "底 422×171 @1425；文字 398×159 @1437,830（top/wrap/**max_lines 4**——同 ③）"),
                 ("栏底（保留）", "`fc.smallmap`(z5)", "190 – 1019", "443×829 @1416,190 **不动**"),
                 ("播放/暂停（同位置互斥）", "`fc.pbkick`(z20) / `fc.pbkick_pause`(z20) ＋ `fc.pbkick_hit`(z95)",
                  "301 – 426", "119×119 @1578,304（件中心 1637.5,363.5 ＝ 大播放窗中心）；热区 125×125 @1575,301")])
        for a, b, c, d in segs:
            L.append("| %s | %s | %s | %s |" % (a, b, c, d))
        io.open(os.path.join(EVID, "生成器改动_%s.md" % tag), "w", encoding="utf-8",
                newline="\n").write("\n".join(L) + "\n")

    # ── ③ 右栏元素_改后清单.tsv（全部 fc. 元素 ＋ 已删 12 件）──
    lines = ["#\tid\tkind\tz\tx\ty\tw\th\t关键字段\t本批状态\t说明"]
    _N = [0]

    def add(i, e, status, memo, pre=False):
        _N[0] += 1
        n = _N[0]
        if e is None:
            lines.append("%d\t%s\t—\t—\t—\t—\t—\t—\t—\t%s\t%s" % (n, i, status, memo))
            return
        k = []
        f = e.get("font") or {}
        if e.get("kind") == "text":
            k.append("font=%s/%s/%s" % (f.get("size"), f.get("bold"), f.get("color")))
            if f.get("outline"):
                k.append("outline=%sx%s" % (f.get("outline_color"), f.get("outline_width")))
            k.append("%s/%s/wrap=%s/max_lines=%s" % (e.get("align"), e.get("valign"),
                                                    e.get("wrap"), e.get("max_lines")))
            k.append("sample=%s" % (e.get("sample") or "")[:24].replace("\n", "⏎"))
        if e.get("asset") or e.get("dynamic"):
            k.append("asset=%s" % (e.get("asset") if e.get("asset") is not None else "null"))
        if e.get("dynamic"):
            k.append("dynamic=%s" % e["dynamic"])
        if e.get("state_assets"):
            k.append("state_assets=%s" % ",".join(sorted(
                "%s:%s" % (kk, vv.split("/")[-1]) for kk, vv in e["state_assets"].items())))
        if e.get("nine"):
            k.append("nine=l%st%sr%sb%s" % (e["nine"].get("l"), e["nine"].get("t"),
                                            e["nine"].get("r"), e["nine"].get("b")))
        if e.get("color"):
            k.append("color=%s" % e["color"])
        if e.get("opacity") is not None and e.get("kind") in ("rect", "image"):
            k.append("opacity=%s" % e.get("opacity"))
        if e.get("action") is not None and e.get("kind") == "hit":
            k.append("action=%r" % (e.get("action"),))
        if e.get("vis_flag"):
            k.append("vis_flag=%s:%s" % (e.get("vis_flag"), e.get("vis_when")))
        if e.get("visible_default") is False:
            k.append("visible_default=False")
        if e.get("flow_state"):
            k.append("flow_state=%s" % e["flow_state"])
        lines.append("%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
                     % (n, i, e.get("kind"), e.get("z"), e.get("x"), e.get("y"), e.get("w"),
                        e.get("h"), "; ".join(k), status, memo))

    for i in DELETED:
        add(i, before.get(i), "★已删除", "本批从 STATIC_ELEMENTS_JSON 删除（**素材文件保留**）")
    for i in sorted(before):                      # 其余改前静态件
        if i in DELETED or i in RIGHT_IDS:
            continue
        a = after.get(i)
        same = a is not None and {k: v for k, v in before[i].items() if k != "note"} == \
            {k: v for k, v in a.items() if k != "note"}
        add(i, a or before[i], "未动" if same else "（改前件）",
            "与改前逐字段相同" if same else "改前件")
    for i in ADDED:
        add(i, after.get(i), "★新增", "本批新增（冻结 §B.2）")
    for i in CHANGED:
        add(i, after.get(i), "★改动", "本批改动（冻结 §B.3）")
    # 右栏点名「保留不动」的栏底（冻结 §B.4）
    add("fc.smallmap", after.get("fc.smallmap"), "未动（保留）",
        "栏底保留不动（冻结 §B.4；`x`/`w`/`h` 与 PSB 原样）")
    # 其余全部 fc. 元素（生成物：图内容层）
    gen_ids = [k for k in after if not re.match(r"^(fc\.(dim|mtab|title|scroll|p_|pbk_|smallmap|mini|mapview|play_|scr_|zoom_|shift_|jump|fusen_|close|sysbar))", k)]
    for i in gen_ids:
        if i in ADDED or i in CHANGED or i in RIGHT_IDS:
            continue
        e = after[i]
        memo = "生成物（图内容层，本批未改）"
        if e.get("vis_flag") == "fc_layer":
            memo += "；带层旗标 `fc_layer`"
        add(i, e, "生成物", memo)
    io.open(os.path.join(EVID, "右栏元素_改后清单.tsv"), "w", encoding="utf-8",
            newline="\n").write("\n".join(lines) + "\n")
    print("written: 生成器改动_前.md / 生成器改动_后.md / 右栏元素_改后清单.tsv（%d 行）" % _N[0])
    print("静态件：改前 %d → 改后 %d（右栏件 %d → %d）"
          % (len(before), len(after),
             len([i for i in RIGHT_IDS if i in before]), len([i for i in RIGHT_IDS if i in after])))


if __name__ == "__main__":
    main()

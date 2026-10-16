# -*- coding: utf-8 -*-
r"""ISSUE-20260927-02 · F 组（backlog 三处遗留彻底收尾）· **幂等**改数据脚本。

只动 `layout\screens\26_backlog.json`：
  ① `bl.list.item_buttons[jump].y`   26 → 18      （上移 8px：胶囊可见体中线对到文案首行墨迹中线）
  ② `bl.list.item_buttons[replay].y` 18 → 10      （同簇同步上移 8px）
  ③ `bl.list.item_buttons[jump].x`   28 → 15      （回 PSB 口径 223−208；+13 前提已被行带件 alpha 实测否证）
  ④ `bl.list.item_buttons[replay].x` 154 → 141    （回 PSB 口径 349−208）
  ⑤ 四处 note **追加**本轮口径（屏级 / bl.list / jump / replay；**旧句一字不改**）

**不改**：item_h / gap / max_rows / item_text / item_frame / 滚动三件与 4 个热区 / labels / actions /
font / 机制字段（`%row%` 动作串、state_assets、nine 等一律原样）。

幂等：重跑时先判「四个数值是否已是目标态」与「四处 note 是否已带本轮标记」——
两者都满足则**一个字节都不写**（打印 no-op）；只缺 note 时只补 note。

断言：
  · 落盘前断言盘上数值 ∈ {旧值, 新值}（防止在第三者改过的文件上乱写）；
  · 旧值 / 新值必须**成组**出现（不接受「y 已新、x 仍旧」这类半吊子态）；
  · 关键锚点唯一性（`"key": "jump"` 后的 x/y、`"key": "replay"` 后的 x/y 各只出现一次）。

用法（在 UI 组根目录跑）：
    python _工作\ISSUE-20260927-02_backlog收尾\复现脚本\apply_f_backlog_finalize.py [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TARGET = os.path.join(UI, "layout", "screens", "26_backlog.json")
BACKUP = os.path.abspath(os.path.join(HERE, "..", "原形备份", "26_backlog.json"))

MARK = "F 组收尾（2026-09-27，ISSUE-20260927-02"

# ---------------------------------------------------------------- 数值改动
OLD = {"jump_x": 28, "jump_y": 26, "replay_x": 154, "replay_y": 18}
NEW = {"jump_x": 15, "jump_y": 18, "replay_x": 141, "replay_y": 10}

ANCHORS = {
    "jump":   ('"key": "jump"', r'"x": (\d+),', r'"y": (\d+),'),
    "replay": ('"key": "replay"', r'"x": (\d+),', r'"y": (\d+),'),
}

NOTES = {
    "screen": "**PSV 换皮",
    "list":   "回想消息块列表",
    "jump":   "跳转键",
    "replay": "重新播放键",
}

NOTE_RE = re.compile(r'"note": "((?:[^"\\]|\\.)*)"')     # 转义感知：正确取到整条 note 的字符串体


def note_body(s, which):
    """返回 (整段 match 对象, 字符串体)。锚点唯一性一并断言。"""
    hits = [m for m in NOTE_RE.finditer(s) if m.group(1).startswith(NOTES[which])]
    assert len(hits) == 1, "note 锚点异常（命中 %d 条）：%s" % (len(hits), which)
    return hits[0], hits[0].group(1)

APPEND = {
    "screen": (
        "\n★ **F 组收尾（2026-09-27，ISSUE-20260927-02 · 用户「需要你彻底收尾」）**：本屏 ①（按钮与文案"
        "视觉中线）与 ②（`item_buttons` x 回 PSB 口径，各 −13）已落地，见 `bl.list` 与两键 note。\n"
        "★ **③ 两端口径差（未决 · 需主代理裁决 · 本轮不得改 tjs / replica.js）**：同一枚「跳转」标签"
        "相对**胶囊可见体中心**的高度两端不同 —— **引擎高 6.0px**（标签文本元素由 "
        "`ui_widget.tjs::uiWidgetDrawList` 建：`valign:\"middle\"` + `h = b.h`；`ui_theme.tjs::uiThemeLayoutText` 的 "
        "`middle` 只把**行盒**（`blockH = 1 × lineH`）居中，`ui_theme.tjs::uiThemeRenderText` 再把字形墨迹画在"
        "**行盒顶端**）｜**HTML 高 3.0px**（`复刻/replica.js::buildList` 的 item_buttons 支：`lineHeight = 字号×行距` + "
        "`translateY(−(lineH−size)/2)` 半行距补偿后仍余约 3px；容器 `.ui-list-item-btn-label` 为 flex 居中）。"
        "两端差 **3px**，且两端都比胶囊中心高。**建议（供主代理裁决）**：① 若只求「两端一致」——**只改引擎一端**，"
        "`ui_widget.tjs::uiWidgetDrawList` 的 item_buttons 标签支把标签元素 `y` 由 `br.y` 增约 3px（两端同为「高 3px」）；"
        "② 若还要求「标签在胶囊内真正居中」——引擎 +6px（`ui_widget.tjs::uiWidgetDrawList`，同类见 "
        "`ui_widget.tjs::uiWidgetDrawHit` 的 `hit.label`，须一并评估），HTML 端再 +3px（`复刻/replica.js::buildList` 的 "
        "半行距补偿项）。**不要两端各改一半**（会二次漂移）。数值出处：上一轮实机 / HTML 导图量测 "
        "（`_工作\\ISSUE-20260927-01_backlog\\按钮漂移只读核查.txt` 第四节；本轮复核见 "
        "`_工作\\ISSUE-20260927-02_backlog收尾\\取证\\`）。"
    ),
    "list": (
        "\n★ **F 组收尾（2026-09-27，ISSUE-20260927-02 · 用户「需要你彻底收尾」）**：\n"
        "① **三件视觉中线（实机 `shot_29_backlog.png` 实测，canvas，四块逐一量）**：改动**前** —— 文案首行墨迹中线 "
        "**190.5 / 382.0 / 576.0 / 766.5** ｜「跳转」标签墨迹 **192.5 / 384.5 / 576.5 / 768.5** ｜ 胶囊可见体 "
        "**198.5 / 390.5 / 582.5 / 774.5**（口径 = 素材 `x_ui_jump_off.png` 的 alpha ≥ 128 行 6..23；宽口径 α≥8/64 为 "
        "198.0 / 390.0 / 582.0 / 774.0，见下）⇒ **文案与胶囊差 −8.0 / −8.5 / −6.5 / −8.0**（平均 −7.75）。"
        "改动**后**（两键 y 各 −8，其余字段一字未动）—— 文案 **190.5 / 382.0 / 576.0 / 766.5** ｜ 标签 "
        "**184.5 / 376.5 / 568.5 / 760.5** ｜ 胶囊 **190.5 / 382.5 / 574.5 / 766.5** ⇒ **文案与胶囊差 "
        "0.0 / −0.5 / +1.5 / 0.0（绝对最大 1.5px ≤ 2px ✓）**；改动前同为这四块，差为 "
        "−8.0 / −8.5 / −6.5 / −8.0（平均 −7.75）。行间 ±1.5px 抖动来自各块**首行字形不同**（墨迹 bbox 行数分别为 "
        "30 / 29 / 33 / 30），非位移误差。\n"
        "② **为什么按钮元素整体上移 8px（算式）**：`jump` 元素框 canvas y = 158 + 26 = 184（占行 184..212，坐标中线 198.5）；"
        "素材 `x_ui_jump_off.png` 52×29 且 `h = 素材高`（nine t7/b7 **纵向 1:1 不拉伸**）⇒ 素材第 k 行 = 元素第 k 行；"
        "实测 **alpha ≥ 128 的行 6..23 ⇒ canvas 190..207，中线 198.5 = 元素框坐标中线 198.5（偏置 0.0px）**；"
        "宽口径 alpha ≥ 8 的行 2..26（canvas 186..210，中线 198.0）与 α ≥ 64 的行 5..23（canvas 189..207，中线 198.0）"
        "则比框中线低 **0.5px** ⇒ **「可见体中心相对元素框中心」基本无偏置（0.0 ~ 0.5px）**。文案首行墨迹中线 "
        "190.5（行盒顶 177 + 墨迹行 176..205）⇒ 两者差 198.5 − 190.5 = **8.0px** ⇒ 元素整体上移 **8px**："
        "`jump.y 26 → 18`、`replay.y 18 → 10`（`replay` 为 1:1 件、无 nine，同步位移不再单独微调；其可见体中线 "
        "197.5 ⇒ 位移后 189.5 = 比文案墨迹线高 1.0px）。新矩形仍在块内（jump 18+29 = 47、replay 10+44 = 54 ≤ 188）"
        "⇒ 不触发出块守卫。\n"
        "③ **不可同时满足的一点（如实登记，未硬凑）**：**标签墨迹与胶囊可见体中心的差恒为 −6.0px**（四块实测逐一相同）"
        "—— 这是引擎侧固定行为（`ui_widget.tjs::uiWidgetDrawList` 建标签文本元素时 `valign:\"middle\"` + `h = b.h`；"
        "`ui_theme.tjs::uiThemeLayoutText` 的 `middle` 只把**行盒**（`blockH = 1 × lineH` = 28）居中 ⇒ 行盒顶 = 元素顶；"
        "`ui_theme.tjs::uiThemeRenderText` 把墨迹画在**行盒顶端**）⇒ **位移按钮元素会同时搬动胶囊与标签，该 6px 无法由 "
        "layout 数据消除**。故「三者差 ≤2px」在只动数据的口径下**物理不可达**；本轮取舍 = **让胶囊可见体中线与文案墨迹线"
        "重合**（对应用户原话「胶囊看着吊在下面」），把标签与胶囊的 6px 差交给 ③（两端口径差，需改一端代码，见屏级 note）。\n"
        "④ **x 回 PSB 口径**：`jump x 28 → 15`、`replay x 154 → 141`（各 −13）。自证：行带件 "
        "`ui/x_ui_psv_bklog_row.png`（1526×188）在 x = 0..13 逐列 **alpha 恒为 252（max = mean = 252）**、"
        "RGB 列均值与板中段（x=300/700/1200）一致（极差 < 1/255）⇒ **无横向透明 / 柔光 / 描边边**；旧卡件 "
        "`x_ui_msgblock.png` 的 x≈13 可见卡缘（中部横向 α = 25,28,…,72,217,218,255）是当年 +13 的唯一由来，该前提"
        "**已消失**（旧件保留不删，已不再被引用）。\n"
        "⑤ **本轮未动的字段**：`item_h 188` / `gap 4` / `max_rows 4` / `item_text`(219,19,1291×168) / `item_frame` / "
        "滚动三件与 4 个热区 / `labels` / `actions` / `font` / 机制字段（`%row%` 动作串、`state_assets`、`nine`）。"
    ),
    "jump": (
        "\n★ **F 组收尾（2026-09-27，ISSUE-20260927-02）· 本 note 前两句作废，以本段为准**：\n"
        "① **x 28 → 15**（回 PSB 口径 223−208）：原文「+13 形体修正」的前提已被实测否证 —— 现件 "
        "`ui/x_ui_psv_bklog_row.png` 在 x = 0..13 逐列 alpha 恒为 252（无横向透明/柔光边），旧卡件 "
        "`x_ui_msgblock.png` 的 x≈13 卡缘才是 +13 的由来；行带硬切至 x = 0 ⇒ 控件按 PSB 口径落 15 即「距行带左缘 15px」，"
        "不再需要形体修正。\n"
        "② **y 26 → 18**（上移 8px）：原文「与文本区首行中心(≈40)垂直居中」是**行盒口径**；PSV 轮把 `item_text.y` 由 10 "
        "改 19 后，实机量得胶囊可见体中心 198.5 比文案首行**墨迹**中线 190.5 低 8.0px。实测素材可见体中心相对元素框"
        "中心**无偏置**（`x_ui_jump_off.png` 52×29，α≥128 行 6..23 ⇒ 中心 14.5 = 框中心，且 h = 素材高 ⇒ 纵向 1:1 不拉伸）"
        "⇒ 元素整体上移 8px 后胶囊中线 = 文案首行墨迹中线（差 0.0px）。算式与四块数值见 `bl.list` note ①②。"
        "新矩形（块内局部）15,18,94×29：18+29 = 47 ≤ `item_h` 188，不触发出块守卫；与 replay（141,10,44×44）x 间距 33px。"
    ),
    "replay": (
        "\n★ **F 组收尾（2026-09-27，ISSUE-20260927-02）· 本 note 前两句作废，以本段为准**：\n"
        "① **x 154 → 141**（回 PSB 口径 349−208）：「+13 形体修正」的前提与 jump 条同因，已由行带件 "
        "`ui/x_ui_psv_bklog_row.png` 的横向 alpha 实测（x0..13 恒 252、无可见边）否证。\n"
        "② **y 18 → 10**（与 jump 同簇上移 8px）：实测 `x_ui_spk2_off.png`（44×44，α≥8 行 1..42 ⇒ 中心 21.5）比元素框中心 "
        "22.0 高 0.5px ⇒ 位移后图标可见体中线 189.5，比文案首行墨迹中线（190.5）高 1.0px，仍在 ≤2px 内；本键为纯图标键"
        "（无 label）⇒ 不涉 ③ 的标签口径差。新矩形（块内局部）141,10,44×44：10+44 = 54 ≤ 188，不触发出块守卫。"
    ),
}


def load():
    return io.open(TARGET, encoding="utf-8", newline="").read()


def save(s):
    io.open(TARGET, "w", encoding="utf-8", newline="").write(s)


def read_nums(s):
    out = {}
    for key, (ka, rx, ry) in ANCHORS.items():
        i = s.find(ka)
        assert i >= 0, "锚点缺失：" + ka
        assert s.count(ka) == 1, "锚点不唯一：" + ka
        mx = re.search(rx, s[i:i + 200])
        my = re.search(ry, s[i:i + 200])
        out[key + "_x"] = int(mx.group(1))
        out[key + "_y"] = int(my.group(1))
    return out


def sub_num(s, key, axis, old, new):
    ka = ANCHORS[key][0]
    i = s.find(ka)
    pat = ANCHORS[key][1 if axis == "x" else 2]
    m = re.search(pat, s[i:i + 200])
    a, b = i + m.start(), i + m.end()
    assert s[a:b] == '"%s": %d,' % (axis, old), "盘上值不是预设旧值：%r" % s[a:b]
    return s[:a] + '"%s": %d,' % (axis, new) + s[b:]


def inject_note(s, which, body):
    """在 `which` 那条 note 的**字符串体内末尾**追加 body（旧句一字不改）。

    落点算法：转义感知地匹配整条 note 字符串，**在该字符串的收尾引号前插入**。
    （不能假设 note 后面一定跟逗号 —— 对象最后一个键后面的分隔符是 `\\r\\n`，
      按 `'",'` 找收尾会把插入点落到下一个键的字符串里。）
    """
    m, seg = note_body(s, which)
    assert MARK not in seg, "note 已含本轮标记（幂等保护）：" + which
    return s[:m.end() - 1] + json.dumps(body, ensure_ascii=False)[1:-1] + s[m.end() - 1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    s0 = load()
    before_md5 = hashlib.md5(s0.encode("utf-8")).hexdigest()
    nums = read_nums(s0)
    print("盘上现值：", json.dumps(nums, ensure_ascii=False))
    print("备份 md5：%s（%s）" % (hashlib.md5(io.open(BACKUP, encoding="utf-8").read().encode("utf-8")).hexdigest(),
                              os.path.relpath(BACKUP, UI)))

    group_old = all(nums[k] == OLD[k] for k in OLD)
    group_new = all(nums[k] == NEW[k] for k in NEW)
    assert group_old or group_new, (
        "盘上数值既不是本轮旧值组也不是新值组（拒绝在他人改动上写入）：%s" % nums)

    notes_done = all(MARK in note_body(s0, w)[1] for w in NOTES)

    if group_new and notes_done:
        print("NO-OP：数值与四处 note 均已是本轮目标态，一个字节都不写。")
        return

    s = s0
    if group_old:
        for key in ("jump", "replay"):
            s = sub_num(s, key, "x", OLD[key + "_x"], NEW[key + "_x"])
            s = sub_num(s, key, "y", OLD[key + "_y"], NEW[key + "_y"])
        print("已改数值：jump (28,26) → (15,18)；replay (154,18) → (141,10)")
    else:
        print("数值已是新值组，仅补 note。")

    for w in ("screen", "list", "jump", "replay"):
        if MARK in note_body(s, w)[1]:
            print("  note[%s] 已带标记，跳过" % w)
            continue
        s = inject_note(s, w, APPEND[w])
        print("  note[%s] 已追加本轮口径" % w)

    # ---- 落盘前自证：解析 + 断言 ----
    d = json.loads(s)
    lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
    bj = [b for b in lst["item_buttons"] if b["key"] == "jump"][0]
    br = [b for b in lst["item_buttons"] if b["key"] == "replay"][0]
    assert (bj["x"], bj["y"]) == (NEW["jump_x"], NEW["jump_y"]), "jump 终值不符"
    assert (br["x"], br["y"]) == (NEW["replay_x"], NEW["replay_y"]), "replay 终值不符"
    for eid in ("bl.list",):
        pass
    # 未动字段核对
    assert lst["item_h"] == 188 and lst["gap"] == 4 and lst["max_rows"] == 4
    assert lst["item_text"] == {"x": 219, "y": 19, "w": 1291, "h": 168, "wrap": True,
                                "max_lines": 4, "align": "left", "valign": "top"}
    assert lst["item_frame"] == {"asset": "ui/x_ui_psv_bklog_row.png", "opacity": 150}
    assert bj["w"] == 94 and bj["h"] == 29 and bj["nine"] == {"l": 13, "t": 7, "r": 13, "b": 7}
    assert bj["action"] == "backlog_jump:%row%" and bj["label"] == "跳转"
    assert br["w"] == 44 and br["h"] == 44 and br["action"] == "backlog_replay:%row%"
    assert "nine" not in br and "label" not in br
    # 新矩形在块内、互不重叠、不压文案区
    assert bj["y"] + bj["h"] <= 188 and br["y"] + br["h"] <= 188
    assert bj["x"] + bj["w"] <= br["x"] and br["x"] + br["w"] < lst["item_text"]["x"]
    print("自证 PASS：终值 (jump %d,%d) (replay %d,%d)；item_h/gap/max_rows/item_text/item_frame/尺寸/动作/标签 均未变；"
          "两键在块内且互不重叠、不压文案区（文案左沿 %d）"
          % (bj["x"], bj["y"], br["x"], br["y"], lst["item_text"]["x"]))

    if a.dry_run:
        print("DRY-RUN：未写盘。")
        return
    save(s)
    after_md5 = hashlib.md5(load().encode("utf-8")).hexdigest()
    print("已落盘：%s" % os.path.relpath(TARGET, UI))
    print("md5 %s → %s（字节数 %d → %d；行数 %d → %d）"
          % (before_md5[:12], after_md5[:12], len(s0.encode("utf-8")), len(s.encode("utf-8")),
             s0.count("\r\n"), s.count("\r\n")))


if __name__ == "__main__":
    main()

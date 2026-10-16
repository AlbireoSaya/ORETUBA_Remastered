# -*- coding: utf-8 -*-
r"""ISSUE-20260927-01 · C 组（回想屏逐块文案 对齐 / 字号 / 位置）· **幂等**改数据脚本。

只动 `layout\screens\26_backlog.json` 里 `bl.list.item_text` 的**纵向位置**这一个字段
＋ 两处 note 的**追加**（旧句一字不改）：

    item_text.y : 10 → 19   （= 恢复 M06「块内按钮与文案首行中线齐平」的设计口径：
                             jump y26 / replay y18 即按首行中线 19 + 42/2 = 40.5 定；
                             19 + h168 = 187 ≤ item_h 188 ⇒ 不触发出块守卫、4 行容量不变）

**不改**：align（本就 left）、x（219）、w（1291）、h（168）、font / 行距、item_buttons、
item_h、gap、max_rows、滚动三件、热区、机制字段。

幂等：重跑先判当前是否已是目标态 —— 已是则**一个字节都不写**（打印 no-op）。
自证：改后重解析 JSON，并**逐路径**列出与改前的差异（断言只有 3 处：y + 两条 note）。

用法：
    python _工作\ISSUE-20260927-01_backlog\apply_c_backlog_text.py            # 落盘
    python _工作\ISSUE-20260927-01_backlog\apply_c_backlog_text.py --dry-run  # 只报差异
"""
import io, os, sys, json, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
TARGET = os.path.join(UI, "layout", "screens", "26_backlog.json")
BACKUP = os.path.join(HERE, "原形备份", "26_backlog.json")

ANCHOR_ITEMTEXT = '"item_text": {\n        "x": 219,\n        "y": 10,\n        "w": '
REPL_ITEMTEXT = '"item_text": {\n        "x": 219,\n        "y": 19,\n        "w": '

NOTE_ELEM_ANCHOR = '保留不删**）。",\n      "item_text": {'
NOTE_ELEM_V1 = (
    "保留不删**）。"
    "\\n★ **文字对齐 / 字号 / 位置复核（2026-09-27，ISSUE-20260927-01 · C 组）**："
    "① **对齐源 = `item_text.align`**（本屏取值 left）：两端消费**同一字段** —— "
    "krkr `ui_widget.tjs::uiWidgetItemText`（缺省链 `item_text.align` → `list.align` → left；`valign` 同理 → top）"
    "→ `ui_widget.tjs::uiWidgetDrawList` 的 item_text 支 → `ui_theme.tjs::uiThemeLayoutText` / `uiThemeRenderText`"
    "（按 align 逐行定位：left ⇒ `x = el.x`）；"
    "HTML `复刻/replica.js::buildList` 的 itemText 支（`labInner.style.textAlign = itemText.align || e.align || 'left'`、"
    "`lab.style.left = itemText.x`、行高 = `font.size × line_spacing`）。"
    "**未给 `item_text` 的旧标签路径**两端缺省都是 center（krkr 旧支 `align ?: center` ／ HTML `e.align || 'center'`）"
    "——那才是「每块按自身宽度居中、长短不一时左沿参差」的成因；本屏自 M06 起走 item_text 路径，不复现该现象。"
    "② **四块左沿实测一致（本轮未改）**：`item_text.x = 219` ⇒ 四块左沿恒为 `list.x + 219 = 388`，与文案长短无关；"
    "实机导图 `shot_29..45_backlog.png` 量得四块墨迹左沿 **389 / 389 / 389 / 389（极差 0px，+1px = 字形左侧留白）**，"
    "右沿 1116 / 1314 / 1440 / 1650 各异（⇒ 左对齐成立）。`align` / `x` / `w` 本轮**均未改**。"
    "③ **块内纵向位置（本轮唯一改动）**：`item_text.y` **10 → 19**。设计意图 = 块内两个按钮与**文案首行中线**齐平"
    "（`jump` y26、`replay` y18 即按「首行中线 ≈ 40」定，见各自 note；首行中线 = `y + floor(30×1.4)/2` ⇒ y ≈ 19.5）。"
    "PSV 换皮轮把 y 由 19 降到 10（h 173→168）而按钮未同步 ⇒ 按钮比首行低 9px；"
    "实机量得「首行墨迹中心 182 / 两按钮中心 198.5」差 **16.5px**（= 9px 回归 + 7.5px 行盒-墨迹固有差）。"
    "改回 19 后 `19 + 168 = 187 ≤ item_h 188`（不触发出块守卫），`max_lines=4` 容量不变。"
    "④ **字号 / 行距未改**：`font.size = 30`（继承 `bl.list.font`）、行距 = `fonts.line_spacing.body` = 1.4 "
    "⇒ `lineH = floor(30 × 1.4) = 42`、`4 × 42 = 168 = item_text.h`，与 M06 容量实测（真实语料 4 行 0 截断）同口径；"
    "PSV 轮加宽 `w` 1117→1291 只会**减少**所需行数。"
    "⑤ **残留（已上报，本轮不硬改）**：引擎 `uiThemeRenderText` 把字形墨迹画在**行盒顶端**（墨迹中心 ≈ `y + 15`），"
    "故「行盒中线对齐」后按钮与**墨迹**中心仍差约 7px；要彻底消除需把首行**墨迹**中心对到 40.5（`y ≈ 26.5`，超出行高 188）"
    "⇒ 必须同时动 `item_buttons` 或 `h/max_lines`，属主代理裁决项。"
    '",\n      "item_text": {'
)
# v2 = v1 ＋ 横向复核句（同上；⑥ 追加在⑤之后、仍在同一条 note 内）
NOTE_ELEM_ADD = NOTE_ELEM_V1.replace(
    "属主代理裁决项。",
    "属主代理裁决项。"
    "⑥ **横向对齐经用户原图复量确认无问题（用户 2026-09-27 截图，1282×752 游戏窗口图）**："
    "四行文案左沿 **canvas 390 / 390 / 390 / 392（极差 ≤3px；主代理量测 3px、本模块独立复量 2px，差值为字形左侧留白）**，"
    "与本模块对实机导图 `shot_29_backlog.png` 的实测（389 / 389 / 389 / 389，极差 0px）一致 "
    "⇒ **横向不存在对齐缺陷**；后续会话**不得**再据「四块按自身宽度居中、左沿参差」的旧描述去改 `align` / `x`（该描述已由主代理撤回）。"
    "同图独立复核的纵向结论一致：首行墨迹中线比「跳转」标签墨迹中线高 9.0–10.5px（本文 ③ 的同一现象，本轮已由 y 复位处置）。")

NOTE_SCREEN_ANCHOR = '原样。",\n  "elements"'
NOTE_SCREEN_V1 = (
    "原样。"
    "\\n★ **C 组复核（2026-09-27，ISSUE-20260927-01）**：逐块文案的**对齐 / 字号 / 位置**复核完成 —— "
    "横向对齐由 `item_text.align`（left）与 `item_text.x`（219）决定，四块实测左沿**一致（极差 0px）**；"
    "本轮唯一改动 = `item_text.y` **10 → 19**（恢复「块内按钮与文案首行中线齐平」的设计口径；19 + 168 ≤ item_h 188）。"
    "机制依据、两端行为、diff 范围与实机量测见 `bl.list` 的 note 与 `_工作\\\\ISSUE-20260927-01_backlog\\\\`。"
    '",\n  "elements"'
)
# v2 = v1 ＋ 用户在截图上圈注后的横向复核结论（主代理 2026-09-27 明确要求写进 note，
#      以免后续会话再按「四块按自身宽度居中」的**已撤回**描述去改横向）
NOTE_SCREEN_ADD = NOTE_SCREEN_V1.replace(
    "机制依据、两端行为、diff 范围与实机量测见 `bl.list` 的 note 与 `_工作\\\\ISSUE-20260927-01_backlog\\\\`。",
    "★ **横向已复量无问题（用户原图）**：四行文案左沿 canvas 极差 ≤3px（主代理量测 3px / 本模块独立复量 2px，差值 = 字形左侧留白）"
    "⇒ 横向对齐**无缺陷**；后续会话**不得**再据「四块按自身宽度居中、左沿参差」的旧描述去改 `align` / `x`（该描述已撤回）。"
    "★ 机制依据、两端行为、diff 范围与实机量测见 `bl.list` 的 note 与 `_工作\\\\ISSUE-20260927-01_backlog\\\\`。")


def load(p):
    """读为「\\n 归一」的文本；返回 (文本, 原文件换行符) —— 写回时必须还原同一换行符，
    否则整文件行尾会从 CRLF 变 LF（= 无谓的全文件 diff）。"""
    raw = io.open(p, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8").replace("\r\n", "\n"), eol


def diff_paths(a, b, path="$", out=None):
    """逐路径列出两棵 JSON 树的差异。"""
    if out is None:
        out = []
    if type(a) is not type(b):
        out.append((path, repr(a), repr(b)))
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((path + "." + k, "<缺>", "<新增>"))
            elif k not in b:
                out.append((path + "." + k, "<删除>", "<缺>"))
            else:
                diff_paths(a[k], b[k], path + "." + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path + ".length", len(a), len(b)))
        for i in range(min(len(a), len(b))):
            diff_paths(a[i], b[i], "%s[%d]" % (path, i), out)
    elif a != b:
        out.append((path, repr(a), repr(b)))
    return out


def plan(s):
    todo, out = [], s
    if ANCHOR_ITEMTEXT in out:
        out = out.replace(ANCHOR_ITEMTEXT, REPL_ITEMTEXT, 1)
        todo.append("item_text.y 10 -> 19")
    elif REPL_ITEMTEXT in out:
        todo.append("item_text.y 已是 19（跳过）")
    else:
        raise SystemExit("FAIL 找不到 item_text 的 y 锚点")
    # 元素 note：全新 → 写 v2；已是 v2 → 跳过；已是 v1 → 原位升级 v1→v2
    if NOTE_ELEM_ANCHOR in out:
        out = out.replace(NOTE_ELEM_ANCHOR, NOTE_ELEM_ADD, 1)
        todo.append("bl.list 元素 note 追加 C 组口径（v2）")
    elif "横向对齐经用户原图复量确认无问题" in out:
        todo.append("元素 note 已含横向复核句（跳过）")
    elif NOTE_ELEM_V1 in out:
        out = out.replace(NOTE_ELEM_V1, NOTE_ELEM_ADD, 1)
        todo.append("bl.list 元素 note 原地升级 v1 → v2（补 ⑥ 横向复核句）")
    else:
        raise SystemExit("FAIL 找不到元素 note 的锚点")
    # 屏级 note：同上
    if NOTE_SCREEN_ANCHOR in out:
        out = out.replace(NOTE_SCREEN_ANCHOR, NOTE_SCREEN_ADD, 1)
        todo.append("屏级 note 追加 C 组口径（v2）")
    elif "横向已复量无问题（用户原图）" in out:
        todo.append("屏级 note 已含横向复核句（跳过）")
    elif NOTE_SCREEN_V1 in out:
        out = out.replace(NOTE_SCREEN_V1, NOTE_SCREEN_ADD, 1)
        todo.append("屏级 note 原地升级 v1 → v2（补横向复核句）")
    else:
        raise SystemExit("FAIL 找不到屏级 note 的锚点")
    return out, todo


def main():
    dry = "--dry-run" in sys.argv
    s, eol = load(TARGET)
    out, todo = plan(s)
    print("原文件换行符 = %r（写回时逐字还原）" % eol)
    print("变更清单：")
    for t in todo:
        print("  -", t)
    if out == s:
        print("== 幂等 no-op：目标态已达成，未写盘 ==")
        return 0
    old, new = json.loads(s), json.loads(out)
    print("改后 JSON：解析通过")
    diffs = diff_paths(old, new)
    print("实测差异路径（共 %d 处）：" % len(diffs))
    for p, x, y in diffs:
        if p.endswith(".note"):
            print("  %s : note 追加 %d 字符" % (p, len(str(y)) - len(str(x))))
        else:
            print("  %s : %s -> %s" % (p, x, y))
    expect = {"$.note", "$.elements[2].note", "$.elements[2].item_text.y"}
    got = set(p for p, _, _ in diffs)
    assert got and got <= expect, "差异路径不符合预期：%s" % sorted(got)
    print("断言：差异必属 {item_text.y, bl.list.note, 屏级 note}（本次 %d 处）—— 其余字段逐字段未变"
          % len(diffs))
    body = out.replace("\n", eol).encode("utf-8")
    if not dry:
        if not os.path.exists(BACKUP):
            shutil.copyfile(TARGET, BACKUP)
            print("已留原形备份：", BACKUP)
        io.open(TARGET, "wb").write(body)
        raw_new = io.open(TARGET, "rb").read()
        assert raw_new == body, "写盘字节不一致"
        if eol == "\r\n":
            assert raw_new.count(b"\r\n") == raw_new.count(b"\n"), "行尾未还原为 CRLF"
        print("已写盘：%s（%d 字节；换行符 %r 已还原；行数 %d → %d）"
              % (TARGET, len(raw_new), eol,
                 io.open(BACKUP, "rb").read().count(b"\n"), raw_new.count(b"\n")))
    else:
        print("--dry-run：未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())

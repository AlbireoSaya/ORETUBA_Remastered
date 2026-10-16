# -*- coding: utf-8 -*-
"""
ISSUE-20260927-01 / 模块 D —— 选择支（choices）文字改「白字 + 黑色描边」· 复现脚本
================================================================================

背景（用户原话）：「选项的字体应该是白色+黑色描边，现在的方案根本看不清楚字。」
现状：`layout/screens/36_choices.json` 的 `ch.choices`（list）文字用
      `@palette.node_locked` = **#4A4A56 深灰**，无描边；压在 PSV 换皮后的
      深蓝/粉药丸条（`ui/x_ui_psv_choice_norm.png` / `_sel.png`）上，实测对比度 ≈1.3–1.9:1。

改动（唯一改动点 = 该 list 的 `font` 四个键）：
      color           @palette.node_locked (#4A4A56)  →  @palette.text_primary (#FFFFFF)
      outline         (无)                            →  true
      outline_color   (无)                            →  "#000000"
      outline_width   (无)                            →  2
      ⇒ **四个取值逐字照抄对话框先例**：`layout/screens/10_dialog.json` 的
        `dlg.text` / `dlg.name` / `dlg.choices`（同屏同参，未自创任何数值）。

用法（幂等；默认无参 = `--check`）：
      python m01_choices_text.py --apply     # 写入目标值（已是目标值则零改动）
      python m01_choices_text.py --check     # 只读断言：当前=目标值 + 与原形备份逐键 diff 范围
      python m01_choices_text.py --paths     # 只读断言：两端渲染路径确实消费 font.outline
      python m01_choices_text.py --measure   # 只读：从实机导图测对比度 + 出改后合成预览图
      python m01_choices_text.py             # = --check + --paths + --measure

★ 本脚本只写两处：目标屏 JSON，与自己的 `取证\\` 目录。
  不跑 gen_layout.py / verify_ui.py / 巡演（本 issue 4 模块并行，共享产物由主代理统一跑）。
★ 只写 `文件::函数名`，不写行号（本工程行号必漂移）。
"""

import argparse
import hashlib
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# 路径
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))          # …\复现脚本
WORK = os.path.dirname(HERE)                               # …\ISSUE-20260927-01_选择支
UIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # …\UI组
PROJ = os.path.abspath(os.path.join(UIG, "..", "..", ".."))   # …\临时\wt-qbicons

SCREEN = os.path.join(UIG, "layout", "screens", "36_choices.json")
PALETTE = os.path.join(UIG, "layout", "palette.json")
DIALOG = os.path.join(UIG, "layout", "screens", "10_dialog.json")
BACKUP = os.path.join(WORK, "原形备份", "36_choices.json")
EVID = os.path.join(WORK, "取证")
SHOTS = os.path.join(PROJ, "临时", "ui_run", "runtime", "savedata")

# 两端渲染路径（只写 `文件::函数名`，不写行号）
TJS_WIDGET = os.path.join(UIG, "krkr", "game", "ui_widget.tjs")
TJS_THEME = os.path.join(UIG, "krkr", "game", "ui_theme.tjs")
JS_REPLICA = os.path.join(UIG, "复刻", "replica.js")
GEN_LAYOUT = os.path.join(UIG, "工具", "gen_layout.py")

# 先例元素（照抄来源）
PRECEDENT = [("10_dialog.json", "dlg.text"), ("10_dialog.json", "dlg.name"),
             ("10_dialog.json", "dlg.choices")]

# ----------------------------------------------------------------------------
# 目标值（= 对话框先例）
# ----------------------------------------------------------------------------
TARGET_COLOR = "@palette.text_primary"
TARGET_OUTLINE = True
TARGET_OUTLINE_COLOR = "#000000"
TARGET_OUTLINE_WIDTH = 2

# 精确文本块（整块替换 ⇒ 其余字节零改动；缩进/键序照 dlg.* 先例）
OLD_FONT_BLOCK = (
    '      "font": {\r\n'
    '        "size": 44,\r\n'
    '        "bold": true,\r\n'
    '        "color": "@palette.node_locked",\r\n'
    '        "shadow": false,\r\n'
    '        "shadow_color": "@palette.shadow",\r\n'
    '        "shadow_ofs": 0\r\n'
    '      },'
)
NEW_FONT_BLOCK = (
    '      "font": {\r\n'
    '        "size": 44,\r\n'
    '        "bold": true,\r\n'
    '        "color": "@palette.text_primary",\r\n'
    '        "shadow": false,\r\n'
    '        "shadow_color": "@palette.shadow",\r\n'
    '        "shadow_ofs": 0,\r\n'
    '        "outline": true,\r\n'
    '        "outline_color": "#000000",\r\n'
    '        "outline_width": 2\r\n'
    '      },'
)

# note 追加段（旧句只追加不覆盖）。JSON 字符串内换行写作字面 `\n`（两个字符）。
_APPEND = (
    '\\n★ **ISSUE-20260927-01（2026-09-27 · 模块 D · 用户裁决）**：用户原话「选项的字体应该是白色+黑色描边，'
    '现在的方案根本看不清楚字。」⇒ 本 list 的文字色由「深灰 `@palette.node_locked`（#4A4A56）」改为'
    '「白 `@palette.text_primary`（#FFFFFF）」，并加 **8 向 2px 纯黑描边**（`font.outline:true` / '
    '`outline_color:\\"#000000\\"` / `outline_width:2`）。**四个取值逐字照抄对话框先例** '
    '`10_dialog.json` 的 `dlg.text` / `dlg.name` / `dlg.choices`（同屏同参），未自创任何数值。'
    '\\n  · **渲染路径（两端都已核，无需改引擎）**：本 list **未声明 `item_text`** ⇒ 走**逐项标签旧路径**——'
    'krkr `ui_widget.tjs::uiWidgetDrawList` 的旧标签分支 → `ui_theme.tjs::uiThemeApplyFont`（解析 '
    '`outline`/`outline_color`/`outline_width` 三键）→ `ui_theme.tjs::uiThemeDrawLine`（经 '
    '`uiThemeDrawOutline` 按 8 个方向先画描边、**最后画正文**）；'
    'HTML `复刻\\\\replica.js::buildList` 的旧标签分支 → `textShadowAll` → `textOutlineShadow`（8 条同序 '
    'text-shadow）。**逐项文本两端都消费 `font.outline`。**'
    '\\n  · **三态覆盖**：常态/悬停/按下共用同一套 `font`（三态只换 `item_frame.state_assets` 的**底图**，'
    '文字层不换）⇒ 一次改动同时覆盖三态。'
    '\\n  · **未动**：几何（x/y/w/h/item_h/gap/max_rows）、三态素材、热区、`item_frame`、`item_frame.state_assets`、'
    '`highlight`/`highlight_font_color`、`scroll`、`align`、`font.size`/`bold`/`shadow*` —— diff 范围自证见 '
    '`_工作\\\\ISSUE-20260927-01_选择支\\\\复现脚本\\\\m01_choices_text.py --check`。'
    '\\n  · 对比度量化与改后合成预览：`_工作\\\\ISSUE-20260927-01_选择支\\\\取证\\\\`。'
)


def read_raw(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def md5(b):
    return hashlib.md5(b).hexdigest()


def target_text_from(raw):
    """把 raw 里的 OLD 块换成 NEW 块（已是 NEW 则原样返回）。"""
    if NEW_FONT_BLOCK in raw:
        return raw
    if OLD_FONT_BLOCK not in raw:
        raise SystemExit("[FATAL] 既找不到旧 font 块，也找不到新 font 块 —— 数据已被改动，请人工核对")
    return raw.replace(OLD_FONT_BLOCK, NEW_FONT_BLOCK, 1)


def append_note(raw, anchor, tail):
    """在两处 note 的**最末尾**（最后一个句号之后、收尾引号之前）插入追加段；已追加则幂等返回。

    anchor = note 收尾若干字符（含最后一个句号）+ 收尾引号及其后的结构字符，用于定位且保证唯一；
    tail   = 收尾引号及其后的结构字符（不含最后那句）。
    ★ 必须**逐 note 判断幂等**（不能用「文件里出现过 ISSUE 号」当判据 —— 屏级 note 追加后，
      元素 note 会被误判为已完成而漏追加）。
    """
    done = '主代理**。' + _APPEND + tail
    if done in raw:
        return raw
    # ★ 幂等判定必须**限定在本 note 的区域内**（不能用「整份文件里出现过 ISSUE 号」——
    #   屏级 note 追加后，元素 note 会被误判为已完成而漏追加）
    idx = raw.find(anchor)
    if idx >= 0 and SENT in raw[max(0, idx - len(_APPEND) - 400): idx]:
        raise SystemExit("[FATAL] 本 note 已有 ISSUE-20260927-01 追加段但与当前脚本不一致 —— "
                         "请从 `原形备份\\36_choices.json` 重新开始，不得叠加追加")
    if idx < 0:
        raise SystemExit("[FATAL] note 锚点未找到：%r" % anchor[:60])
    return raw.replace(anchor, '主代理**。' + _APPEND + tail, 1)


TAIL_SCREEN = '\\n",\r\n  "elements": ['
TAIL_ELEM = '\\n"\r\n    }\r\n  ]\r\n}\r\n'
ANCHOR_SCREEN = '主代理**。' + TAIL_SCREEN
ANCHOR_ELEM = '主代理**。' + TAIL_ELEM
# 追加段唯一哨兵（每次追加恰好出现一次；用于逐 note 判定幂等与自证）
SENT = "★ **ISSUE-20260927-01（2026-09-27 · 模块 D · 用户裁决）**"


def rendered_text():
    raw = read_raw(SCREEN)
    out = target_text_from(raw)
    # ★ 不在此处前置断言锚点存在 —— 已追加过的文件锚点必然已消失，交由 append_note 逐 note 判定幂等
    out = append_note(out, ANCHOR_SCREEN, TAIL_SCREEN)
    out = append_note(out, ANCHOR_ELEM, TAIL_ELEM)
    # ★ 落盘前必须自证「仍是合法 JSON」，且两处 note 都已追加
    try:
        doc = json.loads(out)
    except Exception as ex:  # noqa: BLE001
        raise SystemExit("[FATAL] 渲染结果不是合法 JSON（note 追加段里多半有未转义的引号）：%s" % ex)
    assert doc["note"].count(SENT) == 1, "[FATAL] 屏级 note 追加段缺失或重复"
    assert doc["elements"][0]["note"].count(SENT) == 1, "[FATAL] 元素 note 追加段缺失或重复"
    assert doc["note"].rstrip().endswith("取证\\`。"), "[FATAL] 屏级 note 追加段不在末尾"
    return out


# ----------------------------------------------------------------------------
# --apply
# ----------------------------------------------------------------------------
def cmd_apply():
    raw = read_raw(SCREEN)
    out = rendered_text()
    if out == raw:
        print("[apply] 已是目标状态，零改动（幂等）md5=%s" % md5(raw.encode("utf-8")))
        return 0
    with open(SCREEN, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("[apply] 已写入 %s" % SCREEN)
    print("        md5 %s → %s" % (md5(raw.encode("utf-8")), md5(out.encode("utf-8"))))
    # 幂等自证：再渲染一次必须与落盘逐字节相同
    again = rendered_text()
    assert again == out, "[FATAL] 非幂等：二次渲染与首次不同"
    print("        [OK] 幂等自证：二次渲染与落盘逐字节相同")
    return 0


# ----------------------------------------------------------------------------
# --check
# ----------------------------------------------------------------------------
class _Missing(object):
    def __repr__(self):
        return "<missing>"


MISSING = _Missing()


def _diff_paths(a, b, p=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            key = (p + "." + k) if p else k
            out += _diff_paths(a.get(k, MISSING), b.get(k, MISSING), key)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((p + "[]", "len=%d" % len(a), "len=%d" % len(b)))
        else:
            for i in range(len(a)):
                out += _diff_paths(a[i], b[i], "%s[%d]" % (p, i))
    else:
        if a != b:
            out.append((p, a, b))          # ★ 保留**原值**（打印时才 repr）——
    return out                              #   否则「note 纯追加」的 startswith 判定会拿到 repr 串而恒假


ALLOW_EXACT = {
    "elements[0].font.color",
    "elements[0].font.outline",
    "elements[0].font.outline_color",
    "elements[0].font.outline_width",
}
ALLOW_PREFIX_EXTEND = {"elements[0].note", "note"}

FROZEN = [
    "id", "title_cn", "owner",
    "elements[0].id", "elements[0].kind", "elements[0].z", "elements[0].visible_default",
    "elements[0].orientation", "elements[0].x", "elements[0].y", "elements[0].w",
    "elements[0].item_h", "elements[0].gap", "elements[0].max_rows",
    "elements[0].labels", "elements[0].actions", "elements[0].align",
    "elements[0].item_frame", "elements[0].highlight", "elements[0].highlight_font_color",
    "elements[0].scroll", "elements[0].source",
    "elements[0].font.size", "elements[0].font.bold",
    "elements[0].font.shadow", "elements[0].font.shadow_color", "elements[0].font.shadow_ofs",
]


def _get(doc, path):
    cur = doc
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            cur = cur[int(part[1:-1])]
        else:
            cur = cur[part]
    return cur


def cmd_check():
    ok = True
    cur_raw = read_raw(SCREEN)
    bak_raw = read_raw(BACKUP)
    doc = json.loads(cur_raw)
    bak = json.loads(bak_raw)

    print("=" * 78)
    print("[check] 对比度修复 · diff 范围自证")
    print("=" * 78)
    print("  原形备份 md5 : %s" % md5(bak_raw.encode("utf-8")))
    print("  当前文件 md5 : %s" % md5(cur_raw.encode("utf-8")))

    el = doc["elements"][0]
    f = el["font"]
    print("\n  [目标值核对] ch.choices.font")
    checks = [("color", f.get("color"), TARGET_COLOR),
              ("outline", f.get("outline"), TARGET_OUTLINE),
              ("outline_color", f.get("outline_color"), TARGET_OUTLINE_COLOR),
              ("outline_width", f.get("outline_width"), TARGET_OUTLINE_WIDTH)]
    for k, got, want in checks:
        mark = "OK " if got == want else "FAIL"
        if got != want:
            ok = False
        print("    %s %-14s %r" % (mark, k, got))

    print("\n  [先例核对] 对话框同名字段（照抄来源）")
    dlg = json.load(open(DIALOG, encoding="utf-8"))
    byid = {e["id"]: e for e in dlg["elements"]}
    for fname, eid in PRECEDENT:
        df = byid[eid]["font"]
        same = (df.get("color") == TARGET_COLOR if eid != "dlg.name" else True)
        print("    %-16s color=%-22s outline=%s width=%s" %
              (eid, df.get("color"), df.get("outline"), df.get("outline_width")))

    print("\n  [diff 范围] 相对原形备份的全部差异键")
    diffs = _diff_paths(bak, doc)
    if not diffs:
        print("    （无差异 —— 未 apply）")
    bad = []
    for path, a, b in diffs:
        if path in ALLOW_EXACT:
            kind = "允许（font 渲染键）  %r → %r" % (a, b)
        elif path in ALLOW_PREFIX_EXTEND:
            prefix_ok = (isinstance(a, str) and isinstance(b, str)
                         and b.startswith(a) and SENT in b[len(a):])
            kind = "允许（note 纯追加，+%d 字符）" % (len(b) - len(a)) if prefix_ok \
                else "**不允许（非纯追加）** bak=%r cur_tail=%r" % (a[-30:], b[-60:])
            if not prefix_ok:
                bad.append(path)
        else:
            kind = "**不允许**  %r → %r" % (a, b)
            bad.append(path)
        print("    %-38s %s" % (path, kind))
    if bad:
        ok = False
        print("    [FAIL] 越界改动：%s" % bad)
    else:
        print("    [OK] 全部差异都落在 font 渲染键 / note 纯追加（几何与机制字段零改动）")

    print("\n  [冻结字段逐项比对] 几何 / 素材 / 机制")
    frozen_ok = True
    for path in FROZEN:
        try:
            a = _get(bak, path)
        except Exception:
            a = "<no-in-bak>"
        b = _get(doc, path)
        if a != b:
            frozen_ok = False
            ok = False
            print("    FAIL %-34s 备份=%r 当前=%r" % (path, a, b))
    print("    [%s] %d 项冻结字段" % ("OK" if frozen_ok else "FAIL", len(FROZEN)))

    print("\n  [元素数] %d（期望 1）" % len(doc["elements"]))
    if len(doc["elements"]) != 1:
        ok = False

    print("\n[check] %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ----------------------------------------------------------------------------
# --paths：两端渲染路径断言（结构检查，无行号）
# ----------------------------------------------------------------------------
def _func_body(src, name):
    """粗粒度取函数体：从 `function <name>(` 起到大括号配平为止。"""
    i = src.find("function " + name + "(")
    if i < 0:
        return None
    j = src.find("{", i)
    if j < 0:
        return None
    depth = 0
    for k in range(j, len(src)):
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
    return None


def cmd_paths():
    ok = True
    print("=" * 78)
    print("[paths] 文字渲染路径：逐项文本在两端是否消费 font.outline")
    print("=" * 78)

    tw = read_raw(TJS_WIDGET)
    tt = read_raw(TJS_THEME)
    rj = read_raw(JS_REPLICA)

    # --- krkr ①：uiWidgetDrawList 的旧标签分支存在，并且（a）不带 item_text 时走 else 分支
    dl = _func_body(tw, "uiWidgetDrawList")
    if dl is None:
        print("  FAIL krkr/ui_widget.tjs::uiWidgetDrawList 未找到"); return 1
    has_arg_apply = "uiThemeApplyFont(stage, fontSpec, el)" in dl
    has_drawline = "uiThemeDrawLine(stage, tx, ty, label, f, opa)" in dl
    print("  krkr 逐项标签旧路径 ui_widget.tjs::uiWidgetDrawList")
    print("    %s 调用 uiThemeApplyFont(stage, fontSpec, el)（取得含 outline 的 f）" % ("OK " if has_arg_apply else "FAIL"))
    print("    %s 调用 uiThemeDrawLine(stage, tx, ty, label, f, opa)（把 f 交给描边绘制）" % ("OK " if has_drawline else "FAIL"))
    ok &= has_arg_apply and has_drawline
    # 旧路径走 else（无 item_text）—— 本屏确实无 item_text
    cur = json.load(open(SCREEN, encoding="utf-8"))
    no_item_text = "item_text" not in cur["elements"][0]
    print("    %s 本屏 ch.choices 无 `item_text` ⇒ 走该旧标签分支" % ("OK " if no_item_text else "FAIL"))
    ok &= no_item_text

    # --- krkr ②：uiThemeApplyFont 解析三键
    af = _func_body(tt, "uiThemeApplyFont")
    keys = ["fontSpec.outline === true", "fontSpec.outline_color", "fontSpec.outline_width"]
    print("  krkr 字体解析 ui_theme.tjs::uiThemeApplyFont")
    for k in keys:
        hit = (af is not None) and (k in af)
        print("    %s 解析 %s" % ("OK " if hit else "FAIL", k))
        ok &= hit

    # --- krkr ③：uiThemeDrawLine 真画出描边
    dl2 = _func_body(tt, "uiThemeDrawLine")
    hit_outline = (dl2 is not None) and ("uiThemeDrawOutline(" in dl2)
    order_ok = hit_outline and dl2.find("uiThemeDrawOutline(") < dl2.find("layer.drawText(x, y, s, f.color")
    print("  krkr 绘制 ui_theme.tjs::uiThemeDrawLine")
    print("    %s 调用 uiThemeDrawOutline()（先描边）" % ("OK " if hit_outline else "FAIL"))
    print("    %s 正文 drawText 在其后（正文压在最上层）" % ("OK " if order_ok else "FAIL"))
    ok &= hit_outline and order_ok
    # 8 方向表
    dirs_ok = "UIThemeOutlineDirs" in tt and tt.count("0 - 1") >= 4
    print("    %s 方向表 UIThemeOutlineDirs（8 向，含对角线）" % ("OK " if dirs_ok else "FAIL"))
    ok &= dirs_ok

    # --- HTML ①：buildList 旧标签分支用 textShadowAll(listFont)
    bl = _func_body(rj, "buildList")
    rj_hit = (bl is not None) and ("textShadowAll(listFont)" in bl)
    print("  HTML 逐项标签旧路径 复刻/replica.js::buildList")
    print("    %s 旧标签分支调用 textShadowAll(listFont)" % ("OK " if rj_hit else "FAIL"))
    ok &= rj_hit
    # --- HTML ②：textShadowAll → textOutlineShadow 读三键
    tsa = _func_body(rj, "textShadowAll")
    tos = _func_body(rj, "textOutlineShadow")
    print("    %s textShadowAll 合成 textOutlineShadow" % ("OK " if (tsa and "textOutlineShadow(f)" in tsa) else "FAIL"))
    ok &= bool(tsa and "textOutlineShadow(f)" in tsa)
    keys2 = ["f.outline", "f.outline_width", "f.outline_color"]
    for k in keys2:
        hit = (tos is not None) and (k in tos)
        print("    %s textOutlineShadow 读 %s" % ("OK " if hit else "FAIL", k))
        ok &= hit
    dirs2_ok = (tos is not None) and ("[[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]]" in tos)
    print("    %s 方向表与 krkr 同序同向（8 条 text-shadow）" % ("OK " if dirs2_ok else "FAIL"))
    ok &= dirs2_ok

    # --- krkr ④：选中项「换字色」的浅拷贝必须带上描边三键（否则高亮项会丢描边）
    sc = _func_body(tw, "uiWidgetDictShallowCopy")
    print("  krkr 选中项换字色 ui_widget.tjs::uiWidgetDictShallowCopy / uiWidgetFontWithColor")
    for k in ("d.outline", "d.outline_color", "d.outline_width"):
        hit = (sc is not None) and (k in sc)
        print("    %s 逐键列举 %s（高亮项换色时不丢描边）" % ("OK " if hit else "FAIL", k))
        ok &= hit

    # --- 生成器透传：gen_layout.py 的 resolve_deep 是「键全透传」的递归实现，无 font 白名单
    gl = read_raw(GEN_LAYOUT)
    gen_ok = ("for k, v in node.items()" in gl) and ("resolve_deep(v, palette" in gl)
    print("  生成器透传 工具/gen_layout.py")
    print("    %s resolve_deep 逐键递归（新增 font 子键原样透传，无白名单会静默丢键）"
          % ("OK " if gen_ok else "FAIL"))
    ok &= gen_ok

    print("\n[paths] %s" % ("PASS —— 逐项文本两端都消费 font.outline，无需改引擎" if ok else "FAIL"))
    return 0 if ok else 1


# ----------------------------------------------------------------------------
# --measure：从实机导图测对比度 + 出改后合成预览
# ----------------------------------------------------------------------------
def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    r, g, b = (_srgb_to_lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _hex(colors, key):
    return colors[key]["value"]


def _pill_vs_text(path, item_rect, text_rgb, backdrop_rgb):
    """在实机导图上量：文字带内「药丸底（合成到 backdrop 后）的亮度」与文字色的对比度。

    药丸素材 alpha≈179（70%），故实际观感 = 0.702×丸色 + 0.298×底。
    返回 %[ ink_rows, ink_cells, bg_lum_min/max/med, contrast_before/after ]（局部坐标见 docstring）。
    """
    im = Image.open(path).convert("RGBA")
    px = im.load()
    x0, y0, w, h = item_rect
    tr, tg, tb = text_rgb
    # ① 找文字墨迹：改前文字色是精确不透明的 #4A4A56（实测逐像素命中）
    ink = {}
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            r, g, b, a = px[x, y]
            if a >= 250 and abs(r - tr) <= 1 and abs(g - tg) <= 1 and abs(b - tb) <= 1:
                ink[(x, y)] = True
    if not ink:
        return None
    ys = sorted({p[1] for p in ink})
    xs = sorted({p[0] for p in ink})
    ink_rows = (ys[0], ys[-1])
    ink_cols = (xs[0], xs[-1])
    # ② 药丸底：与墨迹**同一行**、但在 x 上取文字本地窗口（左右各 ≥150px、避开局端羽尖）
    #    并排除墨迹列 ±6（避开 AA 过渡）；丸体沿 x 恒定 ⇒ 同行的窗外像素即字形正下方的底色。
    win_lo = max(x0 + 20, ink_cols[0] - 260)
    win_hi = min(x0 + w - 20, ink_cols[1] + 260)
    bad_x = set(range(ink_cols[0] - 6, ink_cols[1] + 7))
    samples = []
    spread = []
    for y in range(ys[0], ys[-1] + 1):
        row = []
        for x in range(win_lo, win_hi + 1):
            if x in bad_x:
                continue
            r, g, b, a = px[x, y]
            if a < 100:
                continue
            af = a / 255.0
            eff = tuple(int(round(af * c + (1 - af) * bd)) for c, bd in zip((r, g, b), backdrop_rgb))
            row.append(eff)
            samples.append(eff)
        if row:
            lr = [_lum(c) for c in row]
            spread.append(max(lr) - min(lr))
    if not samples:
        return None
    lums = sorted(_lum(c) for c in samples)
    med = lums[len(lums) // 2]
    return {
        "path": os.path.basename(path),
        "ink_rows": ink_rows,
        "ink_cols": ink_cols,
        "ink_px": len(ink),
        "bg_n": len(samples),
        "bg_lum_min": lums[0],
        "bg_lum_max": lums[-1],
        "bg_lum_med": med,
        "bg_rgb_med": samples[len(samples) // 2],
        "bg_rgb_worst": samples[lums.index(max(lums))],
        "row_spread_max": max(spread) if spread else 0.0,
        "c_before": min(_contrast(text_rgb, samples[lums.index(med)]),
                        _contrast(text_rgb, samples[lums.index(max(lums))])),
        "c_after": min(_contrast((255, 255, 255), samples[lums.index(med)]),
                       _contrast((255, 255, 255), samples[lums.index(max(lums))])),
        "_samples": samples,
    }


def _synth_after(shot_path, item_rect, dst_path, text, font_src):
    """合成「改后」预览：把原墨迹按**逐行同色**精确回填丸底（丸体沿 x 恒定），
    再按引擎公式画 8 向 2px 黑描边 + 白字，并把新墨迹与原墨迹**逐像素对齐**。"""
    im = Image.open(shot_path).convert("RGBA")
    px = im.load()
    x0, y0, w, h = item_rect
    tr, tg, tb = 74, 74, 86
    ink = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)
           if px[x, y][3] >= 250 and abs(px[x, y][0] - tr) <= 1
           and abs(px[x, y][1] - tg) <= 1 and abs(px[x, y][2] - tb) <= 1]
    if not ink:
        return None
    # 逐行取一个「非墨迹」的药丸像素作为该行的底（丸体在 x 上恒定，实测成立）
    row_fill = {}
    for (x, y) in ink:
        if y not in row_fill:
            fx = None
            for cand in range(x0 + 5, x0 + w - 5, 3):
                r, g, b, a = px[cand, y]
                if a >= 100 and not (abs(r - tr) <= 1 and abs(g - tg) <= 1 and abs(b - tb) <= 1):
                    fx = (r, g, b, a)
                    break
            row_fill[y] = fx
    for (x, y) in ink:
        if row_fill[y]:
            px[x, y] = row_fill[y]
    # 渲染新文字：bold 微软雅黑 44（= 该 list 的 font.size/bold）
    half = 40
    tmp = Image.new("RGBA", (w + 2 * half, h + 2 * half), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    font = ImageFont.truetype(font_src, 44)
    d.text((half, half), text, font=font, fill=(255, 255, 255, 255), anchor="la")
    bb = tmp.getbbox()
    core = tmp.crop(bb)
    # 8 向描边层（2px），与 krkr uiThemeDrawOutline 的方向表逐项一致
    od = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    ring = Image.new("RGBA", core.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ring)
    ox, oy = half - bb[0], half - bb[1]
    for (dx, dy) in od:
        dr.text((ox + dx * 2, oy + dy * 2), text, font=font, fill=(0, 0, 0, 255), anchor="la")
    # 对齐：新墨迹的 alpha 包围盒左上 = 原墨迹包围盒左上
    ib = next(iter(ink))
    minx = min(p[0] for p in ink)
    miny = min(p[1] for p in ink)
    # core 的 alpha bbox（去掉透明边）已在 crop 时取得 ⇒ 左上即新墨迹左上
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    lay.paste(ring, (minx, miny), ring)
    lay.paste(core, (minx, miny), core)
    im.alpha_composite(lay)
    im.save(dst_path)
    return {"out": dst_path, "ink_px": len(ink)}


def cmd_measure():
    os.makedirs(EVID, exist_ok=True)
    doc = json.load(open(SCREEN, encoding="utf-8"))
    pal = json.load(open(PALETTE, encoding="utf-8"))
    colors = pal["colors"]
    el = doc["elements"][0]
    item_h, gap, x, y, w = el["item_h"], el["gap"], el["x"], el["y"], el["w"]
    n = len(el["labels"])
    rects = [(x, y + i * (item_h + gap), w, item_h) for i in range(n)]

    before_rgb = (0x4A, 0x4A, 0x56)          # @palette.node_locked（改前）
    assert _hex(colors, "node_locked").upper() == "#4A4A56", "palette.node_locked 变了"
    assert _hex(colors, "text_primary").upper() == "#FFFFFF", "palette.text_primary 变了"

    print("=" * 78)
    print("[measure] 文字 × 药丸底 对比度（实机导图取色）")
    print("=" * 78)
    print("  数据：x=%d y=%d w=%d item_h=%d gap=%d 项数=%d  字号=%s bold=%s" %
          (x, y, w, item_h, gap, n, el["font"]["size"], el["font"]["bold"]))
    print("  改前文字色 = @palette.node_locked %s = %s" % (_hex(colors, "node_locked"), before_rgb))
    print("  改后文字色 = @palette.text_primary %s = (255,255,255)" % _hex(colors, "text_primary"))
    print("  先例（照抄来源，10_dialog.json）")
    _dlg = json.load(open(DIALOG, encoding="utf-8"))
    _byid = {e["id"]: e for e in _dlg["elements"]}
    for _eid in ("dlg.text", "dlg.name", "dlg.choices"):
        _f = _byid.get(_eid, {}).get("font", {})
        print("      %-11s color=%-24s outline=%s color=%s width=%s" %
              (_eid, _f.get("color"), _f.get("outline"),
               _f.get("outline_color"), _f.get("outline_width")))

    cases = [
        ("常态 normal（蓝紫丸）", "shot_05_choices.png", 0),
        ("悬停 hover（粉丸）", "shot_06_choices.png", 1),
        ("按下 pressed（粉丸）", "shot_07_choices.png", 2),
        ("常态 normal（覆盖空转，复核）", "shot_09_choices.png", 0),
    ]
    results = {}
    for label, shot, idx in cases:
        p = os.path.join(SHOTS, shot)
        if not os.path.exists(p):
            print("  [SKIP] 缺实机导图 %s" % shot)
            continue
        # ★ 口径：choices 屏**自身无背景元素** ⇒ 实机导图该区为透明底；
        #   故在「黑底」与「白底」两个候选背景下各算一遍，并在结论里注明。
        r_black = _pill_vs_text(p, rects[idx], before_rgb, (0, 0, 0))
        r_white = _pill_vs_text(p, rects[idx], before_rgb, (255, 255, 255))
        if r_black is None:
            print("  [SKIP] %s 第 %d 项未找到墨迹" % (shot, idx))
            continue
        results[label] = (r_black, r_white)
        print("\n  ── %s ｜ %s 第 %d 项" % (label, shot, idx))
        print("     墨迹：行 y%d..%d  列 x%d..%d  命中 %d px" %
              (r_black["ink_rows"][0], r_black["ink_rows"][1],
               r_black["ink_cols"][0], r_black["ink_cols"][1], r_black["ink_px"]))
        print("     丸底（文字带内、x 窗 %d..%d 且排除墨迹列 ±6）采样 %d px，"
              "实测丸色中位 %s、最亮 %s，素材 alpha=179(70%%)；"
              "同行横向极差 ≤ %.4f（≈0 ⇒ 丸体沿 x 恒定，窗外像素即字形正下方色）" %
              (max(rects[idx][0] + 20, r_black["ink_cols"][0] - 260),
               min(rects[idx][0] + rects[idx][2] - 20, r_black["ink_cols"][1] + 260),
               r_black["bg_n"], r_black["bg_rgb_med"], r_black["bg_rgb_worst"],
               r_black["row_spread_max"]))
        for tag, r in (("黑底", r_black), ("白底", r_white)):
            print("       [%s] 合成后丸底亮度 L %.4f..%.4f（中位 %.4f）" %
                  (tag, r["bg_lum_min"], r["bg_lum_max"], r["bg_lum_med"]))
            print("            改前 文字#4A4A56 vs 丸底 = %5.2f:1（取最不利）" % r["c_before"])
            print("            改后 白字#FFFFFF vs 丸底 = %5.2f:1（取最不利）" % r["c_after"])
            if tag == "黑底":
                print("            描边#000000 vs 白字 = %5.2f:1（轮廓对比，与底色无关）" %
                      _contrast((0, 0, 0), (255, 255, 255)))
                print("            描边#000000 vs 丸底 = %5.2f:1" % _contrast((0, 0, 0), r["bg_rgb_worst"]))

    # ---- 改后合成预览（原墨迹逐行精确回填丸底，再画 8 向 2px 黑描边 + 白字）----
    print("\n  ── 改后合成预览（合成图，非实机）")
    font_src = r"C:\Windows\Fonts\msyhbd.ttc"
    if not os.path.exists(font_src):
        font_src = None
        print("     [WARN] 缺 msyhbd.ttc，跳过合成预览")
    sheets = []
    for label, shot, idx in cases:
        p = os.path.join(SHOTS, shot)
        if not os.path.exists(p) or font_src is None:
            continue
        crop = (rects[idx][0], rects[idx][1], rects[idx][0] + rects[idx][2], rects[idx][1] + rects[idx][3])
        bf = Image.open(p).convert("RGBA").crop(crop)
        dst = os.path.join(EVID, "after_synth_%s" % shot)
        _synth_after(p, rects[idx], dst, el["labels"][idx], font_src)
        af = Image.open(dst).convert("RGBA").crop(crop)
        pair = Image.new("RGBA", (crop[2], crop[3] * 2 + 6), (24, 24, 28, 255))
        pair.paste(bf, (0, 0), bf)
        pair.paste(af, (0, crop[3] + 6), af)
        sheets.append((label, pair))
        print("     %s → %s（上=改前实机，下=改后合成）" % (label, os.path.basename(dst)))
    if sheets:
        W = max(s.size[0] for _, s in sheets)
        H = sum(s.size[1] for _, s in sheets) + 8 * (len(sheets) - 1)
        sheet = Image.new("RGBA", (W, H), (16, 16, 20, 255))
        yy = 0
        for _, s in sheets:
            sheet.paste(s, (0, yy), s)
            yy += s.size[1] + 8
        outp = os.path.join(EVID, "sheet_choices_text_before_after.png")
        sheet.save(outp)
        print("\n     合并对照图 → %s" % outp)

    print("\n[measure] 完成（实机『改后』图须由主代理统一重跑巡演后复核）")
    return 0


# ----------------------------------------------------------------------------
# --mutate：变异自证（把机制/数据逐条打废，看守卫是否真报警；全在内存/临时副本，不碰磁盘真身）
# ----------------------------------------------------------------------------
def _run_quiet(fn):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn()
    return rc, buf.getvalue()


def cmd_mutate():
    global SCREEN, BACKUP, TJS_THEME
    os.makedirs(EVID, exist_ok=True)
    tmp = os.path.join(EVID, "_mut")
    os.makedirs(tmp, exist_ok=True)
    orig = (SCREEN, BACKUP, TJS_THEME)
    cases = []
    try:
        # M1 · 数据侧丢掉 font.outline ⇒ --check 的目标值核对必须 FAIL
        d = json.loads(read_raw(SCREEN))
        del d["elements"][0]["font"]["outline"]
        p1 = os.path.join(tmp, "m1_no_outline.json")
        with open(p1, "w", encoding="utf-8", newline="") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        SCREEN = p1
        rc, _ = _run_quiet(cmd_check)
        cases.append(("M1 数据缺 font.outline ⇒ check 必须 FAIL", rc != 0))

        # M2 · 原形备份被改几何 ⇒ diff 范围守卫必须 FAIL
        SCREEN = orig[0]
        b = json.loads(read_raw(BACKUP))
        b["elements"][0]["item_h"] = 999
        p2 = os.path.join(tmp, "m2_geom_backup.json")
        with open(p2, "w", encoding="utf-8", newline="") as f:
            json.dump(b, f, ensure_ascii=False, indent=2)
        BACKUP = p2
        rc, _ = _run_quiet(cmd_check)
        cases.append(("M2 备份几何被改 ⇒ diff 范围守卫必须 FAIL", rc != 0))

        # M3 · 把引擎描边调用整条打废 ⇒ --paths 必须 FAIL
        BACKUP = orig[1]
        t = read_raw(TJS_THEME).replace("uiThemeDrawOutline(layer, x, y, s, f, opa);", "0;")
        assert t != read_raw(TJS_THEME), "M3 变异锚点未命中"
        p3 = os.path.join(tmp, "m3_theme.tjs")
        with open(p3, "w", encoding="utf-8", newline="") as f:
            f.write(t)
        TJS_THEME = p3
        rc, _ = _run_quiet(cmd_paths)
        cases.append(("M3 引擎 uiThemeDrawOutline 调用被打废 ⇒ paths 必须 FAIL", rc != 0))

        # M4 · 数据带上 item_text ⇒ 「走逐项标签旧路径」断言必须 FAIL
        TJS_THEME = orig[2]
        d2 = json.loads(read_raw(SCREEN))
        d2["elements"][0]["item_text"] = {"x": 1, "y": 1, "w": 10, "h": 10}
        p4 = os.path.join(tmp, "m4_item_text.json")
        with open(p4, "w", encoding="utf-8", newline="") as f:
            json.dump(d2, f, ensure_ascii=False, indent=2)
        SCREEN = p4
        rc, _ = _run_quiet(cmd_paths)
        cases.append(("M4 数据带 item_text ⇒ 渲染路径断言必须 FAIL", rc != 0))
    finally:
        SCREEN, BACKUP, TJS_THEME = orig

    print("=" * 78)
    print("[mutate] 变异自证（每条都必须报警，否则说明守卫没覆盖）")
    print("=" * 78)
    bad = 0
    for name, fired in cases:
        print("    %s %s" % ("OK  " if fired else "FAIL", name))
        if not fired:
            bad += 1
    print("\n[mutate] %s（%d/%d 报警）" %
          ("PASS" if bad == 0 else "FAIL", len(cases) - bad, len(cases)))
    return 1 if bad else 0


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--paths", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()
    if a.apply:
        return cmd_apply()
    if not (a.check or a.paths or a.measure or a.mutate):
        a.check = a.paths = a.measure = a.mutate = True
    rc = 0
    if a.check:
        rc |= cmd_check()
        print()
    if a.paths:
        rc |= cmd_paths()
        print()
    if a.mutate:
        rc |= cmd_mutate()
        print()
    if a.measure:
        rc |= cmd_measure()
    return rc


if __name__ == "__main__":
    sys.exit(main())

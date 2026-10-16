# -*- coding: utf-8 -*-
"""UI 布局生成器（UI 组 · ISSUE-20260919-11）

单一数据源 -> 三处产物：
    layout/screens/*.json + layout/palette.json
        -> layout/ui_layout.json     人读 + 机器读（合并结果）
        -> krkr/game/ui_layout.tjs   krkr 侧（TJS2 Dictionary 字面量）
        -> 复刻/ui_layout.js          HTML 复刻侧（window.UI_LAYOUT）

用法：
    cd "工程\\我们没有翅膀——格雷塔迦露德与柳木原\\UI组\\工具"
    python gen_layout.py [--check-only]

设计约束（与 layout/_schema.md 一致）：
    * 元素 id 全局唯一；
    * "@palette.<key>" 必须能在 palette.json 中解析；
    * kind=image 且带 nine 时，w/h 必须 >= 九宫格左右/上下边距之和；
    * 未写 z 的元素按声明顺序自动编号（从该屏起点续号）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)                       # …/UI组
LAYOUT = os.path.join(UI, "layout")
SCREENS = os.path.join(LAYOUT, "screens")
KRKR_GAME = os.path.join(UI, "krkr", "game")
REPLICA = os.path.join(UI, "复刻")

PAL_RE = re.compile(r"^@palette\.([A-Za-z0-9_.]+)$")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 色板 ──────────────────────────────────────────────────────────────
def load_palette():
    raw = load_json(os.path.join(LAYOUT, "palette.json"))
    colors = raw["colors"]
    out = {}
    for k, v in colors.items():
        out[k] = v["value"]
    return out


def resolve(value, palette, where):
    """把 "@palette.x" 解析为实际值；非引用值原样返回。"""
    if isinstance(value, str):
        m = PAL_RE.match(value)
        if m:
            key = m.group(1)
            if key not in palette:
                raise SystemExit("[FAIL] %s 引用了不存在的色板键：%s" % (where, key))
            return palette[key]
    return value


def resolve_deep(node, palette, where):
    if isinstance(node, dict):
        return {k: resolve_deep(v, palette, where + "." + k) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_deep(v, palette, where + "[%d]" % i) for i, v in enumerate(node)]
    return resolve(node, palette, where)


# ── 校验 ──────────────────────────────────────────────────────────────
def validate(screen, path):
    errs = []
    sid = screen.get("id")
    if not sid:
        errs.append("%s: 缺 id" % path)
    seen = set()
    z = 0
    for el in screen.get("elements", []):
        eid = el.get("id")
        if not eid:
            errs.append("%s: 元素缺 id" % path)
            continue
        if eid in seen:
            errs.append("%s: 元素 id 重复：%s" % (path, eid))
        seen.add(eid)
        if "z" not in el:
            el["z"] = z
        z = max(z, int(el.get("z", 0))) + 1
        if el.get("kind") == "image":
            nine = el.get("nine")
            if nine:
                if el.get("w", 0) < nine.get("l", 0) + nine.get("r", 0):
                    errs.append("%s/%s: w=%s 小于九宫格左右边距和 %s"
                                % (path, eid, el.get("w"), nine.get("l", 0) + nine.get("r", 0)))
                if el.get("h", 0) < nine.get("t", 0) + nine.get("b", 0):
                    errs.append("%s/%s: h=%s 小于九宫格上下边距和 %s"
                                % (path, eid, el.get("h"), nine.get("t", 0) + nine.get("b", 0)))
        if el.get("kind") == "list":
            labels, actions = el.get("labels", []), el.get("actions", [])
            if len(labels) != len(actions):
                errs.append("%s/%s: labels(%d) 与 actions(%d) 长度不等"
                            % (path, eid, len(labels), len(actions)))
        if el.get("kind") in ("image", "list") and not el.get("source") and not el.get("dynamic"):
            errs.append("%s/%s: 缺 source（素材溯源路径）" % (path, eid))
    return errs


# ── 输出 ──────────────────────────────────────────────────────────────
def hex_to_tjs_int(v):
    if isinstance(v, str) and v.startswith("#") and len(v) == 7:
        return int(v[1:], 16)
    return v


def tjs_escape(s):
    """TJS2 双引号字符串字面量的转义（键与值共用同一把尺，避免只转义值）。"""
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def tjs_literal(node, indent=0):
    pad = "  " * indent
    if isinstance(node, dict):
        if not node:
            return "%[]"
        items = []
        for k, v in node.items():
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)):
                items.append("%s  %s: %s" % (pad, k, tjs_literal(v, indent + 1)))
            else:
                # TJS2 内联字典的键只有两条产生式（tjs2/syntax/tjs.y 的 dic_elm）：
                # `T_SYMBOL ":" expr`（裸标识符键）或 `expr_no_comma "," expr`（逗号式）。
                # 带引号的 `"k": v` **是语法错误**——execStorage 时整份 ui_layout.tjs
                # 直接 FATAL（`语法有误 （syntax error）`），屏级 flags_default 带点键
                # （如 `fc.state.0001`）曾因此让 --preset states 装载失败。
                # ★ 键与值同样转义（一审 F-4）：否则含 `"` 的键会发射非法 TJS，
                #   而 assert_no_quoted_dict_keys 的判据认不出这种形态 ⇒ 漏网。
                items.append('%s  "%s", %s' % (pad, tjs_escape(k), tjs_literal(v, indent + 1)))
        return "%[\n" + ",\n".join(items) + "\n" + pad + "]"
    if isinstance(node, list):
        return "[" + ", ".join(tjs_literal(v, indent) for v in node) + "]"
    if isinstance(node, bool):
        return "true" if node else "false"
    if node is None:
        return "void"
    if isinstance(node, str):
        return '"%s"' % tjs_escape(node)
    return str(node)


def assert_no_quoted_dict_keys(text):
    """落盘前自检：TJS2 内联字典**不接受**带引号的键（`"k": v` ⇒ 语法错误）。

    判据只认「行首（缩进后）一个未转义的双引号 + 引号内内容 + 冒号」——
    值里的引号都被 tjs_literal 转义成 \\" ，且不在行首，故不会误判。
    违反即抛错 ⇒ main 不写任何产物（三处保持一致，不会出现「json 已写、tjs 炸」）。
    """
    for i, line in enumerate(text.split("\n"), 1):
        if re.match(r'^\s*"(?:[^"\\]|\\.)*"\s*:', line):
            raise AssertionError(
                "ui_layout.tjs 第 %d 行出现非法字典键（TJS2 不接受 \"k\": v，"
                "须写裸标识符 `k: v` 或逗号式 `\"k\", v`）：%s" % (i, line.strip()))
    return True


def to_tjs(tree):
    def conv(node):
        if isinstance(node, dict):
            return {k: conv(v) for k, v in node.items()}
        if isinstance(node, list):
            return [conv(v) for v in node]
        return hex_to_tjs_int(node)

    body = tjs_literal(conv(tree), 0)
    assert_no_quoted_dict_keys(body)
    return (
        "// ============================================================\n"
        "// ui_layout.tjs —— 【自动生成，禁止手改】\n"
        "// 来源：UI组/layout/screens/*.json + layout/palette.json\n"
        "// 生成器：UI组/工具/gen_layout.py\n"
        "// 改动布局请改 screens/*.json 后重跑生成器。\n"
        "// ============================================================\n"
        "var UILayoutData = " + body + ";\n"
    )


def to_js(tree):
    return (
        "// ============================================================\n"
        "// ui_layout.js —— 【自动生成，禁止手改】\n"
        "// 来源：UI组/layout/screens/*.json + layout/palette.json\n"
        "// 生成器：UI组/工具/gen_layout.py\n"
        "// ============================================================\n"
        "window.UI_LAYOUT = " + json.dumps(tree, ensure_ascii=False, indent=2) + ";\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    palette = load_palette()
    index = load_json(os.path.join(SCREENS, "_index.json"))
    root_meta = load_json(os.path.join(LAYOUT, "_root.json"))

    tree = dict(root_meta)
    tree["palette"] = {k: v for k, v in palette.items()}
    tree["screens"] = {}

    errs = []
    for entry in index["screens"]:
        path = os.path.join(SCREENS, entry["file"])
        if not os.path.exists(path):
            errs.append("[未产出] %s（%s，归属 %s）—— 若该模块尚未开工属正常，开工后须补齐"
                        % (entry["file"], entry["title_cn"], entry["owner"]))
            continue
        screen = load_json(path)
        if screen.get("id") != entry["id"]:
            errs.append("%s: id 与 _index.json 不一致（文件 %s / 索引 %s）"
                        % (entry["file"], screen.get("id"), entry["id"]))
        errs += validate(screen, entry["file"])
        tree["screens"][entry["id"]] = resolve_deep(screen, palette, entry["id"])

    hard = [e for e in errs if not e.startswith("[未产出]")]
    for e in errs:
        print(("  ! " if not e.startswith("[未产出]") else "  - ") + e)

    if hard:
        print("\n[FAIL] 硬错误 %d 条，未生成。" % len(hard))
        return 1
    if args.check_only:
        print("\n[OK] --check-only 通过（%d 屏已产出）" % len(tree["screens"]))
        return 0

    os.makedirs(KRKR_GAME, exist_ok=True)
    os.makedirs(REPLICA, exist_ok=True)

    # 三处产物**先全部算出再落盘**：任何一处自检失败都不得留下半套（三处一致铁律）。
    merged_text = json.dumps(tree, ensure_ascii=False, indent=2)
    tjs_text = to_tjs(tree)
    js_text = to_js(tree)

    merged = os.path.join(LAYOUT, "ui_layout.json")
    with open(merged, "w", encoding="utf-8") as f:
        f.write(merged_text)
    with open(os.path.join(KRKR_GAME, "ui_layout.tjs"), "w", encoding="utf-8") as f:
        f.write(tjs_text)
    with open(os.path.join(REPLICA, "ui_layout.js"), "w", encoding="utf-8") as f:
        f.write(js_text)

    print("\n[OK] 已生成：")
    print("  %s  (%d 屏)" % (os.path.relpath(merged, UI), len(tree["screens"])))
    print("  %s" % os.path.relpath(os.path.join(KRKR_GAME, "ui_layout.tjs"), UI))
    print("  %s" % os.path.relpath(os.path.join(REPLICA, "ui_layout.js"), UI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
# -*- coding: utf-8 -*-
r"""m05_entry_hit_layer_scope.py —— ★ 第 4 批（裁决 4）机检自证：**入口热区的作用域闭环**

判据（对**五个屏预设**逐一实跑复算，不是只看交付样例）：

    「存在 `fc.entry.<NNNN>_hit` ⇒ 其 `layer` 指向的独立层**在本预设内确有元素**」
      且「每个已产出的独立层 ⇒ 既有入口热区（进得去）、又有按组返回键（回得来）」。

即：入口热区**只在「该组的独立层确实产出」时才产** —— 否则点一下会切到**未产层** ⇒
屏面变空且回不来（HTML 实测 `_工作\ISSUE-20260928-02_HTML\证据\E3_screen1_entry点击后.png`）。

背景（第 4 批要修的口径）：上一批除 `screen1` 外的档（`screen2`/`ref150`/`states` 无独立层、
`frag` 只有第 1 组）也照产 6 个 `fc.entry.*_hit`，各自指向**未产出的层** ⇒ 演示档是坑。

本脚本：
  · 逐预设实跑 `gen_flow_layout.py --preset <p> --out _out/32_flowchart.<p>.json`（**只写 `_out/`**，不动屏文件）；
  · 逐预设列出：预设 / 产出的入口热区数 / 各自 `layer` / 该 `layer` 对应的层内元素数；
  · 硬断言上面两条判据（任一预设违反 ⇒ 退出码 1）；
  · `screen1` 另断言 **6/6**；
  · **反向自证**：把一份内存副本注入一个指向 `frag9`（该档未产）的热区 ⇒ 判定函数必须报错
    （证明这套检查**不是恒真**）。

幂等：只写 `_out/`（可覆盖再生）；不落任何屏文件、不改任何输入。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
OUT = os.path.join(HERE, "_out")
PY = sys.executable

PRESETS = ("screen1", "screen2", "ref150", "states", "frag")
# 每个预设**应当**产出的独立层（= `PRESETS[p]["frag_groups"]`；写死在自证里＝独立于生成器参数，
# 免得「生成器改了口径、自证跟着一起改」这同一种恒真陷阱）。
EXPECT_LAYERS = {
    "screen1": ["frag1", "frag2", "frag3", "frag4", "frag5", "frag6"],
    "screen2": [],
    "ref150": [],
    "states": [],
    "frag": ["frag1"],
}
LAYER_FLAG = "fc_layer"

FAILS = []


def bad(msg):
    FAILS.append(msg)
    print("    ✗ %s" % msg)


def gen(preset):
    out = os.path.join(OUT, "32_flowchart.%s.json" % preset)
    r = subprocess.run([PY, os.path.join(UI, "工具", "gen_flow_layout.py"),
                        "--preset", preset, "--out", out],
                       cwd=UI, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[FAIL] 生成预设 %s 失败：%s" % (preset, (r.stderr or r.stdout)[-400:]))
    return json.load(open(out, encoding="utf-8"))


def produced_layers(els):
    """本屏**实际产出**的独立层（取值来自 `fc_layer` 的 `vis_when` 且形如 `frag<G>`）。"""
    return sorted({e.get("vis_when") for e in els
                   if e.get("vis_flag") == LAYER_FLAG
                   and str(e.get("vis_when", "")).startswith("frag")})


def layer_elem_count(els, layer):
    """该层在本屏内的元素数（同层旗标 + 同 `vis_when`）。"""
    return sum(1 for e in els
               if e.get("vis_flag") == LAYER_FLAG and e.get("vis_when") == layer)


def entry_hits(els):
    return [e for e in els
            if e["id"].startswith("fc.entry.") and e["id"].endswith("_hit")]


def check_screen(scr):
    """返回问题清单（空 = 通过）。**纯函数**，供反向自证对内存副本调用。"""
    els = scr["elements"]
    prods = produced_layers(els)
    hits = entry_hits(els)
    problems = []
    # ① 存在热区 ⇒ 其 layer 在本屏确有元素（裁决 4 的核心）
    for h in hits:
        lg = h.get("layer")
        if lg not in prods or layer_elem_count(els, lg) == 0:
            problems.append("%s 的 layer=%r 在屏内**无元素**（点进去屏面为空且回不来）"
                            % (h["id"], lg))
    # ② 每个已产层 ⇒ 进得去（有入口热区）+ 回得来（有按组返回键）
    for lg in prods:
        if not any(h.get("layer") == lg for h in hits):
            problems.append("独立层 %s 已产出但**无入口热区**（去不了）" % lg)
        back = "fc.%s_back_hit" % lg
        if not any(e["id"] == back and e.get("action") == "flow_layer"
                   and e.get("layer") == "main" for e in els):
            problems.append("独立层 %s 有入口但缺按组返回键 %s（进得去回不来）" % (lg, back))
    return problems


def main():
    print("=" * 78)
    print("m05 · 入口热区作用域闭环自证（裁决 4：热区只在「该组独立层确实产出」时才产）")
    print("=" * 78)
    print("  预设 / 产出的入口热区数 / 各自 layer / 对应层元素数")
    print("-" * 78)
    rows = []
    for preset in PRESETS:
        scr = gen(preset)
        els = scr["elements"]
        prods = produced_layers(els)
        hits = entry_hits(els)
        detail = []
        for h in hits:
            lg = h.get("layer")
            detail.append("%s→%s(%d 件)" % ((str(h["id"]).replace("fc.entry.", "").replace("_hit", "")),
                                            lg, layer_elem_count(els, lg)))
        rows.append((preset, len(els), len(hits), prods, detail))
        print("  %-8s 元素 %3d ｜ 入口热区 %d 个 ｜ 产出层 %-32s ｜ %s"
              % (preset, len(els), len(hits),
                 str(prods) if prods else "（无）",
                 "；".join(detail) if detail else "（无热区）"))

    print("-" * 78)
    # 逐预设跑硬判据（读 `_out/` 里刚落盘的产物；目录已含本轮实跑值）
    for preset in PRESETS:
        scr = json.load(open(os.path.join(OUT, "32_flowchart.%s.json" % preset), encoding="utf-8"))
        probs = check_screen(scr)
        exp = EXPECT_LAYERS[preset]
        got = produced_layers(scr["elements"])
        if got != exp:
            probs = probs + ["产出层 %s ≠ 自证期望 %s（口径漂移）" % (got, exp)]
        print("  %-8s 产出层 %-34s 入口热区 %d ｜ 判据：%s"
              % (preset, str(got) if got else "（无）", len(entry_hits(scr["elements"])),
                 "✓ 通过" if not probs else "✗ %s" % probs))
        for p in probs:
            bad("%s：%s" % (preset, p))

    # ★ 交付样例必须 6/6
    s1 = json.load(open(os.path.join(OUT, "32_flowchart.screen1.json"), encoding="utf-8"))
    n1 = len(entry_hits(s1["elements"]))
    print("-" * 78)
    print("  交付样例 screen1 入口热区 **%d/6** %s" % (n1, "✓" if n1 == 6 else "✗（应为 6）"))
    if n1 != 6:
        bad("交付样例 screen1 应有 6 个入口热区，实为 %d" % n1)

    # ── 反向自证：这套检查不是恒真 ─────────────────────────────────────
    print("\n【反向自证 · 变异必须被拦下】")
    import copy
    mut = copy.deepcopy(s1)
    mut["elements"].append({
        "id": "fc.entry.0099_hit", "kind": "hit", "z": 95, "visible_default": True,
        "x": 100, "y": 100, "w": 100, "h": 60,
        "action": "flow_layer", "layer": "frag9", "label": "",
        "vis_flag": LAYER_FLAG, "vis_when": "main",
    })
    mprobs = check_screen(mut)
    print("  变异A（注入 layer=frag9 的悬空热区）：报错 %d 条 ⇒ %s"
          % (len(mprobs), "✓ 被拦下" if mprobs else "✗ 恒真！"))
    if not mprobs:
        bad("反向自证失败：悬空入口热区未被检出（判据恒真）")
    else:
        print("      %s" % mprobs[0])

    mut2 = copy.deepcopy(s1)
    mut2["elements"] = [e for e in mut2["elements"] if e["id"] != "fc.frag1_back_hit"]
    m2 = check_screen(mut2)
    print("  变异B（删 fc.frag1_back_hit）：报错 %d 条 ⇒ %s"
          % (len(m2), "✓ 被拦下" if m2 else "✗ 恒真！"))
    if not m2:
        bad("反向自证失败：缺返回键未被检出")
    else:
        print("      %s" % m2[0])

    print("=" * 78)
    print("结果：**%s**" % ("全部通过" if not FAILS else "不通过（%d 条）" % len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())

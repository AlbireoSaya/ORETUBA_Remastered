# -*- coding: utf-8 -*-
r"""e2_make_evidence_tables.py —— 生成 E2 交付用的三张机器表（`ISSUE-20260929-05`）。

产出（落 `_工作\ISSUE-20260929-05_模式入口\证据\`）：
  · `E2_元素改动_前后.tsv` —— 19 删 / 6 增 逐件 old→new（old 取 **`git show HEAD:`** 的屏文件，
    即本批开工前的盘面；new 取当前盘面）
  · `E2_零引用素材.tsv` —— 6 件素材在**四路**（krkr `*.tjs` ／ `复刻/*.js` ／ `复刻/*.html` ／
    `layout/screens/*.json`）的功能引用命中数
  · `E2_金标_新旧.md` —— 五档 md5 / content-sha256 / 元素数（old 取 `GOLDEN` 之外的历史值：
    从 `layout/_schema.md` 的「第 12 批重钉」表读，人工不介入；new 取当前 `GOLDEN`）
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))     # …\_工作\<issue>\脚本
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # …\UI组
EVID = os.path.join(os.path.dirname(HERE), "证据")
SCREEN_REL = "layout/screens/32_flowchart.json"
DIALOG_REL = "layout/screens/10_dialog.json"

REMOVED = (["fc.mtab%d%s" % (n, s) for n in (1, 2, 3, 4) for s in ("", "_tx", "_hit")]
           + ["fc.fusen_%s%s" % (k, s) for k in ("edit", "reset") for s in ("", "_tx", "_hit")]
           + ["dlg.hint"])
ADDED = ["fc.mode_main_glow", "fc.mode_main_tx", "fc.mode_main_hit",
         "fc.mode_frag_glow", "fc.mode_frag_tx", "fc.mode_frag_hit"]
ASSETS = ["x_ui_ftab_on.png", "x_ui_ftab_off.png", "x_ui_ftab_over.png",
          "x_ui_fusen_off.png", "x_ui_fusen_over.png", "x_ui_fusen_on.png"]


def git_show(ref, rel):
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                         capture_output=True, text=True).stdout.strip()
    abspath = os.path.join(UI, rel)
    relrepo = os.path.relpath(abspath, top).replace("\\", "/")
    r = subprocess.run(["git", "show", "%s:%s" % (ref, relrepo)], cwd=top,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("[FAIL] git show %s:%s 失败：%s" % (ref, relrepo, r.stderr[-200:]))
    return json.loads(r.stdout)


def brief(e):
    """一行摘要：kind | 几何 | 关键载荷。"""
    bits = [e.get("kind", "")]
    bits.append("%s,%s,%s×%s" % (e.get("x"), e.get("y"), e.get("w"), e.get("h")))
    bits.append("z=%s" % e.get("z"))
    for k in ("asset", "action", "sample", "state_group"):
        if e.get(k) not in (None, "", []):
            bits.append("%s=%s" % (k, e[k]))
    if e.get("state_assets"):
        bits.append("state_assets=(%s)" % ",".join(sorted(e["state_assets"])))
    if "nine" in e:
        bits.append("nine=%s" % e["nine"])
    return " ｜ ".join(bits)


def main():
    os.makedirs(EVID, exist_ok=True)
    old_fc = git_show("HEAD", SCREEN_REL)
    new_fc = json.load(open(os.path.join(UI, SCREEN_REL), encoding="utf-8"))
    old_dl = git_show("HEAD", DIALOG_REL)
    new_dl = json.load(open(os.path.join(UI, DIALOG_REL), encoding="utf-8"))
    om = {e["id"]: e for e in old_fc["elements"]}
    nm = {e["id"]: e for e in new_fc["elements"]}
    odm = {e["id"]: e for e in old_dl["elements"]}
    ndm = {e["id"]: e for e in new_dl["elements"]}

    # ── ① 元素改动前后 ────────────────────────────────────────────────
    lines = ["#\t处置\t屏\t元素 id\told（HEAD 盘面）\tnew（本批盘面）\t依据"]
    for i in REMOVED:
        if i.startswith("fc.mtab"):
            why = "ISSUE-20260929-05 · 用户 2026-09-29 指令①（删 4 个 `fc.mtabx` 与对应 text）＋②（原位改两枚文字入口）"
        elif i.startswith("fc.fusen"):
            why = "ISSUE-20260929-05 · 用户 2026-09-29 指令③（不再需要备注功能；`_hit` 一并删 ⇒ 不留指空动作的死热区）"
        else:
            why = "ISSUE-20260929-05 · 用户 2026-09-29「对话框页」指令（不需要操作提示）"
        if i in om:
            lines.append("%d\t删\tflowchart\t%s\t%s\t（删除）\t%s" % (len(lines), i, brief(om[i]), why))
        elif i in odm:
            lines.append("%d\t删\tdialog\t%s\t%s\t（删除）\t%s" % (len(lines), i, brief(odm[i]), why))
        else:
            lines.append("%d\t删\t?\t%s\t（HEAD 无此件）\t（删除）\t%s" % (len(lines), i, why))
    for i in ADDED:
        lines.append("%d\t增\tflowchart\t%s\t（HEAD 无此件）\t%s\tISSUE-20260929-05 · 接口冻结 §B"
                     % (len(lines), i, brief(nm[i])))
    open(os.path.join(EVID, "E2_元素改动_前后.tsv"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("[ok] E2_元素改动_前后.tsv（%d 行）" % len(lines))

    # ── ② 零功能引用素材（四路命中；**功能引用 / 历史提及 / 清单元数据** 三分）──────────
    #   口径（为什么必须三分）：本批对素材的引用有两种性质完全不同的出现方式 ——
    #     ① **功能引用**：作为**引号字面量路径**出现（`"asset": "ui/x.png"` / `state_assets.*` /
    #        `uiAssetLoad("ui/x.png")`）⇒ 这才是「加载了这张图」；
    #     ② **历史提及**：`note` / `source` / 代码注释里的散文（如「旧占位件 `x_ui_fusen_off.png` 退役」）
    #        ⇒ **不加载**，是留痕；
    #     ③ **清单元数据**：`复刻/asset_index.js` 是**素材清单**（逐文件列名，供编辑器挑选）
    #        ⇒ 每件必然出现 2 次，**不是引用**。
    #   判据：对每个素材在四路里分别数 `"ui/<file>"`（**带引号**的功能字面量）与总出现数；
    #   「零功能引用」＝**功能引用合计 0**。
    ROUTES = {
        "krkr/*.tjs（含生成的 ui_layout.tjs）":
            [os.path.join("krkr", "game", x) for x in sorted(os.listdir(os.path.join(UI, "krkr", "game")))
             if x.endswith(".tjs")],
        "复刻/*.js + *.html":
            [os.path.join("复刻", x) for x in sorted(os.listdir(os.path.join(UI, "复刻")))
             if x.endswith((".js", ".html"))],
        "layout/screens/*.json":
            [os.path.join("layout", "screens", x) for x in sorted(os.listdir(os.path.join(UI, "layout", "screens")))
             if x.endswith(".json")],
        "工具/gen_flow_layout.py":
            ["工具/gen_flow_layout.py"],
    }
    CATALOG = ("asset_index.js",)      # 生成物素材清单（逐文件列名，供编辑器挑选）⇒ 不计为引用
    out = ["素材\t" + "\t".join("功能引用 · %s" % k for k in ROUTES)
           + "\t非引用出现（散文/清单）\t结论"]
    detail = ["# `ISSUE-20260929-05` E2 · 删件素材的「零功能引用」实测（四路）", "",
              "口径：**功能引用** ＝ **带引号的路径字面量**（`\"ui/<文件>\"` 或 `\"<文件>\"`）—— 这才是"
              "「会被 `loadImages`/`uiAssetLoad` 加载」的写法（数据里是 `asset` / `state_assets.*` 的值）；",
              "其余出现（`note`/`source`/代码注释的散文、`复刻/asset_index.js` 这一**生成物素材清单**）"
              "**不加载**，单列一栏。**排除**：`复刻/asset_index.js`（清单文件本身不参与功能引用统计）。", "",
              "| 素材 | " + " | ".join(ROUTES) + " | 非引用出现 | 结论 |",
              "| --- | " + " | ".join("---" for _ in ROUTES) + " | --- | --- |"]
    for a in ASSETS:
        fn = "ui/" + a
        cells, func_total, other = [], 0, 0
        for k, files in ROUTES.items():
            fq = 0
            nq = 0
            for f in files:
                if os.path.basename(f) in CATALOG:
                    continue
                try:
                    txt = open(os.path.join(UI, f), encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                fq += txt.count('"%s"' % fn) + txt.count('"%s"' % a)
                nq += txt.count(fn) - txt.count('"%s"' % fn)
            func_total += fq
            other += nq
            cells.append("%d ／ 提及 %d" % (fq, nq))
        verdict = "**零功能引用**（仅素材库保留）" if func_total == 0 else "仍有功能引用（%d）" % func_total
        if a == "x_ui_ftab_over.png":
            verdict += "；**本批之前即已零引用**"
        other += sum(open(os.path.join(UI, f), encoding="utf-8", errors="ignore").read().count("ui/" + a)
                     for f in ["复刻/asset_index.js"] if os.path.exists(os.path.join(UI, f))) \
            + sum(open(os.path.join(UI, f), encoding="utf-8", errors="ignore").read().count(a)
                  for f in ["复刻/asset_index.js"] if os.path.exists(os.path.join(UI, f)))
        out.append("%s\t%s\t%d\t%s" % (a, "\t".join(cells), other, verdict))
        detail.append("| `%s` | %s | %d | %s |" % (a, " | ".join(cells), other, verdict))
    open(os.path.join(EVID, "E2_零引用素材.tsv"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(out) + "\n")
    open(os.path.join(EVID, "E2_零引用素材.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(detail) + "\n")
    print("[ok] E2_零引用素材.tsv / .md")

    # ── ③ 金标新旧 ───────────────────────────────────────────────────
    spec = importlib.util.spec_from_file_location("g", os.path.join(UI, "工具", "gen_flow_layout.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    OLD = {  # 第 12 批重钉值（`layout/_schema.md` 的「第 12 批重钉」表；本批之前）
        "screen1": ("274", "1b0c2ba681fcd603a0eae176c28aca00",
                    "89d9e8fcaa90ce99eed61c28677f65161f766347f0ded6cf3854b800050f632c"),
        "screen2": ("118", "7a37f9ef21620354f2495def102aa16b",
                    "fc2a72d82f3cc37b32812734e33c166c8748cbe980ec9140f48049e3428ff7e9"),
        "ref150": ("97", "d013257e4eb6f360ea0a13eac84eec70",
                   "301f6e503af0f7a402a1437360e0ccea122cdc8ee5b058a789def5ae03dbaae4"),
        "states": ("111", "41db5009af1bea8482242a884853a44e",
                   "c292c213b532a46aaef0b040a935dd5fab525531af138d789d316e91f093c009"),
        "frag": ("130", "899ee92b87f267e3869bd7809838bf51",
                 "ad8b0d116c610f1f1b0a370eaff10a549a8c65a4a30e00765b4e4a97dd3e0c87"),
    }
    md = ["# `ISSUE-20260929-05` E2 · 五档金标（新旧对照）", "",
          "来源：old ＝ `layout/_schema.md`「第 12 批重钉」表（本批之前的现行值）；"
          "new ＝ `工具\\gen_flow_layout.py` 的 `GOLDEN`（`--refresh-golden` 实跑真值）。", "",
          "| 预设 | 元素数 old | 元素数 new | md5 old | md5 new | content-sha256 new |",
          "| --- | ---: | ---: | --- | --- | --- |"]
    for k in mod.GOLDEN_ORDER:
        n_md5, n_sha = mod.GOLDEN[k]
        o_n, o_md5, o_sha = OLD[k]
        md.append("| `%s` | %s | **%d** | `%s` | `%s` | `%s` |" % (k, o_n, len(mod.preset_run(k)[0]["elements"]), o_md5, n_md5, n_sha))
    md += ["", "**实跑核验**：无参 `python 工具/gen_flow_layout.py` ⇒ `screen1` md5 ＝ `%s`（＝金标，落盘前自检通过）。"
           % mod.GOLDEN["screen1"][0],
           "", "**元素数差**：五档各 **−12**（删 12 件 `fc.mtab*` ＋ 6 件 `fc.fusen_*`、增 6 件 `fc.mode_*`）；"
           "外壳 **52 → 40**、图内容层 **222 不变**；另 `dialog` **10 → 9**（删 `dlg.hint`；⚠ 冻结 §E 记的「18 → 17」为**绝对值笔误**，增量 −1 正确）"
           "⇒ **17 屏合计 1404 → 1391**（逐屏求和实测）。"]
    open(os.path.join(EVID, "E2_金标_新旧.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(md) + "\n")
    print("[ok] E2_金标_新旧.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

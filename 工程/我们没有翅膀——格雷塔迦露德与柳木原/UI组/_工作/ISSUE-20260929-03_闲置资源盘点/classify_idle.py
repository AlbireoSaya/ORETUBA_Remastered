# -*- coding: utf-8 -*-
r"""classify_idle.py —— 把 `闲置盘点.json` 的闲置件分成**可执行的四档**（顾问模式 · 只读）

在 `audit_unused_assets.py` 的三档（在用 / 软闲置 / 孤儿）之上，回答用户真正要的问题：
**「哪些能删、删了会不会失去能力、能不能再生」。**

对每个「闲置族」（文件名前 3–4 段）判定：

| 档 | 判据 | 处置建议 |
| --- | --- | --- |
| **备选集** | 该族的**前缀**在 `.md` 里被明说为「共 N 组」「需要时」「备选」「可换」等用途说明 | **建议保留**（删了会失去能力：换转场规则 / 换三态件 / 回退件 …） |
| **可复现** | 该族前缀在 `工具\*.py` 的**生成器**里出现（＝有脚本能重新产出） | **可删**（删了能重生成；省体积） |
| **已删屏/已换源遗留** | 文档里有「已删/已换/被取代」的叙述，且**无生成器** | **可删**（但**先留档**，按工程「只增不删」口径先归档再删） |
| **纯孤儿** | 全库（屏/代码/脚本/文档）无人提及，且无生成器 | **可删**（零风险） |

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python classify_idle.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                      capture_output=True, text=True).stdout.strip()
INV = os.path.join(HERE, "闲置盘点.json")

# 「备选集」的文本特征（文档里出现这些词 ⇒ 该族是有意保留的能力，不是垃圾）
KEEP_HINTS = ("共 ", "需要时", "备选", "可换", "回退", "留档", "保留", "三态", "两态", "按需")
# 「已删/已换源」的文本特征
DROP_HINTS = ("已删", "已废除", "已退场", "被取代", "已换成", "已改为", "旧占位", "已废弃", "重导")


def family(name):
    stem = name[:-4]
    p = stem.split("_")
    if stem.startswith(("x_ui_", "x_gen_", "x_gal_", "x_psv_")):
        return "_".join(p[:3])
    return p[0]


def tool_texts():
    out = {}
    for root, _d, fs in os.walk(os.path.join(UI, "工具")):
        if "__pycache__" in root:
            continue
        for f in fs:
            if f.endswith(".py"):
                out[os.path.join(root, f)] = io.open(os.path.join(root, f),
                                                     encoding="utf-8", errors="replace").read()
    return out


def doc_texts():
    rels = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "*.md"],
                          cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8").stdout.splitlines()
    out = {}
    for rel in rels:
        if rel.startswith("临时/"):
            continue
        p = os.path.join(REPO, rel)
        if os.path.isfile(p):
            out[rel] = io.open(p, encoding="utf-8", errors="replace").read()
    return out


def main():
    inv = json.load(io.open(INV, encoding="utf-8"))
    idle = [i for i in inv["items"] if i["tier"] != "在用"]
    tools = tool_texts()
    docs = doc_texts()

    fams = {}
    for i in idle:
        fams.setdefault(family(i["file"]), []).append(i)

    rows = []
    for fam, items in sorted(fams.items(), key=lambda kv: -sum(x["bytes"] for x in kv[1])):
        n = len(items)
        b = sum(x["bytes"] for x in items)
        # 生成器面
        gen = [os.path.relpath(p, UI) for p, t in tools.items() if fam in t]
        # 文档面：找提到该族的句子
        keep_why, drop_why, doc_hit = "", "", ""
        cnt = 0
        for rel, t in docs.items():
            for m in re.finditer(re.escape(fam), t):
                s = t[max(0, m.start() - 160):m.start() + 160].replace("\n", " ")
                cnt += 1
                if not doc_hit:
                    doc_hit = "%s｜%s" % (rel, s.strip()[:230])
                if not keep_why and any(h in s for h in KEEP_HINTS):
                    keep_why = s.strip()[:200]
                if not drop_why and any(h in s for h in DROP_HINTS):
                    drop_why = s.strip()[:200]
                if keep_why and drop_why and doc_hit:
                    break
        if keep_why and not drop_why:
            tier = "备选集（建议保留）"
        elif drop_why:
            tier = "已删屏/已换源遗留（可删，先留档）"
        elif gen:
            tier = "可复现（可删，脚本能再生）"
        elif cnt == 0:
            tier = "纯孤儿（零提及，可删）"
        elif keep_why:
            tier = "备选集（建议保留）"
        else:
            tier = "仅文档提及（需人判）"
        rows.append(dict(fam=fam, n=n, b=b, tier=tier, gen=gen[:2], cnt=cnt,
                         keep_why=keep_why, drop_why=drop_why, doc_hit=doc_hit))

    print("=" * 108)
    print("闲置族分档（闲置合计 %d 件 / %.2f MB）" % (len(idle), sum(i["bytes"] for i in idle) / 1048576))
    print("=" * 108)
    order = ["备选集（建议保留）", "可复现（可删，脚本能再生）", "已删屏/已换源遗留（可删，先留档）",
             "纯孤儿（零提及，可删）", "仅文档提及（需人判）"]
    tot = {}
    for t in order:
        rs = [r for r in rows if r["tier"] == t]
        if not rs:
            continue
        nn = sum(r["n"] for r in rs)
        bb = sum(r["b"] for r in rs)
        tot[t] = (nn, bb)
        print("\n【%s】%d 件 / %.2f MB（%d 个族）" % (t, nn, bb / 1048576, len(rs)))
        for r in sorted(rs, key=lambda x: -x["b"])[:18]:
            print("  %-26s %3d 件 %9.2f MB  族提及 %3d 次  %s"
                  % (r["fam"], r["n"], r["b"] / 1048576, r["cnt"],
                     ("生成器: " + ",".join(r["gen"])) if r["gen"] else "无生成器"))
            if r["keep_why"]:
                print("        ∧ 保留理由：%s" % r["keep_why"][:150])
            if r["drop_why"]:
                print("        ∧ 可删理由：%s" % r["drop_why"][:150])
        if len(rs) > 18:
            print("  …（另有 %d 个族，见分档.tsv）" % (len(rs) - 18))

    print("\n" + "=" * 108)
    print("★ 汇总")
    for t in order:
        if t in tot:
            print("   %-34s %4d 件  %8.2f MB" % (t, tot[t][0], tot[t][1] / 1048576))
    keep = tot.get("备选集（建议保留）", (0, 0))
    can = sum(tot[t][1] for t in order if t != "备选集（建议保留）" and t in tot)
    can_n = sum(tot[t][0] for t in order if t != "备选集（建议保留）" and t in tot)
    print("   ──────────────────────────────────────────────────────────")
    print("   **建议保留（备选集）** %4d 件  %8.2f MB" % keep)
    print("   **可删候选**           %4d 件  %8.2f MB" % (can_n, can / 1048576))
    print("   素材库合计 %d 件 / %.2f MB ⇒ 若只删「可删候选」，降到 %.2f MB"
          % (inv["total"]["files"], inv["total"]["bytes"] / 1048576,
             (inv["total"]["bytes"] - can) / 1048576))

    with io.open(os.path.join(HERE, "闲置族分档.tsv"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write("tier\tfamily\tfiles\tbytes\tgen\tmentions\tkeep_why\tdrop_why\n")
        for r in sorted(rows, key=lambda x: (order.index(x["tier"]), -x["b"])):
            fh.write("%s\t%s\t%d\t%d\t%s\t%d\t%s\t%s\n" % (
                r["tier"], r["fam"], r["n"], r["b"], ",".join(r["gen"]), r["cnt"],
                r["keep_why"], r["drop_why"]))


if __name__ == "__main__":
    main()

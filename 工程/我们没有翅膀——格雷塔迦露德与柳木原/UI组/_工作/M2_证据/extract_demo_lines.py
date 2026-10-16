# -*- coding: utf-8 -*-
"""M2 · 从真实语料抽取演示台词 -> krkr/game/ui_demo_script.tjs

数据源（只读）：工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\剧本\\scene_ot.jsonl
抽取方式：按显式 (scene_id, lineno) 白名单逐条取 lines[] 里的 speaker / cn 字段，
          保证可复现、可溯源（每条台词在 README 里写明 scene_id + lineno）。
禁止：自造剧情。本脚本只做「取原文」这件事。

用法：
    python extract_demo_lines.py
输出：
    <UI组>/krkr/game/ui_demo_script.tjs
"""
from __future__ import annotations

import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))            # …/UI组/_工作/M2_证据
UI = os.path.dirname(os.path.dirname(HERE))                  # …/UI组
OUT = os.path.join(UI, "krkr", "game", "ui_demo_script.tjs")
def find_src() -> str:
    """scene_ot.jsonl 的位置。

    本模块在独立 worktree（临时\\wt-ui）里作业，而 `资源组\\` 只存在于主工作树；
    因此优先取 worktree 内路径，取不到再回退主工作树（只读）。
    """
    workroot = os.path.dirname(os.path.dirname(os.path.dirname(UI)))  # …/我们没有翅膀——格雷塔迦露德与柳木原
    cands = [
        os.path.join(workroot, "资源组", "剧本", "scene_ot.jsonl"),
        os.path.join(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原",
                     "资源组", "剧本", "scene_ot.jsonl"),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    raise SystemExit("[FAIL] 找不到 scene_ot.jsonl，试过：\n  " + "\n  ".join(cands))


SRC = find_src()

# 白名单：全部取自 ot 本篇（scene_ot.jsonl），跨 12 个场景、18 个不同说话人
PICKS = [
    ("ot_s01_01a", 31),
    ("ot_s01_01a", 33),
    ("ot_s01_01a", 89),
    ("ot_s01_02a", 156),
    ("ot_s01_02a", 176),
    ("ot_s01_02a", 1118),
    ("ot_s01_02c", 46),
    ("ot_s01_02c", 97),
    ("ot_s01_02e", 90),
    ("ot_s01_03a", 386),
    ("ot_s01_04a", 671),
    ("ot_s01_04b1", 121),
    ("ot_s01_04c", 10),
    ("ot_s01_04c", 245),
    ("ot_s01_04g", 41),
    ("ot_s01_04i", 68),
    ("ot_s01_05a", 22),
    ("ot_s01_05b", 77),
    ("ot_s01_13a", 51),
    ("ot_s01_17a", 58),
    ("ot_s02_02a", 64),
    ("ot_s02_02a", 341),
    ("ot_s02_03b", 460),
    ("ot_s02_11b", 53),
    ("ot_s03_01a", 15),
    ("ot_s03_02a", 44),
    ("ot_s03_03a", 135),
    ("ot_s04_17b", 459),
]


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    want = {}
    for sc, ln in PICKS:
        want.setdefault(sc, set()).add(ln)

    found = {}
    with io.open(SRC, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            d = json.loads(raw)
            sc = d.get("scene_id")
            if sc not in want:
                continue
            for l in d.get("lines", []):
                key = (sc, l.get("lineno"))
                if l.get("lineno") in want[sc] and l.get("speaker") and l.get("cn"):
                    found[key] = (l["speaker"], l["cn"], l.get("jp", ""))

    missing = [(sc, ln) for sc, ln in PICKS if (sc, ln) not in found]
    if missing:
        raise SystemExit("[FAIL] 白名单里这些 (scene, lineno) 没取到台词：%r" % missing)

    rows = []
    for sc, ln in PICKS:
        sp, cn, jp = found[(sc, ln)]
        rows.append((sc, ln, sp, cn, jp))

    lines = []
    lines.append("// ============================================================")
    lines.append("// ui_demo_script.tjs —— 【由脚本生成，请勿手改】")
    lines.append("// 生成器：UI组/_工作/M2_证据/extract_demo_lines.py")
    lines.append("// 数据源：资源组/剧本/scene_ot.jsonl（只读）")
    lines.append("// 内容  ：全部为原版真实中文台词（ot 本篇），未自造任何剧情")
    lines.append("// 每条自带 scene_id 与 lineno，供溯源；README_运行方式.md 有同样清单")
    lines.append("// ============================================================")
    lines.append("var UIDemoLineCount = %d;" % len(rows))
    lines.append("var UIDemoSceneId  = [%s];" % ", ".join('"%s"' % r[0] for r in rows))
    lines.append("var UIDemoLineno   = [%s];" % ", ".join(str(r[1]) for r in rows))
    lines.append("var UIDemoSpeaker  = [%s];" % ", ".join('"%s"' % esc(r[2]) for r in rows))
    lines.append("var UIDemoText     = [%s];" % ", ".join('"%s"' % esc(r[3]) for r in rows))
    lines.append("")

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print("[OK] wrote %s  (%d lines)" % (OUT, len(rows)))
    for i, (sc, ln, sp, cn, _jp) in enumerate(rows):
        print("  %2d  %-11s L%-5d %-8s %s" % (i + 1, sc, ln, sp, cn[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
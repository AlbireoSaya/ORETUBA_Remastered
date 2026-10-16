# -*- coding: utf-8 -*-
r"""M37 · 展开态**整列区域的点击胜者分布**（1px 全扫描，复算 `uiScreenClick` 口径）

■ 用途
  README §八① 原来登记的是 M36 结构的「4 344 px 点击穿透带」（左带 x1842..1844 +
  11 条项间缝）。M37 形态重构后整条把手退场，该结论必须**重算**——
  本脚本给出新结构的逐元素胜出像素数与「穿透带」构成，作为 README 与报告的实测依据。

■ 口径
  · 可见性 / 命中一律复用 `工具\test_click_reach.py` 的 `flag_visible` / `scan_counts`
    （**单一实现**，避免与守门分叉）；
  · 扫描区域 = 12 个项热区的**并集矩形**（从数据推出，不写死坐标）；
  · 展开态取值从 12 项热区自身的 (vis_flag, vis_when) 推出（不写死 flag 名/取值）。

■ 用法
    python _工作\M37_展开态点击分布.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(UI, "工具"))
from test_click_reach import flag_visible, scan_counts            # noqa: E402

SCREEN = os.path.join(UI, "layout", "screens", "35_quickbar.json")


def main():
    d = json.load(io.open(SCREEN, encoding="utf-8"))
    els = d["elements"]
    flags = dict(d.get("flags_default") or {})
    hits = [e for e in els if str(e.get("id", "")).startswith("quick.hit_")]
    flags[hits[0]["vis_flag"]] = hits[0]["vis_when"]              # 展开态（从数据推出）
    x0 = min(e["x"] for e in hits)
    y0 = min(e["y"] for e in hits)
    x1 = max(e["x"] + e["w"] for e in hits)
    y1 = max(e["y"] + e["h"] for e in hits)
    rect = [x0, y0, x1 - x0, y1 - y0]
    area = rect[2] * rect[3]
    wins = scan_counts(els, rect, flags, 1, lambda w: w["id"] if w else "(无)")
    print("=" * 78)
    print("展开态整列区域 %s（%d px）的点击胜者分布｜flags=%s"
          % (tuple(rect), area, json.dumps({k: v for k, v in flags.items()}, ensure_ascii=False)))
    print("=" * 78)
    tot = 0
    for k in sorted(wins, key=lambda k: -wins[k]):
        print("  %-22s %7d px  (%.2f%%)" % (k, wins[k], 100.0 * wins[k] / area))
        tot += wins[k]
    print("  %-22s %7d px" % ("合计", tot))
    print("\n  其中「无命中（穿透到承载屏）」= %d px（%.2f%%）" % (wins.get("(无)", 0),
          100.0 * wins.get("(无)", 0) / area))
    print("  非该项自身的其它命中 = %d px（%.2f%%）"
          % (sum(v for k, v in wins.items() if k not in ("(无)",) and k not in
                 [e["id"] for e in hits]), 100.0 * sum(v for k, v in wins.items()
                 if k not in ("(无)",) and k not in [e["id"] for e in hits]) / area))
    # 穿透带构成
    gap_rows = 0
    for a, b in zip(sorted(hits, key=lambda e: e["y"]), sorted(hits, key=lambda e: e["y"])[1:]):
        gap_rows += max(0, b["y"] - (a["y"] + a["h"]))
    print("  项间缝行数 = %d（%d 条缝 × %d 行宽）⇒ 缝面积 = %d px（与上表「无命中」互证）"
          % (gap_rows, len(hits) - 1, gap_rows // max(1, len(hits) - 1), gap_rows * rect[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

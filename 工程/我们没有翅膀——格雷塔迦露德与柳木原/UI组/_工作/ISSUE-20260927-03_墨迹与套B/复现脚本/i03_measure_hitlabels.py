# -*- coding: utf-8 -*-
r"""ISSUE-20260927-03 · 模块 I · `hit.label`（元素级热区标签）墨迹中线量测（改前/改后，两端通用）。

■ 量什么（两端同口径，canvas / 元素坐标系 1:1）
  在**元素矩形**内找「标签颜色」的像素（`font.color` 经 `layout\palette.json` 解引用；
  本件 = `@palette.node_locked` = #4A4A56），逐行计数，行内 ≥2 像素才算有墨 ⇒ 墨迹行区间 → 中线；
  与**元素框纵向中线**（= 按钮可见体中线；`x_ui_jump_off.png` 实测可见体中线 = 元素框中线）
  比较，delta < 0 = 墨迹偏高。

■ 为什么用「标签颜色」而不是「与背景差异」的通用判据
  素材补齐后元素矩形里是**整块按钮美术**（多色），「与矩形内众数颜色不同」会把整块美术误判成墨迹
  （本轮实测：h64 的件被判成「墨迹 64 行」= 整个矩形）。标签颜色是**唯一已知的先验**，故按它筛。

■ 用法
    python …\i03_measure_hitlabels.py <png> [<png> …]
      屏幕按**文件名**判定（含 `ending` / `fragment` 者各量对应主语；两者都含则都量）。
"""
import json
import os
import re
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))   # 复现脚本 → 模块 → _工作 → UI组
SCREENS = os.path.join(UI, "layout", "screens")
PALETTE = os.path.join(UI, "layout", "palette.json")

SUBJ = {                                   # 文件名关键词 -> (屏幕 json, 元素 id, 说明)
    "ending": ("29_ending.json", "ed.hit_skip", "片尾·跳过热区（字号 26 / h 64）"),
    "fragment": ("31_fragment.json", "fragment.hit_back", "断章·返回热区（字号 30 / h 58）"),
}
INK_MIN_PX = 2        # 该行至少这么多「标签色」像素才算有墨
INK_TOL = 20          # 与标签色的 L1 距离容差（抗锯齿边缘不计）


def resolve_color(c):
    if isinstance(c, str) and c.startswith("@palette."):
        key = c.split(".", 1)[1]
        pal = json.load(open(PALETTE, encoding="utf-8"))
        node = pal.get("colors", pal).get(key)
        if isinstance(node, dict):
            node = node.get("value")
        c = node
    if isinstance(c, str) and re.match(r"^#[0-9A-Fa-f]{6}$", c):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    return None


def elem(screen_json, eid):
    d = json.load(open(os.path.join(SCREENS, screen_json), encoding="utf-8"))
    for e in d["elements"]:
        if e["id"] == eid:
            return e
    return None


def measure(path, screen_json, eid, note):
    e = elem(screen_json, eid)
    x0, y0, w, h = e["x"], e["y"], e["w"], e["h"]
    col = resolve_color((e.get("font") or {}).get("color"))
    im = Image.open(path).convert("RGB")
    px = im.load()

    def near(c):
        return abs(c[0] - col[0]) + abs(c[1] - col[1]) + abs(c[2] - col[2]) <= INK_TOL

    rows = [y for y in range(y0, y0 + h)
            if sum(1 for x in range(x0, x0 + w) if near(px[x, y])) >= INK_MIN_PX]
    res = {"el": eid, "note": note, "rect": (x0, y0, w, h), "font": (e.get("font") or {}).get("size"),
           "color": col, "box_mid": y0 + (h - 1) / 2.0}
    if rows:
        res.update(ink=(rows[0], rows[-1], len(rows)), ink_mid=(rows[0] + rows[-1]) / 2.0,
                   delta=(rows[0] + rows[-1]) / 2.0 - res["box_mid"])
    return res


def main():
    print("hit.label 墨迹中线 vs 元素框中线（canvas 坐标；delta < 0 = 墨迹偏高）")
    print("=" * 108)
    for p in sys.argv[1:]:
        base = os.path.basename(p)
        keys = [k for k in SUBJ if k in base]
        if not keys:
            print("（跳过，文件名里没有 ending/fragment 关键词）：%s" % base)
            continue
        print("图：%s" % base)
        for k in keys:
            sj, eid, note = SUBJ[k]
            r = measure(p, sj, eid, note)
            if "ink" not in r:
                print("  %-18s 未测到墨迹（矩形内无「标签色」像素）" % eid)
                continue
            print("  %-18s 字号 %-3s 色 %s 矩形 %s ｜ 墨迹行 %3d..%3d（%2d 行）中线 %6.1f ｜ "
                  "框中线 %6.1f ｜ **delta %+5.1f** ｜ %s"
                  % (r["el"], r["font"], r["color"], r["rect"], r["ink"][0], r["ink"][1],
                     r["ink"][2], r["ink_mid"], r["box_mid"], r["delta"], r["note"]))
        print("-" * 108)


if __name__ == "__main__":
    main()

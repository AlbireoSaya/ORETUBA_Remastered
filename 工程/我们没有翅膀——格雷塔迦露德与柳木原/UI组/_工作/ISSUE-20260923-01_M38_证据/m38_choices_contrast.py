# -*- coding: utf-8 -*-
r"""M38 · 「白字可读性」量化：未高亮选择肢项 vs 对话正文/角色名（同一口径）

■ 背景（vision 子代理 2026-09-23 独立验收）
  `dlg.choices` 原只有单向投影（`shadow_ofs:3`）、**无描边**；第 2 条未高亮项是白字
  `@palette.text_menu`，压在**白色羽翼**上时「阿斯嘉」三字几乎消失。
  量化口径 = **文字像素中，2px 邻域内存在暗像素的比例**
  （vision 实测：选择肢第 2 条 13.9% ｜ 对话正文 51.1% ｜ 角色名 67.4%）。

■ 本脚本的口径与标定
  · 文字像素 = 与 `palette.json` 中该元素**文字色**逐通道差 ≤ `TOL` 的像素；
  · 暗像素   = 亮度 L < `DARK`；邻域 = 切比雪夫半径 `RADIUS`；
  · **TOL 由 vision 的实测值反向标定**：全条矩形上 TOL=16 时修前 = **13.9%**（与 vision 逐位一致），
    故本脚本默认 TOL=16，并在输出里同时打印 TOL=16/24 两档，避免「挑一个好看的容差」。
  · **两个分母都报**：
      ① `full`  = 整条矩形（= vision 的口径，含透过半透明面板的白色羽翼背景 ⇒ 分母被背景稀释）；
      ② `label` = 标签自身的排版盒（由数据 + 同字体度量算出：align=center、valign=middle、
                 行高 = floor(size × line_spacing)）⇒ 分母即「字形 + 笔画间空隙」，
                 这正是「描边要把它与背景分开」的那块像素。
  · 三个被测对象（几何/颜色**全部读数据**，不写死）：
      `dlg.choices` 第 2 条（未高亮）｜ `dlg.text`（正文，仅 shot_03）｜ `dlg.name`（名字，仅 shot_03）。

■ 用法
    python m38_choices_contrast.py [--tol 16] <图片> [<图片> ...]
    # 参数里带 "03" 的图会一并算 正文/名字 两个对照主语；带 "04" 的图算选择肢
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
DARK = 100
RADIUS = 2
FONT_CANDIDATES = ["msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc"]


def load_data():
    sc = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
    pal = json.load(open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]
    els = {e["id"]: e for e in sc["elements"]}

    def rgb(key):
        v = pal[key]["value"]
        return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))

    return els, rgb


def pick_font(size):
    for f in FONT_CANDIDATES:
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
        if os.path.exists(p):
            return ImageFont.truetype(p, size), p
    return None, None


def ratio(im, box, text_rgb, tol, verbose=False):
    roi = im.crop(box).convert("RGB")
    px, gray = roi.load(), roi.convert("L").load()
    w, h = roi.size
    text_px = [(x, y) for y in range(h) for x in range(w)
               if all(abs(px[x, y][c] - text_rgb[c]) <= tol for c in range(3))]
    tset, hit = set(text_px), 0
    for (x, y) in text_px:
        found = False
        for dy in range(-RADIUS, RADIUS + 1):
            for dx in range(-RADIUS, RADIUS + 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and gray[xx, yy] < DARK:
                    found = True
                    break
            if found:
                break
        if found:
            hit += 1
    ink = sum(1 for y in range(h) for x in range(w)
              if gray[x, y] < DARK
              and any((x + dx, y + dy) in tset
                      for dy in range(-RADIUS, RADIUS + 1) for dx in range(-RADIUS, RADIUS + 1)))
    if verbose:
        print("        [%s] 框 %dx%d ｜ 文字像素 %d ｜ 命中 %d ｜ 暗墨迹 %d"
              % (box, w, h, len(text_px), hit, ink))
    return len(text_px), hit, (100.0 * hit / max(1, len(text_px))), ink


def choices_boxes(el):
    """整条矩形（uiWidgetListSpan/ItemRect 口径）与标签排版盒（uiWidgetDrawList 口径）。"""
    n = len(el["labels"])
    span = n * el["item_h"] + max(0, n - 1) * el["gap"]
    y0 = el["stack_bottom"] - span
    iy = y0 + 1 * (el["item_h"] + el["gap"])
    full = (int(el["x"]), int(iy), int(el["x"]) + int(el["w"]), int(iy + el["item_h"]))
    size = int(el["font"]["size"])
    lineH = max(size, int(size * 1.4))                      # uiThemeApplyFont: floor(size*spacing)
    ty = iy + (int(el["item_h"]) - lineH) // 2              # uiWidgetDrawList: (h - lineH)/2
    font, _ = pick_font(size)
    label = el["labels"][1]
    adv = font.getlength(label) if font else size * len(label)
    cx = int(el["x"]) + int(el["w"]) // 2
    lab = (int(cx - adv / 2), int(ty), int(cx + adv / 2) + 1, int(ty + lineH))
    return full, lab, lineH


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=int, default=16)
    ap.add_argument("images", nargs="+")
    a = ap.parse_args()

    els, rgb = load_data()
    cho = els["dlg.choices"]
    full, lab, lineH = choices_boxes(cho)
    print("口径：暗像素 L<%d ｜ 邻域 切比雪夫 %dpx ｜ 主容差 TOL=%d（对照档 24）"
          % (DARK, RADIUS, a.tol))
    print("选择肢第 2 条：整条矩形 %s（vision 口径）｜ 标签排版盒 %s（行高 %d，由数据复算）\n"
          % (full, lab, lineH))

    for p in a.images:
        if not os.path.exists(p):
            print("!! 缺件 %s" % p)
            continue
        im = Image.open(p).convert("RGB")
        print("── %s" % os.path.basename(p))
        for tag, box, key in (("① 整条矩形（含背景）", full, "text_menu"),
                              ("② 标签排版盒（字形+笔画空隙）", lab, "text_menu")):
            for tol in (a.tol, 24):
                n, hit, r, ink = ratio(im, box, rgb(key), tol)
                print("   %-28s TOL=%-3d 文字像素 %5d ｜ 命中 %5d ｜ **%5.1f%%** ｜ 暗墨迹 %5d"
                      % (tag, tol, n, hit, r, ink))
        # 对照主语（几何与色值全部读数据）
        for eid, key, need03 in (("dlg.text", "text_primary", True),
                                 ("dlg.name", "text_name", True)):
            if need03 and "03" not in os.path.basename(p):
                continue
            e = els[eid]
            box = (int(e["x"]), int(e["y"]), int(e["x"]) + int(e["w"]), int(e["y"]) + int(e["h"]))
            print("   [对照] %-10s 框 %s" % (eid, box))
            for tol in (a.tol, 24):
                n, hit, r, ink = ratio(im, box, rgb(key), tol)
                print("        TOL=%-3d 文字像素 %5d ｜ 命中 %5d ｜ **%5.1f%%** ｜ 暗墨迹 %5d"
                      % (tol, n, hit, r, ink))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

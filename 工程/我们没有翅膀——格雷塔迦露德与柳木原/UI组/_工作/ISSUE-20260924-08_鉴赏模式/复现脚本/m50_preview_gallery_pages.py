# -*- coding: utf-8 -*-
r"""m50_preview_gallery_pages.py —— CG 鉴赏页**几何合成预览**（证据图，非引擎/HTML 截图）

■ 为什么需要它
    `27_gallery.json` 的栏位缩略图 / 栏位内差分键 / `n/N` 计数都走 **M1 尚未落盘的 `item_variants`**，
    而 HTML 复刻端的**翻页**也还没有数据侧入口 ⇒ 本日无法用「引擎自导 PNG / HTML 无头截图」看到
    缩略图与第 2..12 页。故本脚本**只读** `layout\screens\27_gallery.json` 的几何
    （**不复制任何数值**），把该 JSON 指定的真实素材按该 JSON 的坐标合成成 1:1 画面，
    用于目视验收「24 栏齐整 / 缩略图观感 / 差分键与计数位置 / 页码控件 / 末页 22 栏」。

■ 诚实边界（不得当成实机证据）
    · 文字（`n/N`、`x / 12`）由本脚本用 PIL 字体**近似**绘制（实机为引擎绘制，字形与基线会略有差异）；
    · 不含 M1 的机制行为（翻页动画、悬停态、差分切换）—— 本图只证明**几何与素材**；
    · 第 1 页用「页 1 的 24 栏」，第 12 页用「页 12 的 22 栏 + 2 个空位」。

■ 运行
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m50_preview_gallery_pages.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
UI_GROUP = os.path.dirname(os.path.dirname(ISSUE_DIR))
SCREEN = os.path.join(UI_GROUP, "layout", "screens", "27_gallery.json")
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(ISSUE_DIR, "M2_证据")
CG_ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组" \
          r"\_工作\ISSUE-20260924-08_鉴赏模式\CG候选集"
BG_CAND = [os.path.join(CG_ROOT, "代表图", "001_ai_01.png"),
           os.path.join(CG_ROOT, "代表图", "021_asu01.png")]

FONT_CANDS = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
              r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"]


def load_font(size):
    for p in FONT_CANDS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_text_outlined(canvas, box, text, size, color=(255, 255, 255), ow=2):
    """在 box 内居中绘制带描边文字（近似引擎的 font.outline 8 方向）"""
    f = load_font(size)
    d = ImageDraw.Draw(canvas)
    x0, y0, w, h = box
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = x0 + (w - tw) // 2 - bb[0]
    ty = y0 + (h - th) // 2 - bb[1]
    for dx in (-ow, 0, ow):
        for dy in (-ow, 0, ow):
            if dx or dy:
                d.text((tx + dx, ty + dy), text, font=f, fill=(0, 0, 0, 255))
    d.text((tx, ty), text, font=f, fill=tuple(color) + (255,))


def main():
    with open(SCREEN, encoding="utf-8") as f:
        scr = json.load(f)
    els = {e["id"]: e for e in scr["elements"]}
    cells, dim = els["gal.cells"], els["gal.dim"]
    iv = cells["item_variants"]
    frame_off = cells["item_frame"]["state_assets"]["normal"]
    prev_off, next_off = iv["prev"]["state_assets"]["normal"], iv["next"]["state_assets"]["normal"]
    pg_prev, pg_next = els["gal.pg_prev"], els["gal.pg_next"]
    pg_tx = els["gal.pg_tx"]

    iw, ih, gap = cells["item_w"], cells["item_h"], cells["gap"]
    cols, rows = cells["max_cols"], cells["max_rows"]
    per_page = cols * rows
    frames = iv["frames"]
    n_pages = (len(frames) + per_page - 1) // per_page

    def ap(a):
        return os.path.join(ASSETS, os.path.basename(a))

    plate = Image.open(ap(frame_off)).convert("RGBA")
    vprev = Image.open(ap(prev_off)).convert("RGBA")
    vnext = Image.open(ap(next_off)).convert("RGBA")
    pgp = Image.open(ap(pg_prev["asset"])).convert("RGBA")
    pgn = Image.open(ap(pg_next["asset"])).convert("RGBA")

    bg_src = next((p for p in BG_CAND if os.path.exists(p)), None)
    assert bg_src, "找不到背景入料"
    bg0 = Image.open(bg_src).convert("RGB")
    # 铺满 1920×1080（等比放大 + 居中裁切）—— 模拟「剧情背景透出」
    sc = max(1920 / bg0.width, 1080 / bg0.height)
    bg = bg0.resize((int(round(bg0.width * sc)), int(round(bg0.height * sc))), Image.LANCZOS)
    bx = (bg.width - 1920) // 2
    by = (bg.height - 1080) // 2
    bg = bg.crop((bx, by, bx + 1920, by + 1080)).convert("RGBA")

    os.makedirs(EVID, exist_ok=True)
    out = []
    for page in (1, n_pages):
        canvas = bg.copy()
        # 压暗层（@palette.backdrop + opacity）
        canvas = Image.alpha_composite(
            canvas, Image.new("RGBA", (1920, 1080), (0, 0, 0, dim["opacity"])))
        first = (page - 1) * per_page
        n_here = 0
        for k in range(per_page):
            idx = first + k
            if idx >= len(frames):
                break
            col, row = k % cols, k // cols
            x = cells["x"] + col * (iw + gap)
            y = cells["y"] + row * (ih + gap)
            canvas.alpha_composite(plate, (x, y))
            th = iv["thumb"]
            tp = ap(frames[idx][0])
            tim = Image.open(tp).convert("RGBA")
            assert tim.size == (th["w"], th["h"]), (tp, tim.size)
            canvas.alpha_composite(tim, (x + th["x"], y + th["y"]))
            canvas.alpha_composite(vprev, (x + iv["prev"]["x"], y + iv["prev"]["y"]))
            canvas.alpha_composite(vnext, (x + iv["next"]["x"], y + iv["next"]["y"]))
            t = iv["text"]
            draw_text_outlined(canvas, (x + t["x"], y + t["y"], t["w"], t["h"]),
                               "1 / %d" % len(frames[idx]), t["font"]["size"])
            n_here += 1
        canvas.alpha_composite(pgp, (pg_prev["x"], pg_prev["y"]))
        canvas.alpha_composite(pgn, (pg_next["x"], pg_next["y"]))
        draw_text_outlined(canvas, (pg_tx["x"], pg_tx["y"], pg_tx["w"], pg_tx["h"]),
                           "%d / %d" % (page, n_pages), pg_tx["font"]["size"],
                           color=(232, 232, 240), ow=0)
        p = os.path.join(EVID, "m50_preview_page%02d.png" % page)
        canvas.convert("RGB").save(p, optimize=True)
        out.append((p, n_here))
        print("  页 %2d / %d：绘制 %d 栏（空位 %d）-> %s"
              % (page, n_pages, n_here, per_page - n_here, p))
    print("网格：%d 列 × %d 行 = %d 栏/页 ｜ 外框 (%d,%d,%d,%d) ｜ 页数 = %d ｜ 末页 %d 栏"
          % (cols, rows, per_page, cells["x"], cells["y"], cells["w"], cells["h"], n_pages,
             len(frames) - (n_pages - 1) * per_page))
    return 0


if __name__ == "__main__":
    sys.exit(main())
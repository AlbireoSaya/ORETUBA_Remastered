# -*- coding: utf-8 -*-
r"""psv_preview_abasic.py —— A 基础组三屏「**按数据复算的预计上屏图**」（离线合成，供人眼复核几何）。

★ 这不是引擎渲染，也**不替代**巡演/HTML 截图：本脚本只用 PIL 按 `layout/screens/*.json` 的
  x/y/w/h 把**素材**贴到 1920×1080 画布上，用于在**不开引擎、不跑浏览器**的前提下核对
  「按钮有没有落在留白里 / 热区有没有盖住烘焙文字 / 条间距是否重叠」这类**几何**问题。
  实机观感（字体度量、AA、九宫格采样）一律以主代理的 krkr 巡演与 1:1 截图为准。

产物（`证据\`）：
  preview_21_typeA.png   确认框·含烘焙 YES/NO 型（板 01）+ 热区标注 + 局部放大
  preview_21_typeB.png   确认框·无 YES/NO 型（板 20）+ 我方按钮 + 热区标注 + 局部放大
  preview_36_choices.png 选择支（常态 2 行 + 悬停 1 行，字号 44 / 条 1240×107 / 节距 124）
  preview_22_loading.png 加载（背景 + 压暗 + PSV 加载牌）
用法：python 证据\psv_preview_abasic.py
"""
from __future__ import annotations

import json
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCR = os.path.join(UI, "layout", "screens")
AST = os.path.join(UI, "krkr", "assets", "ui")
PAL = json.load(io.open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]
FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"


def hexc(v):
    return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))


def load(asset):
    return Image.open(os.path.join(AST, os.path.basename(asset))).convert("RGBA")


def blit_nine(dst, src, x, y, w, h, nine=None, opacity=255):
    """按 `uiWidgetNine`/`uiWidgetBlitAsset` 的口径合成（全零 nine = 整图拉伸）。"""
    if opacity < 255:
        src = src.copy()
        a = src.split()[3].point(lambda v: v * opacity // 255)
        src.putalpha(a)
    if not nine or all(nine.get(k, 0) == 0 for k in "ltrb"):
        dst.alpha_composite(src.resize((int(w), int(h)), Image.NEAREST), (int(x), int(y)))
        return
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    sw, sh = src.size
    cols = [(0, l, x, l), (l, sw - r, x + l, w - l - r), (sw - r, sw, x + w - r, r)]
    rows = [(0, t, y, t), (t, sh - b, y + t, h - t - b), (sh - b, sh, y + h - b, b)]
    for sx0, sx1, dx, dw in cols:
        for sy0, sy1, dy, dh in rows:
            if sx1 <= sx0 or sy1 <= sy0 or dw <= 0 or dh <= 0:
                continue
            piece = src.crop((sx0, sy0, sx1, sy1)).resize((int(dw), int(dh)), Image.NEAREST)
            dst.alpha_composite(piece, (int(dx), int(dy)))


def elements(fn):
    return json.load(io.open(os.path.join(SCR, fn), encoding="utf-8"))["elements"]


def draw_hits(d, els, outline=(0, 220, 0, 255)):
    for e in els:
        if e["kind"] == "hit":
            d.rectangle([e["x"], e["y"], e["x"] + e["w"] - 1, e["y"] + e["h"] - 1],
                        outline=outline, width=3)


def font(size):
    try:
        return ImageFont.truetype(FONT_CJK, size)
    except Exception:
        return ImageFont.load_default()


def preview_confirm(nn, out):
    els = elements("21_confirm.json")
    canvas = Image.new("RGBA", (1920, 1080), hexc(PAL["backdrop"]["value"]) + (255,))
    # cf.dim：@palette.backdrop × opacity/255
    dim = [e for e in els if e["id"] == "cf.dim"][0]
    canvas.alpha_composite(Image.new("RGBA", (1920, 1080),
                                     hexc(PAL[dim["color"].split(".")[-1]]["value"]) + (dim["opacity"],)))
    for e in els:
        if e["id"] == "cf.panel_%s" % nn:
            canvas.alpha_composite(load(e["asset"]), (e["x"], e["y"]))
    for e in els:                       # 板号匹配的补按钮（图 + 文字）
        if e.get("vis_when") == nn and e["kind"] == "image":
            blit_nine(canvas, load(e["asset"]), e["x"], e["y"], e["w"], e["h"], e.get("nine"))
        if e.get("vis_when") == nn and e["kind"] == "text":
            d = ImageDraw.Draw(canvas)
            f = font(e["font"]["size"])
            tb = d.textbbox((0, 0), e["sample"], font=f)
            d.text((e["x"] + (e["w"] - (tb[2] - tb[0])) / 2 - tb[0],
                    e["y"] + (e["h"] - (tb[3] - tb[1])) / 2 - tb[1]),
                   e["sample"], font=f, fill=hexc(PAL["node_locked"]["value"]) + (255,))
    d = ImageDraw.Draw(canvas)
    d.text((20, 20), "21 确认框 · 板 %s（%s YES/NO）｜绿框 = 热区（数据 x/y/w/h）"
           % (nn, "含烘焙" if nn in ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
                                    "11", "12", "25", "43", "44") else "无"),
           font=font(28), fill=(255, 255, 255, 255))
    draw_hits(d, els)
    canvas.convert("RGB").save(os.path.join(HERE, out))
    # 局部放大（热区带）
    crop = Image.new("RGB", (1920, 1080))
    crop.paste(canvas.convert("RGB"))
    z = crop.crop((700, 560, 1180, 690)).resize((4 * 480, 4 * 130), Image.NEAREST)
    z.save(os.path.join(HERE, out.replace(".png", "_zoom.png")))
    print("  -> %s (+ _zoom)" % out)


def preview_choices():
    els = elements("36_choices.json")
    li = [e for e in els if e["id"] == "ch.choices"][0]
    canvas = Image.new("RGBA", (1920, 1080), hexc(PAL["backdrop"]["value"]) + (255,))
    d = ImageDraw.Draw(canvas)
    f = font(li["font"]["size"])
    labels = ["这是第一个选项", "这是第二个选项", "悬停/按下态（粉）"]
    for i, lab in enumerate(labels):
        state = "hover" if i == 2 else "normal"
        asset = li["item_frame"]["state_assets"][state]
        y = li["y"] + i * (li["item_h"] + li["gap"])
        blit_nine(canvas, load(asset), li["x"], y, li["w"], li["item_h"], li["item_frame"]["nine"],
                  li["item_frame"]["opacity"])
        tb = d.textbbox((0, 0), lab, font=f)
        d.text((li["x"] + (li["w"] - (tb[2] - tb[0])) / 2 - tb[0],
                y + (li["item_h"] - (tb[3] - tb[1])) / 2 - tb[1]), lab, font=f,
               fill=hexc(PAL["node_locked"]["value"]) + (255,))
        d.rectangle([li["x"], y, li["x"] + li["w"] - 1, y + li["item_h"] - 1],
                    outline=(0, 220, 0, 255), width=2)
    d.text((20, 20), "36 选择支｜3 项：常态×2 + 悬停×1（绿框 = item 矩形 %d×%d；节距 %d = item_h %d + gap %d）"
           "｜x=%d 居中（(1920-%d)/2）｜字号 %d"
           % (li["w"], li["item_h"], li["item_h"] + li["gap"], li["item_h"], li["gap"],
              li["x"], li["w"], li["font"]["size"]), font=font(28), fill=(255, 255, 255, 255))
    preview_dir = HERE
    canvas.convert("RGB").save(os.path.join(preview_dir, "preview_36_choices.png"))
    z = canvas.convert("RGB").crop((330, 280, 1600, 700)).resize((int(1270 * 1.3), int(420 * 1.3)),
                                                                Image.LANCZOS)
    z.save(os.path.join(preview_dir, "preview_36_choices_zoom.png"))
    print("  -> preview_36_choices.png (+ _zoom)")


def preview_loading():
    els = elements("22_loading.json")
    canvas = Image.new("RGBA", (1920, 1080))
    for e in els:
        if e["kind"] == "image":
            blit_nine(canvas, load(e["asset"]), e["x"], e["y"], e["w"], e["h"], e.get("nine"),
                      e.get("opacity", 255))
    for e in els:
        if e["kind"] == "rect":
            canvas.alpha_composite(Image.new("RGBA", (e["w"], e["h"]),
                                             hexc(PAL[e["color"].split(".")[-1]]["value"]) + (e["opacity"],)),
                                   (e["x"], e["y"]))
    for e in els:                     # 板（z=10，压在 dim 之上）
        if e["id"] == "ld.plate":
            canvas.alpha_composite(load(e["asset"]), (e["x"], e["y"]))
    d = ImageDraw.Draw(canvas)
    d.text((20, 20), "22 加载提示｜底 + 压暗(%d) + PSV 加载牌 640×240 @ (%d,%d)（墨迹居中 ⇒ 画布中心）"
           % ([e for e in els if e["kind"] == "rect"][0]["opacity"],
              [e for e in els if e["id"] == "ld.plate"][0]["x"],
              [e for e in els if e["id"] == "ld.plate"][0]["y"]),
           font=font(28), fill=(255, 255, 255, 255))
    canvas.convert("RGB").save(os.path.join(HERE, "preview_22_loading.png"))
    canvas.convert("RGB").crop((560, 340, 1360, 700)).resize((1600, 720), Image.LANCZOS)\
        .save(os.path.join(HERE, "preview_22_loading_zoom.png"))
    print("  -> preview_22_loading.png (+ _zoom)")


if __name__ == "__main__":
    print("离线几何复算预览（非引擎渲染）：")
    preview_confirm("01", "preview_21_typeA.png")
    preview_confirm("20", "preview_21_typeB.png")
    preview_choices()
    preview_loading()

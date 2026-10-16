# -*- coding: utf-8 -*-
r"""psv_config_mock.py —— 25 设置屏换皮后的 **1:1 离线合成**（不做巡演、不启浏览器）

读 `layout/screens/25_config.json`，按 flag（`cfg_page` = sys / snd）把该页可见的元素
按 z 序合成到 1920×1080；`image` 走九宫格（近似：按 nine 切 3×3 拉伸）、`text` 用系统字体
按框位绘制、`hit`/`slider` 画框线。用途：**布局/重叠/越界的目视核对**（引擎逐字排版另由巡演承担）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏换皮\复现脚本\psv_config_mock.py --page sys --out <png>
    python ...\psv_config_mock.py --page snd --out <png> [--zones]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
ASSETS = os.path.join(UI, "krkr", "assets")
OUTDIR = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏换皮", "_证据")
FONT = "C:/Windows/Fonts/msyh.ttc"

PANEL = (130, 196, 1794, 916)          # PSV 面板（越界核对用）


def asset_path(a):
    a = str(a).strip().replace("\\", "/")
    return os.path.join(ASSETS, a if "/" in a else ("ui/" + a))


def nine_resize(im, w, h, n):
    l, t, r, b = n["l"], n["t"], n["r"], n["b"]
    if l == t == r == b == 0:
        return im.resize((w, h), Image.LANCZOS)
    sw, sh = im.size
    mw, mh = sw - l - r, sh - t - b
    cw, ch = w - l - r, h - t - b
    out = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    # 先整体拉伸中格，再贴四角/四边（与引擎 operateStretch 的近似）
    mid = im.crop((l, t, sw - r, sh - b)).resize((max(1, cw), max(1, ch)), Image.LANCZOS)
    out.paste(mid, (l, t))
    corners = [(0, 0, l, t, 0, 0), (sw - r, 0, sw, t, w - r, 0),
               (0, sh - b, l, sh, 0, h - b), (sw - r, sh - b, sw, sh, w - r, h - b)]
    for (x0, y0, x1, y1, dx, dy) in corners:
        if x1 > x0 and y1 > y0 and dx < w and dy < h:
            out.paste(im.crop((x0, y0, x1, y1)), (dx, dy))
    if t > 0 and cw > 0:
        out.paste(im.crop((l, 0, sw - r, t)).resize((cw, t), Image.LANCZOS), (l, 0))
    if b > 0 and cw > 0:
        out.paste(im.crop((l, sh - b, sw - r, sh)).resize((cw, b), Image.LANCZOS), (l, h - b))
    if l > 0 and ch > 0:
        out.paste(im.crop((0, t, l, sh - b)).resize((l, ch), Image.LANCZOS), (0, t))
    if r > 0 and ch > 0:
        out.paste(im.crop((sw - r, t, sw, sh - b)).resize((r, ch), Image.LANCZOS), (w - r, t))
    return out


def visible(e, flags):
    if e.get("visible_default") is False:
        return False
    vf, vw = e.get("vis_flag"), e.get("vis_when")
    if not vf:
        return True
    cur = flags.get(vf, "")
    return (cur != "") if vw == "*" else (cur == vw)


def draw_text(img, e, fill):
    d = ImageDraw.Draw(img)
    f = e.get("font", {})
    size = int(f.get("size", 24))
    try:
        font = ImageFont.truetype(FONT, size)
    except Exception:
        font = ImageFont.load_default()
    txt = str(e.get("sample", ""))
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    lines = txt.split("\n")
    if e.get("wrap"):
        flat = []
        for ln in lines:
            flat.extend([ln[i:i + max(1, int(w // (size * 1.02)))]
                         for i in range(0, max(1, len(ln)), max(1, int(w // (size * 1.02))))])
        lines = flat[:int(e.get("max_lines", 99))]
    lh = int(size * 1.4)
    total = lh * len(lines)
    ty = {"top": y, "middle": y + (h - total) // 2, "bottom": y + h - total}.get(e.get("valign", "middle"), y)
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=font)
        tw = bb[2] - bb[0]
        tx = {"left": x, "center": x + (w - tw) // 2, "right": x + w - tw}.get(e.get("align", "left"), x)
        d.text((tx, ty), ln, font=font, fill=fill)
        ty += lh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", choices=["sys", "snd"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--zones", action="store_true", help="叠加面板/标签列/行框辅助线")
    ap.add_argument("--config", default=SCREEN)
    args = ap.parse_args()

    doc = json.load(open(args.config, encoding="utf-8"))
    # ★ 页派生（与产品同口径，`ui_screens.tjs::uiScreenConfigSyncPage`）：
    #   值键（cfg_v_*）的**页归属写在同行的 hit 上** ⇒ 非本页的值键置空串，
    #   否则 mock 会呈现「产品不可达的跨页残留」（源：`_schema.md`「值键的页归属是算出来的」）。
    key_page = {}
    for e in doc["elements"]:
        eid = e["id"]
        if eid.startswith("cfg.o_") and eid.endswith("_on_hit"):
            key_page[eid[len("cfg.o_"):-len("_on_hit")]] = e.get("vis_when", "")
    key_page["vchar"] = "snd"
    flags = {"cfg_page": args.page}
    for k, v in doc["flags_default"].items():
        if k.startswith("cfg_v_"):
            pg = key_page.get(k[len("cfg_v_"):])
            flags[k] = v if (pg == args.page) else ""
    flags["cfg_vchar"] = "asu" if args.page == "snd" else ""
    canvas = Image.new("RGBA", (1920, 1080), (28, 30, 38, 255))
    els = [e for e in doc["elements"] if visible(e, flags)]
    els.sort(key=lambda e: e.get("z", 0))
    missing = []
    for e in els:
        k = e["kind"]
        if k == "rect":
            lay = Image.new("RGBA", (e["w"], e["h"]), (20, 24, 40, int(e.get("opacity", 255))))
            canvas.alpha_composite(lay, (e["x"], e["y"]))
        elif k == "image" and e.get("asset"):
            p = asset_path(e["asset"])
            if not os.path.isfile(p):
                missing.append(e["asset"])
                continue
            im = Image.open(p).convert("RGBA")
            if e.get("nine"):
                im = nine_resize(im, e["w"], e["h"], e["nine"])
            elif im.size != (e["w"], e["h"]):
                im = im.resize((e["w"], e["h"]), Image.LANCZOS)
            if e.get("opacity", 255) < 255:
                a = im.getchannel("A").point(lambda v: v * e["opacity"] // 255)
                im.putalpha(a)
            canvas.alpha_composite(im, (e["x"], e["y"]))
        elif k == "text":
            col = e.get("font", {}).get("color", "#FFFFFF")
            if isinstance(col, str) and col.startswith("@palette."):
                pal = json.load(open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))
                key = col.split(".")[1]
                col = "#FFFFFF"
                cc = pal.get("colors", {})
                if isinstance(cc, dict) and key in cc:
                    col = cc[key].get("value", "#FFFFFF")
            draw_text(canvas, e, col)
        elif k == "slider":
            rail = (e.get("rail") or {}).get("asset")
            if rail:
                p = asset_path(rail)
                if os.path.isfile(p):
                    im = Image.open(p).convert("RGBA")
                    canvas.alpha_composite(im, (e["x"], e["y"] + (e["h"] - im.height) // 2))
            hd = (e.get("handle") or {}).get("asset")
            if hd:
                p = asset_path(hd)
                if os.path.isfile(p):
                    im = Image.open(p).convert("RGBA")
                    sp = e["max"] - e["min"]
                    t = (e.get("value", 0) - e["min"]) / sp if sp else 0
                    hx = e["x"] + int(t * e["w"]) - im.width // 2
                    canvas.alpha_composite(im, (hx, e["y"] + (e["h"] - im.height) // 2))
        elif k == "hit":
            sa = e.get("state_assets") or {}
            if sa.get("normal"):
                p = asset_path(sa["normal"])
                if os.path.isfile(p):
                    im = Image.open(p).convert("RGBA")
                    if e.get("nine"):
                        im = nine_resize(im, e["w"], e["h"], e["nine"])
                    elif im.size != (e["w"], e["h"]):
                        im = im.resize((e["w"], e["h"]), Image.LANCZOS)
                    canvas.alpha_composite(im, (e["x"], e["y"]))

    if args.zones:
        d = ImageDraw.Draw(canvas)
        d.rectangle([PANEL[0], PANEL[1], PANEL[2], PANEL[3]], outline=(255, 0, 128, 255), width=3)
        d.rectangle([136, 178, 396, 240], outline=(0, 255, 200, 255), width=2)      # label_zone c1
        d.rectangle([152, 178, 430, 256], outline=(255, 200, 0, 255), width=2)      # label_zone c2
        for y in (786, 262, 336, 410, 484):     # 5 条旧滑槽的源位置
            d.rectangle([916, y, 1636, y + 60], outline=(255, 90, 90, 255), width=2)
        d.text((20, 20), "page=%s  元素=%d  %s" % (args.page, len(els), os.path.basename(args.out)),
               fill=(255, 255, 0, 255))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    canvas.convert("RGB").save(args.out)
    print("OK %s（%d 元素；缺件 %s）" % (args.out, len(els), sorted(set(missing)) or "无"))


if __name__ == "__main__":
    main()

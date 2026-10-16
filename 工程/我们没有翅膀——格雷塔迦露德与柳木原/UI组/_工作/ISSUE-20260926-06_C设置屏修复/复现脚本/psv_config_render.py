# -*- coding: utf-8 -*-
r"""psv_config_render.py —— 25 设置屏 **1:1 离线合成**（修复轮证据用；不启引擎、不开浏览器）

读 `layout/screens/25_config.json`（`--config` 可指向别的版本，如 C 组换皮版备份），
按 flag 把该页可见元素按 z 序合成到 1920×1080：
  · `image`/`hit.sate_assets.normal` 走九宫格（近似：3×3 拉伸）；无 nine 且尺寸不等 ⇒ LANCZOS；
  · `text` 按框位用系统字体（msyh.ttc）绘制，`@palette.*` 解析为色值，支持 align/valign/wrap；
  · `slider` 画 rail（1:1，按元素高居中）+ handle（按 value 定位）；
  · 页派生与产品同口径（`ui_screens.tjs::uiScreenConfigSyncPage`）：值键的页归属写在同行
    `_on_hit` 的 vis_when 上，非本页的值键置空串（否则会呈现「产品不可达的跨页残留」）。

**用途**：修复轮的前后对照与逐条自证（引擎逐字排版另由巡演承担，本轮不跑巡演）。
用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏修复\复现脚本\psv_config_render.py \
        --config layout/screens/25_config.json --page sys --out <png> [--set cfg_v_display=full]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image, ImageDraw, ImageFont   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSETS = os.path.join(UI, "krkr", "assets")
FONT = "C:/Windows/Fonts/msyh.ttc"


def load_palette():
    p = os.path.join(UI, "layout", "palette.json")
    with open(p, encoding="utf-8") as fh:
        return {k: v["value"] for k, v in json.load(fh)["colors"].items()}


def asset_path(a):
    a = str(a).strip().replace("\\", "/")
    return os.path.join(ASSETS, a if "/" in a else ("ui/" + a))


def nine_resize(im, w, h, n):
    l, t, r, b = n["l"], n["t"], n["r"], n["b"]
    if l == t == r == b == 0:
        return im.resize((max(1, w), max(1, h)), Image.LANCZOS)
    sw, sh = im.size
    cw, ch = max(1, w - l - r), max(1, h - t - b)
    out = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    out.paste(im.crop((l, t, sw - r, sh - b)).resize((cw, ch), Image.LANCZOS), (l, t))
    for (x0, y0, x1, y1, dx, dy) in [(0, 0, l, t, 0, 0), (sw - r, 0, sw, t, w - r, 0),
                                     (0, sh - b, l, sh, 0, h - b),
                                     (sw - r, sh - b, sw, sh, w - r, h - b)]:
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


def value_key_pages(doc):
    kp = {}
    for e in doc["elements"]:
        eid = e["id"]
        if eid.startswith("cfg.o_") and eid.endswith("_on_hit"):
            kp[eid[len("cfg.o_"):-len("_on_hit")]] = e.get("vis_when", "")
    kp["vchar"] = "snd"
    return kp


def flags_for(doc, kp, page, over):
    f = {"cfg_page": page}
    for k, v in doc["flags_default"].items():
        if k.startswith("cfg_v_"):
            f[k] = v if kp.get(k[len("cfg_v_"):]) == page else ""
    f["cfg_vchar"] = "asu" if page == "snd" else ""
    f.update(over)
    return f


def draw_text(canvas, e, col):
    d = ImageDraw.Draw(canvas)
    f = e.get("font", {})
    size = int(f.get("size", 24))
    font = ImageFont.truetype(FONT, size)
    lines = str(e.get("sample", "")).split("\n")
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    if e.get("wrap"):
        per = max(1, int(w // (size * 1.02)))
        flat = []
        for ln in lines:
            flat.extend([ln[i:i + per] for i in range(0, max(1, len(ln)), per)])
        lines = flat[:int(e.get("max_lines", 99))]
    lh = int(size * 1.4)
    ty = {"top": y, "middle": y + (h - lh * len(lines)) // 2,
          "bottom": y + h - lh * len(lines)}.get(e.get("valign", "middle"), y)
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=font)
        tw = bb[2] - bb[0]
        tx = {"left": x, "center": x + (w - tw) // 2, "right": x + w - tw}.get(e.get("align", "center"), x)
        d.text((tx, ty), ln, font=font, fill=col)
        ty += lh


def render(doc, pal, page, over, size=(1920, 1080)):
    kp = value_key_pages(doc)
    flags = flags_for(doc, kp, page, over)
    canvas = Image.new("RGBA", size, (28, 30, 38, 255))
    els = sorted([e for e in doc["elements"] if visible(e, flags)], key=lambda e: e.get("z", 0))
    missing = []
    for e in els:
        k = e["kind"]
        if k in ("image", "hit"):
            a = e.get("asset") or (e.get("state_assets") or {}).get("normal")
            if not a:
                continue
            p = asset_path(a)
            if not os.path.isfile(p):
                missing.append(a)
                continue
            im = Image.open(p).convert("RGBA")
            if e.get("nine"):
                im = nine_resize(im, e["w"], e["h"], e["nine"])
            elif im.size != (e["w"], e["h"]):
                im = im.resize((e["w"], e["h"]), Image.LANCZOS)
            if e.get("opacity", 255) < 255:
                im = im.copy()
                im.putalpha(im.getchannel("A").point(lambda v: v * e["opacity"] // 255))
            canvas.alpha_composite(im, (e["x"], e["y"]))
        elif k == "text":
            col = e.get("font", {}).get("color", "#FFFFFF")
            if isinstance(col, str) and col.startswith("@palette."):
                col = pal.get(col.split(".", 1)[1], "#FFFFFF")
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
                    t = (e.get("value", e["min"]) - e["min"]) / sp if sp else 0
                    hx = e["x"] + int(t * (e["w"] - im.width)) + im.width // 2 - im.width // 2
                    canvas.alpha_composite(im, (hx, e["y"] + (e["h"] - im.height) // 2))
    return canvas.convert("RGB"), len(els), sorted(set(missing))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(UI, "layout", "screens", "25_config.json"))
    ap.add_argument("--page", choices=["sys", "snd"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", action="append", default=[], help="覆盖 flag，如 cfg_v_display=full（可多次）")
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as fh:
        doc = json.load(fh)
    over = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        over[k] = v
    img, n, missing = render(doc, load_palette(), args.page, over)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    img.save(args.out)
    print("OK %s ｜ 页=%s ｜ 可见元素 %d ｜ 覆盖 %s ｜ 缺件 %s"
          % (args.out, args.page, n, over or "无", missing or "无"))


if __name__ == "__main__":
    main()

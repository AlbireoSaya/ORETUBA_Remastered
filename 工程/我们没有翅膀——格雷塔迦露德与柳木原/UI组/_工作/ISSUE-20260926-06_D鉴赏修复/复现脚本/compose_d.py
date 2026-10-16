# -*- coding: utf-8 -*-
r"""compose_d.py —— D 组五屏（27/28/37/38/39）**引擎同口径 1:1 离线合成器**。

用途：vision 的缺陷清单是拿「实机导出图」量的；本轮修复必须能在**同一口径**下自证。
本脚本按引擎 `ui_widget.tjs` / `ui_theme.tjs` 的绘制口径，把 `layout/screens/*.json`
的**真实元素**（z 稳定升序、九宫格 nearest 拉伸、list 折行网格、item_variants 缩略图、
引擎绘制文字、rect 填充、slider、attach 附加层叠画）画成 1920×1080 的图 ⇒
「改前 / 改后」逐像素可比，且可对**底图烘焙物**（面板边框、槽框线、「?」、走带条）直接做像素测量。

■ 与引擎逐条对齐的口径（改一处须改两处）
  · 绘制顺序：`uiWidgetDrawScreen` 的**稳定插入排序**（z 升序、同 z 保声明序）；
  · 附加层：承载屏画完后再按普通屏叠画 `attach` 指向的屏（`uiScreenDrawAttach`）；
  · 九宫格：`uiWidgetBlitAsset` → `uiWidgetNine`（九块 **nearest** 拉伸）；
  · 无 nine：`operateStretch` 到元素 w/h（本工程的 1:1 件即等尺寸）；
  · 文字：`uiThemeLayoutText`（valign=middle ⇒ y = el.y + floor((h − lineH)/2)）＋
    `uiThemeRenderText`（align 左/中/右）；`font.bold` 用 `msyhbd.ttc`、`font.outline`
    用 PIL `stroke_width` 近似（Kirikiri 的描边机件）；
  · list：`uiWidgetListItemRect`（col = i % max_cols、row = i // max_cols）＋ `item_frame`
    九宫格逐格铺 ＋ `item_variants.thumb/prev/next/text` ＋ `item_text`/`item_buttons`；
  · rect：`colorRect(color, opacity)` ⇒ RGBA 半透明填充。

■ 用法
    python _工作\ISSUE-20260926-06_D鉴赏修复\复现脚本\compose_d.py <屏id> <out.png> [--host]
      --host：带外壳（把 39 作为承载屏的 attach 附加层一起画）
    例：python ... compose_d.py dress  out.png --host

本脚本是**只读**的：只读 layout JSON 与 krkr\assets\ui\ 素材，不写任何屏数据。
"""
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(WORK))
SCR = os.path.join(UI, "layout", "screens")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"

PAL = json.load(open(os.path.join(UI, "layout", "palette.json"), encoding="utf-8"))["colors"]
_ROOT = json.load(open(os.path.join(UI, "layout", "_root.json"), encoding="utf-8"))
_C = _ROOT.get("canvas", {"width": 1920, "height": 1080})
CANVAS = (int(_C["width"]), int(_C["height"]))


def color(v, default=(0, 0, 0)):
    if v is None:
        return default
    if isinstance(v, str) and v.startswith("@palette."):
        k = v.split(".", 1)[1]
        v = PAL[k]["value"]
    if isinstance(v, str) and v.startswith("#") and len(v) == 7:
        return (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16))
    return default


def load(name):
    r"""读屏数据。环境变量：
      * `COMPOSE_D_LAYOUT=<dir>`（绝对路径或相对 UI 组的相对路径）⇒ 从该目录读屏数据；
      * `COMPOSE_D_PRISTINE=1` ⇒ 从 `备份_修复轮前\`（D 轮输出 = 本轮修复前）读屏数据。
    两者配合 `COMPOSE_D_BG_PRISTINE=1` 即可复现**本轮修复前的完整画面**。"""
    d = os.environ.get("COMPOSE_D_LAYOUT")
    if os.environ.get("COMPOSE_D_PRISTINE") == "1":
        d = os.path.join(WORK, "备份_修复轮前")
    if d and not os.path.isabs(d):
        d = os.path.join(UI, d)
    with open(os.path.join(d or SCR, name), encoding="utf-8") as f:
        return json.load(f)


def asset_image(ref):
    r"""读素材；`COMPOSE_D_BG_PRISTINE=1` 时，**本轮改过的底图件**改读 `备份_改前\` 里的原图。"""
    fn = ref.split("/", 1)[1]
    if os.environ.get("COMPOSE_D_BG_PRISTINE") == "1":
        b = os.path.join(WORK, "备份_改前", fn)
        if os.path.exists(b):
            return Image.open(b).convert("RGBA")
    return Image.open(os.path.join(ASSETS, fn)).convert("RGBA")


def nine_blit(src, dw, dh, nine):
    """照抄 ui_widget.tjs 的 uiWidgetNine（九块 nearest 拉伸）。"""
    l, t, r, b = nine.get("l", 0), nine.get("t", 0), nine.get("r", 0), nine.get("b", 0)
    sw, sh = src.size
    scw, sch = max(0, sw - l - r), max(0, sh - t - b)
    dcw, dch = max(0, dw - l - r), max(0, dh - t - b)
    out = Image.new("RGBA", (max(1, dw), max(1, dh)), (0, 0, 0, 0))
    cells = [(0, 0, l, t, 0, 0, l, t), (l, 0, dcw, t, l, 0, scw, t),
             (l + dcw, 0, r, t, l + scw, 0, r, t),
             (0, t, l, dch, 0, t, l, sch), (l, t, dcw, dch, l, t, scw, sch),
             (l + dcw, t, r, dch, l + scw, t, r, sch),
             (0, t + dch, l, b, 0, t + sch, l, b), (l, t + dch, dcw, b, l, t + sch, scw, b),
             (l + dcw, t + dch, r, b, l + scw, t + sch, r, b)]
    for (dx, dy, ddw, ddh, sx, sy, ssw, ssh) in cells:
        if ddw <= 0 or ddh <= 0 or ssw <= 0 or ssh <= 0:
            continue
        piece = src.crop((sx, sy, sx + ssw, sy + ssh)).resize((ddw, ddh), Image.NEAREST)
        out.alpha_composite(piece, (dx, dy))
    return out


def blit_asset(canvas, ref, x, y, w, h, nine=None, opacity=255):
    art = asset_image(ref)
    if opacity < 255:
        a = art.getchannel("A").point(lambda v: v * opacity // 255)
        art.putalpha(a)
    img = nine_blit(art, w, h, nine) if nine else art.resize((max(1, w), max(1, h)), Image.NEAREST)
    canvas.alpha_composite(img, (int(x), int(y)))


def make_font(spec, default_size):
    f = spec or {}
    size = int(f.get("size", default_size))
    path = FONT_B if f.get("bold") else FONT_R
    return ImageFont.truetype(path, size), f


def draw_text(canvas, el, text):
    fnt, f = make_font(el.get("font"), 24)
    col = color(f.get("color"), (0, 0, 0))
    stroke_w = int(f.get("outline_width", 0)) if f.get("outline") else 0
    stroke_c = color(f.get("outline_color"), (0, 0, 0))
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    align = el.get("align", "left")
    valign = el.get("valign", "top")
    tw = fnt.getlength(text)
    if align == "center":
        tx = x + (w - tw) / 2.0
    elif align == "right":
        tx = x + w - tw
    else:
        tx = x
    asc, desc = fnt.getmetrics()
    th = asc + desc
    if valign == "middle":
        ty = y + (h - th) / 2.0
    elif valign == "bottom":
        ty = y + h - th
    else:
        ty = y
    d = ImageDraw.Draw(canvas)
    d.text((tx, ty), text, font=fnt, fill=col + (255,),
           stroke_width=stroke_w, stroke_fill=stroke_c + (255,) if stroke_w else None)


def list_local(el, index, part):
    """照 uiWidgetListItemRect / uiWidgetVariantRect / uiWidgetItemLocalRect 的块内局部矩形。"""
    cols = int(el.get("max_cols", 1))
    iw, ih, gap = el.get("item_w", el["w"]), el.get("item_h", 10), el.get("gap", 0)
    cx = index % cols
    cy = index // cols
    bx = el["x"] + cx * (iw + gap)
    by = el["y"] + cy * (ih + gap)
    if part is None:
        return bx, by, iw, ih
    spec = part
    return bx + spec.get("x", 0), by + spec.get("y", 0), spec.get("w", iw), spec.get("h", ih)


def draw_list(canvas, el, page=0):
    cols = int(el.get("max_cols", 1))
    rows = int(el.get("max_rows", 1))
    n = cols * rows
    opa = int(el.get("opacity", 255))
    lif = el.get("highlight")
    ifr = el.get("item_frame")
    if ifr:
        for i in range(n):
            bx, by, bw, bh = list_local(el, i, None)
            a = ifr.get("asset") or (ifr.get("state_assets") or {}).get("normal")
            blit_asset(canvas, a, bx, by, bw, bh, ifr.get("nine"),
                       int(ifr.get("opacity", opa)))
    if lif:                                  # 高亮块：page 0 ⇒ 无 focus（focus=-1）不画
        pass
    itx = el.get("item_text")
    btns = el.get("item_buttons") or []
    vv = el.get("item_variants")
    labels = el.get("labels") or []
    for i in range(n):
        idx = page * n + i
        if idx >= len(labels):
            break
        bx, by, bw, bh = list_local(el, i, None)
        if vv:
            frames = vv.get("frames") or []
            row = frames[idx] if idx < len(frames) else None
            if row:
                tx, ty, tw, th = list_local(el, i, vv.get("thumb") or {"x": 0, "y": 0, "w": bw, "h": bh})
                thumb = vv.get("thumb") or {}
                blit_asset(canvas, row[0], tx, ty, tw, th, thumb.get("nine"))
                for key in ("prev", "next"):
                    spec = vv.get(key)
                    if not spec or not spec.get("asset"):
                        continue
                    px, py, pw, ph = list_local(el, i, spec)
                    blit_asset(canvas, spec["asset"], px, py, pw, ph, spec.get("nine"))
                tsp = vv.get("text")
                if tsp:
                    lx, ly, lw, lh = list_local(el, i, tsp)
                    fake = {"kind": "text", "x": lx, "y": ly, "w": lw, "h": lh,
                            "font": tsp.get("font", el.get("font")),
                            "align": tsp.get("align", "center"),
                            "valign": tsp.get("valign", "middle")}
                    draw_text(canvas, fake, "1/%d" % len(row))
        if btns:
            for b in btns:
                bxx, byy, bww, bhh = list_local(el, i, b)
                a = b.get("asset") or (b.get("state_assets") or {}).get("normal")
                if a:
                    blit_asset(canvas, a, bxx, byy, bww, bhh, b.get("nine"), int(b.get("opacity", opa)))
                if b.get("label"):
                    fake = {"kind": "text", "x": bxx, "y": byy, "w": bww, "h": bhh,
                            "font": b.get("font", el.get("font")),
                            "align": b.get("align", "center"), "valign": "middle"}
                    draw_text(canvas, fake, b["label"])
        if itx:
            lx, ly, lw, lh = list_local(el, i, itx)
            fake = {"kind": "text", "x": lx, "y": ly, "w": lw, "h": lh,
                    "font": itx.get("font", el.get("font")),
                    "align": itx.get("align", "left"), "valign": itx.get("valign", "middle")}
            draw_text(canvas, fake, labels[idx])


def draw_slider(canvas, el):
    r = el.get("rail") or {}
    a = r.get("asset") or el.get("asset")
    if a:
        blit_asset(canvas, a, el["x"], el["y"], el["w"], el["h"], r.get("nine") or el.get("nine"))
    h = el.get("handle") or {}
    if h.get("asset"):
        hx = el["x"] + h.get("x", 0)
        hy = el["y"] + h.get("y", 0)
        blit_asset(canvas, h["asset"], hx, hy, h.get("w", 20), h.get("h", el["h"]), h.get("nine"))


def visible(el, screen):
    return el.get("visible_default", True) is not False


def draw_screen(canvas, screen, annotate=False):
    els = screen["elements"]
    order = sorted(range(len(els)), key=lambda i: els[i].get("z", 0))
    for i in order:
        el = els[i]
        k = el["kind"]
        if k == "image":
            if el.get("asset"):
                blit_asset(canvas, el["asset"], el["x"], el["y"], el["w"], el["h"],
                           el.get("nine"), int(el.get("opacity", 255)))
        elif k == "rect":
            w, h = int(el["w"]), int(el["h"])
            if w > 0 and h > 0:
                lay = Image.new("RGBA", (w, h), color(el.get("color"), (0, 0, 0))
                                + (int(el.get("opacity", 255)),))
                canvas.alpha_composite(lay, (int(el["x"]), int(el["y"])))
        elif k == "text":
            draw_text(canvas, el, str(el.get("sample", "")))
        elif k == "list":
            draw_list(canvas, el)
        elif k == "slider":
            draw_slider(canvas, el)


def compose(screen_id, out, host=False):
    canvas = Image.new("RGBA", CANVAS, (255, 255, 255, 255))
    base = os.environ.get("COMPOSE_D_LAYOUT")
    if os.environ.get("COMPOSE_D_PRISTINE") == "1":
        base = os.path.join(WORK, "备份_修复轮前")
    if base and not os.path.isabs(base):
        base = os.path.join(UI, base)
    base = base or SCR
    files = sorted(f for f in os.listdir(base) if f.endswith(".json"))
    sc = next(s for s in (load(f) for f in files) if s.get("id") == screen_id)
    draw_screen(canvas, sc)
    if host and sc.get("attach"):
        sh = next(s for s in (load(f) for f in files) if s.get("id") == sc["attach"])
        draw_screen(canvas, sh)
    canvas.convert("RGB").save(out, optimize=True)
    print("wrote", out, canvas.size)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    compose(a[0], a[1], host="--host" in a)

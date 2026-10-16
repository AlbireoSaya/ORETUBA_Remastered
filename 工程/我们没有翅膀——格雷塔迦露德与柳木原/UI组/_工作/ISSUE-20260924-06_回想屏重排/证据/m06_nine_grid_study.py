# -*- coding: utf-8 -*-
r"""M06 · 回想屏重排 · 块底板 `x_ui_msgblock.png` 九宫格实测（是否形变 + t/b 取值）

■ 问题（接口冻结书 §1 排版约束 2 / §3 素材契约）
  现 `bl.list.item_frame.nine = {l:60, t:0, r:60, b:0}`。块高从 240 压到 ~205 后，
  `t=b=0` 会把**整张 266 高的源图**纵向拉伸/压缩到 item_h ⇒ 圆角与边缘柔光被纵向压扁。
  本脚本**用引擎同口径的九宫格算法**（`krkr/game/ui_widget.tjs:145 uiWidgetNine`，
  九块分别 operateStretch + stNearest）在候选 t/b 下逐像素重绘，并给出可目视的对照图。

■ 引擎同口径要点（照抄 uiWidgetNine）
  · 源小于边距即失败（srcW < l+r || srcH < t+b）→ 本脚本先自证不触发；
  · 中段尺寸 dcw/dch 为负时钳位 0，且 dw/dh<=0 的块跳过；
  · 采样 = **nearest**（PIL 的 Image.NEAREST 同义），α 通道整体 × opacity/255。

■ 判定用事实（本脚本打印，不靠目测）
  · 源图「形体」实测：左带 (x 0..60) α 达峰值的行区间 = 竖向直边区间；
    逐行 α≥128 的左界 = 圆角曲线；由此得圆角半径 r 与柔光带宽 g ⇒ **t=b ≥ g+r 是充分条件**。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\证据\m06_nine_grid_study.py
  产物（同目录）：
    m06_msgblock_nine_compare.png   —— t=b=0 / t=b=32 的「整块 + 左上角 6× 放大」对照
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))      # <UI组>
ASSET = os.path.join(UI, "krkr", "assets", "ui", "x_ui_msgblock.png")

ITEM_H = 205            # 候选块高（4×205 = 820 ≤ 832，见接口冻结书 §1）
ITEM_W = 1349


# ─────────────────────────────────────────────── 源图形体实测
def shape_probe(path):
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    px = im.load()
    prof = [max(px[x, y][3] for x in range(0, 60)) for y in range(H)]
    mx = max(prof)
    top = next(y for y in range(H) if prof[y] >= mx * 0.99)
    bot = H - 1 - next(y for y in range(H) if prof[H - 1 - y] >= mx * 0.99)

    def left(y, thr=128):
        for x in range(0, 300):
            if px[x, y][3] >= thr:
                return x
        return None

    curve = [left(y) for y in range(0, 60)]
    first = next(y for y in range(60) if curve[y] is not None)
    straight = next(v for v in curve if v is not None and v <= min(v2 for v2 in curve if v2 is not None))
    radius = curve[first] - straight          # 首行拐点与直边的水平差 = 圆角半径
    # 柔光带：形体左界(x=straight)之外，α 从 0 升到峰值的宽度
    glow = straight
    return im, dict(size=(W, H), body_top=top, body_bot=bot, straight_x=straight,
                    corner_first_row=first, radius=radius, glow=glow)


# ─────────────────────────────────────────────── 九宫格（引擎同口径）
def nine_blit(src, dx, dy, dw, dh, nine):
    """照抄 uiWidgetNine：九块分别 nearest 拉伸；返回 (目标图, 备注)"""
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    srcW, srcH = src.size
    if srcW < l + r or srcH < t + b:
        return None, "源 %dx%d 小于边距 l+r=%d t+b=%d" % (srcW, srcH, l + r, t + b)
    scw, sch = srcW - l - r, srcH - t - b
    dcw, dch = max(0, dw - l - r), max(0, dh - t - b)
    cells = [
        (dx, dy, l, t, 0, 0, l, t),
        (dx + l, dy, dcw, t, l, 0, scw, t),
        (dx + l + dcw, dy, r, t, l + scw, 0, r, t),
        (dx, dy + t, l, dch, 0, t, l, sch),
        (dx + l, dy + t, dcw, dch, l, t, scw, sch),
        (dx + l + dcw, dy + t, r, dch, l + scw, t, r, sch),
        (dx, dy + t + dch, l, b, 0, t + sch, l, b),
        (dx + l, dy + t + dch, dcw, b, l, t + sch, scw, b),
        (dx + l + dcw, dy + t + dch, r, b, l + scw, t + sch, r, b),
    ]
    layer = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
    for (ddx, ddy, ddw, ddh, sx, sy, sw, sh) in cells:
        if ddw <= 0 or ddh <= 0 or sw <= 0 or sh <= 0:
            continue
        piece = src.crop((sx, sy, sx + sw, sy + sh)).resize((ddw, ddh), Image.NEAREST)
        layer.paste(piece, (ddx - dx, ddy - dy), piece)
    return layer, ""


def render_block(src, nine, item_h=ITEM_H, item_w=ITEM_W):
    img, note = nine_blit(src, 0, 0, item_w, item_h, nine)
    return img, note


# ─────────────────────────────────────────────── 拼图（目视对照）
def checker(w, h, c1=(112, 120, 134), c2=(84, 92, 106), s=8):
    im = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if ((x // s) + (y // s)) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=c2)
    return im


def main():
    src, facts = shape_probe(ASSET)
    print("=" * 92)
    print("M06 · 块底板九宫格实测　源件 %s" % os.path.relpath(ASSET, UI).replace("\\", "/"))
    print("=" * 92)
    print("源尺寸 %dx%d" % facts["size"])
    print("竖向直边区间（左带 x0..60 达峰值 α 的行）：y %d..%d" % (facts["body_top"], facts["body_bot"]))
    print("形体左界（α≥128 直边）：x = %d ⇒ **圆角外的柔光带 = %d px**" % (facts["straight_x"], facts["glow"]))
    print("圆角首行 y=%d、该行左界 x=%d ⇒ **圆角半径 ≈ %d px**"
          % (facts["corner_first_row"], facts["straight_x"] + facts["radius"], facts["radius"]))
    need = facts["glow"] + facts["radius"]
    print("⇒ 竖向细节区总高 = 柔光 %d + 圆角 %d = **%d px**" % (facts["glow"], facts["radius"], need))
    print("⇒ 充分条件：**t = b ≥ %d** 时圆角与柔光整段 1:1 绘制（纵向零形变）" % need)
    print()

    variants = [
        ("t=b=0（现状）", dict(l=60, t=0, r=60, b=0)),
        ("t=b=34（本次选定）", dict(l=60, t=34, r=60, b=34)),
    ]
    print("块高 item_h=%d、块宽 item_w=%d 下的九宫格目标中段：" % (ITEM_H, ITEM_W))
    for name, nine in variants:
        _, note = nine_blit(src, 0, 0, ITEM_W, ITEM_H, nine)
        scw, sch = src.size[0] - nine["l"] - nine["r"], src.size[1] - nine["t"] - nine["b"]
        dcw, dch = ITEM_W - nine["l"] - nine["r"], ITEM_H - nine["t"] - nine["b"]
        print("  %-18s 中段源 %dx%d → 目标 %dx%d（纵向缩放 %.3f，横向 %.3f）%s"
              % (name, scw, sch, dcw, dch, dch / float(sch), dcw / float(scw),
                 ("｜" + note) if note else ""))
    print()

    # 角部纵向形变量化：圆角段在目标里占多少行
    for name, nine in variants:
        t = nine["t"]
        if t == 0:
            # 整图纵向缩放 → 圆角纵向被压缩
            k = (ITEM_H - nine["t"] - nine["b"]) / float(src.size[1] - nine["t"] - nine["b"])
            rows = facts["radius"] * k
        else:
            k = 1.0
            rows = facts["radius"]
        print("  %-18s 圆角纵向实际行数 = %d × %.3f = **%.1f 行**（源 %d 行）⇒ 纵向压扁 %.0f%%"
              % (name, facts["radius"], k, rows, facts["radius"], (1 - rows / facts["radius"]) * 100))

    # ── 目视对照图：上排 = 左上角 4× 放大并排；下排 = 整块 1:1 叠放
    pad, gap = 20, 16
    crop_src, zoom = 150, 4
    rendered = []
    for name, nine in variants:
        full, note = render_block(src, nine)
        assert full is not None, note
        crop = full.crop((0, 0, crop_src, crop_src)).resize((crop_src * zoom, crop_src * zoom), Image.NEAREST)
        rendered.append((name, full, crop))

    # 量化：两种 t/b 的渲染逐像素差（证明「确实有差别、差别在哪」）
    pa, pb = rendered[0][1].load(), rendered[1][1].load()
    dmax, dn = 0, 0
    for yy in range(ITEM_H):
        for xx in range(ITEM_W):
            dd = max(abs(pa[xx, yy][i] - pb[xx, yy][i]) for i in range(4))
            if dd > dmax:
                dmax = dd
            if dd > 8:
                dn += 1
    print("\n两种 t/b 的渲染逐像素差：max=%d（0-255），|Δ|>8 的像素 %d / %d（%.2f%%）"
          % (dmax, dn, ITEM_W * ITEM_H, 100.0 * dn / (ITEM_W * ITEM_H)))

    cw = crop_src * zoom
    sheet_w = max(pad * 2 + cw * 2 + gap, pad * 2 + ITEM_W)
    sheet_h = pad + 22 + cw + gap + 22 + ITEM_H + gap + 22 + ITEM_H + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), (32, 36, 44))
    d = ImageDraw.Draw(sheet)
    y = pad
    d.text((pad, y), "左上角 %d×%d @%dx：左 t=b=0（现状） / 右 t=b=34（本次选定）" % (crop_src, crop_src, zoom),
           fill=(240, 244, 252))
    y += 22
    for i, (name, full, crop) in enumerate(rendered):
        cbg = checker(cw, cw)
        cbg.paste(crop, (0, 0), crop)
        sheet.paste(cbg, (pad + i * (cw + gap), y))
    y += cw + gap
    for name, full, crop in rendered:
        d.text((pad, y), "%s / 整块 1:1（%dx%d）" % (name, ITEM_W, ITEM_H), fill=(240, 244, 252))
        y += 22
        bg = checker(ITEM_W, ITEM_H)
        bg.paste(full, (0, 0), full)
        sheet.paste(bg, (pad, y))
        y += ITEM_H + gap
    out = os.path.join(HERE, "m06_msgblock_nine_compare.png")
    sheet.save(out)
    print("对照图：%s（%dx%d）" % (os.path.relpath(out, UI).replace("\\", "/"), sheet.width, sheet.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())

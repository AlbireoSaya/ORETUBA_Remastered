#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
eyecatch_compose.py —— 章节过场卡合成器（ISSUE-20261005-03；16:9 满屏版 ISSUE-20261005-06）
================================================================================
几何（原版 800×600 坐标系，反解自 PC 本篇实机；见 会话交接_20261005-03 §2.3）：
  相框外框 (14,16)-(274,501) ｜ 章名 (326,36) ｜ 分线1 (297,64) ｜ Chapter 行 (326,71)
  日期 右沿对齐 x≈797 / y=537（1:1 绘制）｜ 分线2 (297,564) ｜ Wing 行 (623,570)
画布布局（**16:9 满屏版**，用户 2026-10-05 定稿）：
  · 4:3 卡**贴最左**（0..1439，SCALE=1080/600=1.8）——不再是「居中＋两侧留黑」；
  · 右带 1440..1920（480 宽）填**与卡面同料同色的棋盘底纹**：
      两级抖动色从 `ot_ec{N}_bg.png` 的 **RGB 原图直取**（勿走灰度——会把暖奶油画成中性灰），
      在卡坐标系生成 10px 方块棋盘后与卡面走**同一道 LANCZOS 1.8×**；
  · 交界 x=1440 烘焙**剪开虚线**（18/14 间距、3px、#4A4A4A）＋剪刀 ✂＋竖排「沿虚线剪开」；
    Q 版人物由运行期随机贴在右带（见 emit_chibi.py / ui_story.tjs），**不在本层**。
字体：剪刀用 `seguisym.ttf`、竖排文字用 `msyh.ttc`（系统字体；缺失 ⇒ **抛错**，不静默降级
  ——用户明确要「剪刀＋文字」，降级等于悄悄改设计）。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

SCALE = 1080.0 / 600.0                    # 1.8
CARD_W = int(800 * SCALE)                 # 1440（卡贴最左）
STRIP_X = CARD_W                          # 1440
STRIP_W = 1920 - CARD_W                   # 480
INNER = (15, 17, 274, 587)   # 框内（实测外框线 (14,16)-(274,587)；照片须盖满内区，否则露底图暗纹）
POS = {"name": (326, 36), "line1": (297, 64), "chap": (326, 71),
       "line2": (297, 564), "wing": (623, 570)}
DATE_X, DATE_Y = 531, 536          # 实测反解：件 1:1 绘制（件内墨迹 (28,1) ⇒ 墨迹落 (559,537)，与实机逐像素一致）

# ---- 剪开虚线（烘焙进整卡）----
TEAR_X = CARD_W                      # 1440：卡/带交界
TEAR_COLOR = (74, 74, 74)            # #4A4A4A
TEAR_DASH, TEAR_GAP, TEAR_W = 18, 14, 3
TEAR_ICON_Y = 70
TEAR_ICON_SIZE = 46
TEAR_LABEL = "沿虚线剪开"
TEAR_LABEL_SIZE = 30
FONT_SYM = r"C:\Windows\Fonts\seguisym.ttf"
FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"


def _font(path, size, what):
    if not os.path.isfile(path):
        raise RuntimeError("eyecatch_compose：缺字体 %s（%s）——剪刀/竖排文字是定稿设计，不静默降级" % (path, what))
    return ImageFont.truetype(path, size)


def dither_colors(bg_rgba):
    """从题卡底图 **RGB 原图** 取奶油底的两级抖动色与方块边长。
    ★ 勿改成灰度取样：那会把 (248,245,242)/(246,242,237) 读成 246/243 再画成中性灰，
      右带与卡面就「一暖一冷」（2026-10-05 实测踩过）。"""
    rgb = bg_rgba.convert("RGB")
    g = rgb.convert("L")
    px = g.load()
    v0 = px[0, 5]
    P = 0
    for x in range(1, 200):
        if px[x, 5] != v0:
            P = x
            break
    if P == 0:
        P = 10                                    # 实测 800×600 系底纹方块 = 10px
    c0 = rgb.getpixel((P // 2, 5))                # 块(0,0)
    c1 = rgb.getpixel((P + P // 2, 5))            # 块(1,0)
    return c0, c1, P


def gen_cardspace(w, h, c0, c1, p, bx0, by0=0):
    """卡坐标系棋盘：块号从 (bx0,by0) 起算，值 = c0 if (bx+by) 偶 else c1（与卡面同相位延续）。"""
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        by = by0 + y // p
        for x in range(w):
            bx = bx0 + x // p
            px[x, y] = c0 if ((bx + by) & 1) == 0 else c1
    return im


def draw_tearline(im, x=TEAR_X, color=TEAR_COLOR):
    """在整卡上烘焙剪开虚线（满高）＋剪刀＋竖排文字。x＝虚线中心。"""
    d = ImageDraw.Draw(im)
    y = 0
    H = im.size[1]
    skip0, skip1 = TEAR_ICON_Y - 42, TEAR_ICON_Y + 42        # 剪刀处留缺口（真实包装的画法）
    while y < H:
        y2 = min(y + TEAR_DASH, H)
        if not (y2 > skip0 and y < skip1):
            d.rectangle([x - TEAR_W // 2, y, x + TEAR_W // 2, y2 - 1], fill=color)
        y += TEAR_DASH + TEAR_GAP
    fsym = _font(FONT_SYM, TEAR_ICON_SIZE, "剪刀符号")
    bb = d.textbbox((0, 0), "✂", font=fsym)
    d.text((x - (bb[2] - bb[0]) / 2 - bb[0], TEAR_ICON_Y - (bb[3] - bb[1]) / 2 - bb[1]),
           "✂", font=fsym, fill=color)
    fcjk = _font(FONT_CJK, TEAR_LABEL_SIZE, "竖排标签")
    ly = TEAR_ICON_Y + 60
    for ch in TEAR_LABEL:
        bb = d.textbbox((0, 0), ch, font=fcjk)
        d.text((x + 18 - bb[0], ly - bb[1]), ch, font=fcjk, fill=color)
        ly += TEAR_LABEL_SIZE + 4
    return im


def compose(ch, mmdd, photo_path, sys_dir, out_path, w=1920, h=1080):
    """合成并落盘。ch＝章号 1..6；mmdd＝'1203' 或 None（无日期）；photo_path＝照片文件或 None。"""
    s = SCALE
    bg = Image.open(os.path.join(sys_dir, "ot_ec%d_bg.png" % ch)).convert("RGBA")
    c0, c1, P = dither_colors(bg)
    card = Image.new("RGB", (w, h), c0)
    # ① 4:3 卡贴最左
    card.paste(bg.convert("RGB").resize((CARD_W, h), Image.LANCZOS), (0, 0))
    # ② 右带：与卡面同料同色（卡坐标系 10px 棋盘 → 同一道 LANCZOS 1.8×）
    w_card = int(round(STRIP_W / s))
    strip = gen_cardspace(w_card, 600, c0, c1, P, 80, 0)      # 卡 x=800 起算 ⇒ 块号 80，与卡面同相位
    card.paste(strip.resize((STRIP_W, h), Image.LANCZOS), (STRIP_X, 0))
    card = card.convert("RGBA")
    # ③ 相框照片
    notes = []
    if photo_path and os.path.isfile(photo_path):
        p = Image.open(photo_path).convert("RGB")
        bx0, by0 = int(math.floor(INNER[0] * s)), int(math.floor(INNER[1] * s))
        bx1, by1 = int(math.ceil(INNER[2] * s)), int(math.ceil(INNER[3] * s))
        bw, bh = bx1 - bx0, by1 - by0
        sc = max(bw / p.size[0], bh / p.size[1])
        p2 = p.resize((max(int(p.size[0] * sc), 1), max(int(p.size[1] * sc), 1)), Image.LANCZOS)
        ox, oy = (p2.size[0] - bw) // 2, (p2.size[1] - bh) // 2
        card.paste(p2.crop((ox, oy, ox + bw, oy + bh)), (bx0, by0))
    else:
        notes.append("无照片")
    # ④ 文字分件（卡坐标系 × 1.8，卡已贴最左 ⇒ 不再加 XOFF）
    for k, fmt in (("name", "ot_ec%d_name.png"), ("chap", "ot_ec%d_chap.png"), ("wing", "ot_ec%d_wing.png")):
        p = Image.open(os.path.join(sys_dir, fmt % ch)).convert("RGBA")
        p2 = p.resize((max(int(p.size[0] * s), 1), max(int(p.size[1] * s), 1)), Image.LANCZOS)
        x, y = POS[k]
        card.alpha_composite(p2, (int(x * s), int(y * s)))
    for k, nm in (("line1", "ot_ec_line1.png"), ("line2", "ot_ec_line2.png")):
        p = Image.open(os.path.join(sys_dir, nm)).convert("RGBA")
        p2 = p.resize((max(int(p.size[0] * s), 1), max(int(p.size[1] * s), 1)), Image.LANCZOS)
        x, y = POS[k]
        card.alpha_composite(p2, (int(x * s), int(y * s)))
    if mmdd:
        dp = os.path.join(sys_dir, "ot_ec_%s.png" % mmdd)
        if os.path.isfile(dp):
            d = Image.open(dp).convert("RGBA")
            d2 = d.resize((int(d.size[0] * s), int(d.size[1] * s)), Image.LANCZOS)
            card.alpha_composite(d2, (int(DATE_X * s), int(DATE_Y * s)))
        else:
            notes.append("缺日期件 %s" % mmdd)
    else:
        notes.append("无日期")
    # ⑤ 剪开虚线（最后画：压在卡/带之上，保证虚线完整）
    draw_tearline(card.convert("RGB")).save(out_path)
    return notes

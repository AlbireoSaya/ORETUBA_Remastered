# -*- coding: utf-8 -*-
r"""e2_make_visual_evidence.py —— 从巡演 PNG 裁出模式入口的**目视证据图**（`ISSUE-20260929-05` E2）。

输入：巡演导出帧（`临时\ui_run\runtime\savedata\shot_NN_flowchart.png`）——
      `102` = 悬停（`_over`）／`103` = 按下（`_press`）／`104` = 交叉对照（main over + frag normal）／
      `105` = 复位（normal）。
输出（落 `_工作\ISSUE-20260929-05_模式入口\证据\`）：
  · `E2_目视_入口三态对照.png` —— 四行（normal / over / press / 交叉对照），裁入口带 ×2 放大，加行标签
  · `E2_目视_入口与标题牌间隙.png` —— 入口带 ＋ 标题牌（y25..161）×2，标注间隙
  · `E2_目视_整屏.png` —— 巡演整帧（缩小到 50%）
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw

SAVE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\ui_run\runtime\savedata"
EVID = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "证据")
BAND = (20, 10, 470, 100)          # 入口带（含左右余量）
SOURCES = [("105", "normal（复位后）", (255, 255, 255)),
           ("102", "hover ⇒ x_ui_modetab_over.png", (120, 255, 160)),
           ("103", "press ⇒ x_ui_modetab_press.png", (255, 190, 120)),
           ("104", "交叉对照：main=over / frag=normal", (200, 200, 255))]


def shot(n):
    return Image.open(os.path.join(SAVE, "shot_%s_flowchart.png" % n)).convert("RGB")


def main():
    os.makedirs(EVID, exist_ok=True)
    z = 2
    rows = []
    for n, label, col in SOURCES:
        im = shot(n).crop(BAND)
        im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
        strip = Image.new("RGB", (im.width + 8, im.height + 26), (18, 18, 22))
        strip.paste(im, (4, 22))
        d = ImageDraw.Draw(strip)
        d.text((6, 6), "shot_%s  %s" % (n, label), fill=col)
        rows.append(strip)
    wmax = max(r.width for r in rows)
    h = sum(r.height + 4 for r in rows)
    sheet = Image.new("RGB", (wmax, h), (8, 8, 10))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height + 4
    sheet.save(os.path.join(EVID, "E2_目视_入口三态对照.png"))
    print("[ok] E2_目视_入口三态对照.png", sheet.size)

    # 入口带 + 标题牌（y25..161）—— 见证「与 fc.titleplate 的 8px 间隙」
    im = shot("105").crop((20, 10, 520, 175))
    im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
    canvas = Image.new("RGB", (im.width + 8, im.height + 26), (18, 18, 22))
    canvas.paste(im, (4, 22))
    d = ImageDraw.Draw(canvas)
    d.text((6, 6), "shot_105 flowchart ｜ 入口带 y25..85 与 fc.titleplate y93 的 8px 间隙（×2）",
           fill=(255, 255, 255))
    canvas.save(os.path.join(EVID, "E2_目视_入口与标题牌间隙.png"))
    print("[ok] E2_目视_入口与标题牌间隙.png", canvas.size)

    full = shot("105")
    full = full.resize((full.width // 2, full.height // 2), Image.LANCZOS)
    full.save(os.path.join(EVID, "E2_目视_整屏.png"))
    print("[ok] E2_目视_整屏.png", full.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

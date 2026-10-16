# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · 补充抽查证据（超出随机 15 组之外的定向核查）

A. 跨源合并的 4 组（同组含 ot 与 otv 两个源代号）——查是否把不同场景并成一组
B. 因「选中源 ≠ 剧本引用源」被规则滤掉的 12 行——查漏掉的是不是真 CG

输出：CG候选集\抽查证据\补充\*.png   只读源；幂等。
"""
from __future__ import annotations

import io
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CGDIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\CG背景"
EV = os.path.join(OUT, "抽查证据", "补充")
TW = 520
FONT = r"C:\Windows\Fonts\msyh.ttc"


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def strip(title, names, outname):
    ims = []
    for n in names:
        im = Image.open(os.path.join(CGDIR, n)).convert("RGB")
        k = TW / im.width
        ims.append((n, im.resize((TW, max(1, int(round(im.height * k)))), Image.LANCZOS)))
    H = max(i.height for _, i in ims)
    W = len(ims) * TW + (len(ims) - 1) * 10 + 24
    sheet = Image.new("RGB", (W, H + 84), (16, 17, 20))
    d = ImageDraw.Draw(sheet)
    d.text((12, 10), title, font=font(30), fill=(240, 240, 244))
    x = 12
    for n, im in ims:
        sheet.paste(im, (x, 60))
        d.rectangle([x, 60, x + im.width - 1, 60 + im.height - 1], outline=(90, 96, 110))
        d.text((x + 6, 60 + im.height + 6), n, font=font(22), fill=(200, 205, 215))
        x += TW + 10
    p = os.path.join(EV, outname)
    sheet.save(p, optimize=True)
    print(u"-> %s %s" % (os.path.basename(p), sheet.size))


# A. 跨源合并 4 组（组内全部已选成员）
CROSS = {
    "asu07": ["cg_asu07.png", "cg_asu07a.png", "cg_asu07b.png"],
    "asu08": ["cg_asu08.png", "cg_asu08a.png", "cg_asu08b.png"],
    "kob02": ["cg_kob02.png", "cg_kob02a.png"],
    "miy01": ["cg_miy01.png", "cg_miy01a.png"],
}

# B. 被规则滤掉但剧本确有引用者（列出该组在清单里的全部文件，含已选中的）
#    格式: 标题后缀 -> 文件列表
FILTERED = {
    "ai_04_全缺": ["cg_ai_04.png"],
    "ai_05_全缺": ["cg_ai_05.png"],
    "ai_06_缺3差": ["cg_ai_06.png", "cg_ai_06a.png", "cg_ai_06b.png", "cg_ai_06c.png"],
    "asu01_缺1差": ["cg_asu01.png", "cg_asu01a.png"],
    "hiy07_全缺": ["cg_hiy07.png"],
    "ec10_全缺": ["ec10.png"],
    "ec16_全缺": ["ec16.png"],
    "ec21_全缺": ["ec21.png"],
}


def main():
    os.makedirs(EV, exist_ok=True)
    for name, names in CROSS.items():
        strip(u"跨源合并核查 · 组 %s ｜ 全部已选差分 %d 件（判定：是否同一场景）"
              % (name, len(names)), names, u"A_跨源_%s.png" % name)
    for tag, names in FILTERED.items():
        strip(u"规则滤除核查 · %s ｜ 清单内全部文件 %d 件（判定：是否为真事件 CG）"
              % (tag, len(names)), names, u"B_滤除_%s.png" % tag)


if __name__ == "__main__":
    main()
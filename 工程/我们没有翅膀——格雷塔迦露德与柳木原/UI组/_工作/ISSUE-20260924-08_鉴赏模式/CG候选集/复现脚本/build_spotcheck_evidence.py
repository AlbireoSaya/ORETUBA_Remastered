# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · 抽查证据生成：把抽查清单里每组**全部差分**并排拼一张对照图。

只看代表图无法判断「同组是否真的只差表情/动作」，故并排全部成员。
输出：CG候选集\抽查证据\组<序号>_<组名>.png（每组一张，成员横向排列 + 文件名标注）
只读源；幂等。
"""
from __future__ import annotations

import csv
import glob
import io
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.abspath(OUT)
CGDIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\CG背景"
EV = os.path.join(OUT, "抽查证据")
LIST = os.path.join(OUT, "抽查清单.tsv")

TW = 520
FONT = r"C:\Windows\Fonts\msyh.ttc"


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def main():
    os.makedirs(EV, exist_ok=True)
    for f in glob.glob(os.path.join(EV, "*.png")):
        os.remove(f)                         # 先清掉上一轮样本的图（保留 补充\ 子目录）
    rows = list(csv.DictReader(io.open(LIST, encoding="utf-8-sig"), delimiter="\t"))
    for r in rows:
        names = r["统一名列表"].split("、")
        ims = []
        for n in names:
            im = Image.open(os.path.join(CGDIR, n)).convert("RGB")
            k = TW / im.width
            ims.append((n, im.resize((TW, max(1, int(round(im.height * k)))), Image.LANCZOS)))
        H = max(i.height for _, i in ims)
        W = len(ims) * TW + (len(ims) - 1) * 10 + 24
        sheet = Image.new("RGB", (W, H + 84), (16, 17, 20))
        d = ImageDraw.Draw(sheet)
        d.text((12, 10), u"第 %s 组  %s  ｜ 差分 %s 件  ｜ %s"
               % (r["组序号"], r["组名"], r["差分件数"], r["抽样理由"]), font=font(30), fill=(240, 240, 244))
        x = 12
        for n, im in ims:
            sheet.paste(im, (x, 60))
            d.rectangle([x, 60, x + im.width - 1, 60 + im.height - 1], outline=(90, 96, 110))
            d.text((x + 6, 60 + im.height + 6), n, font=font(22), fill=(200, 205, 215))
            x += TW + 10
        p = os.path.join(EV, u"组%s_%s.png" % (r["组序号"], r["组名"]))
        sheet.save(p, optimize=True)
        print(u"-> %s  %s" % (os.path.basename(p), sheet.size))


if __name__ == "__main__":
    main()
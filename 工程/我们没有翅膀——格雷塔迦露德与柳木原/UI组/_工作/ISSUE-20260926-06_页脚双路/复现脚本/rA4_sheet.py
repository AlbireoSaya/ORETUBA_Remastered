# -*- coding: utf-8 -*-
r"""rA4 · 对比表：左=原版日文 / 中=A 新定稿 / 右=B 保留现值
行标签 = 件名 + 中文项 + 行号
输出：PSV系统UI参考\_复核_20260926\页脚双路\页脚双路_对比.png
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
TEXT = {
    "otv_save_bg.png": "确定 / 删除数据 / 返回",
    "otv_load_bg.png": "确定 / 删除数据 / 返回",
    "otv_quick_load_bg.png": "确定 / 返回",
    "otv_bklog.png": "语音播放 / 返回",
    "otv_gm_bg1.png": "部分图片可滚动查看 / 确定 / 返回",
    "otv_mu_bg.png": "播放／停止 / 返回 / 选择",
    "otv_mv_bg.png": "播放 / 返回",
}


def orig(name):
    im = Image.open(os.path.join(SRC, name))
    if im.mode == "RGBA":
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    return im.convert("RGB").crop((FX0, FY0, FX1, FY1))


if __name__ == "__main__":
    CROPX = 90
    CW = FX1 - FX0 - CROPX
    HH = 148
    LH = HH + 10
    HEAD = 34
    LBL = 268
    GAP = 14
    W = LBL + 3 * CW + GAP * 4
    H = HEAD + LH * len(ORDER) + 18
    sheet = Image.new("RGB", (W, H), (238, 240, 246))
    d = ImageDraw.Draw(sheet)
    fh = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 19)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 14)
    xs = [GAP + LBL, GAP + LBL + CW + GAP, GAP + LBL + 2 * (CW + GAP)]
    heads = ["原版日文（PSV 烘焙）", "A 程序化·新定稿（除字底＝10 屏同背景底板 + 黑体左对齐）",
             "B 生图（保留现值）"]
    for x, t in zip(xs, heads):
        d.rectangle([x, 6, x + CW, HEAD - 6], fill=(44, 62, 110))
        d.text((x + 8, 9), t, font=fh, fill=(255, 255, 255))
    y = HEAD + 6
    for i, n in enumerate(ORDER):
        o = orig(n).crop((CROPX, 0, CROPX + CW, HH))
        a = Image.open(os.path.join(OUT, n.replace(".png", "") + "_A_程序化.png")).convert("RGB").crop(
            (CROPX, 0, CROPX + CW, HH))
        b = Image.open(os.path.join(OUT, n.replace(".png", "") + "_B_生图.png")).convert("RGB").crop(
            (CROPX, 0, CROPX + CW, HH))
        for x, im in zip(xs, [o, a, b]):
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + CW, y + HH], outline=(180, 186, 200))
        d.text((GAP + 4, y + 4), n.replace("otv_", "").replace("_bg", ""), font=fh, fill=(24, 30, 50))
        d.text((GAP + 4, y + 30), TEXT[n], font=fs, fill=(60, 72, 96))
        d.text((GAP + 4, y + 52), "行 %d / 7" % (i + 1), font=fs, fill=(120, 130, 150))
        d.text((GAP + 4, y + 74), "中文项 %d 项" % len(TEXT[n].split(" / ")), font=fs, fill=(120, 130, 150))
        y += LH
    d.text((GAP + 4, H - 24),
           "页脚区 @2× 裁片 (880,940)-(1904,1088) = 1024×148（1× 口径 (440,470)-(952,544)）；三列同一裁框。"
           "A 路中文按原文字框左端起排、图标原位；右端不等宽为现状（已按用户裁决接受）。",
           font=fs, fill=(90, 100, 120))
    p = os.path.join(OUT, "页脚双路_对比.png")
    sheet.save(p)
    print("sheet ->", p, sheet.size)

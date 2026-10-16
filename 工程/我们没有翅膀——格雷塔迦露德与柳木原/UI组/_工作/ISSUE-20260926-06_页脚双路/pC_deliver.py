# -*- coding: utf-8 -*-
r"""pC · 交付：B 路选优（run2）落盘 + 生成对比表 页脚双路_对比.png
输出目录：PSV系统UI参考\_复核_20260926\页脚双路\
"""
import sys, os, json, shutil
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
FB = os.path.join(WORK, "_证据", "B_footer")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路"); os.makedirs(OUT, exist_ok=True)

FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
CN = {
    "otv_save_bg.png": "确定 / 删除数据 / 返回",
    "otv_load_bg.png": "确定 / 删除数据 / 返回",
    "otv_quick_load_bg.png": "确定 / 返回",
    "otv_bklog.png": "语音播放 / 返回",
    "otv_gm_bg1.png": "部分图片可滚动查看 / 确定 / 返回",
    "otv_mu_bg.png": "播放／停止 / 返回 / 选择",
    "otv_mv_bg.png": "播放 / 返回",
}
PICK = {n: 2 for n in ORDER}   # 逐件选优结果（见报告）

def orig(name):
    im = Image.open(os.path.join(SRC, name))
    if im.mode == "RGBA":
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    return im.convert("RGB").crop((FX0, FY0, FX1, FY1))

if __name__ == "__main__":
    # 1) B 落盘
    for n in ORDER:
        src = os.path.join(FB, "%s_B_run%d.png" % (n.replace(".png", ""), PICK[n]))
        dst = os.path.join(OUT, n.replace(".png", "") + "_B_生图.png")
        shutil.copyfile(src, dst)
        print("B ->", dst)
    # 2) 对比表
    CROPX = 90            # 页脚裁片左起 90px 起为内容区（内容 x971 -> 裁片 91）
    CW = FX1 - FX0 - CROPX
    LH = 148 + 10
    HEAD = 34
    LBL = 250
    GAP = 14
    W = LBL + 3 * CW + GAP * 4
    H = HEAD + LH * len(ORDER) + 16
    sheet = Image.new("RGB", (W, H), (238, 240, 246))
    d = ImageDraw.Draw(sheet)
    fh = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 20)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    xs = [GAP + LBL, GAP + LBL + CW + GAP, GAP + LBL + 2 * (CW + GAP)]
    heads = ["原版日文（PSV 烘焙）", "A 程序化（除字+黑体 msyhbd 40px）",
             "B 生图（gpt-image-2.5-sunburst · run2）"]
    for x, t in zip(xs, heads):
        d.rectangle([x, 6, x + CW, HEAD - 6], fill=(44, 62, 110))
        d.text((x + 10, 9), t, font=fh, fill=(255, 255, 255))
    y = HEAD + 6
    for n in ORDER:
        o = orig(n).crop((CROPX, 0, CROPX + CW, 148))
        a = Image.open(os.path.join(OUT, n.replace(".png", "") + "_A_程序化.png")).convert("RGB").crop(
            (CROPX, 0, CROPX + CW, 148))
        b = Image.open(os.path.join(OUT, n.replace(".png", "") + "_B_生图.png")).convert("RGB").crop(
            (CROPX, 0, CROPX + CW, 148))
        for x, im in zip(xs, [o, a, b]):
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + CW, y + 148], outline=(180, 186, 200))
        d.text((GAP + 4, y + 6), n.replace("otv_", "").replace("_bg", ""), font=fh, fill=(24, 30, 50))
        d.text((GAP + 4, y + 34), CN[n], font=fs, fill=(70, 80, 100))
        d.text((GAP + 4, y + 56), "行 %d / 7" % (ORDER.index(n) + 1), font=fs, fill=(120, 130, 150))
        y += LH
    d.text((GAP + 4, H - 22), "页脚区 @2× 裁片 (880,940)-(1904,1088)＝1024×148；1× 口径 (440,470)-(952,544)。"
                              "原始页脚日文项与 A/B 均为同一裁框、同一比例。", font=fs, fill=(90, 100, 120))
    p = os.path.join(OUT, "页脚双路_对比.png")
    sheet.save(p)
    print("sheet ->", p, sheet.size)

# -*- coding: utf-8 -*-
r"""t5 · 刷新 `_复核_20260926\页脚双路\页脚双路_对比.png`（A/B/原件 三列对照印相表）

为什么要重出：该表由上一轮的 `pC_deliver.py` 产出，其中 B 列写死 `PICK=run2`；本轮按图标位移判据
把 `otv_bklog` 换成 **run1**、`otv_gm_bg1` 换成 **run3**（替换后 `*_B_生图.png` 已更新）⇒ 旧表与新交付件
不一致，属**过期证据**。本脚本按**当前交付件**重出，表头写明实际采用的 run（不覆盖原脚本，原脚本留档）。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
PICK = json.load(open(os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路", "footer_B_pick.json"),
                      encoding="utf-8"))
FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088
OFF = {"otv_save_bg.png": 4, "otv_load_bg.png": 4, "otv_quick_load_bg.png": 4, "otv_bklog.png": 4,
       "otv_gm_bg1.png": 0, "otv_mu_bg.png": 0, "otv_mv_bg.png": 0}
ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
         "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
CN = {"otv_save_bg.png": "确定 / 删除数据 / 返回", "otv_load_bg.png": "确定 / 删除数据 / 返回",
      "otv_quick_load_bg.png": "确定 / 返回", "otv_bklog.png": "语音播放 / 返回",
      "otv_gm_bg1.png": "部分图片可滚动查看 / 确定 / 返回",
      "otv_mu_bg.png": "播放／停止 / 返回 / 选择", "otv_mv_bg.png": "播放 / 返回"}

def orig(n):
    im = Image.open(os.path.join(SRC, n)).convert("RGBA")
    flat = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")
    o = OFF[n]
    return flat.crop((FX0, FY0 + o, FX1, FY1 + o))

if __name__ == "__main__":
    CROPX, CW, LH, HEAD, LBL, GAP = 90, FX1 - FX0 - 90, 158, 34, 250, 14
    W = LBL + 3 * CW + GAP * 4
    H = HEAD + LH * len(ORDER) + 34
    sheet = Image.new("RGB", (W, H), (238, 240, 246))
    d = ImageDraw.Draw(sheet)
    fh = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 20)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    xs = [GAP + LBL, GAP + LBL + CW + GAP, GAP + LBL + 2 * (CW + GAP)]
    bl = "＋".join(sorted({PICK[n]["label"] for n in ORDER if PICK[n]["replaced"]}))
    heads = ["原版日文（PSV 烘焙）", "A 程序化（除字+黑体）",
             "B 生图（gpt-image-2.5-sunburst）｜本轮换件：%s" % (bl or "无")]
    for x, t in zip(xs, heads):
        d.rectangle([x, 6, x + CW, HEAD - 6], fill=(44, 62, 110))
        d.text((x + 10, 9), t, font=fh, fill=(255, 255, 255))
    y = HEAD + 6
    for n in ORDER:
        tag = "【本轮换件：%s】" % PICK[n]["label"] if PICK[n]["replaced"] else ""
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
        d.text((GAP + 4, y + 56), tag, font=fs, fill=(170, 40, 40) if tag else (120, 130, 150))
        d.text((GAP + 4, y + 78), "Σ|Δ|=%d" % PICK[n]["metric"], font=fs, fill=(70, 80, 100))
        y += LH
    d.text((GAP + 4, H - 26), "页脚区 @2× 裁片 (880,940)-(1904,1088)＝1024×148；三列同裁框同比例。"
                              "Σ|Δ| = 图标中心位移之和（判据见 _工作\\…\\复现脚本\\s2_icon_disp.py）。",
           font=fs, fill=(90, 100, 120))
    p = os.path.join(OUT, "页脚双路_对比.png")
    sheet.save(p)
    print("sheet ->", p, sheet.size)

# -*- coding: utf-8 -*-
"""对话框九宫格图标：派生「与格子同尺寸、内容居中、等高统一」的显示用图标。

为什么需要它（M26 → M27 修订）：
  1) **清晰度**：若在 layout 里用 `nine:{l:0,t:0,r:0,b:0}` 让引擎运行期整图缩放，
     krkr 的 `operateStretch` 下采样质量差（近邻采样）⇒ 图标模糊。故预先缩放。
  2) **对齐（M27 修订）**：源 `功能图标.png` 是 3×3 网格，但**每个图标在各自格子内的
     位置并不一致**（实测内容中心 x 极差 72px / y 极差 23px），直接整格缩放再摆到格子里
     会**位置参差**。故本脚本改为：**按内容包围盒裁切 → 统一缩放到等高 → 居中放进
     与格子同尺寸的画布**，从源头消除位置差。

输出：`x_gen_dicon_<序>_<语义>.png`，尺寸 = 格子尺寸（CW×CH），内容居中、等高 = CONTENT_H。
可复跑、幂等；源只读。
"""
from __future__ import annotations
import os
from PIL import Image, ImageFilter

UI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(UI, "krkr", "assets", "ui")

CW, CH = 80, 75          # 输出画布 = 九宫格格子尺寸（layout 里 79.6667x75，取整 80x75）
CONTENT_H = 64           # 内容（图形 + 烘焙标签）统一高度
ALPHA_TH = 20            # 内容包围盒的 alpha 阈值
SHARPEN = (1, 60, 3)     # UnsharpMask(radius, percent, threshold)
# 顺序 = 用户 2026-09-20 指定（从上到下、从左往右）
ORDER = ["01_qsave", "02_qload", "07_config", "03_skip", "04_prev",
         "08_close", "05_save", "06_load", "09_repeat"]


def derive(src_path: str, dst_path: str):
    im = Image.open(src_path).convert("RGBA")
    bb = im.split()[-1].point(lambda v: 255 if v > ALPHA_TH else 0).getbbox()
    assert bb, src_path
    content = im.crop(bb)
    w, h = content.size
    tw = max(1, int(round(w * CONTENT_H / float(h))))
    content = content.resize((tw, CONTENT_H), Image.LANCZOS)
    content = content.filter(ImageFilter.UnsharpMask(*SHARPEN))
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.alpha_composite(content, ((CW - tw) // 2, (CH - CONTENT_H) // 2))
    canvas.save(dst_path)
    return bb, content.size


def main():
    for i, tag in enumerate(ORDER, start=1):
        src = os.path.join(SRC, "x_gen_icon_%s.png" % tag)
        assert os.path.exists(src), src
        dst = os.path.join(SRC, "x_gen_dicon_%02d_%s.png" % (i, tag.split("_", 1)[1]))
        bb, cs = derive(src, dst)
        print("  %-30s <- %-26s 内容%s -> %s  画布 %dx%d" % (
            os.path.basename(dst), os.path.basename(src), bb, cs, CW, CH))


if __name__ == "__main__":
    main()

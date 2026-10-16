# -*- coding: utf-8 -*-
r"""r0 · 页脚底板扩展源普查：
页脚背景在 7 件间逐像素一致（q3）。检查 超分2x 下其它 PSV 屏是否共享同一页脚背景，
以便为「7/7 都有字」的右端按钮区（⊗戻る／✿選択）提供额外背景票。
判据：干净区 (x885-965, y995-1085) 逐像素差 <=1 即同一背景。
"""
import sys, os, glob
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
REF = "otv_mv_bg.png"
RY0, RY1, RX0, RX1 = 995, 1085, 885, 965   # 各件皆空的干净区


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                   ).astype(np.float32)
    if a.shape[0] < 1088 or a.shape[1] < 1910:
        return None
    return a[930:1088, 850:1910, :3]


if __name__ == "__main__":
    ref = band(REF)
    print("ref", REF, ref.shape)
    r = ref[RY0 - 930:RY1 - 930, RX0 - 850:RX1 - 850]
    hits = []
    for p in sorted(glob.glob(os.path.join(SRC, "*.png"))):
        n = os.path.basename(p)
        b = band(n)
        if b is None:
            print("  %-26s skip (尺寸不足 %s)" % (n, Image.open(p).size))
            continue
        c = b[RY0 - 930:RY1 - 930, RX0 - 850:RX1 - 850]
        d = np.abs(c - r)
        ok = d.max() <= 1.0
        if ok:
            hits.append(n)
        print("  %-26s max=%7.2f mean=%6.3f  %s" % (n, d.max(), d.mean(), "SAME-BG" if ok else ""))
    print("\n同背景件数 =", len(hits), hits)

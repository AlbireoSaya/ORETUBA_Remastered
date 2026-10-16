# -*- coding: utf-8 -*-
r"""p5 · 文字样式标定：核心蓝 / 描边蓝 / 辉光蓝 / 字心色；连通域检查（纯 numpy + PIL，无 scipy）"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))


def fill_holes(mask_bool):
    """PIL floodfill 从四边灌入，剩余未灌到的内部空洞即 holes"""
    inv = Image.fromarray(((~mask_bool) * 255).astype(np.uint8))
    w, h = inv.size
    for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if inv.getpixel(xy) == 255:
            ImageDraw.floodfill(inv, xy, 128)
    return (np.asarray(inv) == 255)


if __name__ == "__main__":
    for name, words in bbox.items():
        im = Image.open(os.path.join(SRC, name)).convert("RGB")
        a = np.asarray(im).astype(np.float32)
        br = a[:, :, 2] - a[:, :, 0]
        lum = a.mean(axis=2)
        print("=" * 84); print(name)
        for i, w in enumerate(words):
            x0, y0, x1, y1 = w["x0"], w["y0"], w["x1"], w["y1"]
            sub = a[y0 - 6:y1 + 7, x0 - 6:x1 + 7]
            sbr = br[y0 - 6:y1 + 7, x0 - 6:x1 + 7]
            slum = lum[y0 - 6:y1 + 7, x0 - 6:x1 + 7]
            def stat(lo, hi):
                m = (sbr > lo) & (sbr <= hi)
                if m.sum() == 0: return "none"
                return "n=%5d  RGB=(%.0f,%.0f,%.0f)  b-r=%.0f" % (m.sum(), *sub[m].mean(axis=0), sbr[m].mean())
            print("  item%d x%d-%d y%d-%d" % (i + 1, x0, x1, y0, y1))
            print("     b-r>140(核心):", stat(140, 999))
            print("     100<b-r<=140:", stat(100, 140))
            print("     60<b-r<=100 :", stat(60, 100))
            print("     30<b-r<=60  :", stat(30, 60))
            print("     20<b-r<=30  :", stat(20, 30))
            # 字心：b-r>60 空洞内部
            core = sbr > 60
            holes = fill_holes(core)
            if holes.sum():
                print("     字心(空洞) n=%d RGB=(%.0f,%.0f,%.0f) lum=%.1f"
                      % (holes.sum(), *sub[holes].mean(axis=0), slum[holes].mean()))
            # 掩码 b-r>22 的行/列外扩量（相对词框）
            m22 = np.zeros_like(sbr, bool); m22[:] = sbr > 22
            ys = np.flatnonzero(m22.any(axis=1)); xs = np.flatnonzero(m22.any(axis=0))
            # 注意 sub 原点 = (y0-6, x0-6)
            print("     mask(b-r>22) 占 (%d,%d)-(%d,%d) rel框 [%d,%d,%d,%d]  px=%d"
                  % (xs[0], ys[0], xs[-1], ys[-1], xs[0] - 6, ys[0] - 6, xs[-1] - 6 - (x1 - x0), ys[-1] - 6 - (y1 - y0), m22.sum()))

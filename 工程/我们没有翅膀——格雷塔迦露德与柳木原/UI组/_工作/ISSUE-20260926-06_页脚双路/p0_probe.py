# -*- coding: utf-8 -*-
r"""p0 · 页脚区探针：先看清 7 件页脚区的像素构成（亮度直方、行/列投影、墨迹色）"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
NAMES = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png",
         "otv_bklog.png", "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]

def rep(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    print("=" * 70)
    print(name, "size", im.size)
    # 页脚区
    x0, y0, x1, y1 = 860, 940, min(1920, im.width), min(1088, im.height)
    reg = a[y0:y1, x0:x1]
    lum = reg[:, :, :3].mean(axis=2)
    print("  region", (x0, y0, x1, y1), "lum min/mean/max %.1f/%.1f/%.1f" % (lum.min(), lum.mean(), lum.max()))
    print("  alpha min/mean/max %.1f/%.1f/%.1f" % (reg[:, :, 3].min(), reg[:, :, 3].mean(), reg[:, :, 3].max()))
    # 亮部（白字）与暗部（深字）各占多少
    print("  lum>238 px:", int((lum > 238).sum()), " lum<150 px:", int((lum < 150).sum()),
          " lum<100 px:", int((lum < 100).sum()), "  total px:", lum.size)
    # 蓝饱和度
    br = reg[:, :, 2] - reg[:, :, 0]
    print("  b-r  max %.1f  mean %.1f  px(b-r>45): %d" % (br.max(), br.mean(), int((br > 45).sum())))
    # 行投影（暗字 + 亮字）
    darkrow = (lum < 150).mean(axis=1)
    litrow = (lum > 238).mean(axis=1)
    def bands(v, th):
        out = []
        st = None
        for i, x in enumerate(v):
            if x > th and st is None: st = i
            elif x <= th and st is not None: out.append((st + y0, i + y0)); st = None
        if st is not None: out.append((st + y0, len(v) + y0))
        return [(s, e) for s, e in out if e - s >= 3]
    print("  dark row bands (th .01):", bands(darkrow, 0.01))
    print("  lit  row bands (th .01):", bands(litrow, 0.01))
    # 采样几个点看颜色
    for (px, py) in [(1300, 1010), (1500, 1010), (1800, 1010), (900, 970)]:
        if py < im.height and px < im.width:
            print("   px(%d,%d)=" % (px, py), a[py, px].tolist())

if __name__ == "__main__":
    for n in NAMES:
        rep(n)

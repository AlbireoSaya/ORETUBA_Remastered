# -*- coding: utf-8 -*-
r"""pD · A 路「只除字不贴字」版本：量化补底台阶（掩码区平均亮度 vs 窗外环）"""
import sys, os, json, importlib.util
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

WORK = os.path.join(r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作", "ISSUE-20260926-06_页脚双路")
spec = importlib.util.spec_from_file_location("pA", os.path.join(WORK, "pA.py"))
pA = importlib.util.module_from_spec(spec); spec.loader.exec_module(pA)
bb = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))
EV = os.path.join(WORK, "_证据", "A_erase_only"); os.makedirs(EV, exist_ok=True)

if __name__ == "__main__":
    for name, words in bb.items():
        im = Image.open(os.path.join(pA.SRC, name)).convert("RGBA")
        a = np.asarray(im).astype(np.float32)
        band = a[pA.BY0:pA.BY1, pA.BX0:pA.BX1].copy()
        band = np.asarray(Image.alpha_composite(
            Image.new("RGBA", (pA.BX1 - pA.BX0, pA.BY1 - pA.BY0), (255, 255, 255, 255)),
            Image.fromarray(band.astype(np.uint8), "RGBA"))).astype(np.float32)
        br = band[:, :, 2] - band[:, :, 0]
        full = np.zeros(br.shape, bool)
        winall = np.zeros(br.shape, bool)
        for w in words:
            x0, y0, x1, y1 = w["x0"] - pA.BX0, w["y0"] - pA.BY0, w["x1"] - pA.BX0, w["y1"] - pA.BY0
            wx0, wx1 = x0 + pA.ICON_W, min(x1 + 7, br.shape[1])
            wy0, wy1 = max(0, y0 - 5), min(br.shape[0], y1 + 6)
            win = np.zeros(br.shape, bool); win[wy0:wy1, wx0:wx1] = True
            m = pA.dilate_bool((br > pA.BTH) & win, pA.DIL)
            full |= (m | pA.fill_holes(m)) & win
            winall |= win
        filled = pA.interp_fill(band, full, winall, br)
        lum = filled.mean(axis=2)
        # 掩码区 vs 词框上方 12..26px 的环
        ring = np.zeros_like(full)
        for w in words:
            x0, y0, x1 = w["x0"] - pA.BX0, w["y0"] - pA.BY0, w["x1"] - pA.BX0
            ring[y0 - 26:y0 - 12, x0 + pA.ICON_W:x1 + 7] = True
        res = Image.fromarray(np.clip(filled, 0, 255).astype(np.uint8), "RGBA").crop(
            (pA.FX0 - pA.BX0, pA.FY0 - pA.BY0, pA.FX1 - pA.BX0, pA.FY1 - pA.BY0)).convert("RGB")
        res.save(os.path.join(EV, name.replace(".png", "") + "_A_erase_only.png"))
        print("%-24s 掩码区 lum %.2f | 窗外环 lum %.2f | 台阶 %.2f | 掩码px %d"
              % (name, lum[full].mean(), lum[ring].mean(), lum[full].mean() - lum[ring].mean(), int(full.sum())))

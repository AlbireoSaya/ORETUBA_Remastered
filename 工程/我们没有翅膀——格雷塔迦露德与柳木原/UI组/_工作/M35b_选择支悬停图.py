# -*- coding: utf-8 -*-
r"""M35b：重出选择支的**悬停图** `x_ui_choice_over.png`（用户 2026-09-22 裁定）。

■ 问题（二审实测）
  `x_ui_choice_over.png` 与常态 `x_ui_choice_off.png` **逐像素最大差仅 4、平均差 1.14**
  ——等于没变。此前 HTML 复刻靠 replica.css 的 `:hover` 蓝底提供可见反馈，
  但那条叠色因「有组热区不该叠色」被移除（两端一致）后，**选择支的悬停就两端都没有反馈了**。

■ 修法（用户选：套用标题菜单同一套 hover 配方）
  取标题菜单 hover 的**提亮档**：RGB 向白混合 30% ＋ alpha ×1.25。
  ⚠️ **不做外扩白晕**：标题菜单那套还带「紧晕 R3 + 宽晕 R8」，但本素材画布 1135×105
  **几乎被胶囊占满**（`alpha==0` 仅 0.36%），向外扩的光晕会被画布边缘裁出硬边。
  ⚠️ 也不能直接调 `btn_states.hover(im, 0, 0)` —— 半径 0 会走到 `ImageFilter.MaxFilter(1)`，
  **实测把 Python 解释器硬崩**（无输出、退出码 127）。故此处内联同一配方，不经该函数。

■ 可回滚
  `git checkout -- krkr/assets/ui/x_ui_choice_over.png` 即可恢复 M34 原图。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
A = os.path.join(UI, "krkr", "assets", "ui")
OFF, OVER = os.path.join(A, "x_ui_choice_off.png"), os.path.join(A, "x_ui_choice_over.png")

H_WHITE, H_ALPHA = 0.30, 1.25      # 与 btn_states.py 的悬停提亮档一致


def brighten(im):
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = Image.blend(rgb, Image.new("RGB", im.size, (255, 255, 255)), H_WHITE)
    r2, g2, b2 = rgb.split()
    a2 = a.point(lambda v: max(0, min(255, int(round(v * H_ALPHA)))))
    return Image.merge("RGBA", (r2, g2, b2, a2))


def main():
    src = Image.open(OFF).convert("RGBA")
    old = Image.open(OVER).convert("RGBA")      # 改前的 over，供汇报差异
    new = brighten(src)
    new.save(OVER)

    def stats(a, b, lab):
        x = np.array(a).astype(int); y = np.array(b).astype(int)
        d = np.abs(x[..., :3] - y[..., :3]).sum(axis=2)
        e = np.abs(x[..., 3] - y[..., 3])
        print("  %-30s RGB maxDiff=%3d meanDiff=%6.1f ｜ alpha 变>8 的像素 %5d ｜ alpha 均值 %.1f→%.1f"
              % (lab, d.max(), d.mean(), int((e > 8).sum()), x[..., 3].mean(), y[..., 3].mean()))

    n = np.array(Image.open(OVER).convert("RGBA"))
    print("画布 %s ｜ alpha==0 占比 %.2f%%（留白极小，故不做外扩光晕）"
          % (Image.open(OVER).size, float((n[..., 3] == 0).mean() * 100)))
    stats(src, old, "旧 over vs 常态（问题现状）")
    stats(src, n, "新 over vs 常态（重出后）")
    ok = Image.open(OVER).size == src.size and np.abs(np.array(src).astype(int) - n.astype(int))[..., :3].sum(axis=2).max() > 30
    print("  ⇒ 画布一致 + 与常态差异明显：%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

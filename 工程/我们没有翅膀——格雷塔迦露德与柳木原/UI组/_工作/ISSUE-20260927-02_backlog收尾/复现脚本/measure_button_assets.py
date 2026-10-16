# -*- coding: utf-8 -*-
"""量「逐块按钮」三件素材的可见体几何（只读 PNG，不写工程文件）。

目的（本模块 ① 的前置）：
  · `x_ui_jump_off.png`（跳转胶囊，52×29）—— 求**可见体**（胶囊实体）的纵向范围与中心，
    及其相对「元素框中心」的偏置；给出多档 alpha 阈值下的结果，避免单一阈值下结论。
  · `x_ui_spk2_off.png`（重新播放，44×44）—— 同上（1:1 件、无 nine）。
  · `x_ui_psv_bklog_row.png`（回想行带，1526×188）—— 本模块 ② 的自证：
    行带件在 x=0..13 是否**存在可见边**（横向 alpha 剖面）、以及纵向羽化范围。

阈值口径：alpha 剖面按「整列/整行 alpha 最大值」与「均值」两路打印；
可见区间取 alpha ≥ T（T ∈ {8, 32, 64, 128, 192, 250}）的行/列集合的首末项。

用法：python measure_button_assets.py
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSUI = os.path.join(UI, "krkr", "assets", "ui")

THRS = [8, 32, 64, 128, 192, 250]


def prof(im, axis):
    """返回逐行(axis='y')/逐列(axis='x')的 (max_alpha, mean_alpha) 列表。"""
    a = im.getchannel("A")
    W, H = im.size
    out = []
    if axis == "y":
        px = a.load()
        for y in range(H):
            vals = [px[x, y] for x in range(W)]
            out.append((max(vals), sum(vals) / float(W)))
    else:
        px = a.load()
        for x in range(W):
            vals = [px[x, y] for y in range(H)]
            out.append((max(vals), sum(vals) / float(W)))
    return out


def span(p, thr):
    """alpha(max) ≥ thr 的区间 [首, 末]（含），无则 None。"""
    idx = [i for i, (mx, _) in enumerate(p) if mx >= thr]
    return (idx[0], idx[-1]) if idx else None


def report(name):
    p = os.path.join(ASSUI, name)
    im = Image.open(p).convert("RGBA")
    W, H = im.size
    print("=" * 72)
    print("%s  画布 %d×%d" % (name, W, H))
    py = prof(im, "y")
    pxs = prof(im, "x")
    print("  纵向（行）alpha 剖面：行号:max/mean（仅打 alpha 有意义处）")
    for y in range(H):
        mx, mn = py[y]
        if mx > 0:
            print("    y=%-4d max=%3d mean=%6.1f" % (y, mx, mn))
    print("  纵向可见区间（按 max alpha ≥ T）：")
    for t in THRS:
        s = span(py, t)
        if s:
            print("    T=%3d  行 %d..%d   高 %d   中心 %.1f   相对画布中心(%s)偏置 %+.1f"
                  % (t, s[0], s[1], s[1] - s[0] + 1, (s[0] + s[1]) / 2.0,
                     (H - 1) / 2.0 if H % 2 else H / 2.0,
                     (s[0] + s[1]) / 2.0 - (((H - 1) / 2.0) if H % 2 else H / 2.0)))
    print("  横向可见区间（按 max alpha ≥ T）：")
    for t in THRS:
        s = span(pxs, t)
        if s:
            print("    T=%3d  列 %d..%d   宽 %d   中心 %.1f"
                  % (t, s[0], s[1], s[1] - s[0] + 1, (s[0] + s[1]) / 2.0))
    return im


def row_band_horiz():
    name = "x_ui_psv_bklog_row.png"
    p = os.path.join(ASSUI, name)
    im = Image.open(p).convert("RGBA")
    W, H = im.size
    print("=" * 72)
    print("%s  画布 %d×%d  （本模块 ② 自证：x0..13 有无可见边）" % (name, W, H))
    px = im.getchannel("A").load()
    print("  横向 alpha（按列 max / mean），x=0..24 逐列：")
    for x in range(25):
        vals = [px[x, y] for y in range(H)]
        print("    x=%-3d max=%3d mean=%6.2f" % (x, max(vals), sum(vals) / float(H)))
    print("  ... 中段抽查：", end="")
    for x in (100, 400, 763, 1100, 1400, 1520, 1525):
        vals = [px[x, y] for y in range(H)]
        print("x=%d:max=%d/mean=%.1f " % (x, max(vals), sum(vals) / float(H)), end="")
    print()
    # 参考：旧卡件 x_ui_msgblock.png 在 x=0..13 确有可见边（对照）
    old = os.path.join(ASSUI, "x_ui_msgblock.png")
    if os.path.exists(old):
        oi = Image.open(old).convert("RGBA")
        op = oi.getchannel("A").load()
        print("  ［对照］旧卡件 x_ui_msgblock.png 画布 %s 横向 alpha x=0..12：" % (oi.size,))
        print("    " + ", ".join(str(max(op[x, y] for y in range(oi.height)))
                                 for x in range(13)))
        print("    （用于确认「旧件确有柔光边 ⇒ 当年 +13 的前提」）")
    # ★ 横向「有没有可见边」还要看 RGB（可能不是透明边而是描边/暗线）：列均值必须与板中段一致
    print("  横向 RGB 列均值（x=0..16）与板中段抽查（判断有无横向描边/亮度台阶）：")
    rpx = im.load()
    for x in list(range(17)) + [300, 700, 1200, 1525]:
        rs = gs = bs = 0
        for y in range(H):
            r, g, b, _a = rpx[x, y]
            rs += r; gs += g; bs += b
        print("    x=%-4d RGB 列均值 = (%7.3f, %7.3f, %7.3f)" % (x, rs / H, gs / H, bs / H))
    # 纵向羽化
    py = prof(im, "y")
    print("  纵向 alpha（按行 max），仅打 max>0 的首末与分档区间：")
    for t in (8, 32, 128, 250):
        s = span(py, t)
        if s:
            print("    T=%3d  行 %d..%d（高 %d）中心 %.1f" % (t, s[0], s[1], s[1] - s[0] + 1,
                                                         (s[0] + s[1]) / 2.0))


if __name__ == "__main__":
    for n in ("x_ui_jump_off.png", "x_ui_spk2_off.png"):
        report(n)
    row_band_horiz()

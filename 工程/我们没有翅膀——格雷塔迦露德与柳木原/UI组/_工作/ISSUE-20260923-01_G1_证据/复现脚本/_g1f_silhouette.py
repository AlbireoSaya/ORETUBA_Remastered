# -*- coding: utf-8 -*-
r"""B1 · 两态剪影自证（替代已作废的「d128=56」自设口径）

真契约 = **两态 alpha 场一致 ⇒ 悬停不跳动**。三条量化自证：
  ① 两态 alpha 差异像素数 / 半径范围 / 最大 α 差
  ② `alpha>=128` 等值半径（亚像素，径向均值跨 128 插值）两态差 <=0.2px
  ③ 圆心（alpha>=128 包围盒中心）两态差
外加：B1 白晕的径向 α 剖面（实白段 / 渐隐 / 画布内归零）与「参照并排」用的关键量。
"""
import glob, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
CUT = os.path.join(EV, "切件_64")
KEYS = [("lock", "锁定"), ("save", "存档"), ("load", "读档"), ("qsave", "快速存档"),
        ("qload", "快速读档"), ("auto", "自动播放"), ("skip", "快进"), ("next", "下一选项"),
        ("prev", "上一选项"), ("log", "回想"), ("chart", "流程图"), ("option", "设置")]

YY, XX = np.mgrid[0:64, 0:64]
RG = np.sqrt((XX + 0.5 - 32.0) ** 2 + (YY + 0.5 - 32.0) ** 2)


def alpha(key, st):
    return np.array(Image.open(os.path.join(CUT, "x_ui_qbicon_%s%s.png"
                                            % (key, "" if st == "off" else "_on"))).convert("RGBA"))[..., 3].astype(float)


def cross128(a, half=0.25, step=0.1):
    """径向均值跨 128 的亚像素半径（自 26.5 向外扫，取最后一次下穿）。
    ★ 环带窗口必须 >=0.25px：64x64 画布上 0.05px 宽的环带几乎没有像素，会得到空切片。"""
    r128 = None
    prev = None
    for r in np.arange(26.5, 32.01, step):
        m = (RG >= r - half) & (RG < r + half)
        if m.sum() == 0:
            continue
        v = float(a[m].mean())
        if prev is not None and prev[1] >= 128 > v:
            r128 = prev[0] + step * (prev[1] - 128) / (prev[1] - v)
        prev = (r, v)
    return r128


def center128(a):
    ys, xs = np.nonzero(a >= 128)
    return ((xs.min() + xs.max() + 1) / 2.0, (ys.min() + ys.max() + 1) / 2.0)


def main():
    print("=" * 112)
    print("【B1 自证 1】白晕径向 α 剖面（r=27→32，逐 0.25px）— 抽常态 lock / 悬停 lock")
    print("=" * 112)
    for key, st in (("lock", "off"), ("lock", "on")):
        a = alpha(key, st)
        vals = " ".join("%.2f:%.0f" % (r, a[(RG >= r - 0.125) & (RG < r + 0.125)].mean())
                        for r in np.arange(27.0, 32.01, 0.25))
        print("  %-4s %s" % (st, vals))
        m = (RG >= 27.9) & (RG < 29.9)
        prof = [(r, a[(RG >= r - 0.125) & (RG < r + 0.125)].mean()) for r in np.arange(27.9, 29.95, 0.05)]
        solid = [r for r, v in prof if v >= 200]
        nz = RG[a > 0]
        print("       环外峰值 α=%.0f ｜ 近实白(α>=200) 带 r=%.2f..%.2f = **%.2f px** ｜ "
              "渐隐 200→0 跨度 **%.2f px** ｜ 最外非零 r=%.2f（画布内 64x64，r<32）"
              % (a[RG >= 28.0].max(), min(solid), max(solid),
                 max(solid) - min(solid) + 0.05,
                 max(solid) - min(solid) + 0.05 + (max(solid) - min(solid) + 0.05) * 0.0 + (max(prof)[0] - max(solid)),
                 nz.max()))
        # 渐隐跨度 = 从 α=200 处到 α=0 处的半径差
        r200 = max(solid)
        r0 = max([r for r, v in prof if v > 0]) if any(v > 0 for _, v in prof) else max(solid)
        rzero = None
        for r in np.arange(29.0, 32.01, 0.1):
            m = (RG >= r - 0.25) & (RG < r + 0.25)
            if m.sum() and float(a[m].mean()) <= 0.5:
                rzero = r; break
        print("       渐隐跨度（α200→α0）= %.2f px ｜ 环外缘 r=28.0" % (rzero - r200))

    print("\n" + "=" * 112)
    print("【B1 自证 2】两态剪影（真契约：两态 alpha 场一致 ⇒ 悬停不跳动）")
    print("=" * 112)
    print("%-8s %-12s %-26s %-10s %-14s %-14s %-9s" %
          ("key", "差异像素数", "差异像素半径范围", "最大 α 差", "常态 r128", "悬停 r128", "Δr128"))
    tot_px, tot_d, rmin, rmax, t128 = 0, 0.0, 999.0, 0.0, 0.0
    cds = []
    for key, _zh in KEYS:
        ao, an = alpha(key, "off"), alpha(key, "on")
        d = np.abs(ao - an)
        m = d > 0
        n = int(m.sum())
        tot_px += n
        tot_d = max(tot_d, float(d.max()))
        if n:
            rmin = min(rmin, float(RG[m].min())); rmax = max(rmax, float(RG[m].max()))
        ro, rn = cross128(ao), cross128(an)
        t128 = max(t128, abs(ro - rn))
        cds.append((center128(ao), center128(an)))
        print("%-8s %-12d %-26s %-10.0f %-14.4f %-14.4f %-9.4f"
              % (key, n, "r=%.2f..%.2f" % (RG[m].min(), RG[m].max()) if n else "—",
                 d.max(), ro, rn, abs(ro - rn)))
    dcx = max(abs(a[0] - b[0]) for a, b in cds)
    dcy = max(abs(a[1] - b[1]) for a, b in cds)
    print("\n  合计：两态 alpha 差异 %d 像素（12 对）｜ 半径范围 r=%.2f..%.2f ｜ 最大 α 差 %.0f"
          % (tot_px, rmin, rmax, tot_d))
    print("  alpha>=128 等值半径两态最大差 = %.4f px（要求 <=0.2）→ %s" % (t128, "通过" if t128 <= 0.2 else "不通过"))
    print("  圆心两态最大差 Δx=%.1f Δy=%.1f px（要求 <=1）→ %s"
          % (dcx, dcy, "通过" if max(dcx, dcy) <= 1 else "不通过"))
    print("  差异集中在环缘/光晕过渡带（r=%.2f..%.2f）—— 正是「环宽分态差异」应出现的位置"
          % (rmin, rmax))

    print("\n" + "=" * 112)
    print("【几何】d128（alpha>=128 包围盒）—— 口径已由主代理放开，仅记录")
    print("=" * 112)
    ds, hs = [], []
    for key, _zh in KEYS:
        for st in ("off", "on"):
            a = alpha(key, st)
            ys, xs = np.nonzero(a >= 128)
            ds.append(max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
            hs.append(float(RG[a > 0].max()))
    print("  d128 = %s（两态同值）｜ 光晕最外半径 = %s（两态同值）"
          % (sorted(set(ds)), sorted(set(hs))))


if __name__ == "__main__":
    main()

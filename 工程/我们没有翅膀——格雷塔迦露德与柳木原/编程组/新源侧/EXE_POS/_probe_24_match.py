#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_24_match.py — 用 CHR.LPK 取出的立绘位图, 对 baseline.png 做模板匹配, 反解引擎落位 (只读/只写本模块目录).

原理: 画布 800x600 与立绘为 1:1 绘制 ⇒ 立绘像素应与截图逐像素一致(除被遮挡/被对话框压住处).
      用「稀疏关键点距离阈值投票」找 (left, top), 再据此算引擎写入的锚点 x = left + offset_x。

用法:
  python -X utf8 _probe_24_match.py _chr/asu02a.elg.elg _chr/mas01c.elg.elg _chr/asu02.elg.elg _chr/mas01.elg.elg
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\lucifen\Lucifen-Tools")
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")

import numpy as np
from PIL import Image
import elg2png

SHOT = r"E:\ZCode Workspace\Galgame\临时\layer_exp\shots\baseline.png"
X0, Y0 = 6, 30          # 客户端原点(实测)


def load_sprite(p):
    r = elg2png.Reader(open(p, "rb").read())
    img = r.decode()
    return r, img


def main():
    paths = sys.argv[1:]
    shot = Image.open(SHOT).convert("RGB")
    S = np.asarray(shot, dtype=np.int16)            # (H,W,3)
    S = S[Y0:Y0 + 600, X0:X0 + 800]                 # 取客户端区
    H, W, _ = S.shape
    print("client canvas", W, H)

    for p in paths:
        r, img = load_sprite(p)
        A = np.asarray(img.convert("RGBA"), dtype=np.int16)
        ph, pw, _ = A.shape
        alpha = A[:, :, 3]
        print("=== %s  %dx%d  offset=(%d,%d)  opaque=%d" %
              (os.path.basename(p), pw, ph, r.offset_x, r.offset_y, int((alpha > 200).sum())))

        # 稀疏关键点: 只取不透明像素, 每 7 像素取 1
        ys, xs = np.where(alpha > 240)
        sel = np.zeros(len(ys), bool)
        sel[::max(1, len(ys) // 400)] = True
        ys, xs = ys[sel], xs[sel]
        cols = A[ys, xs, :3]
        print("   keypoints=%d" % len(ys))

        # 投票累加: acc[A,B] 中 A=T0+ph, B=L0+pw  (T0/L0 = 立绘左上角)
        acc = np.zeros((H + ph, W + pw), dtype=np.int16)
        for py, px, c in zip(ys, xs, cols):
            d = np.abs(S - c).sum(axis=2)           # (H,W)
            m = (d < 36).astype(np.int16)
            acc[ph - py:ph - py + H, pw - px:pw - px + W] += m
        A0, B0 = np.unravel_index(np.argmax(acc), acc.shape)
        T, L = A0 - ph, B0 - pw
        best = acc[A0, B0]
        print("   coarse best: left=%d top=%d votes=%d/%d" % (L, T, best, len(ys)))

        # 精修: 在 best 附近用全部不透明像素算 MAD / 命中率
        win = 3
        bestcfg = None
        for dL in range(-win, win + 1):
            for dT in range(-win, win + 1):
                l, t = L + dL, T + dT
                if l < -pw or t < -ph or l >= W or t >= H:
                    continue
                # 采样全部不透明像素(步长 3)
                sub = alpha[::3, ::3]
                yy, xx = np.where(sub > 240)
                vy = t + yy * 3
                vx = l + xx * 3
                ok = (vy >= 0) & (vy < H) & (vx >= 0) & (vx < W)
                vy, vx = vy[ok], vx[ok]
                ref = A[(yy * 3)[ok], (xx * 3)[ok], :3]
                d = np.abs(S[vy, vx] - ref).sum(axis=1)
                hit = float((d < 30).mean()) if len(d) else 0.0
                if bestcfg is None or hit > bestcfg[0]:
                    bestcfg = (hit, l, t, float(d.mean()))
        hit, l, t, mad = bestcfg
        print("   refined: left=%d top=%d  hit=%.4f  MAD=%.1f" % (l, t, hit, mad))
        print("   => anchor(cx)= left+offset_x = %d   anchor(cy)= top+offset_y = %d"
              % (l + r.offset_x, t + r.offset_y))
        print("   => anchor as fraction of 1280-space: %.1f / %.1f"
              % ((l + r.offset_x) * 1.6, (t + r.offset_y) * 1.6))


if __name__ == "__main__":
    main()

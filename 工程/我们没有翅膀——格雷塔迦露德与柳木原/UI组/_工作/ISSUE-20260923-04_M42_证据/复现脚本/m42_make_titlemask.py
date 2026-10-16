# -*- coding: utf-8 -*-
"""标题屏菜单区遮罩素材生成器（M42 定稿版，可复现）

用途：重新生成 `krkr/assets/ui/x_ui_titlemask_menu.png` 及四档备选。
形状模型（M42 五轮定稿）：**椭圆基底 + 多频正弦扰动 + 径向浓度衰减**
    r  = hypot(dx/A, dy/B)                  椭圆归一化半径（半轴 A=280 / B=580）
    r' = r · (1 + amp · N(θ, r, x, y))      多频扰动（不规则叶瓣，打破对称）
    α  = 255 · (1 − smoothstep((r' − C0)/FADE))   中心满浓度、向外平滑衰减
    N  = 0.50·sin(3θ+1.1) + 0.30·sin(5θ+2.7) + 0.15·sin(8θ+0.4)
       + 0.20·sin(2.3πr+0.8) + 0.18·sin(x/97+1.9)·sin(y/113+0.6)

档位（用户 2026-09-23 在量化对照图里选定 **P3**）：
    P1 amp=0.28 C0=0.58 FADE=0.55  极不规则，但菜单四角浓度只剩 17/255
    P2 = P1 + 墨点飞溅
    P3 amp=0.18 C0=0.75 FADE=0.40  ★ 定稿：不规则度几乎不变（12 向极差 120 vs 124），四角保住 105–252
    P4 = P3 + 墨点飞溅
落盘素材的**强度旋钮是元素 `title.mask_menu` 的 `opacity`**（素材峰值恒为 255）：
    99% → 252 ｜ 85% → 217 ｜ 25% → 64 ｜ 18% → 46 ｜ **10%（定稿）→ 26**

用法：python m42_make_titlemask.py            # 只生成四档到本目录（不落盘到 assets）
      python m42_make_titlemask.py --install  # 另把 P3 复制到 krkr/assets/ui/x_ui_titlemask_menu.png
"""
import argparse, math, os, shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))                       # 证据目录（四档产物落这里）
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))            # …/UI组
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

X0, Y0, W, H = 0, 140, 880, 940          # 元素摆放：x0 y140，素材 880×940
CX, CY = 424 - X0, 708 - Y0              # 椭圆中心（菜单包围盒 x256..592 / y360..1056 的中心）
A, B = 280.0, 580.0
SPLASH = [(150, 300, 46, 70), (740, 830, 34, 52), (250, 900, 26, 44)]   # 墨点飞溅（画布坐标）
VARIANTS = {"P1": (0.28, 0.58, 0.55, False), "P2": (0.28, 0.58, 0.55, True),
            "P3": (0.18, 0.75, 0.40, False), "P4": (0.18, 0.75, 0.40, True)}


def smoothstep(t):
    if t <= 0.0: return 0.0
    if t >= 1.0: return 1.0
    return t * t * (3.0 - 2.0 * t)


def noise(theta, r, x, y):
    return (0.50 * math.sin(3.0 * theta + 1.1)
            + 0.30 * math.sin(5.0 * theta + 2.7)
            + 0.15 * math.sin(8.0 * theta + 0.4)
            + 0.20 * math.sin(2.3 * math.pi * r + 0.8)
            + 0.18 * math.sin(x / 97.0 + 1.9) * math.sin(y / 113.0 + 0.6))


def build(amp, c0, fade, splash):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = []
    for y in range(H):
        for x in range(W):
            rx, ry = (x - CX) / A, (y - CY) / B
            r = math.hypot(rx, ry)
            rp = r * (1.0 + amp * noise(math.atan2(ry, rx), r, x, y))
            a = 255.0 * (1.0 - smoothstep((rp - c0) / fade))
            if splash:
                for (sx, sy, pa, pr) in SPLASH:
                    a += pa * (1.0 - smoothstep(math.hypot(x - (sx - X0), y - (sy - Y0)) / pr))
            px.append((0, 0, 0, max(0, min(255, int(round(a))))))
    im.putdata(px)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true", help="把定稿档 P3 复制到 krkr/assets/ui/")
    a = ap.parse_args()
    for tag, (amp, c0, fade, sp) in VARIANTS.items():
        im = build(amp, c0, fade, sp)
        p = os.path.join(OUT, "mask_%s_%s.png" % (tag, "泼墨带飞溅" if sp else "泼墨无飞溅"))
        im.save(p)
        al = im.getchannel("A")
        rs = []
        for i in range(12):
            th = 2 * math.pi * i / 12; last = 0
            for rr in range(20, 620, 2):
                xx, yy = int(CX + rr * math.cos(th)), int(CY + rr * math.sin(th) * 1.6)
                if 0 <= xx < W and 0 <= yy < H and al.getpixel((xx, yy)) >= 128: last = rr
            rs.append(last)
        pts = ((256, 360), (592, 360), (256, 1056), (592, 1056), (424, 708))
        print("  %s amp=%.2f C0=%.2f FADE=%.2f 飞溅=%s ｜ 12向等值半径极差=%d ｜ 菜单点α=%s"
              % (tag, amp, c0, fade, sp, max(rs) - min(rs),
                 "/".join(str(al.getpixel((p[0] - X0, p[1] - Y0))) for p in pts)))
    if a.install:
        shutil.copyfile(os.path.join(OUT, "mask_P3_泼墨无飞溅.png"),
                        os.path.join(ASSETS, "x_ui_titlemask_menu.png"))
        print("  已安装定稿档 P3 → krkr/assets/ui/x_ui_titlemask_menu.png")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""M42 遮罩的**形状度量审计**（一审打回项 R5 的独立复核，2026-09-23）

背景：原生成器 `m42_make_titlemask.py` 用「12 向等值半径极差」证明"形状确实不规则"，
      并附注「矩形/椭圆时为 0」。一审指出该度量有缺陷：采样时把 y 方向乘了 1.6，
      而椭圆半轴比 B/A = 580/280 = 2.07，二者不匹配 ⇒ **理想椭圆在该度量下也不为 0**。

本脚本做三件事（只读，不写任何图片）：
  1. 复算原度量：定稿档 P3 与 amp=0 的理想椭圆，给出两者数值（证明该度量不能区分）；
  2. 给出**归一化度量**：在椭圆归一化半径域取 α=128 等值线，极差对理想椭圆应为 ~0；
  3. 复算菜单包围盒四角/中心浓度与四边边缘 α（用于文档口径核对）。

用法：python m42_metric_audit.py
"""
import math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.abspath(os.path.join(HERE, ".."))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSET = os.path.join(UI, "krkr", "assets", "ui", "x_ui_titlemask_menu.png")

X0, Y0, W, H = 0, 140, 880, 940
CX, CY = 424 - X0, 708 - Y0
A, B = 280.0, 580.0


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


def ideal_ellipse():
    """amp=0 的理想椭圆（P3 的 C0/FADE），返回 RGBA Image。"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = []
    for y in range(H):
        for x in range(W):
            r = math.hypot((x - CX) / A, (y - CY) / B)
            a = 255.0 * (1.0 - smoothstep((r - 0.75) / 0.40))
            px.append((0, 0, 0, max(0, min(255, int(round(a))))))
    im.putdata(px)
    return im


def metric_old(al):
    """原生成器的度量：12 向、y 乘 1.6、取 α≥128 的最大采样半径（步长 2）。"""
    rs = []
    for i in range(12):
        th = 2 * math.pi * i / 12
        last = 0
        for rr in range(20, 620, 2):
            xx, yy = int(CX + rr * math.cos(th)), int(CY + rr * math.sin(th) * 1.6)
            if 0 <= xx < W and 0 <= yy < H and al.getpixel((xx, yy)) >= 128:
                last = rr
        rs.append(last)
    return rs


def metric_norm(al, n=72):
    """归一化度量：真几何采样，α 首次跌破 128 处换算为椭圆归一化半径 r_norm。

    理想椭圆下 r_norm 恒定（极差 ~0）；带扰动时极差越大越不规则。
    ⚠️ 只统计**等值线落在画布内**的方向：椭圆在画布外（下缘、左右角，半径 B=580
       远超画布高度）的方向上，射线会先离开画布而没有真正的等值线穿越——这类方向
       必须剔除并单独计数，否则"画布裁切"会被误当成"形状不规则"（本脚本初版即犯此错，
       理想椭圆一度算出 0.3127 的假极差）。
    返回 (vals, n_used, n_clipped)。
    """
    vals, clipped = [], 0
    for i in range(n):
        th = 2 * math.pi * i / n
        cross = None
        prev = None
        left_canvas = False
        for rr in range(6, 900, 1):
            xx, yy = int(round(CX + rr * math.cos(th))), int(round(CY + rr * math.sin(th)))
            if not (0 <= xx < W and 0 <= yy < H):
                left_canvas = True
                break
            a = al.getpixel((xx, yy))
            if prev is not None and prev >= 128 > a:
                cross = rr
                break
            prev = a
        if cross is None:
            if left_canvas:
                clipped += 1
            continue
        vals.append(math.hypot(cross * math.cos(th) / A, cross * math.sin(th) / B))
    return vals, len(vals), clipped


def main():
    if not os.path.exists(ASSET):
        print("!! 找不到素材：%s" % ASSET)
        return 1
    disk = Image.open(ASSET).convert("RGBA")
    al = disk.getchannel("A")
    print("素材：%s" % ASSET)
    print("  尺寸=%s  模式=%s  md5 见下方 shell 校验" % (disk.size, disk.mode))

    # 0. 基本剖面
    import hashlib
    raw = open(ASSET, "rb").read()
    print("  字节=%d  md5=%s" % (len(raw), hashlib.md5(raw).hexdigest()))
    nonblack = sum(1 for p in disk.getdata() if p[:3] != (0, 0, 0))
    print("  非黑像素（RGB≠0）= %d" % nonblack)

    # 1. 原度量
    r_p3 = metric_old(al)
    ie = ideal_ellipse()
    r_id = metric_old(ie.getchannel("A"))
    print("\n[1] 原度量（12 向、y×1.6、步长 2）")
    print("    定稿 P3      : min=%d max=%d 极差=%d" % (min(r_p3), max(r_p3), max(r_p3) - min(r_p3)))
    print("    amp=0 理想椭圆: min=%d max=%d 极差=%d  ← 一审指出的基线" % (min(r_id), max(r_id), max(r_id) - min(r_id)))

    # 2. 归一化度量
    v_p3, h1, m1 = metric_norm(al)
    v_id, h2, m2 = metric_norm(ie.getchannel("A"))
    print("\n[2] 归一化度量（真几何采样 72 向、α 首次跌破 128、换算椭圆归一化半径）")
    print("    定稿 P3      : n=%d 越界漏测=%d r_norm min=%.4f max=%.4f 极差=%.4f (=相对 %.1f%%)"
          % (h1, m1, min(v_p3), max(v_p3), max(v_p3) - min(v_p3),
             100.0 * (max(v_p3) - min(v_p3)) / (sum(v_p3) / len(v_p3))))
    print("    amp=0 理想椭圆: n=%d 越界漏测=%d r_norm min=%.4f max=%.4f 极差=%.4f"
          % (h2, m2, min(v_id), max(v_id), max(v_id) - min(v_id)))
    print("    ⇒ 理想椭圆基线≈0，P3 极差显著 >0，此度量才可用于证明不规则")

    # 3. 菜单点 / 边缘
    pts = ((256, 360), (592, 360), (256, 1056), (592, 1056), (424, 708))
    print("\n[3] 菜单包围盒四角+中心 α（素材，锁 255）：%s"
          % "/".join(str(al.getpixel((p[0] - X0, p[1] - Y0))) for p in pts))
    lmax = max(al.getpixel((0, y)) for y in range(H))
    rmax = max(al.getpixel((W - 1, y)) for y in range(H))
    tmax = max(al.getpixel((x, 0)) for x in range(W))
    bmax = max(al.getpixel((x, H - 1)) for x in range(W))
    lcnt = sum(1 for y in range(H) if al.getpixel((0, y)) > 0)
    tcnt = sum(1 for x in range(W) if al.getpixel((x, 0)) > 0)
    print("[4] 四边边缘 α 最大值/非零列数：左 %d/%d ｜ 右 %d/%d ｜ 上 %d/%d（列区间见下）｜ 下 %d/%d"
          % (lmax, lcnt, rmax, sum(1 for y in range(H) if al.getpixel((W - 1, y)) > 0),
             tmax, tcnt, bmax, sum(1 for x in range(W) if al.getpixel((x, H - 1)) > 0)))
    xs = [x for x in range(W) if al.getpixel((x, 0)) > 0]
    if xs:
        print("    上缘非零列 x 区间 = %d..%d" % (min(xs), max(xs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

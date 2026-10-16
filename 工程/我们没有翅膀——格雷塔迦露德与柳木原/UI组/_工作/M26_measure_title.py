# -*- coding: utf-8 -*-
"""M26 · 标题 7 按钮「文字行带中心」像素实测（左 62% 宽的 alpha 行剖面，取首末非空行）。

输出：每件的
  - 完整内容 bbox（alpha>th 全图）
  - 文字行带 y0..y1（左 62% 宽列的 alpha 行剖面首末非空行）
  - 文字行带中心
并给出按 T=852、k=0.66 反算的 cell_y（一位小数），以及新文字中心。

用法：python M26_measure_title.py [alpha_threshold]
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UI = os.path.join(ROOT, "krkr", "assets", "ui")

NAMES = [
    "x_gen_menu_1_start.png",
    "x_gen_menu_2_continue.png",
    "x_gen_menu_3_load.png",
    "x_gen_menu_4_flowchart.png",
    "x_gen_menu_5_extra.png",
    "x_gen_menu_6_config.png",
    "x_gen_menu_7_exit.png",
]

T = 852.0   # 目标文字中心（画布坐标）
K = 0.66    # 统一倍率（保持 M25）

from PIL import Image

def analyze(path, th, left_frac=0.62):
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    a = im.getchannel("A")
    px = a.load()
    # 完整内容 bbox
    bb = im.getbbox()  # 用 alpha>0 的 bbox
    # 更严谨：按阈值算 bbox
    xs0, ys0, xs1, ys1 = W, H, -1, -1
    for y in range(H):
        for x in range(W):
            if px[x, y] > th:
                if x < xs0: xs0 = x
                if x > xs1: xs1 = x
                if y < ys0: ys0 = y
                if y > ys1: ys1 = y
    # 文字行带：左 62% 宽列
    xlim = int(W * left_frac)
    rows = []
    for y in range(H):
        n = 0
        for x in range(xlim):
            if px[x, y] > th:
                n += 1
                break
        if n:
            rows.append(y)
    if rows:
        ty0, ty1 = rows[0], rows[-1]
    else:
        ty0 = ty1 = None
    return dict(size=(W, H), content_bbox=(xs0, ys0, xs1, ys1),
                band=(ty0, ty1),
                band_center=(None if ty0 is None else (ty0 + ty1) / 2.0),
                xlim=xlim)


def main():
    th = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    print("alpha 阈值 th = %d ；文字行带取样宽度 = 左侧 62%%（0..%d）" % (th, int(439 * 0.62)))
    print()
    hdr = "%-28s %-16s %-14s %-9s %-9s %-10s %-9s %-10s" % (
        "文件", "完整内容bbox(y0..y1)", "文字行带(y0..y1)", "行带中心", "cell_y", "cell_y(1位)", "新文字中心", "误差")
    print(hdr)
    print("-" * len(hdr))
    res = []
    for n in NAMES:
        p = os.path.join(UI, n)
        r = analyze(p, th)
        c = r["band_center"]
        cell_y = T - c * K
        cell_y1 = round(cell_y, 1)
        new_center = cell_y1 + c * K
        err = new_center - T
        res.append(dict(file=n, band=r["band"], center=c, cell_y_raw=cell_y,
                        cell_y=cell_y1, new_center=new_center, err=err,
                        content_bbox=r["content_bbox"]))
        print("%-28s %-16s %-14s %-9s %-9.3f %-10.1f %-9.3f %+.3f" % (
            n, "%d..%d" % (r["content_bbox"][1], r["content_bbox"][3]),
            "%d..%d" % r["band"], c, cell_y, cell_y1, new_center, err))
    print()
    cs = [x["center"] for x in res]
    print("文字行带中心极差 = %.2f .. %.2f = %.2f px（源图，未缩放）" % (min(cs), max(cs), max(cs) - min(cs)))
    nc = [x["new_center"] for x in res]
    print("新文字中心极差   = %.3f .. %.3f = %.3f px（目标 T=%.1f）" % (min(nc), max(nc), max(nc) - min(nc), T))
    out = os.path.join(HERE, "M26_证据", "M26_title_measure.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dict(th=th, K=K, T=T, items=res), f, ensure_ascii=False, indent=2)
    print("已写出：%s" % out)


if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""ISSUE-20260927-02 · F 组 · 回想屏「三件视觉中线 + 按钮 x 左沿」实机量测（只读 PNG，幂等）。

量什么（逐块 4 行，全部 canvas 坐标）：
  ① 文案**首行墨迹**中线 —— 只取首行行盒窗口（item_text.y + 行高 42）内的深色像素（阈值 = 该窗口
     亮度中位数 − 60，与上一轮 `measure_shot_text_edges.py` 同口径），取墨迹行的首末 → 中线。
  ② 按钮**胶囊可见体**中线 —— 两路：
     (a) **素材口径（主）**：`krkr/assets/ui/x_ui_jump_off.png` 的逐行 alpha（h29 = 素材高 29
         ⇒ nine t7/b7 **纵向 1:1 无拉伸**，素材第 k 行 = 元素第 k 行 = canvas `元素y + k`）；
         多档阈值 T 各给一个中线。
     (b) **实机口径（独立交叉验证）**：在按钮矩形内，逐行比较「按钮带内亮度」与「同 y 行带基线亮度」
         （基线取 x = 行带内、按钮左侧的 10 列）⇒ 差值超阈的行即胶囊可见体，取首末 → 中线。
  ③ 按钮**标签墨迹**中线 —— 按钮矩形内的深色像素（lum < 120；胶囊体是浅色 ⇒ 该阈值天然只留标签）。
  ④ 两个按钮的**可见体 x 左沿**（胶囊/图标的实绘左沿）与「行带左缘」的距离。

目标（本模块 ①）：文案首行墨迹中线 ≈ 胶囊可见体中线 ≈ 标签墨迹中线，三者差 ≤2px。
目标（本模块 ②）：两键元素 x = PSB 口径（jump 15 / replay 141），即距行带左缘 15 / 141 px。

用法：python measure_shot_backlog.py <shot_29_backlog.png> [...]
"""
import os
import sys
import json

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
ASSUI = os.path.join(UI, "krkr", "assets", "ui")

THRS = [8, 64, 128, 250]


def lum3(px):
    r, g, b = px[0], px[1], px[2]
    return 0.299 * r + 0.587 * g + 0.114 * b


def load_spec():
    d = json.load(open(SCREEN, encoding="utf-8"))
    lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
    return lst


def asset_alpha_rows(name):
    im = Image.open(os.path.join(ASSUI, name)).convert("RGBA")
    a = im.getchannel("A")
    W, H = im.size
    px = a.load()
    cols = []
    for x in range(W):
        vals = [px[x, y] for y in range(H)]
        cols.append((max(vals), sum(vals) / float(H)))
    rows = []
    for y in range(H):
        vals = [px[x, y] for x in range(W)]
        rows.append((max(vals), sum(vals) / float(W)))
    return (W, H), rows, cols


def span(p, thr):
    idx = [i for i, (mx, _) in enumerate(p) if mx >= thr]
    return (idx[0], idx[-1]) if idx else None


def band_profile(px, y, x0, x1):
    vals = [lum3(px[x, y]) for x in range(x0, x1)]
    return sum(vals) / len(vals)


def measure(path):
    lst = load_spec()
    it = lst["item_text"]
    L, T, W, ITH, GAP = lst["x"], lst["y"], lst["w"], lst["item_h"], lst["gap"]
    btns = lst["item_buttons"]
    bj = [b for b in btns if b["key"] == "jump"][0]
    br = [b for b in btns if b["key"] == "replay"][0]
    (AW, AH), arows, acols = asset_alpha_rows("x_ui_jump_off.png")
    (RW, RH), rrows, rcols = asset_alpha_rows("x_ui_spk2_off.png")

    im = Image.open(path).convert("RGB")
    Wc, Hc = im.size
    px = im.load()
    pitch = ITH + GAP
    lineH = None
    print("=" * 100)
    print("实机导图：%s  (%dx%d)" % (os.path.basename(path), Wc, Hc))
    print("数据：list(x%d y%d w%d item_h%d gap%d)  item_text(x%d y%d w%d h%d)"
          % (L, T, W, ITH, GAP, it["x"], it["y"], it["w"], it["h"]))
    print("       jump(x%d y%d w%d h%d)  replay(x%d y%d w%d h%d)"
          % (bj["x"], bj["y"], bj["w"], bj["h"], br["x"], br["y"], br["w"], br["h"]))
    # ---- 素材口径：胶囊可见体（映射进元素矩形；h29 = 素材高 ⇒ 纵向 1:1）----
    print("  胶囊素材（x_ui_jump_off.png %d×%d）纵向 alpha 可见区间（映射到画布 y = 元素y + k）：" % (AW, AH))
    cap_center = {}
    for thr in THRS:
        s = span(arows, thr)
        ry = T + 0 * pitch + bj["y"]
        cap_center[thr] = (s[0] + s[1]) / 2.0 + ry
        print("     T=%3d  素材行 %2d..%2d（高 %2d） ⇒ 画布 y %d..%d  中线 %.1f  （元素框中线 %.1f）"
              % (thr, s[0], s[1], s[1] - s[0] + 1, ry + s[0], ry + s[1],
                 (s[0] + s[1]) / 2.0 + ry, ry + (bj["h"] - 1) / 2.0))
    print("  重播素材（x_ui_spk2_off.png %d×%d）纵向 alpha 可见区间：")
    for thr in THRS:
        s = span(rrows, thr)
        ry = T + 0 * pitch + br["y"]
        print("     T=%3d  素材行 %2d..%2d（高 %2d） ⇒ 画布 y %d..%d  中线 %.1f  （元素框中线 %.1f）"
              % (thr, s[0], s[1], s[1] - s[0] + 1, ry + s[0], ry + s[1],
                 (s[0] + s[1]) / 2.0 + ry, ry + (br["h"] - 1) / 2.0))
    print("  胶囊素材横向可见区间（映射到画布 x = 元素x + k）：")
    for thr in (8, 64, 128):
        s = span(acols, thr)
        print("     T=%3d  素材列 %2d..%2d（宽 %2d） ⇒ 画布 x %d..%d"
              % (thr, s[0], s[1], s[1] - s[0] + 1, L + bj["x"] + s[0], L + bj["x"] + s[1]))
    print()
    print("  逐块量测（canvas 坐标）：")
    hdr = ("   块 | 行带y0 | 文案首行墨迹(y 首..末,中线) | 标签墨迹(y 首..末,中线) | "
           "胶囊中线(素材T128/实机) | 文案−胶囊 | 文案−标签 | 标签−胶囊")
    print(hdr)
    print("   " + "-" * (len(hdr) + 12))
    for i in range(4):
        ry0 = T + i * pitch
        # --- 文案首行 ---
        ty0 = ry0 + it["y"]
        ty1 = ty0 + 41                      # 首行行盒 42 高（只取首行，避开第二行）
        tx0, tx1 = L + it["x"], L + it["x"] + it["w"] - 1
        wy0 = ty0 - 5        # 上侧外扩：字形墨迹可越出行盒顶（实测首行墨迹自 176 起，行盒顶 177）
        vals = sorted(lum3(px[x, y]) for y in range(wy0, ty1 + 1, 2) for x in range(tx0, tx1 + 1, 3))
        med = vals[len(vals) // 2]
        thr = med - 60
        rows = [y for y in range(wy0, ty1 + 1)
                if sum(1 for x in range(tx0, tx1 + 1) if lum3(px[x, y]) < thr) >= 2]
        t_first, t_last = rows[0], rows[-1]
        t_mid = (t_first + t_last) / 2.0
        # --- 标签墨迹（按钮矩形内深色像素）---
        jx0, jy0 = L + bj["x"], ry0 + bj["y"]
        jx1, jy1 = jx0 + bj["w"] - 1, jy0 + bj["h"] - 1
        lrows = [y for y in range(jy0 - 5, jy1 + 5)
                 if sum(1 for x in range(jx0, jx1 + 1) if lum3(px[x, y]) < 175) >= 1]
        lcols = [x for x in range(jx0, jx1 + 1)
                 if sum(1 for y in range(jy0, jy1 + 1) if lum3(px[x, y]) < 175) >= 1]
        l_mid = (lrows[0] + lrows[-1]) / 2.0
        # --- 胶囊可见体（实机口径：与行带基线比较）---
        base = [band_profile(px, y, L + 2, L + 12) for y in range(jy0, jy1 + 1)]
        prows = []
        for k, y in enumerate(range(jy0, jy1 + 1)):
            xs = list(range(jx0 + 8, jx0 + 20)) + list(range(jx1 - 20, jx1 - 8))
            m = sum(lum3(px[x, y]) for x in xs) / float(len(xs))
            if abs(m - base[k]) > 3.0:
                prows.append(y)
        p_mid = (prows[0] + prows[-1]) / 2.0 if prows else None
        p_span = (prows[0], prows[-1]) if prows else None
        # --- 重播图标可见体（实机口径）---
        rx0, ry_ = L + br["x"], ry0 + br["y"]
        rx1, ry1 = rx0 + br["w"] - 1, ry_ + br["h"] - 1
        rbase = [band_profile(px, y, L + 2, L + 12) for y in range(ry_, ry1 + 1)]
        rp = []
        for k, y in enumerate(range(ry_, ry1 + 1)):
            m = sum(lum3(px[x, y]) for x in range(rx0, rx1 + 1)) / float(br["w"])
            if abs(m - rbase[k]) > 3.0:
                rp.append(y)
        r_mid = (rp[0] + rp[-1]) / 2.0 if rp else None
        print("   %2d | %5d | y %3d..%3d  %6.1f | y %3d..%3d %6.1f | %6.1f / %s | "
              "%+5.1f | %+5.1f | %+5.1f"
              % (i, ry0, t_first, t_last, t_mid, lrows[0], lrows[-1], l_mid,
                 cap_center[128] + i * pitch, ("%.1f" % p_mid) if p_mid is not None else "n/a",
                 t_mid - (cap_center[128] + i * pitch), t_mid - l_mid,
                 l_mid - (cap_center[128] + i * pitch)))
        if i == 0:
            print("       块0 明细：文案首行墨迹行 %d..%d（%d 行）；标签墨迹行 %d..%d（%d 行）、"
                  "列 %d..%d（宽 %d）；胶囊实机可见体行 %s；重播图标实机可见体行 %s 中线 %s"
                  % (t_first, t_last, t_last - t_first + 1, lrows[0], lrows[-1], len(lrows),
                     lcols[0], lcols[-1], lcols[-1] - lcols[0] + 1,
                     ("%d..%d（%d 行）" % (p_span[0], p_span[1], p_span[1] - p_span[0] + 1)) if p_span else "n/a",
                     ("%d..%d" % (rp[0], rp[-1])) if rp else "n/a",
                     ("%.1f" % r_mid) if r_mid is not None else "n/a"))
    print()
    print("  x 左沿（块0）：")
    # 胶囊实绘左沿（实机口径）：按钮矩形内、与行带基线差异 > 3 的最左列
    ry0 = T
    jy0 = ry0 + bj["y"]
    jy1 = jy0 + bj["h"] - 1
    base = [band_profile(px, y, L + 2, L + 12) for y in range(jy0, jy1 + 1)]
    pcols = []
    for x in range(L + 2, L + bj["x"] + bj["w"]):
        m = sum(lum3(px[x, y]) for y in range(jy0, jy1 + 1)) / float(bj["h"])
        b = sum(base) / len(base)
        if abs(m - b) > 3.0:
            pcols.append(x)
    print("     jump 元素矩形 canvas x %d..%d（宽 %d）；胶囊实绘左沿 canvas x %s"
          "（素材 alpha 口径 T64 ⇒ %d）；距行带左缘（canvas %d）= %s px"
          % (L + bj["x"], L + bj["x"] + bj["w"] - 1, bj["w"],
             (pcols[0] if pcols else "n/a"), L + bj["x"] + span(acols, 64)[0], L,
             (pcols[0] - L) if pcols else "n/a"))
    print("     replay 元素矩形 canvas x %d..%d（宽 %d）；图标实绘左沿 = %d（素材 alpha 口径 T64）："
          "距行带左缘 = %d px"
          % (L + br["x"], L + br["x"] + br["w"] - 1, br["w"],
             L + br["x"] + span(rcols, 64)[0], L + br["x"] + span(rcols, 64)[0] - L))
    return


if __name__ == "__main__":
    for p in sys.argv[1:]:
        measure(p)

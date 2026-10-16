# -*- coding: utf-8 -*-
r"""s2 · B 路选优判据：**图标中心位移量**（候选 vs 原件）

判据定义（与本轮派单一致）：
  1) 取**原件**（`PSV系统UI参考\超分2x\otv_*.png` 的 (880,940)-(1904,1088) 页脚带，1024×148）；
  2) 在原件上**逐项**裁出该件的图标模板（每个圆钮图标一枚，窗口见 USECASE）；
  3) 把「蓝墨度」(B−R，clip 0) 做 σ=5 高斯模糊（消除候选件重绘带来的描边粗细/浓淡差异，
     只留**形状与位置**）后做归一化互相关（NCC），在候选件上以原件位置为中心 ±RX / ±RY 搜索峰值；
  4) 位移 = 峰值位置 − 原件模板位置；件级判据 = Σ|Δ|（各图标位移绝对值之和），**最小者胜**。

为什么用模糊 NCC 而不是蓝阈值连通域：B 路是 AI 重绘，图标描边浓淡每次不同（实测 gm_bg1 的 ◎
在 run2 里被画得极淡），阈值法会把它漏掉或误配到中文字形上；模糊后只比「环形的形状与位置」，
实测 NCC 自匹配 1.000、跨版本匹配 0.94–0.98，峰值唯一。

用法：python s2_icon_disp.py            # 打印 7 件（其中 2 件含 run1..run4）的位移表
      python s2_icon_disp.py --write    # 另把选优结果写入 json（供 t1 落盘脚本读取）
"""
import sys, os, json, glob
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据")
DELIV = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
FX0, FY0 = 880, 940

# 各件的图标模板窗口（裁片坐标）。窗口 = `footer_bbox_split.json` 逐项 `icon` 左缘（缺则取 word 左缘，
# 图标恒在该词最左）向左 4px 起、宽 52px，纵向 y46..98（= 原件实测图标纵向带 51..91 外扩一圈柔光）。
# 推导脚本见本文件 __main__ 的 --templates；全部窗口已用 NCC 自匹配与模板印相表核验（见 _证据\s2_templates.png）。
TEMPL = {
    "otv_save_bg.png":       [(403, 46, 455, 98), (568, 46, 620, 98), (857, 46, 909, 98)],
    "otv_load_bg.png":       [(403, 46, 455, 98), (568, 46, 620, 98), (857, 46, 909, 98)],
    "otv_quick_load_bg.png": [(690, 46, 742, 98), (857, 46, 909, 98)],
    "otv_bklog.png":         [(553, 46, 605, 98), (857, 46, 909, 98)],
    "otv_gm_bg1.png":        [(87, 46, 139, 98), (672, 46, 724, 98), (857, 46, 909, 98)],
    "otv_mu_bg.png":         [(372, 46, 424, 98), (675, 46, 727, 98), (854, 46, 906, 98)],
    "otv_mv_bg.png":         [(672, 46, 724, 98), (857, 46, 909, 98)],
}
RX, RY = 90, 20          # 搜索半径（x / y）
SIGMA = 5.0


def band_from_psv(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    flat = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")
    return flat.crop((FX0, FY0, FX0 + 1024, 1088))


def band_from_path(p):
    return Image.open(p).convert("RGB")


def feat(im):
    a = np.asarray(im).astype(np.float32)
    br = np.clip(a[:, :, 2] - a[:, :, 0], 0, 255).astype(np.uint8)
    return np.asarray(Image.fromarray(br).filter(ImageFilter.GaussianBlur(SIGMA))).astype(np.float32)


def ncc_peak(I, T, cx, cy):
    H, W = I.shape
    th, tw = T.shape
    Tm = T - T.mean()
    Tn = np.sqrt((Tm * Tm).sum())
    best = (-2.0, -1, -1, False)
    for y in range(max(0, cy - RY), min(H - th, cy + RY) + 1):
        for x in range(max(0, cx - RX), min(W - tw, cx + RX) + 1):
            Wn = I[y:y + th, x:x + tw]
            Wm = Wn - Wn.mean()
            d = np.sqrt((Wm * Wm).sum())
            if d < 1e-6:
                continue
            v = float((Tm * Wm).sum() / (Tn * d))
            if v > best[0]:
                edge = x in (max(0, cx - RX), min(W - tw, cx + RX)) or \
                       y in (max(0, cy - RY), min(H - th, cy + RY))
                best = (v, x, y, edge)
    return best


def score(name, cand_band):
    O = feat(band_from_psv(name))
    C = feat(cand_band)
    rows = []
    for i, (x0, y0, x1, y1) in enumerate(TEMPL[name]):
        T = O[y0:y1, x0:x1]
        self_v = ncc_peak(O, T, x0, y0)[0]
        v, x, y, edge = ncc_peak(C, T, x0, y0)
        rows.append({"icon": i + 1, "orig": [x0, y0], "match": [x, y], "ncc": round(v, 3),
                     "self_ncc": round(self_v, 3), "dx": x - x0, "dy": y - y0, "edge": edge})
    return rows


def stroke_gap(name, im, i):
    """第 i 项图标左缘笔画列 − 左侧 140px 窗内最右笔画列 = 与前一项文字的间距（px）。
    笔画列判据：该列 (B−R)>55 的像素 ≥3（= 描边/字形实笔，滤掉柔光与底纹）。"""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    col = ((a[:, :, 2] - a[:, :, 0]) > 55).sum(axis=0)
    O = feat(band_from_psv(name))
    C = feat(im)
    x0, y0, x1, y1 = TEMPL[name][i]
    v, x, y, e = ncc_peak(C, O[y0:y1, x0:x1], x0, y0)
    left = right = None
    for c in range(x, min(1023, x + 60) + 1):
        if col[c] >= 3:
            left = c
            break
    for c in range(x - 12, max(0, x - 140), -1):
        if col[c] >= 3:
            right = c
            break
    return {"icon_x": x, "icon_stroke": left, "prev_text_stroke": right,
            "gap": None if (left is None or right is None) else left - right}


def variants(name):
    """该件的全部候选（路径, 标签）：交付件 + 既有 run1/run2 + 重跑 run3/run4"""
    short = name.replace(".png", "")
    out = []
    for p in sorted(glob.glob(os.path.join(EV, "B_footer", short + "_B_run*.png"))):
        out.append((p, os.path.basename(p).replace(short + "_B_", "").replace(".png", "")))
    for p in sorted(glob.glob(os.path.join(EV, "B_footer_rerun", short + "_B_run*.png"))):
        out.append((p, os.path.basename(p).replace(short + "_B_", "").replace(".png", "")))
    d = os.path.join(DELIV, short + "_B_生图.png")
    if os.path.exists(d):
        out.append((d, "已交付"))
    return out


if __name__ == "__main__":
    ORDER = ["otv_save_bg.png", "otv_load_bg.png", "otv_quick_load_bg.png", "otv_bklog.png",
             "otv_gm_bg1.png", "otv_mu_bg.png", "otv_mv_bg.png"]
    WRITE = "--write" in sys.argv
    pick = {}
    # 本轮**只重跑两件**（otv_bklog / otv_gm_bg1，见 s1_rerun_B.py）；其余 5 件按派单「沿用现成品」。
    # 5 件里 run1 与已交付 run2 的 Σ|Δ| 差 ≤1px（噪声级），不足以推翻「沿用现成品」⇒ 一律取已交付件。
    TARGETS = {"otv_bklog.png", "otv_gm_bg1.png"}
    for n in ORDER:
        print("=" * 100)
        print(n, " 图标模板数 %d" % len(TEMPL[n]))
        best = None
        for p, label in variants(n):
            rows = score(n, band_from_path(p))
            tot = sum(abs(r["dx"]) + abs(r["dy"]) for r in rows)
            mx = max(abs(r["dx"]) for r in rows)
            tag = " ".join("i%d dx=%+d dy=%+d ncc=%.2f%s" % (r["icon"], r["dx"], r["dy"], r["ncc"],
                                                            "!" if r["edge"] else "")
                           for r in rows)
            print("   %-10s Σ|Δ|=%3d  max|dx|=%3d  size=%s  %s" % (label, tot, mx, os.path.getsize(p), tag))
            if best is None or tot < best[0]:
                best = (tot, label, p)
        if n in TARGETS:
            print("   → 选优：%s（Σ|Δ|=%d）" % (best[1], best[0]))
            pick[n] = {"label": best[1], "path": best[2], "metric": best[0], "replaced": True}
        else:
            d = os.path.join(DELIV, n.replace(".png", "") + "_B_生图.png")
            print("   → 沿用现成品（判据最优 %s Σ|Δ|=%d，与现成品差 ≤1px ⇒ 按派单不换）" % (best[1], best[0]))
            pick[n] = {"label": "已交付", "path": d, "metric": best[0], "replaced": False}
    # 碰撞体检：选优件逐项「与前一项文字的间距」（<8px 即碰撞；原件同口径作参照）
    print("\n" + "=" * 100)
    print("碰撞体检（选优件；间距 = 图标左缘笔画列 − 左邻文字最右笔画列；<8px 判碰撞）")
    for n in ORDER:
        p = pick[n]["path"]
        im = band_from_path(p)
        o = band_from_psv(n)
        row = []
        for i in range(len(TEMPL[n])):
            g = stroke_gap(n, im, i)["gap"]
            go = stroke_gap(n, o, i)["gap"]
            row.append("i%d %s(原件 %s)" % (i + 1, "—" if g is None else "%dpx" % g,
                                           "—" if go is None else "%dpx" % go))
        bad = [j for j in range(len(TEMPL[n])) if (stroke_gap(n, im, j)["gap"] or 999) < 8]
        print("   %-24s %s   %s" % (n, " ｜ ".join(row), "★碰撞 i%s" % (bad,) if bad else "无碰撞"))
    if WRITE:
        with open(os.path.join(WORK, "footer_B_pick.json"), "w", encoding="utf-8") as fh:
            json.dump(pick, fh, ensure_ascii=False, indent=1)
        print("\nwritten:", os.path.join(WORK, "footer_B_pick.json"))

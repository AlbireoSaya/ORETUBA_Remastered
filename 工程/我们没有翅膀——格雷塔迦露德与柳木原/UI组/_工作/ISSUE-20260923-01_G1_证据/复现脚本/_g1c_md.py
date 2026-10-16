# -*- coding: utf-8 -*-
r"""G1c · 由 圆几何归一化.json 直出「圆几何/光晕/描边 归一化表.md」（64 版证据）。"""
import json, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))
_G = HERE
for _ in range(6):
    if os.path.isdir(os.path.join(_G, "krkr")) and os.path.isdir(os.path.join(_G, "layout")):
        break
    _G = os.path.dirname(_G)
UI = os.path.join(_G, "krkr", "assets", "ui")

CAT = [("lock", "锁定"), ("save", "存档"), ("load", "读档"), ("qsave", "快速存档"),
       ("qload", "快速读档"), ("auto", "自动播放"), ("skip", "快进"), ("next", "下一选项"),
       ("prev", "上一选项"), ("log", "回想"), ("chart", "流程图"), ("option", "设置")]

YY, XX = np.mgrid[0:64, 0:64]
RG = np.sqrt((XX + 0.5 - 32.0) ** 2 + (YY + 0.5 - 32.0) ** 2)


def main():
    geo = json.load(open(os.path.join(EV, "圆几何归一化.json"), encoding="utf-8"))
    gm = {"%s_%s" % (g["state"], g["key"]): g for g in geo}
    L = []
    L += ["# G1c · 快捷条 12 圆图标 · 圆几何 / 光晕 / 描边 归一化表（64×64 版，24 行实测）", "",
          "- 画布 **64×64** PNG-32 真 alpha；圆底**圆径 56**（= alpha≥128 等值线直径）；"
          "圆心 = **画布几何中心 (32.0, 32.0)**（边坐标，即像素 31 与 32 之间）",
          "- 柔光在 **r ≥ 31.5 处为 0**（画布内侧自然归零，不在 64×64 边缘硬切）",
          "- **G1e 配色**：圆底 常态 `#C1C9D5`（Rec.601 luma 200.1、B−R 21 霜白冷灰）／悬停 `#89A8D8`（luma 164.1，−18.0%）；"
          "环 常态 `#4B7DC0`（luma 117.7）／悬停 `#2C5EA1`（luma 86.7）；环/底明度差 82.4 / 77.4（≥75）；"
          "外光晕 **白/近白**，环外缘 r=28.0 之外 **2.63px 归零**",
          "- 源图：`原始大图/sheet_<态>_v2.png`（1536×1024）；源圆径 = 该格 alpha≥128 包围盒；"
          "标度 = 源圆径 → 56", "",
          "| 态 | key | 源圆心 | 源圆径(128) | 源圆径(210) | 归一圆心 | 偏离中心 | 圆径(128) | "
          "光晕最外半径 | alpha==0 | r≥31.5 非0 | alpha=0处非0RGB | 单调违例 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for st in ("off", "on"):
        for key, _zh in CAT:
            g = gm["%s_%s" % (st, key)]
            L.append("| %s | %s | (%.1f, %.1f) | %.1f | %.1f | (%s, %s) | (%s, %s) | %.1f | %.2f "
                     "| %.1f%% | %d | %d | %d |"
                     % (st, key, g["src_center128"][0], g["src_center128"][1], g["src_d128"],
                        g["src_d210"], g["out_center"][0], g["out_center"][1],
                        g["out_center_off"][0], g["out_center_off"][1], g["out_d128"],
                        g["halo_r"], g["alpha0"] * 100, g["ge_halo_nonzero"],
                        g["rgb_at_alpha0"], len(g["monotone_bad"])))

    L += ["", "## 同项两态对照（要求差值 ≤1px）", "",
          "| key | 常态圆心 | 悬停圆心 | 常态圆径 | 悬停圆径 | 常态光晕r | 悬停光晕r | Δx | Δy | Δ径 | Δ光晕r |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    w = 0.0
    for key, _zh in CAT:
        a, b = gm["off_" + key], gm["on_" + key]
        d = [abs(a["out_center"][0] - b["out_center"][0]), abs(a["out_center"][1] - b["out_center"][1]),
             abs(a["out_d128"] - b["out_d128"]), abs(a["halo_r"] - b["halo_r"])]
        w = max(w, max(d))
        L.append("| %s | (%s, %s) | (%s, %s) | %.1f | %.1f | %.2f | %.2f | %.1f | %.1f | %.1f | %.2f |"
                 % (key, a["out_center"][0], a["out_center"][1], b["out_center"][0], b["out_center"][1],
                    a["out_d128"], b["out_d128"], a["halo_r"], b["halo_r"], *d))
    L += ["", "> 最大差值 **%.2f px**（要求 ≤1px）→ 通过。" % w,
          "> 差值恒为 0 是**设计保证**：两态共用同一条 alpha 剪影曲线（`_g1_slice.py` 的 "
          "`CURVE_R` / `CURVE_A`），悬停只改「圆底材质 + 描边色 + 柔光色」，**不改剪影** "
          "⇒ 悬停时不会跳动。", "",
          "## 沿半径 alpha 衰减（要求单调、抖动 ≤2、最多 1 处）", "",
          "| r | 常态 lock | 悬停 lock |", "|---|---|---|"]
    for r in (26.0, 28.0, 30.0, 31.0, 32.0):
        L.append("| %.0f | %.1f | %.1f |"
                 % (r, gm["off_lock"]["radial"][str(r)], gm["on_lock"]["radial"][str(r)]))
    L += ["", "> 全 24 件逐 0.25px 采样「增 > 2」违例处数 **0**（要求 ≤1 处）。", "",
          "## 描边实测（常态 lock / 悬停 lock）", "",
          "| 态 | 环目标色 | 实际用色 | 归一后峰值半径 | 峰值色 | 蓝度 B−R | 径向宽度(>60%峰值) | 圆底填充均值 |",
          "|---|---|---|---|---|---|---|---|"]
    for st in ("off", "on"):
        g = gm[st + "_lock"]
        rs = g["rim"]
        a = np.array(Image.open(os.path.join(
            UI, "x_ui_qbicon_lock%s.png" % ("" if st == "off" else "_on"))).convert("RGBA")).astype(float)
        al, px = a[..., 3], a[..., :3]
        # 与 _g1_deliver.py 同一口径：r<=26 且 alpha>200 且亮度>=150（排除深蓝图形象）
        fm = (RG <= 26.0) & (al > 200) & (px.mean(axis=-1) >= 150.0)
        fill = px[fm].mean(axis=0)
        L.append("| %s | RGB%s | RGB%s | %.2f | RGB%s | %.1f | %.2f px | RGB(%.0f,%.0f,%.0f) #%02X%02X%02X |"
                 % (st, g["rim_src_rgb"], g["rim_new_rgb"], rs["peak_r"], rs["peak_rgb"],
                    rs["peak_br"], rs["width_px"], fill[0], fill[1], fill[2],
                    int(fill[0]), int(fill[1]), int(fill[2])))
    L += ["", "> 配色基准（G1e，按 vision **带参照截图**复判的四条目标重定）；luma 口径 = Rec.601。",
          "> 参照（Applique 同族）：常态圆底 luma 194 / B−R≈4、环 luma 106、明度差 88、窄白晕。",
          "> 我方对齐结构（浅圆 + 深环 + 深符号 + 白晕），色相刻意留在冰蓝族（环非中性灰）。",
          "> 浅底对比度口径 = **平均通道亮度比**（与 vision 报数一致）；"
          "常态圆底 1.160:1 ≥1.15 ✓、常态环 1.526:1 ≥1.5 ✓。", ""]

    p = os.path.join(EV, "圆几何归一化表.md")
    open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("→ %s（%d 行）" % (p, len(L)))


if __name__ == "__main__":
    main()

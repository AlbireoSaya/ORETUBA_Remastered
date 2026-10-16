# -*- coding: utf-8 -*-
r"""m57_solve_green.py —— 「已读对勾」绿牌的**数值求解**（不试色）

Issue : **ISSUE-20260928-03**（一审打回修复：适用范围——对勾对**三种**节点面都必须达标）
起因 : 一审实测指出：对勾永远画在节点面左上角，而**三类节点的可见实体面颜色不同**
       （section 浅蓝 / select 中蓝 / frag 浅紫），故「对某一面达标」不成立；
       上一版按 `#C4D7F6` 单面选的 `#3F8A5A` 对 select 面只有 **1.71:1**。

■ 判据（按优先级，全部对**三面同时**成立）
    ① 对三面（section / select / frag）**全部 ≥2.5:1**（硬）
    ② 争取对**最差面**（select）**≥3.0:1**
    ③ 白勾对绿牌 ≥4.5:1
    ④ 色相仍是「绿」：HSL 色相 ∈ [110,155]°（不得变墨绿黑）
    ⑤ 约束来源：WCAG 相对亮度比 `(L_face + 0.05) / (L_green + 0.05) ≥ T`
       ⇒ 对**最亮面无效、最暗面是绑定约束**：`L_green ≤ (L_select + 0.05)/T − 0.05`

■ 做法：**数值求解**
    1. 面色取两组：**交付清单给定色**（section `#C4D7F6` / select `#61AED6` / frag `#D3B3F8`）
       ＋ **从三件节点底图实测的可见面中位色**（α≥250 实体的逐通道中位）——取二者中**更苛刻**
       的那组作为绑定面亮度（保守）。
    2. 目标亮度上界由 ②（T=3.0，对最暗面）反解，再乘一个安全余量系数。
    3. 在该上界与 ④ 的色相区间内**穷举整数 RGB**，取 WCAG 亮度最大者（＝在约束边界上最亮的绿）。
    4. 输出候选表（含色相 / 饱和度 / 白勾对比度 / 三面对比度），供人工在「边界上的最亮绿」里挑。
    5. **同一组函数供生成器与证据脚本共用**（`CK_PLATE` 由本脚本的结论手工回填，
       生成器内**重跑同一判据**做断言）。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_solve_green.py"
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")

# 交付清单给定的三面（一审表左列的「给定色」）
FACE_GIVEN = {"section": (0xC4, 0xD7, 0xF6), "select": (0x61, 0xAE, 0xD6), "frag": (0xD3, 0xB3, 0xF8)}
SRC = {"section": "x_ui_node_section_off.png", "select": "x_ui_node_select_off.png",
       "frag": "x_ui_node_frag_off.png"}
GREEN_OLD = (0x5A, 0xA0, 0x6A)      # @palette.node_visited（未压深）
GREEN_PREV = (0x3F, 0x8A, 0x5A)     # 上一版（按单面 #C4D7F6 压深）—— 变异自证用它
THR_HARD, THR_GOAL = 2.5, 3.0
WHITE = (255, 255, 255)
HUE_LO, HUE_HI = 110.0, 155.0
HUE_SRC = 133.7                     # @palette.node_visited #5AA06A 的 HSL 色相（选定规则的贴近目标）
SAT_LO, SAT_HI = 0.60, 0.85         # 饱和度带：保「绿」、避开灰绿 / 墨绿
MARGIN = 0.97                       # 亮度上界安全余量（对「给定色」与「实测中位色」两组的更苛刻者）


def lin(c):
    c = float(c) / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def L(rgb):
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = L(a), L(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hue_of(rgb):
    r, g, b = (v / 255.0 for v in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        h = 60.0 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2)
    else:
        h = 60.0 * ((r - g) / d + 4)
    return h % 360.0


def sat_of(rgb):
    mx, mn = max(rgb) / 255.0, min(rgb) / 255.0
    return 0.0 if mx == 0 else (mx - mn) / mx


def measured_face_median(path):
    """节点底图**可见面**实测中位色：α≥250 的实体像素逐通道取中位"""
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.int64)
    sel = a[:, :, 3] >= 250
    med = [int(np.median(a[:, :, i][sel])) for i in range(3)]
    return tuple(med), int(sel.sum())


def main():
    print("=" * 118)
    print("m57_solve_green.py · 已读对勾绿牌数值求解（ISSUE-20260928-03 一审打回修复）")
    print("-" * 118)
    faces = {}
    print("面色（两组）：")
    for k, g in FACE_GIVEN.items():
        med, n = measured_face_median(os.path.join(OUT, SRC[k]))
        faces[k] = dict(given=g, med=med)
        print("  %-8s 给定 %s L=%.5f ｜ 底图实测中位 %s L=%.5f（α≥250 实体 %d px）"
              % (k, "#%02X%02X%02X" % g, L(g), "#%02X%02X%02X" % med, L(med), n))
    l_given = min(L(v["given"]) for v in faces.values())
    l_med = min(L(v["med"]) for v in faces.values())
    l_bind = min(l_given, l_med)
    print("-" * 118)
    print("绑定面亮度（两组中最苛刻者）= min(给定 %.5f, 实测 %.5f) = **%.5f**" % (l_given, l_med, l_bind))
    for t in (THR_HARD, THR_GOAL):
        print("  T=%.1f ⇒ 绿牌亮度上界 L ≤ (%.5f + 0.05)/%.1f − 0.05 = **%.6f**"
              % (t, l_bind, t, (l_bind + 0.05) / t - 0.05))
    l_ub = (l_bind + 0.05) / THR_GOAL - 0.05
    l_target = l_ub * MARGIN
    print("  ⇒ 取目标 L ≤ %.6f（= 上界 × 余量 %.2f）" % (l_target, MARGIN))
    print("-" * 118)

    # ── 穷举：色相 ∈ [110,155]° 且 L ≤ l_target 的整数 RGB，取 L 最大者 ──
    cands = []
    for r in range(256):
        for g in range(256):
            for b in range(256):
                h = hue_of((r, g, b))
                if not (HUE_LO <= h <= HUE_HI):
                    continue
                ll = L((r, g, b))
                if ll > l_target:
                    continue
                cands.append((ll, (r, g, b), h, sat_of((r, g, b))))
    cands.sort(key=lambda t: -t[0])
    print("候选（色相 ∈ [%.0f,%.0f]° 且 L ≤ %.6f）共 %d 个；按亮度从高到低取前 12："
          % (HUE_LO, HUE_HI, l_target, len(cands)))
    print("%-10s %-9s %-7s %-7s %-9s %-9s %-9s %-9s"
          % ("绿牌", "HSL色相°", "饱和度", "WCAG L", "白勾:牌", "section", "select", "frag"))
    for ll, rgb, h, s in cands[:12]:
        print("%-10s %-9.1f %-7.3f %-7.5f %-9.3f %-9.3f %-9.3f %-9.3f"
              % ("#%02X%02X%02X" % rgb, h, s, ll, contrast(WHITE, rgb),
                 contrast(rgb, faces["section"]["med"]), contrast(rgb, faces["select"]["med"]),
                 contrast(rgb, faces["frag"]["med"])))

    # ── 选定规则（写死在脚本里 ⇒ 可复现、可复核） ──────────────────────────────
    print("-" * 118)
    print("选定规则：① L ≤ 上界×%.2f（三面 ≥3.0 有余量）；② 饱和度 ∈ [%.2f, %.2f]"
          "（保「绿」、避开灰绿/墨绿）；③ 在满足 ①② 的候选中取 **L 最大**（边界上最亮的绿）；"
          "④ 同 L 并列时取 **色相最接近 palette 原值 %.1f°** 者。" % (MARGIN, SAT_LO, SAT_HI, HUE_SRC))
    pool = [c for c in cands if SAT_LO <= c[3] <= SAT_HI]
    best_l = max(c[0] for c in pool)
    pool2 = [c for c in pool if c[0] >= best_l - 2e-5]
    pick = min(pool2, key=lambda c: (abs(c[2] - HUE_SRC), c[3]))
    print("  满足 ② 的候选 %d 个；其中 L 最大档（≥%.5f − 2e-5）%d 个；选定 **#%02X%02X%02X**"
          "（色相 %.1f° / 饱和 %.3f / L %.5f）"
          % (len(pool), best_l, len(pool2), pick[1][0], pick[1][1], pick[1][2],
             pick[2], pick[3], pick[0]))
    print("%-10s %-9s %-7s %-7s %-9s %-9s %-9s %-9s"
          % ("绿牌", "HSL色相°", "饱和度", "WCAG L", "白勾:牌", "section", "select", "frag"))
    for ll, rgb, h, s in pool2[:8]:
        print("%-10s %-9.1f %-7.3f %-7.5f %-9.3f %-9.3f %-9.3f %-9.3f"
              % ("#%02X%02X%02X" % rgb, h, s, ll, contrast(WHITE, rgb),
                 contrast(rgb, faces["section"]["med"]), contrast(rgb, faces["select"]["med"]),
                 contrast(rgb, faces["frag"]["med"])))
    print("-" * 118)
    for tag, g in (("原值 @palette.node_visited", GREEN_OLD), ("上一版（单面压深）", GREEN_PREV),
                   ("**选定（本脚本推荐）**", pick[1])):
        h, s, ll = hue_of(g), sat_of(g), L(g)
        row = [contrast(g, faces[k]["med"]) for k in ("section", "select", "frag")]
        rowg = [contrast(g, faces[k]["given"]) for k in ("section", "select", "frag")]
        print("%-24s %s ｜色相 %.1f° 饱和 %.3f ｜L %.5f ｜白勾:牌 %.3f"
              % (tag, "#%02X%02X%02X" % g, h, s, ll, contrast(WHITE, g)))
        print("%-24s    实测中位面 %.3f / %.3f / %.3f（section/select/frag，门槛 2.5 / 目标 3.0）｜"
              "给定面 %.3f / %.3f / %.3f ｜ %s"
              % ("", row[0], row[1], row[2], rowg[0], rowg[1], rowg[2],
                 ("三面全 ≥2.5 ✔ 且全 ≥3.0 ✔" if min(row) >= THR_GOAL and min(rowg) >= THR_GOAL
                  else ("三面全 ≥2.5 ✔（未全达 3.0）" if min(min(row), min(rowg)) >= THR_HARD
                        else "**有面 <2.5 ✘**"))))
    print("=" * 118)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""把 轮廓解析化_数字证据.json 转成可读数字证据 txt（只读 json，写同目录 txt）。"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
OUT = HERE.parents[1] / "取证" / "圆角候选"
J = OUT / "轮廓解析化_数字证据.json"
rep = json.loads(J.read_text(encoding="utf-8"))
L = []
A = L.append

A("节点底图「轮廓解析化 + 柔光重做」数字证据（ISSUE-20260927-07 · 解析化轮）")
A("=" * 108)
A("参数：轮廓 = alpha 的 50%% 覆盖交叉点（CROSS=%.1f）；掩码阈值 SOLID=%d（未改）；"
  % (rep["params"]["CROSS"], rep["params"]["SOLID_THR"]))
A("      alpha = Σ_s w_s · f_s(到轮廓的有符号距离 t)（f_s = 逐边实测径向剖面表，外正内负；w_s = 轮廓法线在各边的分量）")
A("      底色 %s（%s）" % (str(rep["bg"]), rep["bg_src"]))
A("")

A("【1】实体矩形（50% 交叉点）与半径实测")
A("-" * 108)
A("%-8s %-38s %-9s %s" % ("类", "rect (x0, x1, y0, y1)", "宽×高", "逐角半径（一维搜索 / 45° 对角校核）"))
for k, v in rep["kinds"].items():
    r = v["rect"]
    cs = " ".join("%s=%.2f(45°%.2f)" % (c, v["corners"][c]["r"], v["corners"][c]["r45"])
                  for c in ("TL", "TR", "BR", "BL"))
    A("%-8s (%8.3f,%9.3f,%7.3f,%7.3f) %6.2f×%-6.2f %s  ⇒ 均值 %.2f"
      % (k, r[0], r[1], r[2], r[3], r[1] - r[0], r[3] - r[2], cs, v["r_mean"]))
A("")
A("  说明：「半径不变」档 = 用上表的**逐角**实测半径（不做圆整）；r=12/16/20 档 = 四角同一半径。")
A("        ⚠ 45° 口径是**有偏仪器**：对「理想解析弧」标定（同一函数测 r=12/16/20 的解析圆角矩形）得")
A("          r=12 → TL 10.24 / TR 12.20 / BR 13.72 / BL 12.02；r=20 → TL 18.30 / TR 19.93 / BR 21.82 / BL 20.08")
A("          （TL 恒偏低 ≈ −1.7、BR 恒偏高 ≈ +1.8，TR/BL 准）⇒ 45° 值只能**同角相对比较**，")
A("          绝对半径以上表的「一维搜索（相切约束）」为准（对理想弧实测 12.01/16.01/20.01，无偏）。")
A("          相对比较示例：section TL 原件 6.99 ⇒「半径不变」档 6.99、r=12 档 10.24（同一仪器，差值可信）。")
A("        直线带 = 去掉四角（角半径+2）后的中央区：%s"
  % "；".join("%s 行[%d..%d] 列[%d..%d]" % (k, v["band"]["rows"][0], v["band"]["rows"][1],
                                            v["band"]["cols"][0], v["band"]["cols"][1])
             for k, v in rep["kinds"].items()))

A("")
A("【2】四边向外柔光剖面表（相位无关的 1px 环带均值；0 = 50% 交叉点轮廓；外正内负）")
A("-" * 108)
A("  ②-1 向外 d = 0..12 px")
A("  %-9s %-3s %s" % ("类", "边", "".join("%7d" % d for d in range(13))))
for k, kv in rep["annulus"].items():
    if k.startswith("_"):
        continue
    for s in ("L", "T", "R", "B"):
        o = kv[s]["orig"]
        A("  %-9s %-3s %s" % (k, s, "".join("     —" if x is None else "%7.1f" % x for x in o)))
A("    剖面表带 margin（去掉角区的最小边距）= %s px"
  % ", ".join("%s:%d" % (k, v) for k, v in rep["annulus"]["_margin"].items()))
A("  ②-2 候选（半径不变档）同口径 + 与现状的最大偏差")
for k, kv in rep["annulus"].items():
    if k.startswith("_"):
        continue
    for s in ("L", "T", "R", "B"):
        c = kv[s]["cand"]
        A("  %-9s %-3s %s ｜ 最大偏差 %.2f" % (k, s,
          "".join("     —" if x is None else "%7.1f" % x for x in c), kv[s]["max_dev"]))
A("  判定：section 的柔光**带明显方向性**（L 72.0 / B 74.8 是 T 36.9 / R 41.9 的约 2 倍 ⇒ 偏左下）；")
A("        select / frag 近似对称、底边略强（select B 106.4 vs T 93.1；frag B 109.5 vs T 93.0）。")
A("        候选按边分别套用本表 ⇒ 各边剖面与现状的最大偏差仅 0.25–0.65（直边无回归）。")

A("")
A("【3】底边「凸起」修前 / 修后（select，off）")
A("-" * 108)
n = rep["notch"]
A("  修前：y=56 行 alpha（x=155..180）= %s" % " ".join("%d" % v for v in n["orig"]))
A("        其中 x=%d 处 alpha=%d < %d ⇒ 掩码(alpha>=230)在该列缺 1 格 ⇒ 圆盘腐蚀的描边环带鼓包。"
  % (n["x_notch"], n["orig_at_notch"], rep["params"]["SOLID_THR"]))
for tag, v in n["cand"].items():
    A("  修后：%-6s y=56 行 alpha（同列）= %s  掩码缺口=%s（该行中位 %d）"
      % (tag, " ".join("%d" % x for x in v["row"]), v["holes"] or "无", v["med"]))
A("")
A("  描边在 x=158..176 各列的**竖向径向宽度**（覆盖率沿法线积分，单位 1× px）：")
A("    %-14s %s" % ("x=", " ".join("%5d" % x for x in rep["notch_ring"]["x"])))
for nm, v in rep["notch_ring"]["widths"].items():
    A("    %-14s %s" % (nm, " ".join("%5.2f" % x for x in v)))
_w = rep["notch_ring"]["widths"]["现状(正式件)"]
A("    ⇒ 现状在峰值列出现 %s 的鼓包（峰值 +%.2fpx，跨 6 列 = 圆盘腐蚀核半径）；"
  % ("/".join("%.2f" % v for v in _w if v > 2.004), max(_w) - 2.0))
A("      候选四档全部 2.00 平坦 ⇒ 凸起消失，且不靠调阈值。")

A("")
A("【4】候选件指标（半径复测 / 直边偏差 / 掩码）")
A("-" * 108)
for k, kv in rep["kinds"].items():
    A("  %s（%s）" % (k, kv["sprite"]))
    for tag, r in kv["rows"].items():
        rm = " ".join("%s%s" % (c, ("%.2f" % r["r_measured"][c]["r"]) if r["r_measured"][c]["r"] else "—")
                      for c in ("TL", "TR", "BR", "BL"))
        A("    %-6s 半径复测 %s ｜ 直边 |Δ|max=%.0f@%s（>2: %d / >4: %d / >8: %d / 共 %d 点）"
          % (tag, rm, r["straight_dev_max"], tuple(r["straight_dev_max_xy"]),
             r["straight_n_gt2"], r["straight_n_gt4"], r["straight_n_gt8"], r["straight_n"]))
        A("             整图改动 %d px（|Δ|>2 %d / >8 %d；升 %d / 降 %d）｜ 掩码首/末实体：%s"
          % (r["n_diff_px"], r["n_diff_gt2"], r["n_diff_gt8"], r["n_alpha_up"], r["n_alpha_down"],
             " ".join("%s%s" % (s, (r["mask"][s]["uniq"] if len(r["mask"][s]["uniq"]) < 4
                                   else "[%d..%d]" % (r["mask"][s]["uniq"][0], r["mask"][s]["uniq"][-1])))
                      for s in ("L", "T", "R", "B"))))
    A("    掩码（现状）：%s" % " ".join(
        "%s%s" % (s, (kv["rows"]["半径不变"]["mask_orig"][s]["uniq"]
                      if len(kv["rows"]["半径不变"]["mask_orig"][s]["uniq"]) < 4
                      else "[%d..%d]" % (kv["rows"]["半径不变"]["mask_orig"][s]["uniq"][0],
                                         kv["rows"]["半径不变"]["mask_orig"][s]["uniq"][-1])))
        for s in ("L", "T", "R", "B")))
A("  直边偏差的性质：≥90% 的直边像素 |Δ|≤2；|Δ|>8 的少数点全部落在边缘过渡那一格，")
A("  偏差幅度 = 原件自身沿边的行间噪声（实测 std 3–7，如 select 顶边 y=7 行 157..191）。")

A("")
A("【5】角部「旧折线残留」与平台带（新轮廓之外、距轮廓 ≤3px 的角区）")
A("-" * 108)
for k, kv in rep["kinds"].items():
    for tag, v in kv["corner_residual"].items():
        A("  %-8s %-6s 像素 n=%4d ｜ 最大 alpha=%.0f ｜ >=128: %3d ｜ >=200: %3d ｜ alpha∈[57,63]: %3d"
          % (k, tag, v["n"], v["max"], v["n_ge128"], v["n_ge200"], v["plateau_57_63"]))
A("  注：「现状」行的同口径 = 以该件逐角实测半径的解析轮廓为基准量原件 ⇒ 显示旧折线的残留")
A("      （select 3 px≥128、frag 5 px≥128，最大 160/139）；候选四档一律 0 ⇒ 旧折线轮廓不再残留。")
A("      平台带计数：候选与原件的同区间计数同量级（select 25–48 vs 24；frag 32–46 vs 43；section 4–7 vs 7）")
A("      ⇒ 未引入新的平台带（已无 GLOW_CAP 式截断）。")

A("")
A("【6】select 描边跟随性（沿解析轮廓法线的径向宽度，覆盖率积分）")
A("-" * 108)
for nm, v in rep["stroke"].items():
    if not v:
        continue
    A("  %-24s 直边 p05/med/p95/max = %s/%s/%s/%s ｜ 圆角弧 %s/%s/%s/%s ｜ n=%s/%s"
      % (nm, v["直边"]["p05"], v["直边"]["med"], v["直边"]["p95"], v["直边"]["max"],
         v["圆角弧"]["p05"], v["圆角弧"]["med"], v["圆角弧"]["p95"], v["圆角弧"]["max"],
         v["直边"]["n"], v["圆角弧"]["n"]))
    A("  %-24s 宽度 <1 的采样 %s/%s ｜ >3 的采样 %s/%s"
      % ("", v["直边"]["n_lt1"], v["圆角弧"]["n_lt1"], v["直边"]["n_gt3"], v["圆角弧"]["n_gt3"]))
_st = rep["stroke"]
_c = [_st[t]["圆角弧"] for t in ("半径不变", "r=12", "r=16", "r=20")]
_s = [_st[t]["直边"] for t in ("半径不变", "r=12", "r=16", "r=20")]
A("  ⇒ 候选四档：直边 p05–med = %.3f–%.2f（max ≤%.2f）；圆角弧 med %.3f–%.3f、max %.3f–%.3f，无一处 >3。"
  % (min(x["p05"] for x in _s), max(x["med"] for x in _s), max(x["max"] for x in _s),
     min(x["med"] for x in _c), max(x["med"] for x in _c),
     min(x["max"] for x in _c), max(x["max"] for x in _c)))
A("     正式件：直边 %.3f–%.2f，圆角弧 p05 %.3f / med %.3f / max %.3f；上一轮 min 削减式 r16：圆角弧 p05 %.3f（角部偏薄）/ med %.3f。"
  % (_st["现状(正式件)"]["直边"]["p05"], 2.0, _st["现状(正式件)"]["圆角弧"]["p05"],
     _st["现状(正式件)"]["圆角弧"]["med"], _st["现状(正式件)"]["圆角弧"]["max"],
     _st["上一轮 r=16（min 削减式）"]["圆角弧"]["p05"],
     _st["上一轮 r=16（min 削减式）"]["圆角弧"]["med"]))
A("     ⇒ 描边仍 ≈2px、四角与直边齐平，无新毛刺；且环带像素数 1172（正式件 1176）、改动像素 100% 落在环带内。")

A("")
A("【7】与主代理给定式 max(cov*255, glow) 的对照（glow 取实测向外剖面）")
A("-" * 108)
for k, v in rep["formula_vs_profile"].items():
    A("  %-8s 给定式直边 |Δ|max=%.0f（>8 的 %d / %d 点）｜ 剖面表式 |Δ|max=%.0f"
      % (k, v["formula_straight_dev_max"], v["formula_n_gt8"], v["straight_n"],
         v["profile_straight_dev_max"]))
A("  例（select 底边）：原件 y=56 行 = 235 235 236 236 235 233 231 229 230 234 …；y=57 行 = 142 144 147 …")
A("                    给定式 y=56 行 = 255（全 255，比原件亮 +20）／ y=57 行 = 203（比原件亮 +61）")
A("  ⇒ 原件边沿不是 box 覆盖度（自带约 2–3px 软肩），给定式会把软肩裁成硬边（select 底边轮廓 0.5px 外扩、")
A("     frag 直边最大偏 113）⇒ 故本轮把 cov 项换成同源的径向剖面表（对直边零回归），主代理可覆核。")

A("")
A("【8】on 态可行性（用 off 的实体矩形 + off 的逐角实测半径 + on 的剖面表 ⇒ 预测 on）")
A("-" * 108)
for k, v in rep["on_check"].items():
    A("  %-8s 真实 on rect=%s ｜ 预测=%s ｜ 偏差=%s"
      % (k, [round(x, 2) for x in v["rect_on_real"]], [round(x, 2) for x in v["rect_pred"]],
         [round(x, 2) for x in v["rect_dev"]]))
    A("           半径（真实 on / 预测，各以自身 rect 为锚，同仪器）%s ｜ %s"
      % (" ".join("%s%s" % (c, v["r_on_real"][c]) for c in ("TL", "TR", "BR", "BL")),
         " ".join("%s%s" % (c, v["r_pred"][c]) for c in ("TL", "TR", "BR", "BL"))))
    A("           |Δalpha| max=%d mean=%.2f（>8 的 %d / %d px = %.1f%%）"
      % (v["alpha_diff_max"], v["alpha_diff_mean"], v["alpha_diff_gt8"], v["alpha_n"],
         100.0 * v["alpha_diff_gt8"] / v["alpha_n"]))
A("  ⇒ 「on = 同一几何 + 更强柔光」成立：预测的 50% 交叉矩形与真实 on 相差 ≤0.04px；")
A("     但 on 的「50% 交叉轮廓」本身随柔光外扩（且角部外扩更多）⇒ 不能用它定实体几何（本轮用 off 几何 + on 剖面表）；")
A("     残差集中在四角（4–5% 像素 |Δ|>8，max 54–78）：on 件角部柔光有 2D 叠加，径向单参数剖面无法完全复现。")
A("     on 态候选已另存 `附_on态可行验证_候选_解析轮廓_x_ui_node_<kind>_on_r原件.png`（本轮正式候选集仍限 off）。")

txt = OUT / "轮廓解析化_数字证据.txt"
txt.write_text("\n".join(L) + "\n", encoding="utf-8")
print("写出 %s（%d 行）" % (txt, len(L)))

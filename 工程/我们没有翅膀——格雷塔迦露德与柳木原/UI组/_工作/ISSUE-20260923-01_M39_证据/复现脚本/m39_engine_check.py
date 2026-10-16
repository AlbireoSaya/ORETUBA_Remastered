# -*- coding: utf-8 -*-
r"""M39 · **引擎实拍的强度/剖面自证**：逐档反推 α_eff 并与解析预测比对（含两端交叉核对）

■ 口径
  基准 = `_工作\ISSUE-20260923-01_M38_证据\M38_AB_新实现_shot_03_dialog.png`（同屏同帧、**无遮罩元素**）
  反推 α_eff(y) = 该行「画面层矩形内、亮度>8 且不在正文矩形内」的像素上
                  mean|Δ| / mean(亮度) × 255
  预测 α_eff(y) = 255·[1−Π(1−aᵢ/255)]，aᵢ = 255·t^γ·opacityᵢ/255，t=(y−y0)/(h−1)

■ 为什么必须有这一步（本轮真实教训）
  第一版引擎脚本在同一份 TJS 上连续打补丁 ⇒「双叠 150×2」实拍其实出的是「双叠 255×2」
  （y=950 反推 201 vs 预测 135）。**巡检只看到"跑完/出图/日志干净"，看不出来** ——
  只有把"实测强度"反推出来跟预测对上，才能证明导出的**正是**那一档。

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_engine_check.py
"""
import io
import json
import os
import sys

import shutil

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
M38 = os.path.join(UI, "_工作", "ISSUE-20260923-01_M38_证据")
LINES = []

# (标签, 文件名, 画布上沿 y, 高 h, 剖面 gamma, 各层 opacity)
CASES = [
    ("引擎导出 · 单层 150（第一轮）", "M39_引擎导出_dialog_遮罩150.png", 680, 400, 1.6, [150]),
    ("引擎导出 · 单层 255", "M39_引擎导出_dialog_遮罩255.png", 680, 400, 1.6, [255]),
    ("引擎导出 · 双叠 150×2", "M39_引擎导出_dialog_双叠150x2.png", 680, 400, 1.6, [150, 150]),
    ("引擎导出 · 剖面C（y400 h680 线性）", "M39_引擎导出_dialog_剖面C.png", 400, 680, 1.0, [150]),
    ("引擎导出 · 剖面D（y200 h880 t^0.8）", "M39_引擎导出_dialog_剖面D.png", 200, 880, 0.8, [150]),
    # ★ 定稿方向
    ("引擎导出 · 定稿250px 线性 85%", "M39_引擎导出_dialog_250px_线性85.png", 830, 250, 1.0, [217]),
    ("引擎导出 · 现行 A（y680 h400 t^1.6 59%）", "M39_引擎导出_dialog_现行A.png", 680, 400, 1.6, [150]),
    # ★ 定稿轮：贴底 350px 线性，85% / 90%
    ("引擎导出 · 定稿350px 85%", "M39_引擎导出_dialog_350px_85.png", 730, 350, 1.0, [217]),
    ("引擎导出 · 定稿350px 90%", "M39_引擎导出_dialog_350px_90.png", 730, 350, 1.0, [230]),
]
YS = [200, 300, 400, 500, 600, 680, 700, 750, 800, 850, 900, 950, 990, 1010, 1050, 1079]


def say(s=""):
    print(s)
    LINES.append(s)


def load(p):
    im = Image.open(p)
    im.load()
    if im.size != (1920, 1080):
        im = im.crop((0, 0, 1920, 1080))
    return np.asarray(im.convert("RGB"), dtype=np.float64)


def pred(y, y0, h, gamma, layers):
    if y < y0 or y >= y0 + h:
        return 0.0
    t = (y - y0) / float(h - 1)
    a = 255.0
    for op in layers:
        a *= (1.0 - (255.0 * (t ** gamma) * op / 255.0) / 255.0)
    return 255.0 - a


def main():
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    tx = el["dlg.text"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))
    pr = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    pr = pr.get("基本", pr)
    pb = [int(v) for v in pr["content-rect"].split(",")]

    say("=" * 104)
    say("M39 · 引擎实拍自证（反推 α_eff vs 解析预测）")
    say("=" * 104)
    say("  基准（无遮罩）= M38_AB_新实现_shot_03_dialog.png ｜ 画面层矩形 = %s ｜ 正文矩形 y%d..%d"
        % (pb, tb[1], tb[3]))
    A = load(os.path.join(M38, "M38_AB_新实现_shot_03_dialog.png"))
    lum = A.mean(axis=2)
    base_sel = np.zeros(A.shape[:2], dtype=bool)
    base_sel[pb[1]:pb[3], pb[0]:pb[2]] = True
    base_sel &= (lum > 8)
    base_sel[tb[1]:tb[3], tb[0]:tb[2]] = False        # 排除文字矩形（含其描边）
    say("  参与统计的基准像素：%d" % int(base_sel.sum()))

    worst_all = 0.0
    for tag, fn, y0, h, gamma, layers in CASES:
        p = os.path.join(EVID, fn)
        if not os.path.exists(p):
            say("\n■ %s —— **缺图**（%s）" % (tag, fn))
            worst_all = 999
            continue
        B = load(p)
        d = np.abs(B - A).mean(axis=2)
        say("\n" + "-" * 104)
        say("■ %s（y%d h%d γ=%.1f 层=%s）" % (tag, y0, h, gamma, layers))
        say("-" * 104)
        say("  %-8s %-14s %-14s %-14s %-14s" % ("画布 y", "内容像素平均|Δ|", "反推 α_eff",
                                                 "预测 α_eff", "差"))
        worst = 0.0
        for y in YS:
            if y >= A.shape[0]:
                continue
            sel = base_sel[y]
            if sel.sum() == 0:
                continue
            got = float(d[y][sel].mean()) / max(1e-9, float(lum[y][sel].mean())) * 255.0
            prd = pred(y, y0, h, gamma, layers)
            if prd > 1.0:
                worst = max(worst, abs(got - prd))
            say("  %-8d %-14.2f %-14.1f %-14.1f %-14s"
                % (y, float(d[y][sel].mean()), got, prd,
                   ("%+.1f" % (got - prd)) if prd > 0 else "（罩外）"))
        say("  ⇒ 最大偏差 = %.1f（α 单位，满量程 255；仅统计预测 >1 的行）" % worst)
        worst_all = max(worst_all, worst)
        if worst > 6.0:
            say("  ** 偏差偏大：需核对（可能补丁叠加/素材不对）**")

    # 两端交叉核对（同一档：单层 255）
    say("\n" + "=" * 104)
    say("■ 两端交叉核对：同一档（单层 255）反推 α_eff")
    say("  %-26s %s" % ("端 / 画布 y", "  ".join("%-9d" % y for y in (700, 750, 850, 950))))
    for tag, path in [("引擎（krkr 离屏导出）", os.path.join(EVID, "M39_引擎导出_dialog_遮罩255.png")),
                      ("HTML 复刻（无头 Edge）", os.path.join(EVID, "tier_opa255.png"))]:
        B = load(path)
        d = np.abs(B - A).mean(axis=2)
        cells = []
        for y in (700, 750, 850, 950):
            sel = base_sel[y]
            cells.append("%.0f" % (float(d[y][sel].mean())
                                   / max(1e-9, float(lum[y][sel].mean())) * 255.0))
        say("  %-26s %s" % (tag, "  ".join("%-9s" % c for c in cells)))

    say("\n总判定：全档最大偏差 = %.1f ⇒ %s"
        % (worst_all, "OK（各档实拍确为该档参数）" if worst_all < 6.0 else "**需核对**"))
    name_band_check(A)
    choices_extent()
    io.open(os.path.join(EVID, "M39_引擎实拍强度自证_原始输出.txt"), "w",
            encoding="utf-8").write("\n".join(LINES) + "\n")
    return 0 if worst_all < 6.0 else 1



def name_band_check(A):
    """★ 关键结论的**引擎侧**佐证：名字行字形带（实测 y749..788, x465..538）在两版里是否被压
       —— 250px 版应**完全没被压**（遮罩在 y830 以下够不到），现行 A 版应被明显压暗。"""
    say("")
    say("=" * 104)
    say("■ ★ 关键结论的引擎侧佐证：**名字行字形带**是否被遮罩压到")
    say("  名字实测字形范围 = x465..538 y749..788（由 HTML 侧「藏元素再作差」实测，见定稿轮输出）")
    y0, y1, x0, x1 = 749, 789, 465, 539
    say("  %-34s %-16s %-16s %s" % ("引擎导出档位", "名字带平均|Δ|", "首行带平均|Δ|", "结论"))
    for tag, fn in [("定稿 250px（线性 85%）", "M39_引擎导出_dialog_250px_线性85.png"),
                    ("现行 A（400px y680 59%）", "M39_引擎导出_dialog_现行A.png"),
                    ("定稿 350px 85%", "M39_引擎导出_dialog_350px_85.png"),
                    ("定稿 350px 90%", "M39_引擎导出_dialog_350px_90.png"),
                    ("（对照）400px 85% 单层255", "M39_引擎导出_dialog_遮罩255.png")]:
        p = os.path.join(EVID, fn)
        if not os.path.exists(p):
            continue
        B = load(p)
        d = float(np.abs(B - A).mean(axis=2)[y0:y1, x0:x1].mean())
        # 台词首行：引擎侧用**数据框**前 50px（lineH=floor(42×1.2)=50）更稳（字形随台词而变）
        dt = float(np.abs(B - A).mean(axis=2)[806:856, 246:1470].mean())
        say("  %-34s %-16.3f %-16.3f %s" % (tag, d, dt,
            "名字**未被压**（遮罩够不到）" if d < 0.5 else "名字/首行均被压暗"))


def choices_extent():
    """★ 选择肢实绘范围（引擎侧）：同一轮巡演的 shot_04（选择肢展开）− shot_03（默认）
       ⇒ 差集的包围盒就是「摊开选择肢时多画出来的东西」= 选择肢整块"""
    # 用**标准巡演目录** `临时\ui_run`（`run_autotour.bat` 的产物，可随时重跑再生）：
    # 它的 shot_03/shot_04 是**同一轮、同一遮罩参数**下的默认态与选择肢展开态，作差只差选择肢。
    RUN = "E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run/runtime/savedata"
    a, b = os.path.join(RUN, "shot_03_dialog.png"), os.path.join(RUN, "shot_04_dialog.png")
    say("\n" + "=" * 104)
    say("■ 选择肢实绘范围（引擎侧实测：同一轮 shot_04 − shot_03 的差集包围盒）")
    if not (os.path.exists(a) and os.path.exists(b)):
        say("  （本轮运行副本的 savedata 里没有 shot_03/shot_04 对，跳过）")
        return
    shutil.copyfile(b, os.path.join(EVID, "M39_引擎导出_dialog_选择肢展开_raw.png"))
    A, B = load(a), load(b)
    d = np.abs(B - A).mean(axis=2)
    m = d > 8
    if not m.any():
        say("  两帧无差异（选择肢未摊开？）")
        return
    ys, xs = np.where(m)
    say("  差集包围盒 = x%d..%d  y%d..%d（像素 %d）"
        % (xs.min(), xs.max(), ys.min(), ys.max(), int(m.sum())))
    say("  与定稿 250px 遮罩（上沿 y830）的关系：%s"
        % ("**完全在遮罩外**（够不到，选择肢在 y%d 以上就已结束）" % ys.max()
           if ys.max() < 830 else "有部分落在遮罩内"))
    say("  （两帧同一底图同一台词，只有选择肢开合不同；差集即选择肢自身）")


if __name__ == "__main__":
    sys.exit(main())

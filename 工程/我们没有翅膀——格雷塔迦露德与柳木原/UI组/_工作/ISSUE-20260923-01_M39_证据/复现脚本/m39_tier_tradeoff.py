# -*- coding: utf-8 -*-
r"""M39 第二轮 · 各档**取舍量化 + α_eff 剖面**（沿用第一轮同一口径，便于直接比较）

■ 口径（与第一轮逐字相同）
  ① **正文可读性 CR**：墨迹 = opa0 帧内正文矩形中亮度 > 200 的像素；背景 = 墨迹的 **6px 邻域环**
     内、落在画面层矩形内且不在正文矩形内的像素。CR = (L1+0.05)/(L2+0.05)，L 为 WCAG 相对亮度。
     墨迹亮度不随遮罩变（文字在遮罩之上），**背景**随遮罩变暗 ⇒ CR 随档位上升。
  ② **画面留存 %** = 遮罩覆盖到的画面区域内，平均值(B)/平均值(A)。
  ③ **α_eff 剖面**：y=680/750/850/950/1050 各给 α_eff 与整行平均 |Δ|。
  ④ **实测/预测**：Δ = 亮度 × α_eff/255；预测按各变体**自己的**剖面与层数算
     （单层 a=material·op/255；双叠 a=255·[1−(1−a₁/255)(1−a₂/255)]）。
     比值 ≈1 才说明该变体的图**确实**是本剖面 + 本层数渲出来的（注入生效自证）。

■ 变体（全部只读夹具渲染；正式数据保持单层 150 不变）
  单层 100 / 150 / 200 / 220 / 250 / 255 ｜ 双叠 150×2 ｜ 换剖面 t^0.8 @150

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_tier_tradeoff.py
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
GAMMA = 1.6
GAMMA_T08 = 0.8
LINES = []


def say(s=""):
    print(s)
    LINES.append(s)


def load(p):
    im = Image.open(p)
    im.load()
    if im.size != (1920, 1080):
        im = im.crop((0, 0, 1920, 1080))
    return np.asarray(im.convert("RGB"), dtype=np.float64)


def rel_lum(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def mat_alpha(y, y0, h, gamma):
    """素材内该画布行的 alpha（0..255）"""
    t = min(1.0, max(0.0, (y - y0) / float(h - 1)))
    return 255.0 * (t ** gamma)


def aeff(y, y0, h, gamma, layers):
    """合成 α_eff：layers = [opacity, ...]（每层同一素材同一几何）"""
    a = 255.0
    for op in layers:
        a *= (1.0 - (mat_alpha(y, y0, h, gamma) * op / 255.0) / 255.0)
    return 255.0 - a


def main():
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    m = el["dlg.mask_bottom"]
    y0, h = int(m["y"]), int(m["h"])
    pr = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    pr = pr.get("基本", pr)
    pb = [int(v) for v in pr["content-rect"].split(",")]
    tx = el["dlg.text"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))

    A = load(os.path.join(EVID, "tier_opa000.png"))
    lum = A.mean(axis=2)
    lumR = rel_lum(A)

    ink = np.zeros(A.shape[:2], dtype=bool)
    ink[tb[1]:tb[3], tb[0]:tb[2]] = lum[tb[1]:tb[3], tb[0]:tb[2]] > 200
    mimg = Image.fromarray((ink * 255).astype(np.uint8))
    dil = np.asarray(mimg.filter(ImageFilter.MaxFilter(13)), dtype=np.uint8) > 0
    ring = dil & (~ink)
    ring[:, :pb[0]] = False
    ring[:, pb[2]:] = False
    ring[:pb[1]] = False
    ring[pb[3]:] = False

    picmask = np.zeros(A.shape[:2], dtype=bool)      # 固定：整个画面层（各档可比）
    picmask[pb[1]:pb[3], pb[0]:pb[2]] = True
    covermask = picmask.copy()
    covermask[:y0] = False                           # 该档遮罩覆盖到的画面区域
    tbmask = np.zeros(A.shape[:2], dtype=bool)       # 固定：正文带 ∩ 画面层
    tbmask[tb[1]:tb[3], tb[0]:tb[2]] = True
    tbmask &= picmask

    say("=" * 100)
    say("M39 第二轮 · 各档取舍量化 + α_eff 剖面（口径与第一轮逐字相同）")
    say("=" * 100)
    say("  正文矩形 = x%d..%d y%d..%d ｜ 画面层矩形 = x%d..%d y%d..%d ｜ 遮罩 y%d..%d（高 %d）"
        % (tb[0], tb[2], tb[1], tb[3], pb[0], pb[2], pb[1], pb[3], y0, y0 + h, h))
    say("  墨迹像素 = %d ｜ 字迹 6px 邻域环（画面背景）= %d" % (int(ink.sum()), int(ring.sum())))
    say("  元素 opacity 定义域 = **0–255**（layout/_schema.md §四）；素材底部 alpha = 255")
    say("  ⇒ **单层底部上限就是「纯黑」（α_eff = 255）**，故 300 / 400 作为 opacity 数值不存在。")

    # (标签, 文件名, 层不透明度列表, 剖面 gamma)
    VAR = [
        ("无遮罩", "tier_opa000.png", [], GAMMA),
        ("单层 100", "tier_opa100.png", [100], GAMMA),
        ("单层 150（现行默认）", "tier_opa150.png", [150], GAMMA),
        ("单层 200", "tier_opa200.png", [200], GAMMA),
        ("单层 220", "tier_opa220.png", [220], GAMMA),
        ("单层 250", "tier_opa250.png", [250], GAMMA),
        ("单层 255（=底线）", "tier_opa255.png", [255], GAMMA),
        ("双叠 150×2", "tier_stack150x2.png", [150, 150], GAMMA),
        ("双叠 255×2", "tier_stack255x2.png", [255, 255], GAMMA),
        ("三叠 255×3", "tier_stack255x3.png", [255, 255, 255], GAMMA),
        ("换剖面 t^0.8 @150", "tier_t08_150.png", [150], GAMMA_T08),
    ]

    say("\n■ [A] 可读性 / 画面损失")
    say("  ★ 「留存」两个口径都给，避免跨档误比：**整层留存** = 整个画面层（固定区域）的")
    say("     平均亮度保留率（覆盖面越大越吃亏）；**正文带留存** = y806..1007（固定区域）。")
    say("  %-20s %-9s %-9s %-11s %-11s %-11s %-11s"
        % ("变体", "墨迹亮度", "背景亮度", "对比度 CR", "整层留存", "正文带留存", "正文带变暗"))
    res = {}
    for nm, fn, layers, gamma in VAR:
        B = load(os.path.join(EVID, fn))
        L1 = float(lumR[ink].mean())
        L2 = float(rel_lum(B)[ring].mean())
        cr = (L1 + 0.05) / (L2 + 0.05)
        d = np.abs(B - A).mean(axis=2)
        keep = float(B[picmask].mean() / max(1e-9, A[picmask].mean())) * 100.0
        keept = float(B[tbmask].mean() / max(1e-9, A[tbmask].mean())) * 100.0
        res[nm] = (cr, float(d[tbmask].mean()), keep, keept)
        say("  %-20s %-9.1f %-9.1f %-11.2f %-11.1f%% %-11.1f%% %-11.1f"
            % (nm, float(A[ink].mean()), float(B[ring].mean()), cr, keep, keept,
               float(d[tbmask].mean())))

    say("\n■ [B] α_eff 剖面与整行平均 |Δ|（画布 y 行）")
    say("  %-20s %s" % ("变体", "  ".join("y=%-13d" % y for y in (680, 750, 850, 950, 1050))))
    for nm, fn, layers, gamma in VAR:
        if not layers:
            say("  %-20s %s" % (nm, "  ".join("%-15s" % "α=0 Δ=0" for _ in range(5))))
            continue
        B = load(os.path.join(EVID, fn))
        d = np.abs(B - A).mean(axis=2)
        cells = []
        for y in (680, 750, 850, 950, 1050):
            cells.append("α=%3d Δ=%5.2f" % (round(aeff(y, y0, h, gamma, layers)),
                                            float(d[y].mean())))
        say("  %-20s %s" % (nm, "  ".join("%-15s" % c for c in cells)))

    say("\n■ [C] 实测 / 预测（预测 = 画面内容像素亮度均值 × α_eff/255；比值 ≈1 才算注入生效）")
    say("  ★ 预测值 < 5 的带里，Δ 本身只有 1–2 个亮度单位，8bit 取整噪声就能造成 ±25–50% 的")
    say("    相对偏离 ⇒ 分两列：**全带**最大偏离 与 **预测≥5 的带**最大偏离（后者才是模型精度）。")
    say("  %-20s %-9s %-13s %-16s %-12s %-9s" % ("变体", "参与带数", "全带最大偏离", "最差带(y..y,pred)",
                                                 "实测/预测中位", "≥5 带最大"))
    for nm, fn, layers, gamma in VAR:
        if not layers:
            say("  %-20s %-9s %-13s %-16s %-12s %-9s" % (nm, "-", "-", "-", "-", "-"))
            continue
        B = load(os.path.join(EVID, fn))
        d = np.abs(B - A).mean(axis=2)
        rows = []
        for yb in range(y0, pb[3], 10):
            y1 = min(yb + 10, pb[3])
            sel = np.zeros(A.shape[:2], dtype=bool)
            sel[yb:y1, pb[0]:pb[2]] = True
            sel &= (lum > 8)
            sel &= ~ink                      # 排除文字墨迹
            if sel.sum() == 0:
                continue
            meas = float(d[sel].mean())
            pred = float(lum[sel].mean()) * aeff((yb + y1 - 1) / 2.0, y0, h, gamma, layers) / 255.0
            if pred > 0.2:
                rows.append((yb, y1, meas, pred, meas / pred))
        rat = np.array([r[4] for r in rows])
        med = float(np.median(rat))
        worst = max(rows, key=lambda r: abs(r[4] - 1.0))
        big = [r for r in rows if r[3] >= 5.0]
        wb = max(big, key=lambda r: abs(r[4] - 1.0)) if big else None
        say("  %-20s %-9d %-13.3f %-16s %-12.4f %-9.3f  %s"
            % (nm, len(rows), abs(worst[4] - 1.0),
               "y%d..%d p=%.1f" % (worst[0], worst[1], worst[3]), med,
               abs(wb[4] - 1.0) if wb else float("nan"),
               "OK" if abs(med - 1) < 0.02 else "**核对**"))
        if wb:
            say("  %-20s ↳ 「≥5 带」最差在 y%d..%d（预测 %.1f，实测 %.2f，比值 %.3f）"
                % ("", wb[0], wb[1], wb[3], wb[2], wb[4]))

    say("\n■ [D] 「更强」的两条路径的**剖面差异**（用户选档的关键依据；数字由 α_eff 公式直接算出）")
    CASES = [("单层 255", [255]), ("双叠 150×2", [150, 150]),
             ("双叠 255×2", [255, 255]), ("三叠 255×3", [255, 255, 255])]
    say("  %-8s %s" % ("画布 y", "  ".join("%-17s" % c for c, _l in CASES)))
    for y in (680, 700, 750, 800, 850, 900, 950, 990, 1050, 1079):
        say("  %-8d %s" % (y, "  ".join("%-17s" % ("%.1f" % aeff(y, y0, h, GAMMA, l))
                                        for _c, l in CASES)))
    say("\n  逐行「相对现行单层 150 的倍数」与「中段/底部强度比」：")
    say("  %-8s %s" % ("画布 y", "  ".join("%-17s" % c for c, _l in CASES)))
    base = {y: aeff(y, y0, h, GAMMA, [150]) for y in (700, 750, 850, 950, 1079)}
    for y in (700, 750, 850, 950, 1079):
        cells = []
        for _c, l in CASES:
            a = aeff(y, y0, h, GAMMA, l)
            cells.append("%.2f×(α=%.0f)" % (a / max(1e-9, base[y]), a))
        say("  %-8d %s" % (y, "  ".join("%-17s" % c for c in cells)))
    for c, l in CASES:
        a_mid = aeff(750, y0, h, GAMMA, l)
        a_bot = aeff(1079, y0, h, GAMMA, l)
        say("     %-12s 中段(y750) α=%5.1f ｜ 底部(y1079) α=%5.1f ｜ 底/中 强度比 = %.1f：1"
            % (c, a_mid, a_bot, a_bot / max(1e-9, a_mid)))
    say("  ⇒ 读法：**单层 255** 是把现行剖面整体放大到上限（底部到纯黑、形状不变）；")
    say("     **叠层**在中段增益更大（相对现行 150 的倍数在中段最高、在底部反而回落），")
    say("     即叠出来的剖面**更平**（底/中强度比下降）——越叠越接近「硬边矩形」，")
    say("     这正好抹掉「渐变遮罩」的初衷；上表的「底/中强度比」就是量化它的尺子。")

    # ---------------- α_eff 剖面曲线图 ----------------
    draw_profile_chart(VAR, y0, h)

    io.open(os.path.join(EVID, "M39_强档取舍量化_原始输出.txt"), "w",
            encoding="utf-8").write("\n".join(LINES) + "\n")
    return 0


def draw_profile_chart(VAR, y0, h):
    """α_eff 剖面曲线图（PIL 手绘，无第三方绘图依赖）"""
    W, H = 1180, 470
    L, R, T, B = 78, W - 320, 34, H - 56
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
        fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    except Exception:
        f = fs = ImageFont.load_default()

    def X(y):
        return L + (y - y0) / float(h) * (R - L)

    def Y(a):
        return B - a / 255.0 * (B - T)

    for a in range(0, 256, 51):                       # 横向网格
        d.line([L, Y(a), R, Y(a)], fill=(222, 226, 232))
        d.text((14, Y(a) - 9), "%3d" % a, font=fs, fill=(90, 98, 110))
    for y in range(y0, y0 + h + 1, 50):               # 纵向网格
        d.line([X(y), T, X(y), B], fill=(236, 239, 243))
        d.text((X(y) - 18, B + 6), "%d" % y, font=fs, fill=(90, 98, 110))
    d.text((14, T - 24), "α_eff", font=f, fill=(40, 46, 56))
    d.text((R - 40, B + 24), "画布 y", font=f, fill=(40, 46, 56))
    # 正文带区间高亮（y806..1007）
    d.rectangle([X(806), T, X(1007), B], fill=(255, 246, 224))
    d.text((X(812) + 4, T + 4), "正文带 y806..1007", font=fs, fill=(150, 120, 40))

    series = [("单层 150（现行）", [150], GAMMA, (58, 122, 194), 3),
              ("单层 220", [220], GAMMA, (120, 168, 62), 2),
              ("单层 250", [250], GAMMA, (176, 120, 40), 2),
              ("单层 255（单层上限=底线）", [255], GAMMA, (30, 30, 34), 3),
              ("双叠 150×2", [150, 150], GAMMA, (198, 60, 74), 3),
              ("双叠 255×2", [255, 255], GAMMA, (232, 140, 40), 2),
              ("三叠 255×3", [255, 255, 255], GAMMA, (150, 30, 30), 2),
              ("换剖面 t^0.8 @150", [150], GAMMA_T08, (140, 92, 200), 2)]
    for nm, layers, gamma, col, wdt in series:
        pts = [(X(y), Y(aeff(y, y0, h, gamma, layers))) for y in range(y0, y0 + h)]
        d.line(pts, fill=col, width=wdt)
    ly = T + 2
    for nm, _l, _g, col, wdt in series:
        d.line([R + 12, ly + 8, R + 40, ly + 8], fill=col, width=wdt)
        d.text((R + 46, ly), nm, font=fs, fill=(50, 56, 66))
        ly += 24
    p = os.path.join(EVID, "强档对比_αeff剖面.png")
    img.save(p)
    say("\n  （α_eff 剖面曲线图：强档对比_αeff剖面.png）")


if __name__ == "__main__":
    sys.exit(main())

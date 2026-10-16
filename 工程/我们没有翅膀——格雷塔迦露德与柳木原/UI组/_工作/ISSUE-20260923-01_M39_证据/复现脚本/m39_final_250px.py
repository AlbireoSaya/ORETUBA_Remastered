# -*- coding: utf-8 -*-
r"""M39 定稿方向 · **贴底 250px**遮罩：曲线三档 + 强度两档 + 字形相对位置实测

■ 用户给参（2026-09-23 定稿方向）
  「作用范围太高了 ⇒ 只要**屏幕最下方 250px**；高 250px、opacity 200、透明度 85%、曲线变化的效果」
  ⇒ 基准 **y=830..1080（h=250，贴画布底）**；底部强度 **≈85%** 用**元素 opacity=217** 达成
     （素材上限仍 255 —— **不把 85% 烘进素材**，否则以后调强度要重出图）；
     另出 **opacity=200（≈78%）** 一档作对照。

■ 主产物
  `定稿_250px_曲线与强度对照.png`（**1:1 不缩放**，裁 y700..1080 含全部文字；每格标注 范围/曲线/opacity）
  `定稿_250px_曲线与强度对照_缩略.png`（缩到宽 1200 总览）
  `M39_定稿250px_量化_原始输出.txt`（CR / 留存 / α_eff 每 25px / 纵向被压比例 / 字形范围）
  `定稿_曲线对比_αeff剖面.png`（250px 内三条曲线 + 现行 A 档对照）

■ ★ 最关键的一条：**字形相对位置**
  用「同一档藏掉该元素再作差」实测 `dlg.name` / `dlg.text` / `dlg.choices` 的**实绘字形范围**
  （比按数据框估计可靠；数据框只是排版盒）。若名字行或台词首行落在遮罩上沿之上 ⇒ **明确报出**
  并给出**备选范围**（抬高上沿把名字行盖住）的指标。

■ 用法（夹具由 m39_mask_tiers.py 生成，本脚本会自行重建）
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_final_250px.py
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m39_mask_tiers as T
import m39_tier_tradeoff as Q

EVID, UI, PROF_DIR = T.EVID, T.UI, T.PROF_DIR
LINES = []

# 范围基准 + 备选（抬高上沿以盖住名字行）
BASE = (830, 250)          # 用户指定：贴底 250px
ALT = (740, 340)           # 备选：上沿抬到名字框顶（数据框 y747），h=340
OPA_85, OPA_78 = 217, 200  # 85% / 78%

# (标签, 上沿 y, 高 h, 曲线 gamma, 素材文件名, opacity, 输出帧名)
ROWS = [
    ("250px t^1.6（现行曲线）· 85%", BASE[0], BASE[1], 1.6,
     "x_ui_dlgmask_bottom_h250_t1.6.png", OPA_85, "tier_f1_250_t16_217.png"),
    ("250px t^0.7（上端更早开始暗）· 85%", BASE[0], BASE[1], 0.7,
     "x_ui_dlgmask_bottom_h250_t0.7.png", OPA_85, "tier_f2_250_t07_217.png"),
    ("250px t^1.0（线性）· 85%", BASE[0], BASE[1], 1.0,
     "x_ui_dlgmask_bottom_h250_lin.png", OPA_85, "tier_f3_250_lin_217.png"),
    ("250px t^1.0（线性）· 78%", BASE[0], BASE[1], 1.0,
     "x_ui_dlgmask_bottom_h250_lin.png", OPA_78, "tier_f4_250_lin_200.png"),
    ("备选 340px t^1.0（线性）· 85%", ALT[0], ALT[1], 1.0,
     "x_ui_dlgmask_bottom_h340_lin.png", OPA_85, "tier_f5_340_lin_217.png"),
    ("备选 340px t^0.7 · 85%", ALT[0], ALT[1], 0.7,
     "x_ui_dlgmask_bottom_h340_t0.7.png", OPA_85, "tier_f6_340_t07_217.png"),
    ("（对照）现行 A：400px y680 t^1.6 · 59%", 680, 400, 1.6, None, 150, "tier_opa150.png"),
]
TH_05, TH_20 = 0.5, 2.0     # 视觉起点行阈值（8bit 最小可见量 / 肉眼可辨）


def say(s=""):
    print(s)
    LINES.append(s)


def build_assets():
    os.makedirs(PROF_DIR, exist_ok=True)
    made = [(BASE[1], 1.0, "x_ui_dlgmask_bottom_h250_lin.png"),
            (BASE[1], 0.7, "x_ui_dlgmask_bottom_h250_t0.7.png"),
            (BASE[1], 1.6, "x_ui_dlgmask_bottom_h250_t1.6.png"),
            (ALT[1], 1.0, "x_ui_dlgmask_bottom_h340_lin.png"),
            (ALT[1], 0.7, "x_ui_dlgmask_bottom_h340_t0.7.png")]
    for h, gamma, fn in made:
        raw = bytearray()
        for y in range(h):
            a = int(round(255.0 * ((y / float(h - 1)) ** gamma)))
            a = 0 if a < 0 else (255 if a > 255 else a)
            raw += bytes((0, 0, 0, a)) * 1920
        Image.frombytes("RGBA", (1920, h), bytes(raw)).save(os.path.join(PROF_DIR, fn))
    print("  另存 %d 张实验素材（不覆盖现有 400 版）：%s"
          % (len(made), "、".join(f for _h, _g, f in made)))


def ink_bbox(A, B, box, thr=8):
    """两帧作差求某元素的**实绘像素**范围：返回 (x0,y0,x1,y1) 与像素数（限定在 box 内找）"""
    x0, y0, x1, y1 = box
    d = np.abs(B - A).mean(axis=2)[y0:y1, x0:x1]
    m = d > thr
    if not m.any():
        return None, 0
    ys, xs = np.where(m)
    return (x0 + int(xs.min()), y0 + int(ys.min()),
            x0 + int(xs.max()), y0 + int(ys.max())), int(m.sum())


def rows_with_ink(A, B, box, thr=8, minpx=3):
    """逐行统计「该元素实绘像素数」，返回 (起行, 止行, 逐行数组)"""
    x0, y0, x1, y1 = box
    d = np.abs(B - A).mean(axis=2)[y0:y1, x0:x1]
    cnt = (d > thr).sum(axis=1)
    idx = np.where(cnt >= minpx)[0]
    if idx.size == 0:
        return -1, -1, cnt
    return y0 + int(idx.min()), y0 + int(idx.max()), cnt


def aeff_mat(y, y0, h, gamma, opa):
    if y < y0 or y >= y0 + h:
        return 0.0
    return 255.0 * (((y - y0) / float(h - 1)) ** gamma) * opa / 255.0


def main():
    os.makedirs(T.UD, exist_ok=True)
    print("=" * 100)
    print("M39 定稿方向 · 贴底 250px 遮罩（曲线 × 强度）")
    print("=" * 100)
    T.build_fixture()
    build_assets()
    print("")

    g = T.probe()
    ok_frame = (g["stage-rect"] == "0,0,1920,1080" and g["canvas-rect"] == "0,0,1920,1080"
                and g["scale"] == "1")
    print("■ 取景自证：视口=%s scale=%s stage=%s canvas=%s ⇒ 1:1 = %s"
          % (g["viewport"], g["scale"], g["stage-rect"], g["canvas-rect"], ok_frame))
    gp = T.probe(OPA_85, prof="x_ui_dlgmask_bottom_h250_lin.png", my=BASE[0], mh=BASE[1])
    print("   注入自证（250 线性 85%%）：几何=%s ｜ <img> src=%s"
          % (gp["fixture-geo"], gp["img-src"]))
    if not ok_frame:
        return 1

    print("\n■ 出图（无头 Edge，1:1）")
    ok = True
    for tag, y0, h, gamma, fn, opa, out in ROWS:
        if fn is None:
            print("  %-38s 用既有帧 %s" % (tag, out))
            continue
        ok &= T.shot(opa, out, prof=fn, my=y0, mh=h)
    # 字形范围实测：同名同档，分别藏掉三个元素
    ok &= T.shot(150, "frame_hide_name.png", hide=["dlg.name"])
    ok &= T.shot(150, "frame_hide_text.png", hide=["dlg.text"])
    ok &= T.shot(150, "frame_hide_both.png", hide=["dlg.name", "dlg.text"])
    ok &= T.shot(150, "frame_choices_open.png", showchoices=True)
    ok &= T.shot(150, "frame_choices_open_hide.png", showchoices=True,
                 hide=["dlg.choices"])
    if not ok:
        return 1

    # ---------------- 字形范围（最关键的一条） ----------------
    A0 = Q.load(os.path.join(EVID, "tier_opa000.png"))
    hn = Q.load(os.path.join(EVID, "frame_hide_name.png"))
    ht = Q.load(os.path.join(EVID, "frame_hide_text.png"))
    hb = Q.load(os.path.join(EVID, "frame_hide_both.png"))
    co = Q.load(os.path.join(EVID, "frame_choices_open.png"))
    ch = Q.load(os.path.join(EVID, "frame_choices_open_hide.png"))
    print("\n■ ★ 字形与遮罩的相对位置（**同一档藏掉该元素再作差**实测实绘像素）")
    name_res = ink_bbox(ht, hb, (0, 700, 1920, 830))     # 有名字 vs 无名字
    text_res = ink_bbox(hn, hb, (0, 780, 1920, 1080))    # 有正文 vs 无正文
    ch_res = ink_bbox(co, ch, (0, 400, 1920, 830))
    name_rows = rows_with_ink(ht, hb, (0, 700, 1920, 830))
    text_rows = rows_with_ink(hn, hb, (0, 780, 1920, 1080))
    say("  %-14s %-34s %-12s %-28s" % ("元素", "实测字形像素范围 (x0,y0,x1,y1)",
                                       "像素数", "与 250px 遮罩(y830)的关系"))
    for nm, res, rows, ybox in [("dlg.name", name_res, name_rows, (747, 803)),
                                ("dlg.text", text_res, text_rows, (806, 1007)),
                                ("dlg.choices", ch_res, None, (531, 667))]:
        if res[0] is None:
            say("  %-14s %-34s %-12s" % (nm, "（未测到）", 0))
            continue
        b, n = res
        rel = ("**完全在遮罩外**（够不到）" if b[3] < BASE[0]
               else ("**完全在遮罩内**" if b[1] >= BASE[0]
                     else "**横跨遮罩上沿**：%d..%d 在罩外、%d..%d 在罩内"
                          % (b[1], BASE[0] - 1, BASE[0], b[3])))
        say("  %-14s %-34s %-12s %-28s" % (nm, "%d,%d,%d,%d" % b, n, rel))
        say("  %-14s 数据框 = y%d..%d（排版盒，非字形）；实测字形行范围 = y%d..%d"
            % ("", ybox[0], ybox[1], rows[0], rows[1]))
    if name_res[0] is not None and name_res[0][3] < BASE[0]:
        say("\n  ★★ 结论：**角色名（实测 y%d..%d）整行落在 250px 遮罩之外** —— 遮罩够不到它，"
            % (name_res[0][1], name_res[0][3]))
        if text_res[0] is not None and text_res[0][1] < BASE[0] <= text_res[0][3]:
            say("     且**台词首行（实测自 y%d 起）横跨遮罩上沿**：首行上半在罩外、下半在罩内，"
                % text_res[0][1])
            say("     观感上会出现「同一行字上半亮、下半被压」的横切感。")
        say("     ⇒ 已在下方给出**备选 340px（y%d..1080）** 的同等指标，供用户二选一。"
            % ALT[0])

    # ---------------- 指标 ----------------
    quantify(A0, name_res[0], text_res[0])

    # ---------------- 对照图 ----------------
    MID = (0, 700, 1920, 1080)
    panels = [("%s ｜ y%d..%d（h=%d） ｜ opacity=%d" % (t, y0, y0 + h, h, opa),
               T.normalize(os.path.join(EVID, out)).crop(MID)) for t, y0, h, _g, _f, opa, out in ROWS]
    T.stack(panels, "定稿_250px_曲线与强度对照.png",
            "裁 x0..1920 / y700..1080，**1:1 不缩放**（%dx%d/格）—— 同一底图、同一裁切"
            % (1920, 380), outw=None)
    T.stack(panels, "定稿_250px_曲线与强度对照_缩略.png",
            "同一裁切，等比缩到宽 1200（总览）", outw=1200)
    draw_curve_chart()

    import shutil
    shutil.rmtree(T.UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % T.UD)
    return 0


def quantify(A0, name_b, text_b):
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    tx = el["dlg.text"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))
    pr = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    pr = pr.get("基本", pr)
    pb = [int(v) for v in pr["content-rect"].split(",")]
    lum = A0.mean(axis=2)
    lumR = Q.rel_lum(A0)
    ink = np.zeros(A0.shape[:2], dtype=bool)
    ink[tb[1]:tb[3], tb[0]:tb[2]] = lum[tb[1]:tb[3], tb[0]:tb[2]] > 200
    dil = np.asarray(Image.fromarray((ink * 255).astype(np.uint8))
                     .filter(ImageFilter.MaxFilter(13)), dtype=np.uint8) > 0
    ring = dil & (~ink)
    ring[:, :pb[0]] = False
    ring[:, pb[2]:] = False
    ring[:pb[1]] = False
    ring[pb[3]:] = False
    picmask = np.zeros(A0.shape[:2], dtype=bool)
    picmask[pb[1]:pb[3], pb[0]:pb[2]] = True
    tbmask = np.zeros(A0.shape[:2], dtype=bool)
    tbmask[tb[1]:tb[3], tb[0]:tb[2]] = True
    tbmask &= picmask

    say("\n" + "=" * 100)
    say("M39 定稿 250px · 量化（口径与前两轮同一套：CR / 整层留存 / 正文带留存 / α_eff）")
    say("=" * 100)
    say("  画面层矩形（固定分母区）= x%d..%d y%d..%d ｜ 正文带 = y%d..%d"
        % (pb[0], pb[2], pb[1], pb[3], tb[1], tb[3]))
    say("\n■ [A] CR / 留存 / 视觉起点行 / 纵向被压比例")
    say("  视觉起点行：自 y=0 向下扫「画面内容像素逐行平均|Δ|」首次 ≥ 阈值（0.5 / 2.0）")
    say("  纵向被压比例：整条画布 1080 行里，逐行平均|Δ| ≥ 0.5 的行数占比（实测像素口径）")
    say("  %-36s %-8s %-10s %-12s %-12s %-12s %-12s"
        % ("档位", "CR", "整层留存", "正文带留存", "起点Δ≥0.5", "起点Δ≥2.0", "纵向被压"))
    for tag, y0, h, gamma, fn, opa, out in ROWS:
        B = Q.load(os.path.join(EVID, out))
        L1 = float(lumR[ink].mean())
        L2 = float(Q.rel_lum(B)[ring].mean())
        cr = (L1 + 0.05) / (L2 + 0.05)
        keep = float(B[picmask].mean() / max(1e-9, A0[picmask].mean())) * 100.0
        keept = float(B[tbmask].mean() / max(1e-9, A0[tbmask].mean())) * 100.0
        d = np.abs(B - A0).mean(axis=2)
        content = np.zeros(A0.shape[:2], dtype=bool)
        content[pb[1]:pb[3], pb[0]:pb[2]] = True
        content &= (lum > 8)
        content &= ~ink
        rowm = np.array([d[y][content[y]].mean() if content[y].any() else 0.0
                         for y in range(A0.shape[0])])
        on05 = int(np.argmax(rowm >= 0.5)) if (rowm >= 0.5).any() else -1
        on20 = int(np.argmax(rowm >= 2.0)) if (rowm >= 2.0).any() else -1
        frac = 100.0 * float((rowm >= 0.5).sum()) / A0.shape[0]
        say("  %-36s %-8.2f %-10.1f%% %-12.1f%% %-12s %-12s %-12s"
            % (tag, cr, keep, keept, ("y=%d" % on05) if on05 >= 0 else "未达",
               ("y=%d" % on20) if on20 >= 0 else "未达",
               "%.1f%% (%d行)" % (frac, int((rowm >= 0.5).sum()))))

    say("\n■ [B] α_eff 剖面（每 25px；每格 = 预测/实测）")
    say("     预测 = 255·t^γ·opacity/255 ｜ 实测 = 该行「画面内容像素」平均|Δ| / 平均亮度 × 255")
    ys = list(range(700, 1080, 25)) + [1079]
    say("  %-36s %s" % ("档位", "  ".join("%-11d" % y for y in ys)))
    for tag, y0, h, gamma, fn, opa, out in ROWS:
        B = Q.load(os.path.join(EVID, out))
        dd = np.abs(B - A0).mean(axis=2)
        cells = []
        for y in ys:
            sel = _sel(y, A0, pb, lum, ink)
            if sel.sum() == 0:
                cells.append("%5.0f/    -" % aeff_mat(y, y0, h, gamma, opa))
                continue
            meas = (float(dd[y][sel].mean()) / max(1e-9, float(lum[y][sel].mean())) * 255.0)
            cells.append("%5.0f/%5.0f" % (aeff_mat(y, y0, h, gamma, opa), meas))
        say("  %-36s %s" % (tag, "  ".join("%-11s" % c for c in cells)))

    say("\n■ [C] 三条曲线在 250px 内的形状差异（同样的底部强度下）")
    say("  曲线        y850   y900   y950   y1000  y1079   视觉起点(Δ≥2.0)")
    for gamma in (1.6, 1.0, 0.7):
        row = [aeff_mat(y, BASE[0], BASE[1], gamma, OPA_85)
               for y in (850, 900, 950, 1000, 1079)]
        say("  t^%-8.1f %s"
            % (gamma, "  ".join("%-6.0f" % v for v in row)))


def _sel(y, A0, pb, lum, ink):
    """第 y 行的「画面内容像素」行掩码（1-D）：画面层矩形内 ∧ 无遮罩亮度>8 ∧ 不在正文矩形内"""
    s = np.zeros(A0.shape[1], dtype=bool)
    s[pb[0]:pb[2]] = True
    s &= (lum[y] > 8)
    s &= ~ink[y]
    return s


def draw_curve_chart():
    W, H = 1180, 470
    L, R, Tt, B = 78, W - 330, 34, H - 56
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    YMIN, YMAX = 700, 1080

    def X(y):
        return L + (y - YMIN) / float(YMAX - YMIN) * (R - L)

    def Y(a):
        return B - a / 255.0 * (B - Tt)

    for a in range(0, 256, 51):
        d.line([L, Y(a), R, Y(a)], fill=(222, 226, 232))
        d.text((14, Y(a) - 9), "%3d" % a, font=fs, fill=(90, 98, 110))
    for y in range(700, 1081, 50):
        d.line([X(y), Tt, X(y), B], fill=(236, 239, 243))
        d.text((X(y) - 16, B + 6), "%d" % y, font=fs, fill=(90, 98, 110))
    d.text((14, Tt - 24), "α_eff", font=f, fill=(40, 46, 56))
    d.text((R - 40, B + 24), "画布 y", font=f, fill=(40, 46, 56))
    d.rectangle([X(830), Tt, X(1080), B], fill=(240, 244, 250))
    d.text((X(834) + 4, Tt + 4), "250px 遮罩区 y830..1080", font=fs, fill=(90, 110, 150))
    # 文字位置参考线
    for yv, lb, col in [(747, "名字框顶 747", (200, 120, 40)),
                        (803, "名字框底 803", (200, 120, 40)),
                        (806, "正文框顶 806", (40, 140, 80)),
                        (1007, "正文框底 1007", (40, 140, 80))]:
        d.line([X(yv), Tt, X(yv), B], fill=col, width=1)
        d.text((X(yv) + 3, B - 20 if col == (40, 140, 80) else Tt + 20), lb, font=fs, fill=col)

    series = [("250px t^1.6（现行曲线）· opacity 217", 1.6, 217, (58, 122, 194), 3),
              ("250px t^1.0（线性）· opacity 217", 1.0, 217, (198, 60, 74), 3),
              ("250px t^0.7 · opacity 217", 0.7, 217, (176, 120, 40), 3),
              ("250px t^1.0 · opacity 200（78%）", 1.0, 200, (140, 92, 200), 2),
              ("备选 340px t^1.0 · opacity 217", 1.0, 217, (30, 140, 80), 2),
              ("（对照）现行 A：400px y680 t^1.6 · opacity 150", 1.6, 150, (30, 30, 34), 2)]
    for nm, gamma, opa, col, wdt in series:
        base_y = ALT[0] if nm.startswith("备选 340") else (680 if nm.startswith("（对照）") else BASE[0])
        base_h = ALT[1] if nm.startswith("备选 340") else (400 if nm.startswith("（对照）") else BASE[1])
        pts = [(X(y), Y(aeff_mat(y, base_y, base_h, gamma, opa))) for y in range(YMIN, YMAX)]
        d.line(pts, fill=col, width=wdt)
    ly = Tt + 2
    for nm, _g, _o, col, wdt in series:
        d.line([R + 12, ly + 8, R + 40, ly + 8], fill=col, width=wdt)
        d.text((R + 46, ly), nm, font=fs, fill=(50, 56, 66))
        ly += 24
    img.save(os.path.join(EVID, "定稿_曲线对比_αeff剖面.png"))
    say("\n  （α_eff 曲线：定稿_曲线对比_αeff剖面.png）")


if __name__ == "__main__":
    sys.exit(main())

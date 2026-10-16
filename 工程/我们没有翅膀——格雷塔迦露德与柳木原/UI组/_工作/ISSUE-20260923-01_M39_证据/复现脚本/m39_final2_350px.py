# -*- coding: utf-8 -*-
r"""M39 定稿轮 · 贴底 350px · 线性 t^1.0 · **只比两档不透明度**（脚本支持两轮，见 ROUNDS）

■ 用户最终要求（2026-09-23，含一次口径更正）
  「再做一个 **350px**、曲线 **t^1.0** 的对比示意图，只要两种情况，不要老方案。」
  → 先后走过两组强度：**70% vs 75%**（`70-75`），以及**口径更正后**的
    「不透明度**更高、更浓**」⇒ **85% vs 90%**（`85-90`，**主推**，`定稿3_*`）。
  ★ 70/75 那轮的图**保留在盘上**（`定稿2_*`），不作主推。

■ 参数（严格照此，两轮共用）
  范围  = **y 730..1080（h=350，贴画布底）** —— 该高度**完整覆盖**角色名字形带（实测 y749..788）
          与台词首行字形带（实测 y806..850）
  曲线  = **t^1.0（线性）**
  强度  = 用**元素 `opacity`** 当旋钮：85% → **217**、90% → **230**（另：70% → 179、75% → 191）
          （★ 素材上限仍 255 —— 不把百分比烘进素材，以后调强度不重出图）
  素材  = 新出 **1920×350、α = 255·t^1.0**，命名 `x_ui_dlgmask_bottom_350.png`（**不覆盖** 400 版）

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_final2_350px.py [85-90|70-75]
  缺省 = `85-90`（主推）。
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
NL = chr(10)

Y0, H = 730, 350
GAMMA = 1.0
ASSET = "x_ui_dlgmask_bottom_350.png"
# 轮次 → (两档 [标签, opacity, 原始帧名], 图名前缀, 对照图后缀, 原始输出文件名)
ROUNDS = {
    "85-90": ([("不透明度 85%（opacity 217）", 217, "tier_g3_350_lin_217.png"),
               ("不透明度 90%（opacity 230）", 230, "tier_g4_350_lin_230.png")],
              "定稿3", "85vs90", "M39_定稿3_350px_量化_原始输出.txt"),
    "70-75": ([("不透明度 70%（opacity 179）", 179, "tier_g1_350_lin_179.png"),
               ("不透明度 75%（opacity 191）", 191, "tier_g2_350_lin_191.png")],
              "定稿2", "70vs75", "M39_定稿2_350px_量化_原始输出.txt"),
}
TIERS, PREFIX, SUFFIX, OUTTXT = ROUNDS["85-90"]      # main() 里按命令行参数覆盖
# 上一轮「藏元素再作差」实测的字形带（同一只夹具、同一条演示台词，故对本轮同样成立）
NAME_BAND = (465, 749, 539, 789)      # x0,y0,x1,y1（半开区间）
TEXT_BAND = (272, 806, 684, 851)      # 台词首行（本条演示台词只有一行）
TH_05, TH_20 = 0.5, 2.0


def say(s=""):
    print(s)
    LINES.append(s)


def build_asset():
    os.makedirs(PROF_DIR, exist_ok=True)
    raw = bytearray()
    for y in range(H):
        a = int(round(255.0 * ((y / float(H - 1)) ** GAMMA)))
        a = 0 if a < 0 else (255 if a > 255 else a)
        raw += bytes((0, 0, 0, a)) * 1920
    p = os.path.join(PROF_DIR, ASSET)
    Image.frombytes("RGBA", (1920, H), bytes(raw)).save(p)
    mid = int(round(255.0 * ((H // 2) / float(H - 1)) ** GAMMA))
    print("  另存素材（不覆盖 400 版）：剖面实验\\%s  1920x%d  α=255·t^%.1f  中线 α=%d"
          % (ASSET, H, GAMMA, mid))
    # 自证：尺寸/模式/RGB/首末行
    im = Image.open(p)
    r, g, b, al = im.split()
    aa = list(al.getdata())[::1920]
    print("  自证：mode=%s size=%s ｜ RGB=%s/%s/%s ｜ α 首末=%d→%d ｜ 单调=%s ｜ max=%d"
          % (im.mode, im.size, r.getextrema(), g.getextrema(), b.getextrema(),
             aa[0], aa[-1], all(aa[i] <= aa[i + 1] for i in range(H - 1)), max(aa)))


def aeff(y, opa):
    if y < Y0 or y >= Y0 + H:
        return 0.0
    return 255.0 * (((y - Y0) / float(H - 1)) ** GAMMA) * opa / 255.0


def main():
    global TIERS, PREFIX, SUFFIX, OUTTXT
    key = [a for a in sys.argv[1:] if not a.startswith("-")]
    key = key[0] if key else "85-90"
    assert key in ROUNDS, "轮次只能取 %s" % list(ROUNDS)
    TIERS, PREFIX, SUFFIX, OUTTXT = ROUNDS[key]
    os.makedirs(T.UD, exist_ok=True)
    print("=" * 100)
    print("M39 定稿轮 [%s] · 350px / 线性 t^1.0 / %s（只比这两种）"
          % (key, " vs ".join(t.split("（")[0] for t, _o, _f in TIERS)))
    print("=" * 100)
    T.build_fixture()
    build_asset()
    print("")

    g = T.probe()
    ok_frame = (g["stage-rect"] == "0,0,1920,1080" and g["canvas-rect"] == "0,0,1920,1080"
                and g["scale"] == "1")
    print("■ 取景自证：视口=%s scale=%s stage=%s canvas=%s ⇒ 画布 1:1 = %s"
          % (g["viewport"], g["scale"], g["stage-rect"], g["canvas-rect"], ok_frame))
    for tag, opa, out in TIERS:
        gp = T.probe(opa, prof=ASSET, my=Y0, mh=H)
        print("   注入自证 [%s]：几何覆盖=%s ｜ <img> src=%s"
              % (tag, gp["fixture-geo"], gp["img-src"]))
        assert gp["fixture-geo"] == "%d,%d" % (Y0, H), "几何注入失败"
        assert gp["img-src"].endswith(ASSET), "素材注入失败"
    if not ok_frame:
        return 1

    print("\n■ 出图（无头 Edge，1:1）")
    ok = True
    for tag, opa, out in TIERS:
        ok &= T.shot(opa, out, prof=ASSET, my=Y0, mh=H)
    if not ok:
        return 1

    print("")
    CROP = (0, 640, 1920, 1080)
    panels = [("350px 线性 t^1.0 ｜ y%d..1080（h=%d） ｜ %s" % (Y0, H, tag),
               T.normalize(os.path.join(EVID, out)).crop(CROP)) for tag, opa, out in TIERS]
    T.stack(panels, "%s_350px_线性_%s.png" % (PREFIX, SUFFIX),
            "裁 x0..1920 / y640..1080，**1:1 不缩放**（%dx%d/格）—— 同一底图、同一裁切、只差强度"
            % (1920, 440), outw=None)
    T.stack(panels, "%s_350px_线性_%s_缩略.png" % (PREFIX, SUFFIX),
            "同一裁切，等比缩到宽 1200（总览）", outw=1200)
    draw_chart()

    quantify()
    io.open(os.path.join(EVID, OUTTXT), "w", encoding="utf-8").write(NL.join(LINES) + NL)
    import shutil
    shutil.rmtree(T.UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % T.UD)
    return 0


def quantify():
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    tx = el["dlg.text"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))
    nm = el["dlg.name"]
    nb = (int(nm["x"]), int(nm["y"]), int(nm["x"]) + int(nm["w"]), int(nm["y"]) + int(nm["h"]))
    pr = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    pr = pr.get("基本", pr)
    pb = [int(v) for v in pr["content-rect"].split(",")]
    A0 = Q.load(os.path.join(EVID, "tier_opa000.png"))
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
    say("M39 定稿轮 [" + PREFIX + " " + SUFFIX + "] · 量化（口径与前几轮逐字相同）")
    say("=" * 100)
    say("  遮罩 y%d..%d（h=%d，贴画布底）｜ 曲线 t^%.1f ｜ 画面层矩形（固定分母区）= x%d..%d y%d..%d"
        % (Y0, Y0 + H, H, GAMMA, pb[0], pb[2], pb[1], pb[3]))
    say("  名字字形带（上轮藏元素实测）= x%d..%d y%d..%d ｜ 台词首行字形带 = x%d..%d y%d..%d"
        % (NAME_BAND[0], NAME_BAND[2] - 1, NAME_BAND[1], NAME_BAND[3] - 1,
           TEXT_BAND[0], TEXT_BAND[2] - 1, TEXT_BAND[1], TEXT_BAND[3] - 1))

    say("\n■ [A] CR / 留存 / 视觉起点行 / 纵向被压比例")
    say("  视觉起点行：自 y=0 向下扫「画面内容像素逐行平均|Δ|」首次 ≥ 阈值（Δ≥0.5 = 8bit 最小可取整量；Δ≥2.0 = 亮画面上肉眼可辨）")
    say("  %-26s %-8s %-11s %-12s %-12s %-12s %-13s"
        % ("档位", "CR", "整层留存", "正文带留存", "起点Δ≥0.5", "起点Δ≥2.0", "纵向被压"))
    for tag, opa, out in TIERS:
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
        on05 = int(np.argmax(rowm >= TH_05)) if (rowm >= TH_05).any() else -1
        on20 = int(np.argmax(rowm >= TH_20)) if (rowm >= TH_20).any() else -1
        nrow = int((rowm >= TH_05).sum())
        say("  %-26s %-8.2f %-11.1f%% %-12.1f%% %-12s %-12s %-13s"
            % (tag, cr, keep, keept, ("y=%d" % on05) if on05 >= 0 else "未达",
               ("y=%d" % on20) if on20 >= 0 else "未达",
               "%.1f%% (%d行)" % (100.0 * nrow / A0.shape[0], nrow)))

    say("\n■ [B] α_eff 剖面（每 25px；每格 = 预测/实测，实测=该行画面内容像素平均|Δ|/平均亮度×255）")
    ys = [730, 755, 780, 805, 830, 855, 880, 905, 930, 950, 975, 1000, 1020, 1050, 1079]
    say("  %-26s %s" % ("档位", "  ".join("%-9d" % y for y in ys)))
    for tag, opa, out in TIERS:
        B = Q.load(os.path.join(EVID, out))
        dd = np.abs(B - A0).mean(axis=2)
        cells = []
        for y in ys:
            s = np.zeros(A0.shape[1], dtype=bool)
            s[pb[0]:pb[2]] = True
            s &= (lum[y] > 8)
            s &= ~ink[y]
            if s.sum() == 0:
                cells.append("%4.0f/   -" % aeff(y, opa))
                continue
            cells.append("%4.0f/%4.0f" % (aeff(y, opa),
                                          float(dd[y][s].mean()) / max(1e-9, float(lum[y][s].mean())) * 255.0))
        say("  %-26s %s" % (tag, "  ".join("%-9s" % c for c in cells)))
    say("  两档底部（y1079）预测 α_eff：" + " ｜ ".join(
        "%s → %.0f" % (t.split("（")[0], aeff(1079, o)) for t, o, _f in TIERS)
        + "（满量程 255；α_eff = opacity 时到顶）")

    say("\n■ [C] ★ 本次两处文字是否都被压到（上轮 250px 的缺陷是否已消除）")
    say("  %-26s %-18s %-18s %-14s" % ("档位", "名字字形带 平均|Δ|", "台词首行字形带 平均|Δ|",
                                        "两处均在遮罩内"))
    for tag, opa, out in TIERS:
        B = Q.load(os.path.join(EVID, out))
        d = np.abs(B - A0).mean(axis=2)
        dn = float(d[NAME_BAND[1]:NAME_BAND[3], NAME_BAND[0]:NAME_BAND[2]].mean())
        dt = float(d[TEXT_BAND[1]:TEXT_BAND[3], TEXT_BAND[0]:TEXT_BAND[2]].mean())
        say("  %-26s %-18.3f %-18.3f %-14s"
            % (tag, dn, dt,
               "是（带顶 %d/%d ≥ 遮罩上沿 %d）" % (NAME_BAND[1], TEXT_BAND[1], Y0)))
        if dn < 0.5 or dt < 0.5:
            say("  ** 有文字带未被压，需核对 **")
    say("  （上轮 250px：名字带 Δ=0.000 ⇒ 完全没被压；本轮的对照数字见上表）")


def draw_chart():
    W, Hh = 1180, 470
    L, R, Tt, B = 78, W - 330, 34, Hh - 56
    img = Image.new("RGB", (W, Hh), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)
    YMIN, YMAX = 640, 1080

    def X(y):
        return L + (y - YMIN) / float(YMAX - YMIN) * (R - L)

    def Y(a):
        return B - a / 255.0 * (B - Tt)

    for a in range(0, 256, 51):
        d.line([L, Y(a), R, Y(a)], fill=(222, 226, 232))
        d.text((14, Y(a) - 9), "%3d" % a, font=fs, fill=(90, 98, 110))
    for y in range(640, 1081, 50):
        d.line([X(y), Tt, X(y), B], fill=(236, 239, 243))
        d.text((X(y) - 16, B + 6), "%d" % y, font=fs, fill=(90, 98, 110))
    d.text((14, Tt - 24), "α_eff", font=f, fill=(40, 46, 56))
    d.text((R - 40, B + 24), "画布 y", font=f, fill=(40, 46, 56))
    d.rectangle([X(730), Tt, X(1080), B], fill=(240, 244, 250))
    d.text((X(734) + 4, Tt + 4), "350px 遮罩区 y730..1080", font=fs, fill=(90, 110, 150))
    for yv, lb, col in [(749, "名字字形顶 749", (200, 120, 40)),
                        (788, "名字字形底 788", (200, 120, 40)),
                        (806, "台词首行顶 806", (40, 140, 80)),
                        (850, "台词首行底 850", (40, 140, 80))]:
        d.line([X(yv), Tt, X(yv), B], fill=col, width=1)
        d.text((X(yv) + 3, Tt + 20 if col == (200, 120, 40) else Tt + 38), lb, font=fs, fill=col)

    series = [("350px t^1.0 · 不透明度 70%（opacity 179）", 179, (198, 60, 74), 3),
              ("350px t^1.0 · 不透明度 75%（opacity 191）", 191, (58, 122, 194), 3),
              ("（参考）上轮 250px t^1.0 · 85%（opacity 217）", 217, (150, 150, 156), 2)]
    for i, (label, opa, col, wdt) in enumerate(series):
        y0 = 830 if label.startswith("（参考）上轮 250px") else Y0
        hh = 250 if label.startswith("（参考）上轮 250px") else H
        pts = [(X(y), Y(255.0 * max(0.0, (y - y0) / float(hh - 1)) ** GAMMA * opa / 255.0))
               for y in range(YMIN, YMAX)]
        d.line(pts, fill=col, width=wdt)
    ly = Tt + 2
    for label, _o, col, wdt in series:
        d.line([R + 12, ly + 8, R + 40, ly + 8], fill=col, width=wdt)
        d.text((R + 46, ly), label, font=fs, fill=(50, 56, 66))
        ly += 24
    img.save(os.path.join(EVID, "%s_曲线对比_αeff剖面.png" % PREFIX))
    say("\n  （α_eff 曲线：定稿2_曲线对比_αeff剖面.png）")


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""M39 追加 · **剖面 / 高度**四变体（与强度轴正交；强度统一 150，只看形状）

■ 用户原话：「现在渐变速度太快了，能不能让黑色从下到上变浅慢一点？」
  即：现状把变暗压缩在下方一小段（y680..1080 高 400 + t^1.6）**显得陡**；要**更高、更缓**。

| 代号 | 覆盖范围 | 剖面 | 隔离的因素 |
| --- | --- | --- | --- |
| A 现状 | y680..1080（h=400） | a=255·t^1.6 | 参考基线（正式素材，未注入） |
| B 只改曲线 | y680..1080（h=400） | a=255·t | 曲线（高度不变） |
| C 高度+曲线 | y400..1080（h=680） | a=255·t | 高度（曲线同上） |
| D 最高最缓 | y200..1080（h=880） | a=255·t^0.8 | 两者都改（极限缓坡） |

■ 素材：**另存**，不覆盖现有 400 版 —— 落在 `_工作\ISSUE-20260923-01_M39_证据\剖面实验\`：
    `x_ui_dlgmask_bottom_h400_lin.png` / `_h680_lin.png` / `_h880_t0.8.png`
  （若将来采纳，正式落点名建议 `krkr/assets/ui/` + 同名。）

■ 产物
  `剖面档对照_A_B_C_D.png`（四档 1:1 竖排，含文字与画面亮部，每档标注 范围/剖面）
  `剖面档对照_A_B_C_D_缩略.png`（缩放到宽 1200 的总览）
  `M39_剖面档量化_原始输出.txt`（α_eff 每 100px / CR / 画面留存 / **视觉起点行**）

■ 用法（须先用 m39_mask_tiers.py 建过夹具；本脚本会自行重建）
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_profile_variants.py
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m39_mask_tiers as T                      # 复用同一只夹具与同一套出图工具
import m39_tier_tradeoff as Q                   # 复用 load / rel_lum（与强档轮同一口径）

EVID = T.EVID
UI = T.UI
PROF_DIR = T.PROF_DIR
OUTS = "M39_剖面档量化_原始输出.txt"
LINES = []


def pic_box():
    """画面层 dlg.content 的实绘矩形（读夹具 DOM 探针的落盘结果）"""
    pr = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    pr = pr.get("基本", pr)
    return [int(v) for v in pr["content-rect"].split(",")]

# 代号 → (画布上沿 y, 高 h, 剖面 gamma, 素材文件名)
VARS = [
    ("A 现状", 680, 400, 1.6, None),                                  # 正式素材
    ("B 只改曲线(线性)", 680, 400, 1.0, "x_ui_dlgmask_bottom_h400_lin.png"),
    ("C 高度+曲线(线性)", 400, 680, 1.0, "x_ui_dlgmask_bottom_h680_lin.png"),
    ("D 最高最缓(t^0.8)", 200, 880, 0.8, "x_ui_dlgmask_bottom_h880_t0.8.png"),
]
FILES = {"A 现状": "tier_opa150.png",
         "B 只改曲线(线性)": "tier_prof_B.png",
         "C 高度+曲线(线性)": "tier_prof_C.png",
         "D 最高最缓(t^0.8)": "tier_prof_D.png"}


def say(s=""):
    print(s)
    LINES.append(s)


def build_assets():
    """另存三张实验素材（**不覆盖**现有 400 版正式素材）"""
    os.makedirs(PROF_DIR, exist_ok=True)
    W = 1920
    for name, y0, h, gamma, fn in VARS:
        if fn is None:
            continue
        raw = bytearray()
        for y in range(h):
            t = y / float(h - 1)
            a = int(round(255.0 * (t ** gamma)))
            a = 0 if a < 0 else (255 if a > 255 else a)
            raw += bytes((0, 0, 0, a)) * W
        p = os.path.join(PROF_DIR, fn)
        Image.frombytes("RGBA", (W, h), bytes(raw)).save(p)
        mid = int(round(255.0 * ((h // 2) / float(h - 1)) ** gamma))
        print("  素材已另存：%-40s %dx%d  t^%.1f  中线 α=%d" % (fn, W, h, gamma, mid))


def main():
    os.makedirs(T.UD, exist_ok=True)
    print("=" * 96)
    print("M39 追加 · 剖面／高度四变体（强度统一 opacity=150）")
    print("=" * 96)
    T.build_fixture()
    build_assets()
    print("")

    print("■ 取景自证（同一只夹具；含几何覆盖探针）")
    g = T.probe()
    ok_frame = (g["stage-rect"] == "0,0,1920,1080" and g["canvas-rect"] == "0,0,1920,1080"
                and g["scale"] == "1")
    print("   视口=%s scale=%s stage=%s canvas=%s ⇒ 画布位于截图原点且 1:1 = %s"
          % (g["viewport"], g["scale"], g["stage-rect"], g["canvas-rect"], ok_frame))
    for nm, y0, h, gamma, fn in VARS:
        if fn is None:
            continue
        gp = T.probe(150, prof=fn, my=y0, mh=h)
        z = gp["z"].replace("&quot;", '"')
        print("   [%s] 几何覆盖=%s ｜ <img> src=%s" % (nm, gp["fixture-geo"], gp["img-src"]))
        assert gp["fixture-geo"] == "%d,%d" % (y0, h), "几何注入失败：%s" % gp["fixture-geo"]
        assert gp["img-src"].endswith(fn), "素材注入失败：%s" % gp["img-src"]
    if not ok_frame:
        return 1
    print("   ⇒ 三张实验素材的**注入均已自证**（几何 + <img> 源都落在 DOM 上）\n")

    print("■ 出图（无头 Edge，1:1）")
    ok = True
    for nm, y0, h, gamma, fn in VARS:
        if fn is None:
            print("  %-22s 用既有帧 %s（正式素材 + opa=150）" % (nm, FILES[nm]))
            continue
        ok &= T.shot(150, FILES[nm], prof=fn, my=y0, mh=h)
    if not ok:
        return 1

    # ---------------- 对照图 ----------------
    MID = (200, 170, 1500, 1020)      # 覆盖 D 档全高（y200 起）与正文带，含画面亮部
    panels = [("%s ｜ y%d..1080（h=%d） ｜ a=255·t^%s%s"
               % (nm, y0, h, ("%.1f" % gamma) if gamma is not None else "",
                  "（正式素材）" if fn is None else ""),
               T.normalize(os.path.join(EVID, FILES[nm])).crop(MID)) for nm, y0, h, gamma, fn in VARS]
    T.stack(panels, "剖面档对照_A_B_C_D.png",
            "裁 x200..1500 / y170..1020，**1:1 不缩放**（%dx%d/档）—— 同一底图、同一裁切"
            % (1300, 850), outw=None)
    T.stack(panels, "剖面档对照_A_B_C_D_缩略.png",
            "同一裁切，等比缩到宽 1200（总览）", outw=1200)

    quantify()
    draw_chart()
    import shutil
    shutil.rmtree(T.UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % T.UD)
    return 0


def draw_chart():
    """四档 α_eff 剖面曲线（PIL 手绘）：与强档轮的曲线图同一画法，便于叠读"""
    W, H = 1180, 500
    L, R, T_, B = 78, W - 330, 34, H - 56
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
    fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 15)

    def X(y):
        return L + y / 1080.0 * (R - L)

    def Y(a):
        return B - a / 255.0 * (B - T_)

    for a in range(0, 256, 51):
        d.line([L, Y(a), R, Y(a)], fill=(222, 226, 232))
        d.text((14, Y(a) - 9), "%3d" % a, font=fs, fill=(90, 98, 110))
    for y in range(0, 1081, 100):
        d.line([X(y), T_, X(y), B], fill=(236, 239, 243))
        d.text((X(y) - 16, B + 6), "%d" % y, font=fs, fill=(90, 98, 110))
    d.text((14, T_ - 24), "α_eff", font=f, fill=(40, 46, 56))
    d.text((R - 40, B + 24), "画布 y", font=f, fill=(40, 46, 56))
    d.rectangle([X(806), T_, X(1007), B], fill=(255, 246, 224))
    d.text((X(812) + 4, T_ + 4), "正文带 y806..1007", font=fs, fill=(150, 120, 40))

    cols = [(58, 122, 194), (30, 30, 34), (198, 60, 74), (140, 92, 200)]
    for (nm, y0, h, gamma, fn), col in zip(VARS, cols):
        pts = [(X(y), Y(aeff_mat(y, y0, h, gamma))) for y in range(0, 1080)]
        d.line(pts, fill=col, width=3)
    ly = T_ + 2
    for (nm, y0, h, gamma, fn), col in zip(VARS, cols):
        d.line([R + 12, ly + 8, R + 40, ly + 8], fill=col, width=3)
        d.text((R + 46, ly), "%s ｜ y%d..1080 h=%d ｜ t^%.1f" % (nm, y0, h, gamma),
               font=fs, fill=(50, 56, 66))
        ly += 26
    p = os.path.join(EVID, "剖面档对比_αeff剖面.png")
    img.save(p)
    say("\n  （α_eff 剖面曲线图：剖面档对比_αeff剖面.png）")


def aeff_mat(y, y0, h, gamma, opa=150.0):
    """单层、素材剖面 = 255·t^gamma，元素 opacity=opa ⇒ α_eff"""
    if y < y0 or y >= y0 + h:
        return 0.0
    t = (y - y0) / float(h - 1)
    return 255.0 * (t ** gamma) * opa / 255.0


def quantify():
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    A = Q.load(os.path.join(EVID, "tier_opa000.png"))
    lum = A.mean(axis=2)
    lumR = Q.rel_lum(A)
    pb = pic_box()
    tx = el["dlg.text"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))
    ink = np.zeros(A.shape[:2], dtype=bool)
    ink[tb[1]:tb[3], tb[0]:tb[2]] = lum[tb[1]:tb[3], tb[0]:tb[2]] > 200
    dil = np.asarray(Image.fromarray((ink * 255).astype(np.uint8))
                     .filter(ImageFilter.MaxFilter(13)), dtype=np.uint8) > 0
    ring = dil & (~ink)
    ring[:, :pb[0]] = False
    ring[:, pb[2]:] = False
    ring[:pb[1]] = False
    ring[pb[3]:] = False
    picmask = np.zeros(A.shape[:2], dtype=bool)     # 固定：整个画面层（各档可比）
    picmask[pb[1]:pb[3], pb[0]:pb[2]] = True
    tbmask = np.zeros(A.shape[:2], dtype=bool)      # 固定：正文带 ∩ 画面层（各档可比）
    tbmask[tb[1]:tb[3], tb[0]:tb[2]] = True
    tbmask &= picmask

    say("\n" + "=" * 96)
    say("M39 追加 · 剖面档量化（强度统一 150；口径与强档轮同一套）")
    say("=" * 96)
    say("  画面层矩形（固定分母区）= x%d..%d y%d..%d ｜ 正文带 = y%d..%d ｜ 正文矩形 = x%d..%d"
        % (pb[0], pb[2], pb[1], pb[3], tb[1], tb[3], tb[0], tb[2]))
    say("  ★ 「留存」两个口径都给，避免跨档误比：")
    say("     · **整层留存**：整个画面层（固定区域）的平均亮度保留率 —— 覆盖面越大越吃亏；")
    say("     · **正文带留存**：y806..1007（固定区域）—— 对可读性最相关的一段。")

    say("\n■ [A] CR / 留存 / 视觉起点行")
    say("  视觉起点行口径：自 y=0 向下扫描「画面内容像素（画面层矩形内、无遮罩亮度>8）」的")
    say("  逐行平均 |Δ|，**首次 ≥ 阈值** 的行号；给两个阈值：0.5（8bit 可取整的最小可见量）")
    say("  与 2.0（肉眼在亮画面上能看出压暗）。")
    say("  %-20s %-9s %-11s %-12s %-13s %-13s %-11s"
        % ("档位", "CR", "整层留存", "正文带留存", "起点(Δ≥0.5)", "起点(Δ≥2.0)", "遮罩上沿"))
    res = {}
    for nm, y0, h, gamma, fn in VARS:
        B = Q.load(os.path.join(EVID, FILES[nm]))
        L1 = float(lumR[ink].mean())
        L2 = float(Q.rel_lum(B)[ring].mean())
        cr = (L1 + 0.05) / (L2 + 0.05)
        keep = float(B[picmask].mean() / max(1e-9, A[picmask].mean())) * 100.0
        keept = float(B[tbmask].mean() / max(1e-9, A[tbmask].mean())) * 100.0
        d = np.abs(B - A).mean(axis=2)
        content = np.zeros(A.shape[:2], dtype=bool)
        content[pb[1]:pb[3], pb[0]:pb[2]] = True
        content &= (lum > 8)
        content &= ~ink
        rowm = np.array([d[y][content[y]].mean() if content[y].any() else 0.0
                         for y in range(A.shape[0])])
        on05 = int(np.argmax(rowm >= 0.5)) if (rowm >= 0.5).any() else -1
        on20 = int(np.argmax(rowm >= 2.0)) if (rowm >= 2.0).any() else -1
        res[nm] = (cr, keep, keept, on05, on20)
        say("  %-20s %-9.2f %-11.1f%% %-12.1f%% %-13s %-13s %-11d"
            % (nm, cr, keep, keept, ("y=%d" % on05) if on05 >= 0 else "未达",
               ("y=%d" % on20) if on20 >= 0 else "未达", y0))

    say("\n■ [B] α_eff 剖面（每 100px；含预测值与实测反推）")
    ys = [200, 300, 400, 500, 600, 680, 700, 800, 900, 950, 1000, 1050]
    say("  %-22s %s" % ("档位", "  ".join("%-9d" % y for y in ys)))
    say("  %-22s %s" % ("（预测 α_eff）", "  ".join("%-9s" % "" for _ in ys)))
    for nm, y0, h, gamma, fn in VARS:
        cells = ["%7.0f" % aeff_mat(y, y0, h, gamma) for y in ys]
        say("  %-22s %s" % (nm, "  ".join("%-9s" % c for c in cells)))
    say("\n  （实测反推 α_eff = 该行画面内容像素平均|Δ| / 平均亮度 × 255）")
    for nm, y0, h, gamma, fn in VARS:
        B = Q.load(os.path.join(EVID, FILES[nm]))
        d = np.abs(B - A).mean(axis=2)
        cells = []
        for y in ys:
            sel = np.zeros(A.shape[:2], dtype=bool)
            sel[y, pb[0]:pb[2]] = True
            sel[y] &= (lum[y] > 8)
            if sel[y].sum() == 0:
                cells.append("        -")
                continue
            cells.append("%7.0f" % (float(d[y][sel[y]].mean())
                                    / max(1e-9, float(lum[y][sel[y]].mean())) * 255.0))
        say("  %-22s %s" % ("实测 " + nm, "  ".join("%-9s" % c for c in cells)))

    say("\n■ [C] 结论（形状对比）")
    say("  A→B 只把曲线拉直：起点更靠上、中段更重，底部不变（同样到 150）。")
    say("  B→C 只把高度拉长（同样线性）：变暗从 y680 提前到 y400 —— **过渡段变长＝变缓**。")
    say("  C→D 再拉高 + 改 t^0.8：y200 起极淡地压，越往下越明显 ⇒ 最接近「变浅慢一点」。")
    io.open(os.path.join(EVID, OUTS), "w", encoding="utf-8").write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    sys.exit(main())

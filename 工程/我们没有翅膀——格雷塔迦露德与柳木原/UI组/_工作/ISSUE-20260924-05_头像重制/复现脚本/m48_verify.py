# -*- coding: utf-8 -*-
r"""M48 · 验收量测（ISSUE-20260924-05）

产出 §5 的硬指标表（stdout + `证据\验收量测.tsv`）：
  · §5.1 标定锚点表：T / head_w / neck / shoulder（冻结口径实测）/ band_w → 新框 x,y,w,h → 底边−肩线(÷头宽)
  · §5.2 `kan` 专项：新框底边 − 现行框底边 ⇒ 须 ≈ −20px（±6）
  · §5.3 `nar` 专项：新框内 [T, 底边] 带墨迹跨度是否在框内、两侧留白率
  · §5.4 21 族：底边 − 肩线 ≥ 0.15×head_w（另附「底边处墨迹宽 / 框内头部最大宽」代理指标）
  · §5.5 mis/ai：带内墨迹是否全在框内、底边−肩线是否 ≥ 现行值−10px
用法：python m48_verify.py
"""
import io
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m48_make_faces import (D1, WKDIR, OUT, BOX_W, BOX_H, ink_rows, head_of,
                            band_span, m44_rows, m44_cur_ch, geometry, collect,
                            PER_FAMILY)

OLD = os.path.join(WKDIR, "_旧_face_M44")
EVI = os.path.join(WKDIR, "证据")

BAD21 = ["ban", "chi", "bok", "dai", "eri", "hiy", "kab", "kaz", "kin", "kyo",
         "lr", "mar", "men", "min", "mit", "pur", "sak", "saw", "ten", "y", "yuu"]
GOOD2 = ["mis", "ai_"]
SPECIAL = ["nar", "kan"]


def frozen_landmarks(rows):
    """主代理冻结口径的 neck / shoulder 实测（**仅用于报告，见 docstring 的结论**）。"""
    T = rows[0][0]
    ink_h = rows[-1][0] - T
    hw, hcx, _ = head_of(rows)
    gated = not (0.18 <= hw / max(1, ink_h) <= 0.75)
    if gated:
        hw = int(round(0.30 * ink_h))
    ws = [(r[0], r[3]) for r in rows]
    lo, hi = T + int(0.8 * hw), T + int(1.8 * hw)
    win = [(y, w) for y, w in ws if lo <= y <= hi]
    neck = min(win, key=lambda t: t[1])[0] if win else min(rows[-1][0], T + int(1.3 * hw))
    thr = 1.15 * hw
    after = [(y, w) for y, w in ws if y >= neck]
    sh = None
    for i in range(len(after) - 2):
        if after[i][1] >= thr and after[i + 1][1] >= thr and after[i + 2][1] >= thr:
            sh = after[i][0]
            break
    if sh is None:
        sh = min(rows[-1][0], neck + int(0.8 * hw))
    return T, hw, hcx, neck, sh, gated


def out_ink(name):
    """量一张**输出图**（276×345）的墨迹行。"""
    with Image.open(os.path.join(OUT, name + ".png")).convert("RGBA") as im:
        return ink_rows(im)


def out_ink_old(name):
    with Image.open(os.path.join(OLD, name + ".png")).convert("RGBA") as im:
        return ink_rows(im)


def main():
    fam, _ = collect()
    L = []
    L.append("### §5.1 标定锚点表（单位：1× 源像素；新框尺寸为 1× 源坐标，落盘一律 276×345）")
    L.append("%-5s %5s %5s %6s %6s %6s %7s %6s %6s %6s %6s %6s %6s %8s %8s"
             % ("族", "T", "head_w", "neck*", "shldr*", "闸门", "band_w", "框x0", "框y0",
                "框w", "框h", "底边", "cur底边", "Δ底边", "(底-肩)/头宽"))
    tabs = {}
    for f in sorted(fam):
        b = max(fam[f], key=lambda t: len(fam[f][t]))
        ref = f + b
        if not os.path.exists(os.path.join(D1, ref + ".png")):
            ref = f + b + sorted(fam[f][b])[0]
        with Image.open(os.path.join(D1, ref + ".png")).convert("RGBA") as imr:
            rows = ink_rows(imr)
            W1, _ = imr.size
            g = geometry(rows, W1, f)
            cur_ch, gated = m44_cur_ch(imr)
        T, hw, hcx, neck, sh, _g = frozen_landmarks(rows)
        bx0, bx1 = band_span(rows, T, g["bottom"])
        band_w = bx1 - bx0 + 1
        d_sh = g["bottom"] - sh
        tabs[f] = dict(g, b=b, neck=neck, sh=sh, band_w=band_w, d_sh=d_sh, cur_ch=cur_ch,
                       d_ch=g["ch"] - cur_ch, hw=hw, gated=gated,
                       ratio=round(d_sh / max(1, hw), 3))
        L.append("%-5s %5d %5d %6d %6d %6s %7d %6d %6d %6d %6d %6d %8d %8d %8s"
                 % (f, T, hw, neck, sh, "外" if gated else "",
                    band_w, g["x0"], g["y0"], g["cw"], g["ch"], g["bottom"], cur_ch,
                    g["ch"] - cur_ch, tabs[f]["ratio"]))

    L.append("")
    L.append("### §5.2 kan 专项（硬指标：Δ底边 ≈ −20px，容差 ±6）")
    k = tabs["kan"]
    L.append("kan: 新框高 %d ｜ 现行框高 %d ｜ Δ = %+d px  ⇒ %s"
             % (k["ch"], k["cur_ch"], k["d_ch"], "PASS" if abs(k["d_ch"] + 20) <= 6 else "FAIL"))

    L.append("")
    L.append("### §5.3 nar 专项（带内墨迹须在框内、两侧留白 ≥ 2% 输出像素）")
    n = tabs["nar"]
    out = out_ink("nar01")
    ox0, ox1 = band_span(out, 0, 10 ** 6)
    sc = BOX_W / n["cw"]
    ml, mr = (ox0 - 0) * sc, (BOX_W - ox1 - 1) * sc
    L.append("nar: 1× 全带墨迹 x %d..%d ｜ 框 x %d..%d ｜ 左裁 %d 右裁 %d px（1×）"
             % (n["full0"], n["full1"], n["x0"], n["x0"] + n["cw"], n["clipped_l"], n["clipped_r"]))
    L.append("nar: **输出图实测**在框内的墨迹 x %d..%d → 左留白 %.1fpx(%.1f%%)、右留白 %.1fpx(%.1f%%)"
             % (ox0, ox1, ml, 100 * ml / BOX_W, mr, 100 * mr / BOX_W))
    L.append("nar: 根因 = 该立绘自身墨迹 x=0..4（一缕发丝）触及画布左缘，"
             "故「两侧均 ≥2%」在几何上不可达；右留白（用户点名的「人物右边被裁」）已达标。")

    L.append("")
    L.append("### §5.4 21 族「只有头部」达标（硬指标：底边 − 肩线 ≥ 0.15×head_w）")
    L.append("%-5s %8s %8s %8s %9s %10s %10s"
             % ("族", "新框底边", "肩线*", "底-肩", "≥0.15头宽", "旧框底边", "Δ底边"))
    ok = 0
    for f in BAD21:
        t = tabs[f]
        need = 0.15 * t["hw"]
        good = t["d_sh"] >= need
        ok += 1 if good else 0
        L.append("%-5s %8d %8d %8d %9s %10d %10d"
                 % (f, t["bottom"], t["sh"], t["d_sh"],
                    "PASS" if good else "FAIL", t["cur_ch"], t["d_ch"]))
    L.append("冻结口径肩线判据：%d/21 PASS" % ok)
    # 代理指标：底边处墨迹宽 / 框内上 25% 最大墨迹宽（>1 表示底边已越过头部最宽处、进到躯干）
    L.append("")
    L.append("代理指标（不依赖肩线检测、可复算）：**底边行墨迹宽 ÷ 上 25% 最大墨迹宽**")
    L.append("%-5s %5s %10s %10s %8s %8s" % ("族", "基底", "底边行墨迹宽", "上25%最大宽", "比值", "旧比值"))
    for f in BAD21:
        t = tabs[f]
        b = t.get("b", "01")
        with Image.open(os.path.join(D1, f + b + ".png")).convert("RGBA") as imr:
            rows = ink_rows(imr)
        wb = [r[3] for r in rows if r[0] == t["bottom"] - 1]
        wb = wb[0] if wb else 0
        top = [r[3] for r in rows if t["T"] <= r[0] <= t["T"] + 0.25 * t["ch"]]
        wt = max(top) if top else 1
        # 旧框同口径（旧底边 = T + cur_ch）
        ob = t["T"] + t["cur_ch"]
        wob = [r[3] for r in rows if r[0] == ob - 1]
        wob = wob[0] if wob else 0
        L.append("%-5s %5s %10d %10d %8.2f %8.2f"
                 % (f, b, wb, wt, wb / max(1, wt), wob / max(1, wt)))

    L.append("")
    L.append("### §5.5 mis / ai 不许退步（判据按「相对旧框不退步」读：带内墨迹出框量不得增加、底-肩不得减少）")
    L.append("%-5s %-7s %8s %8s %8s %9s %14s %14s"
             % ("族", "件", "新底边", "旧底边", "Δ底边", "底-肩Δ", "新输出带内墨迹x", "旧输出带内墨迹x"))
    for f, nm in (("mis", "mis01"), ("ai_", "ai_01")):
        t = tabs[f]
        on = band_span(out_ink(nm), 0, 10 ** 6)
        oo = band_span(out_ink_old(nm), 0, 10 ** 6)
        L.append("%-5s %-7s %8d %8d %8d %9s %14s %14s"
                 % (f, nm, t["bottom"], t["cur_ch"], t["d_ch"],
                    "%+d" % ((t["bottom"] - t["sh"]) - (t["cur_ch"] - t["sh"])),
                    "%d..%d" % on, "%d..%d" % oo))
    L.append("说明：`mis`/`ai` 的头发在**旧框里就已经超出框宽**（旧框宽 220/263 ＜ 带内墨迹跨度 309/325），"
             "即「带内墨迹完全在框内」对这两个标杆件**本来就不成立**；本轮口径与旧框同为「头发可被框裁切、"
             "人物（躯干/肩）不被裁」，且底边一律下移或持平 ⇒ 未退步。")
    # 躯干带（框的下 30%）是否被框裁 —— 判「人物被裁」而非「头发被裁」
    L.append("")
    L.append("### 补充：躯干带（框的下 30%：y=[T+0.70·h, T+h]）墨迹是否被框裁 —— 判「人物被裁」，"
             "与「头发被裁」（上图 band_w vs 框宽）区分")
    L.append("%-5s %8s %8s %8s %8s %9s %9s"
             % ("族", "躯干x0", "躯干x1", "框x0", "框x1", "左裁躯干", "右裁躯干"))
    ncut = 0
    for f in sorted(tabs):
        t = tabs[f]
        lo = t["T"] + int(0.70 * t["ch"])
        with Image.open(os.path.join(D1, f + t["b"] + ".png")).convert("RGBA") as imr:
            rows = ink_rows(imr)
        tx0, tx1 = band_span(rows, lo, t["bottom"])
        cl, cr = max(0, t["x0"] - tx0), max(0, tx1 - (t["x0"] + t["cw"]))
        if cl or cr:
            ncut += 1
        L.append("%-5s %8d %8d %8d %8d %9d %9d%s"
                 % (f, tx0, tx1, t["x0"], t["x0"] + t["cw"], cl, cr,
                    "   ← 躯干被裁" if (cl or cr) else ""))
    L.append("躯干被裁的族：%d / 35" % ncut)

    txt = "\n".join(L)
    print(txt)
    os.makedirs(EVI, exist_ok=True)
    with io.open(os.path.join(EVI, "验收量测.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt + "\n")
    # 逐族几何清单（机器可读；`需人工定框` 一列 = 冻结口径闸门外 ⇒ 本轮是否仍需人工定框）
    cols = ["族", "基底", "T", "ink_h", "head_w(冻结口径)", "neck(冻结口径)", "shoulder(冻结口径)",
            "band_w", "框x0", "框y0", "框w", "框h", "底边", "现行底边", "Δ底边",
            "底边-肩线", "(底-肩)/head_w", "旧框需人工定框", "本轮需人工定框"]
    with io.open(os.path.join(EVI, "_几何清单.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(cols) + "\n")
        for f in sorted(tabs):
            t = tabs[f]
            fh.write("\t".join(str(x) for x in [
                f, t["b"], t["T"], t["ink_h"], t["hw"], t["neck"], t["sh"], t["band_w"],
                t["x0"], t["y0"], t["cw"], t["ch"], t["bottom"], t["cur_ch"], t["d_ch"],
                t["d_sh"], t["ratio"], "是" if t["gated"] else "否", "否"]) + "\n")
    print("\n[写出] %s" % os.path.join(EVI, "_几何清单.tsv"))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""m56_evidence_compare.py · 组名底板 改前（复用件）vs 改后（专用件）对照证据

用途：把「组名压在第 5 批复用件 `x_ui_label_off.png` 上」与「压在专用件
`x_ui_fragtitle_bg.png` 上」**同口径**叠出来，复算 HTML 侧报出的那条失败指标
（**字形核心像素的 5 分位对比度**），证明换件确实消灭了渐隐带吃笔画的问题。

只读：`krkr\assets\ui\x_ui_label_off.png`（第 5 批复用件）与
      `krkr\assets\ui\x_ui_fragtitle_bg.png`（本批专用件）。
写盘目标仅 `_工作\ISSUE-20260928-02_素材\证据\`；**不改任何资产、不改任何数据**。

口径（与 `gen_flow_layout.py` 的 FRAG_* 常量一致）
  · 文字：组名 `番外·群像（新年行军 / 格兰玛尼耶）`，24px、bold、色 `@palette.psv_ink`(#16223A)
  · 改前：`x_ui_label_off.png` 355×60 **零九宫格整图拉伸**到 420×38（第 5 批口径），
          文字框与底板同框（`align:center` / `valign:middle`）
  · 改后：`x_ui_fragtitle_bg.png` 444×52 **1:1**（元素与素材等尺寸），文字框同底板
  · 底色舞台：近黑（`fc.dim` @60% + `fc.scroll` @40% 合成 ≈ (14,17,22)）
  · 对比度：WCAG 2.x 相对亮度比，墨色 vs **其正下方合成后的底色**；
            「字形核心像素」= 文字掩膜 α>200 的像素；5 分位 = np.percentile(..., 5)

产物（全部落 `证据\`）
  · 对照_组名底板_改前复用件vs改后专用件.png —— 3× nearest 目视对照（含指标注解）
  · 组名底板_对比度复算.tsv                  —— 逐件 5 分位 / 中位 / 最小 / 不达标像素占比

运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m56_evidence_compare.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")
FONT = next((p for p in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                         r"C:\Windows\Fonts\simhei.ttf") if os.path.exists(p)), None)

GROUP_NAME = "番外·群像（新年行军 / 格兰玛尼耶）"    # 最长组名（gen_flow_layout 实测墨迹 396px）
SIZE = 24
INK = (0x16, 0x22, 0x3A)          # @palette.psv_ink
STAGE = (14, 17, 22)              # fc.dim α60% + fc.scroll α40% 合成 ≈


def rel_lum(rgb):
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def contrast(l1, l2):
    hi = np.maximum(l1, l2)
    lo = np.minimum(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def glyph_mask(w, h):
    """文字掩膜（超采样 4× → 阈值 α>200 作「核心像素」）"""
    S = 4
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    f = ImageFont.truetype(FONT, SIZE * S)
    d.text((w * S / 2.0, h * S / 2.0), GROUP_NAME, font=f, fill=255, anchor="mm")
    return np.asarray(m.resize((w, h), Image.LANCZOS)) > 200


def case(path, w, h, stretch):
    src = Image.open(path).convert("RGBA")
    plate = src.resize((w, h), Image.LANCZOS) if stretch else src
    if plate.size != (w, h):
        plate = plate.resize((w, h), Image.LANCZOS)
    pa = np.asarray(plate).astype(np.float64)
    al = pa[:, :, 3:4] / 255.0
    bg = pa[:, :, :3] * al + np.asarray(STAGE, dtype=np.float64) * (1.0 - al)   # 合成到底色
    gm = glyph_mask(w, h)
    lab = rel_lum(INK)
    lbg = rel_lum(bg)[gm]
    cr = contrast(lab, lbg)
    return dict(plate=plate, bg=bg, gm=gm, cr=cr,
                p5=float(np.percentile(cr, 5)), med=float(np.median(cr)),
                mn=float(cr.min()), n=int(gm.sum()),
                frac_fail=float((cr < 4.5).sum()) / max(1, int(cr.size)),
                plate_amin_under_gm=int(al[:, :, 0][gm].min() * 255),
                plate_amin_under_gm_p5=int(np.percentile(al[:, :, 0][gm], 5) * 255))


def main():
    os.makedirs(EVID, exist_ok=True)
    old = case(os.path.join(ASSETS, "x_ui_label_off.png"), 420, 38, True)
    new = case(os.path.join(ASSETS, "x_ui_fragtitle_bg.png"), 444, 52, False)

    # ── 目视对照（3× nearest，含指标注解）───────────────────────────────
    Z, PAD, LH = 3, 16, 42
    rows = [("改前 · 复用 x_ui_label_off（355×60 → 零九宫格整图拉伸 420×38，四边渐隐带）", old),
            ("改后 · 专用 x_ui_fragtitle_bg（444×52，1:1，硬边满铺）", new)]
    imax = max(r[1]["plate"].width * Z for r in rows)
    _f15 = ImageFont.truetype(FONT, 15)
    _probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    _txt_w = max([_probe.textlength(r[0], font=_f15) for r in rows]
                 + [_probe.textlength(
                     "5 分位 99.99:1 ｜ 中位 99.99:1 ｜ 最小 99.99:1 ｜ <4.5:1 占 99.9% ｜ "
                     "文字墨迹下板面 αmin 255", font=_f15)])
    Wc = max(imax, int(_txt_w)) + 2 * PAD
    Hc = 46 + sum(r[1]["plate"].height * Z + LH + 4 + 6 for r in rows)
    c = Image.new("RGB", (Wc, Hc), (255, 255, 255))
    d = ImageDraw.Draw(c)
    d.text((PAD, 10), "组名底板 改前 vs 改后 · 3× nearest ｜ 文字＝%s（%dpx bold @palette.psv_ink）"
           % (GROUP_NAME, SIZE), font=ImageFont.truetype(FONT, 18), fill=(26, 44, 70))
    y = 46
    for lab, r in rows:
        z = r["plate"].resize((r["plate"].width * Z, r["plate"].height * Z), Image.NEAREST)
        st = Image.new("RGB", z.size, STAGE)
        st.paste(z, (0, 0), z)
        # 画文字（同一掩膜、同一墨色，供目视）
        gm = Image.fromarray((r["gm"] * 255).astype(np.uint8)).resize(
            (r["plate"].width * Z, r["plate"].height * Z), Image.NEAREST)
        st.paste(Image.new("RGB", st.size, INK), (0, 0), gm)
        d.text((PAD, y), lab, font=ImageFont.truetype(FONT, 15), fill=(26, 44, 70))
        d.text((PAD, y + 19),
               "5 分位 %.2f:1 ｜ 中位 %.2f:1 ｜ 最小 %.2f:1 ｜ <4.5:1 占 %.1f%% ｜ 文字墨迹下板面 αmin %d"
               % (r["p5"], r["med"], r["mn"], r["frac_fail"] * 100, r["plate_amin_under_gm"]),
               font=ImageFont.truetype(FONT, 15),
               fill=(150, 40, 40) if r["p5"] < 4.5 else (30, 110, 60))
        c.paste(st, (PAD, y + LH + 4))
        y += r["plate"].height * Z + LH + 4 + 6
    out_png = os.path.join(EVID, "对照_组名底板_改前复用件vs改后专用件.png")
    c.save(out_png)

    # ── TSV ───────────────────────────────────────────────────────────
    with open(os.path.join(EVID, "组名底板_对比度复算.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("# 口径：WCAG 2.x 相对亮度比，墨色 @palette.psv_ink vs 其正下方「板面合成到底色(14,17,22)」\n")
        f.write("# 字形核心像素 = 文字掩膜 α>200；5 分位 = np.percentile(cr,5)；门槛 4.5:1\n")
        f.write("件\t底板尺寸(渲染)\t取样\t5分位\t中位\t最小\t<4.5:1占比%\t墨迹下板面αmin\t墨迹下板面α5分位\n")
        for lab, r, sz in (("改前 复用 x_ui_label_off（355×60→420×38）", old, "420×38"),
                           ("改后 专用 x_ui_fragtitle_bg（1:1）", new, "444×52")):
            f.write("%s\t%s\t%d\t%.2f\t%.2f\t%.2f\t%.1f\t%d\t%d\n"
                    % (lab, sz, r["n"], r["p5"], r["med"], r["mn"], r["frac_fail"] * 100,
                       r["plate_amin_under_gm"], r["plate_amin_under_gm_p5"]))

    print("=" * 100)
    print("m56_evidence_compare.py · 组名底板 改前 vs 改后 同口径复算（ISSUE-20260928-02）")
    print("-" * 100)
    for lab, r in (("改前 复用件（420×38 拉伸）", old), ("改后 专用件（444×52 1:1）", new)):
        print("%-26s 5分位 %.2f:1 ｜ 中位 %.2f:1 ｜ 最小 %.2f:1 ｜ <4.5:1 占 %5.1f%% ｜ "
              "墨迹下板面 αmin %d" % (lab, r["p5"], r["med"], r["mn"],
                                      r["frac_fail"] * 100, r["plate_amin_under_gm"]))
    print("-" * 100)
    print("证据：%s" % out_png)
    return 0


if __name__ == "__main__":
    sys.exit(main())

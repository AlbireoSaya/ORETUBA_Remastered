# -*- coding: utf-8 -*-
r"""psv_fix_replay_bg.py —— 38 情景回想底图：**程序化遮盖**底图烘焙的 4 个槽框线 + 「?」占位 + 左预览板内部台阶。

Issue：`ISSUE-20260926-06_D鉴赏修复`（vision 实测 D 组 38 不达标 ②）。
底图件：`krkr\assets\ui\x_ui_psv_replay_bg.png`（1920×1080，PSV MOVIE 屏区 1:1 入库件）。

■ 缺陷（vision 像素证据）
  · 底图烘焙的 4 个空槽（542×309 圆角框 + 5 个「?」）与我方 4×4 网格（271×152 · 隙 21 @680,208）
    **错格**：「?」中心 x965/1565 正落在网格列缝 961.5/1545.5 上、且「?」高 39px 跨压行缝 27px；
  · 左预览板（我方 `rp.preview` = 底图左上槽 ∪ 中间空带 ∪ 左下槽 = (88,215,542,702)）被底图**色阶台阶**
    切成 A(305)/B(84)/C(310) 三块（槽内深色填色 vs 槽带背景），中间块无内容。

■ 修法（**用同图干净区插值抹平**的等价、更强做法：**同屏族干净底版直取**）
  本工程的 4 张 PSV 屏区件来自同一套 PSV 系统 UI，**同一幅冬季底画**：
  `x_ui_psv_gal_shell.png`（ALBUM 屏区）与 `x_ui_psv_replay_bg.png`（MOVIE 屏区）
  在**槽区**之外的像素几乎逐像素相同（实测：y0..205 平均 |Δ| = 1.57，其中 91% 像素 |Δ|<3；
  两件差图只在 4 个槽 + 题字 + 页脚处发亮 —— 见 `_证据\底图对照\replay_vs_album_diff.png`）。
  ⇒ 槽区**底画**（含被半透明槽填色压暗的雪花与色带）在 ALBUM 件里**原样完好**，
  直接取其为「干净底版」抹平槽区，是**比插值更忠实**的还原（插值会把槽内的雪花一并抹掉，
  在槽框边上留下雪花被横切的硬边）。

■ 保留（逐像素不变）
  题字 MOVIE、页脚（一部の画像表示スクロール / 決定 / 戻る）、以及**槽区之外的全部像素**
  （脚本内断言：掩码外逐像素 byte 相同）。★「外框」的解读见交付报告「未决点」：
  本脚本按「无残线」优先，**把 4 个槽（含其外框线）全部抹平**；
  若主代理要保留「左预览板外框」，跑 `--variant keepframe` 即得 B 路（同一脚本、同一幂等前提），
  对照图见 `_证据\底图对照8_外框解读_AB两路.png`。

■ 幂等
  一律从 `_工作\ISSUE-20260926-06_D鉴赏修复\备份_改前\x_ui_psv_replay_bg.png`（**改前 pristine**）
  出发计算（不是「在现图上再抹一次」）⇒ 重复运行逐字节相同；备份缺失即报错退出。

用法：python 工具\psv_fix_replay_bg.py [--variant keepframe]
"""
import hashlib
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                     # noqa: E402
from PIL import Image                                  # noqa: E402

UI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # <UI组>
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
WORK = os.path.join(UI, "_工作", "ISSUE-20260926-06_D鉴赏修复")
PRISTINE = os.path.join(WORK, "备份_改前", "x_ui_psv_replay_bg.png")
PLATE = os.path.join(ASSETS, "x_ui_psv_gal_shell.png")                 # 干净底版（ALBUM 屏区）
TARGET = os.path.join(ASSETS, "x_ui_psv_replay_bg.png")
EV = os.path.join(WORK, "_证据", "底图对照")

# 4 个槽的掩码（含外框线与抗锯齿，±4px 余量）；(x0, y0, x1, y1)，x1/y1 不含
MASK_SLOTS = [(84, 212, 635, 528),      # 槽 A（上排左，= 我方 rp.preview 上半）
              (684, 212, 1235, 528),    # 槽 B（上排中）
              (1283, 212, 1835, 528),   # 槽 C（上排右）
              (83, 603, 635, 921)]      # 槽 D（下排左，= 我方 rp.preview 下半）
FEATHER = 3                             # 掩码外沿羽化（px）：把底版与原图的 1 级噪声差抹平

# 「保留左预览板外框」B 路（备选；`--variant keepframe`）：外框 = 槽 A 上沿 + 左右沿 + 槽 D 下沿
FRAME_BANDS = [(86, 213, 634, 219),     # 板外框 · 上沿（槽 A 上框线 y214..217）
               (86, 213, 93, 520),      # 板外框 · 左沿上段（x86..91）
               (86, 611, 93, 919),      # 板外框 · 左沿下段（x86..91）—— 断开处即槽 A 下框线/槽 D 上框线
               (627, 213, 634, 520),    # 板外框 · 右沿上段
               (627, 611, 634, 919),    # 板外框 · 右沿下段
               (86, 913, 634, 919)]     # 板外框 · 下沿（槽 D 下框线 y914..917）


def alpha_map(w, h, masks, feather):
    """掩码权重：掩码内 = 1，掩码外 FEATHER px 内线性淡出。"""
    a = np.zeros((h, w), np.float32)
    for (x0, y0, x1, y1) in masks:
        a[y0:y1, x0:x1] = 1.0
    if feather > 0:
        for _ in range(feather):
            p = np.pad(a, 1, mode="edge")
            a = np.maximum(a, np.maximum.reduce([p[:-2, 1:-1], p[2:, 1:-1],
                                                 p[1:-1, :-2], p[1:-1, 2:]]) - 1.0 / feather)
    return np.clip(a, 0, 1)


def main(variant_keepframe=False):
    for p in (PRISTINE, PLATE):
        assert os.path.exists(p), "缺件（不可静默按现图猜）：" + p
    old = Image.open(PRISTINE).convert("RGBA")
    plate = Image.open(PLATE).convert("RGBA")
    assert old.size == plate.size == (1920, 1080), (old.size, plate.size)
    nov = np.asarray(old).astype(np.float32)
    npl = np.asarray(plate).astype(np.float32)

    # ── 自证 1：两件在槽区之外同画（对齐证明）──────────────────────────
    band = (slice(530, 600), slice(60, 1300))
    d_band = np.abs(nov[band][..., :3] - npl[band][..., :3]).mean()
    print("对齐自证：槽间干净带 (y530..600, x60..1300) 平均 |Δ| = %.2f（阈值 <3）" % d_band)
    assert d_band < 3.0, "两件底画未对齐，不得据此还原"

    masks = list(MASK_SLOTS)
    if variant_keepframe:
        # 外框带从掩码里减去（保留外框线）
        inner = []
        for (x0, y0, x1, y1) in MASK_SLOTS:
            inner.append((x0, y0, x1, y1))
        a = alpha_map(1920, 1080, inner, FEATHER)
        for (x0, y0, x1, y1) in FRAME_BANDS:
            a[y0:y1, x0:x1] = 0.0
        for _ in range(FEATHER):                       # 反向羽化，避免外框边出现 1px 折角
            p = np.pad(a, 1, mode="edge")
            a = np.minimum(a, np.maximum.reduce([p[:-2, 1:-1], p[2:, 1:-1],
                                                 p[1:-1, :-2], p[1:-1, 2:]]) + 1.0 / FEATHER)
        alpha = np.clip(a, 0, 1)
    else:
        alpha = alpha_map(1920, 1080, masks, FEATHER)

    out = nov * (1 - alpha[..., None]) + npl * alpha[..., None]
    res = np.clip(out + 0.5, 0, 255).astype(np.uint8)

    # ── 自证 2：掩码外逐像素 byte 相同 ────────────────────────────────
    hard = alpha > 0
    diff = np.abs(res.astype(int) - np.asarray(old).astype(int)).sum(axis=2)
    outside = diff[~hard]
    assert outside.max() == 0, "掩码外被改动：max|Δ|=%d" % outside.max()
    print("掩码外逐像素不变 ✓（改动像素 %d / %d）" % (int(hard.sum()), hard.size))

    # ── 自证 3：无残线、无亮度台阶 ────────────────────────────────────
    lum = res.mean(axis=2)
    src_lum = np.asarray(old).mean(axis=2)

    def line_peak(seg, axis):
        """沿 axis 的行/列中位数剖面：返回最大的「相对邻域凸起」（px 亮度）。
        残线 = 槽框线（峰值 248 而底画 150..215）⇒ 该行/列中位数会凸起数十级。"""
        prof = np.array([np.median(s) for s in (seg if axis == 0 else seg.T)])
        n = len(prof)
        peaks = []
        for i in range(n):
            lo, hi = max(0, i - 8), min(n, i + 9)
            nb = np.concatenate([prof[lo:max(0, i - 3)], prof[min(n, i + 4):hi]])
            if len(nb):
                peaks.append(abs(prof[i] - nb.mean()))
        return max(peaks) if peaks else 0.0

    #   ★ B 路（保留外框）时，外框线是**有意保留**的，故残线检查退到内区（inset 14px）做
    inset = 14 if variant_keepframe else 8
    for k, (x0, y0, x1, y1) in enumerate(MASK_SLOTS, 1):
        seg = lum[y0 + inset:y1 - inset, x0 + inset:x1 - inset]
        seg0 = src_lum[y0 + inset:y1 - inset, x0 + inset:x1 - inset]
        ph, pv = line_peak(seg, 0), line_peak(seg, 1)
        ph0 = line_peak(seg0, 0)
        print("  槽 %d 残留「横线凸起」= %.1f、纵线凸起 = %.1f（改前横线凸起 %.1f；阈值 <12）"
              % (k, ph, pv, ph0))
        assert ph < 12 and pv < 12, "槽 %d 仍有残线" % k
    # 台阶：掩码上下沿跨边框差（应在噪声级）
    for k, (x0, y0, x1, y1) in enumerate(MASK_SLOTS, 1):
        if variant_keepframe:
            continue          # B 路保留外框 ⇒ 跨框必然有台阶，不做该检查
        edge = abs(np.median(lum[y0 + 1, x0 + 10:x1 - 10]) - np.median(lum[y0 - 1, x0 + 10:x1 - 10]))
        edge2 = abs(np.median(lum[y1 - 2, x0 + 10:x1 - 10]) - np.median(lum[y1 + 1, x0 + 10:x1 - 10]))
        print("  槽 %d 跨上边框差 Δ = %.2f、跨下边框差 Δ = %.2f（阈值 <6）" % (k, edge, edge2))
        assert edge < 6 and edge2 < 6, "槽 %d 有亮度台阶" % k

    if variant_keepframe:
        for (x0, y0, x1, y1) in FRAME_BANDS:
            seg = lum[y0:y1, x0:x1]
            assert (seg > 235).any(), "外框带 %s 内未见框线" % ((x0, y0, x1, y1),)
        print("B 路：左预览板外框 4 条边带保留 ✓")

    os.makedirs(EV, exist_ok=True)
    tag = "_keepframe" if variant_keepframe else ""
    out_png = os.path.join(EV, "x_ui_psv_replay_bg_FIXED%s.png" % tag)
    Image.fromarray(res, "RGBA").save(out_png, optimize=True)
    if not variant_keepframe:
        old_bytes = open(TARGET, "rb").read()
        Image.fromarray(res, "RGBA").save(TARGET, optimize=True)
        new_bytes = open(TARGET, "rb").read()
        print("落盘 %s  %d 字节（改前 %d）" % (os.path.relpath(TARGET, UI), len(new_bytes), len(old_bytes)))
        print("md5 = %s" % hashlib.md5(new_bytes).hexdigest())
    print("对照图：%s" % os.path.relpath(out_png, UI))
    return 0


if __name__ == "__main__":
    sys.exit(main(variant_keepframe="--variant" in sys.argv and "keepframe" in sys.argv))

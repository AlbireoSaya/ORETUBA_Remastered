# -*- coding: utf-8 -*-
r"""M39 · 遮罩**像素自证**：目标导向的差值统计（证明「真生效 + 底深上浅的渐变」而非硬边矩形）

■ 三组 A/B（**只差遮罩强度，其余一切相同**）
  A. HTML 端：夹具 `?opa=0`（无遮罩）vs `?opa=100 / 150 / 200`  —— 同一夹具页、同一虚拟时钟
  B. 引擎端：`M39_引擎导出_dialog_遮罩150.png`（本次巡演，含遮罩）
     vs `_工作\ISSUE-20260923-01_M38_证据\M38_AB_新实现_shot_03_dialog.png`（M38 同屏同帧、无遮罩元素）
     —— 两侧同一份 dialog 数据，唯一差别 = 本次新增的 `dlg.mask_bottom`

■ 预测量（唯一模型，只有这一个自由量）
    Δ_pred(y) = 该像素质点亮度均值 × α_eff/255
    α_eff(y) = round(255 × ((y−y0)/(h−1))^1.6) × opacity/255
  即「黑遮罩按 alpha 合成」的标准公式。**实测/预测 ≈ 1** 才说明生效的正是本素材的本剖面。

■ 断言（三条，逐条给原始数字）
  ① **差异只在 y ≥ y0**（=遮罩元素上沿）：y < y0 区域 Δ>0 的像素数必须为 0。
  ② **越靠下差异越大（底深上浅，不是硬边矩形）**：把 y0..画面下沿分成 10px 带，逐带算
     「画面内容像素」的平均 |Δ|，必须**单调不减**（允许 0.5/255 量化噪声）。
     ★ 口径要点：**统计时排除 `dlg.name` / `dlg.text` 的矩形** —— 它们在 z 上**高于**遮罩
       （z=22 > 15），是**刻意不被压**的；把它们算进来会污染剖面（实测文字带内会有一次下凹，
       那不是遮罩失效，恰恰是「文字未被压」的正面证据，见断言③）。
       y ≥ 990 处 letterbox（4:3 源下 1200×900 居中 ⇒ 画面下沿 990）是纯黑，压黑不变 ⇒
       该段「内容像素」为 0，不参与单调性判定（物理上正确）。
  ③ **文字不受遮罩影响**（遮罩在文字之下）：文字带内，把「文字墨迹」（无遮罩亮度 > 200）
     与「同带画面背景」（亮度 8..200）的 |Δ| 分开统计 —— 墨迹应≈0，背景应≈预测值。

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_mask_diff_proof.py
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
M38 = os.path.join(UI, "_工作", "ISSUE-20260923-01_M38_证据")
GAMMA = 1.6
LINES = []
RECTS = {}          # id -> (x0,y0,x1,y1)
PIC_BOX = (0, 0, 0, 0)
FULL = None         # opa=255 满强度帧（HTML 端专用；引擎端无此对照，为 None）
Y0, H = 680, 400


def say(s=""):
    print(s)
    LINES.append(s)


def material_alpha(y):
    t = min(1.0, max(0.0, (y - Y0) / float(H - 1)))
    return 255.0 * (t ** GAMMA)


def load(p):
    """读图并**归一到画布 1:1**（1920×1080）——无头截图为「窗口尺寸」故可能更大，
    画布位于其左上原点（取景由 m39_mask_tiers.py 的 DOM 探针断言过）。"""
    im = Image.open(p)
    im.load()
    if im.size != (1920, 1080):
        im = im.crop((0, 0, 1920, 1080))
    return np.asarray(im.convert("RGB"), dtype=np.float64)


def rect_mask(shape, ids):
    """ids 所列矩形并集（用于统计时排除「在遮罩之上」的元素）"""
    m = np.zeros(shape, dtype=bool)
    for i in ids:
        x0, y0, x1, y1 = RECTS[i]
        m[max(0, y0):min(shape[0], y1), max(0, x0):min(shape[1], x1)] = True
    return m


def fill(shape, box):
    m = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = box
    m[max(0, y0):min(shape[0], y1), max(0, x0):min(shape[1], x1)] = True
    return m


def diff_block(name, A, B, opa, excl):
    d = np.abs(B - A).mean(axis=2)
    lumA = A.mean(axis=2)
    is_content = ((lumA > 8) & fill(A.shape[:2], PIC_BOX)
                  & (~rect_mask(A.shape[:2], excl_ids)))
    say("\n  [② 10px 带剖面] 「画面内容像素」= 亮度 > 8 **且落在画面层 dlg.content 实绘矩形 "
        "%s 内** **且不在 %s 矩形内**" % (PIC_BOX, "+".join(sorted(excl_ids))))
    say("     （画面矩形之外只有 letterbox 纯黑与页面外壳：压黑不变 ⇒ Δ=0，例如 y≥%d 的"
        "整行 Δ 恒为 0 —— 这是物理正确，不是遮罩失效）" % PIC_BOX[3])
    say("\n" + "-" * 78)
    say("■ %s（遮罩 opacity=%d）" % (name, opa))
    say("-" * 78)

    n_up = int((d[:Y0] > 0).sum())
    say("  [① y < %d 无差异] Δ>0 像素数 = %d（期望 0）｜ 该区最大 Δ = %.3f"
        % (Y0, n_up, float(d[:Y0].max())))
    dd = d.copy()
    dd[:Y0] = 0
    rws = np.where(dd.max(axis=1) > 0)[0]
    say("     Δ>0 的纵向范围 = y %d .. %d"
        % (int(rws.min()) if rws.size else -1, int(rws.max()) if rws.size else -1))

    say("\n  [② 10px 带剖面] 只统计「画面内容像素」= 亮度>8 **且不在 %s 矩形内**"
        % "+".join(sorted(excl_ids)))
    say("     %-14s %-10s %-13s %-13s %-11s" % ("画布 y 带", "内容像素", "实测平均|Δ|",
                                                  "预测平均|Δ|", "实测/预测"))
    prev, mono_ok, ratios, nband = -1.0, True, [], 0
    for yb in range(Y0, 1080, 10):
        y1 = min(yb + 10, 1080)
        sel = is_content[yb:y1]
        n = int(sel.sum())
        if n == 0:
            say("     y %4d..%-4d %-10d %-13s %-13s %-11s"
                % (yb, y1, 0, "（无内容：letterbox 纯黑）", "-", "-"))
            continue
        meas = float(d[yb:y1][sel].mean())
        lm = float(lumA[yb:y1][sel].mean())
        # Δ = 亮度 × α_eff/255（α_eff = 素材 α × opacity/255；标准黑遮罩 alpha 合成）
        a_eff = material_alpha((yb + y1 - 1) / 2.0) * opa / 255.0
        pred = lm * a_eff / 255.0
        r = meas / pred if pred > 1e-6 else float("nan")
        if pred > 1.0:                      # 预测 <1 时量化噪声占主导，不入单调性判定
            nband += 1
            ratios.append(r)
            if meas + 0.5 < prev:
                mono_ok = False
            prev = meas
        say("     y %4d..%-4d %-10d %-13.3f %-13.3f %-11.3f" % (yb, y1, n, meas, pred, r))
    say("     ⇒ 单调不减（排除预测<1 的量化带）= %s ｜ 实测/预测 中位数 = %.3f（期望 ≈1.0）"
        " ｜ 参与判定 %d 带" % (mono_ok, float(np.median(ratios)), nband))

    say("\n  [③ 文字不受遮罩影响]（遮罩在文字**之下**）—— 满强度 opa=255 vs opa=0")
    say("     判据（同 y、同 α_eff 的**对照配对**）：文字矩形 x246..1470 与「同排画面但矩形外」")
    say("           的窄带 x1470..1560（纯画面，α_eff 同值）逐像素比。只取亮像素（lum>200）：")
    say("           纯画面带**全被压**（Δ 很大）；文字矩形内应多出一批「Δ≈0」的像素 = 白墨本身。")
    say("           ⇒ 判据成立 = 画面带未压占比 ≈0 且 文字矩形未压占比明显更高。")
    if FULL is None:
        say("     （本组无满强度对照，跳过；z 序由数据断言：遮罩 z=%s < 文字 z=%s/%s）"
            % (m["z"], el["dlg.name"]["z"], el["dlg.text"]["z"]))
        return (n_up == 0) and mono_ok, ratios
    F = FULL
    dF = np.abs(F - A).mean(axis=2)
    rows = np.zeros(A.shape[:2], dtype=bool)
    rows[RECTS["dlg.name"][1]:RECTS["dlg.text"][3], :] = True
    inrect = rect_mask(A.shape[:2], ["dlg.name", "dlg.text"])
    bgstrip = fill(A.shape[:2], PIC_BOX) & rows & (~inrect)
    say("     行范围 y%d..%d（名字顶..正文底）｜ 该范围 α_eff 满强度 = %.0f..%.0f"
        % (RECTS["dlg.name"][1], RECTS["dlg.text"][3] - 1,
           material_alpha(RECTS["dlg.name"][1]), material_alpha(RECTS["dlg.text"][3] - 1)))
    say("     %-30s %-9s %-12s %-13s %-13s"
        % ("区域（亮像素 lum>200）", "亮像素数", "未压|Δ|<2 占比", "未压者最亮值", "全体平均|Δ|"))
    shares = {}
    max_untouched = 0.0
    for zn, zm in [("文字矩形（名字 ∪ 正文）", inrect & rows),
                   ("同排纯画面带（矩形外）", bgstrip)]:
        sel = zm & (lumA > 200)
        n = int(sel.sum())
        if n == 0:
            say("     %-30s %-9d (无亮像素)" % (zn, 0))
            continue
        dp, lp = dF[sel], lumA[sel]
        un = dp < 2.0
        shares[zn] = 100.0 * float(un.mean())
        if un.any() and zn.startswith("文字"):
            max_untouched = float(lp[un].max())
        say("     %-30s %-9d %-12.2f%% %-13.1f %-13.1f"
            % (zn, n, shares[zn], float(lp[un].max()) if un.any() else 0.0, float(dp.mean())))
    a = shares.get("文字矩形（名字 ∪ 正文）", 0.0)
    b = shares.get("同排纯画面带（矩形外）", 100.0)
    maxun = max_untouched
    # 判据：同排纯画面带「一个未被压的亮像素都没有」（b ≈ 0）；文字矩形内却有一批，
    #       且其中含最亮档（≥250）的像素 ⇒ 那些就是没被压的白墨 ⇒ 文字在遮罩之上。
    #       （占比 a 随该行字数而变，故阈值不写死百分比，只要求 a > 0 且 b ≈ 0。）
    ink_ok = (b < 0.1) and (a > 0.0) and (maxun >= 250.0)
    say("     ⇒ 画面带未压 %.2f%%（应 ≈0）｜ 文字矩形未压 %.2f%%（应 >0）｜ 未压者最亮 %.0f"
        "（应 ≥250）⇒ %s" % (b, a, maxun, ink_ok))

    say("\n  [④ 逐行原始值] 整行 1920px 平均 |Δ| ／ 画面内容像素平均 |Δ|")
    for y in [Y0, 700, 750, 800, 850, 900, 950, 985, 1020, 1050]:
        y = min(y, d.shape[0] - 1)
        sel = is_content[y]
        say("     y=%4d  整行=%7.3f   内容像素(%4d)=%7.3f   该行 α_eff=%6.1f"
            % (y, float(d[y].mean()), int(sel.sum()),
               float(d[y][sel].mean()) if sel.any() else 0.0,
               material_alpha(y) * opa / 255.0))
    return (n_up == 0) and mono_ok and ink_ok, ratios


def main():
    global Y0, H, RECTS, excl_ids, PIC_BOX, FULL
    # 画面层实绘矩形由 M39 夹具的 DOM 探针写盘（M39_夹具取景自证.json），此处读回 ——
    # 双方都读同一份数据推导出来的框，脚本里不写死任何坐标。
    probe = json.load(io.open(os.path.join(EVID, "M39_夹具取景自证.json"), encoding="utf-8"))
    probe = probe.get("基本", probe)          # 兼容单层结构（旧版只写扁平 dict）
    PIC_BOX = tuple(int(v) for v in probe["content-rect"].split(","))
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    m = el["dlg.mask_bottom"]
    Y0, H = int(m["y"]), int(m["h"])
    for k in ("dlg.name", "dlg.text", "dlg.choices", "dlg.hint", "dlg.mode_tag"):
        e = el.get(k)
        if not e or "y" not in e or int(e.get("z", 0)) <= int(m["z"]):
            continue
        RECTS[k] = (int(e["x"]), int(e["y"]), int(e["x"]) + int(e["w"]),
                    int(e["y"]) + int(e["h"]))
    # 只排「会被文字墨迹污染剖面」的两件：名字与正文（选择肢默认隐藏、hint/mode_tag 在画面上带外）
    excl_ids = ["dlg.name", "dlg.text"]
    RECTS = {k: v for k, v in RECTS.items() if k in excl_ids}

    say("=" * 78)
    say("M39 遮罩像素自证（差值统计；全部几何读自 layout/screens/10_dialog.json）")
    say("=" * 78)
    say("  遮罩：x=%s y=%s w=%s h=%s opacity=%s（z=%s）｜ 剖面 a=255*t^%.1f ｜ 素材最大 255"
        % (m["x"], m["y"], m["w"], m["h"], m["opacity"], m["z"], GAMMA))
    say("  画面层 dlg.content 实绘矩形 = %s（取自夹具 DOM 探针，与截图同一次渲染）" % (PIC_BOX,))
    for k, v in sorted(RECTS.items()):
        say("  排除矩形 %-10s x%d..%d y%d..%d（z=%s > 遮罩 z=%s）"
            % (k, v[0], v[2], v[1], v[3], el[k]["z"], m["z"]))

    okA = True
    A0 = load(os.path.join(EVID, "tier_opa000.png"))
    FULL = load(os.path.join(EVID, "tier_opa255.png"))
    for opa, nm in [(100, "HTML 端 · 弱档"), (150, "HTML 端 · 默认档"), (200, "HTML 端 · 强档")]:
        o, _ = diff_block("%s（同夹具页 opa=0 vs opa=%d）" % (nm, opa), A0,
                          load(os.path.join(EVID, "tier_opa%03d.png" % opa)), opa, None)
        okA &= o

    say("\n" + "=" * 78)
    say("■ 引擎端 A/B（两份都是**引擎自己离屏导出**的 dialog 屏，非窗口抓屏）")
    say("=" * 78)
    say("  A = M38_AB_新实现_shot_03_dialog.png（M38 同屏同帧，数据中**无** dlg.mask_bottom）")
    say("  B = M39_引擎导出_dialog_遮罩150.png（本次巡演，含 dlg.mask_bottom opacity=150）")
    okB, _ = diff_block("引擎端 · 默认档 150", load(os.path.join(M38, "M38_AB_新实现_shot_03_dialog.png")),
                        load(os.path.join(EVID, "M39_引擎导出_dialog_遮罩150.png")), 150, None)

    say("\n" + "=" * 78)
    say("总判定：HTML 端（三档）%s ｜ 引擎端 %s" % ("OK" if okA else "NG", "OK" if okB else "NG"))
    say("=" * 78)
    io.open(os.path.join(EVID, "M39_遮罩像素自证_原始输出.txt"), "w",
            encoding="utf-8").write("\n".join(LINES) + "\n")
    return 0 if (okA and okB) else 1


if __name__ == "__main__":
    sys.exit(main())

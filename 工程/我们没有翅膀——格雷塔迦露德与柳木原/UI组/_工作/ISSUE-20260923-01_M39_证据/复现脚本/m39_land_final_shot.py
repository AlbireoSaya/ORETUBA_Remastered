# -*- coding: utf-8 -*-
r"""M39 落地 · 最终引擎实拍取图 + 2× 放大裁切 + 引擎侧强度自证

产物（EVID）：
  `M39_引擎导出_dialog_最终_350px90.png`        —— 本机巡演 dialog 屏的**引擎离屏导出**原图（1920×1080）
  `M39_引擎放大裁切_最终_名字+全文_2x.png`       —— 含**角色名 + 全文 + 画面亮部**的 2× 裁切
  `M39_落地_引擎终稿自证_原始输出.txt`

自证（不沿用早前结论，全部现算）：
  ① 反推 α_eff(每25px) vs 解析预测 `255·t^1.0·opacity/255`（opacity=230、y0=730、h=350）
     —— 基准取 `_工作\ISSUE-20260923-01_M38_证据\M38_AB_新实现_shot_03_dialog.png`（同屏同帧、无遮罩元素）
  ② 名字字形带（实测 x465..538 y749..788）与台词首行带（数据框 y806..856）的平均 |Δ| —— 两处都应 >0
  ③ 遮罩上沿以上（y<730）必须无差异（Δ≡0）
"""
import io
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
M38 = os.path.join(UI, "_工作", "ISSUE-20260923-01_M38_证据")
SD = ("E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run/runtime/savedata")
GAMMA = 1.0
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


def main():
    sc = json.load(io.open(os.path.join(UI, "layout", "screens", "10_dialog.json"),
                           encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    m = el["dlg.mask_bottom"]
    y0, h, opa = int(m["y"]), int(m["h"]), int(m["opacity"])
    tx, nm = el["dlg.text"], el["dlg.name"]
    tb = (int(tx["x"]), int(tx["y"]), int(tx["x"]) + int(tx["w"]), int(tx["y"]) + int(tx["h"]))
    nb = (int(nm["x"]), int(nm["y"]), int(nm["x"]) + int(nm["w"]), int(nm["y"]) + int(nm["h"]))

    say("=" * 96)
    say("M39 落地 · 引擎终稿取图与自证")
    say("=" * 96)
    say("  数据侧（读的就是已落地的 10_dialog.json）：asset=%s x=%s y=%s w=%s h=%s opacity=%s z=%s"
        % (m["asset"], m["x"], m["y"], m["w"], m["h"], m["opacity"], m["z"]))

    src = os.path.join(SD, "shot_03_dialog.png")
    assert os.path.exists(src), "巡演未产出 shot_03_dialog.png（先跑 run_autotour.bat）"
    dst = os.path.join(EVID, "M39_引擎导出_dialog_最终_350px90.png")
    shutil.copyfile(src, dst)
    say("  [OK] 引擎离屏导出已取：M39_引擎导出_dialog_最终_350px90.png（%d 字节）"
        % os.path.getsize(dst))

    # 2× 放大裁切：含名字 + 全文 + 画面亮部（裁 x150..1550 / y700..1030；1:1 数据见 layout）
    CROP, Z = (150, 700, 1550, 1030), 2
    im = Image.open(dst).convert("RGB")
    c = im.crop(CROP)
    out2 = os.path.join(EVID, "M39_引擎放大裁切_最终_名字+全文_2x.png")
    c.resize((c.width * Z, c.height * Z), Image.NEAREST).save(out2)
    say("  [OK] 2× 放大裁切：M39_引擎放大裁切_最终_名字+全文_2x.png（画布区域 %s ×%d → %dx%d）"
        % (CROP, Z, c.width * Z, c.height * Z))
    say("       裁切是否含 名字框(x%d..%d y%d..%d) 与 正文框(x%d..%d y%d..%d)：%s"
        % (nb[0], nb[2], nb[1], nb[3], tb[0], tb[2], tb[1], tb[3],
           CROP[0] <= nb[0] and nb[2] <= CROP[2] and CROP[1] <= nb[1] and nb[3] <= CROP[3]
           and CROP[0] <= tb[0] and tb[2] <= CROP[2] and tb[1] >= CROP[1] and tb[3] <= CROP[3]))

    # ---- 自证 ----
    base_p = os.path.join(M38, "M38_AB_新实现_shot_03_dialog.png")
    say("\n■ ① 反推 α_eff vs 解析预测（基准 = M38 同屏同帧、无遮罩元素）")
    A, B = load(base_p), load(dst)
    d = np.abs(B - A).mean(axis=2)
    lum = A.mean(axis=2)
    ink = np.zeros(A.shape[:2], dtype=bool)
    ink[tb[1]:tb[3], tb[0]:tb[2]] = lum[tb[1]:tb[3], tb[0]:tb[2]] > 200
    sel_all = np.zeros(A.shape[:2], dtype=bool)
    sel_all[nb[1]:nb[3], nb[0]:nb[2]] = True
    sel_all[tb[1]:tb[3], tb[0]:tb[2]] = True
    content = (lum > 8) & (~sel_all)
    say("  %-9s %-14s %-14s %-13s %-9s" % ("画布 y", "平均|Δ|", "反推 α_eff", "预测 α_eff", "差"))
    worst = 0.0
    for y in (700, 730, 750, 780, 830, 880, 950, 990):
        s = content[y]
        if s.sum() == 0:
            say("  %-9d （无画面内容：letterbox 纯黑，压黑不变）" % y)
            continue
        meas = float(d[y][s].mean())
        got = meas / max(1e-9, float(lum[y][s].mean())) * 255.0
        prd = (0.0 if y < y0 else 255.0 * (((y - y0) / float(h - 1)) ** GAMMA) * opa / 255.0)
        if prd > 1.0:
            worst = max(worst, abs(got - prd))
        say("  %-9d %-14.2f %-14.1f %-13.1f %-9s"
            % (y, meas, got, prd, ("%+.1f" % (got - prd)) if prd > 0 else "（罩外）"))
    say("  ⇒ 最大偏差 = %.1f（α 单位，满量程 255）" % worst)

    say("\n■ ② 两处文字是否都被压到（引擎侧）")
    dn = float(d[nb[1]:nb[3], nb[0]:nb[2]].mean())
    dt = float(d[tb[1]:tb[1] + 50, tb[0]:tb[2]].mean())
    say("  名字框（x%d..%d y%d..%d）平均|Δ| = %.3f" % (nb[0], nb[2], nb[1], nb[3], dn))
    say("  台词首行（数据框前 50px：y%d..%d）平均|Δ| = %.3f" % (tb[1], tb[1] + 50, dt))
    say("  ⇒ 两处均 >0 = %s（250px 那一版这里名字是 0.000）" % (dn > 0.5 and dt > 0.5))

    say("\n■ ③ 遮罩上沿以上必须无差异")
    n_up = int((d[:y0] > 0).sum())
    say("  y < %d 的 Δ>0 像素数 = %d（期望 0）｜ 该区最大 Δ = %.3f" % (y0, n_up, float(d[:y0].max())))
    below = d[y0:]
    rws = np.where(below.max(axis=1) > 0)[0]
    say("  Δ>0 的纵向范围 = y %d .. %d"
        % (y0 + int(rws.min()) if rws.size else -1, y0 + int(rws.max()) if rws.size else -1))

    ok = (worst < 6.0) and (n_up == 0) and dn > 0.5 and dt > 0.5
    say("\n  总判定：%s" % ("**通过**（落地的 350px/线性/90% 在引擎侧逐项成立）" if ok
                          else "**需核对**"))
    io.open(os.path.join(EVID, "M39_落地_引擎终稿自证_原始输出.txt"), "w",
            encoding="utf-8").write("\n".join(LINES) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

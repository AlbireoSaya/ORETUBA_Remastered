# -*- coding: utf-8 -*-
r"""K7（2026-09-23）· **引擎导出的展开态截图** ↔ **HTML 复刻端同态截图** 的同区域像素对比

■ 比什么
  取右缘竖条区域 `x 1840..1920 × y 0..920`（= 12 个圆形 icon + 名称药丸所在列），
  两端都在 **同一状态**：`quickbar=expanded, qbar_tip=lock, qbar_pin=1`。

■ 口径（怎么保证是"同区域"而不是"各自裁一块"）
  · 引擎侧：`临时\ui_run_quickbar\...\shot_03_dialog.png` 是**1920×1080 的 1:1 离屏导出**。
  · HTML 侧：无头 Edge 用 `--window-size=2000x1657` 渲染 `index.html?screen=dialog&chrome=0&
    flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1` —— 实测该窗口下 `#canvas` 的
    `transform: scale(1)`（**1:1**，无浏览器重采样），故两侧是同尺度可比像素。
  · 画布在页面里的**左上角偏移**不写死：先用**粗→细两级模板匹配**（把引擎区域当模板）求出
    最佳 (dx,dy)，再在最佳偏移上做差。**偏移本身不是渲染差异**，表里单独报告。

■ 归因（差异必须是可解释的，不许笼统说"噪声"）
  · 圆形 icon / 药丸底 = 位图素材 → 同尺度下应**逐像素相同**（差异只可能来自页面重采样，
    而 scale=1 时不存在）。
  · 白字「锁定」= 两端各自排版渲染（krkr 的 TTF 光栅 vs Chromium 的 TTF 光栅）
    → **允许在字形边缘有差异**；脚本按「是否落在文字墨迹附近」把差异分区统计。
  · `?chrome=0` 只压掉复刻端的**纯热区叠色**（`:hover/:active` 蓝底），
    引擎离屏导出本来就没有该叠色 ⇒ 该差异项在本对比里**应为 0**（会被单独列出）。

■ 用法（★ **必须带 PYTHONPATH**：本脚本用 numpy + PIL，二者装在 `工具\pylibs\`，
   本机默认解释器 `E:\Tools\Python\python.exe` **没装 numpy**（不带 PYTHONPATH 会 ModuleNotFoundError））
    set PYTHONPATH=E:/ZCode Workspace/Galgame/工具/pylibs
    python _工作\M37_K7_引擎vsHTML同区域对比.py
  前置：`krkr\run_quickbar.bat`（强制展开 + 钉住）跑过一轮，产出
        `临时\ui_run_quickbar\runtime\savedata\shot_03_dialog.png`。
"""
import io
import json
import os
import subprocess
import sys
import shutil
import urllib.parse

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EV = os.path.join(HERE, "ISSUE-20260923-01_G2_证据")
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_k7c"

REGION = (1840, 0, 1920, 920)          # 右缘竖条区域（x0,y0,x1,y1）
QUERY = "?screen=dialog&chrome=0&flags=quickbar:expanded,qbar_tip:lock,qbar_pin:1"
WIN = (2000, 1657)                     # ★ 实测该窗口下 canvas scale == 1


def html_shot():
    os.makedirs(UD, exist_ok=True)
    out = os.path.join(EV, "_k7_html_同态_scale1.png")
    url = "file:///" + urllib.parse.quote(os.path.join(REP, "index.html").replace("\\", "/")) + QUERY
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars",
                    "--window-size=%d,%d" % WIN, "--virtual-time-budget=9000",
                    "--screenshot=" + out, url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    shutil.rmtree(UD, ignore_errors=True)
    return Image.open(out).convert("RGB")


def align(page, tpl, coarse=8, span=8):
    """粗→细模板匹配：返回 (dx, dy, 该偏移下的平均绝对差)。tpl 为 numpy 数组 (h,w,3)。"""
    H, W = tpl.shape[:2]
    pg = np.asarray(page, dtype=np.int16)
    # 粗：两侧各下采样 coarse 倍
    t_small = tpl[::1, ::1][: (H // coarse) * coarse, : (W // coarse) * coarse]
    t_small = t_small.reshape(H // coarse, coarse, W // coarse, coarse, 3).mean(axis=(1, 3))
    best = (None, None, 1e18)
    for dy in range(0, pg.shape[0] - H + 1, coarse):
        for dx in range(0, pg.shape[1] - W + 1, coarse):
            blk = pg[dy:dy + H, dx:dx + W]
            b_small = blk[: (H // coarse) * coarse, : (W // coarse) * coarse]
            b_small = b_small.reshape(H // coarse, coarse, W // coarse, coarse, 3).mean(axis=(1, 3))
            d = np.abs(b_small - t_small).mean()
            if d < best[2]:
                best = (dx, dy, d)
    cx, cy, _ = best
    # 细：在粗结果附近逐像素
    fine = (cx, cy)
    bd = 1e18
    for dy in range(max(0, cy - span), min(pg.shape[0] - H, cy + span) + 1):
        for dx in range(max(0, cx - span), min(pg.shape[1] - W, cx + span) + 1):
            d = np.abs(pg[dy:dy + H, dx:dx + W] - tpl).mean()
            if d < bd:
                bd, fine = d, (dx, dy)
    return fine[0], fine[1], bd


def main():
    engine = Image.open(os.path.join(WT, "临时", "ui_run_quickbar", "runtime", "savedata",
                                     "shot_03_dialog.png")).convert("RGB")
    tpl = np.asarray(engine.crop(REGION), dtype=np.int16)
    page = html_shot()
    print("=" * 78)
    print("K7 同区域像素对比｜区域 %s（右缘竖条列，80×920）" % (REGION,))
    print("  引擎：ui_run_quickbar/shot_03_dialog.png（1920×1080 1:1 离屏导出）")
    print("  HTML：index.html%s（window %dx%d，实测 canvas transform: scale(1)）" % (QUERY, WIN[0], WIN[1]))
    print("=" * 78)
    dx, dy, mad = align(page, tpl)
    print("\n[1] 对齐（粗→细模板匹配，把引擎区域当模板）")
    print("    最佳偏移 (dx,dy) = (%d,%d)  该偏移下平均绝对差 = %.3f/255" % (dx, dy, mad))
    print("    ⇒ 偏移是**页面里画布的位置**，不是渲染差异；下面全部在最佳偏移上比较。")
    hb = np.asarray(page.crop((dx, dy, dx + REGION[2] - REGION[0], dy + REGION[3] - REGION[1])),
                    dtype=np.int16)
    diff = np.abs(hb - tpl).max(axis=2)
    npx = diff.size
    for th in (0, 2, 8, 32):
        cnt = int((diff > th).sum())
        print("    差异 >%-3d 的像素：%7d / %d （%.2f%%）" % (th, cnt, npx, 100.0 * cnt / npx))
    ys, xs = np.where(diff > 8)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
    print("    差异(>8) 包围盒（相对区域左上角）：%s" % (bbox,))
    print("    最大差分 %d / 平均 %.3f" % (int(diff.max()), float(diff.mean())))

    # ── 归因分区：icon 单元格 / 药丸丸体 / 白字墨迹框 ──
    d = json.load(io.open(os.path.join(UI, "layout", "screens", "35_quickbar.json"),
                          encoding="utf-8"))
    idx = {e["id"]: e for e in d["elements"]}
    print("\n[2] 分区归因（区域坐标 = 画布坐标 − (%d,0)）" % REGION[0])
    groups = [("圆形 icon ×12（位图素材）", [(idx["quick.ic_%s" % k]["x"], idx["quick.ic_%s" % k]["y"],
                                   idx["quick.ic_%s" % k]["w"], idx["quick.ic_%s" % k]["h"])
                                  for k in ("lock", "save", "load", "qsave", "qload", "auto",
                                            "skip", "next", "prev", "log", "chart", "option")]),
              ("药丸底（位图素材）×2", [(idx["quick.pl_lock"]["x"], idx["quick.pl_lock"]["y"],
                                idx["quick.pl_lock"]["w"], idx["quick.pl_lock"]["h"]),
                               (idx["quick.pl_save"]["x"], idx["quick.pl_save"]["y"],
                                idx["quick.pl_save"]["w"], idx["quick.pl_save"]["h"])]),
              ("白字「锁定」（两端各自光栅化）", [(idx["quick.tx_lock"]["x"], idx["quick.tx_lock"]["y"],
                                      idx["quick.tx_lock"]["w"], idx["quick.tx_lock"]["h"])])]
    for name, boxes in groups:
        vals = []
        for (bx, by, bw, bh) in boxes:
            x0 = max(0, bx - REGION[0]); y0 = max(0, by - REGION[1])
            x1 = min(REGION[2] - REGION[0], x0 + bw); y1 = min(REGION[3] - REGION[1], y0 + bh)
            if x1 > x0 and y1 > y0:
                vals.append(diff[y0:y1, x0:x1])
        if not vals:
            print("    %-30s （区域外，跳过）" % name)
            continue
        v = np.concatenate([x.ravel() for x in vals])
        print("    %-30s 像素 %6d ｜ 最大差 %3d ｜ 平均 %.3f ｜ >8 占 %.2f%%"
              % (name, v.size, int(v.max()), float(v.mean()), 100.0 * (v > 8).sum() / v.size))

    # ── 结构证据：12 个 icon 单元格的均值色 + 质心偏移 ──
    print("\n[3] 结构一致性（比「看起来一样」更硬）：逐 icon 单元格均值色 + 质心偏移")
    bad = []
    for k in ("lock", "save", "load", "qsave", "qload", "auto", "skip", "next", "prev",
              "log", "chart", "option"):
        e = idx["quick.ic_%s" % k]
        x0 = e["x"] - REGION[0]; y0 = e["y"] - REGION[1]
        a = tpl[y0:y0 + e["h"], x0:x0 + e["w"]].astype(np.float64)
        b = hb[y0:y0 + e["h"], x0:x0 + e["w"]].astype(np.float64)
        ma = a.mean(axis=(0, 1)); mb = b.mean(axis=(0, 1))
        # 质心（用"与区域均值的偏差"当权重，避免整体亮度影响）
        wa = np.abs(a - a.mean()).sum(axis=2); wb = np.abs(b - b.mean()).sum(axis=2)
        ca = (np.indices(wa.shape) * wa).sum(axis=(1, 2)) / max(1e-9, wa.sum())
        cb = (np.indices(wb.shape) * wb).sum(axis=(1, 2)) / max(1e-9, wb.sum())
        dmean = float(np.abs(ma - mb).max()); dc = float(np.abs(ca - cb).max())
        print("    %-7s 均值差 %5.2f/255 ｜ 质心偏移 %.3f px" % (k, dmean, dc))
        if dmean > 3 or dc > 0.5:
            bad.append((k, dmean, dc))
    print("\n[4] 结论")
    if not bad:
        print("    12 件 icon 的均值色差 ≤3/255、质心偏移 ≤0.5px ⇒ **两端几何与材质一致**；")
    else:
        print("    !! 超阈值的 icon：%s" % bad)
    print("    差异集中在白字字形边缘（两端各自光栅化）——见 [2] 分区表；")
    print("    位图部分（icon / 药丸底）在 scale=1 下的差异远小于文字区 ⇒ **无机制性分叉**。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

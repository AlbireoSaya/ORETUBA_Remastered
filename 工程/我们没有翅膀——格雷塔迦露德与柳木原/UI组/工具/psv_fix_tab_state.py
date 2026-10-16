# -*- coding: utf-8 -*-
r"""psv_fix_tab_state.py —— 23/24 页签**选中态加强**：派生 `x_ui_psv_tab_sel.png`（幂等）

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）· **A 基础组修复轮**（本轮派单缺陷 ④-轻）。
对象：由既有件 `krkr\assets\ui\x_ui_tab_on.png`（181×70）**派生**新件
      `krkr\assets\ui\x_ui_psv_tab_sel.png`（181×70），供 23 存档 / 24 读档 的**当前页签**使用。

■ 为什么（缺陷原文）
  「页签选中态过弱：选中/未选中在带体 y50–75 仅差 ≤3/255 → 加强选中态（如加深底色或加描边），不动机制」。
  实测（带体内两态均不透明的 4246 px）：逐像素 |on−off| **中位数 4 / 均值 7.3 / p90 10**（≤3/255 量级吻合）
  ⇒ 玩家分不清哪个页签是当前页。

■ 做法（**不动机制**：不加 flag、不改 action、不改元素几何/文字/热区，只换一件「选中态」图）
  · **不修改共享件** `x_ui_tab_on/off.png`（`28_music.json` 也在用 ⇒ 改它会动别的屏，违反本工程纪律）；
  · 由 `x_ui_tab_on.png` **确定性重着色**派生本件：`RGB' = (R×0.55, G×0.68, B×0.92)`（四舍五入、逐通道钳位），
    **alpha 逐像素原样保留** ⇒ 形状/描边/柔光结构不变，只在「霜白→冰蓝」方向上加深（PSV 页面的主色即冰蓝），
    字体色 `@palette.node_locked`(#4A4A56) 在该底色上对比度 ≈4.6:1（可读）。
  · **同一件在 23/24 分别用在「当前页签」上**：23 存档 ⇒ tab_a(存档)=本件、tab_b(读档)=`x_ui_tab_off.png`；
    24 读档 ⇒ tab_a=`x_ui_tab_off.png`、tab_b(读档)=本件。（原状是两屏都 `tab_a=on` ⇒ 读档屏高亮的是
    **存档**页签——属同一缺陷的语义面，本轮一并订正；详见 `psv_fix_saveload.py`。）
  · 体积：新件仅 181×70，`RGB & 0xFC`（6bit）+ `optimize=True, compress_level=9`，**alpha 无损失**。

■ 自证（脚本输出）
  · 尺寸/模式与源件同形（181×70 RGBA）；alpha 与 `x_ui_tab_on.png` **逐像素相同**；
  · 「带体 y30..60（= 屏 y50..75 对应的源行）」内 `|sel − off|` 的 中位数/均值/p90 与改造前对比；
  · 重跑逐字节相同（幂等，确定性重着色 + 固定编码参数）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\psv_fix_tab_state.py
"""
from __future__ import annotations

import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
OUT = os.path.join(UI, "krkr", "assets", "ui")

SRC = "x_ui_tab_on.png"
DST = "x_ui_psv_tab_sel.png"
OFF = "x_ui_tab_off.png"
GAIN = (0.55, 0.68, 0.92)                # 选中态重着色增益（R/G/B）
BAND = (30, 60)                          # 带体行区间（源件内；= 屏 y50..75 对应的行）


def band_diff(a, b):
    """带体内两态均不透明像素的逐像素 |Δ| 统计（max 通道差）。"""
    ra, rb = a[BAND[0]:BAND[1]], b[BAND[0]:BAND[1]]
    both = (ra[:, :, 3] > 200) & (rb[:, :, 3] > 200)
    d = np.abs(ra[:, :, :3].astype(int) - rb[:, :, :3].astype(int)).max(axis=2)
    return int(both.sum()), float(np.median(d[both])), float(d[both].mean()), float(np.percentile(d[both], 90))


def main():
    p_src = os.path.join(OUT, SRC)
    p_off = os.path.join(OUT, OFF)
    p_dst = os.path.join(OUT, DST)
    src = Image.open(p_src).convert("RGBA")
    off = Image.open(p_off).convert("RGBA")
    assert src.size == off.size == (181, 70), "页签件尺寸异常：%s vs %s" % (src.size, off.size)
    a = np.array(src).astype(float)
    r, g, b, al = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    out = np.stack([np.clip(np.round(r * GAIN[0]), 0, 255),
                    np.clip(np.round(g * GAIN[1]), 0, 255),
                    np.clip(np.round(b * GAIN[2]), 0, 255), al], axis=2).astype(np.uint8)
    # 6bit（RGB）+ alpha 原样（派单纪律：alpha 不许有损）
    out[:, :, :3] &= 0xFC
    im = Image.fromarray(out, "RGBA")
    assert (np.array(im.getchannel("A")) == np.array(src.getchannel("A"))).all(), "alpha 被改动"
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    data = buf.getvalue()
    old = open(p_dst, "rb").read() if os.path.exists(p_dst) else None

    n0, m0, a0, p0 = band_diff(np.array(src), np.array(off))
    n1, m1, a1, p1 = band_diff(out, np.array(off))
    print("=" * 96)
    print("23/24 页签选中态加强：派生 %s ← %s（增益 %s，alpha 原样）" % (DST, SRC, GAIN))
    print("=" * 96)
    print("  尺寸/模式      ：%s RGBA（与 %s / %s 同形 ✓）" % (im.size, SRC, OFF))
    print("  带体 y%d..%d 两态差：改造前 中位 %.0f / 均值 %.1f / p90 %.0f（%d px）"
          % (BAND[0], BAND[1], m0, a0, p0, n0))
    print("  %-32s改造后 中位 %.0f / 均值 %.1f / p90 %.0f（%d px）"
          % ("", m1, a1, p1, n1))
    assert m1 > m0 * 3, "选中态对比未显著加强（中位 %.0f → %.0f）" % (m0, m1)
    print("  alpha 逐像素与 %s 相同 ✓；RGB 已按 & 0xFC 降 6bit ✓" % SRC)
    if old == data:
        print("  磁盘现状       ：**逐字节相同**（幂等，无需重写）md5 %s"
              % hashlib.md5(data).hexdigest()[:12])
    else:
        with open(p_dst, "wb") as f:
            f.write(data)
        print("  落盘           ：%s（%s，%d 字节）"
              % (DST, ("改" if old else "新"), len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

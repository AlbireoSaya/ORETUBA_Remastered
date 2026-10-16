# -*- coding: utf-8 -*-
r"""t4 · 落地后自证（对 `原形备份\` 逐件比对）

1) **改动的像素只落在粘贴矩形内**：矩形 (880, py)-(1904,1080) 之外，RGB 与 alpha 与改前**逐像素相同**；
2) **alpha 通道全程未变**（RGBA 件：页脚带 alpha 原 255，贴后仍 255；全图 alpha 逐像素相同）；
3) **粘贴矩形内的 RGB 与 B 裁片（&0xFC 后）逐像素相同**（证明没有额外处理/缩放）；
4) 打印逐件尺寸与体积，及 assets/ui 总体积。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI = os.path.join(BASE, "krkr", "assets", "ui")
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
BAK = os.path.join(WORK, "原形备份")
PICK = json.load(open(os.path.join(WORK, "footer_B_pick.json"), encoding="utf-8"))
PAIRS = [("x_ui_psv_save_bg.png", "otv_save_bg.png", 4), ("x_ui_psv_load_bg.png", "otv_load_bg.png", 4),
         ("x_ui_psv_quick_load_bg.png", "otv_quick_load_bg.png", 4),
         ("x_ui_psv_backlog_bg.png", "otv_bklog.png", 4),
         ("x_ui_psv_gal_shell.png", "otv_gm_bg1.png", 0), ("x_ui_psv_music_bg.png", "otv_mu_bg.png", 0),
         ("x_ui_psv_replay_bg.png", "otv_mv_bg.png", 0)]


def rgba(p):
    im = Image.open(p)
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    al = np.asarray(im.convert("RGBA"))[:, :, 3].astype(np.int16)
    return a, al, im.mode


ok = True
print("=" * 110)
print("落地后自证（对照 `_工作\\ISSUE-20260926-06_页脚双路\\原形备份\\`）")
print("=" * 110)
for tgt, src, off in PAIRS:
    new, al_new, mode = rgba(os.path.join(UI, tgt))
    old, al_old, _ = rgba(os.path.join(BAK, tgt))
    py = 940 - off
    rows = 1080 - py
    crop = np.asarray(Image.open(PICK[src]["path"]).convert("RGB")).astype(np.int16)[0:rows] & 0xFC
    # 1) 矩形外逐像素相同（RGB + alpha）
    outside_new = new.copy(); outside_old = old.copy()
    outside_new[py:, 880:1904] = 0; outside_old[py:, 880:1904] = 0
    same_out_rgb = bool((outside_new == outside_old).all())
    oa_new = al_new.copy(); oa_old = al_old.copy()
    oa_new[py:, 880:1904] = 0; oa_old[py:, 880:1904] = 0
    same_out_a = bool((oa_new == oa_old).all())
    # 2) alpha 全图未变 + 带内 alpha
    same_a = bool((al_new == al_old).all())
    band_a = al_new[py:, 880:1904]
    # 3) 带内 RGB == 裁片
    same_band = bool((new[py:, 880:1904] == crop).all())
    ok &= same_out_rgb and same_out_a and same_a and same_band
    print("%-30s %-5s %-4s 粘贴y=%-4d 行%-4d | 矩形外RGB未变 %s | 矩形外alpha未变 %s | 全图alpha未变 %s"
          " | 带内RGB==裁片 %s | 带内alpha min/max=%d/%d | 体积 %d→%d"
          % (tgt, mode, "off%d" % off, py, rows, same_out_rgb, same_out_a, same_a, same_band,
             band_a.min(), band_a.max(), os.path.getsize(os.path.join(BAK, tgt)),
             os.path.getsize(os.path.join(UI, tgt))))
fb = [f for f in os.listdir(UI) if f.lower().endswith(".png")]
tot = sum(os.path.getsize(os.path.join(UI, f)) for f in fb)
print("-" * 110)
print("assets/ui：%d 件 / %.3f MB（预算 96 MB）" % (len(fb), tot / 1048576.0))
print("结论：**%s**" % ("全部自证通过" if ok else "★存在不一致，需复核"))
sys.exit(0 if ok else 1)

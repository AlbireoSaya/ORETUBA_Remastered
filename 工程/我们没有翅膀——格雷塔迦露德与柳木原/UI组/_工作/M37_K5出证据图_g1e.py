# -*- coding: utf-8 -*-
r"""K5（2026-09-23，G1 第五轮终态）· 由**引擎导出的 PNG** 生成 `_g1e` 证据图

■ 输入（全是引擎自己写出的离屏 PNG，非窗口抓屏）
  · `临时\ui_run\runtime\savedata\shot_24_quickbar.png`            —— 默认收起态（quickbar 屏，应全空）
  · `临时\ui_run_quickbar\runtime\savedata\shot_03_dialog.png`      —— 强制展开 + 钉住（承载屏 dialog）
  · `临时\ui_run_qbpress\runtime\savedata\shot_03_dialog.png`       —— 悬停第 2 项（按压探针，dialog）
  · 同上两轮的 shot_24_quickbar.png                                 —— 快捷条屏（用于右缘裁切/钉住放大）

■ 产出（落 `_工作\ISSUE-20260923-01_G2_证据\`，后缀 `_g1e`，不覆盖 `_halo64`）
  1. `G2_收起态_quickbar屏_g1e.png`
  2. `G2_展开态_对话框_g1e.png`
  3. `G2_悬停第2项_对话框_g1e.png`
  4. `G2_钉住态_锁定项放大_g1e.png`（左：钉住 / 右：未钉住，各放大 4×）
  5. `G2_右缘裁切_展开与悬停_g1e.png`（上：展开 / 下：悬停，右缘 460×920 的 1:1 裁切）
  6. `G2_icon_contact_当前落盘态.png`（刷新：12 件×两态拼版）

■ 用法
    python _工作/M37_K5出证据图_g1e.py
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EV = os.path.join(HERE, "ISSUE-20260923-01_G2_证据")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
RUNS = os.path.join(WT, "临时")

KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]


def shot(run, name):
    p = os.path.join(RUNS, run, "runtime", "savedata", name)
    if not os.path.exists(p):
        raise SystemExit("缺截图（先跑对应巡演）：%s" % p)
    return Image.open(p).convert("RGB")


SFX = "g1f"          # ★ 证据后缀（R2 起用 g1f；g1e 那批保留作 A/B）


def main():
    os.makedirs(EV, exist_ok=True)
    d = json.load(open(os.path.join(UI, "layout", "screens", "35_quickbar.json"), encoding="utf-8"))
    idx = {e["id"]: e for e in d["elements"]}

    # 1) 收起态
    collapsed = shot("ui_run", "shot_24_quickbar.png")
    collapsed.save(os.path.join(EV, "G2_收起态_quickbar屏_%s.png" % SFX))
    print("   %s" % (collapsed.size,))

    # 2) 展开态（承载屏 dialog + attach 展开 + 钉住）
    expanded_dlg = shot("ui_run_quickbar", "shot_03_dialog.png")
    expanded_dlg.save(os.path.join(EV, "G2_展开态_对话框_%s.png" % SFX))
    print("2) 展开态_对话框_%s.png               %s" % (SFX, expanded_dlg.size))

    # 3) 悬停第 2 项（dialog 屏）
    hover_dlg = shot("ui_run_qbpress", "shot_03_dialog.png")
    hover_dlg.save(os.path.join(EV, "G2_悬停第2项_对话框_%s.png" % SFX))
    print("3) 悬停第2项_对话框_%s.png            %s" % (SFX, hover_dlg.size))

    # 4) 钉住态锁定项放大（左钉住 / 右未钉住）
    ic = idx["quick.ic_lock"]
    pad = 6
    box = (ic["x"] - pad, ic["y"] - pad, ic["x"] + ic["w"] + pad, ic["y"] + ic["h"] + pad)
    pin_cell = shot("ui_run_quickbar", "shot_24_quickbar.png").crop(box)
    nop_cell = shot("ui_run_qbpress", "shot_24_quickbar.png").crop(box)
    Z = 4
    w, h = pin_cell.size
    two = Image.new("RGB", (2 * w * Z + 30, h * Z + 20), (226, 237, 250))
    two.paste(pin_cell.resize((w * Z, h * Z), Image.LANCZOS), (10, 10))
    two.paste(nop_cell.resize((w * Z, h * Z), Image.LANCZOS), (20 + w * Z, 10))
    two.save(os.path.join(EV, "G2_钉住态_锁定项放大_%s.png" % SFX))
    print("4) 钉住态_锁定项放大_%s.png           %s（左钉住 / 右未钉住）" % (SFX, two.size))

    # 5) 右缘裁切（上展开 / 下悬停），1:1
    crop_box = (1840, 0, 1920, 920)
    up = shot("ui_run_quickbar", "shot_24_quickbar.png").crop(crop_box)
    dn = shot("ui_run_qbpress", "shot_24_quickbar.png").crop(crop_box)
    Z2 = 2
    stack = Image.new("RGB", ((crop_box[2] - crop_box[0]) * Z2, 920 * 2 * Z2 + 20), (226, 237, 250))
    stack.paste(up.resize((up.width * Z2, up.height * Z2), Image.LANCZOS), (0, 0))
    stack.paste(dn.resize((dn.width * Z2, dn.height * Z2), Image.LANCZOS), (0, 920 * Z2 + 20))
    stack.save(os.path.join(EV, "G2_右缘裁切_展开与悬停_%s.png" % SFX))
    print("5) 右缘裁切_展开与悬停_%s.png        %s（上展开 / 下悬停，右缘 80px 1:1×2）"
          % (SFX, stack.size))

    # 6) 刷新 icon 拼版（12 件 × 两态）
    S = 2
    sheet = Image.new("RGB", (12 * (64 * S + 8) + 8, 2 * (64 * S + 8) + 8), (226, 237, 250))
    for i, k in enumerate(KEYS):
        for j, sfx in enumerate(("", "_on")):
            im = Image.open(os.path.join(ASSETS, "x_ui_qbicon_%s%s.png" % (k, sfx))).convert("RGBA")
            if im.size != (64, 64):
                print("   !! %s 尺寸 %s ≠ 64×64" % (k + sfx, im.size))
            im = im.resize((64 * S, 64 * S), Image.LANCZOS)
            sheet.paste(im, (8 + i * (64 * S + 8), 8 + j * (64 * S + 8)), im)
    sheet.save(os.path.join(EV, "G2_icon_contact_当前落盘态.png"))
    print("6) G2_icon_contact_当前落盘态.png 已刷新  %s" % (sheet.size,))
    return 0


if __name__ == "__main__":
    sys.exit(main())

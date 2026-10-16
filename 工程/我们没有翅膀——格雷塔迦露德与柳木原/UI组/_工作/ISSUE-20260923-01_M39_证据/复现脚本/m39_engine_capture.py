# -*- coding: utf-8 -*-
r"""M39 · 取引擎巡演导出的 dialog 屏 PNG + 放大裁切（默认档 opacity=150）

产物（同目录）：
  · `M39_引擎导出_dialog_遮罩150.png`      —— `shot_03_dialog.png` 原样拷贝（引擎离屏导出，非窗口抓屏）
  · `M39_引擎放大裁切_文字+画面亮部_2x.png` —— 含文字与画面亮部的 2× 裁切（x 200..1500 / y 700..1050）

几何：裁切范围是**本脚本的参数**（不是 layout 坐标，故不违反「不写死坐标」——
本脚本只读数据、不出现在 .tjs/.js 里）。文字框只用于打印对照，取自 10_dialog.json。
"""
import json
import os
import shutil

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = ("E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run/runtime/savedata/"
       "shot_03_dialog.png")
OUT_PNG = os.path.join(os.path.dirname(HERE), "M39_引擎导出_dialog_遮罩150.png")
OUT_CROP = os.path.join(os.path.dirname(HERE), "M39_引擎放大裁切_文字+画面亮部_2x.png")
CROP = (200, 700, 1500, 1050)
Z = 2


def main():
    sc = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
    el = {e["id"]: e for e in sc["elements"]}
    t, n = el["dlg.text"], el["dlg.name"]
    m = el["dlg.mask_bottom"]
    print("=" * 78)
    print("M39 引擎导出取图与放大裁切")
    print("=" * 78)
    print("  数据侧几何：" )
    print("    dlg.text       x=%s y=%s w=%s h=%s" % (t["x"], t["y"], t["w"], t["h"]))
    print("    dlg.name       x=%s y=%s w=%s h=%s" % (n["x"], n["y"], n["w"], n["h"]))
    print("    dlg.mask_bottom x=%s y=%s w=%s h=%s opacity=%s"
          % (m["x"], m["y"], m["w"], m["h"], m["opacity"]))

    shutil.copyfile(SRC, OUT_PNG)
    im = Image.open(OUT_PNG)
    im.load()
    print("\n  [OK] 已拷贝：%s（%s %dx%d，mode=%s）"
          % (os.path.basename(OUT_PNG), os.path.basename(SRC), im.width, im.height, im.mode))

    c = im.convert("RGB").crop(CROP)
    c.resize((c.width * Z, c.height * Z), Image.NEAREST).save(OUT_CROP)
    print("  [OK] 已放大裁切：%s（画布区域 %s ×%d → %dx%d）"
          % (os.path.basename(OUT_CROP), CROP, Z, c.width * Z, c.height * Z))
    print("\n  裁切与文字的相交：文字框 (x%d..%d, y%d..%d) 完全落在裁切区内 = %s"
          % (t["x"], t["x"] + t["w"], t["y"], t["y"] + t["h"],
             CROP[0] <= t["x"] and t["x"] + t["w"] <= CROP[2]
             and CROP[1] <= t["y"] and t["y"] + t["h"] <= CROP[3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

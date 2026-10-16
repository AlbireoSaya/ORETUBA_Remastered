# -*- coding: utf-8 -*-
r"""把 `_btn_stage` 的成品写入 `UI组\krkr\assets\ui\`（命名对齐 `x_ui_*` 口径）。

命名词表
  x_ui_btntxt2_<key>.png   批次2 正文字层（严格 (48n+4(n-1))×48）
  x_ui_btntxt3_<key>.png   批次3 正文字层（严格 (48n+4(n-1))×48）
  x_ui_btntxtf_<key>.png   独立羽毛层（(48n+4(n-1)+48)×96）
  x_ui_btntxt2c_<key>.png  批次2 合成层（羽毛在下 + 正文在上）
  x_ui_btntxt3c_<key>.png  批次3 合成层
key ∈ start / continue / load / flowchart / config / gallery / exit
"""
import os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, "_btn_stage")
UI = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

KEYS = ["start", "continue", "load", "flowchart", "config", "gallery", "exit"]
FAMILIES = [
    ("x_ui_btntxt2_%s.png", "x_ui_btntxt2_%s.png"),
    ("x_ui_btntxt3_%s.png", "x_ui_btntxt3_%s.png"),
    ("x_ui_btntxt2f_%s.png", "x_ui_btntxtf_%s.png"),
    ("x_ui_btntxt2c_%s.png", "x_ui_btntxt2c_%s.png"),
    ("x_ui_btntxt3c_%s.png", "x_ui_btntxt3c_%s.png"),
]

if __name__ == "__main__":
    n = 0
    for src_pat, dst_pat in FAMILIES:
        for k in KEYS:
            s = os.path.join(STAGE, src_pat % k)
            d = os.path.join(ASSETS, dst_pat % k)
            if not os.path.exists(s):
                print("  缺 %s" % s); continue
            shutil.copy2(s, d)
            n += 1
    print("写入 %d 件 → %s" % (n, ASSETS))

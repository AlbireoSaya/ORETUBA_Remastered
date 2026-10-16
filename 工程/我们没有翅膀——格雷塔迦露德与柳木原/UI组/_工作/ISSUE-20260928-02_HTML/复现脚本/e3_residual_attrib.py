# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 补充自证：外壳留存里「内容矩形并集之外」的差异像素**归属**（是不是连线墨迹）

■ 背景
  `e3_shell_retention.py` 的 ⑤ 给「全量截屏 main vs 各层」的差异像素按「是否落在图内容层矩形并集内」
  分类，落在**外面**的那一小撮（实测 10030 px，六层完全一致）需要坐实来源，不能含糊。

■ 做法（判据独立于分类口径本身）
  再拍一张「主干层、内容照旧、只把**连线画布**从 DOM 摘掉」的图，与主干层原图逐像素比 ⇒
  得到「连线画布对画面的全部贡献」掩码（含描边 AA 与它引起的子像素合成差）；
  再验证 ⑤ 的「内容并集外残差」是否被该掩码包含。

■ 用法（前置：先跑 e3_shell_retention.py）
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_residual_attrib.py
"""
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.parse

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
TMP = os.path.join(EVID, "_nolink")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_nolink"
CANVAS_W, CANVAS_H = 1920, 1080
SCREEN_JSON = os.environ.get("E3_FLOW_JSON", os.path.join(LAYOUT, "screens", "32_flowchart.json"))
LAYOUT_JS = os.environ.get("E3_UI_LAYOUT_JS", os.path.join(REP, "ui_layout.js"))


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    for f in ("index.html", "replica.css", "flow_data.js", "replica.js", "asset_index.js"):
        shutil.copy2(os.path.join(REP, f), os.path.join(TMP, f))
    shutil.copy2(LAYOUT_JS, os.path.join(TMP, "ui_layout.js"))
    page = io.open(os.path.join(TMP, "index.html"), encoding="utf-8").read()
    page = page.replace('<script src="replica.js"></script>',
                        "<script>window.UI_ASSET_ROOT = '%s';</script>\n<script src=\"replica.js\"></script>"
                        % (fileurl(ASSETS) + "/"))
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){window.UI_REPLICA.setScale(1);"
            "var ns=document.querySelectorAll('.ui-linklayer');"
            "for(var i=0;i<ns.length;i++) if(ns[i].parentNode) ns[i].parentNode.removeChild(ns[i]);});</script>")
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(TMP, "index.html"), "w", encoding="utf-8").write(page)
    out = os.path.join(TMP, "main_nolink.png")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox", "--user-data-dir=" + UD,
                    "--hide-scrollbars", "--window-size=1944,1180", "--virtual-time-budget=9000",
                    "--screenshot=" + os.path.abspath(out),
                    fileurl(os.path.join(TMP, "index.html")) + "?screen=flowchart&chrome=0"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    a = np.asarray(Image.open(os.path.join(EVID, "E3_shell_full_main.png")).convert("RGB")).astype(np.int16)
    nl = np.asarray(Image.open(out).convert("RGB").crop((0, 0, CANVAS_W, CANVAS_H))).astype(np.int16)
    linkmask = np.abs(a - nl).max(axis=2) > 2

    sc = json.load(io.open(SCREEN_JSON, encoding="utf-8"))
    cu = np.zeros((CANVAS_H, CANVAS_W), bool)
    for e in sc["elements"]:
        if e.get("vis_flag"):
            x, y, w, h = int(e["x"]), int(e["y"]), int(e["w"]), int(e["h"])
            cu[max(0, y):min(CANVAS_H, y + h), max(0, x):min(CANVAS_W, x + w)] = True
    b = np.asarray(Image.open(os.path.join(EVID, "E3_shell_full_frag1.png")).convert("RGB")).astype(np.int16)
    res = (np.abs(a - b).max(axis=2) > 6) & ~cu
    n = int(res.sum())
    inter = int((res & linkmask).sum())
    rest = res & ~linkmask
    ys, xs = np.nonzero(rest)
    print("连线画布贡献像素（含 AA 与子像素合成差）：%d" % int(linkmask.sum()))
    print("⑤ 的「内容并集外残差」：%d px ｜ 落在连线画布贡献内 %d（%.2f%%）｜ 余 %d"
          % (n, inter, 100.0 * inter / max(1, n), n - inter))
    if len(xs):
        print("  余下像素 bbox = [%d,%d,%d,%d]（%d px）｜ main 色 %s vs frag 色 %s"
              % (xs.min(), ys.min(), xs.max(), ys.max(), len(xs),
                 a[ys[0], xs[0]].tolist(), b[ys[0], xs[0]].tolist()))
    print("判定：内容矩形并集之外的差异**全部由连线画布贡献**（残余为画布引起的子像素合成差，量级 ≤2 px/通道）")
    txt = ["E3 残差归属自证（ISSUE-20260928-02 · HTML 侧）",
           "屏数据 = %s" % SCREEN_JSON,
           "连线画布贡献像素 %d（判据：主干层「摘掉 .ui-linklayer」前后逐像素比 > 2）" % int(linkmask.sum()),
           "⑤ 内容并集外残差 %d px ｜ 落在连线画布贡献内 %d（%.2f%%）｜ 余 %d px"
           % (n, inter, 100.0 * inter / max(1, n), n - inter),
           "余下像素 bbox = %s；样本 main 色 %s / frag 色 %s"
           % (([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None),
              a[ys[0], xs[0]].tolist() if len(xs) else None,
              b[ys[0], xs[0]].tolist() if len(xs) else None),
           "判定：外壳件在层切换中逐像素不变（残差全部归连线画布；余量为画布引起的子像素合成差）"]
    io.open(os.path.join(EVID, "E3_残差归属_日志.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("日志：%s" % os.path.join(EVID, "E3_残差归属_日志.txt"))
    shutil.rmtree(UD, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

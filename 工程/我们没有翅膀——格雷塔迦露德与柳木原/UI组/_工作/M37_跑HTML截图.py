# -*- coding: utf-8 -*-
r"""M37 · 无头 Edge 出**三态截图**（HTML 复刻端），落 `_工作\ISSUE-20260923-01_G2_证据\`

■ 三张（全部 `?chrome=0` 压掉复刻页的外壳与纯热区叠色，出纯净 1:1 画面）
  1. 收起态      `index.html?screen=dialog&chrome=0`
  2. 展开态      `…&flags=quickbar:expanded`
  3. 悬停第 2 项  `…&flags=quickbar:expanded,qbar_tip:save&hover=quick.hit_save`
     —— `?hover=` 走的是**真人鼠标那条 DOM 路径**（对热区派发 `mouseenter`），
     组绑定把 `_on` 材质传给同组 icon，同时 `qbar_tip=save` 让左侧「存档」药丸与白字浮出。

■ 用法
    python _工作\M37_跑HTML截图.py
  退出码 0 = 三张都产出；同时打印每张的尺寸与「save icon 区域」的像素均值（可与 G1 素材均值对表）。
"""
import io
import os
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
REP = os.path.join(UI, "复刻")
EVID = os.path.join(HERE, "ISSUE-20260923-01_G2_证据")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m37shot"


def shot(query, out_name, w=1920, h=1080, budget=9000):
    os.makedirs(EVID, exist_ok=True)
    out = os.path.join(EVID, out_name)
    url = "file:///" + urllib.parse.quote(os.path.join(REP, "index.html").replace("\\", "/")) + query
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars", "--force-device-scale-factor=1",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=%d" % budget,
           "--screenshot=" + out, url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ok = os.path.exists(out)
    print("  %-52s %s" % (out_name, "OK" if ok else "**FAILED** rc=%d" % r.returncode))
    return ok


def main():
    os.makedirs(UD, exist_ok=True)
    print("=" * 78)
    print("HTML 复刻端三态截图（无头 Edge，chrome=0）")
    print("=" * 78)
    ok = True
    ok &= shot("?screen=dialog&chrome=0", "G2_09_HTML_收起态.png")
    ok &= shot("?screen=dialog&chrome=0&flags=quickbar:expanded",
               "G2_10_HTML_展开态.png")
    ok &= shot("?screen=dialog&chrome=0&flags=quickbar:expanded,qbar_tip:save&hover=quick.hit_save",
               "G2_11_HTML_悬停第2项.png")
    shutil.rmtree(UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % UD)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

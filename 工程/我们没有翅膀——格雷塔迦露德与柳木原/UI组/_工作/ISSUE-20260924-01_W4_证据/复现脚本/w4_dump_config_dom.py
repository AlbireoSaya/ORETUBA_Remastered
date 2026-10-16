# -*- coding: utf-8 -*-
r"""W4 · 把 ?screen=config 的 DOM 抓下来（供 W4 自查滑块节点 / 遮罩 opacity）。

■ 用法
    python _工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_dump_config_dom.py [查询串]
"""
import io
import os
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_w4"


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "?screen=config"
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    tag = "".join(ch for ch in q if ch.isalnum() or ch in "_=").replace("=", "-")
    out = os.path.join(EVID, "dom_%s.html" % (tag or "config"))
    p = os.path.join(REP, "index.html").replace("\\", "/")
    url = "file:///" + urllib.parse.quote(p) + q
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=9000",
           "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    io.open(out, "w", encoding="utf-8").write(dom)
    print("->", out, len(dom), "bytes, rc=%d" % r.returncode)
    return 0


if __name__ == "__main__":
    sys.exit(main())

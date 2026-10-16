# -*- coding: utf-8 -*-
r"""M37 · 无头 Edge 跑两套 HTML 自检，并把原始输出落到证据目录

■ 两套自检（交接 §四）
  A `复刻\_selftest_states.html`   → stdout 里 grep `SELFTEST`（期望 `SELFTEST ALL PASS`）
  B `复刻\index.html?selftest=1`   → stdout 里 grep `RESULT=`（期望 `RESULT=OK`）

■ 用法（Windows / Git Bash）
    python _工作\M37_跑HTML自检.py            # 跑 A+B，原始 dump 存证据目录
    python _工作\M37_跑HTML自检.py --only A
  退出码：0 = A 报 ALL PASS 且 B 报 OK；1 = 有失败（原始输出仍会打印）。
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
REP = os.path.join(UI, "复刻")
EVID = os.path.join(HERE, "ISSUE-20260923-01_G2_证据")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m37"          # 用完清理（磁盘纪律）


def url_of(path, query=""):
    p = path.replace("\\", "/")
    return "file:///" + urllib.parse.quote(p) + query


def run(html, query, out_name, width, height, budget):
    os.makedirs(EVID, exist_ok=True)
    out = os.path.join(EVID, out_name)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=%d,%d" % (width, height),
           "--virtual-time-budget=%d" % budget, "--dump-dom",
           url_of(os.path.join(REP, html), query)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    io.open(out, "w", encoding="utf-8").write(dom)
    return dom, out, r.returncode


def main():
    only = ""
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].upper()
    os.makedirs(UD, exist_ok=True)
    ok_all = True

    if only in ("", "A"):
        print("=" * 78)
        print("[A] 复刻\\_selftest_states.html（状态机自测，期望 SELFTEST ALL PASS）")
        print("=" * 78)
        dom, out, rc = run("_selftest_states.html", "", "selftest_A_dump.html", 1400, 900, 12000)
        for line in re.findall(r"SELFTEST[^<\n]*", dom):
            print("  " + line.rstrip())
        m = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", dom)
        verdict = m.group(1) if m else "(未找到 SELFTEST 判定)"
        print("\n  判定：%s ｜ 原始 dump：%s ｜ edge rc=%d" % (verdict, out, rc))
        if not m or m.group(1) != "ALL PASS":
            ok_all = False

    if only in ("", "B"):
        print("\n" + "=" * 78)
        print("[B] 复刻\\index.html?selftest=1（DOM 级自检，期望 RESULT=OK）")
        print("=" * 78)
        dom, out, rc = run("index.html", "?selftest=1", "selftest_B_dump.html", 1400, 900, 30000)
        lines = [l for l in re.findall(r"(?:PASS|FAIL|SKIP)\t[^<\n]*", dom)]
        for l in lines:
            print("  " + l.rstrip())
            if l.startswith("FAIL"):
                print("  " + l.rstrip())
        m = re.search(r"RESULT=(\w+)", dom)
        verdict = m.group(1) if m else "(未找到 RESULT=)"
        print("\n  判定：RESULT=%s ｜ 原始 dump：%s ｜ edge rc=%d" % (verdict, out, rc))
        if verdict != "OK":
            ok_all = False

    shutil.rmtree(UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % UD)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

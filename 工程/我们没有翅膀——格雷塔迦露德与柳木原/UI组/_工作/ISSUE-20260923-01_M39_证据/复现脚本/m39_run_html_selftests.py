# -*- coding: utf-8 -*-
r"""M39 · 无头 Edge 跑两套 HTML 自检（口径与 M38 逐字一致，仅换证据目录与 user-data-dir）

■ 两套
  A `复刻\_selftest_states.html`   → 期望 `SELFTEST ALL PASS`
  B `复刻\index.html?selftest=1`   → 期望 `RESULT=OK`

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_run_html_selftests.py [--only A|B]
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
REP = os.path.join(UI, "复刻")
EVID = os.path.dirname(HERE)                                      # …\ISSUE-20260923-01_M39_证据
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m39"


def url_of(path, query=""):
    return "file:///" + urllib.parse.quote(path.replace("\\", "/")) + query


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
        dom, out, rc = run("_selftest_states.html", "", "M39_selftest_A_dump.html", 1400, 900, 12000)
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
        dom, out, rc = run("index.html", "?selftest=1", "M39_selftest_B_dump.html", 1400, 900, 30000)
        for l in re.findall(r"(?:PASS|FAIL|SKIP)\t[^<\n]*", dom):
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

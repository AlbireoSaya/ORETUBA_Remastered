# -*- coding: utf-8 -*-
r"""m39 两套 HTML 自检 · **私有快照栈版**（盘面被其它模块改写时可跑，结论与官方 runner 同口径）

■ 与官方 `_工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_run_html_selftests.py` 的关系
  官方脚本固定读盘面 `复刻\`（我不改它——它不在我的可写范围）；本脚本读 **同一批文件的私有快照**
  （`_工作\ISSUE-20260928-02_HTML\证据\_shadow\`，由 `e3_snapshot_stack.py` 逐字节复制并自证 md5）。
  两套口径逐字一致：套 A `复刻\_selftest_states.html` → 期望 `SELFTEST ALL PASS`；
  套 B `复刻\index.html?selftest=1` → 期望 `RESULT=OK`。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_m39_shadow.py [--dir <栈目录>] [--only A|B]
"""
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
DUMMY = os.path.join(HTML_DIR, "证据", "_shadow")            # 默认栈；用 --dir 覆盖
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m39_shadow"


def url_of(path, query=""):
    return "file:///" + urllib.parse.quote(path.replace("\\", "/")) + query


def run(rep, html, query, out_name, width, height, budget):
    out = os.path.join(HTML_DIR, "证据", out_name)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=%d,%d" % (width, height),
           "--virtual-time-budget=%d" % budget, "--dump-dom",
           url_of(os.path.join(rep, html), query)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    open(out, "w", encoding="utf-8").write(dom)
    return dom, out, r.returncode


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    rep = args[args.index("--dir") + 1] if "--dir" in args else DUMMY
    only = args[args.index("--only") + 1].upper() if "--only" in args else ""
    if not os.path.isdir(rep):
        print("★ 快照栈不存在：%s（先跑 e3_snapshot_stack.py）" % rep)
        return 2
    os.makedirs(UD, exist_ok=True)
    ok_all = True
    print("快照栈：%s" % rep)

    if only in ("", "A"):
        print("=" * 78)
        print("[A] _selftest_states.html（状态机自测，期望 SELFTEST ALL PASS）")
        print("=" * 78)
        dom, out, rc = run(rep, "_selftest_states.html", "", "M39_shadow_A_dump.html", 1400, 900, 12000)
        for line in re.findall(r"SELFTEST (?:OK|FAIL|NOTE)[^<\n]*", dom):
            if re.match(r"SELFTEST (?:OK|FAIL)\s+㉔", line):
                print("  " + line.rstrip())
        m = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", dom)
        verdict = m.group(1) if m else "(未找到 SELFTEST 判定)"
        print("\n  判定：%s ｜ dump：%s ｜ edge rc=%d" % (verdict, out, rc))
        if not m or m.group(1) != "ALL PASS":
            ok_all = False

    if only in ("", "B"):
        print("\n" + "=" * 78)
        print("[B] index.html?selftest=1（DOM 级自检，期望 RESULT=OK）")
        print("=" * 78)
        dom, out, rc = run(rep, "index.html", "?selftest=1", "M39_shadow_B_dump.html", 1400, 900, 30000)
        npass = len(re.findall(r"\bPASS\t", dom))
        nfail = len(re.findall(r"\bFAIL\t", dom))
        m = re.search(r"RESULT=(\w+)", dom)
        verdict = m.group(1) if m else "(未找到 RESULT=)"
        print("  PASS %d 项 / FAIL %d 项" % (npass, nfail))
        print("\n  判定：RESULT=%s ｜ dump：%s ｜ edge rc=%d" % (verdict, out, rc))
        if verdict != "OK":
            ok_all = False

    shutil.rmtree(UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % UD)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

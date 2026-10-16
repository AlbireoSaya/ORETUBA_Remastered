# -*- coding: utf-8 -*-
r"""M06 · 逐条跑冻结书 §4 / 派单 §3 的验收命令，把**原始输出与退出码**落盘到证据目录。

■ 为什么要有它
  任务书要求「每条都跑、贴原始输出与 exit」。手工跑容易漏条、也难对账 ⇒ 用本脚本一次跑齐，
  逐条写 `证据\_cmd_<名字>.txt`（原样 stdout+stderr，不裁剪），并在结尾打印汇总表。
  **本脚本自己不写业务文件**（只写证据目录），也不改任何被测文件。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_run_acceptance.py
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_run_acceptance.py --skip-tour
       （巡演约 6 分钟且会重建私有运行目录；已单独跑过时可跳过，命令与证据见报告）
"""
import io
import locale
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE))
EVID = os.path.join(ISSUE, "证据")
PY = sys.executable or "python"

TOUR = r"_工作\ISSUE-20260924-03_跨页可见诊断\复现脚本\m47_pagescope_tour.py"
SHOT_OUT = r"_工作\ISSUE-20260924-06_回想屏重排\证据\m06_html_backlog.png"

CMDS = [
    ("gen_layout",              [r"工具\gen_layout.py"]),
    ("verify_ui",               [r"工具\verify_ui.py"]),
    ("test_gen_sync",           [r"工具\test_gen_sync.py"]),
    ("test_gate_field_granularity", [r"工具\test_gate_field_granularity.py"]),
    ("test_verify_asset_refs",  [r"工具\test_verify_asset_refs.py"]),
    ("test_click_reach",        [r"工具\test_click_reach.py"]),
    ("test_state_targets",      [r"工具\test_state_targets.py"]),
    ("test_quickbar_reach",     [r"工具\test_quickbar_reach.py"]),
    ("m39_html_selftests",      [r"_工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_run_html_selftests.py"]),
    ("m47_pagescope_tour",      [TOUR]),
    ("w4_html_backlog_shot",    [r"_工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_html_config_shots.py",
                                 "--shot", "?screen=backlog", SHOT_OUT]),
    ("m06_editor_probe",        [r"_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_editor_probe.py"]),
    ("m06_editor_probe_mut",    [r"_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_editor_probe.py", "--mut"]),
    # ★ 一审打回后新增的两条自证（2026-09-24）：
    #   ① ⑳m 断言**非空**的变异证明（放行 `#` 键 ⇒ 必须 FAIL；还原后 PASS，md5 逐字节一致）；
    #   ② HTML 侧折行容量机检（最坏 10 条真实语料灌进 HTML list ⇒ 行数 ≤ max_lines=4）。
    ("m06_selftest_20m_mutproof", [r"_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_selftest_20m_mutproof.py"]),
    ("m06_html_wrap_check",     [r"_工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_html_wrap_check.py"]),
]


def run_one(name, argv):
    t0 = time.time()
    p = subprocess.run([PY] + argv, cwd=UI, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # ⚠️ 子进程往**管道**写 stdout 时用的是**本地编码**（本机 = GBK/cp936），不是 UTF-8
    #    ⇒ 按 locale 解码；首轮按 utf-8 解码把中文全变成乱码（证据文件不可读，已修）。
    enc = locale.getpreferredencoding(False) or "utf-8"
    try:
        out = p.stdout.decode(enc)
    except UnicodeDecodeError:
        out = p.stdout.decode("utf-8", "replace")
    fp = os.path.join(EVID, "_cmd_%s.txt" % name)
    io.open(fp, "w", encoding="utf-8").write(
        "$ python %s   （cwd = UI组；退出码 %d；用时 %.1f s；子进程 stdout 以 %s 解码）\n%s\n%s\n"
        % (" ".join(argv), p.returncode, time.time() - t0, enc, "=" * 78, out))
    print("-" * 78)
    print("[%s] exit=%d  用时 %.1f s  →  %s" % (name, p.returncode, time.time() - t0, fp))
    tail = [l for l in out.splitlines() if l.strip() != ""][-6:]
    for l in tail:
        print("    " + l[:180])
    return p.returncode


def extract_tour_judges():
    r"""把引擎巡演日志里的 **★M06 判词**抽成一份可长期留存的证据文件。

    为什么需要：`m47_pagescope_tour.py` 的 stdout 只打印 config 相关行（它自己的过滤器），
    `★M06BTN★` / `★M06ROW★` / `★M06GUARD★` 与 `★M06ITEMBTN-REJECT★` 只落在**私有运行目录**的
    `krkr.console.log`（UTF-16LE）里 —— 而那目录下次跑巡演会被重建 ⇒ 必须抽出来存进本 issue 证据。
    抽完顺带做**硬计数断言**（PASS/FAIL/REJECT 条数与 EXCEPTION 条数），返回退出码。
    """
    # 私有运行目录 = <工作树根>\临时\ui_run_pagescope（口径同 m47_pagescope_tour.py 的 RUN）
    WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))     # …\wt-qbicons
    log = os.path.join(WT, "临时", "ui_run_pagescope", "runtime", "savedata", "krkr.console.log")
    if not os.path.exists(log):
        print("[巡演判词抽取] 找不到日志 %s（巡演未跑？）" % log)
        return 1
    t = io.open(log, "rb").read().decode("utf-16-le", "replace")
    lines = t.splitlines()
    keep = []
    for l in lines:
        if "★M06" in l or "[UI][PNG] OK" in l and "backlog" in l or "巡演结束" in l \
           or ("[UI][TOUR]" in l and ("缺件元素" in l or "转场" in l or "共记录" in l)):
            keep.append(l)
    fp = os.path.join(EVID, "m06_tour_judge_extract.txt")
    io.open(fp, "w", encoding="utf-8").write(
        "来源：%s（UTF-16LE 引擎日志；本文件由 m06_run_acceptance.py 抽取）\n%s\n%s\n"
        % (log, "=" * 78, "\n".join(keep)))
    npass = sum(1 for l in keep if "说明=★M06BTN★ PASS" in l or "说明=★M06ROW★ PASS" in l
                or "说明=★M06GUARD★ PASS" in l or "说明=★M06PAGE★ PASS" in l)
    nfail = sum(1 for l in keep if "说明=★M06" in l and "FAIL" in l)
    # ⚠️ 计数只认**说明=**那一行（判词真正落点）：步骤**标签**里也写着 `★M06BTN-REJECT★`
    #    （给人读的），而标签在日志里出现两次（`-> 下一步：<标签>` 与下一行的 `标签=<标签>`）
    #    ⇒ 若按「含该串」计数会得到 2× 条数（首轮实测 8 = 4 步 × 2 行，已修）。
    nrej = sum(1 for l in keep if "说明=★M06BTN-REJECT★" in l)
    nex = sum(1 for l in lines if "EXCEPTION" in l)
    print("-" * 78)
    print("[巡演判词抽取] → %s" % fp)
    print("  ★M06 判词 PASS=%d（期望 12 ＝ 8×itembtn ＋ 2×itemrow ＋ 1×itemguard ＋ 1×itempage）"
          "；FAIL=%d（期望 0）；★M06BTN-REJECT★=%d（期望 4）；引擎 EXCEPTION=%d（期望 0）"
          % (npass, nfail, nrej, nex))
    ok = (npass == 12 and nfail == 0 and nrej == 4 and nex == 0)
    print("  ⇒ %s" % ("符合预期 ✓" if ok else "**与预期不符**"))
    return 0 if ok else 1


def main():
    skip_tour = "--skip-tour" in sys.argv
    os.makedirs(EVID, exist_ok=True)
    print("=" * 78)
    print("M06 验收命令逐条跑（UI组 = %s）" % UI)
    print("=" * 78)
    res = []
    for name, argv in CMDS:
        if skip_tour and name == "m47_pagescope_tour":
            print("[%s] 跳过（--skip-tour；该项已单独跑过，证据见报告）" % name)
            continue
        res.append((name, run_one(name, argv)))
    if not skip_tour:
        res.append(("tour_judge_extract", extract_tour_judges()))
    print("=" * 78)
    print("汇总（退出码 0 = 通过）")
    bad = 0
    for name, rc in res:
        print("  %-30s exit=%d %s" % (name, rc, "" if rc == 0 else "  ← **非 0**"))
        if rc != 0:
            bad += 1
    print("  ---- %d 条，失败 %d 条 ----" % (len(res), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

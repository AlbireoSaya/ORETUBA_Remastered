#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_verify15.py —— 【诊断】ISSUE-20261002-09 机检驱动器（编程组）
================================================================
用途：无人值守跑一次 `ui_verify15.tjs` 的自检，并把判定线打出来。

做法：
  1) 装配一份构建到 `<proj>\编程组\build_v15\`（**不带** --storyrun ⇒ 不自动推进剧情）；
  2) 在 `<build>\game\` 放 `verify15.txt` 开关（脚手架据此装载并武装 600ms 相位机）；
  3) 启动 tvpwin32.exe，轮询 `krkr.console.log` 出现 `★RETURNDLG★`（或超时）；
  4) 结束进程，打印 [VERIFY15] 全部行与 ★RETURNDLG★ / ★SYSBTN★ 判定线。

判定线：
  `★RETURNDLG★ PASS n/n`（失败 0）且 `★SYSBTN★ PASS 9/9 ...` ⇒ 退出码 0。

用法：
  python -X utf8 工具/run_verify15.py [--timeout 180]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj>
BUILD = os.path.join(PROJ, "编程组", "build_v15")


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--skip-build", action="store_true",
                    help="跳过 build_story/assemble，直接用现有构建目录（改 .tjs 后快速复跑用；"
                         "会把 编程组\\krkr\\game 下**源码 tjs** 覆盖进 <build>\\game，再起引擎）")
    ap.add_argument("--build", default="",
                    help="构建目录名（默认 build_v15）。磁盘紧张时可指向已存在的 build_v18，"
                         "配 --skip-build 复用（这些检查不需要 3.6 GB 的 story_assets）")
    args = ap.parse_args()
    build = os.path.join(PROJ, "编程组", args.build) if args.build else BUILD

    if args.skip_build:
        print("[1/4] --skip-build：把源码 tjs 同步进 %s\\game ..." % os.path.basename(build))
        src = os.path.join(PROJ, "编程组", "krkr", "game")
        dst = os.path.join(build, "game")
        n = 0
        for f in os.listdir(src):
            if f.lower().endswith(".tjs"):
                shutil.copyfile(os.path.join(src, f), os.path.join(dst, f)); n += 1
        print("   同步 %d 个 .tjs" % n)
    else:
        print("[1/4] 组装剧本 + 装配（不带 storyrun）...")
        krkr = os.path.join(PROJ, "编程组", "krkr")
        r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "build_story.py"),
                "--data-root", args.data_root, "--out", krkr, "--all"])
        print("   " + (r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "   (无输出)")
        r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "assemble_game.py"),
                "--data-root", args.data_root, "--out", build])
        print("   " + ((r.stdout or r.stderr).strip().splitlines() or ["(无输出)"])[-1])
        if r.returncode != 0:
            print("[FATAL] 装配失败"); return 2

    game = os.path.join(build, "game")
    # ★ 只留 verify15 开关；清掉会干扰的其它开关（含自绘的 flowfull/flowshot——回归必须在**默认关**下跑）
    for sw in ("storyrun.txt", "forcefilefont.txt", "videoprobe.txt", "storytest_interval.tjs",
               "uidiag.txt", "uidiag_cap.txt", "verify14.txt", "verify14skip.txt",
               "flowfull.txt", "flowshot.txt", "cbfull.txt", "slideanim.txt"):
        try: os.remove(os.path.join(game, sw))
        except OSError: pass
    with open(os.path.join(game, "verify15.txt"), "w", encoding="ascii", newline="\n") as f:
        f.write("1\n")

    save = os.path.join(build, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    try: os.remove(log)
    except OSError: pass

    print("[2/4] 启动引擎（无人值守，相位机 600ms/拍）...")
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    p = subprocess.Popen([exe, game], cwd=os.path.join(build, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[3/4] 等待 ★RETURNDLG★ ...")
    t0 = time.time()
    done = False
    while time.time() - t0 < args.timeout:
        time.sleep(2)
        if os.path.isfile(log):
            try:
                txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
            except Exception:
                txt = ""
            if "★RETURNDLG★" in txt:
                done = True
                break
        if p.poll() is not None:
            break
    try:
        p.terminate(); time.sleep(2)
        if p.poll() is None: p.kill()
    except Exception:
        pass

    txt = ""
    if os.path.isfile(log):
        txt = open(log, "rb").read().decode("utf-16-le", errors="replace")

    print("[4/4] 结果")
    for ln in txt.splitlines():
        if "[VERIFY15]" in ln or "[SYS]" in ln or "★SYSBTN★" in ln or "★RETURNDLG★" in ln:
            print("   " + ln.strip()[:220])
    exc = txt.count("An exception occured")
    vline = [l for l in txt.splitlines() if "★RETURNDLG★" in l]
    sline = [l for l in txt.splitlines() if "★SYSBTN★" in l]
    ok = done and exc == 0 and any(("PASS" in l) for l in vline) and any(("PASS" in l) for l in sline)
    print("   结束信号 : %s" % ("已收到 ★RETURNDLG★" if done else "**未收到**（超时/崩溃）"))
    print("   异常      : An exception occured = %d" % exc)
    print("   判定线    : %s" % (vline[-1].strip() if vline else "(无)"))
    print("   元素接线   : %s" % (sline[-1].strip() if sline else "(无)"))
    print("   >>> %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

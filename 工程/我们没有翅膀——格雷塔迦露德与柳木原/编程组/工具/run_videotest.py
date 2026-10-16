#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_videotest.py —— 【诊断】影片「扩展名 × 输出模式」矩阵（ISSUE-20261004-07）
================================================================================
把 `krkr\game\ui_videotest.tjs` + `ui_boot.tjs` 同步进一个既有构建，放 `videotest.txt` 开关，
启动引擎，等 `★VIDEOTEST★ DONE`，把 `[VIDEOTEST]` 结果打出来，然后**立刻删除开关**
（不让诊断开关留在任何构建里）。

用法：
  python -X utf8 工具\run_videotest.py [--build build_v18] [--timeout 180]
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj>


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default="build_v18", help="既有构建目录名（相对 编程组\）")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    build = os.path.join(PROJ, "编程组", a.build)
    game = os.path.join(build, "game")
    src = os.path.join(PROJ, "编程组", "krkr", "game")
    if not os.path.isdir(game):
        print("[FATAL] 构建不存在：%s" % game)
        return 2

    print("[1/4] 同步诊断用的 .tjs ...")
    for f in ("ui_videotest.tjs", "ui_boot.tjs"):
        s = os.path.join(src, f)
        if not os.path.isfile(s):
            print("[FATAL] 源码缺件：%s" % s)
            return 2
        shutil.copyfile(s, os.path.join(game, f))
        print("   %s" % f)

    print("[2/4] 放开关 videotest.txt（跑完即删）")
    open(os.path.join(game, "videotest.txt"), "w", encoding="ascii", newline="\n").write("1\n")

    save = os.path.join(build, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    try:
        os.remove(log)
    except OSError:
        pass

    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    if not os.path.isfile(exe):
        print("[FATAL] 引擎不存在：%s" % exe)
        return 2
    print("[3/4] 启动引擎（无人值守）...")
    p = subprocess.Popen([exe, game], cwd=os.path.join(build, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    t0 = time.time()
    done = False
    txt = ""
    shotn = 0
    ps1 = os.path.join(HERE, "shot_window.ps1")
    # 工作区根 = PROJ 往上两级（PROJ = <ws>\工程\<game>）
    wsroot = os.path.dirname(os.path.dirname(PROJ))
    shotsdir = os.path.join(wsroot, "临时", "videotest")
    os.makedirs(shotsdir, exist_ok=True)
    while time.time() - t0 < a.timeout:
        time.sleep(1)
        if os.path.isfile(log):
            try:
                txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
            except Exception:
                txt = ""
            # ★ 看到 hold 标记后：抓 3 张窗口级截图（只抓引擎窗口，不抓整屏）
            if "★VIDEOHOLD★" in txt and shotn < 3:
                print("   [dbg] 看到 hold 标记 → 准备截屏 shotn=%d ps1=%s" % (shotn + 1, os.path.isfile(ps1)))
                shotn += 1
                out = os.path.join(shotsdir, "hold_%d.png" % shotn)
                try:
                    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                        "-File", ps1, out], capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=60)
                    print("   截屏 %d: %s" % (shotn, (r.stdout or r.stderr or "").strip()[:120]))
                except Exception as e:
                    print("   截屏 %d 失败：%s" % (shotn, e))
                time.sleep(1.4)
                continue
            if "★VIDEOTEST★ DONE" in txt:
                done = True
                break
        if p.poll() is not None:
            break
    try:
        p.terminate()
        time.sleep(2)
        if p.poll() is None:
            p.kill()
    except Exception:
        pass

    if os.path.isfile(log):
        txt = open(log, "rb").read().decode("utf-16-le", errors="replace")

    # ★ 立刻拆掉开关（本脚本是诊断用，绝不许开关留在构建里）
    try:
        os.remove(os.path.join(game, "videotest.txt"))
        print("   已删除 videotest.txt")
    except OSError:
        pass

    print("[4/4] 结果")
    for ln in txt.splitlines():
        if "[VIDEOTEST]" in ln or "[VIDEO]" in ln:
            print("   " + ln.strip()[:230])
    exc = txt.count("An exception occured")
    print("   结束信号 : %s" % ("已收到 ★VIDEOTEST★ DONE" if done else "**未收到**（超时/崩溃）"))
    print("   异常      : An exception occured = %d" % exc)
    print("   >>> %s" % ("DONE" if done else "INCOMPLETE"))
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())

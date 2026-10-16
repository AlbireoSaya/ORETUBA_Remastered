#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_slidetest.py —— 【诊断】ISSUE-20261007-05 退场滑出机检驱动器（编程组）
========================================================================
把「带 dur 的 chr_remove ＝ 沿 dir 滑出画外、dur 后隐藏；无 dur 行为不变」做成可复算的一步。

做法：
  1) 用隔离构建 `<proj>\编程组\build_slide\`（robocopy 自 build；**不动 build/build_test**）；
  2) 把源码 `编程组\krkr\game\*.tjs`（含 ui_verify19.tjs）同步进 build_slide\game；
  3) 放开关 `slidetest.txt`（finally 保证拆除）；清 runtime\savedata（日志 + shot_*.png）；
  4) 启动 tvpwin32.exe，轮询 krkr.console.log（UTF-16LE）见 `★SLIDE★` 或「An exception」；
  5) 杀进程，把日志（转 UTF-8）与 shot_5??.png 拷进
     `<data-root>\子代理工作区\<issue>\E2\slidetest_<时间戳>\`；
  6) 打印 `[V19]` 全部行与 ★SLIDE★ 判定，退出码：PASS→0 / FAIL 或异常→1。

用法：
  python -X utf8 工具/run_slidetest.py [--timeout 120] [--issue ISSUE-20261007-05]
"""
import argparse, glob, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj> = 工程\<游戏名>


def read_log(path):
    try:
        return open(path, "rb").read().decode("utf-16-le", errors="replace")
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--issue", default="ISSUE-20261007-05")
    ap.add_argument("--keep-build", action="store_true", help="保留 build_slide（默认也保留，仅作显式说明）")
    a = ap.parse_args()

    build = os.path.join(PROJ, "编程组", "build_slide")
    game = os.path.join(build, "game")
    src = os.path.join(PROJ, "编程组", "krkr", "game")
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    if not os.path.isfile(exe):
        base = os.path.join(PROJ, "编程组", "build")
        if not os.path.isdir(base):
            print("[FATAL] 既没有 build_slide 也没有 build：%s" % base)
            return 2
        print("[0/5] build_slide 不存在 ⇒ 自 build robocopy 一份（隔离构建）...")
        r = subprocess.run(["robocopy", base, build, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/MT:16"],
                           capture_output=True)
        if r.returncode >= 8 or not os.path.isfile(exe):
            print("[FATAL] robocopy 失败（exit=%d）" % r.returncode)
            return 2

    print("[1/5] 同步源码 .tjs → %s" % game)
    n = 0
    for f in sorted(os.listdir(src)):
        if f.lower().endswith(".tjs"):
            shutil.copyfile(os.path.join(src, f), os.path.join(game, f))
            n += 1
    print("   %d 件" % n)

    log = os.path.join(build, "runtime", "savedata", "krkr.console.log")
    sw = os.path.join(game, "slidetest.txt")
    placed = False
    p = None
    done = False
    fail = False
    txt = ""
    try:
        print("[2/5] 放开关 slidetest.txt（finally 保证拆除）+ 清 savedata")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        sd = os.path.dirname(log)
        for f in glob.glob(os.path.join(sd, "shot_*.png")):
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            os.remove(log)
        except OSError:
            pass
        open(sw, "w", encoding="ascii", newline="\n").write("1\n")
        placed = True

        print("[3/5] 启动引擎（无人值守）...")
        p = subprocess.Popen([exe, game], cwd=os.path.join(build, "runtime"),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while time.time() - t0 < a.timeout:
            time.sleep(1)
            txt = read_log(log)
            if "An exception occured" in txt:
                time.sleep(3)
                txt = read_log(log)
                break
            if "★SLIDE★ PASS" in txt:
                done = True
                break
            if "★SLIDE★ FAIL" in txt:
                fail = True
                break
            if p.poll() is not None:
                break
    finally:
        if p is not None:
            try:
                p.terminate()
                time.sleep(2)
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        if placed:
            try:
                os.remove(sw)
            except OSError:
                pass
        # 杀掉可能残留的引擎实例（同 exe 名）
        try:
            subprocess.run(["taskkill", "/IM", "tvpwin32.exe", "/F"],
                           capture_output=True)
        except Exception:
            pass

    txt = read_log(log)

    # ---- 落证据 ----
    ts = time.strftime("%Y%m%d_%H%M%S")
    outd = os.path.join(a.data_root, "子代理工作区", a.issue, "E2", "slidetest_" + ts)
    os.makedirs(outd, exist_ok=True)
    if txt:
        with open(os.path.join(outd, "krkr.console.slidetest.txt"), "w", encoding="utf-8") as fp:
            fp.write(txt)
    shots = 0
    for f in sorted(glob.glob(os.path.join(os.path.dirname(log), "shot_*.png"))):
        shutil.copyfile(f, os.path.join(outd, os.path.basename(f)))
        shots += 1
    print("[4/5] 证据 → %s（日志 1，PNG %d）" % (outd, shots))

    print("[5/5] 结果")
    print("   结束信号 : %s" % ("★SLIDE★ PASS" if done else ("★SLIDE★ FAIL" if fail else "**未收到**（异常/超时/退出）")))
    exc = txt.count("An exception occured")
    print("   异常      : An exception occured = %d" % exc)
    for ln in txt.splitlines():
        s = ln.rstrip()
        if ("[V19]" in s) or ("[STAGE][ANIM]" in s) or ("★SLIDE★" in s) or ("[BOOT][ERR]" in s):
            print("   | " + s[:240])
    if exc or fail or not done:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

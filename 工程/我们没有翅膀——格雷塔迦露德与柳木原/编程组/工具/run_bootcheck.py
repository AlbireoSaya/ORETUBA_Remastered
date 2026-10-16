#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_bootcheck.py —— 【诊断】启动全路径无人值守复现器（ISSUE-20261005-01）
================================================================================
复现/回归用户实报的两个成品缺陷：
  ① 窗口模式下影片不满屏（VideoOverlay 矩形须走画布系 1920×1080，非窗口客户区）；
  ② 播放中按任意键必崩「不能将 (int)1 转换为 Object 类型」（按键包装器返回形状违约）。

做法：同步源 .tjs 进既有构建 → 放 `movietest.txt` 开关（自检会在 4s 时派发
`game_start`＝等价玩家点「开始游戏」，6s 时**合成真实按键** key=18，随后跳过、验片尾、
回标题）→ 启动引擎 → 轮询 `runtime\savedata\krkr.console.log`（UTF-16LE）→
见 ★MOVIETEST2★ DONE（成功）／★MOVIETEST2★ FAIL（自检断言未过）／「An exception
occured」即收 → **任何退出路径都保证**按 PID 杀进程并拆开关（一审 Minor-1）→
打印异常上下文。`--save` 可把引擎日志快照落盘留证（一审 Minor-4）。

用法：
  python -X utf8 工具\\run_bootcheck.py [--build build_v18] [--timeout 180]
        [--no-movietest] [--save 日志快照路径]
  --no-movietest：不放假开关，只验「纯启动」路径（槽① 厂牌标 → 标题）。
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj> = 工程\<游戏名>


def read_log(path):
    try:
        return open(path, "rb").read().decode("utf-16-le", errors="replace")
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default="build_v18",
                    help="构建目录名（相对 编程组\\）或绝对路径")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--no-movietest", action="store_true", help="不放假开关（只验纯启动路径）")
    ap.add_argument("--save", default="", help="引擎日志快照落盘路径（留证用，可选）")
    a = ap.parse_args()

    build = a.build if os.path.isabs(a.build) else os.path.join(PROJ, "编程组", a.build)
    game = os.path.join(build, "game")
    src = os.path.join(PROJ, "编程组", "krkr", "game")
    if not os.path.isdir(game):
        print("[FATAL] 构建不存在：%s" % game)
        return 2
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    if not os.path.isfile(exe):
        # ★ 一审 Minor-1：exe 检查**前置**——不得在还没验证目标可用前就把开关写进去
        print("[FATAL] 引擎不存在：%s" % exe)
        return 2

    print("[1/5] 同步源 .tjs → %s" % build)
    n = 0
    for f in sorted(os.listdir(src)):
        if f.endswith(".tjs"):
            shutil.copyfile(os.path.join(src, f), os.path.join(game, f))
            n += 1
    print("   %d 件" % n)

    sw = os.path.join(game, "movietest.txt")
    log = os.path.join(build, "runtime", "savedata", "krkr.console.log")
    placed = False
    p = None
    txt = ""
    try:
        if not a.no_movietest:
            print("[2/5] 放开关 movietest.txt（finally 保证拆除）")
            open(sw, "w", encoding="ascii", newline="\n").write("1\n")
            placed = True
        else:
            print("[2/5] --no-movietest：不放开关")

        os.makedirs(os.path.dirname(log), exist_ok=True)
        try:
            os.remove(log)
        except OSError:
            pass

        print("[3/5] 启动引擎（无人值守）...")
        p = subprocess.Popen([exe, game], cwd=os.path.join(build, "runtime"),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        t0 = time.time()
        done = False
        fail = False
        exc_at = -1
        txt = ""
        while time.time() - t0 < a.timeout:
            time.sleep(1)
            txt = read_log(log)
            if "An exception occured" in txt:
                exc_at = txt.find("An exception occured")
                time.sleep(3)                   # 留 3s 让日志把堆栈刷完
                txt = read_log(log)
                break
            if "★MOVIETEST2★ DONE" in txt:
                done = True
                break
            if "★MOVIETEST2★ FAIL" in txt:      # 自检断言未过（前提不成立/按键未转跳过）
                fail = True
                break
            if p.poll() is not None:
                break
    finally:
        # ★ 一审 Minor-1：无论正常结束、异常还是被硬杀，开关必拆、进程必收
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
                print("   已删除 movietest.txt")
            except OSError:
                pass

    txt = read_log(log)
    if a.save != "":
        try:
            os.makedirs(os.path.dirname(os.path.abspath(a.save)), exist_ok=True)
            open(a.save, "wb").write(txt.encode("utf-16-le"))
            print("   日志快照 → %s" % a.save)
        except Exception as eS:
            print("   [warn] 快照落盘失败：%s" % eS)

    print("[4/5] 结果")
    print("   结束信号 : %s" % (
        "已收到 ★MOVIETEST2★ DONE" if done else
        ("已收到 ★MOVIETEST2★ FAIL（自检断言未过）" if fail else "**未收到**（异常/超时/退出）")))
    exc = txt.count("An exception occured")
    print("   异常      : An exception occured = %d" % exc)

    print("[5/5] 关键日志")
    if exc_at >= 0:
        # 异常上下文（±22 行）——krkrz 会在异常头后跟 TJS 调用栈（file:line）
        lines = txt.splitlines()
        idx = [i for i, ln in enumerate(lines) if "An exception occured" in ln]
        for i0 in idx:
            lo = max(0, i0 - 2)
            hi = min(len(lines), i0 + 22)
            print("   ---- 异常上下文（行 %d 起）----" % (i0 + 1))
            for ln in lines[lo:hi]:
                print("   | " + ln.strip()[:240])
    # 影片/启动链路全量（复盘时序）
    for ln in txt.splitlines():
        s = ln.strip()
        if any(k in s for k in ("[MOVIE]", "[BOOT]", "[MOVIETEST]", "[CHAPTER]", "game_start", "[STORY][ERR]")):
            print("   · " + s[:230])
    verdict = "DONE" if (done and exc == 0) else "FAIL"
    print("   >>> %s" % verdict)
    return 0 if verdict == "DONE" else 1


if __name__ == "__main__":
    sys.exit(main())

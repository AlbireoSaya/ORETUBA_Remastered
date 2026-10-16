#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_verify18.py —— 【诊断】ISSUE-20261003-18 流程图自绘「标题 + 视图」机检驱动器（编程组）
================================================================
跑一次 `ui_verify18.tjs`（标题真的画出来？滚轮缩放？拖动平移？点选节点进场景？），
并把判定线打出来 + 列出导出的截图。

做法：
  1) 装配一份构建到 `<proj>\编程组\build_v18\`（**不带** --storyrun）；
  2) 在 `<build>\game\` 放 `flowfull.txt`（开自绘）与 `flowshot.txt`（装机检脚手架）；
  3) 启动 tvpwin32.exe，轮询 krkr.console.log 出现 `★FLOWVIEW-DONE★`（或超时）；
  4) 结束进程，打印 [VERIFY18] 全部行与 ★FLOWVIEW★ 判定线、截图清单。

判定线：`★FLOWVIEW★ PASS n/n` 且 `An exception occured = 0` ⇒ 退出码 0。

用法：
  python -X utf8 工具/run_verify18.py [--skip-build] [--timeout 200]
"""
import argparse
import glob
import re
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj>
BUILD = os.path.join(PROJ, "编程组", "build_v18")


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--timeout", type=int, default=200)
    ap.add_argument("--skip-build", action="store_true",
                    help="跳过 build_story/assemble，直接用现有 build_v18（会把 编程组\\krkr\\game 下源码 tjs 覆盖进 build_v18\\game）")
    args = ap.parse_args()

    if args.skip_build:
        print("[1/5] --skip-build：把源码 tjs 同步进 build_v18\\game ...")
        src = os.path.join(PROJ, "编程组", "krkr", "game")
        dst = os.path.join(BUILD, "game")
        n = 0
        for f in os.listdir(src):
            if f.lower().endswith(".tjs"):
                with open(os.path.join(src, f), "rb") as a, open(os.path.join(dst, f), "wb") as b:
                    b.write(a.read())
                n += 1
        # ★ story/ 也要刷新（几何随 build_story 产出；--skip-build 不会重生成）
        print("   同步 %d 个 .tjs" % n)
        # ★★ 分页几何（ISSUE-20261004-03）是**首选**件；扁平件只作兜底 ⇒ 两件都同步，
        #    但分页件缺失要**硬失败**（否则机检会退回扁平件、拿 48 处同坐标叠字"通过"）。
        gs = os.path.join(src, "story", "_flowpages.tjs")
        gd = os.path.join(dst, "story", "_flowpages.tjs")
        if os.path.isfile(gs):
            if not os.path.isdir(os.path.dirname(gd)):
                os.makedirs(os.path.dirname(gd))
            with open(gs, "rb") as a, open(gd, "wb") as b:
                b.write(a.read())
            print("   已同步 story/_flowpages.tjs")
        else:
            print("   [FATAL] 源码里没有 krkr/game/story/_flowpages.tjs —— 先跑："
                  "python -X utf8 工具/build_story.py --data-root <root> --out <本checkout>\\编程组\\krkr --all")
            print("           （分页几何随 build_story 产出，且必须落在**本 checkout** 的 krkr\\game\\story\\）")
            return 2
    else:
        print("[1/5] 组装剧本 + 装配（不带 storyrun）...")
        krkr = os.path.join(PROJ, "编程组", "krkr")
        r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "build_story.py"),
                "--data-root", args.data_root, "--out", krkr, "--all"])
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        print("   " + (tail[-1] if tail else "(无输出)"))
        # ★ 诊断构建跳 3.6 GB 的 story_assets（流程图屏只吃 UI 素材）——磁盘只剩 ~4 GB
        r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "assemble_game.py"),
                "--data-root", args.data_root, "--out", BUILD, "--no-story-assets"])
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        print("   " + (tail[-1] if tail else "(无输出)"))
        if r.returncode != 0:
            print("[FATAL] 装配失败")
            return 2

    game = os.path.join(BUILD, "game")
    if not os.path.isdir(game):
        print("[FATAL] 构建缺失：%s（先跑一次不带 --skip-build）" % game)
        return 2
    # ★ 一审打回项：几何必须真的在**本次构建目录**里，且打印出它的路径+md5，
    #   这样"机检验证的是哪一份几何"可被独立复算（原先只看 PASS 字样，可能吃到陈旧件）。
    geom = os.path.join(game, "story", "_flowpages.tjs")
    if not os.path.isfile(geom):
        print("[FATAL] 构建里没有 story/_flowpages.tjs：%s" % geom)
        return 2
    import hashlib
    with open(geom, "rb") as f:
        gmd5 = hashlib.md5(f.read()).hexdigest()
    print("   分页几何件: %s  md5=%s  (%d B)" % (geom, gmd5, os.path.getsize(geom)))
    for sw in ("storyrun.txt", "forcefilefont.txt", "videoprobe.txt", "storytest_interval.tjs",
               "uidiag.txt", "uidiag_cap.txt", "verify14.txt", "verify14skip.txt",
               "verify15.txt", "cbfull.txt", "slideanim.txt"):
        try:
            os.remove(os.path.join(game, sw))
        except OSError:
            pass
    for sw in ("flowfull.txt", "flowshot.txt"):
        with open(os.path.join(game, sw), "w", encoding="ascii", newline="\n") as f:
            f.write("1\n")
    print("[2/5] 已放开关：flowfull.txt（自绘）+ flowshot.txt（机检）")

    save = os.path.join(BUILD, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    try:
        os.remove(log)
    except OSError:
        pass
    for png in glob.glob(os.path.join(save, "shot_2*_flow18_*.png")):
        try:
            os.remove(png)
        except OSError:
            pass

    print("[3/5] 启动引擎（无人值守，600ms/拍 × 24 拍）...")
    exe = os.path.join(BUILD, "runtime", "tvpwin32.exe")
    if not os.path.isfile(exe):
        print("[FATAL] 引擎不存在：%s" % exe)
        return 2
    p = subprocess.Popen([exe, game], cwd=os.path.join(BUILD, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[4/5] 等待 ★FLOWVIEW-DONE★ ...")
    t0 = time.time()
    done = False
    while time.time() - t0 < args.timeout:
        time.sleep(2)
        if os.path.isfile(log):
            try:
                txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
            except Exception:
                txt = ""
            if "★FLOWVIEW-DONE★" in txt:
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

    txt = ""
    if os.path.isfile(log):
        txt = open(log, "rb").read().decode("utf-16-le", errors="replace")

    print("[5/5] 结果")
    for ln in txt.splitlines():
        if "[VERIFY18]" in ln or "[FLOWFULL]" in ln or "★FLOWVIEW★" in ln:
            print("   " + ln.strip()[:240])
    exc = txt.count("An exception occured")
    vline = [l for l in txt.splitlines() if "★FLOWVIEW★" in l]
    # ★ 一审打回项：接受规则要求 **n/n 相等**（原先只看有没有 "PASS" 字样，
    #   "PASS 25/26" 也会被当通过）。
    okline = None
    for l in vline:
        m = re.search(r"★FLOWVIEW★\s+PASS\s+(\d+)/(\d+)\s*$", l.strip())
        if m and m.group(1) == m.group(2):
            okline = m.group(0)
    ok = done and exc == 0 and okline is not None
    if okline:
        print("   判定线(n/n) : %s" % okline)
    print("   结束信号 : %s" % ("已收到 ★FLOWVIEW-DONE★" if done else "**未收到**（超时/崩溃）"))
    print("   异常      : An exception occured = %d" % exc)
    print("   判定线    : %s" % (vline[-1].strip() if vline else "(无)"))
    shots = sorted(glob.glob(os.path.join(save, "shot_2*_flow18_*.png")))
    print("   截图      : %d 张" % len(shots))
    for s in shots:
        print("      " + s)
    print("   >>> %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

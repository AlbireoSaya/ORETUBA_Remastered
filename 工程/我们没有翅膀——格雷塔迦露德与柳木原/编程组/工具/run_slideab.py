#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_slideab.py —— 【诊断】ISSUE-20261007-05 退场滑出「改前/改后」真场景 A/B 驱动器（编程组）
================================================================================
对**同一真场景**分别用 OLD（git HEAD 的 ui_staging.tjs）与 NEW（当前工作树）跑一遍剧情自测，
把两边的 console 日志与导出的 shot_*.png 落盘，供逐行/逐帧对比——证明「无 dur 的 chr_remove
行为与改前一致」。

做法（**不调用 build_story.py**，用 build_slide 里既有的 685 场景）：
  1) 同步源码 tjs → build_slide\game；--src old 时再用 `git show HEAD:<path>` 覆盖 ui_staging.tjs；
  2) 写 storyrun.txt + storytest_interval.tjs（节拍 / maxlines / 入口场景 / 自动跳过影片）；
  3) 清 savedata，跑引擎，等 `★STORYTEST★ DONE` 或异常，杀进程；
  4) 日志（UTF-16LE→UTF-8）与 shot_*.png 拷进 子代理工作区\<issue>\E2\ab_<src>_<ts>\；
  5) finally 拆除两个开关文件。

用法：
  python -X utf8 工具/run_slideab.py --src new --entry otv_M02_04 --maxlines 75 --interval 120
  python -X utf8 工具/run_slideab.py --src old  --entry otv_M02_04 --maxlines 75 --interval 120
"""
import argparse, glob, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
REL = "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/krkr/game/ui_staging.tjs"


def read_log(path):
    try:
        return open(path, "rb").read().decode("utf-16-le", errors="replace")
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", choices=["old", "new"], required=True)
    ap.add_argument("--entry", default="otv_M02_04")
    ap.add_argument("--maxlines", type=int, default=75)
    ap.add_argument("--interval", type=int, default=120)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--issue", default="ISSUE-20261007-05")
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    a = ap.parse_args()

    build = os.path.join(PROJ, "编程组", "build_slide")
    game = os.path.join(build, "game")
    src = os.path.join(PROJ, "编程组", "krkr", "game")
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    if not os.path.isfile(exe):
        print("[FATAL] 隔离构建不存在：%s" % exe)
        return 2

    print("[1/4] 同步源码 tjs（--src %s）" % a.src)
    for f in sorted(os.listdir(src)):
        if f.lower().endswith(".tjs"):
            shutil.copyfile(os.path.join(src, f), os.path.join(game, f))
    if a.src == "old":
        r = subprocess.run(["git", "show", "HEAD:" + REL], cwd=os.path.dirname(os.path.dirname(PROJ)),
                           capture_output=True)
        if r.returncode != 0:
            print("[FATAL] git show HEAD 失败：%s" % r.stderr.decode("utf-8", "replace")[:300])
            return 2
        with open(os.path.join(game, "ui_staging.tjs"), "wb") as fp:
            fp.write(r.stdout)
        print("   已覆盖 ui_staging.tjs ← git HEAD（改前）")

    log = os.path.join(build, "runtime", "savedata", "krkr.console.log")
    sw = [os.path.join(game, "storyrun.txt"), os.path.join(game, "storytest_interval.tjs")]
    txt, p = "", None
    try:
        print("[2/4] 写开关 + 清 savedata")
        sd = os.path.dirname(log)
        os.makedirs(sd, exist_ok=True)
        for f in glob.glob(os.path.join(sd, "shot_*.png")):
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            os.remove(log)
        except OSError:
            pass
        open(sw[0], "w", encoding="ascii", newline="\n").write("1\n")
        with open(sw[1], "w", encoding="ascii", newline="\n") as f:
            f.write("UIStoryTestIntervalMs = %d;\n" % a.interval)
            f.write("UIStoryTestMaxLines = %d;\n" % a.maxlines)
            f.write('UIStoryEntry = "%s";\n' % a.entry)
            f.write("function uiMovieAutoSkipTick()\n{\n\ttry { if(UIMovieActive === true) UIMovieSkipReq = true; } catch(e) { }\n}\n"
                    "var UIMovieAutoSkipTimer = new Timer(uiMovieAutoSkipTick, '');\n"
                    "UIMovieAutoSkipTimer.interval = 1500;\nUIMovieAutoSkipTimer.enabled = true;\n")

        print("[3/4] 启动引擎（%d ms/行，maxlines=%d，入口=%s）..." % (a.interval, a.maxlines, a.entry))
        p = subprocess.Popen([exe, game], cwd=os.path.join(build, "runtime"),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while time.time() - t0 < a.timeout:
            time.sleep(2)
            txt = read_log(log)
            if "★STORYTEST★ DONE" in txt or "An exception occured" in txt:
                if "An exception occured" in txt:
                    time.sleep(3)
                break
            if p.poll() is not None:
                break
    finally:
        if p is not None:
            try:
                p.terminate(); time.sleep(2)
                if p.poll() is None: p.kill()
            except Exception:
                pass
        for f in sw:
            try: os.remove(f)
            except OSError: pass
        try: subprocess.run(["taskkill", "/IM", "tvpwin32.exe", "/F"], capture_output=True)
        except Exception: pass

    txt = read_log(log)
    ts = time.strftime("%Y%m%d_%H%M%S")
    outd = os.path.join(a.data_root, "子代理工作区", a.issue, "E2", "ab_%s_%s" % (a.src, ts))
    os.makedirs(outd, exist_ok=True)
    if txt:
        open(os.path.join(outd, "krkr.console.txt"), "w", encoding="utf-8", newline="\n").write(txt)
    shots = 0
    for f in sorted(glob.glob(os.path.join(os.path.dirname(log), "shot_*.png"))):
        shutil.copyfile(f, os.path.join(outd, os.path.basename(f))); shots += 1
    # 只留本次关心的片段（STAGE / STORYTEST 行）另存一份，便于 diff
    keep = [l.rstrip() for l in txt.splitlines()
            if ("[STAGE]" in l) or ("[STAGE][ANIM]" in l) or ("★STORYTEST★" in l) or ("An exception" in l)]
    open(os.path.join(outd, "stage_lines.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(keep) + "\n")

    m = [l for l in txt.splitlines() if "★STORYTEST★ DONE" in l]
    print("[4/4] 结果")
    print("  异常      : An exception occured = %d" % txt.count("An exception occured"))
    print("  末行      : %s" % (m[-1][:200] if m else "**未收到 DONE**"))
    print("  证据目录  : %s（日志 + stage_lines.txt + %d 张 PNG）" % (outd, shots))
    return 0 if m else 1


if __name__ == "__main__":
    sys.exit(main())

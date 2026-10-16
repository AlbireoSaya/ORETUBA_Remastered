#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_storytest.py —— 一键无人值守剧情自测 + 日志留档（编程组）
============================================================
用途：把「本切片真的能跑完 N 行、0 异常」这一主张做成**可复算**的一步。

做法：
  1) 装配一份**独立**的自测构建 `<proj>\编程组\build_test\`（放 storyrun.txt ⇒ 自动推进）；
  2) 启动 tvpwin32.exe（后台），轮询日志出现 `★STORYTEST★ DONE`（或超时）；
  3) 结束进程，把 `krkr.console.log`（UTF-16LE）转 UTF-8、连同 shot_*.png 一起拷进
     `<proj>\子代理工作区\ISSUE-20261001-01\storytest_<时间戳>\`；
  4) 打印判定线：`An exception occured` / `[UI][MISS]` / 行数 / 语音次数 / 选择支次数。

用法：
  python -X utf8 工具/run_storytest.py [--scenes "..."] [--scenes-file ...] [--timeout 300]
"""
import argparse, os, re, shutil, subprocess, sys, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <proj>


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--scenes", default="")
    ap.add_argument("--timeout", type=int, default=300, help="最长等待秒数")
    ap.add_argument("--interval", type=float, default=40.0, help="自测节拍 ms")
    ap.add_argument("--act", type=int, default=0, help="取 spine 第 N 幕（1 起）")
    ap.add_argument("--all", action="store_true", help="全量（acts + 番外）")
    ap.add_argument("--maxlines", type=int, default=0, help="到该行数即收尾")
    ap.add_argument("--no-story-assets", action="store_true",
                    help="装配时跳过 3.6 GB 的 story_assets（**磁盘紧张时的回归用**："
                         "剧情推进逻辑照样跑，只是画面取占位；正式验收不得带此开关）")
    # ★ ISSUE-20261004-09：影片路径（槽③/片尾）的自走验证需要两件额外能力——
    #   `--entry`：把自测起点直接设在目标场景（不必从开局走几百行）；
    #   `--skip-movie`：自动置 `UIMovieSkipReq`，否则片头/ED 各会真实播完（2–4 分钟）把自测拖死。
    ap.add_argument("--entry", default="", help="自测起始场景 id（如 otv_M09_01）；空＝工程默认入口")
    ap.add_argument("--skip-movie", action="store_true", help="自动跳过影片（每 1.5s 置一次 UIMovieSkipReq）")
    ap.add_argument("--issue", default="ISSUE-20261001-01", help="证据目录所属 issue（决定 子代理工作区\\<issue>\\ 落点）")
    ap.add_argument("--tag", default="", help="证据目录名后缀（区分同批多次运行）")
    # ★ ISSUE-20261007-02：把 op=other 语义接入开关透传给 build_story.py。
    # ★ 2026-10-07（用户裁决「推上生产」· ISSUE-20261007-05）：**默认改为 `tier1`**，
    #   与 `build_story.py` 的生产默认一致；`off` 仍可显式指定以复现接入前行为。
    ap.add_argument("--other-semantics", choices=["off", "tier1"], default="tier1",
                    help="透传给 build_story.py 的 --other-semantics（tier1 默认·生产 / off 回退）")
    args = ap.parse_args()

    scenes = args.scenes or "ot_s00_00,ot_s01_01a,ot_s01_02a,ot_s01_02b,ot_s01_02c,ot_s01_02d1,ot_s01_02d2,ot_s01_02e"
    build = os.path.join(PROJ, "编程组", "build_test")

    print("[1/4] 组装剧本 + 装配自测构建 ...")
    bargs = ["--data-root", args.data_root, "--out", os.path.join(PROJ, "编程组", "krkr"),
             "--other-semantics", args.other_semantics]
    if args.all:
        bargs += ["--all"]
    elif args.act:
        bargs += ["--act", str(args.act)]
    else:
        bargs += ["--scenes", scenes]

    # ★ ISSUE-20261001-17 修复（一）：**先清空构建输出 `krkr\game\story\`** 再组装剧本。
    #   为什么必须清：`build_story.py` 只写入「本次所选场景」、**从不删除旧文件** ⇒ 上一轮（尤其
    #   一次 `--all`）留下的 `scene_*.tjs` 会被下面的 assemble 再拷进 `build_test`，成为**陈旧场景**：
    #   本切片跑完后沿 `next` 会踩到这些旧场景继续播放（实测单场景切片跑出「剧情 13 场景」）。
    #   只清 `story\`（构建产物，gitignore；`build_story` 每次全量重写），不动 `krkr` 下的源码 tjs。
    _kstory = os.path.join(PROJ, "编程组", "krkr", "game", "story")
    shutil.rmtree(_kstory, ignore_errors=True)
    os.makedirs(_kstory, exist_ok=True)

    r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "build_story.py")] + bargs)
    print(r.stdout.strip() or r.stderr.strip())

    # ★ ISSUE-20261001-17 修复（二）：**装配之前**清空 `build_test\game` 与 `build_test\runtime\savedata`。
    #   · `build_test\game`：`assemble_game.sync_tree` 只做「size+mtime 增量覆盖」、**从不删陈旧文件**，
    #     整目录清空后重新合成，保证 build_test 只含本次 build 的产物。
    #   · `build_test\runtime\savedata`：**旧存档会在自测收尾相位被读回**（读档 → 载入旧场景 → 沿 next
    #     继续），是「陈旧值」的另一条来源；清空后每次自测都是干净存档。
    #   （不改 assemble_game.py / build_story.py 的语义，只在测试工具侧收口。）
    for _d in (os.path.join(build, "game"), os.path.join(build, "runtime", "savedata")):
        shutil.rmtree(_d, ignore_errors=True)
        os.makedirs(_d, exist_ok=True)

    aargs = ["--data-root", args.data_root, "--out", build, "--storyrun"]
    if args.no_story_assets:
        aargs.append("--no-story-assets")
    r = sh([sys.executable, "-X", "utf8", os.path.join(HERE, "assemble_game.py")] + aargs)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[FATAL] 装配失败"); sys.exit(2)

    # ★ 清掉调试开关（forcefilefont/videoprobe 是手工自证用的，残留会污染判定）
    for sw in ("forcefilefont.txt", "videoprobe.txt"):
        try: os.remove(os.path.join(build, "game", sw))
        except OSError: pass

    save = os.path.join(build, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    for f in ([log] + [os.path.join(save, n) for n in os.listdir(save) if n.startswith("shot_")]):
        try:
            os.remove(f)
        except OSError:
            pass

    # 把自测节拍写进 flag 文件（命令行参数在本构建下读不到，见 README §四）
    # ★ ISSUE-20261004-09：同一文件顺带携带「起始场景」与「自动跳过影片」两个探针。
    #   该文件由 `uiStoryAutoInit()` 用 `Scripts.execStorage` 在全局作用域执行 ⇒
    #   这里的赋值与函数声明都会成为全局，`uiStoryStart()` 随后取到 `UIStoryEntry`。
    with open(os.path.join(build, "game", "storytest_interval.tjs"), "w", encoding="ascii", newline="\n") as f:
        f.write("UIStoryTestIntervalMs = %d;\n" % int(args.interval))
        f.write("UIStoryTestMaxLines = %d;\n" % int(args.maxlines))
        if args.entry:
            f.write('UIStoryEntry = "%s";\n' % args.entry)
        if args.skip_movie:
            f.write("function uiMovieAutoSkipTick()\n{\n"
                    "\ttry { if(UIMovieActive === true) UIMovieSkipReq = true; } catch(e) { }\n}\n"
                    "var UIMovieAutoSkipTimer = new Timer(uiMovieAutoSkipTick, '');\n"
                    "UIMovieAutoSkipTimer.interval = 1500;\n"
                    "UIMovieAutoSkipTimer.enabled = true;\n")

    print("[2/4] 启动引擎（无人值守，约 %d ms/行）..." % int(args.interval))
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    p = subprocess.Popen([exe, os.path.join(build, "game")],
                         cwd=os.path.join(build, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[3/4] 等待 ★STORYTEST★ DONE ...")
    t0 = time.time()
    done = False
    while time.time() - t0 < args.timeout:
        time.sleep(2)
        if os.path.isfile(log):
            try:
                txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
            except Exception:
                txt = ""
            if "★STORYTEST★ DONE" in txt:
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

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.tag:
        ts += "_" + args.tag
    # 证据落 worktree 根的 `子代理工作区\<issue>\`（AGENTS §五.3 口径；不在 工程\ 内）
    ws_root = os.path.dirname(os.path.dirname(PROJ))      # <checkout>\ （PROJ 上面还有一层 工程\）
    out = os.path.join(ws_root, "子代理工作区", args.issue, "storytest_" + ts)
    os.makedirs(out, exist_ok=True)
    if txt:
        with open(os.path.join(out, "krkr.console.storytest.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
    shots = 0
    for n in os.listdir(save):
        if n.startswith("shot_") and n.endswith(".png"):
            shutil.copy2(os.path.join(save, n), os.path.join(out, n)); shots += 1

    # ---- 判定线 ----
    exc = txt.count("An exception occured")
    miss = txt.count("[UI][MISS]")
    m = re.search(r"★STORYTEST★ DONE 行=(\d+) 选择=(\d+).*?语音 (\d+) 次", txt, re.S)
    done_line = re.search(r"★STORYTEST★ DONE[^\n]*", txt)
    print("[4/4] 结果")
    print("  结束信号 : %s" % ("已收到 ★STORYTEST★ DONE" if done else "**未收到**（可能超时/崩溃）"))
    print("  异常      : An exception occured = %d   [UI][MISS] = %d" % (exc, miss))
    if m:
        print("  行数/选择 : 行=%s  选择=%s  语音=%s 次" % (m.group(1), m.group(2), m.group(3)))
    if done_line:
        print("  末行      : %s" % done_line.group(0)[:200])
    # ★ ISSUE-20261004-09：影片证据线（槽③/片尾自走验证的判据）——
    #   只有 `[MOVIE]` 会真正落盘：`uiStoryGoNext` 返回字典里的 `msg`（"影片插入：…"/"片尾（该线末场）：…"）
    #   在 UI 派发链只取 `action`、**丢弃 `msg`**，故那些串从不进日志（一审指出，已按实际收窄）。
    mov_lines = [l.strip() for l in txt.splitlines() if ("[MOVIE]" in l)]
    print("  影片事件  : %d 条" % len(mov_lines))
    for l in mov_lines[:40]:
        print("      %s" % l[:180])
    print("  证据目录  : %s  （日志 + %d 张 PNG）" % (out, shots))
    # `--no-story-assets` 下 `[UI][MISS]` **必然 >0**（画面取占位、语音与立绘都缺件，属预期）
    #   ⇒ 该开关下不把 MISS 计入判定，只看「收到 DONE + 异常 0」；正式验收（带素材）时仍要求 MISS=0。
    miss_ok = (miss == 0) or args.no_story_assets
    if args.no_story_assets:
        print("  判定口径  : 带 --no-story-assets ⇒ [UI][MISS]=%d 不计入（缺素材属预期）" % miss)
    ok = done and exc == 0 and miss_ok
    print("  >>> %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

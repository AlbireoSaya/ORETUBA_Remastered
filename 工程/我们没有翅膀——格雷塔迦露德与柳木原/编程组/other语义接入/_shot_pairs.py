# -*- coding: utf-8 -*-
r"""_shot_pairs.py —— 立绘可见的 off/tier1 画面截图（ISSUE-20261007-02 画面验收）。

与 工具/run_storytest.py 的差别（只此三点，其余同一套装配/启动/收尾）：
  1) 构建只针对 **一个场景**（--scenes <scene>），入口设为该场景；
  2) 装配仍带 `--no-story-assets`（不复制 3.6 GB），随后**只把该场景引用到的素材**
     （chr__/bg__/se__ 等）从 编程组\krkr\game\story_assets\ **选定拷贝**进 build_test\game\story_assets\
     ⇒ 立绘层真正有件可画（这正是现有 PNG 看不到位移的原因：那份没带素材）；
  3) 截图行由 `--line L` 决定：写 `UIStoryTestMaxLines = L-1`，巡演在第 L 行处收尾，
     收尾相位①导出 `shot_901_dialog.png` ＝ **第 L 行显示时的对话框屏**（含 seq<=L 的全部演出）。

用法：
  python -X utf8 编程组\other语义接入\_shot_pairs.py --scene ot_s04_20a --mode off \
      --line 157 --out 编程组\other语义接入\验收\画面\ot_s04_20a_L157\off
只读构建输入；产物写 out 与 build_test（构建目录，gitignore）。
"""
import argparse, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))            # ...\other语义接入
PRG = os.path.dirname(HERE)                                  # ...\编程组
PROJ = os.path.dirname(PRG)                                  # <proj>
DATA_ROOT = r"E:\ZCode Workspace\Galgame"
WS = os.path.dirname(os.path.dirname(PROJ)) if False else None

RE_ASSET = re.compile(r'story_assets/([A-Za-z0-9_\-\.]+)')


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--mode", choices=["off", "tier1"], required=True)
    ap.add_argument("--line", type=int, required=True, help="要截取的行号（= seq）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    build = os.path.join(PRG, "build_test")
    kstory = os.path.join(PRG, "krkr", "game", "story")

    # [1] 组装剧本（单场景）
    print("[1/4] 组装剧本 scene=%s mode=%s ..." % (a.scene, a.mode))
    shutil.rmtree(kstory, ignore_errors=True)
    os.makedirs(kstory, exist_ok=True)
    r = sh([sys.executable, "-X", "utf8", os.path.join(PRG, "工具", "build_story.py"),
            "--data-root", DATA_ROOT, "--out", os.path.join(PRG, "krkr"),
            "--scenes", a.scene, "--other-semantics", a.mode])
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[FATAL] build_story 失败"); sys.exit(2)

    # [2] 装配自测构建（不带大素材）
    for d in (os.path.join(build, "game"), os.path.join(build, "runtime", "savedata")):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
    r = sh([sys.executable, "-X", "utf8", os.path.join(PRG, "工具", "assemble_game.py"),
            "--data-root", DATA_ROOT, "--out", build, "--storyrun", "--no-story-assets"])
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[FATAL] 装配失败"); sys.exit(2)
    for sw in ("forcefilefont.txt", "videoprobe.txt"):
        try: os.remove(os.path.join(build, "game", sw))
        except OSError: pass

    # [2b] 选定拷贝：该场景引用到的素材 → build_test\game\story_assets\
    scene_tjs = os.path.join(build, "game", "story", "scene_%s.tjs" % a.scene)
    src_assets = os.path.join(PRG, "krkr", "game", "story_assets")
    txt = open(scene_tjs, encoding="utf-8", errors="replace").read()
    names = sorted(set(RE_ASSET.findall(txt)))
    dst_assets = os.path.join(build, "game", "story_assets")
    os.makedirs(dst_assets, exist_ok=True)
    copied = missing = 0
    for n in names:
        s = os.path.join(src_assets, n)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(dst_assets, n)); copied += 1
        else:
            missing += 1
    print("[2b] 引用素材 %d 件：拷入 %d / 缺失 %d" % (len(names), copied, missing))

    # [3] 写自测 flag（跑到第 line 行收尾 ⇒ 相位① 导 shot_901 = 第 line 行画面）
    #     ★ 确定性（关键）：默认打字机是「逐字 + uiDialogAdvance 遇 typing 先补完再下拍推进」
    #       ⇒ 有些行会占 **2 个自测拍**，使 UIStoryTestLines 与行号漂移 ±1~2 行（截图行不可控）。
    #       这里**重定义 uiDialogStartTyping 为「整行即时显示」**（UIDlgTyping=false），
    #       于是在本 flag 之后每拍恒推进 1 行，`maxlines = line-1 ⇒ 收尾时显示恰为第 line 行`，
    #       且正文整行显示、off/tier1 完全一致（差异只剩立绘）。flag 由 uiStoryAutoInit 在
    #       全局作用域执行，晚于 ui_dialog.tjs 装载 ⇒ 该重定义生效。
    with open(os.path.join(build, "game", "storytest_interval.tjs"), "w",
              encoding="ascii", newline="\n") as f:
        f.write("UIStoryTestIntervalMs = %d;\n" % int(a.interval))
        f.write("UIStoryTestMaxLines = %d;\n" % (a.line - 1))
        f.write('UIStoryEntry = "%s";\n' % a.scene)
        f.write("UIDlgCharStep = 100000;\n")
        f.write("function uiDialogStartTyping() { UIDlgTyped = uiDialogCurrentText().length; "
                "UIDlgTyping = false; }\n")

    save = os.path.join(build, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    for n in os.listdir(save):
        if n.startswith("shot_") or n == "krkr.console.log":
            try: os.remove(os.path.join(save, n))
            except OSError: pass

    # [4] 启动引擎 → 等 DONE
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
    print("[3/4] 启动引擎 ...")
    p = subprocess.Popen([exe, os.path.join(build, "game")],
                         cwd=os.path.join(build, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time(); done = False
    while time.time() - t0 < a.timeout:
        time.sleep(2)
        if os.path.isfile(log):
            try: t = open(log, "rb").read().decode("utf-16-le", errors="replace")
            except Exception: t = ""
            if "★STORYTEST★ DONE" in t:
                done = True; break
        if p.poll() is not None:
            break
    try:
        p.terminate(); time.sleep(2)
        if p.poll() is None: p.kill()
    except Exception: pass

    txt = ""
    if os.path.isfile(log):
        txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
    open(os.path.join(out, "_console.txt"), "w", encoding="utf-8", newline="\n").write(txt)

    # 收集 PNG
    shots = 0
    for n in sorted(os.listdir(save)):
        if n.startswith("shot_") and n.endswith(".png"):
            shutil.copy2(os.path.join(save, n), os.path.join(out, n)); shots += 1

    exc = txt.count("An exception occured")
    m = re.search(r"★STORYTEST★ DONE 行=(\d+)", txt)
    # 确认该场景确实应用到目标行
    applied = "line=%d" % a.line
    print("[4/4] 结束信号=%s 异常=%d 行数=%s PNG=%d" % (done, exc, (m.group(1) if m else "?"), shots))
    print("  目标行日志命中(%s)=%s" % (applied, applied in txt))
    print("  产物：%s" % out)
    ok = done and exc == 0
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

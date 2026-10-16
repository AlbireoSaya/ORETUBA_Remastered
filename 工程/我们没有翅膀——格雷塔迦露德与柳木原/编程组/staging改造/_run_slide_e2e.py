# -*- coding: utf-8 -*-
r"""_run_slide_e2e.py —— E2 端到端：**真 tier1 生成物**载入真场景，验证 `!r` 退场按源侧 ms 滑出。

与 `other语义接入\_shot_pairs.py` 同套路（组装单场 → 装配 → 选定拷贝素材 → 起引擎收图），
只多两处：
  1) `--mode` 固定 `tier1`（要的就是**真产出 `dur` 的生成物**）；
  2) `storytest_interval.tjs` 里**额外注入一个 20ms 采样器**（TJS，只读观察 + 导出 PNG）：
     捕捉任何在跑的「滑出」动画（`UIStageAnim[i].hide===true`），逐拍记 `t` 与槽 `x`，
     并在 ≈25% / 55% 进度处各导一张 PNG（`shot_601/602_dialog.png`）⇒ **中间帧可见的证据**。
     ★ 采样器只写在 `build_test\game\storytest_interval.tjs`（**测试 flag，非游戏文件**）；
       **未改 `ui_staging.tjs` / `ui_boot.tjs` / 任何 game\*.tjs**。

用法：
  python -X utf8 编程组\staging改造\_run_slide_e2e.py --scene ot_s03_06e1 --line 181 \
      --out 编程组\staging改造\验收\slide_e2e\<场>
"""
import argparse, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))          # ...\编程组\staging改造
PRG = os.path.dirname(HERE)                                # ...\编程组
PROJ = os.path.dirname(PRG)                                # <proj>
DATA_ROOT = r"E:\ZCode Workspace\Galgame"
RE_ASSET = re.compile(r'story_assets/([A-Za-z0-9_\-\.]+)')

# ★ 注入到 storytest_interval.tjs 的采样器（TJS2；全部 try/catch 包裹，绝不干扰自测主循环）
PROBE_TJS = r'''
// ==== E2 采样器（ISSUE-20261007-05 · 只读观察 + 导图；非游戏逻辑）====
var uxE2Timer = null;
var uxE2Armed = false;
var uxE2T0 = 0;
var uxE2N = 0;
var uxE2Ticks = 0;
var uxE2Shots = 0;
var uxE2Warm = 0;
var uxE2Done = false;
var uxE2Slot = -1;
var uxE2Tot = 0;
function uxE2Now() { try { return 0 + System.getTickCount(); } catch(e) { return 0; } }
function uxE2Shot(n) {
	try { UIStoryWin.redraw(); } catch(e1) { }
	try { UIStoryWin.exportPng("dialog", n); } catch(e2) { }
}
function uxE2Tick() {
	uxE2Ticks++;
	if(uxE2Ticks % 20 == 1) Debug.message("[E2] 心跳 #" + uxE2Ticks + " t=" + uxE2Now() + " armed=" + uxE2Armed);
	if(uxE2Done) return;
	// ★ 预热必须在**对话框屏已建立**之后做（否则 UIStoryWin 为空、导出必失败，滑出时的首张导出极慢）
	if(uxE2Warm < 2) {
		var scr = "";
		try { scr = "" + uiScreenCurrent(); } catch(eS) { scr = ""; }
		if(scr == "dialog") {
			uxE2Warm++;
			var tw = uxE2Now();
			uxE2Shot(596 + uxE2Warm);
			Debug.message("[E2] 预热#" + uxE2Warm + " 用时 " + (uxE2Now() - tw) + "ms");
			return;
		}
	}
	var n = 0;
	try { n = UIStageSlots.count; } catch(e0) { return; }
	if(n <= 0) return;
	var hit = -1;
	for(var i = 0; i < n; i++) {
		var a = null;
		try { a = UIStageAnim[i]; } catch(e1) { a = null; }
		if(a === void || a === null) continue;
		var h = false; try { h = (a.hide === true); } catch(e2) { h = false; }
		if(h) { hit = i; break; }
	}
	if(hit < 0) return;
	if(!uxE2Armed) {
		uxE2Armed = true; uxE2T0 = uxE2Now(); uxE2N = 0; uxE2Slot = hit; uxE2Shots = 0;
		try { uxE2Tot = 0 + UIStageAnim[hit].total; } catch(e3) { uxE2Tot = 0; }
		var tag = ""; try { tag = "" + UIStageAnim[hit].tag; } catch(e3b) { tag = "?"; }
		var fx = -1, tx = -1, w0 = -1;
		try { fx = 0 + UIStageAnim[hit].fx; tx = 0 + UIStageAnim[hit].tx; } catch(e3c) { }
		try { w0 = 0 + UIStageSlots[hit].w; } catch(e3d) { }
		Debug.message("[E2] 捕获真数据滑出：槽" + hit + " tag=" + tag + " total=" + uxE2Tot
			+ "ms fx=" + fx + " tx=" + tx + " 件宽=" + w0);
	}
	var el = uxE2Now() - uxE2T0;
	var x = -99999;
	try { x = 0 + UIStageSlots[uxE2Slot].x; } catch(e4) { x = -99999; }
	var live = 0; try { live = 0 + UIStageAnim.count; } catch(e5) { live = 0; }
	uxE2N++;
	Debug.message("[E2] #" + uxE2N + " t=" + el + "ms 槽" + uxE2Slot + " x=" + x + " live=" + live);
	if(uxE2Shots < 3) {
		// ★ 不看真实时间：按**采样拍数**取帧（每拍 ≈20ms）。**不在 #1 导出**——导出本身要 ~500ms
		//   且会阻塞消息循环；放在 #1 会把整段滑出挡掉。取 #8 / #14 两拍（≈160/280ms，滑出中段）
		//   与收尾一拍 ⇒ 导出的**调用时刻**就落在滑出中段（`exportPng` 取的是调用当帧的画面）。
		var want = false;
		if(uxE2Shots == 0 && uxE2N == 8) want = true;
		else if(uxE2Shots == 1 && uxE2N == 14) want = true;
		else if(uxE2Shots == 2 && (live <= 0 || x <= -20000)) want = true;
		if(want) {
			uxE2Shots++;
			var ts = uxE2Now();
			var xb = x;
			uxE2Shot(600 + uxE2Shots);
			Debug.message("[E2] 导出#" + uxE2Shots + " 于 #" + uxE2N + " x(调用前)=" + xb
				+ " 用时 " + (uxE2Now() - ts) + "ms");
		}
	}
	if(uxE2Shots >= 3) uxE2Done = true;
}
function uxE2Start() {
	if(uxE2Timer !== null) return;
	try {
		uxE2Timer = new Timer(uxE2Tick, '');
		uxE2Timer.interval = 20;
		uxE2Timer.enabled = true;
	} catch(e) { Debug.message("[E2][ERR] Timer 建立失败：" + e.message); return; }
	Debug.message("[E2] 采样器启动（20ms/拍）；typeof(global)=" + typeof(global));
}
uxE2Start();
'''


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--line", type=int, required=True, help="收尾行；须 > 退场 seq（让滑出走完）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=40.0)
    ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    build = os.path.join(PRG, "build_test")
    kstory = os.path.join(PRG, "krkr", "game", "story")

    print("[1/4] 组装剧本（tier1）scene=%s ..." % a.scene)
    shutil.rmtree(kstory, ignore_errors=True)
    os.makedirs(kstory, exist_ok=True)
    r = sh([sys.executable, "-X", "utf8", os.path.join(PRG, "工具", "build_story.py"),
            "--data-root", DATA_ROOT, "--out", os.path.join(PRG, "krkr"),
            "--scenes", a.scene, "--other-semantics", "tier1"])
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[FATAL] build_story 失败"); sys.exit(2)

    print("[2/4] 装配（--storyrun --no-story-assets）...")
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

    print("[2b] 选定拷贝素材 ...")
    txt = open(os.path.join(build, "game", "story", "scene_%s.tjs" % a.scene),
               encoding="utf-8", errors="replace").read()
    names = sorted(set(RE_ASSET.findall(txt)))
    src_assets = os.path.join(PRG, "krkr", "game", "story_assets")
    dst_assets = os.path.join(build, "game", "story_assets")
    os.makedirs(dst_assets, exist_ok=True)
    copied = missing = 0
    for n in names:
        s = os.path.join(src_assets, n)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(dst_assets, n)); copied += 1
        else:
            missing += 1
    print("     引用素材 %d：拷入 %d / 缺失 %d" % (len(names), copied, missing))

    print("[3/4] 写 flag（含 E2 采样器）...")
    with open(os.path.join(build, "game", "storytest_interval.tjs"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("UIStoryTestIntervalMs = %d;\n" % int(a.interval))
        f.write("UIStoryTestMaxLines = %d;\n" % (a.line - 1))
        f.write('UIStoryEntry = "%s";\n' % a.scene)
        f.write("UIDlgCharStep = 100000;\n")
        f.write("function uiDialogStartTyping() { UIDlgTyped = uiDialogCurrentText().length; "
                "UIDlgTyping = false; }\n")
        f.write(PROBE_TJS)

    save = os.path.join(build, "runtime", "savedata")
    os.makedirs(save, exist_ok=True)
    log = os.path.join(save, "krkr.console.log")
    for n in os.listdir(save):
        if n.startswith("shot_") or n == "krkr.console.log":
            try: os.remove(os.path.join(save, n))
            except OSError: pass

    print("[4/4] 启动引擎 ...")
    exe = os.path.join(build, "runtime", "tvpwin32.exe")
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
    time.sleep(1)
    try:
        p.terminate(); time.sleep(2)
        if p.poll() is None: p.kill()
    except Exception:
        pass

    txt = ""
    if os.path.isfile(log):
        txt = open(log, "rb").read().decode("utf-16-le", errors="replace")
    open(os.path.join(out, "_console.txt"), "w", encoding="utf-8", newline="\n").write(txt)
    shots = 0
    for n in sorted(os.listdir(save)):
        if n.startswith("shot_") and n.endswith(".png"):
            shutil.copy2(os.path.join(save, n), os.path.join(out, n)); shots += 1
    exc = txt.count("An exception occured")
    n_probe = len(re.findall(r"\[E2\] #", txt))
    print("     结束=%s 异常=%d PNG=%d ｜ [E2] 采样点 %d" % (done, exc, shots, n_probe))
    print("     产物：%s" % out)
    sys.exit(0 if (done and exc == 0) else 1)


if __name__ == "__main__":
    main()

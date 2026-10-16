# -*- coding: utf-8 -*-
r"""M43 · krkr 侧「进入本章」按钮的**目标导向**自证（复现脚本）

■ 证明什么（不是"没报错"，而是"真的发生了"）
  动作 `flow_enter`（流程图屏 `fc.jump_hit`）三条分支逐条断言：
    ① 无可进入节点（`UIFlowCursor == ""`）→ **明确提示**（含「无可进入节点」）、**不进剧情**；
    ② 光标节点未解锁            → 提示「未解锁」+ 解锁条件、**不进剧情**；
    ③ 光标节点已解锁            → **真的进入 dialog 屏** 且 **该节点被标记已读** 且 **状态已落盘**。
  ③ 走的是**真实点击路径**：`UIScrMouseSink.handleClick(cx, cy)`（= 窗口 `onMouseDown` 内调用的
  同一个函数，坐标取 `fc.jump_hit` 元素的几何中心，**坐标从 layout 数据读，不写死**）。
  ⚠️ 不直接调 `onMouseDown` 的原因：它在 `tourOn` 时提前 return（巡演期间真实鼠标事件被屏蔽），
  那是巡演特有的门禁，不是点击语义本身；`handleClick` 是 `onMouseDown` 去掉门禁后的那一行。

■ 怎么跑（flag 文件机制；命令行参数在本 krkrz 1.4.0.8 读不到，见 README_运行方式.md）
  本脚本镜像 game/assets/runtime 到 `临时\ui_run_m43probe`，把探针体写进
  `game\press_probe.tjs`（startup.tjs 的 `uiInitPressProbe()` 用 `Scripts.execStorage` 执行它，
  时机在 ⑧.5 之后、巡演第一步之前 —— 此时 `UIScrMouseSink`/`stageLayer` 均已就绪），
  再放 `autotour.txt` 让引擎约 45 秒自退。读日志 grep `[UI][M43PROBE]`。

■ 用法
    python _工作\ISSUE-20260923-06_M43_证据\复现脚本\m43_run_krkr_flowenter_probe.py
  退出码 0 ⟺ 日志里 `M43PROBE RESULT=PASS`（三条分支全过）。
"""
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # …\UI组
KRKR = os.path.join(UI, "krkr")
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))            # …\wt-m43-chapter
RUN = os.path.join(WT, "临时", "ui_run_m43probe")

# ── 探针体（TJS2；**不写死任何坐标**，元素矩形一律读 UILayoutData）──────────────
PROBE = r'''// ★ M43 探针（由 _工作\ISSUE-20260923-06_M43_证据\复现脚本\m43_run_krkr_flowenter_probe.py 生成）
//   目标导向断言：动作 flow_enter 的三条分支。只读 layout 数据，不写死坐标。
function m43ElRect(sid, elId)
{
	if(UILayoutData.screens[sid] === void) return null;
	var els = UILayoutData.screens[sid].elements;
	for(var i = 0; i < els.count; i++)
		if(("" + els[i].id) == ("" + elId)) return els[i];
	return null;
}
function m43NodeIds()
{
	var out = [];
	for(var i = 0; i < UIFlowData.nodes.count; i++) out.push("" + UIFlowData.nodes[i].id);
	return out;
}
function m43FirstLocked()
{
	var ids = m43NodeIds();
	for(var i = 0; i < ids.count; i++)
		if(uiFlowStateOf(ids[i]) == "locked") return ids[i];
	return "";
}
// ★ 挑一个「可前往但**尚未**已读」的节点 —— 这样 ③ 的「已读」才能看到 false -> true 的真实翻转
//   （若拿根节点 N01，它首次运行即已标记已读，断言就退化成恒真）
function m43FirstAvailableUnvisited()
{
	var ids = m43NodeIds();
	for(var i = 0; i < ids.count; i++)
		if(uiFlowStateOf(ids[i]) == "available" && UIFlowVisited[ids[i]] !== true) return ids[i];
	return "";
}
function m43Verdict(name, ok, detail)
{
	Debug.message("[UI][M43PROBE] " + (ok ? "PASS" : "FAIL") + "  " + name + "  —— " + detail);
	return ok;
}
var M43AllOK = true;

// ── 准备：按真实入口打开流程图（open_flowchart 会 push 屏并置光标）──────────────
uiFlowEnsureReady();
var openRes = uiActionDispatch("open_flowchart", -1);
var scrAfterOpen = uiScreenCurrent();
M43AllOK = m43Verdict("前置：open_flowchart 真的进了 flowchart 屏",
	(scrAfterOpen == "flowchart"),
	"screen=" + scrAfterOpen + " ｜ 光标=" + UIFlowCursor + " ｜ 当前节点=" + UIFlowCurrent
	+ " ｜ msg=" + openRes.msg) && M43AllOK;

var rect = m43ElRect("flowchart", "fc.jump_hit");
var rAction = (rect === null) ? "(无该元素)" : ("" + rect.action);
M43AllOK = m43Verdict("前置：fc.jump_hit 的 action 就是 flow_enter",
	(rAction == "flow_enter"),
	"action=" + rAction + " ｜ 矩形=" + ((rect === null) ? "?" : (rect.x + "," + rect.y + " "
	+ rect.w + "x" + rect.h))) && M43AllOK;

// ── ① 无可进入节点 ────────────────────────────────────────────────────────────
var keepCursor = UIFlowCursor;
UIFlowCursor = "";
var r1 = uiActionDispatch("flow_enter", -1);
var ok1 = (uiScreenCurrent() == "flowchart") && (("" + r1.msg).indexOf("无可进入节点") >= 0);
M43AllOK = m43Verdict("① 无光标节点：明确提示且不进剧情", ok1,
	"screen=" + uiScreenCurrent() + " ｜ msg=" + r1.msg) && M43AllOK;

// ── ①b 光标指向**不存在的节点**（防御分支；★ 一审 Minor-3 补测）────────────────
UIFlowCursor = "NXX";                        // 保证不与任何真实节点 id 相同
var r1b = uiActionDispatch("flow_enter", -1);
var ok1b = (uiScreenCurrent() == "flowchart") && (("" + r1b.msg).indexOf("无可进入节点") >= 0);
M43AllOK = m43Verdict("①b 节点不存在：明确提示且不进剧情", ok1b,
	"cursor=NXX ｜ screen=" + uiScreenCurrent() + " ｜ msg=" + r1b.msg) && M43AllOK;
UIFlowCursor = keepCursor;

// ── ② 未解锁节点 ──────────────────────────────────────────────────────────────
var locked = m43FirstLocked();
if(locked == "")
{
	M43AllOK = m43Verdict("② 未解锁节点：提示解锁条件且不进剧情", false,
		"没有找到任何 locked 节点（前置不成立，无法证明该分支）") && M43AllOK;
}
else
{
	UIFlowCursor = locked;
	var beforeV = (UIFlowVisited[locked] === true);
	var r2 = uiActionDispatch("flow_enter", -1);
	var ok2 = (uiScreenCurrent() == "flowchart") && (("" + r2.msg).indexOf("未解锁") >= 0)
		&& (UIFlowVisited[locked] !== true) && (beforeV === false);
	M43AllOK = m43Verdict("② 未解锁节点：提示解锁条件且不进剧情", ok2,
		"节点=" + locked + " ｜ screen=" + uiScreenCurrent() + " ｜ msg=" + r2.msg
		+ " ｜ 该节点已读=" + UIFlowVisited[locked]) && M43AllOK;
}

// ── ③ 已解锁节点：**真实点击路径**（元素几何中心 → handleClick）─────────────────
UIFlowCursor = keepCursor;
var target = m43FirstAvailableUnvisited();
if(target == "") target = UIFlowCursor;
UIFlowCursor = target;          // ★ 探针要按「真实用户先选中该节点」的前置来点按钮
var visitedBefore = (UIFlowVisited[target] === true);
var scrBefore = uiScreenCurrent();
var cx = rect.x + Math.floor(rect.w / 2);
var cy = rect.y + Math.floor(rect.h / 2);
Debug.message("[UI][M43PROBE] 合成点击 " + cx + "," + cy + "（fc.jump_hit 中心）");
UIScrMouseSink.handleClick(cx, cy);
var scrAfter = uiScreenCurrent();
var visitedAfter = (UIFlowVisited[target] === true);
var ok3 = (scrBefore == "flowchart") && (scrAfter == "dialog") && visitedAfter
	&& (visitedBefore === false) && (UIFlowCurrent == target);
M43AllOK = m43Verdict("③ 点 fc.jump_hit 中心：进入 dialog 屏 且 该节点由未读变已读", ok3,
	"节点=" + target + " ｜ screen " + scrBefore + " -> " + scrAfter
	+ " ｜ 已读 " + visitedBefore + " -> " + visitedAfter + " ｜ 当前节点=" + UIFlowCurrent) && M43AllOK;

// ── ④ 状态已落盘（读回状态文件里的 visited= 行）────────────────────────────────
var savedVisited = "(未读到)";
try
{
	var a = new Array();
	a.load(UIFlowStatePath);
	for(var j = 0; j < a.count; j++)
		if(("" + a[j]).indexOf("visited=") == 0) { savedVisited = "" + a[j]; break; }
}
catch(eL) { savedVisited = "(load 失败：" + eL.message + ")"; }
M43AllOK = m43Verdict("④ 状态文件里含该节点", (("" + savedVisited).indexOf(target) >= 0),
	"state=" + UIFlowStatePath + " ｜ " + savedVisited) && M43AllOK;

Debug.message("[UI][M43PROBE] RESULT=" + (M43AllOK ? "PASS" : "FAIL"));
'''


def main():
    if os.path.isdir(RUN):
        shutil.rmtree(RUN, ignore_errors=True)
    os.makedirs(RUN)
    for sub in ("game", "runtime"):
        shutil.copytree(os.path.join(KRKR, sub), os.path.join(RUN, sub))
    shutil.copytree(os.path.join(KRKR, "assets"), os.path.join(RUN, "game", "assets"))
    # 干净起点：清掉上一次的状态文件（否则 visited 会被上一次巡演污染）
    sd = os.path.join(RUN, "runtime", "savedata")
    os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        try:
            os.remove(os.path.join(sd, f))
        except OSError:
            pass
    io.open(os.path.join(RUN, "game", "press_probe.tjs"), "w",
            encoding="utf-8", newline="\n").write(PROBE)
    io.open(os.path.join(RUN, "game", "autotour.txt"), "w",
            encoding="utf-8", newline="\n").write("autotour\n")
    print("[run] %s" % RUN)
    subprocess.Popen([os.path.join(RUN, "runtime", "tvpwin32.exe"), os.path.join(RUN, "game")],
                     cwd=os.path.join(RUN, "runtime"))
    print("[run] 引擎已启动（约 45 秒自退）；请稍候再读日志。")
    return 0


def read_log():
    log = os.path.join(RUN, "runtime", "savedata", "krkr.console.log")
    if not os.path.exists(log):
        print("日志尚未生成：%s" % log)
        return 1
    txt = io.open(log, "rb").read().decode("utf-16-le", "replace")
    for line in txt.splitlines():
        if "[UI][M43PROBE]" in line:
            print("  " + line.strip())
    m = re.search(r"M43PROBE\] RESULT=(\w+)", txt)
    verdict = m.group(1) if m else "(未找到 RESULT=)"
    print("\n判定：RESULT=%s" % verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    if "--read" in sys.argv:
        sys.exit(read_log())
    sys.exit(main())
# -*- coding: utf-8 -*-
"""E2（第 2 步）复现脚本：给 krkr/game/ui_screens.tjs 加「current 环的内存副本注入」巡演件

为什么需要它（不是绕开 states 预设，而是独立的一支负向对照）：
  `--preset states` 依赖屏数据里的 `flags_default["fc.state.<NNNN>"]` 才能点亮叠加件，
  而那份数据目前**引擎加载不了**（生成器把带点的键写成了 TJS2 不接受的 `"k": v` 形式，
  见 `e2_run_states_patched_mirror.py` 的说明）⇒ 环的**绘制路径**要在别的屏上取证。
  本件在**内存副本**上把 3 个节点底图标成 `current`（2 个可见 + 1 个 `vis_when` 改成
  不可达值 ⇒ **应当不画环**），下一步读上一帧的环计数并还原 —— 与 M06/M08 的
  「内存副本 + 变体自证」同一套路，**不写盘、不碰数据文件**。

用法：python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_patch_ui_screens_flowring.py"
幂等：重复运行会在断言处失败（说明已打过）。
"""
import io
import os

P = os.path.join("krkr", "game", "ui_screens.tjs")

FUNCS = r'''
// ------------------------------------------------------------
// ★★ ISSUE-20260928-02（第 2 步）· `current` 高亮环的**内存副本注入**（巡演负向对照）★★
//   为什么需要：环的绘制入口在 `ui_flow_layer.tjs`（post-pass），要证明它「画了、画在哪、
//   画了几个、哪些**不该**画」；本体屏数据（交付样例 screen1/screen2）**不含** `flow_state`
//   （冻结 §一.1：缺省不写 ⇒ 无环），而含五态声明的 `--preset states` 屏数据当前**引擎
//   加载不了**（生成器缺陷，见 E2 报告「阻塞项」）⇒ 在本巡演步骤里做一支**独立**取证：
//   · `set`：把 3 个节点底图**在内存里**标成 `flow_state="current"`（2 个保持可见，
//     第 3 个把 `vis_when` 改成**不可达层名**）——下一步的帧就会画 2 个环、跳过 1 个；
//   · `clear`：先读**上一帧**的环计数（由 ui_flow_layer.tjs 记）+ 打 PASS/FAIL 判词，
//     再把内存副本还原（`flow_state` / `vis_when` 逐字段回填）。
//   ★ 与 M06/M08 的「内存副本夹具」同一套路：**不写盘**，只改运行期对象；`clear` 一定还原。
//   ★ 预期：2 画 / 1 跳过 —— 后者是**冻结 §四.5「命中与绘制恒同集」**的自证
//     （`vis_when` 不满足的节点既不可点、也不画环）。
// ------------------------------------------------------------
var UIScrFlowRingBackup = null;      // Array<Dictionary>：{el, prev, hasVisw, prevVisw}

function uiScreenFlowRingNodeList(sc)
{
	var out = [];
	for(var i = 0; i < sc.elements.count; i++)
	{
		var el = sc.elements[i];
		if(el.kind != "image") continue;
		var sid = "" + el.id;
		if(sid.indexOf("fc.node.") != 0) continue;
		if(sid.indexOf("_") >= 0) continue;      // 只要节点**底图**（不带 _tx/_hit/_dim/_new）
		out.push(el);
	}
	return out;
}

// 找一个**不等于**当前层值的层名（用于把第 3 个节点改成不可见；不写死任何具体层名）
function uiScreenFlowRingOtherLayer(sc, cur)
{
	var lflag = "";
	if(UIScrFlowLinksOK) lflag = uiFlowLinkLayerFlagName(sc);
	if(lflag == "") return "★not-a-layer★";
	for(var i = 0; i < sc.elements.count; i++)
	{
		var el = sc.elements[i];
		if(("" + el.vis_flag) != lflag) continue;
		var w = el.vis_when;
		if(w === void || w === null) continue;
		if(("" + w) != cur) return "" + w;
	}
	return "★not-a-layer★";
}

function uiScreenSyntheticFlowRing(spec)
{
	var mode = "" + spec;
	var sid = uiScreenCurrent();
	if(!uiScreenExists(sid) || sid != "flowchart")
		return "★FLOWRING-SKIP★ 当前屏=" + sid + "（本步骤只在流程图屏有效，跳过）";
	var sc = UILayoutData.screens[sid];

	if(mode == "clear")
	{
		// ★ 顺序要紧：先读**上一帧**的环计数（那是 set 之后那一帧画的），再还原内存副本
		var drawn = UIScrFlowLayerOK ? UIFlowLayerRingDrawn : -1;
		var skip  = UIScrFlowLayerOK ? UIFlowLayerRingSkip : -1;
		var n = 0;
		if(UIScrFlowRingBackup !== null)
		{
			for(var i = 0; i < UIScrFlowRingBackup.count; i++)
			{
				var b = UIScrFlowRingBackup[i];
				b.el.flow_state = b.prev;
				if(b.hasVisw === true) b.el.vis_when = b.prevVisw;
				n++;
			}
			UIScrFlowRingBackup = null;
		}
		var ok = (drawn == 2) && (skip == 1);
		return "★FLOWRING★ " + (ok ? "PASS" : "FAIL")
			+ "  内存注入=3 件（2 可见 + 1 隐藏）"
			+ "  上一帧环实画=" + drawn + "（期望 2）  跳过=" + skip
			+ "（期望 1：隐藏节点**不画环** ⇒ 冻结 §四.5 命中与绘制同集）"
			+ "  已还原 " + n + " 件"
			+ "  （判据：`ui_flow_layer.tjs` 的 rings 行；本步骤不写盘）";
	}

	// ---- set：内存副本注入 ----
	var nodes = uiScreenFlowRingNodeList(sc);
	if(nodes.count < 3)
		return "★FLOWRING-SKIP★ 本屏节点底图只找到 " + nodes.count + " 件（<3），跳过";
	var cur = "";
	if(UIScrFlowLinksOK)
	{
		var lf = uiFlowLinkLayerFlagName(sc);
		if(lf != "") cur = uiScreenFlagGet(lf);
	}
	var other = uiScreenFlowRingOtherLayer(sc, cur);
	UIScrFlowRingBackup = [];
	var ids = "";
	for(var k = 0; k < 3; k++)
	{
		var el = nodes[k];
		var b = %[ el: el, prev: el.flow_state, hasVisw: false, prevVisw: void ];
		el.flow_state = "current";
		if(k == 2)
		{
			// 第 3 件：**可见性守卫的负向对照** —— 把它的 vis_when 改成不可达层名
			b.hasVisw = true;
			b.prevVisw = el.vis_when;
			el.vis_when = other;
		}
		UIScrFlowRingBackup.push(b);
		ids = ids + ((k > 0) ? "," : "") + ("" + el.id);
	}
	return "★FLOWRING-SET★ 已在**内存**里注入 3 件 current（不写盘）：" + ids
		+ "  ｜ 第 3 件 vis_when " + ((UIScrFlowLayerOK) ? "改为不可达层名" : "改为不可达值")
		+ "「" + other + "」（当前层值=「" + ((cur == "") ? "(空)" : cur) + "」）"
		+ "  ｜ 下一帧应画 2 个环（节点矩形内缩 1px / r=16 / w=3 / @palette.node_current，"
		+ "post-pass 画在全部节点之上）";
}
'''

REP1_OLD = '''// ★ M47：合成拖动（巡演验收用）—— spec 形如 `<hit 元素id>:<目标值>`'''
REP1_NEW = FUNCS.strip('\n') + '\n\n' + REP1_OLD

REP2_OLD = '''	else if(st.kind == "flowclick") // ★ 第 2 步：走真实点击入口切层（命中参数 → flow_layer）
	{
		note = uiScreenSyntheticFlowClick(st.v);
	}'''
REP2_NEW = REP2_OLD + '''
	else if(st.kind == "flowring") // ★ 第 2 步：current 环的内存副本注入（含「隐藏节点不画环」负向对照）
	{
		note = uiScreenSyntheticFlowRing(st.v);
	}'''

REP3_OLD = '''	%[ kind: "flowstate", v: "1",         label: "★运行态★ 只读断言：回主干后（fc_layer==main ⇒ 连线恢复）" ],'''
REP3_NEW = REP3_OLD + '''
	//   ④ `flowring`＝**内存副本注入**（不写盘）：把 3 个节点底图标成 `current`（2 可见 +
	//      1 个 `vis_when` 改成不可达层名）⇒ 下一步的帧应画 2 个环、跳过 1 个；`clear` 步
	//      先读上一帧环计数打 `★FLOWRING★ PASS|FAIL`，再还原内存副本。
	//      为什么另起一支：交付样例屏**不含** `flow_state`（缺省不写 ⇒ 无环），含五态的
	//      `--preset states` 屏数据当前**引擎加载不了**（生成器把带点的键写成 TJS2 不接受
	//      的 `"k": v`，见 E2 报告阻塞项）⇒ 环的绘制路径需要一支独立取证 + 负向对照。
	%[ kind: "flowring", v: "set",       label: "★运行态★ 内存注入：3 件 current（2 可见 + 1 隐藏）" ],
	%[ kind: "flowring", v: "clear",     label: "★运行态★ 断言环计数（2 画 / 1 跳过）并还原内存副本" ],'''


def main():
    s = io.open(P, encoding="utf-8", newline="").read()
    for label, old, new in (
        ("funcs", REP1_OLD, REP1_NEW),
        ("step kind", REP2_OLD, REP2_NEW),
        ("tour steps", REP3_OLD, REP3_NEW),
    ):
        n = s.count(old)
        assert n == 1, "%s : found %d (expected 1)" % (label, n)
        s = s.replace(old, new)
        print("ok:", label)
    io.open(P, "w", encoding="utf-8", newline="").write(s)
    print("patched:", P)


if __name__ == "__main__":
    main()

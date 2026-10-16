# -*- coding: utf-8 -*-
"""E2（第 2 步）复现脚本：把「运行态 / 层」的巡演验收件打进 krkr/game/ui_screens.tjs

幂等性：全部替换都是**精确单次匹配**，重复运行第二次即断言失败（= 已打过）。
用法：python _工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_patch_ui_screens_tour.py
"""
import io
import os

P = os.path.join("krkr", "game", "ui_screens.tjs")

FUNCS = r'''
// ------------------------------------------------------------
// ★★ ISSUE-20260928-02（第 2 步）· 流程图「运行态 / 层」的巡演验收件 ★★
//   两个步骤类型（见 UIScrTourSteps 的「运行态」块）：
//     · `flowstate` —— **只读**断言：读当前屏数据报「节点 `flow_state` 分布 / 连线 `state`
//       档位分布 / 应画 `current` 环条数 / 层 flag 当前值」。对 `--preset states` 即
//       「五档节点 + 三档连线同屏」的自证；对默认预设即「无 `flow_state` ⇒ 0 环」的负向自证。
//     · `flowclick` —— **走真实点击入口**（按下 -> 抬起 -> `uiScreenClick` 命中 -> 参数 ->
//       `uiActionDispatch`，与 `handleClick` / M47 合成点击同批入口）去点「层切换热区」
//       （数据里 `action=="flow_layer"` 且 `layer==<v>` 的那个 hit）。
//       · 本屏数据**没有该层元素** ⇒ **明确跳过**（`★FLOWLAYER-SKIP★`）且**不做任何状态变更**
//         —— 默认 / `states` / `ref150` / `screen2` 预设本就没有番外独立层元素，跳过才是对的；
//         `frag` 预设才会真切换。
//       · 判词 `★FLOWLAYER★ PASS|FAIL` 直接落进巡演日志（可机检）。
//   为什么走真实点击而不是直接写 flag：本步骤要证明的是「**热区 -> 命中参数 -> 动作 -> flag ->
//   重绘/命中集**」这条链通着；直接写 flag 只能证明 flag 可写（那是对实现的复述）。
// ------------------------------------------------------------
function uiScreenFlowStateLine()
{
	var sid = uiScreenCurrent();
	if(!uiScreenExists(sid) || sid != "flowchart")
		return "★FLOWSTATE-SKIP★ 当前屏=" + sid + "（本断言只在流程图屏有效，跳过）";
	var sc = UILayoutData.screens[sid];
	var els = sc.elements;

	// ① 节点 `flow_state` 分布（只有节点底图带该字段；缺省不写 = available，冻结 §一.1）
	var stKeys = ["locked", "available", "visited", "current", "new"];
	var stCnt  = [0, 0, 0, 0, 0];
	var curIds = [];
	var unset  = 0;
	for(var i = 0; i < els.count; i++)
	{
		var el = els[i];
		if(el.kind != "image") continue;
		var st = el.flow_state;
		if(st === void || st === null || ("" + st) == "") { unset++; continue; }
		var sv = "" + st;
		var found = false;
		for(var k = 0; k < stKeys.count; k++)
		{
			if(stKeys[k] == sv) { stCnt[k]++; found = true; break; }
		}
		if(!found) unset++;
		if(sv == "current") curIds.push("" + el.id);
	}
	var withState = stCnt[0] + stCnt[1] + stCnt[2] + stCnt[3] + stCnt[4];

	// ② 连线 `state` 档位分布（顶层键 links；色/宽/箭头已由生成器解析，两端不判配色）
	var lkCnt = [0, 0, 0];
	if(sc.links !== void && sc.links !== null && sc.links.count !== void)
	{
		for(var m = 0; m < sc.links.count; m++)
		{
			var sv2 = "" + sc.links[m].state;
			if(sv2 == "normal") lkCnt[0]++;
			else if(sv2 == "visited") lkCnt[1]++;
			else if(sv2 == "noroute") lkCnt[2]++;
		}
	}
	var lkTotal = lkCnt[0] + lkCnt[1] + lkCnt[2];

	// ③ 层 flag 当前值（flag 名从数据推导；连线模块缺失时用层模块的兜底名）
	var lflag = "";
	if(UIScrFlowLinksOK) lflag = uiFlowLinkLayerFlagName(sc);
	if(lflag == "" && UIScrFlowLayerOK) lflag = UIFlowLayerFlagFallback;
	var lval = (lflag == "") ? "(无层 flag)"
		: (lflag + "=" + ((uiScreenFlagGet(lflag) == "") ? "(空)" : uiScreenFlagGet(lflag)));

	var cur3 = "";
	for(var c = 0; c < curIds.count && c < 3; c++) cur3 = cur3 + ((c > 0) ? "," : "") + curIds[c];

	return "★FLOWSTATE★ 屏=" + sid + " 元素=" + els.count
		+ " ｜ flow_state：有字段 " + withState + " 件（"
		+ stKeys[0] + "=" + stCnt[0] + " " + stKeys[1] + "=" + stCnt[1] + " "
		+ stKeys[2] + "=" + stCnt[2] + " " + stKeys[3] + "=" + stCnt[3] + " "
		+ stKeys[4] + "=" + stCnt[4] + "）｜ 无该字段 " + unset + " 件（缺省=available）"
		+ " ｜ 应画 current 环 " + stCnt[3] + " 个" + ((cur3 == "") ? "" : ("[" + cur3 + "]"))
		+ " ｜ 连线 " + lkTotal + " 条（normal=" + lkCnt[0] + " visited=" + lkCnt[1] + " noroute=" + lkCnt[2] + "）"
		+ " ｜ 层 " + lval
		+ " ｜ 环实画（上一帧）=" + (UIScrFlowLayerOK ? ("" + UIFlowLayerRingDrawn) : "(模块缺失)");
}

function uiScreenSyntheticFlowClick(spec)
{
	var layer = "" + spec;
	var sid = uiScreenCurrent();
	if(!uiScreenExists(sid) || sid != "flowchart")
		return "★FLOWLAYER-SKIP★ 当前屏=" + sid + "（本步骤只在流程图屏有效，跳过）";
	var sc = UILayoutData.screens[sid];

	// 层 flag 名（数据推导优先）
	var lflag = "";
	if(UIScrFlowLinksOK) lflag = uiFlowLinkLayerFlagName(sc);
	if(lflag == "" && UIScrFlowLayerOK) lflag = UIFlowLayerFlagFallback;
	if(lflag == "")
		return "★FLOWLAYER-SKIP★ 本屏元素 vis_flag 全为空（无层 flag），跳过";

	// ① 目标层守卫：本屏数据里有没有该层的元素（`vis_when == layer` 且带层 flag）
	var layerEls = 0;
	for(var i = 0; i < sc.elements.count; i++)
	{
		var e0 = sc.elements[i];
		if(("" + e0.vis_flag) != lflag) continue;
		if(("" + e0.vis_when) == layer) layerEls++;
	}
	if(layerEls <= 0)
		return "★FLOWLAYER-SKIP★ 本屏数据无「" + layer + "」层元素 ⇒ 跳过（**不做任何状态变更**；"
			+ "默认/states/ref150/screen2 预设没有番外独立层元素，只有 --preset frag 才有）";

	// ② 找该层的层切换热区
	var hit = null;
	for(var j = 0; j < sc.elements.count; j++)
	{
		var e1 = sc.elements[j];
		if(e1.kind != "hit") continue;
		if(("" + e1.action) != "flow_layer") continue;
		var lv = e1.layer;
		if(lv === void || lv === null) continue;
		if(("" + lv) != layer) continue;
		hit = e1;
		break;
	}
	if(hit === null)
		return "★FLOWLAYER-SKIP★ 本屏有「" + layer + "」层元素（" + layerEls
			+ " 件）但**没有** layer=\"" + layer + "\" 的 flow_layer 热区 ⇒ 跳过";

	// ③ 可见性守卫（与真实命中**同一谓词**）：当前不可见 ⇒ 跳过（不伪造点击）
	if(!uiScreenElementVisible(hit))
		return "★FLOWLAYER-SKIP★ " + hit.id + " 当前不可见（vis_flag=" + lflag
			+ " vis_when=" + hit.vis_when + "＜当前层=" + uiScreenFlagGet(lflag) + "）⇒ 跳过";

	// ④ 真实点击路径（与 handleClick / M47 合成点击同批入口）
	var hr = uiWidgetRect(hit);
	var cx = hr.x + Math.floor(hr.w / 2);
	var cy = hr.y + Math.floor(hr.h / 2);
	var before = uiScreenFlagGet(lflag);
	uiScreenPressUpdate(cx, cy);
	var dragged = (UIScrDragSlider != "");
	uiScreenPressClear();
	var act = "", idx = -1;
	try
	{
		var r = uiScreenClick(void, cx, cy);
		if(r !== void && r !== null)
		{
			act = (r.action === void || r.action === null) ? "" : ("" + r.action);
			idx = (r.index === void) ? -1 : r.index;
		}
	}
	catch(eC) { act = ""; }
	var hitParam = uiScreenHitLayer();
	var msg = "";
	if(act != "")
	{
		try
		{
			var res = uiActionDispatch(act, idx);
			msg = (res !== void && res.msg !== void) ? ("" + res.msg) : "";
		}
		catch(eA) { msg = "分发异常：" + eA.message; }
	}
	var after = uiScreenFlagGet(lflag);
	var ok = (act == "flow_layer") && (after == layer);
	return "★FLOWLAYER★ " + (ok ? "PASS" : "FAIL")
		+ "  目标层=" + layer + "  点击热区=" + hit.id + " 中心=" + cx + "," + cy
		+ "  命中动作=" + ((act == "") ? "(空)" : act)
		+ "  命中参数 layer=" + ((hitParam == "") ? "(空)" : hitParam)
		+ "  层值 " + ((before == "") ? "(空)" : before) + " -> " + ((after == "") ? "(空)" : after)
		+ "  拖动=" + (dragged ? ("启动(" + UIScrDragSlider + ")") : "未启动")
		+ "  重绘=下一步 tourTick（本步骤返回后由巡演统一 redraw）"
		+ (msg == "" ? "" : ("  msg=" + msg));
}
'''

REP1_OLD = '''// ★ M47：合成拖动（巡演验收用）—— spec 形如 `<hit 元素id>:<目标值>`'''
REP1_NEW = FUNCS.strip('\n') + '\n\n' + REP1_OLD

REP2_OLD = '''	else if(st.kind == "galattach") // ★ M1：外壳在四个承载屏下的绘制 + 命中复用
	{
		note = uiScreenSyntheticGalAttach(st.v);
	}'''
REP2_NEW = REP2_OLD + '''
	else if(st.kind == "flowstate") // ★ 第 2 步：流程图运行态只读断言（五态/三档/环数/层值）
	{
		note = uiScreenFlowStateLine();
	}
	else if(st.kind == "flowclick") // ★ 第 2 步：走真实点击入口切层（命中参数 → flow_layer）
	{
		note = uiScreenSyntheticFlowClick(st.v);
	}'''

REP3_OLD = '''	%[ kind: "action", v: "open_flowchart", label: "剧情流程图占位" ],'''
REP3_NEW = REP3_OLD + '''
	// ★★ ISSUE-20260928-02（第 2 步）· 流程图「运行态 / 层」巡演块 ★★
	//   位置有意放在 `open_flowchart` **之后**：此刻屏 = flowchart，且后续各屏（ending /
	//   loading / title）与末尾的 M46 负向对照（依赖 title 屏）都不受影响。
	//   ① `flowstate`＝**只读**断言，读**当前屏数据**报：
	//      节点 `flow_state` 分布 / 连线 `state` 档位分布 / 应画 `current` 环条数 / 层 flag 值。
	//      `--preset states` ⇒ 五档节点 + 三档连线同屏（应画环 3 个）；默认预设 ⇒ 无 `flow_state`、0 环。
	//   ② `flowclick`＝**真实点击**层切换热区（命中 → `UIScrHitLayer` → `flow_layer` → flag）：
	//      数据里没有该层元素时**明确跳过**（`★FLOWLAYER-SKIP★`，不做任何状态变更）；
	//      `--preset frag`（可配 `run_autotour.bat frag1` 强制层）才会真切换并打出
	//      `★FLOWLAYER★ PASS|FAIL`。
	//   ③ 两态由图见证：本块每一步之后的 PNG 由 `tourRecord` 导出（`shot_NN_flowchart.png`）
	//      —— `fc_layer=main` 有连线、`fc_layer=frag1` 无连线。
	%[ kind: "screen",    v: "flowchart", label: "★运行态★ 流程图（层/运行态随预设数据而定）" ],
	%[ kind: "flowstate", v: "1",         label: "★运行态★ 只读断言：flow_state 分布 + 连线档位 + 应画环数 + 层值" ],
	%[ kind: "flowclick", v: "frag1",     label: "★运行态★ 真实点击：层入口热区（layer=frag1 ⇒ 切独立层）" ],
	%[ kind: "flowstate", v: "1",         label: "★运行态★ 只读断言：切层后（独立层：连线 0 / 主干不可见）" ],
	%[ kind: "flowclick", v: "main",      label: "★运行态★ 真实点击：返回主干热区（layer=main ⇒ 回主干）" ],
	%[ kind: "flowstate", v: "1",         label: "★运行态★ 只读断言：回主干后（fc_layer==main ⇒ 连线恢复）" ],'''


def main():
    s = io.open(P, encoding="utf-8").read()
    for label, old, new in (
        ("funcs", REP1_OLD, REP1_NEW),
        ("step kinds", REP2_OLD, REP2_NEW),
        ("tour block", REP3_OLD, REP3_NEW),
    ):
        n = s.count(old)
        assert n == 1, "%s : found %d (expected 1)" % (label, n)
        s = s.replace(old, new)
        print("ok:", label)
    io.open(P, "w", encoding="utf-8", newline="").write(s)
    print("patched:", P)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""E2（第 2 步）复现脚本：修正 `flowring` 步骤的**判词口径**（改为相对基线的增量）

起因（states 预设实机轮）：被判 `★FLOWRING★ FAIL  上一帧环实画=4（期望 2）` ——
    屏上本来就有 2 个 `flow_state=="current"` 的节点（states 预设），叠上注入的 2 个可见节点
    ⇒ 实画 4 个**完全正确**；错的是判词把「期望」写成了绝对数 2。
修法：`set` 步先记**基线**（屏上已有几个 current、其中几个不可见），`clear` 步按
    `期望实画 = 基线可见数 + 2`、`期望跳过 = 基线不可见数 + 1` 判定。

用法：python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_fix_flowring_verdict.py"
"""
import io
import os

P = os.path.join("krkr", "game", "ui_screens.tjs")
MARK = "var UIScrFlowRingBackup = null;      // Array<Dictionary>：{el, prev, hasVisw, prevVisw}"

NEW_STATE = (MARK + "\n"
             + "var UIScrFlowRingBase = -1;        // set 步记下的**基线**：屏上原有几个 current\n"
             + "var UIScrFlowRingBaseSkip = -1;    // 基线里**不可见**（因而本就不画环）的几个\n")

OLD_CLEAR = """		var ok = (drawn == 2) && (skip == 1);
		return "★FLOWRING★ " + (ok ? "PASS" : "FAIL")
			+ "  内存注入=3 件（2 可见 + 1 隐藏）"
			+ "  上一帧环实画=" + drawn + "（期望 2）  跳过=" + skip
			+ "（期望 1：隐藏节点**不画环** ⇒ 冻结 §四.5 命中与绘制同集）"
			+ "  已还原 " + n + " 件"
			+ "  （判据：`ui_flow_layer.tjs` 的 rings 行；本步骤不写盘）";"""

NEW_CLEAR = """		// ★ 判词口径 = **增量**，不是绝对数：屏上原有 N 个 current（states 预设里有 2 个）
		//   是**数据**，注入的 3 件是**本次增量**；首版写成「期望恒为 2/1」⇒ 在 states 预设
		//   上真画了 4 个却判 FAIL（错的是判词，不是机制 —— 实机轮已暴露并修正）。
		var eb = (UIScrFlowRingBase < 0) ? 0 : UIScrFlowRingBase;
		var ebs = (UIScrFlowRingBaseSkip < 0) ? 0 : UIScrFlowRingBaseSkip;
		var wantDrawn = eb + 2;
		var wantSkip  = ebs + 1;
		var ok = (drawn == wantDrawn) && (skip == wantSkip);
		return "★FLOWRING★ " + (ok ? "PASS" : "FAIL")
			+ "  内存注入=3 件（2 可见 + 1 隐藏）"
			+ "  基线（注入前）=" + eb + " 个 current（其中不可见 " + ebs + "）"
			+ "  上一帧环实画=" + drawn + "（期望 基线+" + 2 + "=" + wantDrawn + "）"
			+ "  跳过=" + skip + "（期望 基线不可见+" + 1 + "=" + wantSkip
			+ "：隐藏节点**不画环** ⇒ 冻结 §四.5 命中与绘制同集）"
			+ "  已还原 " + n + " 件"
			+ "  （判据：`ui_flow_layer.tjs` 的 rings 行；本步骤不写盘）";"""

OLD_SET = """	var nodes = uiScreenFlowRingNodeList(sc);
	if(nodes.count < 3)
		return "★FLOWRING-SKIP★ 本屏节点底图只找到 " + nodes.count + " 件（<3），跳过";"""

NEW_SET = """	var nodes = uiScreenFlowRingNodeList(sc);
	if(nodes.count < 3)
		return "★FLOWRING-SKIP★ 本屏节点底图只找到 " + nodes.count + " 件（<3），跳过";

	// ★ 先记基线（注入前）：屏上原有几个 `flow_state=="current"`、其中几个不可见
	//   —— 判词要按**增量**判（见 clear 步注释：首版写成绝对数，在 states 预设上误判）。
	UIScrFlowRingBase = 0;
	UIScrFlowRingBaseSkip = 0;
	for(var b0 = 0; b0 < sc.elements.count; b0++)
	{
		var e2 = sc.elements[b0];
		if(e2.kind != "image") continue;
		var s2 = e2.flow_state;
		if(s2 === void || s2 === null || ("" + s2) != "current") continue;
		UIScrFlowRingBase = UIScrFlowRingBase + 1;
		if(!uiScreenElementVisible(e2)) UIScrFlowRingBaseSkip = UIScrFlowRingBaseSkip + 1;
	}"""


def main():
    s = io.open(P, encoding="utf-8", newline="").read()
    assert s.count(MARK) == 1, "MARK %d" % s.count(MARK)
    s = s.replace(MARK, NEW_STATE)
    for label, old, new in (("clear 判词", OLD_CLEAR, NEW_CLEAR), ("set 基线", OLD_SET, NEW_SET)):
        n = s.count(old)
        assert n == 1, "%s : %d" % (label, n)
        s = s.replace(old, new)
        print("ok:", label)
    io.open(P, "w", encoding="utf-8", newline="").write(s)
    print("patched:", P)


if __name__ == "__main__":
    main()

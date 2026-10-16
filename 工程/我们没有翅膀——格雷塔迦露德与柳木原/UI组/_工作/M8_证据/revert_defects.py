#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
revert_defects.py —— 把 M8 的修复逐条还原，造出一份"修复前"的可运行副本，
用于生成 before 证据（黑屏 PNG + 异常日志）。

用法（在 wt-ui worktree 根执行）：
    python revert_defects.py <src_game_dir> <dst_game_dir>

<src_game_dir> = 工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/krkr/game （M8 修复后的版本）
<dst_game_dir> = 临时/ui_run_before/game                            （还原后的副本，会被创建）

只还原"会造成缺陷"的最小改动，不改其它加固（例如 uiDialogDraw 的 try/catch 必须一并还原，
否则 D3 的异常会被吞掉、选择肢屏不会变黑）。
"""
import os, shutil, sys

def patch(path, pairs):
    s = open(path, encoding='utf-8').read()
    for i, (a, b) in enumerate(pairs):
        if a not in s:
            raise SystemExit('NOT FOUND in %s : %r' % (path, a[:60]))
        s = s.replace(a, b, 1)
    open(path, 'w', encoding='utf-8').write(s)
    print('reverted', os.path.basename(path), len(pairs), 'site(s)')

def main(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    assets = os.path.join(os.path.dirname(src), 'assets')
    if os.path.isdir(assets):
        shutil.copytree(assets, os.path.join(dst, 'assets'))
    open(os.path.join(dst, 'autotour.txt'), 'w').write('autotour')

    # ---- D1: TJS2 无 String.lastIndexOf ----
    patch(os.path.join(dst, 'ui_flow.tjs'), [
        ('var cut = uiFlowLastIndexOf(p, UIStateName);',
         'var cut = p.lastIndexOf(UIStateName);'),
        # ---- D2: 大小写不符 uiFlowNodeIndex ----
        ('var cur = UIFlowNodeIndex[UIFlowCurrent];\n\t\tvar s = "当前节点："',
         'var cur = uiFlowNodeIndex[UIFlowCurrent];\n\t\tvar s = "当前节点："'),
    ])

    # ---- D3: 包装器无 try/catch（异常外溢到别的屏）----
    p = os.path.join(dst, 'ui_flow.tjs')
    s = open(p, encoding='utf-8').read()
    i = s.find('\t\tuiScreenDraw = function(stage)')
    j = s.find('\t\treturn UIFlowOrigKey(key);', i)
    j = s.find('\n', j) + 1
    orig = '''		uiScreenDraw = function(stage)
		{
			uiFlowEnsureReady();
			var id = uiScreenCurrent();
			if(id == "flowchart") uiFlowSyncFlowchart();
			else if(id == "chapter") uiFlowSyncChapter();
			else if(id == "fragment" && UIFragDrawHook !== null) return UIFragDrawHook(stage);

			var n = UIFlowOrigDraw(stage);
			if(id == "flowchart") uiFlowDrawMarkers(stage);
			return n;
		};

		uiActionDispatch = function(action, index)
		{
			uiFlowEnsureReady();
			var act = "" + action;
			if(act.indexOf("flow_node_") == 0) return uiFlowSelectNode(act.substring(10));
			if(act == "chapter_enter") return uiFlowEnterChapter(index);
			if(act == "fragment_enter" && UIFragDispatchHook !== null) return UIFragDispatchHook(index);
			if(act == "open_flowchart" || act == "open_chapter" || act == "open_fragment")
			{
				var r = UIFlowOrigDispatch(action, index);
				uiFlowOnOpen(act);
				return r;
			}
			return UIFlowOrigDispatch(action, index);
		};

		uiScreenKey = function(key)
		{
			uiFlowEnsureReady();
			var id = uiScreenCurrent();
			if(id == "flowchart") return uiFlowFlowchartKey(key);
			if(id == "fragment" && UIFragKeyHook !== null) return UIFragKeyHook(key);
			return UIFlowOrigKey(key);
		};
'''
    k = s.find('};', j)          # 吃掉修复版多出来的一个 }
    s = s[:i] + orig + s[k+3:]
    open(p, 'w', encoding='utf-8').write(s)
    print('reverted ui_flow.tjs wrapper')

    # ---- D1 同类：TJS2 无全局 parseInt（ui_fragment.tjs 抛错 → 番外屏内容不完整）----
    patch(os.path.join(dst, 'ui_fragment.tjs'), [
        ('var g = uiFragmentAtoi(s.substring(1, us));\n'
         '\tvar i = uiFragmentAtoi(s.substring(us + 1));',
         'var g = parseInt(s.substring(1, us));\n'
         '\tvar i = parseInt(s.substring(us + 1));'),
    ])

    # ---- D3/D4: ctx 缺 forceShow + uiDialogDraw 无兜底 ----
    patch(os.path.join(dst, 'ui_dialog.tjs'), [
        ('var ctx = %[ page: %[], focus: %[], hide: %[], forceShow: %[],\n'
         '\t             textOverride: %[], boxOverride: %[], opacityOverride: %[],\n'
         '\t             phase: (UIDlgCursorOn ? 0.0 : 1.0) ];',
         'var ctx = %[ page: %[], focus: %[], hide: %[], textOverride: %[],\n'
         '\t             boxOverride: %[], phase: (UIDlgCursorOn ? 0.0 : 1.0) ];'),
    ])
    p = os.path.join(dst, 'ui_dialog.tjs')
    s = open(p, encoding='utf-8').read()
    i = s.find('function uiDialogDraw(stage, screen)')
    j = s.find('\n}', i) + 2
    s = s[:i] + ('function uiDialogDraw(stage, screen)\n'
                 '{\n'
                 '\tvar ctx = uiDialogBuildCtx(stage, screen);\n'
                 '\treturn uiWidgetDrawScreen(stage, screen, ctx);\n'
                 '}') + s[j:]
    open(p, 'w', encoding='utf-8').write(s)
    print('reverted ui_dialog.tjs')

    # ---- D5: 演示背景 ----
    p = os.path.join(dst, 'ui_demo_script.tjs')
    s = open(p, encoding='utf-8').read()
    i = s.find('// ============================================================\n// ★ M8 追加段')
    if i > 0:
        s = s[:i]
        open(p, 'w', encoding='utf-8').write(s)
        print('reverted ui_demo_script.tjs')

    # ---- D6: 转场遮罩名 ----
    patch(os.path.join(dst, 'startup.tjs'), [
        ('var UI_TRANS_RULE      = "ui/x_mask_rule000_1280.png";',
         'var UI_TRANS_RULE      = "ui/rule000.png";'),
        ('this.tourRecord(drawn);', 'this.tourRecord(0);'),
    ])
    print('done ->', dst)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
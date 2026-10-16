# -*- coding: utf-8 -*-
r"""M43 · HTML 复刻端「进入本章」按钮的**目标导向**自证（复现脚本）

■ 证明什么（与 krkr 侧探针同口径，见同目录 m43_run_krkr_flowenter_probe.py）
  动作 `flow_enter`（流程图屏 `fc.jump_hit`）三条分支，逐条断言**真的发生了什么**：
    ① 无光标节点 → 明确提示、**不换屏**；
    ② 未解锁     → 提示解锁条件、**不换屏**；
    ③ 已解锁未读 → **真的切到 dialog 屏** 且 该节点 **由未读变已读** 且 当前节点跟着变。
  点击走**真实 DOM 事件**：`document.querySelector('[data-ui-id="fc.jump_hit"]').click()`
  （该节点的 click 监听由 replica.js 的 buildHit 挂上，最终派发 `doAction('flow_enter')`）。

■ 做法（沿用 M39 的两套自检 + G2 的 DOM 探针先例）
  探针页必须与 `krkr/` 同级（replica.js 按 `../krkr/assets/ui/` 解析贴图），故本脚本把探针页
  **临时写进 `复刻/`**（`_m43_flowenter_probe.html`），跑完无头 Edge 后**删除**，
  并把一份副本归档到本证据目录（`m43_flowenter_probe.html`）。

■ 用法
    python _工作\ISSUE-20260923-06_M43_证据\复现脚本\m43_run_html_flowenter_probe.py
  退出码 0 ⟺ dump 里 `SELFTEST ALL PASS` 且 `M43PROBE RESULT=PASS`。
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                                        # …\ISSUE-20260923-06_M43_证据
UI = os.path.dirname(os.path.dirname(EVID))                         # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m43"
TMP_PAGE = "_m43_flowenter_probe.html"

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>M43 · flow_enter 目标导向探针</title>
<!-- 自动生成（勿手改）：_工作\\ISSUE-20260923-06_M43_证据\\复现脚本\\m43_run_html_flowenter_probe.py -->
<link rel="stylesheet" href="replica.css">
<style>#verdict { font: 13px/1.7 monospace; white-space: pre-wrap; padding: 8px; }
       .ok { color: #0a0; } .bad { color: #c00; font-weight: bold; }</style>
</head>
<body>
<div id="stage"><div id="canvas" style="position:absolute;left:0;top:0"></div></div>
<div id="verdict">running…</div>
<script src="ui_layout.js"></script>
<script src="flow_data.js"></script>
<script src="replica.js"></script>
<script>
(function () {
  var log = [], fails = 0;
  function say(ok, name, detail) {
    if (!ok) fails++;
    log.push((ok ? 'M43PROBE OK   ' : 'M43PROBE FAIL ') + name + (detail ? '  —— ' + detail : ''));
  }
  function toastText() {
    var t = document.querySelector('.ui-toast');
    return t ? (t.textContent || '') : '';
  }
  function nodeIds() {
    var d = window.UI_FLOW_DATA, out = [];
    if (!d || !d.nodes) return out;
    for (var i = 0; i < d.nodes.length; i++) out.push(String(d.nodes[i].id));
    return out;
  }
  function firstLocked() {
    var ids = nodeIds(), R = window.UI_REPLICA;
    for (var i = 0; i < ids.length; i++) if (R.flowStateOf(ids[i]) === 'locked') return ids[i];
    return '';
  }
  function firstAvailableUnvisited() {
    var ids = nodeIds(), R = window.UI_REPLICA, st = R.flowState();
    for (var i = 0; i < ids.length; i++)
      if (R.flowStateOf(ids[i]) === 'available' && !st.visited[ids[i]]) return ids[i];
    return '';
  }

  function run() {
    var R = window.UI_REPLICA;
    if (!R || !window.UI_LAYOUT || !window.UI_FLOW_DATA) {
      say(false, '前置', 'UI_REPLICA / UI_LAYOUT / UI_FLOW_DATA 未加载'); return done();
    }
    R.renderScreen('flowchart');
    var d = document.querySelector('[data-ui-id="fc.jump_hit"]');
    say(!!d, '前置：flowchart 屏渲染出 fc.jump_hit', d ? ('action=' + d.getAttribute('data-ui-action')) : '未找到');
    if (!d) return done();
    say(d.getAttribute('data-ui-action') === 'flow_enter', '前置：fc.jump_hit 的 action = flow_enter',
        'action=' + d.getAttribute('data-ui-action'));
    var tx = document.querySelector('[data-ui-id="fc.jump_tx"]');
    say(!!tx && (tx.textContent || '').indexOf('进入本章') >= 0, '前置：按钮文案为「进入本章」',
        'text=' + (tx ? tx.textContent : '(未找到)'));
    var st0 = R.flowState();
    say(st0.current === 'N01' && st0.cursor === 'N01', '前置：进入流程图屏后光标对齐当前节点（= krkr uiFlowOnOpen）',
        'current=' + st0.current + ' cursor=' + st0.cursor);

    /* ① 无光标节点 */
    st0.cursor = '';
    var scr0 = R.state.screen;
    d.click();
    say(R.state.screen === scr0 && /无可进入节点/.test(toastText()),
        '① 无光标节点：明确提示且不换屏',
        'screen=' + R.state.screen + ' ｜ toast=' + toastText());

    /* ①b 光标指向**不存在的节点**（防御分支；★ 一审 Minor-3 补测） */
    st0.cursor = 'NXX';                       /* 保证不与任何真实节点 id 相同 */
    var scr0b = R.state.screen;
    d.click();
    say(R.state.screen === scr0b && /无可进入节点/.test(toastText()),
        '①b 节点不存在：明确提示且不换屏',
        'cursor=NXX ｜ screen=' + R.state.screen + ' ｜ toast=' + toastText());

    /* ② 未解锁 */
    var locked = firstLocked();
    if (!locked) { say(false, '② 未解锁节点', '找不到 locked 节点（前置不成立）'); }
    else {
      st0.cursor = locked;
      var beforeV = !!st0.visited[locked];
      var scrB = R.state.screen;
      d.click();
      say(R.state.screen === scrB && /未解锁/.test(toastText()) && !st0.visited[locked] && !beforeV,
          '② 未解锁节点：提示解锁条件且不换屏',
          '节点=' + locked + ' ｜ screen=' + R.state.screen + ' ｜ toast=' + toastText());
    }

    /* ③ 已解锁未读 —— 真的进剧情 + 真的标记已读 */
    var target = firstAvailableUnvisited();
    if (!target) { say(false, '③ 已解锁节点', '找不到「可前往且未读」的节点（前置不成立）'); }
    else {
      st0.cursor = target;
      var vBefore = !!st0.visited[target];
      var scrB2 = R.state.screen;
      d.click();
      var vAfter = !!R.flowState().visited[target];
      say(scrB2 === 'flowchart' && R.state.screen === 'dialog' && vBefore === false && vAfter === true
          && R.flowState().current === target,
          '③ 点 fc.jump_hit：切到 dialog 屏 且 该节点由未读变已读',
          '节点=' + target + ' ｜ screen ' + scrB2 + ' -> ' + R.state.screen
          + ' ｜ 已读 ' + vBefore + ' -> ' + vAfter + ' ｜ current=' + R.flowState().current
          + ' ｜ 已读计数=' + R.flowVisitedCount());
    }
    done();
  }

  function done() {
    log.push('SELFTEST ' + (fails ? ('FAILED ' + fails + ' 项') : 'ALL PASS'));
    log.push('M43PROBE RESULT=' + (fails ? 'FAIL' : 'PASS'));
    document.getElementById('verdict').innerHTML =
      log.map(function (l) {
        return '<span class="' + (l.indexOf('FAIL') >= 0 ? 'bad' : 'ok') + '">' + l + '</span>';
      }).join('\n');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);
  else go();
  function go() { try { run(); } catch (e) { say(false, '探针内部异常', (e && e.message) || String(e)); done(); } }
})();
</script>
</body>
</html>
"""


def main():
    page = os.path.join(REP, TMP_PAGE)
    io.open(page, "w", encoding="utf-8", newline="\n").write(PAGE)
    os.makedirs(UD, exist_ok=True)
    url = "file:///" + urllib.parse.quote(page.replace("\\", "/"))
    out = os.path.join(EVID, "M43_flowenter_probe_dump.html")
    try:
        r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                            "--user-data-dir=" + UD, "--hide-scrollbars",
                            "--window-size=1400,900", "--virtual-time-budget=12000",
                            "--dump-dom", url],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dom = r.stdout.decode("utf-8", "replace")
        io.open(out, "w", encoding="utf-8").write(dom)
        for line in re.findall(r"M43PROBE (?:OK|FAIL) +[^<\n]*", dom):
            print("  " + line.strip())
        for line in re.findall(r"SELFTEST (?:ALL PASS|FAILED \d+ 项)", dom):
            print("\n  " + line)
        m = re.search(r"M43PROBE RESULT=(\w+)", dom)
        verdict = m.group(1) if m else "(未找到 RESULT=)"
        print("\n判定：RESULT=%s ｜ 原始 dump：%s ｜ edge rc=%d" % (verdict, out, r.returncode))
        ok = (verdict == "PASS")
    finally:
        try:
            os.remove(page)
        except OSError:
            pass
        # 归档：① 探针页源码（复现用）② 运行后的 DOM dump（证据）
        io.open(os.path.join(EVID, "m43_flowenter_probe_page.html"), "w",
                encoding="utf-8", newline="\n").write(PAGE)
        if os.path.exists(out):
            shutil.copyfile(out, os.path.join(EVID, "m43_flowenter_probe_dom_snapshot.html"))
        shutil.rmtree(UD, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
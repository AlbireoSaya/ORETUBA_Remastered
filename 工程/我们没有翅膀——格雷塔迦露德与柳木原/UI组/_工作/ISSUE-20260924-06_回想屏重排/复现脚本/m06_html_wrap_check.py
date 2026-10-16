# -*- coding: utf-8 -*-
r"""M06 · **HTML 侧折行容量机检**（一审 Minor 登记项：「HTML 折行与引擎等价的机检缺失」）。

■ 它回答什么 / 不回答什么（**别把它当等价证明**）
  回答：把**引擎折行行数最多的 N 条真实语料**灌进 HTML 的 `bl.list`，HTML 渲染后每条
        实际需要几行、是否 ≤ `max_lines=4`（即 HTML 侧不会丢字 / 不会溢出文本区）。
  不回答：HTML 与引擎**逐字等价** —— CSS 折行不实现 krkr 的行首/行尾禁则，度量也不同，
        故两侧行数在边界上可以差 1。本脚本只兜「HTML 侧容量不足」这一类回归。

■ 数据来源
  · 语料「最坏 N 条」直接取自既有证据 `证据\m06_capacity_report.txt`（引擎折行算法已判过），
    避免重复跑 96680 条（那一步的证据脚本是 `证据\m06_measure_capacity.py`）。
  · HTML 侧：无头 Edge 渲染 `复刻\replica.js`，把 `bl.list.labels` 换成这 N 条、`max_rows=N`、
    `item_text.max_lines=4`，逐条量**去掉 line-clamp 后的真实行数**（高度 / 行距）。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_html_wrap_check.py
  退出码：0 = 全部 ≤ 4 行；1 = 有条目在 HTML 侧超 4 行（须调排版/上报）。
"""
import io
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE))
REP = os.path.join(UI, "复刻")
TMP = os.path.join(UI, "临时")
REPORT = os.path.join(ISSUE, "证据", "m06_capacity_report.txt")
HARNESS = os.path.join(TMP, "_m06_wrapcheck.html")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m06wrap"
MAX_LINES = 4


def worst_lines_from_report(n=10):
    """从容量报告里取「折行行数最多」的 N 条（`[k 行 / c 字] 文本`）。"""
    out = []
    for ln in io.open(REPORT, encoding="utf-8"):
        m = re.match(r"^\s*\[(\d+) 行 / (\d+) 字\]\s*(.+?)\s*$", ln)
        if m:
            out.append((int(m.group(1)), m.group(3)))
        if len(out) >= n:
            break
    return out


HARNESS_HTML = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="../复刻/replica.css">
<div id="canvas" style="position:absolute;left:0;top:0"></div><pre id="wrapcheck">PENDING</pre>
<script src="../复刻/ui_layout.js"></script>
<script src="../复刻/replica.js"></script>
<script>
/* ⚠️ replica.js 的 boot() 挂在 DOMContentLoaded（readyState==='loading' 时）—— 本脚本在其后
   注册同一事件，故**晚于** boot 执行（监听器按注册序触发）⇒ layerEl 已就绪。 */
document.addEventListener('DOMContentLoaded', function () {
 try {
  var lines = %(lines)s;
  var LAY = window.UI_LAYOUT, RPC = window.UI_REPLICA;
  var L = null;
  LAY.screens.backlog.elements.forEach(function (e) { if (e.id === 'bl.list') L = e; });
  if (!L) { document.getElementById('wrapcheck').textContent = 'ERR no bl.list'; return; }
  L.labels = lines.slice();
  L.max_rows = lines.length;              /* 全部放一页，逐条量 */
  if (L.item_text) L.item_text.max_lines = %(maxl)d;
  RPC.renderScreen('backlog', { noHistory: true });

  function trueLines(inner) {
    var cs = getComputedStyle(inner);
    var lh = parseFloat(cs.lineHeight) || 0;
    if (!lh) return -1;
    var c = inner.cloneNode(true);
    c.style.display = 'block';
    c.style.webkitLineClamp = 'none';
    c.style.overflow = 'visible';
    c.style.position = 'absolute';
    c.style.left = '-99999px'; c.style.top = '0';
    c.style.width = cs.width;
    c.style.whiteSpace = cs.whiteSpace;
    c.style.wordBreak = cs.wordBreak;
    document.body.appendChild(c);
    var h = c.getBoundingClientRect().height;
    document.body.removeChild(c);
    return Math.round(h / lh);
  }
  var inners = document.querySelectorAll('.ui-list-item-text-inner');
  var res = [];
  for (var i = 0; i < inners.length; i++)
    res.push({ text: inners[i].textContent, lines: trueLines(inners[i]) });
  document.getElementById('wrapcheck').textContent = 'WRAPCHECK_JSON=' + JSON.stringify(res);
 } catch (e) {
  document.getElementById('wrapcheck').textContent = 'WRAPCHECK_ERR=' + (e && e.message ? e.message : e);
 }
});
</script>
"""


def main():
    if not os.path.exists(REPORT):
        print("缺容量报告：", REPORT)
        return 2
    worst = worst_lines_from_report(10)
    if not worst:
        print("容量报告里没解析到「最坏」条目")
        return 2
    print("语料最坏 %d 条（取自 %s，引擎折行行数）：" % (len(worst), os.path.basename(REPORT)))
    for k, t in worst:
        print("  引擎 %d 行 | %d 字 | %s" % (k, len(t), t[:40] + ("…" if len(t) > 40 else "")))

    os.makedirs(TMP, exist_ok=True)
    html = HARNESS_HTML % {"lines": json.dumps([t for _, t in worst], ensure_ascii=False),
                           "maxl": MAX_LINES}
    io.open(HARNESS, "w", encoding="utf-8", newline="").write(html)
    os.makedirs(UD, exist_ok=True)
    url = "file:///" + urllib.parse.quote(HARNESS.replace("\\", "/"))
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--user-data-dir=" + UD, "--hide-scrollbars",
                        "--window-size=1920,1080", "--virtual-time-budget=8000", "--dump-dom", url],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    merr = re.search(r"WRAPCHECK_ERR=([^<]*)</pre>", dom)
    if merr:
        print("浏览器侧异常：", merr.group(1))
        return 2
    m = re.search(r"WRAPCHECK_JSON=(\[.*?\])</pre>", dom, re.S)
    if not m:
        print("未拿到测量结果；dump 片段：", dom[:400])
        return 2
    res = json.loads(m.group(1))
    print("\nHTML 侧实测（去掉 line-clamp 后的真实行数）：")
    bad = []
    for i, item in enumerate(res):
        eng = worst[i][0] if i < len(worst) else -1
        ok = item["lines"] <= MAX_LINES
        if not ok:
            bad.append(i)
        print("  #%d HTML %d 行（引擎 %d 行）%s | %s"
              % (i, item["lines"], eng, "OK" if ok else "★超限", item["text"][:40]))
    print("\n结论：HTML 侧 %d 条全部 ≤ %d 行 = %s"
          % (len(res), MAX_LINES, "是" if not bad else "否（超限 %d 条）" % len(bad)))
    print("（注：本检查只证明 **HTML 侧容量足够**，不证明与引擎逐字等价 —— CSS 不实现 krkr 禁则。）")
    try:
        os.remove(HARNESS)
    except OSError:
        pass
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
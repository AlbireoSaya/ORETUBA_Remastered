# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 第 2 步新素材的**三态回落链**端到端自证（真渲染，一页跑完，不看数据看 DOM）

■ 验什么
  `接口冻结.md` §三 由 E4 产、E1 接线的新件（NEW 角标 / 回放窗底板 / 回放键 / 缩放·横移·纵滚三态件
  / 付箋三态）在**复刻侧**必须按既有回落链 `pressed > hover > normal > asset` 正确呈现。
  本脚本把 flowchart 屏**一次渲染**进一个探针页，然后**逐件**派发
  `mouseenter` → `mousedown` → `mouseup` → `mouseleave`，每一步读**内层态图节点的实际贴图名**，
  与数据里的 `state_assets`（含回落）逐项比对。

■ 为什么值得单独跑（自检页已有 ⑴–⑸/⑱/㉔d/㉔e）
  ① 自检页的主语带 `state_group`，而本轮流程图有 22 件 `state_assets` **无组**；
  ② 本脚本覆盖**每一件**（不是抽样一件），输出可直接贴进报告；
  ③ 它同时是 `attachStates` 无组路径修复（见 replica.js 该处注释）的回归夹具。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_newasset_states.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
EVID = os.path.join(HTML_DIR, "证据")
TMP = os.path.join(EVID, "_newasset")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_newasset"

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8"><link rel=stylesheet href="replica.css"></head>
<body><div id="canvas" style="position:absolute;left:0;top:0"></div><pre id="out">run</pre>
<script src="ui_layout.js"></script><script src="flow_data.js"></script><script src="replica.js"></script>
<script>
var IDS = %s;
function inner(id){var n=document.querySelector('[data-ui-id="'+id+'"]');
  return n?(n.querySelector('.ui-stateimage')||n.querySelector('.ui-nine')):null;}
function cur(id){var n=inner(id); if(!n) return '(无节点)';
  var s=n.style.backgroundImage||n.style.borderImageSource||'';
  var m=/url\\("?([^")]+)"?\\)/.exec(s);
  return m?decodeURIComponent(m[1]).replace(/^.*\\//,''):'(无)';}
function fire(id,t,btn){var n=document.querySelector('[data-ui-id="'+id+'"]'); if(!n) return;
  n.dispatchEvent(new MouseEvent(t,{bubbles:false,cancelable:true,view:window,button:(btn||0),buttons:1}));}
window.addEventListener('load',function(){
  try{
    window.UI_REPLICA.renderScreen('flowchart',{noHistory:true});
    var rows=[];
    IDS.forEach(function(id){
      fire(id,'mouseleave');
      var normal=cur(id);
      fire(id,'mouseenter');
      var hover=cur(id);
      fire(id,'mousedown',0);
      var press=cur(id);
      fire(id,'mouseup',0);
      var back=cur(id);
      fire(id,'mouseleave');
      var out=cur(id);
      rows.push({id:id,normal:normal,hover:hover,pressed:press,back:back,out:out});
    });
    document.getElementById('out').textContent='NEWASSET '+JSON.stringify(rows);
  }catch(e){document.getElementById('out').textContent='NEWASSET-ERR '+e.message;}
});
</script></body></html>"""


def state_of(e):
    sa = e.get("state_assets") or {}
    base = e.get("asset")
    return {"normal": sa.get("normal") or base,
            "hover": sa.get("hover") or sa.get("normal") or base,
            "pressed": sa.get("pressed") or sa.get("hover") or sa.get("normal") or base}


def main():
    os.makedirs(EVID, exist_ok=True)
    with io.open(os.path.join(LAYOUT, "screens", "32_flowchart.json"), encoding="utf-8") as f:
        sc = json.load(f)
    subs = [e for e in sc.get("elements", [])
            if e.get("state_assets") and (e["state_assets"].get("hover") or e["state_assets"].get("pressed"))]
    ids = [e["id"] for e in subs]

    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    for f in ("replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"):
        src = os.path.join(REP, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(TMP, f))
    io.open(os.path.join(TMP, "probe.html"), "w", encoding="utf-8").write(PAGE % json.dumps(ids))
    os.makedirs(UD, exist_ok=True)
    url = "file:///" + urllib.parse.quote(os.path.join(TMP, "probe.html").replace(os.sep, "/"))
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox", "--user-data-dir=" + UD,
                        "--window-size=1400,900", "--virtual-time-budget=9000", "--dump-dom", url],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"NEWASSET (\[.*?\])</pre>", dom, re.S)
    if not m:
        e = re.search(r"NEWASSET-ERR ([^<]*)</pre>", dom)
        print("探针失败：" + (e.group(1) if e else dom[:300]))
        return 1
    rows = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))

    def base(p):
        return str(p or "").split("/")[-1]

    bad, lines = [], []
    byid = {e["id"]: e for e in subs}
    for row in rows:
        w = state_of(byid[row["id"]])
        got = [row["normal"], row["hover"], row["pressed"], row["back"], row["out"]]
        want = [base(w["normal"]), base(w["hover"]), base(w["pressed"]), base(w["hover"]), base(w["normal"])]
        ok = (got == want)
        if not ok:
            bad.append("%s 实测 %s ≠ 数据回落链 %s" % (row["id"], got, want))
        lines.append("%-16s %s ｜ 初=%-26s 悬停=%-26s 按下=%-26s 抬起=%-26s 移出=%s"
                     % (row["id"], "OK  " if ok else "MISMATCH", got[0], got[1], got[2], got[3], got[4]))
    print("主语 %d 件（flowchart 屏带三态 state_assets 的元素）｜ 逐件派发 mouseenter/mousedown/mouseup/mouseleave" % len(subs))
    for l in lines:
        print("  " + l)
    io.open(os.path.join(EVID, "E3_新素材三态_日志.txt"), "w", encoding="utf-8").write(
        "主语 %d 件\n" % len(subs) + "\n".join(lines) + "\n\n"
        + ("判定：全部 == 数据回落链（pressed > hover > normal > asset）" if not bad
           else "判定：不一致 %d 件\n" % len(bad) + "\n".join(bad)))
    print("\n判定：%s" % ("全部 == 数据回落链（pressed > hover > normal > asset）" if not bad
                       else "不一致 %d 件：%s" % (len(bad), "；".join(bad[:4]))))
    shutil.rmtree(UD, ignore_errors=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""probe_frag_links.py —— 「番外独立层还画不画主干连线」的两端取证探针

用户 2026-09-28 报告：**在 HTML 侧**看 Fragment 番外层时，画面里出现「类似主线的剧情连接线」；
诉求＝**独立的番外剧情之间不要连线**。

本探针**不靠肉眼看像素**，直接读渲染器台账（`UI_REPLICA.state.links`），并在两处落点各测一遍：
  · **复刻件** `复刻/index.html`（人工验收用）
  · **可视化编辑器** `复刻/editor.html`（用户实际在看的那一个）
每处测两态：**主干**（不切层）与 **番外层**（`doAction('flow_layer', {layer:'frag1'})`）。

判据（与 `krkr/game/ui_flow_links.tjs` 冻结 §四.1 同一句话）：`fc_layer != 主干值` ⇒ **一条都不画**。
引擎侧实测：frag4 层逐帧 `seen=0 drawn=0`（见本目录 `读数.md`）。

用法（PYTHONPATH 见脚本头注释）：
    python probe_frag_links.py
输出：`证据/台账.tsv`、`证据/<tag>.png`（各态截图）、stdout 摘要。
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))                 # …\复现脚本
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))      # …\UI组（HERE 已是目录 ⇒ 上三级）
assert os.path.basename(UI) == "UI组", UI
ISSUE = os.path.dirname(HERE)
REP = os.path.join(UI, "复刻")
ASSETS = os.path.join(UI, "krkr", "assets")
LAYOUT_JS = os.path.join(REP, "ui_layout.js")
EVID = os.path.join(ISSUE, "证据")
TMP = os.path.join(EVID, "_stacks")
UD = r"E:/ZCode Workspace/Galgame/临时/edge_fraglinks"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
COPY = ["index.html", "editor.html", "editor.css", "editor_core.js", "editor_ui.js",
        "replica.css", "replica.js", "flow_data.js", "asset_index.js", "screen_index.js"]


def fileurl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return "file:///" + (p[0].lower() + p[1:] if p[1:2] == ":" else p)


def build(tag, page_file, layer):
    dst = os.path.join(TMP, tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        src = os.path.join(REP, f)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dst, f))
    shutil.copy2(LAYOUT_JS, os.path.join(dst, "ui_layout.js"))
    page = io.open(os.path.join(dst, page_file), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    lyr = ("'%s'" % layer) if layer else "''"
    hook = ("<script>window.addEventListener('load',function(){"
            "var R=window.UI_REPLICA; if(!R) return;"
            "if(%s){ if(R.doAction){ try{R.doAction('flow_layer',{layer:%s});}catch(e){ window.__LAYER_ERR=''+e; } } }"
            "var L=R.state&&R.state.links?R.state.links:null;"
            "window.__PROBE={layer:R.getFlag?R.getFlag('fc_layer'):'',"
            "blocked:L?!!L.blocked:null,"
            "drawn:L&&L.drawn?L.drawn.length:-1,"
            "layerField:L?(L.layer||''):'',"
            "rejects:L&&L.rejects?L.rejects.slice(0,3):[]};"
            "document.title='PROBE='+JSON.stringify(window.__PROBE);"
            "});</script>") % (("true" if layer else "false"), lyr)
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, page_file), "w", encoding="utf-8").write(page)
    return dst


def run(dst, page_file):
    url = fileurl(os.path.join(dst, page_file)) + "?screen=flowchart&chrome=0"
    png = os.path.join(EVID, os.path.basename(dst) + ".png")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars",
                    "--window-size=1944,1180", "--virtual-time-budget=9000",
                    "--screenshot=" + os.path.abspath(png), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                          "--user-data-dir=" + UD + "_dom", "--hide-scrollbars",
                          "--window-size=1944,1180", "--virtual-time-budget=9000",
                          "--dump-dom", url],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8", "replace")
    probe = None
    k = dom.find("PROBE=")
    if k >= 0:
        seg = dom[k + 6:].split("<")[0].strip()
        try:
            probe = json.loads(seg)
        except Exception:
            probe = {"raw": seg[:200]}
    return probe, png


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(EVID, exist_ok=True)
    rows = []
    for page_file, ptag in (("index.html", "复刻"), ("editor.html", "编辑器")):
        for layer, ltag in ((None, "主干"), ("frag1", "番外层")):
            tag = "%s_%s" % (ptag, ltag)
            dst = build(tag, page_file, layer)
            probe, png = run(dst, page_file)
            print("  %-10s %-6s ⇒ %s" % (ptag, ltag, probe))
            rows.append((ptag, ltag, probe or {}, png))
    with io.open(os.path.join(EVID, "台账.tsv"), "w", encoding="utf-8") as f:
        f.write("落点\t层态\tfc_layer取值\tblocked(层判据)\t实际画出连线数\t台账里的层字段\trejects\n")
        for ptag, ltag, pr, _png in rows:
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                ptag, ltag, pr.get("layer", ""), pr.get("blocked"), pr.get("drawn"),
                pr.get("layerField", ""), ";".join(pr.get("rejects", []))[:120]))
    print("\n写出 %s" % os.path.join(EVID, "台账.tsv"))


if __name__ == "__main__":
    main()

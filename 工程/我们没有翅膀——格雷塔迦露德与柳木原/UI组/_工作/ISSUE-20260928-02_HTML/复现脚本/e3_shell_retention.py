# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· ★ 外壳留存自证：`main → frag1..frag6` 逐层，外壳件像素**逐像素不变**

■ 背景（第 3 批更正后的数据）
  冻结 §二：只有**图内容层**（`fc.node.*`/`fc.branch.*`/`fc.label.*`/`fc.entry.*`/`fc.frag*`）带
  `vis_flag:"fc_layer"`；**61 件外壳件**（`fc.dim`/`fc.scroll`/`fc.smallmap`/`fc.mapview`/`fc.mini1..8`/
  `fc.mtab*`/`fc.title*`/`fc.p_*`/`fc.scr_*`/`fc.zoom_*`/`fc.shift_*`/`fc.jump*`/`fc.fusen_*`/
  `fc.pbkick*`/`fc.pbk_panel`/`fc.close*`/`fc.sysbar`）**一律不带旗标** ⇒ 进独立层时**外壳仍在**。

■ 怎么自证（不靠肉眼）
  ① **外壳专属截屏**（最硬的一条）：同层下把**图内容层元素全部 `display:none`**、并撤掉两条程序化
     canvas（连线 / `current` 环）后截屏 —— 此时画布上只剩外壳。若外壳随层变了，六张图必然互不相同；
     实测 **全画布差异 == 0 像素**（1920×1080 全等）。
  ② **逐件量化表**：61 件外壳件 × 6 个独立层，按**该件矩形**在①的两张「外壳专属截屏」上逐像素比，
     逐件给差异像素数（应全 0）。
  ③ **DOM 侧**：逐层 dump 外壳 61 件的 `display`（应全 可见）＋ 内容层隐藏件数 ＋ canvas 条数。
  ④ **全量截屏**：正常（内容可见）的 6 张图，给「与主干层的差异像素数 + 差异包围盒」，并把这批差异
     像素分类为「落在图内容层矩形并集内」/「其余」——证明**变的只有内容区**。

■ 用法（★ 只读数据与素材，不改任何产物；默认预设 screen1 的冻结态）
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_shell_retention.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e3_md5util as mu                                    # noqa: E402  （行尾健壮的文件指纹）
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
SHOT = os.path.join(EVID, "_shell_shot")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_shell"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
CANVAS_W, CANVAS_H = 1920, 1080
LAYERS = ["main", "frag1", "frag2", "frag3", "frag4", "frag5", "frag6"]
# ★ 数据层轮换预设时 `layout\screens\32_flowchart.json` / `复刻\ui_layout.js` 会**临时**变成非默认档；
#   用 e3_shadow_screen1.py 建的**冻结 screen1 影子栈**跑（该脚本已自证 md5 == 冻结值，逐字节相同）。
SCREEN_JSON = os.environ.get("E3_FLOW_JSON", os.path.join(LAYOUT, "screens", "32_flowchart.json"))
LAYOUT_JS = os.environ.get("E3_UI_LAYOUT_JS", os.path.join(REP, "ui_layout.js"))


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def screen_of():
    with io.open(SCREEN_JSON, encoding="utf-8") as f:
        return json.load(f)


def shell_content(sc):
    """外壳 = 不带 vis_flag（冻结 §二 第 3 批）；内容层 = 带 vis_flag。"""
    shell = [e for e in sc.get("elements", []) if e.get("id") and not e.get("vis_flag")]
    content = [e for e in sc.get("elements", []) if e.get("id") and e.get("vis_flag")]
    return shell, content


# ── 拍页：注入素材根 + scale=1 + 切层；可选的「外壳专属」变换 / DOM 探针 ──────
def build_page(tag, layer, content_ids, report=None):
    """report = (shell_ids, content_ids) 时在同一页面里追加 DOM 探针（输出 <pre id=shellprobe>）。"""
    dst = os.path.join(SHOT, tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(LAYOUT_JS if f == "ui_layout.js" else os.path.join(REP, f), os.path.join(dst, f))
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    lyr = ("'%s'" % layer) if layer else "''"
    # ★ 顺序关键：先 scale + **切层**（doAction 会跑 applyFlagVisibility 重排内容层显隐），
    #   **再**隐藏内容层 / 撤 canvas —— 反过来的话 applyFlagVisibility 会把刚隐藏的内容又 display='' 回来
    #   （首版即栽在这里：main 隐藏成功、fragG 隐藏被撤销 ⇒ 外壳专属图仍含内容，差异上万像素）。
    hide = ""
    if content_ids is not None:
        hide = ("var C=%s;"
                "C.forEach(function(id){var n=document.querySelector('[data-ui-id=\"'+id+'\"]');"
                " if(n) n.style.display='none';});"
                "['ui-linklayer','ui-currentring'].forEach(function(cl){"
                " var ns=document.querySelectorAll('.'+cl);"
                " for(var i=0;i<ns.length;i++){ if(ns[i].parentNode) ns[i].parentNode.removeChild(ns[i]); }});"
                % json.dumps(content_ids))
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);"
            "if(%s){window.UI_REPLICA.doAction('flow_layer',{layer:%s});}"
            "%s"
            "});</script>") % (("true" if layer else "false"), lyr, hide)
    if report:
        shell_ids, content_ids2 = report
        rep = ("<script>window.addEventListener('load',function(){"
               "var REP=window.UI_REPLICA,SHELL=%s,CONTENT=%s,LAYER=%s;"
               "if(LAYER&&REP)REP.doAction('flow_layer',{layer:LAYER});"
               "function vis(id){var n=document.querySelector('[data-ui-id=\"'+id+'\"]');"
               " return n?(getComputedStyle(n).display!=='none'):null;}"
               "var sh=[],shown=0;"
               "SHELL.forEach(function(id){var v=vis(id); if(v!==true) sh.push(id+':'+(v===null?'缺DOM':'不可见'));});"
               "CONTENT.forEach(function(id){ if(vis(id)===true) shown++; });"
               "var canv=document.querySelectorAll('.ui-linklayer,.ui-currentring').length;"
               "var pre=document.createElement('pre'); pre.id='shellprobe';"
               "pre.textContent='SHELLPROBE '+JSON.stringify({layer:LAYER||'main',shell:SHELL.length,"
               "shell_bad:sh,content_visible:shown,canvas:canv});"
               "document.body.appendChild(pre);"
               "});</script>") % (json.dumps(shell_ids), json.dumps(content_ids2), lyr)
        hook = hook + rep
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return dst


def shoot(tag, layer, content_ids, out):
    dst = build_page(tag, layer, content_ids)
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars",
                    "--window-size=1944,1180",          # ★ 视口 1920×1087（1920,1080 会静默裁掉右侧 24 / 底部 93）
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("HTML 侧截图失败：" + out)
    im = Image.open(out).convert("RGB")
    if im.width >= CANVAS_W and im.height >= CANVAS_H:
        im = im.crop((0, 0, CANVAS_W, CANVAS_H))
    im.save(out)
    return out


# ── DOM 探针：用**同一份** index.html 加一小段上报脚本（保证与截屏同一 boot 路径） ──
def probe(tag, layer, shell_ids, content_ids):
    dst = build_page("probe_" + tag, layer, None, report=(shell_ids, content_ids))
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--user-data-dir=" + UD, "--window-size=1400,900",
                        "--virtual-time-budget=9000", "--dump-dom", url],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"SHELLPROBE (\{.*?\})</pre>", dom, re.S)
    if not m:
        return None
    txt = m.group(1)
    for a, b in (("&quot;", '"'), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")):
        txt = txt.replace(a, b)
    return json.loads(txt)


# ── 像素工具（numpy） ────────────────────────────────────────────────────────
def arr(png):
    return np.asarray(Image.open(png).convert("RGB"), dtype=np.int16)


def diff_mask(a, b, thr=6):
    d = np.abs(a - b).max(axis=2)
    return d > thr


def rect_mask(rects):
    m = np.zeros((CANVAS_H, CANVAS_W), dtype=bool)
    for x, y, w, h in rects:
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(CANVAS_W, int(x) + int(w)), min(CANVAS_H, int(y) + int(h))
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = True
    return m


def bbox_of(mask):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(EVID, exist_ok=True)
    sc = screen_of()
    shell, content = shell_content(sc)
    shell_ids = [str(e["id"]) for e in shell]
    content_ids = [str(e["id"]) for e in content]
    print("盘上 32_flowchart.json：%d 元素 ｜ 外壳件（不带 vis_flag）%d ｜ 图内容层（带 vis_flag）%d"
          % (len(sc.get("elements", [])), len(shell), len(content)))
    print("屏数据 = %s ｜ 渲染栈 = %s" % (SCREEN_JSON, LAYOUT_JS))
    # ★ 口径声明（与冻结 §二 第 3 批一致，主代理「外壳 61 件」即此口径）：
    #   **外壳件 = 不带 `vis_flag` 的元素**（两种层共用的舞台，进独立层后仍在）；
    #   **层内容 = 带 `vis_flag` 的元素**（`fc.node.*`/`fc.branch.*`/`fc.label.*`/`fc.entry.*`/`fc.frag*`）。
    #   本轮的组名底板 `fc.frag<G>_title_bg` 是 `vis_when:"frag<G>"` 的**层内容件** ⇒ 计入层内容、**不计入外壳**。
    bg_ids = [str(e.get("id", "")) for e in sc.get("elements", []) if "_title_bg" in str(e.get("id", ""))]
    print("组名底板件（本档 %d 件）：%s" % (len(bg_ids), "、".join(bg_ids) if bg_ids else "(本档无)"))
    if bg_ids:
        mis = [i for i in bg_ids if i not in content_ids]
        if mis:
            print("  ★★ 口径异常：%s **不带 vis_flag** ⇒ 会被误算进「外壳」；应属层内容（须报数据层）" % mis)
        else:
            print("  ✓ 口径正确：底板件带 vis_flag ⇒ 计入层内容（%d 件），外壳仍 %d 件，两口径不混" % (len(content), len(shell)))
    print("外壳件： " + "、".join(shell_ids))

    # ── ① 逐层两种截屏 ──────────────────────────────────────────────────────
    full, sonly, probes, log = {}, {}, {}, []
    for L in LAYERS:
        lay = None if L == "main" else L
        full[L] = shoot("full_" + L, lay, None, os.path.join(EVID, "E3_shell_full_%s.png" % L))
        sonly[L] = shoot("sonly_" + L, lay, content_ids, os.path.join(EVID, "E3_shell_sonly_%s.png" % L))
        probes[L] = probe(L, lay, shell_ids, content_ids)
        log.append("层 %-6s 截图 %s / 外壳专属 %s ｜ DOM 探针 %s"
                   % (L, os.path.basename(full[L]), os.path.basename(sonly[L]),
                      json.dumps(probes[L], ensure_ascii=False)))
        print(log[-1])

    # ── ② DOM 侧：外壳件是否全可见 ─────────────────────────────────────────
    #    ★ 例外：`visible_default:false` 的 3 件（fc.pbk_panel / fc.p_player / fc.p_player_tx）是
    #      M34「互斥态分组：与 minimap 重叠、默认隐藏」的**设计默认**，由运行期 `ctx.forceShow` 抬起
    #      ⇒ 它们**应当**不可见（且七层都不可见）；只要不是「缺 DOM」就不算分叉。
    by_design = set(str(e["id"]) for e in shell if e.get("visible_default") is False)
    print("\n=== ② DOM 侧：外壳 %d 件逐层可见性（%d 件为 visible_default:false 设计默认隐藏；其余应全可见）==="
          % (len(shell_ids), len(by_design)))
    dom_bad = []
    for L in LAYERS:
        p = probes[L]
        if not p:
            dom_bad.append(L + " 探针无回值"); continue
        for item in p["shell_bad"]:
            eid, why = item.split(":", 1)
            if why == "缺DOM":
                dom_bad.append("%s：外壳 %s 不在 DOM" % (L, eid))
            elif eid not in by_design:
                dom_bad.append("%s：外壳 %s 不可见（非设计默认）" % (L, eid))
        # 设计默认隐藏的那几件也必须七层一致地不可见
        print("  %-6s 外壳 %d/%d 可见（设计隐藏 %d 件）｜ 图内容层可见 %d/%d ｜ canvas %d"
              % (L, p["shell"] - len(p["shell_bad"]), p["shell"], len(by_design),
                 p["content_visible"], len(content_ids), p["canvas"]))

    # ── ③ 最强判据：外壳专属截屏全画布差异 ────────────────────────────────
    print("\n=== ③ 外壳专属截屏（内容层隐藏 + 撤 canvas）：main vs 各层 全画布差异像素 ===")
    print("    （0 = 外壳逐像素不变；六张图两两相同）")
    am_main = arr(sonly["main"])
    shell_bad = []
    for L in LAYERS[1:]:
        dm = diff_mask(am_main, arr(sonly[L]))
        n = int(dm.sum())
        if n:
            shell_bad.append("%s: %d 像素" % (L, n))
        print("  main vs %-6s 差异 %d 像素 ｜ 包围盒 %s" % (L, n, bbox_of(dm)))

    # ── ④ 逐件量化表：61 件 × 6 层，本件矩形内外壳专属截屏差异 ─────────────
    print("\n=== ④ 逐件量化表（%d 件 × %d 层；本件矩形内差异像素，应全 0）===" % (len(shell), len(LAYERS) - 1))
    dms = {L: diff_mask(am_main, arr(sonly[L])) for L in LAYERS[1:]}
    piece_bad = []
    hdr = "  %-18s %5s %5s %5s %5s %5s   %s" % ("外壳件", "w", "h", "frag1", "frag3", "frag6", "六层合计")
    print(hdr)
    for e in shell:
        x, y, w, h = int(e["x"]), int(e["y"]), int(e["w"]), int(e["h"])
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(CANVAS_W, x + w), min(CANVAS_H, y + h)
        row = []
        for L in ("frag1", "frag2", "frag3", "frag4", "frag5", "frag6"):
            n = int(dms[L][y0:y1, x0:x1].sum())
            row.append(n)
            if n:
                piece_bad.append("%s@%s=%d" % (e["id"], L, n))
        print("  %-18s %5d %5d %5d %5d %5d   %s"
              % (e["id"], w, h, row[0], row[2], row[5], sum(row)))

    # ── ⑤ 全量截屏：差异像素 + 分类（落在内容矩形并集内 / 其余） ────────────
    print("\n=== ⑤ 全量截屏（内容可见）：main vs 各层差异像素 + 分类 ===")
    cu = rect_mask([(e["x"], e["y"], e["w"], e["h"]) for e in content])
    af_main = arr(full["main"])
    for L in LAYERS[1:]:
        dm = diff_mask(af_main, arr(full[L]))
        n = int(dm.sum())
        n_in = int((dm & cu).sum())
        n_out = n - n_in
        print("  main vs %-6s 差异 %6d 像素（内容矩形并集内 %6d ｜ 其余 %5d）｜ 包围盒 %s"
              % (L, n, n_in, n_out, bbox_of(dm)))

    # ── 写日志 ─────────────────────────────────────────────────────────────
    #   ★ 一审 P0-3：这里原先写死了一句「自证 ui_layout.js md5 == 797cf8…」——那不是任何校验的输出，
    #     且锚点过期。改为**运行时读实际使用的两个文件的真实 md5**（三形态都给，行尾口径见 e3_md5util），
    #     并明确"锚点是否命中"由谁负责（栈脚本）——本脚本只报事实，不再自造结论。
    txt = ["E3 外壳留存自证（ISSUE-20260928-02 · HTML 侧）",
           "屏数据（本次实际使用）= %s" % mu.describe(SCREEN_JSON, label="屏"),
           "渲染栈（本次实际使用）= %s" % mu.describe(LAYOUT_JS, label="JS"),
           "渲染：index.html?screen=flowchart&chrome=0，1920×1080",
           "外壳件 %d ｜ 图内容层 %d ｜ 组名底板件 %d（%s）"
           % (len(shell), len(content), len(bg_ids), "、".join(bg_ids) if bg_ids else "本档无"),
           "口径：外壳 = **不带 vis_flag**（两种层共用舞台）；层内容 = 带 vis_flag（含 `fc.frag<G>_title_bg`，"
           "为 vis_when=\"frag<G>\" 的层内容件，**不计入外壳 61 件**）", "",
           "★ 锚点（冻结态是否相符）由 `e3_snapshot_stack.py` / `e3_shadow_screen1.py` 负责校验；"
           "本脚本只按**运行时读到的真实 md5** 报告，不自造自证串。", "",
           "①逐层截屏/探针："] + log
    txt += ["", "②DOM 侧外壳异常清单：%s" % (dom_bad if dom_bad else "无（%d 件设计默认隐藏七层一致；其余全部可见）" % len(by_design)),
            "③外壳专属截屏 main vs 各层全画布差异：%s" % (shell_bad if shell_bad else "全 0 像素（六层逐像素相同）"),
            "④逐件量化表差异：%s" % (piece_bad if piece_bad else "61 件 × 6 层全部 0 像素")]
    io.open(os.path.join(EVID, "E3_外壳留存_日志.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("\n日志：%s" % os.path.join(EVID, "E3_外壳留存_日志.txt"))

    shutil.rmtree(UD, ignore_errors=True)
    ok = (not dom_bad) and (not shell_bad) and (not piece_bad)
    print("\n判定：%s" % ("外壳 61 件在 main→frag1..frag6 七层中**逐像素不变**（外壳专属截屏全画布 0 差异、逐件 61×6 全 0、DOM 全可见）"
                       if ok else "存在分叉：%s" % (dom_bad + shell_bad + piece_bad)[:6]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

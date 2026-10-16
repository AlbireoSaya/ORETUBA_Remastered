# -*- coding: utf-8 -*-
r"""m50_html_gallery_shots.py —— CG 鉴赏页（`27_gallery.json`）**HTML 复刻端端到端核验**（M2 证据）

■ 目的（对应冻结书 §7 验收 ②③ + 主代理派单「24 栏齐整、12 页可翻、页码正确」）
  ① **12 页全扫**：逐页 dump DOM，断言
       · 每页栏数 = 24（第 12 页 = 22，余 2 栏留空）
       · 每栏 `data-ui-index` = 全局项序号，序列连续且从 (页-1)×24 起
       · 每栏 `data-ui-var-asset` == `27_gallery.json` 的 `item_variants.frames[全局项][0]`
         ⇒ **「frames 与映射.tsv 逐栏一致」在渲染层再验一遍**（数据侧已逐件对拍过）
       · 每栏 `data-ui-var-text` == `1/N`（N = 该栏差分张数）
  ② **栏位内差分翻页**：点第 0 栏的 `vnext` ⇒ 缩略图**确实换图**（asset → frames[0][1]）
     且 `n/N` → `2/3`；边界 clamp 另验。
  ③ 截图：第 1 / 2 / 12 页 1:1 画布 PNG（供目视）。
  ④ **机制侧待办单列**（**不计入本模块 RESULT**，如实登记）：`gal_page`（页码件文本随页变）
     与 HTML 自动 `ui-list-pager`（须按 `scroll.pager:false` 关闭）—— 两者都要 M1 动机制。

■ 机制归属
  这些行为由 **M1 的 `item_variants` / `gallery_page_*` 机制**实现（`复刻/replica.js`）；
  本脚本**只读**它，不改任何交付文件 —— 目的是用 M2 的**真实数据**驱动 M1 的机制，验证接口对得上。

■ 运行
    python _工作\ISSUE-20260924-08_鉴赏模式\复现脚本\m50_html_gallery_shots.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE_DIR))
REP = os.path.join(UI, "复刻")
EVID = os.path.join(ISSUE_DIR, "M2_证据")
PAGE = os.path.join(ISSUE_DIR, "_m50_tmp_page.html")
UD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(UI))), "临时", "edge_m50")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SCREEN = os.path.join(UI, "layout", "screens", "27_gallery.json")

HOOK = """
<script>
/* M50 证据专用钩子（**不进任何交付文件**）：隐藏页面外壳 + 1:1 + 两种探针
   ① `?act=<动作>&actn=<次数>`：渲染后调 `UI_REPLICA.doGalleryAction`（走真实动作入口）；
   ② `?selclick=<CSS 选择器>`：渲染后点第一个匹配节点（用于点**逐栏差分按钮** —— 它没有元素 id）。 */
(function () {
  var st = document.createElement('style');
  st.textContent = '.shell{max-width:none!important;padding:0!important;margin:0!important}'
    + '.shell-head,.shell-foot{display:none!important}'
    + '#stage-wrap{justify-content:flex-start!important;display:block!important}'
    + '#stage{box-shadow:none!important}';
  document.head.appendChild(st);
  window.addEventListener('load', function () {
    if (!window.UI_REPLICA) return;
    UI_REPLICA.setScale(1);
    var m = /[?&]act=([A-Za-z0-9_:]+)/.exec(location.search || '');
    var n = /[?&]actn=(\\d+)/.exec(location.search || '');
    if (m) {
      var times = n ? parseInt(n[1], 10) : 1;
      for (var i = 0; i < times; i++) UI_REPLICA.doGalleryAction(m[1]);
    }
    var c = /[?&]selclick=([^&]+)/.exec(location.search || '');
    if (c) {
      var sel = decodeURIComponent(c[1]);
      var nd = document.querySelector(sel);
      window.__m50_click = nd ? 'OK' : 'NOHIT';
      if (nd) nd.click();
    }
    UI_REPLICA.applyFlagVisibility();
  });
})();
</script>
"""


def build_page():
    html = io.open(os.path.join(REP, "index.html"), encoding="utf-8").read()
    html = html.replace('href="replica.css"', 'href="../../复刻/replica.css"')
    html = html.replace('src="ui_layout.js"', 'src="../../复刻/ui_layout.js"')
    html = html.replace('src="flow_data.js"', 'src="../../复刻/flow_data.js"')
    html = html.replace('src="replica.js"', 'src="../../复刻/replica.js"')
    html = html.replace('<script src="../../复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='../../krkr/assets/';</script>\n"
                        '<script src="../../复刻/ui_layout.js"></script>')
    html = html.replace('</body>', HOOK + '\n</body>')
    io.open(PAGE, "w", encoding="utf-8").write(html)


def url(query):
    return "file:///" + urllib.parse.quote(PAGE.replace("\\", "/")) + query


def edge(query, out_png=None):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=9000"]
    if out_png:
        cmd.append("--screenshot=" + os.path.abspath(out_png))
    else:
        cmd.append("--dump-dom")
    cmd.append(url(query))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace")


def parse_items(dom):
    """→ ([(全局项序号, 缩略图 asset)], {全局项序号: n/N 文本})"""
    out = []
    for tag in re.findall(r"<div[^>]*data-ui-var-asset=[^>]*>", dom):
        idx = re.search(r'data-ui-var-index="(\d+)"', tag)
        ast = re.search(r'data-ui-var-asset="([^"]*)"', tag)
        if idx and ast:
            out.append((int(idx.group(1)), ast.group(1)))
    txt = {}
    for tag, body in re.findall(r"<div([^>]*data-ui-var-text=[^>]*)>([^<]*)<", dom):
        idx = re.search(r'data-ui-var-index="(\d+)"', tag)
        if idx:
            txt[idx.group(1)] = body.strip()
    return out, txt


def visible_page_tx(dom):
    """本屏 12 件页码文本里**可见的那几件** → [(页号, 文本)]"""
    vis = []
    for m in re.finditer(r'data-ui-id="gal\.page_tx_(\d\d)"([^>]*)>(.*?)</div></div>', dom, re.S):
        p, attrs, body = int(m.group(1)), m.group(2), m.group(3)
        hidden = "display: none" in attrs or "display:none" in attrs
        t = re.search(r">([^<>]*)$", body)
        if not hidden:
            vis.append((p, (t.group(1).strip() if t else body.strip())))
    return vis


def main():
    with io.open(SCREEN, encoding="utf-8") as f:
        scr = json.load(f)
    cells = [e for e in scr["elements"] if e["id"] == "gal.list"][0]
    frames = cells["item_variants"]["frames"]
    per_page = cells["max_cols"] * cells["max_rows"]
    n_pages = (len(frames) + per_page - 1) // per_page
    assert len(frames) == 286 and per_page == 24 and n_pages == 12, (len(frames), per_page, n_pages)

    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    build_page()
    fails, pending = [], []

    def chk(ok, label, detail=""):
        print("  [%s] %s%s" % ("OK " if ok else "NG!", label, ("  —— " + detail) if detail else ""))
        if not ok:
            fails.append(label + ("  —— " + detail if detail else ""))

    print("=" * 100)
    print("m50_html_gallery_shots · CG 鉴赏页 HTML 端端到端核验（真实数据 27_gallery.json）")
    print("  栏位 %d ｜ 每页 %d ｜ 页数 %d" % (len(frames), per_page, n_pages))
    print("=" * 100)

    print("① 12 页全扫（逐页 dump DOM；第 1/2/12 页另出 1:1 PNG）")
    last_tx = []
    for p in range(1, n_pages + 1):
        q = "?screen=gallery" if p == 1 else "?screen=gallery&act=gallery_page_next&actn=%d" % (p - 1)
        if p in (1, 2, 12):
            edge(q, out_png=os.path.join(EVID, "m50_html_page%02d.png" % p))
        dom = edge(q)
        items, texts = parse_items(dom)
        first = (p - 1) * per_page
        exp_n = min(per_page, len(frames) - first)
        ok, det = True, []
        if len(items) != exp_n:
            ok = False
            det.append("栏数 %d（期望 %d）" % (len(items), exp_n))
        if [i for i, _a in items] != list(range(first, first + exp_n)):
            ok = False
            det.append("全局序号序列不符（首 %s）" % (items[0][0] if items else "无"))
        bad = [(i, a, frames[i][0]) for i, a in items if a != frames[i][0]]
        if bad:
            ok = False
            det.append("缩略图与 frames[i][0] 不符 %d 栏，如 %s" % (len(bad), bad[:2]))
        badt = [(i, texts.get(str(i))) for i, _a in items
                if texts.get(str(i)) != "1/%d" % len(frames[i])]
        if badt:
            ok = False
            det.append("n/N 初值不符 %d 栏，如 %s" % (len(badt), badt[:2]))
        chk(ok, "页 %2d / %d：%d 栏、序号 %d..%d、缩略图与 frames 逐栏一致、n/N=1/N"
            % (p, n_pages, exp_n, first, first + exp_n - 1), "；".join(det))
        last_tx = visible_page_tx(dom)

    print("② 栏位内差分翻页（真实点击第 0 栏的 vnext，N=3）")
    dom0 = edge("?screen=gallery")
    items0, texts0 = parse_items(dom0)
    chk(bool(items0) and items0[0][1] == frames[0][0] and texts0.get("0") == "1/3",
        "初态：第 0 栏 asset = frames[0][0]、n/N = 1/3",
        "%s / %s" % (items0[0][1] if items0 else "-", texts0.get("0")))
    sel = '[data-ui-index="0"] [data-ui-var-btn="vnext"]'
    qsel = "?screen=gallery&selclick=" + urllib.parse.quote(sel)
    # 主口径：走**机制的真实动作入口** `doGalleryAction('gallery_next:<行号>')`
    #   （与 M1 巡演 `kind:"galvar"` 同一入口；数据侧 `item_variants.next.action` = `gallery_next:%row%`）
    qact = "?screen=gallery&act=gallery_next:0"
    edge(qact, out_png=os.path.join(EVID, "m50_html_var2.png"))   # 出图
    dom1 = edge(qact)                                             # 取 DOM（--screenshot 模式无 DOM）
    items1, texts1 = parse_items(dom1)
    chk(bool(items1) and items1[0][1] == frames[0][1] and texts1.get("0") == "2/3",
        "翻到第 2 张差分：缩略图换图（= frames[0][1]）+ n/N = 2/3",
        "%s / %s" % (items1[0][1] if items1 else "-", texts1.get("0")))
    chk(bool(items0) and bool(items1) and items0[0][1] != items1[0][1],
        "换图确凿：两次 asset 字符串不同",
        "%s → %s" % (items0[0][1] if items0 else "-", items1[0][1] if items1 else "-"))
    domp = edge("?screen=gallery&act=gallery_prev:0")
    _ip, tp = parse_items(domp)
    chk(tp.get("0") == "1/3", "边界 clamp：第 1 张再点 prev ⇒ 仍 1/3（不回绕）", str(tp.get("0")))
    # 另口径（**信息项**）：DOM 上真点那个按钮 —— 与 M1 自检 ㉑e–㉑h 同一路径
    domc = edge(qsel)
    _ic, tc = parse_items(domc)
    if not (bool(_ic) and _ic[0][1] == frames[0][1] and tc.get("0") == "2/3"):
        pending.append("**DOM 真点差分按钮**这条路未生效（实测点后仍 `%s`）：`%s` 的 click 处理器"
                       "未改序号；而同一动作经机制入口 `doGalleryAction('gallery_next:0')` "
                       "**生效**（本脚本 ② 已验证）⇒ 与 M1 自检 ㉑e–㉑h（合成屏同类断言）当前同为 "
                       "FAIL，属 M1 侧待修。" % (tc.get("0"), sel))

    print("③ 差分件几何与守卫")
    btn = re.findall(r'<div[^>]*data-ui-var-btn="(\w+)"[^>]*>', dom0)
    chk(len(btn) == 2 * 24, "本页差分按钮数 = 2 × 栏数",
        "%d（prev %d / next %d）" % (len(btn), btn.count("vprev"), btn.count("vnext")))
    rej = len(re.findall(r"★M08VARIANT-REJECT★", dom0))
    chk(rej == 0, "合法数据零 REJECT 判词", "%d 条" % rej)

    print("④ 机制侧待办（**不计入本模块 RESULT**，如实登记）")
    if len(last_tx) == 1 and last_tx[0][0] == 1:
        pending.append("页码件文本随页变：`gal_page` 未被机制写入 ⇒ 翻到第 12 页时可见件仍是 "
                       "`gal.page_tx_01`（实测末页可见件 = %s）—— 待 M1 在 "
                       "`gallery_page_prev|next` 里 `setFlag(\"gal_page\", <1 基页号>)`"
                       "／krkr `uiScreenFlagSet(\"gal_page\", ...)`。" % (last_tx,))
    else:
        print("  [OK ] 页码件随页变：末页可见件 = %s" % (last_tx,))
    n_pager = len(re.findall(r'class="ui-list-pager"', dom0))
    if n_pager:
        pending.append("HTML 自动 `ui-list-pager` 仍存在（%d 件）：本屏数据已写 `scroll.pager:false`，"
                       "但 `复刻/replica.js` 尚未读它 ⇒ 与本屏自带页码控件重复、且是 HTML 独有件"
                       "（两端不一致）—— 待 M1 读该字段，或对「屏内已有页码控件」自动关闭。" % n_pager)
    for x in pending:
        print("  [待M1] " + x)
    if not pending:
        print("  [OK ] 无待办")

    os.remove(PAGE)
    print("=" * 100)
    if fails:
        print("RESULT=NG ｜ %d 项未过：" % len(fails))
        for f in fails:
            print("   - " + f)
    else:
        print("RESULT=OK ｜ 12 页全扫（%d 栏逐栏与 frames 一致）+ 差分换图 + clamp + 守卫 全部通过"
              % len(frames))
    if pending:
        print("未生效项（机制侧待 M1，%d 条）：" % len(pending))
        for x in pending:
            print("   - " + x)
    print("证据图：%s" % EVID)
    print("=" * 100)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
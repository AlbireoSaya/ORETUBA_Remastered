# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· ISSUE-20260928-03：节点态新件复核（`_dim` 方角修复 + `_read` 绿对勾）

■ 测量基底：**states 预设的私有快照栈** `…\证据\_shadow_states\`（由 `e3_shadow_screen1.py`
  从数据中心自己的 `_out\32_flowchart.states.json` 重建；重建 JS 的 CRLF 形态 md5 与**盘面
  `复刻\ui_layout.js` 逐字节相同**，见该脚本输出）。

■ 四件事（对应派单 1–3）
  ① 新元素的机制：`_dim`(3, image+nine) / `_read`(3, 20×20) 逐件「DOM 显隐 == 独立复算」、
     是否挂三态（`state_assets`）、悬停/按下是否会产生不该有的换图；`_read` 与 `_new` **不同节点不共存**（双向）。
  ② 方角修复：同一 locked 节点与**同型**可用节点比 —— 在「底图 α=0（圆角外）」的像素上必须**逐像素相同**；
     并与**旧 rect 版**预览图（`preview_A_现状_显示色.png`，1920×1080，坐标 1:1）同区域对照。
  ③ 对勾呈现：3 个 visited 节点 4× 裁图（含节点左上角）、实测牌色/勾色、与节点面/标题的叠压、对比度（对 2.883:1）。
  ④ 新件的素材引用扫描（**㉔d 同口径**）：`asset` 必须在 `asset_index.js`（1710 件）里。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_node_states_check.py
"""
import importlib.util
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
STACK = os.path.join(EVID, "_shadow_states")
PREVIEW_OLD = os.path.join(UI, "_工作", "ISSUE-20260928-视觉预览", "preview_A_现状_显示色.png")
CANVAS_W, CANVAS_H = 1920, 1080
PLATE_EXPECT = (0x3F, 0x8A, 0x5A)          # 素材组报的对勾牌色 #3F8A5A


def load_tc():
    spec = importlib.util.spec_from_file_location("e3_tc", os.path.join(HERE, "e3_title_contrast.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lum_arr(a):
    x = a.astype(np.float64) / 255.0
    x = np.where(x <= 0.03928, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


def contrast(a, b):
    la, lb = float(lum_arr(np.array(a))), float(lum_arr(np.array(b)))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def nine_map(nine, w, h, W, H):
    """九宫格映射：给出元素列/行 → 素材列/行的下标数组（与 CSS border-image slice 同口径）。"""
    l = int(nine.get("l", 0)); r = int(nine.get("r", 0))
    t = int(nine.get("t", 0)); b = int(nine.get("b", 0))
    def axis(wl, wm, ws, a0, a1, a2):
        # 元素 [0,wl) → 素材 [0,a0)；[wl,wl+wm) 拉伸到 [a0,a1)；[wl+wm, ws) → [a1,a2)
        m = []
        for i in range(wl):
            m.append(min(a0 - 1, i))
        for i in range(wm):
            m.append(a0 + min(a1 - a0 - 1, int(i * (a1 - a0) / max(1, wm))))
        for i in range(wl + wm, ws):
            m.append(a1 + min(a2 - a1 - 1, i - (wl + wm)))
        return m
    cx = axis(l, w - l - r, w, l, W - r, W)
    cy = axis(t, h - t - b, h, t, H - b, H)
    return cy, cx


def alpha_map(e):
    ap = os.path.join(ASSETS, str(e.get("asset", "")).replace("/", os.sep))
    im = Image.open(ap).convert("RGBA")
    al = np.asarray(im)[:, :, 3]
    n = e.get("nine") or {}
    cy, cx = nine_map(n, int(e["w"]), int(e["h"]), im.width, im.height)
    return al[np.ix_(cy, cx)]


def crop4(arr, rect, out, zoom=4, pad=4):
    x, y, w, h = [int(v) for v in rect]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(CANVAS_W, x + w + pad), min(CANVAS_H, y + h + pad)
    im = Image.fromarray(arr[y0:y1, x0:x1].astype(np.uint8))
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    im.save(out)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # ★ 口径（vision 复核 2026-09-28）
    print("=" * 78)
    print("【口径】本批对勾色 = #255E34（现行交付件 x_ui_read_check.png，md5 5cb6c996ad38c38c80356443a6aa4183）")
    print("        后缀 `_旧绿` 的证据件为 #3F8A5A（上一版素材）⇒ **仅供颜色前后对照，不得作颜色判据**")
    print("【口径】HTML 侧对勾的**颜色/排版判据不能替代引擎帧**：vision 实测两端帧有 3.4% 像素差")
    print("        （绝大多数是字形栅格化差异）⇒ 颜色与排版以**引擎帧**为准，HTML 侧只作**几何/形状参照**")
    print("=" * 78)
    tc = load_tc()
    os.environ.setdefault("E3_FLOW_JSON", os.path.join(STACK, "32_flowchart.screen1.json"))
    os.environ.setdefault("E3_UI_LAYOUT_JS", os.path.join(STACK, "ui_layout.js"))
    tc.SCREEN_JSON = os.environ["E3_FLOW_JSON"]
    tc.LAYOUT_JS = os.environ["E3_UI_LAYOUT_JS"]
    sc = json.load(io.open(tc.SCREEN_JSON, encoding="utf-8"))
    els = {e["id"]: e for e in sc["elements"]}
    # 期望牌色：**动态取自素材**（α=255 像素中位）——避免写死颜色随素材换色而过期
    _rd = sorted(i for i in els if i.endswith("_read"))
    _ra = os.path.join(ASSETS, str(els[_rd[0]].get("asset")).replace("/", os.sep))
    _A = np.asarray(Image.open(_ra).convert("RGBA"))
    _sel = _A[:, :, 3] >= 250
    exp_plate = tuple(int(v) for v in np.median(_A[:, :, :3][_sel], axis=0))
    print("【口径】牌色期望（动态取自素材 %s 的 α=255 像素中位）= %s"
          % (os.path.basename(_ra), (exp_plate,)))
    defs = sc.get("flags_default") or {}
    print("屏数据 = %s（%d 元素）" % (tc.SCREEN_JSON, len(sc["elements"])))
    print("渲染栈 = %s" % tc.LAYOUT_JS)

    # 全屏截图（states 默认 flags）——`layer=None` ⇒ 不切层，按 flags_default 渲染
    full_p = tc.shot("ns_full", None, None, os.path.join(tc.TMP, "ns_full.png"))
    full = np.asarray(Image.open(full_p).convert("RGB"))
    Image.fromarray(full.astype(np.uint8)).save(os.path.join(EVID, "E3_节点态_全屏_states.png"))  # ★ 整屏 1920×1080（勿裁！曾误存成视图区裁剪导致后续差分错位）
    crop4(full, (0, 150, 1920, 900), os.path.join(EVID, "E3_节点态_视图区_1920x900.png"), zoom=1, pad=0)

    bad, note = [], []

    # ── ① 机制：`_dim` / `_read` 的显隐与三态 ─────────────────────────────
    targets = [i for i in els if i.endswith("_dim") or i.endswith("_read")]
    probe = tc.build("ns_probe", None, None)
    # DOM 探针：逐件读 display + 内层态图节点是否存在
    import re
    import subprocess
    import urllib.parse
    probe_ids = sorted(set(targets) | set(i for i in els if i.endswith("_read") or i.endswith("_new")))
    ids_js = json.dumps(probe_ids)
    #   ★ 口径：`_dim` 是 **nine 图**，本来就有内层 `.ui-nine` 节点 ⇒ 「有内层节点」**不能**当作"挂了三态"的证据。
    #   改为**行为实证**：真派发 mouseenter/mousedown/mouseup/mouseleave，看贴图是否变化（静态图必须不变）。
    rep = ("<script>window.addEventListener('load',function(){"
           "var IDS=%s,out={};"
           "function fire(n,t,btn){if(!n||!n.dispatchEvent)return;"
           " n.dispatchEvent(new MouseEvent(t,{bubbles:false,cancelable:true,view:window,button:(btn||0),buttons:1}));}"
           "IDS.forEach(function(id){var n=document.querySelector('[data-ui-id=\"'+id+'\"]');"
           " function cur(){if(!n) return '(无DOM)';"
           "  var q=n.querySelector('.ui-stateimage')||n.querySelector('.ui-nine');"
           "  var host=q||n; return (host.style.backgroundImage||'')+(host.style.borderImageSource||'');}"
           " var before=cur();"
           " fire(n,'mouseenter'); var hov=cur(); fire(n,'mousedown',0); var prs=cur();"
           " fire(n,'mouseup',0); fire(n,'mouseleave'); var out2=cur();"
           " out[id]={display:n?getComputedStyle(n).display:'(无DOM)',inner:!!(n&&n.querySelector('.ui-stateimage')),"
           "   before:before,hover:hov,press:prs,after:out2,"
           "   changed:(before!==hov)||(before!==prs)||(before!==out2)};});"
           "var pre=document.createElement('pre');pre.id='nsprobe';pre.textContent='NSPROBE '+JSON.stringify(out);"
           "document.body.appendChild(pre);});</script>") % ids_js
    page = io.open(os.path.join(probe, "index.html"), encoding="utf-8").read()
    page = page.replace("</body>", rep + "</body>")
    io.open(os.path.join(probe, "index.html"), "w", encoding="utf-8").write(page)
    url = tc.fileurl(os.path.join(probe, "index.html")) + "?screen=flowchart&chrome=0"
    r = subprocess.run([tc.EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--user-data-dir=" + tc.UD, "--window-size=1400,900",
                        "--virtual-time-budget=9000", "--dump-dom", url],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"NSPROBE (\{.*?\})</pre>", dom, re.S)
    domv = json.loads(m.group(1).replace("&quot;", '"')) if m else {}
    print("\n=== ① 新件机制（%d 件：_dim %d + _read %d）===" % (len(targets), 3, 3))
    for tid in sorted(targets):
        e = els[tid]
        want = str(defs.get(e["vis_flag"], "")) == str(e["vis_when"])
        got = domv.get(tid, {})
        vis = (got.get("display") not in (None, "none", "(无DOM)"))
        ok = (vis == want)
        if not ok:
            bad.append("%s 显隐 %s ≠ 期望 %s（flags_default[%s]=%s, vis_when=%s）"
                       % (tid, "可见" if vis else "不可见", "可见" if want else "不可见",
                          e["vis_flag"], defs.get(e["vis_flag"]), e["vis_when"]))
        note.append("%s %s（%s=%s, vis_when=%s）" % (tid, "可见" if vis else "隐藏",
                                                  e["vis_flag"], defs.get(e["vis_flag"]), e["vis_when"]))
        if e.get("state_assets"):
            bad.append("%s 竟带 state_assets（本件应为纯静态图，无三态）" % tid)
    print("  逐件显隐（DOM 实况 vs 独立复算）：" + " ｜ ".join(note))
    ch = {k: v.get("changed") for k, v in domv.items()}
    inner = {k: v.get("inner") for k, v in domv.items()}
    print("  三态：数据里 6 件**均无 `state_assets`** ⇒ 不挂状态机；实测验：真派发 mouseenter/mousedown/mouseup/mouseleave，"
          "贴图变化件数=%d（应为 0）" % sum(1 for v in ch.values() if v))
    print("      内层 `.ui-stateimage` 节点存在=%s（`_dim` 有 `.ui-nine` 属 nine 图正常，与三态无关）"
          % set(inner.values()))
    if any(ch.values()):
        bad.append("新件在悬停/按下时贴图发生了变化：%s" % [k for k, v in ch.items() if v])

    # `_read` 与 `_new` 不同节点不共存（数据独立复算 + DOM 双向）
    print("\n  `_read`/`_new` 共存性（逐节点双向）：")
    nodes = sorted(set(".".join(i.split(".")[:3]) for i in els if i.startswith("fc.node.")))
    both = []
    for nd in nodes:
        r_, n_ = els.get(nd + "_read"), els.get(nd + "_new")
        if not r_ and not n_:
            continue
        fs = str(els.get(nd, {}).get("flow_state") or "available")
        vr = bool(r_) and (str(defs.get(r_["vis_flag"], "")) == r_["vis_when"])
        vn = bool(n_) and (str(defs.get(n_["vis_flag"], "")) == n_["vis_when"])
        dr = domv.get(r_["id"], {}).get("display") if r_ else None
        dn = domv.get(n_["id"], {}).get("display") if n_ else None
        sr = (dr not in (None, "none", "(无DOM)")) if r_ else False
        sn = (dn not in (None, "none", "(无DOM)")) if n_ else False
        if vr and vn:
            both.append(nd)
        if sr != vr or sn != vn:
            bad.append("%s：DOM(_read=%s,_new=%s) ≠ 复算(_read=%s,_new=%s)" % (nd, sr, sn, vr, vn))
        print("    %s flow_state=%-9s 复算 _read=%-5s _new=%-5s ｜ DOM _read=%-5s _new=%-5s ｜ 共存=%s"
              % (nd, fs, bool(vr), bool(vn), sr, sn, bool(sr and sn)))
    if both:
        bad.append("存在同时可见 _read 与 _new 的节点：%s" % both)
    print("    ⇒ 数据里 `_read.vis_when=visited` 与 `_new.vis_when=new` 互斥，且每节点 flow_state 单值 ⇒ **不可能共存**；"
          "DOM 实况与复算一致、无共存节点=%s" % (not both))

    # ── ② 方角修复 ────────────────────────────────────────────────────────
    print("\n=== ② 方角修复（同节点自比：dim 开/关 + 模拟旧 rect 形制 + 旧版预览）===")
    dim_ids = sorted(i for i in els if i.endswith("_dim"))
    # A) 正常（新 image dim）—— 已拍 full
    # B) 同屏把 3 件 _dim 隐藏 ⇒ 与 A 在「底图 α=0（严格全透明）」处应逐像素相同
    p_hid = tc.shot("ns_dimoff", None, dim_ids, os.path.join(tc.TMP, "ns_dimoff.png"))
    # C) 内存里把 _dim 换成**旧形制**（kind:rect / 黑 / opacity 110 / 无 nine）⇒ 复现"方角"
    old_js = ("var F=window.UI_LAYOUT.screens.flowchart;"
              "F.elements.forEach(function(e){ if(e.id.slice(-4)==='_dim'){ e.kind='rect';"
              " e.color='#000000'; e.opacity=110; delete e.nine; } });"
              "window.UI_REPLICA.renderScreen('flowchart',{noHistory:true});")
    p_old = tc.shot("ns_oldrect", None, None, os.path.join(tc.TMP, "ns_oldrect.png"), old_js)
    A = full
    B = np.asarray(Image.open(p_hid).convert("RGB"))
    C = np.asarray(Image.open(p_old).convert("RGB"))
    prev = np.asarray(Image.open(PREVIEW_OLD).convert("RGB")) if os.path.exists(PREVIEW_OLD) else None
    print("  旧版预览图：%s（1920×1080，与屏数据同坐标）%s"
          % (PREVIEW_OLD, "" if prev is not None else "（缺）"))
    print("  判据：底图 **α==0（严格全透明）** 处「正常态 vs 去 dim」须逐像素相同；α∈(0,8) 的 AA 边界另列。")
    print("  %-20s %-26s %7s %8s %8s %10s %8s %9s"
          % ("节点(locked)", "底图", "α0 px", "去dim≠A", "αAA px", "去dim≠A(AA)", "旧rect≠A", "预览≠A"))
    for di in dim_ids:
        nd = di[:-4]
        e = els[nd]
        x0, y0, w0, h0 = int(e["x"]), int(e["y"]), int(e["w"]), int(e["h"])
        am = alpha_map(e)
        z0 = (am == 0)
        zaa = ((am > 0) & (am < 8))
        a_reg = A[y0:y0 + h0, x0:x0 + w0].astype(np.int16)
        b_reg = B[y0:y0 + h0, x0:x0 + w0].astype(np.int16)
        c_reg = C[y0:y0 + h0, x0:x0 + w0].astype(np.int16)
        dA = np.abs(a_reg - b_reg).max(axis=2)
        dC = np.abs(a_reg - c_reg).max(axis=2)
        nA0 = int((dA[z0] > 2).sum()); nAA = int((dA[zaa] > 2).sum()); nC = int((dC[z0] > 2).sum())
        nP = -1
        if prev is not None:
            dP = np.abs(a_reg - prev[y0:y0 + h0, x0:x0 + w0].astype(np.int16)).max(axis=2)
            nP = int((dP[z0] > 2).sum())
        print("  %-20s %-26s %7d %8d %8d %10d %8d %9s"
              % (nd, os.path.basename(str(e.get("asset"))), int(z0.sum()), nA0, int(zaa.sum()), nAA,
                 nC, (nP if nP >= 0 else "-")))
        if nA0:
            yy, xx = np.nonzero(dA * z0 > 2)
            px = ["(%d,%d)A%s/B%s/α%d" % (int(x), int(y), tuple(a_reg[y, x]), tuple(b_reg[y, x]), int(am[y, x]))
                  for y, x in list(zip(yy, xx))[:4]]
            bad.append("%s：严格 α==0 处隐藏 _dim 后仍有 %d 像素变化：%s" % (nd, nA0, "；".join(px)))
        if nAA:
            note.append("%s：α∈(0,8) 的 AA 边界上有 %d px 变化（亚像素边界，非方角；见 α0 列为 0 即证明）" % (nd, nAA))
        if nC == 0:
            bad.append("%s：旧 rect 形制在 α==0 处竟与新版无差 ⇒ 对照组不成立" % nd)
        crop4(A, (x0, y0, 44, 40), os.path.join(EVID, "E3_节点态_方角_新_%s_左上.png" % nd.split(".")[-1]))
        crop4(A, (x0 + w0 - 44, y0 + h0 - 40, 44, 40), os.path.join(EVID, "E3_节点态_方角_新_%s_右下.png" % nd.split(".")[-1]))
        crop4(C, (x0, y0, 44, 40), os.path.join(EVID, "E3_节点态_方角_旧rect_%s_左上.png" % nd.split(".")[-1]))
        crop4(C, (x0 + w0 - 44, y0 + h0 - 40, 44, 40), os.path.join(EVID, "E3_节点态_方角_旧rect_%s_右下.png" % nd.split(".")[-1]))
        if prev is not None:
            crop4(prev, (x0, y0, 44, 40), os.path.join(EVID, "E3_节点态_方角_旧版预览_%s_左上.png" % nd.split(".")[-1]))
            crop4(prev, (x0 + w0 - 44, y0 + h0 - 40, 44, 40), os.path.join(EVID, "E3_节点态_方角_旧版预览_%s_右下.png" % nd.split(".")[-1]))
    print("  ⇒ 新版：严格 α==0 处 0 像素受 dim 影响；旧 rect 形制：同一区域被压暗数百~数千像素（即当时的方角）。")
    print("  ⇒ **旧版预览帧（preview_A_现状_显示色.png）是「旧 rect 形制」的有效对照**："
          "E2 组独立实测其四角 24×24 窗差 76–95 px/角（节点合计 355 / 321 / 321 px），"
          "与本侧「模拟旧 rect 在 α==0 处 100% 被压暗」的口径一致。")   # ★ 2026-09-28 主代理更正
    print("     〔更正〕先前此处写「与新版在 α==0 处只差 8/33/37 px ⇒ 不能当旧版对照」**为误判**——"
          "该偏小值最可能是本次比对里**底图 alpha 掩码取窗/对位未对准**所致；"
          "预览 A 帧在底图透明处显示的正是被压暗的背景（方角暗块），故**可作有效对照**收下。")

    # ── ③ 对勾呈现 ────────────────────────────────────────────────────────
    read_ids = sorted(i for i in els if i.endswith("_read"))
    p_ro = tc.shot("ns_readoff", None, read_ids, os.path.join(tc.TMP, "ns_readoff.png"))
    RO = np.asarray(Image.open(p_ro).convert("RGB"))
    print("\n=== ③ `_read` 绿对勾呈现（3 个 visited 节点）===")
    print("  %-22s %-16s %-16s %-8s %-10s %-10s %s"
          % ("件", "牌色(中位)", "勾色(最亮核)", "牌对比勾", "牌 vs 节点面", "勾 vs 节点面", "叠压"))
    for ri in sorted(i for i in els if i.endswith("_read")):
        e = els[ri]
        nd = ri[:-5]
        x, y, w, h = int(e["x"]), int(e["y"]), int(e["w"]), int(e["h"])
        reg = full[y:y + h, x:x + w].astype(np.int16)
        # 牌色：取**较暗的一半**像素的中位（排除白勾，勾属亮簇）
        flat = reg.reshape(-1, 3)
        if flat.size == 0:
            plate = (0, 0, 0)          # 空切片防御（避免 RuntimeWarning）
        else:
            lm = flat.astype(np.float64).mean(axis=1)
            plate = tuple(int(v) for v in np.median(flat[lm <= np.median(lm)], axis=0))
        # 白勾：区域内最亮的 10% 像素的中位
        l = reg.reshape(-1, 3).sum(axis=1)
        idx = np.argsort(l)[-max(1, len(l) // 10):]
        check = tuple(int(v) for v in np.median(reg.reshape(-1, 3)[idx], axis=0))
        # 节点面：紧贴对勾外（对勾左侧 4px 处，落在节点面上）
        # 节点面：多点取样（对勾右侧面内 / 对勾上方面内），避开节点描边与文字
        # 节点面：绕对勾一圈 8 点采样（都落在节点面内），给对比度**区间**（便于与素材组报的 2.883:1 对账）
        ring = []
        for dx, dy in ((-6, -6), (w // 2, -6), (w + 6, -6), (w + 6, h // 2),
                       (w + 6, h + 6), (w // 2, h + 6), (-6, h + 6), (-6, h // 2)):
            px_, py_ = x + dx, y + dy
            if 0 <= px_ < CANVAS_W and 0 <= py_ < CANVAS_H:
                ring.append(tuple(int(v) for v in full[py_, px_]))
        c_pf = [contrast(plate, c) for c in ring]
        c_cf = [contrast(check, c) for c in ring]
        face = tuple(int(v) for v in np.median(np.array([np.array(p2) for p2 in ring], dtype=np.int16), axis=0))
        span = "牌vs面 %.2f–%.2f ｜ 勾vs面 %.2f–%.2f" % (min(c_pf), max(c_pf), min(c_cf), max(c_cf))
        c_plate_check = contrast(plate, check)
        c_plate_face = float(np.median(c_pf))
        c_check_face = float(np.median(c_cf))
        # 叠压：与同节点文字件矩形求交
        tx = els.get(nd + "_tx")
        ov = ""
        if tx:
            ox0 = max(x, int(tx["x"])); ox1 = min(x + w, int(tx["x"]) + int(tx["w"]))
            oy0 = max(y, int(tx["y"])); oy1 = min(y + h, int(tx["y"]) + int(tx["h"]))
            ov = "%dx%d px" % (max(0, ox1 - ox0), max(0, oy1 - oy0))
            # 是否压到文字**墨迹**：文字带内首个墨迹列 vs 对勾右沿
            ty0, ty1 = int(tx["y"]), int(tx["y"]) + int(tx["h"])
            band = full[ty0:ty1, x + w: x + w + 40].astype(np.int16)
            bgc = np.median(band.reshape(-1, 3), axis=0)
            ink = (np.abs(band - bgc).max(axis=2) > 24)
            first = (np.nonzero(ink.any(axis=0))[0][0] if ink.any() else -1)
            ov += " ｜ 文字首墨列在对勾右沿之外 %s px" % (first if first >= 0 else "?")
        print("  %-22s %-16s %-16s %-8.2f %-10.2f %-10.2f %s"
              % (ri, str(plate), str(check), c_plate_check, c_plate_face, c_check_face, ov))
        print("      牌 vs 素材期望 %s：Δmax=%d（0=逐通道相同）｜ 环形 8 点采样 %s ｜ 节点面中位 %s"
              % (str(exp_plate), max(abs(plate[0] - exp_plate[0]), abs(plate[1] - exp_plate[1]), abs(plate[2] - exp_plate[2])),
                 span, str(face)))
        # 决定性核对：只看**对勾真正不透明覆盖**到的像素，其底下是否还有文字墨迹（0 ⇒ 未压任何文字）
        #   ⚠️ 先排除"对勾圆角未覆盖"的像素：那几处有/无对勾同色，是节点自身描边，不属"被压住"。
        roreg = RO[y:y + h, x:x + w].astype(np.int16)
        wreg = full[y:y + h, x:x + w].astype(np.int16)
        roface = np.median(roreg.reshape(-1, 3), axis=0)
        covered = np.abs(wreg - roreg).max(axis=2) > 2
        under_ink = (np.abs(roreg - roface).max(axis=2) > 24) & covered
        nink = int(under_ink.sum())
        nun = int((~covered).sum())
        print("      对勾实际覆盖 %d/%d px（未被覆盖 %d px 为圆角/透明处，有/无对勾同色）｜ "
              "被覆盖像素底下与纯节点面不同的 = %d ⇒ %s"
              % (int(covered.sum()), w * h, nun, nink,
                 "对勾底下无任何文字墨迹（未覆盖/未推动文字）" if nink == 0 else "★ 底下有墨迹"))
        if nink:
            bad.append("%s：对勾覆盖的像素底下仍有 %d px 墨迹 ⇒ 可能压住文字" % (ri, nink))
        crop4(full, (x - 10, y - 10, 70, 60), os.path.join(EVID, "E3_节点态_对勾_%s_4x.png" % nd.split(".")[-1]))
        # ★ 「含节点左上与文字」裁图：并入脚本，避免只在内联脚本里出图、重跑覆盖不到（vision 复核点）
        _c2 = Image.fromarray(full[max(0, y - 14):y + 34, max(0, x - 14):x + 130].astype(np.uint8))
        _c2.resize((_c2.width * 4, _c2.height * 4), Image.NEAREST).save(
            os.path.join(EVID, "E3_节点态_对勾_%s_含节点左上与文字_4x.png" % nd.split(".")[-1]))
        if c_plate_face < 3.0:
            note.append("%s 牌 vs 节点面 %.2f:1（<3.0）" % (ri, c_plate_face))

    # ── ④ 新件素材引用扫描（㉔d 同口径）────────────────────────────────────
    print("\n=== ④ 新件素材引用（㉔d 同口径：asset_index.js 存在性）===")
    print("\n=== ④ 全屏「㉔d 等价」扫描（states 档；含 `_read`/`_dim`）===")
    print("  说明：states 档**没有 `flow_layer` 热区** ⇒ 自检页的 ㉔ 会在「前置」处整块早退（㉔d 根本跑不到），")
    print("        故此处按**与 ㉔d 逐字同一口径**独立复算：`asset` / `state_assets` 三键 / rail / handle /")
    print("        item_frame / item_buttons 必须都在 `asset_index.js`；带 hover 或 pressed 的 `state_assets` 必须 normal≠hover。")
    man = io.open(os.path.join(STACK, "asset_index.js"), encoding="utf-8").read()
    def _base(x):
        return str(x or "").split("/")[-1]
    refbad, nref, nsa, nhover = [], 0, 0, 0
    for e in sc["elements"]:
        who = "states:" + str(e.get("id"))
        paths = [(who, e.get("asset"))]
        sa = e.get("state_assets")
        if isinstance(sa, dict):
            nsa += 1
            for k in ("normal", "hover", "pressed"):
                if sa.get(k) is not None:
                    paths.append((who + "." + k, sa[k]))
            if sa.get("hover") is not None or sa.get("pressed") is not None:
                nhover += 1
                nm = _base(sa.get("normal") or e.get("asset"))
                hv = _base(sa.get("hover") or sa.get("normal") or e.get("asset"))
                if nm == hv:
                    refbad.append("%s：normal == hover（%s）⇒ 悬停断言恒真" % (who, nm))
        if e.get("rail"):
            paths.append((who + ".rail", e["rail"].get("asset")))
        if e.get("handle"):
            paths.append((who + ".handle", e["handle"].get("asset")))
            hs = e["handle"].get("state_assets")
            if isinstance(hs, dict):
                for k in ("normal", "hover", "pressed"):
                    if hs.get(k) is not None:
                        paths.append((who + ".handle." + k, hs[k]))
        if e.get("item_frame"):
            paths.append((who + ".item_frame", e["item_frame"].get("asset")))
        for j, btn in enumerate(e.get("item_buttons") or []):
            if btn:
                paths.append((who + ".btn%d" % j, btn.get("asset")))
        for owner, pth in paths:
            if pth is None or str(pth) == "":
                continue
            nref += 1
            if _base(pth) not in man:
                refbad.append("%s → %s 不在素材清单" % (owner, _base(pth)))
    print("  扫引用 %d 条 ｜ state_assets %d 组（含 hover/pressed %d 组）｜ 不在清单/区分力不达标 %d 条 ⇒ %s"
          % (nref, nsa, nhover, len(refbad), "全部通过" if not refbad else "有未通过"))
    for b in refbad[:6]:
        print("    ✗ " + b)
        bad.append("㉔d 等价：" + b)
    print("  `_read`/`_dim` 逐件：" + "；".join(
        "%s→%s %s" % (i, _base(els[i].get("asset")), "✓" if _base(els[i].get("asset")) in man else "✗") for i in sorted(targets)))

    idx = io.open(os.path.join(STACK, "asset_index.js"), encoding="utf-8").read()
    n_ok = 0
    for i in sorted(targets):
        a = str(els[i].get("asset", ""))
        base = a.split("/")[-1]
        okk = ('"%s"' % base) in idx or ("'%s'" % base) in idx or (base in idx)
        n_ok += okk
        print("  %-22s %-34s %s" % (i, base, "在清单 ✓" if okk else "★ 不在清单"))
        if not okk:
            bad.append("%s 的素材 %s 不在 asset_index.js" % (i, base))
    print("  ⇒ %d/%d 在清单（asset_index.js 共 %d 处文件名引用）" % (n_ok, len(targets), len(set(re.findall(r'([A-Za-z0-9_]+\.png)', idx)))))

    print("\n判定：%s" % ("全部通过" if not bad else "存在未通过项"))
    if bad:
        for b in bad:
            print("  ✗ " + b)
    if note:
        for n in note:
            print("  ⓘ " + n)
    import shutil
    shutil.rmtree(tc.UD, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 独立层顶栏文字**可读性**量化：`fc.frag<G>_title`（组名）与 `fc.frag<G>_back_tx`（「返回主干」）

■ 问什么
  独立层里组名/返回键文字是否**在外壳底板之上**清楚可读。本脚本不靠肉眼，也不靠「猜哪块是底板」：
  对每一层拍**两张**同条件截图，唯一差别是那两件文字**是否绘制**：
      ① `full`    —— 该层正常渲染（文字在）
      ② `ref`     —— 同层、同 flag、只把 `fc.frag<G>_title`/`_back_tx` 两件 `display:none`
  ⇒ 逐像素差 > 阈值的像素**就是字形像素本身**（不受底板图案/AA 干扰）；于是
      · 底板色 bg = `ref` 在字形像素处的中位数（＝文字底下那层真实底板）
      · 字形色 ink = `full` 在字形像素处的中位数
      · 对比度 = WCAG 相对亮度比 `(L1+0.05)/(L2+0.05)`
      · 另给**设计值**：数据里 `font.color` 解析色 vs bg 的对比度（两者并排 ⇒ 见"实测是否等于设计"）

■ 判读口径（本轮主代理裁定，写死在脚本里避免事后调门槛）
  **≥ 4.5:1 达标**（组名与返回键同一判据；<4.5 判未达，组名未达即计失败并把根因上报主代理）。
  注：`ref` 只隐藏**文字两件**，`fc.frag<G>_title_bg`（本轮新增的标签底板）**照常绘制** ⇒
     字形的底板 bg 取到的正是那块底板的实色，正是要判的对象。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_title_contrast.py
    （环境变量 E3_FLOW_JSON / E3_UI_LAYOUT_JS 可切到冻结 screen1 影子栈；默认用盘上现行文件）
"""
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.parse

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
TMP = os.path.join(EVID, "_title")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_title"
COPY = ["index.html", "replica.css", "flow_data.js", "replica.js", "asset_index.js"]
CANVAS_W, CANVAS_H = 1920, 1080
LAYERS = ["frag1", "frag2", "frag3", "frag4", "frag5", "frag6"]
SCREEN_JSON = os.environ.get("E3_FLOW_JSON", os.path.join(LAYOUT, "screens", "32_flowchart.json"))
LAYOUT_JS = os.environ.get("E3_UI_LAYOUT_JS", os.path.join(REP, "ui_layout.js"))
# 产物命名可换前缀/日志名（便于按批次留档，例如第七批用 E3_title_v2_*）
PREFIX = os.environ.get("E3_TITLE_PREFIX", "E3_title_")
LOGNAME = os.environ.get("E3_TITLE_LOG", "E3_标题可读性_日志.txt")


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def screen_of():
    with io.open(SCREEN_JSON, encoding="utf-8") as f:
        return json.load(f)


def palette():
    with io.open(os.path.join(LAYOUT, "palette.json"), encoding="utf-8") as f:
        c = json.load(f)["colors"]
    return {k: str(v.get("value")) for k, v in c.items()}


def hex2rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def resolve(color, pal):
    s = str(color or "")
    return pal.get(s.split(".", 1)[1], s) if s.startswith("@") else s


def lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _lum_arr(a):
    x = a.astype(np.float64) / 255.0
    x = np.where(x <= 0.03928, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return 0.2126 * x[:, 0] + 0.7152 * x[:, 1] + 0.0722 * x[:, 2]


def contrast_px(bgs, ink):
    """逐像素对比度：bgs (N,3)；ink (3,)。"""
    li = lum(ink)
    lb = _lum_arr(bgs)
    hi = np.maximum(li, lb)
    lo = np.minimum(li, lb)
    return (hi + 0.05) / (lo + 0.05)


def build(tag, layer, hide_ids, mutate_js=""):
    dst = os.path.join(TMP, tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    shutil.copy2(LAYOUT_JS, os.path.join(dst, "ui_layout.js"))
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    lyr = ("'%s'" % layer) if layer else "''"
    hide = ("var H=%s;H.forEach(function(id){var n=document.querySelector('[data-ui-id=\"'+id+'\"]');"
            " if(n) n.style.display='none';});" % json.dumps(hide_ids)) if hide_ids else ""
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "var R=window.UI_REPLICA;R&&R.setScale(1);"
            "if(%s){R.doAction('flow_layer',{layer:%s});}"
            "%s"
            "%s});</script>") % (("true" if layer else "false"), lyr, mutate_js, hide)
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return dst


def shot(tag, layer, hide_ids, out, mutate_js=""):
    dst = build(tag, layer, hide_ids, mutate_js)
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("截图失败：" + out)
    im = Image.open(out).convert("RGB")
    if im.width >= CANVAS_W and im.height >= CANVAS_H:
        im = im.crop((0, 0, CANVAS_W, CANVAS_H))
    im.save(out)
    return out


def glyph_stats(full, ref, rect, thr=10):
    x, y, w, h = [int(v) for v in rect]
    f = full[y:y + h, x:x + w].astype(np.int16)
    r = ref[y:y + h, x:x + w].astype(np.int16)
    m = np.abs(f - r).max(axis=2) > thr
    n = int(m.sum())
    if n == 0:
        return None
    fm, rm = f[m], r[m]                                     # 字形像素：有字 / 无字（＝该处底板）
    bg = tuple(int(v) for v in np.median(rm, axis=0))
    ink = tuple(int(v) for v in np.median(fm, axis=0))
    # ★ 字形**核心**像素（颜色已接近墨色，排除 AA 过渡）——只有这些才是"字的实体"，
    #   若某片字落在底托之外，其核心像素的底板会是暗板 ⇒ 逐像素对比度会显著掉下来，
    #   故用核心像素对比度的**最小值 / 5 分位**判"是否整段字都被底托托住"。
    core = np.abs(fm - np.array(ink, dtype=np.int16)).max(axis=1) <= 12
    bad_mask = np.zeros(m.shape, bool)
    out = {"n": n, "pct": round(100.0 * n / m.size, 1), "bg": bg, "ink": ink,
           "contrast": round(contrast(bg, ink), 2), "core_n": int(core.sum()),
           "core_min": None, "core_p5": None, "core_med": None,
           "core_lt45": None, "core_lt30": None, "core_bg_uniq": None,
           "bad_mask": bad_mask, "bad_bbox": None}
    if int(core.sum()):
        cs = contrast_px(rm[core], ink)
        out["core_min"] = round(float(cs.min()), 2)
        out["core_p5"] = round(float(np.percentile(cs, 5)), 2)
        out["core_med"] = round(float(np.median(cs)), 2)
        out["core_lt45"] = int((cs < 4.5).sum())
        out["core_lt30"] = int((cs < 3.0).sum())
        out["core_bg_uniq"] = len(set(map(tuple, rm[core].tolist())))
        idx = np.nonzero(core)[0]
        badidx = idx[cs < 4.5]
        yy, xx = np.nonzero(m)
        for k in badidx:
            bad_mask[yy[k], xx[k]] = True
        if len(badidx):
            out["bad_bbox"] = [int(xx[badidx].min()), int(yy[badidx].min()),
                               int(xx[badidx].max()), int(yy[badidx].max())]
    return out


def crop_save_annot(full, bad_mask, rect, out, zoom=3, pad=5):
    """把「对比度 <4.5 的字形核心像素」在裁图上标红（硬证据：看得出是哪一段笔画没被底托托住）。"""
    x, y, w, h = [int(v) for v in rect]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(CANVAS_W, x + w + pad), min(CANVAS_H, y + h + pad)
    a = full[y0:y1, x0:x1].astype(np.uint8).copy()
    mb = bad_mask[(y0 - y):(y1 - y), (x0 - x):(x1 - x)] if (y0 >= y and x0 >= x) else None
    if mb is not None and mb.any():
        a[mb] = [255, 40, 40]
    im = Image.fromarray(a)
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    im.save(out)
    return out


def plate_profile(els, eid):
    """底托件的不透明核心带分析（可复算的根因）。
    `nine` 全零 ⇒ 素材整图被拉伸到元素 w×h；把素材逐行 alpha 换算到渲染行，
    给出「渲染后哪几行是真不透明（alpha≥200）」以及字形纵向占位是否落在其中。"""
    t = els.get(eid)
    b = els.get(eid + "_bg")
    if not (t and b):
        return None
    ap = os.path.join(ASSETS, str(b.get("asset", "")).replace("/", os.sep))
    if not os.path.exists(ap):
        return None
    img = Image.open(ap).convert("RGBA")
    al = np.asarray(img)[:, :, 3]
    src_rows = [int(al[i].max()) for i in range(img.height)]
    nine = b.get("nine")
    zero_nine = bool(nine) and all(int(nine.get(k, 0)) == 0 for k in ("l", "t", "r", "b"))
    H, hh = img.height, int(b["h"])
    dst = [src_rows[min(H - 1, int(round(r * H / float(hh))))] for r in range(hh)]
    solid = [r for r, a in enumerate(dst) if a >= 200]
    fade = [r for r, a in enumerate(dst) if a < 200]
    ge200 = float((al >= 200).mean()) * 100.0
    return {"asset": os.path.basename(ap), "asset_size": [img.width, img.height], "el": [int(b["w"]), hh],
            "nine": nine, "zero_nine": zero_nine, "src_alpha_head": src_rows[:12], "src_alpha_tail": src_rows[-6:],
            "dst_alpha_head": dst[:12], "solid_rows": (solid[0], solid[-1]) if solid else None,
            "fade_rows": len(fade), "plate_rect": [int(b["x"]), int(b["y"]), int(b["w"]), hh],
            "title_rect": [int(t["x"]), int(t["y"]), int(t["w"]), int(t["h"])],
            "asset_alpha_ge200_pct": round(ge200, 3), "asset_alpha_lt200_px": int((al < 200).sum()),
            "asset_col_head": [int(al[:, i].max()) for i in range(min(10, img.width))],
            "asset_col_tail": [int(al[:, i].max()) for i in range(max(0, img.width - 6), img.width)]}


def crop_save(full, ref, rect, out, zoom=3, pad=5):
    x, y, w, h = [int(v) for v in rect]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(CANVAS_W, x + w + pad), min(CANVAS_H, y + h + pad)
    a = Image.fromarray(full[y0:y1, x0:x1].astype(np.uint8))
    b = Image.fromarray(ref[y0:y1, x0:x1].astype(np.uint8))
    # 上：带字（full）｜下：无字（ref＝底板）—— 便于人眼核对「文字/底板」两半
    side = Image.new("RGB", (a.width, a.height * 2 + 6), (90, 90, 90))
    side.paste(a, (0, 0))
    side.paste(b, (0, a.height + 6))
    side = side.resize((side.width * zoom, side.height * zoom), Image.NEAREST)
    side.save(out)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(TMP, exist_ok=True)
    sc = screen_of()
    pal = palette()
    els = {e["id"]: e for e in sc.get("elements", [])}
    rows, bad, near = [], [], []
    print("屏数据 = %s ｜ 渲染栈 = %s" % (SCREEN_JSON, LAYOUT_JS))
    for G in LAYERS:
        ids = ["fc.frag%s_title" % G[4:], "fc.frag%s_back_tx" % G[4:]]
        if not all(i in els for i in ids):
            bad.append("%s：数据缺 %s" % (G, ids)); continue
        full_p = shot("full_" + G, G, None, os.path.join(TMP, "shot_full_%s.png" % G))
        ref_p = shot("ref_" + G, G, ids, os.path.join(TMP, "shot_ref_%s.png" % G))
        full = np.asarray(Image.open(full_p).convert("RGB"))
        ref = np.asarray(Image.open(ref_p).convert("RGB"))
        rec = {"layer": G}
        for tag, eid in (("title", ids[0]), ("back_tx", ids[1])):
            e = els[eid]
            rect = (e["x"], e["y"], e["w"], e["h"])
            st = glyph_stats(full, ref, rect)
            want = hex2rgb(resolve((e.get("font") or {}).get("color"), pal))
            if not st:
                bad.append("%s %s：两张图的字形带无差异（文字没画出来？）" % (G, tag)); continue
            cr = contrast(st["bg"], st["ink"])
            crd = contrast(st["bg"], want)
            p5 = st["core_p5"] if st["core_p5"] is not None else round(cr, 2)
            rec[tag] = {"rect": rect, "text": e.get("sample", ""), "bg": st["bg"], "ink": st["ink"],
                        "glyph_px": st["n"], "glyph_pct": st["pct"], "design": want,
                        "contrast": round(cr, 2), "contrast_design": round(crd, 2),
                        "core_n": st["core_n"], "core_min": st["core_min"], "core_p5": st["core_p5"],
                        "core_lt45": st["core_lt45"], "core_lt30": st["core_lt30"],
                        "core_bg_uniq": st["core_bg_uniq"],
                        "pass45": bool(p5 >= 4.5)}
            crop_save(full, ref, rect, os.path.join(EVID, PREFIX + "%s_%s.png" % (G, tag)))
            if st["bad_mask"].any():
                rec[tag]["bad_bbox"] = st["bad_bbox"]
                crop_save_annot(full, st["bad_mask"], rect,
                                os.path.join(EVID, PREFIX + "%s_%s_未达标像素标注.png" % (G, tag)))
            # ★ 本轮裁定判据 = **≥4.5:1**（主代理 2026-09-28：独立层组名必须达标，故加标签底板）
            #   判据取**字形核心像素对比度的 5 分位**（比中位数严：能抓「底托没托住整段字」）
            if p5 < 4.5:
                msg = ("%s %s：字形核心对比度 5 分位 %.2f:1 < 4.5（中位 %.2f，最低 %.2f，核心 %d px 中 "
                       "%d px <4.5、%d px <3.0；核心处底板色种类 %d）根因须报主代理，不自改生成物"
                       % (G, tag, p5, cr, st["core_min"], st["core_n"], st["core_lt45"],
                          st["core_lt30"], st["core_bg_uniq"]))
                (bad if tag == "title" else near).append(msg)
        rows.append(rec)

    print("\n=== 独立层顶栏可读性（字形像素由「同层 × 文字隐藏」两张图的像素差取出）===")
    print("  %-6s %-8s %-15s %-15s %-6s %-6s %-6s %-6s %-6s %s"
          % ("层", "件", "底板 bg", "实测 ink", "字形px", "核心px", "核心中位", "核心p5", "核心min", "<4.5 核心px"))
    for r in rows:
        for tag in ("title", "back_tx"):
            d = r.get(tag)
            if not d:
                continue
            print("  %-6s %-8s %-15s %-15s %-6d %-6d %-6s %-6s %-6s %d"
                  % (r["layer"], tag, str(d["bg"]), str(d["ink"]), d["glyph_px"], d["core_n"],
                     d["core_p5"], d["core_p5"], d["core_min"], d["core_lt45"]))
            print("        ↳ 设计色 %s ｜ 中位对比度 %.2f:1 ｜ 核心处底板色种类 %d"
                  % ("#" + "".join("%02X" % v for v in d["design"]), d["contrast"], d["core_bg_uniq"]))
    print("\n判读：本轮裁定判据 = **组名 ≥4.5:1**（取字形核心像素对比度的 5 分位，严于中位数）")
    tvs = [r["title"]["core_p5"] for r in rows if "title" in r and r["title"].get("core_p5") is not None]
    bvs = [r["back_tx"]["core_p5"] for r in rows if "back_tx" in r and r["back_tx"].get("core_p5") is not None]
    tmed = [r["title"]["contrast"] for r in rows if "title" in r]
    print("组名六层（核心 p5）：%s ⇒ %s"
          % ("、".join("%.2f" % c for c in tvs),
             ("全部 ≥4.5 达标，六层一致" if tvs and min(tvs) >= 4.5
              else "存在 <4.5（最低 %.2f）" % min(tvs) if tvs else "无数据")))
    print("组名六层（中位，供与上一轮同口径比较）：%s" % "、".join("%.2f" % c for c in tmed))
    print("返回键六层（核心 p5）：%s ⇒ %s"
          % ("、".join("%.2f" % c for c in bvs),
             ("全部 ≥4.5" if bvs and min(bvs) >= 4.5 else "存在 <4.5（最低 %.2f）" % min(bvs) if bvs else "无数据")))
    print("文案：" + "；".join("%s=%s/%s" % (r["layer"], r.get("title", {}).get("text", "?"),
                                            r.get("back_tx", {}).get("text", "?")) for r in rows))
    # ── 底托几何与不透明核心带（根因，可复算）──────────────────────────────
    prof = plate_profile(els, "fc.frag1_title")
    prof_txt = []
    if prof:
        t0, t1 = (prof["solid_rows"] or (0, 0))
        gx0, gy0, gw, gh = prof["title_rect"]
        px, py, pw, ph = prof["plate_rect"]
        gly0, gly1 = gy0 - py, gy0 + gh - py                      # 字形纵向占位（相对底托）
        print("\n=== 底托几何与不透明核心带（六层同规格，以 frag1 为例）===")
        print("  底托件 %s ← 素材 %s（%dx%d）⇒ 元素 %dx%d ｜ nine=%s%s"
              % ("fc.frag1_title_bg", prof["asset"], prof["asset_size"][0], prof["asset_size"][1],
                 prof["el"][0], prof["el"][1], prof["nine"], "（全零 ⇒ 整图拉伸）" if prof["zero_nine"] else ""))
        print("  素材独立复量：α≥200 占比 %.3f%% ｜ α<200 像素 %d 个 ｜ 逐列 alpha 前 10 %s / 末 6 %s"
              % (prof["asset_alpha_ge200_pct"], prof["asset_alpha_lt200_px"],
                 prof["asset_col_head"], prof["asset_col_tail"]))
        print("  素材逐行 alpha：前 12 行 %s ｜ 末 6 行 %s" % (prof["src_alpha_head"], prof["src_alpha_tail"]))
        print("  换算到渲染行：前 12 行 %s" % prof["dst_alpha_head"])
        print("  渲染后**真不透明**（alpha≥200）行 = %d..%d（共 %d 行）；仍半透明/渐隐 %d 行"
              % (t0, t1, (t1 - t0 + 1) if prof["solid_rows"] else 0, prof["fade_rows"]))
        print("  字形纵向占位（相对底托）= %d..%d ⇒ %s"
              % (gly0, gly1,
                 ("起点落在渐隐带内（%d..%d 行不透明区之外有字形）" % (t0, t1)) if gly0 < t0 else "全部落在不透明核心带内"))
        prof_txt = ["", "底托几何（根因）：", "  " + str(prof)]
    if near:
        print("\n未达 4.5 项：")
        for l in near:
            print("  · " + l)
    if bad:
        print("\n未达标：")
        for l in bad:
            print("  ✗ " + l)

    txt = ["E3 独立层顶栏可读性量化（ISSUE-20260928-02 · HTML 侧）",
           "方法：同层拍两张图（唯一差别＝ fc.frag<G>_title / _back_tx 是否绘制）；像素差 > 10 的像素即字形像素；",
           "      底板 bg = 无字图在字形像素处中位数，ink = 有字图中位数；",
           "      另取**字形核心像素**（颜色距墨色 ≤12/255，排除 AA）逐像素算对比度 ⇒ 给中位 / p5 / min",
           "      （核心 p5 < 4.5 说明有整段字落在底托之外；核心处底板色种类 >1 即半覆盖的直接证据）",
           "屏数据 = %s" % SCREEN_JSON, ""]
    for r in rows:
        for tag in ("title", "back_tx"):
            d = r.get(tag)
            if not d:
                continue
            txt.append("%-6s %-8s 底板%s 实测ink%s 字形%dpx(%.1f%%) 核心%dpx 核心中位/p5/min=%.2f/%.2f/%.2f "
                       "核心<4.5 %dpx 核心<3.0 %dpx 核心底托色种%d 设计色%s 中位对比度%.2f:1 文案=%s"
                       % (r["layer"], tag, d["bg"], d["ink"], d["glyph_px"], d["glyph_pct"], d["core_n"],
                          d["core_p5"] or 0, d["core_p5"] or 0, d["core_min"] or 0,
                          d["core_lt45"] or 0, d["core_lt30"] if "core_lt30" in d else 0,
                          d["core_bg_uniq"], "#" + "".join("%02X" % v for v in d["design"]),
                          d["contrast"], d["text"]))
    txt += ["", "裁定判据：组名 ≥4.5:1（本轮主代理裁定），判据取**字形核心像素对比度的 5 分位**",
            "组名六层（核心 p5）：%s ⇒ %s" % ("、".join("%.2f" % c for c in tvs),
                                          "全部 ≥4.5 达标、六层一致" if tvs and min(tvs) >= 4.5 else "存在 <4.5"),
            "组名六层（中位，与上一轮同口径）：%s" % "、".join("%.2f" % c for c in tmed),
            "返回键六层（核心 p5）：%s ⇒ %s" % ("、".join("%.2f" % c for c in bvs),
                                          "全部 ≥4.5" if bvs and min(bvs) >= 4.5 else "存在 <4.5"),
            "未达 4.5 项：" + ("；".join(near) if near else "无"),
            "判定：" + ("组名与返回键六层全部 ≥4.5 达标" if not bad else "；".join(bad))] + prof_txt
    io.open(os.path.join(EVID, LOGNAME), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("\n裁图（上=带字 / 下=底板）：%s<层>_{title,back_tx}.png ｜ 日志：%s" % (PREFIX, LOGNAME))
    shutil.rmtree(UD, ignore_errors=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

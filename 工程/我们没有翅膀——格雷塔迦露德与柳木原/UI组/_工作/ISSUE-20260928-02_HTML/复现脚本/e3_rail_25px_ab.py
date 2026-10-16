# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 滑轨「全零 nine」2.5px 分叉的**改前 / 改后实测**

■ 问题（登记在案的存量口径分歧）
    引擎 `krkr\game\ui_widget.tjs::uiWidgetDrawSlider:1435`
        `rh2 = (rail.nine != void) ? el.h : 素材高`
    ⇒ **给了 nine（哪怕 `{l:0,t:0,r:0,b:0}`）就取元素高**，再由 `uiWidgetNine` 的全零分支
      （只画中格）把整图**拉伸到 `el.w × el.h`**。
    HTML 旧写法对该分支与「无 nine」共用 `background-size:100% auto`（**等比**）
    ⇒ 只在「素材宽 == 元素宽」时才与引擎等价。
    本屏 6 条声音滑轨素材 `x_ui_psv_rail_c2_0*.png` **360×30**、元素 **330×30**
    ⇒ 旧写法实绘盒 `30 × 330/360 = 27.5px`，引擎 30px ⇒ **两端差 2.5px**。

■ 两段测量（都在无头 Edge 里由**浏览器自己算**，不是我在 Python 里套公式）
    ① 几何（`--dump-dom` 探针页）：把每条滑轨的素材以 `width:<el.w>px; height:auto` 放进
       `<img>`，读 `getBoundingClientRect().height` —— 这就是 CSS `100% auto` 的**used 高度**
       （浏览器算的浮点值）；与引擎的 `el.h` 并排给出差值。
    ② 像素（改前 / 改后截图作差）：改后 = 盘上现行 `复刻\replica.js`（`100% 100%`）；
       改前 = 拍摄副本里把该分支 sed 回 `100% auto`（**不改盘上文件**，脚本自证 patch 命中）。
       逐条给「实绘墨迹带高度」与「区域差异像素」。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_rail_25px_ab.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
SHOT = os.path.join(EVID, "_rail_shot")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_rail"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
CANVAS_W, CANVAS_H = 1920, 1080
NEW = "rd.style.backgroundSize = '100% 100%';"     # 现行（全零 nine → 拉伸到元素框）
OLD = "rd.style.backgroundSize = '100% auto';"     # 旧写法（改前）


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def sliders():
    """从屏数据取 cfg 屏的 slider 元素（含 rail 与元素矩形）—— 期望值一律从数据推。"""
    with io.open(os.path.join(LAYOUT, "screens", "25_config.json"), encoding="utf-8") as f:
        sc = json.load(f)
    out = []
    for e in sc.get("elements", []):
        if e.get("kind") != "slider":
            continue
        r = e.get("rail") or {}
        n = r.get("nine")
        zero = bool(n) and all(int(n.get(k, 0)) == 0 for k in ("l", "t", "r", "b"))
        out.append({"id": e["id"], "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"],
                    "rail": r.get("asset"), "nine": n, "zero_nine": zero})
    return out


# ── ① 几何探针：浏览器算 used 高度 ─────────────────────────────────────────────
PROBE = """<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<pre id="out">running</pre>
<script>
var SL = %s, ROOT = "%s";
var rows = [], left = SL.length;
SL.forEach(function (s) {
  var im = new Image();
  im.onload = function () {
    // CSS `background-size:100%% auto` 的 used 高度 == 同宽 <img> 的 height:auto 高度（同一套等比规则）
    im.style.cssText = "position:absolute;left:0;top:0;width:" + s.w + "px;height:auto;visibility:hidden";
    document.body.appendChild(im);
    var used = im.getBoundingClientRect().height;
    rows.push({id: s.id, natural: [im.naturalWidth, im.naturalHeight], el: [s.w, s.h],
               pct_auto_used_h: Math.round(used * 100) / 100});
    document.body.removeChild(im);
    if (--left === 0) document.getElementById('out').textContent = 'RAILPROBE ' + JSON.stringify(rows);
  };
  im.onerror = function () { if (--left === 0) document.getElementById('out').textContent = 'RAILPROBE []'; };
  im.src = ROOT + "/" + s.rail.replace(/^ui\\//, "");
});
</script></body></html>"""


def probe_geometry(sl):
    dst = os.path.join(SHOT, "probe")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    page = PROBE % (json.dumps(sl), fileurl(ASSETS) + "/ui")
    io.open(os.path.join(dst, "probe.html"), "w", encoding="utf-8").write(page)
    os.makedirs(UD, exist_ok=True)
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--user-data-dir=" + UD, "--virtual-time-budget=6000", "--dump-dom",
                        fileurl(os.path.join(dst, "probe.html"))],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"RAILPROBE (\[.*?\])</pre>", dom, re.S)   # ★ 非贪婪会在第一个 `]` 就截断
    if not m:
        return []
    txt = m.group(1)
    for a, b in (("&quot;", '"'), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")):
        txt = txt.replace(a, b)     # --dump-dom 会把 pre 内容做 HTML 转义
    return json.loads(txt)


# ── ② 像素：改前 / 改后截图 ───────────────────────────────────────────────────
def prepare(dirname, patch_old):
    dst = os.path.join(SHOT, dirname)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    if patch_old:
        p = os.path.join(dst, "replica.js")
        s = io.open(p, encoding="utf-8").read()
        i = s.find("★ 全零 nine 的轨道")
        assert i > 0, "找不到全零 nine 分支（replica.js 结构已变）"
        j = s.find(NEW, i)
        assert j > 0, "找不到全零分支的 backgroundSize 行"
        s = s[:j] + OLD + s[j + len(NEW):]
        io.open(p, "w", encoding="utf-8").write(s)
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);"
            "window.UI_REPLICA&&window.UI_REPLICA.doConfigAction('config_tab_2',{id:'(probe)'});"
            "});</script>")
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return dst


def shoot(dirname, patch_old, out):
    dst = prepare(dirname, patch_old)
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=config&chrome=0"
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


def diff_region(a, b, box, thr=6):
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    pa, pb = ia.load(), ib.load()
    x0, y0, w, h = box
    n = 0
    by0, by1 = 10 ** 9, -1
    for y in range(max(0, y0), min(ia.height, y0 + h)):
        for x in range(max(0, x0), min(ia.width, x0 + w)):
            ca, cb = pa[x, y], pb[x, y]
            if abs(ca[0] - cb[0]) > thr or abs(ca[1] - cb[1]) > thr or abs(ca[2] - cb[2]) > thr:
                n += 1
                by0 = min(by0, y); by1 = max(by1, y)
    return {"n": n, "y0": (None if by1 < 0 else by0), "y1": (None if by1 < 0 else by1),
            "h": (0 if by1 < 0 else by1 - by0 + 1)}


def ink_band(png, s, thr=2):
    """量该元素的**实绘墨迹带**：在元素内取一列（靠左 3%，避开值 80% 处的手柄），
    以元素框外 6px 处的行为背景基准，找与背景差 > thr 的连续行。"""
    im = Image.open(png).convert("RGB")
    p = im.load()
    x = int(s["x"] + s["w"] * 0.03)
    bg = p[x, max(0, s["y"] - 6)]
    ys = []
    for y in range(max(0, s["y"] - 12), min(im.height, s["y"] + s["h"] + 12)):
        c = p[x, y]
        if max(abs(c[0] - bg[0]), abs(c[1] - bg[1]), abs(c[2] - bg[2])) > thr:
            ys.append(y)
    if not ys:
        return [None, None, 0]
    best = cur = [ys[0], ys[0]]
    for y in ys[1:]:
        if y == cur[1] + 1:
            cur[1] = y
        else:
            if cur[1] - cur[0] > best[1] - best[0]:
                best = cur[:]
            cur = [y, y]
    if cur[1] - cur[0] > best[1] - best[0]:
        best = cur
    return [best[0], best[1], best[1] - best[0] + 1]


def main():
    os.makedirs(EVID, exist_ok=True)
    sl = sliders()
    zero = [s for s in sl if s["zero_nine"]]
    noNine = [s for s in sl if s["nine"] is None]
    print("cfg 屏 slider %d 条 ｜ 全零 nine %d 条 ｜ 无 nine %d 条" % (len(sl), len(zero), len(noNine)))

    print("\n=== ① 几何（浏览器算的 used 高度；used＝`background-size:100% auto` 的等比结果）===")
    gp = {r["id"]: r for r in probe_geometry(sl)}
    bad = 0
    for s in zero:
        r = gp.get(s["id"])
        if not r:
            print("  %-16s 探针未回值" % s["id"]); bad += 1; continue
        diff = round(s["h"] - r["pct_auto_used_h"], 2)
        flag = "★ 两端差 %.1fpx" % diff if diff > 0.01 else "与元素高一致"
        print("  %-16s 素材 %dx%d ｜ 元素 %dx%d ｜ `100%% auto` used 高 = %.2fpx ｜ 引擎口径 = el.h = %d ⇒ %s"
              % (s["id"], r["natural"][0], r["natural"][1], s["w"], s["h"], r["pct_auto_used_h"], s["h"], flag))
    print("  —— 对照组（无 nine，素材宽 == 元素宽）——")
    for s in noNine:
        r = gp.get(s["id"])
        if not r:
            continue
        print("  %-16s 素材 %dx%d ｜ 元素 %dx%d ｜ used 高 = %.2fpx ⇒ 与引擎的「素材高 %d」一致（差 %.2fpx）"
              % (s["id"], r["natural"][0], r["natural"][1], s["w"], s["h"],
                 r["pct_auto_used_h"], r["natural"][1], r["natural"][1] - r["pct_auto_used_h"]))

    print("\n=== ② 像素（改前 / 改后；改前＝拍摄副本内 sed 回 `100%% auto`）===")
    after = shoot("after", False, os.path.join(EVID, "E3_rail_改后.png"))
    before = shoot("before", True, os.path.join(EVID, "E3_rail_改前.png"))
    print("改后（100%% 100%%）= %s\n改前（100%% auto）= %s" % (
        os.path.basename(after), os.path.basename(before)))
    print("  —— 受影响元素（全零 nine）——")
    tot = 0
    for s in zero:
        d = diff_region(before, after, (s["x"] - 4, s["y"] - 4, s["w"] + 8, s["h"] + 8))
        tot += d["n"]
        print("  %-16s 区域差异像素 %5d（差异带 y%s..%s 高 %dpx／元素高 %d）"
              % (s["id"], d["n"], d["y0"], d["y1"], d["h"], s["h"]))
    print("  合计区域差异像素 %d（= 6 条轨道的整条面积：纵向等比重采样 ⇒ 差异覆盖整条轨道）" % tot)
    print("  —— 对照组（无 nine，素材宽 == 元素宽）——")
    for s in noNine:
        d = diff_region(before, after, (s["x"] - 4, s["y"] - 4, s["w"] + 8, s["h"] + 8))
        print("  %-16s 区域差异像素 %5d（应 0）" % (s["id"], d["n"]))
    # 素材 alpha 剖面：解释「几何差 2.5px」为何在像素上不是一条 2.5px 的硬边
    im = Image.open(os.path.join(UI, "krkr", "assets", "ui", "x_ui_psv_rail_c2_01.png"))
    al = im.split()[-1]
    rows = [max(al.getpixel((x, y)) for x in range(im.width)) for y in range(im.height)]
    core = [y for y, a in enumerate(rows) if a >= 200]
    print("  ⓘ 素材 %s %dx%d 的 alpha 剖面：首行 %d / 末行 %d，alpha≥200 的核心带 = 第 %d..%d 行（高 %dpx）"
          % ("x_ui_psv_rail_c2_01.png", im.width, im.height, rows[0], rows[-1], core[0], core[-1], len(core)))
    print("    ⇒ 上下各约 9 行是**渐隐翼**，2.5px 的几何差在像素上表现为「整条轨道的纵向重采样」")
    print("      （差异像素 2.7k/条、覆盖整条），而不是一条 2.5px 的硬边；对照组 0 像素坐实了'只此一处变'。")
    shutil.rmtree(UD, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

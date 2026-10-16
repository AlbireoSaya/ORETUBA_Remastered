# -*- coding: utf-8 -*-
r"""ISSUE-20260927-05 · E3（HTML 复刻端连线 `links`）自证探针。

■ 依据
    `_工作\ISSUE-20260927-05_流程图实现\边与节点数据契约.md`（v1.1）§三
    + `复刻\replica.js` §4.9（E3 新增的 `links` 渲染）
    + `复刻\_selftest_states.html` 的 ㉒（自检断言）

■ 三件事
  ① **自检断言**：无头 Edge 跑 `_selftest_states.html`，看 ㉒ 的判决；并用
     `?links=badpt` / `?links=degen` 两个负向对照证明断言**有牙齿**（有意改坏 ⇒ 必须 FAIL）。
  ② **夹具几何的唯一来源**：`?links=dump` 让自检页把内存夹具的 links 原样吐出来，
     拍摄副本直接注入这份 JSON ⇒ 夹具几何只有一处定义（不会与自检页分叉）。
  ③ **像素级自证**（不信「HTML 看起来对」）：同一临时副本渲染两次 ——
       A：把 `flowchart.links` 强制清空的基线；B：带 links（真实数据优先，否则夹具）。
       `diff = B − A` 即**只由连线层产生的像素**（本工程 M39 定下的作差口径），
       再逐条核对：折线覆盖率 / 线宽 == w / 箭头三角的朝向·底边半宽·填充面积 /
       非箭头链接末端宽度 / 差异像素不外溢到几何之外。

■ 用法
    python _工作\ISSUE-20260927-05_流程图实现\复现脚本\E3_links_probe.py
    退出码 0 = 全部符合期望。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)                        # …\ISSUE-20260927-05_流程图实现
UI = os.path.dirname(os.path.dirname(MOD))         # …\UI组
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(MOD, "取证")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_e3"

COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]

# 拍摄页钩子：隐藏页面外壳 + 强制 1:1（与 i03 同款；只在临时副本里注入）
HOOK = """
<style>
.shell{max-width:none!important;padding:0!important;margin:0!important}
.shell-head,.shell-foot{display:none!important}
#stage-wrap{justify-content:flex-start!important;display:block!important}
#stage{box-shadow:none!important}
</style>
<script>
window.addEventListener('load', function () {
  if (window.UI_REPLICA && window.UI_REPLICA.setScale) window.UI_REPLICA.setScale(1);
});
</script>
"""


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def edge(url, dump=True, window="1400,900", budget=15000):
    os.makedirs(UD, exist_ok=True)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=" + window, "--virtual-time-budget=%d" % budget]
    if dump:
        cmd.append("--dump-dom")
    cmd.append(url)
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace")


def verdict_text(dom):
    i = dom.find('id="verdict"')
    if i < 0:
        return ""
    j = dom.find("</div>", i)
    return dom[i:j if j > 0 else i + 400000]


# ────────────────────────────── ① 自检断言 + 负向对照 ──────────────────────────────
SELFTEST_MODES = [("", "ALL PASS"), ("fixture", "ALL PASS"),
                  ("badpt", "MUST FAIL"), ("degen", "MUST FAIL")]


def run_selftests():
    print("=" * 96)
    print("① 自检 ㉒（links 渲染）＋ 负向对照")
    print("=" * 96)
    ok = True
    for mode, want in SELFTEST_MODES:
        q = ("?links=" + mode) if mode else ""
        dom = edge(fileurl(os.path.join(REP, "_selftest_states.html")) + q)
        vt = verdict_text(dom)
        m = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", vt)
        got = m.group(1) if m else "(未找到判定)"
        line22 = re.search(r"SELFTEST (OK|FAIL) +㉒ [^<\n]*", vt)
        is_fail22 = bool(line22) and line22.group(1) == "FAIL"
        crashed = "执行期异常" in vt
        notes = re.findall(r"SELFTEST NOTE [^<\n]*", vt)
        # ★ 判定期望必须落到**㉒ 那一行**：只判「不是 ALL PASS」会把
        #   「夹具自身崩了（执行期异常）」误读成「断言有牙齿」（首版实测栽过：
        #   badpt 分支引用了已改名变量 ⇒ run() 抛 ReferenceError，判决恰好也是 FAILED）。
        if want == "ALL PASS":
            good = (got == "ALL PASS") and not crashed
        else:
            good = is_fail22 and not crashed
        ok = ok and good
        print("-" * 96)
        print("[%-8s] 期望 %-10s 实得 %-16s %s" % (mode or "(无)", want, got, "✓" if good else "✗ 与期望不符"))
        print("   ㉒：" + (line22.group(0).strip() if line22 else "(未找到 ㉒ 行)"))
        for n in notes[:3]:
            print("   " + n.strip())
        if got != "ALL PASS":
            for f in re.findall(r"SELFTEST FAIL [^<\n]*", vt)[:6]:
                print("   " + f.strip())
    return ok


# ────────────────────────────── ①b 层序判据的变异自证（临时副本） ──────────────────────────────
# ★ ISSUE-20260927-05 二审（层序统一）：断言「阈值 == min(节点普通 z)−1」与「逐元素：普通 z < 阈值
#   ⟺ 在连线之下」不可能被**数据**变异触发（渲染与断言读同一份数据 ⇒ 自洽），故必须变异**机制**。
#   做法沿用本工程既有惯例（i03「修前夹具」/ m02 的 `?mut=`）：把 `复刻\` 复制到临时目录，
#   对 **副本的 replica.js** 做**定点文本替换**（命中数必须 == 1，否则夹具失效即报错），
#   再跑自检页；㉒ 必须 FAIL。三种变异各打一个判据：
#     zoffby1  阈值少减 1（`min(节点 z) − 1` → `min(节点 z)`）      ⇒ 判据①（阈值）必须报警
#     zoldrule 阈值换成**旧 HTML raw 口径**（min(节点 raw z) − 1）   ⇒ 判据① 必须报警
#     zcanvas  阈值不动、**层号折算**换成旧 raw 口径                ⇒ 判据③（逐元素错侧）必须报警
ZMUT = {
    "zoffby1": ("    if (nodeMin !== null) return nodeMin - 1;",
                "    if (nodeMin !== null) return nodeMin;"),
    "zoldrule": ("    if (nodeMin !== null) return nodeMin - 1;",
                 "    if (nodeMin !== null) { var _m = null;\n"
                 "      for (var _i = 0; _i < els.length; _i++) { var _e = els[_i];\n"
                 "        if (_e && String(_e.id || '').indexOf('fc.node.') === 0) {\n"
                 "          var _r = Number(_e.z) * 100 + _i; if (_m === null || _r < _m) _m = _r; } }\n"
                 "      return _m; }"),
    "zcanvas": ("    if (aboveMin !== null) return aboveMin - 1;", None),   # 替换见下（多行）
}


def selftest_dir(zmut=None, drop_line_spacing=False):
    """临时副本：全部 `复刻\` 文件 + 可选的两类定点变异。返回 index 页所在目录。"""
    tag = (zmut or "clean") + ("_nols" if drop_line_spacing else "")
    dst = os.path.join(EVID, "E3_selftest_" + tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY + ["_selftest_states.html"]:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    if zmut:
        if zmut not in ZMUT:
            raise SystemExit("未知 zmut：" + zmut)
        src = ZMUT[zmut][0]
        rp = os.path.join(dst, "replica.js")
        s = io.open(rp, encoding="utf-8").read()
        n = s.count(src)
        if n != 1:
            raise SystemExit("变异夹具失效：%s 的锚点命中 %d/1 —— 请同步更新本脚本" % (zmut, n))
        if zmut == "zcanvas":
            # 层号折算换成旧口径：取「节点族 min(raw z) − 1」
            anchor = "    if (aboveMin !== null) return aboveMin - 1;"
            repl = ("    var _m = null;\n"
                    "    for (var _i = 0; _i < els.length; _i++) { var _e = els[_i];\n"
                    "      if (_e && String(_e.id || '').indexOf('fc.node.') === 0) {\n"
                    "        var _r = Number(_e.z) * 100 + _i; if (_m === null || _r < _m) _m = _r; } }\n"
                    "    if (_m !== null) return _m - 1;\n"
                    "    if (aboveMin !== null) return aboveMin - 1;")
            s = s.replace(anchor, repl)
        else:
            s = s.replace(src, ZMUT[zmut][1])
        io.open(rp, "w", encoding="utf-8").write(s)
    if drop_line_spacing:
        # 负向对照：把**布局数据**里的元素级 line_spacing 删掉 ⇒ lineHeight 应回落基线 1.4×字号
        lp = os.path.join(dst, "ui_layout.js")
        s = io.open(lp, encoding="utf-8").read()
        n = s.count('"line_spacing": 1.0')
        if n < 1:
            raise SystemExit("line_spacing 负向对照夹具失效：ui_layout.js 里没有 \"line_spacing\": 1.0")
        s = s.replace('"line_spacing": 1.0', '"line_spacing__dropped": 1.0')
        io.open(lp, "w", encoding="utf-8").write(s)
    return dst


def run_selftest_at(directory, query=""):
    return edge(fileurl(os.path.join(directory, "_selftest_states.html")) + query)


def zmut_proof():
    print("=" * 96)
    print("①b 层序判据的变异自证（改**机制**，不是改数据 —— 阈值/折算各挪一档 ⇒ ㉒ 必须报警）")
    print("=" * 96)
    ok = True
    for zmut, why in (("zoffby1", "阈值少减 1（min(节点 z)−1 → min(节点 z)）"),
                      ("zoldrule", "阈值换成旧 HTML raw 口径（min(节点 raw z)−1）"),
                      ("zcanvas", "阈值不动、层号折算换成旧 raw 口径")):
        d = selftest_dir(zmut)
        dom = run_selftest_at(d)
        vt = verdict_text(dom)
        got = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", vt)
        got = got.group(1) if got else "(未找到判定)"
        line = re.search(r"SELFTEST (OK|FAIL) +㉒ [^<\n]*", vt)
        is_fail = bool(line) and line.group(1) == "FAIL"
        good = is_fail and ("执行期异常" not in vt)
        ok = ok and good
        print("-" * 96)
        print("[%-9s] %s" % (zmut, why))
        print("           判定 %-16s %s" % (got, "✓ 断言有牙齿" if good else "✗ 断言未报警"))
        print("           " + (line.group(0).strip()[:300] if line else "(未找到 ㉒ 行)"))
        shutil.rmtree(d, ignore_errors=True)
    return ok


# ────────────────────────────── ①c 元素级 line_spacing 生效自证 ──────────────────────────────
def line_spacing_proof():
    """读**已渲染 DOM** 的 inline style：`_tx` 的 `.ui-text-inner` 的 lineHeight 应 = 字号 ×
    元素级 `line_spacing`（新数据 19 × 1.0 = 19px），而不是基线 1.4（26.6px）。
    负向对照：把布局数据里的该键改名 ⇒ lineHeight 必须回落到 19×1.4=26.6px（证明 19px 来自该键）。"""
    print("=" * 96)
    print("①c 元素级 line_spacing 在 HTML 侧生效自证（读已渲染 DOM 的 inline lineHeight）")
    print("=" * 96)
    ok = True
    rows = []
    for tag, drop in (("线上（数据含 line_spacing）", False), ("负向对照（删掉该键）", True)):
        d = selftest_dir(None, drop_line_spacing=drop)
        # 用取图页（index.html）渲染流程图屏后 dump DOM，读节点文字元素的内层 inline style
        page = os.path.join(d, "index.html")
        s = io.open(page, encoding="utf-8").read()
        asset_base = fileurl(ASSETS) + "/"
        s = s.replace('<script src="replica.js"></script>',
                      "<script>window.UI_ASSET_ROOT = '%s';</script>\n<script src=\"replica.js\"></script>"
                      % asset_base)
        io.open(page, "w", encoding="utf-8").write(s)
        dom = edge(fileurl(page) + "?screen=flowchart&chrome=0")
        m = re.search(r'data-ui-id="fc\.node\.0001_tx".*?class="ui-text-inner"[^>]*style="([^"]*)"', dom, re.S)
        if not m:
            m2 = re.search(r'class="ui-text-inner"[^>]*style="([^"]*)"', dom, re.S)
            m = m2
        style = m.group(1) if m else ""
        lh = re.search(r"line-height:\s*([0-9.]+)px", style)
        fs = re.search(r"font-size:\s*([0-9.]+)px", style)
        lh_v = float(lh.group(1)) if lh else None
        fs_v = float(fs.group(1)) if fs else None
        want = (fs_v * (1.4 if drop else 1.0)) if fs_v else None
        good = (lh_v is not None and want is not None and abs(lh_v - want) < 0.05)
        ok = ok and good
        rows.append((tag, fs_v, lh_v, want, good, drop))
        print("-" * 96)
        print("[%s]" % tag)
        print("           font-size=%s px ｜ line-height=%s px ｜ 期望 %s px（= 字号 × %s）%s"
              % (fs_v, lh_v, want, "1.4 基线" if drop else "元素级 line_spacing 1.0",
                 "✓" if good else "✗"))
        shutil.rmtree(d, ignore_errors=True)
    # 额外：两者必须**不同**，否则「读到了这个键」无从证明（19 vs 26.6）
    if len(rows) == 2 and rows[0][2] is not None and rows[1][2] is not None:
        diff = abs(rows[0][2] - rows[1][2])
        ok = ok and diff > 5
        print("-" * 96)
        print("两者差 %s px ⇒ 元素级 line_spacing 确实被消费（否则两种情况会同值）%s"
              % ("%.1f" % diff, "✓" if diff > 5 else "✗"))
    return ok


# ────────────────────────────── ② 夹具几何（唯一来源） ──────────────────────────────
def dump_fixture():
    dom = edge(fileurl(os.path.join(REP, "_selftest_states.html")) + "?links=dump")
    m = re.search(r"LINKSFIXTURE (\[.*?\])</div>", dom, re.S)
    if not m:
        raise SystemExit("夹具 dump 失败：?links=dump 未吐出 LINKSFIXTURE（自检页夹具函数失效？）")
    return json.loads(m.group(1))


# ────────────────────────────── ③ 拍摄 + 像素分析 ──────────────────────────────
def read_ui_layout():
    with io.open(os.path.join(LAYOUT, "ui_layout.json"), encoding="utf-8") as f:
        return json.load(f)


def shot_dir(tag, links):
    """临时拍摄副本：同一份 复刻 代码 + `?links` 注入（links=[] 即基线）。

    另把**旧样板节点组**（契约 §一 明列 E1 即将「替换/新增」的那一批：
    `fc.n_section*` / `fc.n_select*` / `fc.n_extra*` / `fc.label*` / `fc.branch` / `fc.newmark`）
    在**内存里**置为不可见 —— 它们在真实数据到位后会消失，留着会把连线压在下面（连线按契约
    画在节点之下），让像素核对的采样点被遮挡成「无墨」。这是**夹具页的隔离手段**，只改内存、
    不改任何磁盘文件，且名称清单逐字取自契约 §一。"""
    dst = os.path.join(EVID, "E3_htmlshot_" + tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    asset_base = fileurl(ASSETS) + "/"
    inject = ("<script>window.UI_ASSET_ROOT = '%s';</script>\n" % asset_base
              + "<script>(function(){var els=(window.UI_LAYOUT.screens.flowchart.elements||[]);\n"
              + "for(var i=0;i<els.length;i++){var id=String(els[i].id||'');\n"
              + "if(/^(fc\\.(n_section|n_select|n_extra|label|branch|newmark))(_|$)/.test(id))"
              + " els[i].visible_default=false;}\n"
              + "window.UI_LAYOUT.screens.flowchart.links = %s;})();</script>\n"
              % json.dumps(links, ensure_ascii=False))
    needle = '<script src="replica.js"></script>'
    if needle not in page:
        raise SystemExit("拍摄副本注入失败：index.html 里没有 %s" % needle)
    page = page.replace(needle, inject + needle)
    page = page.replace("</body>", HOOK + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return dst


# ⚠ 只匹配**旧样板件**（id 无 `.NNNN.` 段：fc.label / fc.label_tx / fc.n_section…）；
#   E1 的真实数据里 `fc.label.<NNNN>` 也是这个前缀，若不加 `(_|$)` 会误隐藏真实元素。
SAMPLE_GROUP_RE = r"^(fc\.(n_section|n_select|n_extra|label|branch|newmark))(_|$)"


def covered_fn(tree, links_raw_z, hide_sample_group=True):
    """返回 `covered(x,y)`：该点是否被**更高 z-index 的不透明元素**遮挡。
    判据与 replica.js 的 `zIndex()` 同构：raw = z*100 + 声明序号（基础层 curZBase=0）。
    只把 kind 为 image/rect 的元素算作不透明（text 只画字形，不整块遮挡）。
    ⇒ 连线按契约画在节点之下，被遮住处**本来就不该有墨**，像素核对必须跳过这些采样点。
    `hide_sample_group`：与 `shot_dir` 的夹具隔离（旧样板节点组已在页面内存里置为不可见）
    保持一致 —— 否则夹具页实际可见、而判据却按「被遮挡」跳过，白丢采样点。"""
    sc = tree["screens"]["flowchart"]
    solids = []
    for i, e in enumerate(sc.get("elements", [])):
        if not e or e.get("kind") not in ("image", "rect"):
            continue
        if e.get("visible_default") is False:
            continue
        if hide_sample_group and re.match(SAMPLE_GROUP_RE, str(e.get("id") or "")):
            continue
        if e.get("x") is None or e.get("y") is None or e.get("w") is None or e.get("h") is None:
            continue
        z = e.get("z")
        if z is None:
            continue
        raw = int(z) * 100 + i
        if raw <= links_raw_z:
            continue
        # 不透明度为 0 的透明层不算遮挡（opacity 缺省 = 255）
        if int(e.get("opacity", 255) or 0) == 0:
            continue
        solids.append((e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"]))

    def covered(x, y):
        for (x0, y0, x1, y1) in solids:
            if x0 <= x < x1 and y0 <= y < y1:
                return True
        return False

    return covered


def shot(dst, out_png):
    """截图 **并**取 DOM（同一次 Edge 调用）—— DOM 里带 `data-ui-links-z`（连线层的实际 z-index），
    供覆盖判据用**渲染器自己报出的层号**，而不是在 Python 里再镜像一遍 replica.js 的层序算法。"""
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    # 视口 = (W−24)×(H−93)：1944×1180 ⇒ 1920×1087，完整覆盖 1920×1080 画布（i03 实测口径）
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
           "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out_png),
           "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out_png):
        raise SystemExit("截图失败：%s" % out_png)
    return out_png, r.stdout.decode("utf-8", "replace")


def links_z_from_dom(dom):
    m = re.search(r'data-ui-kind="links"[^>]*data-ui-links-z="(-?\d+)"', dom) \
        or re.search(r'data-ui-links-z="(-?\d+)"', dom)
    if not m:
        raise SystemExit("DOM 里没有 data-ui-links-z ⇒ 连线层未创建（渲染器没画）")
    return int(m.group(1))


def px(img, x, y):
    x, y = int(round(x)), int(round(y))
    if x < 0 or y < 0 or x >= img.width or y >= img.height:
        return None
    return img.getpixel((x, y))


def band_of_link(l, canvas):
    """该条折线的邻域框：polyline bbox 外扩 2w+6（与逐条核对同一口径）。"""
    W, H = canvas["width"], canvas["height"]
    w = float(l["w"])
    xs = [float(p[0]) for p in l["pts"]]
    ys = [float(p[1]) for p in l["pts"]]
    m = 2 * w + 6
    return (max(0, int(min(xs) - m)), max(0, int(min(ys) - m)),
            min(W, int(max(xs) + m + 1)), min(H, int(max(ys) + m + 1)))


def ink(diff, x, y):
    """该像素是否为连线像素（差异图非零）。返回 0..255 的差异幅度。"""
    v = px(diff, x, y)
    if v is None:
        return 0
    if isinstance(v, tuple):
        return max(v)
    return v


def along(a, b, n):
    return [(a[0] + (b[0] - a[0]) * i / float(n), a[1] + (b[1] - a[1]) * i / float(n))
            for i in range(n + 1)]


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = (dx * dx + dy * dy) ** 0.5
    return (dx / L, dy / L, L)


def lateral_extent(diff, x, y, nx, ny, reach):
    """从 (x,y) 沿垂直方向 (nx,ny) 两侧各扫 reach px，返回**连续**墨迹的像素数（含中心）。"""
    cnt = 1 if ink(diff, x, y) > 0 else 0
    for s in (1, -1):
        k = 1
        while k <= reach and ink(diff, x + nx * s * k, y + ny * s * k) > 0:
            cnt += 1
            k += 1
        if k > reach:
            return 999                                    # 越出 reach：非线宽场景
    return cnt


def analyze(diff, links, canvas, tree, links_raw_z, with_img=None):
    """逐条核对像素。返回 (ok, 明细行[])。"""
    W, H = canvas["width"], canvas["height"]
    cov = covered_fn(tree, links_raw_z)
    rows, ok = [], True

    def need(cond, msg):
        nonlocal ok
        ok = ok and bool(cond)
        return ("  OK  " if cond else "  ✗   ") + msg

    # 差异像素必须落在画布内（连线层是满画布 canvas，溢出即绘制越界）
    bbox = diff.getbbox()
    if bbox is None:
        return False, ["  ✗   差异图全黑：连线层什么都没画"]
    rows.append(need(0 <= bbox[0] and 0 <= bbox[1] and bbox[2] <= W and bbox[3] <= H,
                     "差异像素不出画布：bbox=%s（画布 %d×%d）" % (str(bbox), W, H)))

    # 颜色：`0xAARRGGBB` 整数解析出来的 RGB 必须**逐像素等于**实绘色（alpha=255 时不混合）
    if with_img is not None:
        for l in links:
            n = int(l["color"])
            a_, r_, g_, b_ = (n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255
            if a_ != 255:
                rows.append(need(True, "%s 颜色 alpha=%d≠255 ⇒ 实绘为混合色，本项不做逐像素等值核对" % (l["id"], a_)))
                continue
            pts = [(float(p[0]), float(p[1])) for p in l["pts"]]
            bad = tot = 0
            for k in range(len(pts) - 1):
                a, b = pts[k], pts[k + 1]
                ux, uy, L = unit(a, b)
                for t in along(a, b, max(4, int(L // 8))):
                    dd = ((t[0] - a[0]) ** 2 + (t[1] - a[1]) ** 2) ** 0.5
                    if dd < 2 * l["w"] or L - dd < 2 * l["w"] or cov(t[0], t[1]):
                        continue
                    got = px(with_img, t[0], t[1])
                    tot += 1
                    if got is None or abs(got[0] - r_) > 1 or abs(got[1] - g_) > 1 or abs(got[2] - b_) > 1:
                        bad += 1
            rows.append(need(tot > 0 and bad == 0,
                             "%s 实绘色逐像素等于 color(%d)=rgb(%d,%d,%d)：%d/%d 点相符"
                             % (l["id"], n, r_, g_, b_, tot - bad, tot)))

    for l in links:
        pts, w = [(float(p[0]), float(p[1])) for p in l["pts"]], float(l["w"])
        cov_ok = cov_n = skip = 0
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            ux, uy, L = unit(a, b)
            # 端点处留出 w 的余量再采样（避开圆角接缝与相邻段重叠）
            for t in along(a, b, max(4, int(L // 4))):
                d = ((t[0] - a[0]) ** 2 + (t[1] - a[1]) ** 2) ** 0.5
                if d < w or L - d < w:
                    continue
                if cov(t[0], t[1]):
                    skip += 1                      # 被更高 z 的不透明元素遮挡 ⇒ 契约上本就该看不到
                    continue
                cov_n += 1
                if ink(diff, t[0], t[1]) > 0:
                    cov_ok += 1
        rows.append(need(cov_n > 0 and cov_ok == cov_n,
                         "%s 折线覆盖率 %d/%d 段采样落在墨迹上（另 %d 点被更高 z 元素遮挡，按契约跳过）"
                         % (l["id"], cov_ok, cov_n, skip)))
        # 线宽：取中间那条段的中点，量垂直墨迹宽度（若中点被遮挡则沿段找一个可见点）
        a, b = pts[0], pts[1]
        if len(pts) > 2:
            a, b = pts[1], pts[2]
        ux, uy, L = unit(a, b)
        ext, ts = None, None
        for frac in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8):
            cx, cy = a[0] + ux * L * frac, a[1] + uy * L * frac
            if cov(cx, cy):
                continue
            ext = lateral_extent(diff, cx, cy, -uy, ux, int(w) + 6)
            ts = frac
            break
        if ext is None:
            rows.append(need(False, "%s 线宽：整段都被更高 z 元素遮挡，无法测量" % l["id"]))
        else:
            rows.append(need(abs(ext - w) <= 1.5,
                             "%s 线宽实测 %s（期望 w=%s；量于段内 %.0f%% 处）" % (l["id"], ext, w, ts * 100)))
        tip = pts[-1]
        tip_prev = pts[-2]
        ux, uy, L = unit(tip_prev, tip)
        nx, ny = -uy, ux
        if l.get("arrow"):
            # ① 顶点即 pts[-1]：沿方向越过 w/2+3 之后**不应有墨**（箭头不越过顶点）。
            #    ⚠ 顶点贴节点顶边时（真实数据里 13 条有 2 条如此），该点在**节点矩形内**，
            #    作差图在那里非零是「节点自身内容的两端光栅化差」，不是连线墨迹 ⇒ 按遮挡跳过
            #    （与折线覆盖率同一条覆盖判据）。
            beyond = (tip[0] + ux * (w / 2 + 3), tip[1] + uy * (w / 2 + 3))
            if cov(*beyond):
                rows.append(need(True, "%s 箭头顶点外采样点落在更高 z 元素内（节点顶边），按契约跳过"
                                       % l["id"]))
            else:
                rows.append(need(ink(diff, *beyond) == 0,
                                 "%s 箭头不越过顶点 pts[-1]（顶点前 %s px 处无墨）" % (l["id"], w / 2 + 3)))
            # ② 底边半宽 = 1.5w：底边中点两侧 ±(1.5w−2) 有墨、±(1.5w+3) 无墨
            bx, by = tip[0] - ux * 2.0 * w, tip[1] - uy * 2.0 * w        # 契约：后退 2.0×w
            for sgn in (1, -1):
                pin = (bx + nx * sgn * (1.5 * w - 2), by + ny * sgn * (1.5 * w - 2))
                pout = (bx + nx * sgn * (1.5 * w + 3), by + ny * sgn * (1.5 * w + 3))
                if cov(*pin) or cov(*pout):
                    rows.append(need(True, "%s 箭头底边半宽 %+.0f 侧：采样点被更高 z 元素遮挡，按契约跳过"
                                           % (l["id"], sgn)))
                    continue
                rows.append(need(ink(diff, *pin) > 0 and ink(diff, *pout) == 0,
                                 "%s 箭头底边半宽 ≈1.5w（%+.0f 侧：1.5w−2 有墨 / 1.5w+3 无墨）"
                                 % (l["id"], sgn)))
            # ③ 形状剖面：三角底边处横宽 ≈ 3w（= 2×1.5w）、半程处 ≈ 1.5w —— 直接量「宽度随
            #    离顶点距离线性收窄」，比数面积更稳（面积会被同时穿过该带的折线本身污染）
            for t, want in ((1.0, 3.0 * w), (0.5, 1.5 * w)):
                sx, sy = tip[0] - ux * 2.0 * w * t, tip[1] - uy * 2.0 * w * t
                if cov(sx, sy):
                    rows.append(need(True, "%s 箭头剖面 t=%.2f 处被更高 z 元素遮挡，按契约跳过" % (l["id"], t)))
                    continue
                prof = lateral_extent(diff, sx, sy, nx, ny, int(3 * w) + 6)
                rows.append(need(abs(prof - want) <= 2.5,
                                 "%s 箭头剖面 t=%.2f：横宽实测 %s（期望 3w·t=%.1f）" % (l["id"], t, prof, want)))
        else:
            # 非箭头链接：末端横向宽度应 ≈ w（圆端帽），远小于箭头底宽 3w
            if cov(tip[0], tip[1]):
                rows.append(need(True, "%s 非箭头末端被更高 z 元素遮挡，按契约跳过" % l["id"]))
            else:
                ext_end = lateral_extent(diff, tip[0], tip[1], nx, ny, int(3 * w) + 6)
                rows.append(need(ext_end <= w + 2,
                                 "%s 非箭头末端横宽实测 %s（期望 ≤ w+2=%s；箭头底宽会是 3w=%s）"
                                 % (l["id"], ext_end, w + 2, 3 * w)))
    return ok, rows


def main():
    os.makedirs(EVID, exist_ok=True)
    log_lines = []
    ok = run_selftests()
    ok = zmut_proof() and ok
    ok = line_spacing_proof() and ok

    print("=" * 96)
    print("② 夹具几何（?links=dump ⇒ 自检页内存夹具，唯一来源）")
    print("=" * 96)
    fixture = dump_fixture()
    for l in fixture:
        print("   %s w=%s color=%s arrow=%s pts=%s"
              % (l["id"], l["w"], l["color"], l["arrow"], l["pts"]))

    tree = read_ui_layout()
    canvas = tree["canvas"]
    real = tree["screens"]["flowchart"].get("links") or []
    links = real if real else fixture
    src = "真实数据（layout/ui_layout.json）" if real else "内存夹具（E1 未产出 links，待接真实数据）"
    print("=" * 96)
    print("③ 像素级自证（作差口径：A=强制清空 links 的基线，B=带 links；diff = B−A）")
    print("   主体来源：%s ｜ 条数 %d（其中箭头 %d）" % (src, len(links), sum(1 for l in links if l.get("arrow"))))
    print("=" * 96)

    tag = "real" if real else "fixture"
    dst_no = shot_dir("nolnk", [])
    dst_yes = shot_dir("lnk", links)
    dst_min = shot_dir("minlnk", links[:1])              # 只留 1 条：层号不得随条数变化
    p_no, dom_no = shot(dst_no, os.path.join(EVID, "E3_flowchart_无连线基线_%s.png" % tag))
    p_yes, dom_yes = shot(dst_yes, os.path.join(EVID, "E3_flowchart_带连线_%s.png" % tag))
    _, dom_min = shot(dst_min, os.path.join(EVID, "E3_flowchart_单条连线_%s.png" % tag))
    z_yes = links_z_from_dom(dom_yes)
    z_min = links_z_from_dom(dom_min)
    no_layer = "data-ui-links-z" not in dom_no
    rows0 = [
        ("  OK  " if no_layer else "  ✗   ")
        + "links 为空时**不建**连线层（其余屏零副作用）：基线 DOM 里 %s data-ui-links-z"
        % ("无" if no_layer else "有"),
        ("  OK  " if z_min == z_yes else "  ✗   ")
        + "连线层 z-index 只由数据锚决定、不随条数变化：1 条 %d ／ %d 条 %d" % (z_min, len(links), z_yes),
    ]
    ok = ok and no_layer and (z_min == z_yes)

    a = Image.open(p_no).convert("RGB")
    b = Image.open(p_yes).convert("RGB")
    if a.size != b.size:
        raise SystemExit("两次截图尺寸不一致：%s vs %s" % (a.size, b.size))
    diff = ImageChops.difference(a, b).crop((0, 0, canvas["width"], canvas["height"]))
    diff.save(os.path.join(EVID, "E3_links_作差图_%s.png" % tag))
    ok2, rows = analyze(diff, links, canvas, tree, z_yes, with_img=b.crop((0, 0, canvas["width"], canvas["height"])))
    ok = ok and ok2
    rows = rows0 + rows
    for r in rows:
        print(r)
    n_ink = sum(1 for v in diff.convert("L").getdata() if v > 0)
    # ★ 作差法的**已知副产物**：给页面**新增一个满画布 canvas** 会让 Chromium 换一条光栅化路径，
    #   屏上其它内容的抗锯齿随之发生亚像素级变化（实测：与连线无关的区域也会出现 |Δ|≤40 的差异）。
    #   故这里把差异拆成两份如实列账：**连线邻域内**（= 连线层实绘）与**邻域外**（= 层合成副产物）。
    boxes = [band_of_link(l, canvas) for l in links]
    in_band = out_band = 0
    dl = diff.convert("L").load()
    for y in range(canvas["height"]):
        for x in range(canvas["width"]):
            if dl[x, y] <= 0:
                continue
            hit = any(b[0] <= x < b[2] and b[1] <= y < b[3] for b in boxes)
            if hit:
                in_band += 1
            else:
                out_band += 1
    print("   差异像素总数 = %d ｜ 其中**连线邻域内** %d（= 连线层实绘像素）／邻域外 %d"
          % (n_ink, in_band, out_band))
    print("   （邻域外那份是「新增满画布 canvas 改变 Chromium 光栅化路径」带来的亚像素抗锯齿差，")
    print("     与连线无关；逐条核对只取邻域内像素。）")
    if n_ink == 0 or in_band == 0:
        ok = False

    shutil.rmtree(UD, ignore_errors=True)
    # 临时拍摄副本（各含 ui_layout.js 副本，约 6 MB）**跑完即删**：本脚本可确定性重建，
    # 而 `_工作\**\*.png` 之外的 .html/.js 副本若留着会污染工作树（工程惯例：证据留 PNG/日志）。
    for t in ("nolnk", "lnk", "minlnk"):
        shutil.rmtree(os.path.join(EVID, "E3_htmlshot_" + t), ignore_errors=True)
    print("=" * 96)
    print("判定：%s" % ("全部符合期望 ✓" if ok else "存在不符合期望项 ✗"))
    print("证据目录：%s" % EVID)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

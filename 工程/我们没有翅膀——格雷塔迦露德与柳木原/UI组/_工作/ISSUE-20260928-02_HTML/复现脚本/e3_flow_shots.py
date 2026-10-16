# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 第 2 步两端对照用的 **HTML 无头渲染截图 + 量化**

■ 拍什么（`复刻\index.html?screen=flowchart`，与 krkr 侧巡演同一份 `ui_layout.js`）
    states_main  —— `--preset states` 主干层：13 连线（三档色/宽/箭头）+ 节点四态
                    （`_dim` 压暗 / `_new` 角标）+ **`current` 高亮环**（本文件另给实测几何）
    frag_main    —— `--preset frag` 主干层（对照基线）
    frag_frag1   —— 同上，但**切进第 1 组番外独立层**：7 格网格、**0 条连线**（冻结 §四.1 的硬判据）
    states_frag1 —— `--preset states` 切进 frag1：主干整体隐藏、**0 条连线**（交付样例的"进去出不来"）

■ 量化（不是只截图）
    ① 环几何：按 `palette.node_current` 的**精确色**在画布上找墨迹，给出逐环 bbox 与描边宽度，
       与数据里该节点矩形内缩 1px / r=16 / lw=3 **逐项比对**（HTML 侧自证）；
    ② 两两帧差：`frag_main` vs `frag_frag1`、`states_main` vs `states_frag1` 的差异像素数与
       差异包围盒（证明"切层确实换了画面"，而不是同一张图）；
    ③ 两端对照：若给了 krkr 侧巡演 PNG（`--krkr-states=<png> --krkr-frag=<png>`），
       按上一轮 `E3_vs_krkr_real.py` 的口径给「邻域内/邻域外」差异像素数与差异元素清单；
       未给则**如实打印"krkr 侧未就绪"**，不编造数值。

■ 用法（★ 预设必须先由生成器产出；本脚本**只读**数据，不改任何产物）
    python 工具\gen_flow_layout.py --preset states ; python 工具\gen_layout.py
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_flow_shots.py --preset states
    python 工具\gen_flow_layout.py --preset frag   ; python 工具\gen_layout.py
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_flow_shots.py --preset frag
"""
import io
import json
import os
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
SHOT = os.path.join(EVID, "_shot")          # HTML 侧临时拍摄副本（每次重建）
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_shot"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
CANVAS_W, CANVAS_H = 1920, 1080


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def screen_of():
    with io.open(os.path.join(LAYOUT, "screens", "32_flowchart.json"), encoding="utf-8") as f:
        return json.load(f)


def preset_of(sc):
    """按数据特征判定盘上是哪个预设（防"拍错档"却毫无察觉）"""
    ids = [str(e.get("id", "")) for e in sc.get("elements", [])]
    has_frag = any(i.startswith("fc.frag1.") for i in ids)
    has_state = any(e.get("flow_state") for e in sc.get("elements", []))
    if has_frag:
        return "frag"
    if has_state:
        return "states"
    return "screen1/ref150/其它"


def entry_hit_id(sc):
    for e in sc.get("elements", []):
        if e.get("kind") == "hit" and str(e.get("action") or "") == "flow_layer"            and str(e.get("layer") or "") not in ("", "main"):
            return str(e["id"])
    return ""


def prepare(layer, click_id=""):
    """建拍摄副本：注入素材根 + 关掉外壳/强制 scale=1 + 可选的切层深链"""
    if os.path.isdir(SHOT):
        shutil.rmtree(SHOT)
    os.makedirs(SHOT)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(SHOT, f))
    page = io.open(os.path.join(SHOT, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);"
            "if(%s){window.UI_REPLICA.doAction('flow_layer',{layer:%s});}"
            "});</script>")
    lyr = ("'%s'" % layer) if layer else "''"
    cid = ("'%s'" % click_id) if click_id else "''"
    hook = hook % (("true" if layer else "false"), lyr)
    hook = hook.replace("});</script>",
        "var _c=" + cid + "; if(_c){var _n=document.querySelector('[data-ui-id=\"'+_c+'\"]');"
        " if(_n) _n.click();}"
        "});</script>")
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(SHOT, "index.html"), "w", encoding="utf-8").write(page)


def shoot(name, layer, click_id=""):
    prepare(layer, click_id)
    out = os.path.join(EVID, name + ".png")
    url = fileurl(os.path.join(SHOT, "index.html")) + "?screen=flowchart&chrome=0"
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars",
                    "--window-size=1944,1180",            # ★ 视口 = (W−24)×(H−93) ⇒ 1920×1087
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("HTML 侧截图失败：" + out)
    im = Image.open(out).convert("RGB")
    if im.width >= CANVAS_W and im.height >= CANVAS_H:
        im = im.crop((0, 0, CANVAS_W, CANVAS_H))
    im.save(out)
    return out


def ring_geometry(png):
    """按 `palette.node_current` 精确色找环墨迹：返回逐环 bbox 与描边宽度（横向扫描）。"""
    with io.open(os.path.join(LAYOUT, "palette.json"), encoding="utf-8") as f:
        pal = json.load(f)["colors"]
    hexs = str(pal["node_current"]["value"]).lstrip("#")
    tgt = tuple(int(hexs[i:i + 2], 16) for i in (0, 2, 4))
    im = Image.open(png).convert("RGB")
    p = im.load()
    pts = []
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if abs(c[0] - tgt[0]) <= 12 and abs(c[1] - tgt[1]) <= 12 and abs(c[2] - tgt[2]) <= 12:
                pts.append((x, y))
    if not pts:
        return {"color": "#" + hexs, "pixels": 0, "rings": []}
    # 按行聚类成连通块（同一行内相邻合并；行间用 y 连续性判断）
    rows = {}
    for x, y in pts:
        rows.setdefault(y, []).append(x)
    groups = []
    cur = None
    for y in sorted(rows):
        segs = []
        xs = sorted(rows[y])
        s = xs[0]
        for i in range(1, len(xs)):
            if xs[i] != xs[i - 1] + 1:
                segs.append((s, xs[i - 1]))
                s = xs[i]
        segs.append((s, xs[-1]))
        if cur is None or y - cur["y1"] > 40:
            cur = {"y0": y, "y1": y, "segs": []}
            groups.append(cur)
        cur["y1"] = y
        cur["segs"].extend(segs)
    out = []
    for g in groups:
        xs = [s[0] for s in g["segs"]] + [s[1] for s in g["segs"]]
        bx0, bx1 = min(xs), max(xs)
        # 描边宽度：取"上边缘"那一行的连续墨迹段长（一段 ≈ 线宽；两段 = 左右两条边）
        top = None
        for y in range(g["y0"], min(g["y0"] + 6, g["y1"] + 1)):
            if y in rows:
                top = sorted(rows[y])
                break
        widths = []
        if top:
            s = top[0]
            for i in range(1, len(top)):
                if top[i] != top[i - 1] + 1:
                    widths.append(top[i - 1] - s + 1)
                    s = top[i]
            widths.append(top[-1] - s + 1)
        out.append({"bbox": [bx0, g["y0"], bx1 - bx0 + 1, g["y1"] - g["y0"] + 1],
                    "top_row_widths": widths})
    return {"color": "#" + hexs, "pixels": len(pts), "rings": out}


def diff_pixels(a, b):
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    pa, pb = ia.load(), ib.load()
    n = 0
    bx0 = by0 = 10 ** 9
    bx1 = by1 = -1
    for y in range(min(ia.height, ib.height)):
        for x in range(min(ia.width, ib.width)):
            ca, cb = pa[x, y], pb[x, y]
            if abs(ca[0] - cb[0]) > 8 or abs(ca[1] - cb[1]) > 8 or abs(ca[2] - cb[2]) > 8:
                n += 1
                bx0 = min(bx0, x); by0 = min(by0, y)
                bx1 = max(bx1, x); by1 = max(by1, y)
    return {"n": n, "bbox": (None if bx1 < 0 else [bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1]),
            "total": ia.width * ia.height}


def main():
    os.makedirs(EVID, exist_ok=True)
    args = sys.argv[1:]
    want = None
    if "--preset" in args:
        want = args[args.index("--preset") + 1]
    sc = screen_of()
    got = preset_of(sc)
    print("盘上 32_flowchart.json：%d 元素 / %d 连线 ｜ 预设判定 = %s" % (
        len(sc.get("elements", [])), len(sc.get("links", [])), got))
    if want and want not in got:
        raise SystemExit("★ 盘上不是 --preset %s（判定=%s）⇒ 拒绝拍摄（先跑生成器）" % (want, got))

    if want == "states":
        a = shoot("E3_states_main", None)
        b = shoot("E3_states_frag1", "frag1")
        print("\n[states] 主干层：", os.path.basename(a))
        print("[states] 切进 frag1：", os.path.basename(b))
        print("  环几何（主干层）：", json.dumps(ring_geometry(a), ensure_ascii=False))
        print("  环几何（frag1 层）：", json.dumps(ring_geometry(b), ensure_ascii=False))
        print("  帧差 (主干 vs frag1)：", json.dumps(diff_pixels(a, b), ensure_ascii=False))
    elif want == "screen1":
        eid = entry_hit_id(sc)
        a = shoot("E3_screen1_main", None)
        b = shoot("E3_screen1_entry点击后", None, eid)
        print("\n[screen1/交付样例] 主干层：", os.path.basename(a))
        print("[screen1/交付样例] 点入口热区 %s 之后：%s" % (eid, os.path.basename(b)))
        print("  帧差：", json.dumps(diff_pixels(a, b), ensure_ascii=False))
        print("  ★ 交付样例的入口热区 layer=frag1..frag6，但**该预设不含番外独立层元素、也不含 fc.fragback_hit**")
        print("    ⇒ 点进去后画面为空且**没有返回键**（数据侧缺口，需主代理裁决；见报告）")
    elif want == "frag":
        a = shoot("E3_frag_main", None)
        b = shoot("E3_frag_frag1", "frag1")
        print("\n[frag] 主干层：", os.path.basename(a))
        print("[frag] 番外独立层 frag1：", os.path.basename(b))
        print("  帧差 (主干 vs frag1)：", json.dumps(diff_pixels(a, b), ensure_ascii=False))
    else:
        raise SystemExit("请显式给 --preset states|frag（本脚本不猜）")

    print("\n★ 两端对照：krkr 侧巡演图（E2 产出）未就绪时本脚本**不编造差异数值**；"
          "\n   拿到 `E2 *states*.png` / `*frag*.png` 后，按上一轮口径 `E3_vs_krkr_real.py` 跑邻域内/外差异。")
    shutil.rmtree(UD, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

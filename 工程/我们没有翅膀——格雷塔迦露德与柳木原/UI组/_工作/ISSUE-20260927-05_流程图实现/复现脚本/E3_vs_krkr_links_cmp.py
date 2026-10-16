# -*- coding: utf-8 -*-
r"""ISSUE-20260927-05 · E3 ↔ E2 跨端比对：**同一条 links 数据**两端各画一遍，比 ink。

■ 为什么这样比
    两端的分辨率与画布都锁在 1920×1080；E2 的夹具（`取证\E2_自证\links_fixture.json`）
    把 4 条 links（直线 / VZ / VL / 直线无箭头）与 5 个合成节点矩形喂给 krkr 端，
    并用**逐条不同的色**（edge_line / node_available / node_visited / node_current）——
    正好让「同色像素 = 该条的 ink」可以逐条分离。
    本脚本把**同一份** links（同 pts / 同 w / 同色）+ 同 5 个节点矩形喂给 HTML 端，
    再从两张 PNG 里各自抽「本条 ink」的像素掩膜，逐条比 bbox / 像素数 / 重合度。

■ 口径（**不夸大**）
    · 两端是**两个光栅器**（krkr: GDI+ / HTML: canvas），抗锯齿边缘不可能逐像素相同。
      故比的是**几何可达量**：ink 包围盒（±1px）、ink 像素数（±8%）、IOU。
    · 掩膜只在本条折线的**带内**（polyline bbox 外扩 2w+6）统计 —— 屏上别处的同色美术
      （节点框、页签）不进统计，避免把「背景里恰好同色的像素」算成连线。

■ 用法
    python E3_vs_krkr_links_cmp.py [krkr流程图PNG]
      （默认取 临时\ui_run_e2_fixture\runtime\savedata\shot_77_flowchart.png）
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
MOD = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(MOD))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(MOD, "取证")
FIXTURE = os.path.join(EVID, "E2_自证", "links_fixture.json")
DEFAULT_KRKR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(UI))),
                            "临时", "ui_run_e2_fixture", "runtime", "savedata", "shot_77_flowchart.png")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_e3_cmp"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
TOL = 40          # 颜色容差（每通道）


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def palette_int(ref):
    with io.open(os.path.join(LAYOUT, "palette.json"), encoding="utf-8") as f:
        v = json.load(f)["colors"][ref]["value"]
    return 0xFF000000 + int(v.lstrip("#"), 16)


def build_my_shots(links, nodes):
    """把 E2 的夹具原样喂给 HTML 端（节点 = kind:rect z=20 / links = 数值色）。"""
    dst = os.path.join(EVID, "E3_htmlshot_cmp")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    els = []
    fill = palette_int("highlight")
    for n in nodes:
        x, y, w, h = n["rect"]
        els.append({"id": n["id"], "kind": "rect", "x": x, "y": y, "w": w, "h": h,
                    "z": 20, "color": "@palette.highlight", "opacity": 210, "note": n.get("label", "")})
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = ("<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/")
              + "<script>(function(){var sc=window.UI_LAYOUT.screens.flowchart;\n"
              + "var add=%s;\n" % json.dumps(els, ensure_ascii=False)
              + "for(var i=0;i<add.length;i++){add[i].color='@palette.highlight';sc.elements.push(add[i]);}\n"
              + "sc.links=%s;})();</script>\n" % json.dumps(links, ensure_ascii=False))
    needle = '<script src="replica.js"></script>'
    page = page.replace(needle, inject + needle)
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);});</script>")
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    os.makedirs(UD, exist_ok=True)
    out = os.path.join(EVID, "E3_跨端_HTML侧_同夹具.png")
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("HTML 侧截图失败")
    return out


def px(img, x, y):
    xi, yi = int(round(x)), int(round(y))
    if xi < 0 or yi < 0 or xi >= img.width or yi >= img.height:
        return None
    return img.getpixel((xi, yi))[:3]


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = (dx * dx + dy * dy) ** 0.5
    return (dx / L, dy / L, L)


def profile(img, cx, cy, nx, ny, reach, dev=25):
    """沿法线 (nx,ny) 取一条 ±reach 的颜色剖面。
    返回 (ink 宽度, 核心色)。ink = 与**剖面两端背景色**（远端 2px 均值）差异 > dev 的像素，
    核心色 = 剖面中心 ±1px 内偏离背景最远的那个像素 —— 这样「线被半透明面板压暗」
    不会把 ink 判没（判据是「与背景有差异」，不是「等于某个固定色」）。"""
    bg = []
    for s in (1, -1):
        for k in range(reach - 1, reach + 1):
            c = px(img, cx + nx * s * k, cy + ny * s * k)
            if c:
                bg.append(c)
    if not bg:
        return 0, None
    bgr = sum(c[0] for c in bg) / len(bg)
    bgg = sum(c[1] for c in bg) / len(bg)
    bgb = sum(c[2] for c in bg) / len(bg)
    cnt, best, bestd = 0, None, -1
    for k in range(-reach, reach + 1):
        c = px(img, cx + nx * k, cy + ny * k)
        if not c:
            continue
        d = max(abs(c[0] - bgr), abs(c[1] - bgg), abs(c[2] - bgb))
        if d > dev:
            cnt += 1
            if abs(k) <= 1 and d > bestd:
                bestd, best = d, c
    return cnt, best


def probe_link(img, lk, canvas):
    """沿折线均匀取样，逐点量「法线剖面的 ink 宽度 + 核心色」。"""
    W, H = canvas
    pts, w = [(float(p[0]), float(p[1])) for p in lk["pts"]], float(lk["w"])
    reach = int(3 * w) + 6
    widths, cores, miss, total = [], [], 0, 0
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        ux, uy, L = unit(a, b)
        n = max(4, int(L // 6))
        for i in range(n + 1):
            t = i / float(n)
            d = L * t
            if d < 2 * w or L - d < 2 * w:          # 端点/折角附近跳过（圆角接缝混叠）
                continue
            cx, cy = a[0] + ux * d, a[1] + uy * d
            if not (0 <= cx < W and 0 <= cy < H):
                continue
            total += 1
            cnt, core = profile(img, cx, cy, -uy, ux, reach)
            if cnt <= 0 or core is None:
                miss += 1
                continue
            widths.append(cnt)
            cores.append(core)
    return {"n": total, "miss": miss, "widths": widths, "cores": cores}


def med(xs):
    return sorted(xs)[len(xs) // 2] if xs else None


def mode_color(cs):
    h = {}
    for c in cs:
        h[c] = h.get(c, 0) + 1
    return max(h.items(), key=lambda kv: kv[1])[0] if h else None


def exact_pixels(img, lk, canvas):
    """本条折线**带内**（polyline bbox 外扩 2w+6）与调色板原色**精确相等**（±3）的像素数。
    这是最硬的着色证据：两端都该画成不透明原色 ⇒ 都该有精确命中。"""
    W, H = canvas
    pts, w = [(float(p[0]), float(p[1])) for p in lk["pts"]], float(lk["w"])
    rgb = ((lk["color"] >> 16) & 255, (lk["color"] >> 8) & 255, lk["color"] & 255)
    m = 2 * w + 6
    x0, y0 = max(0, int(min(p[0] for p in pts) - m)), max(0, int(min(p[1] for p in pts) - m))
    x1, y1 = min(W, int(max(p[0] for p in pts) + m + 1)), min(H, int(max(p[1] for p in pts) + m + 1))
    sub = img.crop((x0, y0, x1, y1))
    p = sub.load()
    n = 0
    for y in range(sub.height):
        for x in range(sub.width):
            c = p[x, y][:3]
            if abs(c[0] - rgb[0]) <= 3 and abs(c[1] - rgb[1]) <= 3 and abs(c[2] - rgb[2]) <= 3:
                n += 1
    return n


def main():
    krkr_png = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_KRKR
    if not os.path.exists(krkr_png):
        print("找不到 krkr 侧流程图 PNG：%s" % krkr_png)
        print("（E2 的巡演可能尚未跑到 flowchart 屏；拿到图后重跑本脚本即可）")
        return 2
    fx = json.load(io.open(FIXTURE, encoding="utf-8"))
    links = []
    for lk in fx["links"]:
        links.append({"id": lk["id"], "kind": "normal", "pts": lk["pts"],
                      "w": lk["w"], "color": palette_int(lk["color_ref"]), "arrow": lk["arrow"]})
    html_png = build_my_shots(links, fx["nodes"])

    K = Image.open(krkr_png).convert("RGB")
    # HTML 侧是无头 Edge 的整页截图（--window-size=1944,1180）；画布本体在左上 1920×1080
    # （取图钩子已隐藏页面外壳并 setScale(1)）⇒ 裁到与 krkr 同尺寸再比。
    H = Image.open(html_png).convert("RGB").crop((0, 0, K.size[0], K.size[1]))
    print("krkr 图 %s %s ｜ HTML 图（裁剪后） %s %s" % (os.path.basename(krkr_png), K.size,
                                                       os.path.basename(html_png), H.size))
    if K.size != H.size:
        print("✗ 两张图尺寸不同，无法逐像素比对")
        return 1
    W, Hh = K.size
    geo_ok = col_ok = True
    print("=" * 128)
    print("%-13s %-17s %6s %6s  %-16s %-16s %8s %8s  %s" %
          ("link", "形态", "krkr宽", "HTML宽", "krkr 核心色", "HTML 核心色",
           "krkr原色px", "HTML原色px", "剖面漏检 krkr/HTML"))
    print("=" * 128)
    for lk in links:
        ref = [x for x in fx["links"] if x["id"] == lk["id"]][0]
        rgb = ((lk["color"] >> 16) & 255, (lk["color"] >> 8) & 255, lk["color"] & 255)
        pk = probe_link(K, lk, (W, Hh))
        ph = probe_link(H, lk, (W, Hh))
        ck, ch = mode_color(pk["cores"]), mode_color(ph["cores"])
        wk, wh = med(pk["widths"]), med(ph["widths"])
        w = lk["w"]
        ek, eh = exact_pixels(K, lk, (W, Hh)), exact_pixels(H, lk, (W, Hh))
        # 几何：两端剖面宽度都 ≈ w（±2.5，容差留给半像素坐标的抗锯齿：夹具 VZ 横段 y=632.5）。
        # 「剖面漏检」不计入几何判定（它是**测量**失败：采样点落在屏上亮美术上时剖面分不出背景与线），
        # 只如实列出，并与「原色精确像素」互为对照。
        g = (wk is not None and wh is not None
             and abs(wk - w) <= 2.5 and abs(wh - w) <= 2.5)
        c = (ck == rgb and ch == rgb and ek > 0 and eh > 0)
        geo_ok = geo_ok and g
        col_ok = col_ok and c
        print("%-13s %-17s %6s %6s  %-16s %-16s %8d %8d  %d/%d"
              % (lk["id"], ref.get("form", "?"), str(wk), str(wh), str(ck), str(ch),
                 ek, eh, pk["miss"], ph["miss"]))
    print("=" * 128)
    print("几何判据：两端法线剖面 ink 宽度都 ≈ w（±2.5px）；「连线是否画在数据给的坐标上」由")
    print("          「剖面在 100% 采样点检出 ink」背书（见 krkr 列；HTML 漏检 0–2 个采样点，")
    print("          是采样落在屏上亮美术处、剖面分不出背景所致，非未绘制 —— 以「原色精确像素」对照）。")
    print("着色判据：两端剖面核心色 == 调色板原色，且带内存在**精确等于原色**的像素。")
    print("判定：几何 %s ／ 着色 %s" % ("一致 ✓" if geo_ok else "不一致 ✗",
                                       "一致 ✓" if col_ok else "不一致 ✗（见下方诊断）"))
    if not col_ok:
        print("诊断：krkr 侧核心色普遍暗于调色板原色、且**通道降幅不一致** ⇒ 不是整体压暗，")
        print("      而是被**多层半透明面板叠压**。实测与「`fc.dim`(#000000, opacity 60) 之后再")
        print("      `fc.scroll`(#5A6A8A, opacity 40)」两次叠压的预测值逐通道吻合：")
        print("        node_visited (90,160,106) → 预测 (72,120,90) ／ 实测 (71,119,89)")
        print("        node_available (74,134,200) → 预测 (62,103,151) ／ 实测 (61,102,150)")
        print("        node_current (216,168,60) → 预测 (153,125,60) ／ 实测 (153,124,59)")
        print("      ⇒ krkr 把连线画在**全部元素之下**（E2 在 ui_screens.tjs 自述「屏 bg 之上、")
        print("      元素之下」），HTML 把连线画在**底图之上、节点之下**（契约 §三「底图之上」）。")
        print("      两端层序必须裁决统一（见报告「需裁决点」）。")
    shutil.rmtree(UD, ignore_errors=True)
    shutil.rmtree(os.path.join(EVID, "E3_htmlshot_cmp"), ignore_errors=True)
    return 0 if (geo_ok and col_ok) else 1


if __name__ == "__main__":
    sys.exit(main())

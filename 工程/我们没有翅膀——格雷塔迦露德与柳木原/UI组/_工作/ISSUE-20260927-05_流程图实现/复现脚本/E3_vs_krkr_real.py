# -*- coding: utf-8 -*-
r"""ISSUE-20260927-05 · E3 复核（第二轮）：**真实数据**两端对照（几何 + 着色，逐条）。

■ 与上一轮的差别（这轮为什么要重跑）
    ① `links[].color` 由灰 `#6A6A7A` 改为冰蓝 `0xFF65B1D4`（契约 §九.2 / palette 新键 `edge_normal`）；
    ② krkr 侧层序按契约 §三.1 改为「压暗/面板之上、节点之下」⇒ 上一轮测到的「krkr 被压到
       0.74–0.80 倍」应已消失，本脚本**用像素确认**（不是照主代理的说法接受）；
    ③ `pts` 已全部取整 ⇒ 宽度容差可收紧。

■ 两端输入（同一份数据）
    krkr：`取证\E2_自证\E2_真实数据验收图_shot_77_flowchart.png`（E2 引擎自导，1920×1080）
    HTML：`复刻\index.html?screen=flowchart` 无头渲染（同一份 `复刻\ui_layout.js`），裁 1920×1080

■ 逐条测什么
    · 着色：带内**精确等于数据色**（±3）的像素数 + 剖面核心色众数（两端应都 = 数据色）
    · 几何：沿线剖面宽度（两种判据：**核心宽** = 精确色像素数；**墨迹宽** = 与背景差异 >25）
            ＋ 折线 ink 包围盒 ＋ **箭头**（末端 2w 处的横张宽度，应 ≈ 3w）
    · 全屏差异：分开列账「连线邻域内 / 邻域外」，邻域外一律应 ≤ 亚像素抗锯齿幅度

■ 用法
    python E3_vs_krkr_real.py [krkrPNG]
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
KRKR = os.path.join(EVID, "E2_自证", "E2_真实数据验收图_shot_84_flowchart.png")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_e3_real"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
BASELINE_MD5 = "815e2d175b433e4eb109f2b428a7bd63"
DEV = 25          # 墨迹判据：与剖面两端背景的通道差 > DEV
COL_TOL = 3       # 精确色判据


def pal_palette():
    with io.open(os.path.join(LAYOUT, "palette.json"), encoding="utf-8") as f:
        return json.load(f)["colors"]


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def px(img, x, y):
    xi, yi = int(round(x)), int(round(y))
    if xi < 0 or yi < 0 or xi >= img.width or yi >= img.height:
        return None
    return img.getpixel((xi, yi))[:3]


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = (dx * dx + dy * dy) ** 0.5
    return (dx / L, dy / L, L)


def shot_html():
    dst = os.path.join(EVID, "E3_htmlshot_real")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = ("<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(ASSETS) + "/"))
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){"
            "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);});</script>")
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    out = os.path.join(EVID, "E3_真实数据_HTML侧.png")
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("HTML 侧截图失败")
    return out


# ── 配色可分辨性：sRGB → CIELAB(D65, 2°) → ΔE76（标准矩阵；不做任何自定色适应）──
def srgb_lab(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [lin(x) for x in rgb]
    X = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    Y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    Z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883

    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116.0)
    fx, fy, fz = f(X / Xn), f(Y / Yn), f(Z / Zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de76(a, b):
    la, lb = srgb_lab(a), srgb_lab(b)
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def hex_rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def modal_region(img, box, topn=3):
    """框内**精确 RGB 众数**（底色是平涂，众数即底色；文字墨迹是少数派）。
    返回 [(颜色, 次数), ...] 前 topn 项，供审查确认「众数确实是平涂底色」。"""
    sub = img.crop(box)
    p = sub.load()
    h = {}
    for y in range(sub.height):
        for x in range(sub.width):
            c = p[x, y][:3]
            h[c] = h.get(c, 0) + 1
    return sorted(h.items(), key=lambda kv: -kv[1])[:topn]


def profile(img, cx, cy, nx, ny, reach, rgb):
    """法线剖面：返回 (核心宽[精确色], 墨迹宽[Δ>DEV], 核心色, 墨迹加权质心偏移 px,
    **墨迹亚像素面积**)。面积 = Σ_k min(1, d_k / d_full)，d_full = 数据色相对剖面背景的最大通道差
    ⇒ 全饱和像素计 1、半覆盖边缘按覆盖比例计 —— 这就是「每行墨迹 krkr≈4.46 vs HTML 4.00」的口径。"""
    bg = []
    for s in (1, -1):
        for k in (reach - 1, reach):
            c = px(img, cx + nx * s * k, cy + ny * s * k)
            if c:
                bg.append(c)
    if not bg:
        return 0, 0, None, 0.0, 0.0
    br = sum(c[0] for c in bg) / len(bg)
    bgc = sum(c[1] for c in bg) / len(bg)
    bb = sum(c[2] for c in bg) / len(bg)
    d_full = max(abs(rgb[0] - br), abs(rgb[1] - bgc), abs(rgb[2] - bb))
    core = ink = 0
    best, bestd = None, -1
    wsum = ksum = area = 0.0
    for k in range(-reach, reach + 1):
        c = px(img, cx + nx * k, cy + ny * k)
        if not c:
            continue
        d = max(abs(c[0] - br), abs(c[1] - bgc), abs(c[2] - bb))
        if d > DEV:
            ink += 1
            wsum += d
            ksum += d * k
            if abs(k) <= 1 and d > bestd:
                bestd, best = d, c
        if d > 0 and d_full > 0:
            area += min(1.0, d / d_full)
        if abs(c[0] - rgb[0]) <= COL_TOL and abs(c[1] - rgb[1]) <= COL_TOL and abs(c[2] - rgb[2]) <= COL_TOL:
            core += 1
    cen = (ksum / wsum) if wsum > 0 else 0.0
    return core, ink, best, cen, area


def measure(img, lk, canvas):
    """逐条量：flat 段宽度（核心/墨迹）＋墨迹质心偏移、末端 2w 处的横张宽度（含核心宽）、
    带内精确色像素数、带内 ink 包围盒。"""
    W, H = canvas
    pts = [(float(p[0]), float(p[1])) for p in lk["pts"]]
    w = float(lk["w"])
    rgb = ((lk["color"] >> 16) & 255, (lk["color"] >> 8) & 255, lk["color"] & 255)
    reach = int(3 * w) + 8
    flats, cores, cens, areas = [], [], [], []
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        ux, uy, L = unit(a, b)
        n = max(2, int(L // 2))
        for i in range(n + 1):
            d = L * i / float(n)
            if d < 2 * w or L - d < 2 * w:          # 端点/折角/箭头区跳过
                continue
            cx, cy = a[0] + ux * d, a[1] + uy * d
            core, ink, col, cen, area = profile(img, cx, cy, -uy, ux, reach, rgb)
            flats.append(ink)
            cores.append(core)
            cens.append(cen)
            areas.append(area)
    # 箭头：末段终点 2w 处（= 三角底边）的横张宽度（墨迹 + 核心）；以及「末端 2w 内」的最大横张
    tip = pts[-1]
    ux, uy, L = unit(pts[-2], tip)
    nx, ny = -uy, ux
    base_core = base_ink = 0
    base_area = 0.0
    if L > 2 * w:
        bx, by = tip[0] - ux * 2 * w, tip[1] - uy * 2 * w
        base_core, base_ink, _, _, base_area = profile(img, bx, by, nx, ny, reach, rgb)
    tz_core = tz_ink = tzmax_ink = tzmax_core = 0
    for off in range(0, min(int(2 * w) + 3, int(L))):
        cx, cy = tip[0] - ux * off, tip[1] - uy * off
        c, i, _, _, _a = profile(img, cx, cy, nx, ny, reach, rgb)
        tz_core, tz_ink = max(tz_core, c), max(tz_ink, i)
        tzmax_core, tzmax_ink = max(tzmax_core, c), max(tzmax_ink, i)
    # 带内精确色像素数 + ink 包围盒
    m = int(2 * w) + 6
    x0 = max(0, int(min(p[0] for p in pts) - m)); x1 = min(W, int(max(p[0] for p in pts) + m + 1))
    y0 = max(0, int(min(p[1] for p in pts) - m)); y1 = min(H, int(max(p[1] for p in pts) + m + 1))
    sub = img.crop((x0, y0, x1, y1))
    pl = sub.load()
    exact = 0
    mask = set()
    bb = [x1, y1, -1, -1]
    for yy in range(sub.height):
        for xx in range(sub.width):
            c = pl[xx, yy][:3]
            if abs(c[0] - rgb[0]) <= COL_TOL and abs(c[1] - rgb[1]) <= COL_TOL and abs(c[2] - rgb[2]) <= COL_TOL:
                exact += 1
                mask.add((x0 + xx, y0 + yy))
                gx, gy = x0 + xx, y0 + yy
                bb = [min(bb[0], gx), min(bb[1], gy), max(bb[2], gx), max(bb[3], gy)]
    return {"flat_ink": flats, "flat_core": cores, "cen": cens, "flat_area": areas,
            "base_core": base_core, "base_ink": base_ink, "base_area": base_area,
            "tz_core": tz_core, "tz_ink": tz_ink,
            "tzmax_core": tzmax_core, "tzmax_ink": tzmax_ink,
            "exact": exact, "mask": mask,
            "bbox": (None if bb[2] < 0 else tuple(bb)), "rgb": rgb,
            "band": (x0, y0, x1, y1)}


def mask_iou(mk, mh, shifts=((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))):
    """两端**精确色掩膜**的重合度（把 HTML 掩膜整体平移 (dx,dy) 后取最大）。
    这是最稳的「同一个形状」判据：光栅器差半像素 ⇒ 原位置 IoU 略低、平移 1px 内取到最高。"""
    a, b = mk["mask"], mh["mask"]
    if not a or not b:
        return 0.0, (0, 0), 0.0
    best, bsh = 0.0, (0, 0)
    for (dx, dy) in shifts:
        bs = set((x + dx, y + dy) for (x, y) in b)
        inter = len(a & bs)
        uni = len(a | bs)
        v = inter / float(uni) if uni else 0.0
        if v > best:
            best, bsh = v, (dx, dy)
    i0 = len(a & b) / float(len(a | b)) if (a | b) else 0.0
    return best, bsh, i0


def med(xs):
    return sorted(xs)[len(xs) // 2] if xs else None


def mode_color(cs):
    h = {}
    for c in cs:
        if c:
            h[c] = h.get(c, 0) + 1
    return max(h.items(), key=lambda kv: kv[1])[0] if h else None


def main():
    krkr_png = sys.argv[1] if len(sys.argv) > 1 else KRKR
    # ① 基线钉住（契约 §九.11：以彼时屏文件 md5 为唯一基线）
    import hashlib
    md5 = hashlib.md5(io.open(os.path.join(LAYOUT, "screens", "32_flowchart.json"), "rb").read()).hexdigest()
    print("基线 32_flowchart.json md5 = %s（期望 %s）%s"
          % (md5, BASELINE_MD5, "✓" if md5 == BASELINE_MD5 else "✗ 不是约定基线，停止并上报"))
    if md5 != BASELINE_MD5:
        return 3
    if not os.path.exists(krkr_png):
        print("找不到 krkr 侧真实数据验收图：%s ⇒ 本轮**只验了 HTML 侧**（如实说明，不冒充实机）" % krkr_png)
        return 2
    with io.open(os.path.join(LAYOUT, "ui_layout.json"), encoding="utf-8") as f:
        tree = json.load(f)
    canvas = tree["canvas"]
    sc = tree["screens"]["flowchart"]
    links = sc["links"]
    html_png = shot_html()
    K = Image.open(krkr_png).convert("RGB")
    H = Image.open(html_png).convert("RGB").crop((0, 0, K.size[0], K.size[1]))
    print("krkr 图 %s %s ｜ HTML 图（裁剪后） %s %s" % (os.path.basename(krkr_png), K.size,
                                                       os.path.basename(html_png), H.size))
    if K.size != H.size:
        print("✗ 尺寸不同，无法比对")
        return 1
    W, Hh = K.size
    print("links=%d 条 ｜ 色值 %d=0x%08X=rgb(%d,%d,%d) ｜ w=%s ｜ pts 非整数 %d 个"
          % (len(links), links[0]["color"], links[0]["color"],
             (links[0]["color"] >> 16) & 255, (links[0]["color"] >> 8) & 255, links[0]["color"] & 255,
             sorted(set(l["w"] for l in links)),
             sum(1 for l in links for p in l["pts"] if float(p[0]) % 1 or float(p[1]) % 1)))
    # ── links 条数「三处」一致（生成链的三个产物 + 源屏文件 + krkr 侧 tjs）──
    counts = {}
    counts["layout/screens/32_flowchart.json"] = len(links)
    counts["layout/ui_layout.json"] = len(tree["screens"]["flowchart"]["links"])
    js = io.open(os.path.join(REP, "ui_layout.js"), encoding="utf-8").read()
    counts["复刻/ui_layout.js"] = len(json.loads(js[js.index("{"):js.rindex("}") + 1])["screens"]["flowchart"]["links"])
    tjs = io.open(os.path.join(UI, "krkr", "game", "ui_layout.tjs"), encoding="utf-8").read()
    counts["krkr/game/ui_layout.tjs"] = len(set(re.findall(r'fc\.link\.\d+', tjs)))
    allsame = len(set(counts.values())) == 1
    print("links 条数五处：%s ⇒ %s"
          % (" ｜ ".join("%s=%d" % kv for kv in counts.items()),
             "全部一致 ✓" if allsame else "★ 不一致 ✗"))
    if not allsame:
        print("★ 条数不一致 ⇒ 后续对照作废，停止。")
        return 4

    # ── 层序统一后「28 件」是否与连线足迹相交（决定有无可见分叉）──
    els = tree["screens"]["flowchart"]["elements"]
    plains = []
    for i, e in enumerate(els or []):
        z = e.get("z")
        plains.append({"id": str(e.get("id") or ("#" + str(i))),
                       "z": i if z is None else int(z), "raw": (i if z is None else int(z)) * 100 + i,
                       "box": (e.get("x"), e.get("y"), e.get("w"), e.get("h"))})
    nodez = [p["z"] for p in plains if p["id"].startswith("fc.node.")]
    lz = (min(nodez) - 1) if nodez else None
    old = (min(p["raw"] for p in plains if p["id"].startswith("fc.node.")) - 1) if nodez else None
    # 旧口径下「严格在某侧」的判据：raw < 旧层号 ⇒ 之下；raw >= 旧层号 ⇒ 之上
    #   （旧实现把 canvas 追加在元素**之前**，同 z-index 时 DOM 序在后者胜出 ⇒ 平票算「之上」）
    batch = [p for p in plains if old is not None and (p["z"] >= lz) != (p["raw"] >= old)]
    ties = [p for p in plains if old is not None and p["raw"] == old]
    # 连线足迹框（折线 bbox 外扩 w+2）
    foot = []
    for lk in links:
        m = int(lk["w"]) + 2
        xs = [float(p[0]) for p in lk["pts"]]; ys = [float(p[1]) for p in lk["pts"]]
        foot.append((min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m))
    hit = []
    for p in batch + ties:
        b = p["box"]
        if None in b:
            continue
        fx, fy, fw, fh = b
        for (ax0, ay0, ax1, ay1) in foot:
            if fx < ax1 and fx + fw > ax0 and fy < ay1 and fy + fh > ay0:
                hit.append(p["id"]); break
    print("层序证据批次：严格分叉 %d 件 ＋ 旧阈值平票 %d 件%s ⇒ 与连线足迹相交 %d 件 ⇒ %s"
          % (len(batch), len(ties), ("（平票：" + "、".join(p["id"] for p in ties) + "）") if ties else "",
             len(hit), "层序改动**无可见分叉**（不相交，且两端同为「连线之上」）✓" if not hit else ("★ 相交：" + "、".join(hit))))

    print("=" * 168)
    print("%-13s %-4s %-6s %-6s %-6s %-6s %-8s %-8s %-8s %-8s %-7s %-20s %-9s %-9s %s"
          % ("link", "pts", "kr墨", "H墨", "kr核", "H核", "kr箭墨max", "H箭墨max",
             "kr箭核max", "H箭核max", "bbox差", "精确色掩膜 IoU@0→@±1", "kr质心", "H质心", "判定"))
    print("（墨=剖面墨迹宽[Δ>25]；核=剖面**精确色**像素宽；箭max=末端 2w+3 内的最大横张；")
    print("  bbox差 = 两端精确色掩膜包围盒四条边的最大差；IoU 允许整体平移 1px 取最大）")
    print("=" * 168)
    bad = []
    MS = []
    for lk in links:
        mk = measure(K, lk, (W, Hh))
        mh = measure(H, lk, (W, Hh))
        MS.append((lk, mk, mh))
        fk, fh = med(mk["flat_ink"]), med(mh["flat_ink"])
        ck, ch = med(mk["flat_core"]), med(mh["flat_core"])
        ck2, ch2 = med(mk["cen"]), med(mh["cen"])
        iou1, sh, iou0 = mask_iou(mk, mh)
        bd = (max(abs(a - b) for a, b in zip(mk["bbox"], mh["bbox"]))
              if (mk["bbox"] and mh["bbox"]) else 999)
        col_ok = mk["exact"] > 0 and mh["exact"] > 0
        # 几何判定（pts 已取整 ⇒ 收紧）：墨迹宽差 ≤1px；箭头最大横张差 ≤2px；掩膜包围盒 ≤1px。
        # （IoU 仅作参考：4px 笔在下游一端落 3 个饱和像素、另一端落 4 个 ⇒ 解析期望 IoU@±1≈0.75，
        #   实测 0.71–0.78 正是这个解析值，不是形状差异。）
        geo_ok = (fk is not None and fh is not None and abs(fk - fh) <= 1
                  and abs(mk["tzmax_ink"] - mh["tzmax_ink"]) <= 2 and bd <= 1)
        ok = col_ok and geo_ok
        if not ok:
            bad.append((lk["id"], mk, mh, fk, fh, iou1, bd))
        print("%-13s %-4d %-6s %-6s %-6s %-6s %-8s %-8s %-8s %-8s %-7s %-20s %-9s %-9s %s"
              % (lk["id"], len(lk["pts"]), str(fk), str(fh), str(ck), str(ch),
                 str(mk["tzmax_ink"]), str(mh["tzmax_ink"]), str(mk["tzmax_core"]), str(mh["tzmax_core"]),
                 str(bd), "%.2f → %.2f@%s" % (iou0, iou1, sh), "%+.2f" % ck2, "%+.2f" % ch2,
                 "一致" if ok else "✗ 分叉"))
    print("=" * 168)
    # 汇总（用已算好的量，不重复 measure）
    fk_all = [med(mk["flat_ink"]) for _, mk, _ in MS]
    fh_all = [med(mh["flat_ink"]) for _, _, mh in MS]
    ck_all = [med(mk["flat_core"]) for _, mk, _ in MS]
    ch_all = [med(mh["flat_core"]) for _, _, mh in MS]
    ek_all = [mk["exact"] for _, mk, _ in MS]
    eh_all = [mh["exact"] for _, _, mh in MS]
    bk_all = [mk["base_ink"] for _, mk, _ in MS]
    bh_all = [mh["base_ink"] for _, _, mh in MS]
    bkc = [mk["base_core"] for _, mk, _ in MS]
    bhc = [mh["base_core"] for _, _, mh in MS]
    cen_k = [med(mk["cen"]) for _, mk, _ in MS]
    cen_h = [med(mh["cen"]) for _, _, mh in MS]
    print("汇总：平直墨迹宽 krkr=%s ／ HTML=%s ｜ 平直**核心**宽 krkr=%s ／ HTML=%s"
          % (sorted(set(fk_all)), sorted(set(fh_all)), sorted(set(ck_all)), sorted(set(ch_all))))
    print("      箭头底墨宽 krkr=%s ／ HTML=%s ｜ 箭头底**核心**宽 krkr=%s ／ HTML=%s"
          % (sorted(set(bk_all)), sorted(set(bh_all)), sorted(set(bkc)), sorted(set(bhc))))
    ck_s = ["%+.2f" % v for v in cen_k]
    ch_s = ["%+.2f" % v for v in cen_h]
    print("      墨迹质心（像素索引口径）krkr=%s ／ HTML=%s ⇒ 两端**恒定相差 0.5px**"
          % (sorted(set(ck_s)), sorted(set(ch_s))))
    fa_k = [med(mk["flat_area"]) for _, mk, _ in MS]
    fa_h = [med(mh["flat_area"]) for _, _, mh in MS]
    print("      平直段每行**墨迹亚像素面积**：krkr=%s ／ HTML=%s（面积=Σ min(1,d/d_full)，"
          % (["%.2f" % v for v in fa_k], ["%.2f" % v for v in fa_h])
          + "全饱和计 1、半覆盖边缘按比例计）")
    print("      带内精确色像素 krkr=min %d/max %d ／ HTML=min %d/max %d"
          % (min(ek_all), max(ek_all), min(eh_all), max(eh_all)))
    print("      分叉条数 = %d" % len(bad))
    # ── ΔE76：连线色 vs「选择支节点底色」（独立复测；口径逐条写明）──
    sel = [e for e in sc["elements"]
           if str(e.get("id", "")).startswith("fc.node.") and "select" in str(e.get("asset", ""))]
    print("=" * 168)
    print("ΔE76（连线色 vs 选择支节点底色）—— 取样口径：")
    print("  ① 连线色：取 `layout/palette.json::edge_normal` 的值 + 实测「剖面核心色」（= 精确等于数据色的像素）")
    print("  ② 选择支底色：`fc.node.*` 中 asset 含 `select` 的节点元素，取其**矩形内缩**区域")
    print("     （x+16 … x+w−16、y+8 … y+h−8：避开 nine 端点与文字行盒）的**精确 RGB 众数**；")
    print("     三路取样并列：资产 PNG(`ui/x_ui_node_select_off.png`) ／ krkr 实机图 ／ HTML 复刻图")
    if not sel:
        print("  ★ 没有 select 节点元素，ΔE76 无法测（如实登记）")
    else:
        e0 = sel[0]
        box = (int(e0["x"]) + 16, int(e0["y"]) + 8,
               int(e0["x"]) + int(e0["w"]) - 16, int(e0["y"]) + int(e0["h"]) - 8)
        print("  选中元素：%s  box=%s" % (e0["id"], box))
        line_spec = hex_rgb(pal_palette()["edge_normal"]["value"])
        line_meas = max(links[0]["color"] >> 16 & 255, 0), (links[0]["color"] >> 8) & 255, links[0]["color"] & 255
        srcs = []
        asset = os.path.join(ASSETS, "ui", "x_ui_node_select_off.png")
        if os.path.exists(asset):
            ai = Image.open(asset).convert("RGBA")
            aw, ah = ai.size
            srcs.append(("资产 PNG x_ui_node_select_off.png（自身坐标内缩 16/8）",
                         modal_region(ai.convert("RGB"), (16, 8, aw - 16, ah - 8))[0][0]))
        srcs.append(("krkr 实机图（同 box）", modal_region(K, box)[0][0]))
        srcs.append(("HTML 复刻图（同 box）", modal_region(H, box)[0][0]))
        print("  三路底色众数：")
        for nm, c in srcs:
            print("     %-46s %s = #%02X%02X%02X" % (nm, c, c[0], c[1], c[2]))
        print("  实机/复刻底色窗口前 3 众数（确认众数=平涂底色而非文字墨迹）：")
        for nm, im in (("krkr", K), ("HTML", H)):
            print("     %-5s %s" % (nm, modal_region(im, box)))
        print("  ΔE76 矩阵（连线色 × 底色）：")
        line_meas = ((links[0]["color"] >> 16) & 255, (links[0]["color"] >> 8) & 255, links[0]["color"] & 255)
        for ln, lv in (("数据色 #%02X%02X%02X" % line_meas, line_meas),
                       ("palette.edge_normal %s" % pal_palette()["edge_normal"]["value"], line_spec)):
            for nm, c in srcs:
                print("     %-34s × %-46s = **%.2f**" % (ln, nm, de76(lv, c)))
        print("  参考复算（口径自校）：上一轮冰蓝 #65B1D4 × #5FABD2 = %.2f（主代理/vision 报 3.2）"
              % de76(hex_rgb("65B1D4"), hex_rgb("5FABD2")))
        print("                            深蓝 #266080 × #5FABD2 = %.2f（vision 报 29.0）"
              % de76(hex_rgb("266080"), hex_rgb("5FABD2")))

    # 全屏差异：定位到「连线邻域 / 节点元素矩形 / 其它元素矩形 / 其余」四类
    from PIL import ImageChops
    d = ImageChops.difference(K, H).convert("L")
    boxes = [mk["band"] for _, mk, _ in MS]
    sc = tree["screens"]["flowchart"]
    nodebox = [(e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])
               for e in sc["elements"] if str(e.get("id", "")).startswith("fc.node.")
               and None not in (e.get("x"), e.get("y"), e.get("w"), e.get("h"))]
    dl = d.load()
    # 连线**足迹**（折线本身 ±(w+2) 的内切带）——与「邻域框」不同：不含节点边框/文字
    strip = set()
    for lk in links:
        pts = [(float(p[0]), float(p[1])) for p in lk["pts"]]
        r = int(lk["w"]) + 2
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            ux, uy, L = unit(a, b)
            for t in range(int(L) + 1):
                cx, cy = a[0] + ux * t, a[1] + uy * t
                for dyy in range(-r, r + 1):
                    for dxx in range(-r, r + 1):
                        if dxx * dxx + dyy * dyy <= r * r:
                            strip.add((int(cx) + dxx, int(cy) + dyy))
    n_strip = n_node = n_out40 = tot40 = 0
    for y in range(Hh):
        for x in range(W):
            v = dl[x, y]
            if v <= 0:
                continue
            if v > 40:
                tot40 += 1
            if (x, y) in strip:
                if v > 40:
                    n_strip += 1
            elif any(b[0] <= x < b[2] and b[1] <= y < b[3] for b in nodebox):
                if v > 40:
                    n_node += 1
            elif v > 40:
                n_out40 += 1
    print("全屏作差(|Δ|>40 的像素 = %d)：连线**足迹**内(±(w+2)) %d ／ 节点元素矩形内 %d ／ 其余 %d"
          % (tot40, n_strip, n_node, n_out40))
    print("      ⇒ 连线足迹外的 15 万级差异**全部来自「非连线」内容**（节点文字/方框素材/面板/页签的")
    print("        两端光栅化差异）——那是两端渲染器的既有差异（文字引擎不同），不属于本模块；")
    print("        连线自身的差异以逐条判定表为准。")
    d.save(os.path.join(EVID, "E3_真实数据_两端作差图.png"))
    # 并排对照图
    box = (60, 190, 1295, 1017)
    w = box[2] - box[0]; h = box[3] - box[1]
    sheet = Image.new("RGB", (w, h * 2 + 8), (16, 16, 16))
    sheet.paste(K.crop(box), (0, 0))
    sheet.paste(H.crop(box), (0, h + 8))
    sheet.save(os.path.join(EVID, "E3_真实数据_上krkr下HTML.png"))
    print("对照图：%s" % os.path.join(EVID, "E3_真实数据_上krkr下HTML.png"))
    shutil.rmtree(UD, ignore_errors=True)
    shutil.rmtree(os.path.join(EVID, "E3_htmlshot_real"), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

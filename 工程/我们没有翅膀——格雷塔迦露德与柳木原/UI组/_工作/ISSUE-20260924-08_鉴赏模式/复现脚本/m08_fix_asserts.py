# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · 用户三条修复指令的验收断言（T1 墨迹量测 / T2 名单 7 行 / T3 dr.big 容纳）

■ 用法
    python m08_fix_asserts.py --t1 <music页1:1截图.png>   # T1：30 行逐行断言「文字墨迹 ⊆ 胶囊条内」
    python m08_fix_asserts.py --t2                        # T2：dress 屏人名 7 行数据断言
    python m08_fix_asserts.py --t3                        # T3：面板 56 件 ⊆ dr.big + chrome 不重叠
    python m08_fix_asserts.py                             # T2+T3（T1 需截图参数）

■ T1 量测口径（一手数字，不凭印象）
  · 行几何：`28_music.json` 的 `mu.list`（x171,y207,item 526×59,gap1,3×10）——数据为唯一真相源；
  · 胶囊可见体：`x_ui_bgm_row_off.png` 的 alpha 实测（行/列 alpha>64 的密集带）；
  · 文字墨迹：截图上 item_text 窗口（块内 x40,y0,w434,h59）内亮度 <90 的像素
    （文字色 = 深藏青 node_locked；胶囊边 #0079B6 亮度 ≈100，不会误报）；
  · 断言：墨迹 bbox 上下沿均须落进胶囊密集带内、且与带沿留 ≥1px 余量（骑线即 FAIL）。
"""
import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCR = os.path.join(UI, "layout", "screens")
ASSET = os.path.join(UI, "krkr", "assets", "ui")

FAILS = []


def check(ok, msg):
    print(("  [OK] " if ok else "  [FAIL] ") + msg)
    if not ok:
        FAILS.append(msg)


def load(sid):
    return json.load(io.open(os.path.join(SCR, sid), encoding="utf-8"))


# ---------------------------------------------------------------- T1
def _capsule_interior(png_path):
    """胶囊「亮填充内带」一手实测（PNG alpha>200 的像素）：
    行/列均值亮度 >200 = 填充区（描边行均值 ~161-178、填充行 ~239，阈值 200 干净分离）。
    返回 (x0, y0, x1, y1)，块内坐标。"""
    im = Image.open(png_path).convert("RGBA")
    W, H = im.size
    pa = im.load()

    def rowmean(y):
        v = [pa[x, y] for x in range(W) if pa[x, y][3] > 200]
        if not v:
            return 0.0, 0
        return sum(0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in v) / len(v), len(v)

    def colmean(x):
        v = [pa[x, y] for y in range(H) if pa[x, y][3] > 200]
        if not v:
            return 0.0, 0
        return sum(0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in v) / len(v), len(v)

    rows = [y for y in range(H) if rowmean(y)[0] > 200 and rowmean(y)[1] > W * 0.5]
    cols = [x for x in range(W) if colmean(x)[0] > 200 and colmean(x)[1] > H * 0.5]
    return (cols[0], rows[0], cols[-1], rows[-1])


def _row_ink_margins(img, rx, ry, cap, tw, thr=90):
    """一行胶囊内的文字墨迹量测：只扫「亮填充内带 ∩ 文字窗」上的深色像素。
    带外是页面底色（临时页隐藏外壳后为纯黑）与描边行，不算墨迹；带内填充亮（实测 ~239）。
    cap = (x0,y0,x1,y1) 内带（块内坐标）；x 取 max(内带+4, 文字窗+4)..min(内带-4, 文字窗-4)
    —— 实测圆角弧伪影在带外缘 x≤42 / ≥477（dy12..15、42..44），文字窗 x40..473 内缩 4px 后
    （44..470）恰好全部排除。
    返回 (首墨行偏移, 末墨行偏移, 墨迹像素数)；无墨迹返回 None。"""
    px = img.load()
    x0 = rx + max(cap[0] + 4, tw["x"] + 4)
    x1 = rx + min(cap[2] - 4, tw["x"] + tw["w"] - 4)
    y0, y1 = cap[1], cap[3]
    first = last = None
    cnt = 0
    for dy in range(y0, y1 + 1):
        c = 0
        for x in range(x0, x1 + 1):
            p = px[x, ry + dy]
            if (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) < thr:
                c += 1
        if c:
            cnt += c
            if first is None:
                first = dy
            last = dy
    if first is None:
        return None
    return (first, last, cnt)


def _t1_one(img, mu, cap):
    """对一张 1:1 截图逐行量测；返回逐行 dict 列表（含 PASS/FAIL）。"""
    iw, ih, gap = mu["item_w"], mu["item_h"], mu["gap"]
    cols, rows_n = mu["max_cols"], mu["max_rows"]
    out = []
    for i in range(min(cols * rows_n, len(mu["labels"]))):
        c, r = i % cols, i // cols
        rx = mu["x"] + c * (iw + gap)
        ry = mu["y"] + r * (ih + gap)
        m = _row_ink_margins(img, rx, ry, cap, mu["item_text"])
        if m is None:
            out.append({"row": i + 1, "ok": False, "why": "内带未测到墨迹"})
            continue
        first, last, cnt = m
        mt, mb = first - cap[1], cap[3] - last       # 对亮填充内带上下沿的余量
        ok = (mt >= 1 and mb >= 1 and cnt >= 20)
        out.append({"row": i + 1, "ok": ok, "first": first, "last": last,
                    "mt": mt, "mb": mb, "cnt": cnt})
    return out


def t1(shot, engine_png=None):
    print("===== T1 · BGM 页 30 行「文字墨迹 ⊆ 胶囊条内」量测 =====")
    d = load("28_music.json")
    mu = [e for e in d["elements"] if e["id"] == "mu.list"][0]

    cap = _capsule_interior(os.path.join(ASSET, "x_ui_bgm_row_off.png"))
    print("  亮填充内带（PNG alpha>200 且行/列均值亮度>200 实测）: 块内 x%d..%d y%d..%d（描边与圆角弧在外）"
          % (cap[0], cap[2], cap[1], cap[3]))

    img = Image.open(shot).convert("RGB")
    if img.size != (1920, 1080):
        print("  [WARN] 截图尺寸 %s ≠ 1920×1080（非 1:1，量测前需确认缩放）" % (img.size,))
    res = _t1_one(img, mu, cap)
    print("  %-4s %-22s %-16s %-9s %s" % ("行", "墨迹行偏移", "对内带余量", "墨迹px", "判定"))
    for r in res:
        if "first" not in r:
            check(False, "第 %d 行：%s" % (r["row"], r["why"]))
            continue
        print("  %-4d y%d..%d              上余%+2d 下余%+2d   %-9d %s"
              % (r["row"], r["first"], r["last"], r["mt"], r["mb"], r["cnt"],
                 "PASS" if r["ok"] else "FAIL ← 骑线/出框"))
    check(all(r["ok"] for r in res) and len(res) == 30,
          "T1(HTML) 汇总：30/30 行墨迹完全落在胶囊条内（对内带余量 ≥1px）")

    if engine_png:
        eimg = Image.open(engine_png).convert("RGB")
        eres = _t1_one(eimg, mu, cap)
        bad = []
        for e in eres:
            if "first" not in e:
                bad.append("第%d行引擎无墨迹" % e["row"])
                continue
            if not (e["mt"] >= 1 and e["mb"] >= 1):
                bad.append("第%d行引擎出框(余%d/%d)" % (e["row"], e["mt"], e["mb"]))
        hmt = [r["mt"] for r in res if "mt" in r]
        hmb = [r["mb"] for r in res if "mb" in r]
        emt = [e["mt"] for e in eres if "mt" in e]
        emb = [e["mb"] for e in eres if "mb" in e]
        print("  引擎对照（%s）：余量范围 HTML 上余%s..下余%s ｜ 引擎 上余%s..下余%s"
              % (os.path.basename(engine_png),
                 min(hmt), min(hmb), min(emt), min(emb)))
        check(not bad, "T1(引擎) 对照：引擎端 30 行同样入条（异常：%s）" % (bad or "无"))


# ---------------------------------------------------------------- T2
def t2():
    print("===== T2 · dress 屏人名 7 行数据断言 =====")
    d = load("37_dress.json")
    by = {e["id"]: e for e in d["elements"]}
    want = ["渡来明日香", "山科京", "玉泉日和子", "凤鸣", "羽田小鸠", "香田亚衣", "林田美咲"]
    fams = ["asu", "miy", "hiy", "nar", "kob", "ai_", "mis"]
    gone = [i for i in range(8, 13)
            for n in ("dr.name_tx_%d" % i, "dr.hit_name_%d" % i) if n in by]
    check(not gone, "第 8..12 行（tx+hit）已全部删除（残留：%s）" % (gone or "无"))
    for i, (nm, fm) in enumerate(zip(want, fams), 1):
        e = by.get("dr.name_tx_%d" % i)
        h = by.get("dr.hit_name_%d" % i)
        if not e or not h:
            check(False, "第 %d 行缺失" % i)
            continue
        g_ok = (e["x"] == 34 and e["y"] == 181 + 60 * (i - 1) and e["w"] == 192 and e["h"] == 47)
        check(e["sample"] == nm and g_ok and h["x"] == 0 and h["y"] == e["y"] and h["h"] == 47,
              "第 %d 行「%s」sample/几何 (x34 y%d 192×47) / 热区同步 %s"
              % (i, nm, e["y"], "OK" if g_ok else "错"))
        check("`%s`" % fm in e["note"], "第 %d 行 note 登记立绘族 `%s`" % (i, fm))
    sm = by["dr.sel_mark"]
    check(sm["y"] == 193 and 181 <= sm["y"] and sm["y"] + sm["h"] <= 228,
          "dr.sel_mark (x%d y%d %dx%d) 落第 1 行（y181..228）" % (sm["x"], sm["y"], sm["w"], sm["h"]))
    check("T2 名单定版" in d["note"] and "只有主角，不加配角" in d["note"] and "`miy`" in d["note"],
          "屏 note 登记「11→7 行 + 用户裁定 + 7 条族映射（含 kyo→miy 订正）」")
    nl = by["dr.namelist"]
    check(181 + 60 * 6 + 47 <= nl["y"] + nl["h"], "第 7 行底 y%d ⊆ 底图（y%d..%d）" % (181 + 60 * 6 + 47, nl["y"], nl["y"] + nl["h"]))


# ---------------------------------------------------------------- T3
def t3():
    print("===== T3 · 面板 56 件 ⊆ dr.big + chrome 不重叠 =====")
    d = load("37_dress.json")
    by = {e["id"]: e for e in d["elements"]}
    big = by["dr.big"]
    bx0, by0, bx1, by1 = big["x"], big["y"], big["x"] + big["w"], big["y"] + big["h"]
    check((bx0, by0, bx1, by1) == (204, 164, 986, 550),
          "dr.big = (204,164) 782×386（实测 x%d y%d w%d h%d）" % (big["x"], big["y"], big["w"], big["h"]))
    check(0 <= bx0 and bx1 <= 1920 and 0 <= by0 and by1 <= 1080, "dr.big ⊆ 1920×1080 画布")

    import re
    pat = re.compile(r"^dr\.(btn|btn_tx|hit)_(keep|hide|dress[0-4]|pose[0-2]|diff[013]|level[0-2]|faceright)$")
    panel = [e for e in d["elements"] if pat.match(e["id"]) or e["id"].startswith("dr.row_tx_") or e["id"] == "dr.face_tx"]
    check(len(panel) == 56, "面板元素共 56 件（实测 %d）" % len(panel))
    bad = []
    for e in panel:
        ex0, ey0 = e["x"], e["y"]
        ex1, ey1 = ex0 + e["w"], ey0 + e["h"]
        if not (ex0 >= bx0 and ey0 >= by0 and ex1 <= bx1 and ey1 <= by1):
            bad.append("%s(x%d y%d %dx%d)" % (e["id"], ex0, ey0, e["w"], e["h"]))
    check(not bad, "56 件面板元素矩形全部 ⊆ dr.big（出框：%s）" % (bad or "无"))

    # 边距（视觉余量，一手数字）
    labs = [e for e in panel if e["id"].startswith("dr.row_tx_")]
    d4 = by["dr.btn_dress4"]
    keep = by["dr.btn_keep"]
    ftx = by["dr.face_tx"]
    print("  边距：左 %d（row_tx）右 %d（dress4）上 %d（keep）下 %d（face_tx）"
          % (min(e["x"] for e in labs) - bx0, bx1 - (d4["x"] + d4["w"]),
             keep["y"] - by0, by1 - (ftx["y"] + ftx["h"])))

    # 有意保持在板外的 chrome：与 dr.big 零重叠
    chrome = ["dr.ctrl", "dr.reset", "dr.namelist"] + \
             ["dr.hit_ctrl_%s" % k for k in ("left", "bg", "right", "time", "text", "textwin", "capture", "save", "load", "hide", "help")] + \
             ["dr.hit_reset", "dr.dim"]
    chrome = [c for c in chrome if c in by]
    ov = []
    for cid in chrome:
        e = by[cid]
        ex0, ey0, ex1, ey1 = e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"]
        if cid == "dr.dim":      # 全屏压暗层，属设计内叠放，不在断言内
            continue
        if ex0 < bx1 and ex1 > bx0 and ey0 < by1 and ey1 > by0:
            ov.append(cid)
    check(not ov, "chrome（控制条/reset/人名列表/热区）与 dr.big 零重叠（重叠：%s）" % (ov or "无"))

    # 外壳页签条（39_gal_shell）：条带 y0..87 与 dr.big 无纵向交集
    sh = load("39_gal_shell.json")
    strip = [e for e in sh["elements"] if e["id"] == "gs.strip"][0]
    check(strip["y"] + strip["h"] <= by0, "外壳页签条底 y%d ≤ dr.big 顶 y%d" % (strip["y"] + strip["h"], by0))


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--t1" in args:
        ep = None
        if "--engine" in args:
            ep = args[args.index("--engine") + 1]
        t1(args[args.index("--t1") + 1], ep)
    if "--t2" in args or not any(a.startswith("--t") for a in args):
        t2()
    if "--t3" in args or not any(a.startswith("--t") for a in args):
        t3()
    print("===== %s =====" % ("FAIL（%d 条）" % len(FAILS) if FAILS else "ALL PASS"))
    sys.exit(1 if FAILS else 0)

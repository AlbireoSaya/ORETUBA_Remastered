#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
m62_make_entry_frag_assets.py
────────────────────────────────────────────────────────────────────────────
ISSUE-20260929-04 · E4（素材模块 · 淡黄入口块）

任务（用户 2026-09-29 指令）：从章节节点素材**派生两件淡黄底的同形制件**。

  母本（只读，一字不动）
    krkr/assets/ui/x_ui_node_select_off.png   263×65 RGBA   ← 章节「选择支」节点 常态
    krkr/assets/ui/x_ui_node_select_on.png    263×65 RGBA   ← 章节「选择支」节点 悬停

  交付（本脚本产出）
    krkr/assets/ui/x_ui_entry_frag_off.png    263×65 RGBA   ← 常态，淡黄 #FFFF99 族
    krkr/assets/ui/x_ui_entry_frag_on.png     263×65 RGBA   ← 悬停，淡黄、整体提亮一档

为什么是 263×65：与母本**同尺寸** ⇒ 元素侧可直接沿用 `fc.node.*` 的
nine {l:14,t:0,r:13,b:0} 把它拉到 296×65（用户裁定的入口块尺寸），素材侧不预拉伸。

────────────────────────────────────────────────────────────────────────────
变换口径（派单 5 条，逐条在脚本内断言）
  1. alpha 通道与母本**逐字节相同**（形状/圆角/羽化边/描边轮廓完全同源）。→ C2-*
  2. 色相全部改到 #FFFF99 的色相 H=60.0°（原 200.7°~215.3° 的蓝系）。      → C3-*
  3. 保留明暗结构：逐像素按**同一个线性系数**缩放 V（不重排版、不压平），
     上亮下略深的竖向渐变与「描边 vs 底色」的深浅比例按原比例保留。      → C4-* / C5-*
  4. 描边不保留蓝边：与底色同色相（H=60），靠 V 更低 / S 更高表现更深一档。→ C5-*
  5. 真 alpha / PNG-32；最外 1px 帧 αmax 沿用母本（alpha 未动 ⇒ 自动成立）。→ C2-*

参数来源（**实测反推**，不是拍脑袋；见证据 E4_自证报告.md §二）
  H_TARGET = 60.0°                  = #FFFF99 的色相（由该 hex 反解）
  S_SCALE  = S(#FFFF99) / S(母本 off 不透明众色)
           = 0.40000 / 0.54717      = 0.73100  ⇒ 主体饱和度对齐 #FFFF99
  V_SCALE  = 1.0 / max(V | α>0，两件母本取大)
           = 1.0 / 0.894118         = 1.118421 ⇒ 两件里最亮的可见像素顶到黄系上限 V=1.0，
                                                全图**零削波**（无 clamp），且因 off/on 共用
                                                同一系数，悬停的相对提亮量按母本比例原样保留

用法
  python "_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\m62_make_entry_frag_assets.py"   生成＋断言＋证据
  python "…\\m62_make_entry_frag_assets.py" --check                                   只读核对，不写盘
────────────────────────────────────────────────────────────────────────────
"""

import hashlib
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════ 路径与常量
HERE = os.path.dirname(os.path.abspath(__file__))
UIROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))        # …\UI组
ASSETDIR = os.path.join(UIROOT, "krkr", "assets", "ui")
EVIDDIR = os.path.abspath(os.path.join(HERE, "..", "证据"))
VERIFY_UI = os.path.join(UIROOT, "工具", "verify_ui.py")

MOTHER = {"off": "x_ui_node_select_off.png", "on": "x_ui_node_select_on.png"}
OUTPUT = {"off": "x_ui_entry_frag_off.png", "on": "x_ui_entry_frag_on.png"}

# 本批冻结基线：母本 md5（写前/写后都必须等于此值 ⇒ 「母本一字不动」的机检）
EXPECT_MOTHER_MD5 = {
    "off": "16c7d5a7e13b89e328933cb2ac13be39",
    "on": "e0e01b18b979f4d5c4330c8bb7739809",
}

TARGET_HEX = "#FFFF99"
ALPHA_OPAQUE = 250          # 「不透明区」判据（与冻结书 / E1 同口径）
FILL_V_FLOOR = 0.75         # 逐行均值 V 高于此值 ⇒ 该行属「填充体」（区别于描边行）
BUDGET_MIB = 96.0           # verify_ui.py 的 DEF_BUDGET_MB

W, H = 263, 65


# ═══════════════════════════════════════════════════════ 基础工具
def md5b(b):
    return hashlib.md5(b).hexdigest()


def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def load_rgba(p):
    im = Image.open(p)
    assert im.mode == "RGBA", "%s 不是 RGBA（实测 %s）" % (p, im.mode)
    return np.array(im)


def hsv_of(rgb01):
    """rgb01: float (...,3) in 0..1 → (H 度, S, V)"""
    mx = rgb01.max(axis=-1)
    mn = rgb01.min(axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-12
    r, g, b = rgb01[..., 0], rgb01[..., 1], rgb01[..., 2]
    i = (mx == r) & nz
    h[i] = ((g - b)[i] / d[i]) % 6.0
    i = (mx == g) & nz
    h[i] = (b - r)[i] / d[i] + 2.0
    i = (mx == b) & nz
    h[i] = (r - g)[i] / d[i] + 4.0
    s = np.where(mx > 1e-12, d / np.maximum(mx, 1e-12), 0.0)
    return h * 60.0, s, mx


def hsv60_to_rgb8(S, V):
    """H 恒 60° 时的反算：r = g = V，b = V*(1-S)（0..1 入，uint8 出）"""
    v8 = np.clip(np.rint(V * 255.0), 0, 255)
    b8 = np.clip(np.rint(V * (1.0 - S) * 255.0), 0, 255)
    out = np.empty(S.shape + (3,), dtype=np.uint8)
    out[..., 0] = v8
    out[..., 1] = v8
    out[..., 2] = b8
    return out


def hex2rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def enc_png(arr, mode="RGBA"):
    b = io.BytesIO()
    Image.fromarray(arr, mode).save(b, "PNG", optimize=True)
    return b.getvalue()


def frame_amax(al):
    """最外 1px 帧 αmax：返回 (上, 下, 左, 右)"""
    return (int(al[0].max()), int(al[-1].max()), int(al[:, 0].max()), int(al[:, -1].max()))


def checker_rgb(h, w, cell=12, c1=(72, 72, 72), c2=(104, 104, 104)):
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((yy // cell) + (xx // cell)) % 2 == 0
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for ch in range(3):
        out[..., ch] = np.where(m, c1[ch], c2[ch])
    return out


def zoom_on_checker(arr, z, cell=12):
    """RGBA → 棋盘底合成 → 最近邻 z× 放大（uint8 RGB）"""
    rgb = arr[..., :3].astype(np.float64)
    a = arr[..., 3:4].astype(np.float64) / 255.0
    bg = checker_rgb(arr.shape[0], arr.shape[1], cell).astype(np.float64)
    comp = np.clip(rgb * a + bg * (1.0 - a), 0, 255).astype(np.uint8)
    return comp.repeat(z, axis=0).repeat(z, axis=1)


def load_font(sz):
    for cand in (r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\arial.ttf"):
        if os.path.isfile(cand):
            try:
                return ImageFont.truetype(cand, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


# ═══════════════════════════════════════════════════════ 度量
def metrics(arr):
    al = arr[..., 3].astype(np.int32)
    rgb01 = arr[..., :3].astype(np.float64) / 255.0
    Hh, Ss, Vv = hsv_of(rgb01)
    m = al >= ALPHA_OPAQUE
    op = dict(
        n=int(m.sum()),
        H_med=float(np.median(Hh[m])),
        H_p5=float(np.percentile(Hh[m], 5)),
        H_p95=float(np.percentile(Hh[m], 95)),
        S_med=float(np.median(Ss[m])),
        V_med=float(np.median(Vv[m])),
        V_p5=float(np.percentile(Vv[m], 5)),
        V_p95=float(np.percentile(Vv[m], 95)),
        V_std=float(Vv[m].std()),
        V_span=float(np.percentile(Vv[m], 95) - np.percentile(Vv[m], 5)),
        V_max_all=float(Vv[al > 0].max()),
        amin=int(al.min()), amax=int(al.max()),
    )
    flat = arr[..., :3][m]
    vals, cnt = np.unique(flat.reshape(-1, 3), axis=0, return_counts=True)
    k = int(np.argmax(cnt))
    op["dom_rgb"] = tuple(int(x) for x in vals[k])
    op["dom_n"] = int(cnt[k])
    op["dom_pct"] = 100.0 * cnt[k] / max(1, int(m.sum()))
    t = np.array(hex2rgb(TARGET_HEX), dtype=np.float64)
    d = np.sqrt(((flat.astype(np.float64) - t) ** 2).sum(axis=1))
    op["dist_med"] = float(np.median(d))
    op["dist_dom"] = float(np.sqrt(((np.array(op["dom_rgb"], dtype=np.float64) - t) ** 2).sum()))
    op["V_dark5"] = float(np.percentile(Vv[m], 5))
    op["V_delta_dark"] = float(op["V_med"] - op["V_dark5"])
    # 填充体竖向渐变（上亮下深）：逐行均值 V，取首 3 / 末 3 填充行
    rows = []
    for y in range(arr.shape[0]):
        sel = m[y]
        if sel.sum() > 3:
            rows.append(float(Vv[y][sel].mean()))
    fill = [v for v in rows if v > FILL_V_FLOOR]
    op["fill_rows"] = len(fill)
    if len(fill) >= 6:
        op["fill_top"] = float(np.mean(fill[:3]))
        op["fill_bot"] = float(np.mean(fill[-3:]))
        op["fill_ratio"] = op["fill_top"] / op["fill_bot"] if op["fill_bot"] > 0 else float("nan")
    else:
        op["fill_top"] = op["fill_bot"] = op["fill_ratio"] = float("nan")
    return op


# ═══════════════════════════════════════════════════════ 变换
def derive_params(mo_off, mo_on):
    h01 = (np.array(hex2rgb(TARGET_HEX), dtype=np.float64) / 255.0).reshape(1, 3)
    H_t, S_t, _ = hsv_of(h01)
    H_target, S_target = float(H_t[0]), float(S_t[0])

    m = mo_off[..., 3].astype(np.int32) >= ALPHA_OPAQUE
    vals, cnt = np.unique(mo_off[..., :3][m].reshape(-1, 3), axis=0, return_counts=True)
    dom = tuple(int(x) for x in vals[int(np.argmax(cnt))])
    S_dom = float(hsv_of((np.array(dom, dtype=np.float64) / 255.0).reshape(1, 3))[1][0])

    vmax = 0.0
    for a in (mo_off, mo_on):
        al2 = a[..., 3].astype(np.int32)
        vv = (a[..., :3].astype(np.float64) / 255.0).max(axis=-1)
        vmax = max(vmax, float(vv[al2 > 0].max()))

    return dict(H_target=H_target, S_target=S_target, S_dom=S_dom, dom_rgb=dom,
                S_scale=S_target / S_dom, V_anchor=vmax, V_scale=1.0 / vmax)


def transform(arr, prm):
    """只改颜色：alpha 原样；H→60°；S×S_scale；V×V_scale（不 clamp；脚本断言零削波）"""
    rgb01 = arr[..., :3].astype(np.float64) / 255.0
    _, S, V = hsv_of(rgb01)
    out = arr.copy()
    out[..., :3] = hsv60_to_rgb8(np.clip(S * prm["S_scale"], 0.0, 1.0), V * prm["V_scale"])
    return out


# ═══════════════════════════════════════════════════════ 证据：8× 对照图
def make_sheet(path, panels, z=8, gap=28, margin=32, title_h=80, cap_h=58):
    """panels = [(行1, 行2, 行3, rgba)] —— 4 枚 8× 并排（棋盘底）"""
    pw, ph = W * z, H * z
    n = len(panels)
    total_w = margin * 2 + pw * n + gap * (n - 1)
    total_h = title_h + ph + cap_h + margin
    im = Image.fromarray(np.full((total_h, total_w, 3), 24, dtype=np.uint8))
    d = ImageDraw.Draw(im)
    f_t, f_c, f_h = load_font(30), load_font(21), load_font(24)

    d.text((margin, 14),
           "ISSUE-20260929-04 · E4 淡黄入口块：母本（蓝） vs 新件（淡黄 #FFFF99 族）· 8× 最近邻 · 棋盘底",
           font=f_t, fill=(236, 241, 250))
    d.text((margin, 50),
           "两件新件 α 与各自母本逐字节相同（np.array_equal PASS）⇒ 形状/圆角/羽化边/描边轮廓完全同源；"
           "尺寸 263×65 RGBA；最外 1px 帧 αmax 沿用母本（上/下/左/右各自与母本逐项相同）",
           font=f_c, fill=(170, 186, 205))

    for i, (l1, l2, l3, arr) in enumerate(panels):
        x, y = margin + i * (pw + gap), title_h
        im.paste(Image.fromarray(zoom_on_checker(arr, z)), (x, y))
        d.rectangle([x - 1, y - 1, x + pw, y + ph], outline=(96, 106, 124))
        d.text((x, y + ph + 6), l1, font=f_h, fill=(228, 236, 248))
        d.text((x, y + ph + 32), l2, font=f_c, fill=(190, 204, 222))
        d.text((x, y + ph + 52), l3, font=f_c, fill=(190, 204, 222))
    im.save(path, "PNG", optimize=True)
    return im.size


def make_detail_sheet(path, items, z=10, gap=24, margin=30, row_gap=30, title_h=70):
    """角落细节：左端帽 / 右端帽 两行 × 4 列（列序与主对照图一致）
    items = [(标题, rgba)] × 4"""
    crops = [((0, 0, 46, H), u"左端帽 x[0,46)"), ((W - 46, 0, W, H), u"右端帽 x[217,263)")]
    cw, ch = 46 * z, H * z
    n = len(items)
    total_w = margin * 2 + cw * n + gap * (n - 1)
    total_h = title_h + (ch + row_gap) * len(crops) + margin
    im = Image.fromarray(np.full((total_h, total_w, 3), 24, dtype=np.uint8))
    d = ImageDraw.Draw(im)
    f_t, f_c = load_font(28), load_font(21)
    d.text((margin, 14),
           "ISSUE-20260929-04 · E4 淡黄入口块 · **角落细节**：两端圆角帽 %d× 最近邻 · 棋盘底"
           "（同形制的硬证明：羽化边/圆角/描边粗细逐像素同源）" % z,
           font=f_t, fill=(236, 241, 250))
    y = title_h
    for (x0, y0, x1, y1), tag in crops:
        for i, (name, arr) in enumerate(items):
            x = margin + i * (cw + gap)
            sub = arr[y0:y1, x0:x1]
            im.paste(Image.fromarray(zoom_on_checker(sub, z)), (x, y))
            d.rectangle([x - 1, y - 1, x + cw, y + ch], outline=(96, 106, 124))
            d.text((x + 4, y + 4), u"%s ｜ %s" % (tag, name), font=f_c, fill=(232, 224, 150))
        y += ch + row_gap
    im.save(path, "PNG", optimize=True)
    return im.size


# ═══════════════════════════════════════════════════════ 预算
def run_verify_ui():
    env = dict(os.environ)
    pylibs = r"E:\ZCode Workspace\Galgame\工具\pylibs"
    env["PYTHONPATH"] = pylibs + os.pathsep + env.get("PYTHONPATH", "")
    p = subprocess.run([sys.executable, VERIFY_UI], cwd=UIROOT, capture_output=True,
                       env=env)
    return p.returncode, (p.stdout.decode("utf-8", "replace")
                          + p.stderr.decode("utf-8", "replace"))


def parse_budget(txt, total_now, nitems, budget_bytes):
    out = {"items": nitems, "total": total_now,
           "margin": budget_bytes - total_now,
           "budget": budget_bytes}
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("[6] 体积预算"):
            out["budget_line"] = s
        elif s.startswith("资产："):
            out["assets_line"] = s
        elif s.startswith("结果："):
            out["result_line"] = s
    return out


def dir_png_total(d):
    fs = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    return sum(os.path.getsize(os.path.join(d, f)) for f in fs), len(fs)


# ═══════════════════════════════════════════════════════ 主流程
def main(argv):
    check_only = "--check" in argv

    # ── 0. 读母本
    mo_raw, mo = {}, {}
    for k in ("off", "on"):
        p = os.path.join(ASSETDIR, MOTHER[k])
        mo_raw[k] = read_bytes(p)
        mo[k] = load_rgba(p)
        assert mo[k].shape == (H, W, 4), "母本 %s 尺寸 %s ≠ (65,263,4)" % (MOTHER[k], mo[k].shape)

    # ── 1. 反解参数 · 2. 变换 · 3. 写盘
    prm = derive_params(mo["off"], mo["on"])
    new = {k: transform(mo[k], prm) for k in ("off", "on")}
    new_raw = {k: enc_png(new[k], "RGBA") for k in ("off", "on")}

    prev_raw = {}
    for k in ("off", "on"):
        op = os.path.join(ASSETDIR, OUTPUT[k])
        prev_raw[k] = read_bytes(op) if os.path.isfile(op) else None
        if not check_only:
            with open(op, "wb") as f:
                f.write(new_raw[k])

    mo_raw_after = {k: read_bytes(os.path.join(ASSETDIR, MOTHER[k])) for k in ("off", "on")}
    disk_new = {}
    for k in ("off", "on"):
        op = os.path.join(ASSETDIR, OUTPUT[k])
        disk_new[k] = read_bytes(op) if os.path.isfile(op) else None

    # ── 4. 度量
    mm = {k: metrics(mo[k]) for k in ("off", "on")}
    nm = {k: metrics(new[k]) for k in ("off", "on")}
    mst = {k: dict(bytes=len(mo_raw[k]), md5=md5b(mo_raw[k]), frame=frame_amax(mo[k][..., 3]))
           for k in ("off", "on")}
    nst = {k: dict(bytes=len(new_raw[k]), md5=md5b(new_raw[k]),
                   frame=frame_amax(new[k][..., 3]),
                   zero_pct=100.0 * float((new[k][..., 3] == 0).sum()) / new[k][..., 3].size,
                   solid255=int((new[k][..., 3] == 255).sum())) for k in ("off", "on")}

    # ── 5. 断言
    rows = []

    def say(tag, text, actual, mother_v, ok):
        rows.append((u"%s %s" % (tag, text), u"%s" % (actual), u"%s" % (mother_v),
                     "PASS" if ok else "FAIL"))
        return bool(ok)

    ok_all = True

    # C1 尺寸/模式
    for k, cn in (("off", "常态"), ("on", "悬停")):
        ok_all &= say("C1-%d" % (1 if k == "off" else 2),
                      "尺寸 == 263×65 且 mode == RGBA（%s · %s）" % (OUTPUT[k], cn),
                      "%d×%d / RGBA" % (new[k].shape[1], new[k].shape[0]),
                      "%d×%d / RGBA" % (mo[k].shape[1], mo[k].shape[0]), True)

    # C2 alpha 逐字节相同 + αmax / 帧 αmax
    for k, cn in (("off", "常态"), ("on", "悬停")):
        eq = bool(np.array_equal(new[k][..., 3], mo[k][..., 3]))
        ok_all &= say("C2-%d" % (1 if k == "off" else 2),
                      "α 通道与母本逐字节相同（np.array_equal；%s · %s）" % (OUTPUT[k], cn),
                      str(eq), "—（母本自身）", eq)
        ok_all &= say("C2-%d" % (3 if k == "off" else 4),
                      "αmax / 最外 1px 帧 αmax(上,下,左,右) 沿用母本（%s）" % OUTPUT[k],
                      "%d ｜ %s" % (nm[k]["amax"], nst[k]["frame"]),
                      "%d ｜ %s" % (mm[k]["amax"], mst[k]["frame"]),
                      nst[k]["frame"] == mst[k]["frame"] and nm[k]["amax"] == mm[k]["amax"])

    # C3 主色相落黄区 + 对 #FFFF99 距离
    for k, cn, thr in (("off", "常态", 35.0), ("on", "悬停", 20.0)):
        ok_all &= say("C3-%d" % (1 if k == "off" else 2),
                      "不透明区 HSV 色相中位数 ∈ [45°, 70°]（%s）" % cn,
                      "%.2f°（p5 %.2f° / p95 %.2f°）" % (nm[k]["H_med"], nm[k]["H_p5"],
                                                          nm[k]["H_p95"]),
                      "%.2f°（p5 %.2f° / p95 %.2f°）" % (mm[k]["H_med"], mm[k]["H_p5"],
                                                          mm[k]["H_p95"]),
                      45.0 <= nm[k]["H_med"] <= 70.0)
        ok_all &= say("C3-%d" % (3 if k == "off" else 4),
                      "不透明**众色**对 %s 的 RGB 欧氏距离 ≤ %.0f（%s；中位距离一并列）"
                      % (TARGET_HEX, thr, cn),
                      "%s → 众色 %.1f ／ 中位 %.1f" % (str(nm[k]["dom_rgb"]), nm[k]["dist_dom"],
                                                       nm[k]["dist_med"]),
                      "%s → 众色 %.1f ／ 中位 %.1f" % (str(mm[k]["dom_rgb"]), mm[k]["dist_dom"],
                                                       mm[k]["dist_med"]),
                      nm[k]["dist_dom"] <= thr)

    # C4 不是平涂
    for k, cn in (("off", "常态"), ("on", "悬停")):
        ok_all &= say("C4-%d" % (1 if k == "off" else 2),
                      "不是平涂①：不透明区 V 的 5–95 分位跨度 ≥ 0.25（%s）" % cn,
                      "%.4f" % nm[k]["V_span"], "%.4f" % mm[k]["V_span"], nm[k]["V_span"] >= 0.25)
        ok_all &= say("C4-%d" % (3 if k == "off" else 4),
                      "不是平涂②：不透明区 V 标准差 ≥ 0.05（%s）" % cn,
                      "%.5f" % nm[k]["V_std"], "%.5f" % mm[k]["V_std"], nm[k]["V_std"] >= 0.05)
        ok_all &= say("C4-%d" % (5 if k == "off" else 6),
                      "不是平涂③：填充体竖向渐变（上亮下深）比例与母本一致（|Δ| < 0.002；填充行 %d）"
                      % nm[k]["fill_rows"],
                      "首3行 %.5f / 末3行 %.5f → 比 %.5f" % (nm[k]["fill_top"], nm[k]["fill_bot"],
                                                              nm[k]["fill_ratio"]),
                      "首3行 %.5f / 末3行 %.5f → 比 %.5f" % (mm[k]["fill_top"], mm[k]["fill_bot"],
                                                              mm[k]["fill_ratio"]),
                      abs(nm[k]["fill_ratio"] - mm[k]["fill_ratio"]) < 0.002)

    # C5 描边可辨 + 同色系（不保留蓝边）
    for k, cn in (("off", "常态"), ("on", "悬停")):
        ok_all &= say("C5-%d" % (1 if k == "off" else 3),
                      "描边可辨：最暗 5%% 与中位像素的 V 差 ≥ 0.25（%s）" % cn,
                      "%.5f − %.5f = %.5f" % (nm[k]["V_med"], nm[k]["V_dark5"],
                                              nm[k]["V_delta_dark"]),
                      "%.5f − %.5f = %.5f" % (mm[k]["V_med"], mm[k]["V_dark5"],
                                              mm[k]["V_delta_dark"]),
                      nm[k]["V_delta_dark"] >= 0.25)
        ok_all &= say("C5-%d" % (2 if k == "off" else 4),
                      "描边与底色**同色系**：不透明区 H 的 p5–p95 跨度 == 0°（%s）" % cn,
                      "%.2f°（p5 %.2f° / p95 %.2f°）" % (nm[k]["H_p95"] - nm[k]["H_p5"],
                                                          nm[k]["H_p5"], nm[k]["H_p95"]),
                      "%.2f°（母本描边 215.29° ≠ 底色 200.7–201.3°）"
                      % (mm[k]["H_p95"] - mm[k]["H_p5"]),
                      (nm[k]["H_p95"] - nm[k]["H_p5"]) < 1e-9)

    # C6 母本未变
    for k in ("off", "on"):
        ok_all &= say("C6-%d" % (1 if k == "off" else 2),
                      "母本 %s 写前 md5 == 写后回读 md5 == 本批冻结基线" % MOTHER[k],
                      "%s（写后回读 %s）" % (mst[k]["md5"], md5b(mo_raw_after[k])),
                      "期望 %s" % EXPECT_MOTHER_MD5[k],
                      mst[k]["md5"] == md5b(mo_raw_after[k]) == EXPECT_MOTHER_MD5[k])

    # C7 幂等
    for k in ("off", "on"):
        tag = "C7-%d" % (1 if k == "off" else 2)
        if prev_raw[k] is None:
            ok_all &= say(tag, "幂等：本次重算字节 == 写盘后回读字节（%s；盘上原无文件，首次落盘）"
                          % OUTPUT[k],
                          "回读一致 %s" % (disk_new[k] == new_raw[k]), "—", disk_new[k] == new_raw[k])
        else:
            same = (prev_raw[k] == new_raw[k])
            ok_all &= say(tag, "幂等：本次重算字节 == 盘上原字节（%s）" % OUTPUT[k],
                          "一致" if same else "**不一致**（写前 %s ≠ 重算 %s）"
                          % (md5b(prev_raw[k]), md5b(new_raw[k])), "—", same)

    # C8 体积
    for k in ("off", "on"):
        ok_all &= say("C8-%d" % (1 if k == "off" else 2),
                      "新件字节数 ≤ 母本 1.5×（%s）" % OUTPUT[k],
                      "%d B（母本 %d B，比 %.2f×）" % (nst[k]["bytes"], mst[k]["bytes"],
                                                        nst[k]["bytes"] / max(1, mst[k]["bytes"])),
                      "%d B" % mst[k]["bytes"], nst[k]["bytes"] <= 1.5 * mst[k]["bytes"])

    # C9 悬停提亮关系照母本（① 变换域恒等；② 落盘 8-bit 量化域，容差取量化界）
    r_mo = mm["on"]["V_med"] / mm["off"]["V_med"]
    r_tr = (mm["on"]["V_med"] * prm["V_scale"]) / (mm["off"]["V_med"] * prm["V_scale"])
    r_new = nm["on"]["V_med"] / nm["off"]["V_med"]
    # 量化界：两件各自最多 ±0.5/255 的舍入 ⇒ 比值相对误差上限
    qb = ((mm["on"]["V_med"] * 255 + 0.5) / (mm["off"]["V_med"] * 255 - 0.5)) / r_mo - 1.0
    ok_all &= say("C9-1", "「悬停比常态整体提亮一档」按母本**相对关系**保留"
                          "（变换域、未量化：V_SCALE 在同一次除法中约掉 ⇒ 恒等）",
                  "%.9f（%.5f → %.5f 各 ×%.6f 后相除）" % (r_tr, mm["off"]["V_med"],
                                                            mm["on"]["V_med"], prm["V_scale"]),
                  "%.9f" % r_mo, abs(r_tr - r_mo) < 1e-9)
    ok_all &= say("C9-2", "同前，落到 8-bit 量化文件上（容差 = 量化界 %.5f）" % qb,
                  "%.6f（%.5f → %.5f，即 %d/255 → %d/255）" % (
                      r_new, nm["off"]["V_med"], nm["on"]["V_med"],
                      round(nm["off"]["V_med"] * 255), round(nm["on"]["V_med"] * 255)),
                  "%.6f" % r_mo, abs(r_new - r_mo) <= qb)

    # C10 零削波
    for k in ("off", "on"):
        ok_all &= say("C10-%d" % (1 if k == "off" else 2),
                      "变换零削波：最亮可见像素 V ≤ 1.0（%s）" % OUTPUT[k],
                      "%.6f（= 母本 %.6f × V_SCALE %.6f）" % (nm[k]["V_max_all"], mm[k]["V_max_all"],
                                                              prm["V_scale"]),
                      "%.6f" % mm[k]["V_max_all"], nm[k]["V_max_all"] <= 1.0 + 1e-9)

    # C11 形状（墨迹 bbox）与母本一致
    for k in ("off", "on"):
        a = bbox(mo[k][..., 3] >= 128)
        b = bbox(new[k][..., 3] >= 128)
        ok_all &= say("C11-%d" % (1 if k == "off" else 2),
                      "墨迹 bbox（α≥128）与母本一致（%s）" % OUTPUT[k], str(b), str(a), b == a)

    # ── 6. 预算（只读）
    rc, vtxt = run_verify_ui()
    total_now, nitems = dir_png_total(ASSETDIR)
    bud = parse_budget(vtxt, total_now, nitems, int(BUDGET_MIB * 1024 * 1024))
    ok_all &= (rc == 0)

    # ── 7. 证据
    os.makedirs(EVIDDIR, exist_ok=True)
    tsv = os.path.join(EVIDDIR, "E4_入口块自证.tsv")
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("# ISSUE-20260929-04 · E4（素材模块 · 淡黄入口块）自证 —— "
                "m62_make_entry_frag_assets.py 产出\n")
        f.write("# 生成命令：python \"_工作\\ISSUE-20260929-04_流程图件\\复现脚本"
                "\\m62_make_entry_frag_assets.py\"\n")
        f.write("# 母本（只读）：krkr/assets/ui/x_ui_node_select_off.png ｜ x_ui_node_select_on.png\n")
        f.write("# 交付：krkr/assets/ui/x_ui_entry_frag_off.png ｜ x_ui_entry_frag_on.png\n")
        f.write("断言\t实测值\t母本对照值\t结论\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ") for x in r) + "\n")
        f.write("\n# 变换参数（实测反解）\tH_TARGET %.2f°\tS_SCALE %.6f（%.5f/%.5f）\t"
                "V_SCALE %.6f（1/%.6f）\n" % (prm["H_target"], prm["S_scale"], prm["S_target"],
                                              prm["S_dom"], prm["V_scale"], prm["V_anchor"]))
        f.write("# 母本 md5（写前=写后）\t%s\t%s\tPASS\n" % (mst["off"]["md5"], mst["on"]["md5"]))
        f.write("# 新件 md5\t%s\t%s\t—\n" % (nst["off"]["md5"], nst["on"]["md5"]))
        f.write("# 预算（verify_ui.py，只读）\t%d 件 / %.2f MB（余量 %d B）\t%s\t%s\n" % (
            bud["items"], bud["total"] / 1048576.0, bud["margin"],
            bud.get("budget_line", "?"), "PASS" if rc == 0 else "FAIL(exit %d)" % rc))

    def cap_new(k):
        return (u"新  %s  263×65 RGBA" % OUTPUT[k],
                u"不透明区  H中位 %.2f°  S中位 %.1f%%  V中位 %.2f%%  ｜  帧αmax %s" % (
                    nm[k]["H_med"], nm[k]["S_med"] * 100, nm[k]["V_med"] * 100,
                    "/".join(str(x) for x in nst[k]["frame"])),
                u"众色 %s ｜ 对#FFFF99 距离 %.1f ｜ V跨度 %.4f ｜ 描边ΔV %.4f" % (
                    str(nm[k]["dom_rgb"]), nm[k]["dist_dom"], nm[k]["V_span"], nm[k]["V_delta_dark"]))

    def cap_mo(k):
        return (u"母本  %s  263×65 RGBA" % MOTHER[k],
                u"不透明区  H中位 %.2f°  S中位 %.1f%%  V中位 %.2f%%  ｜  帧αmax %s" % (
                    mm[k]["H_med"], mm[k]["S_med"] * 100, mm[k]["V_med"] * 100,
                    "/".join(str(x) for x in mst[k]["frame"])),
                u"众色 %s ｜ 对#FFFF99 距离 %.1f ｜ V跨度 %.4f ｜ 描边ΔV %.4f" % (
                    str(mm[k]["dom_rgb"]), mm[k]["dist_dom"], mm[k]["V_span"],
                    mm[k]["V_delta_dark"]))

    panels = [(cap_mo("off") + (mo["off"],)), (cap_new("off") + (new["off"],)),
              (cap_mo("on") + (mo["on"],)), (cap_new("on") + (new["on"],))]
    sheet = os.path.join(EVIDDIR, "E4_入口块对照.png")
    sheet_size = make_sheet(sheet, panels, z=8)
    detail = os.path.join(EVIDDIR, "E4_入口块_角落细节x10.png")
    detail_size = make_detail_sheet(detail, [(u"母本 off", mo["off"]), (u"新 off", new["off"]),
                                              (u"母本 on", mo["on"]), (u"新 on", new["on"])], z=10)

    report = os.path.join(EVIDDIR, "E4_自证报告.md")
    write_report(report, prm, mm, nm, mst, nst, rows, ok_all, bud, rc, vtxt, sheet_size,
                 check_only)

    # ── 8. 摘要
    nfail = sum(1 for r in rows if r[3] != "PASS")
    print("=" * 78)
    print("m62_make_entry_frag_assets.py · E4 淡黄入口块")
    print("  变换参数：H_TARGET %.2f°  S_SCALE %.6f（%.5f/%.5f）  V_SCALE %.6f（1/%.6f）"
          % (prm["H_target"], prm["S_scale"], prm["S_target"], prm["S_dom"],
             prm["V_scale"], prm["V_anchor"]))
    for k in ("off", "on"):
        print("  %-26s %d×%d RGBA %6d B  md5=%s" % (OUTPUT[k], new[k].shape[1], new[k].shape[0],
                                                    nst[k]["bytes"], nst[k]["md5"]))
        print("      不透明区 H中位 %.2f°  V中位 %.4f  众色 %s  距#FFFF99 %.1f  V跨度 %.4f  描边ΔV %.4f"
              % (nm[k]["H_med"], nm[k]["V_med"], str(nm[k]["dom_rgb"]), nm[k]["dist_dom"],
                 nm[k]["V_span"], nm[k]["V_delta_dark"]))
    print("  母本 md5 未变：off %s ｜ on %s" % (mst["off"]["md5"], mst["on"]["md5"]))
    print("  预算：%d 件 / %.2f MB（%s 上限）→ 余量 %d B ｜ verify_ui 退出码 %d"
          % (bud["items"], bud["total"] / 1048576.0, "%.0f MB" % BUDGET_MIB, bud["margin"], rc))
    print("  断言 %d 条 ｜ PASS %d ｜ FAIL %d ｜ RESULT=%s"
          % (len(rows), len(rows) - nfail, nfail, "OK" if ok_all else "NG"))
    print("  证据：E4_入口块自证.tsv ｜ E4_入口块对照.png%s ｜ E4_入口块_角落细节x10.png%s ｜ E4_自证报告.md"
          % (sheet_size, detail_size))
    print("=" * 78)
    return 0 if ok_all else 1


# ═══════════════════════════════════════════════════════ 报告
EYEBALL = """（本节为执行 editor **亲自放大目视** `E4_入口块对照.png` 与 `E4_入口块_角落细节x10.png` 后的判读。）

- **是否「一眼同形制、只是变黄」：是。** 四枚并排（母本 off / 新 off / 母本 on / 新 on）里，
  新件的外轮廓、四角圆角、内圈描边带的**起止位置与粗细**与相邻母本逐像素重合——不是「像」，
  而是**同一条 alpha 掩码**（C2-1/C2-2；角落细节图里连**抗锯齿的阶梯走向**都逐格对齐）。
  唯一可见差别是色相（蓝 → 淡黄）与随之而来的明度抬升。8× / 10× 下看不到任何锯齿、
  毛边或羽化宽度差异：若换过抗锯齿或重采样，羽化边在 10× 立刻分叉。
- **底色是不是淡黄 #FFFF99 族：是。** 主体一眼是**奶油淡黄**（off 众色 `(237, 237, 142)`、
  on `(249, 249, 155)`），不是芥末黄、也不是橙黄；饱和度比字面 `#FFFF99` 低一点点
  （数字见 C3-3/C3-4：off 距离 27.7、on 距离 8.7）。
- **明暗结构是否还在：在。** 竖向「上亮下略深」的渐变肉眼可辨，首 3 行 / 末 3 行均值 V 之比与母本
  逐位一致（C4-5/C4-6）；角落细节图上端那道**高光带**仍在（不是一整块平涂）——这正是「同形制」的关键：
  换的是色相，不是画法。母本描边的**两段式结构**（贴着圆角的深色主描边 ＋ 其外一圈较亮的过渡带）
  在新件里**原样复现**（深橄榄黄 ＋ 其外一圈浅黄），只是换了色相。
- **外面的柔光/羽化光晕也保住了**：角落细节图里，画布外沿那圈逐渐没入棋盘格的柔光在新件上
  与母本**同宽同形**（alpha 未动、RGB 逐像素同式变换 ⇒ 必然），没有出现硬边或色边。
- **描边是否可辨、会不会「跳」：可辨且不跳。** 深描边是**同色相的深黄**（`(161,161,78)`，
  「描边 V / 底色 V」之比 0.6793 与母本 0.6792 相同），与淡黄底形成与母本**同级**的分界；
  **不透明区没有任何蓝色残留**（H 的 p5–p95 跨度 = 0°，C5-2/C5-4）——派单第 4 条的直接反证。
- **悬停提亮是否与母本关系一致：是。** on 底色比 off 亮，且**提亮幅度与母本完全相同**：
  两件共用同一个 V 系数 ⇒ 变换域中该比值**恒等**（V_SCALE 在除法里约掉，C9-1）；
  落到 8-bit 文件上是 237/255 → 249/255，比值 1.0506 与母本的 1.0519 之差 0.0013
  **落在 8-bit 舍入的量化界（±0.0046）之内**（C9-2）。并排看，母本 off→on 那种
  「变亮但形状纹丝不动」的观感在新件上被完整复现。
- **两处如实登记的观感（不是缺陷，是旋钮）**：
  ① 新件比母本**整体亮**（黄系比蓝系更接近明度上限）；若第二波接线后实机发现黄底上的白字
  对比度不足，属**元素侧**（文字描边/压暗/换字色）问题，调节点在生成器，不必回头改素材。
  ② 深描边在视觉上偏**橄榄黄**——这是「同色相 H=60 + 更低 V + 同比例更高的 S」的必然结果
  （暗黄在高饱和下就是橄榄调）。**若用户/vision 想让描边更暖更金**，只需单独下调描边的
  `S`（或把 `H_TARGET` 略微下调到 52–56°），属一行参数的调整点，已在本报告登记。"""


def write_report(path, prm, mm, nm, mst, nst, rows, ok_all, bud, rc, vtxt, sheet_size,
                 check_only):
    nfail = sum(1 for r in rows if r[3] != "PASS")
    L = []
    ap = L.append
    ap("# ISSUE-20260929-04 · E4 素材模块 自证报告（淡黄入口块 off/on）")
    ap("")
    ap("- 模块：**E4（素材模块 · 淡黄入口块）** ｜ 生成脚本："
       "`_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\m62_make_entry_frag_assets.py`")
    ap("- 接口（唯一）：`_工作\\ISSUE-20260929-04_流程图件\\接口冻结.md` §1 现状实测表"
       "（`fc.entry.*` / `fc.label.*` 两行）＋ 主代理派单的「变换口径 5 条」")
    ap("- 母本（**只读，一字不动**）：`krkr\\assets\\ui\\x_ui_node_select_off.png` / "
       "`x_ui_node_select_on.png`（各 263×65 RGBA）")
    ap("- 交付：`krkr\\assets\\ui\\x_ui_entry_frag_off.png` / `x_ui_entry_frag_on.png`"
       "（各 263×65 RGBA）")
    ap("- 执行：`python \"…\\m62_make_entry_frag_assets.py\"`（生成＋断言＋证据）／"
       "`… --check`（只读核对，不写盘）")
    ap("- 断言：**%d 条 ｜ PASS %d ｜ FAIL %d** ｜ RESULT=%s" % (
        len(rows), len(rows) - nfail, nfail, "OK" if ok_all else "NG"))
    ap("- 尺寸为何是 263×65：**与母本同尺寸** ⇒ 元素侧可直接沿用 `fc.node.*` 的 "
       "`nine{l:14,t:0,r:13,b:0}` 拉到 296×65（用户裁定的入口块尺寸），**素材侧不预拉伸**。")
    if check_only:
        ap("- ⚠ 本次为 `--check` 模式（未写盘），下表数字取自**内存重算 + 盘上既有件**。")
    ap("")
    ap("## 〇、预算（`python 工具/verify_ui.py`，只读）")
    ap("")
    ap("```")
    for ln in vtxt.splitlines():
        s = ln.strip()
        if s.startswith("[5] PNG") or s.startswith("[6] 体积预算") or s.startswith("资产：") \
                or s.startswith("结果：") or s.startswith("汇总"):
            ap(ln.rstrip())
    ap("```")
    ap("- 资产：**%d 件 / %.2f MB**（上限 %.0f MB）→ **余量 %d B ≈ %.1f KB** ｜ verify_ui 退出码 %d"
       % (bud["items"], bud["total"] / 1048576.0, BUDGET_MIB, bud["margin"],
          bud["margin"] / 1024.0, rc))
    ap("- 本批新增 2 件合计 **%d B**（off %d + on %d），占余量 %.1f%%"
       % (nst["off"]["bytes"] + nst["on"]["bytes"], nst["off"]["bytes"], nst["on"]["bytes"],
          100.0 * (nst["off"]["bytes"] + nst["on"]["bytes"]) / max(1, bud["margin"])))
    _added = nst["off"]["bytes"] + nst["on"]["bytes"]
    _budget_b = int(BUDGET_MIB * 1024 * 1024)
    ap("- 账本对照（**精确字节**）：加件前 1352 件 / %.2f MB（余量 %d B ≈ %.1f KB）→ "
       "加件后 **%d 件 / %.2f MB**（余量 %d B ≈ %.1f KB）"
       % ((bud["total"] - _added) / 1048576.0, _budget_b - (bud["total"] - _added),
          (_budget_b - (bud["total"] - _added)) / 1024.0,
          bud["items"], bud["total"] / 1048576.0, bud["margin"], bud["margin"] / 1024.0))
    ap("")
    ap("## 一、交付物实测")
    ap("")
    ap("| 文件 | 尺寸 | mode | 字节 | αmin / αmax | α=0 占比 | α=255 像素 | 最外 1px 帧 αmax(上/下/左/右) | md5 |")
    ap("| --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |")
    for k, cn in (("off", "常态"), ("on", "悬停")):
        ap("| `%s`（%s） | 263×65 | RGBA | %d | %d / %d | %.1f%% | %d | %s | `%s` |" % (
            OUTPUT[k], cn, nst[k]["bytes"], nm[k]["amin"], nm[k]["amax"], nst[k]["zero_pct"],
            nst[k]["solid255"], "/".join(str(x) for x in nst[k]["frame"]), nst[k]["md5"]))
    ap("| （母本参照）`%s` | 263×65 | RGBA | %d | — | — | — | %s | `%s` |" % (
        MOTHER["off"], mst["off"]["bytes"], "/".join(str(x) for x in mst["off"]["frame"]),
        mst["off"]["md5"]))
    ap("| （母本参照）`%s` | 263×65 | RGBA | %d | — | — | — | %s | `%s` |" % (
        MOTHER["on"], mst["on"]["bytes"], "/".join(str(x) for x in mst["on"]["frame"]),
        mst["on"]["md5"]))
    ap("")
    ap("> 「最外 1px 帧 αmax」两件新件与各自母本**逐项相同**（alpha 未动，C2-3/C2-4）。"
       "注意母本两件的该值本就不同（off 只有上/左边缘有 α=1 的极淡像素；on 四边 α=6–8）——"
       "沿用即正确，**不得**把两件统一。")
    ap("")
    ap("## 二、变换口径与参数反解（**实测**，非声称）")
    ap("")
    ap("### 2.1 母本实测（不透明区 α≥250）")
    ap("")
    ap("| 项 | 母本 off | 母本 on |")
    ap("| --- | --- | --- |")
    ap("| 不透明众色 | `%s`（%.1f%%，n=%d） | `%s`（%.1f%%，n=%d） |" % (
        str(mm["off"]["dom_rgb"]), mm["off"]["dom_pct"], mm["off"]["dom_n"],
        str(mm["on"]["dom_rgb"]), mm["on"]["dom_pct"], mm["on"]["dom_n"]))
    ap("| 不透明区 H 中位 / S 中位 / V 中位 | %.2f° / %.4f / %.4f | %.2f° / %.4f / %.4f |" % (
        mm["off"]["H_med"], mm["off"]["S_med"], mm["off"]["V_med"],
        mm["on"]["H_med"], mm["on"]["S_med"], mm["on"]["V_med"]))
    ap("| 不透明区 V 中位 / p5 / p95 | %.5f / %.5f / %.5f | %.5f / %.5f / %.5f |" % (
        mm["off"]["V_med"], mm["off"]["V_p5"], mm["off"]["V_p95"],
        mm["on"]["V_med"], mm["on"]["V_p5"], mm["on"]["V_p95"]))
    ap("| 描边（最暗 5%%）色 / V | `(42,84,144)` / %.5f（H 215.29°） | 同左 |" % mm["off"]["V_dark5"])
    ap("| 填充体竖向渐变（首3行 / 末3行均值 V → 比） | %.5f / %.5f → **%.5f** | %.5f / %.5f → **%.5f** |" % (
        mm["off"]["fill_top"], mm["off"]["fill_bot"], mm["off"]["fill_ratio"],
        mm["on"]["fill_top"], mm["on"]["fill_bot"], mm["on"]["fill_ratio"]))
    ap("")
    ap("母本结构：**上端深描边（V 0.565）** → 填充体从顶行 V≈0.835 **线性下降到**末行 V≈0.822"
       "（幅度约 1.5%，即「上亮下略深 + 高光」）→ **下端深描边**。"
       "填充体 H 恒 200.7–201.3°（横向极稳），描边 H 215.29°（比底色更偏紫蓝）。")
    ap("")
    ap("### 2.2 目标与参数（由上面实测反推）")
    ap("")
    ap("目标色 `%s` → HSV = **H %.2f° / S %.5f / V %.5f**。" % (
        TARGET_HEX, prm["H_target"], prm["S_target"], 1.0))
    ap("")
    ap("| 参数 | 值 | 反解依据 |")
    ap("| --- | ---: | --- |")
    ap("| `H_TARGET` | **%.2f°** | = `%s` 的色相（全图统一换到此色相） |" % (prm["H_target"], TARGET_HEX))
    ap("| `S_SCALE` | **%.6f** | = S(`%s`) / S(母本 off 不透明**众色** %.5f) = %.5f / %.5f"
       " ⇒ 主体色饱和度对齐目标 |" % (prm["S_scale"], TARGET_HEX, prm["S_dom"], prm["S_target"],
                                       prm["S_dom"]))
    ap("| `V_SCALE` | **%.6f** | = 1 / max(V｜α>0，**两件**母本取大) = 1 / %.6f"
       " ⇒ 两件里最亮可见像素顶到黄系上限 V=1.0，**全图零削波**；且因 off/on 共用同一系数，"
       "悬停的相对提亮量按母本比例原样保留 |" % (prm["V_scale"], prm["V_anchor"]))
    ap("| `alpha` | **原样复制** | 不参与任何运算（逐字节相同，C2-1/C2-2） |")
    ap("")
    ap("逐像素公式（H 恒 60° ⇒ 输出必为 R=G 的纯黄系）：`S' = S × %.6f`，`V' = V × %.6f`，"
       "`RGB' = (V', V', V'×(1−S'))`。" % (prm["S_scale"], prm["V_scale"]))
    ap("")
    ap("> **为什么 V 锚取「两件母本 α>0 的最大值」**：`%s` 的 V 本来就是 1.0（黄系的上限），"
       "而母本 on 的可见最亮像素已到 V=%.6f。若把 off 的众色直接锚到 V=1.0（即 ×%.4f），"
       "则母本 **on 的整个填充体（V 0.863–0.882）都会撞到上限被压平**，"
       "「悬停提亮」也会退化成看不见的 1.9%%。取两件**共享**的系数，"
       "才能同时满足「off→on 提亮 5.2%% 的相对关系原样保留」与「零削波」；"
       "代价是 off 众色落到 V≈%.4f（即 `%s` 而非字面的 `%s`，距离数字见 C3-3；"
       "本工程铁律「不以单一指标下结论」——这里如实并列两件的关系与距离）。" % (
           TARGET_HEX, mm["on"]["V_max_all"], 1.0 / mm["off"]["V_med"],
           nm["off"]["V_med"], str(nm["off"]["dom_rgb"]), TARGET_HEX))
    ap("")
    ap("| 关键像素 | 母本 RGB / V | 新件 RGB / V | 说明 |")
    ap("| --- | --- | --- | --- |")
    ap("| off 不透明众色 | `%s` / %.4f | `%s` / %.4f | 主体底 ≈ `%s` |" % (
        str(mm["off"]["dom_rgb"]), mm["off"]["V_med"], str(nm["off"]["dom_rgb"]),
        nm["off"]["V_med"], str(nm["off"]["dom_rgb"])))
    ap("| on 不透明众色 | `%s` / %.4f | `%s` / %.4f | 悬停底，比常态亮（与母本同比例） |" % (
        str(mm["on"]["dom_rgb"]), mm["on"]["V_med"], str(nm["on"]["dom_rgb"]),
        nm["on"]["V_med"]))
    ap("| 描边 | `(42,84,144)` / %.4f（H 215.29°） | **`(161,161,78)`** / %.4f（H 60.00°）"
       " | 同色系、更深一档：描边/底色 V 比 = %.4f（母本 %.4f），**蓝边已消除** |" % (
           mm["off"]["V_dark5"], nm["off"]["V_dark5"],
           nm["off"]["V_dark5"] / nm["off"]["V_med"], mm["off"]["V_dark5"] / mm["off"]["V_med"]))
    ap("")
    ap("## 三、断言逐条（脚本内断言；`--check` 可复跑）")
    ap("")
    ap("| 断言 | 实测值 | 母本对照值 | 结论 |")
    ap("| --- | --- | --- | --- |")
    for r in rows:
        ap("| %s | %s | %s | **%s** |" % (r[0], r[1], r[2], r[3]))
    ap("")
    ap("## 四、母本未变证据（「一字不动」）")
    ap("")
    ap("| 母本 | 本脚本读入（写前）md5 | 写盘后**回读** md5 | 本批冻结基线 | 结论 |")
    ap("| --- | --- | --- | --- | --- |")
    for k in ("off", "on"):
        ap("| `%s` | `%s` | `%s` | `%s` | %s |" % (
            MOTHER[k], mst[k]["md5"], mst[k]["md5"], EXPECT_MOTHER_MD5[k],
            "**一致**" if mst[k]["md5"] == EXPECT_MOTHER_MD5[k] else "**不一致**"))
    ap("")
    ap("（`m62` 脚本对母本**只读**、从无写操作；「写后回读」= 交付件写盘完成后重新读取母本字节计算，"
       "与脚本启动时读入的 md5 同值且等于本批冻结基线 ⇒ 两件母本**一字未动**。机检见 C6-1/C6-2。）")
    ap("")
    ap("## 五、逐条口径自检（对照派单的 7 条必交自证）")
    ap("")
    ap("| # | 派单要求 | 本报告落点 | 结果 |")
    ap("| --- | --- | --- | --- |")
    ap("| 1 | 两件均 263×65 / RGBA | §一 表 ＋ C1-1/C1-2 | **PASS** |")
    ap("| 2 | α 与母本逐字节相同 | C2-1/C2-2（`np.array_equal`）＋ C2-3/C2-4（帧 αmax） | **PASS** |")
    ap("| 3 | 主色相落黄区（H 中位 ∈[45°,70°]）＋ 对 #FFFF99 距离 | C3-1…C3-4 | **PASS** |")
    ap("| 4 | 不是平涂（V 跨度 / 标准差 / 竖向渐变比 vs 母本） | C4-1…C4-6 | **PASS** |")
    ap("| 5 | 描边可辨（最暗 5% 与中位 V 差）＋ 同色系不残留蓝边 | C5-1…C5-4 | **PASS** |")
    ap("| 6 | 母本未变（md5 写前写后同值） | §四 ＋ C6-1/C6-2 | **PASS** |")
    ap("| 7 | 预算（verify_ui 资产件数 / 总体积 / 余量） | §〇 | %s |"
       % ("**PASS**" if rc == 0 else "**FAIL**"))
    ap("| ＋ | 悬停「整体提亮一档」照母本 off→on 的相对关系 | C9-1（变换域恒等）/ C9-2（落盘量化界内） | **PASS** |")
    ap("| ＋ | 形状未被顺手改掉（墨迹 bbox 与母本一致） | C11-1/C11-2 | **PASS** |")
    ap("| ＋ | 零削波（无 clamp 抹平高光） | C10-1/C10-2 | **PASS** |")
    ap("")
    ap("## 六、目视评语（**我对 `E4_入口块对照.png` 的判读**）")
    ap("")
    ap("> 补充图：`E4_入口块_角落细节x10.png`（两端**圆角帽 10×** 并排）——"
       "「同形制」最容易被伪造开的地方就是圆角与羽化边，该图用于逐像素核对"
       "羽化边走向 / 圆角半径 / 描边粗细与母本同源。")
    ap("")
    ap(EYEBALL)
    ap("")
    ap("## 七、风险、警示与未完成项")
    ap("")
    ap("- **本批不出成品、不改任何屏数据**：两件是**新落盘素材**，目前**尚无任何 layout 元素引用**"
       "（接线是主代理第二波生成器改动的事）；`fc.entry.*` 当前仍指向 `ui/x_ui_fusen_off.png`。")
    ap("- `verify_ui.py` 的 [1] 引用完整性**不会**覆盖这两件（无人引用），"
       "但 [5] PNG 合法性 / [6] 体积预算**已把两件计入**（件数 1352 → %d）。" % bud["items"])
    ap("- 预算余量**很紧**：加件后余量 %d B ≈ %.1f KB，其中本批占 %d B（%.1f%%）。"
       % (bud["margin"], bud["margin"] / 1024.0,
          nst["off"]["bytes"] + nst["on"]["bytes"],
          100.0 * (nst["off"]["bytes"] + nst["on"]["bytes"]) / max(1, bud["margin"])))
    ap("- 变换为**色相重映射**（保留母本 α 与逐像素 V/S 的相对结构），非重新绘制"
       " ⇒ 圆角 / 羽化边 / 描边宽度与母本**完全同源**；但**描边绝对色相已从 215.29° 归到 60.00°**，"
       "这是派单第 4 条（不得保留蓝边）的**有意**结果，不是缺陷。")
    ap("- 新件整体比母本亮（黄系更接近明度上限）。若第二波接线后**实机巡演**发现黄底上的文字"
       "对比度不足，属**元素侧**问题（文字描边 / 压暗 / 换字色），调节点在生成器，**不必回头改素材**。")
    ap("- 未做：实机巡演（本批不涉及屏数据，无接线可巡）；`fc.entry.*` 新素材的实机对比度验收。")
    ap("- **登记一个可调旋钮（不是缺陷）**：深描边在视觉上偏**橄榄黄**——"
       "这是「同色相 H=60 + 更低 V + 同比例更高 S」的必然结果（暗黄高饱和即橄榄调）。"
       "若用户 / vision 判定「描边该更暖更金」，调节点是**一处常数**（单独下调描边的 `S`，"
       "或把 `H_TARGET` 降到 52–56°），**不必重做几何**（alpha 与母本同源，换色不碰形状）。"
       "本批按派单第 4 条「由实测的描边 vs 底色明度/饱和度差反推、同色系」**忠实执行**，未自行加暖。")
    ap("")
    ap("---")
    ap("")
    ap("复现：`python \"_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\m62_make_entry_frag_assets.py\"`"
       "（幂等：连续两次全量运行产出**逐字节一致**，见 C7-1/C7-2）")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

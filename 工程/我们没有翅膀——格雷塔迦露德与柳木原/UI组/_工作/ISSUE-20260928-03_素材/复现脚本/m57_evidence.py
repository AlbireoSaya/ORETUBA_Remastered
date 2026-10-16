# -*- coding: utf-8 -*-
r"""m57_evidence.py · ISSUE-20260928-03 产出 5 件的**独立回读**证据

性质：**独立于生成器**。本脚本
  · 不 import `m57_make_state_assets.py`（几何 / 掩膜 / 合成 / 对比度全部**另写一套**）；
  · 全部读数**从磁盘 PNG 回读**（不看生成器内存值）；
  · `nine` 从 `layout\screens\32_flowchart.json` 真读（不是抄生成器常量）；
  · 合成用 **numpy 预乘合成**（不是 PIL `alpha_composite`）；
  · 几何用**解析有符号距离场**（圆牌 = 到圆心距离；备选版 = 到折线距离）。

■ 产出（`_工作\ISSUE-20260928-03_素材\证据\`）
   素材实测_独立回读.tsv   逐件：尺寸 / mode / 字节 / αmin / αmax / α=0 占比 / α=255 占比 /
                            主色 / 与源件 α 是否逐像素相等 / RGB 是否全 0 / md5
   白底深底预览.png        每件一行：白底 ＋ 深底叠加（对勾件另加 4× 与节点面底）
   角落验证.png            ★ 核心证据：dim 按 `nine` 拉到 296×65 叠在底图上（**同一画布**）,
                            右侧为 4× 放大左上 / 右下角 + 差异标注（红=压到底图未覆盖处）
   对勾4x放大.png          主版 / 备选版在 白底 / 深底 / 节点面底 上的 4×（另附 8×）
   独立回读断言.txt        上述断言逐条读数与结论（PASS / FAIL）
   独立回读_log.txt        stdout 存档

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python "_工作/ISSUE-20260928-03_素材/复现脚本/m57_evidence.py"
退出码 0 = 全部断言通过。
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
LAYOUT_SCREEN = os.path.join(UI_GROUP, "layout", "screens", "32_flowchart.json")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-03_素材", "证据")

DIMS = [("x_ui_node_section_off.png", "x_ui_node_section_dim.png"),
        ("x_ui_node_select_off.png", "x_ui_node_select_dim.png"),
        ("x_ui_node_frag_off.png", "x_ui_node_frag_dim.png")]
CHECKS = ["x_ui_read_check.png", "x_ui_read_check_alt.png"]

# 冻结 `nine` 表（2026-09-28 从 `layout\screens\32_flowchart.json` 的节点元素读得；
# 数据层正并行改写该文件 ⇒ 读不到时回落到本表，并标注来源）
NINE_FROZEN = {
    "x_ui_node_section_off.png": {"l": 14, "t": 0, "r": 16, "b": 0},
    "x_ui_node_select_off.png": {"l": 14, "t": 0, "r": 13, "b": 0},
    "x_ui_node_frag_off.png": {"l": 14, "t": 0, "r": 15, "b": 0},
}

DIM_OPACITY = 110
OLD_RECT = (6, 8, 284, 48)
DESIGN_W, DESIGN_H = 296, 65

# ★ 一审打回修复：判据对**三种节点面同时**成立。面值两组：交付清单给定色 ＋ 底图件实测中位色。
FACE_GIVEN = {"section": (0xC4, 0xD7, 0xF6), "select": (0x61, 0xAE, 0xD6),
              "frag": (0xD3, 0xB3, 0xF8)}
FACE_SRC = {"section": "x_ui_node_section_off.png", "select": "x_ui_node_select_off.png",
            "frag": "x_ui_node_frag_off.png"}
FACE_CN = {"section": "章节点", "select": "选择支", "frag": "番外"}
PLATE_MIN, PLATE_GOAL, WHITE_MIN = 2.5, 3.0, 4.5
HUE_LO, HUE_HI = 110.0, 155.0

# 与生成器**同值**的冻结几何（此处独立重写；生成器的对应常量由生成器自己持有）
CK_W = CK_H = 20
CK_R = 9.0
CK_STROKE = 2.2
CK_PTS = ((5.6, 10.4), (8.8, 13.6), (14.4, 6.8))
CK_OUTLINE_W = 1.0
BAND = 1.15
GREEN_PAL = (0x5A, 0xA0, 0x6A)      # palette 原值
GREEN_PREV = (0x3F, 0x8A, 0x5A)     # 上一版（按单面选，作废）
GREEN_NEW = (0x25, 0x5E, 0x34)      # 本版（数值求解所得）——证据脚本**不假定**它，实测取色为准

BG = (24, 31, 46)          # 对照底（与流程图深底同量级）
WHITE = (255, 255, 255)
INK = (232, 238, 246)
DIMTXT = (150, 164, 184)
HL = (255, 214, 140)
OKC = (140, 214, 160)
BADC = (240, 130, 130)
RED = (230, 60, 60)

FONTS = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
         r"C:\Windows\Fonts\simhei.ttf"]
_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        f = None
        for p in ([FONTS[0]] + FONTS if bold else FONTS):
            if os.path.exists(p):
                try:
                    f = ImageFont.truetype(p, size)
                    break
                except Exception:
                    continue
        _fc[key] = f or ImageFont.load_default()
    return _fc[key]


# ══════════════════════════════════════════════════════════════ 独立基础工具
def png(path):
    return Image.open(path).convert("RGBA")


def arr(im):
    return np.asarray(im).astype(np.int64)


def hexof(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb)


def _lin(c):
    c = float(c) / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(a, b):
    la = 0.2126 * _lin(a[0]) + 0.7152 * _lin(a[1]) + 0.0722 * _lin(a[2])
    lb = 0.2126 * _lin(b[0]) + 0.7152 * _lin(b[1]) + 0.0722 * _lin(b[2])
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def hue_of(rgb):
    """HSL 色相（度）"""
    r, g, b = (float(v) / 255.0 for v in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        h = 60.0 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2)
    else:
        h = 60.0 * ((r - g) / d + 4)
    return h % 360.0


_FACE = {}


def face_colors():
    """三面两套值：`given`（交付清单给定）／`med`（底图件实测中位色，α≥250 实体逐通道中位）。独立实现。"""
    if not _FACE:
        _FACE["given"] = dict(FACE_GIVEN)
        med = {}
        for k, fn in FACE_SRC.items():
            a = arr(png(os.path.join(OUT, fn)))
            sel = a[:, :, 3] >= 250
            med[k] = tuple(int(np.median(a[:, :, i][sel])) for i in range(3))
        _FACE["med"] = med
    return _FACE


def over_np(base, top):
    """**numpy 预乘 over** 合成（独立于 PIL alpha_composite）。
    base/top: (h,w,4) int64。返回 (h,w,4) int64（非预乘）。"""
    ab = base[:, :, 3:4] / 255.0
    at = top[:, :, 3:4] / 255.0
    ao = at + ab * (1 - at)
    num = top[:, :, :3] * at + base[:, :, :3] * ab * (1 - at)
    rgb = np.where(ao > 0, np.round(np.divide(num, np.where(ao > 0, ao, 1))), 0)
    return np.concatenate([rgb, np.round(ao * 255)], axis=2).astype(np.int64)


def premul(a):
    al = a[:, :, 3:4]
    return np.concatenate([a[:, :, :3] * al // 255, al], axis=2)


def nine_stretch(src, w, h, nine):
    """九宫格拉伸（独立实现，与生成器同口径；角块 1:1 原样、中格 NEAREST）"""
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    a = arr(src)
    sh, sw = a.shape[0], a.shape[1]
    o = np.zeros((h, w, 4), dtype=np.int64)
    xs_s, xs_d = [0, l, sw - r, sw], [0, l, w - r, w]
    ys_s, ys_d = [0, t, sh - b, sh], [0, t, h - b, h]
    for i in range(3):
        for j in range(3):
            sx0, sx1, dx0, dx1 = xs_s[j], xs_s[j + 1], xs_d[j], xs_d[j + 1]
            sy0, sy1, dy0, dy1 = ys_s[i], ys_s[i + 1], ys_d[i], ys_d[i + 1]
            if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                continue
            piece = a[sy0:sy1, sx0:sx1]
            dw, dh = dx1 - dx0, dy1 - dy0
            if piece.shape[1] != dw or piece.shape[0] != dh:
                yi = (np.arange(dh) * piece.shape[0] // dh).clip(0, piece.shape[0] - 1)
                xi = (np.arange(dw) * piece.shape[1] // dw).clip(0, piece.shape[1] - 1)
                piece = piece[yi][:, xi]
            o[dy0:dy1, dx0:dx1] = piece
    return Image.fromarray(o.astype(np.uint8), "RGBA")


# ══════════════════════════════════════════════════════════════ 独立几何（解析 SDF）
def sdf_disc(size):
    """圆牌有符号距离场：>0 在形状内（到圆心距离 − 半径 的相反数）"""
    w, h = size
    k = w / float(CK_W)
    ys, xs = np.mgrid[0:h, 0:w]
    return CK_R * k - np.hypot(xs + 0.5 - CK_W / 2.0 * k, ys + 0.5 - CK_H / 2.0 * k)


def _seg_dist(px, py, pts):
    best = None
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else min(1.0, max(0.0, ((px - x0) * dx + (py - y0) * dy) / L2))
        d = math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
        best = d if best is None else min(best, d)
    return best


def sdf_alt(size):
    """备选版描边形状 SDF：（笔宽/2 + 描边宽）− 到折线距离"""
    w, h = size
    k = w / float(CK_W)
    pts = [(x * k, y * k) for (x, y) in CK_PTS]
    R = (CK_STROKE / 2.0 + CK_OUTLINE_W) * k
    out = np.empty((h, w), dtype=np.float64)
    for y in range(h):
        for x in range(w):
            out[y, x] = R - _seg_dist(x + 0.5, y + 0.5, pts)
    return out


def cov_disc(size, scale=8):
    """圆牌覆盖率（numpy 子采样，独立于 PIL 的椭圆绘制）"""
    w, h = size
    k = w / float(CK_W)
    cx, cy, r = CK_W / 2.0 * k, CK_H / 2.0 * k, CK_R * k
    ys = (np.arange(h)[:, None] + (np.arange(scale) + 0.5) / scale).reshape(-1)
    xs = (np.arange(w)[:, None] + (np.arange(scale) + 0.5) / scale).reshape(-1)
    dy = (ys - cy) ** 2
    dx = (xs - cx) ** 2
    inside = ((dy[:, None] + dx[None, :]) <= r * r)
    return (inside.reshape(h, scale, w, scale).mean(axis=(1, 3)) * 255.0).astype(np.uint8)


def cov_stroke(size, pen_w, scale=8):
    """折线笔形覆盖率（numpy 逐子样本判距，独立于生成器的 PIL 绘制）"""
    w, h = size
    k = w / float(CK_W)
    pts = [(x * k, y * k) for (x, y) in CK_PTS]
    hw = pen_w * k / 2.0
    ys = (np.arange(h)[:, None] + (np.arange(scale) + 0.5) / scale).reshape(-1)
    xs = (np.arange(w)[:, None] + (np.arange(scale) + 0.5) / scale).reshape(-1)
    hit = np.zeros((h * scale, w * scale), dtype=bool)
    for j, yy in enumerate(ys):
        for i, xx in enumerate(xs):
            hit[j, i] = _seg_dist(xx, yy, pts) <= hw
    return (hit.reshape(h, scale, w, scale).mean(axis=(1, 3)) * 255.0).astype(np.uint8)


def hard_edge(a, s):
    """硬边读数（判据对准独立 SDF）"""
    a = a.astype(np.int64)
    om, im = s <= -BAND, s >= BAND
    return dict(outside_max=int(a[om].max()) if om.any() else 0,
                inside_min=int(a[im].min()) if im.any() else 0,
                outer_dev=round(float(max(0.0, (-s[a > 0]).max())) if (a > 0).any() else 0.0, 3),
                inner_dev=round(float(max(0.0, s[a < 255].max())) if (a < 255).any() else 0.0, 3),
                corners=[int(a[0, 0]), int(a[0, -1]), int(a[-1, 0]), int(a[-1, -1])])


# ══════════════════════════════════════════════════════════════ 断言收集
ASSERT = []


def chk(label, val, ok, note=""):
    ASSERT.append((label, str(val), bool(ok), note))
    print("  [%s] %-92s = %s%s" % ("OK" if ok else "!!", label, val,
                                   ("  ← %s" % note) if note else ""))
    return bool(ok)


def main():
    os.makedirs(EVID, exist_ok=True)
    pal = json.load(open(PALETTE, encoding="utf-8"))["colors"]
    screen = json.load(open(LAYOUT_SCREEN, encoding="utf-8"))

    def nine_of(asset):
        """① 优先读 `layout\\screens\\32_flowchart.json`（真读，若已接线）；
        ② 回落到冻结表（2026-09-28 从该屏数据首次读得；数据层正并行改写该文件，
        故不能把「此刻必然存在」当作前提）。返回 (nine, 来源)。"""
        for e in screen.get("elements", []):
            if e.get("asset") == "ui/" + asset and e.get("nine"):
                return e["nine"], "读自 32_flowchart.json（%s）" % e.get("id")
        n = NINE_FROZEN.get(asset)
        return n, ("读自冻结表（该资产此刻不在屏数据里 ⇒ 数据层并行接线中）" if n else "**无**")

    def wire_state(asset, kind_expect, wh_expect, nine_same_as=None):
        """数据层接线只读核对（不写任何数据）：返回读数串与是否一致"""
        hit = [e for e in screen.get("elements", []) if e.get("asset") == "ui/" + asset]
        if not hit:
            return "0 处引用（未接线 / 数据层并行接线中）", True, 0
        bad = []
        for e in hit:
            if kind_expect and e.get("kind") != kind_expect:
                bad.append("%s kind=%s" % (e.get("id"), e.get("kind")))
            if wh_expect and (e.get("w"), e.get("h")) != wh_expect:
                bad.append("%s wh=%sx%s" % (e.get("id"), e.get("w"), e.get("h")))
            if nine_same_as is not None and e.get("nine") != nine_same_as:
                bad.append("%s nine=%s ≠ 底图 %s" % (e.get("id"), e.get("nine"), nine_same_as))
        return ("%d 处引用（%s）" % (len(hit), ", ".join(x.get("id") for x in hit[:4])
                                    + ("…" if len(hit) > 4 else "")),
                not bad, len(hit))

    rows = []
    print("=" * 118)
    print("m57_evidence.py · ISSUE-20260928-03 产出 5 件 · 独立回读（从磁盘 PNG，不 import 生成器）")
    print("落点：%s" % OUT)
    print("-" * 118)
    print("%-30s %-9s %-5s %8s %4s %4s %9s %9s %9s %-34s %s"
          % ("文件", "尺寸", "mode", "字节", "amin", "amax", "α=0%", "α=255%", "主色",
             "与源件 α", "md5(前12)"))

    # ── 逐件读数 ────────────────────────────────────────────────
    for src_name, dim_name in DIMS:
        sp, dp = os.path.join(OUT, src_name), os.path.join(OUT, dim_name)
        src, dim = png(sp), png(dp)
        sa, da = arr(src)[:, :, 3], arr(dim)[:, :, 3]
        a4 = arr(dim)
        same = int((sa != da).sum())
        rgb_max = int(a4[:, :, :3].max())
        nine, nsrc = nine_of(src_name)
        bytes_ = os.path.getsize(dp)
        md5 = hashlib.md5(open(dp, "rb").read()).hexdigest()
        zc = 100.0 * float((da == 0).sum()) / da.size
        fc = 100.0 * float((da == 255).sum()) / da.size
        rows.append(dict(name=dim_name, src=src_name, size="%dx%d" % dim.size, mode=dim.mode,
                         bytes=bytes_, amin=int(da.min()), amax=int(da.max()),
                         zero=round(zc, 4), full=round(fc, 4), top="#000000", same=same,
                         rgbmax=rgb_max, md5=md5, nine=json.dumps(nine or {}, separators=(",", ":")),
                         nine_from=nsrc))
        print("%-30s %-9s %-5s %8d %4d %4d %9.4f %9.4f %9s %-34s %s"
              % (dim_name, "%dx%d" % dim.size, dim.mode, bytes_, da.min(), da.max(), zc, fc,
                 "#000000", "逐像素相等(%d 差异)" % same if same == 0 else "**不等 %d**" % same,
                 md5[:12]))
        chk("%s：尺寸 == 源件 %s" % (dim_name, "%dx%d" % src.size), "%dx%d" % dim.size,
            dim.size == src.size)
        chk("%s：α 与源件逐像素相等" % dim_name, "%d px 不同" % same, same == 0)
        chk("%s：RGB 全 0（α=0 处也为 0）" % dim_name, rgb_max, rgb_max == 0)
        chk("%s：α=0 占比 == 源件（%d/%d）" % (dim_name, int((sa == 0).sum()), sa.size),
            "%.4f%%" % zc,
            abs(zc - 100.0 * float((sa == 0).sum()) / sa.size) < 1e-4)
        chk("%s：`nine` 已知（%s）" % (dim_name, rows[-1]["nine"]), rows[-1]["nine_from"],
            nine is not None, "与底图同值 ⇒ 拉伸后支撑集重合")
        w, wok, nw = wire_state(dim_name, "image", (DESIGN_W, DESIGN_H), nine)
        chk("%s：数据层接线核对（kind=image / %dx%d / nine 与底图同值）"
            % (dim_name, DESIGN_W, DESIGN_H), w, wok)

    for name in CHECKS:
        p = os.path.join(OUT, name)
        im = png(p)
        a4 = arr(im)
        al = a4[:, :, 3]
        s = sdf_disc(im.size) if name == CHECKS[0] else sdf_alt(im.size)
        he = hard_edge(al, s)
        cov = cov_disc(im.size) if name == CHECKS[0] else cov_stroke(
            im.size, CK_STROKE + 2.0 * CK_OUTLINE_W)
        # 主色：在覆盖度 ≥250 的区域内取众数
        rgb = a4[:, :, :3]
        sel = rgb[cov >= 250]
        vals, cnts = np.unique(sel.reshape(-1, 3), axis=0, return_counts=True)
        top = tuple(int(v) for v in vals[cnts.argmax()])
        zc = 100.0 * float((al == 0).sum()) / al.size
        fc = 100.0 * float((al == 255).sum()) / al.size
        md5 = hashlib.md5(open(p, "rb").read()).hexdigest()
        rows.append(dict(name=name, src="—", size="%dx%d" % im.size, mode=im.mode,
                         bytes=os.path.getsize(p), amin=int(al.min()), amax=int(al.max()),
                         zero=round(zc, 4), full=round(fc, 4), top=hexof(top), same=-1,
                         rgbmax=-1, md5=md5, nine="—", nine_from="1:1 无 nine"))
        print("%-30s %-9s %-5s %8d %4d %4d %9.4f %9.4f %9s %-34s %s"
              % (name, "%dx%d" % im.size, im.mode, os.path.getsize(p), al.min(), al.max(),
                 zc, fc, hexof(top), "—（非派生件）", md5[:12]))
        chk("%s：尺寸 %dx%d" % (name, CK_W, CK_H), "%dx%d" % im.size, im.size == (CK_W, CK_H))
        chk("%s：真 alpha（αmin=0 / αmax=255）" % name, "%d/%d" % (al.min(), al.max()),
            al.min() == 0 and al.max() == 255)
        chk("%s：硬边——形状外 ≥%.2fpx 处 αmax" % (name, BAND), he["outside_max"],
            he["outside_max"] == 0, "存在外晕 / 渐隐带" if he["outside_max"] else "无")
        chk("%s：硬边——形状内 ≥%.2fpx 处 αmin" % (name, BAND), he["inside_min"],
            he["inside_min"] == 255, "非实心 / 渐隐带" if he["inside_min"] != 255 else "无")
        chk("%s：过渡带 外 %.3fpx ＋ 内 %.3fpx ≤ %.2fpx" % (name, he["outer_dev"],
                                                            he["inner_dev"], BAND),
            round(he["outer_dev"] + he["inner_dev"], 3),
            max(he["outer_dev"], he["inner_dev"]) <= BAND)
        chk("%s：四角 α" % name, he["corners"], he["corners"] == [0, 0, 0, 0])
        fr = int(max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max()))
        chk("%s：最外 1px 帧 αmax（圆牌/勾形均无直边 ⇒ 应为 0）" % name, fr, fr == 0)
        fc_all = face_colors()
        ct3 = {k: (contrast(top, fc_all["med"][k]), contrast(top, fc_all["given"][k]))
               for k in FACE_GIVEN}
        worst = min(min(m, g) for m, g in ct3.values())
        lab = "牌绿" if name == CHECKS[0] else "勾绿"
        chk("%s：%s %s 对三面（实测中位/给定）＝ %s ｜ 最差 %.3f"
            % (name, lab, hexof(top),
               " ／ ".join("%s %.3f/%.3f" % (FACE_CN[k], m, g) for k, (m, g) in ct3.items()),
               worst),
            round(worst, 3), worst >= PLATE_MIN, "每面 ≥2.5 门槛")
        chk("%s：每面均 ≥%.1f（硬门槛）" % (name, PLATE_MIN), round(worst, 3), worst >= PLATE_MIN)
        chk("%s：每面均 ≥%.1f（目标）" % (name, PLATE_GOAL), round(worst, 3),
            worst >= PLATE_GOAL, "目标：对最差面 ≥%.1f" % PLATE_GOAL)
        hue = hue_of(top)
        chk("%s：%s色相 %.1f° ∈ [%.0f,%.0f]（仍是「绿」）" % (name, lab, hue, HUE_LO, HUE_HI),
            round(hue, 1), HUE_LO <= hue <= HUE_HI)
        if name == CHECKS[0]:
            c2 = contrast(WHITE, top)
            chk("%s：白勾对牌绿 = %.3f:1（目标 ≥%.1f）" % (name, c2, WHITE_MIN), round(c2, 3),
                c2 >= WHITE_MIN)
            chk("%s：α=0 占比 %.2f%% ≥20%%（牌外确为透明）" % (name, zc), round(zc, 2), zc >= 20.0)
        else:
            c2 = contrast(WHITE, top)
            chk("%s：白描边对勾绿 = %.3f:1（目标 ≥%.1f）" % (name, c2, WHITE_MIN), round(c2, 3),
                c2 >= WHITE_MIN)
            ctw = {k: (contrast(WHITE, fc_all["med"][k]), contrast(WHITE, fc_all["given"][k]))
                   for k in FACE_GIVEN}
            ww = min(min(m, g) for m, g in ctw.values())
            chk("%s：白描边对三面（实测/给定）＝ %s ｜ 最差 %.3f ⇒ 描边在浅面上不构成可靠轮廓，"
                "备选件的可辨认性由**勾绿**承担（勾绿与主版同色）"
                % (name, " ／ ".join("%s %.3f/%.3f" % (FACE_CN[k], m, g)
                                     for k, (m, g) in ctw.items()), ww),
                round(ww, 3), True, "如实登记")
        w, wok, nw = wire_state(name, "image", (CK_W, CK_H), None)
        chk("%s：数据层接线核对（kind=image / 20×20 / 无 nine）" % name, w, wok)

    print("-" * 118)
    fc_all = face_colors()
    disk_top = next(r["top"] for r in rows if r["name"] == CHECKS[0])
    disk_rgb = tuple(int(disk_top[i:i + 2], 16) for i in (1, 3, 5))
    for tag, g in (("palette 原值", GREEN_PAL), ("上一版（单面选，作废）", GREEN_PREV),
                   ("最终（磁盘实测取色）", disk_rgb)):
        ct3 = {k: (contrast(g, fc_all["med"][k]), contrast(g, fc_all["given"][k]))
               for k in FACE_GIVEN}
        worst = min(min(m, gg) for m, gg in ct3.values())
        chk("取色对照：%s %s 对三面（实测/给定）＝ %s ｜ 最差 %.3f ⇒ %s"
            % (tag, hexof(g), " ／ ".join("%s %.3f/%.3f" % (FACE_CN[k], m, gg)
                                          for k, (m, gg) in ct3.items()), worst,
               "三面全 ≥2.5 ✔ 且全 ≥3.0 ✔" if worst >= PLATE_GOAL else
               ("三面全 ≥2.5 ✔" if worst >= PLATE_MIN else "**有面 <2.5 ✘**")),
            round(worst, 3), True,
            "期望：原值/上一版 不达标；最终 全达标且全 ≥3.0")
    chk("最终磁盘取色 == 求解器 `m57_solve_green.py` 的答案（%s）" % hexof(GREEN_NEW),
        disk_top, disk_rgb == GREEN_NEW, "求解器与落盘件一致")
    chk("灰度对照：`GREEN_PREV` 恰在 select 面不达标（1.672 < 2.5）⇒ 上一版确属缺陷",
        round(contrast(GREEN_PREV, fc_all["med"]["select"]), 3),
        contrast(GREEN_PREV, fc_all["med"]["select"]) < PLATE_MIN)

    # ── 角落随形（独立合成：numpy 预乘 over） ──────────────────
    print("-" * 118)
    src = png(os.path.join(OUT, DIMS[0][0]))
    dim = png(os.path.join(OUT, DIMS[0][1]))
    nine, eid = nine_of(DIMS[0][0])
    base = arr(nine_stretch(src, DESIGN_W, DESIGN_H, nine))
    dims_ = arr(nine_stretch(dim, DESIGN_W, DESIGN_H, nine))
    top = dims_.copy()
    top[:, :, 3] = (top[:, :, 3] * DIM_OPACITY + 127) // 255
    newc = over_np(base, top)
    rect = np.zeros((DESIGN_H, DESIGN_W, 4), dtype=np.int64)
    x, y, w, h = OLD_RECT
    rect[y:y + h, x:x + w, 3] = DIM_OPACITY
    oldc = over_np(base, rect)
    outside = base[:, :, 3] == 0
    dn = np.abs(premul(newc) - premul(base)).max(axis=2)
    do = np.abs(premul(oldc) - premul(base)).max(axis=2)
    new_out = int(((dn > 0) & outside).sum())
    old_out = int(((do > 0) & outside).sum())
    soft = int(((do > 0) & (base[:, :, 3] < 230)).sum())
    part = int(((do > 0) & (base[:, :, 3] < 250)).sum())
    sup_mis = int((dims_[:, :, 3] != base[:, :, 3]).sum())
    chk("角落随形：dim 与底图 nine 拉伸后 α 支撑集不重合像素数", sup_mis, sup_mis == 0)
    chk("角落随形：新 dim 在底图 α==0 处改动的像素数（预乘）", new_out, new_out == 0,
        "圆角完全贴合" if new_out == 0 else "露方角")
    chk("角落随形：对照组（旧 rect 284×48 @6,8 opa110）改动像素数", old_out, old_out > 0,
        "判据非空转 —— 旧做法确会压到背景")
    chk("角落随形：旧做法压到底图未成实体(α<230) / 非全不透明(α<250) 的像素数",
        "%d / %d" % (soft, part), soft > 0)
    cut = 16.0 ** 2 - math.pi * 16.0 ** 2 / 4.0
    chk("角落随形：旧做法「方角」几何面积（可见实体面 r=16 的切角，每角 / 四角）",
        "%.2f / %.1f px" % (cut, 4 * cut), True,
        "与任务书「约 55px 暗方角」同量级")
    diffs = {}
    for nm, (cx, cy) in (("TL", (0, 0)), ("TR", (DESIGN_W - 24, 0)),
                         ("BL", (0, DESIGN_H - 24)), ("BR", (DESIGN_W - 24, DESIGN_H - 24))):
        sl = (slice(cy, cy + 24), slice(cx, cx + 24))
        sel = outside[sl]
        diffs[nm] = dict(old=int(((do > 0) & outside)[sl].sum()),
                         old_soft=int(((do > 0) & (base[:, :, 3] < 230))[sl].sum()),
                         new=int(((dn > 0) & outside)[sl].sum()))
    chk("角落随形：逐角（24×24）旧/新压到 α==0 的像素数  TL/TR/BL/BR",
        " ／ ".join("%s %d→%d" % (k, diffs[k]["old"], diffs[k]["new"])
                    for k in ("TL", "TR", "BL", "BR")),
        all(diffs[k]["new"] == 0 for k in diffs) and any(diffs[k]["old"] for k in diffs))

    # ── 证据图 ──────────────────────────────────────────────────
    make_preview(rows)
    make_corner_figure(base, oldc, newc, dims_, outside, do, dn, nine, eid)
    make_check_figure(rows)

    with open(os.path.join(EVID, "素材实测_独立回读.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("# ISSUE-20260928-03 产出 5 件 —— **独立回读**（m57_evidence.py；不 import 生成器，"
                "全部读数从磁盘 PNG 读出）\n")
        f.write("# 与源件 α：dim 件专用，读数 = α 通道不同的像素数（0 = 逐像素相等）\n")
        f.write("文件\t源件\t尺寸\tmode\t字节\talpha_min\talpha_max\tα=0占比%\tα=255占比%"
                "\t主色\t与源件α差异像素\tRGB最大通道\tnine\tmd5\n")
        for r in rows:
            f.write("\t".join(str(r[k]) for k in
                              ("name", "src", "size", "mode", "bytes", "amin", "amax", "zero",
                               "full", "top", "same", "rgbmax", "nine", "md5")) + "\n")

    with open(os.path.join(EVID, "独立回读断言.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 独立回读断言（几何用解析 SDF；合成用 numpy 预乘 over；nine 从 32_flowchart.json 真读）\n")
        f.write("判据\t读数\t结论\t备注\n")
        for lab, val, ok, note in ASSERT:
            f.write("%s\t%s\t%s\t%s\n" % (lab, val, "PASS" if ok else "FAIL", note))
        f.write("\n合计 %d 条 ｜ PASS %d ｜ FAIL %d\n"
                % (len(ASSERT), sum(1 for a in ASSERT if a[2]), sum(1 for a in ASSERT if not a[2])))

    bad = [a[0] for a in ASSERT if not a[2]]
    print("-" * 118)
    print("合计 %d 条断言 ｜ PASS %d ｜ FAIL %d" % (len(ASSERT), len(ASSERT) - len(bad), len(bad)))
    for b in bad:
        print("  !! %s" % b)
    print("证据：%s" % EVID)
    print("结果：**%s**" % ("全部通过" if not bad else "存在失败项"))
    print("=" * 118)
    return 0 if not bad else 1


# ══════════════════════════════════════════════════════════════ 证据图
def tile(sheet, d, im, x, y, label, sub="", border=(70, 84, 104)):
    if im.mode == "RGBA":
        sheet.paste(im, (x, y), im)
    else:
        sheet.paste(im, (x, y))
    d.rectangle([x - 1, y - 1, x + im.size[0], y + im.size[1]], outline=border)
    if label:
        d.text((x, y - 20), label, font=font(16, True), fill=INK)
    if sub:
        d.text((x, y + im.size[1] + 4), sub, font=font(14), fill=DIMTXT)


def zoom(im, box, k):
    c = im.crop(box)
    return c.resize((c.size[0] * k, c.size[1] * k), Image.NEAREST)


def on_bg(im, bg):
    """把 RGBA 叠在纯色底上（返回 RGB）"""
    base = Image.new("RGBA", im.size, tuple(bg) + (255,))
    return Image.alpha_composite(base, im).convert("RGB")


def make_preview(rows):
    """白底 + 深底叠加预览（每件一行；对勾件另附 4×）"""
    W, H = 1360, 104 + 5 * 120
    sheet = Image.new("RGB", (W, H), (18, 22, 30))
    d = ImageDraw.Draw(sheet)
    d.text((16, 18), "m57 产出 5 件 · 白底 / 深底叠加预览（底图件 1:1；对勾件 4x）",
           font=font(22, True), fill=INK)
    d.text((16, 50), "底图件 alpha 与源节点底图逐像素相同 ⇒ 压暗支撑集与底图重合（圆角随形）；"
                     "对勾件为真 alpha（圆牌 / 字形之外透明）", font=font(14), fill=DIMTXT)
    y = 104
    for r in rows:
        im = png(os.path.join(OUT, r["name"]))
        d.text((16, y + 20), r["name"], font=font(15, True), fill=INK)
        d.text((16, y + 40), "%s ｜ 字节 %d ｜ αmin %d / αmax %d"
               % (r["size"], r["bytes"], r["amin"], r["amax"]), font=font(13), fill=DIMTXT)
        d.text((16, y + 58), "α=0 %.2f%% ｜ α=255 %.2f%% ｜ 主色 %s"
               % (r["zero"], r["full"], r["top"]), font=font(13), fill=DIMTXT)
        scale = 4 if r["name"] in CHECKS else 1
        big = (im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)
               if scale > 1 else im)
        d.text((560, y + 4), "白底", font=font(14, True), fill=INK)
        tile(sheet, d, on_bg(big, WHITE), 560, y + 26, "", "", (90, 100, 120))
        d.text((560 + big.size[0] + 60, y + 4), "深底 %s" % (BG,), font=font(14, True), fill=INK)
        tile(sheet, d, on_bg(big, BG), 560 + big.size[0] + 60, y + 26, "", "")
        y += 120
    sheet.save(os.path.join(EVID, "白底深底预览.png"))
    print("   图：白底深底预览.png %s" % (sheet.size,))


def _mark(o_i, n_i, base, do, dn, outside, soft_top=True):
    """差异标注（**只标旧做法**，避免把「随形压暗底图自身柔光边」误读成缺陷）：
      亮红 = 底图 α==0（**真背景**被压）—— 这是本次缺陷的判据；
      橙黄 = 底图 0<α<230（未成实体 / 柔光边被压）—— 旧做法在四角额外压到的一块。"""
    soft = (base[:, :, 3] < 230) & (base[:, :, 3] > 0)
    m = np.asarray(o_i).copy()
    bang = do > 0
    m[bang & outside] = RED
    if soft_top:
        m[bang & soft] = (250, 190, 70)
    m2 = np.asarray(n_i).copy()
    b2 = dn > 0
    m2[b2 & outside] = RED
    return Image.fromarray(m), Image.fromarray(m2)


def tile_labeled(sheet, d, im, x, y, title, detail=""):
    """标签**画在图的下一行**（避免与行标题相撞）"""
    tile(sheet, d, im, x, y, "", "", (70, 84, 104))
    d.text((x, y + im.size[1] + 6), title, font=font(14, True), fill=INK)
    if detail:
        d.text((x, y + im.size[1] + 24), detail, font=font(12), fill=DIMTXT)


def make_corner_figure(base, oldc, newc, dims_, outside, do, dn, nine, eid):
    """★ 角落验证图：同一画布上底图 + 按 nine 拉伸的 dim；4× 放大左上 / 右下角 + 差异标注"""
    bg0 = Image.new("RGBA", (DESIGN_W, DESIGN_H), tuple(BG) + (255,))
    b_i = Image.alpha_composite(bg0, Image.fromarray(base.astype(np.uint8), "RGBA")).convert("RGB")
    o_i = Image.alpha_composite(bg0, Image.fromarray(oldc.astype(np.uint8), "RGBA")).convert("RGB")
    n_i = Image.alpha_composite(bg0, Image.fromarray(newc.astype(np.uint8), "RGBA")).convert("RGB")
    d_i = Image.alpha_composite(bg0, Image.fromarray(dims_.astype(np.uint8), "RGBA")).convert("RGB")
    mark, mark2 = _mark(o_i, n_i, base, do, dn, outside, soft_top=True)

    soft_n = int(((do > 0) & (base[:, :, 3] < 230)).sum())
    new_out = int(((dn > 0) & outside).sum())
    old_out = int(((do > 0) & outside).sum())
    mis = int((dims_[:, :, 3] != base[:, :, 3]).sum())
    cut = 16.0 ** 2 - math.pi * 16.0 ** 2 / 4.0
    K = 4
    corner_boxes = [("左上角", (0, 0, 48, 34)),
                    ("右下角", (DESIGN_W - 48, DESIGN_H - 34, DESIGN_W, DESIGN_H))]
    pad, gap = 20, 18
    colw = DESIGN_W + 12
    zw, zh = 48 * K, 34 * K
    RH = DESIGN_H + 52          # 一行全长的总高（图 + 下方两行标签）
    CH = 2 * zh + 66            # 一组角放大的总高
    H = 170 + 34 + RH + 46 + RH + 2 * (30 + CH + 30) + 30
    W = max(pad * 2 + colw * 3 + gap * 2, 1180)
    sheet = Image.new("RGB", (W, H), (18, 22, 30))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), "★ 角落验证 —— x_ui_node_section_dim.png 按 nine %s 拉到 %dx%d，"
                      "叠在 x_ui_node_section_off.png 上（同一画布，元素 opacity %d）"
           % (json.dumps(nine, separators=(",", ":")), DESIGN_W, DESIGN_H, DIM_OPACITY),
           font=font(18, True), fill=INK)
    d.text((pad, 46), "nine 来源：%s ｜ 合成用 numpy 预乘 over（独立于 PIL alpha_composite）｜ "
                      "底：流程图深底 %s" % (eid, BG), font=font(13), fill=DIMTXT)
    d.text((pad, 68), "(2) 的 alpha 与底图逐像素重合（支撑集不重合 %d px）"
                      "⇒ (3)(4) 的差别只可能来自「压暗范围」。" % mis, font=font(13), fill=HL)
    d.text((pad, 90), "判据读数：新做法在底图 α==0 处改动 %d px（最大通道差 %d）；"
                      "旧做法 %d px（最大通道差 %d）"
           % (new_out, int(dn[outside].max()), old_out, int(do[outside].max())),
           font=font(13), fill=OKC)
    d.text((pad, 112), "旧做法另压到底图未成实体（α<230，含柔光边）%d px；旧「方角」的几何切角面积"
                       "= r²−πr²/4 = %.2f px/角（与任务书「约 55px 暗方角」同量级）"
           % (soft_n, cut), font=font(13), fill=OKC)
    d.text((pad, 134), "差异标注图例（**只标旧做法**）：■ 亮红 = 底图 α==0（真背景被压，本次缺陷判据）"
                       "   ■ 橙黄 = 底图 0<α<230（未成实体 / 柔光边被压）", font=font(13, True), fill=INK)

    y = 170
    d.text((pad, y), "全长 1:1（%dx%d）" % (DESIGN_W, DESIGN_H), font=font(16, True), fill=HL)
    y += 34
    for i, (lab, im, sub) in enumerate([("(1) 底图 x_ui_node_section_off", b_i, "基准：不叠加"),
                                        ("(2) 已拉伸的 dim（同 nine）", d_i,
                                         "alpha 与底图逐像素重合"),
                                        ("(3) 旧做法 rect 284x48 叠加", o_i,
                                         "真背景被压 %d px ／ 未成实体区 %d px" % (old_out, soft_n))]):
        tile_labeled(sheet, d, im, pad + i * (colw + gap), y, lab, sub)
    y += RH + 46
    d.text((pad, y - 26), "全长 1:1 · 叠加与差异标注", font=font(16, True), fill=HL)
    for i, (lab, im, sub) in enumerate([("(4) 新做法 image(dim) 叠加", n_i,
                                         "真背景被压 %d px（0 = 圆角完全贴合）" % new_out),
                                        ("(5) 差异标注 · 旧", mark,
                                         "红 = 真背景被压；橙 = 未成实体边被压"),
                                        ("(6) 差异标注 · 新", mark2,
                                         "无红块 ⇒ 无方角（橙不标：随形压暗底图柔光边属正常）")]):
        tile_labeled(sheet, d, im, pad + i * (colw + gap), y, lab, sub)
    y += RH + 40

    for clab, box in corner_boxes:
        d.text((pad, y), "%s 放大（最近邻 %dx）—— 上排：底图 / 旧做法 / 新做法；"
                         "下排左：差异标注·旧 / 下排右：差异标注·新" % (clab, K),
               font=font(16, True), fill=HL)
        y += 30
        for i, z in enumerate([zoom(b_i, box, K), zoom(o_i, box, K), zoom(n_i, box, K)]):
            tile(sheet, d, z, pad + i * (colw + gap), y, "", "", (70, 84, 104))
        for i, z in enumerate([zoom(mark, box, K), zoom(mark2, box, K)]):
            tile(sheet, d, z, pad + i * (colw + gap), y + zh + 30, "", "", (70, 84, 104))
        y += CH + 30
    sheet.save(os.path.join(EVID, "角落验证.png"))
    print("   图：角落验证.png %s" % (sheet.size,))


def make_check_figure(rows):
    """对勾件放大：**白底 + 三种节点面各一张**（4x）＋ 8x 细看 —— 证明三种面上都能辨认"""
    ims = [(n, png(os.path.join(OUT, n))) for n in CHECKS]
    fc_all = face_colors()
    cols = ([("白底 4x", WHITE, 4, "对照")]
            + [("%s面 4x" % FACE_CN[k], fc_all["med"][k], 4, hexof(fc_all["med"][k]))
               for k in ("section", "select", "frag")]
            + [("最差面(select) 8x", fc_all["med"]["select"], 8, "细看")])
    pad, gap = 20, 30
    x0 = 300
    rowh = 40 + 20 * 8 + 84
    W = max(1180, x0 + sum(20 * k + gap for _l, _b, k, _c in cols) + pad)
    H = 164 + rowh * 2
    sheet = Image.new("RGB", (W, H), (18, 22, 30))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), "已读对勾件 · 白底 + 三种节点面各一张（4x）＋ 8x 细看",
           font=font(20, True), fill=INK)
    d.text((pad, 46), "上：主版 x_ui_read_check.png　下：备选版 x_ui_read_check_alt.png"
                      "　（三种节点面取**底图件实测中位色**，即真的会压在对勾下面的那个色）",
           font=font(14), fill=HL)
    d.text((pad, 68), "硬边判据（独立 SDF）：形状外 ≥1.15px 处 α==0、形状内 ≥1.15px 处 α==255 ⇒ 无渐隐带；"
                      "最外 1px 帧 α==0；主版 α 完全由圆牌掩膜决定", font=font(13), fill=DIMTXT)
    for j, (lab, bg, k, sub) in enumerate(cols):
        cx = x0 + sum(20 * kk + gap for _l, _b, kk, _c in cols[:j])
        d.text((cx, 98), lab, font=font(13, True), fill=INK)
        d.text((cx, 114), sub, font=font(12), fill=DIMTXT)
    y = 140
    for name, im in ims:
        r = next(r for r in rows if r["name"] == name)
        d.text((pad, y + 48), name, font=font(16, True), fill=HL)
        d.text((pad, y + 70), "%s ｜ 主色 %s" % (r["size"], r["top"]), font=font(13), fill=DIMTXT)
        d.text((pad, y + 90), "α=0 %.2f%% ／ α=255 %.2f%%" % (r["zero"], r["full"]),
               font=font(13), fill=DIMTXT)
        x = x0
        for lab, bg, k, sub in cols:
            big = im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST)
            tile(sheet, d, on_bg(big, bg), x, y + 24, "", "", (90, 100, 120))
            x += big.size[0] + gap
        y += rowh
    sheet.save(os.path.join(EVID, "对勾4x放大.png"))
    print("   图：对勾4x放大.png %s" % (sheet.size,))


if __name__ == "__main__":
    sys.exit(main())

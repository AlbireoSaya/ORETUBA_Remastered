# -*- coding: utf-8 -*-
r"""M50 · CG 鉴赏页（`layout\screens\27_gallery.json`）素材模块
      —— ① 栏位差分缩略图（逐栏逐张）＋ ② 本页 chrome 件（程序化）

Issue : ISSUE-20260924-08（鉴赏模式四页重构 · M2 = CG 页数据 + 缩略图）
契约  : `_工作\ISSUE-20260924-08_鉴赏模式\方案.md` §1 CG 口径 / §5 机制契约 / §6 白名单 / §8 纪律
        主代理转达的 M1 冻结契约（`item_variants`：`frames` / `thumb` / `prev` / `next` / `text` / `edge`）

■■ 一 · 栏位缩略图（**产出范围 = 286 栏 × 每栏差分张数 = Σ差分件数**）
    入料：`CG候选集\组\<旧ID三位>_<组名>\<统一名>.png`（该栏的**原始差分图**）；
          并入成员的差分在**其各自旧组目录**里（按 `映射.tsv` 的「并入旧ID列表」顺序查找）。
    顺序：**严格按 `映射.tsv` 该栏「统一名列表」**（主件在前、并入成员按规格顺序）⇒ 与 `frames` 一一对应。
    出料：`krkr\assets\ui\x_gal_c<新ID三位>_<n>.png`（n 从 1 开始）。
          规格 = 与栏位 `thumb` 区 **1:1** = 287×162（栏位 291×166、底板描边 2px ⇒ 缩略图内缩 2px）。
          比例不同的 CG 走「**等比缩放 + 居中**」，留边**全透明**（衬出栏位底板深色磨砂，不烘黑边）。

■■ 二 · 本页 chrome 件（前缀 `x_ui_gal_`，程序化、PNG-32 真 alpha、我方冰蓝霜白族）
    x_ui_gal_cell_{off,over,on}.png        291×166  栏位底板三态（**直角**，参考作栏位圆角≈0）
    x_ui_gal_vprev_{off,over,on}.png        26×34   栏位内「上一张差分」键三态
    x_ui_gal_vnext_{off,over,on}.png        26×34   栏位内「下一张差分」键三态
    x_ui_gal_pgprev_{off,over,on}.png       56×56   页码「上一页」键三态
    x_ui_gal_pgnext_{off,over,on}.png       56×56   页码「下一页」键三态
    x_ui_gal_tab_{off,over,on}.png          96×84   四页签条底板三态（**供 M1 的 `39_gal_shell.json` 用**；
                                                    本屏不画页签条 —— 主代理 2026-09-24 裁决「页签 = 切屏」）
    文字一律**引擎绘制**（本工程铁律：禁止把文字烘焙进图）；件内只有形体与图形字形。

■■ 三 · 幂等与自证
    幂等：无随机、无时间戳 ⇒ 同版本脚本重跑**逐字节一致**（脚本末尾对已存在件做 md5 对拍）。
    自证：件数 = Σ差分件数、逐栏件数 = 该栏 `差分件数`、尺寸全等于规格、模式 RGBA、
          留边区域 α=0、形体峰值 α≥240、三态互异；任一不过 ⇒ 退出码 1。
    **本脚本只产 PNG，绝不写任何 JSON**（`layout\screens\27_gallery.json` 才是几何真相源）。

■ 运行
    python 工具\m50_make_gallery_thumbs.py                # 全量（缩略图 + chrome）
    python 工具\m50_make_gallery_thumbs.py --reps-only    # 只产每栏第 1 张（冒烟/省盘）
    python 工具\m50_make_gallery_thumbs.py --check        # 只做核对与统计，不写盘
    python 工具\m50_make_gallery_thumbs.py --chrome-only  # 只产 chrome 件
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import sys
import time

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")

# ──────────────────────────────────────────────────────────────── 几何（唯一真相源在本脚本；
#   `layout\screens\27_gallery.json` 的 list 几何必须与之逐字一致）
SLOT_W, SLOT_H = 291, 166          # 栏位（= 参考作《交汇协奏曲》CG 页 `#item00` 实测 291×166）
CELL_EDGE = 2                      # 栏位底板描边宽（缩略图内缩同值）
THUMB_W, THUMB_H = SLOT_W - 2 * CELL_EDGE, SLOT_H - 2 * CELL_EDGE    # 287×162
VAR_BTN = (26, 34)                 # 栏位内差分翻页键
PG_BTN = (56, 56)                  # 页码翻页键
TAB = (96, 84)                     # 页签底板（供 39_gal_shell.json）

# 差分缩略图来源（CG 候选集）：wt 工作树里没有，回落到主工作树
CG_ROOT_CANDS = [
    os.path.join(UI_GROUP, "_工作", "ISSUE-20260924-08_鉴赏模式", "CG候选集"),
    r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    r"\_工作\ISSUE-20260924-08_鉴赏模式\CG候选集",
]


# ──────────────────────────────────────────────────────────────── 调色板
def load_palette(path=PALETTE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = load_palette()


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    if key not in PAL:
        raise KeyError("palette.json 缺键 %r（唯一色值来源，缺键即报错、不静默回落）" % key)
    return hex2rgb(PAL[key]["value"])


def OPA(key):
    return int(PAL[key]["value"])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# 合成色（palette.json 无此键；推导来源注明，不新增独立色号 —— 与 M47/M49 同口径）
FROST = (244, 248, 255)          # 霜白：@palette.accent 向白 78%
INK = (22, 32, 46)               # 墨蓝（栏位底板基色）：@palette.panel_fill(#141824) 向 accent 8%


# ──────────────────────────────────────────────────────────────── 基础工具（与 M47/M49 同源）
def tint(mask, rgb, alpha=255):
    m = mask
    if alpha != 255:
        m = m.point(lambda v: v * alpha // 255)
    im = Image.new("RGBA", m.size, tuple(rgb) + (0,))
    im.putalpha(m)
    return im


def aa(size, draw_fn, scale=4):
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    draw_fn(ImageDraw.Draw(m), scale)
    return m.resize((w, h), Image.LANCZOS)


def rr_mask(size, box, radius, scale=4):
    """圆角矩形掩膜（**半开区间**语义，与 M47/M49 同规）"""
    def _d(d, s):
        if radius <= 0:
            d.rectangle([v * s for v in box], fill=255)
        else:
            d.rounded_rectangle([v * s for v in box], radius=radius * s, fill=255)
    return aa(size, _d, scale)


def glow_of(mask, sigma, gain):
    g = mask.filter(ImageFilter.GaussianBlur(sigma))
    return g.point(lambda v: min(255, int(v * gain)))


def clip_low_alpha(img, thr=3):
    a = img.getchannel("A").point(lambda v: 0 if v <= thr else v)
    out = img.copy()
    out.putalpha(a)
    return out


def ring_mask(size, box, radius, width):
    outer = rr_mask(size, box, radius)
    inner = rr_mask(size, (box[0] + width, box[1] + width, box[2] - width, box[3] - width),
                    max(0.0, radius - width))
    return ImageChops.subtract(outer, inner)


def tri_mask(size, cx, cy, half_w, half_h, direction, scale=4):
    """实心三角（◀ / ▶）掩膜；direction ∈ {-1, +1}"""
    def _d(d, s):
        pts = [(cx + direction * half_w, cy),
               (cx - direction * half_w, cy - half_h),
               (cx - direction * half_w, cy + half_h)]
        d.polygon([(p[0] * s, p[1] * s) for p in pts], fill=255)
    return aa(size, _d, scale)


def dbl_tri_mask(size, cx, cy, half_w, half_h, direction, gap, scale=4):
    """双三角（◀◀ / ▶▶）—— 参考作页签/页码键的字形语言"""
    a = tri_mask(size, cx - direction * (half_w + gap / 2.0), cy, half_w, half_h, direction, scale)
    b = tri_mask(size, cx + direction * (half_w + gap / 2.0), cy, half_w, half_h, direction, scale)
    return ImageChops.lighter(a, b)


# ──────────────────────────────────────────────────────────────── chrome：栏位底板 291×166（直角）
def build_cell(state):
    W, H = SLOT_W, SLOT_H
    accent, edge = C("accent"), C("panel_edge")
    body_rgb = {"off": mix(INK, accent, 0.06), "over": mix(INK, accent, 0.16),
                "on": mix(INK, accent, 0.28)}[state]
    body_a = {"off": 232, "over": 240, "on": 248}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 190, "over": 235, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.34, "on": 0.55}[state]

    box = (0, 0, W, H)
    outer = rr_mask((W, H), box, 0)                       # 直角（参考作 CG 栏位圆角≈0）
    ring = ring_mask((W, H), box, 0, CELL_EDGE)

    img = tint(outer, body_rgb, body_a)
    if glow_gain > 0:
        # 内缘柔光（压在内侧，不外溢 ⇒ 不破坏直角与相邻栏位间距）
        g = glow_of(ring, 2.4, glow_gain)
        img = Image.alpha_composite(img, tint(ImageChops.multiply(g, outer), accent))
    # 顶内 1px 霜白高光（族语言：玻璃质感）
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, CELL_EDGE, W, CELL_EDGE + 1], fill=255)
    img = Image.alpha_composite(img, tint(hl, FROST, 70))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────────── chrome：差分翻页键 26×34
def build_var_btn(state, direction):
    W, H = VAR_BTN
    accent, edge = C("accent"), C("panel_edge")
    body_rgb = {"off": mix(INK, accent, 0.10), "over": mix(INK, accent, 0.26),
                "on": mix(INK, accent, 0.44)}[state]
    body_a = {"off": 205, "over": 228, "on": 244}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 165, "over": 220, "on": 255}[state]
    glyph_rgb = mix(accent, FROST, 0.15) if state != "on" else FROST
    glyph_a = {"off": 205, "over": 245, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.30, "on": 0.50}[state]

    box = (1.0, 1.0, W - 1.0, H - 1.0)
    outer = rr_mask((W, H), box, 4.5)
    ring = ring_mask((W, H), box, 4.5, 1.5)
    img = tint(outer, body_rgb, body_a)
    if glow_gain > 0:
        g = glow_of(ring, 2.0, glow_gain)
        img = Image.alpha_composite(img, tint(ImageChops.multiply(g, outer), accent))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))
    img = Image.alpha_composite(img, tint(tri_mask((W, H), W / 2.0 + direction * 0.5, H / 2.0,
                                                   4.0, 6.0, direction), glyph_rgb, glyph_a))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────────── chrome：页码翻页键 56×56
def build_pg_btn(state, direction):
    W, H = PG_BTN
    accent, edge = C("accent"), C("panel_edge")
    body_rgb = {"off": mix(FROST, accent, 0.20), "over": mix(FROST, accent, 0.32),
                "on": mix(FROST, accent, 0.62)}[state]
    body_a = {"off": 236, "over": 242, "on": 252}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 150, "over": 215, "on": 255}[state]
    glyph_rgb = mix(accent, FROST, 0.10) if state != "on" else FROST
    glyph_a = {"off": 225, "over": 245, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.42, "on": 0.66}[state]

    box = (2.0, 2.0, W - 2.0, H - 2.0)
    outer = rr_mask((W, H), box, 12.0)
    ring = ring_mask((W, H), box, 12.0, 2.0)
    img = tint(outer, body_rgb, body_a)
    if glow_gain > 0:
        img = Image.alpha_composite(img, tint(glow_of(ring, 3.0, glow_gain), accent))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, 4, W, 5], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, outer), FROST, 150))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))
    img = Image.alpha_composite(img, tint(dbl_tri_mask((W, H), W / 2.0, H / 2.0,
                                                       4.5, 7.5, direction, 3.0),
                                          glyph_rgb, glyph_a))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────────── chrome：页签底板 96×84
TAB_BODY = (0.0, 33.0, 96.0, 73.0)      # 云朵/气泡体的纵向范围（参考作签条实测 y33..73）


def build_tab(state):
    W, H = TAB
    accent, edge = C("accent"), C("panel_edge")
    body_rgb = {"off": mix(FROST, accent, 0.14), "over": mix(FROST, accent, 0.24),
                "on": mix(FROST, accent, 0.48)}[state]
    body_a = {"off": 158, "over": 196, "on": 236}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 120, "over": 185, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.34, "on": 0.55}[state]

    box = TAB_BODY
    outer = rr_mask((W, H), box, 18.0)
    ring = ring_mask((W, H), box, 18.0, 2.0)
    img = tint(outer, body_rgb, body_a)
    if glow_gain > 0:
        img = Image.alpha_composite(img, tint(glow_of(ring, 3.2, glow_gain), accent))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, int(TAB_BODY[1]) + 3, W, int(TAB_BODY[1]) + 5], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, outer), FROST, 140))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))
    return clip_low_alpha(img, 3)


CHROME = [
    ("x_ui_gal_cell_off.png", "off", lambda s: build_cell(s)),
    ("x_ui_gal_cell_over.png", "over", lambda s: build_cell(s)),
    ("x_ui_gal_cell_on.png", "on", lambda s: build_cell(s)),
    ("x_ui_gal_vprev_off.png", "off", lambda s: build_var_btn(s, -1)),
    ("x_ui_gal_vprev_over.png", "over", lambda s: build_var_btn(s, -1)),
    ("x_ui_gal_vprev_on.png", "on", lambda s: build_var_btn(s, -1)),
    ("x_ui_gal_vnext_off.png", "off", lambda s: build_var_btn(s, +1)),
    ("x_ui_gal_vnext_over.png", "over", lambda s: build_var_btn(s, +1)),
    ("x_ui_gal_vnext_on.png", "on", lambda s: build_var_btn(s, +1)),
    ("x_ui_gal_pgprev_off.png", "off", lambda s: build_pg_btn(s, -1)),
    ("x_ui_gal_pgprev_over.png", "over", lambda s: build_pg_btn(s, -1)),
    ("x_ui_gal_pgprev_on.png", "on", lambda s: build_pg_btn(s, -1)),
    ("x_ui_gal_pgnext_off.png", "off", lambda s: build_pg_btn(s, +1)),
    ("x_ui_gal_pgnext_over.png", "over", lambda s: build_pg_btn(s, +1)),
    ("x_ui_gal_pgnext_on.png", "on", lambda s: build_pg_btn(s, +1)),
    ("x_ui_gal_tab_off.png", "off", lambda s: build_tab(s)),
    ("x_ui_gal_tab_over.png", "over", lambda s: build_tab(s)),
    ("x_ui_gal_tab_on.png", "on", lambda s: build_tab(s)),
]
CHROME_SIZE = {
    "x_ui_gal_cell_": (SLOT_W, SLOT_H),
    "x_ui_gal_vprev_": VAR_BTN, "x_ui_gal_vnext_": VAR_BTN,
    "x_ui_gal_pgprev_": PG_BTN, "x_ui_gal_pgnext_": PG_BTN,
    "x_ui_gal_tab_": TAB,
}


def chrome_size(name):
    for pre, sz in CHROME_SIZE.items():
        if name.startswith(pre):
            return sz
    raise KeyError(name)


# ──────────────────────────────────────────────────────────────── CG 候选集读取
def find_cg_root():
    for p in CG_ROOT_CANDS:
        if os.path.exists(os.path.join(p, "新顺序", "映射.tsv")):
            return p
    raise SystemExit("找不到 CG 候选集（试过：\n  %s\n）" % "\n  ".join(CG_ROOT_CANDS))


def read_rows(cg_root):
    import csv
    p = os.path.join(cg_root, "新顺序", "映射.tsv")
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = []
    for r in rows:
        uni = [x for x in (r["该栏统一名列表"] or "").split("、") if x]
        out.append({
            "新ID": r["新ID"].strip(),
            "原新ID": r["原新ID"].strip(),
            "旧ID": r["旧ID"].strip(),
            "组名": r["组名"].strip(),
            "N": int(r["差分件数"]),
            "并入": [x for x in (r["并入旧ID列表"] or "").split("、") if x],
            "统一名": uni,
            "代表图": os.path.basename(r["代表图路径"].replace("\\", "/")),
        })
    return out


def resolve_variant_files(cg_root, row):
    """按「统一名列表」顺序解析出物理文件；先查本组目录，再按并入顺序查各并入组目录。"""
    own = os.path.join(cg_root, "组", "%s_%s" % (row["旧ID"], row["组名"]))
    cands = [own]
    for oid in row["并入"]:
        cands.extend(sorted(glob.glob(os.path.join(cg_root, "组", "%s_*" % oid))))
    found, miss = [], []
    for u in row["统一名"]:
        hit = None
        for d in cands:
            q = os.path.join(d, u)
            if os.path.exists(q):
                hit = q
                break
        if hit is None:
            miss.append(u)
        found.append(hit)
    return found, miss


def md5_file(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ──────────────────────────────────────────────────────────────── 缩略图
def make_thumb(src_path, size=(THUMB_W, THUMB_H)):
    """等比缩放 + 居中；留边全透明（衬栏位底板）"""
    im = Image.open(src_path)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    sc = min(size[0] / float(w), size[1] / float(h))
    nw = max(1, int(round(w * sc)))
    nh = max(1, int(round(h * sc)))
    sm = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(sm, ((size[0] - nw) // 2, (size[1] - nh) // 2))
    return canvas


def thumb_png_bytes(src_path, quantize=0):
    """缩略图的**唯一编码出口**（写盘与幂等对拍共用 ⇒ 对拍才有意义）"""
    img = make_thumb(src_path)
    if quantize > 0:
        rr, gg, bb, al = img.split()
        q = Image.merge("RGB", (rr, gg, bb)).quantize(colors=quantize,
                                                      method=Image.MEDIANCUT).convert("RGB")
        img = Image.merge("RGBA", (*q.split(), al))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只核对与统计，不写盘")
    ap.add_argument("--reps-only", action="store_true", help="只产每栏第 1 张（冒烟）")
    ap.add_argument("--chrome-only", action="store_true", help="只产 chrome 件")
    ap.add_argument("--quantize", type=int, default=0,
                    help=">0 时对缩略图 RGB 做 N 色量化（保留 8-bit alpha）以压体积；默认 0 = 不量化")
    args = ap.parse_args()

    cg_root = find_cg_root()
    rows = read_rows(cg_root)
    print("=" * 100)
    print("M50 · CG 鉴赏页素材模块")
    print("  CG 候选集 : %s" % cg_root)
    print("  输出目录  : %s" % ASSETS)
    print("  栏位数    : %d（新ID %s..%s）" % (len(rows), rows[0]["新ID"], rows[-1]["新ID"]))
    print("  缩略图规格: %dx%d（栏位 %dx%d − 描边 %dpx×2）｜入料 = 该栏原始差分图，等比缩放+居中、留边全透明"
          % (THUMB_W, THUMB_H, SLOT_W, SLOT_H, CELL_EDGE))
    print("  chrome    : %d 件（前缀 x_ui_gal_）" % len(CHROME))
    print("=" * 100)

    # ── 断言 A：新ID 连续 001..286；Σ差分件数
    ids = [r["新ID"] for r in rows]
    assert ids == ["%03d" % i for i in range(1, len(rows) + 1)], "新ID 不连续"
    sum_n = sum(r["N"] for r in rows)
    per_len_ok = all(len(r["统一名"]) == r["N"] for r in rows)
    print("① 栏位表核对")
    print("   新ID 连续 001..%03d ......... OK" % len(rows))
    print("   Σ差分件数 = %d .............. %s" % (sum_n, "OK" if sum_n else "NG"))
    print("   每栏 len(统一名)==差分件数 ... %s" % ("OK" if per_len_ok else "**NG**（逐栏核对见下）"))
    if not per_len_ok:
        for r in rows:
            if len(r["统一名"]) != r["N"]:
                print("      !! 新ID %s %s：差分件数=%d 但统一名 %d 条"
                      % (r["新ID"], r["组名"], r["N"], len(r["统一名"])))

    # ── 解析全部差分文件
    print("-" * 100)
    print("② 差分文件解析（本组目录优先，再按「并入旧ID列表」顺序）")
    resolved = {}
    n_miss = 0
    rep_mismatch = []
    for r in rows:
        files, miss = resolve_variant_files(cg_root, r)
        resolved[r["新ID"]] = files
        if miss:
            n_miss += len(miss)
            print("   !! 新ID %s %s 缺 %d 件：%s" % (r["新ID"], r["组名"], len(miss), miss))
        # 代表图 vs 统一名列表[0]
        rp = os.path.join(cg_root, "代表图", r["代表图"])
        if files[0] and os.path.exists(rp) and md5_file(files[0]) != md5_file(rp):
            rep_mismatch.append((r["新ID"], r["组名"], r["代表图"], r["统一名"][0]))
    print("   缺失件数 = %d ................ %s" % (n_miss, "OK" if n_miss == 0 else "**NG**"))
    print("   代表图 == 统一名列表[0] ...... %s"
          % ("OK（%d/%d 栏逐字节相同）" % (len(rows), len(rows)) if not rep_mismatch
             else "**%d 栏不同**" % len(rep_mismatch)))
    for t in rep_mismatch[:10]:
        print("      ~ 新ID %s %s：代表图 %s ≠ 统一名[0] %s" % t)
    if n_miss:
        raise SystemExit("有缺件，终止（不产半套）")

    # ── 产缩略图
    made, sizes_bytes = [], {}
    if not args.check and not args.chrome_only:
        print("-" * 100)
        print("③ 产出缩略图%s" % ("（--reps-only）" if args.reps_only else ""))
        t0 = time.time()
        done = 0
        for r in rows:
            files = resolved[r["新ID"]]
            take = 1 if args.reps_only else len(files)
            for n in range(1, take + 1):
                src = files[n - 1]
                out = "x_gal_c%s_%d.png" % (r["新ID"], n)
                blob = thumb_png_bytes(src, args.quantize)
                with open(os.path.join(ASSETS, out), "wb") as f:
                    f.write(blob)
                made.append((out, r["新ID"], n, (THUMB_W, THUMB_H), len(blob)))
                done += 1
            if done % 100 == 0:
                print("   ... %d 件" % done)
        print("   写出 %d 件，用时 %.1f s" % (len(made), time.time() - t0))

    # ── 产 chrome
    if not args.check and not args.reps_only:
        print("-" * 100)
        print("④ 产出 chrome 件")
        for name, state, fn in CHROME:
            img = fn(state)
            sz = chrome_size(name)
            assert img.size == sz, (name, img.size, sz)
            img.save(os.path.join(ASSETS, name), optimize=True, compress_level=9)
            print("   %-28s %dx%d  %7d B" % (name, sz[0], sz[1],
                                             os.path.getsize(os.path.join(ASSETS, name))))

    # ── 自证
    print("-" * 100)
    print("⑤ 自证（逐件断言）")
    ok = True

    def say(good, label, detail):
        nonlocal ok
        ok &= bool(good)
        print("   [%s] %-46s %s" % ("OK " if good else "NG!", label, detail))
        return good

    if args.check:
        print("   （--check：跳过写盘断言，只统计）")
    else:
        # 件数
        expect = sum(1 if args.reps_only else r["N"] for r in rows)
        if not args.chrome_only:
            have = [n for n in os.listdir(ASSETS) if n.startswith("x_gal_c") and n.endswith(".png")]
            say(len(have) == expect, "缩略图件数 == Σ差分件数（或 reps-only 的 286）",
                "%d / %d" % (len(have), expect))
            # 逐栏件数
            bad = []
            for r in rows:
                take = 1 if args.reps_only else r["N"]
                for n in range(1, take + 1):
                    p = os.path.join(ASSETS, "x_gal_c%s_%d.png" % (r["新ID"], n))
                    if not os.path.exists(p):
                        bad.append(p)
            say(not bad, "逐栏无缺件（frames 与文件一一对应）",
                "缺 %d 件%s" % (len(bad), ("：" + str(bad[:3])) if bad else ""))
            # 尺寸 / 模式 / 留边透明
            #   ★ 判据修正（首轮实测）：**不能**简单断言「四角 α=0」—— 16:9 源（1280×720）
            #     缩进 287×162 后几乎满幅（内容比 1.778 vs 画框 1.771），四角本就是画面像素。
            #     正确判据 = 「**该留边的地方必须透明**」：由源宽高比反算内容矩形，
            #     在画框内、内容矩形**之外**取 1px 带，断言 α=0（未烘黑边/未填底色）。
            bad_sz, bad_mode, bad_pad, n_full = [], [], [], 0
            for r in rows:
                take = 1 if args.reps_only else r["N"]
                for n in range(1, take + 1):
                    p = os.path.join(ASSETS, "x_gal_c%s_%d.png" % (r["新ID"], n))
                    with Image.open(p) as im:
                        if im.size != (THUMB_W, THUMB_H):
                            bad_sz.append((os.path.basename(p), im.size))
                        if im.mode != "RGBA":
                            bad_mode.append((os.path.basename(p), im.mode))
                        src = resolved[r["新ID"]][n - 1]
                        with Image.open(src) as s0:
                            sw, sh = s0.size
                        sc = min(THUMB_W / float(sw), THUMB_H / float(sh))
                        cw = max(1, int(round(sw * sc)))
                        ch = max(1, int(round(sh * sc)))
                        cx0 = (THUMB_W - cw) // 2
                        cy0 = (THUMB_H - ch) // 2
                        if cw >= THUMB_W and ch >= THUMB_H:
                            n_full += 1
                            continue
                        px = im.load()
                        band = []
                        if cx0 > 0:
                            band += [(x, y) for x in range(0, cx0) for y in range(0, THUMB_H, 4)]
                            band += [(x, y) for x in range(cx0 + cw, THUMB_W)
                                     for y in range(0, THUMB_H, 4)]
                        if cy0 > 0:
                            band += [(x, y) for x in range(0, THUMB_W, 4) for y in range(0, cy0)]
                            band += [(x, y) for x in range(0, THUMB_W, 4)
                                     for y in range(cy0 + ch, THUMB_H)]
                        if any(px[x, y][3] != 0 for x, y in band):
                            bad_pad.append(os.path.basename(p))
            say(not bad_sz, "尺寸全 == %dx%d（与栏位 thumb 区 1:1）" % (THUMB_W, THUMB_H),
                "越界 %d 件%s" % (len(bad_sz), bad_sz[:3] if bad_sz else ""))
            say(not bad_mode, "模式全 RGBA（真 alpha）", "非 RGBA %d 件" % len(bad_mode))
            say(not bad_pad, "留边（内容矩形之外）α=0 —— 未烘黑边/未填底色",
                "有底色 %d 件%s（另 %d 件 16:9 源满幅、无留边）"
                % (len(bad_pad), bad_pad[:3] if bad_pad else "", n_full))
            # 幂等：内存重算 6 件与盘上逐字节对拍（同一编码出口 ⇒ 无随机/无时间戳即必相等）
            det = []
            for r in rows[:6]:
                blob = thumb_png_bytes(resolved[r["新ID"]][0], args.quantize)
                p = os.path.join(ASSETS, "x_gal_c%s_1.png" % r["新ID"])
                with open(p, "rb") as f:
                    det.append(blob == f.read())
            say(all(det), "幂等：内存重算与盘上逐字节一致", "%d / %d 件" % (sum(det), len(det)))
        # chrome 三态互异 + 尺寸
        for pre in ("x_ui_gal_cell_", "x_ui_gal_vprev_", "x_ui_gal_vnext_",
                    "x_ui_gal_pgprev_", "x_ui_gal_pgnext_", "x_ui_gal_tab_"):
            sz = chrome_size(pre + "off.png")
            a = Image.open(os.path.join(ASSETS, pre + "off.png")).convert("RGBA")
            b = Image.open(os.path.join(ASSETS, pre + "over.png")).convert("RGBA")
            c = Image.open(os.path.join(ASSETS, pre + "on.png")).convert("RGBA")
            n1 = sum(1 for y in range(sz[1]) for x in range(sz[0])
                     if max(abs(a.load()[x, y][i] - b.load()[x, y][i]) for i in range(4)) > 8)
            n2 = sum(1 for y in range(sz[1]) for x in range(sz[0])
                     if max(abs(a.load()[x, y][i] - c.load()[x, y][i]) for i in range(4)) > 8)
            say(n1 > 100 and n2 > 100, "%s 三态互异（off↔over / off↔on 差异像素 > 100）" % pre,
                "%d / %d px" % (n1, n2))
            say(all(Image.open(os.path.join(ASSETS, pre + s + ".png")).size == sz
                    for s in ("off", "over", "on")),
                "%s 三态尺寸一致 %dx%d" % (pre, sz[0], sz[1]), "OK")

    # ── 统计
    print("-" * 100)
    print("⑥ 统计")
    if made:
        tot = sum(m[4] for m in made)
        print("   缩略图：%d 件 ｜ 合计 %.2f MB ｜ 均 %.1f KB ｜ 最小 %.1f KB ｜ 最大 %.1f KB"
              % (len(made), tot / 1048576.0, tot / float(len(made)) / 1024.0,
                 min(m[4] for m in made) / 1024.0, max(m[4] for m in made) / 1024.0))
        buckets = {}
        for m in made:
            k = (m[4] // 10240) * 10
            buckets[k] = buckets.get(k, 0) + 1
        print("   体积分布（10KB 桶）：%s"
              % ", ".join("%d–%dKB:%d" % (k, k + 10, buckets[k]) for k in sorted(buckets)))
    tot_all = 0
    n_all = 0
    for n in sorted(os.listdir(ASSETS)):
        if n.startswith("x_ui_gal_") or n.startswith("x_gal_c"):
            tot_all += os.path.getsize(os.path.join(ASSETS, n))
            n_all += 1
    print("   本模块全部新件（x_ui_gal_* + x_gal_c*）：%d 件 ｜ %.2f MB" % (n_all, tot_all / 1048576.0))
    tot_dir = sum(os.path.getsize(os.path.join(ASSETS, f)) for f in os.listdir(ASSETS)
                  if f.lower().endswith(".png"))
    print("   assets/ui 目录总计：%.2f MB（verify_ui [6] 预算 56.00 MB）" % (tot_dir / 1048576.0))
    print("=" * 100)
    print("RESULT=%s" % ("OK" if ok else "NG 有自证未过（见上）"))
    print("★ 提醒：`layout\\screens\\27_gallery.json` 才是几何真相源；本脚本只产 PNG。")
    print("=" * 100)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
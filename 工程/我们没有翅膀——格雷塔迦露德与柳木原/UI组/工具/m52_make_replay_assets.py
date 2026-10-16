# -*- coding: utf-8 -*-
r"""M52 · 情景回想页（`layout\screens\38_replay.json`）素材模块 —— 程序化生成 `x_ui_rp_*` 全套（11 件）

Issue : ISSUE-20260924-08（鉴赏模式四页重构 · **M4 = 立绘鉴赏 + 情景回想**）
契约  : `_工作\ISSUE-20260924-08_鉴赏模式\方案.md`
        §0（参考件：`工程\交汇协奏曲\解包\gallery\结构清单.md` §2.3 情景回想 19 条 + `layers_75.json`）
        §2（情景回想：第一页 5×5 占位 / 第二页 5×5 放动画）、§8（纪律：PNG-32 真 alpha、
        我方冰蓝霜白、**禁止把文字烘焙进图**）

■■ 产出（全部落 `krkr\assets\ui\`，**新前缀 `x_ui_rp_`，旧件一件不删**）
    ── 栏位底板（`list.item_frame.state_assets` 逐项三态；1:1 件，无 nine；**直角** —— 同 M2 的
       CG 栏位口径：参考作栏位圆角≈0）
    x_ui_rp_cell_{off,over,on}.png    234×133  （对应参考作 `Replay/small/item:normal` 234×133）
    ── 动画占位缩略图（`list.item_variants.frames` 的差分件；1:1 = thumb 区 230×129）
    x_ui_rp_mv_thumb.png              230×129  （胶片齿孔 + ▶ 播放三角，**纯图形无文字**）
    ── 预览板（参考作 `Replay/small/preview` 575×715 青底预览板 ⇒ 我方冰蓝磨砂占位底板）
    x_ui_rp_preview.png               575×715
    ── 页码翻页键（与 M2 的 `x_ui_gal_pg*` / M3 的 `x_ui_bgm_pg*` **同形同尺寸** ——
       直接复用 m50 的 `build_pg_btn()` 绘制，仅落盘为本模块前缀）
    x_ui_rp_pgprev_{off,over,on}.png / x_ui_rp_pgnext_{off,over,on}.png   56×56 × 6 件
    合计 3 + 1 + 1 + 6 = **11 件**

    ★ 栏位内差分翻页键（`item_variants.prev/next`，26×34 三态）**本脚本不产出**：
      直接复用 M2 的 `ui/x_ui_gal_vprev_*.png` / `ui/x_ui_gal_vnext_*.png`（同机制同字形，
      26×34，family 一致）—— 不新增重复件。
    ★ 标题牌**本版不产出**：主代理 2026-09-24 裁决「页签 = 切屏」，共享外壳由 M1 的
      `39_gal_shell.json` 提供，本屏 `attach` 它（与 M2/M3 同口径）⇒ 标题归外壳。
    ★ 不铺整页底图：与 `26_backlog` / `27_gallery` / `28_music` 同口径 —— 系统屏是透明浮层，
      只留一层薄压暗（`rp.dim`），可读性由栏位底板（α 232–248）承担。

■■ 字形一律**图形**、**不含任何文字**
    ▶ 播放三角与胶片齿孔是几何图形（不是文字）；角色名/情景名/页码/`n/N` 一律由引擎绘制。
    「播放中」标记属**运行期**（参考件 §6.3-5 缺口已登记）⇒ 本版只在占位缩略图上烘**静态 ▶**
    表示「这是可播项」，播放态标记留编程组（口径见 38_replay.json 屏 note）。

■■ 风格口径（我方冰蓝霜白族）
    配色一律取自 `layout\palette.json`（唯一色值来源）；霜白 FROST / 墨蓝 INK 为合成色
    （推导自 accent 向白 / panel_fill 向 accent），与 M47/M49/M50 同口径，**不新增色板键**。
    程序化绘制、4× 超采样降采样 ⇒ 真 alpha、无 8-bit 噪声、无棋盘格/白底烘焙、**可复现**
    （无随机、无时间戳 ⇒ 同版本脚本重跑逐字节一致）。

■ 运行
    python 工具\m52_make_replay_assets.py
  退出码 0 = 11 件全部写出且全部自证通过。**本脚本只产 PNG、绝不写任何 JSON**
  （`layout\screens\38_replay.json` 才是几何真相源）。
"""
from __future__ import annotations

import hashlib
import os
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))                 # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                                  # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")

# 与 M2/M3 同一套基础工具（**import，不复制公式**；m50 自身 main 有守卫，import 无副作用）
sys.path.insert(0, HERE)
import m50_make_gallery_thumbs as m50  # noqa: E402  （tint/rr_mask/ring_mask/glow_of/…）

mix = m50.mix
tint = m50.tint
rr_mask = m50.rr_mask
ring_mask = m50.ring_mask
glow_of = m50.glow_of
clip_low_alpha = m50.clip_low_alpha
tri_mask = m50.tri_mask
FROST = m50.FROST
INK = m50.INK
C = m50.C


# ──────────────────────────────────────────────────────────── 几何（唯一真相源在本脚本；
#   `layout\screens\38_replay.json` 的 list / thumb 几何必须与之逐字一致）
CELL_W, CELL_H = 234, 133          # 栏位（= 参考作《交汇协奏曲》情景回想 `Replay/small/item:normal` 实测 234×133）
CELL_EDGE = 2                      # 栏位底板描边宽（缩略图内缩同值，同 M2 口径）
# ★ M4 订正（2026-09-24，首版截图实测）：缩略图**不满幅** —— 底部留 22px 说明条（`list.item_text`，
#   块内局部 (4,109,226,22)）给引擎绘制的占位标签（「情景 001」/「动画 01」）。
#   画序 = item_text 先画、variants 后画 ⇒ 满幅缩略图会把标签压住（首版 230×129 实测标签不可读），
#   故 thumb 高 = 133 − 2×2 − 24(说明条 22 + 间隙 2) = 105。
THUMB_W, THUMB_H = CELL_W - 2 * CELL_EDGE, 105
PREVIEW_W, PREVIEW_H = 575, 715    # 预览板（= 参考作 `Replay/small/preview` 实测 575×715）
PG_BTN = (56, 56)                  # 页码翻页键（与 M2/M3 同形）


# ──────────────────────────────────────────────────────────── 栏位底板 234×133（直角三态）
def build_cell(state):
    """234×133 情景回想栏位底板（风格逐字对齐 m50.build_cell，仅尺寸不同）。"""
    W, H = CELL_W, CELL_H
    accent, edge = C("accent"), C("panel_edge")
    body_rgb = {"off": mix(INK, accent, 0.06), "over": mix(INK, accent, 0.16),
                "on": mix(INK, accent, 0.28)}[state]
    body_a = {"off": 232, "over": 240, "on": 248}[state]
    rim_rgb = edge if state == "off" else accent
    rim_a = {"off": 190, "over": 235, "on": 255}[state]
    glow_gain = {"off": 0.0, "over": 0.34, "on": 0.55}[state]

    box = (0, 0, W, H)
    outer = rr_mask((W, H), box, 0)                       # 直角（参考作栏位圆角≈0）
    ring = ring_mask((W, H), box, 0, CELL_EDGE)
    img = tint(outer, body_rgb, body_a)
    if glow_gain > 0:
        g = glow_of(ring, 2.4, glow_gain)
        img = Image.alpha_composite(img, tint(ImageChops.multiply(g, outer), accent))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, CELL_EDGE, W, CELL_EDGE + 1], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, outer), FROST, 70))
    img = Image.alpha_composite(img, tint(ring, rim_rgb, rim_a))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────── 动画占位缩略图 230×129
def build_mv_thumb():
    """230×129 动画占位缩略图：墨蓝胶片段 + 上下齿孔 + 中央 ▶ 播放三角（纯图形，无文字）。"""
    W, H = THUMB_W, THUMB_H
    accent = C("accent")
    body_rgb = mix(INK, accent, 0.10)
    img = tint(rr_mask((W, H), (0, 0, W, H), 0), body_rgb, 235)

    # 上下胶片齿孔带（每带 12 孔，孔 8×6，圆角 2 —— 几何图形；聚合到全幅掩膜后一次叠加）
    hole = rr_mask((8, 6), (0, 0, 8, 6), 2)
    holes = Image.new("L", (W, H), 0)
    step = (W - 24 - 8) // 11
    for band_y in (7, H - 7 - 6):
        for k in range(12):
            x0 = 12 + (k * step if k > 0 else 0)
            if x0 + 8 > W - 12:
                continue
            holes.paste(hole, (x0, band_y))
    img = Image.alpha_composite(img, tint(holes, FROST, 46))

    # 中央 ▶ 播放三角（外圈细环 + 实心三角 —— 「这是可播项」的**静态占位标记**；
    #   「播放中」态属运行期，参考件 §6.3-5 已登记缺口 ⇒ 留编程组，本版不做）
    cx, cy = W / 2.0, H / 2.0
    ring = ring_mask((W, H), (cx - 26, cy - 26, cx + 26, cy + 26), 26, 3)
    img = Image.alpha_composite(img, tint(ring, FROST, 150))
    tri = tri_mask((W, H), cx + 2, cy, 13, 17, +1)
    img = Image.alpha_composite(img, tint(tri, FROST, 220))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────── 预览板 575×715
def build_preview():
    """575×715 选中情景预览板（占位底板）：冰蓝磨砂 + 细描边 + 顶内高光（族语言同 M2/M3）。
    运行期由编程组贴选中情景画面/播放器；本版为空底板。"""
    W, H = PREVIEW_W, PREVIEW_H
    accent, edge = C("accent"), C("panel_edge")
    box = (0, 0, W, H)
    outer = rr_mask((W, H), box, 0)                       # 直角（参考作预览板同族口径）
    ring = ring_mask((W, H), box, 0, 2)
    img = tint(outer, mix(FROST, accent, 0.24), 200)
    img = Image.alpha_composite(img, tint(glow_of(ring, 3.0, 0.30), accent))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).rectangle([0, 2, W, 3], fill=255)
    img = Image.alpha_composite(img, tint(ImageChops.multiply(hl, outer), FROST, 150))
    img = Image.alpha_composite(img, tint(ring, edge, 170))
    return clip_low_alpha(img, 3)


# ──────────────────────────────────────────────────────────── 产物清单
def chrome_size(name):
    if name.startswith("x_ui_rp_cell_"):
        return (CELL_W, CELL_H)
    if name == "x_ui_rp_mv_thumb.png":
        return (THUMB_W, THUMB_H)
    if name == "x_ui_rp_preview.png":
        return (PREVIEW_W, PREVIEW_H)
    if name.startswith("x_ui_rp_pg"):
        return PG_BTN
    raise AssertionError(name)


def build_assets():
    out = {}
    for st in ("off", "over", "on"):
        out["x_ui_rp_cell_%s.png" % st] = build_cell(st)
    out["x_ui_rp_mv_thumb.png"] = build_mv_thumb()
    out["x_ui_rp_preview.png"] = build_preview()
    for st in ("off", "over", "on"):
        out["x_ui_rp_pgprev_%s.png" % st] = m50.build_pg_btn(st, -1)
        out["x_ui_rp_pgnext_%s.png" % st] = m50.build_pg_btn(st, +1)
    return out


def diff_px(a, b):
    """逐像素 RGBA 四通道最大差 > 8 计 1（与 m51 同一口径）。"""
    n = 0
    pa, pb = a.load(), b.load()
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            if max(abs(pa[x, y][i] - pb[x, y][i]) for i in range(4)) > 8:
                n += 1
    return n


def _say(ok, name, detail):
    print(("  [OK ] " if ok else "  [NG!] ") + "%-40s %s" % (name, detail))
    return ok


def verify(name, img, size):
    ok = True
    ok &= _say(img.size == size, name, "尺寸 %s（期望 %s）" % (img.size, size))
    ok &= _say(img.mode == "RGBA", name, "模式 %s（期望 RGBA）" % img.mode)
    a = img.getchannel("A")
    mx = max(a.getdata())
    ok &= _say(mx >= 240, name, "形体峰值 α=%d（期望 ≥240）" % mx)
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 100)
    print("M52 · 情景回想页 · 素材模块（`x_ui_rp_*` 11 件，程序化生成）")
    print("  输出目录 : %s" % OUT)
    print("  调色板   : %s（唯一色值来源，运行时读取）" % os.path.relpath(PALETTE, UI_GROUP))
    print("  基础工具 : import m50_make_gallery_thumbs（同一套 tint/rr_mask/ring_mask/glow/页码键）")
    print("=" * 100)

    ok_all, rows, built = True, [], build_assets()
    for name, img in built.items():
        size = chrome_size(name)
        assert img.size == size, "%s 尺寸 %s != %s" % (name, img.size, size)
        p = os.path.join(OUT, name)
        img.save(p, optimize=True, compress_level=9)
        rows.append((name, size, os.path.getsize(p)))
        ok_all &= verify(name, img, size)

    # 三态互异自证（族语言：on 明显更蓝更亮）
    print("-" * 100)
    print("三态互异自证（逐组：off↔over、off↔on 差异像素 > 100）：")
    for grp in ("x_ui_rp_cell", "x_ui_rp_pgprev", "x_ui_rp_pgnext"):
        a, o, n = built["%s_off.png" % grp], built["%s_over.png" % grp], built["%s_on.png" % grp]
        d1, d2 = diff_px(a, o), diff_px(a, n)
        ok_all &= _say(d1 > 100 and d2 > 100, grp + " 三态互异",
                       "off↔over %d px ｜ off↔on %d px" % (d1, d2))

    print("-" * 100)
    print("生成清单（文件名 / 尺寸 / 模式 / 字节）：")
    for name, size, b in rows:
        print("  %-32s %dx%d RGBA %7d B" % (name, size[0], size[1], b))
    print("  合计 %d 件 ｜ %d B" % (len(rows), sum(b for _n, _s, b in rows)))
    print("  md5（逐件，供数据侧与审查对账）：")
    for name, _s, _b in rows:
        with open(os.path.join(OUT, name), "rb") as f:
            print("    %-32s %s" % (name, hashlib.md5(f.read()).hexdigest()))
    print("=" * 100)
    print("★ 口径登记（如实，不得声称已生效）：")
    print("  · `x_ui_rp_mv_thumb.png` 上烘的是**静态 ▶ 图形**（表示「这是可播项」的占位标记）；")
    print("    「播放中」标记属运行期（参考件 §6.3-5 缺口），本作无音频/视频代码 ⇒ 留编程组。")
    print("  · 栏位内差分键复用 M2 的 `x_ui_gal_vprev/vnext_*`（本脚本不重复出件）；")
    print("    页码键与 M2/M3 同形（复用 m50 的 build_pg_btn 绘制，落盘为本模块前缀）。")
    print("=" * 100)
    print("RESULT=%s" % ("OK %d 件全部写出且自证通过" % len(rows) if ok_all else "NG 有自证未过（见上）"))
    print("★ 提醒：`layout\\screens\\38_replay.json` 才是几何真相源；本脚本重跑只覆盖这 %d 张 PNG。" % len(rows))
    print("=" * 100)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

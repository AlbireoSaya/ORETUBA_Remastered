# -*- coding: utf-8 -*-
r"""UI 组 · M11 —— 从 AI 生图素材派生新资产（可复跑、幂等）

依据
----
- 用户 2026-09-20 指令：「**彻底坚决使用它们代替老的素材**」。
- 画布基线 1920×1080（`..\00_项目总纲.md` D1 修订注·画布基线（第三条））。

产出（全部落在 `UI组\krkr\assets\ui\`，前缀 `x_gen_`）
------------------------------------------------------
| 源（`生图入料\生成结果\`） | 目标产物 | 变换 |
| --- | --- | --- |
| `功能图标.png` 1536×1024 RGBA | `x_gen_icon_01..09_*.png`（9 件） | **M22 重做**：整图 ×**0.685547** 一次缩放 → 3×3 **等分**网格切分（每件 351×234） |
| `对话框.png` 1672×941 RGBA | `x_gen_dialog.png` | 整体缩到宽 1680（**放大 1.0048×**，见下）。**M22 起不再改动本件**（保留，供 M23 切换引用） |
| `流程图的章节方框.png` 1672×941 RGBA | `x_gen_flownode_1..4_*.png`（4 件） | **M22 重做**：整图 ×**0.491228** 一次缩放 → 按三个局部极小 y=240/468/696 切 4 条带（各件尺寸不同，**倍率相同**） |
| `Fragment.png` 1672×941 RGB | `x_gen_fragpage.png` | 整幅缩到 1920×1080（**放大 1.1483×**，用户明确授权超分/改分辨率） |
| `鉴赏UI.png` 1672×940 RGB | `x_gen_gallerypage.png` | 整幅缩到 1920×1080（**放大 1.1483×**，同上授权） |
| `资源组\美术统一_超分\CG背景\bg63.png` 2904×1440 | `x_bg_system.png` | 中心裁 2560×1440 → 缩到 1920×1080（**0.75× 下采样**） |

M20 追加（用户 2026-09-20 重导素材，**真 alpha / RGBA**）
--------------------------------------------------------
| 源（`生图入料\生成结果\`） | 目标产物 | 变换 |
| --- | --- | --- |
| `游戏logo重置.png` 1697×927 **RGBA** | `x_gen_logo.png`（1 件） | alpha 包围盒(th=8) 裁紧 → 等比缩到宽 **900**（下采样 0.5386×） |
| `系统屏底图重置.png` 1254×1254 **RGBA** | `x_gen_menu_{1..7}_{start,continue,load,flowchart,extra,config,exit}.png` + 同名 `_on.png`（**14 件**） | **M22 重做**：整图 ×**0.70** 一次缩放 → 2 列 × 7 行**统一网格**切分（每件 439×121） |

M22 追加（用户 2026-09-20 根因指令：**「多个素材放进一张图」的压缩素材必须先整图统一缩放、再按网格切分**）
------------------------------------------------------------------------------------------------------
此前 M11/M17/M20 对**每个元素单独裁到 alpha 包围盒、再逐个归一化**，等于给每个元素施加**不同倍率**
（实测 9 个图标 0.762×–1.116×、7 个菜单 0.650×–0.721×、4 条方框 0.970×–1.007×），**相对大小被破坏**。
M22 三件一律改为：**① 定一个件内共用的 k → ② 用 LANCZOS 把整张源图按 k 缩放一次 → ③ 再按网格切分**
（切分线同样 ×k）。**禁止对切出来的元素再单独缩放**。

| 源 | k | 网格 | 产物 |
| --- | --- | --- | --- |
| `功能图标.png` | 0.685547 | 3×3 等分（缩放后 1053×702，格 351×234） | `x_gen_icon_01..09_*.png`，**9 件同尺寸** |
| `系统屏底图重置.png` | 0.70 | 2 列 × 7 行统一网格（缩放后 878×878，格 439×121，原点 y=15） | `x_gen_menu_1..7_*[_on].png`，**14 件同尺寸** |
| `流程图的章节方框.png` | 0.491228 | 按局部极小 y=240/468/696 切 4 条带 → 每条带内取 alpha 包围盒 | `x_gen_flownode_1..4_*.png`，尺寸各异（源本就不同）、**倍率相同** |
| `暂定对话框.png` | 1.0 | alpha>64 包围盒裁切 | `x_gen_dialog2.png` 1628×319（**新增**，旧 `x_gen_dialog.png` 保留不删） |

⛔ 已作废（**只登记，本脚本不再读取、不再产出**）
--------------------------------------------------
`俺翼logo.png`（1697×927 RGB）与 `系统屏底图.png`（1254×1254 RGB）的棋盘格
**是烘焙进像素的（假透明）**，非真 alpha。主代理已试过 5 种去背算法全部失败
（证据 `UI组\_工作\M10_证据\prev_dark_logo.png`：棋盘残留 + 羽毛被掏空）。
**用户已于 2026-09-20 重新导出为真 alpha 的 `游戏logo重置.png` / `系统屏底图重置.png`**
（实测 p90=253 / p99=254，RGBA），上表两行即其派生；旧的两张**不再读取**。

几何
----
`_工作\M20_生成几何.json` —— 全部矩形由脚本从像素**实测**（alpha 包围盒 / 行·列投影 /
亮度投影的局部极小 + 连续性分组），坐标以**输出图**为准。
★ M20 起本脚本的几何输出**改写到 `_工作\M20_生成几何.json`**（含 M11 各段 + M20 的
`logo` / `menu`）；M11 时代的 `_工作\M11_生成几何.json` 已**冻结**，本脚本不再改写它。
★ M22 起**另写一份** `_工作\M22_生成几何.json`（供 M23 直接消费）：含
`icons`（9 件共同尺寸 + k + 网格原点）/ `menu`（14 件共同尺寸 + k + **每格内容包围盒**，
供 M23 做「按内容右边缘对齐」）/ `flownodes`（4 件各自尺寸 + k + 源行区间）/
`dialog2`（裁切后尺寸 + 名字框矩形 + 正文区矩形）。`M20_生成几何.json` 的
`icons`/`menu`/`flownode` 三段同时被更新为 M22 口径（同一份数据，两个落点）。
证据：`_工作\M11_证据\`（M11 各件）+ `_工作\M20_证据\`（M20 的 logo / 菜单叠加预览）
+ `_工作\M22_证据\`（M22 接触印相表 sheet_*、网格叠加、对话框红线叠加），均为红线叠加图，
供目视核对。

纪律
----
- **源素材只读**：`生图入料\生成结果\` 与 `资源组\` 全程零写入（只在内存副本上裁/缩）。
- 测不准就如实报告，**不填估计值**。

复跑：`export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" && python 工具/prep_generated.py`
"""
from __future__ import annotations

import os
import sys
import json
import math

from PIL import Image, ImageDraw

ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UI = os.path.join(ROOT, "UI组")
GEN = os.path.join(UI, "生图入料", "生成结果")
SRC2 = os.path.join(ROOT, "资源组", "美术统一_超分")
OUT = os.path.join(UI, "krkr", "assets", "ui")
WORK = os.path.join(UI, "_工作")
EVID = os.path.join(WORK, "M11_证据")
EVID20 = os.path.join(WORK, "M20_证据")
EVID22 = os.path.join(WORK, "M22_证据")

LOG = []
GEOM = {}
GEOM22 = {}

# M22：旧（逐件归一化）倍率台账，供「旧 vs 新」对照
OLD_SCALES = {}


def log(m):
    print(m)
    LOG.append(m)


# ---------------------------------------------------------------- 基础工具

def lum(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000


def blueness(p):
    return p[2] - max(p[0], p[1])


def groups_from_positions(pos, gap):
    """把升序位置列表按间隔 gap 分组，返回 [(start, end), ...]。"""
    out, s, prev = [], None, None
    for v in pos:
        if s is None:
            s = v
        elif v - prev > gap:
            out.append((s, prev))
            s = v
        prev = v
    if s is not None:
        out.append((s, prev))
    return out


def minima_positions(vals, span, depth):
    """局部极小位置：vals[i] 比左右各 span 处都低 depth 以上。"""
    return [i for i in range(span, len(vals) - span)
            if vals[i] <= vals[i - span] - depth and vals[i] <= vals[i + span] - depth]


def band_minima_groups(vals, span, depth, gap=8):
    """局部极小 -> 描边组 [(start,end), ...]。"""
    return groups_from_positions(minima_positions(vals, span, depth), gap)


def profile_h(px, y0, y1, x0, x1):
    """纵向平均亮度剖面（用于找**竖直**描边）：x 索引。"""
    n = y1 - y0
    return [sum(lum(px[x, y]) for y in range(y0, y1)) // n for x in range(x0, x1)]


def profile_v(px, x0, x1, y0, y1):
    """横向平均亮度剖面（用于找**水平**描边）：y 索引。"""
    n = x1 - x0
    return [sum(lum(px[x, y]) for x in range(x0, x1)) // n for y in range(y0, y1)]


def pick(groups, lo, hi, offset=0):
    """取 start ∈ [lo,hi] 的组（offset 用于剖面起点不为 0 的情况）。"""
    hit = [g for g in groups if lo <= g[0] + offset and g[1] + offset <= hi]
    return hit[0] if hit else None


def pick_last(groups, lo, hi, offset=0):
    hit = [g for g in groups if lo <= g[0] + offset and g[1] + offset <= hi]
    return hit[-1] if hit else None


def split_smallest(groups, n):
    """把描边组切成 n 块，切在**最小的 n-1 个组间间隔**处。

    网格场景里「格内两描边的间隔」与「格与格之间的间隔」大小关系随方向而异
    （Fragment 行：格内 70 > 格间 12；Fragment 列：格内 24 < 高光距 258），
    但「格间间隔恒为最小」这一条在两种方向上都不变，故按最小间隔切分最稳。
    """
    if len(groups) < n:
        return [groups]
    gaps = [(groups[i + 1][0] - groups[i][1], i) for i in range(len(groups) - 1)]
    cut = set(i for _, i in sorted(gaps)[:n - 1])
    out, cur = [], [groups[0]]
    for i, g in enumerate(groups[1:]):
        if i in cut:
            out.append(cur)
            cur = [g]
        else:
            cur.append(g)
    out.append(cur)
    return out


def alpha_bbox(im, box=None, th=8):
    """alpha 包围盒（阈值 th）。返回 (x0,y0,x1,y1) 半开区间。"""
    a = im.getchannel("A")
    if box:
        a = a.crop(box)
        bb = a.point(lambda v: 255 if v >= th else 0).getbbox()
        if bb is None:
            return None
        return (bb[0] + box[0], bb[1] + box[1], bb[2] + box[0], bb[3] + box[1])
    return a.point(lambda v: 255 if v >= th else 0).getbbox()


def rct(x0, y0, x1, y1):
    """半开区间 -> [x, y, w, h]（整数）。"""
    return [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]


def scale_rect(rect, sx, sy):
    return [int(round(rect[0] * sx)), int(round(rect[1] * sy)),
            int(round(rect[2] * sx)), int(round(rect[3] * sy))]


def checker(size, tile=16):
    im = Image.new("RGB", size, (128, 128, 128))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if ((x // tile) + (y // tile)) % 2:
                d.rectangle([x, y, x + tile - 1, y + tile - 1], fill=(168, 168, 168))
    return im


def overlay(img, rects, path, labels=None, color=(255, 0, 0), width=3):
    """把矩形用红线画在图上（透明图垫棋盘底），保存到 path。"""
    base = img.convert("RGBA")
    bg = checker(base.size).convert("RGBA")
    bg.alpha_composite(base)
    d = ImageDraw.Draw(bg)
    for i, r in enumerate(rects):
        x, y, w, h = r
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=color, width=width)
        if labels:
            d.text((x + 4, y + 3), labels[i], fill=(255, 40, 40))
    bg.convert("RGB").save(path)
    log("证据 -> %s" % path)


# ================================================================ M22 统一缩放
# 用户 2026-09-20 根因指令：「多个素材放进一张图」的压缩素材**不得直接使用**，须
# ① 整图按同一倍率 k 缩放一次 → ② 再按网格切分。**禁止对切出的元素再单独缩放**
#（此前逐件归一化导致每个元素倍率不同、相对大小失真）。

def uniform_scale(src, k, tag=""):
    """整张源图按同一倍率 k 缩放**一次**（LANCZOS）。返回 (scaled, k_actual, size)。"""
    W, H = src.size
    tw, th_ = max(1, int(round(W * k))), max(1, int(round(H * k)))
    out = src.resize((tw, th_), Image.LANCZOS)
    log("  [统一缩放%s] 整图 %dx%d ×%.6f -> %dx%d（一次缩放，之后只切不再缩）"
        % (tag, W, H, k, tw, th_))
    return out, k, (tw, th_)


def bbox_in_cell(scaled, cell, th=8):
    """格内 alpha 包围盒，坐标**相对该格左上角**；全透明返回 None。"""
    bb = alpha_bbox(scaled, cell, th=th)
    if bb is None:
        return None
    return [bb[0] - cell[0], bb[1] - cell[1], bb[2] - bb[0], bb[3] - bb[1]]


def fit_uniform_grid(content_bands, k, n, y0_src):
    """求 (y0, ch)：**统一行高** ch + **统一原点** y0，使 n 行内容全部落在各自格内。

    content_bands: 源坐标下的 n 个半开区间 [top, bottom)；y0_src: 期望的网格起点（源坐标）。
    缩放后源像素 [a,b) 覆盖的行是 floor(a·k) .. ceil(b·k)-1（**保守取整**，避免半像素泄漏
    到相邻格——用 round 会把跨界的那一行算进错误的格）。格用半开区间 [y0+i·ch, y0+(i+1)·ch)。
    返回 (y0, ch)；无解返回 (None, None)。
    """
    ys = [(int(math.floor(b[0] * k)), int(math.ceil(b[1] * k))) for b in content_bands]
    # 被内容占据的缩放行（半开区间展开）；**格边界必须落在空行上**，否则会把上一行的
    # 内容切一丝到下一格里（实测：ch 取最大时会这样，污染 M23 用的 content_bbox）
    occupied = set()
    for (t, e) in ys:
        occupied.update(range(t, e))
    want = int(round(y0_src * k))
    cands = []
    for y0 in range(0, 96):
        for ch in range(1, 320):
            if not all(y0 + i * ch <= t and y0 + (i + 1) * ch >= b
                       for i, (t, b) in enumerate(ys)):
                continue
            if any((y0 + i * ch) in occupied for i in range(1, len(ys))):
                continue
            cands.append((y0, ch))
    if not cands:
        return None, None
    # 先取最大行高（格尽量大），同高时取原点最接近期望值的
    best = max(cands, key=lambda c: (c[1], -abs(c[0] - want)))
    return best


def old_scales_of(builder, values):
    """登记「旧（逐件归一化）倍率」台账。"""
    OLD_SCALES[builder] = list(values)


def ratio_line(name, vals):
    lo, hi = min(vals), max(vals)
    return ("%s：旧倍率 %.4f–%.4f（最大/最小 = %.3f）" % (name, lo, hi, hi / lo))


def contact_sheet(entries, path, cell_w, cell_h, cols, bg=(16, 20, 28), label_h=26):
    """等间距接触印相表：entries = [(file, caption)]，图**按原尺寸 1:1 居中**摆放。"""
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * (cell_h + label_h)), bg)
    d = ImageDraw.Draw(sheet)
    for i, (f, cap) in enumerate(entries):
        im = Image.open(f).convert("RGBA")
        bgc = checker((cell_w - 8, cell_h - 8))
        bgc.paste(im.convert("RGB"), ((cell_w - 8 - im.size[0]) // 2, (cell_h - 8 - im.size[1]) // 2),
                  im.getchannel("A"))
        cx, cy = (i % cols) * cell_w, (i // cols) * (cell_h + label_h)
        sheet.paste(bgc, (cx + 4, cy + 4))
        d.text((cx + 6, cy + cell_h + 4), cap, fill=(210, 220, 240))
    sheet.save(path)
    log("证据 -> %s" % path)


# ---------------------------------------------------------------- ① 功能图标

ICON_SEM = ["qsave", "qload", "skip", "prev", "save", "load", "config", "close", "repeat"]
# M22：单元格 = (3t, 2t)，取 t=117 ⇒ 351×234 ⇒ 3×3 网格整体 1053×702 = 画布 1080 的 **65.0%**（要求 60–70%）。
#   k = 351 / 512 = 0.685547（源单元格 512×341.333）；取 60–70% 区间的**中点 65%**。
#   该 k 下 1536k = 1053、1024k = 702 均为 3 的倍数 ⇒ 三格等宽等高，**9 件尺寸完全相同**。
ICON_K = 351.0 / 512.0


def build_icons():
    src = Image.open(os.path.join(GEN, "功能图标.png")).convert("RGBA")
    W, H = src.size
    assert (W, H) == (1536, 1024), src.size
    log("\n--- ① 功能图标.png %dx%d RGBA -> 9 件（M22 统一缩放）---" % (W, H))
    log("k = %.6f（依据：3×3 网格整体高 %.1f px = 画布 1080 的 %.1f%%，取 60–70%% 区间中点）"
        % (ICON_K, 1024 * ICON_K, 1024 * ICON_K / 1080 * 100))

    scaled, k, ssz = uniform_scale(src, ICON_K, "图标")
    cw, ch = ssz[0] // 3, ssz[1] // 3
    log("  3×3 等分网格：格 %dx%d，网格整体 %dx%d（余数 %d x %d 像素丢弃在右/下）"
        % (cw, ch, cw * 3, ch * 3, ssz[0] - cw * 3, ssz[1] - ch * 3))
    log("  旧做法倍率（逐件归一化到宽 192）：见下对照")

    items, warn, old_scales = [], [], []
    for r in range(3):
        for c in range(3):
            idx = r * 3 + c
            cell = (c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)
            out = scaled.crop(cell)
            assert out.size == (cw, ch)
            name = "x_gen_icon_%02d_%s.png" % (idx + 1, ICON_SEM[idx])
            out.save(os.path.join(OUT, name))
            cb = bbox_in_cell(scaled, cell, th=8)
            if cb is None:
                warn.append("格 %d 全透明" % (idx + 1))
            else:
                if cb[0] <= 1 or cb[1] <= 1 or cb[0] + cb[2] >= cw - 1 or cb[1] + cb[3] >= ch - 1:
                    warn.append("格 %d 的 alpha 包围盒贴到格边 %s（可能被网格切到）" % (idx + 1, cb))
            # 旧倍率（对照用）：旧脚本把每格裁紧后缩到宽 192
            ob = alpha_bbox(src, box=(
                round(W * c / 3), round(H * r / 3),
                round(W * (c + 1) / 3), round(H * (r + 1) / 3)), th=8)
            ow = ob[2] - ob[0]
            old_scales.append(192.0 / ow)
            log("%-30s 格(%d,%d) %dx%d  [统一 k=%.6f，未再单独缩放]  内容(格内) %s  %d B"
                % (name, c, r, cw, ch, k, cb, os.path.getsize(os.path.join(OUT, name))))
            items.append({"index": idx + 1, "file": name, "semantic": ICON_SEM[idx],
                          "size": [cw, ch], "cell": list(cell),
                          "content_bbox_in_cell": cb})
    for w in warn:
        log("!! %s" % w)
    old_scales_of("icons", old_scales)
    log("  " + ratio_line("图标", old_scales) + "  → 新：9 件**同一 k = %.6f**（极差 0）" % k)

    grid = {"source_size": [W, H], "scaled_size": list(ssz), "cols": 3, "rows": 3,
            "origin": [0, 0], "cell": [cw, ch], "k": round(k, 6),
            "grid_size": [cw * 3, ch * 3],
            "grid_height_pct_of_1080": round(ch * 3 / 1080 * 100, 1),
            "note": "整图按 k 缩放一次后 3×3 等分；9 件尺寸完全相同 %dx%d" % (cw, ch)}
    GEOM["icons"] = items
    GEOM["icons_grid"] = grid
    GEOM22["icons"] = {"k": round(k, 6), "source_size": [W, H], "scaled_size": list(ssz),
                       "grid": grid, "items": items,
                       "old_scale_range": [round(min(old_scales), 4), round(max(old_scales), 4)]}
    contact_sheet([(os.path.join(OUT, it["file"]),
                    "%s %s %dx%d" % (it["file"], it["semantic"], it["size"][0], it["size"][1]))
                   for it in items],
                  os.path.join(EVID22, "sheet_icons.png"), 400, 270, 3)


# ---------------------------------------------------------------- ② 对话框

def build_dialog():
    src = Image.open(os.path.join(GEN, "对话框.png")).convert("RGBA")
    W, H = src.size
    assert (W, H) == (1672, 941), src.size
    TW = 1680
    TH = int(round(H * TW / W))                       # 945
    out = src.resize((TW, TH), Image.LANCZOS)
    out.save(os.path.join(OUT, "x_gen_dialog.png"))
    sx, sy = TW / W, TH / H
    log("\n--- ② 对话框.png %dx%d RGBA -> x_gen_dialog.png %dx%d（放大 %.4f×%.4f，用户授权）---"
        % (W, H, TW, TH, sx, sy))

    px = src.load()
    # 竖直描边：在带内取 x 方向平均亮度剖面的局部极小
    nb_v = band_minima_groups(profile_h(px, 250, 346, 0, W), 4, 6)
    # 水平描边
    nb_h = band_minima_groups(profile_v(px, 150, 601, 0, H), 4, 6)
    bd_v = band_minima_groups(profile_h(px, 360, 651, 0, W), 4, 6)
    bd_h = band_minima_groups(profile_v(px, 700, 1501, 0, H), 4, 6)
    log("名字框带内竖直描边 %s / 水平描边 %s" % (nb_v, nb_h))
    log("正文区带内竖直描边 %s / 水平描边 %s" % (bd_v, bd_h))

    nb_l = pick(nb_v, 60, 220)
    nb_r = pick_last(nb_v, 500, 720)
    nb_t = pick(nb_h, 200, 300)
    nb_b = pick_last(nb_h, 320, 400)
    bd_l = pick(bd_v, 20, 130)
    bd_r = pick_last(bd_v, 1520, 1660)
    bd_t = pick(bd_h, 280, 350)
    bd_b = pick_last(bd_h, 620, 700)

    def rect_from(l, r, t, b, name):
        if None in (l, r, t, b):
            log("!! %s 有描边未测到：l=%s r=%s t=%s b=%s —— 如实报告，不填估计值"
                % (name, l, r, t, b))
            return None
        outer = rct(l[0], t[0], r[1] + 1, b[1] + 1)
        inner = rct(l[1] + 1, t[1] + 1, r[0], b[0])
        log("%s  描边 l=%s r=%s t=%s b=%s -> 外接 %s  内区 %s（原图坐标）"
            % (name, l, r, t, b, outer, inner))
        return {"outer": scale_rect(outer, sx, sy), "inner": scale_rect(inner, sx, sy)}

    namebox = rect_from(nb_l, nb_r, nb_t, nb_b, "名字框")
    text = rect_from(bd_l, bd_r, bd_t, bd_b, "正文区")

    rects, labels = [], []
    if namebox:
        rects.append(namebox["inner"]); labels.append("namebox.inner")
        rects.append(namebox["outer"]); labels.append("namebox.outer")
    if text:
        rects.append(text["inner"]); labels.append("text.inner")
        rects.append(text["outer"]); labels.append("text.outer")
    overlay(out, rects, os.path.join(EVID, "overlay_dialog.png"), labels)

    GEOM["dialog"] = {
        "image_size": [TW, TH],
        "coordinate_space": "asset-local（%d×%d；在 1920×1080 画布上的摆放由 M13/M14 决定）" % (TW, TH),
        "namebox": namebox,
        "text": text,
        "method": "亮度剖面的局部极小（span=4, depth=6）+ 连续性分组；"
                  "outer = 描边外沿包围盒，inner = 描边内沿（可绘字区）；坐标为输出图 1680×945 口径",
        "source_scale": [round(sx, 6), round(sy, 6)],
    }
    # 单独预览接触印相表
    sheet = Image.new("RGB", (TW, TH + 26), (16, 20, 28))
    bg = checker(out.size)
    bg.paste(out.convert("RGB"), (0, 0), out.getchannel("A"))
    sheet.paste(bg, (0, 0))
    d = ImageDraw.Draw(sheet)
    for r, lb in zip(rects, labels):
        d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], outline=(255, 0, 0), width=3)
        d.text((r[0] + 4, r[1] + 3), lb, fill=(255, 40, 40))
    d.text((6, TH + 6), "x_gen_dialog.png  %dx%d（红线 = 实测几何）" % out.size,
           fill=(210, 220, 240))
    sheet.save(os.path.join(EVID, "sheet_dialog.png"))
    log("证据 -> %s" % os.path.join(EVID, "sheet_dialog.png"))


# ---------------------------------------------------------------- ②b 新对话框（M22）

# 裁切后的两个矩形（坐标**相对裁切图左上角**，半开区间 -> [x, y, w, h]）。
# 实测方法见 `_工作\M22_报告.md`：alpha 逐行/逐列计数定名字框与窗体边界；亮度剖面局部极小定描边；
# 白亮像素(lum>=242/248)与局部对比度定雪花/羽毛装饰范围，据此把可写区内缩到装饰之外。
DIALOG2_BBOX_TH = 64
DIALOG2_NAMBOX_OUTER = [130, 12, 412, 74]     # x 130..542, y 12..86（上/下描边 y=12、86；右描边 x=542）
DIALOG2_NAMBOX_INNER = [185, 22, 345, 56]     # x 185..530, y 22..78（左界 185 避开名字框左上的雪花装饰）
DIALOG2_WIN_OUTER = [21, 60, 1596, 244]       # x 21..1617, y 60..304（窗体四边描边实测）
DIALOG2_TEXT_INNER = [100, 80, 940, 210]      # x 100..1040, y 80..290（左避羽毛 x≤85，右避雪花 x≥1050）


def build_dialog2():
    src = Image.open(os.path.join(GEN, "暂定对话框.png")).convert("RGBA")
    W, H = src.size
    log("\n--- ②b 暂定对话框.png %dx%d RGBA -> x_gen_dialog2.png ---" % (W, H))
    bb = alpha_bbox(src, th=DIALOG2_BBOX_TH)
    log("alpha>%d 包围盒 %s -> 窗体 %dx%d" % (DIALOG2_BBOX_TH, bb, bb[2] - bb[0], bb[3] - bb[1]))
    crop = src.crop(bb)
    cw, ch = crop.size
    k = 1.0
    if not (290 <= ch <= 320):
        k = 300.0 / ch
        crop = crop.resize((max(1, int(round(cw * k))), 300), Image.LANCZOS)
        cw, ch = crop.size
        log("!! 高度 %d 不在用户要求 290–320 内 —— 等比缩到高 300（k=%.6f）" % (bb[3] - bb[1], k))
    else:
        log("高度 %d ∈ [290,320] ⇒ **天然达标，k = 1.0**（不做任何缩放）" % ch)
    crop.save(os.path.join(OUT, "x_gen_dialog2.png"))
    log("-> %s  %dx%d  %d B" % (os.path.join(OUT, "x_gen_dialog2.png"), cw, ch,
                                os.path.getsize(os.path.join(OUT, "x_gen_dialog2.png"))))

    namebox = {"outer": list(DIALOG2_NAMBOX_OUTER), "inner": list(DIALOG2_NAMBOX_INNER)}
    text = {"outer": list(DIALOG2_WIN_OUTER), "inner": list(DIALOG2_TEXT_INNER)}
    for tag, r in (("名字框外接", namebox["outer"]), ("名字框内可写区", namebox["inner"]),
                   ("窗体", text["outer"]), ("正文可写区", text["inner"])):
        log("  %-12s [x %d..%d, y %d..%d]  %dx%d"
            % (tag, r[0], r[0] + r[2] - 1, r[1], r[1] + r[3] - 1, r[2], r[3]))
    # 一致性校验：内区必须含在外接之内
    for nm, o, i in (("名字框", namebox["outer"], namebox["inner"]),
                     ("窗体", text["outer"], text["inner"])):
        assert o[0] <= i[0] and o[1] <= i[1] \
            and i[0] + i[2] <= o[0] + o[2] and i[1] + i[3] <= o[1] + o[3], ("%s 内区越界" % nm)

    overlay(crop, [namebox["outer"], namebox["inner"], text["outer"], text["inner"]],
            os.path.join(EVID22, "overlay_dialog2.png"),
            ["namebox.outer", "namebox.inner", "text.outer", "text.inner"])

    GEOM22["dialog2"] = {
        "file": "x_gen_dialog2.png",
        "source": "生图入料/生成结果/暂定对话框.png",
        "source_size": [W, H], "source_mode": "RGBA",
        "bbox_th": DIALOG2_BBOX_TH, "bbox": list(bb),
        "size": [cw, ch], "k": round(k, 6),
        "coordinate_space": "asset-local（%d×%d，相对裁切图左上角；在 1920×1080 画布上的摆放由 M23 决定）"
                            % (cw, ch),
        "namebox": namebox, "text": text,
        "method": "alpha>%d 包围盒裁切；矩形由像素实测：alpha 逐行/逐列计数定名字框与窗体边界，"
                  "亮度剖面局部极小定描边，白亮像素与局部对比度定雪花/羽毛装饰范围，"
                  "可写区内缩到装饰之外" % DIALOG2_BBOX_TH,
        "note": "旧 x_gen_dialog.png（1680×946，含大片透明边距）**保留不删**，由 M23 决定切换引用",
    }


# ---------------------------------------------------------------- ③ 流程节点条

FLOW_SEM = ["normal", "badend", "important", "goodend"]
# M22：源行剖面在 y=240 / 468 / 696 取局部极小（491/413/491，从不归零——相邻条的柔光相互重叠），
#   故按这三个极小值切成 4 条带；每条带内再取 alpha 包围盒（去重叠）。
#   k 使**最高那条**在画布上约 110–130 px：最高条带内容高 228 ⇒ k = 112/228 = 0.491228，
#   输出高 108/112/112/111（最高 112 ∈ [110,130]），与 M14 版式已算好的「行槽 112」一致 ⇒ 可 1:1 摆放。
FLOW_CUTS = [21, 240, 468, 696, 921]
FLOW_K = 112.0 / 228.0


def build_flownodes():
    src = Image.open(os.path.join(GEN, "流程图的章节方框.png")).convert("RGBA")
    W, H = src.size
    assert (W, H) == (1672, 941), src.size
    a = src.getchannel("A")
    rowc = [sum(1 for x in range(W) if a.getpixel((x, y)) >= 200) for y in range(H)]
    solid = [y for y, c in enumerate(rowc) if c >= 400]
    bands = groups_from_positions(solid, 6)
    log("\n--- ③ 流程图的章节方框.png %dx%d RGBA -> 4 条（M22 统一缩放）---" % (W, H))
    log("alpha>=200 计数 >=400 的实心行段：%s（4 条带外的柔光重叠区）" % (bands,))
    log("行剖面在切点 y=240/468/696 的值：%s（局部极小，从不归零）"
        % [rowc[y] for y in (240, 468, 696)])
    if len(bands) != 4:
        log("!! 实心段数 = %d（期望 4）——如实报告" % len(bands))

    # ① 先在**源坐标**下按切点定 4 条带、逐带取 alpha 包围盒（去重叠）
    src_boxes = []
    for i in range(4):
        y0, y1 = FLOW_CUTS[i], FLOW_CUTS[i + 1]
        bb = alpha_bbox(src, (0, y0, W, y1), th=8)
        src_boxes.append(bb)
        log("  条带%d 源切窗 y %d..%d -> alpha 包围盒 %s（%dx%d）"
            % (i + 1, y0, y1, bb, bb[2] - bb[0], bb[3] - bb[1]))

    # ② 整图按同一个 k 缩放一次
    scaled, k, ssz = uniform_scale(src, FLOW_K, "方框")
    tallest = max(b[3] - b[1] for b in src_boxes)
    log("k = %.6f（依据：最高条带内容 %d px × k ≈ %.1f px，落在要求 110–130 px 内）"
        % (k, tallest, tallest * k))

    # ③ 再按（同样 ×k 的）切分线切分 —— 不再单独缩放
    items, old_scales = [], []
    for i, bb in enumerate(src_boxes):
        x0, y0 = int(round(bb[0] * k)), int(round(bb[1] * k))
        x1, y1 = int(round(bb[2] * k)), int(round(bb[3] * k))
        out = scaled.crop((x0, y0, x1, y1))
        name = "x_gen_flownode_%d_%s.png" % (i + 1, FLOW_SEM[i])
        out.save(os.path.join(OUT, name))
        old_scales.append(1152.0 / (bb[2] - bb[0]))
        log("%-30s 源 %4dx%-3d ×%.6f -> %4dx%-3d  [统一 k，未再单独缩放]  %d B"
            % (name, bb[2] - bb[0], bb[3] - bb[1], k, out.size[0], out.size[1],
               os.path.getsize(os.path.join(OUT, name))))
        items.append({"index": i + 1, "file": name, "semantic": FLOW_SEM[i],
                      "size": [out.size[0], out.size[1]],
                      "src_band": [FLOW_CUTS[i], FLOW_CUTS[i + 1]],
                      "src_alpha_bbox": list(bb), "k": round(k, 6)})
    old_scales_of("flownodes", old_scales)
    log("  " + ratio_line("方框", old_scales) + "  → 新：4 件**同一 k = %.6f**（极差 0）" % k)
    log("  输出高 %s（最高 %d ∈ [110,130]）；尺寸各异是**对的**（源里本来就不同），倍率相同"
        % ([it["size"][1] for it in items], max(it["size"][1] for it in items)))

    GEOM["flownode"] = items
    GEOM["flownode_note"] = ("整图按同一 k 缩放一次后，按源行剖面局部极小 y=240/468/696 切 4 条带，"
                             "每条带内在**源坐标**取 alpha 包围盒、再把该包围盒同样 ×k 后切分；"
                             "4 件倍率相同（k=%.6f），尺寸各异" % k)
    GEOM22["flownodes"] = {"k": round(k, 6), "source_size": [W, H], "scaled_size": list(ssz),
                           "cuts": FLOW_CUTS, "items": items,
                           "old_scale_range": [round(min(old_scales), 4), round(max(old_scales), 4)]}
    contact_sheet([(os.path.join(OUT, it["file"]),
                    "%s  %dx%d" % (it["file"], it["size"][0], it["size"][1])) for it in items],
                  os.path.join(EVID22, "sheet_flownodes.png"), 640, 150, 1)


# ---------------------------------------------------------------- ④ Fragment 整页

def build_fragpage():
    src = Image.open(os.path.join(GEN, "Fragment.png")).convert("RGB")
    W, H = src.size
    assert (W, H) == (1672, 941), src.size
    out = src.resize((1920, 1080), Image.LANCZOS)
    out.save(os.path.join(OUT, "x_gen_fragpage.png"))
    sx, sy = 1920 / W, 1080 / H
    log("\n--- ④ Fragment.png %dx%d RGB -> x_gen_fragpage.png 1920x1080（放大 %.4f×%.4f，用户授权）---"
        % (W, H, sx, sy))
    px = src.load()

    # 标题：y∈[25,80]（**不含** y=82 的面板顶边）内的深色像素包围盒
    xs, ys = [], []
    for y in range(25, 81):
        for x in range(20, 760):
            if lum(px[x, y]) < 190:
                xs.append(x); ys.append(y)
    title = rct(min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs else None
    log("标题包围盒（lum<190, y∈[25,80]）%s" % title)

    # 面板外框：四条长描边（最外两条竖直 / 最外两条水平）
    pv = band_minima_groups(profile_h(px, 100, 880, 0, W), 3, 5)
    ph = band_minima_groups(profile_v(px, 100, 1600, 0, H), 3, 4)
    pl, pr = (pv[0], pv[-1]) if len(pv) >= 2 else (None, None)
    pt, pb = (ph[0], ph[-1]) if len(ph) >= 2 else (None, None)
    log("面板外框描边：left=%s right=%s top=%s bottom=%s" % (pl, pr, pt, pb))
    panel = rct(pl[0], pt[0], pr[1] + 1, pb[1] + 1) if None not in (pl, pr, pt, pb) else None
    if panel is None:
        log("!! 面板外框有描边未测到 —— 如实报告")

    # 40 个格子：8 行 × 5 列
    #   行：格区 x∈[100,1600] 的横向亮度剖面 -> 描边（上/下交替），按最小间隔切成 8 块
    row_all = band_minima_groups(profile_v(px, 100, 1600, 0, H), 3, 4)
    row_strokes = [g for g in row_all if 100 <= g[0] and g[1] <= 880]   # 去面板上下外框
    rows = split_smallest(row_strokes, 8) if len(row_strokes) == 16 else []
    #   列：8 条行中线的**平均**亮度剖面 -> 描边（左/高光/右），按最小间隔切成 5 块
    cols_g = []
    if len(rows) == 8:
        ys = [g[0][0] + (g[-1][1] - g[0][0]) // 2 for g in rows]
        prof = [sum(lum(px[x, y]) for y in ys) // len(ys) for x in range(W)]
        col_all = band_minima_groups(prof, 3, 5)
        col_strokes = [g for g in col_all if 40 <= g[0] and g[1] <= 1640]  # 去面板左右外框
        log("行描边 %d 条 %s" % (len(row_strokes), row_strokes))
        log("列描边 %d 条 %s" % (len(col_strokes), col_strokes))
        cols_g = split_smallest(col_strokes, 5) if len(col_strokes) in (14, 15) else []
    log("行组 %d 组 %s" % (len(rows), [("y%d..%d" % (g[0][0], g[-1][1])) for g in rows]))
    log("列组 %d 组 %s" % (len(cols_g), [("x%d..%d" % (g[0][0], g[-1][1])) for g in cols_g]))

    cells = []
    if len(rows) == 8 and len(cols_g) == 5:
        cols = [(g[0][0], g[-1][1] + 1) for g in cols_g]
        rws = [(g[0][0], g[-1][1] + 1) for g in rows]
        for r in range(8):
            for c in range(5):
                cells.append(rct(cols[c][0], rws[r][0], cols[c][1], rws[r][1]))
        log("列区间 %s" % [("x%d..%d" % (c[0], c[1] - 1)) for c in cols])
        log("行区间 %s" % [("y%d..%d" % (r[0], r[1] - 1)) for r in rws])
    else:
        log("!! 格子描边组数不符（行 %d 组 / 列 %d 组，期望 8 / 5）—— 不生成 40 格几何，如实报告"
            % (len(rows), len(cols_g)))

    rects, labels = [], []
    if title:
        rects.append(scale_rect(title, sx, sy)); labels.append("title")
    if panel:
        rects.append(scale_rect(panel, sx, sy)); labels.append("panel")
    for i, c in enumerate(cells):
        rects.append(scale_rect(c, sx, sy)); labels.append("c%02d" % (i + 1))
    overlay(out, rects, os.path.join(EVID, "overlay_fragpage.png"), labels)

    GEOM["fragpage"] = {
        "image_size": [1920, 1080],
        "coordinate_space": "canvas（1920×1080 满幅）",
        "title": scale_rect(title, sx, sy) if title else None,
        "panel": scale_rect(panel, sx, sy) if panel else None,
        "cells": [scale_rect(c, sx, sy) for c in cells],
        "cells_layout": "5 列 × 8 行，行优先（index 0..39 = 第1行左→右，再第2行…）",
        "method": "亮度投影的局部极小 + 连续性分组：标题=深色像素(lum<190)包围盒；"
                  "面板外框=四条长描边；格子=格区横描边 16 条成 8 对、纵描边 15 条成 5 组三连（左/高光/右）",
        "source_scale": [sx, sy],
    }


# ---------------------------------------------------------------- ⑤ 鉴赏 UI 整页

def build_gallerypage():
    src = Image.open(os.path.join(GEN, "鉴赏UI.png")).convert("RGB")
    W, H = src.size
    assert (W, H) == (1672, 940), src.size
    out = src.resize((1920, 1080), Image.LANCZOS)
    out.save(os.path.join(OUT, "x_gen_gallerypage.png"))
    sx, sy = 1920 / W, 1080 / H
    log("\n--- ⑤ 鉴赏UI.png %dx%d RGB -> x_gen_gallerypage.png 1920x1080（放大 %.4f×%.4f，用户授权）---"
        % (W, H, sx, sy))
    px = src.load()
    pv_lb = band_minima_groups(profile_h(px, 110, 821, 0, W), 3, 4)
    pv_pv = band_minima_groups(profile_h(px, 110, 421, 0, W), 3, 4)
    ph_lb = band_minima_groups(profile_v(px, 100, 701, 0, H), 3, 4)
    # 预览框上沿改用较窄的 x 带，避开外层面板顶边在同高度产生的第二条暗线
    ph_pv = band_minima_groups(profile_v(px, 820, 951, 0, H), 3, 3)
    log("左框竖直描边 %s" % pv_lb)
    log("预览区竖直描边 %s" % pv_pv)
    log("左框水平描边 %d 条 %s" % (len(ph_lb), ph_lb))
    log("预览区水平描边 %s" % ph_pv)

    # 左侧 4 个选择框：左/右竖直描边各一条，水平描边 8 条**逐条成对**（上/下交替）
    lb_l = pick(pv_lb, 30, 90)
    lb_r = pick_last(pv_lb, 700, 770)
    left_boxes = []
    if lb_l and lb_r and len(ph_lb) == 8:
        for k in range(4):
            left_boxes.append(rct(lb_l[0], ph_lb[2 * k][0], lb_r[1] + 1, ph_lb[2 * k + 1][1] + 1))
    log("左侧框：l=%s r=%s 行描边 %d 条 -> %d 件" % (lb_l, lb_r, len(ph_lb), len(left_boxes)))

    # 右侧预览大框
    pv_l = pick(pv_pv, 760, 810)
    pv_r = pick_last(pv_pv, 1600, 1645)
    pv_t = pick(ph_pv, 80, 130)
    pv_b = pick_last(ph_pv, 420, 465)
    preview = (rct(pv_l[0], pv_t[0], pv_r[1] + 1, pv_b[1] + 1)
               if None not in (pv_l, pv_r, pv_t, pv_b) else None)
    log("预览框：l=%s r=%s t=%s b=%s -> %s" % (pv_l, pv_r, pv_t, pv_b, preview))
    if preview is None:
        log("!! 预览框有描边未测到 —— 如实报告")

    # 深色章节名条（暗填充包围盒）+ 其右侧细延伸线
    xs, ys = [], []
    for y in range(430, 520):
        for x in range(790, 1130):
            if lum(px[x, y]) <= 220:
                xs.append(x); ys.append(y)
    namebar = rct(min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs else None
    line = None
    if namebar:
        yc = namebar[1] + namebar[3] // 2
        xs2 = [x for x in range(namebar[0] + namebar[2], 1615) if lum(px[x, yc]) <= 240]
        if xs2:
            line = rct(min(xs2), yc - 2, max(xs2) + 1, yc + 3)
    log("章节名条 %s ；延伸线 %s" % (namebar, line))

    # 4 条浅色简介条（行内计数 >=500 的连续行段）
    rowc = [(y, sum(1 for x in range(850, 1570) if lum(px[x, y]) <= 239))
            for y in range(520, 830)]
    bbands = groups_from_positions([y for y, c in rowc if c >= 500], 6)
    intro_bars = []
    if len(bbands) == 4:
        exts = []
        for (y0, y1) in bbands:
            col = [x for x in range(850, 1580)
                   if sum(1 for y in range(y0, y1 + 1) if lum(px[x, y]) <= 239) >= 3]
            exts.append((min(col), max(col)))
        x0 = sorted(e[0] for e in exts)[len(exts) // 2]
        x1 = sorted(e[1] for e in exts)[len(exts) // 2]
        for (y0, y1) in bbands:
            intro_bars.append(rct(x0, y0, x1 + 1, y1 + 1))
        log("简介条：逐条 x 范围 %s -> 取中位 x %d..%d" % (exts, x0, x1))
    else:
        log("!! 简介条行段数 = %d（期望 4）—— 如实报告" % len(bbands))
    log("简介条行段 %s -> %d 件" % (bbands, len(intro_bars)))

    rects, labels = [], []
    for i, r in enumerate(left_boxes):
        rects.append(scale_rect(r, sx, sy)); labels.append("left%d" % (i + 1))
    if preview:
        rects.append(scale_rect(preview, sx, sy)); labels.append("preview")
    if namebar:
        rects.append(scale_rect(namebar, sx, sy)); labels.append("namebar")
    if line:
        rects.append(scale_rect(line, sx, sy)); labels.append("namebar.line")
    for i, r in enumerate(intro_bars):
        rects.append(scale_rect(r, sx, sy)); labels.append("intro%d" % (i + 1))
    overlay(out, rects, os.path.join(EVID, "overlay_gallerypage.png"), labels)

    GEOM["gallerypage"] = {
        "image_size": [1920, 1080],
        "coordinate_space": "canvas（1920×1080 满幅）",
        "left_boxes": [scale_rect(r, sx, sy) for r in left_boxes],
        "preview": scale_rect(preview, sx, sy) if preview else None,
        "namebar": scale_rect(namebar, sx, sy) if namebar else None,
        "namebar_line": scale_rect(line, sx, sy) if line else None,
        "intro_bars": [scale_rect(r, sx, sy) for r in intro_bars],
        "method": "亮度剖面的局部极小 + 连续性分组：左 4 框=左右竖直描边各一条 × 水平描边 8 条"
                  "按「组间间隔 > 最大间隔/2」两两成对；预览框=四条描边（上沿窗口自 y=92 起，"
                  "避开外层面板顶边）；章节名条=暗填充(lum<=220)包围盒；"
                  "简介条=行内计数(lum<=239, x∈[850,1570]) >=500 的 4 个连续行段，"
                  "x 范围取 4 条的中位（4 条为同一设计行）",
        "source_scale": [round(sx, 6), round(sy, 6)],
    }


# ---------------------------------------------------------------- ⑥ 系统屏满幅背景

def build_bg_system():
    p = os.path.join(SRC2, "CG背景", "bg63.png")
    src = Image.open(p).convert("RGB")
    W, H = src.size
    log("\n--- ⑥ bg63.png %dx%d -> x_bg_system.png（裁 16:9 再缩到 1920×1080）---" % (W, H))
    ch = H
    cw = int(round(H * 16 / 9))                    # 2560
    x0 = (W - cw) // 2
    crop = src.crop((x0, 0, x0 + cw, ch))
    out = crop.resize((1920, 1080), Image.LANCZOS)
    out.save(os.path.join(OUT, "x_bg_system.png"))
    log("源 %dx%d（宽高比 %.4f）-> 中心裁 %d×%d 于 x=%d..%d（裁掉两侧各 %d px）"
        " -> 缩到 1920×1080（%.4f× 下采样） %d B"
        % (W, H, W / H, cw, ch, x0, x0 + cw, x0,
           1920 / cw, os.path.getsize(os.path.join(OUT, "x_bg_system.png"))))
    GEOM["bg_system"] = {
        "file": "x_bg_system.png", "image_size": [1920, 1080],
        "source": "资源组/美术统一_超分/CG背景/bg63.png",
        "source_size": [W, H], "source_aspect": round(W / H, 4),
        "crop_box": [x0, 0, x0 + cw, ch], "crop_size": [cw, ch],
        "scale": round(1920 / cw, 4),
        "note": "源宽高比 %.4f > 16:9 → 裁两侧取 2560×1440 中心区 → 0.75× 下采样到 1920×1080；"
                "用于系统屏满幅背景、不留黑边（用户明确要求）" % (W / H),
    }


# ---------------------------------------------------------------- ⑦ 游戏 logo（M20）

# 目标宽：1920 画布左上角摆放。依据（见 M20 报告）：
#   ① 源裁紧后 1671×589，宽高比 2.837；② M9 旧 logo 为 723×252（宽 = 画布 37.7%）；
#   ③ 放大到 900（画布 46.9%）后高 317，右缘 x=960 仍在中线以内，与右侧菜单（左缘 ≥1548）无重叠。
LOGO_W = 900


def build_logo():
    src = Image.open(os.path.join(GEN, "游戏logo重置.png")).convert("RGBA")
    W, H = src.size
    assert (W, H) == (1697, 927), src.size
    log("\n--- ⑦ 游戏logo重置.png %dx%d RGBA -> x_gen_logo.png ---" % (W, H))
    bb = alpha_bbox(src, th=8)
    if bb is None:
        log("!! alpha 包围盒为空 —— 如实报告，不产出")
        return
    tight = src.crop(bb)
    tw = LOGO_W
    th_ = max(1, int(round(tight.size[1] * tw / tight.size[0])))
    out = tight.resize((tw, th_), Image.LANCZOS)
    out.save(os.path.join(OUT, "x_gen_logo.png"))
    sx = tw / tight.size[0]
    dirs = "放大 %.4f×" % sx if sx > 1.0005 else "下采样 %.4f×" % sx
    log("alpha 包围盒(th=8) %s -> 裁紧 %dx%d -> %dx%d [%s] %d B"
        % (bb, tight.size[0], tight.size[1], tw, th_, dirs,
           os.path.getsize(os.path.join(OUT, "x_gen_logo.png"))))
    # 边缘检查：内容是否贴到源图边界（贴边 = 原画可能被裁）
    if bb[0] <= 0 or bb[1] <= 0 or bb[2] >= W or bb[3] >= H:
        log("!! alpha 包围盒贴到源图边界 %s（原画可能在导出时被裁）—— 如实登记" % (bb,))
    rects = [[bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]]]
    overlay(src, rects, os.path.join(EVID20, "overlay_logo.png"), ["logo alpha bbox th=8"])
    GEOM["logo"] = {
        "file": "x_gen_logo.png",
        "source": "生图入料/生成结果/游戏logo重置.png",
        "source_size": [W, H], "source_mode": "RGBA",
        "alpha_bbox_th8": list(bb),
        "tight_size": [tight.size[0], tight.size[1]],
        "size": [tw, th_], "scale": round(sx, 6), "transform": dirs,
        "note": "按 alpha 包围盒(th=8)裁紧后等比缩到宽 %d（源裁紧 %dx%d，宽高比 %.3f）"
                % (tw, tight.size[0], tight.size[1], tight.size[0] / tight.size[1]),
    }


# ---------------------------------------------------------------- ⑧ 系统屏菜单按钮（M20）

# 语义顺序**按图上顺序**（左列常态自上而下）：
#   1 开始游戏 START / 2 继续游戏 CONTINUE / 3 读取存档 LOAD / 4 流程图 FLOWCHART
#   / 5 鉴赏 EXTRA / 6 环境设定 CONFIG / 7 退出游戏 EXIT
MENU_SEM = ["start", "continue", "load", "flowchart", "extra", "config", "exit"]
MENU_CN = ["开始游戏", "继续游戏", "读取存档", "流程图", "鉴赏", "环境设定", "退出游戏"]
MENU_EN = ["START", "CONTINUE", "LOAD", "FLOWCHART", "EXTRA", "CONFIG", "EXIT"]

# M22：整图统一 k = 0.70。依据：
#   ① 沿用 M20 已实机验证的按钮内容高（旧 104 px）——新 k 得内容高 155×0.70 ≈ 108.5 px（+4%），
#      中文烘焙字随之略大，可读性不降反升；
#   ② 缩放后源图 878×878 ⇒ 2 列各 439、行高由「内容全部落格」约束解得 121 ⇒ 网格总高
#      15 + 7×121 = 862 ≤ 1080，**7 项竖排可 1:1 放进画布**（旧做法需把每项缩到高 104）；
#   ③ 源行的**真实间距不等**（实测行内容段 23–177 / 197–351 / 373–529 / 548–707 / 731–877 /
#      885–1040 / 1060–1219，第 5–6 行间隙仅 8 px）⇒ **等分 2×7 会切到第 6、7 项内容**
#      （已实测坐实，见 `_工作\M22_证据\menu_equalgrid.png`）。故行网格取「统一行高 + 统一原点
#      y0=21（源坐标）」并**逐行校验内容全部落格**；列网格用等分 2 分（列间隙 570–734，安全）。
MENU_K = 0.70
MENU_Y0_SRC = 21.0     # 网格起点（源坐标）：上沿留白，使第 1 行内容（源 y 23）落在格内

def _alpha_bands(cnt, minv=1, gap=3):
    """把「计数 >= minv」的连续段分组（允许 gap 个空洞），返回 [(start, end), ...]。"""
    out, s, prev = [], None, None
    for i, v in enumerate(cnt):
        if v >= minv:
            if s is None:
                s = i
            elif i - prev > gap:
                out.append((s, prev))
                s = i
            prev = i
    if s is not None:
        out.append((s, prev))
    return out


def build_menu():
    src = Image.open(os.path.join(GEN, "系统屏底图重置.png")).convert("RGBA")
    W, H = src.size
    assert (W, H) == (1254, 1254), src.size
    TH = 8
    ap = src.getchannel("A").point(lambda v: 255 if v >= TH else 0)
    px = ap.load()
    colc = [sum(1 for y in range(H) if px[x, y] >= TH) for x in range(W)]
    rowc = [sum(1 for x in range(W) if px[x, y] >= TH) for y in range(H)]
    cols = _alpha_bands(colc, 1, 3)
    rows = _alpha_bands(rowc, 1, 3)
    log("\n--- ⑧ 系统屏底图重置.png %dx%d RGBA -> 14 件（M22 统一缩放）---" % (W, H))
    log("列投影 alpha>0 段 %s（期望 2：左常态 / 右高亮）" % (cols,))
    log("行投影 alpha>0 段 %s（期望 7；间距不等，故不可等分）" % (rows,))
    if len(cols) != 2 or len(rows) != 7:
        log("!! 网格段数不符（列 %d / 行 %d，期望 2 / 7）—— 如实报告，不产出菜单件"
            % (len(cols), len(rows)))
        return
    if cols[0][1] >= cols[1][0]:
        log("!! 两列段重叠 %s —— 列分离失败，不产出" % (cols,))
        return

    # ① 整图按同一个 k 缩放一次
    scaled, k, ssz = uniform_scale(src, MENU_K, "菜单")
    # ② 行网格：统一行高 ch + 统一原点 y0，使 7 行内容全部落格（ch 取满足约束的最大整数）
    y0, ch = fit_uniform_grid(rows, k, 7, MENU_Y0_SRC)
    cw = ssz[0] // 2
    if ch is None:
        log("!! 找不到使 7 行内容全部落格的统一行高 —— 如实报告，不产出")
        return
    log("  列网格：等分 2 分，列界 [0, %d, %d]（源列间隙 %d–%d，安全）"
        % (cw, cw * 2, cols[0][1], cols[1][0]))
    log("  行网格：原点 y0=%d（源 y=%.0f×k），统一行高 ch=%d（源行高 ≈%.1f×k）"
        % (y0, MENU_Y0_SRC, ch, ch / k))
    for i, (ry0, ry1) in enumerate(rows):
        cell = (y0 + i * ch, y0 + (i + 1) * ch)
        # 保守取整：源 [ry0, ry1) 覆盖的缩放行 = floor(ry0·k) .. ceil(ry1·k)-1
        st, sb = int(math.floor(ry0 * k)), int(math.ceil(ry1 * k)) - 1
        assert cell[0] <= st and cell[1] > sb, ("行 %d 内容越格" % (i + 1))
        log("    行%d 内容(缩放后) y %d..%d ⊂ 格 y %d..%d  ✓（上余 %d / 下余 %d px）"
            % (i + 1, st, sb, cell[0], cell[1] - 1, st - cell[0], cell[1] - 1 - sb))
    log("  网格总高 %d + 原点 %d = %d ≤ 1080 ✓（7 项竖排可 1:1 放进画布）"
        % (7 * ch, y0, 7 * ch + y0))

    items, rects, labels, old_scales = [], [], [], []
    for i, (ry0, ry1) in enumerate(rows):
        cy0, cy1 = y0 + i * ch, y0 + (i + 1) * ch
        sem = MENU_SEM[i]
        base = "x_gen_menu_%d_%s" % (i + 1, sem)
        rec = {"index": i + 1, "semantic": sem, "label_cn": MENU_CN[i], "label_en": MENU_EN[i],
               "size": [cw, ch], "src_row_band": [ry0, ry1],
               "cell": [0, cy0, cw, cy1 - cy0]}
        for ci, (cx0, cx1, tag) in enumerate(((0, cw, ""), (cw, cw * 2, "_on"))):
            cell = (cx0, cy0, cx1, cy1)
            out = scaled.crop(cell)
            name = base + tag + ".png"
            out.save(os.path.join(OUT, name))
            cb = bbox_in_cell(scaled, cell, th=TH)
            if cb is None:
                log("!! %s 格全透明 —— 如实报告" % name)
            # 旧倍率（对照用）：旧脚本把每格裁紧后**归一化到高 104**，倍率 = 104 / 内容高
            cband = cols[1] if ci == 1 else cols[0]
            ob = alpha_bbox(src, (cband[0], ry0, cband[1] + 1, ry1 + 1), th=TH)
            old_scales.append(104.0 / (ob[3] - ob[1]))
            log("%-30s 格%s %dx%d  [统一 k=%.6f，未再单独缩放]  内容(格内) %s  %d B"
                % (name, ("L" if ci == 0 else "R"), cw, ch, k, cb,
                   os.path.getsize(os.path.join(OUT, name))))
            rec["normal" if ci == 0 else "hover"] = {"file": name, "content_bbox_in_cell": cb}
            rects.append([cx0, cy0, cw, ch - 1])
            labels.append("%s%d" % ("n" if ci == 0 else "h", i + 1))
        items.append(rec)
    old_scales_of("menu", old_scales)
    log("  " + ratio_line("菜单", old_scales) + "  → 新：14 件**同一 k = %.6f**（极差 0）" % k)

    grid = {"source_size": [W, H], "source_mode": "RGBA", "scaled_size": list(ssz),
            "cols": 2, "rows": 7, "origin": [0, y0], "cell": [cw, ch], "k": round(k, 6),
            "col_bounds": [0, cw, cw * 2],
            "row_bounds": [y0 + i * ch for i in range(8)],
            "grid_size": [cw * 2, y0 + 7 * ch],
            "semantic_order": MENU_SEM, "label_cn": MENU_CN, "label_en": MENU_EN,
            "note": "整图按 k 缩放一次后 2 列 × 7 行统一网格切分；列等分，行统一行高 %d、"
                    "原点 y=%d（源行间距不等，等分会切到第 6/7 项，已实测坐实）；"
                    "14 件尺寸完全相同 %dx%d" % (ch, y0, cw, ch)}
    GEOM["menu"] = items
    GEOM["menu_grid"] = grid
    GEOM22["menu"] = {"k": round(k, 6), "source_size": [W, H], "scaled_size": list(ssz),
                      "grid": grid, "items": items,
                      "old_scale_range": [round(min(old_scales), 4), round(max(old_scales), 4)]}
    overlay(scaled, rects, os.path.join(EVID22, "overlay_menu_grid.png"), labels)

    # 接触印相表：常态 vs 高亮 并排（1:1 原始尺寸）
    colw = cw + 10
    rowh = ch + 26
    sheet = Image.new("RGB", (2 * colw + 24, len(items) * rowh + 10), (16, 20, 28))
    d = ImageDraw.Draw(sheet)
    for it in items:
        yy = 10 + (it["index"] - 1) * rowh
        for j, f in enumerate((it["normal"]["file"], it["hover"]["file"])):
            im = Image.open(os.path.join(OUT, f)).convert("RGBA")
            bg = checker((im.size[0] + 8, im.size[1] + 8))
            bg.paste(im.convert("RGB"), (4, 4), im.getchannel("A"))
            sheet.paste(bg, (8 + j * colw, yy))
        d.text((10, yy + ch + 8), "%d %s / %s  %dx%d"
               % (it["index"], it["label_cn"], it["label_en"], it["size"][0], it["size"][1]),
               fill=(210, 220, 240))
    sheet.save(os.path.join(EVID22, "sheet_menu.png"))
    log("证据 -> %s" % os.path.join(EVID22, "sheet_menu.png"))


# ---------------------------------------------------------------- ⑨ 系统屏菜单按钮（M27，新素材）

# 源：生图入料\生成结果\系统屏底图重置3.png（2048×768 RGBA，用户 2026-09-21 提供）
#   7 列 × 2 行：**第 1 行 = 常规状态，第 2 行 = 悬停（鼠标放上去）状态**（用户说明原文）。
#   列序自左向右 = 开始游戏 / 继续游戏 / 读取存档 / 流程图 / 鉴赏 / 设置 / 退出游戏，
#   与 MENU_SEM 完全一致；中文标签**已烘焙在图上**（沿用既有做法：hit 的 label 留空串）。
# 取代 系统屏底图重置.png（1254×1254，2 列 × 7 行）—— **沿用同一批输出文件名**
#   x_gen_menu_{1..7}_{sem}.png / _on.png，以免旧件残留成孤儿资产。
# 与 ⑧ 的关键差别：⑧ 的源行间距不等，只能「统一行高 + 逐行校验落格」；本源的
#   按钮本体上下沿**逐件一致**（实测常态 7 件本体 y=208..330，悬停 7 件 y≈428..567），
#   故无需行网格——**按按钮本体对齐**即可（用户 2026-09-20 定的口径：按本体/文字块对齐，
#   而不是按含羽毛的包围盒对齐）。
MENU3_SRC = "系统屏底图重置3.png"
MENU3_SIZE = (2048, 768)
MENU3_K = 0.90          # 整图统一倍率（一次缩放，之后只切不再缩）
MENU3_BODY_CY = 862.0   # 按钮本体竖直中心在 1920×1080 画布上的落点
MENU3_BODY_FRAC = 0.5   # 本体行判定：行内 alpha 像素数 ≥ 该比例 × 窗口最大值


def build_menu3():
    path = os.path.join(GEN, MENU3_SRC)
    src = Image.open(path).convert("RGBA")
    W, H = src.size
    log("\n--- ⑨ %s %dx%d RGBA -> 14 件（M27）---" % (MENU3_SRC, W, H))
    if (W, H) != MENU3_SIZE:
        log("!! 尺寸与 M27 记录不符（期望 %s）—— 如实报告，不产出" % (MENU3_SIZE,))
        return
    scaled, k, ssz = uniform_scale(src, MENU3_K, "菜单3")
    SW, SH = ssz
    TH = 8
    ap = scaled.getchannel("A").point(lambda v: 255 if v >= TH else 0)
    px = ap.load()

    # ① 列投影分段：相邻按钮之间的 alpha 全空段即分界
    colc = [sum(1 for y in range(SH) if px[x, y]) for x in range(SW)]
    bands = _alpha_bands(colc, 1, 3)
    log("  列投影 alpha>0 段 %d 个（期望 7）" % len(bands))
    if len(bands) != 7:
        log("!! 列段数不符（期望 7）—— 如实报告，不产出")
        return
    # 列窗口 = 相邻两段之间的中点切分；首尾窗口取内容边界
    bounds = [bands[0][0]]
    for a, b in zip(bands, bands[1:]):
        if a[1] >= b[0]:
            log("!! 列段重叠 %s —— 分列失败，不产出" % ((a, b),))
            return
        bounds.append((a[1] + b[0]) // 2)
    bounds.append(bands[-1][1] + 1)
    log("  列窗口界（缩放后）%s" % (bounds,))
    cs, ce = bands[0][0], bands[-1][1]
    X0 = (1920 - (ce - cs + 1)) / 2.0
    log("  内容横跨 x %d..%d（宽 %d）→ 画布内左缘 X0=%.1f（左右留白各 %.1f px）"
        % (cs, ce, ce - cs + 1, X0, X0))

    rows = ((0, SH // 2), (SH // 2, SH))
    items, rects, labels = [], [], []
    for i in range(7):
        wl, wr = bounds[i], bounds[i + 1]
        win = wr - wl
        info = {"index": i + 1, "semantic": MENU_SEM[i], "label_cn": MENU_CN[i],
                "label_en": MENU_EN[i]}
        # ② 逐状态量测：内容包围盒 + 按钮本体（行内 alpha 计数过半的行段）
        meas = []
        for r, (ry0, ry1) in enumerate(rows):
            rowc = [sum(1 for x in range(wl, wr) if px[x, y]) for y in range(ry0, ry1)]
            mx = max(rowc)
            if mx == 0:
                log("!! 第 %d 行第 %d 列窗口全透明 —— 如实报告，不产出" % (r + 1, i + 1))
                return
            body = [y for y, v in enumerate(rowc, ry0) if v >= MENU3_BODY_FRAC * mx]
            cb = alpha_bbox(scaled, (wl, ry0, wr, ry1), th=TH)
            if cb is None:
                log("!! 第 %d 行第 %d 列窗口内容为空 —— 如实报告，不产出" % (r + 1, i + 1))
                return
            meas.append({"bbox": cb, "body_top": body[0], "body_bot": body[-1],
                         "body_cy": (body[0] + body[-1]) / 2.0})
            log("    行%d 列%d  内容 %s  本体 y %d..%d（高 %d，中心 %.1f）"
                % (r + 1, i + 1, cb, body[0], body[-1], body[-1] - body[0] + 1,
                   (body[0] + body[-1]) / 2.0))
        # ③ 两态共用同一画布尺寸（高 = 两者内容高的较大者），本体中心一律落在画布竖直中点
        ch = max(m["bbox"][3] - m["bbox"][1] for m in meas)
        info["size"] = [win, ch]
        for r, m in enumerate(meas):
            cb = m["bbox"]
            piece = scaled.crop((wl, cb[1], wr, cb[3]))
            canvas = Image.new("RGBA", (win, ch), (0, 0, 0, 0))
            canvas.alpha_composite(piece, (0, int(round(ch / 2.0 - (m["body_cy"] - cb[1])))))
            tag = "" if r == 0 else "_on"
            name = "x_gen_menu_%d_%s%s.png" % (i + 1, MENU_SEM[i], tag)
            canvas.save(os.path.join(OUT, name))
            info["normal" if r == 0 else "hover"] = {
                "file": name, "src_bbox": cb, "body": [m["body_top"], m["body_bot"]]}
            log("%-30s %dx%d  [统一 k=%.6f，未再单独缩放]  %d B"
                % (name, win, ch, k, os.path.getsize(os.path.join(OUT, name))))
            labels.append("%s%d" % ("n" if r == 0 else "h", i + 1))
            rects.append([wl, rows[r][0], win, rows[r][1] - rows[r][0] - 1])
        # ④ 画布几何：本体中心对齐到 MENU3_BODY_CY；横位沿用源列窗口（保相对间距）
        info["layout"] = {"x": round(X0 + (wl - cs), 1),
                          "y": round(MENU3_BODY_CY - ch / 2.0, 1),
                          "w": win, "h": ch}
        log("    → 画布 x=%.1f y=%.1f w=%d h=%d（本体中心 y=%.1f，两态同尺寸）"
            % (info["layout"]["x"], info["layout"]["y"], win, ch, MENU3_BODY_CY))
        items.append(info)

    GEOM["menu"] = items
    GEOM["menu_grid"] = {
        "source": MENU3_SRC, "source_size": [W, H], "source_mode": "RGBA",
        "scaled_size": list(ssz), "k": round(k, 6), "cols": 7, "rows": 2,
        "col_bounds": bounds, "row_bounds": [0, SH // 2, SH],
        "content_span": [cs, ce], "canvas_x0": round(X0, 1),
        "body_center_y": MENU3_BODY_CY,
        "semantic_order": MENU_SEM, "label_cn": MENU_CN, "label_en": MENU_EN,
        "note": "整图按 k 缩放一次后，按**列窗口（相邻按钮 alpha 空隙中点）**× 2 行切分；"
                "两态画布尺寸取齐（高 = 两态内容高较大者），**按钮本体中心统一落在画布竖直中点**，"
                "故悬停切换不跳动、无拉伸变形；布局横位沿用源列窗口以保相对间距。",
    }
    overlay(scaled, rects, os.path.join(EVID22, "overlay_menu3_grid.png"), labels)

    # 接触印相表：常态 / 悬停 上下并排，1:1
    colw = max(it["size"][0] for it in items) + 12
    rowh = max(it["size"][1] for it in items) + 28
    sheet = Image.new("RGB", (7 * colw + 16, 2 * rowh + 14), (16, 20, 28))
    d = ImageDraw.Draw(sheet)
    for it in items:
        xx = 8 + (it["index"] - 1) * colw
        for j, f in enumerate((it["normal"]["file"], it["hover"]["file"])):
            im = Image.open(os.path.join(OUT, f)).convert("RGBA")
            bg = checker((im.size[0] + 8, im.size[1] + 8))
            bg.paste(im.convert("RGB"), (4, 4), im.getchannel("A"))
            sheet.paste(bg, (xx, 8 + j * rowh))
        d.text((xx + 2, 8 + 2 * rowh - 12), "%d %s %dx%d"
               % (it["index"], it["label_cn"], it["size"][0], it["size"][1]),
               fill=(210, 220, 240))
    sheet.save(os.path.join(EVID22, "sheet_menu3.png"))
    log("证据 -> %s" % os.path.join(EVID22, "sheet_menu3.png"))


# ---------------------------------------------------------------- 主流程

def main():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(EVID20, exist_ok=True)
    os.makedirs(EVID22, exist_ok=True)
    log("=" * 78)
    log("M11/M20/M22 · prep_generated.py —— 从 AI 生图素材派生新资产")
    log("源（只读）: %s" % GEN)
    log("输出      : %s" % OUT)
    log("=" * 78)
    log("M20 已可用（真 alpha，本脚本读取并派生）：游戏logo重置.png、系统屏底图重置.png")
    log("已作废（只登记，本脚本不读取、不产出）：俺翼logo.png、系统屏底图.png")
    log("  原因：棋盘格烘焙进像素（假透明），非真 alpha；已被用户 2026-09-20 的重导件取代")

    log("\nM22 起：图标 / 菜单 / 方框三件改为「整图统一倍率缩放 → 按网格切分」；"
        "新增 build_dialog2()（暂定对话框.png -> x_gen_dialog2.png）")
    log("\nM27（2026-09-21）：菜单按钮改源为 系统屏底图重置3.png（2048×768，7 列 × 2 行，"
        "第 1 行常态 / 第 2 行悬停）——build_menu() 停用，改调 build_menu3()（同文件名输出）")

    build_icons()
    build_dialog()
    build_dialog2()
    build_flownodes()
    build_fragpage()
    build_gallerypage()
    build_bg_system()
    build_logo()
    build_menu3()

    log("\n--- 旧 vs 新 倍率对照（M22 核心验收项）---")
    for name in ("icons", "menu", "flownodes"):
        if name in OLD_SCALES:
            vals = OLD_SCALES[name]
            newk = {"icons": ICON_K, "menu": MENU_K, "flownodes": FLOW_K}[name]
            log("  %-10s 旧（逐件归一化）%.4f–%.4f，极差 %.3f×  →  新（统一 k）%.6f，极差 1.000×"
                % (name, min(vals), max(vals), max(vals) / min(vals), newk))

    log("\n--- 产物体积 ---")
    tot = 0
    for f in sorted(os.listdir(OUT)):
        if f.startswith("x_gen_") or f == "x_bg_system.png":
            s = os.path.getsize(os.path.join(OUT, f))
            tot += s
            log("  %-32s %8d B" % (f, s))
    log("M11+M20 新增件合计 %.2f MB" % (tot / 1048576))

    gp = os.path.join(WORK, "M20_生成几何.json")
    with open(gp, "w", encoding="utf-8") as fh:
        json.dump(GEOM, fh, ensure_ascii=False, indent=1)
    log("几何 -> %s" % gp)
    log("（注：_工作\\M11_生成几何.json 已冻结，本脚本不再改写）")

    gp22 = os.path.join(WORK, "M22_生成几何.json")
    with open(gp22, "w", encoding="utf-8") as fh:
        json.dump(GEOM22, fh, ensure_ascii=False, indent=1)
    log("几何 -> %s（供 M23 直接消费）" % gp22)

    lp = os.path.join(EVID20, "prep_generated.log")
    with open(lp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(LOG) + "\n")
    log("日志 -> %s" % lp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
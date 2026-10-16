# -*- coding: utf-8 -*-
r"""psv_evidence_badge.py —— 未愈缺陷修复轮取证：10× 改前/改后对照 + 1:1 右上角合成图 + 三项量化

Issue：`ISSUE-20260926-06` · **未愈缺陷修复轮**（派单缺陷 ①② 的自证产物）。

产出（全部落 `_工作\ISSUE-20260926-06_未愈缺陷修复\取证\`）：
  · `zoom_badge_10x_save.png` / `_load.png` —— 徽章区 **10× 改前/改后对照**（改前 = 重放上一轮
    「上下锚行线性补底」算法；改后 = 盘上现件）+ 差异图；图上带 20px 网格与坐标刻度。
  · `合成_右上角_1to1_改前.png` / `_改后.png` —— 右上角 1:1 合成（底图 + 页签 + 三系统键 + 页码数字），
    按**元素矩形**绘制（供缺陷 ① 的「相交面积 = 0」目视核对），矩形描边 + id 标注。
  · `量化_改前改后.txt` —— 三项量化（补区 stdev / 跨边亮度台阶 / 1px 硬边 + 平坦块）逐项对照。

★ 引擎字形是近似：本工程无引擎渲染权限（派单禁止跑巡演/浏览器），文字用系统字体
  「微软雅黑 Bold」（= `fonts.fallback_faces[0]`）按引擎排版式近似绘制，尺寸/位置按
  `工具\psv_fix_save_badge.py` 与 `复现脚本\psv_fix_saveload_badge.py` 的推导取值。
  图形元素（底图/九宫格按钮/页签）按引擎口径 1:1 合成，**几何关系与实机一致**。

用法：python _工作\ISSUE-20260926-06_未愈缺陷修复\复现脚本\psv_evidence_badge.py
"""
from __future__ import annotations

import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                    # noqa: E402
from PIL import Image, ImageDraw, ImageFont           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(UI, "krkr", "assets", "ui")
REF = os.path.join(UI, "PSV系统UI参考", "AI中文化", "2x")
EV = os.path.join(UI, "_工作", "ISSUE-20260926-06_未愈缺陷修复", "取证")
FONT = "C:/Windows/Fonts/msyhbd.ttc"

# 上一轮（改前）口径
OLD_ERASE = (1763, 80, 1846, 141)
OLD_BLEND = 4
OLD_NUM_BOX = (1663, 68, 180, 80)
OLD_NUM_SIZE = 66
OLD_SYS_Y = 44
# 本轮（改后）口径
NEW_NUM_BOX = (1699, 83, 60, 48)
NEW_NUM_SIZE = 48
NEW_SYS_Y = 22
SYS_ITEMS = [("sv.sys_game", 1062, 210, "返回游戏", "x_ui_btn_m_off"),
             ("sv.sys_title", 1312, 318, "返回标题画面", "x_ui_btn_m_off"),
             ("sv.sys_end", 1670, 210, "退出游戏", "x_ui_btn_m_off")]
TAB_ITEMS = [("sv.tab_a", 340, 181, "存档"), ("sv.tab_b", 526, 181, "读档")]


def Q8(a):
    return np.minimum(248, 8 * ((np.asarray(a).astype(np.int32) + 1) // 8)).astype(np.uint8)


def pristine(name):
    src = {"save": "otv_save_bg_cn.png", "load": "otv_load_bg_cn.png"}[name]
    im = Image.open(os.path.join(REF, src)).convert("RGB")
    return Q8(np.asarray(im.crop((0, 4, 1920, 1084))))


def replay_old_patch(classic):
    """重放上一轮 `工具\\psv_fix_save_badge.py` 的「上下锚行线性补底」⇒ 改前盘上件（像素口径）。"""
    x0, y0, x1, y1 = OLD_ERASE
    arr = classic.astype(np.uint8).copy()
    out = arr.astype(np.float64)

    def anchor(yrow):
        a = arr[yrow, x0:x1, :].astype(np.float64)
        pad = 3
        ext = np.concatenate([np.repeat(a[:1], pad, axis=0), a, np.repeat(a[-1:], pad, axis=0)], axis=0)
        ker = np.ones(2 * pad + 1) / (2 * pad + 1.0)
        return np.stack([np.convolve(ext[:, c], ker, mode="valid") for c in range(ext.shape[1])], axis=1)

    ra = anchor(y0 - 1)
    rb_s = anchor(y1)
    rb_r = arr[y1, x0:x1, :].astype(np.float64)
    n = y1 - y0
    for i, y in enumerate(range(y0, y1)):
        t = (i + 1) / float(n + 1)
        ramp_s = ra * (1 - t) + rb_s * t
        ramp_r = ra * (1 - t) + rb_r * t
        d = (y1 - 1) - y
        w = 0.0 if d >= OLD_BLEND else 1.0 - d / float(OLD_BLEND)
        out[y, x0:x1, :] = np.round(ramp_s * (1 - w) + ramp_r * w)
    return out.astype(np.uint8)


def nine_slice(path, w, h, nine):
    """按引擎九宫格口径把素材铺到 w×h（l/t/r/b 为素材侧边距）。"""
    src = Image.open(path).convert("RGBA")
    l, t, r, b = nine
    sw, sh = src.size
    out = Image.new("RGBA", (w, h))
    xs = [(0, 0, l, l), (l, l, sw - r, w - r), (sw - r, w - r, sw, w)]
    ys = [(0, 0, t, t), (t, t, sh - b, h - b), (sh - b, h - b, sh, h)]
    for (sx0, dx0, sx1, dx1) in xs:
        for (sy0, dy0, sy1, dy1) in ys:
            if dx1 <= dx0 or dy1 <= dy0:
                continue
            piece = src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.paste(piece, (dx0, dy0))
    return out


def draw_text(draw_img, box, size, s, align="right", outline=(0x3E, 0x63, 0xB8, 255),
              fill=(255, 255, 255, 255)):
    """按引擎排版式近似画文本：y_text = y + floor((h − floor(size*1.4))/2)，drawText 顶对齐。"""
    x, y, w, h = box
    lineH = max(size, int(size * 1.4))
    y_text = y + (h - lineH) // 2
    f = ImageFont.truetype(FONT, size)
    tmp = Image.new("RGBA", (1, 1))
    d0 = ImageDraw.Draw(tmp)
    tw = d0.textlength(s, font=f)
    if align == "right":
        xx = x + w - tw
    elif align == "center":
        xx = x + (w - tw) / 2.0
    else:
        xx = x
    layer = Image.new("RGBA", draw_img.size, (0, 0, 0, 0))
    d1 = ImageDraw.Draw(layer)
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            if dx or dy:
                d1.text((xx + dx, y_text + dy), s, font=f, fill=outline)
    d1.text((xx, y_text), s, font=f, fill=fill)
    draw_img.alpha_composite(layer)
    return xx, y_text, tw


def composite(bg, page_no, sys_y, num_box, num_size, annotate=True):
    img = Image.fromarray(bg).convert("RGBA")
    for _, x, w, lab, asset in SYS_ITEMS:
        img.alpha_composite(nine_slice(os.path.join(OUT, asset + ".png"), w, 50, (15, 8, 15, 8)), (x, sys_y))
        draw_text(img, (x, sys_y, w, 50), 18, lab, align="center", outline=(0, 0, 0, 0),
                  fill=(60, 60, 80, 255))
    for _, x, w, lab in TAB_ITEMS:
        img.alpha_composite(nine_slice(os.path.join(OUT, "x_ui_tab_off.png"), w, 60, (0, 0, 0, 0)), (x, 24))
        draw_text(img, (x - 5, 27, w, 60), 27, lab, align="center", outline=(0, 0, 0, 0),
                  fill=(70, 70, 90, 255))
    x, y, w, h = num_box
    draw_text(img, num_box, num_size, str(page_no))
    if annotate:
        d = ImageDraw.Draw(img)
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=(255, 0, 0, 255))
        d.text((x, y - 14), "sv.pgnum box %s" % (num_box,), fill=(255, 0, 0, 255))
        for eid, ex, ew, _, _ in SYS_ITEMS:
            d.rectangle([ex, sys_y, ex + ew - 1, sys_y + 49], outline=(0, 140, 0, 255))
            d.text((ex, sys_y - 12), "%s y%d..%d" % (eid, sys_y, sys_y + 49), fill=(0, 120, 0, 255))
    return img.convert("RGB")


def grid_sheet(tiles, z=10, box=None, title=""):
    """把若干同尺寸小块按 z 倍放大并排，带 20px 网格与坐标刻度。"""
    out = []
    for tag, im in tiles:
        c = im.resize((im.width * z, im.height * z), Image.NEAREST)
        d = ImageDraw.Draw(c)
        if box:
            for sx in range(box[0], box[2] + 1, 20):
                X = (sx - box[0]) * z
                d.line([(X, 0), (X, c.height)], fill=(255, 0, 0))
                d.text((X + 2, 2), str(sx), fill=(255, 255, 0))
            for sy in range(box[1], box[3] + 1, 20):
                Y = (sy - box[1]) * z
                d.line([(0, Y), (c.width, Y)], fill=(0, 200, 0))
                d.text((2, Y + 2), str(sy), fill=(0, 255, 255))
        out.append((tag, c))
    W = sum(c.width for _, c in out) + 10 * (len(out) + 1)
    H = max(c.height for _, c in out) + 30
    sheet = Image.new("RGB", (W, H), (15, 15, 15))
    dd = ImageDraw.Draw(sheet)
    x = 10
    for tag, c in out:
        sheet.paste(c, (x, 26))
        dd.text((x + 4, 8), tag, fill=(255, 255, 0))
        x += c.width + 10
    if title:
        dd.text((10, 8), title, fill=(255, 255, 0))
    return sheet


def metrics(before, after, classic):
    x0, y0, x1, y1 = OLD_ERASE
    rows = []
    for tag, im in (("改前", before), ("改后", after), ("原图", classic)):
        L = im.astype(np.float64).mean(axis=2)
        s_in = L[y0:y1, x0:x1].std()
        M = 20
        big = L[y0 - M:y1 + M, x0 - M:x1 + M]
        m = np.ones(big.shape, bool)
        m[M:M + (y1 - y0), M:M + (x1 - x0)] = False
        s_ring = big[m].std()
        step = [abs(float(np.median(L[y0, x0 + 10:x1 - 10]) - np.median(L[y0 - 1, x0 + 10:x1 - 10]))),
                abs(float(np.median(L[y1 - 1, x0 + 10:x1 - 10]) - np.median(L[y1, x0 + 10:x1 - 10]))),
                abs(float(np.median(L[y0 + 10:y1 - 10, x0]) - np.median(L[y0 + 10:y1 - 10, x0 - 1]))),
                abs(float(np.median(L[y0 + 10:y1 - 10, x1 - 1]) - np.median(L[y0 + 10:y1 - 10, x1])))]
        hard = int((np.abs(np.diff(L[y0 + 2:y1 - 2, x0 + 2:x1 - 2], axis=1)) > 40).sum())
        rows.append((tag, s_in, s_ring, s_in / s_ring, max(step), hard))
    return rows


def main():
    os.makedirs(EV, exist_ok=True)
    lines = ["未愈缺陷修复轮 · 徽章补丁三项量化（补区 = 旧补丁矩形 x%d..%d / y%d..%d）"
             % (OLD_ERASE[0], OLD_ERASE[2] - 1, OLD_ERASE[1], OLD_ERASE[3] - 1),
             "  %-6s %10s %12s %10s %14s %14s" % ("口径", "补区stdev", "区外环带stdev", "比", "跨边台阶(max)", "硬边像素数")]
    for name, page in (("save", 1), ("load", 1)):
        classic = pristine(name)
        before = replay_old_patch(classic)
        after = np.asarray(Image.open(os.path.join(OUT, "x_ui_psv_%s_bg.png" % name)).convert("RGB"))
        assert (after == classic).all(), "%s：盘上件 != 原图（本轮应已删补丁）" % name
        # 量化表
        for tag, s_in, s_ring, ratio, st, hard in metrics(before, after, classic):
            lines.append("  %-6s %10.2f %12.2f %10.2f %14.2f %14d"
                         % ("%s·%s" % (name, tag), s_in, s_ring, ratio, st, hard))
        # 10× 徽章对照（改前 / 改后 / 差异）
        BOX = (1720, 60, 1880, 168)
        diff = np.abs(after.astype(np.int16) - before.astype(np.int16)).sum(axis=2)
        tiles = [("改前(线性补底)", Image.fromarray(before)),
                 ("改后(PSV原图)", Image.fromarray(after)),
                 ("|改后-改前|", Image.fromarray(np.clip(diff * 3, 0, 255).astype(np.uint8)).convert("RGB"))]
        crops = [(t, im.crop(BOX)) for t, im in tiles]
        sheet = grid_sheet(crops, z=10, box=BOX)
        sheet.save(os.path.join(EV, "zoom_badge_10x_%s.png" % name))
        print("saved zoom_badge_10x_%s.png %s" % (name, sheet.size))
        # 1:1 右上角合成
        tb = composite(before, page, OLD_SYS_Y, OLD_NUM_BOX, OLD_NUM_SIZE)
        ta = composite(after, page, NEW_SYS_Y, NEW_NUM_BOX, NEW_NUM_SIZE)
        CROP = (1000, 0, 1920, 330)
        for tag, im in (("改前", tb), ("改后", ta)):
            im.crop(CROP).save(os.path.join(EV, "合成_右上角_1to1_%s_%s.png" % (tag, name)))
        # 对照大图（改前上 / 改后下）
        W = CROP[2] - CROP[0]
        H = (CROP[3] - CROP[1]) * 2 + 30
        big = Image.new("RGB", (W, H), (15, 15, 15))
        big.paste(tb.crop(CROP), (0, 22))
        big.paste(ta.crop(CROP), (0, (CROP[3] - CROP[1]) + 32))
        dd = ImageDraw.Draw(big)
        dd.text((4, 4), "%s 右上角 1:1 · 上=改前(y44, 相交 15116px²) 下=改后(y22, 相交 0)" % name, fill=(255, 255, 0))
        big.save(os.path.join(EV, "合成_右上角_1to1_对照_%s.png" % name))
        print("saved 合成_右上角_1to1_%s（%sx%s）" % (name, W, H))
    txt = "\n".join(lines) + "\n"
    open(os.path.join(EV, "量化_改前改后.txt"), "w", encoding="utf-8").write(txt)
    print(txt)
    print("证据目录：%s" % os.path.relpath(EV, UI))


if __name__ == "__main__":
    main()

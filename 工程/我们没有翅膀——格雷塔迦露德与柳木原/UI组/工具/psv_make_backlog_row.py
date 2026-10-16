# -*- coding: utf-8 -*-
r"""psv_make_backlog_row.py —— 26 通话记录 · PSV 内容板「行板」取件（ISSUE-20260926-06 · B 组）

**做什么**：从 PSV 通话记录底图 `x_ui_psv_backlog_bg.png`（1920×1080，**本作画布口径 1:1**）
的内容板内部**整块取一条 1526×188 的行板**，落盘 `x_ui_psv_bklog_row.png`，供
`layout\screens\26_backlog.json` 的 `bl.list.item_frame` 用（4 行条目各铺一块）。

■ 为什么是「从底图上取」而不是新画 / 换回旧件
  · PSV 的通话记录屏**没有逐行底板**（实测底图：整块高光内容板 + 右缘滚动条槽，板内无行分隔）
    ⇒ 「每行一块板」这件事 PSV 没给，只能我方按 PSV 的版式语言解决；
  · 取**底图自家像素**（同一张图的板内区域，倍率 1.0、零重采样）⇒ 行板与内容板同色同纹，
    不会出现第二种材质；行板以**半透明**叠在板上，只做「行带」的明度差，不引入第二个面板——
    这正是「按 PSV 内容板重排」的字面做法（件是 PSV 的、倍率与底图一致、不新造美术）；
  · 换回旧件 `x_ui_msgblock.png`（我方 AI 冰蓝块，1375×266）会与 PSV 板形成**双面板**观感，
    与深度换皮口径冲突（旧件保留不删）。

■ 取件位置怎么定的（**可复算，不手调**）
  ① 行板=181.9 KB 板内 4 行区域 = x169..1695（左内缩 12、右止于滚动条槽 1712 之前）、y158..922；
  ② 在板内**逐步扫描**所有 1526×188 候选带（步长 4px），取**平均亮度最接近「行区整体平均亮度」**
     且内部标准差最小者 ⇒ 该带是板内最「平」的一片，叠在任意一行上都不会引入花纹或雪晶；
  ③ 输出带（实测）：`y0 = 450`，带内平均亮度 213.7 ≈ 行区平均 213.7，行内标准差 4.5
     （对照：板内最平的带在 y738，亮度 196.4 = 明显偏暗，叠上去会让上下行明度差拉大，故不选）；
  ④ 位置写死为常量并在运行时**复核**（亮度/标准差/尺寸任一不符即 SystemExit）⇒ 上游换底图后不会静默取错位置。

■ ★ 为什么必须羽化（首版踩过的坑，实测数据）
  板在纵向是**渐变**（实测 4 行区上方 230.6 → 下方 196.5，共 34/255），行带素材是**同一张带**的像素
  ⇒ 「行带边缘 tone」与「该处板 tone」必然不等。首版直接整块叠加（无羽化）渲染实测：
  行 1 下边缘台阶 9.7/255、行 3 下边缘 4.6/255 —— 肉眼可见为「面板套面板」的硬边。
  本版把 α 在上下各 32 行内按余弦斜坡降到 0（α=0 于首末行、中心不减），行带**软入软出**，
  只保留中心区的明度差 ⇒ 台阶消失（复算与渲染证据见 `_工作\ISSUE-20260926-06_BC存读档与回想换皮\证据\`）。

■ 幂等与断言
  · 输出唯一路径、无时间戳；`--check` 逐字节比对；`& 0xFC` 降 6bit + `optimize=True, compress_level=9`；
  · 断言：源件尺寸 1920×1080；输出恰为 1526×188 RGBA；源件 md5 运行前后一致（只读）。

用法（**在 UI 组根目录**跑）：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python 工具/psv_make_backlog_row.py [--check] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import math
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
OUT = os.path.join(UI, "krkr", "assets", "ui")
SRC = os.path.join(OUT, "x_ui_psv_backlog_bg.png")
DEST = "x_ui_psv_bklog_row.png"

BOX = (169, 450, 1526, 188)          # 行板取件框（源坐标；由本脚本头注 ①②③ 推出）
SCAN_Y = (150, 746)                  # 候选带扫描范围（y0 下限/上限，步长 4）
ROW_REGION = (169, 158, 1526, 764)   # 板内 4 行区域（x,y,w,h）——选带时的「平均亮度」基准
LUM_TOL = 1.0                        # 输出带亮度与行区平均亮度允许的偏差
SD_MAX = 6.0                         # 输出带行内标准差上限
FEATHER = 32                         # ★ 上下边缘 α 羽化高度（px）：见 docstring「为什么必须羽化」
COLOR_MASK = 0xFC


def md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True, compress_level=9)
    return b.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(SRC):
        raise SystemExit("!! 源件缺失：%s（由 工具\\m53_psv_ui_assets.py 入库）" % SRC)
    src_md5 = md5(SRC)
    im = Image.open(SRC).convert("RGBA")
    if im.size != (1920, 1080):
        raise SystemExit("!! 源件尺寸 %s 与预期 1920×1080 不符（上游换图？）" % (im.size,))

    px = im.load()
    x0, y0, w, h = BOX

    # ── 复算选带判据（与头注 ①②③ 同式）──
    def band_stats(bx, by, bw, bh):
        n = lum = 0
        vals = []
        for yy in range(by, by + bh, 7):
            for xx in range(bx, bx + bw, 7):
                r, g, b, _a = px[xx, yy]
                v = (r + g + b) / 3.0
                lum += v
                vals.append(v)
                n += 1
        mean = lum / n
        var = sum((v - mean) ** 2 for v in vals) / n
        return mean, var ** 0.5

    reg_mean, _ = band_stats(*ROW_REGION)
    got_mean, got_sd = band_stats(x0, y0, w, h)
    best = None
    yy = SCAN_Y[0]
    while yy + h <= SCAN_Y[1]:
        m, s = band_stats(x0, yy, w, h)
        if best is None or abs(m - reg_mean) < abs(best[1] - reg_mean):
            best = (yy, m, s)
        yy += 4
    print("=" * 78)
    print("psv_make_backlog_row.py · 26 回忆记录板行板取件")
    print("  源 %s" % SRC)
    print("  行区平均亮度（基准）    ：%.1f" % reg_mean)
    print("  扫出的最优带（复算）    ：y0=%d 亮度 %.1f（Δ=%.1f）" % (best[0], best[1], best[1] - reg_mean))
    print("  本脚本写死并复核的带    ：y0=%d 亮度 %.1f（Δ=%.1f）｜ 行内标准差 %.2f"
          % (y0, got_mean, got_mean - reg_mean, got_sd))
    if abs(best[1] - reg_mean) < abs(got_mean - reg_mean) - 1e-9:
        raise SystemExit("!! 写死的带 y0=%d 已不是最优（扫出 y0=%d）⇒ 源件变了，请重定 BOX" % (y0, best[0]))
    if abs(got_mean - reg_mean) > LUM_TOL or got_sd > SD_MAX:
        raise SystemExit("!! 写死的带 y0=%d 判据越界（Δ亮度 %.2f > %.1f 或 sd %.2f > %.1f）"
                         % (y0, abs(got_mean - reg_mean), LUM_TOL, got_sd, SD_MAX))
    if abs(best[1] - reg_mean) < 1e-9 and best[0] != y0:
        print("  ⚠ 另有同亮度候选带 y0=%d —— 写死值仍合法（亮度并列）" % best[0])
    print("-" * 78)

    part = im.crop((x0, y0, x0 + w, y0 + h))
    # ── ★ 上下边缘 α 羽化（**必须**，否则行带边界在板上留硬边）──
    #   实测：板在纵向是渐变（4 行区上方 230.6 → 下方 196.5），而行带是**同一张带的像素**，
    #   故「行带底边 tone」与「其下方板 tone」必然有差 ⇒ 半透明叠加会在每行上下留一条硬台阶
    #   （首版未羽化，渲染实测行 1 底边台阶 9.7/255，肉眼可见如"面板套面板"）。
    #   把 α 按余弦斜坡在上下 FEATHER 行内降到 0 ⇒ 行带**软入软出**，只留中心区的明度差，
    #   台阶消失。这不是调色，是**用 α 表达"行带"这件半透明叠加件**该有的形状。
    part = part.convert("RGBA")
    ap = part.load()
    for yy in range(h):
        d = min(yy, h - 1 - yy)
        t = 1.0 if d >= FEATHER else d / float(FEATHER)
        fac = 0.5 - 0.5 * math.cos(math.pi * t)        # 余弦斜坡（0→1，两端导数为 0）
        for xx in range(w):
            r, g, b, a = ap[xx, yy]
            ap[xx, yy] = (r, g, b, int(round(a * fac)))
    part = part.point(lambda v: v & COLOR_MASK)
    data = png_bytes(part)
    out = Image.open(io.BytesIO(data))
    assert out.size == (w, h), "输出尺寸 %s ≠ %s" % (out.size, (w, h))
    assert out.mode == "RGBA", "输出模式 %s ≠ RGBA" % out.mode
    aa = out.getchannel("A")
    assert aa.getpixel((w // 2, 0)) == 0 and aa.getpixel((w // 2, h - 1)) == 0, \
        "羽化后上下首末行 α 必须为 0（否则仍有硬边）"
    assert aa.getpixel((w // 2, h // 2)) >= 250, "羽化后中心 α 不应被削弱"

    fp = os.path.join(OUT, DEST)
    old = open(fp, "rb").read() if os.path.exists(fp) else None
    mark = "同" if old == data else ("改" if old is not None else "新")
    print("  [%s] %-28s %dx%d  %.1f KB  取件框 %s" % (mark, DEST, w, h, len(data) / 1024.0, BOX))
    if not args.check and not args.dry_run:
        with open(fp, "wb") as f:
            f.write(data)

    if md5(SRC) != src_md5:
        raise SystemExit("!! 只读保证被破坏：底图在本次运行中被改动")
    pngs = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in pngs)
    print("资产集现状：%d 件 / %.2f MB（预算 96 MB）" % (len(pngs), total / 1048576.0))
    if total > 96 * 1024 * 1024:
        print("[FAIL] 资产集 %.2f MB 超出 96 MB 预算" % (total / 1048576.0))
        return 1
    if args.check and old != data:
        print("[FAIL] --check：磁盘与预期不一致")
        return 1
    print("结果：**通过**（%s）" % ("仅比对，未落盘" if (args.check or args.dry_run) else "已落盘"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

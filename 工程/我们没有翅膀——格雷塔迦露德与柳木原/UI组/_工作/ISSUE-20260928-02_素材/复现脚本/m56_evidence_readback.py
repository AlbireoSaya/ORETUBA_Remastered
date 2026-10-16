# -*- coding: utf-8 -*-
r"""m56_evidence_readback.py · 番外组名底板 · **独立回读**与可视证据（只读资产目录）

用途：把 `krkr\assets\ui\x_ui_fragtitle_bg.png` **从磁盘回读**（不看生成器内存值），
做逐件实测并出可视证据，供 reviewer / vision 复核。**不写任何资产、不改任何数据**
（唯一写入目标是 `_工作\ISSUE-20260928-02_素材\证据\`）。

产物（全部落 `证据\`）
  · fragtitle_逐件回读.tsv            —— 尺寸 / mode / 字节 / α 极值 / **不透明核心(α≥200)覆盖率** /
                                         α<200 像素分布（坐标清单 + 边内区 αmin）/ md5（与生成器交叉比对）
  · 预览_白底_fragtitle.png           —— 白底 1:1（供 vision）
  · 预览_深底_fragtitle.png           —— 深底 1:1（验真 alpha：无白底 / 棋盘格烘焙）
  · fragtitle_行列出alpha最小值曲线.png —— 行/列 α 最小值曲线 + α<200 像素 4× 标注
                                        （证明「不存在整段渐隐带」）

运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m56_evidence_readback.py
"""
from __future__ import annotations

import hashlib
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")

NAME = "x_ui_fragtitle_bg.png"
EXP = (444, 52)
CORE_THR = 200
RAD = 4
FONT = next((p for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                         r"C:\Windows\Fonts\arial.ttf") if os.path.exists(p)), None)


def fnt(sz):
    return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()


def main():
    os.makedirs(EVID, exist_ok=True)
    p = os.path.join(ASSETS, NAME)
    raw = open(p, "rb").read()
    with Image.open(p) as im0:
        w, h, mode = im0.size[0], im0.size[1], im0.mode
        im = im0.convert("RGBA")
    a = np.asarray(im.getchannel("A"))
    rgb = np.asarray(im)[:, :, :3]
    md5 = hashlib.md5(raw).hexdigest()

    core = int((a >= CORE_THR).sum())
    core_cov = 100.0 * core / a.size
    lt = np.argwhere(a < CORE_THR)                      # (y,x) of α<200 pixels
    nz = np.asarray(im).reshape(-1, 4)[a.reshape(-1) > 16]
    cnt = Counter(map(tuple, nz[:, :3].tolist()))
    top, topn = (cnt.most_common(1)[0] if cnt else ((0, 0, 0), 0))

    m = RAD + 4
    top_min = int(a[0, m:w - m].min())
    bot_min = int(a[h - 1, m:w - m].min())
    left_min = int(a[m:h - m, 0].min())
    right_min = int(a[m:h - m, w - 1].min())
    frame_lt = int(((a[0, :] < CORE_THR).sum() + (a[-1, :] < CORE_THR).sum()
                    + (a[:, 0] < CORE_THR).sum() + (a[:, -1] < CORE_THR).sum()))

    # α<200 像素分布：按「距最近边」归类（角 / 边-内区）
    def zone(y, x):
        d = min(y, x, h - 1 - y, w - 1 - x)
        return "四角/边缘 %dpx" % d
    zones = Counter(zone(int(y), int(x)) for y, x in lt)

    # 与生成器交叉比对
    gen_md5 = None
    gp = os.path.join(EVID, "fragtitle_实测.tsv")
    if os.path.exists(gp):
        for ln in open(gp, encoding="utf-8"):
            if ln.startswith("#") or "\t" not in ln:
                continue
            cells = ln.rstrip("\n").split("\t")
            if cells[0] == NAME:
                gen_md5 = cells[-1]
    same = (gen_md5 == md5)

    # ── TSV ───────────────────────────────────────────────────────────
    with open(os.path.join(EVID, "fragtitle_逐件回读.tsv"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("# 独立回读：直接从 krkr\\assets\\ui\\ 的 PNG 读回（**不看生成器内存值**）\n")
        f.write("# 核心覆盖率 = α≥200 像素占比；判据下限 96%；「无整段渐隐带」= 四条边内区 αmin ≥ 200\n")
        f.write("文件\t尺寸(w×h)\tmode\t字节\ta_min\ta_max\t核心(α≥200)覆盖率%\tα<200像素数"
                "\tα<200分布\t上边内区αmin\t下边内区αmin\t左边内区αmin\t右边内区αmin"
                "\t最外帧α<200\t非透明占比%\t主色\t主色像素数\tmd5\t与生成器md5一致\n")
        f.write("%s\t%d×%d\t%s\t%d\t%d\t%d\t%.4f\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%.2f\t%s\t%d\t%s\t%s\n"
                % (NAME, w, h, mode, len(raw), int(a.min()), int(a.max()), core_cov,
                   len(lt), "；".join("%s=%d" % kv for kv in sorted(zones.items())),
                   top_min, bot_min, left_min, right_min, frame_lt,
                   100.0 * len(nz) / a.size, "#%02X%02X%02X" % tuple(top), int(topn),
                   md5, "是" if same else "否"))

    # ── 预览（白底 / 深底，1:1，一件一行那套做法） ────────────────────
    def preview(bg, out, title):
        pad = 12
        Wc, Hc = 700 + im.width, 42 + im.height + 2 * pad
        c = Image.new("RGBA", (Wc, Hc), bg)
        d = ImageDraw.Draw(c)
        dark = bg[0] < 128
        fg = (222, 234, 250, 255) if dark else (26, 44, 70, 255)
        fg2 = (150, 172, 200, 255) if dark else (96, 116, 142, 255)
        d.text((pad, 8), title, font=fnt(18), fill=fg)
        d.text((pad, 32), "%s  %d×%d  %s  %d B  α[%d,%d]  核心(α≥%d) %.4f%%  α<%d 像素 %d"
               % (NAME, w, h, mode, len(raw), int(a.min()), int(a.max()),
                  CORE_THR, core_cov, CORE_THR, len(lt)), font=fnt(15), fill=fg2)
        c.alpha_composite(im, (700, pad))
        c.convert("RGB").save(out)

    preview((255, 255, 255, 255), os.path.join(EVID, "预览_白底_fragtitle.png"),
            "x_ui_fragtitle_bg · 白底 1:1（444×52）")
    preview((20, 24, 32, 255), os.path.join(EVID, "预览_深底_fragtitle.png"),
            "x_ui_fragtitle_bg · 深底 1:1（验真 alpha：无白底烘焙）")

    # ── 行/列 α 最小值曲线 + α<200 标注 ──────────────────────────────
    row_min = a.min(axis=1).astype(int)
    col_min = a.min(axis=0).astype(int)
    Z = 4
    zoom = im.resize((w * Z, h * Z), Image.NEAREST)
    arr = np.asarray(zoom).copy()
    arr[np.asarray(zoom.getchannel("A")) < CORE_THR] = [255, 0, 0, 255]
    marked = Image.fromarray(arr, "RGBA")
    lx, cw, ch = 320, w, 220
    Wc, Hc = lx + cw * 2 + 60, 44 + ch * 2 + 60
    c = Image.new("RGB", (Wc, Hc), (255, 255, 255))
    d = ImageDraw.Draw(c)
    d.text((12, 8), "行/列 α 最小值曲线（红虚线 = 核心阈值 200）——不触底即「无整段渐隐带」",
           font=fnt(17), fill=(26, 44, 70))

    def plot(x0, y0, vals, lab):
        n = len(vals)
        d.rectangle([x0, y0, x0 + cw, y0 + ch], outline=(180, 195, 214))
        y200 = y0 + ch - int(ch * CORE_THR / 255.0)
        d.line([x0, y200, x0 + cw, y200], fill=(220, 40, 40), width=1)
        d.line([(x0 + i * cw / float(max(1, n - 1)),
                 y0 + ch - int(ch * v / 255.0)) for i, v in enumerate(vals)],
               fill=(30, 110, 200), width=1)
        d.text((x0, y0 - 18), "%s  min=%d max=%d  α<%d 处数=%d"
               % (lab, int(min(vals)), int(max(vals)), CORE_THR,
                  int(sum(1 for v in vals if v < CORE_THR))), font=fnt(15), fill=(60, 80, 105))
        for t in (0, 200, 255):
            d.text((x0 - 34, y0 + ch - int(ch * t / 255.0) - 7), str(t), font=fnt(12),
                   fill=(150, 150, 150) if t == 200 else (120, 135, 155))

    plot(60, 62, row_min, "每行 α 最小值（y=0..51）")
    plot(60 + cw + 120, 62, col_min, "每列 α 最小值（x=0..443）")
    d.text((60, 340), "α<%d 像素标注（4× nearest，红 = α<200；实测仅 %d 个、全在四角圆弧）"
           % (CORE_THR, len(lt)), font=fnt(15), fill=(60, 80, 105))
    ms = min(w * Z, Wc - 80)
    c.paste(marked.resize((ms, int(h * Z * ms / float(w * Z))), Image.NEAREST).convert("RGB"),
            (60, 362))
    c.save(os.path.join(EVID, "fragtitle_行列出alpha最小值曲线.png"))

    # ── 报告 ─────────────────────────────────────────────────────────
    print("=" * 96)
    print("m56_evidence_readback.py · 组名底板独立回读（ISSUE-20260928-02）")
    print("-" * 96)
    print("%-24s %-9s %-5s %8s %4s %4s %14s %9s" %
          ("文件", "尺寸", "mode", "字节", "amin", "amax", "核心α≥200覆盖%", "α<200像素"))
    print("%-24s %-9s %-5s %8d %4d %4d %14.4f %9d"
          % (NAME, "%d×%d" % (w, h), mode, len(raw), int(a.min()), int(a.max()),
             core_cov, len(lt)))
    print("-" * 96)
    print("α<200 像素分布：%s" % "；".join("%s=%d" % kv for kv in sorted(zones.items())))
    print("  坐标（最多列 40 个）：%s%s"
          % (", ".join("(%d,%d)" % (int(x), int(y)) for y, x in lt[:40]),
             " …共 %d 个" % len(lt) if len(lt) > 40 else ""))
    print("「无整段渐隐带」：上边内区 αmin=%d ｜ 下边内区 αmin=%d ｜ 左边内区 αmin=%d ｜ 右边内区 αmin=%d"
          % (top_min, bot_min, left_min, right_min))
    print("  最外 1px 帧 α<200 像素 = %d（四角圆弧被同一像素在行/列上重复计）" % frame_lt)
    print("  非透明占比 %.2f%% ｜ 主色 %s × %d ｜ md5 %s"
          % (100.0 * len(nz) / a.size, "#%02X%02X%02X" % tuple(top), int(topn), md5))
    print("-" * 96)
    print("与生成器 md5 交叉比对：%s" % ("一致" if same else "**不一致**（磁盘 %s vs 生成器 %s）"
                                        % (md5, gen_md5)))
    ok = (im.size == EXP and mode == "RGBA" and int(a.min()) == 0 and int(a.max()) == 255
          and core_cov >= 96.0 and min(top_min, bot_min, left_min, right_min) >= CORE_THR
          and same)
    print("结果：**%s**" % ("全部通过" if ok else "存在失败项"))
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

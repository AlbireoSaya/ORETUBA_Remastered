# -*- coding: utf-8 -*-
r"""m09_evidence.py —— ISSUE-20260926-09 取证：改前 / 改后 实机截图对照

从巡演导出 `临时\ui_run\runtime\savedata\shot_*_config.png` 里自动挑出
**系统页**与**声音页**各一张（按右上立绘区的红色像素判定），裁剪三块区域，
最后合成三张「改前上 / 改后下」对照图。

区域（派单口径）：
  · 左列       x100..800 / y200..900   @1:1
  · 页签区     x120..560 / y130..250   @2x
  · 全屏       1920×1080               @0.5

用法（在 <UI组>\ 下）：
    python "...\复现脚本\m09_evidence.py" --stage before
    python "...\复现脚本\m09_evidence.py" --stage after
    python "...\复现脚本\m09_evidence.py" --compose
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(UI, "_工作", "ISSUE-20260926-09_config", "取证")
SHOTS = os.path.abspath(os.path.join(UI, "..", "..", "..", "临时", "ui_run", "runtime", "savedata"))

BOX_LEFT = (100, 200, 800, 900)
BOX_TAB = (120, 130, 560, 250)
BOX_ROW1 = (700, 240, 1220, 340)          # ★ 订正②：首行「窗口模式 / 全屏模式」值按钮对
TAB_SCALE = 2
ROW1_SCALE = 2
FULL_SCALE = 0.5
BG = (24, 24, 28)
FG = (255, 255, 255)


def font(sz):
    for p in ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def pick_shots():
    """返回 (sys_shot, snd_shot) 绝对路径"""
    out = {}
    for f in sorted(glob.glob(os.path.join(SHOTS, "shot_*_config.png"))):
        im = Image.open(f).convert("RGB")
        px = list(im.crop((1540, 250, 1760, 480)).getdata())
        red = sum(1 for r, g, b in px if r > 140 and r - g > 50 and r - b > 50)
        k = "snd" if red > 3000 else "sys"
        out.setdefault(k, f)
    if len(out) < 2:
        raise SystemExit("!! 未能在 %s 中同时找到系统页与声音页截图（%s）" % (SHOTS, sorted(out)))
    return out["sys"], out["snd"]


def stage(tag):
    os.makedirs(EV, exist_ok=True)
    sysf, sndf = pick_shots()
    print("[%s] 系统页 = %s\n[%s] 声音页 = %s" % (tag, sysf, tag, sndf))
    res = {}
    for k, f in (("sys", sysf), ("snd", sndf)):
        im = Image.open(f).convert("RGB")
        for nm, box, sc in (("left", BOX_LEFT, 1), ("tab", BOX_TAB, TAB_SCALE),
                            ("row1", BOX_ROW1, ROW1_SCALE), ("full", (0, 0, 1920, 1080), FULL_SCALE)):
            c = im.crop(box)
            if sc != 1:
                c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
            p = os.path.join(EV, "_stage_%s_%s_%s.png" % (tag, k, nm))
            c.save(p)
            res[(k, nm)] = p
            print("   %s/%s -> %s %s" % (k, nm, os.path.basename(p), c.size))
    return res


def compose():
    specs = [("left", "改前改后_左列1to1.png", "左列 1:1（x100..800 / y200..900）"),
             ("tab", "改前改后_页签2x.png", "页签区 2×（x120..560 / y130..250）"),
             ("full", "改前改后_全屏0.5x.png", "全屏 0.5×（1920×1080）")]
    F = font(22)
    F2 = font(20)
    made = []
    for nm, out, title in specs:
        cells = []
        for stage_tag in ("before", "after"):
            row = []
            for k in ("sys", "snd"):
                p = os.path.join(EV, "_stage_%s_%s_%s.png" % (stage_tag, k, nm))
                if not os.path.isfile(p):
                    raise SystemExit("!! 缺阶段图：%s（先跑 --stage before/after）" % p)
                row.append(Image.open(p).convert("RGB"))
            cells.append(row)
        cw, ch = cells[0][0].size
        pad, hdr, lab = 20, 34, 30
        W = pad + cw + pad + cw + pad
        H = pad + hdr + lab + ch + pad + lab + ch + pad
        sheet = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(sheet)
        d.text((pad, 8), title + "　｜　ISSUE-20260926-09　｜　列：左=系统页(sys)　右=声音页(snd)", font=F, fill=(150, 220, 255))
        y = pad + hdr
        for ri, (stag, label) in enumerate((("before", "改前（原数据）"), ("after", "改后（本次 issue）"))):
            d.text((pad, y), "%s  ·  %s" % (label, stag), font=F2, fill=FG)
            y += lab
            sheet.paste(cells[ri][0], (pad, y))
            sheet.paste(cells[ri][1], (pad + cw + pad, y))
            y += ch + pad
        p = os.path.join(EV, out)
        sheet.save(p)
        made.append(p)
        print("合成 -> %s %s" % (out, sheet.size))
    return made


def compose_row1():
    """★ 订正② 专用取证：首行「窗口模式 / 全屏模式」值按钮对。

    「改前」那次巡演的原始 1:1 截图已被后续巡演覆盖，故**两侧都从 0.5× 全屏阶段图**取同一区域
    再 ×4 放大 ⇒ 倍率一致、像素均来自实机巡演（改前 0.5× 图摄于 2026-09-27 00:14，早于任何数据改动）。
    """
    x0, y0, x1, y1 = (int(v * FULL_SCALE) for v in BOX_ROW1)
    F = font(22)
    F2 = font(20)
    cells = []
    for stag in ("before", "after"):
        p = os.path.join(EV, "_stage_%s_sys_full.png" % stag)
        if not os.path.isfile(p):
            raise SystemExit("!! 缺阶段图：%s（先跑 --stage before/after）" % p)
        cells.append(Image.open(p).convert("RGB").crop((x0, y0, x1, y1)).resize(
            ((x1 - x0) * 4, (y1 - y0) * 4), Image.NEAREST))
    cw, ch = cells[0].size
    pad, hdr, lab = 20, 34, 28
    sheet = Image.new("RGB", (pad + cw + pad, pad + hdr + lab + ch + pad + lab + ch + pad), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), "首行值按钮对（x700..1220 / y240..340）· 0.5× 全屏阶段图 ×4 · ISSUE-20260926-09 订正②",
           font=F, fill=(150, 220, 255))
    y = pad + hdr
    for stag, cell in zip(("before", "after"), cells):
        txt = ("改前（第一轮中间态：x957 + w221 ⇒ 与 _on 内间距 6px）" if stag == "before"
               else "改后（订正②：x967 + w195 ⇒ 内间距 16px，与其余 7 行一致）")
        d.text((pad, y), txt, font=F2, fill=FG)
        y += lab
        sheet.paste(cell, (pad, y))
        y += ch + pad
    out = os.path.join(EV, "改前改后_首行值按钮4x.png")
    sheet.save(out)
    print("合成 -> %s %s" % (os.path.basename(out), sheet.size))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["before", "after"])
    ap.add_argument("--compose", action="store_true")
    ap.add_argument("--row1", action="store_true")
    a = ap.parse_args()
    if a.stage:
        stage(a.stage)
    if a.compose:
        compose()
    if a.row1:
        compose_row1()
    if not a.stage and not a.compose and not a.row1:
        ap.error("需要 --stage before|after、--compose 或 --row1")

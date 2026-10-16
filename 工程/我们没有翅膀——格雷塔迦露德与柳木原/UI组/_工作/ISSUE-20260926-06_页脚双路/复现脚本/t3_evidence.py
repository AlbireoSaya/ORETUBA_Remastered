# -*- coding: utf-8 -*-
r"""t3 · 取证：① 编辑键条 1:1 合成图（改前/改后）② 7 件页脚 1:1 对照条 ③ 接缝/量化自证
输出到 `_工作\ISSUE-20260926-06_页脚双路\取证\`

合成口径（与 `复刻\replica.css` 一致）：
  · 底图 = `krkr\assets\ui\x_ui_psv_save_bg.png`（z=2，1:1 满屏）；
  · 文字 = msyhbd（回退链首项 Microsoft YaHei Bold）、色 `@palette.node_locked = #4A4A56`、
    字号取元素 `font.size`、`align=center / valign=middle` 画进元素矩形（引擎绘制口径的等效近似）；
  · 九宫格件按「全零 nine = 整体拉伸」处理（本屏 `sv.edit`/`sv.help` 皆 nine 0）。
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI = os.path.join(BASE, "krkr", "assets", "ui")
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
SCR = os.path.join(BASE, "layout", "screens")
EV = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路", "取证"); os.makedirs(EV, exist_ok=True)
FB = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 26)
FS = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 18)
BAND = (900, 976, 1904, 1040)          # 页脚带观察窗（画布坐标）
PAIRS = [("x_ui_psv_save_bg.png", "otv_save_bg.png", 4), ("x_ui_psv_load_bg.png", "otv_load_bg.png", 4),
         ("x_ui_psv_quick_load_bg.png", "otv_quick_load_bg.png", 4),
         ("x_ui_psv_backlog_bg.png", "otv_bklog.png", 4),
         ("x_ui_psv_gal_shell.png", "otv_gm_bg1.png", 0), ("x_ui_psv_music_bg.png", "otv_mu_bg.png", 0),
         ("x_ui_psv_replay_bg.png", "otv_mv_bg.png", 0)]


def flat(im):
    im = im.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")


def draw_text(d, el, palette_node="#4A4A56"):
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", el["font"]["size"])
    tw = d.textlength(el["sample"], font=f)
    x = el["x"] + (el["w"] - tw) / 2.0
    y = el["y"] + (el["h"] - el["font"]["size"]) / 2.0 - 2
    d.text((x, y), el["sample"], font=f, fill=palette_node)


def composite(scr, y_from, y_to, x_from=1040, x_to=1860):
    els = {e["id"]: e for e in scr["elements"]}
    img = flat(Image.open(os.path.join(UI, els["sv.bg"]["asset"].split("/")[-1])))
    for eid in ("sv.help", "sv.edit"):
        e = els[eid]
        a = Image.open(os.path.join(UI, e["asset"].split("/")[-1])).convert("RGBA")
        img.paste(flat(a.resize((e["w"], e["h"]), Image.BILINEAR)), (e["x"], e["y"]))
    d = ImageDraw.Draw(img)
    draw_text(d, els["sv.help_tx"])
    for eid in ("sv.del_tx", "sv.mod_tx", "sv.mov_tx", "sv.cpy_tx"):
        draw_text(d, els[eid])
    return img.crop((x_from, y_from, x_to, y_to))


def main():
    scr = json.load(open(os.path.join(SCR, "23_save.json"), encoding="utf-8"))
    # 改前几何（本脚本只画，不改盘；改前 = 上移前 y）
    before = json.loads(json.dumps(scr))
    for e in before["elements"]:
        if e["id"] in ("sv.edit",) or e["id"].startswith(("sv.del", "sv.mod", "sv.mov", "sv.cpy")):
            e["y"] += 122          # 还原到上移前
    Y0, Y1 = 790, 1080
    a = composite(before, Y0, Y1)
    b = composite(scr, Y0, Y1)
    note = ("改前：编辑键条 y964..1025 压在页脚带（实测墨迹 y982..1030）上 —— 中文压中文；"
            "改后：上移 122px（y842..903），与页脚带、sv.help 均零相交。1:1 合成（字为 msyhbd 近似）")
    sh = Image.new("RGB", (a.width, (a.height + 30) * 2 + 40), (236, 239, 246))
    dd = ImageDraw.Draw(sh)
    dd.text((8, 6), "改前（现状）", font=FB, fill=(150, 30, 40)); sh.paste(a, (0, 34))
    dd.text((8, a.height + 40), "改后（编辑键条上移 122px）", font=FB, fill=(20, 90, 40))
    sh.paste(b, (0, a.height + 68))
    dd.text((8, sh.height - 24), note, font=FS, fill=(60, 66, 84))
    p1 = os.path.join(EV, "合成_编辑键条_1to1_改前改后.png"); sh.save(p1)
    print("→", p1, sh.size)
    # 2× 放大（可读性）
    sh.resize((sh.width * 2, sh.height * 2), Image.LANCZOS).save(
        os.path.join(EV, "合成_编辑键条_2x_改前改后.png"))

    # ② 7 件页脚 1:1 对照条（原版日文 / 落地后中文）
    X0, X1 = BAND[0], BAND[2]
    CW = X1 - X0
    rows = []
    for tgt, src, off in PAIRS:
        o = flat(Image.open(os.path.join(SRC, src))).crop((X0, BAND[1] + off, X1, BAND[3] + off))
        n = flat(Image.open(os.path.join(UI, tgt))).crop(BAND)
        rows.append((tgt, o, n))
    LH = 64 + 64 + 26
    LW = 250
    sheet = Image.new("RGB", (CW + LW + 12, LH * len(rows) + 40), (236, 239, 246))
    d2 = ImageDraw.Draw(sheet)
    d2.text((8, 8), "落地后 7 件页脚 1:1 对照（每件上＝原版日文（源件同坐标），下＝落地后中文（资产件））",
            font=FB, fill=(30, 36, 60))
    y = 40
    for tgt, o, n in rows:
        d2.text((8, y + 14), "%s\n· 原版日文" % tgt, font=FS, fill=(120, 40, 40))
        sheet.paste(o, (LW, y)); y += 64
        d2.text((8, y + 14), "%s\n· 落地后中文" % tgt, font=FS, fill=(20, 90, 50))
        sheet.paste(n, (LW, y)); y += 64 + 26
    p2 = os.path.join(EV, "落地_页脚7件_1to1_对照.png"); sheet.save(p2)
    print("→", p2, sheet.size)

    # ③ 接缝 / 量化自证
    print("\n接缝自证（**引入**的跨边界台阶 = 结果跨边界行差 − 原图同位置行差；纯背景带取 x880..1904 全宽均值）")
    for tgt, src, off in PAIRS:
        A = np.asarray(flat(Image.open(os.path.join(UI, tgt)))).astype(np.int16)
        S = np.asarray(flat(Image.open(os.path.join(SRC, src)))).astype(np.int16)
        py = 940 - off
        step_new = float(np.abs(A[py] - A[py - 1]).mean())
        step_src = float(np.abs(S[py + off] - S[py + off - 1]).mean())
        print("   %-30s 粘贴y=%-4d 结果台阶=%.2f 原图同位置台阶=%.2f ⇒ 脚本引入=%.2f"
              % (tgt, py, step_new, step_src, abs(step_new - step_src)))
    print("\n量化自证（贴后 7 件 RGB 是否统一 step-4：max(v%%4)；0 = 与资产既有口径一致、无跨边界量化差）")
    for tgt, src, off in PAIRS:
        a = np.asarray(flat(Image.open(os.path.join(UI, tgt))))
        print("   %-30s max(v%%4)=%d" % (tgt, int(max((a[:, :, c] % 4).max() for c in range(3)))))
    # 接缝 4× 放大目视证据（页脚带上沿 ±15 行）
    tiles = []
    for tgt, src, off in PAIRS[:4]:
        A = np.asarray(flat(Image.open(os.path.join(UI, tgt)))).astype(np.uint8)
        py = 940 - off
        tiles.append((tgt, Image.fromarray(A[py - 15:py + 15, 900:1904])))
    w = 1004; h = 30
    sh2 = Image.new("RGB", (w * 2, (h * 2 + 24) * len(tiles) + 10), (236, 239, 246))
    d3 = ImageDraw.Draw(sh2)
    y = 6
    for tgt, im in tiles:
        z = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        sh2.paste(z, (0, y + 20)); d3.text((4, y), "%s · 页脚带上沿 ±15 行（2× 放大，边界在正中）" % tgt,
                                           font=FS, fill=(30, 36, 60))
        y += h * 2 + 24
    p3 = os.path.join(EV, "接缝_页脚带上沿_2x.png"); sh2.save(p3)
    print("→", p3, sh2.size)


if __name__ == "__main__":
    main()

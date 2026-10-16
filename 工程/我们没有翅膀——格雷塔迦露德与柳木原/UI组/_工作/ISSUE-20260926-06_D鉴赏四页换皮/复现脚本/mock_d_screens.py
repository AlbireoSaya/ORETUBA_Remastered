# -*- coding: utf-8 -*-
r"""mock_d_screens.py —— D 鉴赏四页（27/28/37/38）＋ 外壳（39）新几何的**版式预演图**。

目的：在改 layout JSON 之前，先把「PSV 底图 1:1 ＋ 我方内容按 PSV 常量重排」的
几何画出来目视复核（底图是否压住英文题字、条带是否切到 28 的 PSV 播放条、
网格与页脚/页码键是否打架）。**只读 layout 数据 + 只画图**，不写任何 JSON。

用法：python _工作\ISSUE-20260926-06_D鉴赏四页换皮\复现脚本\mock_d_screens.py
产出：_工作\...\evidence\mock_<屏>.png（4 张，1920×1080）
"""
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)                     # _工作\ISSUE-..._D鉴赏四页换皮
UI = os.path.dirname(os.path.dirname(WORK))      # <UI组>（WORK = <UI组>\_工作\<issue>）
A = os.path.join(UI, "krkr", "assets", "ui")
EV = os.path.join(WORK, "evidence")
FONT = r"C:\Windows\Fonts\msyh.ttc"

# ---- 拟用几何（写进 JSON 前的候选值）----
SHELL = dict(
    strip=(340, 0, 1580, 100),
    tabs=[(360, 12, 171, 76, "CG鉴赏"), (541, 12, 220, 76, "BGM鉴赏"),
          (771, 12, 258, 76, "立绘鉴赏"), (1039, 12, 229, 76, "情景回想")],
    title=(1290, 22, 300, 56, "鉴赏模式"),
    back=(1660, 22, 230, 56, "返回"),
)
GAL = dict(page="27_gallery", bg="x_ui_psv_gal_shell.png",
           grid=(106, 195, 1707, 681, 171, 96, 21, 9, 6))
MUS = dict(page="28_music", bg="x_ui_psv_music_bg.png",
           list=(169, 504, 1580, 419, 526, 59, 1, 3, 7),
           keys=[(609 + 91 * i, 253, 59, 59) for i in range(8)],
           slider=(718, 360, 488, 29))
DRE = dict(page="37_dress", bg="x_ui_psv_dress_bg.png",
           ctrl=(34, 160, 755, 38), namelist=(0, 212, 182, 641),
           big=(203, 212, 782, 386), reset=(1225, 160, 77, 40),
           name_rows=[(34, 209 + 60 * k, 148, 47) for k in range(7)],
           btns=[(276 + 140 * i, 225, 131, 56) for i in range(5)],
           btn_rows=[(276 + 65 * i, 345, 56, 56) for i in range(3)])
REP = dict(page="38_replay", bg="x_ui_psv_replay_bg.png",
           preview=(88, 215, 542, 309),
           grid=(680, 208, 1147, 671, 271, 152, 21, 4, 4))
PAGEKEYS = [(790, 939, 56, 56), (1074, 939, 56, 56)]


def outline(d, box, color=(255, 0, 0), txt=None, font=None, width=2, fill=None):
    x, y, w, h = box
    if fill:
        d.rectangle([x, y, x + w, y + h], fill=fill)
    for k in range(width):
        d.rectangle([x - k, y - k, x + w + k, y + h + k], outline=color)
    if txt and font:
        d.text((x + 4, y + 4), txt, fill=(0, 0, 0), font=font)


def grid(d, spec, color=(255, 0, 0)):
    x, y, w, h, cw, ch, gap, cols, rows = spec
    for r in range(rows):
        for c in range(cols):
            outline(d, (x + c * (cw + gap), y + r * (ch + gap), cw, ch), color)


def draw_shell(im, d, f):
    x, y, w, h = SHELL["strip"]
    band = Image.open(os.path.join(A, "x_ui_psv_shell_strip.png")).convert("RGBA")
    im.alpha_composite(band, (x, y))
    for (tx, ty, tw, th, lab) in SHELL["tabs"]:
        outline(d, (tx, ty, tw, th), (0, 90, 0), lab, f)
    for key in ("title", "back"):
        tx, ty, tw, th, lab = SHELL[key]
        outline(d, (tx, ty, tw, th), (0, 90, 0), lab, f)


def main():
    f = ImageFont.truetype(FONT, 20)
    f2 = ImageFont.truetype(FONT, 26)
    for cfg in (GAL, MUS, DRE, REP):
        bg = Image.open(os.path.join(A, cfg["bg"])).convert("RGBA")
        d = ImageDraw.Draw(bg)
        if cfg is GAL:
            grid(d, cfg["grid"])
            d.text((110, 170), "gal.list 9×6=54/页 (171×96 gap21)", fill=(180, 0, 0), font=f2)
        elif cfg is MUS:
            x, y, w, h, cw, ch, gap, cols, rows = cfg["list"]
            for r in range(rows):
                outline(d, (x, y + r * (ch + gap), w, ch), (255, 0, 0))
            for b in cfg["keys"]:
                outline(d, b, (0, 0, 220), "K")
            outline(d, cfg["slider"], (0, 0, 220), "slider")
            d.text((160, 460), "mu.list 3×7=21/页 (526×59)  控制键 8 ＋ 滑块 → PSV 信息框",
                   fill=(180, 0, 0), font=f2)
        elif cfg is DRE:
            outline(d, cfg["ctrl"], (0, 0, 220), "dr.ctrl")
            outline(d, cfg["namelist"], (255, 0, 0), "namelist 182")
            outline(d, cfg["big"], (255, 0, 0), "dr.big 782×386")
            outline(d, cfg["reset"], (0, 0, 220), "reset")
            for b in cfg["name_rows"]:
                outline(d, b, (200, 0, 0), "名", f)
            for b in cfg["btns"]:
                outline(d, b, (0, 0, 220))
            for b in cfg["btn_rows"]:
                outline(d, b, (0, 180, 0))
        elif cfg is REP:
            outline(d, cfg["preview"], (0, 0, 220), "rp.preview = 1 个 PSV 影像槽")
            grid(d, cfg["grid"])
            d.text((680, 190), "rp.list 4×4=16/页 (271×152 gap21)", fill=(180, 0, 0), font=f2)
        for pk in PAGEKEYS:
            outline(d, pk, (120, 120, 0))
        draw_shell(bg, d, f)
        out = os.path.join(EV, "mock_%s.png" % cfg["page"])
        bg.convert("RGB").save(out, optimize=True)
        print("wrote", os.path.relpath(out, UI))


if __name__ == "__main__":
    main()

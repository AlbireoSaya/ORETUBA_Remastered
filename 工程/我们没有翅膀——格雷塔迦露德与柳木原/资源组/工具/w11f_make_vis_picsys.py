# -*- coding: utf-8 -*-
"""W11f · 抽样目视 pic/sys 门控候选（同一 stem 的两个代表候选）→ 对照图。"""
import os, sys
from PIL import Image, ImageDraw

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f"))
OUT = os.path.join(WORK, "vis")
os.makedirs(OUT, exist_ok=True)
H, PAD, LABEL = 300, 8, 18


def load(path, h, maxw=520):
    im = Image.open(path).convert("RGBA")
    w = max(1, round(im.width * h / im.height))
    im = im.resize((w, h), Image.LANCZOS)
    if im.width > maxw:
        im = im.resize((maxw, max(1, round(im.height * maxw / im.width))), Image.LANCZOS)
    bg = Image.new("RGBA", (im.width, h), (255, 255, 255, 255))
    bg.alpha_composite(im, (0, (h - im.height) // 2))
    return bg.convert("RGB")


def sheet(items, fname):
    tiles = []
    for lab, pa, pb in items:
        a, b = load(pa, H), load(pb, H)
        t = Image.new("RGB", (a.width + b.width + PAD * 3, H + LABEL + PAD), (250, 250, 250))
        t.paste(a, (PAD, LABEL)); t.paste(b, (PAD * 2 + a.width, LABEL))
        d = ImageDraw.Draw(t)
        d.rectangle([PAD, LABEL, PAD + a.width, LABEL + H], outline=(160, 160, 160))
        d.rectangle([PAD * 2 + a.width, LABEL, PAD * 2 + a.width + b.width, LABEL + H], outline=(160, 160, 160))
        d.text((PAD + 2, 3), lab + "  [A]", fill=(0, 0, 0))
        d.text((PAD * 2 + a.width + 2, 3), "[B]", fill=(180, 0, 0))
        tiles.append(t)
    W = max(t.width for t in tiles)
    Ht = sum(t.height for t in tiles) + PAD * (len(tiles) + 1)
    out = Image.new("RGB", (W + PAD * 2, Ht), (255, 255, 255))
    y = PAD
    for t in tiles:
        out.paste(t, (PAD, y)); y += t.height + PAD
    out.save(os.path.join(OUT, fname))
    print("wrote", fname, out.size)


def P(src, kind, name):
    return os.path.join(LIB, src, kind, name)


if __name__ == "__main__":
    # A = 当前 CG背景 产物源（np/otv），B = 落选的 PC 4:3 版
    pic = [
        ("bg12b  A=np(1280x720) B=ot(800x600)", P("np", "pic", "np_bg12b.png"), P("ot", "pic", "ot_bg12b.png")),
        ("bg41   A=np B=ot", P("np", "pic", "np_bg41.png"), P("ot", "pic", "ot_bg41.png")),
        ("bg01   A=otv(1440x544) B=ot(1200x600)", P("otv", "pic", "otv_bg01.png"), P("ot", "pic", "ot_bg01.png")),
        ("cin081 A=otv(960x540) B=ot(800x600)", P("otv", "pic", "otv_cin081.png"), P("ot", "pic", "ot_cin081.png")),
        ("ec28   A=np B=ot", P("np", "pic", "np_ec28.png"), P("ot", "pic", "ot_ec28.png")),
        ("ec01   A=np B=ot", P("np", "pic", "np_ec01.png"), P("ot", "pic", "ot_ec01.png")),
        ("ef05a  A=np B=ot", P("np", "pic", "np_ef05a.png"), P("ot", "pic", "ot_ef05a.png")),
        ("bg72   A=np B=ot", P("np", "pic", "np_bg72.png"), P("ot", "pic", "ot_bg72.png")),
    ]
    sheet(pic[:4], "picgate_1.png")
    sheet(pic[4:], "picgate_2.png")

    sysx = [
        ("rule000 A=otv(960x544) B=ot(800x600)", P("otv", "etc", "otv_rule000.png"), P("ot", "sys", "ot_rule000.png")),
        ("rule055 A=otv B=ot", P("otv", "etc", "otv_rule055.png"), P("ot", "sys", "ot_rule055.png")),
        ("tl_cfg  A=ot(363x25) B=ota(210x35)", P("ot", "sys", "ot_tl_cfg.png"), P("ota", "sys", "ota_tl_cfg.png")),
        ("ec2_bg  A=otv(1013x658) B=ot(800x600)", P("otv", "sys", "otv_ec2_bg.png"), P("ot", "sys", "ot_ec2_bg.png")),
    ]
    sheet(sysx, "sysgate_1.png")
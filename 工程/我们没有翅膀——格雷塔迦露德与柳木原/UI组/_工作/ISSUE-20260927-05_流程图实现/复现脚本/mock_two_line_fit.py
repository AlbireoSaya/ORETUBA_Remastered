# -*- coding: utf-8 -*-
"""流程图节点「两行标签装不装得下底板」· 三变体对比图（示意，程序化合成）

用途：ISSUE-20260927-05 —— vision 打回「两行标签溢出底板 6–8px」。三种改法给用户看效果：
  V1 现状：元素 296×65、字号 23、行距 1.4   → 两行墨迹 55px ＞ 实体面 49px（溢出）
  V2 缩字号：元素 296×65、字号 18、行距 1.15 → 缩到能装进 49px；代价=屏幕等效 ≈12px
  V3 加高节点：元素 296×84、字号 23、行距 1.4 → 实体面 67px 装得下；代价=比例变、行距要重算

文字落位用**引擎自己的模型**（已用实机图逐行验证）：
  blockH = 行数 × lineH，lineH = floor(font_size × line_spacing)
  blockTop = el.y + floor((h − blockH) / 2)          （valign:"middle" 居中「行盒」）
  inkTop(i) = blockTop + i × lineH，ink 高 ≈ font_size − 1
  ⇒ 实测核对：node.0006（el.y=665、f=23、lineH=32、2 行）→ 墨迹 665–686 / 697–717（模型逐行吻合）

底板（实体面）＝ 素材逐行平均 alpha>200 的行区间；三类实测均为 rows 8..55/56（上下各约 8px 羽化）。

指标定义（**只看首行与末行**，不要用「所有行里最负的那个」——那会把第二行误当成上溢）：
  首行上留 = 实体面上沿 − 首行墨迹顶      （负 = 溢出）
  末行下留 = 实体面下沿 − 末行墨迹底      （负 = 溢出）
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
UI = ROOT / "工程" / "我们没有翅膀——格雷塔迦露德与柳木原" / "UI组"
ASSETS = UI / "krkr" / "assets" / "ui"
REAL = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "取证" / "E2_自证" / "E2_真实数据验收图_shot_84_flowchart.png"
OUT = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "取证" / "对比_两行标签_三变体.png"

BG = (24, 31, 46)
FG = (232, 238, 246)
DIM = (150, 162, 178)
HL = (255, 214, 140)
BAD = (255, 110, 110)
OK = (140, 226, 150)
INK = (0x16, 0x22, 0x3A)
PANEL = (33, 40, 55)
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

NINE = {"section": (14, 16), "select": (14, 13), "frag": (14, 15)}
SAMPLES = [
    ("鹰振翅高飞", "section"),
    ("在世界底层仓皇逃窜", "select"),
    ("如今我们的胸部再度开始", "frag"),
    ("做得太过火的明日香大人", "section"),
    ("黄金之鹰传说八十五章～茨瓦伊城堡的攻防～", "section"),
]
VARIANTS = [
    {"key": "V1", "title": "V1 现状（被 vision 打回）", "h": 65, "f": 23, "ls": 1.4,
     "sub": "元素 296×65 · 字号 23 · 行距 1.4 ｜ 两行墨迹跨度 行距32+字高23=55px ＞ 实体面 49px ｜ 屏幕等效 15.3px"},
    {"key": "V2", "title": "V2 缩字号 + 压行距（版式完全不动）", "h": 65, "f": 19, "ls": 1.0,
     "sub": "元素 296×65 · 字号 19 · 行距 1.0 ｜ 每行可容 12 字 ⇒ 11–12 字标题变单行 ｜ 屏幕等效 12.7px ｜ 两行 5/5px"},
    {"key": "V3", "title": "V3 加高节点（保住字号 23）", "h": 94, "f": 23, "ls": 1.4,
     "sub": "元素 296×94（垂直九宫格补足）· 字号 23 · 行距 1.4 ｜ 实体面 77px ｜ 屏幕等效 15.3px ｜ 两行 7/15px ｜ 代价＝比例变（比参照作高 45%）、行距要重算、一屏行数变少"},
]


def font(sz, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else "C:/Windows/Fonts/msyh.ttc", sz)


def stretch_h(img, out_w, l, r):
    w, h = img.size
    mid = out_w - l - r
    out = Image.new("RGBA", (out_w, h), (0, 0, 0, 0))
    out.paste(img.crop((0, 0, l, h)), (0, 0))
    out.paste(img.crop((l, 0, w - r, h)).resize((mid, h), Image.BILINEAR), (l, 0))
    out.paste(img.crop((w - r, 0, w, h)), (out_w - r, 0))
    return out


def stretch_v(img, out_h, t=8, b=9):
    w, h = img.size
    face = img.crop((0, t, w, h - b))
    out = Image.new("RGBA", (w, out_h), (0, 0, 0, 0))
    out.paste(img.crop((0, 0, w, t)), (0, 0))
    out.paste(face.resize((w, out_h - t - b), Image.BILINEAR), (0, t))
    out.paste(img.crop((0, h - b, w, h)), (0, out_h - b))
    return out


def build(kind, v):
    src = Image.open(ASSETS / f"x_ui_node_{kind}_off.png").convert("RGBA")
    img = stretch_h(src, 296, *NINE[kind])
    if v["h"] != 65:
        img = stretch_v(img, v["h"])
    return img


def face_rows(img):
    a = list(img.getchannel("A").resize((1, img.size[1]), Image.BOX).getdata())
    ys = [i for i, x in enumerate(a) if x > 200]
    return (ys[0], ys[-1])


def wrap(txt, f, box):
    per = max(1, int(box // f))
    return [txt[i:i + per] for i in range(0, len(txt), per)] or [""]


def main():
    global BG
    shot = Image.open(REAL).convert("RGB")
    import numpy as np
    patch = np.asarray(shot.crop((200, 620, 1200, 1000))).reshape(-1, 3)
    BG = tuple(int(v) for v in patch.mean(axis=0))                 # 真实图表底色（干净区均值）
    print("bg =", BG)

    f_title = font(30, True)
    f_h1 = font(24, True)
    f_note = font(18)
    f_tag = font(16)
    f_small = font(15)
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))

    COLS, NW, GAP, PADX = 3, 296, 24, 24
    panel_w = PADX * 2 + COLS * NW + (COLS - 1) * GAP
    W = panel_w + 40
    blocks = []
    for v in VARIANTS:
        rows = (len(SAMPLES) + COLS - 1) // COLS
        panel_h = 34 + rows * (v["h"] + 58)
        blocks.append((v, panel_h))
    H = 74 + 118 + sum(34 + 30 + ph + 30 for _v, ph in blocks) + 250
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    y = 20
    d.text((20, y), "流程图节点「两行标签装不装得下底板」· 三变体对比（程序化合成）", font=f_title, fill=FG)
    y += 34
    d.text((20, y), "底板（实体面）＝素材逐行平均 alpha>200 的行：三类实测均为 rows 8..55/56（上下各约 8px 羽化）", font=f_note, fill=DIM)
    y += 24
    d.text((20, y), "指标只看首行与末行：首行上留＝实体面上沿−首行墨迹顶；末行下留＝实体面下沿−末行墨迹底（负值＝溢出，标红）", font=f_note, fill=DIM)
    y += 30
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print("saved:", OUT, sheet.size)
    for v, _ in blocks:
        out = []
        for txt, kind in SAMPLES:
            node = build(kind, v)
            ft, fb = face_rows(node)
            lineH = int(v["f"] * v["ls"])
            lines = wrap(txt, v["f"], 240)
            top = (v["h"] - lineH * len(lines)) // 2
            up = top - ft                                   # 正 = 首行墨迹在实体面上沿之下（有余量）
            dn = fb - (top + (len(lines) - 1) * lineH + v["f"] - 1)
            out.append(f"{len(txt)}字:{len(lines)}行 上留{up}/下留{dn}")
        print(f"  {v['key']} face={face_rows(build('section', v))}  " + "  ".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

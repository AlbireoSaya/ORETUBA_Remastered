# -*- coding: utf-8 -*-
"""流程图节点「类型可区分」配色 · 三方案对比图（示意，非最终素材）

用途：ISSUE-20260927-05 —— 用户问「节点类型在本作配色下几乎同色」，需先出对比图再裁决。

输入（只读）：
  - 节点/标签底图：UI组\\krkr\\assets\\ui\\x_ui_node_{section,select,frag}_{off,on}.png
                   UI组\\krkr\\assets\\ui\\x_ui_label_{off,on}.png
  - 真实背景与「现状」取样：临时\\ui_run\\runtime\\savedata\\shot_77_flowchart.png（引擎自导实机图）
  - 节点尺寸/nine 取值：UI组\\流程图系统_版式规范.md §1.2 / §五.1（296×65；section l14 r16 / select l14 r13 / frag l14 r15）

输出：UI组\\_工作\\ISSUE-20260927-05_流程图实现\\取证\\对比_节点类型配色_三方案.png
     （`_工作/**/*.png` 被 .gitignore 排除 ⇒ 示意件不入库；本脚本入库）

工艺（全部程序化，可复现，非最终交付素材）：
  1) 九宫格横向拉伸：保留左右两端 1:1，只拉伸中段（BILINEAR）→ 236/263/228×65 → 296×65
  2) 改色：转 HSV，按方案**设定 H/S**、可选**乘 V**，保留原件的 V 明暗与 alpha
  3) 方案 A 的「加粗描边」＝对内缩 2px 的环带（MinFilter 形态学腐蚀后相减）填描边色
  4) 合成到实机截图取样的真实背景块上，1:1 摆放

⚠️ 本图只回答「三类如何区分」；**运行态**（未解锁/已读/可去/当前）与**连线色**是另两条轴，本图不裁。
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]          # _工作/ISSUE-…/复现脚本/<file> → worktree root
UI = ROOT / "工程" / "我们没有翅膀——格雷塔迦露德与柳木原" / "UI组"
ASSETS = UI / "krkr" / "assets" / "ui"
SCREEN = ROOT / "临时" / "ui_run" / "runtime" / "savedata" / "shot_77_flowchart.png"
EVID = UI / "_工作" / "ISSUE-20260927-05_流程图实现" / "取证"
OUT = EVID / "对比_节点类型配色_三方案.png"

W = 1320
M = 20
BG = (24, 31, 46)               # 画布底色（方案块之外）
FG = (232, 238, 246)
FG_DIM = (168, 180, 196)
FG_DIM2 = (120, 134, 152)
HL = (255, 214, 140)
INK = (44, 58, 80)              # 节点标签字色（三方案统一用深墨，便于对比）

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyhbd.ttc", 0), ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0), ("C:/Windows/Fonts/simsun.ttc", 0),
]
_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    cand = ([c for c in FONT_CANDIDATES if "bd" in c[0]] + FONT_CANDIDATES) if bold else FONT_CANDIDATES
    f = None
    for path, idx in cand:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                break
            except Exception:
                continue
    if f is None:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


# ---- 九宫格横向拉伸：两端保留 1:1，只拉中段 ----
def nine_stretch(img, out_w, l, r):
    w, h = img.size
    if w == out_w:
        return img.copy()
    mid_w = out_w - l - r
    out = Image.new("RGBA", (out_w, h), (0, 0, 0, 0))
    out.paste(img.crop((0, 0, l, h)), (0, 0))
    out.paste(img.crop((l, 0, w - r, h)).resize((mid_w, h), Image.BILINEAR), (l, 0))
    out.paste(img.crop((w - r, 0, w, h)), (out_w - r, 0))
    return out


# ---- 改色：设 H/S，可选乘 V；保留原件 V 与 alpha ----
def recolor(img, hue=None, sat=None, vmul=None):
    r, g, b, a = img.split()
    H, S, V = Image.merge("RGB", (r, g, b)).convert("HSV").split()
    if hue is not None:
        H = H.point(lambda _p: int(round(hue / 360.0 * 255)) & 0xFF)
    if sat is not None:
        S = S.point(lambda _p: max(0, min(255, int(round(sat * 255)))))
    if vmul is not None:
        V = V.point(lambda p: max(0, min(255, int(round(p * vmul)))))
    rgb = Image.merge("HSV", (H, S, V)).convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), a))


# ---- 内描边（形变后的环带，不改变外轮廓） ----
def inner_stroke(img, color, width):
    a = img.getchannel("A")
    mask = a.point(lambda p: 255 if p > 128 else 0)
    ring = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(width * 2 + 1)))
    out = img.copy()
    out.paste(Image.new("RGBA", img.size, color + (255,)), (0, 0), ring)
    return out


SCHEMES = [
    {
        "key": "A",
        "title": "方案 A · 同族三档色相 + 选择支加粗描边",
        "sub": "三类同属冰蓝族，靠色相档 + 饱和度 + 描边区分；偏离既有基调最小，改动量＝三张底图调色 + 1 张加描边",
        "kinds": {
            "section": (218, 0.20, 1.00, None, "冰蓝实底 · 无描边"),
            "select": (200, 0.55, 0.86, (42, 84, 144), "偏青蓝 + 2px 深蓝描边"),
            "frag": (268, 0.28, 1.00, None, "淡紫底 · 无描边"),
        },
    },
    {
        "key": "B",
        "title": "方案 B · 仅靠明暗差（最贴参照作风格）",
        "sub": "同一色相，只压明度与饱和度；风格最统一，但在深色底上的亮/中/暗三档区分力最弱",
        "kinds": {
            "section": (216, 0.10, 1.00, None, "最亮（原样）"),
            "select": (216, 0.10, 0.90, None, "中亮（V×0.90）"),
            "frag": (216, 0.10, 0.79, None, "最暗（V×0.79）"),
        },
    },
    {
        "key": "C",
        "title": "方案 C · 三类各用一个色相",
        "sub": "区分力最强，但整屏出现冰蓝/暖金/粉三块异色，与既有冰蓝霜白体系冲突最大；暖金亦与参照作 rline 线色接近",
        "kinds": {
            "section": (210, 0.25, 1.00, None, "冰蓝"),
            "select": (38, 0.60, 1.00, None, "暖金"),
            "frag": (336, 0.35, 1.00, None, "粉"),
        },
    },
]

NINE = {"section": (14, 16), "select": (14, 13), "frag": (14, 15)}
KIND_CN = {"section": "章节点", "select": "选择支节点", "frag": "番外节点"}


def build_node(kind, state, spec):
    src = Image.open(ASSETS / f"x_ui_node_{kind}_{state}.png").convert("RGBA")
    hue, sat, vmul, stroke, _note = spec
    img = nine_stretch(src, 296, *NINE[kind])
    img = recolor(img, hue=hue, sat=sat, vmul=vmul)
    if stroke:
        img = inner_stroke(img, stroke, 2)
    return img


def label_img(state="off"):
    src = Image.open(ASSETS / f"x_ui_label_{state}.png").convert("RGBA")
    return src.resize((333, 38), Image.BILINEAR)   # nine={0,0,0,0} = 整图非等比拉伸


def real_labels():
    import json
    tsv = UI.parent / "资源组" / "05_章节总表.tsv"
    spine = UI.parent / "资源组" / "剧本" / "spine.json"
    chapter, choice, side = "第一章 序", "要追上去吗？", "番外 · 后日谈"
    try:
        with open(tsv, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) <= 5:
                    continue
                t = cols[5].strip()
                if 4 <= len(t) <= 12 and "～" not in t and "　" not in t:
                    chapter = t
                    break
    except Exception as e:
        print("  [warn] tsv:", e)
    try:
        d = json.load(open(spine, encoding="utf-8"))
        for bp in d.get("branch_points", []):
            for ch in bp.get("choices", []) or []:
                if (ch or {}).get("text_cn") and 2 <= len(ch["text_cn"]) <= 12:
                    choice = ch["text_cn"]
                    break
            if choice != "要追上去吗？":
                break
        for ss in d.get("side_stories", []):
            t = (ss or {}).get("title_cn") or ""
            if 2 <= len(t) <= 14:
                side = t
                break
    except Exception as e:
        print("  [warn] spine:", e)
    return chapter, choice, side


def wrap(text, f, maxw, draw):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=f) <= maxw:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def main():
    if not SCREEN.exists():
        print("FATAL: no real screenshot:", SCREEN)
        return 1
    shot = Image.open(SCREEN).convert("RGB")
    print("real screenshot:", shot.size)

    bg_patch = shot.crop((70, 610, 70 + 1260, 940))       # 视口内干净区（样例节点在 y330..587）
    print("bg patch mean rgb:", bg_patch.resize((1, 1)).getpixel((0, 0)))

    chapter, choice, side = real_labels()
    print("labels:", chapter, "|", choice, "|", side)
    txt = {"section": chapter, "select": choice, "frag": side}

    ROW_H = 65
    rows = [("section", 30), ("select", 112), ("frag", 194), ("label", 272)]
    panel_h = 330
    head_h = 66
    cur_h = 420

    f_title = font(32, True)
    f_h1 = font(25, True)
    f_h2 = font(20)
    f_note = font(19)
    f_kind = font(23)
    f_col = font(18)
    f_node = font(22, True)
    note_lines = []

    notes = [
        "① 本图是程序化改色示意（HSV 设 H/S、可选乘 V，保留原件明暗与 alpha；九宫格拉宽只拉中段、两端 1:1），不是最终素材。选定方案后由正式脚本产出 x_ui_node_* 并重跑 emit_asset_index.py。",
        "② 节点内文字由引擎绘制，本图用微软雅黑近似；三方案字色统一用深墨 #2C3A50，以便只看底图差异——实际字色随方案微调。",
        "③ 本图只回答「三类如何区分」。运行态（未解锁/已读/可去/当前）是另一条轴：现有素材每类只有 off/on 两态，状态区分拟主要靠连线色（版式规范 R5），节点态图缺口另行登记。",
        "④ 本图未做整屏合成。选定方案后我会把该方案落成正式素材、跑一遍实机巡演出整屏图，再交你终判。",
        "⑤ 文案取真实数据：章节点取自 05_章节总表 章节标题，选择支取自 spine.json 选项文本，番外取自 side_stories 的 title_cn。",
    ]
    scratch = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for s in notes:
        note_lines += wrap(s, f_note, W - M * 2, scratch)
    note_h = len(note_lines) * 26 + 34

    line_rows = 3
    line_h = 34 * line_rows + 60

    H = (M + 40) + (34 + cur_h + 24) + 3 * (head_h + panel_h + 26) + (34 + line_h + 24) + note_h + 24
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    y = M
    d.text((M, y), "流程图节点「类型可区分」配色 · 三方案对比（示意）", font=f_title, fill=FG)
    d.text((W - 372, y + 8), "画布 1920×1080 · 节点 1:1 实尺寸 296×65", font=f_col, fill=FG_DIM)
    y += 40

    # ---------- 现状 ----------
    d.text((M, y), "现状：三类节点底图几乎同色（实测底色差 ≤4/255，图上只差文字）", font=f_h1, fill=HL)
    y += 34
    crop = shot.crop((520, 315, 900, 605))
    sheet.paste(crop, (M, y))
    d.rectangle([M, y, M + 380, y + 290], outline=(90, 104, 124))
    d.text((M + 4, y + 296), "1:1 特写：章节点 / 选择支节点 / 番外节点（仅文字不同）", font=f_col, fill=FG_DIM)
    tx = M + 420
    d.text((tx, y + 10), "问题", font=f_h2, fill=FG)
    for i, s in enumerate([
        "三类底图实测 fill：",
        "  章节点 #E4EBF5 ／ 选择支 #E2EDF8 ／ 番外 #E2ECF6",
        "三者色差 ≤4/255，肉眼不可辨。",
        "",
        "本作是「冰蓝霜白磨砂玻璃」单色系",
        "（M34 起只换配色、按《交汇协奏曲》",
        "PSB 结构复刻），所以三类必须在我方",
        "这一套配色内部自行拉开差距。",
    ]):
        d.text((tx, y + 40 + i * 26), s, font=f_note, fill=FG_DIM if i != 2 else FG)
    y += cur_h

    # ---------- 三方案 ----------
    for sc in SCHEMES:
        d.text((M, y), sc["title"], font=f_h1, fill=HL)
        d.text((W - 96, y + 4), f"方案 {sc['key']}", font=f_col, fill=FG_DIM2)
        y += 32
        d.text((M, y), sc["sub"], font=f_h2, fill=FG_DIM)
        y += head_h - 32
        sheet.paste(bg_patch, (30, y))
        d.rectangle([30, y, 30 + 1260, y + panel_h], outline=(70, 84, 104))
        py = y
        d.text((176, py + 6), "常态（off）", font=f_col, fill=FG_DIM)
        d.text((526, py + 6), "悬停（on）", font=f_col, fill=FG_DIM)
        for kind, ry in rows:
            by = py + ry
            if kind == "label":
                d.text((44, by + 8), "关联标签", font=f_kind, fill=FG)
                off_l, on_l = label_img("off"), label_img("on")
                sheet.paste(off_l, (150, by), off_l)
                sheet.paste(on_l, (500, by), on_l)
                d.text((860, by + 8), "保持原样（现有形态已与节点可区分）", font=f_note, fill=FG_DIM)
                continue
            spec = sc["kinds"][kind]
            off = build_node(kind, "off", spec)
            on = build_node(kind, "on", spec)
            d.text((44, by + 20), KIND_CN[kind], font=f_kind, fill=FG)
            sheet.paste(off, (150, by), off)
            sheet.paste(on, (500, by), on)
            tw = d.textlength(txt[kind], font=f_node)
            d.text((150 + (296 - tw) / 2, by + 21), txt[kind], font=f_node, fill=INK)
            d.text((500 + (296 - tw) / 2, by + 21), txt[kind], font=f_node, fill=INK)
            d.text((860, by + 10), spec[4], font=f_note, fill=FG_DIM)
            d.text((860, by + 34), f"H={spec[0]}° S={spec[1]:.2f} V×{spec[2]:.2f}", font=f_col, fill=FG_DIM2)
        y += panel_h + 6
        y += 20

    # ---------- 连线色带（仅参考） ----------
    d.text((M, y), "连线色（参照作取值，本轮仅供参考——连线配色另行裁决）", font=f_h1, fill=HL)
    y += 34
    sheet.paste(bg_patch.crop((0, 0, 1260, line_h - 20)), (30, y))
    ly = y + 26
    for i, (lab, col, wd, arrow) in enumerate([
        ("normal（可去）0xFF65B1D4 · 5px 实心箭头", (0x65, 0xB1, 0xD4), 5, True),
        ("nojump（无箭头）0xFF808080 · 3px", (0x80, 0x80, 0x80), 3, False),
        ("rline（特殊）0xFFCBD465 · 6px", (0xCB, 0xD4, 0x65), 6, True),
    ]):
        yy = ly + i * 34
        d.text((44, yy - 6), lab, font=f_col, fill=FG)
        x0, x1 = 470, 700
        d.line([x0, yy + 4, x1 - 40, yy + 4], fill=col, width=wd)
        d.line([x1 - 40, yy + 4, x1 - 40, yy + 20], fill=col, width=wd)
        if arrow:
            d.polygon([(x1 - 48, yy + 20), (x1 - 32, yy + 20), (x1 - 40, yy + 34)], fill=col)
    y += line_h

    # ---------- 口径说明 ----------
    d.text((M, y), "口径与边界", font=f_h2, fill=FG)
    for i, s in enumerate(note_lines):
        d.text((M, y + 30 + i * 26), s, font=f_note, fill=FG_DIM)

    EVID.mkdir(parents=True, exist_ok=True)
    bg_patch.save(EVID / "_bg_patch_real.png")
    sheet.save(OUT)
    print("saved:", OUT, sheet.size)
    # 逐方案实测 fill 色（记录用）
    for sc in SCHEMES:
        vals = []
        for k in ("section", "select", "frag"):
            im = build_node(k, "off", sc["kinds"][k])
            vals.append(f"{k}=#{im.convert('RGB').getpixel((148, 10))[0]:02X}{im.convert('RGB').getpixel((148,10))[1]:02X}{im.convert('RGB').getpixel((148,10))[2]:02X}")
        print("  ", sc["key"], " ".join(vals))
    return 0


if __name__ == "__main__":
    sys.exit(main())

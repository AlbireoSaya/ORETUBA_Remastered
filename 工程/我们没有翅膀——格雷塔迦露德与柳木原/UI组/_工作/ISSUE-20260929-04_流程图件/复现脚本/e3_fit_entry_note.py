# -*- coding: utf-8 -*-
r"""E3 · 番外入口标记（`x_ui_entry_note.png`）：量测、规格化、对照图。

ISSUE-20260929-04 ｜ 冻结书 §A 第 3 行。

    python e3_fit_entry_note.py measure            # 量测全部候选（bbox / 比例 / 槽内可视尺寸）
    python e3_fit_entry_note.py fit E3-J           # 规格化到 86×48 写入 assets（定稿口径）
    python e3_fit_entry_note.py sheet              # 出对照图 证据\E3_入口图标_候选与定稿.png

规格化口径（三条，缺一不可）：
  ① 去尘：α ≤ DUST_GATE 归零（模型在透明区留了 α≈1–2 的灰点，实测）；
  ② 裁到 α > INK_GATE 的内容 bbox（防模型留白偏心）；
  ③ 等比 contain 进**内缩 INSET px** 的框 ⇒ 最外 1px 帧 αmax=0，且绝不非等比拉伸。
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_DIR = os.path.dirname(HERE)
SRC = os.path.join(ITEM_DIR, "生图")
EV = os.path.join(ITEM_DIR, "证据")
UI = os.path.normpath(os.path.join(ITEM_DIR, "..", "..", "krkr", "assets", "ui"))
TARGET = (86, 48)
DUST_GATE = 6
INK_GATE = 8
INSET = 2
FINAL_NAME = "x_ui_entry_note.png"
SHEET_W = 1500

CAND_ORDER = ["E3-A", "E3-B", "E3-C", "E3-D", "E3-E", "E3-F",
              "E3-G", "E3-H", "E3-I", "E3-J"]

# 逐件目视评语（一句：像什么 / 缺什么）—— 作者目视结论，非自动生成
# 注：括号内的比例与槽内尺寸一律**照抄 measure_one 的实测值**（去尘 α≤6 ＋ bbox α>8 口径），不得手写估计。
VERDICTS = {
    "E3-A": "最本能的「书签」形（燕尾＋小孔）；但整幅 0.39:1，等比进 86×48 只剩 17×44（约 17px 宽），槽位八成空置，小孔缩到约 1px 已不可辨。",
    "E3-B": "斜置 30° 让占位好一些（27×44）；但「为何是斜的」无理由，斜置后柔光轮廓发糊，正式感最弱。",
    "E3-C": "比例 1.85 几乎正合槽位（82×44，填充 87%）；但 1:1 下折角只剩一小道弧，整体读作「一块宽底板」——与现占位件最难区分的一件。",
    "E3-D": "近正方纸页（右上折角），1:1 轮廓清楚；但 1.8:1 的槽里只占 44×44，左右各空 21px，像小纸片，未用满槽位。",
    "E3-E": "窄带书签（孔＋浅尖）比例 0.22:1，等比进槽只剩 10×44（约 10px 宽）—— 不可用。",
    "E3-F": "横置吊牌（孔＋燕尾）比例 2.47，1:1 可辨；但描边偏细偏淡，缩小后外轮廓发虚（横置方案第一版）。",
    "E3-G": "比例 1.63，最贴槽位（72×44）；但折角太克制，1:1 下几乎看不出折痕，风险同 C。",
    "E3-H": "粗描边让 1:1 轮廓清楚、孔与燕尾都可辨；整幅 2.62:1 偏宽 ⇒ 槽内 82×31，纵向空掉一半（横置精修第一版）。",
    "E3-I": "1:1 折角清楚、填槽最好（73×44、实体 70×40）；但轮廓＝「宽底板＋一角折起」，仍属底板族，与现占位件的形状差异最小。",
    "E3-J": "★定稿：孔（带环）＋深燕尾＋均匀粗冰蓝描边，1:1 下三者都清楚；语义＝书签／吊牌（入口标记），与正下方组名底板同色族而轮廓完全不同；整幅 2.71:1 ⇒ 槽内 82×30（宽向用满、纵向等比居中）。",
}


def bbox_gate(alpha_img, gate):
    return alpha_img.point(lambda v: 255 if v > gate else 0).getbbox()


def load_meta():
    p = os.path.join(SRC, "_meta.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def cand_path(cid):
    cands = [f for f in os.listdir(SRC) if f.startswith(cid + "_") and f.endswith(".png")]
    return os.path.join(SRC, cands[0]) if cands else None


def measure_one(cid):
    p = cand_path(cid)
    if not p:
        return None
    im = Image.open(p).convert("RGBA")
    a = im.getchannel("A").point(lambda v: 0 if v <= DUST_GATE else v)
    ib = bbox_gate(a, INK_GATE)
    cb = bbox_gate(im.getchannel("A"), 200)
    px = list(im.getchannel("A").getdata())
    r = {"id": cid, "file": os.path.basename(p), "canvas": list(im.size),
         "ink_bbox": list(ib), "ink_size": [ib[2] - ib[0], ib[3] - ib[1]],
         "core_bbox": list(cb), "core_size": [cb[2] - cb[0], cb[3] - cb[1]],
         "alpha_zero": sum(1 for v in px if v == 0),
         "alpha_full": sum(1 for v in px if v == 255),
         "alpha_mid": sum(1 for v in px if 0 < v < 255),
         "total_px": len(px), "alpha_extrema": list(im.getchannel("A").getextrema())}
    iw, ih = r["ink_size"]
    r["ink_aspect"] = round(iw / ih, 3)
    bw, bh = TARGET[0] - 2 * INSET, TARGET[1] - 2 * INSET
    k = min(bw / iw, bh / ih)
    r["fit_scale"] = round(k, 6)
    r["fit_at_slot"] = [round(iw * k, 1), round(ih * k, 1)]
    cw, ch = r["core_size"]
    r["core_at_slot"] = [round(cw * k, 1), round(ch * k, 1)]
    r["fill_ratio"] = round((iw * k) * (ih * k) / (TARGET[0] * TARGET[1]), 4)
    return r


# ---------------------------------------------------------------- 规格化
def normalize(cid, gate_dust=DUST_GATE, gate_ink=INK_GATE, inset=INSET):
    p = cand_path(cid)
    raw = Image.open(p).convert("RGBA")
    src_canvas = list(raw.size)
    a = raw.getchannel("A").point(lambda v: 0 if v <= gate_dust else v)
    raw.putalpha(a)
    ib = bbox_gate(a, gate_ink)
    im = raw.crop(ib)
    bw, bh = TARGET[0] - 2 * inset, TARGET[1] - 2 * inset
    k = min(bw / im.width, bh / im.height)
    nw, nh = max(1, int(round(im.width * k))), max(1, int(round(im.height * k)))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", TARGET, (0, 0, 0, 0))
    canvas.paste(im, ((TARGET[0] - nw) // 2, (TARGET[1] - nh) // 2), im)
    return canvas, {"source": os.path.basename(p), "source_canvas": src_canvas,
                    "dust_gate": gate_dust, "ink_gate": gate_ink, "inset": inset,
                    "crop_bbox": list(ib), "crop_size": [ib[2] - ib[0], ib[3] - ib[1]],
                    "resize": [nw, nh], "scale": round(k, 6), "target": list(TARGET)}


def fit(cid):
    canvas, info = normalize(cid)
    dst = os.path.join(UI, FINAL_NAME)
    canvas.save(dst)
    ca = canvas.getchannel("A")
    frame = [ca.getpixel((x, 0)) for x in range(TARGET[0])]
    frame += [ca.getpixel((x, TARGET[1] - 1)) for x in range(TARGET[0])]
    frame += [ca.getpixel((0, y)) for y in range(TARGET[1])]
    frame += [ca.getpixel((TARGET[0] - 1, y)) for y in range(TARGET[1])]
    info.update({"out": dst, "outer_frame_alpha_max": max(frame),
                 "alpha_extrema": list(ca.getextrema())})
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


# ---------------------------------------------------------------- 绘图工具
def checker(size, sq=8):
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], sq):
        for x in range(0, size[0], sq):
            if ((x // sq) + (y // sq)) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(222, 226, 233))
    return im


def over(im):
    return Image.alpha_composite(checker(im.size).convert("RGBA"), im).convert("RGB")


def font(size, bold=False):
    for n in ("msyh.ttc", "msyhbd.ttc"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def thumb(im, box):
    k = min(box[0] / im.width, box[1] / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def stage_bg():
    r"""真机舞台：bg72.png(2560×1440) 0.75× + fc.dim 60%（冻结书 §B 的 fc.bg 语境）。"""
    bg = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一_超分\CG背景\bg72.png"
    if not os.path.exists(bg):
        return Image.new("RGB", (1920, 1080), (30, 34, 40))
    s = Image.open(bg).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    return Image.blend(s, Image.new("RGB", (1920, 1080), (0, 0, 0)), 0.60)


def stage_scene(icon, region=(40, 175, 420, 300), zoom=5):
    """把图标放到真实位置 (183,190,86×48)，下面接组名底板 (60,242,333×38)。"""
    s = stage_bg().convert("RGBA")
    lb = Image.open(os.path.join(UI, "x_ui_label_off.png")).convert("RGBA")
    s.alpha_composite(lb, (60, 242))
    if icon is not None:
        s.alpha_composite(icon, (183, 190))
    x0, y0, x1, y1 = region
    return s.crop(region).convert("RGB").resize(((x1 - x0) * zoom, (y1 - y0) * zoom), Image.NEAREST)


# ---------------------------------------------------------------- 对照图
def wrap(dr, text, fnt, width):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if dr.textlength(cur + ch, font=fnt) > width:
            lines.append(cur); cur = ch
        else:
            cur += ch
    lines.append(cur)
    return lines


def section(title):
    """开一个自带画布的小节（避免整图 y 偏移算错相撞）。"""
    W = SHEET_W
    hb = 46
    img = Image.new("RGB", (W, hb), (238, 243, 250))
    d = ImageDraw.Draw(img)
    d.text((20, 9), title, font=font(25), fill=(16, 32, 64))
    d.line([(0, hb - 2), (W, hb - 2)], fill=(176, 194, 214), width=2)
    return img, d, hb


def stack(header, body):
    out = Image.new("RGB", (SHEET_W, header.height + body.height), (255, 255, 255))
    out.paste(header, (0, 0))
    out.paste(body, (0, header.height))
    return out


def sheet():
    rows = [measure_one(c) for c in CAND_ORDER]
    rows = [r for r in rows if r]
    meta = load_meta()
    final = Image.open(os.path.join(UI, FINAL_NAME)).convert("RGBA")
    ph = Image.open(os.path.join(UI, "x_ui_fusen_off.png")).convert("RGBA")
    lb = Image.open(os.path.join(UI, "x_ui_label_off.png")).convert("RGBA")
    fs, fm = font(17), font(15)

    secs = []

    # ── §1 候选一览（单列宽行：缩略 + 槽位 2× + 量测 + 逐件评语）
    img, d, hb = section("§1 候选一览（10 件 · 原图缩略 ＋ 目标槽 86×48 的 2× 观感 ＋ 逐件评语；槽内尺寸按源 bbox 推导，定稿实测见 §2）")
    rh, y0 = 132, hb + 8
    body = Image.new("RGB", (SHEET_W, rh * len(rows) + 8), (255, 255, 255))
    bd = ImageDraw.Draw(body)
    for i, r in enumerate(rows):
        yy = 4 + i * rh
        raw = Image.open(os.path.join(SRC, r["file"])).convert("RGBA")
        body.paste(over(thumb(raw, (152, 112))), (12, yy + 8))
        slot = normalize(r["id"])[0].resize((129, 72), Image.LANCZOS)
        body.paste(over(slot), (180, yy + 28))
        m = meta.get(r["id"], {})
        bd.text((322, yy + 6), "%s ｜ %s ｜ 源 %d×%d" % (r["id"], m.get("model", "?"),
                                                        r["canvas"][0], r["canvas"][1]),
                font=font(19), fill=(24, 42, 78))
        bd.text((322, yy + 30), "整幅比例 %.2f:1　⇒　槽内可视 %.0f×%.0f　（实体 %.0f×%.0f，填充 %.0f%%）"
                % (r["ink_aspect"], r["fit_at_slot"][0], r["fit_at_slot"][1],
                   r["core_at_slot"][0], r["core_at_slot"][1], 100 * r["fill_ratio"]),
                font=fm, fill=(70, 82, 100))
        for j, ln in enumerate(wrap(bd, VERDICTS.get(r["id"], ""), fs, 1140)[:3]):
            bd.text((322, yy + 54 + 21 * j), ln, font=fs, fill=(44, 52, 66))
        bd.line([(12, yy + rh - 3), (SHEET_W - 12, yy + rh - 3)], fill=(228, 234, 242))
    img1 = Image.new("RGB", (SHEET_W, hb + body.height))
    img1.paste(img, (0, 0))
    img1.paste(body, (0, hb))
    img = img1

    # ── §2 定稿 4× ＋ 与现占位件并排
    img2, d2, hb2 = section("§2 定稿 4× 放大 ｜ 与现占位件 x_ui_fusen_off.png（仍在用，不删）并排观察")
    b2 = Image.new("RGB", (SHEET_W, 350), (255, 255, 255))
    d9 = ImageDraw.Draw(b2)
    z = 4
    b2.paste(over(final.resize((86 * z, 48 * z), Image.LANCZOS)), (24, 38))
    b2.paste(over(ph.resize((86 * z, 48 * z), Image.LANCZOS)), (24 + 86 * z + 50, 38))
    d9.text((24, 8), "★ 定稿 x_ui_entry_note.png（4×）", font=font(20), fill=(14, 82, 34))
    d9.text((24 + 86 * z + 50, 8), "现占位件 x_ui_fusen_off.png（4×）", font=font(20), fill=(158, 38, 38))
    det = ("（两图均为 86×48 → 4× 放大，棋盘＝透明底；右件的原文件仍在用、本轮不删）
"
           "定稿实测：墨迹 bbox(α>8) 79×28 ｜ 实体 bbox(α>200) 76×24 ｜ 最外 1px 帧 αmax=0 ｜ α 全域 0..255（真 alpha，非棋盘格烘焙）\n"
           "并排评语：新件读作「书签／吊牌」——小圆孔 ＋ 燕尾缺口是现占位件完全没有的形状语素，语义上就是「入口标记」；"
           "两件同为霜白填充＋冰蓝描边的同色族\n"
           "（实测 body 均值：定稿 (210,229,247) vs 占位件 (217,230,242)），并置不生分。差别在「有没有被设计过」："
           "占位件是一枚无描边、无形状语素的空白药丸，新件有明确轮廓与均匀冰蓝描边。")
    yy = 38 + 48 * z + 16
    for j, ln in enumerate(wrap(d9, det, fs, SHEET_W - 56)):
        d9.text((24, yy + 26 * j), ln, font=fs, fill=(48, 56, 70))
    img2 = stack(img2, b2)

    # ── §3 同屏示意
    img3, d3, hb3 = section("§3 同屏示意（真机尺度 1:1 ＝ bg72 0.75× ＋ fc.dim 60% ＋ 组名底板，再 3× nearest 放大）")
    reg, zz = (150, 180, 400, 290), 3
    rows3 = [("★ 定稿（＋ 组名底板）", final, (14, 82, 34),
              "定稿是「被设计过的一枚入口标记」：小圆孔 ＋ 燕尾缺口在 1:1 下都清楚，\n"
              "与正下方组名底板同色族而轮廓完全不同，不会与底板混为一体。"),
             ("现占位件（＋ 组名底板）", ph, (158, 38, 38),
              "占位件是同一槽位的一枚空白药丸：无描边、无形状语素，\n"
              "与下方底板同形同色 ⇒ 两枚「宽底板」上下叠，读者不知道它是什么。"),
             ("仅组名底板（无入口件）", None, (70, 82, 100),
              "对照基线：本行本来就有的组名底板（333×38，x60/y242 起）。")]
    rowh = (reg[3] - reg[1]) * zz + 74
    b3 = Image.new("RGB", (SHEET_W, rowh * len(rows3) + 40), (255, 255, 255))
    d9 = ImageDraw.Draw(b3)
    for i, (lab, icon, col, note) in enumerate(rows3):
        yy = 6 + i * rowh
        b3.paste(stage_scene(icon, reg, zz), (24, yy))
        d9.text((24, yy + (reg[3] - reg[1]) * zz + 8), lab, font=font(20), fill=col)
        for j, ln in enumerate(note.split("\n")):
            d9.text(((reg[2] - reg[0]) * zz + 110, yy + 60 + 26 * j), ln, font=fs, fill=(48, 56, 70))
    d9.text((24, 6 + rowh * len(rows3)),
            "版式事实（layout\\screens\\32_flowchart.json）：fc.entry.NNNN 在 (183, 190/285/380/475/570/665, 86×48)，"
            "组名底板 fc.label.NNNN 在 (60, 242/337/432/527/622/717, 333×38) —— 入口件正压在本组底板正上方居中。",
            font=fs, fill=(90, 100, 116))
    img3 = stack(img3, b3)

    # ── §4 结论
    img4, d4, hb4 = section("§4 结论与可复现信息")
    tail = ("定稿：E3-J ｜ gpt-image-2.5-1k ｜ 1536×1024 ｜ 源整幅 2.68:1 → 去尘(α≤6 归零) → 裁 α>8 内容 bbox → 等比 contain 居中进内缩 82×44 → 落 86×48 RGBA。\n"
            "复现：python 复现脚本\\e3_gen_entry_note.py only E3-J　｜　python 复现脚本\\e3_fit_entry_note.py fit E3-J\n"
            "提示词原文、逐件 HTTP／耗时／产物尺寸、量测表见 证据\\E3_入口图标_参数与记录.md；自证见 证据\\E3_自证报告.md。\n"
            "备选（若主代理／用户更想要「折角便签」读法）：E3-I —— 一条命令可换：python 复现脚本\\e3_fit_entry_note.py fit E3-I。")
    for j, ln in enumerate(tail.split("\n")):
        d4.text((24, hb4 + 10 + 26 * j), ln, font=fs, fill=(48, 56, 70))
    b4 = Image.new("RGB", (SHEET_W, hb4 + 10 + 26 * 4 + 12))
    b4.paste(img4, (0, 0))
    dd = ImageDraw.Draw(b4)
    for j, ln in enumerate(tail.split("\n")):
        dd.text((24, hb4 + 10 + 26 * j), ln, font=fs, fill=(48, 56, 70))
    img4 = b4

    secs = [img, img2, img3, img4]
    # 标题条
    head = Image.new("RGB", (SHEET_W, 92), (255, 255, 255))
    hd = ImageDraw.Draw(head)
    hd.text((20, 12), "E3 · 流程图屏「番外入口」标记 x_ui_entry_note.png —— 候选、定稿与并排观察", font=font(30), fill=(10, 26, 56))
    hd.text((20, 54), "规格（接口冻结 §A 第 3 行）：86×48 RGBA 真 alpha ｜ 书签／折角便签形状 ｜ 一枚 ｜ 纯图形、无任何文字 ｜ 冰蓝霜白同族",
            font=font(16), fill=(74, 86, 104))

    total = 92 + sum(s.height + 14 for s in secs) + 10
    out_img = Image.new("RGB", (SHEET_W, total), (255, 255, 255))
    yy = 0
    out_img.paste(head, (0, yy)); yy += 92
    for s in secs:
        out_img.paste(s, (0, yy)); yy += s.height + 14
    out = os.path.join(EV, "E3_入口图标_候选与定稿.png")
    out_img.save(out)
    print("对照图：", out, out_img.size)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "measure":
        for c in CAND_ORDER:
            r = measure_one(c)
            if r:
                print(json.dumps(r, ensure_ascii=False))
    elif a[0] == "fit":
        fit(a[1])
    elif a[0] == "sheet":
        sheet()
    else:
        raise SystemExit("用法：e3_fit_entry_note.py [measure|fit <id>|sheet]")

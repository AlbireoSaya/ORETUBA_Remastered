# -*- coding: utf-8 -*-
r"""psv_config_evidence.py —— 修复轮证据图：把 `psv_config_render.py` 的 1:1 合成图裁成
「修前 / 修后」对照小图（每条缺陷一张），另出两页整页对照与残留带前后对照。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏修复\复现脚本\psv_config_evidence.py
"""
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
E = os.path.join(UI, "_工作", "ISSUE-20260926-06_C设置屏修复", "_证据")
BAR = (255, 0, 128)

# (输出名, 用哪一对, 裁剪框, 放大倍率, 说明)
CROPS = [
    ("d1_heading_sys", "sys", (110, 150, 520, 300), 2,
     "缺陷①：节题「画面设定」——修前洗白（引擎浅字压浅霜板）/ 修后墨色可读，且让开页签药丸"),
    ("d1_heading_snd", "snd", (110, 150, 520, 300), 2,
     "缺陷①：节题「音量设定」（声音页）"),
    ("d2_value_offrows", "sys", (690, 470, 1000, 700), 2,
     "缺陷②：语音截断 / 隐藏光标两行（当前值 = OFF）——修前整行无药丸 / 修后右槽同款药丸 + 暗字"),
    ("d4_preview_note", "sys", (1160, 820, 1810, 920), 2,
     "缺陷④：预览说明段（#B8B8C8 → #3E4E70，加深 2 档）与右列标签"),
    ("d4_right_labels", "sys", (1160, 200, 1810, 420), 2,
     "缺陷④：右列标签「文本窗口的不透明度」等正压雪花白装饰处"),
    ("d5_6_snd_left", "snd", (120, 440, 800, 800), 2,
     "缺陷⑤⑥：声音页左栏——修前壳左沿 152 / 组题「语音设定」在栏尾（152,706）；"
     "修后壳左沿 136（对齐系统页）、组题上移到 (136,552) 其组之前、后两行下移一档"),
]
PAIRS = [("d2_display_full", "sysfull", (690, 200, 1200, 340), 2,
          "缺陷②：画面模式「全屏模式」为当前值时（shot_19 的状态）——修前整行无药丸 / 修后右槽药丸")]


def stack(pairs, box, zoom, title, out):
    ims = []
    for tag, path in pairs:
        im = Image.open(path).convert("RGB").crop(box)
        ims.append((tag, im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)))
    w = ims[0][1].width
    h = sum(i[1].height for i in ims) + 6 * (len(ims) - 1)
    sheet = Image.new("RGB", (w, h), BAR)
    y = 0
    for _, im in ims:
        sheet.paste(im, (0, y))
        y += im.height + 6
    sheet.save(os.path.join(E, out + ".png"))
    print("  %-22s %s" % (out, title))


def main():
    before_sys = os.path.join(E, "r01_before_sys.png")
    after_sys = os.path.join(E, "r02_after_sys.png")
    before_snd = os.path.join(E, "r03_before_snd.png")
    after_snd = os.path.join(E, "r04_after_snd.png")
    bfull = os.path.join(E, "r06_before_sys_displayfull.png")
    afull = os.path.join(E, "r05_after_sys_displayfull.png")
    src = {"sys": (before_sys, after_sys), "snd": (before_snd, after_snd),
           "sysfull": (bfull, afull)}
    print("证据图（上=修前，下=修后；品红分隔条）：")
    for out, kind, box, zoom, title in CROPS:
        stack([("before", src[kind][0]), ("after", src[kind][1])], box, zoom, title, out)
    for out, kind, box, zoom, title in PAIRS:
        stack([("before", src[kind][0]), ("after", src[kind][1])], box, zoom, title, out)
    # 整页对照（缩到 960 宽，横向并列）
    for tag, (b, a) in (("sys", (before_sys, after_sys)), ("snd", (before_snd, after_snd))):
        ib = Image.open(b).convert("RGB").resize((960, 540), Image.LANCZOS)
        ia = Image.open(a).convert("RGB").resize((960, 540), Image.LANCZOS)
        sheet = Image.new("RGB", (960, 1086), BAR)
        sheet.paste(ib, (0, 0))
        sheet.paste(ia, (0, 546))
        sheet.save(os.path.join(E, "fullpage_%s_before_after.png" % tag))
        print("  fullpage_%s_before_after  整页对照（上=修前 下=修后）" % tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())

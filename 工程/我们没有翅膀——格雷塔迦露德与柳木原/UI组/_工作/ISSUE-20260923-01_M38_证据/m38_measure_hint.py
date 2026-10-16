# -*- coding: utf-8 -*-
"""M38 临时脚本：量 dlg.hint 的两版候选文案在 24px 下的像素宽度，决定是否加「右缘：快捷条」。
用 Microsoft YaHei（krkr fallback_faces[0]，也是 HTML 侧的 CSS 首选）度量。
"""
import json
import os

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
LAY = os.path.join(UI, "layout")

sc = json.load(open(os.path.join(LAY, "screens", "10_dialog.json"), encoding="utf-8"))
hint = [e for e in sc["elements"] if e["id"] == "dlg.hint"][0]
W = hint["w"]
SIZE = hint["font"]["size"]
print("dlg.hint 现框宽 w=%s  字号 size=%s" % (W, SIZE))

CANDIDATES = [
    ("旧（现盘）", "右键：功能图标　空格：快进　Esc：菜单"),
    ("新 A（订正 Esc）", "右键：功能图标　空格：快进　Esc：返回"),
    ("新 B（+右缘快捷条）", "右键：功能图标　空格：快进　Esc：返回　右缘：快捷条"),
]

FACES = ["msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc"]
font = None
used = None
for f in FACES:
    p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
    if os.path.exists(p):
        try:
            font = ImageFont.truetype(p, SIZE)
            used = p
            break
        except Exception as e:
            print("  load fail %s: %s" % (p, e))
print("度量字体：%s" % used)
for tag, s in CANDIDATES:
    w = font.getlength(s)
    print("  %-20s 宽=%7.1f px  占框 %.1f%%  %s  文案=%s"
          % (tag, w, 100.0 * w / W, "OK" if w <= W else "**超宽**", s))

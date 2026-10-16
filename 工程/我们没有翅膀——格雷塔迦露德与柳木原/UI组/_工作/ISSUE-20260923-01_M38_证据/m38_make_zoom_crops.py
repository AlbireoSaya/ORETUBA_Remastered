# -*- coding: utf-8 -*-
r"""M38 · 生成证据用的放大裁切图（全部取自**引擎自己导出的** shot_*.png，非窗口抓屏）

产物（同目录）：
  · `M38_放大裁切_名字+正文_2x.png`        —— 默认态 shot_03 的名字框+正文框 2x（无框方案观感 + 描边可读性）
  · `M38_放大裁切_名字_旧vs新_5x配对.png`  —— 名字框 5x，上=旧渲染器（无描边）／下=M38 新实现（2px 描边）
                                             （同一数据、同一帧号，只差渲染器代码 ⇒ 描边效果的直接对照）
几何一律取自 `layout/screens/10_dialog.json`，本脚本不写死坐标。
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
SC = json.load(open(os.path.join(UI, "layout", "screens", "10_dialog.json"), encoding="utf-8"))
EL = {e["id"]: e for e in SC["elements"]}


def rect(eid, pad=0):
    e = EL[eid]
    return (int(e["x"]) - pad, int(e["y"]) - pad,
            int(e["x"]) + int(e["w"]) + pad, int(e["y"]) + int(e["h"]) + pad)


NEW = Image.open(os.path.join(HERE, "M38_AB_新实现_shot_03_dialog.png")).convert("RGB")
OLD = Image.open(os.path.join(HERE, "M38_AB_旧渲染器_shot_03_dialog.png")).convert("RGB")

# ① 名字 + 正文（上沿取名字框上沿 −6，下沿取正文框上沿 + 3 行 ≈ 180px）
x0, y0 = rect("dlg.name", 6)[0], rect("dlg.name", 6)[1]
x1 = rect("dlg.text", 6)[2]
y1 = rect("dlg.text", 6)[1] + 180
crop = NEW.crop((x0, y0, x1, y1))
Z = 2
crop.resize((crop.width * Z, crop.height * Z), Image.NEAREST).save(
    os.path.join(HERE, "M38_放大裁切_名字+正文_2x.png"))
print("① 名字+正文 2x：画布区域 %s → %dx%d" % ((x0, y0, x1, y1), crop.width * Z, crop.height * Z))

# ② 名字框 5x：旧（无描边）在上、新（2px 描边）在下，中间留 6px 白缝
nb = rect("dlg.name", 4)
cn = NEW.crop(nb)
co = OLD.crop(nb)
Z2 = 5
w, h = cn.width * Z2, cn.height * Z2
pair = Image.new("RGB", (w, h * 2 + 6), (255, 255, 255))
pair.paste(co.resize((w, h), Image.NEAREST), (0, 0))
pair.paste(cn.resize((w, h), Image.NEAREST), (0, h + 6))
pair.save(os.path.join(HERE, "M38_放大裁切_名字_旧vs新_5x配对.png"))
print("② 名字 5x 配对：%s → %dx%d（上=旧渲染器/无描边，下=M38 新实现/2px 描边）"
      % ((nb,), w, h * 2 + 6))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ISSUE-20260927-01 · 右列内收：旧/新几何叠图（证据图，只读底图 + 写 PNG 到 ../证据/）。

红 = 改动前矩形；绿 = 改动后矩形；洋红竖线 = 面板右内沿 1762；橙竖线 = 验收上限 1756；
蓝竖线 = 左列最右 1162。逐件几何取自 `m01_rightcol.py` 的改动表（唯一出处）。
"""
import os
import sys
import importlib.util
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MODDIR = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EVID = os.path.join(MODDIR, "证据")

spec = importlib.util.spec_from_file_location("m01", os.path.join(HERE, "m01_rightcol.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

raw, data = m.load()
els = data["elements"]
tbl = m.build_old_table(els)

for tag, page, bg in (("p1_sys", "sys", "x_ui_psv_cfg_page1.png"),
                      ("p2_snd", "snd", "x_ui_psv_cfg_page2.png")):
    im = Image.open(os.path.join(ROOT, "krkr", "assets", "ui", bg)).convert("RGB")
    dr = ImageDraw.Draw(im)
    for e in els:
        ch = m.changes_for(e, strict=False)
        if not ch:
            continue
        pg = m.page_of(e, m.build_key_page(els))
        if pg is not None and pg != page:
            continue
        ox = tbl[e["id"]].get("x", e["x"])
        ow = tbl[e["id"]].get("w", e["w"])
        old = (ox, e["y"], ox + ow, e["y"] + e["h"])
        new = (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])
        dr.rectangle(old, outline=(230, 30, 30))
        dr.rectangle(new, outline=(0, 170, 0))
    for x, col in ((1762, (255, 0, 255)), (1756, (255, 140, 0)), (1162, (0, 90, 255))):
        dr.line([(x, 190), (x, 1080)], fill=col)
    out = os.path.join(EVID, "叠图_%s_红旧绿新.png" % tag)
    im.save(out)
    print("写出", out)

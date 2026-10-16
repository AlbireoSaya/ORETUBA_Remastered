# -*- coding: utf-8 -*-
r"""pA_test · A 路字体/样式选型：同一位置渲染多个候选，叠成对照图供目视选择"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import importlib.util
import numpy as np
from PIL import Image

WORK = os.path.join(r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作", "ISSUE-20260926-06_页脚双路")
spec = importlib.util.spec_from_file_location("pA", os.path.join(WORK, "pA.py"))
pA = importlib.util.module_from_spec(spec); spec.loader.exec_module(pA)

CANDS = [
    ("msyhbd", r"C:\Windows\Fonts\msyhbd.ttc", 41),
    ("msyh", r"C:\Windows\Fonts\msyh.ttc", 41),
    ("simhei", r"C:\Windows\Fonts\simhei.ttf", 41),
    ("Deng", r"C:\Windows\Fonts\Deng.ttf", 41),
    ("SourceHan", r"C:\Windows\Fonts\SourceHanSansCN-Normal.ttf", 41),
    ("zpix", r"E:\ZCode Workspace\Galgame\工具\pixel-fonts\zpix.ttf", 41),
    ("msyhbd44", r"C:\Windows\Fonts\msyhbd.ttc", 44),
]
NAME = "otv_save_bg.png"
if __name__ == "__main__":
    outs = []
    for tag, f, sz in CANDS:
        p = pA.process(NAME, size=sz, font=f, tag="_" + tag)
        outs.append((tag, p))
    # 对照图：原版一行 + 各候选一行（取 x1280-1720 段 1.5x）
    src = Image.open(os.path.join(pA.SRC, NAME)).convert("RGB")
    row0 = src.crop((1280, 970, 1720, 1050))
    tiles = [("原版日文", row0)]
    for tag, p in outs:
        tiles.append((tag, Image.open(p).convert("RGB").crop((1280 - pA.FX0, 970 - pA.FY0,
                                                             1720 - pA.FX0, 1050 - pA.FY0))))
    S = 2
    W = 440 * S
    H = 80 * S
    out = Image.new("RGB", (W, (H + 4) * len(tiles)), (25, 25, 25))
    for i, (t, im) in enumerate(tiles):
        out.paste(im.resize((W, H), Image.LANCZOS), (0, i * (H + 4)))
    q = os.path.join(pA.EV, "A_font_candidates.png")
    out.save(q)
    print("->", q, out.size, [t for t, _ in tiles])

# -*- coding: utf-8 -*-
r"""pA_test2 · A 路样式终选：描边宽度 / 辉光强度 / 字号 三档对照"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import importlib.util
from PIL import Image

WORK = os.path.join(r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作", "ISSUE-20260926-06_页脚双路")
spec = importlib.util.spec_from_file_location("pA", os.path.join(WORK, "pA.py"))
pA = importlib.util.module_from_spec(spec); spec.loader.exec_module(pA)

F = r"C:\Windows\Fonts\msyhbd.ttc"
CANDS = [("s41_st10", F, 41, 10, 0.85, 0.45),
         ("s44_st10", F, 44, 10, 0.85, 0.45),
         ("s44_st14", F, 44, 14, 1.0, 0.55),
         ("s46_st16", F, 46, 16, 1.0, 0.6)]
NAME = "otv_save_bg.png"
if __name__ == "__main__":
    src = Image.open(os.path.join(pA.SRC, NAME)).convert("RGB")
    tiles = [("ORG", src.crop((1280, 970, 1720, 1050)))]
    for tag, f, sz, stw, g1, g2 in CANDS:
        pA.STROKE_SS, pA.G1A, pA.G2A = stw, g1, g2
        p = pA.process(NAME, size=sz, font=f, tag="_" + tag)
        tiles.append((tag, Image.open(p).convert("RGB").crop(
            (1280 - pA.FX0, 970 - pA.FY0, 1720 - pA.FX0, 1050 - pA.FY0))))
    S = 2
    W, H = 440 * S, 80 * S
    out = Image.new("RGB", (W, (H + 4) * len(tiles)), (25, 25, 25))
    for i, (t, im) in enumerate(tiles):
        out.paste(im.resize((W, H), Image.LANCZOS), (0, i * (H + 4)))
    q = os.path.join(pA.EV, "A_style_candidates.png")
    out.save(q)
    print("->", q, out.size, [t for t, _ in tiles])

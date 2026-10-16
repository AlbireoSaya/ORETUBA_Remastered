# -*- coding: utf-8 -*-
r"""m01_composite.py —— 右上三系统按钮组「改前 / 改后」几何叠加示意图（ISSUE-20260927-01 · 模块 B）

★ **这是几何叠加示意图，不是引擎渲染图**。用途只有一条：让「组右沿与页码徽章列的相对位置」
   一眼可读。**不得**拿它当视觉验收 —— 实机观感须由主代理跑引擎巡演导出 PNG 复核
   （`_schema.md` M06 记录：「HTML 近似合成不能替代实机图做视觉验收」）。

底图：屏内实际引用的 `krkr/assets/ui/x_ui_psv_save_bg.png`（存档屏）/ `x_ui_psv_load_bg.png`（读档屏）；
      本工程两屏底图文件名不同，故分别出图。裁剪区 x1500..1900 / y0..175，2× 放大（nearest），
      叠加框：
        · 红虚线 = **改前**可见件组包络（`原形备份\`）
        · 绿实线 = **改后**可见件组包络（盘上）
        · 青实线 = 引擎绘页码徽章列 `sv.pgnum_01..10`（x1699..1759 / y83..131）
        · 橙实线 = 烘焙「/10」条带（口径 x1763..1845 / y80..140）
        · 黄虚线 = hit 层包络（改前 / 改后）

输出：`取证\合成_右上角_1to1_<save|load>.png`（1:1 裁剪 + 标注）
      `取证\合成_右上角_2x_<save|load>.png`（2× nearest）

用法：python m01_composite.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
SCR = UI / "layout" / "screens"
BAK = HERE.parents[1] / "原形备份"
OUT = HERE.parents[1] / "取证"
ASSETS = UI / "krkr" / "assets" / "ui"

AUTO_VIS = ["sv.sys_game", "sv.sys_game_tx", "sv.sys_title", "sv.sys_title_tx",
            "sv.sys_end", "sv.sys_end_tx"]
AUTO_HIT = ["sv.sys_game_hit", "sv.sys_title_hit", "sv.sys_end_hit"]
BADGE = (1699, 83, 1759, 131)
SLASH10 = (1763, 80, 1845, 140)
CROP = (1500, 0, 1900, 175)


def env(elems):
    xs = [e["x"] for e in elems]
    ys = [e["y"] for e in elems]
    rs = [e["x"] + e["w"] for e in elems]
    bs = [e["y"] + e["h"] for e in elems]
    return (min(xs), min(ys), max(rs), max(bs))


def dashed(dr, box, color, width=1, dash=5, gap=4):
    x0, y0, x1, y1 = box
    for pts in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        (ax, ay), (bx, by) = pts
        n = max(1, int((abs(bx - ax) + abs(by - ay)) / (dash + gap)))
        for i in range(n + 1):
            t0 = i * (dash + gap) / max(1.0, (abs(bx - ax) + abs(by - ay)))
            t1 = min(1.0, t0 + dash / max(1.0, (abs(bx - ax) + abs(by - ay))))
            dr.line([ax + (bx - ax) * t0, ay + (by - ay) * t0,
                     ax + (bx - ax) * t1, ay + (by - ay) * t1], fill=color, width=width)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fn, bgname in (("23_save.json", "x_ui_psv_save_bg.png"),
                       ("24_load.json", "x_ui_psv_load_bg.png")):
        bg = Image.open(ASSETS / bgname).convert("RGB")
        live = json.loads((SCR / fn).read_text(encoding="utf-8"))
        bake = json.loads((BAK / fn).read_text(encoding="utf-8"))
        li = {e["id"]: e for e in live["elements"]}
        bi = {e["id"]: e for e in bake["elements"]}

        o_vis = env([bi[e] for e in AUTO_VIS])
        n_vis = env([li[e] for e in AUTO_VIS])
        o_hit = env([bi[e] for e in AUTO_HIT])
        n_hit = env([li[e] for e in AUTO_HIT])

        for scale, tag in ((1, "1to1"), (2, "2x")):
            img = bg.crop(CROP)
            if scale != 1:
                img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
            dr = ImageDraw.Draw(img)

            def T(b):
                return ((b[0] - CROP[0]) * scale, (b[1] - CROP[1]) * scale,
                        (b[2] - CROP[0]) * scale, (b[3] - CROP[1]) * scale)

            # 参考线：徽章列 / 烘焙 /10
            dr.rectangle(T(BADGE), outline=(0, 220, 220), width=1 * scale)
            dr.rectangle(T(SLASH10), outline=(255, 140, 0), width=1 * scale)
            # 改前（红虚线）/ 改后（绿实线）
            dashed(dr, T(o_vis), (255, 0, 0), width=scale, dash=6 * scale, gap=4 * scale)
            dr.rectangle(T(n_vis), outline=(0, 200, 0), width=1 * scale)
            # hit 层（黄虚线）
            dashed(dr, T(o_hit), (255, 220, 0), width=max(1, scale // 2), dash=4 * scale, gap=3 * scale)
            dashed(dr, T(n_hit), (255, 255, 255), width=max(1, scale // 2), dash=4 * scale, gap=3 * scale)

            out = OUT / ("合成_右上角_%s_%s.png" % (tag, "save" if "23" in fn else "load"))
            img.save(out)
            print("已写出 %s（裁剪 %s ×%d）" % (out, CROP, scale))
        print("   %s：改前可见件组 %s ／ 改后 %s ｜ 徽章列 %s ｜ 烘焙 /10 %s"
              % (fn, o_vis, n_vis, BADGE, SLASH10))


if __name__ == "__main__":
    main()

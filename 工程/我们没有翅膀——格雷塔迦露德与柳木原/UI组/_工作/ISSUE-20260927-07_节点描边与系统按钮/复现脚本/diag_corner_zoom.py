# -*- coding: utf-8 -*-
"""诊断：角部放大（16×）对比 + 45° 径向 alpha 剖面（现状 vs 候选）——只读/只写诊断图到证据目录。"""
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                                       # noqa: E402
from PIL import Image                                                    # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
OUT = UI / "_工作" / "ISSUE-20260927-07_节点描边与系统按钮" / "取证" / "圆角候选"
CUR = UI / "krkr" / "assets" / "ui"
RECT = {"section": (6.734, 229.006, 7.019, 56.810),
        "select": (6.409, 256.176, 6.895, 57.798),
        "frag": (5.970, 221.351, 6.987, 58.545)}
BG = (39, 45, 59)


def bil(a, u, v):
    H, W = a.shape
    u = min(max(u, 0.0), W - 1.001)
    v = min(max(v, 0.0), H - 1.001)
    iu, iv = int(np.floor(u)), int(np.floor(v))
    fu, fv = u - iu, v - iv
    return float(a[iv, iu] * (1 - fu) * (1 - fv) + a[iv, iu + 1] * fu * (1 - fv)
                 + a[iv + 1, iu] * (1 - fu) * fv + a[iv + 1, iu + 1] * fu * fv)


def ray_diag(a, rect, corner, r, dmax=14):
    x0, x1, y0, y1 = rect
    ox = -1.0 if corner in ("TL", "BL") else 1.0
    oy = -1.0 if corner in ("TL", "TR") else 1.0
    cx = (x0 + r) if ox < 0 else (x1 - r)
    cy = (y0 + r) if oy < 0 else (y1 - r)
    k = 1.0 / np.sqrt(2.0)
    out = []
    for d in np.arange(-4.0, dmax + 0.001, 0.5):
        t = r + d
        out.append((round(float(d), 2), round(bil(a, cx + ox * k * t, cy + oy * k * t), 1)))
    return out


def main():
    for kind in ("select",):
        rect = RECT[kind]
        tiles = []
        for tag, fn in (("现状", None), ("半径不变", None), ("r=16", None)):
            slug = {"现状": None, "半径不变": "r原件", "r=16": "r16"}[tag]
            p = (CUR / ("x_ui_node_%s_off.png" % kind) if slug is None else
                 OUT / ("候选_解析轮廓_x_ui_node_%s_off_%s_生效色_描边.png" % (kind, slug)))
            im = Image.open(p).convert("RGBA")
            comp = Image.new("RGB", (im.width + 40, im.height + 40), BG)
            comp.paste(im, (20, 20), im)
            crop = 40
            box = (int(rect[0]) - 8 + 20, int(rect[2]) - 8 + 20)
            tiles.append((tag, comp.crop((box[0], box[1], box[0] + crop, box[1] + crop))))
        Z = 16
        W = 20 + len(tiles) * (40 * Z + 20)
        sh = Image.new("RGB", (W, 40 * Z + 60), (18, 22, 32))
        for i, (tag, t) in enumerate(tiles):
            sh.paste(t.resize((t.width * Z, t.height * Z), Image.NEAREST), (20 + i * (40 * Z + 20), 30))
        sh.save(OUT / "_diag_左上角16x_现状_vs_候选.png")
        print("写出 _diag_左上角16x_现状_vs_候选.png", sh.size)

        print("\n### %s 左上角 45° 径向 alpha（d = 到弧的距离，负=内部）" % kind)
        for tag, p in (("现状", CUR / ("x_ui_node_%s_off.png" % kind)),
                       ("半径不变", OUT / ("候选_解析轮廓_x_ui_node_%s_off_r原件.png" % kind)),
                       ("r=16", OUT / ("候选_解析轮廓_x_ui_node_%s_off_r16.png" % kind))):
            a = np.asarray(Image.open(p).convert("RGBA").getchannel("A")).astype(float)
            r = {"现状": 13.06}.get(tag, 13.06 if tag == "半径不变" else 16.0)
            print("   %-6s %s" % (tag, " ".join("%+.1f:%.0f" % (d, v) for d, v in ray_diag(a, rect, "TL", r))))
        # 底部缺口处 y=56 的整行（含 alpha 与合成观感）
        print("\n### select 底边 y=56/57 行（x=150..190）")
        for tag, p in (("现状", CUR / ("x_ui_node_%s_off.png" % kind)),
                       ("半径不变", OUT / ("候选_解析轮廓_x_ui_node_%s_off_r原件_生效色_描边.png" % kind))):
            im = Image.open(p).convert("RGBA")
            a = np.asarray(im.getchannel("A")).astype(int)
            print("   %-6s y=56 %s" % (tag, " ".join("%3d" % a[56, x] for x in range(150, 191, 2))))


if __name__ == "__main__":
    main()

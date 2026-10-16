#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2_圆角核实_参照POC.py — 用**引擎自己**渲染一张「join × cap 设置矩阵」参照图，
再把生产图（巡演导出 PNG）的折角/端帽**逐像素**与参照图比对，从而**经验地**判定
生产里实际生效的是哪一种 join / cap（不依赖我对 GDI+ 内部几何的任何假设）。

做法
  1) 造一个极小 POC 工程（黑底不透明 + 白/冰蓝线），用**与生产模块完全相同的调用**：
       var app = new GdiPlus.Appearance();
       app.addPen(color, %[width:w, lineJoin:GdiPlus.LineJoinXxx,
                           startCap:GdiPlus.LineCapYyy, endCap:GdiPlus.LineCapYyy], 0, 0);
       layer.drawLines(app, pts);
     渲染三种 join（miter/bevel/round）与三种 cap（flat/square/round）。
     ★ 折线几何**逐字复制生产数据**（fixture 的 fix.link.03 折角形状、fix.link.04 的端帽形状），
       坐标也相同 ⇒ 引擎的 +0.5px 半像素偏移在两侧完全一致，可以直接逐像素比。
  2) 从两张 PNG 里按「墨迹覆盖率」反解每像素覆盖（黑底用颜色反解；生产图用 alpha/颜色反解），
     以折角点/端点为锚对齐，算各参照的逐像素残差，取最小者 = 实际生效的设置。

产物：E2_圆角核实_参照矩阵.png、E2_圆角核实_参照比对.txt
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
UI = HERE.parents[3]
WT = HERE.parents[6]
KRKR = UI / "krkr"
POC = WT / "临时" / "e2_round_poc"

W, H = 1280, 720
INK = (101, 177, 212)          # #FF65B1D4
INK_INT = 0xFF65B1D4
WID = 4

# 折角几何：与 fixture fix.link.03 的形状一致（横 752 + 竖 67，左折后向下）
CORNER_Y = (120, 260, 400)      # 朝向 L：pts [(1000,y),(248,y),(248,y+67)]，臂在角右侧
CORNER_Y2 = (480, 560, 640)     # 朝向 R：pts [(100,y),(400,y),(400,y+67)]，臂在角左侧
JOIN_NAMES = ["miter", "bevel", "round"]
# 端帽几何：与 fixture fix.link.04 一致（竖线长 185）
CAP_X = (700, 900, 1100)
CAP_NAMES = ["flat", "square", "round"]
CAP_Y0, CAP_Y1 = 100, 285


def game_tjs():
    """生成 POC 的 startup.tjs。用 str.replace 而非 % 格式化：TJS 里满屏 %[ 字面量，
       % 格式化会把它当占位符（本轮实测踩过）。"""
    t = """
try { Debug.startLogToFile(); } catch(e0) { }
var W = @W@, H = @H@;
var LOG = "";
try { LOG = "" + Debug.logLocation; } catch(e) { }
function exp(name) {
	try { var b = new Bitmap(); stage.copyToBitmapFromMainImage(b); b.save(LOG + name, "png");
	      Debug.message("[POC] exported " + name); }
	catch(e) { Debug.message("[POC] export FAIL " + e.message); }
}
var linked = false;
try { Plugins.link("layerExDraw.dll"); linked = true; }
catch(e) { Debug.message("[POC] link FAIL " + e.message); }
Debug.message("[POC] linked=" + linked + " log=" + LOG);
var win; var prim; var stage;   // TJS2：必须 var 前置，否则赋值抛「未找到 Member」
var win = new Window();
win.add(prim = new Layer(win, null));
prim.left = 0; prim.top = 0; prim.setImageSize(W, H); prim.type = ltOpaque;
win.setInnerSize(W, H);
win.add(stage = new Layer(win, prim));
stage.left = 0; stage.top = 0; stage.setImageSize(W, H); stage.setSizeToImageSize();
stage.type = ltAlpha; stage.visible = true;
stage.fillRect(0, 0, W, H, 0xFF000000);
function appOf(color, opts) { var a = new GdiPlus.Appearance(); a.addPen(color, opts, 0, 0); return a; }
var WID = @WID@;
var JOINS = @JOINS@;
var CAPS  = @CAPS@;
var CY = @CY@;
var CX = @CX@;
Debug.message("[POC] GdiPlus LJR=" + GdiPlus.LineJoinRound + " LBM=" + GdiPlus.LineJoinBevel
	+ " LJM=" + GdiPlus.LineJoinMiter + " LCF=" + GdiPlus.LineCapFlat
	+ " LCS=" + GdiPlus.LineCapSquare + " LCR=" + GdiPlus.LineCapRound);
for(var i = 0; i < 3; i++) {
	var pts = [[1000, CY[i]], [248, CY[i]], [248, CY[i] + 67]];
	try {
		var a = appOf(0xFF65B1D4, %[ width: WID, lineJoin: JOINS[i],
			startCap: GdiPlus.LineCapFlat, endCap: GdiPlus.LineCapFlat ]);
		stage.drawLines(a, pts);
		Debug.message("[POC] join " + i + " ok");
	} catch(e) { Debug.message("[POC] join " + i + " FAIL " + e.message); }
	var pts2 = [[100, @CY2@[i]], [400, @CY2@[i]], [400, @CY2@[i] + 67]];
	try {
		var a2 = appOf(0xFF65B1D4, %[ width: WID, lineJoin: JOINS[i],
			startCap: GdiPlus.LineCapFlat, endCap: GdiPlus.LineCapFlat ]);
		stage.drawLines(a2, pts2);
	} catch(e4) { Debug.message("[POC] joinR " + i + " FAIL " + e4.message); }
	var cpts = [[CX[i], @Y0@], [CX[i], @Y1@]];
	try {
		var b = appOf(0xFF65B1D4, %[ width: WID, startCap: CAPS[i], endCap: CAPS[i],
			lineJoin: GdiPlus.LineJoinMiter ]);
		stage.drawLines(b, cpts);
	} catch(e2) { Debug.message("[POC] cap " + i + " FAIL " + e2.message); }
}
exp("round_ref.png");
try { win.close(); } catch(e3) { }
"""
    t = t.replace("@W@", str(W)).replace("@H@", str(H)).replace("@WID@", str(WID))
    t = t.replace("@JOINS@", "[ GdiPlus.LineJoinMiter, GdiPlus.LineJoinBevel, GdiPlus.LineJoinRound ]")
    t = t.replace("@CAPS@", "[ GdiPlus.LineCapFlat, GdiPlus.LineCapSquare, GdiPlus.LineCapRound ]")
    t = t.replace("@CY@", "[ %d, %d, %d ]" % CORNER_Y)
    t = t.replace("@CX@", "[ %d, %d, %d ]" % CAP_X)
    t = t.replace("@CY2@", "[ %d, %d, %d ]" % CORNER_Y2)
    t = t.replace("@Y0@", str(CAP_Y0)).replace("@Y1@", str(CAP_Y1))
    return t


def mirror(dst):
    if (dst / "game").exists():
        shutil.rmtree(dst / "game")
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "game").mkdir(exist_ok=True)
    (dst / "game" / "startup.tjs").write_text(game_tjs(), encoding="utf-8")
    if not (dst / "runtime").exists():
        shutil.copytree(KRKR / "runtime", dst / "runtime")
    plug = dst / "runtime" / "plugin"
    plug.mkdir(parents=True, exist_ok=True)
    for f in (KRKR / "plugin").iterdir():
        if f.is_file():
            shutil.copy2(f, plug / f.name)
    sd = dst / "runtime" / "savedata"
    sd.mkdir(parents=True, exist_ok=True)
    for old in sd.glob("*.png"):
        old.unlink()
    return dst


def run_poc():
    dst = mirror(POC)
    exe = dst / "runtime" / "tvpwin32.exe"
    subprocess.Popen([str(exe), str(dst / "game")], cwd=str(dst / "runtime"),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    png = dst / "runtime" / "savedata" / "round_ref.png"
    t0 = time.time()
    while time.time() - t0 < 90:
        time.sleep(2)
        if png.exists() and png.stat().st_size > 0:
            break
    time.sleep(1)
    subprocess.run(["taskkill", "/F", "/IM", "tvpwin32.exe"], capture_output=True)
    if not png.exists():
        raise SystemExit("[FAIL] POC 未导出 round_ref.png（看 临时\\e2_round_poc\\runtime\\savedata\\krkr.console.log）")
    return png


# ---------------------------------------------------------------- 覆盖率反解
def cover_ref(px, x, y):
    """黑底参照图：覆盖率 = Co/Ci 各通道中位（只取 Ci 较大的通道）"""
    p = px[x, y]
    if p[3] < 250:
        return 0.0
    est = sorted((p[k] / INK[k]) if INK[k] > 30 else 0 for k in range(3))
    return max(0.0, min(1.0, est[1]))


def cover_prod(px, x, y, ref):
    """生产图：α = (ao−ab)/(1−ab)（ab 取同区域背景参考；背景不透明时退回颜色反解）"""
    p = px[x, y]
    ao = p[3] / 255.0
    ab = ref[3] / 255.0
    if ab < 0.995:
        return max(0.0, min(1.0, (ao - ab) / (1 - ab)))
    est = []
    for k in range(3):
        d = INK[k] - ref[k]
        if abs(d) > 12:
            est.append((p[k] - ref[k]) / d)
    if not est:
        return 0.0
    est.sort()
    return max(0.0, min(1.0, est[len(est) // 2]))


def map_ref(px, cx, cy, r=7):
    return [[cover_ref(px, cx + dx, cy + dy) for dx in range(-r, r + 1)] for dy in range(-r, r + 1)]


def map_prod(px, cx, cy, bx, by, r=7):
    ref = px[bx, by]
    return [[cover_prod(px, cx + dx, cy + dy, ref) for dx in range(-r, r + 1)] for dy in range(-r, r + 1)]


def resid(a, b):
    n = 0.0
    mx = 0.0
    for ra, rb in zip(a, b):
        for va, vb in zip(ra, rb):
            d = abs(va - vb)
            n += d * d
            mx = max(mx, d)
    cnt = sum(len(r) for r in a)
    return (n / cnt) ** 0.5, mx


def draw_triples(path, items, zoom=14):
    """把生产窗口与三张参照窗口并排放大成一张图（人眼复核用）"""
    r = 7
    cell = (2 * r + 1) * zoom
    out = Image.new("RGB", (cell * (len(items) + 1) + 20 * (len(items) + 2), cell + 46), (18, 18, 22))
    d = ImageDraw.Draw(out)
    x0 = 20
    for title, arr in items:
        im = Image.new("RGB", (2 * r + 1, 2 * r + 1))
        p = im.load()
        for j, row in enumerate(arr):
            for i, v in enumerate(row):
                c = int(max(0, min(1, v)) * 255)
                p[i, j] = (c, c, c)
        im = im.resize((cell, cell), Image.NEAREST)
        out.paste(im, (x0, 30))
        d.text((x0, 12), title, fill=(255, 220, 120))
        x0 += cell + 20
    out.save(path)
    return path


def main():
    png = run_poc()
    print("[1] 参照矩阵 = %s" % png)
    ref = Image.open(png).convert("RGBA")
    rpx = ref.load()

    prod_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (HERE / "E2_巡演图_positive_iceblue_shot_84_flowchart.png")
    prod = Image.open(prod_path).convert("RGBA")
    ppx = prod.load()
    print("[2] 生产图   = %s" % prod_path)

    # 参照锚点：折角在 (248, CY[i])（join），端帽在 (CX[i], CAP_Y0/Y1)
    # 生产锚点：fixture fix.link.03 折角 (248,833)；fix.link.04 端点 (1148,365)/(1148,550)
    print("\n=== A. 折角：生产 fix.link.03 @(248,833)  vs  参照三种 join ===")
    pm = map_prod(ppx, 248, 833, 240, 833)          # 背景参考取折角左侧线外
    items = [("PROD corner", pm)]
    scores = []
    for i, nm in enumerate(JOIN_NAMES):
        rm = map_ref(rpx, 248, CORNER_Y[i])
        rms, mx = resid(pm, rm)
        scores.append((rms, mx, nm))
        items.append(("REF %s" % nm, rm))
    for rms, mx, nm in sorted(scores):
        print("   %-6s  RMS=%.4f  max=%.3f" % (nm, rms, mx))
    print("   ⇒ 最接近 = %s" % sorted(scores)[0][2])
    draw_triples(HERE / "E2_圆角核实_参照矩阵_折角.png", items)

    print("\n=== B. 端帽：生产 fix.link.04 END @(1148,550) vs 参照三种 cap ===")
    pm2 = map_prod(ppx, 1148, 551, 1140, 551)
    items2 = [("PROD end-cap", pm2)]
    scores2 = []
    for i, nm in enumerate(CAP_NAMES):
        rm = map_ref(rpx, CAP_X[i], CAP_Y1 + 1)     # 参照线的下端帽
        rms, mx = resid(pm2, rm)
        scores2.append((rms, mx, nm))
        items2.append(("REF %s" % nm, rm))
    for rms, mx, nm in sorted(scores2):
        print("   %-6s  RMS=%.4f  max=%.3f" % (nm, rms, mx))
    print("   ⇒ 最接近 = %s" % sorted(scores2)[0][2])
    draw_triples(HERE / "E2_圆角核实_参照矩阵_端帽.png", items2)

    with open(HERE / "E2_圆角核实_参照比对.txt", "w", encoding="utf-8") as f:
        f.write("E2 圆角核实 · 参照矩阵比对（%s）\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("参照图: %s\n生产图: %s\n\n" % (png, prod_path))
        f.write("[A] 折角 @(248,833)\n")
        for rms, mx, nm in sorted(scores):
            f.write("    %-6s RMS=%.4f max=%.3f\n" % (nm, rms, mx))
        f.write("    最接近 = %s\n\n" % sorted(scores)[0][2])
        f.write("[B] 端帽 @(1148,550)\n")
        for rms, mx, nm in sorted(scores2):
            f.write("    %-6s RMS=%.4f max=%.3f\n" % (nm, rms, mx))
        f.write("    最接近 = %s\n" % sorted(scores2)[0][2])
    print("\n[3] 报告 = E2_圆角核实_参照比对.txt；对照图 = E2_圆角核实_参照矩阵_*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())

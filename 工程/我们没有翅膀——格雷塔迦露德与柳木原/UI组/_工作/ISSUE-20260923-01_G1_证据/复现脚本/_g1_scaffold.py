# -*- coding: utf-8 -*-
r"""G1 · 快捷条 12 圆图标 · 脚手架图生成（用户要求「提前画好方框约束模型」）

产出：脚手架_grid_4x3.png（1536x1024，4 列 × 3 行）
  每格 = 一个方框 + 框内一枚**淡灰铅笔稿**（该格目标图标的线稿）+ 格号（画在方框外的格间留白）。
  淡灰铅笔稿 = 最强的位置/语义约束：模型只需「把稿子重绘成成品」，
  不必靠文字描述去猜图标形状，也不会把 icon 洗到别的格里。

格序（**data 里的次序**，行优先）：
  1 lock 锁 | 2 save 存档 | 3 load 读档 | 4 qsave 快存
  5 qload 快读 | 6 auto 自动 | 7 skip 快进 | 8 next 下一选项
  9 prev 上一选项 | 10 log 回想 | 11 chart 流程图 | 12 option 设置
"""
import math, os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))   # 本脚本可原位跑，也可在 证据\复现脚本\ 里跑
os.makedirs(EV, exist_ok=True)

CANVAS = (1536, 1024)
COLS, ROWS = 4, 3
CELL_W = CANVAS[0] // COLS                  # 384
CELL_H = CANVAS[1] // ROWS                  # 341 (最后一行吃掉余数)
BOX = 288                                   # 方框边长
SS = 4                                      # 铅笔稿超采样倍率

KEYS = ["lock", "save", "load", "qsave", "qload", "auto",
        "skip", "next", "prev", "log", "chart", "option"]

GRID_GREY = (128, 128, 128, 255)            # 方框线
SKETCH_GREY = (150, 150, 150, 255)          # 铅笔稿
NUM_GREY = (110, 110, 110, 255)             # 格号

# ───────────────────────── 100 单位坐标系里的 12 枚图标线稿 ─────────────────────────
# 约定：坐标 0..100 的正方形；线宽 LW；部分图形用填充（齿轮）。

LW = 9


def _arc_arrow(d, bbox, a0, a1, lw, fill):
    """画圆弧 + 在末端画一个沿切向的箭头（用于「循环」）。"""
    d.arc(bbox, a0, a1, fill=fill, width=lw)
    cx = (bbox[0] + bbox[2]) / 2.0
    cy = (bbox[1] + bbox[3]) / 2.0
    r = (bbox[2] - bbox[0]) / 2.0
    t = math.radians(a1)
    px, py = cx + r * math.cos(t), cy + r * math.sin(t)
    # 切线方向（顺时针，y 向下）
    tx, ty = -math.sin(t), math.cos(t)
    # 法线
    nx, ny = math.cos(t), math.sin(t)
    L, Wd = 16.0, 11.0
    pts = [(px + tx * L, py + ty * L),
           (px - tx * 2 + nx * Wd, py - ty * 2 + ny * Wd),
           (px - tx * 2 - nx * Wd, py - ty * 2 - ny * Wd)]
    d.polygon(pts, fill=fill)


def s_lock(d, lw, C):
    d.arc((30, 20, 70, 62), 180, 360, fill=C, width=lw)          # 锁梁
    d.rounded_rectangle((22, 46, 78, 88), radius=8, outline=C, width=lw)  # 锁体
    d.ellipse((45, 58, 55, 68), fill=C)                          # 钥匙孔
    d.line((50, 67, 50, 77), fill=C, width=lw)


def s_save(d, lw, C):
    d.line((50, 14, 50, 54), fill=C, width=lw)                   # 箭杆
    d.polygon([(32, 40), (50, 62), (68, 40)], fill=C)            # 箭头
    d.line((20, 58, 20, 88), fill=C, width=lw)
    d.line((20, 88, 80, 88), fill=C, width=lw)
    d.line((80, 88, 80, 58), fill=C, width=lw)


def s_load(d, lw, C):
    d.line((50, 62, 50, 22), fill=C, width=lw)
    d.polygon([(32, 38), (50, 16), (68, 38)], fill=C)
    d.line((20, 60, 20, 88), fill=C, width=lw)
    d.line((20, 88, 80, 88), fill=C, width=lw)
    d.line((80, 88, 80, 60), fill=C, width=lw)


def _bolt(d, C):
    """闪电：画在右侧 60..96 的窄条里，与左侧「存档/读档」图形保持留白。"""
    d.polygon([(80, 10), (62, 50), (74, 50), (66, 90), (94, 46), (80, 46)], fill=C)


def _tray(d, lw, C, x0=6, x1=56, ytop=62, ybot=88):
    d.line((x0, ytop, x0, ybot), fill=C, width=lw)
    d.line((x0, ybot, x1, ybot), fill=C, width=lw)
    d.line((x1, ybot, x1, ytop), fill=C, width=lw)


def s_qsave(d, lw, C):
    d.line((31, 14, 31, 46), fill=C, width=lw)
    d.polygon([(18, 34), (31, 54), (44, 34)], fill=C)
    _tray(d, lw, C)
    _bolt(d, C)


def s_qload(d, lw, C):
    d.line((31, 54, 31, 22), fill=C, width=lw)
    d.polygon([(18, 34), (31, 14), (44, 34)], fill=C)
    _tray(d, lw, C)
    _bolt(d, C)


def s_auto(d, lw, C):
    _arc_arrow(d, (14, 14, 86, 86), 150, 400, lw, C)             # 循环箭头
    d.polygon([(40, 38), (66, 52), (40, 66)], fill=C)            # 播放三角


def s_skip(d, lw, C):
    d.polygon([(20, 24), (52, 50), (20, 76)], fill=C)
    d.polygon([(50, 24), (82, 50), (50, 76)], fill=C)


def s_next(d, lw, C):
    d.polygon([(22, 24), (58, 50), (22, 76)], fill=C)
    d.line((70, 24, 70, 76), fill=C, width=lw)


def s_prev(d, lw, C):
    d.line((30, 24, 30, 76), fill=C, width=lw)
    d.polygon([(78, 24), (42, 50), (78, 76)], fill=C)


def s_log(d, lw, C):
    # 摊开的书：左页 / 右页 + 书脊 + 页内文字线
    d.polygon([(14, 28), (48, 36), (48, 82), (14, 74)], outline=C, width=lw)
    d.polygon([(86, 28), (52, 36), (52, 82), (86, 74)], outline=C, width=lw)
    d.line((48, 36, 52, 36), fill=C, width=lw)
    for y in (48, 58, 68):
        d.line((22, y, 41, y + 3), fill=C, width=max(3, lw - 4))
        d.line((59, y + 3, 78, y), fill=C, width=max(3, lw - 4))


def s_chart(d, lw, C):
    d.ellipse((38, 8, 62, 32), outline=C, width=lw)              # 顶节点
    d.ellipse((12, 66, 36, 90), outline=C, width=lw)             # 左下节点
    d.ellipse((64, 66, 88, 90), outline=C, width=lw)             # 右下节点
    d.line((50, 32, 50, 52), fill=C, width=lw)
    d.line((24, 66, 24, 52), fill=C, width=lw)
    d.line((76, 66, 76, 52), fill=C, width=lw)
    d.line((24, 52, 76, 52), fill=C, width=lw)


def s_option(d, lw, C):
    """齿轮：外轮廓按齿形多边形填充，再挖掉中心孔与轴孔。"""
    cx = cy = 50.0
    R, r = 46.0, 36.0
    teeth = 8
    half = 0.34                                     # 单个齿在扇区里的半宽（弧度比）
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step
        for k in range(6):
            f = k / 6.0
            aa = a + (f * step)
            # 前 3/6 沿外径走齿顶，后 3/6 沿内径回落
            rad = R if aa < a + step * half * 2 else r
            pts.append((cx + rad * math.cos(aa), cy + rad * math.sin(aa)))
    d.polygon(pts, fill=C)
    d.ellipse((cx - 15, cy - 15, cx + 15, cy + 15), fill=None)   # 占位（下面单独挖）
    return pts


def draw_gear(d, lw, C):
    cx = cy = 50.0
    R, r = 48.0, 37.0
    teeth = 8
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step
        for k in range(12):
            aa = a + k * step / 12.0
            ph = (k % 12) / 12.0
            rad = R if ph < 0.45 else r
            pts.append((cx + rad * math.cos(aa), cy + rad * math.sin(aa)))
    d.polygon(pts, fill=C)


ICONS = {
    "lock": s_lock, "save": s_save, "load": s_load, "qsave": s_qsave, "qload": s_qload,
    "auto": s_auto, "skip": s_skip, "next": s_next, "prev": s_prev, "log": s_log,
    "chart": s_chart,
}


def sketch(key, size):
    """在 size×size 画布上画 key 的线稿（4× 超采样后降采样，边缘平滑）。"""
    big = size * SS
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = big / 100.0
    lw = max(2, int(round(LW * k / 4.0)))

    class Scaled(object):
        """把 0..100 坐标按 k 缩放的 ImageDraw 代理。"""

        def arc(self, bb, a0, a1, fill=None, width=1):
            d.arc(tuple(v * k for v in bb), a0, a1, fill=fill, width=width)

        def line(self, xy, fill=None, width=1):
            d.line(tuple(v * k for v in xy), fill=fill, width=width)

        def polygon(self, xy, fill=None, outline=None, width=1):
            d.polygon([(x * k, y * k) for x, y in xy], fill=fill, outline=outline, width=width)

        def ellipse(self, bb, fill=None, outline=None, width=1):
            d.ellipse(tuple(v * k for v in bb), fill=fill, outline=outline, width=width)

        def rounded_rectangle(self, bb, radius=0, fill=None, outline=None, width=1):
            d.rounded_rectangle(tuple(v * k for v in bb), radius=radius * k, fill=fill,
                                outline=outline, width=width)

    if key == "option":
        draw_gear(Scaled(), lw, SKETCH_GREY)
        # 挖中心轴孔：直接用透明色重画一个圆
        d.ellipse((50 * k - 14 * k, 50 * k - 14 * k, 50 * k + 14 * k, 50 * k + 14 * k),
                  fill=(0, 0, 0, 0))
        d.ellipse((50 * k - 18 * k, 50 * k - 18 * k, 50 * k + 18 * k, 50 * k + 18 * k),
                  outline=SKETCH_GREY, width=max(2, int(round(8 * k / 4.0))))
    else:
        ICONS[key](Scaled(), lw, SKETCH_GREY)
    return im.resize((size, size), Image.LANCZOS)


def cell_rect(i):
    """第 i 格（0 基）的单元格矩形 → (cx, cy, cw, ch)。"""
    r, c = divmod(i, COLS)
    x = c * CELL_W
    y = r * CELL_H
    h = CANVAS[1] - y if r == ROWS - 1 else CELL_H
    return x, y, CELL_W, h


def main():
    g = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
    except Exception:
        fnt = ImageFont.load_default()

    table = []
    for i, key in enumerate(KEYS):
        cx, cy, cw, ch = cell_rect(i)
        bx = cx + (cw - BOX) // 2
        by = cy + (ch - BOX) // 2
        d.rectangle((bx, by, bx + BOX - 1, by + BOX - 1), outline=GRID_GREY, width=3)
        sk = sketch(key, int(BOX * 0.74))
        ox = bx + (BOX - sk.size[0]) // 2
        oy = by + (BOX - sk.size[1]) // 2
        g.alpha_composite(sk, (ox, oy))
        # 格号画在方框之外的格间留白（左上角）
        d.text((cx + 6, cy + 2), str(i + 1), fill=NUM_GREY, font=fnt)
        table.append((i + 1, key, bx, by, BOX, ox, oy, sk.size[0]))

    p = os.path.join(EV, "脚手架_grid_4x3.png")
    g.save(p)

    # 落盘脚手架几何台账（切件回退用）
    lines = ["# 脚手架几何台账（程序生成，坐标系 1536x1024）", "",
             "| 格 | key | 方框 x,y,w | 铅笔稿 x,y,边长 |", "|---|---|---|---|"]
    for n, key, bx, by, bw, ox, oy, ss in table:
        lines.append("| %d | %s | %d,%d,%d | %d,%d,%d |" % (n, key, bx, by, bw, ox, oy, ss))
    open(os.path.join(EV, "脚手架几何台账.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("脚手架 -> %s  %s" % (p, g.size))
    for n, key, bx, by, bw, ox, oy, ss in table:
        print("  格%-3d %-7s 方框(%d,%d) 稿(%d,%d,%d)" % (n, key, bx, by, ox, oy, ss))


if __name__ == "__main__":
    main()

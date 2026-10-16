# -*- coding: utf-8 -*-
r"""只读复量**用户实机截图**（1282×752 游戏窗口图；canvas = 图内 ×1.5，客户区原点 (1,32)）。

独立判据（不复用主代理那次量测脚本）：
  · 红圈排除：R > G+40 且 R > B+40 ⇒ 用户手绘标注，不参与统计。
  · 行带：按 canvas 设计口径取（`26_backlog.json` 的 list y=158 + 192i、item_h=188），
    图内 = canvas/1.5 + (1,32)；带内上下各让 6px，避开板的上/下沿暗线（那是横向整行线，
    会把「每列都有墨迹」判成真，是首版脚本误判的根因）。
  · 文字墨迹：暗于带中位亮度−60 且非红；左沿 = 整列 ≥3 个墨迹像素的最小列（≥3 才能滤掉 1–2px 的板沿线）。
  · `跳转` 胶囊中线：用**胶囊内的标签墨迹**（左栏窄窗，仅此一处有深色字）的中点代替胶囊中点
    —— 标签在胶囊内垂直居中（`valign:middle`），两者中线相同，且不依赖对淡蓝色板的颜色阈值。
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
USER_SHOT = (r"C:\Users\Administrator\.zcode\cli\image-cache"
             r"\sess_db64b7ca-775b-440a-8318-0c32284871bc"
             r"\image-4b3c2323b38e67b6d10bddbc0ab3568f.png")
OX, OY, S = 1, 32, 1.5
LIST_Y, PITCH, ITEM_H = 158, 192, 188
TXT_X0C, TXT_X1C = 388, 1679        # canvas 文案盒
JMP_X0C, JMP_X1C = 197, 291         # canvas 跳转胶囊（局部 28..122）


def canvas(v, o):
    return (v - o) * S


def img(v, o):
    return v / S + o


def is_red(p):
    return p[0] > p[1] + 40 and p[0] > p[2] + 40


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def med_region(px, x0, x1, y0, y1):
    v = [lum(px[x, y]) for y in range(y0, y1, 2) for x in range(x0, x1, 2) if not is_red(px[x, y])]
    v.sort()
    return v[len(v) // 2]


def ink_rows(px, x0, x1, y0, y1, thr, min_cells):
    out = []
    for y in range(y0, y1):
        c = sum(1 for x in range(x0, x1) if (not is_red(px[x, y])) and lum(px[x, y]) < thr)
        if c >= min_cells:
            out.append(y)
    return out


def main():
    im = Image.open(USER_SHOT).convert("RGB"); px = im.load()
    W, H = im.size
    print("用户截图 %dx%d（canvas 1920×1080 按 setZoom(2,3) 呈现，客户区原点 (1,32)）" % (W, H))
    print("标定自检：canvas x=388 → 图内 %d ｜ 行0 顶 canvas=158 → 图内 %d"
          % (round(img(TXT_X0C, OX)), round(img(LIST_Y, OY))))
    lefts_c, lefts_i, t1 = [], [], []
    jmp_c = []
    for i in range(4):
        ct = LIST_Y + i * PITCH
        y0 = int(img(ct, OY)) + 6
        y1 = int(img(ct + ITEM_H, OY)) - 6
        x0 = int(img(TXT_X0C, OX)); x1 = int(img(TXT_X1C, OX))
        thr = med_region(px, x0, x1, y0, y1) - 60
        cols = []
        for x in range(x0, x1):
            cols.append(sum(1 for y in range(y0, y1) if (not is_red(px[x, y])) and lum(px[x, y]) < thr))
        L = next((x0 + k for k, c in enumerate(cols) if c >= 3), None)
        rr = ink_rows(px, x0, x1, y0, y1, thr, 3)
        first = [y for y in rr if y < rr[0] + 42 / S] if rr else []
        lefts_i.append(L); lefts_c.append(round(canvas(L, OX)))
        t1.append(canvas((first[0] + first[-1]) / 2.0, OY) if first else float("nan"))
        # 跳转 标签墨迹（左栏窄窗）
        jx0, jx1 = int(img(JMP_X0C - 4, OX)), int(img(JMP_X1C + 4, OX))
        jthr = med_region(px, jx0, jx1, y0, y1) - 60
        jr = ink_rows(px, jx0, jx1, y0, y1, jthr, 2)
        jmp_c.append(canvas((jr[0] + jr[-1]) / 2.0, OY) if jr else float("nan"))
        print("  块%d 行带 图内 y=%d..%d ｜ 文案左沿 图内=%s canvas=%s ｜ 首行墨迹 图内=%s..%s "
              "canvas 中线=%.1f ｜ 跳转标签墨迹 canvas=%s..%s 中线=%.1f"
              % (i, y0, y1, L, lefts_c[-1], first[0], first[-1], t1[-1],
                 jr[0] if jr else None, jr[-1] if jr else None, jmp_c[-1]))
    print("四块文案左沿：图内 %s（极差 %dpx）｜ canvas %s（极差 %dpx）"
          % (lefts_i, max(lefts_i) - min(lefts_i), lefts_c, max(lefts_c) - min(lefts_c)))
    print("纵向：首行墨迹中线 canvas %s ｜ 跳转胶囊中线 canvas %s ⇒ Δ=%s"
          % (["%.1f" % v for v in t1], ["%.1f" % v for v in jmp_c],
             ["%.1f" % (b - a) for a, b in zip(t1, jmp_c)]))
    print("（对照：我方巡演导图与数据口径 Δ=16.5px ⇒ 该图与本次改动前状态一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
r"""M25 · 标题菜单底部横排 + 对话框九宫格几何推导（只读计算，不改资产）。

数据来源（只读）：
  * _工作/M22_生成几何.json  menu.items[*].normal.content_bbox_in_cell  —— 每格内容包围盒
  * 用户标注图（与 x_gen_dialog2.png 1:1）—— 绿框正文区 / 黄框九宫格，M23 已对齐验证

输出：把推导结果打印出来，供 01_title.json / 10_dialog.json 抄写。
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
GEO = json.load(open(os.path.join(HERE, "M22_生成几何.json"), encoding="utf-8"))

# ------------------------------------------------------------------ A. 标题菜单横排
CELL_W, CELL_H = 439, 122
AVAIL_X0, AVAIL_X1 = 120, 1800
ROW_CENTER_Y = 855          # 用户标注横带中心
K = 0.66                    # 等倍缩放（7 件同一倍率）
G = 28                      # 内容视觉间距

items = GEO["menu"]["items"]
bboxes = [it["normal"]["content_bbox_in_cell"] for it in items]   # [x,y,w,h]
sum_w = sum(b[2] for b in bboxes)

cw = CELL_W * K             # 缩放后单元格宽
ch = CELL_H * K             # 缩放后单元格高
span = sum_w * K + (len(bboxes) - 1) * G
avail = AVAIL_X1 - AVAIL_X0
start = (AVAIL_X0 + AVAIL_X1) / 2.0 - span / 2.0

print("=" * 72)
print("A. 标题菜单底部横排")
print("  单元格 PNG = %dx%d；内容包围盒宽 = %s（合计 %d px）" % (CELL_W, CELL_H, [b[2] for b in bboxes], sum_w))
print("  k = %.4f ；缩放后单元格 = %.2f x %.2f（取整 %d x %d）" % (K, cw, ch, round(cw), round(ch)))
print("  内容间距 G = %d px；一排内容总宽 span = %.2f px = 可用宽 %d 的 %.2f%%"
      % (G, span, avail, 100.0 * span / avail))
print("  起点 content_left(第1件) = %.2f（可用范围 [%d,%d] 居中）" % (start, AVAIL_X0, AVAIL_X1))
print("  %-3s %-9s %-24s %-24s %-24s" % ("i", "语义", "内容(画布)", "image x/y/w/h", "hit x/y/w/h"))
cx = start
rows = []
for i, (it, b) in enumerate(zip(items, bboxes), 1):
    x0, y0, bw, bh = b
    content_left = cx
    content_top = ROW_CENTER_Y - (y0 + bh / 2.0) * K          # 内容竖直中心对齐横带中心
    img_x = content_left - x0 * K
    img_y = content_top - y0 * K
    rec = dict(i=i, semantic=it["semantic"], img_x=img_x, img_y=img_y,
               content_left=content_left, content_top=content_top,
               content_w=bw * K, content_h=bh * K)
    rows.append(rec)
    print("  %-3d %-9s x=%-7.1f y=%-7.1f w=%-7.1f h=%-7.1f  %-8.1f %-8.1f %-6.1f %-6.1f"
          % (i, it["semantic"], content_left, content_top, bw * K, bh * K,
             img_x, img_y, cw, ch))
    cx += bw * K + G

print("  —— 取整后（写进 JSON 的值）——")
round_rows = []
for r in rows:
    x = int(round(r["img_x"])); y = int(round(r["img_y"]))
    w = int(round(cw)); h = int(round(ch))
    round_rows.append((x, y, w, h))
    print("   %d: image/hit x=%d y=%d w=%d h=%d   （内容左沿 %.1f，右沿 %.1f）"
          % (r["i"], x, y, w, h, r["content_left"], r["content_left"] + r["content_w"]))
    # 内容在画布上的实际左右沿（按取整后的图摆放 + bbox 偏移）
    bx0 = bboxes[r["i"] - 1][0]
    print("      实际内容左沿 = %d + %.2f = %.1f ；右沿 = %.1f"
          % (x, bx0 * K, x + bx0 * K, x + (bx0 + bboxes[r["i"] - 1][2]) * K))
first = round_rows[0]; last = round_rows[-1]
print("  整排：左沿 x=%d（图），右沿 x=%d（图 %d+%d）" % (first[0], last[0] + last[2], last[0], last[2]))
print("  纵向：图 y=%d..%d ；屏幕底边 1080 留空 = %d px" % (first[1], first[1] + first[3], 1080 - (first[1] + first[3])))
print("  文字实测（原图 alpha>230 分带）：中文 ink 高 ≈ 53-55 px，英文 ink 高 ≈ 32-33 px")
print("  → 缩放后中文 ink 高 ≈ %.1f px ；英文 ≈ %.1f px" % (53 * K, 32 * K))

# ------------------------------------------------------------------ B. 九宫格
print("=" * 72)
print("B. 对话框九宫格（用户黄框）")
GX, GY, GW, GH = 1521, 794, 239, 225
CELLW = GW / 3.0
CELLH = GH / 3.0
ICON_W, ICON_H = 351, 234
ki = min(CELLW / ICON_W, CELLH / ICON_H)
iw, ih = ICON_W * ki, ICON_H * ki
print("  九宫格区 = (%d,%d,%d,%d)；格 = %.4f x %.4f（%.2f x %.2f）" % (GX, GY, GW, GH, CELLW, CELLH, CELLW, CELLH))
print("  格线 x: %.2f / %.2f / %.2f / %.2f" % (GX, GX + CELLW, GX + 2 * CELLW, GX + GW))
print("  格线 y: %.2f / %.2f / %.2f / %.2f" % (GY, GY + CELLH, GY + 2 * CELLH, GY + GH))
print("  contain 适配 k = min(%.6f, %.6f) = %.6f" % (CELLW / ICON_W, CELLH / ICON_H, ki))
print("  缩放后图标 = %.4f x %.4f  → 写 %.2f x %.2f" % (iw, ih, iw, ih))
print("  竖直居中偏移 = (%.2f-%.2f)/2 = %.3f" % (CELLH, ih, (CELLH - ih) / 2.0))
names = ["01_qsave", "02_qload", "03_skip", "04_prev", "05_save", "06_load", "07_config", "08_close", "09_repeat"]
acts = ["do_quicksave", "do_quickload", "skip_on", "prev_choice", "open_save", "open_load", "open_config", "hide_window", "replay_voice"]
print("  %-3s %-12s %-24s %-24s %s" % ("i", "asset", "image x/y/w/h", "hit x/y/w/h", "action"))
for i in range(9):
    col, row = i % 3, i // 3
    cellx = GX + col * CELLW
    celly = GY + row * CELLH
    ix = cellx
    iy = celly + (CELLH - ih) / 2.0
    print("  %-3d %-12s x=%-8.2f y=%-8.2f w=%-7.2f h=%-6.2f  x=%-8.2f y=%-8.2f w=%-7.2f h=%-6.2f  %s"
          % (i + 1, names[i], ix, iy, iw, ih, cellx, celly, CELLW, CELLH, acts[i]))

# 标签可读性：图标 PNG 第二带（英文标签）ink 高 37-38 px
print("  图标 PNG 分带实测：图形带高 112-130 px，英文标签带高 37-38 px")
print("  → 缩放后标签 ink 高 = %.1f px（%.1f x %.6f）" % (38 * ki, 38, ki))
print("  → 缩放后图形带高 = %.1f .. %.1f px" % (112 * ki, 130 * ki))

# ------------------------------------------------------------------ C. 正文区
print("=" * 72)
print("C. 对话框正文区（用户绿框）")
TX, TY, TW, TH = 246, 806, 1224, 201
print("  正文区 = (%d,%d,%d,%d) ；右沿 %d（九宫格左沿 %d，间隔 %d）" % (TX, TY, TW, TH, TX + TW, GX, GX - (TX + TW)))
for S, sp, ml in ((40, 1.4, 3), (42, 1.2, 4), (44, 1.2, 3), (46, 1.4, 3), (48, 1.4, 3)):
    lh = int(S * sp)
    print("  size=%d spacing=%.2f max_lines=%d → lineH=%d blockH=%d %s"
          % (S, sp, ml, lh, lh * ml, "OK" if lh * ml <= TH else "**溢出**"))
# -*- coding: utf-8 -*-
"""量实机导图里 4 块文案的实绘左沿 / 墨迹范围（只读 PNG，不写任何工程文件）。

判据（可复算）：文案墨迹 = 相对「本行带中位数亮度」明显更暗的像素。
  · 逐块取带 = item_text 的全局矩形（list.x+item_text.x .. +w，list.y+item_text.y .. +h）
  · 阈值 = 该带亮度中位数 - 60（文字为深色 @palette.node_locked 压浅色板）
  · 左沿 = 该带内「整列至少有 2 个墨迹像素」的最小列号（滤掉单像素噪点）
用法：python measure_shot_text_edges.py <png> [...]
"""
import sys, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")

d = json.load(open(SCREEN, encoding="utf-8"))
lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
it = lst["item_text"]
pitch = lst["item_h"] + lst["gap"]

def band(i):
    """第 i 块的 item_text 全局矩形"""
    x = lst["x"] + it["x"]
    y = lst["y"] + i * pitch + it["y"]
    return x, y, it["w"], it["h"]

def lum(px):
    r, g, b = px[0], px[1], px[2]
    return 0.299 * r + 0.587 * g + 0.114 * b

def measure(path):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    px = im.load()
    print("== %s  (%dx%d)  字号=%s 行距=%s" % (os.path.basename(path), W, H,
          (it.get("font") or lst["font"])["size"], lst.get("line_spacing", "继承")))
    print("   item_text 设计框（全局）: x=%d y=+%d w=%d h=%d  就地各块 y=%s"
          % (band(0)[0], it["y"], it["w"], it["h"],
             [band(i)[1] for i in range(4)]))
    edges = []
    for i in range(4):
        bx, by, bw, bh = band(i)
        bx = max(0, bx); by = max(0, by)
        bw = min(bw, W - bx); bh = min(bh, H - by)
        # 亮度中位数（抽样）
        vals = sorted(lum(px[x, y]) for y in range(by, by + bh, 2) for x in range(bx, bx + bw, 2))
        med = vals[len(vals) // 2]
        thr = med - 60
        cols = []
        for x in range(bx, bx + bw):
            c = sum(1 for y in range(by, by + bh) if lum(px[x, y]) < thr)
            cols.append(c)
        left = next((bx + k for k, c in enumerate(cols) if c >= 2), None)
        right = next((bx + k for k in range(len(cols) - 1, -1, -1) if cols[k] >= 2), None)
        # 墨迹行范围（纵向）
        rows = [y for y in range(by, by + bh)
                if sum(1 for x in range(bx, bx + bw) if lum(px[x, y]) < thr) >= 2]
        edges.append(left)
        print("   块%d 带=(%d,%d,%d,%d) 中位亮=%.0f 阈=%.0f  实绘左沿=%s 右沿=%s 墨迹行=%s..%s"
              % (i, bx, by, bw, bh, med, thr, left, right,
                 rows[0] if rows else None, rows[-1] if rows else None))
    if all(e is not None for e in edges):
        print("   => 左沿集合 = %s   极差 = %d px" % (edges, max(edges) - min(edges)))
    return edges

if __name__ == "__main__":
    for p in sys.argv[1:]:
        measure(p)

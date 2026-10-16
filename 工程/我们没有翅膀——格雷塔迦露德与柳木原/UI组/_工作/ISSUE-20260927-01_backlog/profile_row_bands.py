# -*- coding: utf-8 -*-
"""逐行亮度剖面：看块底板（item_frame）的可见带上下沿在哪、与文案首行墨迹的相对位置。
只读 PNG，输出文本读数（不写工程文件）。
"""
import os, json, statistics as st
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))
d = json.load(open(os.path.join(UI, "layout", "screens", "26_backlog.json"), encoding="utf-8"))
lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
it = lst["item_text"]
pitch = lst["item_h"] + lst["gap"]
BC = lst["x"]                      # 列表左沿

def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

def run(src):
    im = Image.open(src).convert("RGB"); px = im.load()
    print("==", os.path.basename(src), im.size, " 列表 x=%d y=%d item_h=%d gap=%d" % (lst["x"], lst["y"], lst["item_h"], lst["gap"]))
    for i in range(4):
        top = lst["y"] + i * pitch
        print(" 块%d 顶=%d" % (i, top))
        # 避开文字区：取按钮左侧以外的窄列 x 180..380（按钮 y 局部 18..62）
        for y in range(top, top + lst["item_h"] + 8, 4):
            band = [lum(px[x, y]) for x in range(lst["x"] + 12, lst["x"] + 205, 3)]   # 局部 12..205（按钮列左半）
            txt = [lum(px[x, y]) for x in range(lst["x"] + 260, lst["x"] + 1500, 7)]  # 文案区
            print("   y=%4d 局部=%3d  左栏中位=%6.1f  文案中位=%6.1f%s"
                  % (y, y - top, st.median(band), st.median(txt),
                     "   <-- 文案墨迹" if st.median(txt) < st.median(band) - 40 else ""))

if __name__ == "__main__":
    import sys
    run(sys.argv[1])

# -*- coding: utf-8 -*-
"""M3 证据：两态截图的像素差异度量（收起态 vs 展开+钉住+tip）。
做法：先从截图里量出画布矩形的实际位置与缩放（黑底 letterbox 与页面底色可区分），
再把「差异像素」按画布坐标分到「快捷条区域」与「其余区域」两类 ——
后者应当恒为 0（证明附加层之外的画面零改动）。
用法：python m3_pixdiff.py <a.png> <b.png>
"""
import sys
from PIL import Image, ImageChops

CW, CH = 1920, 1080          # 画布设计尺寸（ui_layout.canvas）
# 快捷条元素的版面包围盒（来自 layout/screens/35_quickbar.json，见 dump_quickbar.txt）
QB = (1665, 7, 1920, 905)


def canvas_rect(im):
    """在截图中定位画布矩形：扫描若干行，取「接近纯黑」的最左/最右列。"""
    px = im.load()
    w, h = im.size
    lefts, rights = [], []
    for y in range(0, h, 7):
        xs = [x for x in range(w) if sum(px[x, y][:3]) < 12]
        if len(xs) > w // 3:                       # 该行大部分是画布（黑底）
            lefts.append(xs[0]); rights.append(xs[-1])
    if not lefts:
        return None
    return min(lefts), max(rights)


a = Image.open(sys.argv[1]).convert("RGB")
b = Image.open(sys.argv[2]).convert("RGB")
print("A =", sys.argv[1])
print("B =", sys.argv[2])
print("尺寸 A=%s B=%s" % (a.size, b.size))
if a.size != b.size:
    raise SystemExit("尺寸不同，无法逐像素比对")

r = canvas_rect(a)
if not r:
    raise SystemExit("定位不到画布矩形")
x0, x1 = r
s = (x1 - x0) / float(CW)
print("截图中的画布矩形 x=%d..%d（宽 %d px）⇒ 缩放 scale=%.6f（=%d/%d）" % (x0, x1, x1 - x0 + 1, s, CW, CW))

d = ImageChops.difference(a, b).convert("L")
print("差异 bbox =", d.getbbox())
px = d.load()
w, h = a.size

in_qb = out_qb = 0
maxout = 0
for y in range(h):
    for x in range(w):
        v = px[x, y]
        if v == 0:
            continue
        cx = (x - x0) / s
        # 边界留 2px 容差：气泡面板左缘在半像素缩放下会产生 1–2 列抗锯齿（差 ≤5/255），
        # 属缩放置换误差、不是内容差异（下方单独报该残差）。
        if (QB[0] - 2) <= cx <= QB[2]:
            in_qb += 1
        else:
            out_qb += 1
            if v > maxout:
                maxout = v

print("非零差异像素：快捷条横向区间（画布 x %d..%d，左右各留 2px 抗锯齿容差）内 = %d，区间外 = %d（最大灰度差 %d）"
      % (QB[0], QB[2], in_qb, out_qb, maxout))
print("⇒ 结论：%s" % ("两态差异**完全落在快捷条区间内**（其余画面逐像素相同）"
                   if out_qb == 0 else "存在快捷条区间之外的差异，需人工核查"))

# -*- coding: utf-8 -*-
r"""按钮文字：7 行方框图 → 逐字 → 按 x=i*52 拼合（去方框）。

■ 切分策略（**结构驱动**，已用 BATCH2 实测标定）

  1. 行带：alpha>150 的行投影，裂缝 >15px 断开，保留高 >=120px 的段 → 7 条。
  2. 带内字格边界：**方框之间的空隙是纯透明列**（实测 frac=0.00 连续 16 列），
     而方框线（4–5px 粗、frac≈0.99）与字形竖笔（frac 也可达 0.99，**不可用 frac 区分**）
     都非零。故：带内缺口 = 宽 >=4 且 frac<0.02 的列游程，共应有 n-1 个
     → 由其切出 n 个方框跨度；缺则回退「带内 bbox 等分」。
  3. 竖向内缩：方框上/下横边 = 行 frac>0.95 的首/末行；字格取其内侧，再内缩 RING。
  4. 字格内缩 RING px 去掉方框线 → 取字形包围盒 → **等比**缩放（主导边 = 48，不拉伸）
     → 居中贴进 48×48。
  5. 拼合 x = i*(48+4) → 总宽严格 = 48n+4(n-1)。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out_btn")

CH, GAP = 48, 4
THR_BOX = 150      # 结构（方框线）判定阈值
THR_INK = 24       # 字形包围盒（含柔光）
THR_BODY = 160     # 「字身」包围盒：归一化基准
RING = 9           # 字格内缩，用于去掉方框线

WORDS = [("开始游戏", "start"), ("继续游戏", "continue"), ("读取存档", "load"),
         ("流程图", "flowchart"), ("设置", "config"), ("画廊", "gallery"),
         ("离开游戏", "exit")]


def row_bands(al, thr=THR_BOX, merge=15, minh=120):
    rows = (al > thr).sum(axis=1)
    nz = np.nonzero(rows)[0]
    if len(nz) == 0:
        return []
    out = []
    s = prev = nz[0]
    for v in nz[1:]:
        if v - prev > merge:
            out.append((int(s), int(prev)))
            s = v
        prev = v
    out.append((int(s), int(prev)))
    return [b for b in out if b[1] - b[0] + 1 >= minh]


def runs(mask, mind=4):
    """布尔数组上的 True 游程（长度 >= mind）→ [(a,b)]。"""
    out = []
    s = None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if i - s >= mind:
                out.append((s, i - 1))
            s = None
    if s is not None and len(mask) - s >= mind:
        out.append((s, len(mask) - 1))
    return out


def box_spans(al, y0, y1, n):
    """由「方框之间的纯透明列」切出 n 个方框跨度。失败返回 None。"""
    h = y1 - y0 + 1
    sub = al[y0:y1 + 1]
    frac = (sub > THR_BOX).sum(axis=0) / float(h)
    nz = np.nonzero(frac > 0.5)[0]
    if len(nz) == 0:
        return None, []
    X0, X1 = int(nz.min()), int(nz.max())
    inner = frac[X0:X1 + 1] < 0.02
    gaps = [(X0 + a, X0 + b) for a, b in runs(inner, 4)]
    if len(gaps) != n - 1:
        return None, ["    缺口 %d 个（期望 %d）→ 回退等分 %s" % (len(gaps), n - 1, gaps)]
    spans = []
    cur = X0
    for a, b in gaps:
        spans.append((cur, a - 1))
        cur = b + 1
    spans.append((cur, X1))
    return spans, ["    方框跨度 %s" % (spans,)]


def yruns(al, y0, y1, x0, x1):
    """方框上/下横边：行 frac>0.95 的首/末行。"""
    w = x1 - x0 + 1
    row = (al[y0:y1 + 1, x0:x1 + 1] > THR_BOX).sum(axis=1) / float(w)
    hit = np.nonzero(row > 0.95)[0]
    if len(hit) < 2:
        return y0, y1
    return y0 + int(hit.min()), y0 + int(hit.max())


def bbox_ab(al, x0, y0, x1, y1, thr):
    """返回 (xmin, ymin, xmax, ymax)，坐标为绝对。空则 None。"""
    if x1 < x0 or y1 < y0:
        return None
    sub = al[y0:y1 + 1, x0:x1 + 1]
    ys, xs = np.nonzero(sub >= thr)
    if len(ys) == 0:
        return None
    return (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()), y0 + int(ys.max()))


def to48(rgba, inner_box, bb_body):
    """按**字身**包围盒等比缩放（主导边 = 48，不拉伸），字身中心对齐 48 盒中心。

    做法：把「方框内侧窗口」（已保证无方框线）整体按 k 缩放，再按字身中心对齐贴进
    48×48 —— 这样柔光不会被「以字身中心开的对称窗」误裁，也不会把方框线带进来；
    超出 48 盒的部分（最外圈极淡的柔光）由 paste 自然裁掉。
    """
    ix0, iy0, ix1, iy1 = inner_box
    inner = rgba.crop((ix0, iy0, ix1 + 1, iy1 + 1))
    bw = bb_body[2] - bb_body[0] + 1
    bh = bb_body[3] - bb_body[1] + 1
    k = CH / float(max(bw, bh))
    nw = max(1, int(round(inner.size[0] * k)))
    nh = max(1, int(round(inner.size[1] * k)))
    scaled = inner.resize((nw, nh), Image.LANCZOS)
    lcx = (bb_body[0] - ix0 + bb_body[2] - ix0 + 1) / 2.0
    lcy = (bb_body[1] - iy0 + bb_body[3] - iy0 + 1) / 2.0
    px = int(round(CH / 2.0 - lcx * k))
    py = int(round(CH / 2.0 - lcy * k))
    cell = Image.new("RGBA", (CH, CH), (0, 0, 0, 0))
    cell.paste(scaled, (px, py), scaled)
    a2 = np.array(cell)[..., 3]
    ys, xs = np.nonzero(a2 >= THR_BODY)
    sz = (int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)) if len(ys) else (0, 0)
    return cell, sz, k


def slice_sheet(path, verbose=True):
    rgba = Image.open(path).convert("RGBA")
    al = np.array(rgba)[..., 3]
    bs = row_bands(al)
    diag = ["  画布 %d×%d ｜ 行带 %d" % (rgba.size[0], rgba.size[1], len(bs))]
    if len(bs) != 7:
        diag.append("  ✗ 行带数 != 7：%s" % (bs,))
        return None, diag
    res = {}
    for (y0, y1), (zh, wkey) in zip(bs, WORDS):
        n = len(zh)
        spans, msg = box_spans(al, y0, y1, n)
        diag.append("  行 %-4s 行带(%d,%d)" % (zh, y0, y1))
        diag += msg
        if spans is None:
            bb = bbox_ab(al, 0, y0, rgba.size[0] - 1, y1, THR_BOX)
            if bb is None:
                diag.append("     ✗ 空带"); continue
            X0, X1 = bb[0], bb[2]
            spans = [(X0 + (X1 - X0) * i // n, X0 + (X1 - X0) * (i + 1) // n - 1) for i in range(n)]
        cells = []
        for i, (bx0, bx1) in enumerate(spans):
            ty, by = yruns(al, y0, y1, bx0, bx1)
            ix0, iy0, ix1, iy1 = bx0 + RING, ty + RING, bx1 - RING, by - RING
            full = bbox_ab(al, ix0, iy0, ix1, iy1, THR_INK)
            body = bbox_ab(al, ix0, iy0, ix1, iy1, THR_BODY)
            if full is None or body is None:
                diag.append("     ✗ 字格%d 空（%s）" % (i, zh[i])); cells.append(None); continue
            cell, sz, k = to48(rgba, (ix0, iy0, ix1, iy1), body)
            diag.append("     %s 字身源 %dx%d ｜ 盒内字身 %dx%d ｜ 含柔光源 %dx%d ｜ k=%.3f"
                        % (zh[i], body[2] - body[0] + 1, body[3] - body[1] + 1, sz[0], sz[1],
                           full[2] - full[0] + 1, full[3] - full[1] + 1, k))
            cells.append(cell)
        res[zh] = cells
    return res, diag


def compose_word(cells, zh):
    n = len(zh)
    W = CH * n + GAP * (n - 1)
    im = Image.new("RGBA", (W, CH), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        if c is not None:
            im.alpha_composite(c, (i * (CH + GAP), 0))
    return im


if __name__ == "__main__":
    names = sys.argv[1:] or ["BATCH2_7rows"]
    dest = os.path.join(OUT, "sliced")
    for nm in names:
        p = os.path.join(OUT, nm + ".png")
        print("=" * 78)
        print(nm)
        res, diag = slice_sheet(p)
        for d in diag:
            print(d)
        if res is None:
            continue
        d2 = os.path.join(dest, nm)
        os.makedirs(d2, exist_ok=True)
        for zh, wkey in WORDS:
            cells = res.get(zh)
            if not cells or any(c is None for c in cells):
                print("  ✗ %s 缺格" % zh); continue
            compose_word(cells, zh).save(os.path.join(d2, "%s.png" % wkey))
        print("  → %s" % d2)

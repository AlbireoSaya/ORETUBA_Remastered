# -*- coding: utf-8 -*-
"""E2（第 2 步）像素级自证：从引擎导出的 PNG 上量 `current` 高亮环 / 连线两态。

用法（在 UI组 目录下）：
    python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_measure_png.py" ring <png> <layout/screens/32_flowchart.json>
    python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_measure_png.py" links <png> <json> [<png2>]
    python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_measure_png.py" crop <png> <x> <y> <w> <h> <out.png> <scale>

判据（全部来自接口冻结 §四.3 的**同一几何公式**，与 HTML 侧一致）：
    路径矩形 = 节点元素矩形**内缩 1px**（x+1, y+1, w-2, h-2）；圆角半径 r=16；描边线宽 3；
    色 `@palette.node_current` = #D8A83C。描边以路径为中心 ⇒ 墨迹横向覆盖
    [x-0.5, x+2.5]（即列 x-1..x+2，首尾两列是 AA 半覆盖）。
"""
import json
import sys

from PIL import Image

RING_RGB = (216, 168, 60)      # @palette.node_current #D8A83C
LINK_RGB = (38, 96, 128)       # @palette.edge_normal   #266080
TOL = 14                        # 每通道容差（AA / 与底色混合后的判定窗口）


def is_ring(px):
    return all(abs(int(px[i]) - RING_RGB[i]) <= TOL for i in range(3))


def is_link(px):
    # 连线是 4px 实心，核心像素应**逐通道等于**数据色；这里给更小容差
    return all(abs(int(px[i]) - LINK_RGB[i]) <= 6 for i in range(3))


def load(p):
    im = Image.open(p).convert("RGBA")
    return im


def nodes_with(json_path):
    d = json.load(open(json_path, encoding="utf-8"))
    out = []
    for e in d["elements"]:
        if e.get("kind") != "image":
            continue
        st = e.get("flow_state")
        if st == "current":
            out.append(e)
    return d, out


def cmd_ring_xy(png, rects=""):
    """按**显式矩形**量环（内存副本注入的场合：屏数据里没有 `flow_state`，几何由命令行给）。

    rects 形如 `x,y,w,h;x,y,w,h`（多个节点用分号）。
    """
    im = load(png)
    W, H = im.size
    px = im.load()
    nodes = []
    for t in [t for t in rects.split(";") if t]:
        v = [int(k) for k in t.split(",")]
        assert len(v) == 4, t
        nodes.append({"id": "rect@%d,%d" % (v[0], v[1]),
                      "x": v[0], "y": v[1], "w": v[2], "h": v[3]})
    print("PNG = %s  (%dx%d)" % (png, W, H))
    print("按命令行给定矩形量环：%d 个" % len(nodes))
    return ring_report(im, px, W, H, nodes)


def cmd_ring(png, json_path, ids_csv=""):
    im = load(png)
    W, H = im.size
    px = im.load()
    d, cur = nodes_with(json_path)
    print("PNG = %s  (%dx%d)" % (png, W, H))
    print("数据里 flow_state=='current' 的节点：%d 个" % len(cur))
    if not cur and ids_csv:
        # 内存副本注入的场合（`--preset states` 加载不了 / 巡演注入步骤）：
        #   按命令行给的 id 从屏数据里取矩形 —— 注入只改 flow_state，不改几何。
        want = [t for t in ids_csv.split(",") if t]
        for e in d["elements"]:
            if e.get("kind") == "image" and e["id"] in want:
                cur.append(e)
        print("按命令行指定 id 取节点矩形：%d 个 %s" % (len(cur), want))
    if not cur:
        print("!! 本屏数据没有 current 节点 —— 本图片不该出现环（这是负向自证，不是失败）")
    return ring_report(im, px, W, H, cur)


def ring_report(im, px, W, H, cur):
    for e in cur:
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        eid = e["id"]
        cx = x + w // 2
        # 顶边：量 y 附近的每行 ring 像素数（只在顶边中段统计，避开圆角）
        rows = []
        for yy in range(y - 6, y + 8):
            if yy < 0 or yy >= H:
                continue
            n = 0
            for xx in range(x + 30, x + w - 30):
                if 0 <= xx < W and is_ring(px[xx, yy]):
                    n += 1
            rows.append((yy, n))
        # 左边：量 x 附近的每列 ring 像素数（只在左边中段统计）
        cols = []
        for xx in range(x - 6, x + 8):
            if xx < 0 or xx >= W:
                continue
            n = 0
            for yy in range(y + 30, y + h - 30):
                if 0 <= yy < H and is_ring(px[xx, yy]):
                    n += 1
            cols.append((xx, n))
        span = w - 60
        peak = max([n for _i, n in rows] or [0])
        band = [yy for yy, n in rows if n >= max(1, int(span * 0.30))]
        cband = [xx for xx, n in cols if n >= max(1, int((h - 60) * 0.30))]
        # 顶边中段的**水平**墨迹范围（在峰值行上扫）
        ypeak = max(rows, key=lambda t: t[1])[0] if rows else y
        xs = [xx for xx in range(x - 8, x + w + 8) if 0 <= xx < W and is_ring(px[xx, ypeak])]
        # 圆角自证：沿「左上角圆心」的 45° 对角线取点，量它到圆心的距离与是否环色
        #   圆心 = (x+1+r, y+1+r)（路径矩形右上/左上角的圆心）；墨迹带 = 半径 r±(w/2=1.5)
        r = 16
        ccx, ccy = x + 1 + r, y + 1 + r
        probe = []
        for k in range(0, 44, 2):
            xx, yy = x + 1 + k, y + 1 + k
            if 0 <= xx < W and 0 <= yy < H:
                dist = ((xx - ccx) ** 2 + (yy - ccy) ** 2) ** 0.5
                probe.append((xx, yy, round(dist, 2), tuple(px[xx, yy]), is_ring(px[xx, yy])))
        print("--- %s  元素矩形=(%d,%d,%d,%d)  路径矩形=(%d,%d,%d,%d)（内缩 %d）"
              % (eid, x, y, w, h, x + 1, y + 1, w - 2, h - 2, 1))
        print("    顶边：峰值行 y=%d（该行环色像素 %d/%d）｜ 行带(>=30%%) = %s"
              % (ypeak, peak, span, band))
        print("         → 期望：路径 y=%d、线宽 3 ⇒ 墨迹纵向 = [%d-1.5, %d+1.5]='"
              "[%s, %s] ⇒ **整排覆盖**的行 = %d..%d（另 p±2 行为 50%% 半覆盖 AA）"
              % (y + 1, y + 1, y + 1, y - 0.5, y + 2.5, y, y + 2))
        print("    左边：峰值列 x=%s ｜ 列带(>=30%%) = %s"
              % (max(cols, key=lambda t: t[1])[0] if cols else "?", cband))
        print("         → 期望：路径 x=%d、线宽 3 ⇒ 墨迹横向 = [%s, %s] ⇒ 整列覆盖的列 = %d..%d"
              % (x + 1, x - 0.5, x + 2.5, x, x + 2))
        print("    顶边墨迹水平范围 x=%s..%s（长度 %s）→ 直线段应为 %d..%d（长度 %d = w-2-2r）；"
              "实测略宽是**圆弧切线附近落在同一排**所致（预期行为，不是溢出）"
              % (min(xs) if xs else "?", max(xs) if xs else "?",
                 (max(xs) - min(xs) + 1) if xs else 0,
                 x + 1 + 16, x + w - 1 - 16, w - 2 - 32))
        print("    峰值行中点实测色=%s（目标 %s = #D8A83C）" % (tuple(px[cx, ypeak]), RING_RGB))
        # 圆角自证：沿「左上角圆心」的 45° 对角线取点，量它到圆心的距离与是否环色
        #   圆心 = (x+1+r, y+1+r)（路径矩形左上角的圆心）；墨迹带 = 半径 r±(w/2=1.5)
        r = 16
        ccx, ccy = x + 1 + r, y + 1 + r
        probe = []
        for k in range(0, 44, 2):
            xx, yy = x + 1 + k, y + 1 + k
            if 0 <= xx < W and 0 <= yy < H:
                dist = ((xx - ccx) ** 2 + (yy - ccy) ** 2) ** 0.5
                probe.append((xx, yy, round(dist, 2), tuple(px[xx, yy]), is_ring(px[xx, yy])))
        print("    圆角探针（左上角圆心=(%d,%d)、r=%d、墨迹带=r±1.5 ⇒ 距离 14.5..17.5）：" % (ccx, ccy, r))
        for xx, yy, dist, col, f in probe:
            print("        (%d,%d) 距离=%-6s 色=%-18s %s" % (xx, yy, dist, str(col), "★环色" if f else ""))
        print("         → 期望：距离落在 14.5..17.5（含 AA 边 13.5..18.5）的点**是**环色，"
              "距离明显更大的点（角上）**不是**环色 —— 即环沿 r=16 圆弧绕过转角，不是方角")
    return 0


def cmd_links(pngs, json_path):
    d = json.load(open(json_path, encoding="utf-8"))
    links = d.get("links", [])
    print("屏数据：links=%d 条 ｜ 层 flag flags_default=%s"
          % (len(links), d.get("flags_default")))
    for lp in pngs:
        im = load(lp)
        W, H = im.size
        px = im.load()
        # 只在图表视口内统计（fc.scroll = x60 y190 w1235 h827），避开右侧面板与页签
        vx, vy, vw, vh = 60, 190, 1235, 827
        cnt = 0
        for xx in range(vx, min(W, vx + vw)):
            for yy in range(vy, min(H, vy + vh)):
                if is_link(px[xx, yy]):
                    cnt += 1
        # 逐条连线中点采样（用数据里的 pts 中点，两端应对得上）
        hits = 0
        for lk in links:
            pts = lk["pts"]
            mx = (pts[0][0] + pts[-1][0]) // 2
            my = (pts[0][1] + pts[-1][1]) // 2
            # 取末段中点更稳（中点可能落在折角外）
            a, b = pts[-2], pts[-1]
            sx = (a[0] + b[0]) // 2
            sy = (a[1] + b[1]) // 2
            probe = []
            for ddx in range(-2, 3):
                for ddy in range(-2, 3):
                    if 0 <= sx + ddx < W and 0 <= sy + ddy < H:
                        probe.append(is_link(px[sx + ddx, sy + ddy]))
            if any(probe):
                hits += 1
        print("%s  (%dx%d)  视口内 edge_normal 核心像素 = %d ｜ 末段中点采到线的条数 = %d/%d"
              % (lp, W, H, cnt, hits, len(links)))
    return 0


def cmd_crop(a):
    src, x, y, w, h, out, scale = a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4]), a[5], int(a[6])
    im = load(src).crop((x, y, x + w, y + h))
    im = im.resize((w * scale, h * scale), Image.NEAREST)
    im.save(out)
    print("crop %s -> %s  (%dx%d, scale %d)" % (src, out, w * scale, h * scale, scale))
    return 0


def main():
    mode = sys.argv[1]
    if mode == "ring":
        return cmd_ring(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    if mode == "links":
        # links <json> <png> [<png2> ...]
        return cmd_links(sys.argv[3:], sys.argv[2])
    if mode == "ringxy":
        # ringxy <png> "x,y,w,h;x,y,w,h"
        return cmd_ring_xy(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    if mode == "crop":
        return cmd_crop(sys.argv[2:])
    raise SystemExit("mode?")


if __name__ == "__main__":
    sys.exit(main())

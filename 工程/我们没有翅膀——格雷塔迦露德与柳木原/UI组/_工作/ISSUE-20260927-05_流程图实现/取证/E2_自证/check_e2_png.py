#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_e2_png.py — ISSUE-20260927-05 / E2 · 对引擎自导 PNG 做**像素级**连线核对

契约口径（§三.1 层序 + §七.4 两端一致）
  · 连线画在「压暗/视口底板之上、节点元素之下」⇒ 连线**直接呈现自身色**，
    不再经 `fc.dim`/`fc.scroll` 叠加 ⇒ 预测色 = **从数据读到的那个色值本身**。
  · 判据：|实测 − 数据色| **逐通道 ≤ 2**（R/G/B 与 A 四个通道都比）。
  · **绝不写死颜色**：色值一律从数据读——
      - `--real` 模式：读 `layout\\screens\\32_flowchart.json` 的 `links[].color`；
      - 夹具模式：读 `run_e2_fixture.py` 落盘的 `fixture_effective.json`
        （＝**本次实际注入运行目录**的那份 links，颜色已解析为整数）⇒ 注入与复核同源。
        `--effective <file>` 可指向别的副本（用于「把数据改成另一个色，断言仍/不再 PASS」
        的注入自证）。

其余判据
  ① 线段存在：每条边每段取 3 个采样点（避开折角 8px 内），该点须落在实心中线上；
  ② 箭头开/关：在末段平直处量出线宽 line_run，再在底边附近量最宽 arrow_run ——
       arrow:true  ⇒ arrow_run ≥ 2*line_run − 2（三角底边 = 3w）
       arrow:false ⇒ arrow_run ≤ line_run + 2（只有线本身）
  ③ 遮挡：采样点若被**其它不透明美术**盖住（颜色 ≠ 连线色），单列为「遮」，
     不计通过也不计失败（真实节点框会合法压住部分折线）。
  ④ 负向对照 `--expect-no-links`：走廊上命中连线色的像素必须 **0 个**。

用法
  python check_e2_png.py                                  # 夹具（读 fixture_effective.json）
  python check_e2_png.py --png <某个证据 PNG>              # 指定图
  python check_e2_png.py --real --run-dir <临时\\ui_run>   # 真实数据（读 layout 的 links）
  python check_e2_png.py --effective <被改过色的副本.json>  # 注入自证
  python check_e2_png.py --run-dir <...> --expect-no-links # 负向对照
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
UI = HERE.parents[3]                     # .../UI组
WT = HERE.parents[6]                     # 工作树根

# 与「从数据读到的色值」的逐通道容差（契约 §三.1 / 主代理口径 ≤2）。
#   ⚠ 旧版曾用 45（叠加链预测的容差）——在真实节点美术上产生过 1 点巧合命中，
#     现改为直接比对数据色 ⇒ 巧合命中在结构上不可能。
TOL = 2


def hexstr(c):
    return "#%08X" % (c & 0xFFFFFFFF)


def png_path(args):
    if args.png:
        return Path(args.png)
    run_dir = Path(args.run_dir)
    got = sorted((run_dir / "runtime" / "savedata").glob("shot_*_flowchart.png"))
    if not got:
        raise SystemExit("[FAIL] 没找到 shot_*_flowchart.png（巡演没走到流程图屏？）")
    return got[-1]


def load_real_links():
    """真实数据：links 直接取仓库 layout\\screens\\32_flowchart.json（E1 生成器产物）"""
    p = UI / "layout" / "screens" / "32_flowchart.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for lk in (d.get("links") or []):
        out.append({"id": lk["id"], "form": lk.get("kind", "normal"), "w": lk["w"],
                    "arrow": bool(lk.get("arrow")), "pts": [list(x) for x in lk["pts"]],
                    "color": lk["color"]})
    return p, out


def load_effective_links(path):
    """夹具：读 run_e2_fixture.py 落盘的「本次实际注入」数据（颜色已解析）"""
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for lk in d["links"]:
        out.append({"id": lk["id"], "form": "fixture", "w": lk["w"],
                    "arrow": bool(lk["arrow"]), "pts": [list(x) for x in lk["pts"]],
                    "color": lk["color"]})
    return p, out


def corridor_points(lk):
    """连线上（避开折角 8px）的采样点——正/负向判据共用同一批点"""
    pts = lk["pts"]
    out = []
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        if x0 == x1 and y0 == y1:
            continue
        for t in (0.3, 0.5, 0.7):
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if min(abs(x - a) + abs(y - b) for a, b in pts) < 8:
                continue
            out.append((i, t, x, y))
    return out


def rgba_of(color):
    c = color & 0xFFFFFFFF
    return ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF, (c >> 24) & 0xFF)


def px_match(p, exp, tol=TOL):
    return max(abs(p[k] - exp[k]) for k in range(4)) <= tol


def classify(px, W, H, x, y, exp):
    """单点分类：link=命中连线色；other=被别的不透明美术压住；empty=无内容
       （3x3 邻域取最优，容忍 AA 与半像素舍入）"""
    hit_link = hit_other = False
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = (int(round(x)) + dx, int(round(y)) + dy)
            if not (0 <= q[0] < W and 0 <= q[1] < H):
                continue
            p = px[q[0], q[1]]
            if px_match(p, exp):
                hit_link = True
            elif p[3] > 200:
                hit_other = True
    if hit_link:
        return "link"
    return "other" if hit_other else "empty"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=str(WT / "临时" / "ui_run_e2_fixture"))
    ap.add_argument("--png", default="", help="直接指定 PNG（默认取 --run-dir 下最新的 shot_*_flowchart.png）")
    ap.add_argument("--real", action="store_true", help="真实数据模式：links 取 layout/screens/32_flowchart.json")
    ap.add_argument("--effective", default="", help="夹具模式读哪个「实际注入」副本（默认 fixture_effective.json）")
    ap.add_argument("--expect-no-links", action="store_true", help="负向对照：断言连线走廊上没有连线")
    args = ap.parse_args()

    png = png_path(args)
    im = Image.open(png).convert("RGBA")
    W, H = im.size
    px = im.load()

    if args.real:
        src, links = load_real_links()
    else:
        eff = args.effective or str(HERE / "fixture_effective.json")
        if not Path(eff).exists():
            raise SystemExit("[FAIL] 缺 %s —— 夹具模式请先跑 run_e2_fixture.py（它会落盘实际注入数据）" % eff)
        src, links = load_effective_links(eff)

    print("PNG      : %s" % png)
    print("size     : %dx%d  mode=RGBA" % (W, H))
    print("色值来源 : %s（%d 条）" % (src, len(links)))
    print("判据     : |实测 − 数据色| 逐通道 ≤ %d（连线直接呈现自身色，不过任何叠加层）" % TOL)
    print("数据色   : %s" % ", ".join(sorted({hexstr(l["color"]) for l in links})))

    # ---------------- 负向对照 ----------------
    if args.expect_no_links:
        n_link = n_other = n_empty = 0
        off = []
        for lk in links:
            exp = rgba_of(lk["color"])
            for (i, t, x, y) in corridor_points(lk):
                c = classify(px, W, H, x, y, exp)
                if c == "link":
                    n_link += 1
                    qc = (int(round(x)), int(round(y)))
                    off.append("%s 段[%d] (%.0f,%.0f) %s" % (lk["id"], i, x, y, px[qc[0], qc[1]]))
                elif c == "other":
                    n_other += 1
                else:
                    n_empty += 1
        print("\n[负向对照] 连线走廊逐点分类（容差 %d）：命中连线色 %d ｜ 被其他美术压住 %d ｜ 无内容 %d"
              % (TOL, n_link, n_other, n_empty))
        for o in off:
            print("   ?? " + o)
        if n_link == 0:
            print("[PASS] 走廊上 0 个连线像素 ⇒ 插件缺件时一条都不画（降级契约成立）")
            return 0
        print("[FAIL] 走廊上仍有 %d 个连线像素 —— 降级没生效" % n_link)
        return 1

    # ---------------- 正向：线段 / 箭头 ----------------
    fails = []
    print("\n%-15s %-8s %-6s %-10s %-18s %s" % ("link", "form", "段号", "数据色", "实测色(3x3内最优)", "判定"))
    for lk in links:
        exp = rgba_of(lk["color"])
        pts = lk["pts"]
        ok_seg = tried = obsc = 0
        best = None
        for (i, t, x, y) in corridor_points(lk):
            tried += 1
            c = classify(px, W, H, x, y, exp)
            qc = (int(round(x)), int(round(y)))
            if 0 <= qc[0] < W and 0 <= qc[1] < H:
                p = px[qc[0], qc[1]]
                if best is None or max(abs(p[k] - exp[k]) for k in range(4)) < max(abs(best[k] - exp[k]) for k in range(4)):
                    best = p
            if c == "link":
                ok_seg += 1
            elif c == "other":
                obsc += 1
            else:
                fails.append("%s 段[%d] t=%.1f 处 (%.0f,%.0f) 实测 %s != 数据色 %s（走廊上无内容）"
                             % (lk["id"], i, t, x, y, best, exp))
        verdict = "OK" if (ok_seg + obsc == tried and ok_seg > 0) else "FAIL"
        print("%-15s %-8s %-6s %-10s %-18s %s" % (
            lk["id"], lk["form"], "%d/%d(+%d遮)" % (ok_seg, tried, obsc), hexstr(lk["color"]), best, verdict))
        if verdict == "FAIL":
            fails.append("%s 线段判定失败：命中 %d / 采样 %d（被遮 %d）" % (lk["id"], ok_seg, tried, obsc))

        # 箭头判定（自校准）
        tipx, tipy = pts[-1]
        px2, py2 = pts[-2]
        dx, dy = tipx - px2, tipy - py2
        n = (dx * dx + dy * dy) ** 0.5
        dx, dy = dx / n, dy / n
        L = 2.0 * lk["w"]
        half = 1.5 * lk["w"]
        bx = int(round(tipx - dx * L))
        by = int(round(tipy - dy * L))

        def run_at(cx, cy):
            cx, cy = int(round(cx)), int(round(cy))
            best_run = 0
            for yrow in range(cy - 3, cy + 4):
                if not (0 <= yrow < H):
                    continue
                r = 0
                for x in range(int(cx - half) - 4, int(cx + half) + 5):
                    if 0 <= x < W and px_match(px[x, yrow], exp):
                        r += 1
                best_run = max(best_run, r)
            return best_run

        run = run_at(bx, by)
        # 线宽基准**多点探测**：单点可能正好落在被遮挡/被别的美术压住的位置
        #   （实测：探针落点 line_run=0 时，arrow:false 的判据会**空洞地通过**）。
        # 探针距端点 c 的合法区间：**必须越过三角底边**（c > L+2）且**不贴到另一端折角**
        #   （c ≤ seglen − 8）。★ 这里的上界只减 8，**不能再减 L** —— 真实数据里有 30px 的
        #   短边（如 [[490,255],[490,285]]），多减一个 L 会把所有探针排除掉，
        #   导致 11/13 条误报 INCONCLUSIVE（本机实测踩过）。
        seglen = ((tipx - px2) ** 2 + (tipy - py2) ** 2) ** 0.5
        cands = [c for c in (L + 10, L + 22, L + 34) if (L + 2) < c <= (seglen - 8)]
        line_run = max([run_at(tipx - dx * c, tipy - dy * c) for c in cands]) if cands else 0
        if line_run <= 0:
            verdict_a = "INCONCLUSIVE（末段平直处探针均未取到线宽：被遮挡或末段过短）"
            okarrow = False
        elif lk["arrow"]:
            okarrow = run >= max(2 * line_run - 2, line_run + 3)
            verdict_a = "OK" if okarrow else "FAIL"
        else:
            okarrow = run <= line_run + 2
            verdict_a = "OK" if okarrow else "FAIL"
        print("   箭头 %-5s : 平直处线宽 %d px ｜ 底边处最宽 %d px → %s"
              % ("true" if lk["arrow"] else "false", line_run, run, verdict_a))
        if not okarrow:
            fails.append("%s 箭头判定失败：arrow_run=%d line_run=%d" % (lk["id"], run, line_run))

    print()
    if fails:
        print("[FAIL] %d 项不符：" % len(fails))
        for f in fails:
            print("   " + f)
        return 1
    print("[PASS] 全部 %d 条边：线段位置、**颜色（逐通道 ≤%d）**、箭头开关均与数据一致" % (len(links), TOL))
    print("       证据 PNG = %s" % png)
    print("       色值来源 = %s" % src)
    return 0


if __name__ == "__main__":
    sys.exit(main())

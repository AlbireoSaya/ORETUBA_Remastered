# -*- coding: utf-8 -*-
r"""M46 · HTML 端「列表逐项三态」目标级验收：三个状态各出一张无头截图 + 位置级断言

■ 判据（与 krkr 侧巡演的同名合成指针步骤一一对应）
  ① 常态（`?screen=choices`）vs 悬停第 2 项（`&hover=ch.choices~1`）逐像素作差
     ⇒ **只有一条选项带变了**：差异框高 ≤ 单条带高（两条带至少相隔一个行距 100 画布 px，
        若两条一起变，差异框必然横跨两带、高度 ≥ 2 行距）。
  ② 常态 vs 按住第 3 项（`&press=ch.choices~2`）同理。
  ③ **哪一条**：悬停差异框上沿与按住差异框上沿之差 == **一个行距**（83+17=100 画布 px × s）
     —— 这条是免偏移的定位判据（不必知道画布在截图里的绝对位置）。
  ④ 整条换图：差异框宽 ≥ 选项条宽 1113 × s × 0.9。
  ⑤ 探针确实走 DOM 事件路径：dump 里出现 `data-ui-hover-probe="1"` / `data-ui-press-probe="1"`。
  ⑥ 缩放比 s **从 DOM 实测**（`#canvas` 的 `style="transform: scale(s)"`），不猜。

■ 用法
    python _工作\M46_逐项三态证据\复现脚本\m46_html_state_shots.py
"""
import io
import os
import re
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))          # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m46"

ROW_H, GAP, ITEM_W = 83, 17, 1113      # layout/screens/36_choices.json
PITCH = ROW_H + GAP


def url(query):
    p = os.path.join(REP, "index.html").replace("\\", "/")
    return "file:///" + urllib.parse.quote(p) + query


def shot(query, out_png=None, dump_dom=None):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1920,1080", "--virtual-time-budget=9000"]
    if out_png:
        cmd.append("--screenshot=" + out_png)
    if dump_dom:
        cmd.append("--dump-dom")
    cmd.append(url(query))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dump_dom:
        dom = r.stdout.decode("utf-8", "replace")
        io.open(dump_dom, "w", encoding="utf-8").write(dom)
        return dom
    return ""


def diff_bbox(a, b):
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox()


def main():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    n_png = os.path.join(EVID, "M46_html_常态.png")
    h_png = os.path.join(EVID, "M46_html_悬停第2项.png")
    p_png = os.path.join(EVID, "M46_html_按住第3项.png")
    dump = os.path.join(EVID, "M46_html_probe_dump.html")

    dom = shot("?screen=choices&hover=ch.choices~1", out_png=h_png, dump_dom=dump)
    shot("?screen=choices", out_png=n_png)
    shot("?screen=choices&press=ch.choices~2", out_png=p_png)
    if not all(os.path.exists(p) for p in (n_png, h_png, p_png)):
        print("判定：FAIL（截图缺文件）")
        return 1

    fails = []
    # ⑥ 缩放比：从 DOM 的 #canvas 内联 transform 实测
    m = re.search(r'id="canvas"[^>]*transform:\s*scale\(([0-9.]+)\)', dom)
    if not m:
        m = re.search(r'transform:\s*scale\(([0-9.]+)\)', dom)
    s = float(m.group(1)) if m else 0.0
    print("⑥ DOM 实测缩放比 s = %.4f（画布 1920×1080）" % s)
    if s <= 0:
        fails.append("⑥ 取缩放比")

    a, b, c = Image.open(n_png), Image.open(h_png), Image.open(p_png)
    print("截图尺寸 =", a.size)
    bb_h, bb_p = diff_bbox(a, b), diff_bbox(a, c)
    print("① 常态 vs 悬停 差异框 =", bb_h)
    print("② 常态 vs 按住 差异框 =", bb_p)
    if not bb_h or not bb_p:
        print("判定：FAIL（作差为空 —— 悬停/按下没有换图）")
        return 1

    def w(bb):
        return bb[2] - bb[0]

    def h(bb):
        return bb[3] - bb[1]

    band_h = ROW_H * s
    tests = [
        ("① 悬停只改一条带（差异框高 ≤ 单条带高 %.1f，实测 %d）" % (band_h + 3, h(bb_h)),
         h(bb_h) <= band_h + 3),
        ("② 按住只改一条带（差异框高 ≤ 单条带高 %.1f，实测 %d）" % (band_h + 3, h(bb_p)),
         h(bb_p) <= band_h + 3),
        ("① 差异确为整条带（高 ≥ 60%% 带高 = %.1f，实测 %d）" % (band_h * 0.6, h(bb_h)),
         h(bb_h) >= band_h * 0.6),
        ("③ 悬停带与按住带相距一个行距（期望 %.1f，实测 %d）" % (PITCH * s, bb_p[1] - bb_h[1]),
         abs((bb_p[1] - bb_h[1]) - PITCH * s) <= 4),
        ("④ 整条换图（差异框宽 ≥ 90%% 条宽 %.1f，实测 %d）" % (ITEM_W * s * 0.9, w(bb_h)),
         w(bb_h) >= ITEM_W * s * 0.9),
        ("④ 覆盖不全带外（差异框宽 ≤ 条宽 %.1f，实测 %d）" % (ITEM_W * s + 4, w(bb_h)),
         w(bb_h) <= ITEM_W * s + 4),
        ("⑤ hover 探针走 DOM 事件路径", 'data-ui-hover-probe="1"' in dom),
    ]
    for name, ok in tests:
        print(("  PASS  " if ok else "  FAIL  ") + name)
        if not ok:
            fails.append(name)

    # 按住态的探针标记另跑一次 dump（避免与 hover 混在同一次导航里）
    dom2 = shot("?screen=choices&press=ch.choices~2", dump_dom=os.path.join(EVID, "M46_html_press_dump.html"))
    ok = 'data-ui-press-probe="1"' in dom2
    print(("  PASS  " if ok else "  FAIL  ") + "⑤ press 探针走 DOM 事件路径")
    if not ok:
        fails.append("⑤ press 探针")

    # 对照图（与 krkr 端同一排布：常态 / 悬停 / 按住）
    pad = 26
    x0 = max(0, min(bb_h[0], bb_p[0]) - pad)
    x1 = min(a.size[0], max(bb_h[2], bb_p[2]) + pad)
    y0 = max(0, min(bb_h[1], bb_p[1]) - pad)
    y1 = min(a.size[1], max(bb_h[1] + h(bb_h), bb_p[1] + h(bb_p)) + pad)
    crops = [im.crop((x0, y0, x1, y1)) for im in (a, b, c)]
    W, H = crops[0].size
    out = Image.new("RGB", (W, H * 3 + 16), (20, 20, 20))
    for i, cr in enumerate(crops):
        out.paste(cr, (0, i * (H + 8)))
    out_png = os.path.join(EVID, "M46_html_三态对照.png")
    out.save(out_png)
    print("对照图 =", out_png, out.size)

    print("判定：" + ("**全部通过**" if not fails else ("未通过 → " + "、".join(fails))))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

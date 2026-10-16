# -*- coding: utf-8 -*-
"""ISSUE-20260927-02 · F 组 · 回想屏三件中线 / 按钮 x 的**断言探针**（只读 PNG + 数据；带退出码）。

判定（逐块 4 行全检，任一失败即 FAIL + 退出码 1）：
  [1] 文案首行墨迹中线 vs 胶囊可见体中线（主口径 α≥128，由元素矩形 + 素材 alpha 推出）：逐块 |Δ| ≤ 2px
  [1b] **定靶对照（块0）**：直接断言「胶囊上下描边真的落在数据给的行上」（元素+6 / +23，邻域深 ≥3.0）
       ⇒ 证明导图里那枚胶囊的位置就是数据说的位置（不依赖 alpha 推导）
  [2] 文案首行墨迹中线 vs 胶囊可见体中线（宽口径 α≥8 / α≥64）：逐块 |Δ| ≤ 2px
  [3] 胶囊可见体中线 vs 重播图标可见体中线：逐块 |Δ| ≤ 2px   ← **纯几何**（两边都是控件、不含文字，
      故无字形抖动；实测恒为 +1.0px，= 两个素材「可见体中心对元素框中心」的 0.0 / 0.5px 之和）
  [4] 文案首行墨迹中线 vs 重播图标中线：**只看四块均值** ≤ 2px（逐块值只打印）——文字的墨迹 bbox 中线
      本身随**该块首行字形**抖动（实测四块墨迹行数 30/29/33/30 ⇒ 逐块 ±1.5px），故不作逐块硬判
  [5] 数据层：jump.x == 15、replay.x == 141（PSB 口径），且两键矩形在块内、互不重叠、不压文案区
  [6] 实机层 x：胶囊实绘左沿 = list.x + jump.x + 4、图标实绘左沿 = list.x + replay.x + 1
  [7] **已知未决（不判 FAIL，只打印）**：标签墨迹中线与胶囊中心恒差 6.0px（引擎侧口径，见 ③）

用法：
    python verify_f_backlog_shot.py <shot_29_backlog.png>        # 断言
    python verify_f_backlog_shot.py --mutate <shot_...png>       # 变异自证：把目标阈值收到 0.1px，必须 FAIL
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCREEN = os.path.join(UI, "layout", "screens", "26_backlog.json")
ASSUI = os.path.join(UI, "krkr", "assets", "ui")

TOL = 2.0
CAP_T128 = 14.5      # 素材 alpha≥128 行 6..23 的中点（相对元素框顶）
CAP_WIDE = 14.0      # alpha≥8 行 2..26 / α≥64 行 5..23 的中点
REPLAY_OFF = 21.5    # x_ui_spk2_off.png alpha≥8 行 1..42 的中点
JUMP_PAD = 4         # 胶囊素材 α≥64 最左列
REPLAY_PAD = 1       # 图标素材 α≥64 最左列


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mutate = "--mutate" in sys.argv
    tol = 0.1 if mutate else TOL
    path = args[0]
    d = json.load(open(SCREEN, encoding="utf-8"))
    lst = [e for e in d["elements"] if e["id"] == "bl.list"][0]
    it = lst["item_text"]
    bj = [b for b in lst["item_buttons"] if b["key"] == "jump"][0]
    br = [b for b in lst["item_buttons"] if b["key"] == "replay"][0]
    im = Image.open(path).convert("RGB")
    px = im.load()
    pitch = lst["item_h"] + lst["gap"]
    fails = []
    txt_icon = []

    def chk(cond, tag, msg):
        print(("  PASS " if cond else "  FAIL ") + tag + "：" + msg)
        if not cond:
            fails.append(tag)

    print("断言探针：%s（容差 %.2fpx%s）" % (os.path.basename(path), tol, "，★变异模式" if mutate else ""))
    for i in range(4):
        ry = lst["y"] + i * pitch
        ty0, ty1 = ry + it["y"], ry + it["y"] + 41
        tx0, tx1 = lst["x"] + it["x"], lst["x"] + it["x"] + it["w"] - 1
        vals = sorted(lum(px[x, y]) for y in range(ty0 - 5, ty1 + 1, 2) for x in range(tx0, tx1 + 1, 3))
        thr = vals[len(vals) // 2] - 60
        rows = [y for y in range(ty0 - 5, ty1 + 1)
                if sum(1 for x in range(tx0, tx1 + 1) if lum(px[x, y]) < thr) >= 2]
        t = (rows[0] + rows[-1]) / 2.0
        jy, rx, ryy = ry + bj["y"], lst["x"] + br["x"], ry + br["y"]
        c128, cwide = jy + CAP_T128, jy + CAP_WIDE
        chk(abs(t - c128) <= tol, "[1]块%d 文案↔胶囊(α≥128)" % i,
            "文案 %.1f vs 胶囊 %.1f ⇒ Δ %+.1f" % (t, c128, t - c128))
        chk(abs(t - cwide) <= tol, "[2]块%d 文案↔胶囊(α≥8/64)" % i,
            "文案 %.1f vs 胶囊 %.1f ⇒ Δ %+.1f" % (t, cwide, t - cwide))
        # [1b] **实机口径（定靶断言）**：直接问「胶囊的上下描边真的落在数据说的行上吗」——
        #   元素 y 由数据给（jump.y），描边在素材的 +6 / +23 行（alpha≥128 的可见体上下缘），
        #   判据 = 该行的列均值比 ±3 行的邻居低 ≥3.0（行带自带纵向渐变，故用**邻域比较**而非绝对阈值）。
        #   列区间取胶囊右半（元素右沿左 24..6px），避开「跳转」墨迹；**只判块0**：块2/3 处底图板更暗、
        #   胶囊与其描边的对比被压到 <3（实测），该判据在那里不成立（不是渲染问题，是判据失效）。
        if i == 0:
            xr = lst["x"] + bj["x"] + bj["w"]
            pv = [sum(lum(px[x, y]) for x in range(xr - 24, xr - 6)) / 18.0
                  for y in range(jy, jy + bj["h"])]
            d_top = pv[6] - min(pv[3], pv[9])
            d_bot = pv[23] - min(pv[20], pv[26])
            chk(d_top <= -3.0 and d_bot <= -3.0, "[1b]块0 实机胶囊描边落在数据行上（元素+6/+23）",
                "元素 top=%d ⇒ 上描边行 %d 深 %+.2f ｜ 下描边行 %d 深 %+.2f｜胶囊可见体中线 %d = 文案 %.1f（Δ %+.1f）"
                % (jy, jy + 6, d_top, jy + 23, d_bot, jy + 14, t, t - (jy + 14)))
        rmid = ryy + REPLAY_OFF
        chk(abs(c128 - rmid) <= tol, "[3]块%d 胶囊↔重播图标" % i,
            "胶囊 %.1f vs 图标 %.1f ⇒ Δ %+.1f" % (c128, rmid, c128 - rmid))
        txt_icon.append(t - rmid)
        # 标签墨迹（未决项，仅打印）
        jx0, jx1 = lst["x"] + bj["x"], lst["x"] + bj["x"] + bj["w"] - 1
        lr = [y for y in range(jy - 5, jy + bj["h"] + 5)
              if sum(1 for x in range(jx0, jx1 + 1) if lum(px[x, y]) < 175) >= 1]
        lm = (lr[0] + lr[-1]) / 2.0
        print("  ....[7]块%d 标签墨迹 %.1f vs 胶囊 %.1f ⇒ Δ %+.1f（引擎侧固定口径 6.0px，未决项，不判）"
              % (i, lm, c128, lm - c128))
    m = sum(txt_icon) / len(txt_icon)
    chk(abs(m) <= tol, "[4] 文案↔图标（四块均值）",
        "逐块 Δ = %s ｜ 均值 %+.2f（逐块抖动来自首行字形）"
        % (", ".join("%+.1f" % v for v in txt_icon), m))
    # 数据层
    chk(bj["x"] == 15, "[5a] jump.x", "=%d（PSB 口径 15）" % bj["x"])
    chk(br["x"] == 141, "[5b] replay.x", "=%d（PSB 口径 141）" % br["x"])
    chk(bj["x"] + bj["w"] <= br["x"] and br["x"] + br["w"] < it["x"], "[5c] 两键互不重叠且不压文案区",
        "jump %d..%d ｜ replay %d..%d ｜ 文案左沿 %d" % (bj["x"], bj["x"] + bj["w"], br["x"], br["x"] + br["w"], it["x"]))
    chk(bj["y"] + bj["h"] <= lst["item_h"] and br["y"] + br["h"] <= lst["item_h"], "[5d] 两键在块内",
        "jump 底 %d ｜ replay 底 %d ｜ item_h %d" % (bj["y"] + bj["h"], br["y"] + br["h"], lst["item_h"]))
    # 实机层 x
    ry0 = lst["y"]
    jy = ry0 + bj["y"]
    base = [sum(lum(px[x, y]) for x in range(lst["x"] + 2, lst["x"] + 12)) / 10.0
            for y in range(jy, jy + bj["h"])]
    pcols = [x for x in range(lst["x"] + 2, lst["x"] + bj["x"] + bj["w"])
             if abs(sum(lum(px[x, y]) for y in range(jy, jy + bj["h"])) / float(bj["h"])
                    - sum(base) / len(base)) > 8.0]   # 阈值 8：行带自带 ~5/255 横向梯度，3 会误判
    # 胶囊的实绘左沿 = **浅色描边**（列均值的局部极小）。
    #   为什么不用「亮度跃升」判据：胶囊填充与行带亮度几乎相同（实测 x189..209 的列均值 228.9 vs
    #   行带 227.3），唯一可测的边界是它自己的描边（x188 列均值 222.19，比紧邻列低 3.5~4.2）。
    exp_j = lst["x"] + bj["x"] + JUMP_PAD
    seg = [sum(lum(px[x, y]) for y in range(jy, jy + bj["h"])) / float(bj["h"])
           for x in range(exp_j - 4, exp_j + 9)]
    lo = min(seg)
    edge_j = (exp_j - 4) + seg.index(lo)
    band_j = sum(seg[:2] + seg[-2:]) / 4.0
    chk(abs(edge_j - exp_j) <= 2 and (band_j - lo) >= 2.0, "[6a] 胶囊实绘左沿（描边极小）",
        "实测 x=%d（素材口径期望 %d = list.x %d + jump.x %d + 素材透明列 %d）｜"
        "描边列均值 %.2f 比紧邻行带 %.2f 低 %.2f（另：亮度跃升法给出首越阈列 x=%s，因填充与行带近同色而偏右）"
        % (edge_j, exp_j, lst["x"], bj["x"], JUMP_PAD, lo, band_j, band_j - lo,
           pcols[0] if pcols else "n/a"))
    rx0, ryy = lst["x"] + br["x"], ry0 + br["y"]
    rbase = [sum(lum(px[x, y]) for x in range(lst["x"] + 2, lst["x"] + 12)) / 10.0
             for y in range(ryy, ryy + br["h"])]
    rcols = [x for x in range(rx0 - 30, rx0 + br["w"])   # 起点取两键间空隙（rx0-30），避免扫到左侧 jump 胶囊
             if abs(sum(lum(px[x, y]) for y in range(ryy, ryy + br["h"])) / float(br["h"])
                    - sum(rbase) / len(rbase)) > 8.0]
    exp_r = rx0 + REPLAY_PAD
    chk(rcols and abs(rcols[0] - exp_r) <= 3, "[6b] 图标实绘左沿",
        "实测 x=%s（期望 %d = list.x %d + replay.x %d + 素材透明列 %d）"
        % (rcols[0] if rcols else "n/a", exp_r, lst["x"], br["x"], REPLAY_PAD))

    print()
    if fails:
        print("结果：FAIL（%d 项）：%s" % (len(fails), ", ".join(fails)))
        sys.exit(1)
    print("结果：全部 PASS（未决项 [7] 不计入）")
    sys.exit(0)


if __name__ == "__main__":
    main()

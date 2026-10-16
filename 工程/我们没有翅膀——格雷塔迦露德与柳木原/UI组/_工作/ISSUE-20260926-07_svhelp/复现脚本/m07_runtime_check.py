# -*- coding: utf-8 -*-
r"""m07 · 实机导图核算：krkr 巡演导出 PNG 里「说明条 / 编辑键条 / 烘焙页脚带」的墨迹行带
（`ISSUE-20260926-07`；幂等、带退出码）

判据：
  · 引擎绘字（`@palette.node_locked = #4A4A56`）⇒ 「暗且低饱和」：max(RGB) < 130 且 max−min < 40。
    该判据**只**拾取引擎绘的深灰字；烘焙页脚的中文是浅蓝白发光字（max(RGB) 高、带描边），
    不在该判据内 ⇒ 两条墨带自然分离，可直接量「说明条带 / 编辑键带」以及二者的间距。
  · 页脚带另有独立判据：逐像素相对该行中位数偏差 > 25（同 `m07_geom_check.py`）。

断言（硬失败）：
  ① 说明条墨带（~y847..892）**整体在**编辑键墨带（~y904..965）之上；
  ② 编辑键墨带底边 → 页脚带墨迹顶 的间距 ≥ 15px；
  ③ 两带之间的无墨行数 > 0（确有分离）。

用法：python m07_runtime_check.py [shot 目录]
"""
import sys, os
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

DEF = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\临时\ui_run\runtime\savedata"
SHOTS = [("shot_10_save.png", "23 存档", (847, 892), (904, 965)),
         ("shot_11_load.png", "24 读档", (847, 892), (904, 965))]
X0, X1 = 1030, 1800
FAILS = []


def bands(a, y0, y1):
    sub = a[y0:y1, X0:X1]
    dark = (sub.max(axis=2) < 130) & ((sub.max(axis=2) - sub.min(axis=2)) < 40)
    rows = dark.sum(axis=1)
    runs, cur = [], None
    for i, c in enumerate(rows):
        if c > 0:
            cur = [y0 + i, y0 + i] if cur is None else [cur[0], y0 + i]
        elif cur is not None:
            runs.append(tuple(cur)); cur = None
    if cur is not None:
        runs.append(tuple(cur))
    return runs, dark


def footer_top(a, xa=1200, xb=1740, ya=940, yb=1080):
    sub = a[ya:yb, xa:xb]
    dev = np.abs(sub - np.median(sub, axis=1, keepdims=True)).max(axis=2)
    cnt = (dev > 25).sum(axis=1)
    for i, c in enumerate(cnt):
        if c > 0:
            return ya + i, int(c)
    return None, 0


def main():
    d = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else DEF
    for fn, tag, (hb0, hb1), (eb0, eb1) in SHOTS:
        p = os.path.join(d, fn)
        a = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
        runs, dark = bands(a, 820, 1000)
        ft, ftc = footer_top(a)
        print("=" * 100)
        print("%s ｜ %s ｜ 尺寸 %s" % (tag, p, (a.shape[1], a.shape[0])))
        print("   暗色墨迹行带（x%d..%d，y820..1000）：%s" % (X0, X1, runs))
        for y0, y1 in runs:
            cols = np.where(dark[y0 - 820:y1 - 820 + 1].any(axis=0))[0]
            print("      y%d..%d（%d 行）  x%d..%d" % (y0, y1, y1 - y0 + 1, X0 + cols.min(), X0 + cols.max()))
        assert len(runs) == 2, "!! 期望恰好 2 条引擎字墨带（说明条 / 编辑键条），实测 %d 条" % len(runs)
        (sy0, sy1), (ey0, ey1) = runs
        assert hb0 <= sy0 and sy1 <= hb1, "!! 说明条墨带 y%d..%d 不在预期盒 %d..%d 内" % (sy0, sy1, hb0, hb1)
        assert eb0 <= ey0 and ey1 <= eb1, "!! 编辑键墨带 y%d..%d 不在预期盒 %d..%d 内" % (ey0, ey1, eb0, eb1)
        assert sy1 < ey0, "!! 说明条墨带未整体位于编辑键墨带之上（%d vs %d）" % (sy1, ey0)
        assert ey0 - sy1 - 1 > 0, "!! 两带之间无分离行"
        print("   ① 说明条墨带 y%d..%d **整体在** 编辑键墨带 y%d..%d 之上 ✓（中间 %d 行无引擎字）"
              % (sy0, sy1, ey0, ey1, ey0 - sy1 - 1))
        print("   ② 页脚带墨迹顶 = y%d（x1200..1740，偏离行中位数 >25 的像素 %d 个）⇒ 距编辑键墨带底 %dpx"
              % (ft, ftc, ft - ey1))
        assert ft - ey1 >= 15, "!! 编辑键墨带底 y%d 距页脚带 y%d 仅 %dpx < 15px" % (ey1, ft, ft - ey1)
        print("   ② 间距 ≥ 15px ✓（且引擎字判据下 y%d..y%d 全无暗色墨）" % (ey1 + 1, ft - 1))
    if FAILS:
        print("FAIL:", FAILS); return 1
    print("\nALL PASS ✓ —— 实机导图上「说明条 → 编辑键条 → 烘焙页脚带」三层自上而下、互不重叠")
    return 0


if __name__ == "__main__":
    sys.exit(main())

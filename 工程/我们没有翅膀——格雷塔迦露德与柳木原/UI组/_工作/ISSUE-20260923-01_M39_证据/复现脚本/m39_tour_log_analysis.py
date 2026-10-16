# -*- coding: utf-8 -*-
r"""M39 · 巡演日志分析：dialog 屏「实绘元素」记账 + 三项干净关键字 + 缺件/异常计数

用法：
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_tour_log_analysis.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LOG = ("E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run/runtime/savedata/"
       "krkr.console.log")


def main():
    if not os.path.exists(LOG):
        print("!! 找不到巡演日志：%s" % LOG)
        return 1
    txt = io.open(LOG, encoding="utf-16-le", errors="replace").read()
    io.open(os.path.join(os.path.dirname(HERE), "M39_巡演日志_krkr.console.log.txt"),
            "w", encoding="utf-8").write(txt)

    print("=" * 78)
    print("M39 巡演日志分析（引擎自己导出的日志，非窗口抓屏）")
    print("  日志：%s" % LOG)
    print("=" * 78)

    # ① [UI][TOUR] 每屏记账
    rows = re.findall(r"\[UI\]\[TOUR\]\s*(.+?)\s*$", txt, re.M)
    print("\n■ [1] [UI][TOUR] 逐屏记账（原始行）")
    for r in rows:
        print("   " + r)

    # ② dialog 屏的实绘元素数（本轮核心：6 → 7）
    print("\n■ [2] dialog 屏「实绘元素」")
    for r in rows:
        if "dialog" in r or "选择肢" in r or "choices" in r:
            m = re.search(r"实绘元素[=: ]*(\d+)", r)
            print("   %-60s → 实绘元素=%s" % (r, m.group(1) if m else "(无该字段)"))

    # ③ 三项干净关键字
    print("\n■ [3] 干净关键字（原始计数）")
    clean = True
    for key, want in [("An exception occured", 0), ("redraw EXCEPTION", 0),
                      ("[UI][MISS]", 0)]:
        n = txt.count(key)
        clean &= (n == want)
        print("   %-24s 出现 %d 次（期望 %d）%s" % (key, n, want, "✓" if n == want else "✗"))
    for key, want in [("截断文本", 0), ("未知 kind", 0), ("缩放元素", 0)]:
        n = txt.count(key)
        print("   %-24s 出现 %d 次（截图/日志口径；M8 基线 %d）" % (key, n, want))

    # ④ 载入素材 / 缺件
    for line in txt.splitlines():
        if "已载入" in line or "缺件" in line:
            print("\n■ [4] 素材载入：" + line.strip())

    # ⑤ PNG 导出计数
    sd = os.path.dirname(LOG)
    pngs = sorted(f for f in os.listdir(sd) if f.startswith("shot_") and f.endswith(".png"))
    print("\n■ [5] PNG 导出：%d 张" % len(pngs))
    for f in pngs:
        print("   " + f)

    print("\n%s" % ("RESULT=OK（三项干净关键字全 0）" if clean else "RESULT=NG（见上）"))
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())

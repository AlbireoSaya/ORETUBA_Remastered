# -*- coding: utf-8 -*-
r"""poll_tour.py —— 等一次 autotour 跑完（读 krkr.console.log 里的 `autotour done` 标记）

用法：python _工作\ISSUE-20260927-06_番外组名\poll_tour.py [超时秒] [标签]
★ 只读：不改任何数据；log 为 UTF-16LE。
"""
import io
import os
import sys
import time

# 工作树根 = 本文件所在目录上溯 5 级（番外组名 → ISSUE-* → _工作 → UI组 → <作品> → 工程 → 工作树）
WT = os.path.dirname(os.path.abspath(__file__))
for _ in range(5):
    WT = os.path.dirname(WT)
RUN = os.path.join(WT, "临时", "ui_run")
LOG = os.path.join(RUN, "runtime", "savedata", "krkr.console.log")

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 360
tag = sys.argv[2] if len(sys.argv) > 2 else "-"

t0 = time.time()
last = None
print("[poll %s] log = %s" % (tag, LOG))
while time.time() - t0 < timeout:
    if os.path.exists(LOG):
        try:
            with io.open(LOG, "r", encoding="utf-16", errors="ignore") as f:
                txt = f.read()
        except Exception as e:                                    # 文件正被引擎写
            txt = ""
            print("  (读失败，重试) %s" % e)
        if "autotour done" in txt:
            print("[poll %s] 命中 autotour done（用时 %.1fs，log %d 字节）"
                  % (tag, time.time() - t0, os.path.getsize(LOG)))
            keys = ("[UI][TOUR]", "quit (autotour done)", "缺件", "缩放", "截断",
                    "EXCEPTION", "异常", "FC", "flowchart", "组名")
            for line in txt.splitlines():
                if any(k in line for k in keys):
                    print("  | " + line.strip()[:400])
            sys.exit(0)
        last = os.path.getsize(LOG)
    time.sleep(8)
print("[poll %s] 超时 %ds 未命中（log 当前 %s 字节）" % (tag, timeout, last))
sys.exit(1)

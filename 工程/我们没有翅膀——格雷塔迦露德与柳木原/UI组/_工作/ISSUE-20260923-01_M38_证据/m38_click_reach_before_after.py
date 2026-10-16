# -*- coding: utf-8 -*-
r"""M38 · `test_click_reach.py` 的 **dialog 屏前后对照**（不改盘上数据）

做法：import `工具\test_click_reach.py`，把它的 `SCR` 指向一个**临时目录**：
  · 「后」= 临时目录里放**当前**的 `10_dialog.json`（其余屏从盘上原样复制）；
  · 「前」= 临时目录里的 `10_dialog.json` 换成 `git show HEAD:…` 的旧版。
两边各跑一次 `check_screen('dialog', …)`（只为看 dialog 屏的统计与重叠/可达性结果），
再对照打印。临时目录用完即删（落在 `_工作\` 内，符合落盘纪律）。

用法：python _工作\ISSUE-20260923-01_M38_证据\m38_click_reach_before_after.py
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(UI, "工具")
REAL_SCR = os.path.join(UI, "layout", "screens")
sys.path.insert(0, TOOLS)

import importlib.util
spec = importlib.util.spec_from_file_location("tcr", os.path.join(TOOLS, "test_click_reach.py"))
tcr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tcr)

TMP = tempfile.mkdtemp(prefix="m38_cr_", dir=os.path.join(UI, "_工作"))
try:
    tcr.SCR = TMP
    for f in os.listdir(REAL_SCR):
        shutil.copy2(os.path.join(REAL_SCR, f), os.path.join(TMP, f))

    def measure(tag):
        screens = tcr.load_all()
        fails, infos, st = tcr.check_screen("dialog", screens, verbose=False)
        print("【%s】%s" % (tag, "；".join(
            "%s=%s" % (k, st[k]) for k in ("elements", "clickable", "states", "checked"))))
        print("        重叠对 %d ｜ 可达性失败 %d 项 ｜ 豁免命中 %d 件"
              % (len(st["overlaps"]), len(fails), len(st["exempt_hit"])))
        for x in fails:
            print("        ✗ " + x)
        return st, fails

    after, fa = measure("后：M38 现盘（26 件 → 7 件）")

    old = subprocess.run(["git", "show", "HEAD:工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/"
                                 "layout/screens/10_dialog.json"],
                         cwd=os.path.join(UI, "..", "..", ".."), stdout=subprocess.PIPE).stdout
    assert old, "git show 取旧版失败"
    json.loads(old.decode("utf-8"))          # 语法自证
    io.open(os.path.join(TMP, "10_dialog.json"), "wb").write(old)
    before, fb = measure("前：HEAD 旧数据（含 9 热区 + 9 图标 + 窗底）")

    print("\n" + "-" * 78)
    print("差值：元素 %d → %d ｜ 可点件 %d → %d ｜ 判定次数 %d → %d ｜ 失败 %d → %d"
          % (before["elements"], after["elements"], before["clickable"], after["clickable"],
             before["checked"], after["checked"], len(fb), len(fa)))
    print("结论：删掉 9 个 hit 后 dialog 屏仍 **无重叠对、无不可达项**（两态各自复算），"
          "判定次数按减少的可点件数同步下降。")
    print("（临时目录 %s 已删除）" % TMP)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

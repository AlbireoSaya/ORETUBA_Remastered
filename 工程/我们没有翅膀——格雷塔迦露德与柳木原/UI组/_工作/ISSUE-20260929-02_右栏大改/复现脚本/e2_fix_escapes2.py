# -*- coding: utf-8 -*-
"""e2_fix_escapes2.py —— 一次性补丁 2：把 `gen_flow_layout.py` 的 PRESET_TABLE 第 11 批段里
**单反斜杠路径**改成双反斜杠（Python 源码合法写法）。反斜杠用 chr(92) 构造，免多层转义歧义。
"""
import io
import os

BS = chr(92)
_HERE = os.path.dirname(os.path.abspath(__file__))                 # …\复现脚本
_UI = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))      # …\UI组
P = os.path.join(_UI, "工具", "gen_flow_layout.py")

s = io.open(P, encoding="utf-8").read()
pairs = [
    ("`_工作" + BS + "ISSUE-20260928-02_第2步" + BS + "复现脚本" + BS + "m06_delivered_sample_ledger.py`",
     "`_工作" + BS * 2 + "ISSUE-20260928-02_第2步" + BS * 2 + "复现脚本" + BS * 2
     + "m06_delivered_sample_ledger.py`"),
]
for old, new in pairs:
    if old in s:
        s = s.replace(old, new)
        print("fixed: %r" % old)
    else:
        print("skip (not found): %r" % old)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("written", P)

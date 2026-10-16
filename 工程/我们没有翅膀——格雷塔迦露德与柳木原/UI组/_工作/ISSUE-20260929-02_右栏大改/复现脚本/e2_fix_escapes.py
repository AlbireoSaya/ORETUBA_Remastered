# -*- coding: utf-8 -*-
"""e2_fix_escapes.py —— 一次性补丁：把 `e2_apply_pane_rework.py` 里 PAUSE_SOURCE 的三处
**单反斜杠路径**改成双反斜杠（Python 源码里的合法写法），避免 SyntaxWarning / 未来的 SyntaxError。

反斜杠一律用 chr(92) 构造，避免多层转义歧义。
"""
import io
import os

BS = chr(92)
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2_apply_pane_rework.py")

s = io.open(P, encoding="utf-8").read()
pairs = [
    ("_工作" + BS + "ISSUE", "_工作" + BS * 2 + "ISSUE"),
    ("右栏大改" + BS + "暂停键", "右栏大改" + BS * 2 + "暂停键"),
    ("暂停键_AI版" + BS + "`", "暂停键_AI版" + BS * 2 + "`"),
]
for old, new in pairs:
    if old in s:
        s = s.replace(old, new)
        print("fixed: %r -> %r" % (old, new))
    else:
        print("skip (not found): %r" % old)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("written", P)

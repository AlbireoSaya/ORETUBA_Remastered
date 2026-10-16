# -*- coding: utf-8 -*-
r"""M37 · **只重跑 `build_quickbar()`**（不改动其它屏）

■ 为什么只跑一个 build 函数
  交接 §三.20：屏 JSON 由生成器产出 ⇒ 改 JSON 必须同步生成器；而生成器的 `__main__`
  会**把所有屏**重跑一遍（其它屏的盘上改动可能未回写生成器 ⇒ 被静默抹掉或被守门拦下）。
  故这里用 `importlib` 只 import 并调用 `build_quickbar()`。

■ 为什么要 `M34_FORCE=1`
  M37 是「形态重构」——`quick.tgl/btn/tips/hit_toggle` **有意退场**，
  `write()` 的防静默清空守门（`_would_lose`）会把这视为「删元素」并拒绝落盘。
  本轮是**有意的整体重建**，故显式放行（`--force` 等价物），
  并在 `_工作\M37_旧素材归档\` 保留旧 JSON 快照与旧素材。
  跑完必须由 `工具\test_gen_sync.py` 自证「生成器能完整复现磁盘」。

■ 用法
    python _工作\M37_重跑quickbar屏.py && cd 工具 && python gen_layout.py
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
TOOLS = os.path.join(UI, "工具")
sys.path.insert(0, TOOLS)

os.environ["M34_FORCE"] = "1"          # 见上方说明：本轮是**有意的整体重建**
sys.argv = [a for a in sys.argv if a != "--force"]

spec = importlib.util.spec_from_file_location(
    "m34_build_screens", os.path.join(TOOLS, "m34_build_screens.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

m.build_quickbar()

p = os.path.join(UI, "layout", "screens", "35_quickbar.json")
import json
d = json.load(io.open(p, encoding="utf-8"))
print("\n[OK] 35_quickbar.json 元素 %d 件" % len(d["elements"]))
print("     flags_default=%s" % json.dumps(d["flags_default"], ensure_ascii=False))
print("     reveal=%s" % json.dumps(d["reveal"], ensure_ascii=False))

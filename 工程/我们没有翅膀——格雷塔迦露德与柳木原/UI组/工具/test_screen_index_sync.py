# -*- coding: utf-8 -*-
r"""test_screen_index_sync.py —— `复刻\screen_index.js`（**编辑器用**屏清单）与 `layout\screens\_index.json` 一致性闸门

★ 为什么要有它（`ISSUE-20260928-07` 一审抓出的 Critical 的**根因修复**）：
  删屏需要**两个**生成器都重跑 —— `工具\gen_layout.py`（三处产物）与 `工具\emit_asset_index.py`
  （`复刻\screen_index.js` + `复刻\asset_index.js`）。前者有 `verify_ui [3]` 等闸门看着，
  **后者此前没有任何闸门** ⇒ 删 `fragment` 屏那轮重跑了它（没出事），删 `ending` 屏这轮**漏跑**了：
  `screen_index.js` 仍列 18 屏（含 `ending`）⇒ `复刻\editor.html` 的屏选择器为空并抛
  `Uncaught TypeError: Cannot read properties of undefined (reading 'title_cn')`
  （`editor_ui.js::buildScreenSel` 里 `L.screens[sid]` 为 undefined）。
  而 `run_all` 34 步与两套 HTML 自检**都覆盖不到**（自检宿主页不加载 `screen_index.js`）。

判据（纯数据层，不起浏览器）：
  `screen_index.js` 里每条 `id` **必须**在 `layout\screens\_index.json` 里登记，且 `file` 字段与登记一致；
  反向：`_index.json` 的每屏**也必须**出现在 `screen_index.js` 里（双向，任一侧漏跑即 FAIL）。
  另报「该文件的 mtime 是否早于 `_index.json`」作**提示**（不判失败：两者可在同一秒内）。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python 工具\test_screen_index_sync.py
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

UI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))         # …\UI组
IDX = os.path.join(UI, "layout", "screens", "_index.json")
SI = os.path.join(UI, "复刻", "screen_index.js")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 78)
    print("test_screen_index_sync · 编辑器屏清单 ↔ _index.json 一致性")
    print("=" * 78)
    fails = []

    idx = json.load(io.open(IDX, encoding="utf-8"))
    want = {s["id"]: s["file"] for s in idx["screens"]}

    raw = io.open(SI, encoding="utf-8").read()
    body = raw[raw.find("["):] if "[" in raw else raw
    try:
        got_list = json.loads(body[body.find("["):body.rfind("]") + 1])
    except Exception as e:                                    # 退回逐条正则扫描
        print("  ⚠ `screen_index.js` 不是纯 JSON 数组（%s）⇒ 退回逐条扫描" % e)
        got_list = [{"id": a, "file": b} for a, b in
                    re.findall(r'"id":\s*"([^"]+)"\s*,\s*"file":\s*"([^"]+)"', raw)]
    got = {e["id"]: e.get("file") for e in got_list}

    print("  `_index.json`：%d 屏 ｜ `screen_index.js`：%d 屏" % (len(want), len(got)))

    only_si = sorted(set(got) - set(want))
    only_idx = sorted(set(want) - set(got))
    if only_si:
        fails.append("`screen_index.js` 有屏而 `_index.json` 没有：%s ⇒ **漏跑 `工具\\emit_asset_index.py`**" % only_si)
    if only_idx:
        fails.append("`_index.json` 有屏而 `screen_index.js` 没有：%s ⇒ **漏跑 `工具\\emit_asset_index.py`**" % only_idx)
    for sid in sorted(set(got) & set(want)):
        if got[sid] != want[sid]:
            fails.append("屏 `%s` 的 file 不一致：screen_index=%s ／ _index=%s" % (sid, got[sid], want[sid]))

    m_i, m_s = os.path.getmtime(IDX), os.path.getmtime(SI)
    print("  mtime：_index=%.0f ／ screen_index=%.0f %s"
          % (m_i, m_s, "（screen_index 更旧 —— 若刚改过 _index 请重跑生成器）" if m_s < m_i - 2 else ""))

    print("-" * 78)
    if fails:
        for f in fails:
            print("  ✗ %s" % f)
        print("结果：**不通过**（退出码 1）—— %d 处（修法：`python 工具\\emit_asset_index.py`）" % len(fails))
        return 1
    print("结果：**通过**（退出码 0）—— 两个清单双向一致（%d 屏），编辑器不会因缺屏抛 TypeError" % len(want))
    return 0


if __name__ == "__main__":
    sys.exit(main())

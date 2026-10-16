# -*- coding: utf-8 -*-
r"""
selftest_picjp_negative.py — 「图片化日文」处置表的**负向自证**（ISSUE-20260930-07）

用途：证明 `build_picjp_disposition.py` 的闸门**真能失败**（不是恒真的装饰）。
一审 N1 曾指出 **G8 是死闸门**——检查点写在 G8 追加 `errs` 之前，故永不触发；
本脚本就是那条缺陷的**回归测试**：把素材账加载器打成空 ⇒ `bytes` 全落空 ⇒ `b_drop == 0` ⇒ 必须非零退出。

自证两条（都能真失败）：
  A 负向：monkeypatch `_ledger_by()` 返回 `{}` → `build()` 必须 `SystemExit(非 0)`，且 stderr/stdout 出现 `G8`
  B 正向对照：原始加载器下 `build()` 必须正常返回（629 行 / 保留 132 行）

用法：
  python -X utf8 selftest_picjp_negative.py     # 退出码 0 = 两条自证都通过
"""
from __future__ import annotations

import importlib.util
import io
import os
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "build_picjp_disposition.py")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    # A 负向自证
    m = _load("bpd_negative")
    m._ledger_by = lambda: {}
    buf = io.StringIO()
    code = None
    try:
        with redirect_stdout(buf):
            m.build()
    except SystemExit as e:
        code = e.code
    out = buf.getvalue()
    if code in (0, None):
        print("[A 失败] 空素材账下 build() 正常退出（code=%r）⇒ G8 仍未生效（死闸门）" % (code,))
        return 1
    if "G8" not in out:
        print("[A 失败] 虽非零退出，但输出里没有 G8 字样 ⇒ 可能是别的闸门先失败（未证到 G8）")
        print("---- 输出 ----\n%s" % out[-800:])
        return 1
    print("[A PASS] 空素材账 ⇒ G8 真失败（非零退出，输出含 G8）")

    # B 正向对照
    m2 = _load("bpd_positive")
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        rows, keep, _h, _n = m2.build()
    if len(rows) != 629 or len(keep) != 132:
        print("[B 失败] 正向对照返回 %d 行 / 保留 %d 行（应 629 / 132）" % (len(rows), len(keep)))
        return 1
    print("[B PASS] 正向对照：629 行 / 保留 132 行")
    print("\n自证结论：两条均通过（负向必须失败、正向必须通过）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

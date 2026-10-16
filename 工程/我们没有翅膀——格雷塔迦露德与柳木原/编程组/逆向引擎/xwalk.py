#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xwalk.py — 用「引擎 VM 操作数字节表」对真实 SOB 代码区做线性走查验证。

引擎 VM = sub at VA 0x433650，分派表 VA 0x433B54（47 个 op：0x00..0x2E）。
下表 = 每个 op 消耗的**操作数字数**（不含 op 自身），由各 handler 反汇编读出：
  0x00:0 0x01:0 0x02:1 0x03:1 0x04:1 0x05:3 0x06:1 0x08:1 0x09:1 0x0A:1 0x0B:1
  0x0C:1 0x0D:3 0x0E:3 0x0F:3 0x10:3 0x11:3 0x12:3 0x13:3 0x14:3 0x15:3 0x16:2
  0x17:2 0x18:3 0x19:3 0x1A:1 0x1B:1 0x1C:1 0x1D:1 0x1E:2 0x1F:2 0x20:2 0x21:2
  0x22:2 0x23:2 0x24:2 0x25:2 0x26:2 0x27:2 0x28:2 0x29:3 0x2A:3 0x2B:3 0x2C:3
  0x2D:3 0x2E:3    （0x07 = 变长 switch，走查时遇之报 unknown）

验证口径：从 cell[0] 起按表推进；**每一个 op 位置的字必须 <= 0x2E**。
若表正确，整段代码应 0 违规地走到末尾（或遇 0x00/未知）。
同时用 decode_sob0.BASE（数据侧反推的长度表）做对照走查，比违规数。

用法：
  python -X utf8 xwalk.py --file <sob>
  python -X utf8 xwalk.py --all [--limit N]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402

VM_LEN = {0x00: 1, 0x01: 1, 0x02: 2, 0x03: 2, 0x04: 2, 0x05: 4, 0x06: 2,
          0x07: 0, 0x08: 2, 0x09: 2, 0x0A: 2, 0x0B: 2, 0x0C: 2, 0x0D: 4,
          0x0E: 4, 0x0F: 4, 0x10: 4, 0x11: 4, 0x12: 4, 0x13: 4, 0x14: 4,
          0x15: 4, 0x16: 3, 0x17: 3, 0x18: 4, 0x19: 4, 0x1A: 2, 0x1B: 2,
          0x1C: 2, 0x1D: 2, 0x1E: 3, 0x1F: 3, 0x20: 3, 0x21: 3, 0x22: 3,
          0x23: 3, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 4,
          0x2A: 4, 0x2B: 4, 0x2C: 4, 0x2D: 4, 0x2E: 4}

# decode_sob0.py（v5 口径）的数据侧反推长度表 —— **本件把它钉在脚本里**，
# 以免 decode_sob0.py 被并行任务改动后本对照不可复现。
# payload 数：{00:2, 01:0, 03:1, 04:1, 05:3, 06:1, 08:3, 0C:1, 0D:0, 13:0, 14:0,
#              17:2, 1E:2, 1F:2, 20:2, 28:2, 2C:3, 2E:0}
BASE_PAYLOAD_V5 = {0x00: 2, 0x01: 0, 0x03: 1, 0x04: 1, 0x05: 3, 0x06: 1, 0x08: 3,
                   0x0C: 1, 0x0D: 0, 0x13: 0, 0x14: 0, 0x17: 2, 0x1E: 2, 0x1F: 2,
                   0x20: 2, 0x28: 2, 0x2C: 3, 0x2E: 0}
BASE_LEN = {t: v + 1 for t, v in BASE_PAYLOAD_V5.items()}


def walk(cells, table, default=1):
    i, bad, unk, n = 0, 0, 0, 0
    bad_at = []
    while i < len(cells):
        t = cells[i]
        if t > 0x2E:
            bad += 1
            if len(bad_at) < 6:
                bad_at.append((i, t))
            # 强行前进 1 词以便统计（口径写清）
            i += 1
            continue
        if t == 0x07:
            unk += 1
            break
        L = table.get(t, default)
        i += L
        n += 1
    return dict(n=n, bad=bad, bad_at=bad_at, unknown07=unk,
                end_ok=(i == len(cells)), end_i=i, total=len(cells))


def main():
    a = sys.argv[1:]
    files = []
    if "--file" in a:
        files = [a[a.index("--file") + 1]]
    elif "--all" in a:
        root = a[a.index("--all") + 1]
        ext = a[a.index("--ext") + 1] if "--ext" in a else ".sob"
        for fn in sorted(os.listdir(root)):
            if fn.lower().endswith(ext):
                files.append(os.path.join(root, fn))
    tot_vm = dict(bad=0, unk=0, files=0, ok=0)
    tot_base = dict(bad=0, unk=0)
    for p in files:
        try:
            sob = Sob0(p)
        except Exception:
            continue
        rvm = walk(sob.cells, VM_LEN)
        rb = walk(sob.cells, BASE_LEN)
        tot_vm["files"] += 1
        tot_vm["bad"] += rvm["bad"]
        tot_vm["unk"] += rvm["unknown07"]
        tot_vm["ok"] += 1 if rvm["end_ok"] else 0
        tot_base["bad"] += rb["bad"]
        tot_base["unk"] += rb["unknown07"]
        if "--file" in a:
            print("%s cells=%d" % (os.path.basename(p), len(sob.cells)))
            print("  VM 表  : items=%d bad(opcode>0x2E)=%d unk07=%d end_ok=%s end_i=%d/%d"
                  % (rvm["n"], rvm["bad"], rvm["unknown07"], rvm["end_ok"],
                     rvm["end_i"], rvm["total"]))
            if rvm["bad_at"]:
                print("    bad@=%s" % rvm["bad_at"])
            print("  BASE 表: items=%d bad=%d unk07=%d end_ok=%s end_i=%d/%d"
                  % (rb["n"], rb["bad"], rb["unknown07"], rb["end_ok"],
                     rb["end_i"], rb["total"]))
            if rb["bad_at"]:
                print("    bad@=%s" % rb["bad_at"])
    if files:
        print("== 汇总 files=%d ==" % tot_vm["files"])
        print("  VM 表  : bad=%d unk07=%d 完整走到末尾的文件=%d/%d"
              % (tot_vm["bad"], tot_vm["unk"], tot_vm["ok"], tot_vm["files"]))
        print("  BASE 表: bad=%d unk07=%d" % (tot_base["bad"], tot_base["unk"]))


if __name__ == "__main__":
    main()

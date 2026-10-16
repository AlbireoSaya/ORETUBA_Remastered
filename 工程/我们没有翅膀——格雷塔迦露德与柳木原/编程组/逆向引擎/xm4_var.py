#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xm4_var.py — user_var.sob（SOB1）逐字段解出 + maps[0] 编号空间核验（ISSUE-20261008-04 M4）。

装载器（ORE_TUBA.EXE `sub_424460`，VA 0x424630..0x4247E7，逐字）：
  magic 'SOB1' | u32 payload_len(=0x1918) | payload[payload_len] |
  u32 count(=916) | count × 10B 记录 [u8 flagA][u8 flagB][u32 payload_off][u32 type] |
  尾部若干 u32

装载器循环（0x4246E3..0x424781）：读 2 标志字节 + 4B off + 4B type；runtim 记录 12B，推入 3 个向量
（[mgr+0x54]/+0x78/+0x9c 三份，对应 payload 3 副本 [mgr+0x74]/+0x98/+0xBC）。
flagA==1 → 该变量值分散在 3 副本（`0x4246FB..0x424763` 建 3 指针）；flagA!=1 → 只取副本 #1（0x424765）。

用法：
  python -X utf8 xm4_var.py --file "<...>/user_var.sob"
  python -X utf8 xm4_var.py --maps0 "<SCRIPT>"     # 全库 maps[0] 值域/键数/与 916 的关系
"""
import os
import struct
import sys
import collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402


def parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"SOB1", d[:4]
    plen = struct.unpack_from("<I", d, 4)[0]
    payload = d[8:8 + plen]
    p = 8 + plen
    cnt = struct.unpack_from("<I", d, p)[0]
    p += 4
    recs = []
    for _ in range(cnt):
        fa, fb = d[p], d[p + 1]
        off, typ = struct.unpack_from("<II", d, p + 2)
        recs.append((fa, fb, off, typ))
        p += 10
    tail = d[p:]
    return d, plen, payload, cnt, recs, tail, p


def read_payload_str(payload, off):
    e = payload.find(b"\x00", off)
    return payload[off:e]


def main():
    a = sys.argv[1:]
    if "--maps0" in a:
        root = a[a.index("--maps0") + 1]
        vals = collections.Counter()
        keys = 0
        mn, mx = 1 << 30, -1
        per_file = []
        for fn in sorted(os.listdir(root)):
            if not fn.lower().endswith(".sob"):
                continue
            try:
                sob = Sob0(os.path.join(root, fn))
            except Exception:
                continue
            m0 = sob.maps[0]
            keys += len(m0)
            for v in m0.values():
                vals[v] += 1
                mn = min(mn, v)
                mx = max(mx, v)
            if m0:
                per_file.append((os.path.basename(fn), len(m0),
                                 min(m0.values()), max(m0.values())))
        print("== maps[0] 全库（%d 文件）==" % len(per_file))
        print("  键总数=%d  value 值域=[0x%X,%d]  不同 value 数=%d" % (keys, mn, mx, len(vals)))
        print("  前 20 个 value 及其出现次数: %s" % vals.most_common(20))
        print("  value 上界 = %d（SOB1 记录数 916 → 下标 0..915）" % mx)
        print("  是否有 value >= 916: %s" % [v for v in vals if v >= 916][:10])
        print("  逐文件（有 maps[0] 者，前 15）:")
        for r in per_file[:15]:
            print("     %-22s keys=%4d  val=[%d,%d]" % r)
        return

    path = a[a.index("--file") + 1] if "--file" in a else \
        r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\user_var.sob"
    d, plen, payload, cnt, recs, tail, pend = parse(path)
    print("== user_var.sob 逐字段 ==")
    print("  文件 %d B | payload_len=%d(0x%X) | count=%d | 记录区 [0x%X,0x%X) | 尾部 %d B"
          % (len(d), plen, plen, cnt, 0x1924, pend, len(tail)))
    fa = collections.Counter(r[0] for r in recs)
    fb = collections.Counter(r[1] for r in recs)
    ty = collections.Counter(r[3] for r in recs)
    print("  flagA 分布: %s" % dict(fa))
    print("  flagB 分布: %s" % dict(fb))
    print("  type   分布: %s" % {hex(k): v for k, v in ty.most_common()})
    offs = [r[2] for r in recs]
    print("  payload_off 值域=[0x%X,0x%X]  min=%d max=%d  唯一数=%d"
          % (min(offs), max(offs), min(offs), max(offs), len(set(offs))))
    print("  单调非降: %s" % all(offs[i] <= offs[i + 1] for i in range(len(offs) - 1)))
    # 头 12 条 + 尾 12 条
    print("  头 12 条: " + " ".join("#%d[A=%d B=%d off=0x%X ty=%d]" % (i, *r)
                                    for i, r in enumerate(recs[:12])))
    print("  尾 12 条: " + " ".join("#%d[A=%d B=%d off=0x%X ty=%d]" % (i, *r)
                                    for i, r in enumerate(recs[-12:], len(recs) - 12)))
    # 尾部结构
    print("  尾部 %d B hex: %s" % (len(tail), tail[:64].hex(" ")))
    if len(tail) >= 4:
        n2 = struct.unpack_from("<I", tail, 0)[0]
        print("  尾部首 u32 = %d（= pairs?）；tail_len=%d；4+n2*8=%d（余 %d B）"
              % (n2, len(tail), 4 + n2 * 8, len(tail) - (4 + n2 * 8)))
        if 4 + n2 * 8 <= len(tail):
            print("    尾部 = u32 %d + %d×(u32,u32) 对 (+%d B 尾零)"
                  % (n2, n2, len(tail) - 4 - n2 * 8))
            for i in range(n2):
                x, y = struct.unpack_from("<II", tail, 4 + i * 8)
                sx = read_payload_str(payload, x) if x < plen else b""
                sy = read_payload_str(payload, y) if y < plen else b""
                print("      pair[%2d] = (0x%X, 0x%X)  p[x]=%r  p[y]=%r"
                      % (i, x, y, sx[:40], sy[:40]))
        # 顺带：payload 内可读串全表
        import re
        print("  payload 内可读串（≥3 连续可打印）:")
        for m in re.finditer(rb"[ -~]{3,}", payload):
            print("     0x%04X  %r" % (m.start(), m.group()[:50]))


if __name__ == "__main__":
    main()

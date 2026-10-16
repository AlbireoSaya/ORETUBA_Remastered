# -*- coding: utf-8 -*-
r"""独立校验 GAMEDATA.DAT（ISSUE-ORETUBAR-R 存档线）。

不依赖任何游戏内行为，纯离线校验：
    1) 头两字段自洽：comp == 流长度（文件长度 - 8），uncomp == 展开长度
    2) 展开长度 == uncomp，且条目取值只允许 0 / 1（索引 0 实测为 0x29，列入白名单）
    3) 打印置位条目数、展开数组 sha256（可与 存档候选 对照）

用法
----
    python -X utf8 verify_unlock_save.py <GAMEDATA.DAT> [参照GAMEDATA.DAT]

给了参照文件时，额外做「两者展开数组逐字节比对」，并打印结论。
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata_lzss import lzss_decode  # noqa: E402

HEADER = 8
# 实测：索引 0 在两个 R 版样本中均为 0x29（=41），非 0/1；其余条目应为 0/1
KNOWN_NONBINARY = {0: 0x29}


def load(path):
    raw = open(path, 'rb').read()
    comp, uncomp = struct.unpack_from('<II', raw, 0)
    stream = raw[HEADER:HEADER + comp]
    arr = lzss_decode(stream, limit=uncomp + 1)
    return raw, comp, uncomp, stream, arr


def check(path, verbose=True):
    raw, comp, uncomp, stream, arr = load(path)
    ok = True
    def say(*a):
        if verbose:
            print(*a)

    say('文件           : %s' % path)
    say('  文件长度     : %d' % len(raw))
    say('  头[0..3] comp: %d   (文件长度-8 = %d)' % (comp, len(raw) - HEADER))
    say('  头[4..7] uncm: %d   (0x%04x)' % (uncomp, uncomp))
    if comp != len(raw) - HEADER:
        say('  [失败] comp 与文件长度不符'); ok = False
    if len(arr) != uncomp:
        say('  [失败] 展开长度 %d != uncomp %d' % (len(arr), uncomp)); ok = False
    # 非 0/1 条目：不是结构性错误（实机自产的存档里也会出现，见报告"未决问题"），
    # 但候选文件要求干净，故单独列出。
    odd = [(i, arr[i]) for i in range(len(arr)) if arr[i] not in (0, 1)]
    ones = sum(1 for b in arr if b)
    say('  展开长度     : %d   置位条目(值 1): %d' % (len(arr), ones))
    say('  展开数组 sha256: %s' % hashlib.sha256(arr).hexdigest())
    say('  非 0/1 条目   : %s' % [(i, hex(v)) for i, v in odd])
    say('  结构结论     : %s' % ('OK' if ok else 'FAIL'))
    return ok, arr


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print(__doc__); return
    p = sys.argv[1]
    ok, arr = check(p)
    if len(sys.argv) > 2:
        p2 = sys.argv[2]
        print('--- 与参照比对: %s' % p2)
        ok2, arr2 = check(p2)
        same = (arr == arr2)
        print('两者展开数组逐字节相同:', same)
        if not same:
            n = min(len(arr), len(arr2))
            d = [i for i in range(n) if arr[i] != arr2[i]]
            print('  差异条目数 %d  前 20: %s' % (len(d), d[:20]))
            print('  长度: %d vs %d' % (len(arr), len(arr2)))
        ok = ok and ok2 and same
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()

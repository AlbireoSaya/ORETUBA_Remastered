# -*- coding: utf-8 -*-
r"""GAMEDATA.DAT 全样本分析（ISSUE-ORETUBAR-R 存档线）：

一次性复现本模块推导时用到的全部证据：
    1) 头字段（comp/uncomp）与流起点（R 版 8 / 原版 18）
    2) 解码长度、置位条目数、非 0/1 条目（含来源追踪：字面量 or 回溯）
    3) "5 字节槽位网格"（i ≡ 1 mod 5）的填充统计
    4) 用户现档 vs 全解锁候选 的差异条目清单（前 N 个）
    5) 原版 A/B 的集合关系（旁证）

用法： python -X utf8 analyze_gamedata.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata_lzss import lzss_decode, lzss_decode_traced  # noqa: E402

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')

SAMPLES = [
    ('R-新档(线上)', os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R SaveData', 'GAMEDATA.DAT'), 8),
    ('R-新档(原始备份)', os.path.join(PROJ, '存档备份', '用户原始存档', 'GAMEDATA.DAT'), 8),
    ('R-全解锁(本仓库自产)', os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT'), 8),
    ('R-全解锁(外部原件)', os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA_备选-外部原件sagaoz.dat'), 8),
    ('原版-玩家解锁态', os.path.join(PROJ, '存档候选', '候选A_原版玩家解锁态.dat'), 18),
    ('原版-全CG存档', os.path.join(PROJ, '存档候选', '候选B_原版全CG存档.dat'), 18),
]


def load(path, hdr):
    import struct
    raw = open(path, 'rb').read()
    comp, uncomp = struct.unpack_from('<II', raw, 0)
    stream = raw[hdr:hdr + comp]
    return raw, comp, uncomp, stream


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    arrs = {}
    print('=== 1/2) 头字段 / 解码统计 ===')
    for name, path, hdr in SAMPLES:
        if not os.path.isfile(path):
            print('%-22s [缺文件] %s' % (name, path)); continue
        raw, comp, uncomp, stream = load(path, hdr)
        dec, src, used = lzss_decode_traced(stream, limit=uncomp + 1)
        arrs[name] = dec
        ones = sum(1 for b in dec if b)
        odd = [(i, dec[i], src[i][0]) for i in range(len(dec)) if dec[i] not in (0, 1)]
        print('%-22s file=%-4d hdr=%-2d comp=%-4d uncomp=%-4d 解出=%-4d 置位=%-4d 非0/1=%s'
              % (name, len(raw), hdr, comp, uncomp, len(dec), ones, odd[:6]))
        # 流起点正确性：原版用 18、R 用 8
    print()
    print('=== 3) 5 字节槽位网格统计（i ≡ 1 mod 5） ===')
    for name in ('R-新档(线上)', 'R-全解锁(本仓库自产)', '原版-玩家解锁态', '原版-全CG存档'):
        dec = arrs.get(name)
        if not dec:
            continue
        # 找槽位起点：置位最密集的 ≡1 mod 5 区间
        for lo in (1, 61, 331):
            slots = [i for i in range(lo, len(dec)) if i % 5 == 1]
            filled = sum(1 for i in slots if dec[i])
            if filled > 200:
                print('%-22s 起点>=%-4d 槽位=%-4d 已置位=%-4d 未置位=%-4d'
                      % (name, lo, len(slots), filled, len(slots) - filled))
    print()
    print('=== 4) 用户现档 vs 全解锁候选 ===')
    a = arrs.get('R-新档(线上)'); b = arrs.get('R-全解锁(本仓库自产)')
    if a and b:
        d = [i for i in range(len(b)) if a[i] != b[i]]
        print('差异条目数 = %d（0 -> 1 的解锁增量）; 前 16: %s' % (len(d), d[:16]))
        print('相同条目数 = %d' % (len(b) - len(d)))
    print()
    print('=== 5) 原版旁证 ===')
    A = arrs.get('原版-玩家解锁态'); B = arrs.get('原版-全CG存档')
    if A and B:
        sa = set(i for i, v in enumerate(A) if v); sb = set(i for i, v in enumerate(B) if v)
        print('原版A 置位=%d 原版B 置位=%d  A⊆B=%s  A-B=%s  |B-A|=%d'
              % (len(sa), len(sb), sa <= sb, sorted(sa - sb)[:8], len(sb - sa)))


if __name__ == '__main__':
    main()

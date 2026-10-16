# -*- coding: utf-8 -*-
r"""GAMEDATA.DAT 结构分析与候选生成（ISSUE-ORETUBAR-R 全解锁存档线）

实测三份样本：
    原版-玩家解锁态  488B  头 d6 01 00 00 | 19 0f 00 00 | 00 00 00 00 00 00 00 01 ...
    原版-全CG存档    485B  头 d3 01 00 00 | 19 0f 00 00 | 00 00 00 00 00 00 00 01 ...
    R版-新档         487B  头 df 01 00 00 | 46 0f 00 00 | 05 29 ea f1 01 f1 ff 03 ...

头 8 字节 = [u32 payload_len][u32 固定值]。原版两份的第二个字段同值 0x0f19，
R 版为 0x0f46 —— 疑为「存档/解锁项目总数」之类随版本变化的常量。
负载区形如 00 01 XX YY 00 01 ZZ WW 04 0a ...，其后为 0fXX 步进位图。
"""
import os, sys, struct, json

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SAMPLES = {
    '原版-玩家解锁态': r'D:\Gal\[Navel]我们没有翅膀\我们没有翅膀 SaveData\GAMEDATA.DAT',
    '原版-全CG存档': os.path.join(PROJ, '参照', '原版全CG存档', 'oretsuba', 'GAMEDATA.DAT'),
    'R版-新档': os.path.join(PROJ, '壌偨偪偵梼偼側偄俼 SaveData', 'GAMEDATA.DAT'),
}


def parse(path):
    d = open(path, 'rb').read()
    plen, magic = struct.unpack_from('<II', d, 0)
    return {
        'size': len(d),
        'payload_len': plen,
        'field2': magic,
        'payload': d[8:8 + plen],
        'raw': d,
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    info = {}
    print('=== 三份样本对照 ===')
    for k, p in SAMPLES.items():
        if not os.path.exists(p):
            print('%-16s 缺失: %s' % (k, p)); continue
        r = parse(p)
        info[k] = r
        print('%-16s size=%-4d payload_len=%-4d field2=0x%04x  载荷前16B=%s'
              % (k, r['size'], r['payload_len'], r['field2'], r['payload'].hex()[:32]))

    # 逐字节差分：原版解锁态 vs 原版全CG存档（同为原版格式，定位解锁数据区）
    a, b = info.get('原版-玩家解锁态'), info.get('原版-全CG存档')
    if a and b:
        print()
        print('=== 原版解锁态 vs 原版全CG存档：载荷逐字节差分 ===')
        pa, pb = a['payload'], b['payload']
        n = min(len(pa), len(pb))
        diffs = [i for i in range(n) if pa[i] != pb[i]]
        print('载荷长度 %d vs %d，差异字节数 %d' % (len(pa), len(pb), len(diffs)))
        print('前 40 处差异 (偏移: 解锁态 全CG档):')
        for i in diffs[:40]:
            print('  0x%03x: %02x %02x' % (i, pa[i], pb[i]))

    # R 版新档与两份原版的公共结构
    r = info.get('R版-新档')
    if r and a:
        print()
        print('=== R 版新档 vs 原版解锁态：头 32B 并列 ===')
        print('  R 版 :', r['raw'][:32].hex())
        print('  原版 :', a['raw'][:32].hex())

    json.dump({k: {'size': v['size'], 'payload_len': v['payload_len'], 'field2': v['field2']}
               for k, v in info.items()},
              open(os.path.join(PROJ, '语料', 'gamedata_samples.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print()
    print('样本信息已写入 语料\\gamedata_samples.json')


if __name__ == '__main__':
    main()

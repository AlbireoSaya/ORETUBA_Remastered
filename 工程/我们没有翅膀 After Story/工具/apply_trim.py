# -*- coding: utf-8 -*-
r"""apply_trim.py —— 回收"等长截断专项重译"结果并回填

1. 校验：条数/顺序与输入一致、**每条 GBK 字节数 ≤ budget**
2. 回填：按 (file, idx) 找到全局 `i`，写回对应的 `批次NN_译文.json`
3. 报告：仍超预算的条目（须为 0）、字节数变化统计

用法：python apply_trim.py [批次号 ...]   # 缺省 1..5
"""
import io
import json
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')


def main():
    which = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(1, 6))
    # (file, idx) -> 全局 i
    idx2i = {}
    for f in sorted(glob.glob(os.path.join(WD, '批次*_原文.json'))):
        for row in json.load(io.open(f, encoding='utf-8'))['lines']:
            idx2i[(row['file'], row['idx'])] = row['i']
    over, applied, saved = [], 0, 0
    for k in which:
        ip = os.path.join(WD, '精简批次%d_输入.json' % k)
        op = os.path.join(WD, '精简批次%d_输出.json' % k)
        if not (os.path.exists(ip) and os.path.exists(op)):
            print('精简批次%d：缺输入或输出，跳过' % k)
            continue
        src = json.load(io.open(ip, encoding='utf-8'))
        out = json.load(io.open(op, encoding='utf-8'))
        if len(src) != len(out):
            print('!! 精简批次%d 条数不符：%d vs %d' % (k, len(src), len(out)))
        # 回填（按批分组写盘）
        by_batch = {}
        for a, b in zip(src, out):
            if a['file'] != b.get('file') or a['idx'] != b.get('idx'):
                print('!! 精简批次%d 顺序不符 @%s#%s' % (k, a['file'], a['idx']))
                continue
            cn = (b.get('cn') or '').strip()
            nb = len(cn.encode('gbk'))
            if nb > a['budget']:
                over.append((a['file'], a['idx'], nb, a['budget'], cn[:40]))
                continue
            i = idx2i.get((a['file'], a['idx']))
            if i is None:
                print('!! 找不到 i：%s#%s' % (a['file'], a['idx']))
                continue
            by_batch.setdefault(i // 800 + 1, []).append((i, cn, nb, len(a['cur'].encode('gbk'))))
        for bn, items in by_batch.items():
            p = os.path.join(WD, '批次%02d_译文.json' % bn)
            d = json.load(io.open(p, encoding='utf-8'))
            mp = {i: (cn, nb, ob) for i, cn, nb, ob in items}
            for row in d['tr']:
                if row['i'] in mp:
                    cn, nb, ob = mp[row['i']]
                    saved += ob - nb
                    row['cn'] = cn
                    applied += 1
            io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
        print('精简批次%d：%d 条回填（跨 %d 个批次）' % (k, len(out), len(by_batch)))
    print('\n回填 %d 条；仍超预算 %d 条；累计减少 %d 字节' % (applied, len(over), saved))
    for o in over[:10]:
        print('  ⚠ %s#%s %d>%d  %s' % o)


if __name__ == '__main__':
    main()
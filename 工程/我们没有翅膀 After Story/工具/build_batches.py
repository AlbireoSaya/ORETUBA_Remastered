# -*- coding: utf-8 -*-
r"""build_batches.py —— 把 18,213 条台词切成可独立交付的翻译批次

批次规则：
  * 按 `语料\台词.json` 的脚本顺序展平，**不跨文件切批**（保证上下文连贯）；
  * 每批约 BATCH 条（默认 800）；
  * 每条分配**全局序号 i**（合并时按 i 校验：数量 + 序号集合必须完全一致）。

产出：
  翻译工作区\批次清单.json          批次 → 文件、条数、i 区间
  翻译工作区\批次<NN>_原文.json     {batch, count, lines:[{i, file, idx, kind, spk, jp}]}
  （子代理产出）翻译工作区\批次<NN>_译文.json  {batch, tr:[{i, cn}]}

用法：python build_batches.py [--batch 800] [--out 翻译工作区]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
LINES = os.path.join(PROJ, '语料', '台词.json')


def main():
    size = 800
    if '--batch' in sys.argv:
        size = int(sys.argv[sys.argv.index('--batch') + 1])
    outdir = os.path.join(PROJ, '翻译工作区')
    os.makedirs(outdir, exist_ok=True)

    data = json.load(io.open(LINES, encoding='utf-8'))
    flat = []
    i = 0
    for fn in sorted(data):
        for m in data[fn]['messages']:
            flat.append({'i': i, 'file': fn, 'idx': m['index'], 'kind': m['kind'],
                         'spk': m.get('speaker'), 'jp': m['text']})
            i += 1

    batches, cur, cur_files = [], [], set()
    for row in flat:
        cur.append(row)
        cur_files.add(row['file'])
        if len(cur) >= size:
            batches.append(cur)
            cur, cur_files = [], set()
    if cur:
        batches.append(cur)

    manifest = []
    for n, b in enumerate(batches, 1):
        name = '批次%02d' % n
        io.open(os.path.join(outdir, name + '_原文.json'), 'w', encoding='utf-8').write(
            json.dumps({'batch': n, 'count': len(b), 'lines': b}, ensure_ascii=False, indent=1))
        manifest.append({'batch': n, 'count': len(b), 'i_from': b[0]['i'], 'i_to': b[-1]['i'],
                         'files': sorted({r['file'] for r in b}),
                         'src': name + '_原文.json', 'dst': name + '_译文.json'})
    io.open(os.path.join(outdir, '批次清单.json'), 'w', encoding='utf-8').write(
        json.dumps({'total_lines': len(flat), 'batch_size': size, 'batches': manifest},
                   ensure_ascii=False, indent=1))
    print('总条数 %d，切成 %d 批（每批约 %d 条）' % (len(flat), len(batches), size))
    for m in manifest:
        print('   %-8s i=%5d..%-5d %4d 条  %d 个文件' %
              ('批次%02d' % m['batch'], m['i_from'], m['i_to'], m['count'], len(m['files'])))


if __name__ == '__main__':
    main()

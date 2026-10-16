# -*- coding: utf-8 -*-
r"""fix_punct.py —— 标点体例归一（`、` 与原文 1:1）

背景：主代理体例 A3 = 原文 `、` 逐处保留为 `、`（通用术语表 §6.1）。
前几批译文（01/02/03/05）把部分 `、` 合并成了 `，`，批次 06 多补了停顿符
→ 本脚本做**纯标点层**归一，逐行把 `、` 的数量对齐到与日文原文一致：
  * 偏少：按「相对位置就近匹配」把对应个数的 `，` 改回 `、`；
  * 偏多：把多余的 `、` 改为 `，`。
不动任何汉字/假名/其它标点，故不改变语义。

用法：python fix_punct.py 1 2 3 5 6 [--dry]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')


def convert(jp, cn):
    """把 cn 里的 `、` 数量对齐到与 jp 一致，返回 (新 cn, 改了几处)"""
    need = jp.count('、') - cn.count('、')
    if need == 0 or not cn:
        return cn, 0
    chars = list(cn)
    if need > 0:
        jp_pos = [i / max(len(jp), 1) for i, c in enumerate(jp) if c == '、']
        cand = [i for i, c in enumerate(chars) if c == '，']
        used = set()
        for p in jp_pos:
            best = None
            for i in cand:
                if i in used:
                    continue
                d = abs(i / max(len(cn), 1) - p)
                if best is None or d < best[0]:
                    best = (d, i)
            if best:
                used.add(best[1])
            if len(used) >= need:
                break
        for i in used:
            chars[i] = '、'
        return ''.join(chars), len(used)
    # 偏多：从右往左把多余的 `、` 改回 `，`
    cand = [i for i, c in enumerate(chars) if c == '、']
    for i in cand[-(-need):]:
        chars[i] = '，'
    return ''.join(chars), -need


def main():
    dry = '--dry' in sys.argv
    batches = [int(x) for x in sys.argv[1:] if x.isdigit()]
    tot = 0
    for n in batches:
        src = json.load(io.open(os.path.join(WD, '批次%02d_原文.json' % n), encoding='utf-8'))['lines']
        dst_p = os.path.join(WD, '批次%02d_译文.json' % n)
        dst = json.load(io.open(dst_p, encoding='utf-8'))
        jp_by_i = {r['i']: (r['jp'] or '') for r in src}
        changed = 0
        for row in dst['tr']:
            jp = jp_by_i.get(row['i'], '')
            cn = row.get('cn') or ''
            if not jp or not cn:
                continue
            new, k = convert(jp, cn)
            if k:
                row['cn'] = new
                changed += 1
        print('批次%02d：%d 行标点归一' % (n, changed))
        tot += changed
        if not dry:
            io.open(dst_p, 'w', encoding='utf-8').write(json.dumps(dst, ensure_ascii=False, indent=1))
    print('合计 %d 行%s' % (tot, '（dry-run，未写入）' if dry else ''))


if __name__ == '__main__':
    main()

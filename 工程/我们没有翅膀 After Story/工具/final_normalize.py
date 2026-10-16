# -*- coding: utf-8 -*-
r"""final_normalize.py —— 交付前最后一次跨批归一（条件化，避免误伤）

处理项（全部按"日文原文"判定，不做无差别替换）：
  1. **顶层 `『』` → `“”`**：JP 该行含 `『』` 且不含 `「`（即非嵌套引语）时，
     译文里的 `‘’` 改回 `“”`——与 01–20 批主流写法统一（嵌套 `『』` 仍作 `‘’`）。
  2. **んむ 系拟声统一为「唔姆」**：仅当 JP 含 `んむ` 时，把 `唔嗯`／`唔呣` → `唔姆`。
  3. **ヨユー → 小意思**：仅当 JP 含 `ヨユー` 时替换。
  4. **コーダイン → 小香田**：仅当 JP 含 `コーダイン` 时替换（原批次 08 误作「闲谈」）。

用法：python final_normalize.py [--dry]
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
    dry = '--dry' in sys.argv
    tot = {1: 0, 2: 0, 3: 0, 4: 0}
    for f in sorted(glob.glob(os.path.join(WD, '批次*_译文.json'))):
        src = json.load(io.open(f.replace('译文', '原文'), encoding='utf-8'))['lines']
        jp = {r['i']: (r['jp'] or '') for r in src}
        d = json.load(io.open(f, encoding='utf-8'))
        k = {1: 0, 2: 0, 3: 0, 4: 0}
        for row in d['tr']:
            cn = row.get('cn') or ''
            j = jp.get(row['i'], '')
            if not cn:
                continue
            # 1 顶层『』
            if '『' in j and '「' not in j and ('‘' in cn or '’' in cn):
                cn = cn.replace('‘', '“').replace('’', '”')
                k[1] += 1
            # 2 んむ 系
            if 'んむ' in j:
                for a in ('唔嗯', '唔呣'):
                    if a in cn:
                        k[2] += cn.count(a)
                        cn = cn.replace(a, '唔姆')
            # 3 ヨユー
            if 'ヨユー' in j and '绰绰有余' in cn:
                k[3] += cn.count('绰绰有余')
                cn = cn.replace('绰绰有余', '小意思')
            # 4 コーダイン
            if 'コーダイン' in j and '闲谈' in cn:
                k[4] += cn.count('闲谈')
                cn = cn.replace('闲谈', '小香田')
            row['cn'] = cn
        if any(k.values()) and not dry:
            io.open(f, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
        for i in k:
            tot[i] += k[i]
        if any(k.values()):
            print('%s: 顶层引号 %d 行 / んむ %d / ヨユー %d / コーダイン %d'
                  % (os.path.basename(f), k[1], k[2], k[3], k[4]))
    print('\n合计：顶层引号 %d 行、んむ %d 处、ヨユー %d 处、コーダイン %d 处%s'
          % (tot[1], tot[2], tot[3], tot[4], '（dry）' if dry else ''))


if __name__ == '__main__':
    main()

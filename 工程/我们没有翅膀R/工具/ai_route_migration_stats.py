# -*- coding: utf-8 -*-
r"""亜衣线译文迁移比例——精确版（ISSUE-ORETUBAR-R）。

两路独立测量：
  A) 同文匹配：以 R 版日文原文为 key，在参照汉化里查同文，判定该处交付的是中文还是残留日文
  B) 场景覆盖：亜衣线全部场景，按槽序归一化对齐，统计参照侧已译/未译/无参照

判据：参照汉化交付的 .sob 中，未译槽仍是日文原文，已译槽是中文。
      「已译」= 含汉字且不含假名。
"""
import os, sys, json
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
REF_JSON = os.path.join(PROJ, '参照', '汉化文本.json')
R_JSON = os.path.join(PROJ, '语料', 'R版台词.json')


def has_kana(s):
    return any(0x3040 <= ord(c) <= 0x30FF for c in s)


def has_han(s):
    return any(0x4E00 <= ord(c) <= 0x9FFF for c in s)


def is_translated(t):
    t = t.strip()
    return has_han(t) and not has_kana(t)


def load():
    r, m = defaultdict(list), defaultdict(list)
    for row in json.load(open(R_JSON, encoding='utf-8')):
        r[os.path.splitext(row['file'])[0]].append(row)
    for row in json.load(open(REF_JSON, encoding='utf-8')):
        m[os.path.splitext(row['file'])[0]].append(row)
    return r, m


def main():
    r, m = load()
    ai = sorted(f for f, rows in r.items() if any(x.get('speaker') == '亜衣' for x in rows))
    print('亜衣有台词的场景: %d 个\n' % len(ai))

    # ---- 参照汉化的整体完成度 ----
    idx = defaultdict(list)
    ref_total = ref_trans = 0
    for sc, rows in m.items():
        for i, row in enumerate(rows):
            t = row['text'].strip()
            if not t:
                continue
            ref_total += 1
            if is_translated(t):
                ref_trans += 1
            else:
                idx[t].append((sc, i))
    print('=== 参照汉化整体 ===')
    print('  槽总数 %d ；已译 %d = %.1f%% ；残留日文 %d = %.1f%%'
          % (ref_total, ref_trans, 100 * ref_trans / ref_total,
             ref_total - ref_trans, 100 * (ref_total - ref_trans) / ref_total))
    print('  （倒入倒排索引的「未译原文」条目: %d）\n' % len(idx))

    # ---- 测量 A ----
    stat = Counter()
    samples = []
    for sc in ai:
        for row in r[sc]:
            t = row['text'].strip()
            if not t or not (has_kana(t) or has_han(t)):
                continue
            stat['r'] += 1
            hit = idx.get(t)
            if not hit:
                stat['no_match'] += 1
                if len(samples) < 6:
                    samples.append((sc, t[:46]))
            elif any(is_translated(m[s][i]['text']) for s, i in hit):
                stat['migratable'] += 1
            else:
                stat['hit_jp'] += 1
    print('=== 测量 A：同文匹配（亜衣线 %d 场景）===' % len(ai))
    t = stat['r']
    print('  可比对槽数: %d' % t)
    print('  ✔ 可迁移（参照侧同文且已译）: %d = **%.1f%%**' % (stat['migratable'], 100 * stat['migratable'] / t))
    print('    同文命中但参照侧仍是日文  : %d = %.1f%%' % (stat['hit_jp'], 100 * stat['hit_jp'] / t))
    print('    参照侧无同文（R 版新增）  : %d = %.1f%%' % (stat['no_match'], 100 * stat['no_match'] / t))
    print('  无同文样例:')
    for s, x in samples:
        print('    [%s] %s' % (s, x))

    # ---- 测量 B ----
    b = Counter()
    for sc in ai:
        rr = [x for x in r[sc] if x['text'].strip()]
        mm = [x for x in m.get(sc, []) if x['text'].strip()]
        b['r'] += len(rr)
        if not mm:
            b['no_ref'] += len(rr)
            continue
        n_r, n_m = len(rr), len(mm)
        for i in range(n_r):
            j = min(int(i * n_m / n_r), n_m - 1)
            if is_translated(mm[j]['text']):
                b['trans'] += 1
            else:
                b['untrans'] += 1
    print()
    print('=== 测量 B：场景覆盖（槽序归一化）===')
    print('  亜衣线槽数 %d' % b['r'])
    print('    参照位置已译  : %d = %.1f%%' % (b['trans'], 100 * b['trans'] / b['r']))
    print('    未译 / 无参照 : %d = %.1f%%' % (b['untrans'] + b['no_ref'], 100 * (b['untrans'] + b['no_ref']) / b['r']))
    print('      （其中 R 版新增文件贡献 %d 槽）' % b['no_ref'])

    # ---- 场景构成 ----
    newf = [f for f in ai if f not in m]
    oldf = [f for f in ai if f in m]
    ns = sum(len([x for x in r[f] if x['text'].strip()]) for f in newf)
    os_ = sum(len([x for x in r[f] if x['text'].strip()]) for f in oldf)
    print()
    print('=== 亜衣线场景构成 ===')
    print('  参照已有场景 %d 个 / %d 槽' % (len(oldf), os_))
    print('  R 版新增场景 %d 个 / %d 槽' % (len(newf), ns))
    print('  新增文件: %s' % newf)


if __name__ == '__main__':
    main()

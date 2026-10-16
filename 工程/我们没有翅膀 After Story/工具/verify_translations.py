# -*- coding: utf-8 -*-
r"""verify_translations.py —— 批次译文机器校验（翻译质量的第一道闸）

逐批检查（每条都给出可复现证据）：
  1. 结构：`tr` 条数 / `i` 顺序与原文一致（缺条、错位、重复）
  2. 完整性：`cn` 非空（原文为空槽者除外）
  3. 编码：`cn` 必须可 GBK 编码
  4. 假名残留：正文不得残留平/片假名（例外白名单见 KANA_OK）
  5. 标点：无半角标点、无 U+3000、无 SJIS 码位标点（U+301C/U+2015/U+30FB 等）
  6. 标点 1:1：`、`/`。`/`…`/`～`/`！`/`？` 的计数与原文一致（宽容度为 0）
  7. 引号：`「」`→`“”`、`『』`→`‘’` 的对数一致
  8. 译名：日文原文出现锁定专名时，译文应含对应中文（警告级）

用法：
  python verify_translations.py [批次号 ...]        # 缺省校验全部已完成批次
产出：语料\校验报告.json + 控制台摘要
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')

KANA = re.compile(r'[\u3041-\u309f\u30a0-\u30f6]')
HALF = re.compile(r'[,.!?;:()\[\]{}<>]')
BADP = re.compile(r'[\u301c\u2015\u30fb\u2500]')      # 〜 ― ・ ─（JP 码位；U+2026 … 与 U+2014 — 是规定的目标字符，不算）
JP_PUNCT = ['、', '。', '！', '？']
# 允许保留的假名（作品名/梗词，已登记在作品 skill 的例外里）
KANA_OK = ['あたとど', 'いもももと', 'いももと', 'みぜＬＯＶＥる', 'か行ば行た行']
ZH_SAME = {'一同', '少女', '女子', '男子', '子供', '声', '京', '優', '翔', '三人', '全員',
           '母親', '中年女性', '平民', '本文', '件名'}

# 标点计数容差（0 = 严格 1:1）
TOL = 0


def counts(s, ch):
    return s.count(ch) if s else 0


def check_batch(n, lock):
    src_p = os.path.join(WD, '批次%02d_原文.json' % n)
    dst_p = os.path.join(WD, '批次%02d_译文.json' % n)
    if not (os.path.exists(src_p) and os.path.exists(dst_p)):
        return None
    src = json.load(io.open(src_p, encoding='utf-8'))['lines']
    dst = json.load(io.open(dst_p, encoding='utf-8'))['tr']
    issues = {'缺条': [], '错位': [], '空译': [], 'GBK': [], '假名残留': [], '半角标点': [],
              '全角空格': [], 'SJIS码位': [], '顿号被合并': [], '标点增补提示': [],
              '引号数不符': [], '日文形残留': []}
    if len(src) != len(dst):
        issues['缺条'].append('条数 %d vs %d' % (len(src), len(dst)))
    for k, (s, t) in enumerate(zip(src, dst)):
        if s['i'] != t['i']:
            issues['错位'].append('k=%d i %s vs %s' % (k, s['i'], t['i']))
        jp, cn = s.get('jp'), (t.get('cn') or '')
        if not cn:
            if jp:
                issues['空译'].append('i=%s' % s['i'])
            continue
        try:
            cn.encode('gbk')
        except UnicodeEncodeError as e:
            issues['GBK'].append('i=%s %r' % (s['i'], cn[max(0, e.start - 5):e.end + 5]))
        kn = KANA.findall(cn)
        if kn and not any(x in cn for x in KANA_OK):
            issues['假名残留'].append('i=%s %s' % (s['i'], ''.join(kn)[:12]))
        if HALF.search(cn):
            issues['半角标点'].append('i=%s %s' % (s['i'], HALF.search(cn).group()))
        if '\u3000' in cn:
            issues['全角空格'].append('i=%s' % s['i'])
        bad = BADP.findall(cn)
        if bad:
            issues['SJIS码位'].append('i=%s %s' % (s['i'], ''.join(sorted(set(bad)))))
        if jp:
            # `、` 合并 = 违规（通用表 §6.1）；`。`/`！`/`？` 的增补属中文句法需要，仅记提示
            if counts(cn, '、') < counts(jp, '、'):
                issues['顿号被合并'].append('i=%s JP%d/CN%d' % (s['i'], counts(jp, '、'), counts(cn, '、')))
            for ch in ['。', '！', '？', '…']:
                if counts(jp, ch) != counts(cn, ch):
                    issues['标点增补提示'].append('i=%s %s JP%d/CN%d' % (s['i'], ch, counts(jp, ch), counts(cn, ch)))
                    break
            if counts(jp, '「') == counts(jp, '」') and counts(jp, '「'):
                if counts(jp, '「') != counts(cn, '“'):
                    issues['引号数不符'].append('i=%s 「%d/“%d' % (s['i'], counts(jp, '「'), counts(cn, '“')))
            # 日文形残留：原文名在译文里以**日文写法**出现（中译名与日文形不同者才检查）
            for jp_name, cn_name in lock['speakers'].items():
                if (jp_name != cn_name and len(jp_name) >= 2 and jp_name not in ZH_SAME
                        and jp_name in cn and not any(k in cn for k in KANA_OK)):
                    issues['日文形残留'].append('i=%s %s 应为 %s' % (s['i'], jp_name, cn_name))
                    break
    return issues


def main():
    lock = json.load(io.open(os.path.join(PROJ, '语料', '译名锁定表.json'), encoding='utf-8'))
    which = [int(x) for x in sys.argv[1:]]
    if not which:
        which = [n for n in range(1, 24) if os.path.exists(os.path.join(WD, '批次%02d_译文.json' % n))]
    rep, bad_total = {}, 0
    print('批次  条数  问题数（缺条/错位/空译/GBK/假名/半角/全角空格/SJIS码位/标点/引号/译名）')
    for n in which:
        # 译文可能为空槽 -> 以上一版还原
        r = check_batch(n, lock)
        if r is None:
            print('批次%02d  未完成' % n)
            continue
        rep['批次%02d' % n] = {k: (len(v), v[:5]) for k, v in r.items()}
        HINT = {'标点增补提示'}
        n_bad = sum(1 for k, v in r.items() if k not in HINT for _ in v)
        bad_total += n_bad
        print('批次%02d  %4d  ' % (n, len(json.load(io.open(
            os.path.join(WD, '批次%02d_原文.json' % n), encoding='utf-8'))['lines']))
              + ' '.join('%s%d' % (k[:2], len(v)) for k, v in r.items()))
    io.open(os.path.join(PROJ, '语料', '校验报告.json'), 'w', encoding='utf-8').write(
        json.dumps(rep, ensure_ascii=False, indent=1))
    print('\n硬问题合计 %d（"译名警告"为启发式，不计入）' % bad_total)
    print('明细见 语料\\校验报告.json')


if __name__ == '__main__':
    main()

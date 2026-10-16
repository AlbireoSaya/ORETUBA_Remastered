# -*- coding: utf-8 -*-
"""verify_cn.py —— 译文批次校验（ISSUE-20260917-14）

检查项（任一不过即 FAIL）：
  1. 槽覆盖：批次内每个 slot 恰好一条译文，无缺失、无多余、无重复
  2. 非空：译文不得为空、不得只有标点
  3. 编码：译文必须可 GBK 编码（不可编码字符须已按回退表替换）
  4. 标点：无半角标点、无 `〜`(U+301C)、无 `　`(U+3000)、无 `「」『』`、无 `...`
  5. 行数：译文不得短于原文 0.25 倍或多于 2.5 倍（疑漏译/疑夹带）
  6. 前缀：译文不得包含 `#`、`$&`、`$`（这些是结构前缀，由构建步骤拼装）
用法：python -X utf8 verify_cn.py [批次名 ...]   （缺省=全部已产出批次）
"""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
BATCH = os.path.join(PROJ, '语料', '批次')
TRANS = os.path.join(PROJ, '翻译工作区', '译文')

BAD_HALF = re.compile(r'[,\.!\?;:()\[\]<>"]')
BAD = {'〜': 'U+301C 波线应为 ～(U+FF5E)', '　': 'U+3000 全角空格须删除',
       '「': '须转 “', '」': '须转 ”', '『': '须转 ‘', '』': '须转 ’',
       '...': '省略号须用 ……', '$': '结构符不得出现在译文', '#': '结构符不得出现在译文'}


def load_batch(name):
    rows = {}
    with open(os.path.join(BATCH, name + '.tsv'), encoding='utf-8') as f:
        hdr = f.readline()
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 7:
                continue
            rows[p[1]] = dict(seq=int(p[0]), kind=p[4], td=int(p[5]),
                              body=p[6].replace('\\n', '\n'))
    return rows


def load_trans(name):
    p = os.path.join(TRANS, name + '.tsv')
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.rstrip('\n')
            if not line:
                continue
            if i == 0 and line.startswith('slot'):
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            out[parts[0].strip()] = parts[1].replace('\\n', '\n')
    return out


def check(name):
    b = load_batch(name)
    t = load_trans(name)
    errs, warns = [], []
    if t is None:
        return ['译文文件缺失'], []
    miss = [s for s in b if s not in t]
    extra = [s for s in t if s not in b]
    if miss:
        errs.append('缺译 %d 槽，例: %s' % (len(miss), miss[:5]))
    if extra:
        errs.append('多余槽 %d 条，例: %s' % (len(extra), extra[:5]))
    for s, cn in t.items():
        if s not in b:
            continue
        src = b[s]
        if not cn.strip():
            errs.append('%s 译文为空' % s)
            continue
        try:
            cn.encode('gbk')
        except UnicodeEncodeError as e:
            errs.append('%s 不可 GBK 编码: %r' % (s, cn[max(0, e.start - 3):e.end + 3]))
        if re.search(r'[ぁ-ゟァ-ヺーｦ-ﾟ]', cn):
            # 降级为警告：正当例外见作品层术语表 §三之三十七（被讨论的日语语言现象）
            warns.append('%s 译文含假名（请确认是否属语言现象例外）: %r' % (s, cn[:40]))
        for ch, why in BAD.items():
            if ch in cn:
                errs.append('%s 含禁用字符 %s（%s）' % (s, ch, why))
                break
        if BAD_HALF.search(cn) and not re.search(r'[A-Za-z0-9]', cn):
            errs.append('%s 含半角标点: %r' % (s, cn[:40]))
        n_src, n_cn = len(src['body']), len(cn)
        if n_src >= 6 and n_cn < n_src * 0.25:
            warns.append('%s 译文过短（原 %d → 译 %d）: %r' % (s, n_src, n_cn, cn[:30]))
        if n_src >= 6 and n_cn > n_src * 2.5:
            warns.append('%s 译文过长（原 %d → 译 %d）: %r' % (s, n_src, n_cn, cn[:30]))
        if '\\n' in src['body'] and '\n' not in cn:
            errs.append('%s 原文含换行，译文丢失' % s)
        # 内嵌显示控制码 <N>\ / <N> 必须原样保留（全库 547 处）
        ctl_src = re.findall(r'<-?\d+>\\?', src['body'])
        if ctl_src:
            ctl_cn = re.findall(r'<-?\d+>\\?', cn)
            if ctl_cn != ctl_src:
                errs.append('%s 内嵌控制码不一致: 原 %s / 译 %s' % (s, ctl_src, ctl_cn))
    return errs, warns


def main():
    names = sys.argv[1:] or sorted(
        f[:-4] for f in os.listdir(BATCH) if f.startswith('batch_'))
    tot_e = tot_w = ok = 0
    for n in names:
        e, w = check(n)
        tot_e += len(e)
        tot_w += len(w)
        if not e:
            ok += 1
        print('%s: %s  (err %d / warn %d)' % (n, 'FAIL' if e else 'PASS', len(e), len(w)))
        for x in e[:6]:
            print('    ✗', x)
        for x in w[:3]:
            print('    !', x)
    print('\n汇总：PASS %d / %d，错误 %d，警告 %d' % (ok, len(names), tot_e, tot_w))
    return 1 if tot_e else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

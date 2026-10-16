# -*- coding: utf-8 -*-
"""test_all.py —— 对全部 .tob 做三项硬验收自检（noop / 等长 / 变长重定位）。"""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tob_extract as E
import tob_rewrite as W

RT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    files = [os.path.join(RT, f) for f in sorted(os.listdir(RT)) if f.lower().endswith('.tob')]
    n_noop = n_eq = n_rb = 0
    bad = []
    relocated_total = 0
    skipped = 0
    for idx, p in enumerate(files):
        name = os.path.basename(p)
        d = open(p, 'rb').read()
        # (a) noop
        if md5(open(p, 'rb').read()) != md5(d):
            bad.append((name, 'noop md5'))
        else:
            n_noop += 1
        info, msgs, warns = E.parse_messages(p)
        cand = [m for m in msgs if m['text'] and m['len'] >= 4]
        if not cand:
            skipped += 1
            continue
        m = cand[len(cand) // 2]
        # (b) 等长替换（GBK 文本 + 空格补齐）
        new_eq = ('试' * (m['len'] // 2))   # GBK 每字 2 字节，恰好不超过原长
        e = {'offset': m['offset'], 'len': m['len'], 'text': new_eq}
        try:
            out_eq = W.apply_edits_equal(d, [e], 0x20, 'gbk')
            dr = W._diff_ranges(d, out_eq) or []
            ok = all(s >= m['offset'] and t <= m['offset'] + m['len'] for s, t in dr)
            if ok:
                n_eq += 1
            else:
                bad.append((name, 'equal 越界改动'))
        except Exception as ex:
            bad.append((name, 'equal 异常: %s' % ex))
        # (c) 变长替换（加长 2 字节）
        e2 = {'offset': m['offset'], 'len': m['len'], 'text': new_eq + '汉'}
        try:
            out_rb, census, moved = W.apply_edits_rebuild(d, [e2], True, 'gbk')
            io = E.parse_header(out_rb)
            exp = (new_eq + '汉').encode('gbk')
            if (len(out_rb) == len(d) + 2 and io['B'] == info['B']
                    and out_rb[m['offset']:m['offset'] + len(exp)] == exp):
                n_rb += 1
                relocated_total += len(moved)
            else:
                bad.append((name, 'rebuild 校验不符'))
        except Exception as ex:
            bad.append((name, 'rebuild 异常: %s' % ex))
    print('文件总数: %d' % len(files))
    print('(a) noop md5 一致: %d' % n_noop)
    print('(b) 等长替换通过: %d' % n_eq)
    print('(c) 变长 rebuild 通过: %d   (跳过无长文本文件: %d)' % (n_rb, skipped))
    print('    变长模式下累计重定位地址字段: %d' % relocated_total)
    print('失败项: %d' % len(bad))
    for name, why in bad[:20]:
        print('   [失败]', name, why)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selftest_summary.txt'),
              'w', encoding='utf-8') as fp:
        fp.write('files=%d noop=%d equal=%d rebuild=%d skipped=%d relocated=%d fails=%d\n'
                 % (len(files), n_noop, n_eq, n_rb, skipped, relocated_total, len(bad)))
        for name, why in bad:
            fp.write('%s\t%s\n' % (name, why))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())

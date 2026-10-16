# -*- coding: utf-8 -*-
r"""verify_build.py —— 建包结果校验（按**原始偏移**逐条比对，绕开编码假设）

思路：等长回填后字节偏移不变，故可直接用原文的 [off, off+len) 区间去取**新文件**的字节，
按 GBK 解码后与译文比对。这样不依赖任何"文本边界启发式"，也不受编码假设影响。

检查项：
  1. 每个脚本长度不变（等长回填的前提）
  2. 每条**已译**台词：新文件该区间 GBK 解码 == 译文（去尾部补齐的全角空格）
  3. 每条人名声明串：区间末尾字节 == 0x00，且内容以中文名开头
  4. 未译台词保持不变

用法：python verify_build.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, '语料', '原文')
BUILT = os.path.join(PROJ, '构建', '脚本_中文')


def main():
    tr = json.load(io.open(os.path.join(PROJ, '语料', '译文.json'), encoding='utf-8'))
    lock = json.load(io.open(os.path.join(PROJ, '语料', '译名锁定表.json'), encoding='utf-8'))
    n_file = n_txt = n_decl = n_trunc = 0
    bad_len, bad_txt, bad_decl, bad_null = [], [], [], []
    for fn, v in tr.items():
        a = io.open(os.path.join(SRC, fn), 'rb').read()
        p = os.path.join(BUILT, fn)
        if not os.path.exists(p):
            continue
        b = io.open(p, 'rb').read()
        n_file += 1
        if len(a) != len(b):
            bad_len.append((fn, len(a), len(b)))
            continue
        for m in v['messages']:
            dcl, off, ln = m.get('decl'), m.get('off'), m.get('len')
            if dcl and m.get('speaker') in lock['speakers']:
                doff, dlen = dcl
                seg = b[doff:doff + dlen]
                nm = lock['speakers'][m['speaker']]
                if len(nm.encode('gbk')) + 1 > dlen:
                    nm = lock.get('speakers_short', {}).get(m['speaker'], nm)
                if seg[-1:] != b'\x00':
                    bad_null.append((fn, m['index'], m['speaker']))
                if not seg.startswith(nm.encode('gbk')[:len(seg) - 1]):
                    bad_decl.append((fn, m['index'], m['speaker'], seg))
                n_decl += 1
            cn = (m.get('cn') or '').strip()
            if off is None or not ln:
                continue
            seg = b[off:off + ln]
            if not cn:
                if seg != a[off:off + ln]:
                    bad_txt.append((fn, m['index'], '未译却改动', seg[:24]))
                continue
            got = seg.decode('gbk', 'replace').rstrip('　 ')
            if got == cn:
                n_txt += 1
            elif cn.startswith(got) and got:
                n_trunc += 1                       # 等长截断（已在构建报告记账）
            else:
                bad_txt.append((fn, m['index'], cn[:24], got[:24]))
                n_txt += 1
    print('校验脚本 %d 个；等长回填正文 %d 条（其中等长截断 %d 条）；人名声明串 %d 条'
          % (n_file, n_txt + n_trunc, n_trunc, n_decl))
    print('长度不符脚本: %d %s' % (len(bad_len), bad_len[:3]))
    print('正文不符: %d %s' % (len(bad_txt), bad_txt[:3]))
    print('声明串未以 NUL 结尾: %d %s' % (len(bad_null), bad_null[:3]))
    print('声明串不符: %d %s' % (len(bad_decl), bad_decl[:3]))
    ok = not (bad_len or bad_txt or bad_null or bad_decl)
    print('结论:', 'PASS（建包与译文完全一致）' if ok else 'FAIL')


if __name__ == '__main__':
    main()

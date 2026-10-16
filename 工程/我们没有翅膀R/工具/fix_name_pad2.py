# -*- coding: utf-8 -*-
r"""名字填充修正（第二版，ISSUE-ORETUBAR-R）。

**实测根因**（对照日文原始记录）：
```
日文：01 01 08 00 | 96be 93fa 8d81 8149 00   ← 尾部是**全角空格**(8149)，body 8 字节
中文：01 01 07 00 | c3f7 c8d5 cfe3 20         ← 尾部是**半角空格**(20)，body 7 字节
```
⇒ 中文版比日文**少 1 字节**，且用**半角空格**；名字框据此渲染出 `□□□`。

**修法**：把名字正文按「**日文原始 body 长度**」用**全角空格**补齐：
  * 目标是让中文 body 长度 == 日文 body 长度（偶数、以全角空格收尾）
  * 若中文名 + 全角空格恰好等于该长度 → 直接用
  * 若差 1 字节（奇偶不匹配）→ 用 1 个**半角空格**收尾（此为个别情况，优先靠改名字长度避免）

本脚本直接读「原始 R 版脚本」拿到每个名字记录的原始长度，再据此生成修正项。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(P, '语料', 'R版SCRIPT')
CUR = os.path.join(P, '语料', '名字中文化.json')
OUT = os.path.join(P, '语料', '名字填充修正2.json')

NUL = b'\x00'
SP = b'\x20'
FW = '\u3000'.encode('gbk')


def ref_len_map():
    """{file: {中文名候选取向: 日文 body 长度}}——按偏移对齐不可行，
    改用「同一文件内名字串的顺序」对齐：逐文件解析两边的声明串序列。"""
    out = {}
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SRC, fn), 'rb').read()
        seq = []
        for m in re.finditer(rb'\x01\x01', raw):
            j = m.start()
            if j + 4 > len(raw):
                continue
            ln = raw[j + 2] | (raw[j + 3] << 8)
            if not (3 <= ln <= 40):
                continue
            body = raw[j + 4:j + 4 + ln]
            if body[-1:] != NUL:
                continue
            core = body[:-1]
            if not core:
                continue
            try:
                t = core.decode('cp932')
            except Exception:
                continue
            if not all((0x3040 <= ord(c) <= 0x30FF) or (0x4E00 <= ord(c) <= 0x9FFF)
                       or c == '\u3000' or ('Ａ' <= c <= 'Ｚ') or c == '\u30fb' for c in t):
                continue
            seq.append((j, ln, t))
        if seq:
            out[fn] = seq
    return out


def main():
    refs = ref_len_map()
    cur = json.load(open(CUR, encoding='utf-8'))
    # 当前中文名记录：按文件分组、按 offset 排序
    by_file = {}
    for r in cur:
        by_file.setdefault(r['file'], []).append(r)
    fixes = []
    stats = {'total': 0, 'fixed': 0, 'halfwidth_left': 0}
    for fn, rows in by_file.items():
        rows.sort(key=lambda x: x['offset'])
        seq = refs.get(fn, [])
        # 按「第 n 个声明串」对齐——中文与日文的声明串顺序一致
        name_seq = [s for s in seq if not s[2].strip().startswith('_')]
        for idx, r in enumerate(rows):
            stats['total'] += 1
            b = bytes(r['text_bytes'])
            if b[-1:] != NUL:
                continue
            core = b[:-1]
            # 去掉尾部空格，得到纯名字
            name = core.rstrip(SP + FW)
            try:
                nm = name.decode('gbk')
            except Exception:
                continue
            # 参考长度：优先用同索引的日文 body 长度
            ref = name_seq[idx][1] if idx < len(name_seq) else None
            if ref is None:
                ref = len(name) + 2      # 兜底：名字 + 全角空格
            # 目标：body 长度 == ref（且为偶数）
            target = ref
            if target <= len(name):
                target = len(name) + 2
            pad = target - len(name)
            if pad % 2:
                # 奇偶不匹配：用一个半角空格收尾（尽量避免）
                newcore = name + FW * (pad // 2) + SP
                stats['halfwidth_left'] += 1
            else:
                newcore = name + FW * (pad // 2)
            if len(newcore) != target:
                continue
            nb = newcore + NUL
            if nb != b:
                fixes.append({'file': fn, 'offset': r['offset'], 'len': target + 1,
                              'text_bytes': list(nb), 'src': 'name-pad2',
                              'text': newcore.decode('gbk', errors='replace')})
                stats['fixed'] += 1
    print('名字记录 %d；需修正 %d；仍含半角空格 %d' % (stats['total'], stats['fixed'], stats['halfwidth_left']))
    from collections import Counter
    c = Counter(x['text'] for x in fixes)
    print('样例（前 12 种）:')
    for k, v in c.most_common(12):
        print('   %-14s %d 条  (body %d 字节)' % (k, v, len(k.encode('gbk'))))
    json.dump(fixes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)


if __name__ == '__main__':
    main()

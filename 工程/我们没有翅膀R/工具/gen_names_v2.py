# -*- coding: utf-8 -*-
r"""重新生成「中文名」映射（正确版，ISSUE-ORETUBAR-R）。

**实测的原始结构**（日文 R 版脚本）：
```
01 01 <u16 len> <名字 SJIS 字节> 00
len = 名字字节数 + 1（含结尾 NUL），**没有任何填充**
例：和馬(4字节) → len=5；明日香(6字节) → len=7
```
⇒ 中文名同样应写成 `名字 GBK 字节 + NUL`，`len = 名字字节数 + 1`，
**不带任何填充**（此前我在构建器里加了空格填充，正是名字框渲染出 `□□□` 的原因）。

本脚本从「原始脚本」逐条定位名字声明串，按顺序与中文名映射配对，生成正确的替换项。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
from name_map import MAP

P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(P, '语料', 'R版SCRIPT')
OUT = os.path.join(P, '语料', '名字中文化.json')

NUL = b'\x00'


def is_name_like(t):
    if not t:
        return False
    for c in t:
        if 0x3040 <= ord(c) <= 0x30FF:
            continue
        if 0x4E00 <= ord(c) <= 0x9FFF:
            continue
        if c == '\u3000' or c == '\u30fb' or ('Ａ' <= c <= 'Ｚ'):
            continue
        if c == ' ':
            continue
        return False
    return any(0x3040 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF for c in t)


def main():
    out = []
    hit = 0
    miss = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SRC, fn), 'rb').read()
        for m in re.finditer(rb'\x01\x01', raw):
            j = m.start()
            if j + 4 > len(raw):
                continue
            ln = raw[j + 2] | (raw[j + 3] << 8)
            if not (3 <= ln <= 40):
                continue
            boff = j + 4
            body = raw[boff:boff + ln]
            if body[-1:] != NUL:
                continue
            core = body[:-1]
            if not core:
                continue
            try:
                t = core.decode('cp932')
            except Exception:
                continue
            if not is_name_like(t):
                continue
            key = t.strip('\u3000 ')
            if key not in MAP:
                miss.append((fn, boff, t))
                continue
            nb = MAP[key].encode('gbk') + NUL
            if len(nb) == 0:
                continue
            out.append({'file': fn, 'offset': boff, 'len': len(nb),
                        'text_bytes': list(nb), 'src': 'name-v2',
                        'text': MAP[key]})
            hit += 1
    print('生成中文名替换项: %d 条' % hit)
    print('未收录（保持原文）: %d 条' % len(miss))
    from collections import Counter
    c = Counter(x['text'] for x in out)
    print('覆盖角色: %d 种' % len(c))
    for k, v in c.most_common(12):
        print('   %-12s %d 条  (body %d 字节)' % (k, v, len(k.encode('gbk')) + 1))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)


if __name__ == '__main__':
    main()

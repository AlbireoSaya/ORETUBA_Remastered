# -*- coding: utf-8 -*-
r"""extract_choices.py —— 抽取解析器漏掉的"选择支提示 + 选项标签"（含字节坐标）

背景：`工具\parse_after.py` 对全项目 40 处记录报 `正文起点未找到`，实测这些记录是
**选择支块**——含提示正文（1 条）+ 若干选项标签（`01 01 <u16 L>` 声明串）。
这些同属显示文本，必须译出（一审组 6 发现）。

产出：语料\选择支补译.json
  [ {file, idx, prompt, prompt_off, prompt_len, options:[{jp, off, len}]} ]
"""
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, '语料', '原文')
sys.path.insert(0, HERE)
sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具')
import parse_after as PA          # noqa: E402
import tob_extract as T           # noqa: E402

DECL = re.compile(rb'\x01\x01(..)')
TEXT = re.compile(rb'(?:[\x20-\x7e\x81-\x9f\xe0-\xfc][\x40-\xfc])+')
BS = chr(92)
KANA = re.compile(r'[\u3041-\u309f\u30a0-\u30f6\u4e00-\u9fff]')


def main():
    rows = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith('.tob'):
            continue
        raw = io.open(os.path.join(SRC, fn), 'rb').read()
        info, msgs, warns = PA.parse(raw)
        if not warns:
            continue
        cs, prev = info['code_start'], info['code_start']
        for k, t in enumerate(info['T']):
            p = t + cs
            text_end = p - 18
            ts, body = T.find_text_start(raw, prev, text_end)
            if ts is None:
                region = raw[prev:text_end]
                first = DECL.search(region)
                head = region[:first.start()] if first else region
                prompt = None
                poff = plen = None
                for m in TEXT.finditer(head):
                    s = m.group(0)
                    if len(s) < 8:
                        continue
                    try:
                        txt = s.decode('cp932')
                    except UnicodeDecodeError:
                        continue
                    if KANA.search(txt) and '\x00' not in txt:
                        prompt = txt.strip('\u3000')
                        poff, plen = prev + m.start(), len(s)
                opts = []
                for mm in DECL.finditer(region):
                    L = struct.unpack('<H', mm.group(1))[0]
                    d = region[mm.start() + 4:mm.start() + 4 + L]
                    if len(d) != L or d[-1] != 0:
                        continue
                    try:
                        s = d[:-1].decode('cp932')
                    except UnicodeDecodeError:
                        continue
                    if BS in s or '.' in s:
                        continue
                    opts.append({'jp': s, 'off': prev + mm.start() + 4, 'len': L - 1})
                rows.append({'file': fn, 'idx': k, 'prompt': prompt, 'prompt_off': poff,
                             'prompt_len': plen, 'options': opts})
            prev = p
    io.open(os.path.join(PROJ, '语料', '选择支补译.json'), 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    np = sum(1 for r in rows if r['prompt'])
    no = sum(len(r['options']) for r in rows)
    print('记录 %d 条：提示 %d 条、选项标签 %d 条' % (len(rows), np, no))
    for r in rows:
        if r['prompt']:
            print('P [%s#%d] %s' % (r['file'], r['idx'], r['prompt']))
        for o in r['options']:
            print('   O [%s#%d] %s' % (r['file'], r['idx'], o['jp']))


if __name__ == '__main__':
    main()

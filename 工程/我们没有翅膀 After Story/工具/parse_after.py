# -*- coding: utf-8 -*-
r"""parse_after.py —— AfterStory 专用 TOB0 解析器（逐条关联 说话人 / 语音 / 立绘 / 正文）

与 R 版 tob_extract.py 的差别（本作实测）：
  * 文本边界沿用 tob_extract 的判据（尾部 18 字节签名 `5b 20 <op> 00 00 00 01 0b 00 00 00 01 01 00 <u32 k>`，
    本作 18,213/18,213 全部命中，零警告）；
  * 记录头 **op 不是固定的 0x19**（本作 op 取 0x18/0x10/… 等多种，依命令而定），
    因此**说话人不能靠 op 判定**——本作把说话人写成标准声明串 `01 01 <u16 L> <SJIS 名> 00`，
    与立绘 `PIC\*.ELG`、语音 `XXX####` 同处一条消息的记录区内。
  * ⇒ 说话人 = 该消息记录区 [上一条结束, 正文起点) 内**最后一个非资源类声明串**。

产出：语料\台词.json（覆盖写）：
  { "<脚本名>": { code_start, B, labels, warnings,
                  messages: [ {index, speaker, voice, image, text, off, len} ] } }

用法：python parse_after.py [--stats]
"""
import io
import json
import os
import re
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, '语料', '原文')
R_TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, R_TOOLS)
import tob_extract as T          # noqa: E402

TAIL_PREFIX = T.TAIL_PREFIX
DECL = re.compile(rb'\x01\x01(..)')


def decls_in(raw, lo, hi):
    """取 [lo,hi) 内的所有声明串 -> [(offset, text)]"""
    out = []
    for m in DECL.finditer(raw, lo, hi):
        L = struct.unpack('<H', m.group(1))[0]
        if L == 0 or L > 200:
            continue
        d = raw[m.start() + 4:m.start() + 4 + L]
        if len(d) != L or d[-1] != 0:
            continue
        body = d[:-1]
        try:
            s = body.decode('cp932')
        except UnicodeDecodeError:
            continue
        out.append((m.start(), s))
    return out


def classify(s):
    """声明串分类：resource / voice / name / none"""
    if '\\' in s or '/' in s or '.' in s:
        return 'resource'
    if re.fullmatch(r'[A-Za-z]{2,4}\d{3,5}[A-Za-z]?', s):
        return 'voice'
    if all(0x20 <= ord(c) < 0x7f for c in s):
        return 'none'
    return 'name'


def parse(raw):
    info = T.parse_header(raw)
    tb, cs = info['T'], info['code_start']
    msgs, warns = [], []
    prev = cs
    for k, t in enumerate(tb):
        p = t + cs                                  # 记录头结束（= 尾部签名结尾）地址
        if p + 6 > len(raw) or raw[p:p + 2] != T.REC_HDR:
            warns.append('k=%d 记录头特征缺失 @0x%x' % (k, p))
            continue
        tail = raw[p - 18:p]
        if tail[:14] != TAIL_PREFIX or struct.unpack_from('<I', tail, 14)[0] != k:
            warns.append('k=%d 尾部签名/序号不符 @0x%x' % (k, p))
        text_end = p - 18
        text_start, body = T.find_text_start(raw, prev, text_end)
        speaker = voice = image = None
        decl_span = None
        if text_start is None:
            warns.append('k=%d 正文起点未找到' % k)
            text = None
        else:
            text = T._decode(body, 'cp932')
            for off, s in decls_in(raw, prev, text_start):
                c = classify(s)
                if c == 'name':
                    speaker = s
                    L = struct.unpack('<H', raw[off + 2:off + 4])[0]
                    decl_span = [off + 4, L]          # 人名声明串：内容起点 / 内容字节数（含末位 NUL）
                elif c == 'voice':
                    voice = s
                elif c == 'resource' and s.upper().startswith('PIC'):
                    image = s
        msgs.append({'index': k, 'kind': 'line', 'speaker': speaker, 'voice': voice,
                     'image': image, 'text': text, 'off': text_start, 'decl': decl_span,
                     'len': (len(body) if body else 0)})
        prev = p
    # 章节标题（op=0x12）不在消息表 T 内，但同为显示文本，单列提取（沿用 R 版判据）
    for t in T.find_title_records(raw, msgs):
        msgs.append({'index': t['index'], 'kind': 'title', 'speaker': None, 'voice': None,
                     'image': None, 'text': t['text'], 'off': t.get('offset'),
                     'len': t.get('len')})
    msgs.sort(key=lambda m: (m['off'] is None, m['off'] or 0))
    return info, msgs, warns


def main():
    stats = '--stats' in sys.argv
    out, spk, voc = {}, Counter(), Counter()
    fail = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = io.open(os.path.join(SRC, fn), 'rb').read()
        try:
            info, msgs, warns = parse(raw)
        except Exception as ex:                      # noqa: BLE001
            fail.append((fn, repr(ex)))
            continue
        out[fn] = {'code_start': info['code_start'], 'B': info['B'], 'labels': info['labels'],
                   'warnings': warns, 'messages': msgs}
        for m in msgs:
            if m['speaker']:
                spk[m['speaker']] += 1
            if m['voice']:
                voc[m['voice'][:3]] += 1
    io.open(os.path.join(PROJ, '语料', '台词.json'), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    total = sum(len(v['messages']) for v in out.values())
    withspk = sum(spk.values())
    warn = sum(len(v['warnings']) for v in out.values())
    print('剧本 %d；解析异常 %d；警告 %d' % (len(out), len(fail), warn))
    print('台词 %d 条；带说话人 %d 条（%.1f%%）' % (total, withspk, 100 * withspk / max(total, 1)))
    print('说话人 %d 种；语音前缀 %s' % (len(spk), voc.most_common(10)))
    if stats:
        print('\n说话人 Top 40:')
        for s, c in spk.most_common(40):
            print('   %-14s %5d' % (s, c))
        print('\n警告样例:')
        for fn, v in list(out.items()):
            if v['warnings']:
                print('  ', fn, v['warnings'][:3])
                break
    for f in fail[:5]:
        print('  FAIL', f)


if __name__ == '__main__':
    main()

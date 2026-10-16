# -*- coding: utf-8 -*-
r"""dump_after.py —— 我们没有翅膀 After Story（Lucifen/LPK1 · TOB0）剧情语料抽取器

用法：
    python dump_after.py            # 全量抽取 + 打印统计
产出：
    语料\原文\SCRIPT.LPK            原版归档副本（只读参照，勿改名——LPK key 由文件名派生）
    语料\原文\<条目名>              192 个条目的明文（172 .tob + 15 .sob + 5 数据文件）
    语料\台词.json                  {条目名: [{index,op,speaker,voice,text,off,len}, ...]}

说明：消息层解析复用《我们没有翅膀R》工程已验证的 tob_extract.py（TOB0 消息表 T[k] 判据，
实测 100% 成立），本脚本只负责批量落盘与统计，不修改任何原始字节。
"""
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
CORPUS = os.path.join(PROJ, '语料')
SRC_DIR = os.path.join(CORPUS, '原文')
R_TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
ORIG_LPK = r'D:\Gal\[Navel]我们没有翅膀 ~ AfterStory ~(GPT-4o translate)\SCRIPT.LPK'

sys.path.insert(0, R_TOOLS)
import lpk_patch as P          # noqa: E402
import tob_extract as T        # noqa: E402


def main():
    os.makedirs(SRC_DIR, exist_ok=True)
    # 1) 归档副本（文件名必须保持 SCRIPT.LPK）
    dst_lpk = os.path.join(SRC_DIR, 'SCRIPT.LPK')
    if not os.path.exists(dst_lpk):
        io.open(dst_lpk, 'wb').write(io.open(ORIG_LPK, 'rb').read())
        print('已复制原版 SCRIPT.LPK ->', dst_lpk)

    lp = P.load(dst_lpk)
    print('SCRIPT.LPK 条目数 =', lp['cnt'], ' flags=0x%02x' % lp['flags'])

    # 2) 落盘明文
    scripts = {}
    kinds = Counter()
    for name, num in lp['ents']:
        e = P.read_entry(lp, name)
        raw = e['plain']
        io.open(os.path.join(SRC_DIR, name), 'wb').write(raw)
        ext = name.rsplit('.', 1)[-1].lower()
        kinds[ext] += 1
        if raw[:4] in (b'TOB0', b'SOB0', b'SOB1'):
            scripts[name] = raw
    print('条目类型:', dict(kinds))

    # 3) 台词抽取
    data = {}
    fail = []
    for name in sorted(scripts):
        raw = scripts[name]
        if raw[:4] != b'TOB0':
            continue
        try:
            info, msgs, warns = T.parse_messages_bytes(raw)
        except Exception as ex:                      # noqa: BLE001
            fail.append((name, repr(ex)))
            continue
        data[name] = {
            'code_start': info['code_start'],
            'B': info['B'],
            'labels': info['labels'],
            'warnings': warns,
            'messages': [
                {'index': m['index'], 'op': m['op'], 'speaker': m['speaker'],
                 'voice': m['voice'], 'text': m['text'], 'off': m.get('offset'),
                 'len': m.get('len')}
                for m in msgs
            ],
        }
    io.open(os.path.join(CORPUS, '台词.json'), 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False, indent=1))

    total = sum(len(v['messages']) for v in data.values())
    chars = sum(len(m['text'] or '') for v in data.values() for m in v['messages'])
    warn = sum(len(v['warnings']) for v in data.values())
    spk = Counter(m['speaker'] for v in data.values() for m in v['messages'] if m['speaker'])
    print('剧本文件 %d 个；解析失败 %d；警告 %d' % (len(data), len(fail), warn))
    print('台词总条数 %d；正文字符 %d' % (total, chars))
    print('说话人有效条数 %d；不同说话人 %d 种' % (sum(spk.values()), len(spk)))
    print('说话人 Top 30:', spk.most_common(30))
    for f in fail[:5]:
        print('  FAIL', f)


if __name__ == '__main__':
    main()

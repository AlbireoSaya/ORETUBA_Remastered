# -*- coding: utf-8 -*-
"""extract_sob0.py —— Lucifen 「SOB0」脚本原文提取（《我们没有翅膀》本篇，ISSUE-20260917-14）

结构（依据引擎自带源码 `参照\\汉化源工程_ORE_TUBA_Chinese\\text\\lucifen\\lucifen.cpp` 逐行对齐实现）：

  [0x00] 'SOB0'
  [0x04] u32 table_size ；table_end = table_size + 0x08
  [0x08 .. table_end]  连续若干张「地址映射表」，每张 = u32 条数 + 条数×(u32 key, u32 value)
                       —— 第 5 张（下标 4）是**字符串指针表**：key=代码地址，value=字符串地址
  [table_end] u32 strings_start ; u32 strings_end
  [..]        header_end = 此处偏移；code_end = strings_start + header_end
  字节码区 [header_end, code_end)：每条指令 4 字节，
      若 (cmd & 0xFFF00000) ∈ {0x01800000, 0x01700000} 且 maps[4] 命中该地址（值落在
      [strings_start, strings_end) 内），则该指令引用一段文本。

字符串的取法（与 lucifen.cpp 完全一致，含选择支的附加串）：
      p = maps[4][addr] + header_end
      c = data[p] ；c==0 → p += 3 ；否则 p 不动
      f = data[p] ；f ∈ {2,3} → p += 4 且 isselect = f-1 ；否则 p 不动
      从 p 起读到 NUL = 第 1 串；随后每个附加串「跳过 2 字节再读到 NUL」。

输出：
  工程\\我们没有翅膀\\语料\\原文\\<脚本名>.jsonl  —— 每行一个文本槽（原文顺序）
  工程\\我们没有翅膀\\语料\\原文\\_汇总.json      —— 全库统计
用法：
  python -X utf8 extract_sob0.py [--dump-sob] [--only 脚本名]
"""
import os
import sys
import json
import struct
import argparse
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)                       # 工程\我们没有翅膀
TOOLS_R = HERE
sys.path.insert(0, TOOLS_R)
import lpk_patch as LP  # noqa: E402

GAME = r'D:/Gal/壌偨偪偵梼偼側偄乣Prelude乣'
OUT_DIR = os.path.join(PROJ, '语料', '原文')
SOB_DIR = os.path.join(PROJ, '解包', 'SCRIPT')

TEXT_CMDS = (0x01800000, 0x01700000)


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def read_nul(d, p):
    e = d.find(b'\x00', p)
    if e < 0:
        e = len(d)
    return d[p:e], e + 1


def parse_sob0(d):
    """返回 (texts, info)。texts = [dict(addr, cmd, sel, idx, raw_bytes)]"""
    if d[:4] != b'SOB0':
        return None, None
    table_size = u32(d, 4)
    table_end = table_size + 8
    off = 8
    maps = []
    while off < table_end:
        n = u32(d, off)
        off += 4
        m = {}
        for _ in range(n):
            m[u32(d, off)] = u32(d, off + 4)
            off += 8
        maps.append(m)
    if len(maps) < 5:
        return None, {'err': 'maps<5 (%d)' % len(maps)}
    strings_start = u32(d, off)
    strings_end = u32(d, off + 4)
    header_end = off + 8
    code_end = strings_start + header_end
    strmap = maps[4]

    texts = []
    for addr in range(0, max(0, code_end - header_end), 4):
        v = strmap.get(addr)
        if v is None or not (strings_start <= v < strings_end):
            continue
        cmd = u32(d, header_end + addr)
        if (cmd & 0xFFF00000) not in TEXT_CMDS:
            continue
        p = v + header_end
        if p >= len(d):
            continue
        c = d[p]
        p = p + 3 if c == 0 else p
        sel = 0
        if p < len(d):
            f = d[p]
            if f in (2, 3):
                p += 4
                sel = f - 1
        raw, p = read_nul(d, p)
        texts.append(dict(addr=addr, cmd=cmd, sel=sel, idx=0, raw=raw))
        for k in range(sel):
            p += 2
            raw, p = read_nul(d, p)
            texts.append(dict(addr=addr, cmd=cmd, sel=sel, idx=k + 1, raw=raw))
    return texts, dict(maps=len(maps), strings=(strings_start, strings_end),
                       header_end=header_end, entries=len(strmap))


def classify(raw):
    """把原始串拆成 (类别, 说话人标签, 语音ID, 正文)。"""
    if b'$&' in raw:
        head, body = raw.split(b'$&', 1)
        if body.endswith(b'$'):
            body = body[:-1]
        spk, voice = '', ''
        if head.startswith(b'#'):
            h = head[1:]
            if b'\\' in h:
                sp, vo = h.split(b'\\', 1)
                spk = sp.decode('cp932', 'replace')
                voice = vo.decode('cp932', 'replace')
            else:
                spk = h.decode('cp932', 'replace')
        return 'dialogue', spk, voice, body
    # 纯参数/资源路径（全 ASCII）不当作剧情
    try:
        raw.decode('ascii')
        return 'ascii', '', '', raw
    except UnicodeDecodeError:
        pass
    return 'other', '', '', raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump-sob', action='store_true', help='同时把 .sob 解包到 解包\\SCRIPT\\')
    ap.add_argument('--only')
    a = ap.parse_args()

    lp = LP.load(os.path.join(GAME, 'SCRIPT.LPK'))
    os.makedirs(OUT_DIR, exist_ok=True)
    if a.dump_sob:
        os.makedirs(SOB_DIR, exist_ok=True)

    summary = dict(scripts={}, totals=collections.Counter(), chars=collections.Counter())
    all_speakers = collections.Counter()
    voices = collections.Counter()
    scripts = [(n, num) for n, num in lp['ents'] if n.lower().endswith('.sob')]
    scripts.sort()
    for name, num in scripts:
        if a.only and name != a.only:
            continue
        plain = LP.read_entry(lp, name)['plain']
        if a.dump_sob:
            open(os.path.join(SOB_DIR, name), 'wb').write(plain)
        texts, info = parse_sob0(plain)
        if texts is None:
            summary['scripts'][name] = dict(info=info, error='not SOB0')
            continue
        rows = []
        for t in texts:
            kind, spk, voice, body = classify(t['raw'])
            body_s = body.decode('cp932', 'replace')
            rows.append(dict(seq=len(rows), addr=t['addr'], cmd='%08X' % t['cmd'],
                             sel=t['sel'], idx=t['idx'], kind=kind,
                             speaker=spk, voice=voice, body=body_s,
                             raw_len=len(t['raw'])))
            summary['totals'][kind] += 1
            if kind == 'dialogue':
                all_speakers[spk] += 1
                voices[voice] += 1
                summary['chars']['dialogue'] += len(body_s)
            else:
                summary['chars'][kind] += len(body_s)
        with open(os.path.join(OUT_DIR, name + '.jsonl'), 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        summary['scripts'][name] = dict(info=info, slots=len(rows))

    summary['totals'] = dict(summary['totals'])
    summary['chars'] = dict(summary['chars'])
    summary['speakers'] = dict(all_speakers.most_common())
    summary['voices_n'] = len(voices)
    with open(os.path.join(OUT_DIR, '_汇总.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT_DIR, '_说话人.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(all_speakers.most_common()), f, ensure_ascii=False, indent=1)

    print('脚本数 =', len(scripts))
    print('槽位分类 =', summary['totals'])
    print('正文字符数 =', summary['chars'])
    print('说话人种类 =', len(all_speakers))
    print('语音 ID 种类 =', len(voices))
    print('输出目录 =', OUT_DIR)
    top = ', '.join('%s(%d)' % (k, v) for k, v in all_speakers.most_common(12))
    print('高频说话人 =', top)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

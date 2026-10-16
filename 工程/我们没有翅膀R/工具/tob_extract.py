# -*- coding: utf-8 -*-
r"""tob_extract.py —— Lucifen「TOB0」剧情脚本语义级文本提取器（ISSUE-ORETUBAR-R）

格式模型（全部经实测验证，418 文件 / 58042 条消息）：

  [0x00] 'TOB0'
  [0x04] u32  标签段大小 = (标签段结束偏移) - 4
  [0x08] u32  标签条数 n
          n × { u8 entry_len; name[entry_len-5]; 0x00; u32 addr }
                 entry_len = len(name)+1+4
  [???]  u32 A; u32 B; B × u32 T     其中 A == 8 + 4*B
  [???]  代码区起点 code_start

  * 地址空间 = 文件内偏移 - code_start（标签值、T 值、跳转目标都在此空间）。
  * T[k] = 第 k 条消息的「结束地址」；消息记录的结构恒为

        <正文原始 SJIS 字节>                      ← 无长度字段、无 NUL 终止
        5b 20 0c 00 00 00 01 0b 00 00 00 01 01 00 <u32 k>   ← 尾部 18 字节

    即正文结束位置 = T[k] + code_start - 18，尾部末 4 字节 == 消息序号 k
    （实测 58042/58042 全部成立，是判定「这是台词」的硬证据）。
  * 消息记录头（正文之前）：

        5b 20 <op> 00 00 00  01 <u32 arg>  <u8 typ>  <载荷...>

    op=0x19 为「有名字的角色台词」：载荷 = 名字串 [语音串] 正文；
        名字/语音串格式 01 01 <u16 L(含 NUL)> <data> 00。
    其它 op（0x10、0x5b、0x51、0x12 ...）为旁白/标题等，载荷不含名字串。
  * 正文结束位置由 T 表确定，正文起点由「正文结束前的最后一个 0x00 之后」
    给出（并做 SJIS 合法性校验）；op=0x19 时另用串链解析交叉验证。

用法：
  python -X utf8 tob_extract.py <tob文件或目录> [--json 输出.json] [--samples N]
                               [--dump 文件前缀] [--quiet]
"""
import os
import sys
import json
import struct

SJIS_LEAD = set(range(0x81, 0xA0)) | set(range(0xE0, 0xFD))

TAIL_PREFIX = b'\x5b\x20\x0c\x00\x00\x00\x01\x0b\x00\x00\x00\x01\x01\x00'
REC_HDR = b'\x5b\x20'


def sjis_len_ok(b):
    """判断字节串是否为「可显示的 SJIS」：不含控制字符（0x00-0x1F 除换行外）。"""
    i, n = 0, len(b)
    if n == 0:
        return True
    while i < n:
        c = b[i]
        if c == 0x00:
            return False
        if 0x20 <= c <= 0x7E:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif c in SJIS_LEAD:
            if i + 1 >= n:
                return False
            t = b[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return False
            i += 2
        else:
            return False
    return True


def decode_sjis(b):
    try:
        return b.decode('cp932')
    except Exception:
        return None


def _decode(b, enc='cp932'):
    try:
        return b.decode(enc)
    except Exception:
        return None


def valid_sjis_plain(b):
    """宽松校验（供串池扫描用）：允许控制字符。"""
    i, n = 0, len(b)
    while i < n:
        c = b[i]
        if c <= 0x7F:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif c in SJIS_LEAD:
            if i + 1 >= n:
                return False
            t = b[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return False
            i += 2
        else:
            return False
    return True


class TobFormatError(Exception):
    pass


def parse_header(d):
    """解析 TOB0 头部。返回 dict(labels, T, code_start)。"""
    if d[:4] != b'TOB0':
        raise TobFormatError('magic 不是 TOB0')
    label_size = struct.unpack_from('<I', d, 4)[0]
    nlab = struct.unpack_from('<I', d, 8)[0]
    p = 0x0c
    labels = []
    for _ in range(nlab):
        if p >= len(d):
            raise TobFormatError('标签段越界')
        ln = d[p]
        if ln < 5 or p + 1 + ln > len(d):
            raise TobFormatError('标签长度非法: %d' % ln)
        name = d[p + 1:p + 1 + ln - 4]
        if name[-1:] != b'\x00':
            raise TobFormatError('标签未以 NUL 结束')
        addr = struct.unpack_from('<I', d, p + ln - 3)[0]
        try:
            nm = name[:-1].decode('cp932')
        except Exception:
            nm = repr(name[:-1])
        labels.append((nm, addr))
        p += 1 + ln
    if p - 4 != label_size:
        # 兼容：不以 label_size 为准的话也无妨，继续
        pass
    if p + 8 > len(d):
        raise TobFormatError('缺少映射段')
    A = struct.unpack_from('<I', d, p)[0]
    B = struct.unpack_from('<I', d, p + 4)[0]
    if A != 8 + 4 * B:
        raise TobFormatError('映射段自述大小不符: A=%d B=%d' % (A, B))
    T = list(struct.unpack_from('<%dI' % B, d, p + 8))
    code_start = p + 8 + 4 * B
    return {'labels': labels, 'T': T, 'code_start': code_start, 'B': B,
            'map_pos': p, 'label_end': p}


def plausible_text(raw):
    """排除结构字节凑出的「假正文」：必须是可显示文本，且不是 1-2 字节的 ASCII 残渣。"""
    if not raw:
        return False
    has_high = any(b >= 0x80 for b in raw)
    if has_high:
        return True
    return len(raw) >= 6


def forward_parse_end(d, start, limit):
    """从 start 正向解析「可显示 SJIS」串，返回解析到的位置（不超过 limit）；
    遇到不可显示字节即停。"""
    i = start
    n = min(limit, len(d))
    while i < n:
        c = d[i]
        if 0x20 <= c <= 0x7E:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif c in SJIS_LEAD:
            if i + 1 >= n:
                return i
            t = d[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return i
            i += 2
        else:
            return i
    return i


def find_text_start(d, lo, text_end):
    """正文起点：窗口内「最早能恰好解析到 text_end 的可显示 SJIS 起点」。

    结构字节（0x00/0x01/0xff 等）不可显示，会切断解析，因此：
      - 正文前是串终止 NUL 时，起点即 NUL 之后；
      - 正文前是 `ff ff ff ff` 之类时，起点即这些字节之后。
    这样既避免把结构字节吞进正文，也不会因 SJIS 双字节边界歧义而截断正文。
    返回 (start, raw) 或 (None, None)。
    """
    for p in range(lo, text_end):
        e = forward_parse_end(d, p, text_end)
        if e == text_end:
            raw = d[p:text_end]
            if plausible_text(raw):
                return p, raw
    return None, None


def peel_trailing_commands(d, lo, e):
    """剥掉正文与尾部之间的「无载荷命令记录」：5b 20 op 00 00 00 01 <u32> 00。

    实测：个别消息正文后跟有 12 字节命令（如 op=0x0e），其后才是 18 字节尾部。
    这些命令必含 0x00（正文不可能含），故剥离是安全的。
    """
    peeled = 0
    while e - 12 >= lo:
        seg = d[e - 12:e]
        if (seg[0] == 0x5b and seg[1] == 0x20 and seg[3:6] == b'\x00\x00\x00'
                and seg[6] == 0x01 and seg[7:10] == b'\x00\x00\x00'
                and seg[11] == 0x00):
            e -= 12
            peeled += 1
        else:
            break
    return e, peeled


def parse_string(d, i):
    """01 01 <u16 L> <data 含 NUL>；返回 (next, text)。"""
    if i + 4 > len(d) or d[i] != 1 or d[i + 1] != 1:
        return None
    L = struct.unpack_from('<H', d, i + 2)[0]
    if L < 1 or i + 4 + L > len(d):
        return None
    blob = d[i + 4:i + 4 + L]
    if blob[-1] != 0x00 or not valid_sjis_plain(blob[:-1]):
        return None
    s = decode_sjis(blob[:-1])
    if s is None:
        return None
    return i + 4 + L, s


def is_voice_id(s):
    """语音 ID 判断：ASCII 大写字母/数字，长度 4-16（如 KAZ1086 / Y131002 / SYU0001）。"""
    if not (4 <= len(s) <= 16):
        return False
    return all(c.isalnum() or c == '_' for c in s) and any(c.isalpha() for c in s) \
        and all(ord(c) < 0x80 for c in s)


def parse_messages(path, strict=True, enc='cp932'):
    """解析一个 .tob 文件，返回 (info, messages, warnings)。"""
    return parse_messages_bytes(open(path, 'rb').read(), strict, enc)


def parse_messages_bytes(d, strict=True, enc='cp932'):
    """解析一段 TOB0 字节，返回 (info, messages, warnings)。enc 为正文解码编码。"""
    info = parse_header(d)
    T, code_start, B = info['T'], info['code_start'], info['B']
    n = len(d)
    msgs = []
    warns = []
    prev_end = code_start
    for k, t in enumerate(T):
        p = t + code_start
        if p + 6 > n or d[p:p + 2] != REC_HDR or d[p + 3:p + 6] != b'\x00\x00\x00':
            warns.append('k=%d 消息结束位置 0x%x 无命令特征' % (k, p))
            if strict:
                continue
        tail = d[p - 18:p]
        if len(tail) != 18 or tail[:14] != TAIL_PREFIX:
            warns.append('k=%d 尾部 18 字节模式不符 @0x%x' % (k, p - 18))
        elif struct.unpack_from('<I', tail, 14)[0] != k:
            warns.append('k=%d 尾部索引 != k (%d)' % (k, struct.unpack_from('<I', tail, 14)[0]))
        text_end = p - 18
        text_end, peeled = peel_trailing_commands(d, prev_end, text_end)
        if peeled:
            warns.append('k=%d 正文后剥离 %d 条无载荷命令' % (k, peeled))
        text_start, raw = find_text_start(d, prev_end, text_end)
        if text_start is None:
            msgs.append({'index': k, 'offset': None, 'len': 0, 'op': None,
                         'speaker': '', 'voice': '', 'text': '', 'error': 'text_start 未找到'})
            prev_end = p
            continue
        text = _decode(raw, enc)
        if text is None:
            warns.append('k=%d 正文解码失败 @0x%x' % (k, text_start))
            text = raw.decode('cp932', errors='replace')
        # 找记录头：窗口 [prev_end, text_start) 内最后一个 `5b 20 op 00 00 00 ...`
        rec = None
        j = text_start - 6
        while j >= prev_end:
            if d[j] == 0x5b and d[j + 1] == 0x20 and d[j + 3:j + 6] == b'\x00\x00\x00' \
               and j + 12 <= n and d[j + 6] == 0x01:
                rec = j
                break
            j -= 1
        op = None
        speaker = ''
        voice = ''
        if rec is not None:
            op = d[j + 2]
            N = struct.unpack_from('<I', d, j + 7)[0]
            # 记录头后是 typ 字节，其后可能跟着若干「串」
            q = j + 12
            strs = []
            while True:
                r = parse_string(d, q)
                if not r:
                    break
                q, s = r
                strs.append(s)
            if op == 0x19 and strs:
                # 串链结束处即正文起点（正文不可能含控制字节，故贪婪解析安全）
                raw2 = d[q:text_end]
                if valid_sjis_plain(raw2) and sjis_len_ok(raw2) and plausible_text(raw2):
                    text_start, raw = q, raw2
                    text = _decode(raw, enc)
                elif is_voice_id(strs[0]) and not (len(strs) >= 2 and not is_voice_id(strs[1])):
                    # 首个即语音 ID（无名字的台词）
                    voice = strs[0]
                    strs = []
                if strs:
                    speaker = strs[0]
                    for s in strs[1:]:
                        if is_voice_id(s):
                            voice = s
                            break
        msgs.append({'index': k, 'offset': text_start, 'len': text_end - text_start,
                     'op': op, 'speaker': speaker, 'voice': voice, 'text': text})
        prev_end = p
    # 补充：op=0x12（章节标题）记录里的串不在消息表内，但同为显示文本，单列提取
    for t in find_title_records(d, msgs):
        msgs.append(t)
    return info, msgs, warns


TITLE_OP = 0x12


def find_title_records(d, msgs):
    """扫描 `5b 20 12 00 00 00 01 <u32> <typ> 01 01 <u16 L> <data 00>` 标题串。

    这些串不在消息表 T 里（不参与消息序号），但会被显示（章节标题卡），
    且带显式长度前缀，边界天然精确。返回附加条目列表。
    """
    n = len(d)
    covered = [(m['offset'], m['offset'] + m['len']) for m in msgs if m.get('offset')]
    out = []
    i = 0
    while True:
        i = d.find(b'\x5b\x20' + bytes([TITLE_OP]) + b'\x00\x00\x00\x01', i)
        if i < 0 or i + 18 > n:
            break
        q = i + 12            # 跳过 typ 字节，串从这里开始
        # typ 后可能还有 01 <u32> 等字段，向后找 01 01 <u16 L> 串
        j = q
        got = False
        while j < min(q + 40, n - 4):
            r = parse_string(d, j)
            if r:
                end, txt = r
                data_off = j + 4
                inside = any(a <= data_off < b for a, b in covered)
                if not inside and txt.strip():
                    out.append({'index': None, 'offset': data_off, 'len': end - data_off - 1,
                                'op': TITLE_OP, 'speaker': '', 'voice': '', 'text': txt,
                                'kind': 'title', 'extra': True})
                got = True
                j = end
                continue
            # 允许 0x01 <u32> 这类字段跳过（5 字节）
            if d[j] == 0x01 and j + 5 <= n:
                j += 5
                continue
            break
        i += 1
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    target = args[0]
    out_json = None
    dump_prefix = None
    show_samples = 20
    quiet = '--quiet' in args
    if '--json' in args:
        out_json = args[args.index('--json') + 1]
    if '--dump' in args:
        dump_prefix = args[args.index('--dump') + 1]
    if '--samples' in args:
        show_samples = int(args[args.index('--samples') + 1])

    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in sorted(os.listdir(target))
                 if f.lower().endswith('.tob')]
    else:
        files = [target]

    all_rows = []
    stats = {'files': 0, 'files_fail': [], 'msgs': 0, 'warns': 0, 'empty': 0,
             'dialogue': 0, 'narration': 0, 'named': 0, 'voiced': 0, 'ops': {}}
    for p in files:
        try:
            info, msgs, warns = parse_messages(p)
        except Exception as e:
            stats['files_fail'].append((os.path.basename(p), str(e)))
            continue
        stats['files'] += 1
        stats['warns'] += len(warns)
        fname = os.path.basename(p)
        for m in msgs:
            stats['msgs'] += 1
            op = m.get('op')
            stats['ops'][op] = stats['ops'].get(op, 0) + 1
            if op == 0x19:
                stats['dialogue'] += 1
            else:
                stats['narration'] += 1
            if m.get('speaker'):
                stats['named'] += 1
            if m.get('voice'):
                stats['voiced'] += 1
            if not m.get('text'):
                stats['empty'] += 1
            row = {'file': fname, 'index': m['index'], 'offset': m['offset'],
                   'len': m['len'], 'op': op, 'speaker': m.get('speaker', ''),
                   'voice': m.get('voice', ''), 'text': m.get('text', ''),
                   'kind': m.get('kind') or ('dialogue' if op == 0x19 else 'narration')}
            if m.get('extra'):
                row['extra'] = True
            if 'error' in m:
                row['error'] = m['error']
            all_rows.extend([row])

    print('文件数: %d  解析失败: %d' % (stats['files'], len(stats['files_fail'])))
    for fn, err in stats['files_fail']:
        print('  [失败] %s: %s' % (fn, err))
    print('消息槽总数: %d  平均每文件: %.1f' % (stats['msgs'], stats['msgs'] / max(1, stats['files'])))
    print('  台词(op=0x19): %d   旁白/其他: %d' % (stats['dialogue'], stats['narration']))
    print('  有名字: %d   有语音: %d   空文本: %d   结构警告: %d'
          % (stats['named'], stats['voiced'], stats['empty'], stats['warns']))
    print('  op 分布: %s' % dict(sorted(stats['ops'].items(), key=lambda kv: -kv[1])[:12]))
    if out_json:
        with open(out_json, 'w', encoding='utf-8') as fp:
            json.dump(all_rows, fp, ensure_ascii=False, indent=1)
        print('JSON 已写出: %s (%d 条)' % (out_json, len(all_rows)))
    if dump_prefix:
        cnt = 0
        for r in all_rows:
            if not r['text']:
                continue
            print('%-14s k=%-4s off=%-8s len=%-4d op=0x%02x %-12s %-8s | %s'
                  % (r['file'], r['index'],
                     ('0x%05x' % r['offset']) if r['offset'] is not None else '-',
                     r['len'], r['op'] or 0,
                     r['speaker'][:12], r['voice'][:8], r['text'].replace('\n', '\\n')[:70]))
            cnt += 1
            if cnt >= show_samples:
                break
    return 0


if __name__ == '__main__':
    sys.exit(main())

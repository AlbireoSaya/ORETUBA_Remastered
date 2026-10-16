# -*- coding: utf-8 -*-
r"""TOB0/SOB0 串池扫描器：定位「长度前缀 + Shift-JIS 串 + NUL」结构。

实测结构（s00_00.tob）：
    1b 00 | 8f 98 95 b6 81 40 ... 81 60 | 00
    ^len=0x1b                        ^SJIS 27 字节      ^NUL 终止
即 [u8 len][len 字节 SJIS][u8 0x00]。长度字段即串字节数（不含终止 NUL）。
"""
import os, sys, json

SJIS_LEAD = set(range(0x81, 0xA0)) | set(range(0xE0, 0xF0))
HALFWIDTH_CATS = {0x0A, 0x0D, 0x20}          # 换行/回车/空格（SJIS 半角）


def decode_sjis(b: bytes):
    try:
        return b.decode('cp932')
    except Exception:
        return None


def valid_sjis(b: bytes) -> bool:
    """严格校验：整串是合法的 SJIS 字节序列，且不含控制字符。

    SJIS 结构：单字节 0x00-0x7F / 0xA1-0xDF；
              双字节 lead 0x81-0x9F,0xE0-0xEF + trail 0x40-0x7E,0x80-0xFC。
    不用黑名单 —— 长度字节的取值空间与内容字节重叠，只能靠整串合法性区分。
    """
    i, n = 0, len(b)
    if n == 0:
        return False
    while i < n:
        c = b[i]
        if c <= 0x7F:
            i += 1
        elif 0xA1 <= c <= 0xDF:
            i += 1
        elif (0x81 <= c <= 0x9F) or (0xE0 <= c <= 0xEF):
            if i + 1 >= n:
                return False
            t = b[i + 1]
            if not (0x40 <= t <= 0x7E or 0x80 <= t <= 0xFC):
                return False
            i += 2
        else:
            return False
    return True


def scan_strings(data: bytes, min_len=2, start=0):
    """扫描所有 [len][bytes][NUL] 结构，要求内容是可打印 SJIS 且含日文字形。

    实测：串前常有一枚 0x00 填充字节（即 [0x00][len][...][0x00]），但并非绝对，
    故扫描时不依赖前缀字节，只按 [len][bytes][NUL] 匹配。
    """
    out = []
    n = len(data)
    i = start
    while i < n - 3:
        ln = data[i]
        if min_len <= ln <= 250 and i + 1 + ln < n:
            blob = data[i + 1:i + 1 + ln]
            if data[i + 1 + ln] == 0x00 and valid_sjis(blob):
                s = decode_sjis(blob)
                if s is not None and s.strip():
                    out.append((i, ln, s))
                    i += 1 + ln + 1
                    continue
        i += 1
    return out


def is_japanese(s: str) -> bool:
    """是否有假名或汉字（用于区分台词与文件名/标识符）。"""
    for ch in s:
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF or 0xFF66 <= o <= 0xFF9F:
            return True
    return False


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print('用法: tob_strings.py <文件或目录> [--json 输出路径] [--dump 前N条]')
        sys.exit(2)
    target = sys.argv[1]
    dump_n = 20
    if '--dump' in sys.argv:
        dump_n = int(sys.argv[sys.argv.index('--dump') + 1])

    files = []
    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in sorted(os.listdir(target))
                 if f.lower().endswith(('.tob', '.sob'))]
    else:
        files = [target]

    total = 0
    jp_total = 0
    all_rows = []
    for p in files:
        data = open(p, 'rb').read()
        ss = scan_strings(data)
        jp = [(o, l, s) for o, l, s in ss if is_japanese(s)]
        total += len(ss)
        jp_total += len(jp)
        all_rows.extend({'file': os.path.basename(p), 'offset': o, 'len': l, 'text': s} for o, l, s in jp)

    print('文件数: %d' % len(files))
    print('扫描到的 [len][str][NUL] 结构: %d' % total)
    print('其中含日文字形（台词候选）: %d' % jp_total)

    if files and len(files) == 1:
        print()
        print('--- %s 的日文串（偏移 / 长度 / 内容）---' % os.path.basename(files[0]))
        for r in all_rows[:dump_n]:
            print('  %06x  len=%3d  %s' % (r['offset'], r['len'], r['text'].replace('\n', '\\n')))

    if '--json' in sys.argv:
        dst = sys.argv[sys.argv.index('--json') + 1]
        json.dump(all_rows, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('JSON 已写出:', dst)


if __name__ == '__main__':
    main()

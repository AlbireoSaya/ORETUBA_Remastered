# -*- coding: utf-8 -*-
r"""Lucifen SOB/TOB 文本提取与回写工具（ISSUE-ORETUBAR-R）

格式（实测于 R 版 .tob 与参照汉化 .sob）：
  脚本数据区内每条命令以 b'#' 开头，形如
      #<说话人>\<语音ID>$&<正文>$        （有语音）
      #<说话人>$&<正文>$                 （无语音）
      #\<语音ID>$&<正文>$                （旁白+语音，说话人字段为「声」）
      #<说话人>$<正文>$                  （无 $& 分隔时的退化形）
  正文字符串以 Shift-JIS 存储，命令串以 b'$' 结尾。

本模块只做「字节级定位 + 就地替换」，不重排脚本结构，保证回写后偏移与长度语义不变。
"""
import os, re, sys, struct, json

CMD_RE = re.compile(rb'#[^\x00$]{0,60}?\$&\$?[^\x00]*?\$', re.S)
ALT_RE = re.compile(rb'#[^\x00$]{0,40}?\$[^\x00]*?\$', re.S)


def split_components(raw: bytes):
    """把一条命令串拆成 (说话人, 语音ID, 正文)。输入含首尾 b'#' / b'$'。"""
    s = raw
    if s.startswith(b'#'):
        s = s[1:]
    if s.endswith(b'$'):
        s = s[:-1]
    speaker = b''
    voice = b''
    text = s
    if b'$&' in s:
        meta, text = s.split(b'$&', 1)
    elif b'$' in s:
        meta, text = s.split(b'$', 1)
    else:
        meta, text = s, b''
    if b'\\' in meta:
        sp, vo = meta.split(b'\\', 1)
        speaker, voice = sp.strip(), vo.strip()
    else:
        speaker = meta.strip()
    return speaker, voice, text


def sjis(b: bytes, errors='replace'):
    return b.decode('cp932', errors=errors)


def iter_commands(data: bytes):
    """产出 (start, end, raw) —— 结束位置为末尾 b'$' 之后。"""
    seen = set()
    for m in CMD_RE.finditer(data):
        if m.start() in seen:
            continue
        seen.add(m.start())
        yield m.start(), m.end(), m.group(0)
    for m in ALT_RE.finditer(data):
        if m.start() in seen:
            continue
        seen.add(m.start())
        yield m.start(), m.end(), m.group(0)


def extract_file(path, keep_empty=False):
    data = open(path, 'rb').read()
    rows = []
    for start, end, raw in iter_commands(data):
        speaker, voice, text = split_components(raw)
        t = sjis(text)
        if not t.strip() and not keep_empty:
            continue
        rows.append({
            'offset': start,
            'len': end - start,
            'speaker': sjis(speaker),
            'voice': sjis(voice),
            'text': t,
        })
    return data, rows


def translate_status(t: str):
    """粗判该槽是否已是中文（用于识别参照汉化里的未译残留）。"""
    cjk_cn = 0
    kana = 0
    for ch in t:
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF:
            kana += 1
        elif 0x4E00 <= o <= 0x9FFF:
            cjk_cn += 1
    return kana, cjk_cn


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 3:
        print('用法: lucifen_text.py <输入目录> <输出json> [--stats]')
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    stats = '--stats' in sys.argv

    files = sorted(f for f in os.listdir(src) if f.lower().endswith(('.tob', '.sob')))
    all_rows = []
    total_slots = 0
    untranslated = []
    for f in files:
        p = os.path.join(src, f)
        try:
            data, rows = extract_file(p)
        except Exception as e:
            print('[错误]', f, e)
            continue
        name = os.path.splitext(f)[0]
        for r in rows:
            r['file'] = f
            r['scene'] = name
        all_rows.extend(rows)
        total_slots += len(rows)
        if stats:
            # 统计仍有假名的槽（疑似未译）
            for r in rows:
                kana, cjk = translate_status(r['text'])
                if kana >= 3 and cjk >= 5:
                    untranslated.append((f, r['offset'], r['text'][:40]))

    with open(dst, 'w', encoding='utf-8') as fp:
        json.dump(all_rows, fp, ensure_ascii=False, indent=1)

    lines = []
    def P(*a):
        s = ' '.join(str(x) for x in a)
        print(s); lines.append(s)

    P('文件数: %d   文本槽总数: %d' % (len(files), total_slots))
    P('输出:', dst)
    if stats:
        P('疑似未译（含假名且含汉字）槽数: %d' % len(untranslated))
        for f, off, t in untranslated[:15]:
            P('   ', f, hex(off), t.replace('\n', ' '))
    open(os.path.join(os.path.dirname(dst), 'extract_log.txt'), 'w', encoding='utf-8').write('\n'.join(lines))


if __name__ == '__main__':
    main()

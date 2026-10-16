"""解析 5pb./MAGES. Tasktype ADV 脚本（纯文本，Shift-JIS），统计文本规模与结构。

用法: python parse_adv.py <脚本目录> [--dump-text out.txt]
"""
import os
import re
import sys
import json
import collections


HDR = re.compile(r'\[([A-Za-z_][A-Za-z0-9_]*)\][ \t]*\r?\n[ \t]*\{')


def parse_blocks(text, pos=0, end=None):
    """递归解析 [Section]{ ... } 结构，返回 [(name, body, nested_blocks)]。"""
    if end is None:
        end = len(text)
    out = []
    i = pos
    while i < end:
        m = HDR.search(text, i, end)
        if not m:
            break
        name = m.group(1)
        j = m.end() - 1
        depth = 0
        k = j
        while k < end:
            if text[k] == '{':
                depth += 1
            elif text[k] == '}':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        body = text[j + 1:k]
        # 只在 '{' 之后、第一个嵌套 header 之前找直属字段
        nm = HDR.search(body)
        direct = body[:nm.start()] if nm else body
        nested = parse_blocks(body, nm.start(), len(body)) if nm else []
        out.append((name, direct, nested))
        i = k + 1
    return out


def walk(blocks):
    """深度优先遍历，产出 (name, direct_body)。"""
    for name, direct, nested in blocks:
        yield name, direct
        for item in walk(nested):
            yield item


def field(body, key):
    m = re.search(r'^\s*:' + key + r'[ \t]+(.*)$', body, re.M)
    return m.group(1).strip() if m else None


def field_str(body, key):
    v = field(body, key)
    if v is None:
        return None
    m = re.match(r'^"(.*)"', v, re.S)
    return m.group(1) if m else v


def main():
    src = sys.argv[1]
    task_types = collections.Counter()
    msg_count = 0
    total_chars = 0
    voice_count = 0
    name_counter = collections.Counter()
    scene_name_counter = collections.Counter()
    texts = []
    files = sorted(os.listdir(src))
    for fn in files:
        p = os.path.join(src, fn)
        if not os.path.isfile(p):
            continue
        raw = open(p, 'rb').read()
        try:
            text = raw.decode('cp932')
        except UnicodeDecodeError:
            text = raw.decode('cp932', 'replace')
        for sec, body in walk(parse_blocks(text)):
            if not re.match(r'^Task\d+$', sec):
                continue
            tt = field_str(body, 'Tasktype')
            if not tt:
                continue
            task_types[tt] += 1
            if tt == 'Message':
                msg_count += 1
                t = field_str(body, 'Message')
                if t:
                    total_chars += len(t)
                    texts.append((fn, sec, t))
                if field_str(body, 'Voice'):
                    voice_count += 1
                nm = field_str(body, 'Name')
                if nm:
                    name_counter[nm] += 1
            elif tt == 'SetSceneName':
                t = field_str(body, 'SceneName') or field_str(body, 'Text')
                if t:
                    scene_name_counter[t] += 1

    print('脚本文件数:', len(files))
    print('Message 数:', msg_count)
    print('台词字符数:', total_chars)
    print('带 Voice 的 Message:', voice_count)
    print()
    print('Tasktype 分布:')
    for k, v in task_types.most_common():
        print('  %-26s %d' % (k, v))
    print()
    print('章节标题(SetSceneName) 数:', len(scene_name_counter), '示例:', list(scene_name_counter)[:15])
    print()
    print('名字框出现的 Name 前 25:')
    for k, v in name_counter.most_common(25):
        print('  %-18s %d' % (k, v))

    if '--dump-text' in sys.argv:
        out = sys.argv[sys.argv.index('--dump-text') + 1]
        with open(out, 'w', encoding='utf-8') as fh:
            for fn, sec, t in texts:
                fh.write('%s\t%s\t%s\n' % (fn, sec, t.replace('\n', '\\n')))
        print('\n已导出文本:', out, len(texts), '条')


if __name__ == '__main__':
    main()

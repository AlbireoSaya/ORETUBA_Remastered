# -*- coding: utf-8 -*-
"""analyze_lang.py —— 对 LPK 内脚本与外挂 SCRIPT_CHS 做可靠的语言判定（只读）

判别原理（避免「GBK 硬解把 SJIS 误判为汉字」这一常见错判）：
  1. 取文件中所有「非 ASCII 连续字节段」（长度 >= 4）。
  2. 对每段同时做 cp932 与 gbk 解码。
  3. 判定：
       - cp932 解出平假名 / 片假名            → JP（真日文）
       - gbk 解出 >= 2 个「SJIS 假名字节被 GBK 解码后的陷阱字符」→ JP（乱码，实为日文）
       - 其余                                  → CN（真 GBK 中文）
     陷阱字符集由代码生成：把全部假名字符 encode('cp932') 后再 decode('gbk')。
"""
import os
import re
import sys
import json
import collections

TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, TOOLS)
import lpk_patch as LP  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀\分析'

HIRA = re.compile('[\u3041-\u309f]')
KATA = re.compile('[\u30a1-\u30fa]')
NON_ASCII_RUN = re.compile(rb'(?:[\x80-\xff][\x20-\xff]){2,}')


def build_trap():
    """SJIS 假名 → GBK 解码后的陷阱字符集（乱码常见字）。"""
    trap = set()
    for cp in list(range(0x3041, 0x3097)) + list(range(0x30A1, 0x30FB)):
        try:
            b = chr(cp).encode('cp932')
        except Exception:  # noqa: BLE001
            continue
        try:
            s = b.decode('gbk')
        except Exception:  # noqa: BLE001
            continue
        for ch in s:
            if ch >= '\u3000':
                trap.add(ch)
    return trap


TRAP = build_trap()


def classify_run(b):
    """返回 ('JP'|'CN', 依据说明)。"""
    try:
        j = b.decode('cp932')
    except Exception:  # noqa: BLE001
        j = b.decode('cp932', errors='replace')
    kana = len(HIRA.findall(j)) + len(KATA.findall(j))
    if kana:
        return 'JP', 'cp932 解出假名 %d 个: %s' % (kana, j[:40])
    try:
        g = b.decode('gbk')
    except Exception:  # noqa: BLE001
        g = b.decode('gbk', errors='replace')
    n_trap = sum(1 for ch in g if ch in TRAP)
    if n_trap >= 2:
        return 'JP', 'GBK 解得假名陷阱字 %d 个: %s' % (n_trap, g[:40])
    return 'CN', 'GBK 解得中文: %s' % g[:40]


def file_stats(data):
    c = collections.Counter()
    examples = {}
    for m in NON_ASCII_RUN.finditer(data):
        b = m.group(0)
        if len(b) < 6:
            continue
        kind, why = classify_run(b)
        c[kind] += 1
        if kind not in examples:
            examples[kind] = (m.start(), why)
    return c, examples


def main():
    lp = LP.load(os.path.join(GAME, 'SCRIPT.LPK'))
    chs_dir = os.path.join(GAME, 'SCRIPT_CHS')

    print('=== A. SCRIPT.LPK 内条目语言判定 ===')
    tot = collections.Counter()
    mixed = []
    per_entry = []
    for name, num in sorted(lp['ents']):
        p = LP.read_entry(lp, name)['plain']
        c, ex = file_stats(p)
        tot.update(c)
        per_entry.append(dict(name=name, jp=c['JP'], cn=c['CN'], size=len(p)))
        if c['CN'] > 0:
            mixed.append((name, c['JP'], c['CN'], ex.get('CN')))
    print('  全 418 条目合计：JP 段 %d ／ CN 段 %d' % (tot['JP'], tot['CN']))
    print('  含「CN 判定」段的条目数：%d' % len(mixed))
    for name, jp, cn, ex in mixed[:15]:
        print('    - %-20s JP=%-6d CN=%-4d 例: %s' % (name, jp, cn, (ex[1][:70] if ex else '')))

    print('\n=== B. 外挂 SCRIPT_CHS 目录语言判定 ===')
    tot2 = collections.Counter()
    per_chs = []
    jp_files = []
    for fn in sorted(os.listdir(chs_dir)):
        path = os.path.join(chs_dir, fn)
        if not os.path.isfile(path):
            continue
        data = open(path, 'rb').read()
        c, ex = file_stats(data)
        tot2.update(c)
        per_chs.append(dict(name=fn, jp=c['JP'], cn=c['CN'], size=len(data)))
        jp_files.append((fn, c['JP'], c['CN']))
    print('  全 %d 文件合计：JP 段 %d ／ CN 段 %d' % (len(per_chs), tot2['JP'], tot2['CN']))
    jp_only = [t for t in jp_files if t[1] > 0 and t[2] == 0]
    most_jp = sorted(jp_files, key=lambda t: -t[1])[:15]
    print('  纯日文（无 CN 段）文件数：%d' % len(jp_only))
    print('  日文残留最多的 15 个文件：')
    for fn, jp, cn in most_jp:
        print('    - %-24s JP=%-6d CN=%-6d' % (fn, jp, cn))

    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(lpk_entries=per_entry, chs_files=per_chs),
              open(os.path.join(OUT, 'lang_stats.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n  明细已写:', os.path.join(OUT, 'lang_stats.json'))


if __name__ == '__main__':
    main()

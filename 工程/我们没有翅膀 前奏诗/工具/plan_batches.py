# -*- coding: utf-8 -*-
"""plan_batches.py —— 《我们没有翅膀 前奏诗》切分翻译批次

· 可译判定：台词（含 `$&`）+ 旁白/章节标题/系统提示（含假名或汉字）；排除纯 ASCII 资源串、
  纯 PUA 图标字形、字体名。
· 顺序：以 `解包\\SCRIPT\\sob_init.dat` 登记的顺序为准（该文件是引擎的脚本调度表，
  实测顺序为 P01→P02→P03→P04→02→03→buru），未登记的脚本排在其后按名排序。
· 交给译者的 `body` **剥掉结尾的结构性 `$`**（构建时按 `td` 标志回补），正文原样保留 `\\n`。
· 产出：`语料\\批次\\batch_NNN.tsv`（列：seq slot speaker voice kind td body）
         `语料\\批次\\_索引.json`
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, '语料', '原文')
OUT = os.path.join(PROJ, '语料', '批次')
MANIFEST = os.path.join(PROJ, '语料', '可译清单.json')
SOB_INIT = os.path.join(PROJ, '解包', 'SCRIPT', 'sob_init.dat')

KANA = re.compile('[\u3041-\u309f\u30a0-\u30fa]')
CJK = re.compile('[\u4e00-\u9fff]')
PUA = re.compile('[\ue000-\uf8ff]')
NON_TEXT = re.compile(r'^[A-Za-z0-9_\\./:%\- ]+$')
FONT = re.compile(r'^(ＭＳ|MS)\s*[ＰP]?(ゴシック|明朝|Gothic|Mincho)')


def load_order():
    """从 sob_init.dat 读出脚本调度顺序 -> {大写名: 序号}"""
    d = open(SOB_INIT, 'rb').read()
    pat = re.compile(rb'[\x20-\x7e]{3,}')
    order = {}
    for m in pat.finditer(d):
        t = m.group().decode('ascii').strip()
        if not re.fullmatch(r'[A-Za-z0-9_]{3,16}', t):
            continue
        if t not in order:
            order[t] = len(order)
    return order


def translatable(r):
    if r['kind'] == 'dialogue':
        return bool(r['body'].strip())
    if r['kind'] != 'other':
        return False
    b = r['body'].strip().rstrip('$').strip()
    if not b or FONT.match(b):
        return False
    core = PUA.sub('', b).strip()
    if not core or NON_TEXT.match(core):
        return False
    return bool(KANA.search(core) or CJK.search(core))


def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    order = load_order()
    BIG = 10 ** 6
    files = sorted(glob.glob(os.path.join(SRC, '*.jsonl')))
    rows = []
    for p in files:
        sc = os.path.basename(p)[:-6]
        if sc.startswith('_'):
            continue
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            r['script'] = sc
            if translatable(r):
                r['slot'] = '%s#%d' % (sc, r['seq'])
                body = r['body']
                r['td'] = 1 if body.endswith('$') else 0
                r['body'] = body[:-1] if r['td'] else body
                rows.append(r)
    rows.sort(key=lambda r: (order.get(r['script'][:-4].upper(), BIG), r['seq']))

    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, '*.tsv')):
        os.remove(f)
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump([{k: r[k] for k in ('script', 'seq', 'slot', 'addr', 'cmd', 'sel', 'idx',
                                      'kind', 'speaker', 'voice', 'td', 'body')} for r in rows],
                  f, ensure_ascii=False)

    batches, cur = [], []
    for r in rows:
        if len(cur) >= batch_size:
            batches.append(cur)
            cur = []
        cur.append(r)
    if cur:
        batches.append(cur)

    index = {}
    for i, b in enumerate(batches, 1):
        name = 'batch_%03d' % i
        with open(os.path.join(OUT, name + '.tsv'), 'w', encoding='utf-8', newline='') as f:
            f.write('seq\tslot\tspeaker\tvoice\tkind\ttd\tbody\n')
            for r in b:
                f.write('%d\t%s\t%s\t%s\t%s\t%d\t%s\n' % (
                    r['seq'], r['slot'], r['speaker'], r['voice'], r['kind'], r['td'],
                    r['body'].replace('\t', ' ').replace('\r', ' ').replace('\n', '\\n')))
        index[name] = dict(slots=len(b), chars=sum(len(r['body']) for r in b),
                           scripts=sorted({r['script'] for r in b}), status='pending')
    json.dump(index, open(os.path.join(OUT, '_索引.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print('可译槽位 = %d' % len(rows))
    print('可译字符 =', sum(len(r['body']) for r in rows))
    print('批次数 = %d（每批 <= %d 槽）' % (len(batches), batch_size))
    print('脚本顺序 =', list(dict.fromkeys(r['script'] for r in rows)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
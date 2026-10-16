"""收集《我们没有翅膀》PS Vita 版「林田美咲线」脚本引用到的全部资源，并解析到归档内文件。

美咲线 = M01_01..M09_02（M 前缀，M01_01 标题「美咲編オープニング」、M09「美咲編エピローグ」）
        + P03_01A..P03_01D（『ある日の美咲』四话）

解析依据（实测结论）：
  · ：Texture N 是「场景内局部编号」——602/1330 个编号在不同脚本里对应不同名字，
    因此**不能按编号解析**，必须按注释里烘焙的资源名解析。
  · 构建工具把符号名替换成了数字/元组，但把结果名留在注释里：
      ：Texture 533 // EF01                          → CG.cpk/ef01.png
      ：Texture 165 // ST_ASU01                       → CHR.cpk/ST_ASU01.png
      ：Number 12,0,1,7,0 // 置換しました<<st_mis01g>>  → CHR.cpk/ST_MIS01G.png
  · ：SE N / ：BGM N / ：Voice N 是**归档内索引**（SE 0..700↔701 条目、Voice 0..26499↔26500 条目完全吻合）。

用法: python collect_misaki_assets.py <脚本解包目录> <解密后 media 目录> <输出目录>
"""
import os
import re
import sys
import csv
import json
import collections

sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工具\pylibs')
from cricodecs import cpk as C  # noqa: E402

VOICE_LINE_RE = re.compile(r':Voice\s+(\d+)\s*(?://\s*(?:\S+\s+)?(\S+))?')
NAME_RE = re.compile(r'//\s*(.*)$', re.M)
ANGLE_RE = re.compile(r'<<([A-Za-z0-9_]+)>>')
TOKEN_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]{2,})')
IDX_FIELD_RE = re.compile(r':(SE|BGM|Voice)\s+(\d+)')


def is_misaki_route(fn):
    return bool(re.match(r'^M\d\d_\d\d$', fn)) or bool(re.match(r'^P03_01[A-Z]$', fn))


def collect(script_dir):
    """返回该线路所有脚本里出现的：注释名集合、索引引用、脚本清单。"""
    names = collections.Counter()          # 注释名 -> 出现次数
    idx = collections.defaultdict(collections.Counter)   # SE/BGM/Voice -> {编号: 次数}
    scripts = []
    for fn in sorted(os.listdir(script_dir)):
        p = os.path.join(script_dir, fn)
        if not os.path.isfile(p) or not is_misaki_route(fn):
            continue
        text = open(p, 'rb').read().decode('cp932', 'replace')
        titles = re.findall(r'//\s*(?:仮|正)タイトル[：:]\s*(.*)', text)
        scenes = re.findall(r':SceneName\s+"([^"]+)"', text)
        msgs = len(re.findall(r':Tasktype\s+"Message"', text))
        scripts.append({'file': fn, 'titles': [t.strip() for t in titles[:2]],
                        'scene_names': scenes[:4], 'messages': msgs,
                        'chars': len(text)})
        # 1) <<name>> 形式
        for m in ANGLE_RE.finditer(text):
            names[m.group(1).lower()] += 1
        # 2) // 注释行里的 ASCII token
        for m in NAME_RE.finditer(text):
            for t in TOKEN_RE.finditer(m.group(1)):
                tok = t.group(1)
                if tok.lower() in ('true', 'false', 'null', 'none'):
                    continue
                names[tok.lower()] += 1
        # 3) 索引引用
        for m in IDX_FIELD_RE.finditer(text):
            idx[m.group(1)][int(m.group(2))] += 1
    return names, idx, scripts


def main():
    script_dir, media, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)

    names, idx, scripts = collect(script_dir)
    print('美咲线脚本文件数:', len(scripts))
    print('   台词总数:', sum(s['messages'] for s in scripts))
    print('   注释名候选数:', len(names))
    for k in idx:
        print('   %-6s 引用编号 %d 种, 范围 %d..%d' % (k, len(idx[k]), min(idx[k]), max(idx[k])))

    # 建归档索引（cricodecs 不支持非 ASCII 路径，先 chdir）
    os.chdir(media)
    archive_files = {}
    for a in ['CG.cpk', 'CHR.cpk', 'SystemData.cpk', 'ETC.cpk']:
        c = C.load(a)
        for i, f in enumerate(c.files):
            archive_files.setdefault(os.path.splitext(f.filename)[0].upper(), []).append(
                {'archive': a, 'index': i, 'filename': f.filename, 'size': f.file_size})
    # media 根下的零散图片（logo 等）
    for sub in ['img/logo']:
        d = os.path.join(media, sub)
        if os.path.isdir(d):
            for fn in os.listdir(d):
                archive_files.setdefault(os.path.splitext(fn)[0].upper(), []).append(
                    {'archive': 'media/' + sub, 'index': -1, 'filename': fn,
                     'size': os.path.getsize(os.path.join(d, fn))})

    resolved, unresolved = [], []
    for nm, cnt in names.most_common():
        hits = archive_files.get(nm.upper())
        if hits:
            for h in hits:
                resolved.append({'name': nm, 'hits': cnt, **h})
        else:
            unresolved.append({'name': nm, 'hits': cnt})

    with open(os.path.join(outdir, '资源引用.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['name', 'hits', 'archive', 'index', 'filename', 'size'],
                           delimiter='\t')
        w.writeheader()
        for r in sorted(resolved, key=lambda x: (x['archive'], x['index'])):
            w.writerow(r)

    with open(os.path.join(outdir, '未解析名.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
        fh.write('name\t出现次数\n')
        for r in unresolved:
            fh.write('%s\t%d\n' % (r['name'], r['hits']))

    with open(os.path.join(outdir, '脚本清单.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
        fh.write('文件\t标题\tSceneName\t台词数\t字节\n')
        for s in scripts:
            fh.write('%s\t%s\t%s\t%d\t%d\n' % (s['file'], ' | '.join(s['titles']),
                                               ' | '.join(s['scene_names']), s['messages'], s['chars']))

    with open(os.path.join(outdir, '索引引用.json'), 'w', encoding='utf-8') as fh:
        json.dump({k: dict(v) for k, v in idx.items()}, fh, ensure_ascii=False, indent=1)

    print()
    print('已解析到归档内文件的名数:', len({r['name'] for r in resolved}))
    print('未能解析的名数:', len(unresolved))
    by_arch = collections.Counter(r['archive'] for r in resolved)
    for a, n in by_arch.most_common():
        print('   %-18s %d 处引用' % (a, n))
    print()
    print('未解析名（前 30，多为系统词/非资源标识）:')
    for r in unresolved[:30]:
        print('   %-24s %d' % (r['name'], r['hits']))


if __name__ == '__main__':
    main()

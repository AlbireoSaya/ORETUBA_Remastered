"""解析脚本中的资源引用（编号 + 注释名），反推「编号 → 归档内文件」的寻址规则。

用法: python resolve_asset_ids.py <脚本目录> <解密后的 media 目录>
"""
import os
import re
import sys
import json
import collections

sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工具\pylibs')
from cricodecs import cpk as C  # noqa: E402

MEDIA = sys.argv[2]
ARCHIVES = ['CG.cpk', 'CHR.cpk', 'SystemData.cpk', 'ETC.cpk']

# 收集脚本里的引用：字段名 -> {编号: Counter(注释名)}
FIELD_RE = re.compile(
    r':(Texture|SE|BGM|Voice|Image|Character|Movie)\s+([0-9,\-]+)\s*(?://\s*(.*))?$', re.M)


def strip_comment(c):
    """从注释里取第一个看起来像名字的 token。"""
    if not c:
        return None
    c = c.strip()
    if c.startswith('//'):
        c = c[2:].strip()
    m = re.match(r'([A-Za-z_][A-Za-z0-9_\-]*)', c)
    return m.group(1) if m else None


def main():
    script_dir = sys.argv[1]
    refs = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for fn in sorted(os.listdir(script_dir)):
        p = os.path.join(script_dir, fn)
        if not os.path.isfile(p):
            continue
        text = open(p, 'rb').read().decode('cp932', 'replace')
        for m in FIELD_RE.finditer(text):
            field, vals, comment = m.group(1), m.group(2), m.group(3)
            name = strip_comment(comment)
            for v in vals.split(','):
                if v.strip().isdigit():
                    refs[field][int(v)][name] += 1

    # 建归档索引（cricodecs 的 C++ 读取器不支持非 ASCII 路径，故先 chdir 再用纯名打开）
    os.chdir(MEDIA)
    index = {}
    for a in ARCHIVES:
        c = C.load(a)
        for i, f in enumerate(c.files):
            base = os.path.splitext(f.filename)[0]
            index.setdefault(base.upper(), []).append((a, i))

    print('=== 引用统计 ===')
    for field in sorted(refs):
        ids = refs[field]
        names = [n for v in ids.values() for n in v if n]
        print('%-10s 编号取值 %5d 种, 范围 %d..%d, 引用 %6d, 带注释名 %d'
              % (field, len(ids), min(ids), max(ids), sum(sum(v.values()) for v in ids.values()), len(names)))

    print()
    print('=== 索引对齐测试（注释名 → 归档内实际索引 vs 脚本编号）===')
    for field in ['Texture', 'SE', 'BGM', 'Voice', 'Movie']:
        if field not in refs:
            continue
        hit = miss = unknown = 0
        examples = []
        for n, cnt in refs[field].items():
            nm = next((k for k in cnt if k), None)
            if not nm:
                unknown += 1
                continue
            locs = index.get(nm.upper())
            if not locs:
                miss += 1
                continue
            hit += 1
            archives = {a for a, i in locs}
            idxs = {i for a, i in locs}
            if len(examples) < 6:
                examples.append((n, nm, sorted(archives), sorted(idxs), n in idxs))
        print('%-10s 注释名能在归档里找到 %d 个, 找不到 %d 个, 无注释 %d 个' % (field, hit, miss, unknown))
        for n, nm, arch, idxs, eq in examples:
            print('    编号 %-7d 名 %-16s 归档 %-22s 索引 %-12s 编号==索引: %s'
                  % (n, nm, ','.join(arch), str(idxs)[:12], eq))
        print()

    json.dump({f: {str(k): dict(v) for k, v in d.items()} for f, d in refs.items()},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'asset_refs.json'), 'w',
                   encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('已导出 asset_refs.json')


if __name__ == '__main__':
    main()

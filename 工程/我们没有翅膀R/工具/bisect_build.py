# -*- coding: utf-8 -*-
r"""二分定位构建器（ISSUE-ORETUBAR-R）。

用法：python -X utf8 bisect_build.py <文件清单 JSON 的键> [--out 名]
用给定文件清单（写在 语料\_bisect.json 里）构建只含这些文件翻译的 LPK，
部署到游戏目录，供实机二分测试。
"""
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP
import tob_rewrite as TR

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
OUT = os.path.join(WS, '临时', '_bisect', 'SCRIPT.LPK')


def main():
    key = sys.argv[1]
    bs = json.load(open(os.path.join(P, '语料', '_bisect.json'), encoding='utf-8'))
    want = set(bs[key])
    print('清单 %s: %d 个文件' % (key, len(want)))

    mig = json.load(open(os.path.join(P, '语料', 'R版迁移映射.json'), encoding='utf-8'))
    new = json.load(open(os.path.join(P, '语料', '新增译文映射.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(P, '语料', '重编码映射.json'), encoding='utf-8'))

    by = {}
    n = 0
    for r in mig + new:
        f = r['file']
        if f not in want:
            continue
        t = r.get('cn') or r.get('text') or ''
        if not t:
            continue
        try:
            b = t.encode('gbk')
        except Exception:
            continue
        by.setdefault(f, []).append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b})
        n += 1
    for r in rec:
        f = r['file']
        if f not in want:
            continue
        tb = r.get('text_bytes')
        b = bytes(tb) if isinstance(tb, list) else r.get('text_bytes_latin1', '').encode('latin-1')
        by.setdefault(f, []).append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b})
    print('译文 %d 条，涉及 %d 文件' % (n, len(by)))

    lpm = LP.load(MEDIA)
    edits = {}
    for f, lst in by.items():
        raw = LP.read_entry(lpm, f)['plain']
        lst = [e for e in lst if e['offset'] + e['len'] <= len(raw)]
        if not lst:
            continue
        try:
            nb, _, _ = TR.apply_edits_rebuild(raw, lst, verify=False)
        except Exception as ex:
            print('  [失败]', f, ex)
            continue
        if nb != raw:
            edits[f] = nb
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    info = LP.patch(MEDIA, OUT, edits)
    print('需替换 %d 条目；LPK %d -> %d' % (len(edits), info['in_size'], info['out_size']))
    # 标题
    import subprocess
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'patch_title2.py'), OUT],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('输出:', OUT, os.path.getsize(OUT))


if __name__ == '__main__':
    main()

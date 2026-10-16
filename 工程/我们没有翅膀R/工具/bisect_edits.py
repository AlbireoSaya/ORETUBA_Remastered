# -*- coding: utf-8 -*-
r"""按编辑条目二分（ISSUE-ORETUBAR-R）。

用法：
  python -X utf8 bisect_edits.py build           # 用 语料\_edit_subset.json 里的索引集构建并部署
  python -X utf8 bisect_edits.py pick first|last  # 把当前集合对半，取前/后半（写入 json）
  python -X utf8 bisect_edits.py show            # 显示当前集合摘要

集合以「s01_02c.tob 的编辑索引」表示（0..N-1），存于 语料\_edit_subset.json。
"""
import os, sys, json, shutil, subprocess

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP
import tob_rewrite as TR

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
SUBSET = os.path.join(P, '语料', '_edit_subset.json')
OUT = os.path.join(WS, '临时', '_bs', 'SCRIPT.LPK')
DEPLOY = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R', 'SCRIPT.LPK')
F = 's01_02c.tob'


def all_edits():
    """返回 (edits 列表（原始坐标，升序）, 元信息列表)。"""
    mig = json.load(open(os.path.join(P, '语料', 'R版迁移映射.json'), encoding='utf-8'))
    new = json.load(open(os.path.join(P, '语料', '新增译文映射.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(P, '语料', '重编码映射.json'), encoding='utf-8'))
    lst = []
    for r in mig + new:
        if r['file'] != F:
            continue
        t = r.get('cn') or r.get('text') or ''
        if not t:
            continue
        try:
            b = t.encode('gbk')
        except Exception:
            continue
        lst.append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b,
                    'src': 'tr', 'desc': t[:24]})
    for r in rec:
        if r['file'] != F:
            continue
        tb = r.get('text_bytes')
        b = bytes(tb) if isinstance(tb, list) else r.get('text_bytes_latin1', '').encode('latin-1')
        lst.append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b,
                    'src': 'rec', 'desc': r.get('text', '')[:24]})
    lst.sort(key=lambda e: e['offset'])
    return lst


def load_subset(n):
    if os.path.exists(SUBSET):
        d = json.load(open(SUBSET, encoding='utf-8'))
        if d.get('total') == n:
            return d['idx']
    idx = list(range(n))
    json.dump({'total': n, 'idx': idx, 'history': ['all']}, open(SUBSET, 'w', encoding='utf-8'))
    return idx


def save_subset(n, idx, hist_note):
    d = json.load(open(SUBSET, encoding='utf-8')) if os.path.exists(SUBSET) else {'history': []}
    d.update({'total': n, 'idx': sorted(idx)})
    d.setdefault('history', []).append(hist_note)
    json.dump(d, open(SUBSET, 'w', encoding='utf-8'))


def main():
    edits = all_edits()
    n = len(edits)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'show'

    if cmd == 'show':
        idx = load_subset(n)
        print('总编辑 %d 条；当前子集 %d 条' % (n, len(idx)))
        print('子集范围: %s .. %s' % (idx[0] if idx else '-', idx[-1] if idx else '-'))
        return

    if cmd == 'pick':
        idx = load_subset(n)
        if len(idx) <= 1:
            print('已收敛到单条：idx=%s' % idx); return
        h = len(idx) // 2
        which = sys.argv[2] if len(sys.argv) > 2 else 'first'
        idx = idx[:h] if which == 'first' else idx[h:]
        save_subset(n, idx, 'pick %s -> %d 条' % (which, len(idx)))
        print('新子集 %d 条: %s .. %s' % (len(idx), idx[0], idx[-1]))
        return

    if cmd == 'only':
        # only <i>  —— 只应用第 i 条
        i = int(sys.argv[2])
        save_subset(n, [i], 'only %d' % i)
        idx = [i]
    else:
        idx = load_subset(n)

    sub = [edits[i] for i in idx]
    lpm = LP.load(MEDIA)
    raw = LP.read_entry(lpm, F)['plain']
    use = [{'offset': e['offset'], 'len': e['len'], 'text_bytes': e['text_bytes']} for e in sub]
    try:
        nb, census, moved = TR.apply_edits_rebuild(raw, use, verify=False)
    except Exception as ex:
        print('重建失败:', ex); return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    info = LP.patch(MEDIA, OUT, {F: nb})
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'patch_title2.py'), OUT],
                   capture_output=True)
    shutil.copy2(OUT, DEPLOY)
    print('=== 已构建并部署 ===')
    print('  子集: %d / %d 条' % (len(idx), n))
    print('  范围: idx %d..%d' % (idx[0], idx[-1]))
    print('  其中译文 %d 条 / 重编码 %d 条'
          % (sum(1 for e in sub if e['src'] == 'tr'), sum(1 for e in sub if e['src'] == 'rec')))
    print('  文件 %d -> %d 字节 (Δ%+d)，重定位 %d 处'
          % (len(raw), len(nb), len(nb) - len(raw), len(moved)))
    print('  示例改动: %s' % '; '.join(e['desc'] for e in sub[:3]))
    print('  LPK: %d 字节' % os.path.getsize(DEPLOY))


if __name__ == '__main__':
    main()

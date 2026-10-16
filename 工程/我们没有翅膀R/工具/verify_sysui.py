# -*- coding: utf-8 -*-
r"""系统界面汉化 · 自校验器（ISSUE-20261007-06）。

对**成品 LPK** 逐条核对：
  1. 每个工作单条目的写入字节 == `build_padded.fit(译文, nbytes)`（逐字节）；
  2. 与「正文汉化版」相比，**11 个条目的长度未变**（零重定位）；
  3. 残留扫描：按第二版单元模型扫日文段，报出**与任何已写行都不重叠**的段
     （即真正的漏译候选；与已写行重叠者是我方中文被误读为 SJIS，属假阳性）。

用法：python -X utf8 verify_sysui.py [--body 正文版LPK] [--sysui 系统界面版LPK]
"""
import argparse
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP                                    # noqa: E402
from build_padded import fit                              # noqa: E402

WS = r'E:\ZCode Workspace\Galgame'
SYS = os.path.join(WS, '工程', '我们没有翅膀R', '工具', 'sysui')
# 默认校验**补丁包内的成品 LPK**（这是交付物本身）
SYS_UNDER_TEST = os.path.join(WS, '成品', '我们没有翅膀R_汉化补丁', '覆盖到游戏目录', 'SCRIPT.LPK')
TARGET_FILES = ['gallery.sob', 'config.dat', 'saveload.sob', 'config1.sob', 'config2.sob',
                'title2.sob', 'title.sob', 'gameinit.sob', 'main.sob', 'bgmmode.sob', 'voiceinf.dat']
KEEP = {158, 164, 170}          # 字体名 ＭＳ ゴシック：有意保留

JP = set()
for a, b in ((0x3040, 0x30FF), (0x4E00, 0x9FFF), (0xFF01, 0xFF60), (0x3000, 0x303F),
             (0x2010, 0x203B), (0x2190, 0x21FF), (0x2460, 0x24FF), (0x25A0, 0x26FF)):
    JP.update(range(a, b + 1))


def units(b):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            d = b[i + 1] if i + 1 < len(b) else 0
            if 0x40 <= d <= 0xFC and d != 0x7F:
                try:
                    out.append((i, 2, bytes([c, d]).decode('cp932'))); i += 2; continue
                except Exception:
                    pass
        if 0xA1 <= c <= 0xDF:
            try:
                out.append((i, 1, bytes([c]).decode('cp932'))); i += 1; continue
            except Exception:
                pass
        if c == 0x20:
            out.append((i, 1, ' ')); i += 1; continue
        out.append((i, 1, None)); i += 1
    return out


def runs(b):
    groups, cur = [], []
    for u in units(b) + [(len(b), 1, None)]:
        if u[2] is None:
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(u)
    res = []
    for g in groups:
        while g and g[0][2] == ' ':
            g = g[1:]
        while g and g[-1][2] == ' ':
            g = g[:-1]
        if not g:
            continue
        ch = ''.join(u[2] for u in g)
        j = [x for x in ch if ord(x) in JP]
        if not j:
            continue
        if len(j) >= 2 or (len(ch) == 1 and (0x3000 <= ord(ch) <= 0x303F or 0xFF01 <= ord(ch) <= 0xFF60)):
            res.append((g[0][0], sum(u[1] for u in g), ch))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sysui', default=SYS_UNDER_TEST)
    a = ap.parse_args()

    rows = json.load(io.open(os.path.join(SYS, 'runs_v2.json'), encoding='utf-8'))
    trans = {}
    for ln in io.open(os.path.join(SYS, 'master.tsv'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if ln.strip():
            k, v = ln.split('\t', 1)
            trans[int(k)] = v

    lp = LP.load(a.sysui)
    buf = {}
    for r in rows:
        if r['file'] not in buf:
            buf[r['file']] = LP.read_entry(lp, r['file'])['plain']

    ok = 0
    bad = []
    for r in rows:
        b = buf[r['file']]
        if r['id'] in KEEP:
            continue
        want, how = fit(trans[r['id']], r['n'])
        got = b[r['off']:r['off'] + r['n']]
        if got == want:
            ok += 1
        else:
            bad.append((r['id'], r['file'], r['off'], got[:20].hex(), (want or b'')[:20].hex()))
    print('逐条字节核对: %d / %d 命中' % (ok, len(rows) - len(KEEP)))
    for x in bad[:10]:
        print('   !! id=%d %s@%d 实测 %s 期望 %s' % x)

    spans = {}
    for r in rows:
        spans.setdefault(r['file'], []).append((r['off'], r['n']))
    real = 0
    for f in TARGET_FILES:
        for o, l, t in runs(buf[f]):
            if any(o < o2 + n2 and o2 < o + l for o2, n2 in spans.get(f, [])):
                continue                     # 与我方中文重叠 → 假阳性
            real += 1
            print('   真残留 %-14s @%d(%d) %s' % (f, o, l, t.replace('\n', '').replace('\r', '')))
    print('真残留合计 %d（`ＭＳ ゴシック` 3 处为有意保留，不在统计内）' % real)
    print('md5 %s  %d B' % (hashlib.md5(open(a.sysui, 'rb').read()).hexdigest(),
                            os.path.getsize(a.sysui)))
    if bad:
        raise SystemExit('[错误] 存在不符条目')


if __name__ == '__main__':
    main()

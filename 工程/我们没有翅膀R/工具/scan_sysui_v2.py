# -*- coding: utf-8 -*-
r"""系统界面文案「第二遍扫描」：找出第一遍漏掉的显示串（ISSUE-20261007-06 一审打回项）。

第一遍判据的三个盲区（一审实测）：
  1. `len(t) >= 3` 丢掉 **2 字串**（する / 行う / 低い / 命令 / 音量 / 咲夜 …）；
  2. 只认 SJIS **双字节**，丢掉 **单字节 SJIS 字符**（｢｣ 括号、孤立的 、「」（）等，它们在
     0xA1–0xDF 区间 —— EXE 已把前导字节判定放宽到 0x81–0xFE，残留会造成**两字节错位**）；
  3. 日文占比 0.7 门槛丢掉 **日文与 ASCII 混排**的串（`Windows95、Windows NT4.0`）。

第二遍把「单元」扩为：SJIS 双字节 / SJIS 单字节(0xA1–0xDF) / 可打印 ASCII，取极大连续段，
再按「含至少 1 个日文字符（假名·汉字·CJK 标点·日文符号）」筛；逐条打印供人工复核。

用法：python -X utf8 scan_sysui_v2.py [--out FILE]
"""
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP                                   # noqa: E402

WS = r'E:\ZCode Workspace\Galgame'
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
RUNS1 = os.path.join(WS, '临时', 'oretsuba_r_patch', '_sysui', 'runs.json')

TARGETS = ['gallery.sob', 'config.dat', 'saveload.sob', 'config1.sob', 'config2.sob',
           'title2.sob', 'title.sob', 'func_lib.sob', 'op.sob', 'sr_02.sob', 'bgmmode.sob',
           'gameinit.sob', 'sr_04.sob', 'sr_03.sob', 'sr_05.sob', 'sr_00.sob', 'sr_01.sob',
           'voiceinf.dat', 'eyecatch.sob', 'main.sob', 'gamereset.sob', 'logo.sob',
           'navel06.sob', 'movieplay.sob']

JP_RANGES = ((0x3040, 0x30FF), (0x4E00, 0x9FFF), (0xFF01, 0xFF60), (0x3000, 0x303F),
             (0x2010, 0x203B), (0x2190, 0x21FF), (0x2460, 0x24FF), (0x25A0, 0x26FF))
JP = set()
for a, b in JP_RANGES:
    JP.update(range(a, b + 1))


def is_jp(ch):
    return ord(ch) in JP


def decode_units(b):
    """把字节切成单元列表 [(off, nbytes, kind, char)]；kind∈{'sjis2','sjis1','break'}。

    **只认 SJIS**（双字节 0x81–0x9F/0xE0–0xFC + 合法后继；单字节 0xA1–0xDF）——
    不把 ASCII 并进来（第一版把它们并进来后，字节码里几乎所有段落都成了候选）。
    """
    out = []
    i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            d = b[i + 1] if i + 1 < len(b) else 0
            if 0x40 <= d <= 0xFC and d != 0x7F:
                try:
                    ch = bytes([c, d]).decode('cp932')
                    out.append((i, 2, 'sjis2', ch)); i += 2; continue
                except Exception:
                    pass
        if 0xA1 <= c <= 0xDF:
            try:
                ch = bytes([c]).decode('cp932')
                out.append((i, 1, 'sjis1', ch)); i += 1; continue
            except Exception:
                pass
        out.append((i, 1, 'break', None)); i += 1
    return out


def is_punct(ch):
    """CJK 标点 / 全角符号：单独成段也算显示文本（、。「」（）％～ 等）。"""
    o = ord(ch)
    return (0x3000 <= o <= 0x303F) or (0xFF01 <= o <= 0xFF60) or \
           (0x2010 <= o <= 0x203B) or (0x2190 <= o <= 0x21FF) or \
           (0x2460 <= o <= 0x24FF) or (0x25A0 <= o <= 0x26FF)


def runs_of(b):
    units = decode_units(b)
    groups, cur = [], []
    for u in units + [(len(b), 1, 'break', None)]:
        if u[2] == 'break':
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(u)
    res = []
    for g in groups:
        chars = ''.join(u[3] for u in g)
        jpn = [ch for ch in chars if is_jp(ch)]
        if not jpn:
            continue
        # 判据：≥2 个日文字符（不限占比以外），或「单字符且为 CJK 标点/符号」
        if len(jpn) >= 2:
            pass
        elif len(chars) == 1 and is_punct(chars):
            pass
        else:
            continue
        while g and g[0][2] == 'space':
            g = g[1:]
        while g and g[-1][2] == 'space':
            g = g[:-1]
        if not g:
            continue
        chars = ''.join(u[3] for u in g)
        jpn = [ch for ch in chars if is_jp(ch)]
        if not jpn or not (len(jpn) >= 2 or (len(chars) == 1 and is_punct(chars))):
            continue
        off = g[0][0]
        ln = sum(u[1] for u in g)
        res.append((off, ln, chars, g))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(WS, '临时', 'oretsuba_r_patch', '_sysui', 'runs_v2.txt'))
    a = ap.parse_args()

    lp = LP.load(MEDIA)
    old = json.load(io.open(RUNS1, encoding='utf-8'))
    oldmap = {}
    for r in old:
        oldmap.setdefault(r['file'], []).append((r['off'], r['n']))

    lines = []
    stat = []
    for name in TARGETS:
        try:
            b = LP.read_entry(lp, name)['plain']
        except KeyError:
            continue
        rs = runs_of(b)
        new = []
        for off, ln, chars, g in rs:
            # 与第一遍重合（被完全包含或完全包含之）→ 视为已处理
            covered = any(off <= o and off + ln >= o + n for o, n in oldmap.get(name, []))
            containing = any(o <= off and o + n >= off + ln for o, n in oldmap.get(name, []))
            if covered or containing:
                continue
            new.append((off, ln, chars, g))
        stat.append((name, len(rs), len(new)))
        lines.append('\n### %s   （第二遍总段 %d，其中**新增** %d）' % (name, len(rs), len(new)))
        for off, ln, chars, g in new:
            lines.append('%7d %4d| %s   [%s|%s]' % (
                off, ln, chars.replace('\n', '').replace('\r', ''),
                b[max(0, off - 6):off].hex(), b[off + ln:off + ln + 6].hex()))
    io.open(a.out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('%-18s %8s %8s' % ('file', 'v2段', '新增'))
    tot = 0
    for n, t, k in stat:
        print('%-18s %8d %8d' % (n, t, k))
        tot += k
    print('新增合计', tot)
    print('明细:', a.out)


if __name__ == '__main__':
    main()

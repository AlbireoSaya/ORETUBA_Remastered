# -*- coding: utf-8 -*-
r"""重编码（终版·结构安全，ISSUE-ORETUBAR-R）。

**前两版的错误（导致实机在「邂逅」前崩溃）**：
  在整段字节流上按「SJIS 可解」做滑动扫描，得到的片段**跨过了结构字节**
  （`01 01 <u16 len>` 头、`5b 20…` 指令、长度前缀等都被卷进"文本"里做转换），
  于是脚本结构被破坏 → 引擎解析失败 → 静默退出。

**正确做法**：以 `01 01 <u16 len>` 声明串为**权威边界**：
  * 保留全部头部字节（`01 01` + 2 字节长度）不动
  * 只把**声明体**按 SJIS 解码 → GBK 编码（长度不变，实测 100% 等长）
  * 结尾若为 NUL 则保留
  这样结构字节永远不被触碰。

只处理「声明体按 SJIS 解码后含假名」的串（即真正的日文内容）；
已经是 GBK 中文的串（含假名极少）跳过。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\重编码映射.json'

FALLBACK = {'\u226a': '\u300a', '\u226b': '\u300b', '\u301c': '\uff5e',
            '\u30fb': '\u00b7', '\u2015': '\u2014', '\u266a': '\u2606'}


def kana(s):
    return sum(1 for c in s if 0x3040 <= ord(c) <= 0x30FF)


def to_gbk(s):
    out = []
    for ch in s:
        try:
            out.append(ch.encode('gbk'))
        except UnicodeEncodeError:
            if ch in FALLBACK:
                out.append(FALLBACK[ch].encode('gbk'))
            else:
                return None
    return b''.join(out)


def main():
    edits = {}
    stats = []
    skipped = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SRC, fn), 'rb').read()
        found = []
        for m in re.finditer(rb'\x01\x01(..)', raw, re.S):
            ln = int.from_bytes(m.group(1), 'little')
            if not (4 < ln < 4000):
                continue
            boff = m.end()
            if boff + ln > len(raw):
                continue
            body = raw[boff:boff + ln]
            core = body.rstrip(b'\x00')
            trail = len(body) - len(core)
            if len(core) < 4:
                continue
            try:
                src = core.decode('cp932')
            except Exception:
                skipped.append((fn, mastart := m.start(), 'SJIS 不可解'))
                continue
            k = kana(src)
            # 只转「确实含日文假名」的串
            if k < 2:
                continue
            nb = to_gbk(src)
            if nb is None:
                skipped.append((fn, m.start(), 'GBK 不可编码'))
                continue
            if len(nb) != len(core):
                skipped.append((fn, m.start(), '长度变化 %d->%d' % (len(core), len(nb))))
                continue
            if nb == core:
                continue
            # 只替换正文区间（保留 01 01 + len 头与尾部 NUL）
            found.append((boff, ln, nb + b'\x00' * trail))
        if found:
            edits[fn] = found
            stats.append((fn, len(found), sum(len(b) for _, _, b in found)))
    print('声明串重编码: %d 文件 / %d 段 / %d 字节'
          % (len(stats), sum(s[1] for s in stats), sum(s[2] for s in stats)))
    print('跳过: %d 条' % len(skipped))
    from collections import Counter
    print('  跳过原因:', Counter(x[2] for x in skipped).most_common())
    print()
    for n, c, b in sorted(stats, key=lambda x: -x[2])[:10]:
        print('  %-18s %3d 段 %7d 字节' % (n, c, b))
    out = []
    for fn, found in edits.items():
        for off, ln, nb in found:
            out.append({'file': fn, 'offset': off, 'len': ln,
                        'text_bytes': list(nb), 'src': 'sjis->gbk(fix2)',
                        'text': nb.decode('gbk', errors='replace')})
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print()
    print('已写出', OUT, '(%d 段)' % len(out))
    print()
    print('=== 样例（s01_01a.tob）===')
    for r in [x for x in out if x['file'] == 's01_01a.tob'][:3]:
        print('  @%d len=%d: %r' % (r['offset'], r['len'], r['text'][:60]))


if __name__ == '__main__':
    main()

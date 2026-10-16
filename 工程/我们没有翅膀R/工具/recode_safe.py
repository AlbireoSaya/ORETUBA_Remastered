# -*- coding: utf-8 -*-
r"""重编码（结构安全版 v2，ISSUE-ORETUBAR-R）。

结构模型（实测）
================
脚本里的日文文本分两类：

1. **纯文本声明串**：`01 01 <u16 L> <SJIS 文本>`（+ 可选尾部 NUL）——场景描述。
2. **复合记录**：`01 01 <u16 L> …` 内部嵌套子记录，形如
   `… 01 01 <u8 len> <子文本> 00 …`，例：`01 01 05 00 91 e9 8e 75 00` → 子文本 `鷹志`。
   角色名在这些子记录里。

安全规则
========
  对每段候选文本：
    ① SJIS **完整解码**（不许 replace）
    ② 含 ≥2 个假名；假名+汉字占比 ≥50%
    ③ 转 GBK 后**字节数不变**（等长 → 不移动任何偏移）
    ④ 文本主体不含控制字符（尾部 NUL 先剥离、转后原样补回）
  对每个文件：全部候选应用后必须仍可被 `tob_extract.parse_messages_bytes`
    解析且**消息槽数不变**，否则整文件放弃。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_extract as EX

SRC = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\重编码映射.json'

NUL = b'\x00'
FALLBACK = {'\u226a': '\u300a', '\u226b': '\u300b', '\u301c': '\uff5e',
            '\u30fb': '\u00b7', '\u2015': '\u2014', '\u266a': '\u2606'}


def kana(s):
    return sum(1 for c in s if 0x3040 <= ord(c) <= 0x30FF)


def han(s):
    return sum(1 for c in s if 0x4E00 <= ord(c) <= 0x9FFF)


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


def convert(b: bytes, min_kana=2, ratio=0.5):
    """字节段 → GBK 字节段（等长）。不可安全转换时返回 None。"""
    if len(b) < 2:
        return None
    core = b.rstrip(NUL)
    trail = len(b) - len(core)
    if len(core) < 2:
        return None
    try:
        s = core.decode('cp932')
    except Exception:
        return None
    k, h = kana(s), han(s)
    if k < min_kana:
        return None
    if (k + h) / max(1, len(s)) < ratio:
        return None
    if any(ord(c) < 0x20 and c not in '\r\n\t' for c in s):
        return None
    nb = to_gbk(s)
    if nb is None or len(nb) != len(core):
        return None
    return nb + NUL * trail


def scan_file(raw):
    """返回 [(offset, length, new_bytes)]。"""
    found = {}
    for m in re.finditer(rb'\x01\x01(..)', raw, re.S):
        L = int.from_bytes(m.group(1), 'little')
        if not (2 < L < 2000):
            continue
        boff = m.end()
        if boff + L > len(raw):
            continue
        body = raw[boff:boff + L]
        # 类型 1：纯文本声明串
        nb = convert(body)
        if nb is not None and nb != body:
            found[(boff, L)] = nb
            continue
        # 类型 2：复合记录 → 内部嵌套子记录
        for sub in re.finditer(rb'\x01\x01(.)', body, re.S):
            sl = sub.group(1)[0]
            if not (2 < sl < 200):
                continue
            soff = sub.end()
            if soff + sl > len(body):
                continue
            core = body[soff:soff + sl]
            nb2 = convert(core, min_kana=0, ratio=0.4)
            if nb2 is None or nb2 == core:
                continue
            txt = core.rstrip(NUL).decode('cp932', errors='replace')
            if kana(txt) == 0 and han(txt) < 2:
                continue
            found[(boff + soff, sl)] = nb2
    return [(o, l, n) for (o, l), n in sorted(found.items())]


def main():
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.tob'))
    if only:
        files = [f for f in files if f in only]
    edits, stats, rejected = {}, [], []
    for fn in files:
        raw = open(os.path.join(SRC, fn), 'rb').read()
        cands = scan_file(raw)
        if not cands:
            continue
        try:
            base = len(EX.parse_messages_bytes(raw, enc='gbk'))
        except Exception:
            base = None
        buf = bytearray(raw)
        for off, ln, nb in cands:
            buf[off:off + ln] = nb
        try:
            new = len(EX.parse_messages_bytes(bytes(buf), enc='gbk'))
        except Exception as e:
            rejected.append((fn, '解析失败 %s' % e)); continue
        if base is not None and new != base:
            rejected.append((fn, '槽数变化 %d→%d' % (base, new))); continue
        edits[fn] = cands
        stats.append((fn, len(cands), sum(l for _, l, _ in cands)))
    print('通过结构校验: %d 文件 / %d 段 / %d 字节'
          % (len(stats), sum(s[1] for s in stats), sum(s[2] for s in stats)))
    print('因结构校验被拒: %d 文件' % len(rejected))
    for r in rejected[:8]:
        print('   ', r)
    print()
    for n, c, b in sorted(stats, key=lambda x: -x[2])[:12]:
        print('  %-18s %3d 段 %7d 字节' % (n, c, b))
    out = []
    for fn, cands in edits.items():
        for off, ln, nb in cands:
            out.append({'file': fn, 'offset': off, 'len': ln,
                        'text_bytes': list(nb), 'src': 'sjis->gbk(safe2)',
                        'text': nb.decode('gbk', errors='replace')})
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print()
    print('已写出', OUT, '(%d 段)' % len(out))


if __name__ == '__main__':
    main()

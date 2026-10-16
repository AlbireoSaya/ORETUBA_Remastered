# -*- coding: utf-8 -*-
r"""名字/描述串的编码归一（ISSUE-ORETUBAR-R）。

问题：角色名标签（如「日和子」）在 GBK 字体下显示为乱码（`擔檻崋`）——
因为它们是**纯汉字无假名**，被上一轮重编码的「含≥2 假名」判据跳过，仍是 SJIS 字节。

本脚本专门处理**短声明串**（名字/称谓）：
  * 判据放宽：**含 ≥1 个汉字或假名**且长度为 2..64 字节
  * 转 GBK，**要求字节数不变**（零位移）
  * 用 SJIS 解码 + GBK 编码，失败则跳过

与 `recode_safe.py` 的区别：不碰长描述串（避免动到可能被跳转引用的长文本），
只处理短名字串 —— 这类串的语义是「显示用标签」，转换后显示为**日文汉字**
（日后要做中文译名时再单独处理长度约束下的替换）。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_extract as EX

SRC = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\重编码映射_名字.json'

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


def conv(b: bytes):
    """短串 → GBK（等长）。不满足条件返回 None。"""
    core = b.rstrip(NUL)
    trail = len(b) - len(core)
    if not (2 <= len(core) <= 64):
        return None
    try:
        s = core.decode('cp932')
    except Exception:
        return None
    if kana(s) + han(s) < 1:
        return None
    if any(ord(c) < 0x20 for c in s):
        return None
    nb = to_gbk(s)
    if nb is None or len(nb) != len(core):
        return None
    return nb + NUL * trail


def main():
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.tob'))
    out = []
    per_file = {}
    for fn in files:
        raw = open(os.path.join(SRC, fn), 'rb').read()
        for m in re.finditer(rb'\x01\x01(.)', raw, re.S):
            sl = m.group(1)[0]
            if not (2 < sl <= 64):
                continue
            soff = m.end()
            if soff + sl > len(raw):
                continue
            seg = raw[soff:soff + sl]
            nb = conv(seg)
            if nb is None or nb == seg:
                continue
            out.append({'file': fn, 'offset': soff, 'len': sl,
                        'text_bytes': list(nb), 'src': 'sjis->gbk(name)',
                        'text': nb.rstrip(NUL).decode('gbk', errors='replace')})
            per_file[fn] = per_file.get(fn, 0) + 1
    print('短串重编码: %d 条 / %d 文件' % (len(out), len(per_file)))
    from collections import Counter
    print('样例:')
    for x in out[:12]:
        print('  %-16s @%-6d len=%-3d %r' % (x['file'], x['offset'], x['len'], x['text']))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)


if __name__ == '__main__':
    main()

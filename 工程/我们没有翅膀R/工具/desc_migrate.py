# -*- coding: utf-8 -*-
r"""场景描述字段的译文迁移（ISSUE-ORETUBAR-R）。

场景描述存于每个 `.tob` 开头的 `01 01 <u16 len> <SJIS 文本>` 声明串，
**不在**此前提取的 58,360 条消息槽里（那些是对话框正文）。
参照汉化（新米汉化组）已译过同一批描述，译文以消息槽形式存在于
`参照\原版汉化SCRIPT_CHS\<同名>.sob` 中（同一场景的第一条长旁白）。

做法：
  1. 取 R 版每个 `.tob` 的第一条描述串（日文原文 + 精确偏移/长度）
  2. 在参照汉化同场景的 `.sob` 里，找**日文原文相同**的槽（字节级匹配），取其译文
  3. 译文按 R 版描述字段的**原字节长度**做等长化（不足补全角空格，过长按字符边界截断）
  4. 输出 `语料\描述译文映射.json`
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(P, '语料', 'R版SCRIPT')
REF = os.path.join(P, '参照', '原版汉化SCRIPT_CHS')
OUT = os.path.join(P, '语料', '描述译文映射.json')

NUL = b'\x00'
FULL = '\u3000'


def first_desc(raw):
    """取文件里第一条 01 01 <u16 len> 描述串（通常紧跟 _START 标签区）。返回 (boff, ln, text)。"""
    for m in re.finditer(rb'\x01\x01(..)', raw[:2000], re.S):
        ln = int.from_bytes(m.group(1), 'little')
        if not (40 < ln < 2000):
            continue
        boff = m.end()
        if boff + ln > len(raw):
            continue
        core = raw[boff:boff + ln].rstrip(NUL)
        try:
            t = core.decode('cp932')
        except Exception:
            continue
        kana = sum(1 for c in t if 0x3040 <= ord(c) <= 0x30FF)
        if kana < 5:
            continue
        return boff, ln, t
    return None


def ref_slots(path):
    """参照 .sob 的槽：[(日文原文, 中文译文)]（按 `#…$&…$` 结构）。"""
    raw = open(path, 'rb').read()
    out = []
    for m in re.finditer(rb'#([^\x00$]{0,80}?)\$&\$?([^\x00]*?)\$', raw, re.S):
        meta, body = m.group(1), m.group(2)
        jp = None
        try:
            jp = body.decode('cp932')
        except Exception:
            pass
        cn = None
        try:
            cn = body.decode('gbk')
        except Exception:
            pass
        out.append((jp, cn))
    return out


def fit(cn: str, need: int):
    try:
        b = cn.encode('gbk')
    except UnicodeEncodeError:
        return None
    if len(b) > need:
        o = []
        n = 0
        for ch in cn:
            cb = ch.encode('gbk')
            if n + len(cb) > need:
                break
            o.append(cb)
            n += len(cb)
        b = b''.join(o)
    pad = need - len(b)
    if pad < 0:
        return None
    s = b + (FULL * (pad // 2)).encode('gbk') + (b' ' if pad % 2 else b'')
    return s if len(s) == need else None


def main():
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.tob'))
    res = []
    no_ref = miss = hit = 0
    for fn in files:
        raw = open(os.path.join(SRC, fn), 'rb').read()
        d = first_desc(raw)
        if not d:
            continue
        boff, ln, jp = d
        refp = os.path.join(REF, os.path.splitext(fn)[0] + '.sob')
        if not os.path.exists(refp):
            no_ref += 1
            continue
        cn = None
        for rjp, rcn in ref_slots(refp):
            if rjp and rjp.strip() == jp.strip():
                cn = rcn
                break
        if not cn:
            miss += 1
            continue
        b = fit(cn, ln)
        if b is None:
            miss += 1
            continue
        res.append({'file': fn, 'offset': boff, 'len': ln,
                    'text_bytes': list(b), 'src': 'desc-migrate',
                    'text': b.decode('gbk', errors='replace').rstrip()})
        hit += 1
    print('命中 %d 个场景描述；无参照 %d；匹配失败 %d' % (hit, no_ref, miss))
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)
    for x in res[:6]:
        print('  %-16s %r' % (x['file'], x['text'][:60]))


if __name__ == '__main__':
    main()

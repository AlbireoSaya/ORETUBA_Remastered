# -*- coding: utf-8 -*-
r"""残留 SJIS 清剿（终版，ISSUE-ORETUBAR-R）。

判据（避开上一版的坑）：
  对每个 `01 01 <u16 len>` 声明串（场景描述 / 角色名）与每条消息槽正文：
    1. 若按 **SJIS 解码后含假名** → 认定为「日文内容」（不管 GBK 能否解出）
    2. 转 GBK；**GBK 无码位的字符做等效回退**（≪→《 ≫→》 〜→～ ・→· 等）
    3. 与原文不同则记为待改

上一版的失败原因：SJIS 日文的字节**恰好**也是合法 GBK 序列（如 `丂巹棫旤`），
按「GBK 能否解出」判定会误判为「已是中文」，从而整段漏掉。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

SRC_DIR = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
OUT_MAP = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\重编码映射_final.json'

FALLBACK = {
    '\u226a': '\u300a', '\u226b': '\u300b',   # ≪ ≫ -> 《 》
    '\u301c': '\uff5e',                        # 〜 -> ～
    '\u30fb': '\u00b7',                        # ・ -> ·
    '\u2015': '\u2014',                        # ― -> —
    '\u266a': '\u2606',                        # ♪ -> ☆
    '\u25cb': '\u25ef', '\u3007': '\u25ef',    # ○ 〇 -> ◯
}


def kana_count(s):
    return sum(1 for c in s if 0x3040 <= ord(c) <= 0x30FF)


def to_gbk(s):
    """转 GBK，逐字符回退不可编码者。返回 (bytes|None, 用到的回退表)。"""
    used = {}
    out = []
    for ch in s:
        try:
            out.append(ch.encode('gbk'))
        except UnicodeEncodeError:
            if ch in FALLBACK:
                out.append(FALLBACK[ch].encode('gbk'))
                used[ch] = FALLBACK[ch]
            else:
                return None, used
    return b''.join(out), used


def scan_sjis_runs(raw, min_len=6):
    """扫描所有「按 SJIS 可解且含假名」的连续段（启发式：以 NUL / 结构字节为界）。"""
    # 用宽松的分段：在每个不可视为 SJIS 文本的字节处断开
    runs = []
    i = 0
    n = len(raw)
    start = None
    while i < n:
        c = raw[i]
        ok = False
        step = 1
        if c == 0x00:
            ok = False
        elif c < 0x20:
            ok = False
        elif c < 0x80:
            ok = True
        elif 0xA1 <= c <= 0xDF:
            ok = True
        elif (0x81 <= c <= 0x9F) or (0xE0 <= c <= 0xEF):
            if i + 1 < n and (0x40 <= raw[i + 1] <= 0x7E or 0x80 <= raw[i + 1] <= 0xFC):
                ok = True
                step = 2
        if ok:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= min_len:
                runs.append((start, i - start))
            start = None
        i += step
    if start is not None and n - start >= min_len:
        runs.append((start, n - start))
    return runs


def main():
    edits = {}
    stats = []
    fallback_used = {}
    for fn in sorted(os.listdir(SRC_DIR)):
        if not fn.lower().endswith('.tob'):
            continue
        raw = open(os.path.join(SRC_DIR, fn), 'rb').read()
        found = []
        for off, ln in scan_sjis_runs(raw):
            seg = raw[off:off + ln]
            # 尾随 NUL 剥离（若有）
            core = seg.rstrip(b'\x00')
            trail = len(seg) - len(core)
            if kana_count_safe(core) < 1:
                continue
            try:
                t = core.decode('cp932')
            except Exception:
                continue
            if kana_count(t) < 1:
                continue
            nb, used = to_gbk(t)
            if nb is None or nb == core:
                continue
            for a, b in used.items():
                fallback_used[a] = fallback_used.get(a, 0) + 1
            found.append((off, len(seg), nb + b'\x00' * trail))
        if found:
            edits[fn] = found
            stats.append((fn, len(found), sum(len(b) for _, _, b in found)))
    print('需要重编码: %d 文件 / %d 段 / %d 字节'
          % (len(stats), sum(s[1] for s in stats), sum(s[2] for s in stats)))
    print('符号回退使用:', fallback_used)
    print()
    for n, c, b in sorted(stats, key=lambda x: -x[2])[:12]:
        print('  %-18s %3d 段 %7d 字节' % (n, c, b))
    out = []
    for fn, found in edits.items():
        for off, ln, nb in found:
            out.append({'file': fn, 'offset': off, 'len': ln,
                        'text_bytes': list(nb), 'src': 'sjis->gbk(final)',
                        'text': nb.decode('gbk', errors='replace')})
    json.dump(out, open(OUT_MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print()
    print('已写出', OUT_MAP, '(%d 段)' % len(out))


def kana_count_safe(b: bytes) -> int:
    """容错计假名数（用 SJIS 解码，坏字节跳过）。"""
    try:
        s = b.decode('cp932')
    except Exception:
        s = b.decode('cp932', errors='replace')
    return kana_count(s)


if __name__ == '__main__':
    main()

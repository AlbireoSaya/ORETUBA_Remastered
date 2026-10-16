# -*- coding: utf-8 -*-
r"""残留 SJIS 段清剿（第二遍，ISSUE-ORETUBAR-R）。

问题：第一遍 `recode_sjis.py` 的清单以「声明串 + 孤立内联」为口径，
实测漏掉了部分文件的场景描述字段（例：`s01_01a.tob` @965 的 290 字节描述）。

本脚本换用**更强的判据**在**成品 LPK** 上直接扫描：
  对每个 .tob 明文，扫描所有「可能为文本」的连续字节段，对每段做双解码判定：
    * 按 **UTF-8→GBK 语义**：已是 GBK 的中文（含汉字且无假名）→ 保留
    * **含日文假名（U+3040–U+30FF）** → 说明是 SJIS 残留 → 转 GBK
  这样不依赖位置清单，直接按「内容是不是日文」判定。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

PROD_LPK = r'E:\ZCode Workspace\Galgame\ORETSUBA_R\ORETSUBA_R\SCRIPT.LPK'
SRC_DIR = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
OUT_MAP = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\重编码映射2.json'


def kana_count(s):
    return sum(1 for c in s if 0x3040 <= ord(c) <= 0x30FF)


def scan_desc_records(raw):
    """扫描 `01 01 <u16 len>` 声明串（含场景描述与角色名）。返回 [(off, len, body_off)]。"""
    out = []
    for m in re.finditer(rb'\x01\x01(..)', raw, re.S):
        ln = int.from_bytes(m.group(1), 'little')
        if 4 < ln < 2000 and m.end() + ln <= len(raw):
            out.append((m.start(), ln, m.end()))
    return out


def main():
    lp = LP.load(PROD_LPK)
    files = sorted(n for n, _ in lp['ents'] if n.lower().endswith('.tob'))
    print('扫描 %d 个 .tob（在成品 LPK 上）' % len(files))
    edits = {}
    stats = []
    for name in files:
        e = LP.read_entry(lp, name)
        raw = e['plain']
        found = []
        # 1) 声明串（描述/角色名）：按「能否 GBK 解出且不含假名」判定
        for off, ln, boff in scan_desc_records(raw):
            body = raw[boff:boff + ln]
            # 去掉尾部 NUL
            core = body.rstrip(b'\x00')
            if not core:
                continue
            gbk_ok = True
            try:
                t = core.decode('gbk')
            except Exception:
                gbk_ok = False
            if gbk_ok:
                # 已是 GBK：若不含假名 → 已是中文，保留
                if kana_count(t) == 0:
                    continue
                # 含假名 → 说明这段其实是 SJIS 被误读成 GBK；需要按 SJIS 解再转 GBK
                try:
                    t2 = core.decode('cp932')
                except Exception:
                    continue
                src_txt = t2
            else:
                try:
                    src_txt = core.decode('cp932')
                except Exception:
                    continue
            if kana_count(src_txt) == 0 and sum(1 for c in src_txt if 0x4E00 <= ord(c) <= 0x9FFF) == 0:
                continue
            try:
                nb = src_txt.encode('gbk')
            except UnicodeEncodeError:
                continue
            if nb != core:
                found.append((off, len(body), nb))
        if found:
            edits[name] = found
            stats.append((name, len(found), sum(len(b) for _, _, b in found)))
    print()
    print('需要重编码的文件: %d 个；总条数 %d' % (len(stats), sum(s[1] for s in stats)))
    tot = sum(s[2] for s in stats)
    print('涉及字节数: %d' % tot)
    print()
    print('=== 前 15 个文件 ===')
    for n, c, b in sorted(stats, key=lambda x: -x[2])[:15]:
        print('  %-18s %3d 条 %6d 字节' % (n, c, b))

    # 写映射（供 build_cn 消费：与现有重编码映射同形）
    out = []
    for name, found in edits.items():
        for off, ln, nb in found:
            out.append({'file': name, 'offset': off, 'len': ln,
                        'text_bytes': list(nb), 'src': 'sjis->gbk(2)',
                        'text': nb.decode('gbk', errors='replace')})
    json.dump(out, open(OUT_MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print()
    print('已写出', OUT_MAP, '(%d 条)' % len(out))


if __name__ == '__main__':
    main()

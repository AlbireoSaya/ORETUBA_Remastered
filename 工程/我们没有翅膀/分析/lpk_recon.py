# -*- coding: utf-8 -*-
"""lpk_recon.py —— 《我们没有翅膀》汉化版资源侦察（只读）

目的：判断 `D:\\Gal\\[Navel]我们没有翅膀\\SCRIPT.LPK` 内是否含**原始日文剧情资源**。

做法（复用 R 版工具链 `工程\\我们没有翅膀R\\工具\\` 的 lpk_patch.py / lucifen_lzss.py）：
  1. 解 SCRIPT.LPK 索引 → 条目清单
  2. 逐条解容器加密 + LZSS，看明文魔数（TOB0 / SOB0 / 其它）
  3. 对剧情脚本做语言判定：SJIS 平假名 / 半角片假名 vs GBK 中文
  4. 与同目录外挂 `SCRIPT_CHS\\*.sob` 做同名比对（覆盖度），抽样对照同一文件的日中文本

只读 D: 盘；仅向本目录写统计与样本。
"""
import os
import sys
import json
import re
import struct

TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, TOOLS)
import lpk_patch as LP  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
SCRIPT_LPK = os.path.join(GAME, 'SCRIPT.LPK')
CHS_DIR = os.path.join(GAME, 'SCRIPT_CHS')
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀\分析'
SAMPLE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀\样本'

HIRA = re.compile('[\u3041-\u309f]')
KATA = re.compile('[\u30a1-\u30fa]')
CJK = re.compile('[\u4e00-\u9fff]')


def decode_sjis(b):
    return b.decode('cp932', errors='replace')


def decode_gbk(b):
    return b.decode('gbk', errors='replace')


def has_sjis_jp(s):
    """真日文判据：含平假名或（片假名且非纯汉字）。"""
    return bool(HIRA.search(s)) or bool(KATA.search(s))


def sample_texts(plain, limit=8):
    """从明文里抽可读双字节串，分别按 SJIS / GBK 解码。"""
    out = []
    for m in re.finditer(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc]){3,}', plain):
        b = m.group(0)
        if len(b) < 12:
            continue
        out.append((m.start(), b))
        if len(out) >= limit * 4:
            break
    return out


def main():
    lp = LP.load(SCRIPT_LPK)
    print('=== SCRIPT.LPK 结构 ===')
    print('  条目数=%d  flags=0x%02x  idx_len=%d  mode=%s  rec_size=%d  entry_crypt=%d  whole_crypt=%d'
          % (len(lp['ents']), lp['flags'], lp['idx_len'],
             'long' if lp['mode'] else 'short', lp['rec_size'],
             lp['is_crypt'], lp['total_crypt']))

    chs_files = set(os.listdir(CHS_DIR))
    chs_lower = {n.lower(): n for n in chs_files}

    stats = {'total': 0, 'TOB0': 0, 'SOB0': 0, 'other': 0}
    rows = []
    jp_bytes_total = 0
    for name, num in sorted(lp['ents']):
        stats['total'] += 1
        try:
            e = LP.read_entry(lp, name)
        except Exception as ex:  # noqa: BLE001
            rows.append(dict(name=name, num=num, err=str(ex)))
            continue
        p = e['plain']
        magic = p[:4]
        kind = magic.decode('latin1') if magic[:3].isalnum() else 'other'
        if magic == b'TOB0':
            stats['TOB0'] += 1
        elif magic == b'SOB0':
            stats['SOB0'] += 1
        else:
            stats['other'] += 1
        # 语言判定：全明文按 SJIS 解，统计平假名数量
        s = decode_sjis(p)
        hira = len(HIRA.findall(s))
        jp_bytes_total += hira
        chs_match = chs_lower.get(name.lower())
        rows.append(dict(name=name, num=num, magic=kind, size=len(p),
                         ul=e['ul'], cl=e['cl'], hira=hira,
                         chs=chs_match, chs_size=(os.path.getsize(os.path.join(CHS_DIR, chs_match))
                                                  if chs_match else None)))

    print('  魔数分布:', stats)
    print('  含平假名条目数 =', sum(1 for r in rows if r.get('hira', 0) > 0))

    miss = [r['name'] for r in rows if not r.get('chs')]
    print('  SCRIPT_CHS 未覆盖条目 (%d):' % len(miss), miss)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'lpk_entries.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    # ---- 抽样：正文级证据 ----
    os.makedirs(SAMPLE, exist_ok=True)
    print('\n=== 抽样正文（LPK 内 / 外挂 CHS 同文件对照）===')
    picks = [n for n in ('s00_00.tob', 's00_00.sob', 's01_01a.tob', 's01_01a.sob',
                         's01_02a.tob', 's01_02a.sob', 'gameinit.sob', 'title.sob')
             if any(n == r['name'] for r in rows if 'name' in r)]
    if not picks:
        picks = [r['name'] for r in rows[:4] if 'err' not in r]
    for name in picks:
        try:
            e = LP.read_entry(lp, name)
        except Exception:  # noqa: BLE001
            continue
        p = e['plain']
        open(os.path.join(SAMPLE, 'LPK_' + name.replace('/', '_')), 'wb').write(p)
        s = decode_sjis(p)
        hira = HIRA.findall(s)
        print('\n--- LPK / %s  (%d 字节, 魔数 %s, 平假名字符 %d 个) ---'
              % (name, len(p), p[:4].decode('latin1', 'replace'), len(hira)))
        for start, b in sample_texts(p, limit=3)[:6]:
            print('   @%-7d SJIS: %s' % (start, decode_sjis(b)[:90]))
            print('   %-8s GBK : %s' % ('', decode_gbk(b)[:90]))
        cm = chs_lower.get(name.lower())
        if cm:
            cp = open(os.path.join(CHS_DIR, cm), 'rb').read()
            open(os.path.join(SAMPLE, 'CHS_' + cm), 'wb').write(cp)
            cs = decode_gbk(cp)
            print('   >>> 同外挂文件 %s (%d 字节)：平假名 %d 个，汉字 %d 个'
                  % (cm, len(cp), len(HIRA.findall(cs)), len(CJK.findall(cs))))
            for m in list(re.finditer(r'[\u4e00-\u9fff][\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\w，。！？、…—～“”‘’：；（）]{6,}',
                                      cs))[:4]:
                print('       CN: %s' % m.group(0)[:80])


if __name__ == '__main__':
    main()

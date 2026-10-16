# -*- coding: utf-8 -*-
r"""修复「从未被覆盖的声明串」（ISSUE-20260915-06 / bug C）。

实测 44 条（L<=64）仍是原始 SJIS → 游戏内乱码：
  * 组合名：鷹志＆京 / 鷲介＆英里子 / 鷲介＆日和子 / 鷲介＆紀奈子 / 英里子＆紀奈子 / 鳴＆亜衣
  * 编号名：００１（s04_01c1/c2 各 13 条）
  * 空白名：U+3000（s04_06k 4 条）
处理：组合名按 name_map.MAP 逐段译；其余按 SJIS→GBK 等值重编码；
      任何无法翻译的**兜底为 SJIS→GBK 重编码**（保证不再有原始 SJIS 残留）。
追加到 语料\重编码映射.json（先备份一次，若备份已存在则不再覆盖）。
"""
import os, re, sys, json, shutil

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import name_map as NM

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
CACHE = os.path.join(WS, '临时', '_audit_cache', 'orig')
REC = os.path.join(Y, '重编码映射.json')
BAK = os.path.join(Y, '重编码映射.json.bak_pre_fixA')


def O(n):
    return open(os.path.join(CACHE, n), 'rb').read()


def convert(s):
    """返回 (中文/重编码目标文本, 方式)。无法处理返回 (None, None)。"""
    if s == '\u3000' or all('\uff10' <= c <= '\uff19' for c in s):
        return s, 'recode'                     # 空白名 / 全角数字编号：等值重编码
    if '\uff06' in s:                          # 全角 ＆
        parts = s.split('\uff06')
        if all(p in NM.MAP for p in parts):
            return '\uff06'.join(NM.MAP[p] for p in parts), 'translate'
    if s in NM.MAP:
        return NM.MAP[s], 'translate'
    return None, None


rec = json.load(open(REC, encoding='utf-8'))
have = set((r['file'], int(r['offset'])) for r in rec if r.get('offset') is not None)

added = []
skip = []
for fn in sorted(os.listdir(CACHE)):
    if not (fn.endswith('.tob') or fn.endswith('.sob')):
        continue
    a = O(fn)
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        if not (3 <= L <= 64):
            continue
        boff = i + 4
        if boff + L > len(a) or a[boff + L - 1] != 0x00:
            continue
        if (fn, boff) in have:
            continue
        body = a[boff:boff + L - 1]
        if all(0x20 <= x < 0x7F for x in body):
            continue                            # 纯 ASCII（语音 ID 等）
        try:
            s = body.decode('cp932')
        except Exception:
            skip.append((fn, boff, L, body.hex(), 'cp932失败'))
            continue
        t, how = convert(s)
        if t is None:
            # 兜底：SJIS→GBK 重编码（日文保持日文显示，不再乱码）
            t, how = s, 'recode-fallback'
        if how == 'translate':
            nb = NM.fit_name(t, L)
        else:
            nb = t.encode('gbk') + b'\x00' if len(t.encode('gbk')) + 1 <= L else None
            if nb is not None and len(nb) < L:
                pad = L - len(nb)
                nb = nb[:-1] + b'\xa1\xa1' * (pad // 2) + (b' ' if pad % 2 else b'') + b'\x00'
        if nb is None or len(nb) != L:
            skip.append((fn, boff, L, body.hex(), '放不下 %r' % t))
            continue
        added.append({'file': fn, 'offset': boff, 'len': L, 'text_bytes': list(nb),
                      'src': 'name-combo' if how == 'translate' else 'recode-combo',
                      'text': t})
        have.add((fn, boff))

print('新增行 %d 条' % len(added))
from collections import Counter
print('方式:', dict(Counter(r['src'] for r in added)))
print('文本:', dict(Counter(r['text'] for r in added)))
for fn, boff, L, h, why in skip:
    print('   [跳过] %-14s @%-6d L=%-3d %s %s' % (fn, boff, L, h, why))

if added:
    if not os.path.exists(BAK):
        shutil.copy2(REC, BAK)
        print('已备份 →', BAK)
    json.dump(rec + added, open(REC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写回 → %s（%d 行）' % (REC, len(rec) + len(added)))
else:
    print('无改动')

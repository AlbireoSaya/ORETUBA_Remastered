# -*- coding: utf-8 -*-
r"""修复「声明串 NUL 结尾丢失」（ISSUE-20260915-06 / bug A · 名字框方块）。

背景：引擎把 `01 01 <u16 L>` 声明串当 NUL 结尾 C 串读；构建器把最后一个字节
写成了 0x20（半角空格），导致引擎越读到下一条记录的 `01 01 <L>` → 名字后 2–3 个方块。

本脚本对**原版以 0x00 结尾、现行为非 0** 的声明串记录做数据级修复：
  * 已有 rec 行 → 行内末字节改为 0x00（长度不变、等长约束保持）；
  * 无 rec 行（历史遗留漏网） → 追加新行 src='fix-nul'，bytes = 原字节、末字节改 0x00。
只读原版缓存（临时\_audit_cache\orig），写 语料\重编码映射.json（先备份）。
"""
import os, re, sys, json, shutil

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
CACHE = os.path.join(WS, '临时', '_audit_cache', 'orig')
REC = os.path.join(Y, '重编码映射.json')
BAK = os.path.join(Y, '重编码映射.json.bak_pre_fixA')


def O(n):
    return open(os.path.join(CACHE, n), 'rb').read()


def C(n):
    return open(os.path.join(os.path.dirname(CACHE), 'cur', n), 'rb').read()


rec = json.load(open(REC, encoding='utf-8'))
row_by = {}
for r in rec:
    row_by[(r['file'], int(r['offset']))] = r
print('rec 行数 %d' % len(rec))

fixed = 0
added = []
last_vals = {}
bad_len = 0
nonnul = 0
nonnul_samples = []
for fn in sorted(os.listdir(CACHE)):
    if not (fn.endswith('.tob') or fn.endswith('.sob')):
        continue
    a = O(fn)
    b = C(fn)
    for m in re.finditer(rb'\x01\x01', a):
        i = m.start()
        if i + 4 > len(a):
            continue
        L = a[i + 2] | (a[i + 3] << 8)
        # 只处理真实名字声明串（L<=64）；L=256 是字节码里 `01 01 00 01` 的误报，绝不能动
        if not (3 <= L <= 64):
            continue
        boff = i + 4
        if boff + L > len(a):
            continue
        if a[boff + L - 1] != 0x00:
            nonnul += 1
            # 诊断：原版即非 NUL 结尾的声明串（记录但不动）
            if len(nonnul_samples) < 8:
                nonnul_samples.append((fn, i, L, a[boff:boff + L].hex()))
            continue
        r = row_by.get((fn, boff))
        if r is not None:
            tb = bytes(r['text_bytes']) if isinstance(r['text_bytes'], list) else \
                r.get('text_bytes_latin1', '').encode('latin-1')
            if len(tb) != int(r['len']):
                bad_len += 1
                continue
            if tb[-1] != 0x00:
                last_vals[tb[-1]] = last_vals.get(tb[-1], 0) + 1
                r['text_bytes'] = list(tb[:-1] + b'\x00')
                fixed += 1
        else:
            # 无行可修，且**现行末字节已被写坏**（非 NUL）→ 补一条修复行。
            # 现行末字节仍为 NUL 的记录（ASCII 素材路径 / 语音 ID 等）保持原样，绝不新增。
            if boff + L <= len(b) and b[boff + L - 1] != 0x00:
                nb = bytearray(a[boff:boff + L])
                nb[-1] = 0x00
                added.append({'file': fn, 'offset': boff, 'len': L,
                              'text_bytes': list(bytes(nb)), 'src': 'fix-nul',
                              'text': bytes(nb).decode('gbk', errors='replace')})

print('修复已有行 %d 条；新增 fix-nul 行 %d 条' % (fixed, len(added)))
print('修复前行末字节分布:', {'0x%02x' % k: v for k, v in last_vals.items()})
print('长度不符被跳过 %d 条；原版即非 NUL 结尾的声明串 %d 条' % (bad_len, nonnul))
for fn, i, L, h in nonnul_samples:
    print('   [非NUL] %-16s @%-6d L=%-3d %s' % (fn, i, L, h))
for r in added[:12]:
    print('   [新增] %-16s @%-6d L=%-3d %r' % (r['file'], r['offset'], r['len'], r['text']))

if fixed or added:
    shutil.copy2(REC, BAK)
    json.dump(rec + added, open(REC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已备份 →', BAK)
    print('已写回 → %s（%d 行）' % (REC, len(rec) + len(added)))
else:
    print('无改动')

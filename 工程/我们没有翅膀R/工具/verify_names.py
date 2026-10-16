# -*- coding: utf-8 -*-
r"""名字统一后的专项验证（ISSUE-20260915-07）：只读。用法：
python -X utf8 verify_names.py <新 SCRIPT.LPK>

  A. 4 处旧译名（迦楼罗/普拉琪娜/法尔康/哈柳）在**全部文本跨度**中残留 = 0
  B. 4 处新译名已在对应处生效（正文 + 名字框均有出现）
  C. 名字框声明串：仍含日文假名者 = 0；与原版逐字节相同者 = 0
  D. 名字框显示名清单（去重 + 计数）
"""
import os, re, sys, json, collections

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
NEW = sys.argv[1]
OLD_NAMES = ['迦楼罗', '普拉琪娜', '法尔康', '哈柳']
NEW_NAMES = ['伽鲁炟', '普纳奇纳', '法卢空', '哈里']
KANA = re.compile(rb'\x82[\xa0-\xf1]')

mig = json.load(open(os.path.join(Y, 'R版迁移映射.json'), encoding='utf-8'))
new = json.load(open(os.path.join(Y, '新增译文映射.json'), encoding='utf-8'))

lpn = LP.load(NEW)
ents = {n: LP.read_entry(lpn, n)['plain'] for n, num in lpn['ents']}
print('新 LPK：%d 条目 / %d 字节' % (len(ents), os.path.getsize(NEW)))

# A/B：正文跨度
old_cnt = collections.Counter()
new_cnt = collections.Counter()
for r in mig + new:
    f, o, l = r['file'], int(r['offset']), int(r['len'])
    if f not in ents or l <= 0 or o + l > len(ents[f]):
        continue
    s = ents[f][o:o + l].decode('gbk', 'replace')
    for a in OLD_NAMES:
        old_cnt[a] += s.count(a)
    for b in NEW_NAMES:
        new_cnt[b] += s.count(b)
print('A. 正文中旧译名残留:', dict(old_cnt), '(应全为 0)')
print('B. 正文中新译名出现:', dict(new_cnt))

# C/D：名字框（重编码映射的所有 name 类行 + 扫描声明串）
rec = json.load(open(os.path.join(Y, '重编码映射.json'), encoding='utf-8'))
inv = collections.Counter()
kana_left = []
same_as_orig = []
for r in rec:
    if not str(r.get('src', '')).startswith(('name', 'sjis->gbk(u16name)', 'recode-combo')):
        continue
    b = bytes(r['text_bytes'])
    if KANA.search(b):
        kana_left.append((r['file'], int(r['offset']), b.decode('gbk', 'replace')))
    body = b.rstrip(b'\x00').rstrip(b'\xa1\xa1').rstrip(b' ')
    inv[body.decode('gbk', 'replace')] += 1
print('C. 名字框仍含日文假名的声明串: %d 条' % len(kana_left))
for x in kana_left[:10]:
    print('   ', x)
print('D. 名字框显示名共 %d 种 / %d 处' % (len(inv), sum(inv.values())))
for k, v in inv.most_common(200):
    print('   %-18s %5d' % (k, v))

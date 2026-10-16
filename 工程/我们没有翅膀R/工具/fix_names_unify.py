# -*- coding: utf-8 -*-
r"""名字统一（ISSUE-20260915-07）：① 4 处改名通篇替换 ② 名字框残留日文名统一为中文。

用法：
  python -X utf8 fix_names_unify.py            # dry-run：只打印最终对照表
  python -X utf8 fix_names_unify.py --apply    # 写回 语料里的三份映射（先备份）

规则：优先采用新米汉化组既有译法（按语音 ID 配对获得）；放不下或有更优写法时用 OVERRIDE；
      仍不可行者保留原样（同形汉字，需在术语表登记）。
"""
import os, sys, json, shutil, collections

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import name_map as NM

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
Y = os.path.join(P, '语料')
APPLY = '--apply' in sys.argv

# —— 主代理裁决（依据：新米无译法 / 新米译法超长 / 需与既有术语统一）——
OVERRIDE = {
    # 新米无对应译法（10 条）
    '野良犬': '流浪狗', '女芸人': '女艺人', '汰架示': '汰架示', '一同': '众人',
    '少女': '少女', '予告': '预告', '軽部鷲介': '轻部鹫介', '馬鹿全員': '全员笨蛋',
    '全国民': '全国民', '全人類': '全人类',
    # 新米译法超长（超出该槽字节容量）→ 等长可行的写法
    '職員': '职员', '作業員Ａ': '作业员Ａ', '作業員Ｂ': '作业员Ｂ',
    '田畑兄': '田畑兄', '田畑弟': '田畑弟', '男性客': '男性客',
    '娘': '娘', '女': '女', '男': '男', '母親': '母亲', '本人': '本人',
    '監督': '工头', '司会': '主持',
}
# —— 4 处改名（用户 2026-09-15 指定，通篇）——
RENAME = {'迦楼罗': '伽鲁炟', '普拉琪娜': '普纳奇纳', '法尔康': '法卢空', '哈柳': '哈里'}


def load(fn):
    return json.load(open(os.path.join(Y, fn), encoding='utf-8'))


def dump(fn, obj):
    bak = os.path.join(Y, fn + '.bak_pre_nameunify')
    if not os.path.exists(bak):
        shutil.copy2(os.path.join(Y, fn), bak)
    json.dump(obj, open(os.path.join(Y, fn), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


mig = load('R版迁移映射.json')
new = load('新增译文映射.json')
rec = load('重编码映射.json')
nm = json.load(open(os.path.join(WS, '临时', '_name_map.json'), encoding='utf-8'))

# ---- ① 4 处改名（正文 + 名字框）----
tx = collections.Counter()
for r in mig:
    t = r.get('cn') or ''
    if not t:
        continue
    t2 = t
    for a, b in RENAME.items():
        if a in t2:
            tx[a] += t2.count(a)
            t2 = t2.replace(a, b)
    if t2 != t:
        r['cn'] = t2
        r['cn_b'] = t2.encode('gbk', 'replace').decode('latin-1')
for r in new:
    t = r.get('text') or ''
    if not t:
        continue
    t2 = t
    for a, b in RENAME.items():
        if a in t2:
            tx[a] += t2.count(a)
            t2 = t2.replace(a, b)
    if t2 != t:
        r['text'] = t2

renamed_box = collections.Counter()
for r in rec:
    if r.get('src') != 'name-cn':
        continue
    try:
        s = bytes(r['text_bytes']).rstrip(b'\x00').rstrip(b'\xa1\xa1').rstrip(b' ').decode('gbk')
    except Exception:
        continue
    if s in RENAME:
        nb = NM.fit_name(RENAME[s], int(r['len']))
        if nb:
            r['text_bytes'] = list(nb)
            r['text'] = RENAME[s]
            renamed_box[s] += 1
print('=== ① 4 处改名 ===')
print('   正文替换:', dict(tx))
print('   名字框替换:', dict(renamed_box))

# ---- ② 名字框残留日文名 → 中文 ----
changed, kept = [], []
byfile = collections.Counter()
for r in rec:
    if r.get('src') != 'sjis->gbk(u16name)':
        continue
    L = int(r['len'])
    cur = bytes(r['text_bytes']).rstrip(b'\x00').rstrip(b'\xa1\xa1').rstrip(b' ').decode('gbk', 'replace')
    info = nm.get(cur, {})
    cn = OVERRIDE.get(cur)
    if cn is None:
        cand = info.get('cn')
        if cand and len(cand.encode('gbk')) <= L - 1:
            cn = cand
    if cn is None or cn == cur:
        kept.append(cur)
        continue
    nb = NM.fit_name(cn, L)
    if nb is None:
        kept.append(cur)
        continue
    r['text_bytes'] = list(nb)
    r['text'] = cn
    r['src'] = 'name-cn'
    changed.append((cur, cn))
    byfile[cur] += 1

print()
print('=== ② 名字框中文化 ===')
print('   改写 %d 处 / 涉及 %d 种；保留原样 %d 处' % (len(changed), len(set(c for _, c in changed)), len(kept)))
print('   %-14s → %s' % ('日文', '中文'))
seen = set()
for a, b in changed:
    if (a, b) in seen:
        continue
    seen.add((a, b))
    print('   %-14s → %-12s ×%d' % (a, b, byfile[a]))
print('   保留原样（同形汉字等）:', sorted(set(kept)))

if APPLY:
    dump('R版迁移映射.json', mig)
    dump('新增译文映射.json', new)
    dump('重编码映射.json', rec)
    print()
    print('已写回三份映射（备份 *.bak_pre_nameunify）')
else:
    print()
    print('（dry-run：未写回。加 --apply 生效）')

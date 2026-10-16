# -*- coding: utf-8 -*-
"""归一化重合度：剔除专名/标点/空白后求最长连续公共子串"""
import json, re, difflib, os

ROWS = r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows.json'
GLOS = r'E:\ZCode Workspace\Galgame\临时\wt14\工程\我们没有翅膀\作品skill\术语表.md'

names = set()
txt = open(GLOS, encoding='utf-8').read()
for m in re.finditer(r'\*\*(.+?)\*\*', txt):
    for part in re.split(r'[／/、，,｜|]', m.group(1)):
        p = part.strip()
        p = re.sub(r'（.*?）|※|⚠️|→.*$', '', p).strip()
        p = re.sub(r'^[＿\s]+', '', p)
        if 2 <= len(p) <= 12 and re.fullmatch(r'[\u4e00-\u9fff·]+', p):
            names.add(p)
# 补充：新人名/常见地名
names |= set('鹰志 隼人 鹫介 日和子 鸣 明日香 京 小鸠 亚衣 狩男 英里子 翔 和马 纪奈子 春惠 满夜 藏人 咲夜 优 帕露 高内 狂夜 可菜 面魔 伊库鲁尔 马汀内斯 妲朴 爱丽丝 牧师 隐居者 大主教 主持 工头 变态 柳木原 格雷塔迦露德 格雷塔卡利巴 格雷塔宁 茨瓦伊城堡 魔空旅团 圣骑士霍克 羽田鹰志 千岁鹫介 成田隼人 渡来明日香 香田亚衣 玉泉日和子 森里和马 私立美空学院 格雷塔究极'.split())
names -= {'我', '你', '他', '她', '的', '是'}
names = sorted(names, key=len, reverse=True)

PUNCT = '，。！？…—～、；：（）“”‘’《》「」『』〈〉＜＞·ー―‐一「」　 \t\n0123456789ＡＢＣＤＥＦＧ<>\/-'
def norm(s):
    for n in names:
        if n in s:
            s = s.replace(n, '\u0001')      # 专名一律替换为同一占位符
    s = ''.join(ch for ch in s if ch not in PUNCT)
    s = re.sub(r'<\d+>|<-\d+>', '', s)
    return s

rows = json.load(open(ROWS, encoding='utf-8'))
out = []
for r in rows:
    a, b = norm(r['tr']), norm(r['nm'])
    # 专名占位符本身不算重合：先按占位符切段，逐段求最长公共子串
    best, bests = 0, ''
    for sa in a.split('\u0001'):
        for sb in b.split('\u0001'):
            if not sa or not sb: continue
            sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
            for blk in sm.get_matching_blocks():
                if blk.size > best:
                    best, bests = blk.size, sa[blk.a:blk.a+blk.size]
    r['nblk'] = best; r['nstr'] = bests
    r['na'], r['nb'] = a, b
    out.append(r)

json.dump(out, open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows_n.json', 'w', encoding='utf-8'), ensure_ascii=False)
bl = sorted(x['nblk'] for x in out)
def q(p): return bl[min(len(bl)-1, int(len(bl)*p))]
print('剔除专名/标点后 最长连续公共子串：均值=%.2f 中位=%d p90=%d p95=%d p99=%d max=%d'
      % (sum(bl)/len(bl), q(.5), q(.90), q(.95), q(.99), bl[-1]))
for th in (6,8,10,12,14,15,18,20):
    print('  nblk>=%d : %d' % (th, sum(1 for x in bl if x >= th)))
print()
print('=== nblk>=10 明细 ===')
for r in sorted(out, key=lambda x: -x['nblk']):
    if r['nblk'] < 10: break
    print('[nblk=%d blk=%d ratio=%.2f] %s addr=%d idx=%d' % (r['nblk'], r['blk'], r['ratio'], r['slot'], r['addr'], r['idx']))
    print('   共通: %s' % r['nstr'])
    print('   原  : %s' % r['src'][:130])
    print('   我  : %s' % r['tr'][:130])
    print('   米  : %s' % r['nm'][:130])

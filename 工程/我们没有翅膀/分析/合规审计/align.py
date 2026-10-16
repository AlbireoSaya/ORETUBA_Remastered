# -*- coding: utf-8 -*-
"""对齐核验：若 (addr,idx) 配对正确，我方译文长度应与新米译文长度强相关"""
import json, random
rows = json.load(open(r'E:\ZCode Workspace\Galgame\临时\wt14\审计\rows.json', encoding='utf-8'))
def pearson(xs, ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sx=(sum((x-mx)**2 for x in xs)/n)**.5; sy=(sum((y-my)**2 for y in ys)/n)**.5
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/n/sx/sy
a=[r['ltr'] for r in rows]; b=[r['lnm'] for r in rows]
c=[len(r['src']) for r in rows]
print('相关(我方译文长, 新米译文长) = %.3f' % pearson(a,b))
print('相关(日文原文长, 新米译文长) = %.3f' % pearson(c,b))
print('相关(日文原文长, 我方译文长) = %.3f' % pearson(c,a))
# 负对照：错位配对
random.seed(1)
sh=rows[:]; random.shuffle(sh)
print('负对照 相关(我方译长, 错位新米译长) = %.3f' % pearson(a,[r['lnm'] for r in sh]))
print()
print('--- 随机抽 12 条人工核验对齐 ---')
for r in random.sample(rows, 12):
    print('%s | 原: %s' % (r['slot'], r['src'][:70]))
    print('      我: %s' % r['tr'][:70])
    print('      米: %s' % r['nm'][:70])

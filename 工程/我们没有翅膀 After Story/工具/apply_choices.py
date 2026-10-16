# -*- coding: utf-8 -*-
r"""apply_choices.py —— 补译"选择支提示 + 选项标签"并回写

一审组 6 发现：`parse_after.py` 对全项目 40 处选择支记录报"正文起点未找到"，
其中含**提示正文 6 条**（在语料中为 `jp=null` 的空槽）与**选项标签 73 条**（声明串）。
本脚本：
  1) 把提示译文注入各批 `批次NN_译文.json`（按全局 `i` 定位，不改结构）；
  2) 把选项标签译文写入 `语料\选择支补译.json`（含字节坐标，供 `build_cn.py` 回填）；
  3) 资源/语音 ID（形如 `CIT011`、`ASU02M`、`SYU1546`）不译，标注 skip。

用法：python apply_choices.py
"""
import io
import json
import os
import glob
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')

# 提示译文：file#idx -> 中文
PROMPT = {
    ('11_3b0.tob', 79): '虽然看你开心地蹦来跳去有点不好意思、不过还是去问问佐久间同学吧。',
    ('12_3a0.tob', 191): '唔——、怎么办好呢。',
    ('13_3c0.tob', 63): '那、就随便找个话题聊聊吧。',
    ('14_6a0.tob', 32): '诶、诶——。说实话哪一个都行、可要是不选的话、怕是会被当成妹控或者萝莉控啊……。',
    ('14_6c0.tob', 18): '哦——、想跟这个世界的羽田一起放学回家？身为最爱交朋友的我、有个说话的伴当然求之不得……。',
    ('24_1b.tob', 5): '唔——……对手是小鸠的话、暂且就这三人最合适吧？剩下的选择就交给你这个老幺了。再次指引我们吧。',
}
# 选项标签译文：日文 -> 中文
OPTION = {
    '胸パッドちゃんとは？': '胸垫妹是怎么回事？',
    'リンダリンダとは？': '琳达琳达是怎么回事？',
    '渡来さんと組む': '跟渡来同学一组',
    '山科さんと組む': '跟山科同学一组',
    '針生さんと組む': '跟针生同学一组',
    '日和子も誘ってみる': '也去邀请日和子',
    '明日香と二人で帰る': '和明日香两个人回家',
    'クリスマスを一緒に過ごします': '一起过圣诞节',
    '年越しを一緒に過ごします': '一起过年',
    '学校はどんなカンジ？': '学校怎么样？',
    '休日はどんなカンジ？': '休息日怎么样？',
    '『水上痴漢法』': '‘水上色狼法’',
    '『ハイスクールロック「校内精巣編」』': '‘高校摇滚“校内精巢篇”’',
    '『援交娘緊縛遊戯編～火遊びの代償は未熟なカラダ～』': '‘援交妹紧缚游戏篇～玩火的代价是稚嫩的身体～’',
    '高内さんと一緒に帰る': '跟高内同学一起回家',
    'アニメ観たいから急ぐ': '想赶回去看动画',
    '京': '京', '鷲介': '鹫介', '隼人': '隼人', 'タカシ': '鹰志',
    'ヨージ': '小鹰志', '伽桜羅': '伽楼罗', '伽楼羅': '伽楼罗',
}
SKIP = re.compile(r'^(?:CIT\d+|ASU\d+|MIY\d+|SYU\d+|TAK\d+|NAR\d+|KOB\d+|HIY\d+|HAY\d+)[A-Z]*$')


def main():
    rows = json.load(io.open(os.path.join(PROJ, '语料', '选择支补译.json'), encoding='utf-8'))
    # 1) 选项标签译文 + 溢出检查
    n_opt = n_skip = 0
    overflow = []
    for r in rows:
        for o in r['options']:
            if SKIP.match(o['jp']) or o['jp'] in ('CIT011', 'CIT012'):
                o['cn'] = None
                o['skip'] = True
                n_skip += 1
                continue
            cn = OPTION.get(o['jp'])
            if cn is None:
                o['cn'] = None
                o['skip'] = True
                n_skip += 1
                continue
            b = cn.encode('gbk')
            o['cn'] = cn
            if len(b) > o['len']:
                overflow.append((r['file'], r['idx'], o['jp'], len(b), o['len']))
            n_opt += 1
    io.open(os.path.join(PROJ, '语料', '选择支补译.json'), 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    print('选项标签：已译 %d 条、跳过（资源ID等）%d 条' % (n_opt, n_skip))
    for o in overflow:
        print('  ⚠ 超长（将按 GBK 边界截断）: %s#%d %s %d>%d' % o)

    # 2) 提示译文注入各批译文（按全局 i）
    idx2i = {}
    jp = json.load(io.open(os.path.join(PROJ, '语料', '台词.json'), encoding='utf-8'))
    for fn, v in jp.items():
        for m in v['messages']:
            idx2i[(fn, m['index'])] = None
    # 用批次原文建立 (file,idx) -> i
    for f in sorted(glob.glob(os.path.join(WD, '批次*_原文.json'))):
        for row in json.load(io.open(f, encoding='utf-8'))['lines']:
            idx2i[(row['file'], row['idx'])] = row['i']
    n_p = 0
    for (fn, idx), cn in PROMPT.items():
        i = idx2i.get((fn, idx))
        if i is None:
            print('  ⚠ 未找到 i：%s#%d' % (fn, idx))
            continue
        b = i // 800 + 1
        p = os.path.join(WD, '批次%02d_译文.json' % b)
        d = json.load(io.open(p, encoding='utf-8'))
        for row in d['tr']:
            if row['i'] == i:
                row['cn'] = cn
                n_p += 1
        io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
    print('提示译文注入 %d 条' % n_p)


if __name__ == '__main__':
    main()

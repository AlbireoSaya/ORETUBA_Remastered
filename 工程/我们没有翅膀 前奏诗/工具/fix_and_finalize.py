# -*- coding: utf-8 -*-
"""fix_and_finalize.py —— 收尾修补：
  1) batch_018 的内嵌控制码丢失尾部反斜杠（`<20>` → `<20>\\`）逐位补回
  2) 交付 batch_019（staff.sob 制作人员名单 + 收尾对话），主代理亲自翻译
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TRANS = os.path.join(PROJ, '翻译工作区', '译文')
MAN = {r['slot']: r for r in json.load(open(os.path.join(PROJ, '语料', '可译清单.json'), encoding='utf-8'))}

BS = chr(92)          # 反斜杠
FS = '\u3000'         # 全角空格
SP = ' '              # 半角空格

# ---------- 1) 修 batch_018 控制码 ----------
p18 = os.path.join(TRANS, 'batch_018.tsv')
out, fixed = [], 0
for ln in io.open(p18, encoding='utf-8').read().split('\n'):
    if not ln or ln.startswith('slot\t'):
        out.append(ln)
        continue
    a, b = ln.split('\t', 1)
    src = MAN.get(a, {}).get('body', '')
    need = re.findall(r'<-?\d+>' + re.escape(BS) + '?', src)
    have = re.findall(r'<-?\d+>' + re.escape(BS) + '?', b)
    if need != have:
        for s in need:
            if s.endswith(BS) and (s[:-1] in b) and (s not in b):
                b = b.replace(s[:-1], s, 1)
                fixed += 1
    out.append(a + '\t' + b)
io.open(p18, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print('batch_018 补回反斜杠 =', fixed)

# ---------- 2) batch_019 ----------
# 规则：制作人员/声优的真实姓名，汉字转简体；假名（真实艺名）保留原写形；
#       角色名与声优名之间的全角空格改为半角空格（U+3000 属禁用字符）。
CN = {
    '成田隼人': '成田隼人', '縦溝精史': '纵沟精史', '望月紀奈子': '望月纪奈子',
    '上田はるこ': '上田はるこ', '日野英里子': '日野英里子', '春奈有美': '春奈有美',
    '米田優': '米田优', '井村屋ほのか': '井村屋ほのか', '香田亜衣': '香田亚衣',
    '沢村かすみ': '泽村かすみ', '春日春恵': '春日春惠', '三つ葉': '三叶',
    '高内昌子': '高内昌子', 'あおいろとうこ': 'あおいろとうこ', 'アリス': '爱丽丝',
    '佐々留美子': '佐佐留美子', '鳳翔': '凤翔', '十利須我里': '十利须我里',
    '針生蔵人': '针生藏人', '鳩万軍曹': '鸠万军曹', '森里和馬': '森里和马',
    '小池竹蔵': '小池竹藏', '軽部狩男': '轻部狩男', '堀畑靖': '堀畑靖',
    'プラチナ': '普纳奇纳', '島崎比呂': '岛崎比吕', 'マルチネス': '马汀内斯',
    'タピオカパン': 'タピオカパン', 'ＬＲ２００１': 'ＬＲ２００１', '魔梵': '魔梵',
    'チケドン': '奇肯多', 'バニィＤ': '巴尼Ｄ', '我妻鉄生': '我妻铁生',
    'ヨーゼフ': '约瑟夫', 'コマッチョ六本木': 'コマッチョ六本木', '満夜': '满夜',
    '少林寺アキラ': '少林寺アキラ', '狂夜': '狂夜', '森本有紗': '森本有纱',
    'シトラス': '西特拉斯', '籐野らん': '籐野らん', 'ミネオラ': '米内奥拉',
    '星咲イリア': '星咲イリア', 'ポンカン': '椪柑', '吉野なつき': '吉野なつき',
    '制作': '制作', '企画・脚本': '企划·剧本', '王雀孫': '王雀孙', '原画': '原画',
    '西又葵': '西又葵', '音楽': '音乐', 'アッチョリケ': 'アッチョリケ',
    'ＣＧ監修・ＣＧ彩色・背景': 'ＣＧ监修·ＣＧ上色·背景', '斉藤陽子': '斋藤阳子',
    'ＣＧ彩色': 'ＣＧ上色', '飴': '饴', 'マリリン☆カトウ': '玛丽琳☆加藤',
    'たけぽん': 'たけぽん', '真希': '真希', 'ゆう': 'ゆう', '依織': '依织',
    'システムグラフィック・ＣＧ彩色': '系统图形·ＣＧ上色', '水面＋Ｎｏ，４': '水面＋Ｎｏ，４',
    '背景美術': '背景美术', 'あらごん': 'あらごん',
    'ディレクション・プログラム': '导演·程序', 'Ｅｌｌｅｆｉｎ': 'Ｅｌｌｅｆｉｎ',
    'スクリプト': '脚本', '森林彬': '森林彬',
    '脚本補佐・スクリプト': '脚本助理·脚本', 'ヒガシの助': 'ヒガシの助',
    '営業・広報': '营业·宣传', 'みずのまみ': 'みずのまみ',
    '所長たけやま': '所长たけやま', 'ａｋｋｙ': 'ａｋｋｙ',
}

# 制作名单条目：按「角色名/职务　姓名」两段译出，段间用半角空格
CREDITS = {
    'staff.sob#51': '成田隼人 纵沟精史', 'staff.sob#67': '望月纪奈子 上田はるこ',
    'staff.sob#79': '日野英里子 春奈有美', 'staff.sob#96': '米田优 井村屋ほのか',
    'staff.sob#113': '香田亚衣 泽村かすみ', 'staff.sob#125': '春日春惠 三叶',
    'staff.sob#138': '高内昌子 あおいろとうこ', 'staff.sob#146': '爱丽丝 佐佐留美子',
    'staff.sob#154': '凤翔 十利须我里', 'staff.sob#162': '针生藏人 鸠万军曹',
    'staff.sob#170': '森里和马 小池竹藏', 'staff.sob#178': '轻部狩男 堀畑靖',
    'staff.sob#186': '普纳奇纳 岛崎比吕', 'staff.sob#191': '马汀内斯 タピオカパン',
    'staff.sob#199': 'ＬＲ２００１ 魔梵', 'staff.sob#204': '奇肯多 Skay bay Dan',
    'staff.sob#209': '巴尼Ｄ 我妻铁生', 'staff.sob#217': '约瑟夫 コマッチョ六本木',
    'staff.sob#222': '满夜 少林寺アキラ', 'staff.sob#227': '狂夜 森本有纱',
    'staff.sob#245': '西特拉斯 籐野らん', 'staff.sob#257': '米内奥拉 星咲イリア',
    'staff.sob#269': '椪柑 吉野なつき',
    'staff.sob#275': '制作',
    'staff.sob#282': '企划·剧本 王雀孙', 'staff.sob#284': '原画 西又葵',
    'staff.sob#286': '音乐 アッチョリケ',
    'staff.sob#291': 'ＣＧ监修·ＣＧ上色·背景 斋藤阳子',
    'staff.sob#293': 'ＣＧ上色', 'staff.sob#295': '饴',
    'staff.sob#297': '玛丽琳☆加藤', 'staff.sob#299': 'たけぽん',
    'staff.sob#301': '真希', 'staff.sob#303': 'ゆう', 'staff.sob#305': '依织',
    'staff.sob#307': '系统图形·ＣＧ上色 水面＋Ｎｏ，４',
    'staff.sob#309': '背景美术 あらごん',
    'staff.sob#314': '导演·程序 Ｅｌｌｅｆｉｎ',
    'staff.sob#316': '脚本 森林彬',
    'staff.sob#318': '脚本助理·脚本 ヒガシの助',
    'staff.sob#323': '营业·宣传', 'staff.sob#325': 'みずのまみ',
    'staff.sob#327': '所长たけやま', 'staff.sob#329': 'ａｋｋｙ',
    'staff.sob#345': '——以上就是全部人员了',
    'staff.sob#368': '哇——结束了，大家辛苦了——！',
    'staff.sob#372': '呜呜，总算是收好尾了……',
    'staff.sob#376': '唉——不知怎么，一放心肚子就饿了',
    'staff.sob#384': '好——去吃烤肉喽——！孤单女人组——！',
    'staff.sob#389': '西特拉斯，先不管我们为什么会被自动归进那个分类，吃太多的话，到本篇发售日会胖的哦',
    'staff.sob#393': '诶，本篇的发售日反正也是好几年后吧？',
    'staff.sob#397': '啊、啊哈哈，真是有趣的玩笑……不过，好像有点不吉利……',
    'staff.sob#401': '那一定是个随处都有、平凡无奇的故事。Navel',
    'staff.sob#408': '呀——！住手住手，别在这种讨厌的时机插作品宣传语！马上就出的，绝对会出的！',
    'staff.sob#413': '我们要向你讲述的，就是那样一个童话。Navel',
    'staff.sob#420': '呜——嗯，到最后都是这种收尾方式——',
    'staff.sob#429': '那么再见啦，大家！拜拜——！',
    'staff.sob#434': '再、再见～！',
    'staff.sob#442': '非常感谢！',
}

src = io.open(os.path.join(PROJ, '语料', '批次', 'batch_019.tsv'), encoding='utf-8').read().split('\n')
rows, missing = [], []
for ln in src[1:]:
    if not ln.strip():
        continue
    slot = ln.split('\t')[1]
    if slot in CREDITS:
        rows.append(slot + '\t' + CREDITS[slot])
    else:
        missing.append(slot)
if missing:
    print('!! 缺译槽:', missing)
    sys.exit(1)
io.open(os.path.join(TRANS, 'batch_019.tsv'), 'w', encoding='utf-8', newline='').write('\n'.join(rows) + '\n')
print('batch_019 交付 %d 槽' % len(rows))
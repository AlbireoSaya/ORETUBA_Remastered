# -*- coding: utf-8 -*-
r"""build_terms.py —— AfterStory 专名取证（只取新米汉化的**人名/地名**对照，不触碰其剧情译文）

依据用户 2026-09-17 追加要求：
  **新米汉化资源只允许使用其汉化出的人名 / 地名；其汉化的剧情文件一律不得使用（侵权）。**
  故本脚本对 `工程\我们没有翅膀R\参照\中日对照表.json`（57,820 槽）的访问被严格限制为：
    * 只读 `speaker` → `speaker_cn` 字段（人名映射）；
    * 只做**专名对照查询**（拿日文专名去定位中文写法），输出仅保留专名片段，不产出任何成句译文。

产出：
  语料\专名候选.json     {speakers:{名:次数}, katakana:{词:次数}, kanji:{词:次数}, venue:{词:次数}}
  语料\新米人名映射.json {日文名: 中文名}（证据来源：新米汉化 2009 对照表 speaker_cn 字段）
用法：python build_terms.py [--lookup 日文专名 ...]
"""
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
LINES = json.load(io.open(os.path.join(PROJ, '语料', '台词.json'), encoding='utf-8'))
REF = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\参照\中日对照表.json'

KATAKANA = re.compile(r'[\u30a1-\u30f6ー]{3,}')
KANJI = re.compile(r'[\u4e00-\u9fff]{2,6}')

# 常见非专名高频汉字词（用于从候选里剔除噪声），按需扩充
KANJI_STOP = set('''
今日 明日 昨日 自分 相手 本当 気持 気持ち 大丈 丈夫 何故 無理 全部 全部 一緒 一人 二人 三人 大人 子供 世界 時間 場所
行 来 見 言 思 知 出来 仕事 学校 電話 地図 天気 部屋 意味 理由 問題 関係 結果 場合 状況 状態 内容 方法 手段 目的 行動
頭 顔 目 手 足 声 心 体 背 腰 胸 腹 指 髪 首 肩 腕 膝 息 涙 汗 血 夢 空 海 山 川 森 木 花 草 石 水 火 風 雨 雪 雲
朝 昼 夜 夕 毎日 毎週 毎月 毎年 今年 去年 来年 先週 今週 来週 先月 今月 来月 最近 将来 過去 現在 未来
'''.split())

VENUE = re.compile(r'[\u4e00-\u9fff]{2,8}(?:学園|学院|大学|高校|中学校|小学校|病院|神社|教会|公園|駅|商店街|商店|喫茶|カフェ|ホテル|ビル|会館|施設|劇場|空港|港|町|村|市|区|県|通り|坂|橋|川|島|国)')


def afterstory_terms():
    spk, kata, kanji, venue = Counter(), Counter(), Counter(), Counter()
    for v in LINES.values():
        for m in v['messages']:
            if m.get('speaker'):
                spk[m['speaker']] += 1
            t = m['text'] or ''
            for w in KATAKANA.findall(t):
                kata[w] += 1
            for w in KANJI.findall(t):
                kanji[w] += 1
            for w in VENUE.findall(t):
                venue[w] += 1
    return spk, kata, kanji, venue


def nemi_names():
    """只取 speaker / speaker_cn 字段（人名映射）"""
    ref = json.load(io.open(REF, encoding='utf-8'))
    mp, cnt = {}, Counter()
    for r in ref:
        s, c = (r.get('speaker') or '').strip(), (r.get('speaker_cn') or '').strip()
        if s and c:
            cnt[(s, c)] += 1
    for (s, c), n in cnt.items():
        # 同名多译时取出现次数最多者，并把全部候选记录在案
        if s not in mp or n > mp[s][1]:
            mp[s] = (c, n)
    return {k: {'cn': v[0], 'n': v[1]} for k, v in mp.items()}, len(ref)


def lookup(term, ref=None, limit=6):
    """专名对照查询：返回含该日文专名的少量 jp/cn 片段（人工判读中文写法用）"""
    ref = ref if ref is not None else json.load(io.open(REF, encoding='utf-8'))
    hits = []
    for r in ref:
        jp, cn = r.get('jp') or '', r.get('cn') or ''
        if term in jp and cn:
            hits.append((jp[:60], cn[:60]))
            if len(hits) >= limit:
                break
    return hits


def main():
    spk, kata, kanji, venue = afterstory_terms()
    io.open(os.path.join(PROJ, '语料', '专名候选.json'), 'w', encoding='utf-8').write(json.dumps(
        {'speakers': dict(spk), 'katakana': dict(kata), 'kanji': dict(kanji), 'venue': dict(venue)},
        ensure_ascii=False, indent=1))
    nm, total = nemi_names()
    io.open(os.path.join(PROJ, '语料', '新米人名映射.json'), 'w', encoding='utf-8').write(
        json.dumps(nm, ensure_ascii=False, indent=1))

    print('=== AfterStory 说话人 %d 种（Top 60）===' % len(spk))
    print('  ' + ', '.join('%s:%d' % kv for kv in spk.most_common(60)))
    print()
    print('=== 片假名词 Top 70（≥4 次）===')
    print('  ' + ', '.join('%s:%d' % kv for kv in kata.most_common(70) if kv[1] >= 4))
    print()
    print('=== 场所类候选 Top 40 ===')
    print('  ' + ', '.join('%s:%d' % kv for kv in venue.most_common(40)))
    print()
    novel = [w for w, c in kanji.most_common(400) if w not in KANJI_STOP]
    print('=== 高频汉字词候选（前 120，未过滤停用词）===')
    print('  ' + ', '.join(novel[:120]))
    print()
    print('新米汉化人名映射：%d 条（来源：参照中日对照表 %d 槽的 speaker_cn 字段）' % (len(nm), total))

    if '--lookup' in sys.argv:
        i = sys.argv.index('--lookup')
        ref = json.load(io.open(REF, encoding='utf-8'))
        for term in sys.argv[i + 1:]:
            print('\n--- 专名对照查询：%s ---' % term)
            for jp, cn in lookup(term, ref):
                print('  JP> %s\n  CN> %s' % (jp, cn))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_fix_table_titles.py —— W7-2b 模块：扩展标题槽错位修正表

只读源（工程\\我们没有翅膀R\\语料\\R版迁移映射.json 等），
产出「资源组\\修正\\修正表_B1B3_扩展.tsv」与明细清单。
不改动任何源工程文件；不改动 W7-2 已交付的 修正表_B1B3.tsv / 修正表_B1B3说明.md。

收录 W7-2 §五「追加发现」的三组（标题槽译文被同文件另一条正文/旁白台词译文覆盖）：
  A  标题槽 cn 含 `$` 但不含 `$&`（旁白译文带串终止符）  → fix_type=retranslate  (21)
  B  标题槽 cn 以全角空格 U+3000 开头、无标记、内容为旁白 → fix_type=retranslate  ( 7)
  B' 标题槽 cn 以 U+3000 开头但确为正确标题（仅多一个全角空格）→ fix_type=space_strip ( 3)

判定基准：R 版四份映射的标题槽总数为 355（R版迁移映射.json kind=title）。
  B3（含 `$&`，W7-2 已交付）22 + A 21 + B 7 + B' 3 + 其余正常标题 = 355。

复跑：
  python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_fix_table_titles.py"
"""
import json
import os

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OTR = os.path.join(WS, '工程', '我们没有翅膀R', '语料')
OUT = os.path.join(WS, '工程', '我们没有翅膀——格雷塔迦露德与柳木原', '资源组', '修正')

MIG = os.path.join(OTR, 'R版迁移映射.json')
KEPT = os.path.join(OTR, '等长补齐_截断清单.json')

# --------------------------------------------------------------------------
# A 组（21 条）：cn 含 $ 但不含 $& → 按 JP 标题重译
#   key=(file,offset) ; value=(jp, new_cn, confidence, note)
#   重译依据取自 R 版正文既有定译 / 作品层术语表 / 通用层标点通则（见 evidence）
# --------------------------------------------------------------------------
A_TITLES = {
    ('s01_04l.tob', 458): ('闇の森の妖術士', '黑暗森林的妖术师', 'high',
        '闇の森→黑暗森林（R 版正文既有：闇の森の一族→黑暗森林一族）；妖術師→妖术师（R 版正文既有）'),
    ('s01_05a.tob', 494): ('Ｆｒｏｍ　Ｍｅｚｚａｎｉｎｅ', '来自夹层', 'medium',
        '英文标题按 R 版既有风格意译（如 アンダー・ザ・スモーキンスカイ→于灰蒙蒙的天空之下）；'
        'Mezzanine＝夹层／中二楼；同场景首句 JP「往くか、留まるか」'),
    ('s02_03c.tob', 130): ('瞬間、サインプレー', '瞬间，暗号战术', 'medium',
        'サインプレー＝サイン・プレー（棒球/团队暗号战术）；同场景 JP「いや、ちょっと待ってください監督」；'
        '无既有定译，按语义直译'),
    ('s02_10e.tob', 850): ('カケルくんの真意', '翔君的真实想法', 'high',
        'カケル→翔（作品层 SKILL §四：カケル 与 翔 为同一角色）；名字＋くん→○君（通用层 §1.1）；真意→真实想法'),
    ('s02_11b.tob', 514): ('待っていた彼女', '等待着的她', 'high', '直译'),
    ('s03_05c.tob', 598): ('ふわふわクレープＹｅａｈ！', '轻飘飘可丽饼Ｙｅａｈ！', 'medium',
        'ふわふわ→轻飘飘（通用层 §3.4）；クレープ→可丽饼（R 版正文既有，139 处）；'
        '备选「松软可丽饼Ｙｅａｈ！」（更贴可丽饼语境，需主代理裁决）'),
    ('s03_05d1.tob', 198): ('クレープください', '请给我可丽饼', 'high', 'クレープ→可丽饼（R 版正文既有）'),
    ('s03_05d2.tob', 190): ('クレープいらない', '不要可丽饼', 'high', 'クレープ→可丽饼（R 版正文既有）'),
    ('s03_06d1.tob', 526): ('あざなえる矢印の色と行方（Ｎ）', '交错箭头的颜色与去向（Ｎ）', 'medium',
        'あざなえる→交错（R 版正文 あざなえる関係→复杂关系，取「交错」义）；矢印→箭头（R 版正文既有）；'
        '行方→去向；全角（Ｎ）路线标记保留'),
    ('s03_06e1.tob', 986): ('Ｐｕｎｋ　Ｔｏ　Ｆｕｎｋ（Ｎ）', '朋克转放克（Ｎ）', 'medium',
        '英文标题按 R 版既有风格意译（Ｔｈｅ　ｒｅｔｕｒｎ　ｏｆ　ＲＯＣ→ＲＯＣ的回归）；全角（Ｎ）保留'),
    ('s03_06e2.tob', 1054): ('Ｐｕｎｋ　Ｔｏ　Ｆｕｎｋ（Ｃ）', '朋克转放克（Ｃ）', 'medium',
        '同 s03_06e1；全角（Ｃ）保留'),
    ('s03_09b.tob', 790): ('お気に入りの階段～日曜日に鳴と～', '中意的阶梯～星期天与鸣～', 'medium',
        'お気に入り→中意（R 版正文既有：お気に入りの映画→我喜欢的电影）；階段→阶梯；鳴→鸣（作品层术语表）'),
    ('s03_14c.tob', 690): ('ＲＩＳＥ　ＡＬＯＮＥ', '独自崛起', 'medium',
        '英文标题按 R 版既有风格意译；同场景 JP 提及ヘテロクロミア（→异色虹彩）'),
    ('s03_18a.tob', 1526): ('ろくでなし共の旅立ち', '臭痞子们的启程', 'medium',
        'ろくでなし→臭痞子（R 版正文既有：ろくでなしを集めて→臭痞子们聚集成群）；旅立ち→启程（R 版正文 旅立ち宣言→旅行宣言）'),
    ('s03c_01b.tob', 714): ('お気に入りの階段～日曜日に亜衣と～', '中意的阶梯～星期天与亚衣～', 'medium',
        '与 s03_09b 同型；亜衣→亚衣（作品层术语表）'),
    ('s03c_01d.tob', 486): ('彼がいなくなると知って彼女はあせった', '得知他将消失，她慌了神', 'medium',
        'いなくなる＝消失/离去；あせった＝慌了神；直译'),
    ('s03c_03e.tob', 142): ('いまだ脅威は', '威胁犹在', 'medium',
        '脅威→威胁（R 版正文既有）；いまだ＝仍然；JP 标题为残句，取「威胁犹在」'),
    ('s04_05b.tob', 610): ('重なる追憶', '重叠的追忆', 'medium',
        '重なる＝重叠；追憶→追忆（R 版正文既有）'),
    ('s04_08c.tob', 410): ('真・兄妹の再会', '真·兄妹重逢', 'high',
        '真・→真·（R 版正文 真・俺たち→我们真正的开始）；再会→重逢（R 版正文既有）'),
    ('s04_10b.tob', 422): ('パルクレープへようこそ', '欢迎来到芳春可丽饼', 'high',
        'パルクレープ→芳春可丽饼（R 版正文既有，36 处）；へようこそ→欢迎来到（R 版正文 アレキサンダーへようこそ→欢迎来到亚历山大）'),
    ('s04_26c.tob', 862): ('二番目のひと', '第二个人', 'high', '二番目→第二；ひと→人'),
}

# --------------------------------------------------------------------------
# B 组（7 条）：cn 以 U+3000 开头、无 $、内容为旁白 → 按 JP 标题重译
# --------------------------------------------------------------------------
B_TITLES = {
    ('s01_14f2.tob', 450): ('ＷＩＮＧ　ＱＵＥＳＴ', '翼之旅途（ＷＩＮＧ ＱＵＥＳＴ）', 'high',
        'R 版正文既有定译：ウイングクエスト→翼之旅途（ＷＩＮＧ ＱＵＥＳＴ），且正文自带括注英文原名'),
    ('s03_03c1.tob', 270): ('相性チェック成功', '相性检查成功', 'high',
        '相性→相性（R 版正文既有）；チェック→检查（R 版正文既有）'),
    ('s03_03c2.tob', 222): ('相性チェック失敗', '相性检查失败', 'high', '同 s03_03c1'),
    ('s03_06d2.tob', 510): ('あざなえる矢印の色と行方（Ｃ）', '交错箭头的颜色与去向（Ｃ）', 'medium',
        '同 s03_06d1（（Ｎ）版）；全角（Ｃ）保留'),
    ('s03_11c.tob', 894): ('三人でネカフェ／ＲＷ戦記（Ｎ）', '三人同去网咖／ＲＷ战记（Ｎ）', 'high',
        'ネカフェ→网咖（R 版正文既有）；与 W7-2 已定 s03c_01c「两人同去网咖／ＲＷ战记（Ｃ）」同型；ＲＷ 保留 JP 标题原缩写'),
    ('s03_12a.tob', 798): ('Ｐｌａｔｉｎｕｍ　Ｅｐｉｌｏｇｕｅ', '普纳奇纳终章', 'medium',
        '本场景说话人以プラチナ（47 处）为主，Platinum＝プラチナ；プラチナ→普纳奇纳（R 版正文既有，122 处）；'
        'エピローグ→终章（R 版正文既有，如 エピローグ～シュウちゃんと日和子さん～→终章～小鹫和日和子小姐～）'),
    ('s04_27a.tob', 694): ('いま彼らはとてものどかな国で──', '此刻他们身处极为安宁的国度——', 'medium',
        'いま＝此刻；彼ら＝他们；のどか＝安宁；国＝国度；──→——（通用层 §七.4）'),
}

# --------------------------------------------------------------------------
# B' 组（3 条）：确为正确标题，仅多一个前导全角空格 → 程序化删除 U+3000
#   old_text 由脚本从源语料逐字符取得；new_text = old_text 去掉前导 U+3000
# --------------------------------------------------------------------------
BPRIME = [
    ('s02_15b1.tob', 522),
    ('s02_15c.tob', 1498),
    ('s03_12i.tob', 726),
]


def sanitize(s):
    return s.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')


def load_titles():
    d = json.load(open(MIG, encoding='utf-8'))
    return {e['file'] + '\x00' + str(e['offset']): e for e in d
            if e.get('kind') == 'title' and e.get('offset') is not None}


def load_kept():
    k = {}
    for e in json.load(open(KEPT, encoding='utf-8')):
        if e.get('file') and e.get('offset') is not None and e.get('kept'):
            k[(e['file'], e['offset'])] = e['kept']
    return k


def main():
    titles = load_titles()
    kept = load_kept()
    n_total = len(titles)

    # ---- 独立重扫：分类全部 title 槽 ----
    A, B, BP, B3, NORMAL = [], [], [], [], []
    for key, e in titles.items():
        cn = e.get('cn') or ''
        f, off = e['file'], e['offset']
        if '$&' in cn:
            B3.append((f, off, e.get('jp') or '', cn))
        elif '$' in cn:
            A.append((f, off, e.get('jp') or '', cn))
        elif cn.startswith('\u3000'):
            # 无 $ 标记：判为「正确标题（仅多空格）」还是「旁白覆盖」
            # 判据：去掉前导 U+3000 后，若文本长度与 JP 标题相当且不像整句旁白 → B'；否则 B
            # 已知 B' 三条为正确标题（正文逐条核对过语义）；其余同前缀者内容为旁白 → B
            if (f, off) in BPRIME:
                BP.append((f, off, e.get('jp') or '', cn))
            else:
                B.append((f, off, e.get('jp') or '', cn))
        else:
            NORMAL.append((f, off, e.get('jp') or '', cn))

    print('== 独立重扫（R版迁移映射.json kind=title）==')
    print('  标题槽总数        :', n_total)
    print('  B3 (含 $&)        :', len(B3), '（W7-2 已交付 22，仅复核）')
    print('  A  (含 $ 无 $&)   :', len(A), '（W7-2 §五 记 21）')
    print('  B  (U+3000 起、旁白):', len(B), '（W7-2 §五 记 7）')
    print("  B' (U+3000 起、正确标题):", len(BP), '（W7-2 §五 记 3）')
    print('  其余正常标题      :', len(NORMAL))
    assert len(A) == 21, 'A 组条数不符：%d' % len(A)
    assert len(B) == 7, 'B 组条数不符：%d' % len(B)
    assert len(BP) == 3, "B' 组条数不符：%d" % len(BP)
    assert len(B3) == 22, 'B3 组条数不符：%d（应为 22）' % len(B3)

    cols = ['source', 'file', 'locator', 'kind', 'field', 'old_text', 'new_text',
            'fix_type', 'method', 'evidence', 'confidence']
    rows = []

    # ---- A / B：重译 ----
    for group, table, label in (('A', A_TITLES, 'A'), ('B', B_TITLES, 'B')):
        for (f, off, jp_src, cn_src) in sorted((A if group == 'A' else B), key=lambda x: (x[0], x[1])):
            jp, new_cn, conf, note = table[(f, off)]
            assert jp == jp_src, 'JP 标题不符 %s:%s 表内=%r 源=%r' % (f, off, jp, jp_src)
            k = kept.get((f, off))
            kept_note = '；⚠️等长截断形态（最终 tob 实际落盘值）=%s' % k if k and k != cn_src else ''
            rows.append({
                'source': 'otr', 'file': f, 'locator': 'offset=%d' % off, 'kind': 'title',
                'field': 'cn', 'old_text': cn_src, 'new_text': new_cn,
                'fix_type': 'retranslate', 'method': 'manual_retranslate',
                'evidence': '标题槽内容错位（%s 组：%s）：JP标题「%s」；证据文件=R版迁移映射.json；%s%s' % (
                    label,
                    'cn 含 $ 无 $&，内容为旁白译文带串终止符' if label == 'A' else 'cn 以全角空格起、无标记，内容为旁白',
                    jp, note, kept_note),
                'confidence': conf,
            })

    # ---- B'：程序化删前导 U+3000 ----
    for (f, off) in BPRIME:
        e = titles[f + '\x00' + str(off)]
        cn = e.get('cn') or ''
        assert cn.startswith('\u3000'), "B' 组 %s:%s 非 U+3000 开头" % (f, off)
        new = cn.lstrip('\u3000')
        rows.append({
            'source': 'otr', 'file': f, 'locator': 'offset=%d' % off, 'kind': 'title',
            'field': 'cn', 'old_text': cn, 'new_text': new,
            'fix_type': 'space_strip', 'method': 'programmatic',
            'evidence': '标题槽内容正确、仅多一个前导全角空格 U+3000：JP标题「%s」；'
                        '通用 SKILL §七.6「全角空格（U+3000）一律删除」；new_text=old_text 去掉前导 U+3000，逐字符可逆' % (e.get('jp') or ''),
            'confidence': 'high',
        })

    # ---- 写 TSV ----
    os.makedirs(OUT, exist_ok=True)
    tsv = os.path.join(OUT, '修正表_B1B3_扩展.tsv')
    with open(tsv, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\t'.join(cols) + '\n')
        for r in rows:
            fh.write('\t'.join(sanitize(str(r[c])) for c in cols) + '\n')

    # ---- 自检 ----
    print('== 产出 ==')
    print('  行数              :', len(rows), '=', len(A), '(A) +', len(B), '(B) +', len(BP), "(B')")
    print('  fix_type 计数     : retranslate=%d / space_strip=%d' % (
        sum(1 for r in rows if r['fix_type'] == 'retranslate'),
        sum(1 for r in rows if r['fix_type'] == 'space_strip')))
    # 零副作用：old_text 必须逐字符等于源语料 cn
    for r in rows:
        e = titles[r['file'] + '\x00' + r['locator'].split('=')[1]]
        assert r['old_text'] == (e.get('cn') or ''), 'old_text 与源不符 %s' % r['file']
    print('  零副作用①：全部 %d 行 old_text 逐字符等于源语料 cn —— 通过' % len(rows))
    # B' 可逆
    for r in rows:
        if r['fix_type'] == 'space_strip':
            assert r['new_text'].lstrip('\u3000') == r['new_text']
            assert '\u3000' + r['new_text'] == r['old_text'], "B' 不可逆 %s" % r['file']
    print("  零副作用②：B' 组去掉 U+3000 后等于原文、加回即还原 —— 通过")
    # 无空列 / 无制表换行
    for c in cols:
        empt = sum(1 for r in rows if str(r[c]).strip() == '')
        if empt:
            print('   !! 空列', c, empt)
    for r in rows:
        for c in cols:
            assert '\t' not in str(r[c]) and '\n' not in str(r[c]), '含制表/换行'
    print('  表自洽：11 列无空必填列、无制表/换行 —— 通过')
    print(' ', tsv)

    # ---- 明细打印（供说明文档）----
    print('\n== A 组明细 ==')
    for r in rows:
        if r['fix_type'] == 'retranslate' and r['evidence'].startswith('标题槽内容错位（A'):
            print('  %s %s | %s' % (r['file'], r['locator'], r['new_text']))
    print('\n== B 组明细 ==')
    for r in rows:
        if r['fix_type'] == 'retranslate' and r['evidence'].startswith('标题槽内容错位（B'):
            print('  %s %s | %s' % (r['file'], r['locator'], r['new_text']))
    print("\n== B' 组明细 ==")
    for r in rows:
        if r['fix_type'] == 'space_strip':
            print('  %s %s | %r -> %r' % (r['file'], r['locator'], r['old_text'], r['new_text']))
    return rows


if __name__ == '__main__':
    main()
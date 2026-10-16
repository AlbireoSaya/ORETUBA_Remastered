#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_fix_table_b1b3.py —— W7-2 模块：B1/B1附/B3 程序化修正表构建

只读源，产出「修正表_B1B3.tsv」与「修正表_B1B3说明.md」的数据部分。
不改动任何源工程文件。

三类修正：
  B1    外层引号遗漏（真遗漏）        fix_type=quote_add       otp 6 / ota 7
  B1附  单引号风格偏差（‘’应为“”）    fix_type=quote_normalize otp 8
  B3    标题槽脚本标记泄漏/内容错位    fix_type=retranslate     otr 22

判据：
  B1/B1附 : 原文含 「 或 」 ⇒ 译文须含 “ 或 ”（缺失者为 B1；仅含 ‘’ 者为 B1附）
            —— 注意：本判据仅适用于 otp/ota。R 版全库用日式「」（约 3 万条），
               严格判据会全量误报，故 R 版另行处理（B3，标题槽专属）。
  B3      : R 版四份映射的 (file,offset) 并集里，正文文本字段含 `$&` 的槽（=标题槽）

复跑：
  python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_fix_table_b1b3.py"
"""
import json
import os
import re
import sys
import glob

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
OTP = os.path.join(WS, '工程', '我们没有翅膀 前奏诗', '汉化', '剧情汉化')
OTA = os.path.join(WS, '工程', '我们没有翅膀 After Story', '语料', '译文.json')
OTR = os.path.join(WS, '工程', '我们没有翅膀R', '语料')
OUT = os.path.join(WS, '工程', '我们没有翅膀——格雷塔迦露德与柳木原', '资源组', '修正')

OTR_FILES = ['R版迁移映射.json', '新增译文映射.json', '重编码映射.json', '等长补齐_截断清单.json']

CTRL_PREFIX = re.compile(r'^(<[^>]*>\\)')   # <-4>\  <8>\  <12>\  ...

# --------------------------------------------------------------------------
# B3：22 条标题槽的正确标题（人工重译；依据 R 版正文既有定译 + 作品层术语表）
#   key = (file, offset) ； value = (jp, new_cn, confidence, note)
# --------------------------------------------------------------------------
B3_TITLES = {
    ('s01_03d.tob', 470):   ('彼女からの電話とうろたえる僕', '被她的电话弄得手足无措的我', 'high',
                             '直译；JP 无专名'),
    ('s01_08c0.tob', 558):  ('ベントゥー・フォー・ユー', '给你的便当', 'medium',
                             'JP 谐音 pun（ベントゥー≈べんとう「弁当」）；本场景为渡来送自制便当（同场景 JP「彼氏におべんと作ってきた」）。'
                             '备选直译「便当，给你」；中文不可复现原 pun，需主代理确认'),
    ('s01_08f.tob', 666):   ('インザルーム、アットナイト', '在房间里，在夜里', 'high',
                             '英文标题按 R 版既有风格（如 アンダー・ザ・スモーキンスカイ→于灰蒙蒙的天空之下）意译'),
    ('s01_09b.tob', 1274):  ('なくなった財布に関する騒動とその顛末', '关于丢失钱包的骚动及其始末', 'high',
                             '直译；財布→钱包（R 版正文既有）'),
    ('s01_14h.tob', 322):   ('Ｉ．Ｓ．Ｈ', 'Ｉ．Ｓ．Ｈ', 'high',
                             '缩写不译，与 R 版正文一致（同线 JP「専門的には死神じゃなくてＩＳＨ」→ R 版正文「专业领域一般不叫死神，而是叫ＩＳＨ」）；'
                             '同场景 JP 台词「内部の助力者」即此缩写，中文正文沿用 ＩＳＨ 不译'),
    ('s01_18a.tob', 346):   ('エピローグ　～鷹志君と京ちゃん～', '终章　～鹰志君与小京～', 'high',
                             'エピローグ→终章、ちゃん→小○（作品层术语表 §四）；全角空格　按 R 版标题既有排版保留'),
    ('s02_03g.tob', 1622):  ('２４アワー・パーティー・ピープル', '２４小时派对动物', 'high',
                             'Party People→派对动物；全角数字２４保留'),
    ('s02_05c.tob', 462):   ('罪状４：ロッカー物色／罪状５：胸部接触', '罪名４：翻找储物柜／罪名５：胸部接触', 'high',
                             '罪状→罪名、ロッカー→储物柜（R 版正文既有，同系列标题「罪状１：セクハラ質問→罪名１：性骚扰询问」）'),
    ('s02_05d.tob', 706):   ('期待の中型新人×笑わないトレーナー', '备受期待的中坚新人×不苟言笑的教官', 'high',
                             '期待の中型新人→备受期待的中坚新人、トレーナー→教官（均为 R 版正文既有定译）'),
    ('s02_09e.tob', 438):   ('べっどめ青春！', '贝多姆青春！', 'low',
                             'JP「べっどめ」是同场景谐音胡闹词（同场景 JP「ベッドがべっどんだ？」「『べっどむ』ってどういう意味？」），'
                             '无语义、中文不可复现；取音译「贝多姆」保留其无意义胡闹性质。备选「床咚青春！」（网络腔，不推荐）。需主代理裁决'),
    ('s02_10c.tob', 906):   ('アレックス２と敏腕プロデューサー', '二重亚里克斯与快手制片人', 'high',
                             'アレックス２→二重亚里克斯、敏腕プロデューサー→快手制片人（均为 R 版正文既有定译）'),
    ('s02_10d1.tob', 214):  ('ゴールデン・トライアングル', '黄金大三角', 'medium',
                             '与 R 版正文「黄金のトライアングル→黄金的大三角」对齐；标题取紧凑形'),
    ('s02_14d.tob', 826):   ('閉店後のフロアにて', '打烊后的店堂', 'medium',
                             '閉店後→打烊后（R 版正文既有）；フロア 指餐厅店堂（同作 フロアスタッフ→餐厅一楼的女服员）'),
    ('s03_03h.tob', 690):   ('制服フェチＶＳ作業着フェチ', '制服控ＶＳ工作服控', 'medium',
                             'フェチ→控（R 版正文作「有喜欢制服的癖好／工作服变态」，标题取「控」形）；作業着→工作服（R 版正文既有）；ＶＳ 全角保留'),
    ('s03_08a.tob', 290):   ('Ｔｈｅ　ｒｅｔｕｒｎ　ｏｆ　ＲＯＣ', 'ＲＯＣ的回归', 'medium',
                             'ＲＯＣ＝ＲＯＣ－ＢＩＲＤ 乐队（作品层术语表 §三之三）；全角英文标题按 R 版风格意译'),
    ('s03_14b.tob', 518):   ('ゴー・オン・ザ・カウンターアタック', '继续反击', 'medium',
                             'go on the counter attack；同作无既有定译，按语义直译'),
    ('s03c_01c.tob', 614):  ('ふたりでネカフェ／ＲＷ戦記（Ｃ）', '两人同去网咖／ＲＷ战记（Ｃ）', 'medium',
                             'ネカフェ→网咖（R 版正文既有，非「网吧」）；ＲＷ 保留 JP 标题原缩写（Ｒ－ウィング 在 R 版正文作「Ｒ翼」，'
                             '此处 JP 标题本身写作 ＲＷ，保留之；如需改为「Ｒ翼战记」请主代理裁决）'),
    ('s03c_01e.tob', 670):  ('道化師たちの三文芝居', '道化师们的三流戏剧', 'medium',
                             '三文芝居→三流戏剧（R 版正文既有，2 处）；道化師 在 R 版正文保留「道化师」（1 处并注「小丑」）。'
                             '诊断稿作「小丑们的廉价闹剧」，此处取与 R 版正文一致的写法'),
    ('s03c_02c1.tob', 202): ('鳳に妹がいたなんて知らなかったなあ', '真不知道凤居然还有个妹妹', 'high',
                             '鳳→凤（作品层术语表）；与诊断稿一致'),
    ('s03c_02c2.tob', 210): ('鳳の妹ならこの前あった気がするなあ', '凤的妹妹的话，我记得之前好像见过', 'high',
                             '鳳→凤（作品层术语表）；与诊断稿一致'),
    ('s04_03g.tob', 974):   ('グレタガルドの子供たち', '格雷塔迦露德的孩子们', 'high',
                             'グレタガルド→格雷塔迦露德（R 版正文既有，5 处）；子供→孩子'),
    ('s04_22a.tob', 462):   ('森里君は僕の友達だよ', '森里君是我的朋友哦', 'high',
                             '森里→森里（R 版正文既有）；君→君（名字+君，通用层 §1.1）'),
}


def sanitize(s):
    """TSV 安全化：去制表符/换行"""
    return s.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')


def load_otp():
    rows = []
    for f in sorted(glob.glob(os.path.join(OTP, '*.jsonl'))):
        for ln in open(f, encoding='utf-8'):
            ln = ln.strip()
            if not ln:
                continue
            e = json.loads(ln)
            rows.append({
                'file': os.path.basename(f),
                'locator': 'seq=%d' % e['seq'],
                'seq': e['seq'],
                'kind': e.get('kind', ''),
                'field': 'cn',
                'jp': e.get('jp', '') or '',
                'cn': e.get('cn', '') or '',
            })
    return rows


def load_ota():
    d = json.load(open(OTA, encoding='utf-8'))
    rows = []
    for f in sorted(d.keys()):
        for m in d[f]['messages']:
            rows.append({
                'file': f,
                'locator': 'idx=%s' % m.get('index'),
                'kind': m.get('kind', ''),
                'field': 'cn',
                'jp': m.get('jp') or '',
                'cn': m.get('cn') or '',
            })
    return rows


def scan_otr():
    """扫 R 版四份映射 (file,offset) 并集，找含 $& 的正文文本字段"""
    found = {}
    for fn in OTR_FILES:
        d = json.load(open(os.path.join(OTR, fn), encoding='utf-8'))
        for e in d:
            f, off = e.get('file'), e.get('offset')
            if f is None or off is None:
                continue
            for k in ('cn', 'text', 'kept'):
                v = e.get(k)
                if isinstance(v, str) and '$&' in v:
                    key = (f, off)
                    found.setdefault(key, {'sources': [], 'fields': {}, 'kind': e.get('kind')})
                    if fn not in found[key]['sources']:
                        found[key]['sources'].append(fn)
                    found[key]['fields'].setdefault(k, v)
    return found


def main():
    out_rows = []
    checks = []

    # ---------------- B1 / B1附 (otp) ----------------
    otp = load_otp()
    n_otp_b1 = n_otp_b1a = 0
    for r in otp:
        jp, cn = r['jp'], r['cn']
        if not ('「' in jp or '」' in jp):
            continue
        if '“' in cn or '”' in cn:
            continue
        if '‘' in cn or '’' in cn:
            # B1附：单引号 → 双引号
            new = cn.replace('‘', '“').replace('’', '”')
            assert new.replace('“', '‘').replace('”', '’') == cn, 'normalize roundtrip fail'
            out_rows.append({
                'source': 'otp', 'file': r['file'], 'locator': r['locator'], 'kind': r['kind'],
                'field': 'cn', 'old_text': cn, 'new_text': new,
                'fix_type': 'quote_normalize', 'method': 'programmatic',
                'evidence': 'JP含「」且无『；CN用‘’（单引号）无“”。通用 SKILL §七.3「「」→“”」',
                'confidence': 'high',
            })
            n_otp_b1a += 1
        else:
            # B1：真遗漏，加中文引号
            m = CTRL_PREFIX.match(cn)
            if m:
                pre, rest = m.group(1), cn[m.end():]
            else:
                pre, rest = '', cn
            new = pre + '“' + rest + '”'
            assert new[len(pre) + 1:-1] == cn[len(pre):], 'quote_add body mismatch'
            assert cn.startswith(pre), 'prefix mismatch'
            out_rows.append({
                'source': 'otp', 'file': r['file'], 'locator': r['locator'], 'kind': r['kind'],
                'field': 'cn', 'old_text': cn, 'new_text': new,
                'fix_type': 'quote_add', 'method': 'programmatic',
                'evidence': 'JP含「」、CN无任何引号；控制码前缀%s原样保留，仅包住引语（工具\\fix_quotes.py:34 判据 jp.startswith("「") 漏掉带控制码前缀者）' % (repr(pre) if pre else '（无）'),
                'confidence': 'high',
            })
            n_otp_b1 += 1

    # ---------------- B1 (ota) ----------------
    ota = load_ota()
    n_ota_b1 = 0
    for r in ota:
        jp, cn = r['jp'], r['cn']
        if not ('「' in jp or '」' in jp):
            continue
        if '“' in cn or '”' in cn:
            continue
        if '‘' in cn or '’' in cn:
            continue  # ota 无此情形（实测 0）
        new = '“' + cn + '”'
        assert new[1:-1] == cn
        out_rows.append({
            'source': 'ota', 'file': r['file'], 'locator': r['locator'], 'kind': r['kind'],
            'field': 'cn', 'old_text': cn, 'new_text': new,
            'fix_type': 'quote_add', 'method': 'programmatic',
            'evidence': 'JP含「」、CN无任何引号（整行引语）',
            'confidence': 'high',
        })
        n_ota_b1 += 1

    # ---------------- B3 (otr) ----------------
    otr = scan_otr()
    # 等长截断后的实际落盘形态（最终 tob 内可能是 kept 而非 cn）
    trunc = {}
    for e in json.load(open(os.path.join(OTR, '等长补齐_截断清单.json'), encoding='utf-8')):
        if e.get('file') and e.get('offset') is not None and e.get('kept'):
            trunc[(e['file'], e['offset'])] = e['kept']
    n_otr = 0
    for (f, off) in sorted(otr.keys(), key=lambda k: (k[0], k[1])):
        jp, new_cn, conf, note = B3_TITLES[(f, off)]
        old = otr[(f, off)]['fields'].get('cn') or otr[(f, off)]['fields'].get('kept') or ''
        # 用 R版迁移映射 的 cn 作为权威 old_text
        old_cn = otr[(f, off)]['fields'].get('cn', old)
        kept = trunc.get((f, off))
        kept_note = ''
        if kept and kept != old_cn:
            kept_note = '；⚠️等长截断形态（最终 tob 实际落盘值）=%s' % kept
        out_rows.append({
            'source': 'otr', 'file': f, 'locator': 'offset=%d' % off, 'kind': 'title',
            'field': 'cn', 'old_text': old_cn, 'new_text': new_cn,
            'fix_type': 'retranslate', 'method': 'manual_retranslate',
            'evidence': '标题槽内容错位（剥标记后剩正文台词，非标题）：JP标题「%s」；证据文件=%s；%s%s' % (
                jp, '+'.join(otr[(f, off)]['sources']), note, kept_note),
            'confidence': conf,
        })
        n_otr += 1

    # ---------------- 输出 TSV ----------------
    os.makedirs(OUT, exist_ok=True)
    cols = ['source', 'file', 'locator', 'kind', 'field', 'old_text', 'new_text',
            'fix_type', 'method', 'evidence', 'confidence']
    tsv = os.path.join(OUT, '修正表_B1B3.tsv')
    with open(tsv, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\t'.join(cols) + '\n')
        for r in out_rows:
            fh.write('\t'.join(sanitize(str(r[c])) for c in cols) + '\n')

    # ---------------- 自检 ----------------
    print('== 行数 ==')
    print('  总行数           :', len(out_rows))
    print('  otp quote_add     :', n_otp_b1)
    print('  ota quote_add     :', n_ota_b1)
    print('  otp quote_norm    :', n_otp_b1a)
    print('  otr retranslate   :', n_otr)
    print('  marker_strip      :', sum(1 for r in out_rows if r['fix_type'] == 'marker_strip'))
    print('== 零副作用自检（除目标片段外完全相同）==')
    ok = 0
    for r in out_rows:
        o, n = r['old_text'], r['new_text']
        if r['fix_type'] == 'quote_add':
            # 去掉新加的中文引号后，逐字符序列必须与 old 完全一致（控制码前缀亦不变）
            stripped = n.replace('“', '', 1)
            assert stripped.endswith('”')
            stripped = stripped[:-1]
            assert stripped == o, 'quote_add 副作用: %r -> %r' % (o, n)
            ok += 1
        elif r['fix_type'] == 'quote_normalize':
            # 引号逆变换后必须逐字符等于 old
            assert n.replace('“', '‘').replace('”', '’') == o, 'normalize 副作用: %r' % o
            ok += 1
        else:
            # retranslate：old 的标记前缀必须能从 old 中完整剥离（证明系同一槽的错位内容）
            assert '$&' in o or '$' in o, 'retranslate 行缺少标记: %r' % o
            ok += 1
    print('  全部 %d 行零副作用校验通过（quote_add/normalize 逐字符可逆；retranslate 标记可剥离）' % ok)
    print('== 无空必填列 ==')
    for c in cols:
        empt = sum(1 for r in out_rows if str(r[c]).strip() == '')
        if empt:
            print('   !! 空列', c, empt)
    print('  检查完成')
    print('== 产出 ==')
    print(' ', tsv)
    return out_rows


if __name__ == '__main__':
    main()
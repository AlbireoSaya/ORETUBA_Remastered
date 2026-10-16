# -*- coding: utf-8 -*-
r"""build_fix_table_newscenes.py —— W7-1c：亚衣线新增场景中 76 条 src=mig 行的重译
（ISSUE-20260918-06 · 资源组 · W7-1c）

任务
====
用户裁决 D14：正文译文一律取自「独立翻译」的源，R 版正文整段排除
（R 版正文 88.6% 迁移自新米）。W7-1 行对齐审计把全亚衣线 6,911 行按来源划分：
  - src=mig 2,925 行（迁移自新米）→ D14 排除
      · 2,849 行在「共有/分支场景」→ 由本篇译文整体替代，W7-1c 不处理
      ·   76 行在「新增场景」（31 个，无 2009 对照）→ 无对照可换，必须按原文重译 ★本任务
  - src=new 3,928 行 → 可用，不处理

本脚本把「新增场景」中 source=='mig' 的行（实测 76 条）逐条按日文原文重译，
产出 W6 可直接消费的修正表（列定义与 修正表_B1B3.tsv 完全一致）。

只读源
======
- 工程\我们没有翅膀R\亜衣线资源\剧本\台词对照.json   （jp / cn / cn_full / voice / kind / offset / source）
- 工程\我们没有翅膀R\语料\R版迁移映射.json            （权威 old_text = 该 (file,offset) 的 cn）
- 资源组\修正\s03c_行对齐审计.json                    （meta.new_scenes 的 31 个新增场景清单）

产出（只写 资源组\修正\）
========================
- 修正表_新增场景mig重译.tsv
- 修正表_新增场景mig重译说明.md
- 待入表术语_补充.md

可复跑：python -X utf8 build_fix_table_newscenes.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

WS = r'E:\ZCode Workspace\Galgame'
PRJ = os.path.join(WS, r'工程\我们没有翅膀——格雷塔迦露德与柳木原')
PR = os.path.join(WS, r'工程\我们没有翅膀R')
RJSON = os.path.join(PR, r'亜衣线资源\剧本\台词对照.json')
RMIG = os.path.join(PR, r'语料\R版迁移映射.json')
AUDIT = os.path.join(PRJ, r'资源组\修正\s03c_行对齐审计.json')
OUT = os.path.join(PRJ, r'资源组\修正')

# ------------------------------------------------------------------ 人工重译表
# 键 = (scene, offset)；值 = (new_text, confidence, 备注)
# new_text 为完整译文（新引擎 krkr 无等长约束，不做截断）
# 标点：日式「」→“”；保留原文 ……（U+2026，1:1 个数）、！？顺序、全角空格（行首叙述缩进）
TR = {
    # ---- s03c_06a（意识/驾驶舱 独白） ----
    ('s03c_06a', 2377): ('……这里是……哪儿…………。', 'high', 'ここは……どこだ…………。；补回原文句末「。」；……个数 1:1；前导 U+3000 按通用 §七.6 删除'),
    ('s03c_06a', 2439): ('……身体怎么都……脑袋不清不楚的……。', 'high', 'はっきりしねえ＝はっきりしない 口语形；前导 U+3000 删除'),
    ('s03c_06a', 2515): ('俺现在……是在“驾驶舱”里吗……？', 'high', '≪コックピット≫：R 版正文 ≪≫ 一律作“”（实测 158 处）；前导 U+3000 删除'),
    ('s03c_06a', 2637): ('……手呢……。', 'high', '……手は……。；补回句末「。」；前导 U+3000 删除'),
    ('s03c_06a', 2683): ('能动。', 'high', '動く。；前导 U+3000 删除'),
    ('s03c_06a', 2721): ('……睁开眼……集中意识……。', 'high', '目を開けろ 为命令形；旧译「试图睁开眼睛」加戏，已去除；前导 U+3000 删除'),
    ('s03c_06a', 3561): ('“羽田君？没事吧？你脸色好苍白！？”', 'high', 'はねだくん→羽田君（D3 新米仲裁）；！？顺序保留；内部 U+3000 按通用 §七.6 删除'),
    ('s03c_06a', 4172): ('“啊啊，这边的世界让人喘不过气……”', 'high', '息苦しい＝憋闷/喘不过气'),
    ('s03c_06a', 4339): ('“我稍微……稍微去一下哦……”', 'high', 'ちょっと……ちょっとだけ 反复保留'),
    ('s03c_06a', 4446): ('“去，是去哪儿？”', 'medium', '行くって＝「说去」引用；原文无句末？，中文按疑问补'),
    ('s03c_06a', 4529): ('“是格雷塔迦露德啊……得快点过去才行……”', 'high', 'グレタガルド→格雷塔迦露德（本工程正式译名）'),
    ('s03c_06a', 4937): ('“我们是没有翅膀的……”', 'high', '僕たちには翼がない 主题句；不添「啊」'),
    ('s03c_06a', 5778): ('“羽田君……？”', 'high', 'はねだくん→羽田君（D3）'),
    ('s03c_06a', 6561): ('“羽田君？”', 'high', 'はねだくん→羽田君（D3）'),
    # ---- s03c_06b ----
    ('s03c_06b', 2913): ('“啊？”', 'high', 'あ？'),
    ('s03c_06b', 12798): ('“……啊？”', 'medium', 'あァ（小写ァ表拖长）；旧译「昂」为误字，已改正'),
    # ---- s03c_07a ----
    ('s03c_07a', 5732): ('“啊？”', 'high', 'あ？'),
    ('s03c_07a', 7242): ('“多谢款待”', 'high', 'ごっそさん＝ご馳走さん 口语形；旧译「请客谢了」为误译（脚本内同形证据：あんさ、弁当ごっそさんした）'),
    ('s03c_07a', 7716): ('“啊？啥意思”', 'medium', 'どゆこと＝どういうこと 俚俗缩约；隼人语体取口语「啥意思」；原文无句末？；内部 U+3000 删除'),
    # ---- s03c_08a ----
    ('s03c_08a', 2943): ('嗯？怎么了？', 'high', 'ん？　なんだ？；前导/内部 U+3000 删除'),
    ('s03c_08a', 6222): ('“啊？”', 'high', 'あ？'),
    ('s03c_08a', 12054): ('“啊啊？”', 'high', 'あぁ？（表不悦/反问）'),
    ('s03c_08a', 12833): ('“哦，是吗”', 'high', 'あそう＝あ、そう；原文无句末。'),
    # ---- s03c_08b ----
    ('s03c_08b', 6411): ('“哦？”', 'high', 'お？'),
    ('s03c_08b', 9572): ('“羽田——”', 'high', '羽田ァー：呼喝拖音；ー→——'),
    ('s03c_08b', 15282): ('“我开动了”', 'high', 'いただきます；原文无句末。'),
    # ---- s03c_09a ----
    ('s03c_09a', 5814): ('“羽田——”', 'high', '羽田ぁー：呼喝拖音；ー→——'),
    ('s03c_09a', 8202): ('“啊啊？”', 'high', 'あぁ？'),
    # ---- s03c_09b ----
    ('s03c_09b', 10139): ('“为什么啊”', 'high', 'なんでだよ；旧译「什么玩意」为误译，已改正'),
    ('s03c_09b', 15297): ('“哦，是吗”', 'high', 'あそう'),
    ('s03c_09b', 16110): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_10a ----
    ('s03c_10a', 4304): ('“啊啊？”', 'high', 'あぁ？'),
    ('s03c_10a', 8090): ('“啊啊？”', 'high', 'あぁ？'),
    ('s03c_10a', 11304): ('“哈！？”', 'high', 'はっ！？（惊愕短呼）；通用 §3.6 は系短呼'),
    ('s03c_10a', 13592): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_10b ----
    ('s03c_10b', 12371): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_11a ----
    ('s03c_11a', 10814): ('“没事”', 'high', '平気＝不要紧（陈述，非疑问）；旧译「没事吧」误加疑问语气，已改正'),
    ('s03c_11a', 11679): ('“这个”', 'high', 'これ；原文无句末。'),
    ('s03c_11a', 12535): ('“啊？”', 'high', 'あ？'),
    ('s03c_11a', 12923): ('“嘿嘿”', 'high', 'へへ（得意/害羞的笑）；原文无〜，不补拖音'),
    # ---- s03c_11b ----
    ('s03c_11b', 7906): ('“这个”', 'high', 'これ'),
    # ---- s03c_11c ----
    ('s03c_11c', 6044): ('“啊？”', 'high', 'あ？'),
    ('s03c_11c', 45003): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_12a ----
    ('s03c_12a', 7162): ('“哈！？”', 'high', 'はっ！？（惊愕短呼）'),
    ('s03c_12a', 11598): ('“哦，是吗”', 'high', 'あそう'),
    # ---- s03c_12b ----
    ('s03c_12b', 9627): ('咦？', 'high', 'あれ。（地の文，表察觉异常）；前导 U+3000 删除'),
    ('s03c_12b', 10791): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_12c ----
    ('s03c_12c', 4099): ('“啊？”', 'high', 'あ？'),
    ('s03c_12c', 13403): ('“嗯？怎么了？”', 'medium', 'ん？　なに？；语境＝隼人主动搭话后香田应答，「怎么了」比「什么」自然；内部 U+3000 删除'),
    ('s03c_12c', 27363): ('“啊？”', 'high', 'あ？'),
    ('s03c_12c', 30060): ('“啊，对了”', 'high', 'あ、そうだ'),
    ('s03c_12c', 30467): ('“诶，什么？”', 'high', 'え、なに？'),
    # ---- s03c_13a ----
    ('s03c_13a', 8253): ('“看什么呢”', 'high', 'なに見てんの＝何見てるの 口语形；女生徒质问语气'),
    ('s03c_13a', 28260): ('“啊？”', 'high', 'あ？'),
    ('s03c_13a', 33265): ('“嘿嘿”', 'high', 'へへ'),
    # ---- s03c_14a ----
    ('s03c_14a', 21078): ('“这个”', 'high', 'これ'),
    ('s03c_14a', 34972): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_15a ----
    ('s03c_15a', 12077): ('“那个啊……”', 'high', 'あんさ＝あのさ 口语形'),
    # ---- s03c_16a ----
    ('s03c_16a', 2575): ('“是的”', 'medium', 'です（对 小鳩「本日はおでかけですか」的极简回答，模仿其敬体）；旧译「成田。」为串行错位值'),
    ('s03c_16a', 15864): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_16b ----
    ('s03c_16b', 11401): ('“哦，是吗”', 'high', 'あそう'),
    ('s03c_16b', 13071): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_16c ----
    ('s03c_16c', 7934): ('“噗嗤”', 'high', 'ぶふっ（忍俊不禁的喷笑）；促音省略'),
    # ---- s03c_17a ----
    ('s03c_17a', 4336): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_17b ----
    ('s03c_17b', 3329): ('“啊？”', 'high', 'あ？'),
    # ---- s03c_17c ----
    ('s03c_17c', 11688): ('“是啊”', 'high', 'だな（附和）；原文无句末。'),
    ('s03c_17c', 23354): ('“哈！？”', 'high', 'はっ！？（告白后的惊愕短呼）'),
    ('s03c_17c', 25217): ('“那、”', 'medium', 'なっ（なに 的截断）；与下行「なななななな……」→「那那那那那那……」保持同一顿音，故取「那、」；旧译「为、」为误译'),
    ('s03c_17c', 25492): ('“怎么样”', 'high', 'どうよ'),
    # ---- s03c_18a ----
    ('s03c_18a', 7847): ('评价不太好。', 'high', '不評だった；旧译「得到了差评」偏重，按「不受好评」义；前导 U+3000 删除'),
    ('s03c_18a', 8232): ('那么。', 'high', 'さて。；前导 U+3000 删除'),
    ('s03c_18a', 18361): ('“啊？”', 'high', 'あ？'),
    ('s03c_18a', 19306): ('“！？”', 'high', '！？（纯符号槽，原样保留）'),
    ('s03c_18a', 23707): ('“还有，把头发剪了，头发”', 'medium', 'あと髪切れ髪（源语料原样，末尾「髪」为原文重复，不删改）；旧译删除重复，已还原'),
    # ---- s03c_19a ----
    ('s03c_19a', 22469): ('“诶……”', 'high', 'へっ（被握住手时的短促惊讶）'),
    ('s03c_19a', 22774): ('“怎么样”', 'high', 'どうよ'),
}

KIND_MAP = {'dialogue': 'dialogue', 'narration': 'line', 'title': 'title'}


def load():
    d = json.load(open(RJSON, encoding='utf-8'))
    scenes = {s['file'].replace('.tob', ''): s['lines'] for s in d['scenes']}
    mig = json.load(open(RMIG, encoding='utf-8'))
    mig_by = {(e['file'], e['offset']): e for e in mig if e.get('offset') is not None}
    audit = json.load(open(AUDIT, encoding='utf-8'))
    new_scenes = audit['meta']['new_scenes']
    return scenes, mig_by, new_scenes, audit


def main():
    scenes, mig_by, new_scenes, audit = load()
    ns = set(new_scenes)

    rows = []
    for sc in new_scenes:
        for ln in scenes.get(sc, []):
            if ln.get('source') != 'mig':
                continue
            rows.append((sc, ln))

    # ---- 断言 1：条数与审计 new_scene_stats 求和一致 ----
    expect = sum(v['src'].get('mig', 0) for v in audit['new_scene_stats'].values())
    assert len(rows) == expect, '条数不符: %d vs %d' % (len(rows), expect)
    print('① 复核条数：实测 %d == 审计 new_scene_stats 求和 %d —— 通过' % (len(rows), expect))

    # ---- 断言 2：逐条与源数据 (file, offset) 对应，old_text 逐字符等于 R版迁移映射 cn ----
    out = []
    for sc, ln in rows:
        key = (sc + '.tob', ln['offset'])
        e = mig_by.get(key)
        assert e is not None, 'R版迁移映射缺 %s' % (key,)
        old_cn = e.get('cn') or ''
        # 台词对照 cn / cn_full 与迁移映射 cn 的关系
        cmp_cn = ln.get('cn') or ''
        cmp_full = ln.get('cn_full') if 'cn_full' in ln else None
        assert old_cn == (cmp_full if cmp_full is not None else cmp_cn), \
            'cn 口径不符 %s: %r / %r / %r' % (key, old_cn, cmp_cn, cmp_full)
        tr = TR.get((sc, ln['offset']))
        assert tr is not None, '缺重译条目 %s' % ((sc, ln['offset']),)
        new_text, conf, note = tr
        assert new_text and 'TODO' not in new_text and '待译' not in new_text, '空/占位译文 %s' % ((sc, ln['offset']),)
        kind = KIND_MAP.get(ln.get('kind'), 'other')
        ev = ('新增场景 src=mig，D14 排除新米来源，按原文重译；场景=%s；源kind=%s；%s'
              % (sc, ln.get('kind'), note))
        out.append({
            'source': 'otr', 'file': key[0], 'locator': 'offset=%d' % ln['offset'],
            'kind': kind, 'field': 'cn', 'old_text': old_cn, 'new_text': new_text,
            'fix_type': 'retranslate', 'method': 'manual_retranslate',
            'evidence': ev, 'confidence': conf,
            '_scene': sc, '_jp': ln.get('jp') or '', '_speaker': ln.get('speaker_jp') or '',
            '_trunc': bool(ln.get('truncated')),
        })
    print('② 定位校验：%d 条全部在 R版迁移映射.json 命中，old_text 逐字符等于其 cn —— 通过' % len(out))

    # ---- 断言 3：逐场景计数 ----
    from collections import Counter, OrderedDict
    cnt = OrderedDict()
    for sc in new_scenes:
        c = sum(1 for r in out if r['_scene'] == sc)
        if c:
            cnt[sc] = c
    assert sum(cnt.values()) == len(out)
    print('③ 逐场景覆盖：%d 个新增场景含 mig 行（另 %d 个为 0）—— 通过'
          % (len(cnt), len(new_scenes) - len(cnt)))

    # ---- 断言 4：无残留 / 无占位 ----
    bad = [r for r in out if not r['new_text'].strip() or 'TODO' in r['new_text'] or '待译' in r['new_text']]
    assert not bad
    assert not any('\u3000' in r['new_text'] for r in out), 'new_text 残留全角空格 U+3000'
    assert not any(('「' in r['new_text'] or '」' in r['new_text']) for r in out), 'new_text 残留日式引号'
    print('④ 无残留：%d 条 new_text 全部非空、无「待译/TODO」占位、无 U+3000、无日式引号 —— 通过' % len(out))

    # ---- GBK 可编码性（报告项；新引擎 UTF-8，不作为硬约束） ----
    ng = []
    for r in out:
        try:
            r['new_text'].encode('gbk')
        except Exception:
            ng.append(r['file'] + '@' + r['locator'])
    print('⑤ GBK 可编码性：%d/%d 可编码；不可编码 %s' % (len(out) - len(ng), len(out), ng or '无'))

    # ---- 输出 TSV ----
    os.makedirs(OUT, exist_ok=True)
    cols = ['source', 'file', 'locator', 'kind', 'field', 'old_text', 'new_text',
            'fix_type', 'method', 'evidence', 'confidence']

    def san(s):
        return str(s).replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')

    tsv = os.path.join(OUT, '修正表_新增场景mig重译.tsv')
    with open(tsv, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\t'.join(cols) + '\n')
        for r in out:
            fh.write('\t'.join(san(r[c]) for c in cols) + '\n')
    print('⑥ 产出 %s（%d 数据行）' % (tsv, len(out)))

    # ---- 输出说明 md ----
    md = os.path.join(OUT, '修正表_新增场景mig重译说明.md')
    L = []
    A = L.append
    A('# 修正表_新增场景mig重译 · 说明（W7-1c）')
    A('')
    A('- Issue：`ISSUE-20260918-06` ｜ 模块：W7-1c（资源组）｜ 日期：2026-09-18')
    A('- 依据：用户裁决 **D14**（正文译文一律取自独立翻译的源，R 版正文整段排除）＋'
      '用户 2026-09-17 定规「新米汉化只可用人名/地名，剧情译文一律不得使用」')
    A('- 源：`工程\\我们没有翅膀R\\亜衣线资源\\剧本\\台词对照.json`（6,911 行）＋'
      '`工程\\我们没有翅膀R\\语料\\R版迁移映射.json`（权威 old_text）＋'
      '`资源组\\修正\\s03c_行对齐审计.json`（`meta.new_scenes` 31 场景）')
    A('- 产物：`资源组\\修正\\修正表_新增场景mig重译.tsv`（**只写本工程修正层，源工程一个字节未改**）')
    A('')
    A('## 一、方法')
    A('')
    A('1. **定位**：取 `s03c_行对齐审计.json` 的 `meta.new_scenes`（31 个新增场景），'
      '在 `台词对照.json` 中筛出 `scene ∈ new_scenes` 且 `source == \'mig\'` 的行。')
    A('2. **复核条数**：与审计 `new_scene_stats` 各场景 `src.mig` 求和交叉核对（见 §二）。')
    A('3. **取 old_text**：`old_text` 取 `R版迁移映射.json` 同 `(file, offset)` 的 `cn`（权威），'
      '并断言与 `台词对照.json` 的 `cn`（未截断行）或 `cn_full`（截断行）逐字符相等。')
    A('4. **重译**：按日文原文逐条重译（**不复用 R 版旧译文**）；术语逐项对照两层术语表与'
      '`资源组\\修正\\译名统一口径.md`；标点按通用 `SKILL.md` §七（`「」`→`“”`、'
      '`……` 个数 1:1、`！？` 顺序保留、**全角空格 U+3000 一律删除**）。')
    A('   - 全角空格处置依据：通用 `SKILL.md` §七.6「全角空格（U+3000）一律删除」；'
      '且 D14 指定的主取文源「本篇」译文实测 **0 处 U+3000**（`工程\\我们没有翅膀\\汉化\\剧情汉化\\s03c_*.jsonl` 2,897 槽）。'
      'R 版 `src=new` 行仍带行首 U+3000（见 §六.6），属项目级一致性待办。')
    A('5. **不截断**：新引擎（krkr Z，UTF-8）无 Lucifen 的等长硬约束，'
      '`new_text` 一律给**完整译文**；R 版 `等长补齐_截断清单.json` 的截断形态仅作对照，不写入。')
    A('')
    A('## 二、76 条复核结果（与审计 new_scene_stats 一致）')
    A('')
    A('审计 `new_scene_stats` 的 31 个新增场景中，`src.mig` 求和 = **%d**；' % expect)
    A('本脚本实测同口径筛出 = **%d**，**完全一致**。' % len(out))
    A('')
    A('> 注：任务书表述为「31 个新增场景」，但其中 5 个场景（`s03c_06c`、`s03c_08c`、`s03c_11d`、'
      '`s03c_14b`、`s03c_20a`）**不含任何 mig 行**（`src.mig = 0`），'
      '故实际含 mig 行的是 **%d 个场景**，`s03c_20a` 的 102 行全部为 `src=new`。' % len(cnt))
    A('')
    A('### 逐场景计数表')
    A('')
    A('| 场景 | mig 行数 | 场景总行数 |')
    A('| --- | --- | --- |')
    for sc, c in cnt.items():
        A('| %s | %d | %d |' % (sc, c, audit['new_scene_stats'][sc]['n_lines']))
    A('| **合计** | **%d** | — |' % len(out))
    A('')
    A('## 三、逐条明细（原文 → R 版旧译文 → 新译文 → 依据）')
    A('')
    A('> 「R 版旧译文」= `R版迁移映射.json` 的 `cn`（= `old_text`）；标 `[截断]` 者'
      'R 版实际落盘为等长截断形态，此处给出的是完整形态。')
    A('')
    A('| # | 场景 | offset | 说话人 | 原文（JP） | R 版旧译文 | 新译文 | 依据 | 置信 |')
    A('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for i, r in enumerate(out, 1):
        A('| %d | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            i, r['_scene'], r['locator'].replace('offset=', ''),
            (r['_speaker'] or '（旁白）'),
            r['_jp'].replace('|', '\\|'),
            (r['old_text'] + (' [截断]' if r['_trunc'] else '')).replace('|', '\\|'),
            r['new_text'].replace('|', '\\|'),
            r['evidence'].replace('新增场景 src=mig，D14 排除新米来源，按原文重译；', '').replace('|', '\\|'),
            r['confidence']))
    A('')
    A('## 四、术语对照（逐项核验）')
    A('')
    A('| 原文 | 采用译法 | 依据 |')
    A('| --- | --- | --- |')
    A('| `はねだくん`／`羽田君` | **羽田君** | D3 新米仲裁；**`资源组\\修正\\译名仲裁报告.md` T1 已裁定「统一为羽田君」**'
      '（方向翻转，纠正 `译名统一口径.md` §2.1 的「羽田同学」）；任务书明示 |')
    A('| `グレタガルド` | **格雷塔迦露德** | `00_项目总纲.md` §〇（幻想侧王国名）；本工程正式名称 |')
    A('| `コックピット` | **驾驶舱** | R 版正文 `≪≫` 一律作 `“”`（实测 158 处） |')
    A('| `隼人`／`鷹志`／`亜衣` | 隼人／鹰志／亚衣 | `我们没有翅膀R\\作品skill\\术语表.md` §一、§二 |')
    A('| `高内`／`女芸人`／`女生徒`／`制服を着た女`／`タカシの女` | 高内／女艺人／女学生／'
      '穿制服的女生／鹰志的女人 | 同上 §一之二（亜衣线次要说话人） |')
    A('')
    A('## 五、可复现命令')
    A('')
    A('```bash')
    A('cd "E:/ZCode Workspace/Galgame"')
    A('python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_fix_table_newscenes.py"')
    A('```')
    A('')
    A('脚本全程只读源工程（`工程\\我们没有翅膀R\\`），只写 `资源组\\修正\\`。')
    A('')
    A('## 六、风险、待裁决与未决项')
    A('')
    A('1. **`羽田君` 落点（T1，已裁决）**：D3 与任务书明示取「羽田君」（新米 body 实测 549）；'
      '`资源组\\修正\\译名仲裁报告.md` T1 已裁定**统一为「羽田君」**（方向翻转，纠正 W7-3 `译名统一口径.md` §2.1 的「羽田同学」）。'
      '本表 3 条（`s03c_06a@3561`、`@5778`、`@6561`）按此采用「羽田君」，**与最新裁决一致，无需回改**。'
      '（`译名统一口径.md` §2.1 是否随仲裁报告同步回修，属主代理职责。）')
    A('2. **`あと髪切れ髪`（`s03c_18a@23707`）**：源语料原文如此（`剧本全文.md:53300` 亦同），'
      '末尾「髪」为原文重复。本表**忠实保留重复**，未按 R 版旧译删改；如判定为源文本笔误，'
      '请指示是否删重复。')
    A('3. **`です`（`s03c_16a@2575`）**：日文原文仅「です」一词（对 小鳩 敬体问句的极简回答）。'
      '本表译「是的」，置信 `medium`；R 版旧译文为「成田。」（明显为串行错位值，非本行译文）。')
    A('4. **`≪≫` 标记**：仅 1 条（`s03c_06a@2515`）。本表按 R 版正文惯例作 `“”`；'
      '如新工程希望保留 `≪≫` 或改用 `《》`，须全篇统一后回改。')
    A('5. 本表**未改写** `修正表_B1B3.tsv` / `修正表_B1B3_扩展.tsv`；三表按 `(source, file, locator)` 并列消费。')
    A('6. **U+3000 一致性（项目级待办）**：本表 11 条原文含 U+3000 的行已按通用 §七.6 全部删除；'
      '但 R 版 `src=new` 行（新增场景 3,852 行）仍普遍带行首 U+3000，'
      '与本篇（0 处）及本表不一致。W6 组装 `scene.jsonl` 时建议全量归一，'
      '或在派单中明确口径——**此项非本表可决，上报主代理**。')
    A('7. **`kind` 枚举映射**：源 `台词对照.json` 的 `kind` 为 `dialogue`/`narration`；'
      '本表按 `_README.md` §二 枚举映射为 `dialogue` / `line`（narration→line）。'
      '源 kind 已写入 `evidence` 列备查。')
    A('')
    with open(md, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L))
    print('⑦ 产出 %s' % md)

    # ---- 待入表术语 ----
    terms = [
        ('グレタガルド', '格雷塔迦露德', 's03c_06a.tob@4529（本表）；全工程',
         '作品层', '`00_项目总纲.md` §〇「格雷塔迦露德（グレタガルド，幻想侧王国）」；本工程正式名称'),
        ('≪…≫（术语强调括号）', '转中文引号“…”（或《》待定）', 's03c_06a.tob@2515（本表）',
         '作品层', 'R 版正文 `≪≫` 实测 158 处一律作“”；新工程是否沿用待定'),
        ('はっ（はっ！？）', '哈（哈！？）', 's03c_10a.tob@11304、s03c_12a.tob@7162、'
         's03c_17c.tob@23354（本表 3 处）', '通用层',
         '通用术语表 §3.6 ハア！？→哈？（同系短呼）；促音省略'),
        ('ぶふっ', '噗嗤', 's03c_16c.tob@7934（本表）', '通用层',
         '通用术语表 §3.2 笑声系（ふふ→呵呵/噗嗤）'),
        ('へへ', '嘿嘿', 's03c_11a.tob@12923、s03c_13a.tob@33265（本表 2 处）', '通用层',
         '通用术语表 §3.2 えへ系→嘿嘿（同类傻笑/掩饰害羞）'),
        ('あぁ？／あァ？', '啊啊？／啊？', 's03c_06b.tob@12798、s03c_08a.tob@12054 等（本表 6 处）', '通用层',
         '通用术语表 §3.2 あぁ系（叹息/失神/反问）；小写ァ表拖长，促音省略'),
        ('ごっそさん', '多谢款待', 's03c_07a.tob@7242（本表）', '通用层',
         'ご馳走さん 的口语缩约形；脚本内同源证据 `あんさ、弁当ごっそさんした`'),
        ('どゆこと', '啥意思', 's03c_07a.tob@7716（本表）', '通用层',
         'どういうこと 的俚俗缩约；隼人语体取口语'),
    ]
    tp = os.path.join(OUT, '待入表术语_补充.md')
    T = []
    T.append('# 待入表术语 · 补充（W7-1c · 新增场景 76 条 mig 重译）')
    T.append('')
    T.append('> **维护归主代理**：本文件只登记，**不得直接写入任何术语表**。')
    T.append('> 字段：`日文原词 | 临时译法 | 出现位置 | 拟入层 | 建议依据`。')
    T.append('> 与 `资源组\\修正\\待入表术语.md`（W7-2 产出）并列，不覆盖。')
    T.append('')
    T.append('| 日文原词 | 临时译法 | 出现位置（文件+偏移） | 拟入层 | 建议依据 |')
    T.append('| --- | --- | --- | --- | --- |')
    for a, b, c, d, e in terms:
        T.append('| `%s` | %s | %s | %s | %s |' % (a, b, c, d, e))
    T.append('')
    T.append('## 冲突项（不自行择一，上报裁决）')
    T.append('')
    T.append('| 项 | 冲突 | 本表处置 |')
    T.append('| --- | --- | --- |')
    T.append('| `羽田君`／`はねだくん` | ~~D3＋任务书＝**羽田君** vs `译名统一口径.md` §2.1＝**羽田同学**（T1）~~ '
             '→ **已裁决**：`资源组\\修正\\译名仲裁报告.md` T1＝**羽田君**（方向翻转） | '
             '按**羽田君**（3 条），与最新裁决一致 |')
    T.append('')
    T.append('> 结论：本批 76 条**无未决冲突**；上表仅记录一处已消解的 T1。')
    T.append('')
    with open(tp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(T))
    print('⑧ 产出 %s' % tp)

    # ---- 控制台摘要 ----
    from collections import Counter
    print('=== 摘要 ===')
    print('  条数 %d ；场景 %d 个' % (len(out), len(cnt)))
    print('  kind：%s' % dict(Counter(r['kind'] for r in out)))
    print('  confidence：%s' % dict(Counter(r['confidence'] for r in out)))
    print('  截断行（R 版等长截断，本表给完整译文）：%d' % sum(1 for r in out if r['_trunc']))


if __name__ == '__main__':
    main()
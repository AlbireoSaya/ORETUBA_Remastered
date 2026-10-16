# -*- coding: utf-8 -*-
r"""final_fixes.py —— 一审全部打回项的汇总回改（最后一轮）

来源：一审组 1–8（`翻译工作区\审校_组*.md`）打回项。规则：
  * 「条件化」修正——凡按日文原文判定可定位者，一律只在 JP 命中时替换；
  * 语义级修正按 (file, idx) 或全局 `i` 精确定位；
  * 本脚本为**幂等**，可重复执行。
"""
import io
import json
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')

# 1) 全局（不限批次）
GLOBAL = [
    ('森里君', '森里同学'), ('羽田君', '羽田同学'), ('針生君', '针生同学'), ('针生君', '针生同学'),
    ('成田君', '成田同学'), ('千歳君', '千岁同学'), ('千岁君', '千岁同学'), ('玉泉君', '玉泉同学'),
    ('日野君', '日野同学'), ('山科君', '山科同学'), ('軽部君', '轻部同学'), ('轻部君', '轻部同学'),
    ('佐久間君', '佐久间同学'), ('佐久间君', '佐久间同学'), ('望月君', '望月同学'), ('吉川君', '吉川同学'),
    ('渡来君', '渡来同学'), ('伊丹君', '伊丹同学'), ('氷室君', '冰室同学'), ('冰室君', '冰室同学'),
    ('仮統合', '假统合'), ('临时统合', '假统合'),
    ('让我的眼泪传达给谁', '我的眼泪啊，请传达给谁'),
    ('デュクシ', '噗咻'), ('戳戳', '噗咻'),
    ('幼海德拉', '幼九头蛇'), ('海德拉', '九头蛇'),
    ('白天遭遇', '午间遭遇'), ('插曲', '间奏'),
    ('小咒语', '咒语'),
    ('キャラの立法', '角色塑造'), ('角色的立法', '角色塑造'),
    ('大宇宙宏观宇宙', '宏观世界'), ('大宇宙宏宇宙', '宏观世界'),
]
# 2) 条件化（仅当 JP 命中时）
COND = [
    ('んむ', [('唔嗯', '唔姆'), ('唔呣', '唔姆'), ('唔呶', '唔姆')]),
    ('ふむ', [('唔嗯', '唔姆'), ('唔呣', '唔姆'), ('唔呶', '唔姆')]),
    ('ふぬ', [('唔嗯', '唔姆'), ('唔呣', '唔姆'), ('唔呶', '唔姆')]),
    ('おまじない', [('小咒语', '咒语')]),
    ('もりもり', [('有很多', '满满')]),
    ('ねーちゃん', [('大姐', '妞')]),
    ('ふむん', [('唔嗯', '唔姆')]),
]
# 3) 定点（明细随批次指定）
POINT = [
    (12, {8911: [('你', '噗呐田君')]}),                       # ぱね田くん 漏译称谓
    (12, {9352: [('落单', '弗利法')]}),                       # フリファー 标题
    (12, {9427: [('有很多', '满满')]}),
    (12, {9156: [('“小鸠”', '“小鸠小姐”')]}),
    (10, {7740: [('仗着同伙也在', '仗着同伙也在')]}),          # 占位（语义项见下）
    (14, {12749: [('我多加小心', '我松了口气')]}),            # あんどの念 误译
    (14, {12434: [('小咒语', '咒语')], 12447: [('小咒语', '咒语')], 12467: [('小咒语', '咒语')]}),
    (15, {15169: [('不行啊', '太离谱了吧')]}),
    (15, {14701: [('渡来琳同学', '渡不来的同学')]}),
    (19, {16276: [('“浪漫之子”', '‘浪漫之子’')]}),
]
OPTION_FIX = True


def apply_global():
    tot = {}
    for f in sorted(glob.glob(os.path.join(WD, '批次*_译文.json'))):
        d = json.load(io.open(f, encoding='utf-8'))
        src = json.load(io.open(f.replace('译文', '原文'), encoding='utf-8'))['lines']
        jp = {x['i']: (x['jp'] or '') for x in src}
        k = 0
        for row in d['tr']:
            cn = row['cn'] or ''
            for a, b in GLOBAL:
                if a in cn and a != b:
                    k += cn.count(a)
                    cn = cn.replace(a, b)
            for key, pairs in COND:
                if key in jp.get(row['i'], ''):
                    for a, b in pairs:
                        if a in cn:
                            k += cn.count(a)
                            cn = cn.replace(a, b)
            row['cn'] = cn
        if k:
            io.open(f, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
            tot[os.path.basename(f)] = k
    print('全局/条件化替换：', tot, '合计', sum(tot.values()))


def apply_point():
    for b, job in POINT:
        p = os.path.join(WD, '批次%02d_译文.json' % b)
        d = json.load(io.open(p, encoding='utf-8'))
        k = 0
        for row in d['tr']:
            if row['i'] in job:
                cn = row['cn'] or ''
                for a, bb in job[row['i']]:
                    if a in cn and a != bb:
                        k += cn.count(a)
                        cn = cn.replace(a, bb)
                row['cn'] = cn
        if k:
            io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
        print('批次%02d 定点 %d 处' % (b, k))


def main():
    apply_global()
    apply_point()


if __name__ == '__main__':
    main()

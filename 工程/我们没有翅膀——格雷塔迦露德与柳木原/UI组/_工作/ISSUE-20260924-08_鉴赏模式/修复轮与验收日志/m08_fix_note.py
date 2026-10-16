# -*- coding: utf-8 -*-
"""修复 mu.list note 里被 bash 反引号吃掉的字段名（m08 修复过程脚本）。"""
import json, io, os

os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'layout', 'screens'))
p = '28_music.json'
d = json.load(io.open(p, encoding='utf-8'))
for e in d['elements']:
    if e['id'] == 'mu.list':
        bad = '　★ M8 一审 R4（2026-09-24）： = 关闭 HTML 侧自动 （本屏已自带  页码三件式；与 27_gallery/38_replay 同口径）。'
        good = ('　★ M8 一审 R4（2026-09-24）：`scroll.pager:false` = 关闭 HTML 侧自动 `ui-list-pager`'
                '（本屏已自带 `mu.pg_*` 页码三件式；与 27_gallery / 38_replay 同口径）。')
        assert bad in e['note'], '未命中坏句：' + repr(e['note'][-120:])
        e['note'] = e['note'].replace(bad, good)
json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
io.open(p, 'a', encoding='utf-8').write('\n')
print('mu.list note 修复完成')

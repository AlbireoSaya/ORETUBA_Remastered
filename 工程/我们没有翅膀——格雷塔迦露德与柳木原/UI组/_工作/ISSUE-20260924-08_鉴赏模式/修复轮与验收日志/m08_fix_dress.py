# -*- coding: utf-8 -*-
"""ISSUE-20260924-08 一审打回修复 · 37_dress.json 的 V1-V5（vision 视觉修复）。
一次性脚本，落在 UI组\临时\（过程文件，不入库）。"""
import json, io

F = '37_dress.json'
d = json.load(io.open(F, encoding='utf-8'))
els = d['elements']
by_id = {e['id']: e for e in els}
assert len(by_id) == len(els), 'id 重复？'

FONT_BTN = {"size": 20, "bold": True, "color": "@palette.node_locked",
            "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0}

# ---------- V4：删除顶部白带 dr.top ----------
# ---------- V3：删除底部游离「返回」dr.hit_back ----------
# ---------- V1①②⑤⑥：删除 4 组 #汎用/模板 tag 叠印件 ----------
DELETE = ['dr.top', 'dr.hit_back',
          'dr.tag_服装', 'dr.tag_tx_服装',
          'dr.tag_時間用', 'dr.tag_tx_時間用',
          'dr.tag_表情', 'dr.tag_tx_表情',
          'dr.tag_背景', 'dr.tag_tx_背景']
for did in DELETE:
    assert did in by_id, '缺 ' + did
d['elements'] = [e for e in els if e['id'] not in DELETE]
by_id = {e['id']: e for e in d['elements']}
print('已删除 %d 件：' % len(DELETE), ' '.join(DELETE))

# ---------- V2：人名列表 11 行文字 x0 → x34（PSB 名前/#text 实测起点） ----------
for i in range(1, 12):
    e = by_id['dr.name_tx_%d' % i]
    assert e['x'] == 0 and e['y'] == 181 + 60 * (i - 1), (e['id'], e['x'], e['y'])
    e['x'] = 34
    e['note'] = (e['note'] + "　★ M8 一审/vision 修复（2026-09-24）：文字起点由 x0 改 **x34**（PSB idx76 "
                 "`名前/#text/*` 实测 x34 y%d w92..114 h21 —— 原先沿用行框 `#rect` 的 x0 把文字贴到屏幕"
                 "左缘（vision：人名列表贴左缘、首末项观感被裁）。纵向仍用行框高度 47 + valign:middle"
                 "（视觉行中心 = 参考 #text 中心 204.5+60k，一致），横向照 #text 起点。"
                 % (194 + 60 * (i - 1)))
print('V2 人名 11 行 x0→34 完成')

# ---------- V1③④：小方块改单字符 + 补 chstate 行标签 4 件 ----------
SINGLE = {'dr.btn_tx_pose0': '1', 'dr.btn_tx_pose1': '2', 'dr.btn_tx_pose2': '3',
          'dr.btn_tx_diff0': '1', 'dr.btn_tx_diff1': '2', 'dr.btn_tx_diff3': '3',
          'dr.btn_tx_level0': 'S', 'dr.btn_tx_level1': 'M', 'dr.btn_tx_level2': 'L'}
for eid, s in SINGLE.items():
    e = by_id[eid]
    old = e['sample']
    e['sample'] = s
    e['note'] = (e['note'] + "　★ M8 vision 修复（2026-09-24）：文字「%s」→「%s」—— 56×56 小方块放不下"
                 "「姿势 1」等 3~4 字（实测溢出成横链，vision ③④）；行标签改由左侧标签条承担（参考作 "
                 "`chstate` (218,251,54,207)），方块内只放单字符（参考作面板 c17/c20 烘焙文字即 "
                 "`1 2 3 / S M L`）。" % (old, s))
print('V1③④ 9 件小方块改单字符')

# chstate 行标签（PSB idx76 chstate (218,251,54,207)：4 标签行带实测 = 局部 y 0..29/59..88/118..147/177..206）
ROWS = [('dr.row_tx_dress', '服装', 251), ('dr.row_tx_pose', '姿势', 310),
        ('dr.row_tx_diff', '差分', 369), ('dr.row_tx_level', '大小', 428)]
new_els = []
for eid, label, y in ROWS:
    new_els.append({
        "id": eid, "kind": "text", "z": 25, "visible_default": True,
        "x": 218, "y": y, "w": 54, "h": 30,
        "font": dict(FONT_BTN),
        "align": "center", "valign": "middle", "wrap": False, "max_lines": 1,
        "sample": label,
        "source": "几何取自《交汇协奏曲》PSB 容器 idx76 `chstate`（p76_c013_l22105.png）",
        "note": "**换装面板行标签**（引擎绘制）。几何 = PSB idx76 `chstate` (218,251,54,207) 的 4 条文字"
                "行带（实测逐带 y 0..29 / 59..88 / 118..147 / 177..206 → 本件 y%d h30，x218 w54）。"
                "★ M8 vision 修复（2026-09-24）新增：M34 用各按钮自己的文字承担标签语义导致 56px 小方块"
                "溢出（vision ③④），现按参考作补回标签条语义——行标签归本件，方块内只放单字符。" % y})
idx = next(i for i, e in enumerate(d['elements']) if e['id'] == 'dr.btn_tx_level2')
d['elements'][idx + 1:idx + 1] = new_els
print('V1 新增 4 件行标签：', ' '.join(e['id'] for e in new_els))

# ---------- V1⑤：表情行 —— faceright 文字改「表情」、face_tx 扩到 #facerect 全宽 ----------
e = by_id['dr.btn_tx_faceright']
e['sample'] = '表情'
e['note'] = (e['note'] + "　★ M8 vision 修复（2026-09-24）：「表情右」→「表情」—— 参考作该钮（`faceright`，"
             "p76_c009_l22100.png）烘焙文字实测即「表情」（53×30 放不下 3 字，「表情右」溢出且与 "
             "`#汎用/表情` 模板叠字，vision ⑤）。循环翻差分的语义由运行期行为承担。")
e = by_id['dr.face_tx']
assert e['w'] == 68
e['w'] = 187
e['sample'] = '表情 01'
e['note'] = ("**当前差分/表情名槽**（引擎绘制，运行期文本槽）。矩形 = PSB idx76 `#facerect` (277,477,187,56)"
             "全宽。★ M8 vision 修复（2026-09-24）：M4 首版为避让 `#汎用/表情` 模板芯片而取左段 w68"
             "（产生孤立「01」，vision ⑤）；该模板芯片本轮已删（参考作可见层无此件），本槽恢复参考实测全宽；"
             "sample 由「01」改「表情 01」（V3 静态版式占位，真值由编程组接）。")
print('V1⑤ faceright/face_tx 完成')

# ---------- V5：初始化钮放大 + 三态（复用既有 state_assets） ----------
for eid in ('dr.reset', 'dr.reset_tx', 'dr.hit_reset'):
    e = by_id[eid]
    assert (e['x'], e['y'], e['w'], e['h']) == (1264, 44, 78, 25), eid
    e['x'], e['y'], e['w'], e['h'] = 1225, 33, 77, 40
by_id['dr.reset']['note'] = ("「初始化」键（PSB idx76 `reset`：オフ (1264,44,78,25)／オンマウス (1260,40,86,33)"
    "／オン (1225,33,154,40)）。★ M8 vision 修复（2026-09-24）：矩形 78×25 → **(1225,33,77,40)** = 参考作"
    "オン态的左半宽 × 全高（x/y 照オン态原点；素材 `x_ui_reset_on.png` 77×40 恰 1:1，off/over 48×25 经 "
    "nine 等比入格）。原 78×25 过小且 20px 文字溢出药丸（vision：初始化过小且白底白字）。三态 "
    "`state_assets` 机制照旧（M35b 口径），`state_group`「dress.reset」与热区联动不变。⚠️ 与参考作オン态 "
    "154 宽的差 = 素材能力上限（48/77 宽源），要 154 宽需重出素材 —— 留美术/主代理裁决。")
by_id['dr.reset_tx']['note'] = ("按钮文字（引擎绘制）。★ M8 vision 修复（2026-09-24）：随 `dr.reset` 放大到 "
    "(1225,33,77,40)；字号维持我方按钮阶梯 20（3 字 60px < 药丸 77px，实测不溢出），墨色 "
    "@palette.node_locked（深墨）在浅药丸上对比充分。")
by_id['dr.hit_reset']['note'] = (by_id['dr.hit_reset']['note'] +
    "　★ M8 vision 修复（2026-09-24）：矩形随 `dr.reset` 同步到 (1225,33,77,40)。")
print('V5 初始化三件放大完成')

json.dump(d, io.open(F, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
io.open(F, 'a', encoding='utf-8').write('\n')
print('37_dress.json 已写盘，元素数', len(d['elements']))

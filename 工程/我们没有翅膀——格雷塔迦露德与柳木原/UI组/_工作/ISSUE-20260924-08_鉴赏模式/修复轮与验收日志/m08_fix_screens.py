# -*- coding: utf-8 -*-
"""ISSUE-20260924-08 一审打回修复 · 数据侧第二批：
37_dress 屏 note 追加、27_gallery（page_flag + note 订正）、28_music（page_flag + pg_tx 两件互斥 + 删 speana）、
38_replay（page_flag + pg_tx 两件互斥 + note 追认）。一次性脚本（UI组\\临时\\）。"""
import json, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(os.path.dirname(HERE), 'layout', 'screens')

def load(f):
    return json.load(io.open(os.path.join(SC, f), encoding='utf-8'))

def save(f, d):
    json.dump(d, io.open(os.path.join(SC, f), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    io.open(os.path.join(SC, f), 'a', encoding='utf-8').write('\n')

# ══════════ 37_dress：屏 note 追加本轮修复记录 ══════════
d = load('37_dress.json')
d['note'] = (d['note'] +
    "\n---\n★ **M8 一审打回 + vision 修复（2026-09-24，本轮）**：\n"
    "① **删 10 件**：`dr.top`（顶部白带，vision ④——他三页无此物；参考作 caption 文字已由外壳承担，本件是"
    "无字的空白横带）；`dr.hit_back`（底部中央「返回」重影，vision ③——参考作 `#helptip` 是运行期提示槽"
    "**非返回键**，M34 误挂 label；返回由外壳 `gs.back_*`（1660,30）承担）；`dr.tag_服装`/`dr.tag_tx_服装`、"
    "`dr.tag_時間用`/`dr.tag_tx_時間用`、`dr.tag_表情`/`dr.tag_tx_表情`、`dr.tag_背景`/`dr.tag_tx_背景`"
    "（4 组叠印件，vision ①②⑤⑥——均来自参考作 `#汎用`/状态三连的**模板层**，参考作可见层无此物：keep 钮"
    "烘焙文字=保持、dress0 由面板烘焙承担、表情=faceright 钮自带、背景无对应按钮）。素材一律保留不删。\n"
    "② **改 24 件 + 增 4 件**：人名 11 行文字 x0→**x34**（`名前/#text` 实测起点，vision 人名贴左缘）；"
    "pose/diff/level 9 件小方块文字改**单字符**（1 2 3 / 1 2 3 / S M L，参考作面板烘焙即此）；新增 4 件"
    "行标签 `dr.row_tx_dress/pose/diff/level`（PSB `chstate` 实测行带）；`dr.btn_tx_faceright`「表情右」→"
    "「表情」；`dr.face_tx` 恢复 `#facerect` 全宽 187；初始化三件（image/text/hit）放大到 **(1225,33,77,40)**。\n"
    "③ **页签 3 文字保持「立绘鉴赏」**（主代理追认：用户指令原文即「立绘鉴赏」；参考作全称「立绘鉴赏模式」"
    "登记为来源事实，外壳 `gs.tab3_tx` 用前者）。\n"
    "④ 本屏**无 list、无页码** ⇒ 不参与 R3 页码 flag 接线（`page_flag` 不声明）。")
save('37_dress.json', d)
print('37_dress note 追加完成')

# ══════════ 27_gallery：page_flag + 两处 note 订正 ══════════
d = load('27_gallery.json')
assert d['id'] == 'gallery'
d['page_flag'] = 'gal_page'
d['note'] = (d.get('note', '') +
    "\n★ **M8 一审 R3 修复（2026-09-24）**：新增屏级字段 **`page_flag: \"gal_page\"`** —— 翻页动作"
    "`gallery_page_prev/next` 写完 `UIScrPage` 后按本字段把页号（1 基）写进 flag（krkr `uiScreenFlagSet` ／"
    "HTML `setFlag`），`gal.page_tx_01..12` 的 `vis_flag:gal_page` 互斥文本由此**真正随页切换**；"
    "`uiScreenPageVariantClearFor` 归零时同步复位 \"1\"。字段语义见 `_schema.md` §六 M1 块。")
gl = None
for e in d['elements']:
    if e['id'] == 'gal.list':
        gl = e
old = 'HTML 侧 `replica.js::buildList` **已按此口径实现**（`row = floor(k/cols)` / `c = k%cols`，`perPage = cols*rowsCap`）；**krkr 侧 `ui_widget.tjs` 的 `uiWidgetListItemRect` / `uiWidgetListPage` / `uiWidgetRect` 需按同一口径补齐**（当前 `uiWidgetRect` 对横向 list 把 `r.h` 写成 span（横向跨度 = 宽度）⇒ 必须先修，否则该 list 的矩形会横跨全屏并吞掉页码键的悬停）。'
new = 'HTML 侧 `replica.js::buildList` **已按此口径实现**（`row = floor(k/cols)` / `c = k%cols`，`perPage = cols*rowsCap`）；krkr 侧 `ui_widget.tjs` 的 `uiWidgetListItemRect` / `uiWidgetListPage` / `uiWidgetRect` **已由 M1 按同一口径补齐**（一审时「`uiWidgetRect` 把 `r.h` 写成 span ⇒ 必须先修」的旧患已修，本句按 M8 一审订正删去过时警告）。'
assert old in gl['note'], 'gal.list note 旧句未命中'
gl['note'] = gl['note'].replace(old, new)
nv = gl['item_variants']['next']
assert nv['x'] == 260 and nv['asset'] == 'ui/x_ui_gal_vnext_off.png'
nv['note'] = nv['note'].replace('（`item_variants.prev`）', '（`item_variants.next`）')
nv['note'] = nv['note'].replace('块内局部 5,66,26×34 —— 落在栏位右侧留边带内', '块内局部 260,66,26×34 —— 落在栏位右侧留边带内')
nv['note'] = nv['note'].replace('三态件 `ui/x_ui_gal_vprev_{off,over,on}.png`', '三态件 `ui/x_ui_gal_vnext_{off,over,on}.png`')
assert 'item_variants.next' in nv['note'] and '260,66' in nv['note'] and 'vnext' in nv['note']
save('27_gallery.json', d)
print('27_gallery 完成（page_flag + 2 处 note 订正）')

# ══════════ 28_music：page_flag + pg_tx 两件互斥 + 删 speana（V6） ══════════
d = load('28_music.json')
assert d['id'] == 'music'
d['page_flag'] = 'music_page'
d['flags_default'] = {'music_page': '1'}
els = d['elements']
pg = None
for e in els:
    if e['id'] == 'mu.pg_tx':
        pg = e
assert pg is not None
base_note = ('页码指示（引擎绘制，几何与 M2 的 `gal.page_tx_01..12` 同款 858,939,204×56）。'
             '★ M8 一审 R3 修复（2026-09-24）：原静态单件「1 / 2」翻页不变（vision/一审），改为与 CG 页同款'
             '的 **2 件互斥文本**（`vis_flag:music_page` + `vis_when:"1"/"2"`），屏级 `page_flag:"music_page"`、'
             '`flags_default.music_page:"1"`；翻页动作把 1 基页号写进该 flag ⇒ 第 2 页显示 2 / 2。'
             '共 2 页（%d 曲 / 每页 %d）。')
tx1 = dict(pg)
tx1['id'] = 'mu.pg_tx_1'
tx1['sample'] = '1 / 2'
tx1['vis_flag'] = 'music_page'
tx1['vis_when'] = '1'
tx1['note'] = base_note % (59, 30) + '本件 = 第 1 页（vis_when:"1"）。'
tx2 = dict(pg)
tx2['id'] = 'mu.pg_tx_2'
tx2['sample'] = '2 / 2'
tx2['vis_flag'] = 'music_page'
tx2['vis_when'] = '2'
tx2['note'] = base_note % (59, 30) + '本件 = 第 2 页（vis_when:"2"）。'
idx = els.index(pg)
els[idx:idx + 1] = [tx1, tx2]
# V6：删 speana（频谱装饰带 781,966,359,48 压页码行 y931..1003）
spe = [e for e in els if e['id'] == 'mu.speana']
assert len(spe) == 1
els.remove(spe[0])
d['note'] = (d['note'] +
    "\n★ **M8 一审 R3/V6 修复（2026-09-24）**：① `mu.pg_tx` 静态单件 → `mu.pg_tx_1/2` 两件互斥（`music_page` "
    "flag，见 `_schema.md` §六 M1 块的屏级 `page_flag` 字段）；② **删 `mu.speana`**（V6：频谱装饰带 "
    "(781,966,359,48) 与页码键（y931..1003）整面叠加且被页码行横穿——参考作该件是**运行期频谱占位矩形**"
    "（`Sound/#speana`，无部件图），参考作 BGM 页**无页码键**故不冲突，本屏补了页码键 ⇒ 装饰让位功能件；"
    "素材 `x_ui_speana.png` 保留不删，编程组做真频谱时可另择位重挂）；③ 曲目行 action `bgm_*` 七键已由"
    "主代理裁决为**拟用名**（音频接线留编程组，见 `_schema.md` §六）。")
save('28_music.json', d)
print('28_music 完成（pg_tx 两件互斥 + page_flag + 删 speana）')

# ══════════ 38_replay：page_flag + pg_tx 两件互斥 + note 追认 ══════════
d = load('38_replay.json')
assert d['id'] == 'replay'
d['page_flag'] = 'replay_page'
d['flags_default'] = {'replay_page': '1'}
els = d['elements']
pg = None
for e in els:
    if e['id'] == 'rp.pg_tx':
        pg = e
assert pg is not None
tx1 = dict(pg)
tx1['id'] = 'rp.pg_tx_1'
tx1['sample'] = '1 / 2'
tx1['vis_flag'] = 'replay_page'
tx1['vis_when'] = '1'
tx1['note'] = ('页码指示「1 / 2」（引擎绘制，M3 同款几何 858,939,204×56）。★ M8 一审 R3 修复（2026-09-24）：'
               '原静态单件翻页不变（如实登记过「恒显示 1 / 2」），现改为与 CG 页同款 **2 件互斥文本**'
               '（`vis_flag:replay_page`），屏级 `page_flag:"replay_page"`、`flags_default.replay_page:"1"`；'
               '翻页动作写 1 基页号 ⇒ 随页切换。本件 = 第 1 页（vis_when:"1"）。')
tx2 = dict(pg)
tx2['id'] = 'rp.pg_tx_2'
tx2['sample'] = '2 / 2'
tx2['vis_flag'] = 'replay_page'
tx2['vis_when'] = '2'
tx2['note'] = ('页码指示「2 / 2」（引擎绘制）。★ M8 一审 R3 修复（2026-09-24）：与 `rp.pg_tx_1` 互斥'
               '（`vis_flag:replay_page` / `vis_when:"2"`）。本件 = 第 2 页。')
idx = els.index(pg)
els[idx:idx + 1] = [tx1, tx2]
d['note'] = d['note'].replace(
    '②动画实为 **10 件**（派单 11 件之差 = `ota_bg.txt` 是 data 文本非 movie，需主代理裁决）',
    '②动画 **10 件**（主代理 2026-09-24 已追认：派单 11 件之差 = `ota_bg.txt` 是 data 文本非动画，ot 2 / ota 3 / otp 1 / otv 2 / np 2）')
d['note'] = d['note'].replace(
    '③`replay_play` 动作名待 M1 补进 `_schema.md` 动作名表；④页码文本未接线（恒 1/2）',
    '③`replay_play:<行号>` 动作名已由 M8 一审 R2 补进 `_schema.md` 动作名表（语义 = **派发即止**，音频/跳转生效留编程组）；④页码文本已接线（M8 一审 R3：`rp.pg_tx_1/2` 两件互斥 + `replay_page` flag，重进归零由 push 路径 `uiScreenPageVariantClearFor` 承担）')
save('38_replay.json', d)
print('38_replay 完成（pg_tx 两件互斥 + page_flag + note 追认）')

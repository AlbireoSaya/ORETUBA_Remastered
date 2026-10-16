# -*- coding: utf-8 -*-
r"""一审打回项修复：生成**第二版工作单**（runs_v2.json）与**主译文表**（master.tsv）。

一审（reviewer）打回的问题与本次修法：
  1. `｢｣`（SJIS 单字节括号，0xA2/0xA3）未被替换 → GBK 下被当前导字节，**两字节错位**；
     修法：把 config1/config2 的两条设置页签名**加宽**到含括号（24 字节），译文自带 `「」`。
  2. `スロット%` 译文被补齐撑断 `%s` → 槽号失效；修法：译文**恰好 9 字节且以 `%` 结尾**。
  3. 抽取盲区漏掉的显示串：2 字串（する/行う/低い/通常/高い/入力/命令）、
     孤立 CJK 标点（、）「）、日文混排短串（音量 ％～ ％）、voiceinf 单字名（咲夜/狂夜/満夜/牧師/鳳 鳴/鳳 翔）、
     全角数字池（５４３２１）→ **补入**。
  4. 夹心英文词（CPU/DirectSound/Windows/Sleep…）语序破坏 → **改写为「…下，…」或把谓语前置**。
  5. `id40` 引擎字面量 `0` 重复 → 译文改成从 `0` 之后接续。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
SYS = os.path.join(WS, '工程', '我们没有翅膀R', '工具', 'sysui')    # 工作单与译文随工具入库（原在 临时，会被清理）
WORK = os.path.join(WS, '工程', '我们没有翅膀R', '工具', 'sysui')  # 子代理产物已随工具入库
SRC = os.path.join(WS, '工程', '我们没有翅膀R', '工具')

sys.path.insert(0, SRC)
import lpk_patch as LP                                   # noqa: E402

# ── 1. 读第一版工作单 + A/B 译文 ─────────────────────────────────────────
rows = json.load(io.open(os.path.join(SYS, 'runs.json'), encoding='utf-8'))
for i, r in enumerate(rows, 1):
    r['id'] = i
trans = {}
for m in ('A', 'B'):
    for ln in io.open(os.path.join(WORK, m, 'out_%s.tsv' % m), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if ln.strip():
            k, v = ln.split('\t', 1)
            trans[int(k)] = v

# ── 2. 加宽两条（含 ｢｣）────────────────────────────────────────────────
WIDEN = {  # file -> (旧offset, 旧n) -> (新offset, 新n, 新译文)
    ('config1.sob', 58151, 22): (58150, 24, '「系统·文本设置」'),
    ('config2.sob', 52991, 22): (52990, 24, '「声音·帧设置」'),
}
newrows = []
for r in rows:
    key = (r['file'], r['off'], r['n'])
    if key in WIDEN:
        off, n, cn = WIDEN[key]
        r = dict(r, off=off, n=n)
        trans[r['id']] = cn
    newrows.append(r)
rows = newrows

# ── 3. 一审指出的语序/字面量问题：改写定稿译文 ──────────────────────────
FIX = {
    # ── 图形类裁决（原在 build_sysui.OVERRIDE，现并入本表，避免两处维护）──
    32:  '图形', 33: '图形缓存限制',
    36:  '设置用于图形缓存的内存最大容量。',
    37:  '运行中频繁发生内存交换时，将设置改为“不进行缓存”可能有所改善。',
    124: '的使用由此处设置。',
    # ── 一审打回项 ──
    8:   '时钟的测量',                       # 起動ログ作成時に + CPU + クロックを計測
    10:  '在应用程序启动时调查运行环境时，设置是否测量',   # 二审：把 8 个全角空格的中缝改为「谓语前置」
    11:  '时钟。',                            # 承接上面 →「…设置是否测量CPU时钟。」
    63:  '进行画面特效等处理时，设置',          # 二审：中缝 3 空格 → 0（恰好 28B）
    61:  '使用率降低',                       # 画面効果処理等で + CPU + 使用率を低減
    64:  '使用率是否降低。',                  # …際に、 + CPU + 使用率を低減するかどうかを設定します。
    74:  '方式',                             # Sleep + を使用（选项名：Sleep方式）
    18:  '下，是否禁止自动启动屏幕保护程序。',
    21:  '下，是否禁止自动切断显示器电源。',
    28:  '下，是否禁止自动进入睡眠模式。',
    40:  '时不进行缓存处理。设为较小值可抑制内存占用，但文本绘制的性能会下降。',
    71:  '下，设置创建缓冲区的内存类型。',
    76:  '下，设置流式播放时的同步处理方法。',
    80:  '下，进行同步处理。',
    85:  '下，设置缓冲区是否获取全局焦点。',
    87:  '下，播放会被静音。',
    91:  '的解码线程优先级设置。',
    103: '下，初始化失败时设置是否显示警告对话框。',
    131: '指令可用时是否使用。', 134: '指令可用时是否使用。',
    137: '指令可用时是否使用。', 140: '指令可用时是否使用。',
    181: '存档栏位%', 184: '存档栏位%', 195: '存档栏位%', 198: '存档栏位%',   # 9B，% 结尾，%s 不被撑断
    206: '光驱。',
}
trans.update(FIX)

# ── 4. 补入第一遍漏掉的显示串（file, off, n, 译文）──────────────────────
ADD = [
    ('config.dat', 79, 4, '执行'), ('config.dat', 332, 4, '执行'),
    ('config.dat', 1686, 2, '、'), ('config.dat', 2722, 2, '）'),
    ('config.dat', 2750, 2, '）'), ('config.dat', 2778, 2, '）'),
    ('config.dat', 2993, 4, '执行'), ('config.dat', 3337, 4, '执行'),
    ('config.dat', 3613, 4, '执行'), ('config.dat', 3852, 4, '执行'),
    ('config.dat', 5131, 4, '低'), ('config.dat', 5157, 4, '普通'), ('config.dat', 5183, 4, '高'),
    ('config.dat', 5992, 4, '输入'),
    ('config.dat', 6123, 2, '「'), ('config.dat', 6158, 2, '「'), ('config.dat', 6385, 2, '「'),
    ('config.dat', 6707, 4, '执行'), ('config.dat', 6902, 4, '执行'),
    ('config.dat', 7157, 4, '指令'), ('config.dat', 7288, 4, '指令'),
    ('config.dat', 7418, 4, '指令'), ('config.dat', 7549, 4, '指令'),
    ('config2.sob', 53039, 4, '音量'), ('config2.sob', 53046, 4, '％～'), ('config2.sob', 53053, 2, '％'),
    ('voiceinf.dat', 627, 4, '咲夜'), ('voiceinf.dat', 643, 4, '狂夜'),
    ('voiceinf.dat', 659, 4, '满夜'), ('voiceinf.dat', 760, 4, '牧师'),   # 二审：漏简化
    ('title.sob', 39029, 2, '５'), ('title.sob', 39032, 2, '４'), ('title.sob', 39035, 2, '３'),
    ('title.sob', 39038, 2, '２'), ('title.sob', 39041, 2, '１'),
    ('title2.sob', 31006, 2, '５'), ('title2.sob', 31009, 2, '４'), ('title2.sob', 31012, 2, '３'),
    ('title2.sob', 31015, 2, '２'), ('title2.sob', 31018, 2, '１'),
]

# voiceinf.dat 的「鳳 鳴 / 鳳 翔」：姓与名各 1 字、中间半角空格，被「≥2 日文字符」判据漏掉 → 定点补
_lp = LP.load(os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK'))
_vd = _lp and LP.read_entry(_lp, 'voiceinf.dat')['plain']
for sur in ('鳳'.encode('cp932'),):
    i = 0
    while True:
        i = _vd.find(sur, i)
        if i < 0:
            break
        seg = _vd[i:i + 5]
        try:
            t = seg.decode('cp932')
        except Exception:
            t = ''
        if len(t) == 3 and t[1] == ' ':
            cn = '凤 ' + ('鸣' if t[2] == '鳴' else '翔' if t[2] == '翔' else t[2])
            ADD.append(('voiceinf.dat', i, 5, cn))
        i += 2

base = max(r['id'] for r in rows)
for k, (f, off, n, cn) in enumerate(ADD, 1):
    rows.append(dict(id=base + k, file=f, off=off, n=n, jp='', before='', after=''))
    trans[base + k] = cn

# ── 5. 写盘 ────────────────────────────────────────────────────────────
json.dump(rows, io.open(os.path.join(SYS, 'runs_v2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
io.open(os.path.join(SYS, 'master.tsv'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join('%d\t%s' % (i, trans[i]) for i in sorted(trans)) + '\n')

print('工作单 v2：%d 行（原 %d + 加宽 2 条保留原 id + 新增 %d）' % (len(rows), base, len(ADD)))
miss = [r['id'] for r in rows if r['id'] not in trans]
print('缺译文:', miss if miss else '无')
over = []
for r in rows:
    cn = trans.get(r['id'])
    if cn is None:
        continue
    try:
        b = cn.encode('gbk')
    except UnicodeEncodeError:
        over.append((r['id'], 'GBK 不可编码', cn)); continue
    if len(b) > r['n']:
        over.append((r['id'], '%d > %d' % (len(b), r['n']), cn))
print('超长/不可编码:', over if over else '无')
print('runs_v2.json / master.tsv 已写出')

# -*- coding: utf-8 -*-
"""
W11c · 系统UI（sys + etc）六源统一
=================================
输入（只读）:
  krkr素材库\{ot,ota,otp,otv}\sys\*.png
  krkr素材库\otv\etc\*.png
  ../../../美术/系统UI尺寸索引.tsv      (W9 全量尺寸索引, 2361 图像)
  ../../../美术/otv素材内容判读.tsv     (W3 人工判读, 306 行)

输出（写入 美术统一\）:
  系统UI\<统一名>.png            统一后的图像（原字节复制）
  清单_系统UI.tsv
  待复核_系统UI.tsv
  _W11c_统计.json                (中间统计, 供自证)

规则: 美术统一_规格.md §二.3 / §三 / §五 / §六
纪律: 只读源; 不缩放/不重编码; 可复跑
"""
import os, sys, json, hashlib, collections, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.dirname(HERE)                      # 资源组
LIB  = os.path.join(RES, 'krkr素材库')
ART  = os.path.join(RES, '美术')
OUT  = os.path.join(RES, '美术统一')
IMGDIR = os.path.join(OUT, '系统UI')

SIZE_INDEX = os.path.join(ART, '系统UI尺寸索引.tsv')
OTV_NOTE   = os.path.join(ART, 'otv素材内容判读.tsv')

SRC_PREFIX = {'ot': 'ot_', 'ota': 'ota_', 'otp': 'otp_', 'otv': 'otv_'}
# 规格 §3.2.3 源优先级
SRC_RANK = {'ot': 0, 'otr': 1, 'ota': 2, 'otp': 3, 'otv': 4, 'np': 5}

CATS = ['消息窗', '菜单', '标题', '存档', '图标', '转场遮罩', '字体', '其他', '未判定']

# ---- W3 usage -> 类别 ----
USAGE2CAT = {
    'transition_mask': '转场遮罩',
    'message_window':  '消息窗',
    'eyecatch':        '标题',
    'logo':            '标题',
    'config':          '菜单',
    'backlog':         '菜单',
    'scene_select':    '菜单',
    'loading':         '其他',
}

# ---- W3 content_note 派生 (usage 为空但有人工描述) ----
NOTE2CAT = [
    ('转场/遮罩', '转场遮罩'), ('纯黑全屏', '转场遮罩'), ('纯白全屏', '转场遮罩'),
    ('纯红全屏', '转场遮罩'), ('纯棕全屏', '转场遮罩'), ('纯黄全屏', '转场遮罩'),
    ('粒子', '其他'), ('纹理', '其他'), ('光柱', '其他'), ('注意事项', '其他'),
    ('章标题卡', '标题'),
    ('CG 相册页', '其他'),
    ('画廊', '菜单'), ('音乐', '菜单'), ('影片', '菜单'),
    ('存档画面底板', '存档'), ('读档画面底板', '存档'), ('快速读档画面底板', '存档'),
    ('存档提示', '存档'), ('存档/读档槽面板', '存档'),
    ('消息窗', '消息窗'), ('选择支窗', '消息窗'),
    ('图标 sprite', '图标'),
    ('系统菜单字', '菜单'),
]


def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        hdr = f.readline().rstrip('\n').split('\t')
        rows = [ln.rstrip('\n').split('\t') for ln in f if ln.strip()]
    return hdr, rows


def md5f(path, buf=1 << 20):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ---------------- 1. 读索引 ----------------
hdr, idx_rows = read_tsv(SIZE_INDEX)
print('[i] 尺寸索引 %d 行 表头=%s' % (len(idx_rows), hdr))
images = []          # (src, kind, w, h, mode, out_relpath, bytes)
for c in idx_rows:
    images.append({'src': c[0], 'kind': c[1], 'w': int(c[2]), 'h': int(c[3]),
                   'mode': c[4], 'rel': c[5].replace('/', os.sep), 'bytes': int(c[6])})

# ---------------- 2. 读 W3 判读 ----------------
hdr2, note_rows = read_tsv(OTV_NOTE)
print('[i] otv判读 %d 行 表头=%s' % (len(note_rows), hdr2))
w3 = {}   # rel(/) -> (usage, content_note)
for c in note_rows:
    w3[c[0]] = (c[5], c[6])

# ---------------- 3. 文件系统核对 ----------------
fs_png = set()
fs_non = []
for s in ('ot', 'ota', 'otp', 'otv'):
    d = os.path.join(LIB, s, 'sys')
    for f in os.listdir(d):
        if f.lower().endswith('.png'):
            fs_png.add(s + '/sys/' + f)
        else:
            fs_non.append((s, 'sys', f, os.path.getsize(os.path.join(d, f))))
d = os.path.join(LIB, 'otv', 'etc')
for f in os.listdir(d):
    if f.lower().endswith('.png'):
        fs_png.add('otv/etc/' + f)
    else:
        fs_non.append(('otv', 'etc', f, os.path.getsize(os.path.join(d, f))))

idx_png = {im['rel'].replace(os.sep, '/') for im in images}
only_fs = fs_png - idx_png
only_idx = idx_png - fs_png
print('[i] 磁盘 png=%d 索引 png=%d  仅磁盘=%d 仅索引=%d' % (len(fs_png), len(idx_png), len(only_fs), len(only_idx)))
if only_fs or only_idx:
    print('[!] 差异: only_fs=%s only_idx=%s' % (sorted(only_fs)[:5], sorted(only_idx)[:5]))

# ---------------- 4. 分组 ----------------
def norm_key(src, rel):
    """规格 §2.3: 去源前缀 + 小写; otv/etc 与 sys 同命名空间(同 stem 才归并)"""
    name = os.path.basename(rel)
    p = SRC_PREFIX[src]
    if not name.lower().startswith(p):
        raise SystemExit('前缀不符: %s %s' % (src, name))
    return name[len(p):].lower()

groups = collections.defaultdict(list)
for im in images:
    k = norm_key(im['src'], im['rel'])
    groups[k].append(im)

# ---------------- 5. 分类判定 ----------------
def aspect_diff(a, b):
    """宽高比相对差 (相对较小者)"""
    ra, rb = a[0] / a[1], b[0] / b[1]
    return abs(ra - rb) / min(ra, rb)

def classify_group(cands):
    if len(cands) == 1:
        return 'single', None
    sizes = {(c['w'], c['h']) for c in cands}
    if len(sizes) == 1:
        hs = {c['md5'] for c in cands}
        return ('same_res_same' if len(hs) == 1 else 'same_res_diff'), None
    # 多尺寸: 比较最大与最小像素候选的宽高比
    srt = sorted(cands, key=lambda c: (c['w'] * c['h'], c['w']))
    amax = aspect_diff((srt[-1]['w'], srt[-1]['h']), (srt[0]['w'], srt[0]['h']))
    # 取全体两两最大差
    pairs = []
    for i in range(len(srt)):
        for j in range(i + 1, len(srt)):
            pairs.append(aspect_diff((srt[i]['w'], srt[i]['h']), (srt[j]['w'], srt[j]['h'])))
    amax = max(pairs) if pairs else 0.0
    return ('diff_res_same_drawing' if amax <= 0.02 else 'diff_res_diff_drawing'), amax

def pick(cands):
    return sorted(cands, key=lambda c: (-(c['w'] * c['h']), -c['w'], SRC_RANK.get(c['src'], 9), c['rel']))[0]

# ---------------- 6. 类别 ----------------
def cat_for(cands, key):
    """优先 W3 人工 -> W3描述派生 -> 启发式"""
    for c in cands:
        if c['src'] == 'otv':
            rel = c['rel'].replace(os.sep, '/')
            u, note = w3.get(rel, ('', ''))
            if u:
                return USAGE2CAT.get(u, '其他'), 'W3人工', 'W3 usage=%s' % u
            if note:
                for kw, cat in NOTE2CAT:
                    if kw in note:
                        return cat, 'W3人工(描述派生)', 'W3 content_note: %s' % note[:40]
                return '未判定', 'W3人工(描述派生)', 'W3 content_note 无匹配关键词: %s' % note[:40]
    return heuristic(key)

import re
# 角色名族（名牌/头像缩略图，280×105 / 320×120 / 100×75 / 198×99）
FAMILY = re.compile(r'^_?(asu|hiy|kob|nar|miy|mis|ai|eri|yuu|mas|aki|ari|har|kin|kaz|kur|sono|yy|taka|yuji|syu|sin|saw|sak|tak)_?\d')

HEUR = [
    (lambda k: k.startswith('rule'), '转场遮罩', '名 rule*（转场 wipe/mask）'),
    (lambda k: k.startswith('tl'), '标题', '名 tl*（title 画面）'),
    (lambda k: 'win' in k or k.startswith('ms_'), '消息窗', '名含 win / ms_（消息窗）'),
    (lambda k: k.startswith('nm_frm'), '消息窗', '名 nm_frm*（消息窗名字框 222×36）'),
    (lambda k: 'log' in k or k.startswith('bk'), '菜单', '名含 log/bk（履历·回想）'),
    (lambda k: any(t in k for t in ('save', 'load', 'qsave', 'qload', 'saving', 'sv_', 'ld_', 'ss_', 'sl_')), '存档', '名含 save/load/sv_/ld_/ss_（存读档）'),
    (lambda k: any(t in k for t in ('cfg', 'config', 'cf_', 'menu', 'sys', 'sm_', 'ex_', 'op_', 'ga_', 'gl_', 'mc_', 'mu_', 'mv_', 'sel', 'cm_')), '菜单', '名含 cfg/menu/sys/gl_/mc_/cm_/sel（菜单·设置）'),
    (lambda k: k.startswith('if_'), '图标', '名 if_*（按钮边框部件 1×5/13×1/228×25）'),
    (lambda k: k.startswith('no_'), '图标', '名 no_*（无数据/无图占位 120×90）'),
    (lambda k: any(t in k for t in ('icon', 'btn', 'skp', 'skip', 'auto', '_s_ret', '_voice', '_prev', '_next')), '图标', '名含 icon/skp/skip/auto/_s_ret/_voice（图标·按钮）'),
    (lambda k: any(t in k for t in ('title', 'logo', 'ec_', 'ec1', 'ec2', 'ec3', 'ec4', 'ec5', 'ec6')), '标题', '名含 title/logo/ec*（标题·过场）'),
    (lambda k: 'font' in k, '字体', '名含 font'),
    (lambda k: FAMILY.match(k), '其他', '角色名族前缀（角色名牌/头像 280×105·320×120·100×75·198×99）'),
    (lambda k: k.startswith('th_'), '其他', '名 th_*（缩略图/控件 UI 件 198×99·92×17·68×5）'),
    (lambda k: any(t in k for t in ('snow_', 'gr_lt', 'noise')), '其他', '名 snow_/gr_lt/noise（粒子·装饰）'),
    (lambda k: re.match(r'^sr_\d', k), '其他', '名 sr_##（408×308 事件 CG 缩略图；W11c 抽看 sr_01 实测）'),
    (lambda k: k in ('op.png', 'sr.png'), '其他', '单体名 op/sr（280×105，与角色名牌同尺寸）'),
    (lambda k: k.startswith('sc_') or re.match(r'^pv\d', k) or k.startswith('movie'), '其他', '名 sc_/pv*/movie*（场景·影片标签 280×105）'),
    (lambda k: any(t in k for t in ('bg', 'paper_', 'kin', 'ten', 'buru', 'yy_', 'e_', 'gc_', 'cg_', 'zz_', 'xx_')), '其他', '名含 bg/角色缩略图等（其他 UI 件）'),
]

def heuristic(key):
    for fn, cat, why in HEUR:
        if fn(key):
            return cat, '启发式', why
    return '未判定', '启发式', '命名无法归类'


# ---- rule* 内容相关性抽检（Lucifen ot 800×600 vs PSV otv 960×544）----
RULE_CORR = {}
try:
    from PIL import Image
    def _sig(p, n=96):
        im = Image.open(p).convert('L').resize((n, n), Image.BILINEAR)
        d = list(im.getdata()); m = sum(d) / len(d)
        v = (sum((x - m) ** 2 for x in d)) ** .5 or 1
        return [(x - m) / v for x in d]
    for k in groups:
        if not k.startswith('rule'):
            continue
        a = [c for c in groups[k] if c['src'] == 'ot']
        b = [c for c in groups[k] if c['src'] == 'otv']
        if a and b:
            sa, sb = _sig(os.path.join(LIB, a[0]['rel'])), _sig(os.path.join(LIB, b[0]['rel']))
            RULE_CORR[k] = round(sum(x * y for x, y in zip(sa, sb)), 3)
    hi = sum(1 for v in RULE_CORR.values() if v >= 0.5)
    print('[i] rule* 内容相关抽检: n=%d 高相关(>=0.5)=%d 低相关=%d' % (len(RULE_CORR), hi, len(RULE_CORR) - hi))
except ImportError:
    print('[!] 无 PIL，跳过 rule 相关抽检')

# ---------------- 7. 组装 ----------------
os.makedirs(IMGDIR, exist_ok=True)
unified, review = [], []
cat_cnt, src_cnt = collections.Counter(), collections.Counter()
total_cand = 0
saved_bytes = 0

for key in sorted(groups):
    cands = groups[key]
    total_cand += len(cands)
    for c in cands:
        p = os.path.join(LIB, c['rel'])
        c['md5'] = md5f(p)
        c['path'] = p
    cls, adiff = classify_group(cands)
    win = pick(cands)
    cat, src_of_cat, why_cat = cat_for(cands, key)
    uname = key
    shutil.copyfile(win['path'], os.path.join(IMGDIR, uname))
    unified.append({
        'uname': uname, 'cat': cat, 'w': win['w'], 'h': win['h'], 'mode': win['mode'],
        'bytes': win['bytes'], 'src': win['src'], 'orig': os.path.basename(win['rel']),
        'ncand': len(cands), 'cls': cls, 'catsrc': src_of_cat, 'why': why_cat,
        'md5': win['md5'],
    })
    cat_cnt[cat] += 1
    src_cnt[win['src']] += 1
    saved_bytes += sum(c['bytes'] for c in cands) - win['bytes']

    need_review = cls in ('same_res_diff', 'diff_res_diff_drawing')
    if need_review or len(cands) > 1 and adiff is not None and adiff > 0.02:
        cand_str = ' ; '.join('%s:%s %dx%d md5=%s' % (c['src'], os.path.basename(c['rel']), c['w'], c['h'], c['md5'][:8])
                              for c in sorted(cands, key=lambda x: (-(x['w'] * x['h']), x['src'])))
        doubt = []
        if cls == 'same_res_diff':
            doubt.append('同尺寸但 md5 不同：内容确有差异（未逐像素比对，仅按 md5 判定）')
        if cls == 'diff_res_diff_drawing':
            dw = max(c['w'] for c in cands) - min(c['w'] for c in cands)
            dh = max(c['h'] for c in cands) - min(c['h'] for c in cands)
            if adiff * 100 > 10:
                doubt.append('宽高比差异 %.1f%%（>2%%）且绝对尺寸差大：疑似不同版式或不同元素' % (adiff * 100))
            elif (dw == 0 or dh == 0) and max(dw, dh) <= 2:
                doubt.append('单边尺寸相同、另一边仅差 %dpx：宽高比启发式在细长/小图上不稳定，实为同一元素的版本差异' % max(dw, dh))
            else:
                doubt.append('宽高比差异 %.1f%%（>2%%）：可能并非同一 UI 元素的不同版本' % (adiff * 100))
        for s in {(c['w'], c['h']) for c in cands}:
            if len({c['md5'] for c in cands if (c['w'], c['h']) == s}) > 1:
                doubt.append('同尺寸 %dx%d 下候选 md5 不同：同尺寸亦存在内容冲突' % s)
        cross = any(c['src'] == 'otv' for c in cands) and any(c['src'] in ('ot', 'ota', 'otp') for c in cands)
        if cross:
            doubt.append('PSV(otv) 与 Lucifen 命名体系跨源同 stem，内容是否同物需人判')
        if key.startswith('rule') and key in RULE_CORR:
            doubt.append('rule 同名同序号：Lucifen 800×600(4:3) vs PSV 960×544(16:9)；内容相关 r=%.3f（%s）'
                         % (RULE_CORR[key], '高' if RULE_CORR[key] >= .5 else '低，几何条纹/渐变在异纵横比下不可比'))
        if key.startswith('ss_bg') and cross:
            doubt.append('Lucifen=800×600 场景选择底板；PSV=960×1012 整页场景选择画面（含日期列表）——粒度不同')
        if key.startswith('ec') and cross:
            _m = {c['md5'] for c in cands if c['w'] == 800 and c['h'] == 600}
            doubt.append('章标题卡：Lucifen 侧 800×600、PSV 侧 1013×658；Lucifen 侧内部 md5 %s'
                         % ('一致' if len(_m) <= 1 else '不一致（%d 种）' % len(_m)))
        review.append({
            'uname': uname, 'cls': cls, 'cands': cand_str,
            'win': '%s:%s %dx%d' % (win['src'], os.path.basename(win['rel']), win['w'], win['h']),
            'why': '§3.2 分辨率优先 w×h=%d（次 w=%d）' % (win['w'] * win['h'], win['w']),
            'doubt': '；'.join(doubt) or '-', 'adiff': adiff,
        })

print('[i] 组数=%d 候选合计=%d 产物=%d' % (len(groups), total_cand, len(unified)))

# ---------------- 8. 输出清单 ----------------
with open(os.path.join(OUT, '清单_系统UI.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\t'.join(['统一名', '类别', '尺寸(w,h)', '模式', '字节', '选中源', '选中原名',
                       '组内候选数', '分类', '判读来源', '理由']) + '\n')
    for r in unified:
        f.write('\t'.join([r['uname'], r['cat'], '%dx%d' % (r['w'], r['h']), r['mode'], str(r['bytes']),
                           r['src'], r['orig'], str(r['ncand']), r['cls'], r['catsrc'], r['why']]) + '\n')

with open(os.path.join(OUT, '待复核_系统UI.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\t'.join(['统一名', '分类', '候选清单(源+原名+尺寸+md5前8)', '选中项', '选中理由', '疑点']) + '\n')
    for r in review:
        f.write('\t'.join([r['uname'], r['cls'], r['cands'], r['win'], r['why'], r['doubt']]) + '\n')

# 非图像条目
non_img = sorted(fs_non)
with open(os.path.join(OUT, '_非图像条目_系统UI.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('源\t子目录\t文件名\t扩展名\t字节\n')
    for s, k, n, b in non_img:
        f.write('%s\t%s\t%s\t%s\t%d\n' % (s, k, n, os.path.splitext(n)[1].lower(), b))

stats = {
    'groups': len(groups), 'products': len(unified), 'total_candidates': total_cand,
    'images': len(images), 'non_images': len(non_img), 'fs_total': len(fs_png) + len(non_img),
    'cat': dict(cat_cnt), 'catsrc': dict(collections.Counter(r['catsrc'] for r in unified)),
    'win_src': dict(src_cnt), 'cls': dict(collections.Counter(r['cls'] for r in unified)),
    'review': len(review), 'saved_bytes': saved_bytes,
    'dup_unames': len(unified) - len({r['uname'] for r in unified}),
    'only_fs': sorted(only_fs), 'only_idx': sorted(only_idx),
    'fs_png': len(fs_png), 'idx_png': len(idx_png),
    'rule_corr_n': len(RULE_CORR),
    'rule_corr_hi': sum(1 for v in RULE_CORR.values() if v >= 0.5),
    'rule_corr_lo': sum(1 for v in RULE_CORR.values() if v < 0.5),
}
with open(os.path.join(OUT, '_W11c_统计.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=1)

print(json.dumps(stats, ensure_ascii=False, indent=1))
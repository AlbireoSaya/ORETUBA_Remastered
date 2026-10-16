# -*- coding: utf-8 -*-
"""W11c 系统UI 自证脚本：7 项验收 + 相似度抽检。只读，不写产物。"""
import os, sys, json, random, hashlib, collections, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.dirname(HERE)
LIB  = os.path.join(RES, 'krkr素材库')
OUT  = os.path.join(RES, '美术统一')
IMG  = os.path.join(OUT, '系统UI')
SRC_PREFIX = {'ot': 'ot_', 'ota': 'ota_', 'otp': 'otp_', 'otv': 'otv_'}

def read_tsv(p):
    with open(p, encoding='utf-8') as f:
        h = f.readline().rstrip('\n').split('\t')
        return h, [ln.rstrip('\n').split('\t') for ln in f if ln.strip()]

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

ok = []
def chk(name, cond, detail=''):
    ok.append((name, bool(cond), detail))
    print(('[PASS] ' if cond else '[FAIL] ') + name + ('  ' + detail if detail else ''))

h_list, rows = read_tsv(os.path.join(OUT, '清单_系统UI.tsv'))
h_rev, rev   = read_tsv(os.path.join(OUT, '待复核_系统UI.tsv'))
h_non, non   = read_tsv(os.path.join(OUT, '_非图像条目_系统UI.tsv'))
stats = json.load(open(os.path.join(OUT, '_W11c_统计.json'), encoding='utf-8'))
print('清单 %d 行 / 待复核 %d 行 / 非图像 %d 行' % (len(rows), len(rev), len(non)))

# ---- 1 组数 == 产物数, 无重复统一名 ----
unames = [r[0] for r in rows]
chk('1 产物数==组数', len(rows) == stats['groups'], '%d vs %d' % (len(rows), stats['groups']))
chk('1 无重复统一名', len(set(unames)) == len(unames), 'unique=%d' % len(set(unames)))
disk = os.listdir(IMG)
chk('1 产物目录文件数==清单行数', len(disk) == len(rows), '%d vs %d' % (len(disk), len(rows)))
chk('1 清单名与磁盘一致', set(disk) == set(unames))

# ---- 2 覆盖率守恒 ----
tot = sum(int(r[7]) for r in rows)
chk('2 Σ组内候选数==图像数', tot == stats['images'], '%d vs %d' % (tot, stats['images']))
grand = stats['images'] + stats['non_images']
chk('2 图像+非图像==磁盘总文件', grand == stats['fs_total'], '%d+%d=%d vs %d' % (
    stats['images'], stats['non_images'], grand, stats['fs_total']))
print('    (任务书给 2372；实测磁盘 2391，差 19)')

# ---- 4 选优正确：逐组复核选中为 w*h 最大 ----
h_idx, idx = read_tsv(os.path.join(RES, '美术', '系统UI尺寸索引.tsv'))
best = {}
for c in idx:
    p = c[5].replace('/', os.sep)
    name = os.path.basename(p)
    key = name[len(SRC_PREFIX[c[0]]):].lower()
    v = int(c[2]) * int(c[3])
    if key not in best or v > best[key][0] or (v == best[key][0] and int(c[2]) > best[key][1]):
        best[key] = (v, int(c[2]), c[0])
bad = []
for r in rows:
    b = best[r[0]]
    if (int(r[2].split('x')[0]) * int(r[2].split('x')[1]), int(r[2].split('x')[0])) != (b[0], b[1]):
        bad.append((r[0], r[2], b))
chk('4 逐组选中为 w*h 最大', not bad, '反例 %d 个 %s' % (len(bad), bad[:5]))

# ---- 6 原字节保真：随机 20 个 cmp ----
random.seed(20260919)
sample = random.sample(rows, 20)
mismatch = []
for r in sample:
    cands = []
    for c in idx:
        name = os.path.basename(c[5].replace('/', os.sep))
        if name[len(SRC_PREFIX[c[0]]):].lower() == r[0]:
            cands.append(os.path.join(LIB, c[5].replace('/', os.sep)))
    out = os.path.join(IMG, r[0])
    if not any(md5(p) == md5(out) for p in cands):
        mismatch.append(r[0])
chk('6 抽 20 产物与源逐字节相同', not mismatch, '不一致 %s' % mismatch)

# ---- 7 待复核收录完整 ----
need = {'same_res_diff', 'diff_res_diff_drawing'}
cls_rev = {r[1] for r in rev}
chk('7 待复核含全部 same_res_diff/diff_res_diff_drawing', need <= cls_rev, str(cls_rev))
chk('7 待复核行数==分类计数', len(rev) == stats['cls'].get('same_res_diff', 0) + stats['cls'].get('diff_res_diff_drawing', 0))

# ---- 3 六个 Lucifen 三源异尺寸组 ----
LUC6 = ['tl_cfg.png', 'tl_exit.png', 'tl_galry.png', 'tl_load.png', 'ec2_bg.png', 'ec3_bg.png']
print('\n=== 3 · Lucifen 三源异尺寸组 ===')
for k in LUC6:
    r = [x for x in rows if x[0] == k][0]
    rr = [x for x in rev if x[0] == k]
    print('%-14s 选中=%s %s 分类=%s 复核=%s' % (k, r[5], r[2], r[8], '是' if rr else '否'))
    if rr:
        print('     候选: %s' % rr[0][2])

# ---- 相似度抽检 (规格 §3.3 可选) ----
try:
    from PIL import Image
    def sig(p, n=96):
        im = Image.open(p).convert('L').resize((n, n), Image.BILINEAR)
        d = list(im.getdata())
        m = sum(d) / len(d)
        v = sum((x - m) ** 2 for x in d) ** .5 or 1
        return [(x - m) / v for x in d]
    def corr(a, b):
        return sum(x * y for x, y in zip(a, b))
    print('\n=== 相似度抽检（缩放到 96×96 灰度后 Pearson 相关；仅启发式） ===')
    for k in LUC6 + ['rule000.png', 'rule055.png', 'rule110.png', 'ec_bg01.png', 'meswin.png']:
        cands = []
        for c in idx:
            name = os.path.basename(c[5].replace('/', os.sep))
            if name[len(SRC_PREFIX[c[0]]):].lower() == k:
                cands.append((c[0], os.path.join(LIB, c[5].replace('/', os.sep))))
        if len(cands) < 2:
            print('%-14s 单候选，跳过' % k)
            continue
        base = sig(cands[0][1])
        out = []
        for s, p in cands[1:]:
            out.append('%s=%.3f' % (s, corr(base, sig(p))))
        print('%-14s 以 %s 为基准: %s' % (k, cands[0][0], '  '.join(out)))
except ImportError:
    print('[!] 无 PIL，跳过相似度抽检')

print('\n==== 汇总 %d/%d PASS ====' % (sum(1 for _, c, _ in ok if c), len(ok)))
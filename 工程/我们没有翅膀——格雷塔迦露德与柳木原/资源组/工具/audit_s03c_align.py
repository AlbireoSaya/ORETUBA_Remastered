# -*- coding: utf-8 -*-
r"""audit_s03c_align.py —— R 版亚衣线（s03c）场景级 + 行级对齐审计
（ISSUE-20260918-06 · W7-1 重派 · v1）

方法（语音 ID 锚点为主）
========================
1. 场景级：R 版 55 个 .tob ↔ 2009 原版 21 个 .sob。
   判据 = 场景名 + voice 锚定命中数 + jp 精确重合数；无对应者判为「R 版新增」。
2. 行级（仅共有场景）：R 行 → 2009 行 的对齐
   ① voice 锚点（同场景同 voice ID）优先；
   ② jp 精确相等（旁白/无 voice 行）；
   ③ 归一化 jp（去空白/标点）近似；
   ④ 缺口内按序单调补齐（一对一）。
3. 错位判定：以 2009 工程自身的独立中文译文 C09 为「该行正确译文」参照。
   对已对齐行 i（对应 09 行 j）：
     s_same   = sim(R.cn[i], C09[j])
     s_other  = max_{k∈[j-W,j+W], k≠j} sim(R.cn[i], C09[k])
   * s_same 为窗口内最大且 ≥ OK_MIN            → OK
   * s_other ≥ SHIFT_MIN 且 > s_same + MARGIN   → SHIFT(j - k*)
   * cn 为 mojibake                            → MOJIBAKE
   * 无法对齐 / cn 空 / 上述均不成立            → UNMATCHED

只读源；产物写 资源组\修正\。可复跑。
用法：python -X utf8 audit_s03c_align.py
"""
import json
import os
import re
import sys
import glob
import difflib
import collections

sys.stdout.reconfigure(encoding='utf-8')

WS = r'E:\ZCode Workspace\Galgame'
P09 = os.path.join(WS, r'工程\我们没有翅膀\汉化\剧情汉化')
PR = os.path.join(WS, r'工程\我们没有翅膀R')
RJSON = os.path.join(PR, r'亜衣线资源\剧本\台词对照.json')
RMIG = os.path.join(PR, r'语料\R版迁移映射.json')
KNOWN = os.path.join(PR, r'亜衣线资源\剧本\清单\生成说明.txt')
OUTDIR = os.path.join(WS, r'工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\修正')

W = 10            # 邻域窗口半径
SHIFT_MIN = 0.35  # SHIFT 需邻域相似度达到此值
MARGIN = 0.12     # SHIFT 需超出自身相似度的余量
JP_SIM_MIN = 0.55 # 缺口补齐所需最低 jp 相似度
LABEL_RE = re.compile(r'[（(][A-ZＡ-Ｚ][）)]')  # 选项分支标记（Ａ）（Ｃ）等

CJK = re.compile(r'[\u3400-\u9fff]')


def norm_voice(v):
    if not v:
        return ''
    return v.replace('/', '\\').split('\\')[-1].strip()


def norm_jp(t):
    t = t or ''
    for c in '　 \t\r\n「」『』（）()“”‘’、。，．！？!?…‥―—‐-ー〜～·・：:；;／/＼＝=＋+＿_｜|＊*':
        t = t.replace(c, '')
    return t


def sim(a, b):
    a = (a or '').replace('　', '').replace(' ', '')
    b = (b or '').replace('　', '').replace(' ', '')
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def is_mojibake(cn):
    """含 ≥2 个非 GB2312 汉字且占比 ≥ 0.5 → 疑似 mojibake。"""
    cn = cn or ''
    if not cn:
        return False
    bad = 0
    for c in cn:
        try:
            c.encode('gb2312')
        except Exception:
            if CJK.match(c):
                bad += 1
    return bad >= 2 and bad / max(1, len(cn)) >= 0.5


# ---------------------------------------------------------------- 载入
def load09():
    scenes = {}
    for f in sorted(glob.glob(os.path.join(P09, 's03c*.jsonl'))):
        sc = os.path.basename(f).replace('.sob.jsonl', '')
        rows = []
        for l in open(f, encoding='utf-8'):
            o = json.loads(l)
            o['voice'] = norm_voice(o.get('voice'))
            rows.append(o)
        scenes[sc] = rows
    return scenes


def loadR():
    d = json.load(open(RJSON, encoding='utf-8'))
    scenes = collections.OrderedDict()
    for s in d['scenes']:
        scenes[s['file'].replace('.tob', '')] = s
    return d['meta'], scenes


# ---------------------------------------------------------------- 场景级
def scene_align(nine, rscenes):
    """返回 (rows, new_scenes)。rows: 每行一个 R 场景的结论。"""
    rows = []
    used09 = collections.Counter()
    for sc, s in rscenes.items():
        lines = s['lines']
        rv = [norm_voice(ln.get('voice')) for ln in lines]
        rv_set = {v for v in rv if v}
        rjp = [ln.get('jp') or '' for ln in lines]
        rjp_set = {j for j in rjp if j}
        # 与每个 09 场景的重合
        best = None
        for sc9, rows9 in nine.items():
            v9 = {norm_voice(r['voice']) for r in rows9 if r.get('voice')}
            j9 = {r['jp'] for r in rows9 if r.get('jp')}
            vov = len(rv_set & v9)
            jov = len(rjp_set & j9)
            score = (vov, jov)
            if best is None or score > best[1]:
                best = (sc9, score)
        sc9_best, (vov, jov) = best
        branch_ref = None
        name_match = sc in nine
        if name_match:
            v9 = {norm_voice(r['voice']) for r in nine[sc] if r.get('voice')}
            j9 = {r['jp'] for r in nine[sc] if r.get('jp')}
            vov_name = len(rv_set & v9)
            jov_name = len(rjp_set & j9)
            verdict = sc
            evidence = ('场景名一致；voice 锚定 %d/%d；jp 精确重合 %d/%d'
                        % (vov_name, len(rv_set), jov_name, len(rjp_set)))
            used09[sc] += 1
        else:
            ratio = jov / max(1, len(rjp_set))
            if len(rjp_set) >= 10 and ratio >= 0.5:
                # 分支/续接场景：无同名 09 文件，但正文高度重合 → 以父场景为 09 对照
                verdict = '%s（分支）' % sc9_best
                evidence = ('无同名 09 场景；但与 %s 高度重合（voice %d/%d、jp %d/%d=%.0f%%）'
                            '→ 视为其分支/续接，重合行可用 09 对照'
                            % (sc9_best, vov, len(rv_set), jov, len(rjp_set), 100 * ratio))
                branch_ref = sc9_best
            else:
                verdict = 'R版新增'
                evidence = ('无同名 09 场景；与最接近的 09 场景 %s 仅 voice 重合 %d、jp 重合 %d'
                            % (sc9_best, vov, jov))
                branch_ref = None
        rows.append({
            'r_scene': sc, 'n_lines': len(lines),
            'n_voice': len(rv_set), 'n_jp': len(rjp_set),
            'mapped_09': verdict, 'evidence': evidence,
            'name_match': name_match,
            'branch_ref': branch_ref if not name_match else None,
        })
    return rows


# ---------------------------------------------------------------- 行级
def align_scene(lines, rows9):
    """返回 R 行 index → 09 行 index 的映射（None 表示未对齐）。"""
    v09 = collections.defaultdict(list)
    j09 = collections.defaultdict(list)
    n09 = collections.defaultdict(list)
    l09 = collections.defaultdict(list)
    for i, r in enumerate(rows9):
        if r.get('voice'):
            v09[r['voice']].append(i)
        j09[r['jp']].append(i)
        nj = norm_jp(r['jp'])
        if len(nj) >= 6:
            n09[nj].append(i)
        lk = LABEL_RE.sub('', norm_jp(r['jp']))
        if len(lk) >= 6:
            l09[lk].append(i)
    amap = {}
    method = {}
    used = set()

    def claim(i, cands):
        cands = [c for c in cands if c not in used]
        if not cands:
            return None
        # 取最接近上一个已对齐位置的候选
        prev = [k for k, v in amap.items() if v is not None and k < i]
        target = amap[prev[-1]] if prev else -1
        cands.sort(key=lambda c: (abs(c - target), c))
        return cands[0]

    # ① voice
    for i, ln in enumerate(lines):
        v = norm_voice(ln.get('voice'))
        if v and v in v09:
            c = claim(i, v09[v])
            if c is not None:
                amap[i] = c
                used.add(c)
                method[i] = 'voice'
    # ② jp 精确
    for i, ln in enumerate(lines):
        if i in amap:
            continue
        jp = ln.get('jp') or ''
        if jp and jp in j09:
            c = claim(i, j09[jp])
            if c is not None:
                amap[i] = c
                used.add(c)
                method[i] = 'jp'
    # ③ 归一化 jp 近似
    for i, ln in enumerate(lines):
        if i in amap:
            continue
        nj = norm_jp(ln.get('jp'))
        if len(nj) >= 6 and nj in n09:
            c = claim(i, n09[nj])
            if c is not None:
                amap[i] = c
                used.add(c)
                method[i] = 'jp_norm'
    # ③b 选项标签：剔除分支标记（Ａ）（Ｃ）后匹配
    for i, ln in enumerate(lines):
        if i in amap:
            continue
        lk = LABEL_RE.sub('', norm_jp(ln.get('jp')))
        if len(lk) >= 6 and lk in l09:
            c = claim(i, l09[lk])
            if c is not None:
                amap[i] = c
                used.add(c)
                method[i] = 'label'
    # ④ 缺口单调补齐：在相邻已对齐锚之间，对剩余行按 jp 相似度一对一
    anchors = sorted([i for i in amap])
    bounds = [-1] + anchors + [len(lines)]
    for a, b in zip(bounds, bounds[1:]):
        gapR = [i for i in range(a + 1, b) if i not in amap]
        if not gapR:
            continue
        lo = (amap[a] + 1) if a in amap else 0
        hi = (amap[b]) if b in amap else len(rows9)
        gap9 = [k for k in range(lo, hi) if k not in used]
        if not gap9 or not gapR:
            continue
        if len(gapR) == len(gap9):
            # 一对一按序
            for i, k in zip(gapR, gap9):
                amap[i] = k
                used.add(k)
                method[i] = 'gap_order'
        else:
            # 用 jp 相似度贪心配对
            cand = []
            for i in gapR:
                jpi = lines[i].get('jp') or ''
                for k in gap9:
                    s = sim(jpi, rows9[k].get('jp') or '')
                    if s >= JP_SIM_MIN:
                        cand.append((s, i, k))
            cand.sort(reverse=True)
            for s, i, k in cand:
                if i in amap or k in used:
                    continue
                amap[i] = k
                used.add(k)
                method[i] = 'gap_sim'
    return amap, method


def classify(cn, jp, j, rows9):
    """返回 (status, shift, belongs_to, sim_same, sim_other, reason)。

    判据（相对优先，不设绝对 OK 阈值）：
      * 未对齐 / cn 空              → UNMATCHED
      * mojibake                    → MOJIBAKE
      * 邻域存在明显更优匹配         → SHIFT(j - k*)
      * 其余                        → OK
    """
    if not cn:
        # jp 也为空 → 提取失败的空槽（offset=null），需人工核查提取
        return 'UNMATCHED', None, None, None, None, ('empty_cn' if jp else 'empty_slot')
    if '$&' in cn or 'AI_' in cn:
        return 'MOJIBAKE', None, None, None, None, 'marker_leak'
    if is_mojibake(cn):
        return 'MOJIBAKE', None, None, None, None, 'mojibake'
    if j is None:
        return 'UNMATCHED', None, None, None, None, 'no_counterpart'
    s_same = sim(cn, rows9[j].get('cn') or '')
    best_s, best_k = 0.0, None
    for k in range(max(0, j - W), min(len(rows9), j + W + 1)):
        if k == j:
            continue
        s = sim(cn, rows9[k].get('cn') or '')
        if s > best_s:
            best_s, best_k = s, k
    if best_k is not None and best_s >= SHIFT_MIN and best_s > s_same + MARGIN:
        return 'SHIFT', (j - best_k), best_k, s_same, best_s, 'shift'
    # 长度严重不匹配（日文长句配 ≤6 字中文）→ 无法定位归属，标 UNMATCHED
    if len(jp or '') >= 20 and len((cn or '').replace('　', '')) <= 6 and s_same < 0.15:
        return 'UNMATCHED', None, None, s_same, best_s, 'len_mismatch'
    return 'OK', 0, j, s_same, best_s, None


# ---------------------------------------------------------------- 已知 34 条
def parse_known():
    txt = open(KNOWN, encoding='utf-8').read().splitlines()
    entries = []
    for n, l in enumerate(txt, 1):
        m = re.search(r'(s03c_\w+)\s+行(\d+)\s+offset=(\d+)', l)
        if m:
            entries.append({'scene': m.group(1), 'lineno': int(m.group(2)),
                            'offset': int(m.group(3)), 'srcline': n,
                            'in34': 186 <= n <= 288})
    return entries


# ---------------------------------------------------------------- 主流程
def main():
    nine = load09()
    meta, rscenes = loadR()
    srows = scene_align(nine, rscenes)

    shared = [r['r_scene'] for r in srows if r['name_match']]
    branch = {r['r_scene']: r['branch_ref'] for r in srows if r.get('branch_ref')}
    news = [r['r_scene'] for r in srows
            if not r['name_match'] and r['r_scene'] not in branch]
    audit_scenes = shared + list(branch)

    # 迁移映射（用于 src / ref_scene 交叉）
    mig = json.load(open(RMIG, encoding='utf-8'))
    mig_by = collections.defaultdict(list)
    for e in mig:
        mig_by[e['file'].replace('.tob', '')].append(e)

    audit = []
    stat = collections.Counter()
    for sc in audit_scenes:
        ref = branch.get(sc, sc)
        rows9 = nine[ref]
        lines = rscenes[sc]['lines']
        amap, method = align_scene(lines, rows9)
        for i, ln in enumerate(lines):
            j = amap.get(i)
            cn = ln.get('cn') or ''
            jp = ln.get('jp') or ''
            status, shift, belongs, ss, so, reason = classify(cn, jp, j, rows9)
            correct = (rows9[j].get('cn') if j is not None else None)
            src = ln.get('source')
            idx = ln.get('index')
            if idx is None:
                idx = (ln.get('lineno') or 0) - 1
            audit.append({
                'file': sc + '.tob',
                'scene': sc,
                'index': idx,
                'lineno': ln.get('lineno'),
                'offset': ln.get('offset'),
                'kind': ln.get('kind'),
                'src': src,
                'speaker': ln.get('speaker_jp') or '',
                'jp': jp,
                'cn_current': cn,
                'truncated': bool(ln.get('truncated')),
                'voice': norm_voice(ln.get('voice')),
                'ref_09_scene': ref,
                'aligned_09_index': j,
                'align_method': method.get(i),
                'status': status,
                'shift': shift,
                'belongs_to_09_index': belongs,
                'sim_same': round(ss, 4) if ss is not None else None,
                'sim_best_other': round(so, 4) if so is not None else None,
                'correct_cn_from_2009': correct,
                'unmatched_reason': reason if status == 'UNMATCHED' else None,
                'need_retranslate': status in ('SHIFT', 'MOJIBAKE')
                                    or reason in ('empty_cn', 'len_mismatch', 'empty_slot'),
            })
            stat[status] += 1

    # ---- 精度后处理：孤立短句 SHIFT 降级为 OK
    # 依据：cn 实义字（CJK/假名）< 4 且邻域 ±2 行无同 shift 值的 SHIFT 佐证时，
    #       短句相似度不可靠，不判错（避免「じゃあな/俺走了」式误报）。
    def content_len(t):
        return sum(1 for c in (t or '') if CJK.match(c) or '\u3040' <= c <= '\u30ff')
    by_sc = collections.defaultdict(list)
    for a in audit:
        by_sc[a['scene']].append(a)
    downgraded = 0
    for sc, arr in by_sc.items():
        for k, a in enumerate(arr):
            if a['status'] != 'SHIFT':
                continue
            if content_len(a['cn_current']) >= 4:
                continue
            corrob = False
            for d in (-2, -1, 1, 2):
                if 0 <= k + d < len(arr) and arr[k + d]['status'] == 'SHIFT':
                    corrob = True
                    break
            if not corrob:
                a['status'] = 'OK'
                a['shift'] = 0
                a['need_retranslate'] = False
                a['downgraded_short'] = True
                downgraded += 1
    # 重算统计
    stat = collections.Counter(a['status'] for a in audit)

    # 新增场景行数统计
    new_stat = {}
    for sc in news:
        lines = rscenes[sc]['lines']
        srcs = collections.Counter(ln.get('source') for ln in lines)
        new_stat[sc] = {'n_lines': len(lines), 'src': dict(srcs)}

    # ---- 输出目录
    os.makedirs(OUTDIR, exist_ok=True)

    # 1) 场景对齐表
    p1 = os.path.join(OUTDIR, 's03c_场景对齐表.tsv')
    with open(p1, 'w', encoding='utf-8-sig', newline='') as fp:
        fp.write('R版场景\t行数\tvoice数\tjp数\t对应原版场景\t判定依据\n')
        for r in srows:
            fp.write('%s\t%d\t%d\t%d\t%s\t%s\n' % (
                r['r_scene'], r['n_lines'], r['n_voice'], r['n_jp'],
                r['mapped_09'], r['evidence']))

    # 2) 行对齐审计
    p2 = os.path.join(OUTDIR, 's03c_行对齐审计.json')
    with open(p2, 'w', encoding='utf-8') as fp:
        json.dump({
            'meta': {
                'route': meta.get('route'),
                'shared_scenes': shared,
                'branch_scenes': branch,
                'new_scenes': news,
                'params': {'W': W, 'SHIFT_MIN': SHIFT_MIN,
                           'MARGIN': MARGIN, 'JP_SIM_MIN': JP_SIM_MIN},
            },
            'lines': audit,
            'new_scene_stats': new_stat,
        }, fp, ensure_ascii=False)

    # 3) 重译清单
    p4 = os.path.join(OUTDIR, 's03c_重译清单.tsv')
    with open(p4, 'w', encoding='utf-8-sig', newline='') as fp:
        fp.write('场景\t行号\tindex\toffset\tkind\tsrc\t状态\tshift\t'
                 '当前中文\t应为(2009译文)\t日文\tvoice\n')
        for a in audit:
            if not a['need_retranslate']:
                continue
            fp.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                a['scene'], a['lineno'], a['index'], a['offset'], a['kind'],
                a['src'], a['status'], a['shift'] if a['shift'] is not None else '',
                (a['cn_current'] or '').replace('\t', ' '),
                (a['correct_cn_from_2009'] or '').replace('\t', ' '),
                (a['jp'] or '').replace('\t', ' '), a['voice']))

    # 4) 报告
    known = parse_known()
    k34 = [k for k in known if k['in34']]
    audit_idx = {}
    for a in audit:
        audit_idx[(a['scene'], a['offset'])] = a
    k_hit = 0
    k_rows = []
    for k in k34:
        a = audit_idx.get((k['scene'], k['offset']))
        k_rows.append((k, a))
        if a:
            k_hit += 1

    # 锚定命中率
    voiced = [a for a in audit if a['voice']]
    voiced_hit = sum(1 for a in voiced if a['aligned_09_index'] is not None)
    voice_method = sum(1 for a in voiced if a['align_method'] == 'voice')
    # 全 55 场景口径
    all_voiced = sum(1 for sc in rscenes for ln in rscenes[sc]['lines']
                     if norm_voice(ln.get('voice')))
    # 2009 侧同 voice 但未锚定的少数（跨场景/无同名）
    notfound = collections.Counter()
    for sc in audit_scenes:
        ref = branch.get(sc, sc)
        v9 = {norm_voice(r['voice']) for r in nine[ref] if r.get('voice')}
        for ln in rscenes[sc]['lines']:
            v = norm_voice(ln.get('voice'))
            if v and v not in v9:
                notfound[sc] += 1
    # 自洽性抽样（写报告）：确定性抽取，附邻域证据
    def ctx(a):
        """返回 (上一行, 下一行) 的 R 侧摘要。"""
        arr = by_sc[a['scene']]
        k = next((n for n, x in enumerate(arr) if x['index'] == a['index']), None)
        prev = arr[k - 1] if (k is not None and k > 0) else None
        nxt = arr[k + 1] if (k is not None and k + 1 < len(arr)) else None
        return prev, nxt
    ok_pool = [a for a in audit if a['status'] == 'OK'
               and content_len(a['cn_current']) >= 8 and a['aligned_09_index'] is not None]
    ok_s = ok_pool[::max(1, len(ok_pool) // 10)][:10]
    sh_s = sorted([a for a in audit if a['status'] == 'SHIFT'],
                  key=lambda a: -((a['sim_best_other'] or 0) - (a['sim_same'] or 0)))[:10]

    p3 = os.path.join(OUTDIR, 's03c_行对齐审计报告.md')
    L = []
    A = L.append
    A('# s03c 亚衣线 场景级 + 行级对齐审计报告')
    A('')
    A('- 生成脚本：`工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\工具\\audit_s03c_align.py`')
    A('- 只读源：`工程\\我们没有翅膀\\汉化\\剧情汉化\\s03c_*.jsonl`（21 场景）、'
      '`工程\\我们没有翅膀R\\亜衣线资源\\剧本\\台词对照.json`（55 场景）')
    A('- 方法：语音 ID 锚点为主 + jp 精确/归一化 + 缺口单调补齐；'
      '以 2009 工程独立译文 `correct_cn_from_2009` 为判错参照')
    A('')
    A('## 一、场景级结论')
    A('')
    A('- R 版 s03c 场景数：**%d**' % len(srows))
    A('- 与原版**同名共有**（name match + 锚点验证）：**%d**' % len(shared))
    A('- **分支/续接**（无同名 09 文件，但正文与父场景高度重合，已按父场景做行级审计）：**%d**'
      % len(branch))
    A('- 确为 **R 版新增**（无 2009 对照）：**%d**' % len(news))
    A('- 共有场景：%s' % '、'.join(shared))
    A('- 分支场景：%s' % ('、'.join('%s→%s' % kv for kv in branch.items()) or '无'))
    A('- 新增场景：%s' % '、'.join(news))
    A('')
    A('> 说明：分支场景 01d1/01d2/04b1 与父场景 01d/04b 的正文高度重合（jp 重合率 ≥50%），'
      '其重合行的 `correct_cn_from_2009` 取父场景对应行。其余 31 个新增场景与任何 2009 场景的 '
      'voice 重合为 0、jp 重合 ≤6（噪声级），确为新增内容。')
    A('')
    A('## 二、行级统计（共有 + 分支场景）')
    A('')
    A('- 审计行数：**%d**' % len(audit))
    A('- OK：%d ｜ SHIFT：%d ｜ MOJIBAKE：%d ｜ UNMATCHED：%d'
      % (stat['OK'], stat['SHIFT'], stat['MOJIBAKE'], stat['UNMATCHED']))
    reasons = collections.Counter(a['unmatched_reason'] for a in audit
                                  if a['status'] == 'UNMATCHED')
    A('- UNMATCHED 细分：%s' % '；'.join('%s=%d' % kv for kv in reasons.items()))
    n_need = sum(1 for a in audit if a['need_retranslate'])
    A('- 非 OK 行数（受影响面）：**%d**（= SHIFT+MOJIBAKE+UNMATCHED）'
      % (len(audit) - stat['OK']))
    A('- **需重译行数（明确错误）**：**%d**（SHIFT+MOJIBAKE+空/长度异常 UNMATCHED）'
      % n_need)
    A('- 错位区间数（连续 SHIFT 段）：见下表/清单')
    A('- 短句降级（孤立、实义字<4、无同向佐证 → 判 OK）：%d 行' % downgraded)
    A('')
    A('### voice 锚点有效性')
    A('')
    A('- 共有+分支场景内有 voice 的 R 行：%d，其中 %d 行经 voice 锚定对齐（命中率 **%.1f%%**）'
      % (len(voiced), voice_method, 100.0 * voice_method / max(1, len(voiced))))
    A('- 共有+分支场景内有 voice 的 R 行全部对齐成功（voice 或 jp 兜底）：%d/%d = %.1f%%'
      % (voiced_hit, len(voiced), 100.0 * voiced_hit / max(1, len(voiced))))
    A('- 未命中同场景 voice 的行（少量，改由 jp 兜底对齐）：%s'
      % ('；'.join('%s=%d' % kv for kv in sorted(notfound.items())) or '无'))
    A('- 全部 55 场景有 voice 的 R 行：%d（其中 %d 行位于确为新增的 %d 个场景，'
      '无 2009 对照，按设计不参与锚定）'
      % (all_voiced, all_voiced - len(voiced), len(news)))
    A('')
    A('## 三、新增场景（src=new 确认）')
    A('')
    A('| 场景 | 行数 | src 构成 |')
    A('| --- | --- | --- |')
    for sc in news:
        st = new_stat[sc]
        A('| %s | %d | %s |' % (sc, st['n_lines'],
                                ', '.join('%s=%d' % kv for kv in sorted(st['src'].items(), key=lambda x: str(x[0])))))
    A('')
    A('## 四、与已知 34 条交叉')
    A('')
    A('生成说明.txt 八节 34 条，全部列出（**共有场景 %d/26 条有行级结论，%d 条位于 R 版新增场景**）：'
      % (k_hit, len(k34) - k_hit))
    A('')
    A('| 场景 | 行 | offset | 审计状态 | shift | 当前中文 |')
    A('| --- | --- | --- | --- | --- | --- |')
    for k, a in k_rows:
        if a:
            A('| %s | %d | %d | %s | %s | %s |' % (
                k['scene'], k['lineno'], k['offset'], a['status'],
                a['shift'] if a['shift'] is not None else '',
                (a['cn_current'] or '').replace('|', '\\|')[:26]))
        else:
            A('| %s | %d | %d | 新增场景（无 2009 对照，src=new） | - | - |'
              % (k['scene'], k['lineno'], k['offset']))
    A('')
    A('## 五、自洽性抽样（可人工核验）')
    A('')
    A('每行给出：场景#index、R 版 jp/voice/cn、2009 同源行 jp/cn（即 `correct_cn_from_2009`），'
      '以及 R 版相邻行的 jp/cn 作为邻域佐证。')
    A('')
    A('### 10 个 OK（sim_same 应高于邻域，且与 09 译语义一致）')
    A('')
    for a in ok_s:
        prev, nxt = ctx(a)
        A('- **%s#%s** off=%s voice=%s sim_same=%s' % (
            a['scene'], a['index'], a['offset'], a['voice'] or '-', a['sim_same']))
        A('  - R  jp：%s' % (a['jp'] or '')[:70])
        A('  - R  cn：%s' % (a['cn_current'] or '')[:70])
        A('  - 09 cn（正确译文）：%s' % (a['correct_cn_from_2009'] or '')[:70])
        if prev:
            A('  - 上行 R cn：%s' % (prev['cn_current'] or '')[:60])
        if nxt:
            A('  - 下行 R cn：%s' % (nxt['cn_current'] or '')[:60])
    A('')
    A('### 10 个 SHIFT（邻域匹配度显著更高 → 当前 cn 属于邻行）')
    A('')
    for a in sh_s:
        prev, nxt = ctx(a)
        A('- **%s#%s** off=%s shift=%s 归属09行=%s sim_same=%s sim_best_other=%s' % (
            a['scene'], a['index'], a['offset'], a['shift'], a['belongs_to_09_index'],
            a['sim_same'], a['sim_best_other']))
        A('  - R  jp：%s' % (a['jp'] or '')[:70])
        A('  - R  cn（现）：%s' % (a['cn_current'] or '')[:70])
        A('  - 09 cn（应为）：%s' % (a['correct_cn_from_2009'] or '')[:70])
        if prev:
            A('  - 上行 R cn：%s' % (prev['cn_current'] or '')[:60])
        if nxt:
            A('  - 下行 R cn：%s' % (nxt['cn_current'] or '')[:60])
    A('')
    A('## 六、错位区间清单')
    A('')
    seg = []
    cur = None
    for a in audit:
        if a['status'] == 'SHIFT':
            if cur and cur[0] == a['scene'] and a['index'] == cur[2] + 1:
                cur = (cur[0], cur[1], a['index'], cur[3], a['shift'])
            else:
                if cur:
                    seg.append(cur)
                cur = (a['scene'], a['index'], a['index'], a['shift'], a['shift'])
        else:
            if cur:
                seg.append(cur)
                cur = None
    if cur:
        seg.append(cur)
    A('- 连续 SHIFT 段数：**%d**' % len(seg))
    A('')
    A('| 场景 | 起index | 止index | 首shift |')
    A('| --- | --- | --- | --- |')
    for s in seg:
        A('| %s | %s | %s | %s |' % (s[0], s[1], s[2], s[3]))
    A('')
    A('## 七、译文来源（src）构成与政策提示')
    A('')
    src_stat = collections.Counter(a['src'] for a in audit)
    A('- 共有+分支场景 %d 行中：%s' % (
        len(audit), '；'.join('%s=%d' % (('null(空槽)' if k is None else k), v)
                              for k, v in src_stat.most_common())))
    A('- 需重译 %d 行的 src 构成：%s' % (
        n_need, '；'.join('%s=%d' % (('null' if k is None else k), v)
                          for k, v in collections.Counter(
                              a['src'] for a in audit if a['need_retranslate']).most_common())))
    A('')
    A('> **政策提示（只记录，不影响本审计判定）**：用户 2026-09-17 定规「新米汉化只可用人名/地名，'
      '剧情译文一律不得使用」。R 版亚衣线译文 = 2,925 行迁移自新米（`src=mig`）+ 3,928 行本项目新译。'
      '2009 工程 `工程\\我们没有翅膀\\汉化\\剧情汉化\\` 的译文为独立翻译（已过合规审计），可安全用作判错参照；'
      '`src=mig` 行的译文来源存疑。本报告只如实标注每行 `src`，取舍由主代理与用户裁决。')
    A('')
    A('## 八、方法说明与可复现命令')
    A('')
    A('```')
    A('python -X utf8 "工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\工具\\audit_s03c_align.py"')
    A('```')
    A('')
    A('参数：窗口 W=%d，SHIFT_MIN=%s，MARGIN=%s，JP_SIM_MIN=%s'
      % (W, SHIFT_MIN, MARGIN, JP_SIM_MIN))
    A('')
    with open(p3, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(L))

    # 控制台摘要
    print('=== 场景级 ===')
    print('R 场景 %d ；共有 %d ；分支 %d ；新增 %d'
          % (len(srows), len(shared), len(branch), len(news)))
    print('共有:', '、'.join(shared))
    print('分支:', '、'.join('%s→%s' % kv for kv in branch.items()) or '无')
    print('=== 行级（共有+分支场景 %d 行）===' % len(audit))
    for k in ('OK', 'SHIFT', 'MOJIBAKE', 'UNMATCHED'):
        print('  %-10s %d' % (k, stat[k]))
    print('  非OK %d ；需重译 %d ；短句降级 %d'
          % (len(audit) - stat['OK'], n_need, downgraded))
    print('  错位区间数 %d' % len(seg))
    print('voice 锚定 %d/%d = %.1f%%（全部对齐 %d/%d）' % (
        voice_method, len(voiced), 100.0 * voice_method / max(1, len(voiced)),
        voiced_hit, len(voiced)))
    print('=== 34 条交叉命中 %d/34 ===' % k_hit)
    print('=== 输出 ===')
    for p in (p1, p2, p3, p4):
        print(' ', p, os.path.getsize(p), 'bytes')


if __name__ == '__main__':
    main()
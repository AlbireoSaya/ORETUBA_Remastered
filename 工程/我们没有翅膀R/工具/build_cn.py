# -*- coding: utf-8 -*-
r"""全量汉化构建器（ISSUE-ORETUBAR-R）。

输入：
  * `语料\R版SCRIPT\*.tob`（R 版原始脚本，418 个）
  * `语料\R版迁移映射.json`（51,736 槽：offset/len + 参照汉化译文）
  * `语料\待翻译清单.json`（6,624 槽：未命中，暂留日文）
  * `语料\重编码映射.json`（可选：残留 SJIS 字段的 GBK 重编码表，见 工具\recode_sjis.py）
  * `ORETSUBA_R\ORETSUBA_R\SCRIPT.LPK`（原始归档）
输出：
  * 打好的 `SCRIPT.LPK`（含全部可迁移译文）
  * 部署到 `<目标副本>\ORETSUBA_R\`（默认 `_VERIFY\GBK\ORETSUBA_R`）

要点：
  * 译文一律以**字节**形式进入（GBK），不过任何编码转换；
  * 未迁移的槽**原样保留日文原始字节**；
  * 每个 .tob 走 `tob_rewrite.apply_edits_rebuild` 做**地址重定位**；
  * 最终用 `lpk_patch.patch` 只替换改动过的条目，其余条目字节原样保留。

命令行（全部可选，**不带参数时行为与本脚本旧版完全一致**）：
  --recode                额外应用 `语料\重编码映射.json`（残留 SJIS -> GBK，消乱码）
  --recode-map PATH       指定重编码映射文件（隐含 --recode）
  --exclude DIR[,DIR..]   部署时跳过这些目标子目录（如 `_VERIFY\GBK\ORETSUBA_R`）
  --out-lpk PATH          指定输出 LPK 路径
  --no-deploy             只产出 LPK，不部署到游戏副本
  --batches               额外应用 `翻译工作区\批次N_译文.json`（未迁移槽的译文；默认关闭）
示例：
  python -X utf8 工具\build_cn.py --recode --no-deploy --out-lpk <临时>\SCRIPT.LPK
"""
import os, sys, json, re, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_rewrite as TR
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SRC_SCRIPTS = os.path.join(PROJ, '语料', 'R版SCRIPT')
MIG = os.path.join(PROJ, '语料', 'R版迁移映射.json')
TODO = os.path.join(PROJ, '语料', '待翻译清单.json')
SRC_LPK = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R', 'SCRIPT.LPK')
OUT_DIR = os.path.join(WS, '_VERIFY', 'GBK')
OUT_LPK = os.path.join(OUT_DIR, 'out', 'SCRIPT.LPK')
GAME = os.path.join(OUT_DIR, 'ORETSUBA_R')          # 默认部署目标（--out-lpk/--no-deploy 可改）
RECODE_MAP = os.path.join(PROJ, '语料', '重编码映射.json')
BATCH_DIR = os.path.join(PROJ, '翻译工作区')


def parse_argv(argv):
    """全部开关可选；不带参数 -> 与旧版行为一致。"""
    opt = {'recode': False, 'recode_map': None, 'exclude': [], 'out_lpk': None,
           'no_deploy': False, 'batches': False, 'extra': False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--recode':
            opt['recode'] = True
        elif a == '--recode-map':
            opt['recode'] = True
            opt['recode_map'] = argv[i + 1]; i += 1
        elif a == '--exclude':
            opt['exclude'] += [x for x in argv[i + 1].split(',') if x]; i += 1
        elif a == '--out-lpk':
            opt['out_lpk'] = argv[i + 1]; i += 1
        elif a == '--no-deploy':
            opt['no_deploy'] = True
        elif a == '--batches':
            opt['batches'] = True
        elif a == '--extra':
            opt['extra'] = True
        else:
            print('[警告] 未知参数忽略: %s' % a)
        i += 1
    return opt


def load_batch_edits():
    """`翻译工作区\批次N_译文.json`（{file,index,offset,text}）-> 与迁移映射同形的编辑表。

    注意：标题（kind=title）的 index 字段为 **None**，不能用 (file,index) 做键，
    否则同文件多个标题会互相覆盖 —— 一律以 **(file, offset)** 对齐待翻译清单取 len。
    """
    todo = json.load(open(TODO, encoding='utf-8'))
    by_off = {(r['file'], int(r['offset'])): r for r in todo}
    by_idx = {(r['file'], r['index']): r for r in todo if r['index'] is not None}
    out = {}
    n_off = n_idx = n_miss = 0
    for i in (1, 2, 3):
        p = os.path.join(BATCH_DIR, '批次%d_译文.json' % i)
        if not os.path.exists(p):
            print('  [跳过] 批次%d 译文不存在: %s' % (i, p))
            continue
        for r in json.load(open(p, encoding='utf-8')):
            if not r.get('text'):
                continue
            ref = by_off.get((r['file'], int(r['offset'])))
            if ref is not None:
                n_off += 1
            else:
                ref = by_idx.get((r['file'], r['index']))
                n_idx += 1
            if ref is None:
                n_miss += 1
                continue
            out[(r['file'], int(r['offset']))] = {
                'file': r['file'], 'offset': int(ref['offset']),
                'len': int(ref['len']), 'text': r['text']}
    print('  批次译文: %d 条（按 offset 对齐 %d / 按 index 对齐 %d / 未匹配 %d）'
          % (len(out), n_off, n_idx, n_miss))
    return out


def load_edits():
    """返回 {file: [{'offset','len','text_bytes'}, ...]}"""
    mig = json.load(open(MIG, encoding='utf-8'))
    print('迁移映射: %d 条' % len(mig))
    by_file = {}
    bad = []
    for r in mig:
        cn = r.get('cn')
        if not cn:
            continue
        try:
            b = cn.encode('gbk')
        except UnicodeEncodeError:
            bad.append((r['file'], r['index'], cn[:30]))
            continue
        d = by_file.setdefault(r['file'], [])
        d.append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b})
    print('  可编码为 GBK: %d 条' % sum(len(v) for v in by_file.values()))
    if bad:
        print('  ⚠ GBK 不可编码 %d 条（跳过，保留日文）' % len(bad))
        for x in bad[:5]:
            print('     ', x)
    # 检查 offset/len 是否与磁盘实际字节一致
    mismatch = 0
    for f, edits in by_file.items():
        raw = open(os.path.join(SRC_SCRIPTS, f), 'rb').read()
        for e in edits:
            seg = raw[e['offset']:e['offset'] + e['len']]
            if seg[:1] not in (b'\x00',) and not seg.rstrip(b'\x00 '):
                mismatch += 1
    return by_file, bad, mismatch


def build_files(edits_by_file):
    """对每个 .tob 施加编辑，返回 {file: new_bytes}"""
    out = {}
    files = sorted(f for f in os.listdir(SRC_SCRIPTS) if f.lower().endswith('.tob'))
    stats = []
    for f in files:
        raw = open(os.path.join(SRC_SCRIPTS, f), 'rb').read()
        edits = edits_by_file.get(f)
        if not edits:
            out[f] = raw
            stats.append((f, 0, len(raw), len(raw)))
            continue
        try:
            new, census, moved = TR.apply_edits_rebuild(raw, edits, verify=False)
            out[f] = new
            stats.append((f, len(edits), len(raw), len(new)))
        except Exception as e:
            print('  [失败] %s: %s' % (f, e))
            out[f] = raw
            stats.append((f, -1, len(raw), len(raw)))
    return out, stats


def load_recode_edits(path):
    """`语料\重编码映射.json`（工具\recode_sjis.py 产出）-> 同形编辑表。"""
    rows = json.load(open(path, encoding='utf-8'))
    by = {}
    for r in rows:
        tb = r.get('text_bytes')
        if isinstance(tb, list):
            tb = bytes(tb)
        elif isinstance(tb, str):
            tb = tb.encode('latin-1')
        else:
            raise ValueError('text_bytes 类型不支持: %r' % type(tb))
        by.setdefault(r['file'], []).append(
            {'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': tb})
    print('重编码映射: %d 条 / %d 文件' % (len(rows), len(by)))
    return by


def merge_edits(mig_by_file, extra_by_file, label):
    """把 extra 编辑并入 mig；**要求同一文件的编辑区间互不重叠**（重叠即报错）。"""
    n_add = n_ovl = 0
    out = {}
    for f in set(mig_by_file) | set(extra_by_file):
        a = list(mig_by_file.get(f, []))
        b = list(extra_by_file.get(f, []))
        if b:
            a.sort(key=lambda e: e['offset'])
            occ = [(e['offset'], e['offset'] + e['len']) for e in a]
            for e in b:
                x, y = e['offset'], e['offset'] + e['len']
                if any(not (y <= p or x >= q) for p, q in occ):
                    n_ovl += 1
                    continue
                a.append(e)
                occ.append((x, y))
                n_add += 1
        out[f] = a
    print('  %s: 并入 %d 条；因区间重叠拒绝 %d 条（重叠=异常，须检查）' % (label, n_add, n_ovl))
    return out, n_ovl


def main():
    opt = parse_argv(sys.argv[1:])
    out_lpk = opt['out_lpk'] or OUT_LPK
    game = GAME
    for ex in opt['exclude']:
        ex = os.path.abspath(ex)
        if os.path.abspath(game).lower().startswith(ex.lower()):
            game = None
    t0 = time.time()
    print('=== 1. 载入译文 ===')
    edits_by_file, bad, mismatch = load_edits()
    print('  涉及文件 %d 个；offset/len 可疑 %d 处' % (len(edits_by_file), mismatch))
    if opt['batches'] or opt['extra']:
        if opt['extra']:
            ep = os.path.join(os.path.dirname(MIG), '新增译文映射.json')
            arr = json.load(open(ep, encoding='utf-8'))
            bat = {(r['file'], r['offset']): r for r in arr}
            print('  新增译文映射: %d 条（%s）' % (len(bat), os.path.basename(ep)))
        else:
            bat = load_batch_edits()
        by = {}
        for r in bat.values():
            try:
                b = r['text'].encode('gbk')
            except UnicodeEncodeError:
                continue
            by.setdefault(r['file'], []).append(
                {'offset': r['offset'], 'len': r['len'], 'text_bytes': b})
        edits_by_file, ovl = merge_edits(edits_by_file, by, '批次译文')
        if ovl:
            print('  [警告] 批次译文与迁移映射区间重叠 %d 条（已跳过）' % ovl)
    if opt['recode']:
        rmap = opt['recode_map'] or RECODE_MAP
        if not os.path.exists(rmap):
            print('  [警告] 重编码映射不存在: %s（本次不应用重编码）' % rmap)
        else:
            rc = load_recode_edits(rmap)
            edits_by_file, ovl = merge_edits(edits_by_file, rc, '重编码映射')
            if ovl:
                print('  [警告] 重编码编辑与译文区间重叠 %d 条（已跳过，须人工检查）' % ovl)
    elif os.path.exists(RECODE_MAP):
        print('  提示：存在 `语料\\重编码映射.json`，本次**未**启用（加 --recode 可应用，'
              '用于消除残留 SJIS 乱码）')

    print()
    print('=== 2. 逐文件重建（含地址重定位）===')
    new_files, stats = build_files(edits_by_file)
    edited = [s for s in stats if s[1] > 0]
    failed = [s for s in stats if s[1] < 0]
    total_delta = sum(s[3] - s[2] for s in stats)
    print('  文件 %d 个；有改动 %d 个；失败 %d 个' % (len(stats), len(edited), len(failed)))
    print('  体积变化: %+d 字节' % total_delta)
    if failed:
        for s in failed[:5]:
            print('     失败:', s[0])

    print()
    print('=== 3. 打进 SCRIPT.LPK ===')
    os.makedirs(os.path.dirname(out_lpk), exist_ok=True)
    # 只替换改动过的 .tob（其余条目字节原样保留，避免引擎拒绝重压流）
    edits = {f: new_files[f] for f in new_files
             if f in edits_by_file and new_files[f] != open(os.path.join(SRC_SCRIPTS, f), 'rb').read()}
    print('  需替换条目: %d 个' % len(edits))
    info = LP.patch(SRC_LPK, out_lpk, edits)
    print('  LPK: %d -> %d 字节' % (info['in_size'], info['out_size']))

    print()
    print('=== 4. 抽查回读 ===')
    lp = LP.load(out_lpk)
    for probe in ['s01_01a.tob', 's01_02a.tob', 's00_00.tob']:
        e = LP.read_entry(lp, probe)
        head = e['plain'][:0]
        # 找第一段 GBK 中文
        m = re.search(rb'(?:[\x81-\xfe][\x40-\xfe]){4,}', e['plain'][:4000])
        sample = ''
        if m:
            try:
                sample = m.group(0).decode('gbk')
            except Exception:
                sample = '(解码失败)'
        print('  %-14s 明文 %d 字节  首段中文: %s' % (probe, len(e['plain']), sample[:40]))

    print()
    print('=== 5. 部署到实机副本 ===')
    if opt['no_deploy'] or game is None:
        print('  已跳过（--no-deploy 或目标在 --exclude 内）')
    elif os.path.isdir(game):
        shutil.copy2(out_lpk, os.path.join(game, 'SCRIPT.LPK'))
        print('  已替换 %s' % os.path.join(game, 'SCRIPT.LPK'))
    else:
        print('  [警告] 副本不存在: %s' % game)
    print()
    print('用时 %.1f 秒' % (time.time() - t0))


if __name__ == '__main__':
    main()

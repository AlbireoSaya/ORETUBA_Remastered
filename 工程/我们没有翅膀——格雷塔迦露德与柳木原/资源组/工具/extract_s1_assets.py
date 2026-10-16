# -*- coding: utf-8 -*-
r"""W1 · 解包《我们没有翅膀》本篇（S1）7 个素材归档 → krkr 素材库 ot/

源（**只读，严禁写入**）：D:\Gal\[Navel]我们没有翅膀\ 下的
    SYS.LPK CHR.LPK PIC.LPK BGM.LPK SE.LPK VOICE.LPK DATA.LPK
出：工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\krkr素材库\ot\
    ├─ chr\   CHR.LPK 全部条目（.elg → .png）
    ├─ pic\   PIC.LPK 全部条目（.elg → .png）
    ├─ sys\   SYS.LPK 全部条目（.elg → .png；.gmp/.lag 等非图像按原字节落盘）
    ├─ bgm\   BGM.LPK 全部条目（.ogg 原字节）
    ├─ se\    SE.LPK 全部条目（.ogg 原字节）
    ├─ voice\ VOICE.LPK 全部条目（.ogg 原字节）
    ├─ movie\ DATA.LPK 全部条目（.mpg 等原字节）
    ├─ _清单.json    每条 = {archive, orig_name, out_relpath, src_bytes, out_bytes, kind}
    └─ _提取摘要.txt 逐归档 条目数/成功/失败/输出体积 + 失败条目 + 总耗时

命名（强制）：ot_<原条目 basename 去扩展名，全小写> + 映射后扩展名
    .elg → .png ； .ogg → .ogg ； 其余保持原扩展名（小写）

工具：**只 import 不复制**
    资源组\工具\lpk_media.py        （参数化加载器，S1 键名 Ore-tachi ni Tsubasa wa Nai）
    工具\lucifen\Lucifen-Tools\elg2png.py  （ELG → PNG，保留 alpha）

用法：
    python -X utf8 extract_s1_assets.py [--only chr,se,...] [--out <目录>] [--no-png]

W5b（ISSUE-20260918-06）修复：SE.LPK 的 Key1 在社区 `LPK-Keys.json` 中有误，已由
`lpk_media.KEY_OVERRIDES` 覆盖（值取自 `gameinit.sob` 自述）。故本脚本重提 SE 即得
可播放文件。`--only se` 时**不覆盖** `_清单.json` 中其它档、也不覆盖 `_提取摘要.txt`
（改写为 `_提取摘要_se.txt`），避免局部重提把全量清单截断。
"""
import os, sys, json, time, collections

sys.stdout.reconfigure(encoding='utf-8')

WS = r'E:\ZCode Workspace\Galgame'
TOOLS = os.path.dirname(os.path.abspath(__file__))
MEDIA = r'D:\Gal\[Navel]我们没有翅膀'
DEFAULT_OUT = os.path.join(WS, '工程', '我们没有翅膀——格雷塔迦露德与柳木原',
                           '资源组', 'krkr素材库', 'ot')
ELG_TOOLS = os.path.join(WS, '工具', 'lucifen', 'Lucifen-Tools')
# 游戏自述密钥所在（只读引用，用于交叉校验；S1 本篇）
GAMEINIT_SOB = os.path.join(WS, '工程', '我们没有翅膀', '解包', 'SCRIPT', 'gameinit.sob')
for p in (TOOLS, os.path.join(WS, '工具', 'pylibs'), ELG_TOOLS):
    sys.path.insert(0, p)

import lpk_media as M              # noqa: E402
from elg2png import Reader as ElgReader   # noqa: E402

GAME = 'Ore-tachi ni Tsubasa wa Nai'      # LPK-Keys.json 中 S1 本篇的键名

# (归档文件, kind, 输出子目录, 是否对 .elg 转 PNG)
ARCHIVES = [
    ('SYS.LPK',   'sys',   'sys'),
    ('CHR.LPK',   'chr',   'chr'),
    ('PIC.LPK',   'pic',   'pic'),
    ('BGM.LPK',   'bgm',   'bgm'),
    ('SE.LPK',    'se',    'se'),
    ('VOICE.LPK', 'voice', 'voice'),
    ('DATA.LPK',  'movie', 'movie'),
]
EXPECT = {'SYS.LPK': 1113, 'CHR.LPK': 989, 'PIC.LPK': 763, 'BGM.LPK': 112,
          'SE.LPK': 582, 'VOICE.LPK': 21036, 'DATA.LPK': 2}

EXT_MAP = {'.elg': '.png', '.ogg': '.ogg'}


def log(*a):
    print(*a, flush=True)


def out_name(orig: str) -> str:
    """ot_<basename 全小写> + 映射扩展名。"""
    base, ext = os.path.splitext(os.path.basename(orig))
    ext = EXT_MAP.get(ext.lower(), ext.lower())
    return 'ot_' + base.lower() + ext


def dir_stat(path):
    tot = n = 0
    for root, _, files in os.walk(path):
        for f in files:
            tot += os.path.getsize(os.path.join(root, f))
            n += 1
    return n, tot


def main():
    only = None
    if '--only' in sys.argv:
        only = set(x.strip().lower() for x in sys.argv[sys.argv.index('--only') + 1].split(','))
    no_png = '--no-png' in sys.argv
    out_root = DEFAULT_OUT
    if '--out' in sys.argv:
        out_root = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])

    log('源（只读）：%s' % MEDIA)
    log('出        ：%s' % out_root)
    log('密钥        ：%s' % GAME)

    # --- 密钥交叉校验：游戏自述(gameinit.sob) vs 社区表(LPK-Keys.json) ---
    if os.path.exists(GAMEINIT_SOB):
        try:
            cc = M.cross_check_keys(GAMEINIT_SOB, GAME)
            log('密钥校验    ：%s 法基址 %s，%d 条，不一致 %d 条'
                % (cc['method'], cc['base_offset'], cc['count'], len(cc['mismatches'])))
            for m in cc['mismatches']:
                log('   ! %s 自述 Key1=0x%08X，社区 0x%08X（已用 KEY_OVERRIDES 覆盖）'
                    % (m['archive'], m['gameinit']['Key1'], m['community']['Key1']))
        except Exception as e:
            log('密钥校验    ：失败 %r（不影响提取）' % (e,))
    t0 = time.time()

    records = []
    per_archive = []          # (归档, 条目数, 成功, 失败, 输出体积)
    failures = []

    for fname, kind, sub in ARCHIVES:
        if only and kind not in only:
            continue
        dst_dir = os.path.join(out_root, sub)
        os.makedirs(dst_dir, exist_ok=True)
        src_path = os.path.join(MEDIA, fname)
        lp = M.load(src_path, game=GAME)
        names = M.names(lp)
        cnt = len(names)
        ok = fail = 0
        t_a = time.time()
        for i, name in enumerate(names, 1):
            rec = dict(archive=fname, orig_name=name, kind=kind)
            try:
                data = M.read(lp, name)
                rec['src_bytes'] = len(data)
                on = out_name(name)
                dst = os.path.join(dst_dir, on)
                ext = os.path.splitext(on)[1].lower()
                if ext == '.png' and not no_png:
                    ElgReader(data).decode().save(dst)
                else:
                    with open(dst, 'wb') as f:
                        f.write(data)
                rec['out_relpath'] = '%s/%s' % (sub, on)
                rec['out_bytes'] = os.path.getsize(dst)
                records.append(rec)
                ok += 1
            except Exception as e:                       # 记录失败，不中断
                fail += 1
                rec['error'] = repr(e)
                failures.append('%s\\%s : %s' % (fname, name, e))
            if i % 500 == 0 or i == cnt:
                log('   %-10s %6d/%d  成功 %d 失败 %d  %.1fs'
                    % (fname, i, cnt, ok, fail, time.time() - t_a))
        n, sz = dir_stat(dst_dir)
        per_archive.append((fname, cnt, ok, fail, sz))
        exp = EXPECT.get(fname)
        flag = '' if exp is None or exp == cnt else '  ⚠ 期望 %d' % exp
        log('   → %-10s 条目 %d 成功 %d 失败 %d 输出 %.1f MB%s'
            % (fname, cnt, ok, fail, sz / 1048576, flag))

    # ---------- 清单 ----------
    # 全量重提：直接写出。局部重提(--only)：与既有清单**合并**，只替换本次涉及的归档，
    # 绝不截断其它档（W5b 修复：避免 `--only se` 把 24597 条的清单写成 582 条）。
    os.makedirs(out_root, exist_ok=True)
    manifest = os.path.join(out_root, '_清单.json')
    done_archives = {a[0] for a in per_archive}
    if only and os.path.exists(manifest):
        with open(manifest, encoding='utf-8') as f:
            old = json.load(f)
        # 保序合并：未涉及归档的条目**原位保留**（不改顺序），只替换本次涉及的归档；
        # 旧清单中不存在的（新归档/新条目）追加到末尾。避免重排其它档（W5b 修复）。
        new_by = collections.defaultdict(dict)
        for r in records:
            new_by[r['archive']][r['out_relpath']] = r
        merged = []
        for r in old:
            a = r.get('archive')
            if a in done_archives:
                nr = new_by[a].pop(r['out_relpath'], None)
                if nr is not None:
                    merged.append(nr)
            else:
                merged.append(r)
        for a, d in new_by.items():
            for rel, nr in d.items():
                merged.append(nr)
        log('清单合并：旧 %d 条 → 保留顺序 + 本次 %d 条 = %d 条'
            % (len(old), len(records), len(merged)))
        records = merged
    with open(manifest, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    # ---------- 摘要 ----------
    total_n = sum(r[1] for r in per_archive)
    total_ok = sum(r[2] for r in per_archive)
    total_fail = sum(r[3] for r in per_archive)
    total_sz = sum(r[4] for r in per_archive)
    lines = ['S1《我们没有翅膀》本篇 素材提取摘要',
             '提取时间：%s' % time.strftime('%Y-%m-%d %H:%M:%S'),
             '源（只读）：%s' % MEDIA,
             '输出：%s' % out_root,
             '键名：%s' % GAME, '',
             '%-10s %8s %8s %8s %12s' % ('归档', '条目数', '成功', '失败', '输出(MB)')]
    for fname, cnt, ok, fail, sz in per_archive:
        lines.append('%-10s %8d %8d %8d %12.2f' % (fname, cnt, ok, fail, sz / 1048576))
    lines.append('%-10s %8d %8d %8d %12.2f'
                 % ('合计', total_n, total_ok, total_fail, total_sz / 1048576))
    lines.append('')
    lines.append('清单条目数：%d（_清单.json）' % len(records))
    lines.append('失败条目：%d' % len(failures))
    for x in failures[:200]:
        lines.append('   ' + x)
    lines.append('')
    lines.append('总耗时 %.1f 秒' % (time.time() - t0))
    txt = '\n'.join(lines)
    # 局部重提(--only)：不覆盖全量摘要，另写 `_提取摘要_<tag>.txt`，全量摘要保持原样
    if only:
        tag = ','.join(sorted(only))
        sum_path = os.path.join(out_root, '_提取摘要_%s.txt' % tag)
    else:
        sum_path = os.path.join(out_root, '_提取摘要.txt')
    with open(sum_path, 'w', encoding='utf-8') as f:
        f.write(txt)
    log('')
    log(txt)
    log('摘要落盘：%s' % sum_path)


if __name__ == '__main__':
    main()
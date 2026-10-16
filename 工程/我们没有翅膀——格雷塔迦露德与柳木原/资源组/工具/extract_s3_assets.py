# -*- coding: utf-8 -*-
r"""W2 · 提取 S3《我们没有翅膀 After Story》7 个素材归档 → krkr 素材库 ota\

源（**只读**，严禁写入）：`D:\Gal\[Navel]我们没有翅膀 ~ AfterStory ~(GPT-4o translate)\`
    SYS.LPK(711) CHR.LPK(1264) PIC.LPK(519) BGM.LPK(120) SE.LPK(602)
    VOICE.LPK(11205) DATA.LPK(4)   —— 合计 14,425 条目

出：`工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\krkr素材库\ota\`
    chr\  pic\  sys\  bgm\  se\  voice\  movie\
    _清单.json      每条 {archive, orig_name, out_relpath, src_bytes, out_bytes, kind}
    _提取摘要.txt   逐归档条目数/成功/失败/输出体积 + 失败逐条 + 总耗时

命名规范（总纲 §七 I1）：`ota_<原条目 basename 去扩展名>` + 扩展名；`.elg`→`.png`，
其余保持原扩展名；文件名统一小写。例：`ai_01.elg` → `ota\chr\ota_ai_01.png`。

依赖（**import 不复制**）：
    资源组\工具\lpk_media.py                      —— 参数化 LPK 素材归档加载器
    工具\lucifen\Lucifen-Tools\elg2png.py          —— ELG→PIL.Image
    工具\pylibs\                                   —— Pillow

用法：
    python -X utf8 extract_s3_assets.py                 # 全量
    python -X utf8 extract_s3_assets.py --archive CHR   # 只跑一档
    python -X utf8 extract_s3_assets.py --limit 5       # 每档只取前 5 条（冒烟）
    python -X utf8 extract_s3_assets.py --no-png        # ELG 按原字节落盘（调试）
"""
import os, sys, json, time, collections

sys.stdout.reconfigure(encoding='utf-8')

WS = r'E:\ZCode Workspace\Galgame'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(WS, '工程', '我们没有翅膀——格雷塔迦露德与柳木原')
SRC = r'D:\Gal\[Navel]我们没有翅膀 ~ AfterStory ~(GPT-4o translate)'
OUT_ROOT = os.path.join(PROJ, '资源组', 'krkr素材库', 'ota')
GAME = 'Ore-tachi ni Tsubasa wa Nai AfterStory'

for p in (HERE, os.path.join(WS, '工具', 'pylibs'),
          os.path.join(WS, '工具', 'lucifen', 'Lucifen-Tools')):
    if p not in sys.path:
        sys.path.insert(0, p)

import lpk_media as M                      # noqa: E402
from elg2png import Reader as ElgReader    # noqa: E402

# 归档 → (输出子目录, 期望条目数)
ARCHIVES = [
    ('SYS',   'sys',   711),
    ('CHR',   'chr',   1264),
    ('PIC',   'pic',   519),
    ('BGM',   'bgm',   120),
    ('SE',    'se',    602),
    ('VOICE', 'voice', 11205),
    ('DATA',  'movie', 4),
]

# 扩展名 → 条目类别（决定输出扩展名与 kind 字段）
def classify(ext):
    if ext == '.elg':
        return 'image', '.png'
    if ext == '.ogg':
        return 'audio', '.ogg'
    if ext == '.mpg':
        return 'movie', '.mpg'
    return 'data', ext


def log(*a):
    print(*a, flush=True)


def main():
    argv = sys.argv[1:]
    only = None
    if '--archive' in argv:
        only = argv[argv.index('--archive') + 1].upper()
    limit = None
    if '--limit' in argv:
        limit = int(argv[argv.index('--limit') + 1])
    no_png = '--no-png' in argv

    log('源（只读）: %s' % SRC)
    log('出          : %s' % OUT_ROOT)
    log('作品键名    : %s' % GAME)
    t_all = time.time()

    records = []            # 清单条目
    failures = []           # 失败条目
    per_archive = []        # 逐归档统计

    for arch, sub, expect in ARCHIVES:
        if only and arch != only:
            continue
        src_path = os.path.join(SRC, arch + '.LPK')
        out_dir = os.path.join(OUT_ROOT, sub)
        os.makedirs(out_dir, exist_ok=True)

        t0 = time.time()
        lp = M.load(src_path, game=GAME)
        names = M.names(lp)
        n_ok = n_fail = 0
        out_bytes_sum = 0
        by_kind = collections.Counter()

        log('[%s] 条目 %d（期望 %d）→ %s' % (arch, len(names), expect, sub))
        for i, name in enumerate(names, 1):
            if limit and i > limit:
                break
            base = os.path.splitext(os.path.basename(name.replace('\\', '/')))[0].lower()
            ext = os.path.splitext(name)[1].lower()
            kind, out_ext = classify(ext)
            out_name = 'ota_' + base + out_ext
            out_rel = '%s/%s' % (sub, out_name)
            out_fp = os.path.join(out_dir, out_name)
            try:
                data = M.read(lp, name)
                if ext == '.elg' and not no_png:
                    img = ElgReader(data).decode()
                    img.save(out_fp)
                else:
                    with open(out_fp, 'wb') as f:
                        f.write(data)
                ob = os.path.getsize(out_fp)
                records.append(dict(archive=arch + '.LPK', orig_name=name,
                                    out_relpath=out_rel, src_bytes=len(data),
                                    out_bytes=ob, kind=kind))
                by_kind[kind] += 1
                out_bytes_sum += ob
                n_ok += 1
            except Exception as e:
                n_fail += 1
                failures.append(dict(archive=arch + '.LPK', orig_name=name,
                                     out_relpath=out_rel, error='%s: %s' % (type(e).__name__, e)))
                log('    !! 失败 %s :: %s' % (name, e))
            if i % 500 == 0:
                log('    … %d/%d（成功 %d / 失败 %d）' % (i, len(names), n_ok, n_fail))

        dt = time.time() - t0
        per_archive.append(dict(archive=arch + '.LPK', dir=sub, entries=len(names),
                                expected=expect, ok=n_ok, fail=n_fail,
                                out_bytes=out_bytes_sum, seconds=round(dt, 1),
                                kinds=dict(by_kind)))
        log('[%s] 完成：成功 %d / 失败 %d / 输出 %.1f MB / %.1fs'
            % (arch, n_ok, n_fail, out_bytes_sum / 1048576, dt))
        lp['mm'].close()
        lp['f'].close()

    # ---------- 清单 ----------
    man_fp = os.path.join(OUT_ROOT, '_清单.json')
    with open(man_fp, 'w', encoding='utf-8') as f:
        json.dump(dict(source=SRC, game=GAME, generated=time.strftime('%Y-%m-%d %H:%M:%S'),
                       root=OUT_ROOT, entries=records, failures=failures,
                       per_archive=per_archive), f, ensure_ascii=False, indent=1)

    # ---------- 摘要 ----------
    tot_entries = sum(p['entries'] for p in per_archive)
    tot_ok = sum(p['ok'] for p in per_archive)
    tot_fail = sum(p['fail'] for p in per_archive)
    tot_out = sum(p['out_bytes'] for p in per_archive)
    lines = ['S3《我们没有翅膀 After Story》素材提取摘要',
             '提取时间：%s' % time.strftime('%Y-%m-%d %H:%M:%S'),
             '源（只读）：%s' % SRC,
             '输出：%s' % OUT_ROOT,
             '工具：资源组\\工具\\lpk_media.py（game=%s）+ elg2png.py' % GAME, '',
             '%-10s %-6s %8s %8s %8s %8s %12s %9s' % (
                 '归档', '目录', '条目数', '期望', '成功', '失败', '输出体积(MB)', '耗时(s)')]
    for p in per_archive:
        lines.append('%-10s %-6s %8d %8d %8d %8d %12.1f %9.1f' % (
            p['archive'], p['dir'], p['entries'], p['expected'], p['ok'], p['fail'],
            p['out_bytes'] / 1048576, p['seconds']))
    lines.append('%-10s %-6s %8d %8d %8d %8d %12.1f %9.1f' % (
        '合计', '', tot_entries, 14425, tot_ok, tot_fail, tot_out / 1048576, time.time() - t_all))
    lines.append('')
    lines.append('条目数对齐：%s（输出 %d / 期望 %d）'
                 % ('一致' if tot_ok == 14425 else '不一致', tot_ok, 14425))
    lines.append('')
    lines.append('失败条目：%d' % len(failures))
    for x in failures:
        lines.append('   %s\\%s  -> %s  :: %s' % (x['archive'], x['orig_name'],
                                                  x['out_relpath'], x['error']))
    lines.append('')
    lines.append('总耗时 %.1f 秒' % (time.time() - t_all))
    txt = '\n'.join(lines)
    with open(os.path.join(OUT_ROOT, '_提取摘要.txt'), 'w', encoding='utf-8') as f:
        f.write(txt + '\n')
    print()
    print(txt)


if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-
r"""提取《我们没有翅膀R》香田亜衣线（s03c_*）全部资源。

源（只读）：`备份\我们没有翅膀R-安装介质\SET_UP\`（原版日文介质）
出：`工程\我们没有翅膀R\亜衣线资源\`
    ├─ 剧本\s03c_*.tob                 55 个原始脚本（字节原样）
    ├─ 图像\CHR\*.png  图像\PIC\*.png    脚本引用的立绘 / 事件 CG（ELG→PNG，保留透明通道）
    ├─ 语音\*.ogg                       脚本配音 ID 对应的语音
    ├─ 音效\*.ogg                       脚本引用的 SE
    ├─ BGM\*.ogg                        BGM.LPK 全量（线路脚本不按名引用 BGM，见说明文档）
    └─ 清单\素材清单.json + 提取摘要.txt

用法：
  python -X utf8 extract_ai_route_assets.py [--no-png] [--skip-bgm] [--limit N]
"""
import os, re, sys, json, time, collections

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
TOOLS = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP')
OUT = os.path.join(WS, '工程', '我们没有翅膀R', '亜衣线资源')
ELG_TOOLS = os.path.join(WS, '工具', 'lucifen', 'Lucifen-Tools')
for p in (TOOLS, os.path.join(WS, '工具', 'pylibs'), ELG_TOOLS):
    sys.path.insert(0, p)

ROUTE_RE = re.compile(r'^s03c_.*\.tob$', re.I)
ASSET_RE = re.compile(rb'([A-Z]{2,6})[\\/]([A-Za-z0-9_]{2,24})\.([A-Za-z0-9]{2,4})')
# 配音 ID 候选：允许 **1 个字母前缀**（如 X055014 / Y051001 —— 旧版限定 2~4 字母，漏了 46 条）。
# 真正的准入过滤在提取阶段以「VOICE.LPK 中确有 <id>.ogg」为准，避免把场景名等字符串误当配音。
VOICE_RE = re.compile(rb'\x01\x01[\x03-\x20]\x00([A-Za-z][_0-9A-Za-z]{2,12})\x00')

import lpk_patch as LP              # SCRIPT.LPK（自研，已验证）
import lpk_media as M               # 其余归档（借道社区工具 + 官方密钥表）
from elg2png import Reader as ElgReader   # ELG → PIL.Image（保留 alpha）


def log(*a):
    print(*a, flush=True)


def dir_stat(path):
    tot = n = 0
    for root, _, files in os.walk(path):
        for f in files:
            tot += os.path.getsize(os.path.join(root, f))
            n += 1
    return n, tot


def main():
    no_png = '--no-png' in sys.argv
    skip_bgm = '--skip-bgm' in sys.argv
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    media = MEDIA
    if '--media' in sys.argv:
        media = sys.argv[sys.argv.index('--media') + 1]
    out_root = OUT
    if '--out' in sys.argv:
        out_root = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    log('源: %s' % media)
    log('出: %s' % out_root)
    t0 = time.time()

    # ---------- 1) 剧本 + 引用扫描 ----------
    log('[1/6] 剧本与引用扫描 …')
    lps = LP.load(os.path.join(media, 'SCRIPT.LPK'))
    route = sorted(n for n, _ in lps['ents'] if ROUTE_RE.match(n))
    os.makedirs(os.path.join(out_root, '剧本'), exist_ok=True)
    refs = collections.defaultdict(set)
    voices = set()
    per_file = {}
    for n in route:
        data = LP.read_entry(lps, n)['plain']
        open(os.path.join(out_root, '剧本', n), 'wb').write(data)
        a, v = set(), set()
        for m in ASSET_RE.finditer(data):
            kind = m.group(1).decode().upper()
            name = '%s.%s' % (m.group(2).decode(), m.group(3).decode())
            refs[kind].add(name)
            a.add('%s\\%s' % (kind, name))
        for m in VOICE_RE.finditer(data):
            v.add(m.group(1).decode())
        voices |= v
        per_file[n] = dict(bytes=len(data), assets=sorted(a), voices=sorted(v))
    log('      脚本 %d 个；素材引用 %s；语音 ID %d 种'
        % (len(route), {k: len(v) for k, v in sorted(refs.items())}, len(voices)))

    inv = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'media': media,
           'route_files': route, 'assets': {}, 'voices': {}, 'bgm': {},
           'missing': [], 'per_file': per_file}

    # ---------- 2) 图像 ----------
    for kind, sub in (('CHR', 'CHR'), ('PIC', 'PIC')):
        want = sorted(refs.get(kind, ()))
        if not want:
            continue
        log('[2/6] %s：目标 %d 个' % (kind, len(want)))
        lp = M.load(os.path.join(media, '%s.LPK' % kind))
        dst = os.path.join(out_root, '图像', sub)
        os.makedirs(dst, exist_ok=True)
        ok = 0
        for i, name in enumerate(want, 1):
            if limit and i > limit:
                break
            if not M.has(lp, name):
                inv['missing'].append('%s.LPK\\%s' % (kind, name))
                continue
            data = M.read(lp, name)
            base = os.path.splitext(name)[0]
            try:
                if no_png:
                    open(os.path.join(dst, base + '.elg'), 'wb').write(data)
                    ext = 'elg'
                else:
                    ElgReader(data).decode().save(os.path.join(dst, base + '.png'))
                    ext = 'png'
                inv['assets']['%s\\%s' % (kind, name)] = dict(
                    archive='%s.LPK' % kind, source_bytes=len(data),
                    out='图像/%s/%s.%s' % (sub, base, ext),
                    out_bytes=os.path.getsize(os.path.join(dst, base + '.' + ext)))
                ok += 1
            except Exception as e:                      # 记录失败，不中断
                inv['missing'].append('%s.LPK\\%s (转换失败: %s)' % (kind, name, e))
            if i % 50 == 0:
                log('      … %d/%d（已成功 %d）' % (i, len(want), ok))
        log('      %s 完成：成功 %d / 目标 %d' % (kind, ok, len(want)))

    # ---------- 2b) 缺失背景的「分片形态」（如 BG06B.ELG → bg06b_0..7.elg）----------
    lp_pic = M.load(os.path.join(media, 'PIC.LPK'))
    frag_names = sorted(n for n in M.names(lp_pic)
                        if re.match(r'^(bg0[67]b)_\d+$', os.path.splitext(n)[0], re.I))
    if frag_names:
        dst = os.path.join(out_root, '图像', 'PIC')
        os.makedirs(dst, exist_ok=True)
        for name in frag_names:
            data = M.read(lp_pic, name)
            base = os.path.splitext(name)[0]
            try:
                if no_png:
                    open(os.path.join(dst, base + '.elg'), 'wb').write(data)
                    ext = 'elg'
                else:
                    ElgReader(data).decode().save(os.path.join(dst, base + '.png'))
                    ext = 'png'
                inv['assets']['PIC\\%s（分片）' % name] = dict(
                    archive='PIC.LPK', source_bytes=len(data), fragment=True,
                    out='图像/PIC/%s.%s' % (base, ext),
                    out_bytes=os.path.getsize(os.path.join(dst, base + '.' + ext)))
            except Exception as e:
                inv['missing'].append('PIC.LPK\\%s (分片转换失败: %s)' % (name, e))
        log('      背景分片补提 %d 个（bg06b_*/bg07b_*）' % len(frag_names))

    # ---------- 3) 语音 ----------
    log('[3/6] 语音 %d 种' % len(voices))
    lp = M.load(os.path.join(media, 'VOICE.LPK'))
    dst = os.path.join(out_root, '语音')
    os.makedirs(dst, exist_ok=True)
    # 准入过滤：只认 VOICE.LPK 中真实存在的 <id>.ogg；其余候选（场景名等）单独记账
    kept = sorted(v for v in voices if M.has(lp, '%s.ogg' % v.lower()))
    not_voice = sorted(v for v in voices if not M.has(lp, '%s.ogg' % v.lower()))
    inv['voice_candidates'] = len(voices)
    inv['voice_not_in_archive'] = not_voice
    voices = set(kept)
    log('[3/6] 语音：候选 %d → 归档中存在 %d（非配音候选 %d，已记入清单）'
        % (inv['voice_candidates'], len(voices), len(not_voice)))
    for vid in sorted(voices):
        cand = '%s.ogg' % vid.lower()
        if not M.has(lp, cand):          # 防御：上一行已过滤，正常不会命中
            inv['missing'].append('VOICE.LPK\\%s' % cand)
            continue
        data = M.read(lp, cand)
        open(os.path.join(dst, cand), 'wb').write(data)
        inv['voices'][vid] = dict(file=cand, size=len(data))
    log('      语音导出 %d / %d' % (len(inv['voices']), len(voices)))

    # ---------- 4) 音效 ----------
    want = sorted(refs.get('SE', ()))
    log('[4/6] 音效 %d 个' % len(want))
    lp = M.load(os.path.join(media, 'SE.LPK'))
    dst = os.path.join(out_root, '音效')
    os.makedirs(dst, exist_ok=True)
    n_se = 0
    for name in want:
        if not M.has(lp, name):
            inv['missing'].append('SE.LPK\\%s' % name)
            continue
        data = M.read(lp, name)
        open(os.path.join(dst, name.lower()), 'wb').write(data)
        inv['assets']['SE\\%s' % name] = dict(archive='SE.LPK', source_bytes=len(data),
                                              out='音效/%s' % name.lower(), out_bytes=len(data))
        n_se += 1
    log('      音效导出 %d / %d' % (n_se, len(want)))

    # ---------- 5) BGM ----------
    if not skip_bgm:
        log('[5/6] BGM.LPK 全量')
        lp = M.load(os.path.join(media, 'BGM.LPK'))
        dst = os.path.join(out_root, 'BGM')
        os.makedirs(dst, exist_ok=True)
        for e in sorted(lp['ents'].values(), key=lambda z: z['name']):
            data = M.read(lp, e['name'])
            open(os.path.join(dst, e['name'].lower()), 'wb').write(data)
            inv['bgm'][e['name'].lower()] = len(data)
        log('      BGM 导出 %d 首' % len(inv['bgm']))
    else:
        log('[5/6] 跳过 BGM')

    # ---------- 6) 清单 + 摘要 ----------
    log('[6/6] 清单与摘要')
    os.makedirs(os.path.join(out_root, '清单'), exist_ok=True)
    with open(os.path.join(out_root, '清单', '素材清单.json'), 'w', encoding='utf-8') as f:
        json.dump(inv, f, ensure_ascii=False, indent=1)
    rows = []
    for label in ('剧本', '图像', '语音', '音效', 'BGM'):
        p = os.path.join(out_root, label)
        if os.path.isdir(p):
            n, sz = dir_stat(p)
            rows.append((label, n, sz))
    tot_n = sum(r[1] for r in rows)
    tot_sz = sum(r[2] for r in rows)
    lines = ['提取时间：%s' % inv['generated'],
             '源：%s' % media,
             '输出：%s' % out_root, '',
             '%-8s %8s %12s' % ('类别', '文件数', '体积(MB)')]
    for label, n, sz in rows:
        lines.append('%-8s %8d %12.1f' % (label, n, sz / 1048576))
    lines.append('%-8s %8d %12.1f' % ('合计', tot_n, tot_sz / 1048576))
    lines.append('')
    lines.append('缺失/失败条目：%d' % len(inv['missing']))
    for x in inv['missing'][:40]:
        lines.append('   ' + x)
    lines.append('')
    lines.append('耗时 %.1f 秒' % (time.time() - t0))
    txt = '\n'.join(lines)
    open(os.path.join(out_root, '清单', '提取摘要.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()

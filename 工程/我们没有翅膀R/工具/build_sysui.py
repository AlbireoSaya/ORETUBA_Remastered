# -*- coding: utf-8 -*-
r"""系统界面文案（SOB0 显示串）等长回写器（ISSUE-20261007-06）。

背景：补丁把字体字符集改成 GB2312，而 SCRIPT.LPK 的系统 SOB
（title/title2/saveload/config*/gameinit/main/gallery/bgmmode/voiceinf）**未纳入汉化**、
仍是 SJIS 字节 ⇒ 在游戏里显示为**乱码汉字**（实测：标题菜单说明气泡）。
本器把这些串按**等长 GBK** 写回——与正文同一套方法，**零重定位**。

原理：
  1. 从**待改的 LPK**（已是汉化版）里按同一判据重新抽取日文串（偏移/长度与构建时一致）；
  2. 用译文表（`id → 中文`）逐条替换，**GBK 字节数必须等于原串字节数**——
     偏短补全角空格（差 1 字节补半角），偏长按 GBK 字符边界截断；
  3. 因长度完全一致 ⇒ 前后所有字节、长度字段、NUL 结尾都不动。

用法：
  python -X utf8 build_sysui.py --report        # 只出对照/自检表，不写 LPK
  python -X utf8 build_sysui.py --apply         # 写回（原地 patch 目标 LPK）
  python -X utf8 build_sysui.py --apply --lpk <路径> --trans <a.tsv> --trans <b.tsv>
"""
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP                                    # noqa: E402
from build_padded import fit, gbk_norm                     # noqa: E402  同一套等长/回退逻辑

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
DEFAULT_LPK = os.path.join(WS, '临时', 'oretsuba_r_patch', '_rebuild', 'SCRIPT.LPK')
WORK = os.path.join(WS, '子代理工作区', 'ISSUE-20261007-06')
# 第二版：主代理汇总表（= A/B 译文 + 一审打回项修复 + 补入漏抽串），
# 由 `工具ix_sysui_round2.py` 生成。工作单同步换成 `runs_v2.json`（含加宽后的两条 ｢｣ 串）。
TRANS = [os.path.join(PROJ, '工具', 'sysui', 'master.tsv')]
RUNS = os.path.join(PROJ, '工具', 'sysui', 'runs_v2.json')
REPORT = os.path.join(WS, '临时', 'oretsuba_r_patch', '_sysui', '回写对照.tsv')

# 主代理裁决覆盖（在子代理译文之上生效；见工程记录「待入表 / 裁决」）
# 主代理裁决**已并入 master.tsv**（见 `fix_sysui_round2.py` 的 FIX 表）；此处保留机制备用。
OVERRIDE = {}

# 字体资源名等**保持原样**的 id（引擎据该名取字体，改动有失效风险）
KEEP_ASIS = {158, 164, 170}


def load_trans(paths):
    m = {}
    for p in paths:
        for ln in io.open(p, encoding='utf-8'):
            ln = ln.rstrip('\n').rstrip('\r')
            if not ln.strip():
                continue
            i, cn = ln.split('\t', 1)
            m[int(i)] = cn
    return m


def extract_runs(lp):
    """校验工作单里的 (file, off, n) 在待改 LPK 中**合法且互不重叠**，并顺带记录原串。

    为什么不做「按判据重新抽取再精确比对」：引擎把多条池串**连续堆放**（中间无反斜杠分隔），
    再加宽 `｢…｣` 后同一判据会与邻串合并成一个更大的段 —— 精确比对会误报。
    真正的正确性保证是**写后逐条字节比对**（见 main() 的 --apply 之后的手工核对脚本 /
    工程记录「验证方式与结果」），此处只做边界与重叠的静态校验。
    """
    rows = json.load(io.open(RUNS, encoding='utf-8'))
    files = {}
    for r in rows:
        files.setdefault(r['file'], None)
    for f in files:
        files[f] = LP.read_entry(lp, f)['plain']
    out = []
    per = {}
    for i, r in enumerate(rows, 1):
        b = files[r['file']]
        off, n = r['off'], r['n']
        if off < 0 or n <= 0 or off + n > len(b):
            raise SystemExit('[错误] %s @%d(%d) 越界（条目长 %d）' % (r['file'], off, n, len(b)))
        for (o2, n2) in per.get(r['file'], []):
            if off < o2 + n2 and o2 < off + n:
                raise SystemExit('[错误] %s @%d(%d) 与 @%d(%d) 重叠'
                                 % (r['file'], off, n, o2, n2))
        per.setdefault(r['file'], []).append((off, n))
        try:
            live = b[off:off + n].decode('cp932', errors='replace')
        except Exception:
            live = ''
        out.append(dict(r, id=i, live_jp=live))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lpk', default=DEFAULT_LPK)
    ap.add_argument('--trans', action='append', default=None)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()

    lpk = a.lpk
    if not os.path.exists(lpk):
        raise SystemExit('[错误] 目标 LPK 不存在：%s' % lpk)
    trans = load_trans(a.trans or TRANS)
    lp = LP.load(lpk)
    rows = extract_runs(lp)

    edits = {}          # file -> {offset: (n, bytes)}
    stats = {'equal': 0, 'padded': 0, 'truncated': 0, 'keep': 0, 'none': 0}
    bad = []
    lines = ['id\tfile\toff\tnbytes\tgbk_len\tstate\tjp\tcn\tfinal']
    for r in rows:
        i = r['id']
        cn = OVERRIDE.get(i, trans.get(i))
        if cn is None:
            stats['none'] += 1
            bad.append((i, '无译文'))
            continue
        if i in KEEP_ASIS and gbk_norm(cn) == r['jp']:
            stats['keep'] += 1
            continue
        b, how = fit(cn, r['n'])
        if b is None or len(b) != r['n']:
            stats['truncated'] += 1
            bad.append((i, '长度不符 how=%s len=%s need=%d' % (how, None if b is None else len(b), r['n'])))
            continue
        stats[how] = stats.get(how, 0) + 1
        edits.setdefault(r['file'], []).append((r['off'], r['n'], b))
        lines.append('%d\t%s\t%d\t%d\t%d\t%s\t%s\t%s\t%s'
                     % (i, r['file'], r['off'], r['n'], len(b), how, r['live_jp'], cn,
                        b.decode('gbk', errors='replace')))

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)   # 临时\ 被清理后仍可重建
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('对照表: %s（%d 行）' % (REPORT, len(lines) - 1))
    print('状态:', stats)
    if bad:
        print('!! 问题行 %d:' % len(bad))
        for i, why in bad[:20]:
            print('   id=%d %s' % (i, why))
        raise SystemExit('[错误] 存在未解决行，已中止')

    if a.apply:
        newblobs = {}
        for f, lst in edits.items():
            raw = LP.read_entry(lp, f)['plain']
            buf = bytearray(raw)
            for off, n, nb in lst:
                assert len(nb) == n
                if bytes(buf[off:off + n]) == nb:
                    continue
                buf[off:off + n] = nb
            blobs = bytes(buf)
            if blobs != raw:
                newblobs[f] = blobs
        print('待重压条目 %d：%s' % (len(newblobs), sorted(newblobs)))
        info = LP.patch(lpk, lpk, newblobs)
        print('LPK: %d -> %d；changed=%s' % (info['in_size'], info['out_size'], info['changed']))
    else:
        print('（未 --apply：只出对照表，未写 LPK）')


if __name__ == '__main__':
    main()

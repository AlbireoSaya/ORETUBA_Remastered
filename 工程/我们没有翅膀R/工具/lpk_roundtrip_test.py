# -*- coding: utf-8 -*-
r"""LPK 全量往返自检：446 条目全部「解码 -> 重编码 -> 写回」，再用引擎解包器验证。

验收：
  a) 补丁器读回的明文与引擎解包器产出的文件逐字节一致（读路径正确）
  b) 重编码后写回的 LPK 能被引擎解包器完整解出，且内容与原文件一致（写路径正确）
"""
import os, sys, subprocess, shutil, filecmp

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as P

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
LIVE_LPK = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R', 'SCRIPT.LPK')
EXTRACTOR = os.path.join(WS, '工具', 'lucifen', 'lucifen_extract', 'extract_lpk.py')
REF_DIR = os.path.join(PROJ, '语料', 'R版SCRIPT')
TMP = os.path.join(WS, '_VERIFY')


def main():
    os.makedirs(TMP, exist_ok=True)
    print('=== a) 读路径校验：补丁器明文 vs 引擎解包器产物 ===')
    lp = P.load(LIVE_LPK)
    bad = []
    n = 0
    for name, num in lp['ents']:
        try:
            e = P.read_entry(lp, name)
        except Exception as ex:
            bad.append((name, 'read_entry 异常: %s' % ex)); continue
        ref = os.path.join(REF_DIR, name)
        if not os.path.exists(ref):
            continue
        r = open(ref, 'rb').read()
        if e['plain'] != r:
            bad.append((name, '内容不一致: 补丁器 %d 字节 / 解包器 %d 字节' % (len(e['plain']), len(r))))
        n += 1
    print('  比对条目 %d 个；不一致 %d 个' % (n, len(bad)))
    for b in bad[:10]:
        print('   ✘', b)
    if bad:
        print('  => 读路径有问题，终止'); return

    print()
    print('=== b) 写路径校验：全量重编码写回 + 引擎解包器解出比对 ===')
    edits = {}
    for name, num in lp['ents']:
        edits[name] = P.read_entry(lp, name)['plain']
    os.makedirs(os.path.join(TMP, 'rt'), exist_ok=True)
    out_lpk = os.path.join(TMP, 'rt', 'SCRIPT.LPK')   # 文件名决定 key，必须仍叫 SCRIPT.LPK
    info = P.patch(LIVE_LPK, out_lpk, edits)
    print('  写回: %d -> %d 字节，条目 %d' % (info['in_size'], info['out_size'], info['n_entries']))

    outdir = os.path.join(TMP, 'rt_extract')
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    r = subprocess.run([sys.executable, '-X', 'utf8', EXTRACTOR, out_lpk, outdir],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()[-3:]
    print('  解包器输出尾部:', tail)
    got = sorted(os.listdir(outdir)) if os.path.isdir(outdir) else []
    want = sorted(os.listdir(REF_DIR))
    print('  解出条目 %d / 期望 %d' % (len(got), len(want)))
    if got != want:
        only_got = set(got) - set(want)
        only_want = set(want) - set(got)
        print('   ✘ 名单不一致；多出:', sorted(only_got)[:5], ' 缺失:', sorted(only_want)[:5])
        return
    mismatch = []
    for f in want:
        a = open(os.path.join(outdir, f), 'rb').read()
        b = open(os.path.join(REF_DIR, f), 'rb').read()
        if a != b:
            mismatch.append(f)
    print('  内容不一致条目: %d' % len(mismatch))
    if mismatch:
        print('   ✘ 前 10:', mismatch[:10])
    else:
        print('  ✔ 全量往返通过：%d 个条目逐字节一致' % len(want))


if __name__ == '__main__':
    main()

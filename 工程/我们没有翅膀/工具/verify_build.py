# -*- coding: utf-8 -*-
"""verify_build.py —— 回写结果往返校验（ISSUE-20260917-14）

校验对象：`汉化\\SCRIPT_CN\\<脚本>.sob`（或 `--lpk` 指定的打补丁 LPK）
做法：**逐字节比对**（避免编码歧义）
  · 有译文的槽 → 回读原始串必须等于 `前缀 + GBK(译文) + 结尾$`（前缀 = 原 `#说话人\\语音$&`）
  · 无译文的槽 → 回读原始串必须与原版**逐字节一致**（证明未误伤）
  · 原先落在 [strings_start, strings_end) 内的字符串地址，回写后必须仍落在该区间（引擎的文本判据）

用法：python -X utf8 verify_build.py [--lpk]
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具')
from extract_sob0 import parse_sob0  # noqa: E402
import build_sob_cn as B             # noqa: E402
import lpk_patch as LP               # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
CN_DIR = os.path.join(PROJ, '汉化', '剧情汉化')
ORIG_DIR = os.path.join(PROJ, '解包', 'SCRIPT')


def raw_slots(data):
    texts, info = parse_sob0(data)
    if texts is None:
        return None
    return {(t['addr'], t['idx']): t['raw'] for t in texts}


def main():
    use_lpk = '--lpk' in sys.argv
    src = LP.load(os.path.join(PROJ, '汉化', 'LPK', 'SCRIPT.LPK')) if use_lpk else None
    tot = dict(scripts=0, ok=0, should=0, unchanged=0, bad_cn=0, bad_jp=0, addr_bad=0, miss=0)
    for path in sorted(glob.glob(os.path.join(CN_DIR, '*.jsonl'))):
        sc = os.path.basename(path)[:-6]
        want = {}
        for line in open(path, encoding='utf-8'):
            r = json.loads(line)
            if r['cn'].strip():
                want[(r['addr'], r['idx'])] = r
        if not want:
            continue
        if use_lpk:
            if sc not in {n for n, _ in src['ents']}:
                continue
            built = LP.read_entry(src, sc)['plain']
        else:
            fp = os.path.join(PROJ, '汉化', 'SCRIPT_CN', sc)
            if not os.path.exists(fp):
                tot['miss'] += 1
                continue
            built = open(fp, 'rb').read()
        tot['scripts'] += 1
        orig = open(os.path.join(ORIG_DIR, sc), 'rb').read()
        o, b = raw_slots(orig), raw_slots(built)
        if o is None or b is None:
            print('!! 非 SOB0:', sc)
            continue
        ho = B.parse_header(bytearray(orig))
        hb = B.parse_header(bytearray(built))
        for addr, v0 in ho['maps'][4].items():
            if ho['sstart'] <= v0 < ho['send']:
                v = hb['maps'][4].get(addr)
                if v is None or not (hb['sstart'] <= v < hb['send']):
                    tot['addr_bad'] += 1
        for k, raw0 in o.items():
            r = want.get(k)
            got = b.get(k)
            if got is None:
                tot['miss'] += 1
                continue
            if r is None:
                if got == raw0:
                    tot['unchanged'] += 1
                else:
                    tot['bad_jp'] += 1
                    if tot['bad_jp'] <= 3:
                        print('  x 未译槽被改动 %s %s#%d' % (sc, hex(k[0]), k[1]))
                continue
            tot['should'] += 1
            trailer = b'$' if raw0.endswith(b'$') else b''
            if r['kind'] == 'dialogue':
                j = raw0.find(b'$&')
                prefix = raw0[:j + 2] if j >= 0 else b''
            else:
                prefix = b''
            exp = prefix + r['cn'].encode('gbk') + trailer
            if got == exp:
                tot['ok'] += 1
            else:
                tot['bad_cn'] += 1
                if tot['bad_cn'] <= 3:
                    print('  x 译文不符 %s %s#%d: 期望尾 %r / 实得尾 %r'
                          % (sc, hex(k[0]), k[1], exp[-30:], got[-30:]))
    print()
    print('脚本 %d｜译文槽逐字节一致 %d / %d｜未译槽原样 %d｜地址越界 %d'
          % (tot['scripts'], tot['ok'], tot['should'], tot['unchanged'], tot['addr_bad']))
    print('失败项：译文不符 %d｜未译槽被改 %d｜缺失 %d'
          % (tot['bad_cn'], tot['bad_jp'], tot['miss']))
    ok = (tot['bad_cn'] == 0 and tot['bad_jp'] == 0 and tot['addr_bad'] == 0 and tot['miss'] == 0)
    print('结论：', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
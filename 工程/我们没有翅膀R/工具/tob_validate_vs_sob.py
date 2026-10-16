# -*- coding: utf-8 -*-
"""validate_vs_sob.py —— TOB 提取结果 vs 参照汉化 SOB 原日文台词 交叉验证。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tob_extract as E

RT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
CH = r'D:\Gal\[Navel]我们没有翅膀\SCRIPT_CHS'


def sob_lines(path):
    b = open(path, 'rb').read()
    out = []
    i = 0
    while True:
        i = b.find(b'#', i)
        if i < 0:
            break
        e = b.find(b'\x00', i)
        raw = b[i:e]
        i += 1
        if b'$&' not in raw:
            continue
        try:
            s = raw.decode('cp932')
        except Exception:
            continue
        if not any(0x3040 <= ord(c) <= 0x30FF for c in s):
            continue
        meta, txt = s.split('$&', 1)
        txt = txt.rstrip('$')
        meta = meta[1:]
        sp, vo = (meta.split('\\', 1) + [''])[:2] if '\\' in meta else (meta, '')
        if sp == '声':
            sp = ''
        out.append({'speaker': sp, 'voice': vo, 'text': txt})
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    tob_files = sorted(f[:-4] for f in os.listdir(RT) if f.lower().endswith('.tob'))
    sog_files = set(f[:-4] for f in os.listdir(CH) if f.lower().endswith('.sob'))
    tot_tob = tot_match = 0
    tot_sob = tot_hit = 0
    tot_sp_ok = tot_sp_n = tot_vo_ok = tot_vo_n = 0
    scenes_no_sob = []
    scenes_full = 0
    drop = []
    for scene in tob_files:
        info, msgs, warns = E.parse_messages(os.path.join(RT, scene + '.tob'))
        texts = [m['text'] for m in msgs if m['text']]
        tot_tob += len(msgs)
        if scene not in sog_files:
            scenes_no_sob.append(scene)
            continue
        sl = sob_lines(os.path.join(CH, scene + '.sob'))
        tot_sob += len(sl)
        if not sl:
            scenes_no_sob.append(scene + '(sob无台词)')
            continue
        sset = {}
        for r in sl:
            sset.setdefault(r['text'], r)
        matched = 0
        for m in msgs:
            if m['text'] and m['text'] in sset:
                matched += 1
                sr = sset[m['text']]
                if sr['speaker']:
                    tot_sp_n += 1
                    if sr['speaker'] == m['speaker']:
                        tot_sp_ok += 1
                if sr['voice']:
                    tot_vo_n += 1
                    if sr['voice'] == m['voice']:
                        tot_vo_ok += 1
        tot_match += matched
        hit = sum(1 for r in sl if r['text'] in set(texts))
        tot_hit += hit
        if hit == len(sl):
            scenes_full += 1
        else:
            drop.append((scene, len(sl), hit, len(msgs), matched))
    print('TOB 场景数: %d   参照 CHS 场景数: %d' % (len(tob_files), len(sog_files)))
    print('TOB 消息总数: %d   参照台词总数: %d' % (tot_tob, tot_sob))
    print('TOB 文本命中参照原文（逐字）: %d (%.2f%%)' % (tot_match, 100.0 * tot_match / max(1, tot_tob)))
    print('参照台词在 TOB 中全部命中: %d (%.2f%%)' % (tot_hit, 100.0 * tot_hit / max(1, tot_sob)))
    print('说话人一致: %d/%d (%.2f%%)   语音一致: %d/%d (%.2f%%)'
          % (tot_sp_ok, tot_sp_n, 100.0 * tot_sp_ok / max(1, tot_sp_n),
             tot_vo_ok, tot_vo_n, 100.0 * tot_vo_ok / max(1, tot_vo_n)))
    print('参照全部命中的场景数: %d' % scenes_full)
    print('无对应参照的场景 (%d): %s' % (len(scenes_no_sob), scenes_no_sob[:40]))
    drop.sort(key=lambda x: x[2] / max(1, x[1]))
    print('命中率最低的场景 (scene, sob台词, 命中, tob消息, 命中):')
    for d in drop[:15]:
        print('   %-12s sob=%-4d hit=%-4d  tob=%-4d match=%-4d  (%.0f%%)'
              % (d[0], d[1], d[2], d[3], d[4], 100.0 * d[2] / max(1, d[1])))


if __name__ == '__main__':
    main()

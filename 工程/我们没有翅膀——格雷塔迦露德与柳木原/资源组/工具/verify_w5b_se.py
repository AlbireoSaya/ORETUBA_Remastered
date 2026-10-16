# -*- coding: utf-8 -*-
r"""W5b 自证 · S1 SE.LPK 密钥修复验收（ISSUE-20260918-06）

对 `资源组\krkr素材库\ot\se\` 的 582 个 .ogg 逐条验证：
  1. ffprobe 解出 codec == vorbis（可播放），统计失败数
  2. 头部结构：d[28:35] == b'\x01vorbis' 且首页 page_seq == 0
  3. 与其它源（ota/otp/otr/np）同 stem 的 SE 交叉比对，分三类计数：
       完全相同 / 仅尾部前缀差异 / 内容不同
  4. 与重提前的坏文件（子代理工作区 ...\W5b\bad_se_backup）逐条 md5 对比，确认确实被修复
  5. 清单字节数守恒（_清单.json 的 out_bytes 与实际一致）

用法：python -X utf8 verify_w5b_se.py
输出：子代理工作区\ISSUE-20260918-06\W5b\W5b自证.json
"""
import os, sys, json, struct, hashlib, subprocess, collections

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
LIB = os.path.join(WS, '工程', '我们没有翅膀——格雷塔迦露德与柳木原', '资源组', 'krkr素材库')
SE_DIR = os.path.join(LIB, 'ot', 'se')
BAD_DIR = os.path.join(WS, '子代理工作区', 'ISSUE-20260918-06', 'W5b', 'bad_se_backup')
OUT_DIR = os.path.join(WS, '子代理工作区', 'ISSUE-20260918-06', 'W5b')
FFPROBE = 'ffprobe'


def ffprobe_codec(path):
    try:
        r = subprocess.run(
            [FFPROBE, '-v', 'error', '-select_streams', 'a:0',
             '-show_entries', 'stream=codec_name', '-of', 'default=nw=1:nk=1', path],
            capture_output=True, timeout=30)
        return r.stdout.decode('utf-8', 'replace').strip(), r.returncode, \
            r.stderr.decode('utf-8', 'replace').strip()[:200]
    except Exception as e:
        return '', -1, repr(e)


def head_ok(d):
    return (len(d) >= 35 and d[28:35] == b'\x01vorbis'
            and d[:4] == b'OggS' and struct.unpack_from('<I', d, 18)[0] == 0)


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    files = sorted(f for f in os.listdir(SE_DIR) if f.lower().endswith('.ogg'))
    print('ot/se 文件数：%d' % len(files))
    res = {'total': len(files), 'playable': 0, 'ffprobe_fail': [],
           'codec_hist': collections.Counter(), 'header_ok': 0, 'header_fail': [],
           'repaired': 0, 'same_as_bad': 0, 'size_mismatch': [], 'cross': {}}

    bad_md5 = json.load(open(os.path.join(OUT_DIR, 'bad_se_md5.json'), encoding='utf-8'))
    manifest = json.load(open(os.path.join(LIB, 'ot', '_清单.json'), encoding='utf-8'))
    man_se = {r['out_relpath'].split('/')[-1]: r['out_bytes']
              for r in manifest if r['archive'] == 'SE.LPK'}

    for i, fn in enumerate(files, 1):
        p = os.path.join(SE_DIR, fn)
        d = open(p, 'rb').read()
        codec, rc, err = ffprobe_codec(p)
        if rc == 0 and codec == 'vorbis':
            res['playable'] += 1
        else:
            res['ffprobe_fail'].append({'file': fn, 'rc': rc, 'codec': codec, 'err': err})
        res['codec_hist'][codec or '(none)'] += 1
        if head_ok(d):
            res['header_ok'] += 1
        else:
            res['header_fail'].append(fn)
        if fn in bad_md5:
            if md5(d) != bad_md5[fn]:
                res['repaired'] += 1
            else:
                res['same_as_bad'] += 1
        if fn in man_se and man_se[fn] != len(d):
            res['size_mismatch'].append({'file': fn, 'manifest': man_se[fn], 'disk': len(d)})
        if i % 100 == 0:
            print('  ffprobe %d/%d  可播 %d' % (i, len(files), res['playable']), flush=True)

    res['codec_hist'] = dict(res['codec_hist'])
    res['ffprobe_fail_n'] = len(res['ffprobe_fail'])
    res['header_fail_n'] = len(res['header_fail'])
    print('[1] ffprobe 可播 %d/%d，失败 %d' % (res['playable'], res['total'], res['ffprobe_fail_n']))
    print('[2] 头部结构 OK %d/%d，失败 %d' % (res['header_ok'], res['total'], res['header_fail_n']))
    print('[4] 与坏版本比对：被修复 %d，与坏版相同 %d' % (res['repaired'], res['same_as_bad']))
    print('[5] 清单字节数不一致 %d 条' % len(res['size_mismatch']))

    # --- [3] 跨源同名比对 ---
    def tail_prefix_diff(a, b):
        """前缀全同、仅尾部差异 → (True, 差异起点, 长度差)"""
        n = min(len(a), len(b))
        k = 0
        while k < n and a[k] == b[k]:
            k += 1
        return k, abs(len(a) - len(b))

    cross = collections.Counter()
    cross_detail = []
    for fn in files:
        stem = fn[len('ot_'):] if fn.startswith('ot_') else fn
        p = os.path.join(SE_DIR, fn)
        a = open(p, 'rb').read()
        for src in ('ota', 'otp', 'otr', 'np'):
            for cand in (src + '_' + stem, fn):
                q = os.path.join(LIB, src, 'se', cand)
                if os.path.exists(q):
                    b = open(q, 'rb').read()
                    if a == b:
                        cls = 'identical'
                    else:
                        k, gap = tail_prefix_diff(a, b)
                        # 仅尾部差异：共同前缀 >= len - 64 且长度差 <= 64
                        if k >= min(len(a), len(b)) - 64 and gap <= 64:
                            cls = 'tail_only'
                        else:
                            cls = 'content_differs'
                    cross[(src, cls)] += 1
                    cross_detail.append({'ot': fn, 'other': src + '/' + cand,
                                         'cls': cls, 'common_prefix': k,
                                         'sizes': [len(a), len(b)]})
                    break
    res['cross'] = {f'{s}|{c}': v for (s, c), v in sorted(cross.items())}
    res['cross_detail'] = cross_detail
    tot_cmp = sum(cross.values())
    print('[3] 跨源同 stem 比对：共 %d 对' % tot_cmp)
    for (s, c), v in sorted(cross.items()):
        print('    ot vs %-4s %-15s %4d (%.1f%%)' % (s, c, v, 100.0 * v / tot_cmp if tot_cmp else 0))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'W5b自证.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('自证落盘：%s' % os.path.join(OUT_DIR, 'W5b自证.json'))


if __name__ == '__main__':
    main()
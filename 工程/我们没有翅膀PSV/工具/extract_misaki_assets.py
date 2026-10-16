"""提取《我们没有翅膀》PS Vita 版「林田美咲线」的资源。

输入：美咲线清单/资源引用.tsv（由 collect_misaki_assets.py 产出）
输出：
  素材/美咲线/images/{cg,chr,etc}/…   图像（PNG 原样）
  素材/美咲线/script/…                31 个线路脚本（SJIS 原样）
  美咲线清单/音频提取清单.json         语音/BGM/SE 的编号与名字（供转码用）

用法: python extract_misaki_assets.py <工程目录> <解密后 media 目录>
"""
import os
import re
import csv
import sys
import json
import shutil
import collections

sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工具\pylibs')
from cricodecs import cpk as C  # noqa: E402

ARCH_DIR = {'CG.cpk': 'images/cg', 'CHR.cpk': 'images/chr',
            'SystemData.cpk': 'images/ui', 'ETC.cpk': 'images/etc',
            'media/img/logo': 'images/logo'}


def is_misaki_route(fn):
    return bool(re.match(r'^M\d\d_\d\d$', fn)) or bool(re.match(r'^P03_01[A-Z]$', fn))


def voice_names(script_dir):
    """从脚本注释里取「语音编号 → 原名」。"""
    m = {}
    for fn in sorted(os.listdir(script_dir)):
        p = os.path.join(script_dir, fn)
        if not os.path.isfile(p):
            continue
        text = open(p, 'rb').read().decode('cp932', 'replace')
        for mm in re.finditer(r':Voice\s+(\d+)\s*(?://\s*([A-Za-z0-9_]+))?', text):
            if mm.group(2):
                m.setdefault(int(mm.group(1)), mm.group(2))
    return m


def main():
    proj, media = sys.argv[1], sys.argv[2]
    out_root = os.path.join(proj, '素材', '美咲线')
    os.makedirs(out_root, exist_ok=True)

    rows = list(csv.DictReader(open(os.path.join(proj, '美咲线清单', '资源引用.tsv'),
                                    encoding='utf-8-sig'), delimiter='\t'))
    cwd = os.getcwd()
    os.chdir(media)
    loaded = {}
    n_img = 0
    for r in rows:
        arch = r['archive']
        dst_dir = os.path.join(out_root, ARCH_DIR.get(arch, 'images/other'))
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, r['filename'])
        if arch.startswith('media/'):
            src = os.path.join(media, arch.split('/', 1)[1], r['filename'])
            shutil.copy2(src, dst)
        else:
            if arch not in loaded:
                loaded[arch] = C.load(arch)
            data = loaded[arch].file_bytes(int(r['index']))
            # 防串位：cricodecs 的 file_bytes 必须传列表下标（不是 CpkEntry.id），
            # 且返回长度应等于 TOC 声明长度，否则立即失败而不是静默写出错文件
            assert len(data) == int(r['size']), 'declared=%d got=%d for %s' % (int(r['size']), len(data), r['filename'])
            open(dst, 'wb').write(data)
        n_img += 1
    os.chdir(cwd)
    print('图像提取:', n_img)

    # 脚本
    sd = os.path.join(proj, '脚本解包')
    dst_sd = os.path.join(out_root, 'script')
    os.makedirs(dst_sd, exist_ok=True)
    n_sc = 0
    for fn in sorted(os.listdir(sd)):
        if is_misaki_route(fn):
            shutil.copy2(os.path.join(sd, fn), os.path.join(dst_sd, fn))
            n_sc += 1
    print('脚本提取:', n_sc)

    # 音频清单
    idx = json.load(open(os.path.join(proj, '美咲线清单', '索引引用.json'), encoding='utf-8'))
    vn = voice_names(sd)
    audio = {
        'voice': sorted(({'index': int(k), 'name': vn.get(int(k))} for k in idx.get('Voice', {})),
                        key=lambda x: x['index']),
        'bgm': sorted(int(k) for k in idx.get('BGM', {})),
        'se': sorted(int(k) for k in idx.get('SE', {})),
    }
    with open(os.path.join(proj, '美咲线清单', '音频提取清单.json'), 'w', encoding='utf-8') as fh:
        json.dump(audio, fh, ensure_ascii=False, indent=1)
    print('音频清单: voice %d / bgm %d / se %d (其中有名字的语音 %d)'
          % (len(audio['voice']), len(audio['bgm']), len(audio['se']),
             sum(1 for v in audio['voice'] if v['name'])))


if __name__ == '__main__':
    main()

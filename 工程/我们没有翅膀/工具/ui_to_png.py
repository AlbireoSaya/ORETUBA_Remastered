# -*- coding: utf-8 -*-
r"""ui_to_png.py —— 把 Lucifen UI 素材（SYS.LPK 的 .elg）全量转成 PNG（ISSUE-20260919-16）

用法：
  python -X utf8 ui_to_png.py                       # 默认：SYS.LPK → 工程\我们没有翅膀\素材提取\UI\
  python -X utf8 ui_to_png.py --out <目录>
  python -X utf8 ui_to_png.py --lpk <LPK 路径>
  python -X utf8 ui_to_png.py --loose <松散目录>     # 另转汉化补丁的松散覆盖层
  python -X utf8 ui_to_png.py --only "gl_.*"        # 只转名字匹配该正则的条目

要点：
  · 只读打开归档（mmap ACCESS_READ），不改动游戏目录任何文件；
  · 直接调用 elg2png 的 Reader.decode()，不起子进程（1099 次转换快得多）；
  · 保留 alpha（RGBA 原样；原图无 alpha 则输出 RGB）；
  · 逐条容错：单条失败只记录，不中断整批；
  · 产出 manifest.json：条目名 / 尺寸 / 模式 / PNG 字节 / 透明像素占比。
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TOOLS = r'E:\ZCode Workspace\Galgame\工具\lucifen\Lucifen-Tools'
PYLIBS = r'E:\ZCode Workspace\Galgame\工具\pylibs'
for p in (TOOLS, PYLIBS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import lpk_sel as S              # noqa: E402
import elg2png                   # noqa: E402
from PIL import Image            # noqa: E402

DEFAULT_LPK = r'D:\Gal\[Navel]我们没有翅膀\SYS.LPK'
DEFAULT_LOOSE = r'D:\Gal\[Navel]我们没有翅膀\SYS'


def alpha_stat(im):
    """返回 (全透明像素数, 半透明像素数, 总像素数)；无 alpha 通道时返回 None。"""
    if 'A' not in im.getbands():
        return None
    a = im.getchannel('A')
    w, h = im.size
    fully = semi = 0
    for v in a.get_flattened_data():
        if v == 0:
            fully += 1
        elif v < 255:
            semi += 1
    return fully, semi, w * h


def convert_bytes(data: bytes, name: str, out_dir: str):
    im = elg2png.Reader(data).decode()
    dst = os.path.join(out_dir, os.path.splitext(name)[0] + '.png')
    im.save(dst)
    st = alpha_stat(im)
    rec = dict(name=name, png=os.path.basename(dst), w=im.size[0], h=im.size[1],
               mode=im.mode, bytes=os.path.getsize(dst))
    if st:
        rec['alpha_transparent'], rec['alpha_semi'], rec['pixels'] = st
    return rec


def run_lpk(lpk_path, out_dir, only):
    lp = S.parse(lpk_path)
    ents = [e for e in lp['ents'] if e['name'].lower().endswith('.elg')]
    if only:
        pat = re.compile(only)
        ents = [e for e in ents if pat.search(e['name'])]
    print('%s：%d 条目 flags=0x%02x，其中 .elg %d 条 → %s'
          % (os.path.basename(lpk_path), len(lp['ents']), lp['flags'], len(ents), out_dir))
    os.makedirs(out_dir, exist_ok=True)
    ok, bad = [], []
    for i, e in enumerate(ents, 1):
        try:
            chunk = bytearray(lp['mm'][e['off']:min(e['off'] + e['sc'], len(lp['mm']))])
            if lp['flags'] & S.X.IS_COMPRESSED:
                chunk = S.X.lzss_decompress(bytes(chunk), e['so'])
            if lp['flags'] & S.X.IS_ENCRYPTED2:
                S.X.decrypt_content_2_full(chunk, S.X.CONTENT_XOR)
            if lp['flags'] & S.X.IS_ENCRYPTED1:
                S.X.decrypt_content_1_first_256(chunk, lp['k1'], S.X.ROTATE_PATTERN)
            if lp['prefix']:
                chunk = bytearray(lp['prefix']) + chunk
            ok.append(convert_bytes(bytes(chunk), e['name'], out_dir))
        except Exception as ex:
            bad.append(dict(name=e['name'], error='%s: %s' % (type(ex).__name__, ex)))
        if i % 100 == 0:
            print('   … %d/%d（成功 %d，失败 %d）' % (i, len(ents), len(ok), len(bad)))
    return ok, bad


def run_loose(loose_dir, out_dir, only):
    files = sorted(f for f in os.listdir(loose_dir) if f.lower().endswith('.elg'))
    if only:
        pat = re.compile(only)
        files = [f for f in files if pat.search(f)]
    print('%s：.elg %d 条 → %s' % (loose_dir, len(files), out_dir))
    os.makedirs(out_dir, exist_ok=True)
    ok, bad = [], []
    for f in files:
        try:
            ok.append(convert_bytes(open(os.path.join(loose_dir, f), 'rb').read(), f, out_dir))
        except Exception as ex:
            bad.append(dict(name=f, error='%s: %s' % (type(ex).__name__, ex)))
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lpk', default=DEFAULT_LPK)
    ap.add_argument('--loose', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--only', default=None)
    a = ap.parse_args()

    if a.loose:
        out = a.out or os.path.join(PROJ, '素材提取', 'UI_汉化补丁层')
        ok, bad = run_loose(a.loose, out, a.only)
        tag = '汉化补丁松散层'
    else:
        out = a.out or os.path.join(PROJ, '素材提取', 'UI')
        ok, bad = run_lpk(a.lpk, out, a.only)
        tag = os.path.basename(a.lpk)

    man = dict(source=tag, out=out, total=len(ok) + len(bad), ok=len(ok), failed=len(bad),
               entries=sorted(ok, key=lambda r: r['name']), errors=bad)
    mp = os.path.join(out, 'manifest.json')
    json.dump(man, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tot = sum(r['bytes'] for r in ok)
    print('\n完成：成功 %d / 失败 %d；PNG 合计 %.1f MB；manifest → %s'
          % (len(ok), len(bad), tot / 1048576, mp))
    for b in bad[:20]:
        print('   ✗ %s  %s' % (b['name'], b['error']))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
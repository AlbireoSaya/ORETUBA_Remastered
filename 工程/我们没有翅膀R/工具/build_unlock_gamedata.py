# -*- coding: utf-8 -*-
r"""生成「R 版全 CG/全回想解锁」GAMEDATA.DAT（ISSUE-ORETUBAR-R 存档线）。

数据来源与性质
--------------
解锁内容（条目数组）= 公开存档站 sagaoz 的 R 版全 CG 存档
    https://sagaoz.net/savedata/a/oretubar_hihumi.zip  (2011-07-02 上传，readme 注明「ＣＧ・回想１００％」)
    下载件与解出物保存在 子代理工作区\ISSUE-ORETUBAR-R\存档\外部样本\ 作为出处凭据。
**本脚本不直接把外部文件当成品**：先把外部文件按逆向出的格式解出「条目数组」，
再用本仓库自己的 LZSS 编码器（工具\gamedata_lzss.py）重新压回，因此产出的
字节流是本仓库自己编出来的，只借用其"解锁内容"。

用法
----
    python -X utf8 build_unlock_gamedata.py [外部GAMEDATA.DAT] [-o 输出]

默认外部样本路径见 SRC_DEFAULT；默认输出 工程\我们没有翅膀R\存档候选\R版全解锁_GAMEDATA.DAT。
构建后自动做往返校验（自产文件解码 == 外部文件解码，逐字节比对）。
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata_lzss import lzss_decode, lzss_encode  # noqa: E402

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SRC_DEFAULT = os.path.join(WS, '子代理工作区', 'ISSUE-ORETUBAR-R', '存档', '外部样本',
                           'sagaoz_oretubar_hihumi', 'GAMEDATA.DAT')
OUT_DEFAULT = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')

# R 版（2011）文件布局：[u32 comp_size][u32 uncomp_size] + LZSS 流，无其它块
R_HEADER = 8
# 原版（2009）文件布局：[u32 comp_size][u32 uncomp_size][10 字节块] + LZSS 流
OLD_HEADER = 18


def read_r(path):
    raw = open(path, 'rb').read()
    comp, uncomp = struct.unpack_from('<II', raw, 0)
    stream = raw[R_HEADER:R_HEADER + comp]
    return raw, comp, uncomp, stream, lzss_decode(stream, limit=uncomp + 1)


def describe(arr):
    ones = sum(1 for b in arr if b)
    odd = [(i, arr[i]) for i, b in enumerate(arr) if b not in (0, 1)]
    return ones, odd


def load_array_text(path):
    """从可入库的 base64 数据源文本读取解锁数组（*.dat 被 .gitignore 忽略时的替代来源）。"""
    import base64
    txt = open(path, encoding='utf-8').read()
    meta = {}
    b64 = []
    in_b64 = False
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if in_b64:
            b64.append(line); continue
        if line.startswith('#'):
            continue
        if line.startswith('array_base64'):
            in_b64 = True; continue
        if '=' in line:
            k, v = line.split('=', 1)
            meta[k.strip()] = v.strip()
    arr = base64.b64decode(''.join(b64))
    return arr, meta


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    src = args[0] if args else SRC_DEFAULT
    out = OUT_DEFAULT
    if '-o' in sys.argv:
        out = sys.argv[sys.argv.index('-o') + 1]

    if src.lower().endswith('.txt'):
        print('源（base64 数据源文本）:', src)
        arr, meta = load_array_text(src)
        raw = None
        comp = uncomp = None
        ones, odd = describe(arr)
        print('  uncomp=%d 展开=%d 置位条目=%d 非0/1条目=%s' % (len(arr), len(arr), ones, odd))
        if meta.get('array_sha256'):
            got = hashlib.sha256(arr).hexdigest()
            print('  数组 sha256 校验: %s (%s)' % (got, '与文本记录一致' if got == meta['array_sha256'] else '不一致!'))
            assert got == meta['array_sha256'], '数组 sha256 与数据源文本记录不符'
    else:
        print('源（外部全CG存档）:', src)
        raw, comp, uncomp, stream, arr = read_r(src)
        ones, odd = describe(arr)
        print('  file=%d comp=%d uncomp=%d 展开=%d 置位条目=%d 非0/1条目=%s'
              % (len(raw), comp, uncomp, len(arr), ones, odd))
        assert len(arr) == uncomp, '展开长度与头不一致'
        assert len(stream) == comp, '流长度与头不一致'

    # 用本仓库编码器重新压回
    new_stream, ntok = lzss_encode(arr)
    new_raw = struct.pack('<II', len(new_stream), len(arr)) + new_stream

    # 往返校验
    back = lzss_decode(new_raw[R_HEADER:R_HEADER + len(new_stream)], limit=len(arr) + 1)
    ok = (back == arr)
    print('自产文件: comp=%d uncomp=%d tokens=%d file=%d  往返一致=%s'
          % (len(new_stream), len(arr), ntok, len(new_raw), ok))
    if not ok:
        diffs = [i for i in range(min(len(back), len(arr))) if back[i] != arr[i]]
        raise SystemExit('往返校验失败，差异位置: %s' % diffs[:20])

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(new_raw)
    print('已写出:', out)
    print('  sha256(自产) =', hashlib.sha256(new_raw).hexdigest())
    if raw is not None:
        print('  sha256(外部) =', hashlib.sha256(raw).hexdigest())
    print('  展开数组 sha256 =', hashlib.sha256(arr).hexdigest())
    print('  两者展开数组是否逐字节相同:', read_r(out)[4] == arr)


if __name__ == '__main__':
    main()

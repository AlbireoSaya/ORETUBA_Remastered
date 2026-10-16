# -*- coding: utf-8 -*-
r"""GAMEDATA.DAT codec（ISSUE-ORETUBAR-R 全解锁存档线）

实测结论（详见 子代理工作区\ISSUE-ORETUBAR-R\存档\报告.md）：

    GAMEDATA.DAT = [u32 comp_size][u32 uncomp_size] + LZSS(comp_size 字节)

LZSS 即引擎（Lucifen Easy Game System DX）自家算法，与 LPK1 归档条目压缩同源：
    · 标志字节在前，1 字节管 8 个 token，bit0 先取（LSB first）
    · bit = 1 → 紧跟 1 字节字面量
    · bit = 0 → 紧跟 2 字节回溯：off = b0 | ((b1 & 0xf0) << 4)，len = (b1 & 0x0f) + 3
    · 滑窗 4096 字节，零初始化，写入游标从 0xfee 起（**off 是窗口绝对下标，非距离**）
    · 解码在输入耗尽或输出达到 uncomp_size 时结束

uncomp_size = 条目总数（= 该作品存档写入的条目条数）；每 1 字节 1 个条目，
取值 0x00 / 0x01（个别条目出现 0xff 等，见报告"未决问题"）。

用法：
    python -X utf8 gamedata_lzss.py decode <GAMEDATA.DAT> <out.bin>
    python -X utf8 gamedata_lzss.py info   <GAMEDATA.DAT>
    python -X utf8 gamedata_lzss.py build  <array.bin> <out GAMEDATA.DAT>
    python -X utf8 gamedata_lzss.py roundtrip <GAMEDATA.DAT>
"""
import struct
import sys


# ---------------------------------------------------------------- 解码
def lzss_decode(compr, limit=1 << 22):
    """严格复刻引擎 LZSS 解码器。返回解压结果；输入耗尽或达 limit 时停止。"""
    out = bytearray()
    win = bytearray(4096)
    wn = 0xFEE
    cur = 0
    n = len(compr)
    flag = 0
    while True:
        flag >>= 1
        if not (flag & 0x0100):
            if cur >= n:
                break
            flag = compr[cur] | 0xFF00
            cur += 1
        if flag & 1:
            if cur >= n:
                break
            d = compr[cur]
            cur += 1
            win[wn] = d
            wn = (wn + 1) & 0xFFF
            out.append(d)
        else:
            if cur + 1 >= n:
                break
            off = compr[cur]
            cb = compr[cur + 1]
            cur += 2
            off |= (cb & 0xF0) << 4
            ln = (cb & 0x0F) + 3
            for i in range(ln):
                d = win[(off + i) & 0xFFF]
                win[wn] = d
                wn = (wn + 1) & 0xFFF
                out.append(d)
        if len(out) >= limit:
            break
    return bytes(out)


def lzss_decode_traced(compr, limit=1 << 22):
    """同 lzss_decode，但额外返回每个输出字节的来源 (类型, 位置) 便于取证。"""
    out = bytearray()
    src = []
    win = bytearray(4096)
    wn = 0xFEE
    cur = 0
    n = len(compr)
    flag = 0
    while True:
        flag >>= 1
        if not (flag & 0x0100):
            if cur >= n:
                break
            flag = compr[cur] | 0xFF00
            cur += 1
        if flag & 1:
            if cur >= n:
                break
            p = cur
            d = compr[cur]
            cur += 1
            win[wn] = d
            wn = (wn + 1) & 0xFFF
            out.append(d)
            src.append(('L', p))
        else:
            if cur + 1 >= n:
                break
            off = compr[cur]
            cb = compr[cur + 1]
            cur += 2
            off |= (cb & 0xF0) << 4
            ln = (cb & 0x0F) + 3
            for i in range(ln):
                d = win[(off + i) & 0xFFF]
                win[wn] = d
                wn = (wn + 1) & 0xFFF
                out.append(d)
                src.append(('M', (off + i) & 0xFFF))
        if len(out) >= limit:
            break
    return bytes(out), src, cur


# ---------------------------------------------------------------- 编码
def lzss_encode(data, max_len=18, min_len=3, max_cand=4096, lazy=True):
    """贪心 + 惰性匹配 LZSS 编码器：逐字节模拟解码器窗口，逐候选校验解码结果与 data 一致。

    返回 (compressed_stream, n_tokens)。
    """
    data = bytes(data)
    n = len(data)
    win = bytearray(4096)
    wn = 0xFEE
    toks = []          # ('L', byte) / ('M', off, len)

    def find(i):
        """在窗口里为 data[i:] 找最长合法 match，返回 (len, off)。"""
        c0 = data[i]
        best_len = 0
        best_off = 0
        seen = 0
        for off in range(4096):
            if win[off] != c0:
                continue
            seen += 1
            if seen > max_cand:
                break
            w = bytearray(win)
            wnp = wn
            ln = 0
            for k in range(max_len):
                if i + k >= n:
                    break
                d = w[(off + k) & 0xFFF]
                if d != data[i + k]:
                    break
                w[wnp] = d
                wnp = (wnp + 1) & 0xFFF
                ln += 1
            if ln > best_len:
                best_len = ln
                best_off = off
                if ln == max_len:
                    break
        return best_len, best_off

    i = 0
    while i < n:
        bl, bo = find(i)
        if bl >= min_len and lazy and i + 1 < n:
            # 惰性匹配：若下一位置的 match 更长，则本位置改发字面量
            nl, no = find(i + 1)
            if nl > bl:
                bl = 0
        if bl >= min_len:
            for k in range(bl):
                d = win[(bo + k) & 0xFFF]
                win[wn] = d
                wn = (wn + 1) & 0xFFF
            toks.append(('M', bo, bl))
            i += bl
        else:
            c0 = data[i]
            win[wn] = c0
            wn = (wn + 1) & 0xFFF
            toks.append(('L', c0))
            i += 1

    # 组装：每 8 个 token 前置 1 个标志字节（bit0 先，未用位填 0，与引擎自身产物一致）
    out = bytearray()
    for g in range(0, len(toks), 8):
        group = toks[g:g + 8]
        flag = 0
        body = bytearray()
        for k, t in enumerate(group):
            if t[0] == 'L':
                flag |= (1 << k)
                body.append(t[1])
            else:
                off, ln = t[1], t[2]
                body.append(off & 0xFF)
                body.append(((off >> 4) & 0xF0) | ((ln - 3) & 0x0F))
        out.append(flag)
        out += body
    return bytes(out), len(toks)


def build_file(array):
    """把条目字节数组打包成完整 GAMEDATA.DAT（头 + LZSS）。"""
    stream, ntok = lzss_encode(array)
    return struct.pack('<II', len(stream), len(array)) + stream, ntok


def parse_file(raw):
    """拆头：返回 (comp_size, uncomp_size, stream, decoded)。"""
    if len(raw) < 8:
        raise ValueError('文件过短')
    comp, uncomp = struct.unpack_from('<II', raw, 0)
    stream = raw[8:8 + comp]
    dec = lzss_decode(stream, limit=uncomp + 1)
    return comp, uncomp, stream, dec


# ---------------------------------------------------------------- CLI
def _cli():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == 'decode':
        raw = open(path, 'rb').read()
        comp, uncomp, stream, dec = parse_file(raw)
        dst = sys.argv[3] if len(sys.argv) > 3 else path + '.dec'
        open(dst, 'wb').write(dec)
        print('comp=%d uncomp=%d decoded=%d -> %s' % (comp, uncomp, len(dec), dst))
    elif cmd == 'info':
        raw = open(path, 'rb').read()
        comp, uncomp, stream, dec = parse_file(raw)
        ones = sum(1 for b in dec if b)
        print('file=%d comp=%d uncomp=%d(0x%x) decoded=%d ones=%d' %
              (len(raw), comp, uncomp, uncomp, len(dec), ones))
        print('decoded==uncomp:', len(dec) == uncomp)
    elif cmd == 'build':
        arr = open(path, 'rb').read()
        raw, ntok = build_file(arr)
        dst = sys.argv[3]
        open(dst, 'wb').write(raw)
        back = lzss_decode(raw[8:8 + struct.unpack_from('<I', raw, 0)[0]], limit=len(arr) + 1)
        print('array=%d tokens=%d file=%d roundtrip=%s -> %s' %
              (len(arr), ntok, len(raw), back == arr, dst))
    elif cmd == 'roundtrip':
        raw = open(path, 'rb').read()
        comp, uncomp, stream, dec = parse_file(raw)
        re_stream, ntok = lzss_encode(dec)
        back = lzss_decode(re_stream, limit=len(dec) + 1)
        print('orig stream=%d  re-encoded stream=%d tokens=%d  roundtrip=%s' %
              (comp, len(re_stream), ntok, back == dec))
    else:
        print(__doc__)


if __name__ == '__main__':
    _cli()

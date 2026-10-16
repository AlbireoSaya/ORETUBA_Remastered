# -*- coding: utf-8 -*-
r"""Lucifen LZSS 压缩/解压（ISSUE-ORETUBAR-R）。

解压算法取自社区实现（crass / lucifen_extract，已用 446 个 LPK 条目实测验证）：

    窗口 4096 字节、零初始化，写入游标从 0xfee 开始；
    控制字节在前，1 字节管 8 个 token，bit0 优先：
      bit = 1 → 字面量（1 字节）
      bit = 0 → 回溯（2 字节）：off = b0 | ((b1 & 0xf0) << 4)
                                len = (b1 & 0x0f) + 3
      off 是「窗口绝对下标」，不是距离 —— 复制时按 (off + i) & (4096-1) 逐字节读窗口。

压缩器按同一模型反向实现：贪心匹配窗口内容，输出最小 token 流；
自校验 = 解压(压缩(x)) == x 逐字节相等。
"""
import sys

WIN = 4096
WIN_MASK = WIN - 1
START = 0xFEE          # 写游标起点（与解压器一致）
MAX_MATCH = 18         # len - 3 <= 0x0f
MIN_MATCH = 3          # len = (b1 & 0x0f) + 3


def decompress(compr: bytes, uncomprlen: int) -> bytes:
    """社区原版解压实现（保持逐字节等价，便于交叉验证）。"""
    uncompr = bytearray(uncomprlen)
    act = 0
    curbyte = 0
    ncur = START
    win = bytearray(WIN)
    flag = 0
    n = len(compr)
    while True:
        flag >>= 1
        if not (flag & 0x0100):
            if curbyte >= n:
                break
            flag = compr[curbyte] | 0xFF00
            curbyte += 1
        if flag & 1:
            if curbyte >= n:
                break
            data = compr[curbyte]; curbyte += 1
            if act >= uncomprlen:
                break
            win[ncur] = data
            ncur = (ncur + 1) & WIN_MASK
            uncompr[act] = data; act += 1
        else:
            if curbyte + 1 >= n:
                break
            off = compr[curbyte]
            ln = compr[curbyte + 1]
            curbyte += 2
            off |= (ln & 0xF0) << 4
            ln = (ln & 0x0F) + 3
            for i in range(ln):
                if act >= uncomprlen:
                    return bytes(uncompr[:act])
                data = win[(off + i) & WIN_MASK]
                win[ncur] = data
                ncur = (ncur + 1) & WIN_MASK
                uncompr[act] = data; act += 1
    return bytes(uncompr[:act])


def compress(data: bytes, level: int = 1) -> bytes:
    """把 data 压成 Lucifen LZSS 流。

    关键不变量（与解压器严格一致）：
      * win 是 4096 字节环形窗，初始全零；写游标 ncur 从 0xfee 起。
      * 回溯的 off 是「窗口绝对下标」，解压时按 (off + i) & 0xfff 逐字节取。
      * 因此**只能引用已经写入过的位置**；还没写过的位置虽为零，引用了也能解对
        （因为解压器同样看到零），但为了与原始流形态接近、避免越界，这里只
        在「已写区域」内搜索匹配。
    已写区域：从 START 起共写了 pos 个字节，即窗口下标集合
      { (START + j) & 0xfff : 0 <= j < pos }
    """
    win = bytearray(WIN)
    ncur = START
    out = bytearray()
    ctrl_pos = 0
    ctrl_bit = 8          # 触发首组分配
    n = len(data)
    pos = 0

    # 3 字节哈希索引：key -> [窗口绝对下标...]（按写入顺序，新的在后）
    idx = {}
    MAX_CAND = 24         # 每个 key 最多保留的候选数

    def new_group():
        nonlocal ctrl_pos, ctrl_bit
        ctrl_pos = len(out)
        out.append(0)      # 占位控制字节
        ctrl_bit = 0

    def h3(p):
        return data[p] | (data[p + 1] << 8) | (data[p + 2] << 16)

    while pos < n:
        if ctrl_bit == 8:
            new_group()

        best_len, best_off = 0, 0
        limit = min(MAX_MATCH, n - pos)
        if limit >= MIN_MATCH and pos > 0:
            need = data[pos:pos + limit]
            # 引擎解压是逐字节「读 (off+k) -> 写 (ncur+k)」。若源区间与本次写入区间
            # 在同一环形窗内重叠，源字节会随写入改变（RLE 式重复），压缩端难以复现。
            # 因此**只选不与写入区间重叠的候选**：仍可引用窗口里的全部历史数据
            # （≥ MAX_MATCH 字节前的都安全），只是放弃部分 RLE 式长匹配，压缩率略降。
            danger = set((ncur + k) & WIN_MASK for k in range(limit))
            for o in reversed(idx.get(h3(pos), [])):
                # 源区间 [o, o+limit) 与危险区不相交才安全
                if any(((o + k) & WIN_MASK) in danger for k in range(limit)):
                    continue
                if win[o] != need[0]:
                    continue
                k = 1
                while k < limit and win[(o + k) & WIN_MASK] == need[k]:
                    k += 1
                if k > best_len:
                    best_len, best_off = k, o
                    if k == limit:
                        break

        if best_len >= MIN_MATCH:
            out.append(best_off & 0xFF)
            out.append(((best_off >> 4) & 0xF0) | ((best_len - MIN_MATCH) & 0x0F))
            ctrl_bit += 1                      # 回溯 token 同样占用一位
            # 与解压器严格同语义：逐字节「读窗口 -> 写窗口」。源/目标在环形窗内重叠时，
            # 该语义等价于 RLE 式重复，逐字节推进即可自动复现（不可整段先取值）。
            for k in range(best_len):
                v = win[(best_off + k) & WIN_MASK]
                npos = ncur
                win[ncur] = v
                ncur = (ncur + 1) & WIN_MASK
                j = pos + k
                if j + 3 <= n:
                    kk = data[j] | (data[j + 1] << 8) | (data[j + 2] << 16)
                    lst = idx.setdefault(kk, [])
                    lst.append(npos)
                    if len(lst) > MAX_CAND:
                        del lst[0]
            pos += best_len
        else:
            out[ctrl_pos] |= (1 << ctrl_bit)
            ctrl_bit += 1
            v = data[pos]
            npos = ncur
            win[ncur] = v
            ncur = (ncur + 1) & WIN_MASK
            if pos + 3 <= n:
                kk = h3(pos)
                lst = idx.setdefault(kk, [])
                lst.append(npos)
                if len(lst) > MAX_CAND:
                    del lst[0]
            out.append(v)
            pos += 1

    return bytes(out)


def selftest(n_files=0):
    import os
    base = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
    if not os.path.isdir(base):
        return False
    files = sorted(f for f in os.listdir(base) if f.endswith(('.tob', '.sob')))[:20]
    ok = 0
    for f in files:
        raw = open(os.path.join(base, f), 'rb').read()
        c = compress(raw)
        d = decompress(c, len(raw))
        same = (d == raw)
        print('  %-16s %7d -> %7d (%.1f%%)  往返一致: %s' % (f, len(raw), len(c), 100.0 * len(c) / len(raw), same))
        ok += 1 if same else 0
    print('往返一致: %d/%d' % (ok, len(files)))
    return ok == len(files)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        print('=== LZSS 压缩器往返自检 ===')
        selftest()

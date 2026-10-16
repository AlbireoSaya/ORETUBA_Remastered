# -*- coding: utf-8 -*-
r"""逐 token 对比压缩器与解压器的窗口状态，定位首个不一致（ISSUE-ORETUBAR-R）。"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WIN, MASK, START, MIN_MATCH, MAX_MATCH = 4096, 4095, 0xFEE, 3, 18


def compress_traced(data):
    """与 lucifen_lzss.compress 同逻辑，但记录每个 token 及其执行后的窗口指纹。"""
    win = bytearray(WIN); ncur = START
    out = bytearray(); ctrl_pos = 0; ctrl_bit = 8
    n = len(data); pos = 0
    idx = {}; MAX_CAND = 24
    toks = []

    def new_group():
        nonlocal ctrl_pos, ctrl_bit
        ctrl_pos = len(out); out.append(0); ctrl_bit = 0

    while pos < n:
        if ctrl_bit == 8:
            new_group()
        best_len, best_off = 0, 0
        limit = min(MAX_MATCH, n - pos)
        if limit >= MIN_MATCH and pos > 0:
            need = data[pos:pos + limit]
            key = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
            for o in reversed(idx.get(key, [])):
                if win[o] != need[0]:
                    continue
                k = 1
                while k < limit and win[(o + k) & MASK] == need[k]:
                    k += 1
                if k > best_len:
                    best_len, best_off = k, o
                    if k == limit:
                        break
        if best_len >= MIN_MATCH:
            out.append(best_off & 0xFF)
            out.append(((best_off >> 4) & 0xF0) | ((best_len - MIN_MATCH) & 0x0F))
            ctrl_bit += 1
            src_vals = []
            for k in range(best_len):
                v = win[(best_off + k) & MASK]
                src_vals.append(v)
                npos = ncur
                win[ncur] = v
                ncur = (ncur + 1) & MASK
                j = pos + k
                if j + 3 <= n:
                    kk = data[j] | (data[j + 1] << 8) | (data[j + 2] << 16)
                    lst = idx.setdefault(kk, [])
                    lst.append(npos)
                    if len(lst) > MAX_CAND:
                        del lst[0]
            toks.append(('ref', pos, best_off, best_len, bytes(src_vals), ncur))
            pos += best_len
        else:
            out[ctrl_pos] |= (1 << ctrl_bit); ctrl_bit += 1
            v = data[pos]; npos = ncur
            win[ncur] = v; ncur = (ncur + 1) & MASK
            if pos + 3 <= n:
                kk = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
                lst = idx.setdefault(kk, [])
                lst.append(npos)
                if len(lst) > MAX_CAND:
                    del lst[0]
            out.append(v)
            toks.append(('lit', pos, v, 1, bytes([v]), ncur))
            pos += 1
    return bytes(out), toks


def decomp_traced(c, outlen):
    win = bytearray(WIN); ncur = START; act = 0
    out = bytearray(); i = 0; n = len(c); flag = 0
    toks = []
    while True:
        flag >>= 1
        if not (flag & 0x100):
            if i >= n: break
            flag = c[i] | 0xff00; i += 1
        if flag & 1:
            if i >= n: break
            v = c[i]; i += 1
            if act >= outlen: break
            win[ncur] = v; ncur = (ncur + 1) & MASK; out.append(v)
            toks.append(('lit', act, v, 1, bytes([v]), ncur)); act += 1
        else:
            if i + 1 >= n: break
            off = c[i]; ln = c[i + 1]; i += 2
            off |= (ln & 0xf0) << 4
            ln = (ln & 0x0f) + 3
            sv = bytearray()
            for k in range(ln):
                if act >= outlen:
                    return bytes(out), toks
                v = win[(off + k) & MASK]
                sv.append(v)
                win[ncur] = v; ncur = (ncur + 1) & MASK; out.append(v); act += 1
            toks.append(('ref', act - ln, off, ln, bytes(sv), ncur))
    return bytes(out), toks


def main():
    base = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
    name = sys.argv[1] if len(sys.argv) > 1 else 's01_01a.tob'
    raw = open(os.path.join(base, name), 'rb').read()
    c, ctoks = compress_traced(raw)
    d, dtoks = decomp_traced(c, len(raw))
    print('%s: %d -> %d ; 压缩 token %d / 解压 token %d' % (name, len(raw), len(c), len(ctoks), len(dtoks)))
    for i, (a, b) in enumerate(zip(ctoks, dtoks)):
        if a != b:
            print('首个不一致的 token #%d' % i)
            print('  压缩侧: type=%s 位置=%d 参数=%s 源字节=%s 游标后=0x%x' % (a[0], a[1], a[2:4], a[4].hex(), a[5]))
            print('  解压侧: type=%s 位置=%d 参数=%s 源字节=%s 游标后=0x%x' % (b[0], b[1], b[2:4], b[4].hex(), b[5]))
            print()
            print('  上下文（压缩侧前 5 个 token）:')
            for t in ctoks[max(0, i - 5):i + 2]:
                print('    ', t[0], 'pos=%d' % t[1], t[2:4], t[4].hex()[:40])
            print('  上下文（解压侧前 5 个 token）:')
            for t in dtoks[max(0, i - 5):i + 2]:
                print('    ', t[0], 'pos=%d' % t[1], t[2:4], t[4].hex()[:40])
            # 数据层面首个差异
            for k in range(min(len(d), len(raw))):
                if d[k] != raw[k]:
                    print()
                    print('  数据首个差异 @%d' % k)
                    break
            return
    print('token 级全部一致；数据一致:', d == raw)
    for i, (a, b) in enumerate(zip(ctoks, dtoks)):
        if a[0] == 'ref' and a[2] != b[2]:
            print('  第 %d 个 ref 的 off 不同: 压缩 %d vs 解压 %d' % (i, a[2], b[2]))
            break


if __name__ == '__main__':
    main()

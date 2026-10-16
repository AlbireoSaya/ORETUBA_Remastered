# -*- coding: utf-8 -*-
r"""定位 LZSS 往返失败的首个 token（ISSUE-ORETUBAR-R）。"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lucifen_lzss as L


def decomp_trace(c, outlen, stop_at=None):
    """解压并记录每个 token 的 (类型, 参数, 解出区间)，便于定位。"""
    win = bytearray(4096); ncur = 0xfee; act = 0
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
            toks.append(('lit', v, act, act + 1, ncur))
            win[ncur] = v; ncur = (ncur + 1) & 0xfff; out.append(v); act += 1
        else:
            if i + 1 >= n: break
            off = c[i]; ln = c[i + 1]; i += 2
            off |= (ln & 0xf0) << 4
            ln = (ln & 0x0f) + 3
            toks.append(('ref', (off, ln), act, act + ln, ncur))
            for k in range(ln):
                if act >= outlen:
                    return bytes(out), toks
                v = win[(off + k) & 0xfff]
                win[ncur] = v; ncur = (ncur + 1) & 0xfff; out.append(v); act += 1
    return bytes(out), toks


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 's01_01a.tob'
    base = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT'
    raw = open(os.path.join(base, name), 'rb').read()
    c = L.compress(raw)
    d, toks = decomp_trace(c, len(raw))
    print('文件 %s: %d -> %d -> %d' % (name, len(raw), len(c), len(d)))
    if d == raw:
        print('往返一致 ✔'); return
    # 找首个差异
    first = None
    for i, (a, b) in enumerate(zip(raw, d)):
        if a != b:
            first = i; break
    print('首个差异 @%d (0x%x)' % (first, first))
    print('  期望:', raw[max(0, first - 12):first + 20].hex())
    print('  实得:', d[max(0, first - 12):first + 20].hex())
    print()
    print('覆盖该位置的 token：')
    for t in toks:
        kind, param, a, b, ncur = t
        if a <= first < b or (a - 2 <= first < b + 2):
            print('  %-4s 输出区间[%d,%d) 写入游标起 0x%03x 参数=%s' % (kind, a, b, ncur, param))
            if kind == 'ref':
                off, ln = param
                src = bytes(((off + k) & 0xfff) for k in range(ln))
                print('        取窗口下标: %s' % src.hex())
                print('        该区间期望字节: %s' % raw[a:b].hex())
    print()
    print('前 8 个 token:')
    for t in toks[:8]:
        print('  ', t)


if __name__ == '__main__':
    main()

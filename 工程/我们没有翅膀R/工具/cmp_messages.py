# -*- coding: utf-8 -*-
r"""逐消息比对：原始 vs 重建，核对除被编辑者外正文完全一致（ISSUE-ORETUBAR-R）。"""
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_extract as EX

P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'


def messages(raw):
    """返回 [(k, 记录起, 记录止, 正文起, 正文止)]（文件坐标）。"""
    info = EX.parse_header(raw)
    cs, T, B = info['code_start'], info['T'], info['B']
    out = []
    for k in range(B):
        end = cs + T[k]
        start = end - 18
        # 正文 = start 之前的一串（由上一记录的结尾到 start）
        out.append((k, start, end, cs + (T[k - 1] if k > 0 else 0), start))
    return out, info


def main():
    orig = open(os.path.join(P, '临时', '_s01_02c_orig.tob'), 'rb').read()
    reb = open(os.path.join(P, '临时', '_s01_02c_rebuilt.tob'), 'rb').read()
    mo, io = messages(orig)
    mr, ir = messages(reb)
    print('消息数 原始 %d / 重建 %d' % (len(mo), len(mr)))
    # 编辑区间（原始坐标）
    mig = json.load(open(os.path.join(P, '语料', 'R版迁移映射.json'), encoding='utf-8'))
    new = json.load(open(os.path.join(P, '语料', '新增译文映射.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(P, '语料', '重编码映射.json'), encoding='utf-8'))
    F = 's01_02c.tob'
    edits = []
    for r in mig + new:
        if r['file'] != F:
            continue
        t = r.get('cn') or r.get('text') or ''
        if not t:
            continue
        try:
            b = t.encode('gbk')
        except Exception:
            continue
        edits.append((int(r['offset']), int(r['len']), b))
    for r in rec:
        if r['file'] != F:
            continue
        tb = r.get('text_bytes')
        b = bytes(tb) if isinstance(tb, list) else r.get('text_bytes_latin1', '').encode('latin-1')
        edits.append((int(r['offset']), int(r['len']), b))
    # 只保留落在「消息正文区间」内的编辑（用于判定该消息是否被改）
    def kind_of(off):
        for k, s, e, bs, be in mo:
            if bs <= off < be:
                return k
        return None

    mism = []
    for k in range(min(len(mo), len(mr))):
        _, sa, ea, bsa, bea = mo[k]
        _, sr, er, bsr, ber = mr[k]
        ta = orig[bsa:bea]
        tr = reb[bsr:ber]
        # 该消息的原始正文区间是否含编辑
        touched = any(bsa <= e[0] < bea for e in edits)
        if touched:
            continue
        if ta != tr:
            mism.append((k, bsa, bea, ta[:48], tr[:48]))
    print('未被编辑但正文不一致的消息: %d' % len(mism))
    for k, bsa, bea, ta, tr in mism[:15]:
        print('  消息 #%d 原始[%d,%d)' % (k, bsa, bea))
        print('     原: %r' % ta)
        print('     新: %r' % tr)


if __name__ == '__main__':
    main()

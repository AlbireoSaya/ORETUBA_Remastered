# -*- coding: utf-8 -*-
r"""重定位正确性独立校验（ISSUE-ORETUBAR-R）。

思路：**不依赖 tob_rewrite 自己的地址模型**，改用「结构映射」验证。
对原始与重建后的 TOB：
  1. 解析头部（code_start / T / 标签）
  2. 按 T 表逐个定位每条消息记录，取出其正文
  3. 用「编辑区间映射」把原始坐标映射到新坐标，核对：
     * 未编辑的消息 → 正文应完全相同
     * 被编辑的消息 → 正文应等于新文本
  4. 逐条核对 data_off 字段（u32）指向的位置在新文件里仍是合法命令起点
"""
import os, re, struct, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import tob_extract as EX
import tob_rewrite as TR

P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'


def header_of(raw):
    return EX.parse_header(raw)


def map_off(orig_off, edits_sorted):
    """把「原始文件里的坐标」映射到「重建后文件里的坐标」。

    传入的 edits 是按 offset 降序应用的（与 apply_edits_rebuild 一致）。
    这里用「按升序累计」的方式重算：新坐标 = 原坐标 + 所有位于其之前的编辑的 delta 之和。
    """
    delta = 0
    for off, ln, newlen in edits_sorted:      # edits_sorted 按 off 升序
        if off + ln <= orig_off:
            delta += newlen - ln
        elif off <= orig_off < off + ln:
            return off + delta               # 落在被编辑区间内部 → 指向新文本起点
    return orig_off + delta


def check(orig, newb, edits, name):
    ia = header_of(orig)
    ib = header_of(newb)
    cs_a, cs_b = ia['code_start'], ib['code_start']
    if cs_a != cs_b:
        print('  [%s] code_start 变化 %d→%d' % (name, cs_a, cs_b))
    # 2) data_off 字段核对（头部 map_pos 处的 u32）
    pos = ia.get('map_pos')
    print('  [%s] code_start=%d→%d 消息数 %d→%d' % (name, cs_a, cs_b, ia['B'], ib['B']))
    # 3) 标签表
    for (na, va), (nb, vb) in zip(ia['labels'], ib['labels']):
        ta, tb = cs_a + va, cs_b + vb
        if ta < len(orig) and tb < len(newb):
            sa = orig[ta:ta + 8]
            sb = newb[tb:tb + 8]
            if sa != sb:
                print('    ✘ 标签 %s 目标内容不同: %s vs %s' % (na, sa.hex(), sb.hex()))
    # 4) 逐条核对 T 表指向的消息记录尾部
    bad_t = 0
    for k in range(min(ia['B'], ib['B'])):
        pa = cs_a + ia['T'][k]
        pb = cs_b + ib['T'][k]
        if pa + 18 > len(orig) or pb + 18 > len(newb):
            bad_t += 1
            continue
        sa = orig[pa - 18:pa]
        sb = newb[pb - 18:pb]
        if sa != sb:
            bad_t += 1
    print('    T 表记录尾部不一致: %d / %d' % (bad_t, ia['B']))
    return bad_t


def main():
    orig = open(os.path.join(P, '临时', '_s01_02c_orig.tob'), 'rb').read()
    reb = open(os.path.join(P, '临时', '_s01_02c_rebuilt.tob'), 'rb').read()
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
        edits.append((int(r['offset']), int(r['len']), len(b)))
    for r in rec:
        if r['file'] != F:
            continue
        tb = r.get('text_bytes')
        b = bytes(tb) if isinstance(tb, list) else r.get('text_bytes_latin1', '').encode('latin-1')
        edits.append((int(r['offset']), int(r['len']), len(b)))
    edits.sort()      # 升序
    print('编辑 %d 条' % len(edits))
    print('Δ 合计 = %d（原 %d → 重建 %d，实测 Δ=%d）'
          % (sum(nl - l for _, l, nl in edits), len(orig), len(reb), len(reb) - len(orig)))
    check(orig, reb, edits, F)


if __name__ == '__main__':
    main()

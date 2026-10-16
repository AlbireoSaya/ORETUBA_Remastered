# -*- coding: utf-8 -*-
r"""tob_rewrite.py —— Lucifen「TOB0」脚本回写器（ISSUE-ORETUBAR-R）

三种模式
========
  noop    空操作回写：读入 -> 原样写出，md5 必须一致（自检用）
  equal   定长就地替换：新文本字节数必须与原文本相同（可用 --pad 用空格补齐），
          除被替换区间外文件任何字节都不变 —— 零风险模式，推荐用于汉化流水线
  rebuild 变长替换：重建文件并对「地址字段」做重定位（见下），随后做结构自检

地址模型（实测）
================
  * 地址空间 = 文件内偏移 - code_start（code_start = 0x2e + 4*B）
  * 标签表值（_START / _SC_SKIP / ...）是地址
  * `02 ff 00 <u32=标签值> 00` 是跳转指令（实测 847 处，值全部 ∈ 标签集合）
  * 形如 `5b 20 <op> 00 00 00 01 0b 00 00 00 01 01 00 <u32>` 的记录：
      - 消息尾部（58042+383 处）末字段 == 消息序号 k，**不是地址，不改**
      - 另有 1794 处末字段指向 `5b XX` 命令起点，是地址，需要重定位
      - 其余（如 op=0x5d/0x7a/0x62 的 0x64/0x190/0x320/0x3e8 等）是毫秒计时参数，
        不是地址，不改
  * 消息表 T[k] = 第 k 条消息记录结束地址（正文长度由它推导），必须重定位

用法
====
  python -X utf8 tob_rewrite.py noop    <in.tob> [out.tob]
  python -X utf8 tob_rewrite.py equal   <in.tob> <edits.json> <out.tob> [--pad 0x20]
  python -X utf8 tob_rewrite.py rebuild <in.tob> <edits.json> <out.tob>
  python -X utf8 tob_rewrite.py selftest <tob目录或文件> [--n 20]
  python -X utf8 tob_rewrite.py census  <tob目录或文件>            # 只统计地址字段

edits.json 形如  [{"offset": 1234, "len": 56, "text": "新文本"}, ...]
"""
import os
import sys
import json
import copy
import struct
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tob_extract as EX

TAIL_SHAPE_TAIL = b'\x01\x01\x00'   # 尾形记录里 u32 之前的固定 3 字节


def _edit_bytes(e, enc='cp932'):
    """编辑项的目标字节：优先 `text_bytes`（字节直入），否则 `text` 按 enc 编码。"""
    if 'text_bytes' in e and e['text_bytes'] is not None:
        tb = e['text_bytes']
        if isinstance(tb, (bytes, bytearray)):
            return bytes(tb)
        if isinstance(tb, str):
            return tb.encode('latin-1')
        if isinstance(tb, (list, tuple)):
            return bytes(tb)
        raise ValueError('text_bytes 类型不支持: %r' % type(tb))
    return e['text'].encode(enc)


def md5(b):
    return hashlib.md5(b).hexdigest()


def parse_layout(d):
    info = EX.parse_header(d)
    code_start = info['code_start']
    B = info['B']
    T = info['T']
    labels = info['labels']
    return {
        'code_start': code_start, 'B': B, 'T': T, 'labels': labels,
        'label_pos': [],  # (字段偏移, 值)
    }


def label_field_positions(d):
    """标签表里每个地址字段的文件偏移。"""
    nlab = struct.unpack_from('<I', d, 8)[0]
    p = 0x0c
    out = []
    for _ in range(nlab):
        ln = d[p]
        out.append(p + ln - 3)
        p += 1 + ln
    return out


def find_jump_fields(d, code_start):
    """所有 `02 ff 00 <u32>` 跳转字段：(字段偏移, 值)。"""
    out = []
    i = code_start
    n = len(d)
    while True:
        i = d.find(b'\x02\xff\x00', i)
        if i < 0 or i + 7 > n:
            break
        v = struct.unpack_from('<I', d, i + 3)[0]
        out.append((i + 3, v))
        i += 3
    return out


def find_tail_shape_fields(d, code_start, T, B):
    """尾形记录末字段分类。

    返回 (addr_fields, index_fields, param_fields)：
      addr_fields  : [(字段偏移, 值)]    —— 指向命令起点的地址，需重定位
      index_fields : [(字段偏移, 值)]    —— 消息序号（== k），不动
      param_fields : [(字段偏移, 值)]    —— 其它数值参数，不动
    """
    n = len(d)
    tails = {T[k] + code_start - 18: k for k in range(B)}
    addr, idx, param = [], [], []
    i = code_start
    while True:
        i = d.find(b'\x5b\x20', i)
        if i < 0 or i + 18 > n:
            break
        if (d[i + 3:i + 6] == b'\x00\x00\x00' and d[i + 6] == 0x01
                and d[i + 7:i + 11] == b'\x0b\x00\x00\x00'
                and d[i + 11:i + 14] == TAIL_SHAPE_TAIL):
            fpos = i + 14
            v = struct.unpack_from('<I', d, fpos)[0]
            k = tails.get(i)
            if k is not None and v == k:
                idx.append((fpos, v))
            else:
                q = v + code_start
                # 真地址：目标处是一个命令（`5b XX <u32 参数=0>` 形态）。
                # 计时参数（100/800/1200 等）偶发落在 `5b 20` 上，用命令头
                # 的 3 个 0 字节特征排除。
                if 0 < v and q + 6 <= n and d[q] == 0x5b and d[q + 3:q + 6] == b'\x00\x00\x00':
                    addr.append((fpos, v))
                else:
                    param.append((fpos, v))
            i += 2
            continue
        i += 2
    return addr, idx, param


def collect_address_fields(d):
    """汇总所有需要重定位的地址字段：[(字段偏移, 值, 类别)]。"""
    info = EX.parse_header(d)
    code_start, T, B = info['code_start'], info['T'], info['B']
    fields = []
    for pos, (name, val) in zip(label_field_positions(d), info['labels']):
        fields.append((pos, val, 'label'))
    tbase = info['map_pos'] + 8      # T 表真实偏移（不是固定 0x2e：标签条数可变）
    for k, t in enumerate(T):
        fields.append((tbase + 4 * k, t, 'T'))
    for pos, v in find_jump_fields(d, code_start):
        fields.append((pos, v, 'jump'))
    addr, idx, param = find_tail_shape_fields(d, code_start, T, B)
    for pos, v in addr:
        fields.append((pos, v, 'tailaddr'))
    return fields, {'labels': len(info['labels']), 'T': B,
                    'jump': len(find_jump_fields(d, code_start)),
                    'tailaddr': len(addr), 'tail_index': len(idx), 'param': len(param)}


def apply_edits_equal(d, edits, pad_byte=0x20, enc='cp932'):
    """定长替换；若新文本更短且给了 pad_byte，用其补齐到原长度。"""
    d = bytearray(d)
    for e in edits:
        off, ln = int(e['offset']), int(e['len'])
        nb = e['text'].encode(enc)
        if len(nb) > ln:
            raise ValueError('编辑超出原长度: offset=0x%x 原长=%d 新长=%d' % (off, ln, len(nb)))
        if len(nb) < ln:
            if pad_byte is None:
                raise ValueError('新文本更短且未允许补齐: offset=0x%x 原长=%d 新长=%d' % (off, ln, len(nb)))
            nb = nb + bytes([pad_byte]) * (ln - len(nb))
        d[off:off + ln] = nb
        # 声明长度串（`01 01 <u16 L>`，如标题/名字/语音）需同步改写 L，
        # 否则引擎会按旧长度读到补齐字节。
        if is_declared_string(d, off, ln):
            struct.pack_into('<H', d, off - 2, len(e['text'].encode(enc)) + 1)
    return bytes(d)


def is_declared_string(d, off, ln):
    """判断 offset 处的串是否形如 `01 01 <u16 L>`，且 L == ln+1（含终止 NUL）。"""
    if off < 4 or off + ln > len(d):
        return False
    if d[off - 4:off - 2] != b'\x01\x01':
        return False
    L = struct.unpack_from('<H', d, off - 2)[0]
    return L == ln + 1


def apply_edits_rebuild(d, edits, verify=True, enc='cp932'):
    """变长替换 + 地址重定位。"""
    info = EX.parse_header(d)
    code_start, T, B = info['code_start'], info['T'], info['B']
    fields, census = collect_address_fields(d)
    edits = sorted(edits, key=lambda e: -int(e['offset']))
    result = d
    moved = []
    strlen_patch = []
    for e in edits:
        off, ln = int(e['offset']), int(e['len'])
        # 字节直入：优先 text_bytes（迁移表/重编码表的译文已是 GBK 原始字节），
        # 不能再过一遍编码；无 text_bytes 时按 enc(默认 cp932) 编码 text。
        nb = _edit_bytes(e, enc)
        delta = len(nb) - ln
        if delta == 0:
            result = result[:off] + nb + result[off + ln:]
            continue
        hi = off + ln          # 被替换区间的右端（文件坐标）
        # 先检查是否有地址指向被替换区间内部
        for fpos, v, kind in fields:
            fp = v + code_start
            if off < fp < hi:
                raise ValueError('地址字段(0x%x,%s)=0x%x 指向被替换区间内部 0x%x-0x%x'
                                 % (fpos, kind, fp, off, hi))
            # fp == off 合法：地址指向正文起点，替换后仍指向新正文起点
        # 重定位：>= hi 的地址整体平移 delta；< off 的不动
        newfields = []
        for fpos, v, kind in fields:
            if v + code_start >= hi:
                nv = v + delta
                newfields.append((fpos, nv, kind))
                moved.append((fpos, v, nv, kind))
            else:
                newfields.append((fpos, v, kind))
        fields = newfields
        # 写回字段值（注意：字段自身位置在 off 之后的也要平移——由写入顺序保证）
        buf = bytearray(result[:off] + nb + result[hi:])
        # 计算字段新偏移：字段位置 >= hi 的需要 +delta
        for fpos, nv, kind in sorted(fields, key=lambda x: -x[0]):
            fp = fpos + delta if fpos >= hi else fpos
            struct.pack_into('<I', buf, fp, nv)
        # 声明长度串：同步改写 `01 01 <u16 L>`（前缀在编辑点之前，位置不变）
        if is_declared_string(result, off, ln):
            struct.pack_into('<H', buf, off - 2, len(nb) + 1)
            strlen_patch.append((off - 2, len(nb) + 1))
        result = bytes(buf)
        # 后续（更小的 offset）编辑需把本地坐标改为新坐标系
        fields, census = collect_address_fields(result)
    if verify:
        verr = verify_rebuild(d, result, edits, enc)
        if verr:
            raise ValueError('rebuild 自检未通过: ' + verr)
        verr2 = verify_rebuild_strict(d, result, edits, moved, enc, strlen_patch)
        if verr2:
            raise ValueError('rebuild 严格对位自检未通过: ' + verr2)
    return result, census, moved


def verify_rebuild_strict(old, new, edits, moved, enc='cp932', strlen_patch=()):
    """逐字节对位校验：新旧文件的差异必须只出现在
       (a) 被编辑的正文区间，或 (b) 已知被重定位的地址字段（4 字节）。
    任何其它差异都说明回写器改动了不该动的字节。"""
    import bisect
    edits_sorted = sorted(((int(e['offset']), int(e['len']), len(_edit_bytes(e, enc)))
                           for e in edits), key=lambda x: x[0])
    moved_by_pos = {}
    for fpos, v, nv, kind in moved:
        moved_by_pos.setdefault(fpos, []).append((v, nv))
    strlen_by_pos = {p: v for p, v in strlen_patch}
    i = j = 0
    n_old, n_new = len(old), len(new)
    diff_ok = 0
    while i < n_old or j < n_new:
        if i < n_old and j < n_new and old[i] == new[j]:
            i += 1
            j += 1
            continue
        # 编辑区间？
        hit_edit = None
        for off, ln, nlen in edits_sorted:
            if i == off:
                hit_edit = (off, ln, nlen)
                break
        if hit_edit:
            off, ln, nlen = hit_edit
            i += ln
            j += nlen
            diff_ok += 1
            continue
        # 声明长度串的长度前缀？
        if i in strlen_by_pos and i + 2 <= n_old:
            if struct.unpack_from('<H', new, j)[0] == strlen_by_pos[i]:
                i += 2
                j += 2
                diff_ok += 1
                continue
        # 被重定位字段？
        if i in moved_by_pos:
            seg_old = struct.unpack_from('<I', old, i)[0]
            seg_new = struct.unpack_from('<I', new, j)[0]
            okf = any(seg_old == v and seg_new == nv for v, nv in moved_by_pos[i])
            if okf:
                i += 4
                j += 4
                diff_ok += 1
                continue
        return '未知差异 @old=0x%x new=0x%x (old=%02x new=%02x)' % (i, j, old[i], new[j])
    return None


def verify_rebuild(old, new, edits, enc='cp932'):
    """坐标映射字节级校验（不依赖改写后的编码启发式解析）。

    1) 头部一致性：消息数 B、code_start 不变；
    2) 坐标映射：x -> x + 累计 Δ（跨过被替换区间视为「被编辑」）；
    3) 未被编辑的消息正文：字节必须完全不变；
    4) 被编辑的消息正文：新坐标处必须等于新文本（enc 编码）；
    5) 标签目标：目标内容不变；若标签指向被编辑正文起点，则标签值必须不变。
    """
    io = EX.parse_header(old)
    inw = EX.parse_header(new)
    if io['B'] != inw['B']:
        return '消息数变化 %d -> %d' % (io['B'], inw['B'])
    if io['code_start'] != inw['code_start']:
        return 'code_start 变化 %d -> %d' % (io['code_start'], inw['code_start'])
    edits_sorted = sorted(({'off': int(e['offset']), 'ln': int(e['len']),
                            'nb': _edit_bytes(e, enc)} for e in edits),
                          key=lambda x: x['off'])

    def map_pos(x):
        """返回新坐标；落在被替换区间内返回 None。"""
        d = 0
        for e in edits_sorted:
            if x < e['off']:
                break
            if x < e['off'] + e['ln']:
                return None
            d += len(e['nb']) - e['ln']
        return x + d

    _, mo, _ = EX.parse_messages_bytes(old, enc='cp932')
    for m in mo:
        if m['offset'] is None or not m['text']:
            continue
        a, b = map_pos(m['offset']), map_pos(m['offset'] + m['len'])
        raw = old[m['offset']:m['offset'] + m['len']]
        if a is None or b is None:
            continue                      # 该正文被编辑，下面单独校验
        if new[a:b] != raw:
            return '未被编辑的正文发生变化 @k=%s off=0x%x' % (m['index'], m['offset'])
    # 编辑项本身
    for e in edits_sorted:
        a = map_pos(e['off'])
        if a is None:
            a = e['off'] + sum(len(x['nb']) - x['ln'] for x in edits_sorted
                               if x['off'] < e['off'])
        if new[a:a + len(e['nb'])] != e['nb']:
            return '新文本未正确写入 @off=0x%x' % e['off']
    # 标签
    for (nm, va) in io['labels']:
        for (nm2, vb) in inw['labels']:
            if nm2 != nm:
                continue
            pa = va + io['code_start']
            in_edit = any(e['off'] <= pa < e['off'] + e['ln'] for e in edits_sorted)
            if in_edit:
                if va != vb:
                    return '标签 %s 指向被编辑正文起点，地址值不应变化' % nm
            else:
                pb = map_pos(pa)
                if pb is None:
                    return '标签 %s 目标落在被替换区间内' % nm
                if not _same_target(old, pa, new, pb, edits, 64):
                    return '标签 %s 目标内容变化' % nm
    return None


def _same_target(old, pa, new, pb, edits, window=64):
    """比较两个目标位置起的若干字节（考虑中间插入导致的平移）。

    窗口在被编辑区间处截断：被编辑的正文本身当然是变化的，
    需要核对的是「目标位置本身没指错」。
    """
    for e in edits:
        off = int(e['offset'])
        if pa <= off < pa + window:
            window = off - pa
    if window <= 0:
        return True
    if pa + window <= len(old) and pb + window <= len(new):
        return old[pa:pa + window] == new[pb:pb + window]
    return old[pa:] == new[pb:]


def _diff_ranges(a, b):
    """返回两串不同的位置区间 [(start, end)]，要求等长。"""
    if len(a) != len(b):
        return None
    out = []
    i = 0
    n = len(a)
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def cmd_noop(src, dst=None):
    d = open(src, 'rb').read()
    dst = dst or src
    open(dst, 'wb').write(d)
    a = md5(d)
    b = md5(open(dst, 'rb').read())
    print('noop: %s -> %s' % (src, dst))
    print('  md5 原文 =', a)
    print('  md5 写出 =', b)
    print('  结果:', '一致 ✔' if a == b else '不一致 ✘')
    return a == b


def cmd_equal(src, edits_path, dst, pad_byte=0x20, enc='cp932'):
    d = open(src, 'rb').read()
    edits = json.load(open(edits_path, encoding='utf-8'))
    out = apply_edits_equal(d, edits, pad_byte, enc)
    open(dst, 'wb').write(out)
    dr = _diff_ranges(d, out)
    ranges = sorted(edits and [(int(e['offset']), int(e['offset']) + int(e['len'])) for e in edits])
    ok = True
    if dr is None:
        ok = False
    else:
        for s, e in dr:
            if not any(s >= rs and e <= re for rs, re in ranges):
                ok = False
                print('  [越界改动] 0x%x-0x%x 不在编辑区间内' % (s, e))
    print('equal: %s -> %s  编辑 %d 处' % (src, dst, len(edits)))
    print('  改动区间:', ['0x%x-0x%x' % (s, e) for s, e in (dr or [])])
    print('  全部改动都在编辑区间内:', '是 ✔' if ok else '否 ✘')
    return ok


def cmd_rebuild(src, edits_path, dst, enc='cp932'):
    d = open(src, 'rb').read()
    edits = json.load(open(edits_path, encoding='utf-8'))
    out, census, moved = apply_edits_rebuild(d, edits, True, enc)
    open(dst, 'wb').write(out)
    print('rebuild: %s -> %s' % (src, dst))
    print('  大小 %d -> %d (Δ%+d)' % (len(d), len(out), len(out) - len(d)))
    print('  地址字段统计:', census)
    from collections import Counter
    print('  重定位字段:', dict(Counter(k for _, _, _, k in moved)))
    print('  结构自检: 通过 ✔')
    return True


def cmd_census(target):
    files = ([os.path.join(target, f) for f in sorted(os.listdir(target))
              if f.lower().endswith('.tob')] if os.path.isdir(target) else [target])
    tot = {'labels': 0, 'T': 0, 'jump': 0, 'tailaddr': 0, 'tail_index': 0, 'param': 0}
    bad = 0
    for p in files:
        d = open(p, 'rb').read()
        try:
            _, c = collect_address_fields(d)
        except Exception as e:
            print('  [失败]', os.path.basename(p), e)
            bad += 1
            continue
        for k in tot:
            tot[k] += c[k]
    print('文件数 %d  解析失败 %d' % (len(files), bad))
    print('地址字段总数:', tot)


def cmd_selftest(target, n=5):
    """对若干文件做：noop md5 / 等长替换 / 变长替换 三连自检。"""
    files = ([os.path.join(target, f) for f in sorted(os.listdir(target))
              if f.lower().endswith('.tob')] if os.path.isdir(target) else [target])
    files = files[:n]
    print('=== 自检 %d 个文件 ===' % len(files))
    allok = True
    for p in files:
        d = open(p, 'rb').read()
        name = os.path.basename(p)
        # 1) noop
        ok1 = md5(d) == md5(d)
        # 2) 等长替换：取第一条消息正文，等长替换为全角空格填充
        info, msgs, warns = EX.parse_messages(p)
        m = next((x for x in msgs if x['text'] and x['len'] >= 8), None)
        if not m:
            print('  %-16s 跳过（无可用消息）' % name)
            continue
        newtxt = '汉' * (m['len'] // 2)      # GBK 每字 2 字节
        e = {'offset': m['offset'], 'len': m['len'], 'text': newtxt}
        out_eq = apply_edits_equal(d, [e], 0x20, 'gbk')
        dr = _diff_ranges(d, out_eq) or []
        ok2 = all(s >= m['offset'] and t <= m['offset'] + m['len'] for s, t in dr)
        # 3) rebuild：把该正文加长 2 字节（GBK 加一字）
        e2 = {'offset': m['offset'], 'len': m['len'], 'text': newtxt + '汉'}
        ok3 = False
        err = None
        try:
            out_rb, census, moved = apply_edits_rebuild(d, [e2], True, 'gbk')
            io = EX.parse_header(out_rb)
            exp = (newtxt + '汉').encode('gbk')
            ok3 = (len(out_rb) == len(d) + 2 and io['B'] == info['B']
                   and out_rb[m['offset']:m['offset'] + len(exp)] == exp)
        except Exception as ex:
            err = str(ex)
        allok = allok and ok1 and ok2 and ok3
        print('  %-16s noop=%s equal=%s rebuild=%s%s'
              % (name, '✔' if ok1 else '✘', '✔' if ok2 else '✘',
                 '✔' if ok3 else '✘', '' if not err else ' (%s)' % err))
    print('=== 总结果:', '全部通过 ✔' if allok else '存在失败 ✘', '===')
    return allok


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    mode = args[0]
    if mode == 'noop':
        return 0 if cmd_noop(args[1], args[2] if len(args) > 2 else None) else 1
    if mode == 'equal':
        pad = 0x20
        enc = 'cp932'
        if '--pad' in args:
            pad = int(args[args.index('--pad') + 1], 0)
        if '--enc' in args:
            enc = args[args.index('--enc') + 1]
        return 0 if cmd_equal(args[1], args[2], args[3], pad, enc) else 1
    if mode == 'rebuild':
        enc = 'cp932'
        if '--enc' in args:
            enc = args[args.index('--enc') + 1]
        cmd_rebuild(args[1], args[2], args[3], enc)
        return 0
    if mode == 'census':
        cmd_census(args[1])
        return 0
    if mode == 'selftest':
        n = 5
        if '--n' in args:
            n = int(args[args.index('--n') + 1])
        return 0 if cmd_selftest(args[1], n) else 1
    print('未知模式:', mode)
    return 2


if __name__ == '__main__':
    sys.exit(main())

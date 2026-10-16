# -*- coding: utf-8 -*-
"""build_sob_cn.py —— 把译文写回 SOB0 脚本（ISSUE-20260917-14）

原理（依据引擎源码 `lucifen.cpp` 的读取语义）：
  SOB0 = [头部：若干映射表 + strings_start/strings_end] + [字节码] + [字符串池]
  字符串地址是**相对 header_end 的偏移**；引擎只在 `strings_start <= maps[4][addr] < strings_end`
  时才认定该指令引用文本 —— 故**新增字符串必须落在 [strings_start, strings_end) 区间内**。
  做法：把「被改动的字符串组」整体（含组头字节与选择支的附加串、以及串间的 2 字节分隔）
  追加到**字符串池末尾**，再把 `strings_end` 扩大同样的字节数，最后改写 maps[4] 的 value 指向新位置。
  —— 原文件其它字节一律不动（与原版等长性无关：本作 SOB0 无长度约束）。

用法：
  python -X utf8 build_sob_cn.py                 # 用 汉化\\剧情汉化\\*.jsonl 生成 汉化\\SCRIPT.CN.LPK
  python -X utf8 build_sob_cn.py --dry           # 只统计，不写 LPK
  python -X utf8 build_sob_cn.py --only s01_01a.sob
"""
import os
import re
import sys
import json
import struct
import argparse
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
TOOLS_R = HERE
sys.path.insert(0, TOOLS_R)
sys.path.insert(0, HERE)
import lpk_patch as LP            # noqa: E402
from extract_sob0 import parse_sob0, classify, read_nul  # noqa: E402

GAME = r'D:/Gal/壌偨偪偵梼偼側偄乣Prelude乣'
CN_DIR = os.path.join(PROJ, '汉化', '剧情汉化')
OUT_LPK = os.path.join(PROJ, '汉化', 'LPK', 'SCRIPT.LPK')
TEXT_CMDS = (0x01800000, 0x01700000)


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


def parse_header(d):
    table_size = u32(d, 4)
    table_end = table_size + 8
    off = 8
    maps = []
    while off < table_end:
        n = u32(d, off)
        off += 4
        m = {}
        for _ in range(n):
            m[u32(d, off)] = u32(d, off + 4)
            off += 8
        maps.append(m)
    strings_start = u32(d, off)
    strings_end = u32(d, off + 4)
    header_end = off + 8
    return dict(table_size=table_size, maps=maps, sstart=strings_start, send=strings_end,
                header_end=header_end, ssend_off=off + 4)


def group_bytes(d, header_end, sa, sstart, send):
    """返回 (组字节区间 (abs_start, abs_end), [ (text_abs_start, text_abs_end), ... ])。

    完全复刻 lucifen.cpp 的定位与「选择支附加串」遍历；串之间的 2 字节分隔原样保留。
    """
    A = sa + header_end
    p = A
    c = d[p]
    if c == 0:
        p += 3
    sel = 0
    if p < len(d):
        f = d[p]
        if f in (2, 3):
            p += 4
            sel = f - 1
    spans = []
    raw, np_ = read_nul(d, p)
    spans.append((p, np_ - 1))          # 正文字节区间（不含 NUL）
    end = np_
    for _ in range(sel):
        p2 = end + 2
        raw, np_ = read_nul(d, p2)
        spans.append((p2, np_ - 1))
        end = np_
    return (A, end), spans


def rebuild_group(d, gstart, gend, spans, newtexts):
    """按原文结构重建组字节：仅替换 spans 指定的正文区间。"""
    out = bytearray()
    cur = gstart
    for (ts, te), nt in zip(spans, newtexts):
        out += d[cur:ts]
        out += nt
        cur = te
    out += d[cur:gend]
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only')
    ap.add_argument('--lpk', action='store_true', help='同时输出打补丁的完整 LPK（严格命名 SCRIPT.LPK）')
    a = ap.parse_args()

    lp = LP.load(os.path.join(GAME, 'SCRIPT.LPK'))
    names = {n: num for n, num in lp['ents']}

    # 载入译文：script -> {addr: {idx: cn}}
    trans = {}
    for p in sorted(glob.glob(os.path.join(CN_DIR, '*.jsonl'))):
        sc = os.path.basename(p)[:-6]
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            if not r['cn'].strip():
                continue
            trans.setdefault(sc, {}).setdefault(r['addr'], {})[r['seq']] = r

    stat = dict(scripts=0, groups=0, slots=0, appended=0)
    edits = {}
    for sc, byaddr in sorted(trans.items()):
        if a.only and sc != a.only:
            continue
        if sc not in names:
            print('!! 脚本不在 LPK 中:', sc)
            continue
        d = bytearray(LP.read_entry(lp, sc)['plain'])
        h = parse_header(d)
        strmap = h['maps'][4]
        # 把译文按 (addr, idx) 归到组
        byidx = {}
        for addr, idxs in byaddr.items():
            for seq, r in idxs.items():
                byidx.setdefault(addr, {})[r['idx']] = r
        new_pool = bytearray()
        repoint = {}          # old_sa -> new_sa
        for addr, idxmap in sorted(byidx.items()):
            sa = strmap.get(addr)
            if sa is None or not (h['sstart'] <= sa < h['send']):
                print('!! 地址无字符串映射:', sc, hex(addr))
                continue
            (g0, g1), spans = group_bytes(d, h['header_end'], sa, h['sstart'], h['send'])
            if len(spans) != max(idxmap) + 1:
                print('!! 组内串数不符:', sc, hex(addr), len(spans), sorted(idxmap))
                continue
            newtexts, touched = [], False
            for i, (ts, te) in enumerate(spans):
                r = idxmap.get(i)
                if r is None:
                    newtexts.append(bytes(d[ts:te]))
                    continue
                body = r['cn'].encode('gbk')
                old = bytes(d[ts:te])
                # 结尾 $ 是引擎格式的一部分：以**原串末字节**为准（不依赖 td 标志）
                trailer = b'$' if old.endswith(b'$') else b''
                if r['kind'] == 'dialogue':
                    k = old.find(b'$&')
                    prefix = old[:k + 2] if k >= 0 else b''
                else:
                    prefix = b''
                newtexts.append(prefix + body + trailer)
                touched = True
                stat['slots'] += 1
            if not touched:
                continue
            nb = rebuild_group(d, g0, g1, spans, newtexts)
            new_sa = h['send'] + len(new_pool)
            new_pool += nb
            repoint[sa] = new_sa
            stat['groups'] += 1
        if not repoint:
            continue
        # 追加池 + 扩 strings_end + 改写 maps[4]
        d += new_pool
        struct.pack_into('<I', d, h['ssend_off'], h['send'] + len(new_pool))
        for k, v in list(strmap.items()):
            if v in repoint:
                strmap[k] = repoint[v]
        # 把 maps[4] 写回头部（maps 在头部中的位置需重新走一遍）
        off = 8
        for mi, m in enumerate(h['maps']):
            n = len(m)
            off += 4
            if mi == 4:
                for kk, vv in sorted(m.items()):
                    struct.pack_into('<II', d, off, kk, vv)
                    off += 8
            else:
                off += 8 * n
        edits[sc] = bytes(d)
        stat['scripts'] += 1
        stat['appended'] += len(new_pool)

    print('参与脚本 %d 个；改写字符串组 %d 个；译文槽 %d；追加池共 %d 字节'
          % (stat['scripts'], stat['groups'], stat['slots'], stat['appended']))
    if a.dry or not edits:
        print('（--dry 或无可写内容，未生成文件）')
        return
    # ① 松散 .sob（默认交付形态；与「新米汉化」的 SCRIPT_CHS 外挂目录同型，无 key 改名风险）
    loose = os.path.join(PROJ, '汉化', 'SCRIPT_CN')
    os.makedirs(loose, exist_ok=True)
    for name, data in sorted(edits.items()):
        open(os.path.join(loose, name), 'wb').write(data)
    print('① 松散脚本已写出: %s（%d 个 .sob）' % (loose, len(edits)))
    # ② 打补丁的完整 LPK —— 文件名必须是 SCRIPT.LPK（引擎按文件名派生 key，改名即解包错乱）
    if a.lpk:
        lpkdir = os.path.join(PROJ, '汉化', 'LPK')
        os.makedirs(lpkdir, exist_ok=True)
        out = os.path.join(lpkdir, 'SCRIPT.LPK')
        LP.patch(os.path.join(GAME, 'SCRIPT.LPK'), out, edits)
        print('② 打补丁 LPK: %s（%d 字节，改动条目 %d）——目录内文件名必须保持 SCRIPT.LPK'
              % (out, os.path.getsize(out), len(edits)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
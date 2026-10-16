#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_23_chrsprite.py — 只读取出指定角色立绘并转 PNG (源只读; 产物只落本模块目录).

用途: 给「PC 立绘落位」一个可复算的实机几何 —— 取立绘位图与其原点(offset_x/offset_y),
      再对 baseline.png 做模板匹配, 反解引擎实际写入的 x。

依赖(只读 import, 不修改):
  工具\\lucifen\\Lucifen-Tools\\lpk_extractor.py  (LPK1 解析 / LZSS / 两层解密)
  工具\\lucifen\\Lucifen-Tools\\elg2png.py        (ELG 解码)

用法:
  python -X utf8 _probe_23_chrsprite.py --list ASU02 MAS01
  python -X utf8 _probe_23_chrsprite.py --extract ASU02A MAS01C
"""
import argparse
import json
import mmap
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ELGTOOLS = r"E:\ZCode Workspace\Galgame\工具\lucifen\Lucifen-Tools"
sys.path.insert(0, ELGTOOLS)

import lpk_extractor as X  # noqa: E402

LPKPATH = r"E:\ZCode Workspace\Galgame\临时\layer_exp\game\CHR.LPK"
# LPK-Keys.json 的 "Ore-tachi ni Tsubasa wa Nai".CHR.LPK
AUX = (2358782922, 1186745565)


def open_lpk(path, aux=AUX):
    f = open(path, "rb")
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    base = os.path.splitext(os.path.basename(path))[0]
    base_sjis = base.encode("cp932", errors="ignore")
    k1, k2 = X.BASE_KEY1, X.BASE_KEY2
    for i in range(len(base_sjis)):
        b = base_sjis[i]
        e = base_sjis[len(base_sjis) - 1 - i]
        k1 ^= e
        k2 ^= b
        k1 = X.rotr32(k1, 7)
        k2 = X.rotl32(k2, 7)
    k1 ^= aux[0]
    k2 ^= aux[1]
    header_x = struct.unpack_from("<I", mm, 4)[0] ^ k2
    flags = (header_x >> 24) & 0xFF
    table_size = header_x & 0xFFFFFF
    if flags & X.ALIGNED_OFFSET:
        table_size = (table_size << 11) - 8
    table = bytearray(mm[8:8 + table_size])
    X.decrypt_table(table, k2, X.ROTATE_PATTERN)
    off = 0
    file_count = struct.unpack_from("<I", table, off)[0]
    off += 4
    prefix_len = table[off]
    off += 1
    prefix = table[off:off + prefix_len]
    off += prefix_len
    offset_size = 4 if table[off] != 0 else 2
    off += 1
    ltlen = struct.unpack_from("<I", table, off)[0]
    off += 4
    entries_off = off + ltlen
    entry_size = 13 if (flags & X.IS_COMPRESSED) else 9
    minis = X.traverse_index(table, off, offset_size, entries_off, entry_size)
    ents = []
    for pos, name in minis:
        p = pos
        ef = 0
        if entry_size & 1:
            ef = table[p]
            p += 1
        o = struct.unpack_from("<I", table, p)[0]
        p += 4
        if flags & X.ALIGNED_OFFSET:
            o <<= 11
        sc = struct.unpack_from("<I", table, p)[0]
        p += 4
        so = sc
        if flags & X.IS_COMPRESSED:
            so = struct.unpack_from("<I", table, p)[0]
        ents.append((name, ef, o, sc, so))
    return dict(mm=mm, f=f, k1=k1, k2=k2, flags=flags, table=table, prefix=prefix,
                file_count=file_count, ents=ents, entry_size=entry_size)


def get_entry(lp, name):
    for n, ef, o, sc, so in lp['ents']:
        if n.upper() == name.upper():
            chunk = bytearray(lp['mm'][o:min(o + sc, len(lp['mm']))])
            if lp['flags'] & X.IS_COMPRESSED:
                chunk = X.lzss_decompress(bytes(chunk), so)
            if lp['flags'] & X.IS_ENCRYPTED2:
                X.decrypt_content_2_full(chunk, X.CONTENT_XOR)
            if lp['flags'] & X.IS_ENCRYPTED1:
                X.decrypt_content_1_first_256(chunk, lp['k1'], X.ROTATE_PATTERN)
            if lp['prefix']:
                chunk = bytearray(lp['prefix']) + chunk
            return bytes(chunk)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lpk", default=LPKPATH)
    ap.add_argument("--list", nargs="*", default=None)
    ap.add_argument("--extract", nargs="*", default=None)
    ap.add_argument("--outdir", default="_chr")
    a = ap.parse_args()

    lp = open_lpk(a.lpk)
    names = [n for n, *_ in lp['ents']]
    print("LPK=%s file_count=%d ents=%d flags=0x%X entry_size=%d prefix=%r" %
          (os.path.basename(a.lpk), lp['file_count'], len(names), lp['flags'],
           lp['entry_size'], lp['prefix']))

    if a.list is not None:
        want = [w.upper() for w in a.list] or [""]
        hit = [n for n in names if any(w in n.upper() for w in want)]
        print("-- match %d --" % len(hit))
        for n in hit[:100]:
            print("   ", n)

    if a.extract:
        od = os.path.join(HERE, a.outdir)
        os.makedirs(od, exist_ok=True)
        for w in a.extract:
            cand = [n for n in names if n.upper() == w.upper()] or \
                   [n for n in names if w.upper() in n.upper()]
            if not cand:
                print("!! not found:", w)
                continue
            nm = cand[0]
            raw = get_entry(lp, nm)
            p = os.path.join(od, nm.replace("\\", "_") + ".elg")
            open(p, "wb").write(raw)
            hdr = raw[:32].hex(" ")
            print("extracted %-16s %8d bytes  hdr=%s" % (nm, len(raw), hdr))
            try:
                import elg2png
                for fname in ("decode", "elg_to_image", "elg_to_pil", "main"):
                    pass
                print("   elg2png funcs:", [f for f in dir(elg2png) if not f.startswith("_")][:20])
            except Exception as e:
                print("   elg2png import err:", e)


if __name__ == "__main__":
    main()

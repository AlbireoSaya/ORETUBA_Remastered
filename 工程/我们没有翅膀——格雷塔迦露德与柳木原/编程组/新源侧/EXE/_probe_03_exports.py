#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_03_exports.py — 只读 PE 导出表转储 (用于判 DS_SPRITE.DLL / tvpgl.dll 的真实身份).

用法: python -X utf8 _probe_03_exports.py <path> [<path> ...]
只读; 不写任何文件.
"""
import struct
import sys


def parse_exports(path):
    with open(path, "rb") as f:
        d = f.read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    assert d[e:e + 4] == b"PE\0\0"
    coff = e + 4
    machine, nsec, ts, psym, nsym, size_opt, chars = struct.unpack_from("<HHIIIHH", d, coff)
    opt = coff + 20
    magic = struct.unpack_from("<H", d, opt)[0]
    is64 = magic == 0x20B
    imgbase = struct.unpack_from("<I", d, opt + 28)[0]
    ndd_off = opt + (112 if is64 else 92)
    ddir_off = opt + (112 if is64 else 96)
    n_ddir = struct.unpack_from("<I", d, ndd_off)[0]
    sec_off = opt + size_opt
    secs = []
    for i in range(nsec):
        o = sec_off + 40 * i
        nm = d[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
        secs.append((nm, vaddr, vsize, rawptr, rawsize))

    def rva2off(rva):
        for nm, vaddr, vsize, rawptr, rawsize in secs:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                delta = rva - vaddr
                return rawptr + delta if delta < rawsize else None
        return None

    out = {"machine": machine, "imgbase": imgbase, "sections": secs, "names": [], "dllname": None}
    if n_ddir < 1:
        return out
    exp_rva, exp_sz = struct.unpack_from("<II", d, ddir_off)
    if exp_rva == 0:
        return out
    o = rva2off(exp_rva)
    # IMAGE_EXPORT_DIRECTORY
    (chardata, tds, major, minor, name_rva, ordinal_base, nfunc, nname,
     addr_funcs, addr_names, addr_ordu) = struct.unpack_from("<IIHHIIIIIII", d, o)
    nb = rva2off(name_rva)
    out["dllname"] = d[nb:d.find(b"\0", nb)].decode("latin1")
    nto = rva2off(addr_names)
    oto = rva2off(addr_ordu)
    fto = rva2off(addr_funcs)
    for i in range(nname):
        nr = struct.unpack_from("<I", d, nto + 4 * i)[0]
        ordi = struct.unpack_from("<H", d, oto + 2 * i)[0]
        frva = struct.unpack_from("<I", d, fto + 4 * ordi)[0]
        no = rva2off(nr)
        nm = d[no:d.find(b"\0", no)].decode("latin1")
        out["names"].append((nm, ordinal_base + ordi, imgbase + frva))
    out["nfunc"] = nfunc
    out["ordinal_base"] = ordinal_base
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("=" * 70)
        print("FILE:", p)
        try:
            r = parse_exports(p)
        except Exception as ex:
            print("  !! parse error:", ex)
            continue
        print("  machine=0x%04X imgbase=0x%08X" % (r["machine"], r["imgbase"]))
        print("  sections:", [(s[0], hex(s[1]), hex(s[2])) for s in r["sections"]])
        print("  export dllname:", r.get("dllname"), " nfunc:", r.get("nfunc"), "ordbase:", r.get("ordinal_base"))
        print("  exported names (%d):" % len(r["names"]))
        for nm, ordv, va in r["names"]:
            print("    %-40s ord=%-5d va=0x%08X" % (nm, ordv, va))

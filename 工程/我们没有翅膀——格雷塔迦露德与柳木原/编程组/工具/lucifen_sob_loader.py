import struct
import hashlib

class InvalidSource(ValueError):
    pass

class NonContainer(InvalidSource):
    pass

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse_container(data, name="fixture.sob"):
    """Six relocation tables store replacement values, NOT disk-word equality."""
    def u32(off, limit=None):
        if off < 0 or off+4 > (len(data) if limit is None else limit):
            raise InvalidSource(f"{name}: truncated u32 at {off}")
        return struct.unpack_from("<I", data, off)[0]
    magic = data[:4]
    if magic == b"SOB1":
        raise NonContainer(f"{name}: SOB1 variable declarations, not a code container")
    if magic not in (b"SOB0", b"SOB2"):
        raise InvalidSource(f"{name}: unsupported magic {magic!r}")
    table_end = 8+u32(4)
    if table_end+8 > len(data):
        raise InvalidSource(f"{name}: table boundary outside file")
    cursor, maps = 8, []
    for ti in range(6):
        count = u32(cursor, table_end); cursor += 4
        if count > (table_end-cursor)//8:
            raise InvalidSource(f"{name}: truncated table {ti}")
        table = {}
        for _ in range(count):
            key, value = u32(cursor, table_end), u32(cursor+4, table_end); cursor += 8
            if key in table:
                raise InvalidSource(f"{name}: duplicate relocation site {key} in table {ti}")
            table[key] = value
        maps.append(table)
    if cursor != table_end:
        raise InvalidSource(f"{name}: six-table length mismatch")
    ss, se = u32(table_end), u32(table_end+4)
    header = table_end+8
    if ss % 4 or ss > se or header+se != len(data):
        raise InvalidSource(f"{name}: invalid code/data/file boundaries")
    if maps[5]:
        raise InvalidSource(f"{name}: nonempty table5 (loader rejects)")
    used = set()
    for ti, table in enumerate(maps):
        for key in table:
            if (key < ss and key % 4) or key+4 > se or key in used:
                raise InvalidSource(f"{name}: unaligned/outside/ambiguous relocation key {key}")
            used.add(key)
    return {"name":name, "magic":magic.decode(), "hash":sha(data), "bytes":len(data),
            "header":header, "ss":ss, "se":se, "maps":maps,
            "cells":list(struct.unpack_from(f"<{ss//4}I",data,header)), "data":data}


def relocate_buffer(buf, maps, code_bytes, base, funcbase, vectors):
    n = len(buf)
    if len(maps) != 6 or len(vectors) != 3:
        raise ValueError("need exactly 6 tables and 3 vectors")
    if not (isinstance(code_bytes, int) and not isinstance(code_bytes, bool)
            and 0 <= code_bytes <= n and code_bytes % 4 == 0):
        raise ValueError("bad code_bytes")
    if maps[5]:
        raise ValueError("table5 must be empty")

    def u32(x):
        return isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 0xffffffff

    if not u32(base) or not u32(funcbase):
        raise ValueError("invalid base/funcbase: not u32")
    for vs in vectors:
        if not isinstance(vs, list) or any(not u32(v) for v in vs):
            raise ValueError("bad vectors")
    out, trace, seen = bytearray(buf), [], set()
    for ti, tb in enumerate(maps):
        if not isinstance(tb, dict):
            raise ValueError("table must be a dict")
        for site, val in tb.items():
            if not u32(site) or site + 4 > n:
                raise ValueError("bad site")
            if site < code_bytes and site % 4:
                raise ValueError("misaligned code site")
            if site in seen:
                raise ValueError("duplicate site")
            seen.add(site)
            if not u32(val):
                raise ValueError("bad value")
            if ti < 3:
                if val >= len(vectors[ti]):
                    raise ValueError("index out of range")
                new = vectors[ti][val]
            elif ti == 3:
                new = (funcbase + val) & 0xffffffff
            else:
                new = (base + val) & 0xffffffff
            old = int.from_bytes(out[site:site + 4], "little")
            out[site:site + 4] = new.to_bytes(4, "little")
            trace.append({"table": ti, "site": site, "old": old, "new": new})
    return out, trace


import struct

def parse_sob1(data):
    buf, p, n = bytes(data), 0, len(data)

    def need(k):
        if k < 0 or p + k > n:
            raise ValueError("truncated")

    need(4)
    if buf[:4] != b"SOB1":
        raise ValueError("bad magic")
    p = 4
    need(4); idsize = struct.unpack_from("<I", buf, p)[0]; p += 4
    need(idsize); initial_data = buf[p:p + idsize]; p += idsize
    need(4); count = struct.unpack_from("<I", buf, p)[0]; p += 4
    need(count * 10)
    records = []
    for i in range(count):
        t, f, off, ex = struct.unpack_from("<BBII", buf, p)
        if off >= idsize:
            raise ValueError("record offset out of range")
        records.append({"index": i, "type": t, "flags": f, "offset": off,
                        "extra": ex, "fileoffset": p})
        p += 10
    need(4); rcount = struct.unpack_from("<I", buf, p)[0]; p += 4
    need(rcount * 8)
    relocs = {}
    for _ in range(rcount):
        site, val = struct.unpack_from("<II", buf, p)
        if site + 4 > idsize:
            raise ValueError("relocation site out of range")
        if site in relocs:
            raise ValueError("duplicate relocation site")
        relocs[site] = val
        p += 8
    tail = p
    need(4); reserved = struct.unpack_from("<I", buf, p)[0]; p += 4
    if reserved != 0:
        raise ValueError("reserved_count nonzero")
    if p != n:
        raise ValueError("trailing bytes")
    return {"initial_data": initial_data, "records": records, "local_relocations": relocs,
            "initial_data_fileoffset": 8, "tail_fileoffset": tail, "bytes": n}

import struct

def bind_sob1(decl, base, arraybase):
    for n in (base, arraybase):
        if isinstance(n, bool) or not isinstance(n, int) or not (0 <= n <= 0xffffffff):
            raise ValueError("base/arraybase must be non-bool uint32")
    data = bytearray(decl["initial_data"])
    for site, off in decl["local_relocations"].items():
        struct.pack_into("<I", data, site, (base + off) & 0xffffffff)
    va, slots = [], []
    for r in decl["records"]:
        if r["type"] == 1:
            slots.append((base + r["offset"]) & 0xffffffff)
            va.append((arraybase + (len(slots) - 1) * 4) & 0xffffffff)
        else:
            va.append((base + r["offset"]) & 0xffffffff)
    return {"data": data, "variable_addresses": va, "array_slots": slots, "records": decl["records"]}

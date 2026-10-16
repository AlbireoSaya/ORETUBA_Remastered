#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applique / あっぷりけ 自定义 XP3 归档（"compressed XP3" 变体）只读解析工具
纯标准库。事实依据见 报告.md。

实测格式 (CrossConcerto / tsukikage, 12 个 .xp3 全部一致):

文件头 (88 字节 = 0x58):
  0x00  u8[11]  魔数 58 50 33 0D 0A 20 0A 1A 8B 67 01  ("XP3\r\n \n\x1a\x8b\x67\x01")
  0x0B  u32     常量 0x17 (=23)         [含义未确认, 所有归档恒定]
  0x0F  u32     常量 0
  0x13  u32     常量 1
  0x17  u32     常量 0x80 (=128)
  0x1B  u8[5]   全 0
  0x20  u32     V = 索引块起始偏移 (唯一随文件变化的数据字段)
  0x24  u32     0
  0x28  u8[48]  伪 PNG 头 (89 50 4E 47 0A 1A 0A 00 ... "Warning\0")  [诱饵/水印]
  0x58          第一个文件数据起点
  V             索引块起点, V = filesize - 17 - zlib_compressed_size

索引块 (在 V 处):
  u8  mode = 1
  u64 csize   (zlib 压缩数据长度)
  u64 usize   (解压后长度)
  u8[csize]   zlib 流 (78 DA ...)

解压后的索引 = 顺序记录序列, 每条记录 = chunk(tag u8[4], u64 size, payload):

  记录0: tag 'Hxv4'  payload 14 字节 = u64 ?, u32 ?, u16 ? (未确认)
  记录n: tag 'File'  payload = 3 个子 chunk:
     'adlr' u64=4  -> u32 adler32(未压缩文件数据)
     'segm' u64=28 -> u32 mode (0=原样存储, 1=zlib压缩)
                      u64 offset (文件内绝对偏移)
                      u64 usize  (解压后大小)
                      u64 csize  (存储大小 = zlib 流长度)
     'info' u64=?  -> u32 flags (0x80000000)
                      u64 usize
                      u64 csize
                      u16 namelen (UTF-16 字符数)
                      u8[namelen*2] name (UTF-16LE)
                      u8[0..3] 对齐填充

  注意: 除 'startup.tjs' 外, 所有条目名均被写入方替换为连续占位名
        U+5000 + (记录序号-1)  (即 倀 倁 倂 ...), 真实文件名已从归档中剥离。
"""
import os, sys, struct, zlib

MAGIC = bytes.fromhex("5850330d0a200a1a8b6701")

class Entry:
    __slots__ = ("index","name","mode","offset","usize","csize","adler","tag")
    def __repr__(self):
        return "<Entry #%d %r mode=%d off=0x%x usize=%d csize=%d>" % (
            self.index, self.name, self.mode, self.offset, self.usize, self.csize)

def read_header(path):
    size = os.path.getsize(path)
    with open(path, "rb") as fp:
        h = fp.read(0x28)
    if h[:11] != MAGIC:
        raise ValueError("bad magic: %s" % h[:11].hex())
    v = struct.unpack_from("<I", h, 0x20)[0]
    consts = (struct.unpack_from("<I", h, 0x0B)[0],
              struct.unpack_from("<I", h, 0x0F)[0],
              struct.unpack_from("<I", h, 0x13)[0],
              struct.unpack_from("<I", h, 0x17)[0],
              h[0x1B:0x20].hex(), struct.unpack_from("<I", h, 0x24)[0])
    return size, v, consts, h

def _subchunks(pay):
    p, r = 0, {}
    while p + 12 <= len(pay):
        tag = pay[p:p+4]
        sz = struct.unpack_from("<Q", pay, p+4)[0]
        if p + 12 + sz > len(pay):
            break
        r[tag] = pay[p+12:p+12+sz]
        p += 12 + sz
    return r

def load_index(path):
    """返回 (size, V, consts, entries, raw_index_bytes)"""
    size, v, consts, _ = read_header(path)
    with open(path, "rb") as fp:
        fp.seek(v)
        mode = fp.read(1)[0]
        csize, usize = struct.unpack("<QQ", fp.read(16))
        blob = fp.read(csize)
    if mode != 1:
        raise ValueError("index mode %d != 1" % mode)
    out = zlib.decompress(blob)
    if len(out) != usize:
        raise ValueError("index usize mismatch %d != %d" % (len(out), usize))
    entries, p, idx = [], 0, 0
    while p + 12 <= len(out):
        tag = out[p:p+4]
        sz = struct.unpack_from("<Q", out, p+4)[0]
        if p + 12 + sz > len(out):
            raise ValueError("index record overrun at 0x%x" % p)
        pay = out[p+12:p+12+sz]
        if tag == b"File":
            d = _subchunks(pay)
            seg, inf = d.get(b"segm"), d.get(b"info")
            if seg and inf and len(seg) == 28:
                emode, off, us, cs = struct.unpack("<IQQQ", seg)
                flags, ius, ics = struct.unpack_from("<IQQ", inf, 0)
                nlen = struct.unpack_from("<H", inf, 20)[0]
                nm = inf[22:22+2*nlen].decode("utf-16le", "replace")
                adl = struct.unpack_from("<I", d.get(b"adlr", b"\0\0\0\0"), 0)[0] if b"adlr" in d else 0
                e = Entry(); e.index = idx; e.name = nm; e.mode = emode
                e.offset = off; e.usize = us; e.csize = cs; e.adler = adl; e.tag = tag
                entries.append(e)
        p += 12 + sz
        idx += 1
    return size, v, consts, entries, out

def extract(path, e):
    with open(path, "rb") as fp:
        fp.seek(e.offset)
        raw = fp.read(e.csize)
    data = zlib.decompress(raw) if e.mode == 1 else raw
    return data

def sniff(b):
    if b[:7] == b"TJS2100": return "TJS2-compiled"
    if b[:4] == b"\x89PNG": return "PNG"
    if b[:3] == b"\xff\xd8\xff": return "JPEG"
    if b[:4] == b"OggS": return "Ogg"
    if b[:4] == b"RIFF": return "RIFF/WAV"
    if b[:4] == b"FORM" and b[8:12] == b"AIFF": return "AIFF"
    if b[:3] == b"ID3" or b[:2] == b"\xff\xfb": return "MP3"
    if b[:4] == b"@UTF": return "CSV(@UTF?)"
    if b[:2] == b"\xfe\xff" or b[:2] == b"\xff\xfe": return "UTF-16 text"
    if b[:4] == b"PSB\0" or b[:4] == b"PSB\x00": return "PSB"
    if b[:4] == b"BM\x00\x00" or b[:2] == b"BM": return "BMP"
    # text heuristics
    try:
        t = b[:400].decode("cp932")
        printable = sum(1 for c in t if c.isprintable() or c in "\r\n\t")
        if printable / max(1, len(t)) > 0.9:
            return "ShiftJIS-text"
    except Exception:
        pass
    try:
        t = b[:400].decode("utf-8")
        printable = sum(1 for c in t if c.isprintable() or c in "\r\n\t")
        if printable / max(1, len(t)) > 0.9:
            return "UTF8-text"
    except Exception:
        pass
    return "unknown"

def cmd_info(argv):
    for p in argv:
        size, v, consts, entries, raw = load_index(p)
        print("== %s" % p)
        print("   size=%d  index_off V=%d (0x%x)  index_usize=%d  records=%d"
              % (size, v, v, len(raw), len(entries) + 1))
        print("   header consts: 0x0B=%#x 0x0F=%#x 0x13=%#x 0x17=%#x 0x1B5=%s 0x24=%#x"
              % consts)
        named = [e for e in entries if len(e.name) > 1]
        print("   named entries: %d -> %s" % (len(named), [e.name for e in named[:20]]))

def cmd_list(argv):
    p = argv[0]
    size, v, consts, entries, raw = load_index(p)
    print("# %s  entries=%d" % (p, len(entries)))
    print("# idx\tname\tmode\toffset\tsize\tcsize")
    for e in entries:
        print("%d\t%s\t%d\t%d\t%d\t%d" % (e.index, e.name, e.mode, e.offset, e.usize, e.csize))

def cmd_sniff(argv):
    p = argv[0]
    limit = int(argv[1]) if len(argv) > 1 else 10**9
    size, v, consts, entries, raw = load_index(p)
    from collections import Counter
    c = Counter()
    for e in entries[:limit]:
        try:
            d = extract(p, e)
            s = sniff(d)
            if s == "ShiftJIS-text" and b"\x40" not in d[:50]:
                pass
        except Exception as ex:
            s = "ERR:%s" % ex
        c[s] += 1
        e.sniff = s
    for k, n in c.most_common():
        print("%8d  %s" % (n, k))

def cmd_dump(argv):
    """dump <xp3> <first> <count> <outdir>"""
    p, first, count, outdir = argv[0], int(argv[1]), int(argv[2]), argv[3]
    size, v, consts, entries, raw = load_index(p)
    os.makedirs(outdir, exist_ok=True)
    for e in entries[first:first+count]:
        d = extract(p, e)
        s = sniff(d)
        name = "%06d_%s_%s" % (e.index, s.replace("/", "_"), e.name.encode("unicode_escape").decode())
        if "." not in e.name:
            name += "." + s.replace("ShiftJIS-text", "txt").replace("TJS2-compiled", "tjsb").replace("unknown", "bin")
        with open(os.path.join(outdir, name), "wb") as f:
            f.write(d)
        print("%-60s %8d bytes  %s" % (name, len(d), s))

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd, args = sys.argv[1], sys.argv[2:]
    {"info": cmd_info, "list": cmd_list, "sniff": cmd_sniff, "dump": cmd_dump}[cmd](args)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xp3pack.py —— 标准 KiriKiri XP3 归档 打包 / 解包 / 检视 工具
（纯 Python 标准库，无第三方依赖；Python 3.8+）

======================================================================
格式依据
======================================================================
本工具完全按 krkrz 1.4.0r2 官方源码实现，未参考任何私有变体：

  * 魔数 / 归档偏移探测：base/XP3Archive.cpp  TVPGetXP3ArchiveOffset()
        11 字节魔数 = 58 50 33 0D 0A 20 0A 1A 8B 67 01
                       "X  P  3  \\r \\n ' ' \\n \\x1a \\x8b g \\x01"
  * 头部：[0x00] magic(11) + [0x0B] u64 index_offset（小端）
  * 索引块（位于 index_offset）：
        u8  index_flag
            bit[0:2] = 编码方式  (base/XP3Archive.h)
                TVP_XP3_INDEX_ENCODE_METHOD_MASK = 0x07
                TVP_XP3_INDEX_ENCODE_RAW          = 0   原样
                TVP_XP3_INDEX_ENCODE_ZLIB         = 1   zlib
            bit[7]   = TVP_XP3_INDEX_CONTINUE = 0x80
                       置位表示「本块之后紧跟下一个 u64 index_offset，
                       还要继续读下一块索引」
        若编码 = zlib : u64 compressed_size, u64 raw_size, zlib 流
        若编码 = raw  : u64 raw_size, 原始字节
  * 索引内容 = 若干个 chunk 顺序拼接；chunk = tag(4) + u64 size + payload
        顶层 chunk：'File'（每个文件一条，可多条连续）
        'File' 内部子 chunk：
            'info' : u32 flags        （bit31 = TVP_XP3_FILE_PROTECTED）
                     u64 original_size     （完整文件原始大小）
                     u64 archived_size     （在归档中占用的字节数）
                     u16 name_length       （UTF-16 码元数，即字符数）
                     UTF-16LE name         （name_length * 2 字节，无 BOM）
            'segm' : 每 28 字节一条分段记录，可多条
                     u32 flags     （bit[0:2]：0=原样 1=zlib）
                     u64 offset    （分段数据在归档文件内的绝对偏移）
                     u64 original_size
                     u64 archived_size
            'adlr' : u32 adler32（完整文件原始数据的 adler32）

  注：引擎读取时对条目名做 NormalizeInArchiveStorageName()
      （全部转小写、'\\' 转 '/'、压缩重复斜杠）；本工具打包时
      直接按该规范写入小写 + '/' 分隔的名字。

======================================================================
命令
======================================================================
  pack    <源目录> <输出.xp3> [--store] [--raw-index] [--include RE] [--exclude RE]
  list    <归档.xp3> [--limit N]
  info    <归档.xp3>
  extract <归档.xp3> <输出目录> [--filter SUBSTR]
  selftest <源目录> [--workdir DIR]

  --store      文件数据不压缩，按原样存储（segm flags=0）
  --raw-index  索引块不压缩（index_flag=0）
"""

import os
import re
import sys
import zlib
import struct
import hashlib
import argparse

import shutil

MAGIC = b"XP3\r\n \n\x1a\x8b\x67\x01"
assert len(MAGIC) == 11

TAG_FILE = b"File"
TAG_INFO = b"info"
TAG_SEGM = b"segm"
TAG_ADLR = b"adlr"

IDX_METHOD_MASK = 0x07
IDX_ENCODE_RAW = 0
IDX_ENCODE_ZLIB = 1
IDX_CONTINUE = 0x80

SEGM_METHOD_MASK = 0x07
SEGM_ENCODE_RAW = 0
SEGM_ENCODE_ZLIB = 1

FILE_PROTECTED = 1 << 31


# ----------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------
def chunk(tag: bytes, payload: bytes) -> bytes:
    if len(tag) != 4:
        raise ValueError("chunk tag must be 4 bytes")
    return tag + struct.pack("<Q", len(payload)) + payload


def iter_chunks(buf: bytes, start: int, size: int):
    """按引擎 FindChunk() 的同一顺序规则遍历 chunk 序列。
    返回 (tag, payload_start, payload_size)。"""
    pos = start
    end = start + size
    while pos + 12 <= end:
        tag = buf[pos:pos + 4]
        (ln,) = struct.unpack_from("<Q", buf, pos + 4)
        pay = pos + 12
        if pay + ln > end:
            raise ValueError(
                "chunk %r 声明长度 %d 超出可用范围（越界，归档可能被截断或格式不符）"
                % (tag, ln))
        yield tag, pay, ln
        pos = pay + ln


def norm_arc_name(name: str) -> str:
    """引擎读取时的 NormalizeInArchiveStorageName() 等价实现。"""
    name = name.replace("\\", "/").lower()
    name = re.sub(r"/{2,}", "/", name)
    return name


def md5_of(path_or_bytes):
    h = hashlib.md5()
    if isinstance(path_or_bytes, (bytes, bytearray)):
        h.update(path_or_bytes)
    else:
        with open(path_or_bytes, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
    return h.hexdigest()


class Xp3FormatError(Exception):
    pass


# ----------------------------------------------------------------------
# 读：头部 / 索引链
# ----------------------------------------------------------------------
def read_u64(f):
    b = f.read(8)
    if len(b) != 8:
        raise Xp3FormatError("读取 u64 时文件提前结束")
    return struct.unpack("<Q", b)[0]


def parse_index_blob(data: bytes):
    """解析一块（已解压/已读出的）索引数据，返回条目列表。"""
    entries = []
    for tag, pay, ln in iter_chunks(data, 0, len(data)):
        if tag != TAG_FILE:
            continue  # 未知 chunk（如 Applique 的 'Hxv4'）按引擎行为直接跳过
        info = segm = adlr = None
        for t2, p2, l2 in iter_chunks(data, pay, ln):
            if t2 == TAG_INFO:
                info = (p2, l2)
            elif t2 == TAG_SEGM:
                segm = (p2, l2)
            elif t2 == TAG_ADLR:
                adlr = (p2, l2)
        if info is None:
            raise Xp3FormatError("'File' chunk 缺少 'info' 子 chunk")
        if segm is None:
            raise Xp3FormatError("'File' chunk 缺少 'segm' 子 chunk")

        flags, org_size, arc_size, name_len = struct.unpack_from("<IQQH", data, info[0])
        raw_name = data[info[0] + 22: info[0] + 22 + name_len * 2]
        if len(raw_name) != name_len * 2:
            raise Xp3FormatError("条目名长度越界")
        name = raw_name.decode("utf-16-le", errors="replace")

        segs = []
        n_seg = segm[1] // 28
        for i in range(n_seg):
            sf, soff, sorg, sarc = struct.unpack_from("<IQQQ", data, segm[0] + i * 28)
            m = sf & SEGM_METHOD_MASK
            if m not in (SEGM_ENCODE_RAW, SEGM_ENCODE_ZLIB):
                raise Xp3FormatError("未知分段编码方式 flags=0x%08x" % sf)
            segs.append({
                "flags": sf,
                "compressed": (m == SEGM_ENCODE_ZLIB),
                "offset": soff,
                "org_size": sorg,
                "arc_size": sarc,
            })

        adler = None
        if adlr is not None and adlr[1] >= 4:
            (adler,) = struct.unpack_from("<I", data, adlr[0])

        entries.append({
            "name": name,
            "flags": flags,
            "org_size": org_size,
            "arc_size": arc_size,
            "adler32": adler,
            "segments": segs,
        })
    return entries


def read_archive_index(path, diag=None):
    """读取 XP3 归档索引；支持 TVP_XP3_INDEX_CONTINUE 索引链。
    diag 为可选 list，会追加诊断行。"""
    if diag is None:
        diag = []
    entries = []
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        fsize = f.tell()
        f.seek(0)
        magic = f.read(11)
        if magic != MAGIC:
            raise Xp3FormatError(
                "不是 XP3 归档：魔数不符\n  期望 %s\n  实际 %s"
                % (MAGIC.hex(" "), magic.hex(" ")))
        diag.append("[ok] 魔数匹配（11 字节） 文件大小 = %d 字节" % fsize)

        index_ofs = read_u64(f)
        diag.append("[ok] 头部 0x0B 处 index_offset = %d (0x%X)" % (index_ofs, index_ofs))

        blocks = 0
        while True:
            if index_ofs + 9 > fsize:
                raise Xp3FormatError(
                    "index_offset=%d 越过文件末尾（文件 %d 字节）" % (index_ofs, fsize))
            f.seek(index_ofs)
            flag = f.read(1)[0]
            method = flag & IDX_METHOD_MASK
            cont = bool(flag & IDX_CONTINUE)
            diag.append("[ok] 索引块 #%d @0x%X  index_flag=0x%02X (method=%d, continue=%s)"
                        % (blocks, index_ofs, flag, method, "yes" if cont else "no"))
            if method == IDX_ENCODE_ZLIB:
                csize = read_u64(f)
                usize = read_u64(f)
                comp = f.read(csize)
                if len(comp) != csize:
                    raise Xp3FormatError("索引 zlib 流被截断")
                data = zlib.decompress(comp)
                if len(data) != usize:
                    raise Xp3FormatError(
                        "索引解压长度不符：声明 %d，实得 %d" % (usize, len(data)))
                diag.append("      zlib 索引：压缩 %d → 解压 %d 字节" % (csize, usize))
            elif method == IDX_ENCODE_RAW:
                usize = read_u64(f)
                data = f.read(usize)
                if len(data) != usize:
                    raise Xp3FormatError("索引原始数据被截断")
                diag.append("      原样索引：%d 字节" % usize)
            else:
                raise Xp3FormatError(
                    "未知索引编码方式 index_flag=0x%02X（method=%d）" % (flag, method))

            got = parse_index_blob(data)
            diag.append("      本块解析出 %d 个 'File' 条目" % len(got))
            entries.extend(got)

            if not cont:
                break
            # CONTINUE 置位：本块之后紧跟下一个 u64 index_offset
            index_ofs = read_u64(f)
            blocks += 1

    return entries


def extract_entry(f, entry, verify_adler=True):
    """按分段读取一个条目的完整原始数据。"""
    out = bytearray()
    for s in entry["segments"]:
        f.seek(s["offset"])
        blob = f.read(s["arc_size"])
        if len(blob) != s["arc_size"]:
            raise Xp3FormatError("条目 %s 的分段数据被截断" % entry["name"])
        if s["compressed"]:
            d = zlib.decompress(blob)
            if len(d) != s["org_size"]:
                raise Xp3FormatError(
                    "条目 %s 分段解压长度不符：声明 %d，实得 %d"
                    % (entry["name"], s["org_size"], len(d)))
            out += d
        else:
            if len(blob) != s["org_size"]:
                # 原样分段时 org_size 可能等于 arc_size；不等则按 arc_size 取
                pass
            out += blob
    data = bytes(out)
    adler_ok = None
    if verify_adler and entry["adler32"] is not None:
        adler_ok = (zlib.adler32(data) & 0xFFFFFFFF) == entry["adler32"]
    return data, adler_ok


# ----------------------------------------------------------------------
# 写：打包
# ----------------------------------------------------------------------
def build_archive(src_root, out_path, store=False, raw_index=False,
                  include=None, exclude=None, verbose=True):
    src_root = os.path.abspath(src_root)
    if not os.path.isdir(src_root):
        raise SystemExit("源目录不存在：%s" % src_root)

    inc_re = re.compile(include) if include else None
    exc_re = re.compile(exclude) if exclude else None

    pairs = []
    for dirpath, _dirnames, filenames in os.walk(src_root):
        for fn in sorted(filenames):
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, src_root)
            arc = norm_arc_name(rel)
            if inc_re and not inc_re.search(arc):
                continue
            if exc_re and exc_re.search(arc):
                continue
            if any(ord(c) > 0xFFFF for c in arc):
                raise SystemExit("条目名含非 BMP 字符，XP3 名称字段只支持 UTF-16 BMP：%s" % arc)
            pairs.append((arc, ap))
    pairs.sort(key=lambda t: t[0])

    if not pairs:
        raise SystemExit("源目录内没有可打包的文件：%s" % src_root)

    header_len = 11 + 8
    body = bytearray()
    records = []

    for arc, ap in pairs:
        with open(ap, "rb") as f:
            data = f.read()
        adler = zlib.adler32(data) & 0xFFFFFFFF
        blob = data
        seg_flag = SEGM_ENCODE_RAW
        if not store:
            comp = zlib.compress(data, 9)
            if len(comp) < len(data):
                blob = comp
                seg_flag = SEGM_ENCODE_ZLIB
        offset = header_len + len(body)
        body += blob
        records.append({
            "name": arc,
            "org_size": len(data),
            "arc_size": len(blob),
            "adler32": adler,
            "segments": [{
                "flags": seg_flag,
                "compressed": seg_flag == SEGM_ENCODE_ZLIB,
                "offset": offset,
                "org_size": len(data),
                "arc_size": len(blob),
            }],
        })
        if verbose:
            print("  + %-48s %8d -> %8d  (%s)"
                  % (arc, len(data), len(blob),
                     "zlib" if seg_flag == SEGM_ENCODE_ZLIB else "raw"))

    # 组装索引
    index_data = bytearray()
    for r in records:
        name_bytes = r["name"].encode("utf-16-le")
        info = struct.pack("<IQQH", 0, r["org_size"], r["arc_size"],
                           len(name_bytes) // 2) + name_bytes
        segm = b"".join(struct.pack("<IQQQ", s["flags"], s["offset"],
                                    s["org_size"], s["arc_size"])
                        for s in r["segments"])
        adlr = struct.pack("<I", r["adler32"])
        payload = (chunk(TAG_INFO, info) + chunk(TAG_SEGM, segm) + chunk(TAG_ADLR, adlr))
        index_data += chunk(TAG_FILE, payload)

    if raw_index:
        index_block = bytes([IDX_ENCODE_RAW]) + struct.pack("<Q", len(index_data)) \
                      + bytes(index_data)
    else:
        comp = zlib.compress(bytes(index_data), 9)
        index_block = bytes([IDX_ENCODE_ZLIB]) + struct.pack("<QQ", len(comp),
                                                             len(index_data)) + comp

    index_offset = header_len + len(body)
    header = MAGIC + struct.pack("<Q", index_offset)

    tmp = out_path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(header)
        f.write(body)
        f.write(index_block)
    os.replace(tmp, out_path)

    total = header_len + len(body) + len(index_block)
    if verbose:
        print("归档写出：%s" % out_path)
        print("  条目数        = %d" % len(records))
        print("  数据区起止    = 0x%X .. 0x%X" % (header_len, index_offset))
        print("  索引偏移      = 0x%X (flag=%d, %s)"
              % (index_offset, 0 if raw_index else 1,
                 "raw" if raw_index else "zlib"))
        print("  文件总大小    = %d 字节" % total)
    return records, index_offset, total


# ----------------------------------------------------------------------
# 打包往返自检
# ----------------------------------------------------------------------
def cmd_selftest(args):
    src = os.path.abspath(args.src)
    # 默认工作目录固定在本脚本同级的 _selftest\，绝不落到系统盘
    if args.workdir:
        workdir = os.path.abspath(args.workdir)
    else:
        workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_selftest")
    os.makedirs(workdir, exist_ok=True)
    print("=" * 70)
    print("XP3 打包 round-trip 自检")
    print("  源目录 : %s" % src)
    print("  工作目录: %s" % workdir)
    print("=" * 70)

    variants = [
        ("a_zlib_idx_zlib_data", dict(store=False, raw_index=False)),
        ("b_zlib_idx_raw_data", dict(store=True, raw_index=False)),
        ("c_raw_idx_zlib_data", dict(store=False, raw_index=True)),
    ]

    # 源文件清单 + md5
    src_files = {}
    for dirpath, _d, filenames in os.walk(src):
        for fn in filenames:
            ap = os.path.join(dirpath, fn)
            src_files[norm_arc_name(os.path.relpath(ap, src))] = md5_of(ap)
    print("源文件 %d 个：" % len(src_files))
    for k in sorted(src_files):
        print("   %-40s md5=%s" % (k, src_files[k]))
    print()

    ok_all = True
    for tag, kw in variants:
        xp3 = os.path.join(workdir, "poc_%s.xp3" % tag)
        outdir = os.path.join(workdir, "extract_%s" % tag)
        print("-" * 70)
        print("[变体 %s] 打包参数 store=%s raw_index=%s" % (tag, kw["store"], kw["raw_index"]))
        build_archive(src, xp3, verbose=False, **kw)
        print("  打包完成：%s (%d 字节)" % (xp3, os.path.getsize(xp3)))

        # list
        diag = []
        entries = read_archive_index(xp3, diag)
        for d in diag:
            print("  %s" % d)
        print("  list → %d 条目" % len(entries))
        names = sorted(e["name"] for e in entries)

        # extract
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
        os.makedirs(outdir)
        with open(xp3, "rb") as f:
            for e in entries:
                data, adler_ok = extract_entry(f, e)
                dst = os.path.join(outdir, e["name"].replace("/", os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as g:
                    g.write(data)
                print("  extract %-40s %8d 字节  adler32=%s"
                      % (e["name"], len(data), "OK" if adler_ok else "MISMATCH"))

        # 比对 md5
        out_files = {}
        for dirpath, _d, filenames in os.walk(outdir):
            for fn in filenames:
                ap = os.path.join(dirpath, fn)
                out_files[norm_arc_name(os.path.relpath(ap, outdir))] = md5_of(ap)
        same = (src_files == out_files)
        print("  往返 md5 比对：%s" % ("全部一致 ✔" if same else "不一致 ✘"))
        if not same:
            ok_all = False
            for k in sorted(set(src_files) | set(out_files)):
                if src_files.get(k) != out_files.get(k):
                    print("     差异 %s : 源=%s 解=%s"
                          % (k, src_files.get(k), out_files.get(k)))
        print()

    print("=" * 70)
    print("自检总结：%s" % ("3/3 变体全部 round-trip 一致 ✔" if ok_all else "存在不一致 ✘"))
    print("=" * 70)
    return 0 if ok_all else 1


# ----------------------------------------------------------------------
# 命令实现
# ----------------------------------------------------------------------
def cmd_pack(args):
    build_archive(args.src, args.out, store=args.store, raw_index=args.raw_index,
                  include=args.include, exclude=args.exclude)
    return 0


def cmd_info(args):
    path = args.archive
    size = os.path.getsize(path)
    print("=" * 70)
    print("XP3 检视：%s" % path)
    print("  文件大小 = %d 字节" % size)
    print("=" * 70)
    with open(path, "rb") as f:
        head = f.read(0x60)
    print("头部前 0x60 字节：")
    for off in range(0, len(head), 16):
        row = head[off:off + 16]
        hexs = " ".join("%02x" % b for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print("  %08x: %-47s  %s" % (off, hexs, asc))
    print()
    print("头部逐字段：")
    print("  [0x00] magic(11)  = %s" % (" ".join("%02x" % b for b in head[:11])))
    magic_matched = head[:11] == MAGIC
    print("                     %s" % ("== 标准 krkrz XP3 魔数 ✔" if magic_matched
                                      else "!= 标准魔数 ✘"))
    (idx,) = struct.unpack_from("<Q", head, 0x0B)
    print("  [0x0B] u64 index_offset = %d (0x%X)" % (idx, idx))
    print()
    if not magic_matched:
        print("结论：不是标准 krkrz XP3 归档，后续解析中止。")
        return 2
    diag = []
    try:
        entries = read_archive_index(path, diag)
    except Xp3FormatError as e:
        for d in diag:
            print("  %s" % d)
        print()
        print("解析失败：%s" % e)
        return 3
    for d in diag:
        print("  %s" % d)
    print()
    prot = [e for e in entries if e["flags"] & FILE_PROTECTED]
    zlib_n = sum(1 for e in entries for s in e["segments"] if s["compressed"])
    raw_n = sum(1 for e in entries for s in e["segments"] if not s["compressed"])
    print("结论：可被本工具（标准实现）解析。")
    print("  条目数            = %d" % len(entries))
    print("  标记 protected 的 = %d" % len(prot))
    print("  分段数            = %d（zlib %d / 原样 %d）" % (zlib_n + raw_n, zlib_n, raw_n))
    print("  首条目            = %r  org=%d arc=%d"
          % (entries[0]["name"], entries[0]["org_size"], entries[0]["arc_size"])
          if entries else "  （无条目）")
    return 0


def cmd_list(args):
    diag = []
    entries = read_archive_index(args.archive, diag)
    if args.diag:
        for d in diag:
            print("# %s" % d)
    entries = sorted(entries, key=lambda e: e["name"])
    n = len(entries)
    if args.limit and args.limit < n:
        shown = entries[:args.limit]
    else:
        shown = entries
    print("# %s : %d 条目（显示 %d）" % (args.archive, n, len(shown)))
    print("%-52s %12s %12s %6s %10s %s"
          % ("name", "org_size", "arc_size", "segs", "adler32", "flags"))
    for e in shown:
        print("%-52s %12d %12d %6d 0x%08x 0x%08x"
              % (e["name"], e["org_size"], e["arc_size"],
                 len(e["segments"]), e["adler32"] or 0, e["flags"]))
    return 0


def cmd_extract(args):
    entries = read_archive_index(args.archive)
    if args.filter:
        entries = [e for e in entries if args.filter in e["name"]]
    if not entries:
        print("没有匹配的条目")
        return 1
    os.makedirs(args.outdir, exist_ok=True)
    bad = 0
    with open(args.archive, "rb") as f:
        for e in entries:
            data, adler_ok = extract_entry(f, e)
            dst = os.path.join(args.outdir, e["name"].replace("/", os.sep))
            os.makedirs(os.path.dirname(dst) or args.outdir, exist_ok=True)
            with open(dst, "wb") as g:
                g.write(data)
            flag = "OK" if adler_ok else ("MISMATCH" if adler_ok is False else "-")
            if adler_ok is False:
                bad += 1
            print("  %-52s %10d  adler32=%s" % (e["name"], len(data), flag))
    print("解出 %d 个条目，adler32 不符 %d 个" % (len(entries), bad))
    return 0


# ----------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="标准 KiriKiri XP3 打包/解包/检视工具（纯标准库）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pack", help="把目录打包成标准 XP3")
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--store", action="store_true", help="文件数据不压缩")
    p.add_argument("--raw-index", action="store_true", help="索引块不压缩")
    p.add_argument("--include", help="只打包匹配该正则的条目名")
    p.add_argument("--exclude", help="排除匹配该正则的条目名")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("list", help="列出归档条目")
    p.add_argument("archive")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--diag", action="store_true", help="附带索引链诊断信息")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("info", help="检视归档头部与索引，给出判定")
    p.add_argument("archive")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("extract", help="解出归档条目")
    p.add_argument("archive")
    p.add_argument("outdir")
    p.add_argument("--filter", default=None)
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("selftest", help="打包→list→解包→md5 往返自检")
    p.add_argument("src")
    p.add_argument("--workdir", default=None)
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

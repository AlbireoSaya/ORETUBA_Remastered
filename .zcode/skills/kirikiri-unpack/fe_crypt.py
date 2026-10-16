#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fe_crypt.py -- KiriKiri 的「FE FE 密文/压缩文本流」容器解密/加密（纯标准库）

格式（依据 krkrz 1.4.0r2 源码 base/TextStream.cpp:92-150）：
    偏移 0   : FE FE                  ← 容器标记
    偏移 2   : mode (1 字节)          ← 0/1 = simple crypt，2 = zlib 压缩
    偏移 3   : FF FE                  ← 原始 BOM（mode 0/1 时才有；mode 2 之后是长度字段）
    mode 2   : u64 compressed + u64 uncompressed + zlib 数据
    正文     : mode 0/1 为「已加密的 UTF-16LE 文本」，逐 16 位单元解密

解密算法（源码原文）：
    mode 1 : ch = ((ch & 0xAAAAAAAA) >> 1) | ((ch & 0x55555555) << 1)   # 相邻位交换（自逆）
    mode 0 : if ch >= 0x20: ch ^= (((ch & 0xfe) << 8) ^ 1)              # 注意：非自逆，本工具只做解密方向的近似
    注：源码注释称 mode 0/1 的加密「does never intend data protection」。

用法：
    python fe_crypt.py info    <文件>              # 判定容器类型与 mode
    python fe_crypt.py decrypt <文件> [输出文件]    # 解出文本（默认打印到 stdout）
    python fe_crypt.py encrypt <文本文件> <输出>    # 用 mode1 重新封装（自逆，写回用）
    python fe_crypt.py xp3 <归档.xp3> <条目名> [输出]  # 直接从 xp3 取条目并解密
"""
import sys, struct, zlib, os

MAGIC = b"\xfe\xfe"

def bitswap16(data: bytes) -> bytes:
    """mode1：每个 16 位单元做相邻位交换（自逆）"""
    out = bytearray(len(data) & ~1)
    for i in range(0, len(out), 2):
        u = data[i] | (data[i + 1] << 8)
        u = ((u & 0xAAAA) >> 1) | ((u & 0x5555) << 1)
        out[i] = u & 0xFF
        out[i + 1] = (u >> 8) & 0xFF
    return bytes(out)

def xor_mode0(data: bytes) -> bytes:
    """mode0：ch ^= (((ch & 0xfe) << 8) ^ 1)（ch >= 0x20 时）"""
    out = bytearray(len(data) & ~1)
    for i in range(0, len(out), 2):
        u = data[i] | (data[i + 1] << 8)
        if u >= 0x20:
            u = (u ^ ((((u & 0xFE) << 8) ^ 1) & 0xFFFF)) & 0xFFFF
        out[i] = u & 0xFF
        out[i + 1] = (u >> 8) & 0xFF
    return bytes(out)

def probe(blob: bytes):
    """返回 (kind, mode, payload_offset)；kind ∈ container/plain"""
    if blob[:2] != MAGIC:
        return "plain", None, 0
    if len(blob) < 5:
        return "container", None, 0
    mode = blob[2]
    if mode in (0, 1):
        if blob[3:5] != b"\xff\xfe":
            return "container", mode, 5   # BOM 异常也照解
        return "container", mode, 5
    if mode == 2:
        return "container", 2, 5
    return "container", mode, 5

def decrypt(blob: bytes):
    """返回 (text_or_None, 说明)"""
    kind, mode, off = probe(blob)
    if kind == "plain":
        return None, "不是 FE FE 容器（按原文返回请直接用文件本身）"
    if mode == 1:
        return bitswap16(blob[off:]).decode("utf-16-le", "replace"), "mode1 simple crypt（相邻位交换）"
    if mode == 0:
        return xor_mode0(blob[off:]).decode("utf-16-le", "replace"), "mode0 simple crypt（XOR；非自逆，加密方向需另行推导）"
    if mode == 2:
        csize, usize = struct.unpack_from("<QQ", blob, off)
        data = zlib.decompress(blob[off + 16:off + 16 + csize])
        assert len(data) == usize, "解压长度不符"
        return data.decode("utf-16-le", "replace"), f"mode2 zlib（{csize} → {usize} 字节）"
    return None, f"未知 mode={mode}"

def encrypt_mode1(text: str) -> bytes:
    """用 mode1 重新封装（写回用；自逆）"""
    body = text.encode("utf-16-le")
    return MAGIC + b"\x01" + b"\xff\xfe" + bitswap16(body)

def _xp3_extract(xp3_path, entry_name):
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("xp3p", os.path.join(here, "xp3pack.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    with open(xp3_path, "rb") as f:
        for x in m.read_archive_index(xp3_path):
            if x["name"] == entry_name:
                d, _ = m.extract_entry(f, x, verify_adler=False)
                return d
    raise SystemExit("归档中找不到条目: " + entry_name)

def main(argv):
    if len(argv) < 3:
        print(__doc__); return 1
    cmd = argv[1]
    if cmd == "info":
        blob = open(argv[2], "rb").read()
        kind, mode, off = probe(blob)
        print(f"文件: {argv[2]}\n  类型: {kind}\n  mode: {mode}\n  正文起点: {off}\n  大小: {len(blob)}")
        return 0
    if cmd == "decrypt":
        blob = open(argv[2], "rb").read()
        txt, why = decrypt(blob)
        if txt is None:
            print("[!]", why); return 2
        print(f"[i] {why}", file=sys.stderr)
        if len(argv) > 3:
            open(argv[3], "w", encoding="utf-8", newline="").write(txt)
            print(f"[i] 已写出 {argv[3]}（{len(txt)} 字符）", file=sys.stderr)
        else:
            sys.stdout.write(txt)
        return 0
    if cmd == "encrypt":
        txt = open(argv[2], encoding="utf-8").read()
        open(argv[3], "wb").write(encrypt_mode1(txt))
        print(f"[i] 已写出 {argv[3]}（mode1 封装）")
        return 0
    if cmd == "xp3":
        blob = _xp3_extract(argv[2], argv[3])
        txt, why = decrypt(blob)
        if txt is None:
            print("[!]", why); return 2
        print(f"[i] {why}", file=sys.stderr)
        if len(argv) > 4:
            open(argv[4], "w", encoding="utf-8", newline="").write(txt)
            print(f"[i] 已写出 {argv[4]}（{len(txt)} 字符）", file=sys.stderr)
        else:
            sys.stdout.write(txt)
        return 0
    print(__doc__); return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

import ctypes


def host_version_ex_a(before):
    if type(before) is not bytes:
        raise TypeError("before must be bytes")
    if len(before) != 148:
        raise ValueError("before must be exactly 148 bytes")
    if int.from_bytes(before[:4], "little") != 148:
        raise ValueError("before first u32 little-endian must be 148")

    guard = b"\xA5" * 128
    total = 128 + 148 + 128
    buf = ctypes.create_string_buffer(total)
    ctypes.memmove(ctypes.addressof(buf), guard + before + guard, total)

    kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
    get_version_ex_a = kernel32.GetVersionExA
    get_version_ex_a.argtypes = [ctypes.c_void_p]
    get_version_ex_a.restype = ctypes.c_int

    ptr = ctypes.c_void_p(ctypes.addressof(buf) + 128)
    ret = get_version_ex_a(ptr)
    err = 0 if ret else ctypes.get_last_error()

    raw = buf.raw
    if raw[:128] != guard or raw[-128:] != guard:
        raise RuntimeError("guard bytes modified")
    middle = raw[128:128 + 148]
    if int.from_bytes(middle[:4], "little") != 148:
        raise RuntimeError("OSVERSIONINFOA size field modified")

    return (bool(ret), middle, err)

import ctypes


def host_upper_ascii_z(payload):
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    n = len(payload)
    if n > 4095:
        raise ValueError("payload length must be <= 4095")
    for byte in payload:
        if byte < 1 or byte > 127:
            raise ValueError("payload bytes must be in 1..127")

    guard = 128
    total = guard + n + 1 + guard
    alloc = total + 0x10000
    buf = ctypes.create_string_buffer(alloc)
    base = ctypes.addressof(buf)
    offset = 0x10000 - (base % 0x10000)
    src = base + offset + guard
    if src < 0x10000:
        raise RuntimeError("unable to place payload at address >= 0x10000")

    ctypes.memset(src - guard, 0xA5, guard)
    if n:
        ctypes.memmove(src, payload, n)
    ctypes.memset(src + n, 0x00, 1)
    ctypes.memset(src + n + 1, 0xA5, guard)

    user32 = ctypes.WinDLL("user32.dll")
    char_upper = user32.CharUpperA
    char_upper.argtypes = [ctypes.c_void_p]
    char_upper.restype = ctypes.c_void_p

    result = char_upper(ctypes.c_void_p(src))
    if result is None or int(result) != src:
        raise RuntimeError("CharUpperA did not return the input pointer")

    if ctypes.string_at(src + n, 1) != b"\x00":
        raise RuntimeError("NUL terminator was modified")
    if ctypes.string_at(src - guard, guard) != b"\xA5" * guard:
        raise RuntimeError("leading guard was modified")
    if ctypes.string_at(src + n + 1, guard) != b"\xA5" * guard:
        raise RuntimeError("trailing guard was modified")

    out = ctypes.string_at(src, n)
    if out != payload.upper():
        raise RuntimeError("CharUpperA output mismatch")
    return out
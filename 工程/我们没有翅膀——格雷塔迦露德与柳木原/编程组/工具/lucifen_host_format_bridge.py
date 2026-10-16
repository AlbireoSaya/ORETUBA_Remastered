from lucifen_host_string_bridge import read_z
import ctypes

_GUARD = b"\xa5" * 128


def _alloc(init):
    total = 128 + len(init) + 128
    buf = ctypes.create_string_buffer(total)
    ctypes.memset(buf, 0xA5, total)
    ctypes.memmove(ctypes.byref(buf, 128), init, len(init))
    return buf, len(init)


def host_format_two_strings(fmt, left, right, before):
    for name, data in (("fmt", fmt), ("left", left), ("right", right)):
        if not isinstance(data, bytes) or b"\x00" in data:
            raise ValueError(name)
    if not isinstance(before, bytes):
        raise ValueError("before")
    if not 1 <= len(before) <= 1024:
        raise ValueError("before")
    if fmt.count(b"%s") != 2:
        raise ValueError("fmt")
    rest = fmt.replace(b"%s", b"")
    if b"%" in rest or any(byte > 0x7F for byte in rest):
        raise ValueError("fmt")
    head, mid, tail = fmt.split(b"%s")
    expected = head + left + mid + right + tail
    if len(expected) + 1 > len(before):
        raise ValueError("before")
    dst, d_len = _alloc(before)
    fb, f_len = _alloc(fmt + b"\x00")
    lb, l_len = _alloc(left + b"\x00")
    rb, r_len = _alloc(right + b"\x00")
    wsprintf = ctypes.CDLL("user32.dll").wsprintfA
    wsprintf.restype = ctypes.c_int
    wsprintf.argtypes = [ctypes.c_void_p] * 4
    count = wsprintf(ctypes.c_void_p(ctypes.addressof(dst) + 128),
                     ctypes.c_void_p(ctypes.addressof(fb) + 128),
                     ctypes.c_void_p(ctypes.addressof(lb) + 128),
                     ctypes.c_void_p(ctypes.addressof(rb) + 128))
    if count != len(expected):
        raise RuntimeError("count")
    got = ctypes.string_at(ctypes.addressof(dst) + 128, d_len)
    if got != expected + b"\x00" + before[len(expected) + 1:]:
        raise RuntimeError("dst")
    for buf, size in ((dst, d_len), (fb, f_len), (lb, l_len), (rb, r_len)):
        base = ctypes.addressof(buf)
        if ctypes.string_at(base, 128) != _GUARD or ctypes.string_at(base + 128 + size, 128) != _GUARD:
            raise RuntimeError("guard")
    return count, got
def bridge_wsprintf_two(read_bytes, write_bytes, dst, fmt, left, right, capacity):
    ok_addr = lambda v: type(v) is int and not isinstance(v, bool) and 1 <= v <= 0xFFFFFFFF
    if not (ok_addr(dst) and ok_addr(fmt) and ok_addr(left) and ok_addr(right)):
        raise ValueError("invalid address")
    if type(capacity) is not int or isinstance(capacity, bool) or not 1 <= capacity <= 1024:
        raise ValueError("invalid capacity")
    if dst + capacity > 2**32:
        raise ValueError("destination out of range")
    src = []
    for a in (fmt, left, right):
        s = read_z(read_bytes, a, 1024)
        if not isinstance(s, (bytes, bytearray)) or a + len(s) + 1 > 2**32:
            raise ValueError("source out of range")
        if not (a + len(s) + 1 <= dst or dst + capacity <= a):
            raise ValueError("source overlaps destination")
        src.append(bytes(s))
    before = read_bytes(dst, capacity)
    if not isinstance(before, (bytes, bytearray)) or len(before) != capacity:
        raise ValueError("destination read failed")
    result = host_format_two_strings(src[0], src[1], src[2], bytes(before))
    if not isinstance(result, tuple) or len(result) != 2:
        raise ValueError("bad format result")
    count, out = result
    if type(count) is not int or isinstance(count, bool) or not isinstance(out, (bytes, bytearray)) or len(out) != capacity:
        raise ValueError("bad format result")
    write_bytes(dst, bytes(out))
    return count
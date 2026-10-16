"""Host-only wrapper: real Windows user32!wsprintfA with the fixed b"%d.%02d.%04d" format."""
import ctypes

_FMT = b"%d.%02d.%04d"
_GUARD = b"\xa5" * 32
_DST = 64
_LO, _HI = -2147483648, 2147483647

_wsprintfA = ctypes.CDLL("user32").wsprintfA
_wsprintfA.argtypes = [ctypes.c_void_p, ctypes.c_char_p]  # only the first 2 entries are fixed
_wsprintfA.restype = ctypes.c_int


def host_format_version3(fmt, values):
    if type(fmt) is not bytes or fmt != _FMT:
        raise ValueError("fmt must be exactly b'%d.%02d.%04d'")
    if type(values) not in (tuple, list) or len(values) != 3:
        raise TypeError("values must be a tuple/list of length 3")
    args = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("each value must be a non-bool int")
        if not (_LO <= value <= _HI):
            raise ValueError("each value must be in int32 range")
        args.append(ctypes.c_int32(value))
    buf = ctypes.create_string_buffer(_GUARD + b"\x00" * _DST + _GUARD, 32 + _DST + 32)
    dst = ctypes.c_void_p(ctypes.addressof(buf) + 32)
    ctypes.memset(dst, 0, _DST)
    count = _wsprintfA(dst, fmt, *args)  # trailing 3 arguments are c_int32
    raw = buf.raw
    if raw[:32] != _GUARD or raw[96:] != _GUARD:
        raise RuntimeError("wsprintfA wrote outside dst (guard clobbered)")
    if not 0 <= count < _DST:
        raise RuntimeError("unexpected wsprintfA return %d" % count)
    if raw[32 + count] != 0 or raw[32:32 + _DST].find(b"\x00") != count:
        raise RuntimeError("NUL terminator mismatch (count=%d)" % count)
    return bytes(raw[32:32 + count])

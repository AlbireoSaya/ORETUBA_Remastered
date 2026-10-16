import ctypes

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_GetLocaleInfoA = _k32.GetLocaleInfoA
_GetLocaleInfoA.argtypes = (ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int)
_GetLocaleInfoA.restype = ctypes.c_int

def host_locale_info_a(locale, lctype, before):
    if any(type(x) is not int or not 0 <= x <= 0xFFFFFFFF for x in (locale, lctype)):
        raise ValueError("locale/lctype must be non-bool u32")
    if not isinstance(before, bytes):
        raise TypeError("before must be bytes")
    cap = len(before)
    if cap > 1024:
        raise ValueError("before too long")
    if cap == 0:
        ctypes.set_last_error(0)
        count = _GetLocaleInfoA(locale, lctype, None, 0)
        return count, b"", 0 if count else ctypes.get_last_error()
    buf = ctypes.create_string_buffer(32 + cap + 32)
    ctypes.memset(buf, 0xA5, len(buf))
    buf[32:32 + cap] = before
    ctypes.set_last_error(0)
    count = _GetLocaleInfoA(locale, lctype, ctypes.addressof(buf) + 32, cap)
    last_error = 0 if count else ctypes.get_last_error()
    if bytes(buf[:32]) != b"\xA5" * 32 or bytes(buf[-32:]) != b"\xA5" * 32:
        raise RuntimeError("guard corrupted")
    return count, bytes(buf[32:32 + cap]), last_error
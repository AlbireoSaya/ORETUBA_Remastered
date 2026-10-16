"""Host-side kernel32!GetVersionExA probe for the 156-byte OSVERSIONINFOEXA."""
import ctypes

_A5 = b"\xA5" * 32
_SIZE = 156
_TOTAL = len(_A5) * 2 + _SIZE

_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
_GetVersionExA = _K32.GetVersionExA
_GetVersionExA.argtypes = (ctypes.c_void_p,)
_GetVersionExA.restype = ctypes.c_int


def host_version156(before):
    """Call kernel32!GetVersionExA on a guarded copy of a 156-byte OSVERSIONINFOEXA."""
    if not isinstance(before, bytes) or len(before) != _SIZE:
        raise ValueError("before must be exactly 156 bytes")
    if int.from_bytes(before[:4], "little") != _SIZE:
        raise ValueError("dwOSVersionInfoSize must be 156 (little-endian)")
    buf = ctypes.create_string_buffer(_TOTAL)
    buf[:] = _A5 + before + _A5
    ctypes.set_last_error(0)
    mid = ctypes.cast(ctypes.byref(buf, len(_A5)), ctypes.c_void_p)
    ok = _GetVersionExA(mid)
    err = ctypes.get_last_error()
    raw = buf.raw
    if raw[:len(_A5)] != _A5 or raw[-len(_A5):] != _A5:
        raise RuntimeError("A5 guard bytes mutated by GetVersionExA")
    after = raw[len(_A5):len(_A5) + _SIZE]
    return bool(ok), after, 0 if ok else err

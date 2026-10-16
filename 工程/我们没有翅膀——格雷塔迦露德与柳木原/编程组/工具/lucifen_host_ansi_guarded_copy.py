import ctypes

from lucifen_host_ansi_guard_buffer import make_guarded, read_guarded
from lucifen_host_lstrcpyn_a import lstrcpynA

_GUARD_LEN = 16
_MIN_LEN = 1
_MAX_LEN = 4096


def host_copy_bounded(payload, before):
    if type(payload) is not bytes:
        raise TypeError("payload must be exactly bytes")
    if type(before) is not bytes:
        raise TypeError("before must be exactly bytes")
    if not _MIN_LEN <= len(before) <= _MAX_LEN:
        raise ValueError("before length must be in 1..4096")
    n = len(before)
    if b"\x00" in payload:
        raise ValueError("payload must not contain NUL")
    if len(payload) > n - 1:
        raise ValueError("payload length must be <= len(before) - 1")

    dst = make_guarded(before)
    src = make_guarded(payload + b"\x00")
    src_raw = src.raw

    dst_ptr = ctypes.addressof(dst) + _GUARD_LEN
    src_ptr = ctypes.addressof(src) + _GUARD_LEN
    if lstrcpynA(dst_ptr, src_ptr, n) != dst_ptr:
        raise RuntimeError("lstrcpynA returned an unexpected destination pointer")

    read_guarded(src, len(payload) + 1)
    if src.raw != src_raw:
        raise RuntimeError("source guarded buffer was modified during copy")
    return read_guarded(dst, n)

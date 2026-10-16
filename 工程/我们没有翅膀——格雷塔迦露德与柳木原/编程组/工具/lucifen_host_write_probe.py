"""actual host SURROGATE validation only.

NOT original guest addresses, not SEH dispatcher or general safety guarantee/deprecated.
Root must verify guest mapping WRITE permission before this host surrogate call.
"""

import ctypes
from ctypes import wintypes

_MAX = 1024 * 1024

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=False)
_IsBadWritePtr = _kernel32.IsBadWritePtr
_IsBadWritePtr.argtypes = (wintypes.LPVOID, ctypes.c_size_t)
_IsBadWritePtr.restype = wintypes.BOOL


def host_bad_write_bytes(payload):
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    n = len(payload)
    if n < 1 or n > _MAX:
        raise ValueError("payload length must be 1..1MiB")

    guard = b"\xA5" * 128
    buf = ctypes.create_string_buffer(guard + payload + guard, 128 + n + 128)
    before = bytes(buf)

    ptr = ctypes.addressof(buf) + 128
    if ptr < 0x10000:
        raise RuntimeError("host pointer below 0x10000")

    result = _IsBadWritePtr(ptr, n)

    if bytes(buf) != before:
        raise RuntimeError("host surrogate buffer mutated")

    return int(result)


def host_bad_write_null(count):
    if type(count) is not int:
        raise TypeError("count must be int")
    if count < 0 or count > _MAX:
        raise ValueError("count must be 0..1MiB")

    return int(_IsBadWritePtr(None, count))
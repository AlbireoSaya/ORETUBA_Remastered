"""Host-side read probe (kernel32.IsBadReadPtr) -- lucifen_host_read_probe.

Scope of this module (this ACTUAL host call is the only thing claimed):

  * It validates actual host surrogate bytes / a null pointer through the real
    kernel32.IsBadReadPtr API.
  * It does NOT validate the original guest virtual addresses: only a surrogate
    host buffer (or NULL) is probed, never a guest address and never an
    arbitrary host pointer supplied by the caller.
  * It is NOT an OS sandbox and NOT an SEH dispatcher: exceptions are not
    raised or caught on the caller's behalf, and no command is executed.
  * IsBadReadPtr is deprecated and is NOT a general safety guarantee.

root must first obtain readable guest bytes through Unicorn and only then hand
the resulting surrogate bytes to host_bad_read_bytes().
"""

import ctypes
from ctypes import wintypes

__all__ = ["host_bad_read_bytes", "host_bad_read_null"]

_MAX_BYTES = 1024 * 1024  # 1 MiB, inclusive upper bound for both helpers
_GUARD_COUNT = 128        # 0xA5 guard bytes placed before and after payload
_GUARD_BYTE = b"\xA5"
_MIN_HOST_PTR = 0x10000   # reject implausible surrogate payload addresses

# Actual host API. use_last_error=True is set, but the error code is never
# interpreted: the BOOL return value is the only authority for the answer.
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.IsBadReadPtr.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
_kernel32.IsBadReadPtr.restype = wintypes.BOOL
_is_bad_read_ptr = _kernel32.IsBadReadPtr


def _check_byte_count(n, allow_zero):
    if n > _MAX_BYTES:
        raise ValueError(
            "length/byte count must be at most %d bytes, got %d"
            % (_MAX_BYTES, n)
        )
    if n < 0:
        raise ValueError("length/byte count must not be negative, got %d" % (n,))
    if n == 0 and not allow_zero:
        raise ValueError(
            "payload must not be empty (length 1..%d)" % (_MAX_BYTES,)
        )


def host_bad_read_bytes(payload):
    """Probe real host surrogate bytes with kernel32.IsBadReadPtr.

    payload must be exactly ``bytes`` with length 1..1 MiB (empty rejected).
    The payload is copied into a live ctypes buffer laid out as
    0xA5*128 + payload + 0xA5*128; the actual API is called on the payload
    address with count == len(payload). The whole buffer is compared before and
    after the call and the payload pointer must be >= 0x10000. Returns
    int(actual BOOL) from the one real host call made here.

    This validates host surrogate bytes only -- not the original guest virtual
    addresses -- and is not an OS sandbox, SEH dispatcher, or a general safety
    guarantee.
    """
    if type(payload) is not bytes:
        raise TypeError(
            "payload must be exactly bytes, not %s"
            % (type(payload).__name__,)
        )

    n = len(payload)
    _check_byte_count(n, allow_zero=False)

    guard = _GUARD_BYTE * _GUARD_COUNT
    blob = guard + payload + guard
    size = len(blob)

    # Filled explicitly with memmove so no terminator/truncation is involved.
    # ``buf`` stays referenced (alive) across the API call below.
    buf = (ctypes.c_char * size)()
    ctypes.memmove(buf, blob, size)

    before = ctypes.string_at(buf, size)
    if before != blob:
        raise RuntimeError("surrogate buffer fill mismatch")

    base = ctypes.addressof(buf)
    ptr = base + _GUARD_COUNT
    if ptr < _MIN_HOST_PTR:
        raise ValueError(
            "surrogate payload address 0x%x is below 0x%x"
            % (ptr, _MIN_HOST_PTR)
        )

    result = _is_bad_read_ptr(ctypes.c_void_p(ptr), ctypes.c_size_t(n))

    after = ctypes.string_at(buf, size)
    if after != before:
        raise RuntimeError("surrogate buffer mutated by IsBadReadPtr")
    if ctypes.addressof(buf) != base:
        raise RuntimeError("surrogate buffer moved during IsBadReadPtr")

    return int(result)


def host_bad_read_null(count):
    """Probe a NULL host pointer with kernel32.IsBadReadPtr(count).

    count must be a strict non-bool int in 0..1 MiB; zero count is supported
    (IsBadReadPtr(NULL, 0) is issued as-is). No arbitrary host pointer is
    accepted. Returns int(actual BOOL) from the one real host call made here.
    """
    if isinstance(count, bool) or type(count) is not int:
        raise TypeError(
            "count must be a strict int (not bool), not %s"
            % (type(count).__name__,)
        )
    _check_byte_count(count, allow_zero=True)

    result = _is_bad_read_ptr(ctypes.c_void_p(None), ctypes.c_size_t(count))
    return int(result)
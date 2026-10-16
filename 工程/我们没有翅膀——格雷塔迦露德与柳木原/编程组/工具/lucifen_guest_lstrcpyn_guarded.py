"""Guarded guest-side lstrcpynA bridge: bounded ANSI prefix, one guest write."""

from lucifen_guest_ansi_prefix import read_ansi_prefix
from lucifen_host_ansi_guarded_copy import host_copy_bounded

_U32_MAX = 0xFFFFFFFF
_MAX_LIMIT = 4096


def _u32(value, name):
    if type(value) is not int:
        raise TypeError("%s must be int" % name)
    if not 1 <= value <= _U32_MAX:
        raise ValueError("%s must be a positive u32" % name)
    return value


def _limit(value):
    if type(value) is not int:
        raise TypeError("limit must be int")
    if not 1 <= value <= _MAX_LIMIT:
        raise ValueError("limit must be in 1..%d" % _MAX_LIMIT)
    return value


def _blob(value, name):
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError("%s must be bytes-like" % name)
    return bytes(value)


def bridge_lstrcpyn_bounded(read, write, destination, source, limit):
    """Return guest destination after copying a bounded ANSI prefix."""
    dest = _u32(destination, "destination")
    src = _u32(source, "source")
    n = _limit(limit)
    if dest + n > _U32_MAX + 1:
        raise ValueError("destination + limit overflows u32")
    if src < dest + n and dest < src + n:  # conservative overlap rejection
        raise ValueError("source and destination ranges overlap")
    prefix = _blob(read_ansi_prefix(read, src, n), "prefix")
    if len(prefix) > n:
        raise ValueError("read_ansi_prefix exceeded limit")
    before = _blob(read(dest, n), "before")
    if len(before) != n:
        raise ValueError("read must return exactly limit bytes")
    out = _blob(host_copy_bounded(prefix, before), "out")
    if len(out) != n:
        raise ValueError("host_copy_bounded must return exactly limit bytes")
    write(dest, out)
    return dest

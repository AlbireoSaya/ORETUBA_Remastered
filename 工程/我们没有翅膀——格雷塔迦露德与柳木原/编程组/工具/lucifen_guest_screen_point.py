"""Decode a Win32 LPARAM screen point into signed 16-bit coordinates."""

__all__ = ["decode_screen_point_lparam"]

_INT_MIN = -(2 ** 31)
_INT_MAX = 2 ** 32 - 1
_MASK32 = 0xFFFFFFFF
_MASK16 = 0xFFFF
_SIGN16 = 0x8000
_WRAP16 = 0x10000

def _is_exact_int(value):
    return type(value) is int

def _signed16(raw):
    if raw >= _SIGN16:
        return raw - _WRAP16
    return raw

def decode_screen_point_lparam(value):
    """Decode an LPARAM packing two signed 16-bit coordinates.

    Accepts only an exact builtin ``int`` (never ``bool`` or an ``int``
    subclass) within [-2**31, 2**32 - 1]. The value is normalized to an
    unsigned 32-bit pattern, then low/high 16-bit halves are reinterpreted
    as signed 16-bit integers and returned as ``(x, y)``.
    """
    if not _is_exact_int(value):
        raise ValueError("value must be an exact builtin int, not bool")
    if value < _INT_MIN or value > _INT_MAX:
        raise ValueError("value out of range for a 32-bit LPARAM")
    packed = value & _MASK32
    x = _signed16(packed & _MASK16)
    y = _signed16((packed >> 16) & _MASK16)
    return (x, y)
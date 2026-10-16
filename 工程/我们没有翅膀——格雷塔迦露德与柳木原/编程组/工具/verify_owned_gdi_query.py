"""Verify an owned 4x4 top-down 32bpp DIB HBITMAP via GetObjectA only."""
import ctypes
from ctypes import wintypes

import lucifen_host_gdi_object_query as _gdi

_GUARD = 32
_A5 = b"\xa5" * _GUARD
_EXPECTED = (("bmWidth", 4), ("bmHeight", 4), ("bmWidthBytes", 16), ("bmPlanes", 1), ("bmBitsPixel", 32))


class _BITMAP(ctypes.Structure):
    _fields_ = (
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p),
    )


def _address(value):
    if value is None or isinstance(value, int):
        return value
    return ctypes.cast(value, ctypes.c_void_p).value


def check_owned_gdi_query(bitmap, bits):
    size = ctypes.sizeof(_BITMAP)
    buf = ctypes.create_string_buffer(_GUARD + size + _GUARD)
    ctypes.memset(buf, 0xA5, _GUARD)
    ctypes.memset(ctypes.byref(buf, _GUARD + size), 0xA5, _GUARD)
    got = _gdi.GetObjectA(bitmap, size, ctypes.byref(buf, _GUARD))
    if got != size:
        raise AssertionError("GetObjectA returned %r, expected %d" % (got, size))
    raw = buf.raw
    if raw[:_GUARD] != _A5 or raw[_GUARD + size:] != _A5:
        raise AssertionError("guard sentinel corrupted around BITMAP buffer")
    info = _BITMAP.from_buffer_copy(raw[_GUARD:_GUARD + size])
    for name, want in _EXPECTED:
        if getattr(info, name) != want:
            raise AssertionError("%s=%r, expected %r" % (name, getattr(info, name), want))
    if info.bmBits != _address(bits):
        raise AssertionError("bmBits=%r, expected %r" % (info.bmBits, _address(bits)))
    return size

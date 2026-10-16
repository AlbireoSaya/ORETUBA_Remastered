import ctypes
from lucifen_host_cursor_get import POINT


class FIXED(ctypes.Structure):
    _fields_ = [
        ("fract", ctypes.c_uint16),
        ("value", ctypes.c_int16),
    ]


class MAT2(ctypes.Structure):
    _fields_ = [
        ("eM11", FIXED),
        ("eM12", FIXED),
        ("eM21", FIXED),
        ("eM22", FIXED),
    ]


class GLYPHMETRICS(ctypes.Structure):
    _fields_ = [
        ("gmBlackBoxX", ctypes.c_uint32),
        ("gmBlackBoxY", ctypes.c_uint32),
        ("gmptGlyphOrigin", POINT),
        ("gmCellIncX", ctypes.c_int16),
        ("gmCellIncY", ctypes.c_int16),
    ]

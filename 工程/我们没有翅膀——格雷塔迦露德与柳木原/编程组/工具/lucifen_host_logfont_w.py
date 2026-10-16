import ctypes


class LOGFONTW(ctypes.Structure):
    _fields_ = [
        ("lfHeight", ctypes.c_int32),
        ("lfWidth", ctypes.c_int32),
        ("lfEscapement", ctypes.c_int32),
        ("lfOrientation", ctypes.c_int32),
        ("lfWeight", ctypes.c_int32),
        ("lfItalic", ctypes.c_ubyte),
        ("lfUnderline", ctypes.c_ubyte),
        ("lfStrikeOut", ctypes.c_ubyte),
        ("lfCharSet", ctypes.c_ubyte),
        ("lfOutPrecision", ctypes.c_ubyte),
        ("lfClipPrecision", ctypes.c_ubyte),
        ("lfQuality", ctypes.c_ubyte),
        ("lfPitchAndFamily", ctypes.c_ubyte),
        ("lfFaceName", ctypes.c_wchar * 32),
    ]

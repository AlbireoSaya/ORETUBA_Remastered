import ctypes

TRANSPARENT = 1
OPAQUE = 2

_gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

TextOutA = _gdi32.TextOutA
TextOutA.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int)
TextOutA.restype = ctypes.c_int

SetBkMode = _gdi32.SetBkMode
SetBkMode.argtypes = (ctypes.c_void_p, ctypes.c_int)
SetBkMode.restype = ctypes.c_int

__all__ = ("TextOutA", "SetBkMode", "TRANSPARENT", "OPAQUE")

import ctypes

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

GdiFlush = gdi32.GdiFlush
GdiFlush.argtypes = []
GdiFlush.restype = ctypes.c_int

__all__ = ["GdiFlush"]

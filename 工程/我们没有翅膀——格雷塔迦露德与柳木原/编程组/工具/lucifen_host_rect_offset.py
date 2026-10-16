import ctypes
from lucifen_host_nccalcsize import RECT
system = ctypes.WinDLL('user32', use_last_error=True)
OffsetRect = system.OffsetRect
OffsetRect.argtypes = [ctypes.POINTER(RECT), ctypes.c_int, ctypes.c_int]
OffsetRect.restype = ctypes.c_int
__all__ = ['OffsetRect']

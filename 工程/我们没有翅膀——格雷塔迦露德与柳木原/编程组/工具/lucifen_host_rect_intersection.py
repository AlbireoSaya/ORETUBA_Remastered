import ctypes
from lucifen_host_nccalcsize import RECT

system = ctypes.WinDLL('user32', use_last_error=True)

IntersectRect = system.IntersectRect
IntersectRect.argtypes = [ctypes.POINTER(RECT), ctypes.POINTER(RECT), ctypes.POINTER(RECT)]
IntersectRect.restype = ctypes.c_int

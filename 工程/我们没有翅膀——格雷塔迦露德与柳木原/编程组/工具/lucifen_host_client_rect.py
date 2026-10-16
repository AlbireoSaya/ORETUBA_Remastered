import ctypes

from lucifen_host_nccalcsize import RECT

system = ctypes.WinDLL('user32', use_last_error=True)

GetClientRect = system.GetClientRect
GetClientRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
GetClientRect.restype = ctypes.c_int

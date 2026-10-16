import ctypes

from lucifen_host_nccalcsize import RECT

system = ctypes.WinDLL("user32", use_last_error=True)

GetWindowRect = system.GetWindowRect
GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
GetWindowRect.restype = ctypes.c_int

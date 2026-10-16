import ctypes
from lucifen_host_text_extent_w import SIZE

system = ctypes.WinDLL('gdi32', use_last_error=True)

GetTextExtentPoint32A = system.GetTextExtentPoint32A
GetTextExtentPoint32A.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(SIZE)]
GetTextExtentPoint32A.restype = ctypes.c_int

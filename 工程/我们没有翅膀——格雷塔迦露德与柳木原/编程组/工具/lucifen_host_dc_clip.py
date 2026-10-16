import ctypes
from lucifen_host_nccalcsize import RECT

system = ctypes.WinDLL("gdi32", use_last_error=True)

GetClipBox = system.GetClipBox
GetClipBox.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
GetClipBox.restype = ctypes.c_int

ERROR = 0
NULLREGION = 1
SIMPLEREGION = 2
COMPLEXREGION = 3

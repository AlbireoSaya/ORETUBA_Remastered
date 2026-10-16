import ctypes
from lucifen_host_cursor_get import POINT
system=ctypes.WinDLL('user32',use_last_error=True)
ClientToScreen=system.ClientToScreen
ClientToScreen.argtypes=[ctypes.c_void_p,ctypes.POINTER(POINT)]
ClientToScreen.restype=ctypes.c_int

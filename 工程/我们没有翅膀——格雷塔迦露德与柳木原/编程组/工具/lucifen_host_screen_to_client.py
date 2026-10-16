import ctypes

from lucifen_host_cursor_get import POINT


system = ctypes.WinDLL('user32', use_last_error=True)

ScreenToClient = system.ScreenToClient
ScreenToClient.argtypes = [ctypes.c_void_p, ctypes.POINTER(POINT)]
ScreenToClient.restype = ctypes.c_int

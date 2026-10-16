import ctypes

system = ctypes.WinDLL("user32", use_last_error=True)
GetCursor = system.GetCursor
GetCursor.argtypes = []
GetCursor.restype = ctypes.c_void_p
__all__ = ["GetCursor"]

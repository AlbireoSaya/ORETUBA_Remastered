import ctypes

system = ctypes.WinDLL("user32", use_last_error=True)
SetCursor = system.SetCursor
SetCursor.argtypes = [ctypes.c_void_p]
SetCursor.restype = ctypes.c_void_p

__all__ = ["SetCursor"]
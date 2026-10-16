import ctypes

system = ctypes.WinDLL('user32', use_last_error=True)
SetCursorPos = system.SetCursorPos
SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
SetCursorPos.restype = ctypes.c_int

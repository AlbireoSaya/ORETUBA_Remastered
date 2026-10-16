import ctypes
system = ctypes.WinDLL('user32', use_last_error=True)
IsWindowEnabled = system.IsWindowEnabled
IsWindowEnabled.argtypes = [ctypes.c_void_p]
IsWindowEnabled.restype = ctypes.c_int

import ctypes
system = ctypes.WinDLL('user32', use_last_error=True)
IsIconic = system.IsIconic
IsIconic.argtypes = [ctypes.c_void_p]
IsIconic.restype = ctypes.c_int

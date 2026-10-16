import ctypes
system = ctypes.WinDLL('gdi32', use_last_error=True)
SaveDC = system.SaveDC
SaveDC.argtypes = [ctypes.c_void_p]
SaveDC.restype = ctypes.c_int

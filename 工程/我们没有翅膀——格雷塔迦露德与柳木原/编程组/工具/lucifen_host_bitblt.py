import ctypes

system = ctypes.WinDLL('gdi32', use_last_error=True)
BitBlt = system.BitBlt
BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
BitBlt.restype = ctypes.c_int

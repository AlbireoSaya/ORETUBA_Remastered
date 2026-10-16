import ctypes
system = ctypes.WinDLL('gdi32', use_last_error=True)
GetPixel = system.GetPixel
GetPixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
GetPixel.restype = ctypes.c_uint32
CLR_INVALID = 0xFFFFFFFF

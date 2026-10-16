import ctypes

system = ctypes.WinDLL('gdi32', use_last_error=True)

system.StretchBlt.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint32,
]
system.StretchBlt.restype = ctypes.c_int
StretchBlt = system.StretchBlt

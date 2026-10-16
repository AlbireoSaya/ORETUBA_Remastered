import ctypes

system = ctypes.WinDLL('gdi32', use_last_error=True)

system.SetDIBitsToDevice.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
]

system.SetDIBitsToDevice.restype = ctypes.c_int
SetDIBitsToDevice = system.SetDIBitsToDevice

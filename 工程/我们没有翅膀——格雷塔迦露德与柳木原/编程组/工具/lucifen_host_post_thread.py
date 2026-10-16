import ctypes
system=ctypes.WinDLL('user32',use_last_error=True)
PostThreadMessageA=system.PostThreadMessageA
PostThreadMessageA.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_size_t,ctypes.c_ssize_t]
PostThreadMessageA.restype=ctypes.c_int

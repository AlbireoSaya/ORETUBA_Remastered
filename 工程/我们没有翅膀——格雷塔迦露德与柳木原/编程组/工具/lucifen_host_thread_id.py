import ctypes
system = ctypes.WinDLL('kernel32', use_last_error=True)
GetThreadId = system.GetThreadId
GetThreadId.argtypes = [ctypes.c_void_p]
GetThreadId.restype = ctypes.c_uint32

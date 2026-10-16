import ctypes
system=ctypes.WinDLL('kernel32',use_last_error=True)
GetThreadPriority=system.GetThreadPriority
GetThreadPriority.argtypes=[ctypes.c_void_p]
GetThreadPriority.restype=ctypes.c_int

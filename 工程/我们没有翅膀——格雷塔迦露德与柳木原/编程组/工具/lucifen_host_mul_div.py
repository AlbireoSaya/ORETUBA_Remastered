import ctypes
system=ctypes.WinDLL('kernel32',use_last_error=True)
MulDiv=system.MulDiv
MulDiv.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int]
MulDiv.restype=ctypes.c_int

import ctypes
system = ctypes.WinDLL('gdi32', use_last_error=True)
GetTextFaceW = system.GetTextFaceW
GetTextFaceW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
GetTextFaceW.restype = ctypes.c_int

import ctypes
system = ctypes.WinDLL('gdi32', use_last_error=True)
GetTextAlign = system.GetTextAlign
GetTextAlign.argtypes = [ctypes.c_void_p]
GetTextAlign.restype = ctypes.c_uint32
SetTextAlign = system.SetTextAlign
SetTextAlign.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
SetTextAlign.restype = ctypes.c_uint32

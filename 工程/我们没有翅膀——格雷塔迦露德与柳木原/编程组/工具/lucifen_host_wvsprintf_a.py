import ctypes

system = ctypes.WinDLL("user32", use_last_error=True)

wvsprintfA = system.wvsprintfA
wvsprintfA.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
wvsprintfA.restype = ctypes.c_int

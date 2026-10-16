import ctypes

system = ctypes.WinDLL("user32", use_last_error=True)

SetCapture = system.SetCapture
SetCapture.argtypes = [ctypes.c_void_p]
SetCapture.restype = ctypes.c_void_p

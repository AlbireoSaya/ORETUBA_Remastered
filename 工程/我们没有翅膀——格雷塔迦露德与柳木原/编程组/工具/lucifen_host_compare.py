import ctypes

k = ctypes.WinDLL("kernel32", use_last_error=True)

lstrcmpA = k.lstrcmpA
lstrcmpA.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lstrcmpA.restype = ctypes.c_int
from ctypes import WinDLL, c_char_p, c_void_p, c_int

k = WinDLL("kernel32", use_last_error=True)

FindFirstFileA = k.FindFirstFileA
FindFirstFileA.argtypes = [c_char_p, c_void_p]
FindFirstFileA.restype = c_void_p

FindNextFileA = k.FindNextFileA
FindNextFileA.argtypes = [c_void_p, c_void_p]
FindNextFileA.restype = c_int

FindClose = k.FindClose
FindClose.argtypes = [c_void_p]
FindClose.restype = c_int
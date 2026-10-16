import ctypes

user32 = ctypes.WinDLL('user32.dll', use_last_error=True)

CharLowerA = user32.CharLowerA
CharLowerA.argtypes = [ctypes.c_void_p]
CharLowerA.restype = ctypes.c_void_p

CharUpperA = user32.CharUpperA
CharUpperA.argtypes = [ctypes.c_void_p]
CharUpperA.restype = ctypes.c_void_p

import ctypes

system=ctypes.WinDLL('user32', use_last_error=True)

RegisterWindowMessageA=system.RegisterWindowMessageA
RegisterWindowMessageA.argtypes=[ctypes.c_char_p]
RegisterWindowMessageA.restype=ctypes.c_uint32

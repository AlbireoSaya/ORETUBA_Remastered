import ctypes
system = ctypes.WinDLL('user32', use_last_error=True)
GetAsyncKeyState = system.GetAsyncKeyState
GetAsyncKeyState.argtypes = [ctypes.c_int]
GetAsyncKeyState.restype = ctypes.c_int16

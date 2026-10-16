import ctypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)

_GetForegroundWindow = _user32.GetForegroundWindow
_GetForegroundWindow.argtypes = []
_GetForegroundWindow.restype = ctypes.c_void_p

GetForegroundWindow = _GetForegroundWindow


def host_foreground_get():
    return GetForegroundWindow()

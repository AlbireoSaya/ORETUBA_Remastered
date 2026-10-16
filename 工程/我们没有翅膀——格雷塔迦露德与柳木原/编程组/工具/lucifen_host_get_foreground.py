# ISSUE-20261011-02-original-fidelity
import ctypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)
GetForegroundWindow = _user32.GetForegroundWindow
GetForegroundWindow.argtypes = []
GetForegroundWindow.restype = ctypes.c_void_p
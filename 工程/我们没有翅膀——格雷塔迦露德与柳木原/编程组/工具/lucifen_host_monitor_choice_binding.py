"""Raw ctypes bindings for user32 monitor choice.

Caller: guard a 16-byte RECT or pass a full owned mapped host HWND.
Borrow the returned HMONITOR; never CloseHandle/Destroy it.
c_void_p preserves full pointer and real NULL/non-NULL.
"""

import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

MonitorFromRect = user32.MonitorFromRect
MonitorFromRect.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
MonitorFromRect.restype = ctypes.c_void_p

MonitorFromWindow = user32.MonitorFromWindow
MonitorFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
MonitorFromWindow.restype = ctypes.c_void_p

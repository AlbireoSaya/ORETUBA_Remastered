"""ctypes binding for the Win32 user32!SetForegroundWindow entry point.

Declaration-only module: it imports the system ``user32`` library and exposes a
single public alias, ``SetForegroundWindow``, with an explicit, typed signature.
No window handle is resolved and no call is issued at import time.
"""

import ctypes

__all__ = ["SetForegroundWindow"]

# System library import; use_last_error preserves the thread's last-error code
# so it can be read back through ctypes.get_last_error() after an invocation.
_user32 = ctypes.WinDLL("user32", use_last_error=True)

# BOOL SetForegroundWindow(HWND hWnd);
# HWND is an opaque pointer-sized handle (c_void_p); BOOL is a 32-bit int.
SetForegroundWindow = _user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.c_void_p]
SetForegroundWindow.restype = ctypes.c_int

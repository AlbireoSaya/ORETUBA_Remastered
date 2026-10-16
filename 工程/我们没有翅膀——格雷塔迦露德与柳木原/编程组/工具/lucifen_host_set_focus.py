"""Raw ctypes binding for user32.SetFocus (candidate delivery).

Scope is strictly the binding itself:
  * no call
  * no wrapper
  * no main

The binding keeps the native full-width pointer return value: the previous
HWND, or NULL when no window had focus. NULL is a legitimate result and is
never treated as failure. No error check, no translation, no truncation.
"""

import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

SetFocus = user32.SetFocus
SetFocus.argtypes = [ctypes.c_void_p]
SetFocus.restype = ctypes.c_void_p

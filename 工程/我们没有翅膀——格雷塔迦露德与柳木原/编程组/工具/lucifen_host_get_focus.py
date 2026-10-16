"""Raw ctypes binding for user32!GetFocus (declaration only).

Scope: no call site, no wrapper, no main/CLI entry point, no cached or
synthesized handle. Only the system user32 DLL is loaded; no original game
module is loaded, probed, or mutated.
"""

import ctypes

# System user32 only; use_last_error=True keeps ctypes.get_last_error() valid.
user32 = ctypes.WinDLL("user32", use_last_error=True)

# HWND GetFocus(void);
GetFocus = user32.GetFocus
GetFocus.argtypes = []
GetFocus.restype = ctypes.c_void_p

__all__ = ["GetFocus"]
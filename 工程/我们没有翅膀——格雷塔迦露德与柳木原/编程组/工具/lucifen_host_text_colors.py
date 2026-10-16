"""Win32 GDI text/background colour entry points (declarations only).

Loads ``gdi32`` and binds the four colour accessors to typed prototypes.
Nothing is invoked at import time, and no handle is created here: callers
supply an existing HDC (a pointer-sized integer) as the first argument.

A COLORREF is a 32-bit ``0x00BBGGRR`` value (low byte = red).
"""

import ctypes

__all__ = [
    "system",
    "GetTextColor",
    "GetBkColor",
    "SetTextColor",
    "SetBkColor",
]

system = ctypes.WinDLL("gdi32", use_last_error=True)

# COLORREF GetTextColor(HDC hdc);
GetTextColor = system.GetTextColor
GetTextColor.argtypes = [ctypes.c_void_p]
GetTextColor.restype = ctypes.c_uint32

# COLORREF GetBkColor(HDC hdc);
GetBkColor = system.GetBkColor
GetBkColor.argtypes = [ctypes.c_void_p]
GetBkColor.restype = ctypes.c_uint32

# COLORREF SetTextColor(HDC hdc, COLORREF color);
SetTextColor = system.SetTextColor
SetTextColor.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
SetTextColor.restype = ctypes.c_uint32

# COLORREF SetBkColor(HDC hdc, COLORREF color);
SetBkColor = system.SetBkColor
SetBkColor.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
SetBkColor.restype = ctypes.c_uint32

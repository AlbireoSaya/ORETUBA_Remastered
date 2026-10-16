from __future__ import annotations

import ctypes


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
    ]


system = ctypes.WinDLL("user32", use_last_error=True)

GetCursorPos = system.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
GetCursorPos.restype = ctypes.c_int

__all__ = ["POINT", "system", "GetCursorPos"]

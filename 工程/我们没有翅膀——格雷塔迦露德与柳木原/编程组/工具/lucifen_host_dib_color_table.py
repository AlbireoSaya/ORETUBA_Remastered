"""GDI DIB color-table bindings for the Lucifen host SDK.

Provides the RGBQUAD structure plus the SetDIBColorTable / GetDIBColorTable
entry points exported by gdi32.

Import-time behavior is limited to loading gdi32 (use_last_error=True):
no GDI API is invoked and no GDI object is allocated while importing.
"""

from __future__ import annotations

import ctypes

__all__ = ["RGBQUAD", "SetDIBColorTable", "GetDIBColorTable"]

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)


class RGBQUAD(ctypes.Structure):
    """Win32 RGBQUAD: four BYTE fields, byte-packed, total size 4."""

    _fields_ = [
        ("rgbBlue", ctypes.c_ubyte),
        ("rgbGreen", ctypes.c_ubyte),
        ("rgbRed", ctypes.c_ubyte),
        ("rgbReserved", ctypes.c_ubyte),
    ]


assert ctypes.sizeof(RGBQUAD) == 4

HDC = ctypes.c_void_p
UINT = ctypes.c_uint32
LPRGBQUAD = ctypes.POINTER(RGBQUAD)

SetDIBColorTable = gdi32.SetDIBColorTable
SetDIBColorTable.argtypes = [HDC, UINT, UINT, LPRGBQUAD]
SetDIBColorTable.restype = UINT

GetDIBColorTable = gdi32.GetDIBColorTable
GetDIBColorTable.argtypes = [HDC, UINT, UINT, LPRGBQUAD]
GetDIBColorTable.restype = UINT

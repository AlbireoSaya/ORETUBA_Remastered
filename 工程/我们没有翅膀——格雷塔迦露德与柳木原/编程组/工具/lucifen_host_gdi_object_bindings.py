"""Raw ctypes bindings for the host gdi32 object calls used by this package.

Callers are responsible for validation of fullhostHDC and HBITMAP handles, for
tracking owned versus borrowed stock objects and old objects, and for ensuring
an own bitmap is unselected before DeleteObject. Owned DCs must be released with
DeleteDC, while borrowed DCs must be released with ReleaseDC. Callers must also
guard BITMAPINFO and bits buffer lifetime and bounds. This module performs no
automatic address checks, sandboxing, operation calls, or original game OS
loading; it only loads the system gdi32 library.
"""

import ctypes

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

CreateCompatibleDC = gdi32.CreateCompatibleDC
CreateCompatibleDC.argtypes = [ctypes.c_void_p]
CreateCompatibleDC.restype = ctypes.c_void_p

SelectObject = gdi32.SelectObject
SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
SelectObject.restype = ctypes.c_void_p

DeleteObject = gdi32.DeleteObject
DeleteObject.argtypes = [ctypes.c_void_p]
DeleteObject.restype = ctypes.c_int

GetStockObject = gdi32.GetStockObject
GetStockObject.argtypes = [ctypes.c_int]
GetStockObject.restype = ctypes.c_void_p

CreateDIBSection = gdi32.CreateDIBSection
CreateDIBSection.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p,
    ctypes.c_uint32,
]
CreateDIBSection.restype = ctypes.c_void_p

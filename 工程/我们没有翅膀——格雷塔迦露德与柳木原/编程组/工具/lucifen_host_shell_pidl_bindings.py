"""Raw ctypes bindings to shell32/ole32 for caller-managed PIDL work.

Caller owns workspace paths, host PIDL validity, buffers, and all ownership.
"""

import ctypes
from ctypes import POINTER, c_int, c_int32, c_uint32, c_void_p

shell32 = ctypes.WinDLL("shell32", use_last_error=True)
ole32 = ctypes.WinDLL("ole32", use_last_error=True)

SHParseDisplayName = shell32.SHParseDisplayName
SHParseDisplayName.argtypes = [
    c_void_p,
    c_void_p,
    POINTER(c_void_p),
    c_uint32,
    POINTER(c_uint32),
]
SHParseDisplayName.restype = c_int32

SHGetPathFromIDListA = shell32.SHGetPathFromIDListA
SHGetPathFromIDListA.argtypes = [c_void_p, c_void_p]
SHGetPathFromIDListA.restype = c_int

CoTaskMemFree = ole32.CoTaskMemFree
CoTaskMemFree.argtypes = [c_void_p]
CoTaskMemFree.restype = None

__all__ = [
    "shell32",
    "ole32",
    "SHParseDisplayName",
    "SHGetPathFromIDListA",
    "CoTaskMemFree",
]

"""Read-only binding for the ANSI EnumDisplaySettingsExA host display enumeration API."""

import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumDisplaySettingsExA = user32.EnumDisplaySettingsExA
EnumDisplaySettingsExA.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_uint32,
]
EnumDisplaySettingsExA.restype = ctypes.c_int

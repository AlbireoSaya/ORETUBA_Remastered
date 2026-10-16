from ctypes import WinDLL, c_void_p, c_int, c_uint32

__all__ = [
    "SWP_NOSIZE",
    "SWP_NOMOVE",
    "SWP_NOACTIVATE",
    "SetWindowPos",
]

SWP_NOSIZE = 1
SWP_NOMOVE = 2
SWP_NOACTIVATE = 16

_user32 = WinDLL("user32", use_last_error=True)

SetWindowPos = _user32.SetWindowPos
SetWindowPos.argtypes = [c_void_p, c_void_p, c_int, c_int, c_int, c_int, c_uint32]
SetWindowPos.restype = c_int

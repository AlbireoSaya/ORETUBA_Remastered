"""user32!PostMessageA binding. Caller owns HWND; no helper, no broadcast default."""
import ctypes
from ctypes import c_void_p, c_uint32, c_size_t, c_ssize_t, c_int

__all__ = ["PostMessageA"]

user32 = ctypes.WinDLL("user32", use_last_error=True)
PostMessageA = user32.PostMessageA
PostMessageA.argtypes = [c_void_p, c_uint32, c_size_t, c_ssize_t]
PostMessageA.restype = c_int

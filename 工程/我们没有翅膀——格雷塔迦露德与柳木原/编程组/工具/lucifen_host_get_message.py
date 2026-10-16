from ctypes import POINTER, WinDLL, c_int, c_uint32, c_void_p

from lucifen_host_msg_types import MSG

user32 = WinDLL("user32", use_last_error=True)

GetMessageA = user32.GetMessageA
GetMessageA.argtypes = [POINTER(MSG), c_void_p, c_uint32, c_uint32]
GetMessageA.restype = c_int

__all__ = ["GetMessageA"]

import ctypes
from lucifen_host_msg_types import MSG

system = ctypes.WinDLL('user32', use_last_error=True)

PeekMessageA = system.PeekMessageA
PeekMessageA.argtypes = [ctypes.POINTER(MSG), ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
PeekMessageA.restype = ctypes.c_int

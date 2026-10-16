import ctypes

from lucifen_host_msg_types import MSG

system = ctypes.WinDLL('user32', use_last_error=True)

DispatchMessageA = system.DispatchMessageA
DispatchMessageA.argtypes = [ctypes.POINTER(MSG)]
DispatchMessageA.restype = ctypes.c_ssize_t

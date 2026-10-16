import ctypes
from lucifen_host_msg_types import MSG

system = ctypes.WinDLL('user32', use_last_error=True)
TranslateMessage = system.TranslateMessage
TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
TranslateMessage.restype = ctypes.c_int

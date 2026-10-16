from ctypes import POINTER, c_int, c_void_p, WinDLL

from lucifen_host_msg_types import MSG

user32 = WinDLL("user32", use_last_error=True)

TranslateAcceleratorA = user32.TranslateAcceleratorA
TranslateAcceleratorA.argtypes = [c_void_p, c_void_p, POINTER(MSG)]
TranslateAcceleratorA.restype = c_int

__all__ = ["TranslateAcceleratorA"]

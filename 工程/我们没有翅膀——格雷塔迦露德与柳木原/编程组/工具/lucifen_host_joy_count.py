import ctypes

_winmm = ctypes.WinDLL('winmm', use_last_error=True)

joyGetNumDevs = _winmm.joyGetNumDevs
joyGetNumDevs.argtypes = []
joyGetNumDevs.restype = ctypes.c_uint32

__all__ = ['joyGetNumDevs']
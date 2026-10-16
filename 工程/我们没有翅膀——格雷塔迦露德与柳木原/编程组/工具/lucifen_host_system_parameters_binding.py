"""Raw ctypes binding for user32.SystemParametersInfoA.

Caller whitelist (NOT enforced by this raw binding): SPI_GETWORKAREA=0x30,
uiParam=0, fWinIni=0, read-only, guarded 16-byte RECT copy. This raw binding
does NOT enforce whitelist, bounds or sandbox; no guest pointer is passed to
the OS and full host pointers are preserved.
"""
import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
SystemParametersInfoA = user32.SystemParametersInfoA
SystemParametersInfoA.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
SystemParametersInfoA.restype = ctypes.c_int

"""Win32 user32.ReleaseCapture raw declaration only - no call at import."""
import ctypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)
ReleaseCapture = _user32.ReleaseCapture
ReleaseCapture.argtypes = []
ReleaseCapture.restype = ctypes.c_int

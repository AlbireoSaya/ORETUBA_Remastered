"""user32!EndPaint binding. Caller must pair with BeginPaint; never substitute ReleaseDC."""
import ctypes

from lucifen_host_paint_types import PAINTSTRUCT

__all__ = ["EndPaint"]

system = ctypes.WinDLL("user32", use_last_error=True)
EndPaint = system.EndPaint
EndPaint.argtypes = [ctypes.c_void_p, ctypes.POINTER(PAINTSTRUCT)]
EndPaint.restype = ctypes.c_int32

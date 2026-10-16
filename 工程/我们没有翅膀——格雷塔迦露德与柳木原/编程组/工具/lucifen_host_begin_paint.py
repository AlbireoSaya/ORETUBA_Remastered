"""自有 SDK 原始绑定：user32!BeginPaint(HWND, LPPAINTSTRUCT*) -> HDC。"""
import ctypes

from lucifen_host_paint_types import PAINTSTRUCT

__all__ = ["BeginPaint"]

system = ctypes.WinDLL("user32", use_last_error=True)
BeginPaint = system.BeginPaint
BeginPaint.argtypes = [ctypes.c_void_p, ctypes.POINTER(PAINTSTRUCT)]
BeginPaint.restype = ctypes.c_void_p
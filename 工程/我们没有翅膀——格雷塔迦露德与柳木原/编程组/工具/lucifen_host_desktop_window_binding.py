"""装载系统 user32；caller 借用 host HWND 映射 guest token，保留完整 host 指针，不能关闭 desktop，禁止 OS 执行 guest callback。本文件不是 window 实现/桌面取证。"""

from ctypes import WinDLL, c_void_p, c_int

user32 = WinDLL("user32", use_last_error=True)

GetDesktopWindow = user32.GetDesktopWindow
GetDesktopWindow.argtypes = []
GetDesktopWindow.restype = c_void_p

IsWindow = user32.IsWindow
IsWindow.argtypes = [c_void_p]
IsWindow.restype = c_int

__all__ = ["user32", "GetDesktopWindow", "IsWindow"]
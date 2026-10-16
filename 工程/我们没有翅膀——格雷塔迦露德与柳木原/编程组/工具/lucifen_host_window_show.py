"""ShowWindow返回先前可见状态，不能按成功标志使用；最终状态由IsWindowVisible另查。"""
import ctypes

_user32 = ctypes.WinDLL('user32', use_last_error=True)

_user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
_user32.ShowWindow.restype = ctypes.c_int

_user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
_user32.IsWindowVisible.restype = ctypes.c_int
ShowWindow = _user32.ShowWindow
IsWindowVisible = _user32.IsWindowVisible
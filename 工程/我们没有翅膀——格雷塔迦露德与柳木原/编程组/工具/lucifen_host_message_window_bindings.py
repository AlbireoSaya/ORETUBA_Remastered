import ctypes
from ctypes import (
    POINTER,
    WINFUNCTYPE,
    c_int,
    c_int32,
    c_size_t,
    c_ssize_t,
    c_uint16,
    c_uint32,
    c_void_p,
    c_wchar_p,
)

WNDPROC = WINFUNCTYPE(c_ssize_t, c_void_p, c_uint32, c_size_t, c_ssize_t)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", c_uint32),
        ("style", c_uint32),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", c_int32),
        ("cbWndExtra", c_int32),
        ("hInstance", c_void_p),
        ("hIcon", c_void_p),
        ("hCursor", c_void_p),
        ("hbrBackground", c_void_p),
        ("lpszMenuName", c_wchar_p),
        ("lpszClassName", c_wchar_p),
        ("hIconSm", c_void_p),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.RegisterClassExW.argtypes = [POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = c_uint16

user32.UnregisterClassW.argtypes = [c_wchar_p, c_void_p]
user32.UnregisterClassW.restype = c_int

user32.CreateWindowExW.argtypes = [
    c_uint32,
    c_wchar_p,
    c_wchar_p,
    c_uint32,
    c_int32,
    c_int32,
    c_int32,
    c_int32,
    c_void_p,
    c_void_p,
    c_void_p,
    c_void_p,
]
user32.CreateWindowExW.restype = c_void_p

user32.DestroyWindow.argtypes = [c_void_p]
user32.DestroyWindow.restype = c_int

user32.DefWindowProcW.argtypes = [c_void_p, c_uint32, c_size_t, c_ssize_t]
user32.DefWindowProcW.restype = c_ssize_t

user32.SendMessageA.argtypes = [c_void_p, c_uint32, c_size_t, c_ssize_t]
user32.SendMessageA.restype = c_ssize_t

user32.IsWindow.argtypes = [c_void_p]
user32.IsWindow.restype = c_int

kernel32.GetModuleHandleW.argtypes = [c_void_p]
kernel32.GetModuleHandleW.restype = c_void_p
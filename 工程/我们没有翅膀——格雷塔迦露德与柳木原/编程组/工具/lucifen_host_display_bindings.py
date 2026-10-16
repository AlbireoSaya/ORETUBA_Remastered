import ctypes
import os

__all__ = [
    "GetSystemMetrics",
    "GetDC",
    "ReleaseDC",
    "GetDeviceCaps",
]

_c_int = ctypes.c_int
_c_void_p = ctypes.c_void_p

_user32 = None
_gdi32 = None

if os.name == "nt":
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    _user32.GetSystemMetrics.argtypes = [_c_int]
    _user32.GetSystemMetrics.restype = _c_int

    _user32.GetDC.argtypes = [_c_void_p]
    _user32.GetDC.restype = _c_void_p

    _user32.ReleaseDC.argtypes = [_c_void_p, _c_void_p]
    _user32.ReleaseDC.restype = _c_int

    _gdi32.GetDeviceCaps.argtypes = [_c_void_p, _c_int]
    _gdi32.GetDeviceCaps.restype = _c_int


def _require(lib):
    if lib is None:
        raise OSError("Win32 display bindings are only available on Windows")


def _as_handle(value):
    if value is None:
        return _c_void_p(None)
    if isinstance(value, _c_void_p):
        return value
    return _c_void_p(int(value))


def GetSystemMetrics(nIndex):
    """GetSystemMetrics(int nIndex) -> int"""
    _require(_user32)
    return int(_user32.GetSystemMetrics(int(nIndex)))


def GetDC(hWnd=None):
    """GetDC(void* HWND) -> void* HDC (NULL becomes None); full pointer width is preserved."""
    _require(_user32)
    return _user32.GetDC(_as_handle(hWnd))


def ReleaseDC(hWnd, hDC):
    """ReleaseDC(void* HWND, void* HDC) -> int"""
    _require(_user32)
    return int(_user32.ReleaseDC(_as_handle(hWnd), _as_handle(hDC)))


def GetDeviceCaps(hDC, nIndex):
    """GetDeviceCaps(void* HDC, int nIndex) -> int"""
    _require(_gdi32)
    return int(_gdi32.GetDeviceCaps(_as_handle(hDC), int(nIndex)))
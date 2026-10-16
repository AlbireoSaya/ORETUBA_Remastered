import ctypes
from ctypes import (
    POINTER,
    WINFUNCTYPE,
    WinDLL,
    c_char_p,
    c_int,
    c_int32,
    c_ssize_t,
    c_uint32,
    c_void_p,
)

__all__ = [
    "RECT",
    "MONITORENUMPROC",
    "user32",
    "gdi32",
    "EnumDisplayMonitors",
    "GetMonitorInfoA",
    "EnumDisplayDevicesA",
    "EnumDisplaySettingsA",
    "CreateDCA",
    "DeleteDC",
]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", c_int32),
        ("top", c_int32),
        ("right", c_int32),
        ("bottom", c_int32),
    ]


MONITORENUMPROC = WINFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(RECT), c_ssize_t)

user32 = WinDLL("user32", use_last_error=True)
gdi32 = WinDLL("gdi32", use_last_error=True)

EnumDisplayMonitors = user32.EnumDisplayMonitors
EnumDisplayMonitors.argtypes = [c_void_p, c_void_p, MONITORENUMPROC, c_ssize_t]
EnumDisplayMonitors.restype = c_int

GetMonitorInfoA = user32.GetMonitorInfoA
GetMonitorInfoA.argtypes = [c_void_p, c_void_p]
GetMonitorInfoA.restype = c_int

EnumDisplayDevicesA = user32.EnumDisplayDevicesA
EnumDisplayDevicesA.argtypes = [c_char_p, c_uint32, c_void_p, c_uint32]
EnumDisplayDevicesA.restype = c_int

EnumDisplaySettingsA = user32.EnumDisplaySettingsA
EnumDisplaySettingsA.argtypes = [c_char_p, c_uint32, c_void_p]
EnumDisplaySettingsA.restype = c_int

CreateDCA = gdi32.CreateDCA
CreateDCA.argtypes = [c_char_p, c_char_p, c_char_p, c_void_p]
CreateDCA.restype = c_void_p

DeleteDC = gdi32.DeleteDC
DeleteDC.argtypes = [c_void_p]
DeleteDC.restype = c_int
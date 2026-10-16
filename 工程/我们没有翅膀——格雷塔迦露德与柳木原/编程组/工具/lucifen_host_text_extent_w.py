import ctypes


class SIZE(ctypes.Structure):
    _fields_ = [
        ("cx", ctypes.c_int32),
        ("cy", ctypes.c_int32),
    ]


system = ctypes.WinDLL("gdi32", use_last_error=True)

GetTextExtentPoint32W = system.GetTextExtentPoint32W
GetTextExtentPoint32W.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.POINTER(SIZE),
]
GetTextExtentPoint32W.restype = ctypes.c_int

import ctypes


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
    ]


class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", POINT),
        ("ptMaxSize", POINT),
        ("ptMaxPosition", POINT),
        ("ptMinTrackSize", POINT),
        ("ptMaxTrackSize", POINT),
    ]


class CREATESTRUCTA(ctypes.Structure):
    _fields_ = [
        ("lpCreateParams", ctypes.c_void_p),
        ("hInstance", ctypes.c_void_p),
        ("hMenu", ctypes.c_void_p),
        ("hwndParent", ctypes.c_void_p),
        ("cy", ctypes.c_int32),
        ("cx", ctypes.c_int32),
        ("y", ctypes.c_int32),
        ("x", ctypes.c_int32),
        ("style", ctypes.c_int32),
        ("lpszName", ctypes.c_void_p),
        ("lpszClass", ctypes.c_void_p),
        ("dwExStyle", ctypes.c_uint32),
    ]

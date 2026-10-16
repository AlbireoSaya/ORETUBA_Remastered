import ctypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)

CreateWindowExA = _user32.CreateWindowExA
CreateWindowExA.argtypes = (
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
)
CreateWindowExA.restype = ctypes.c_void_p

DestroyWindow = _user32.DestroyWindow
DestroyWindow.argtypes = (ctypes.c_void_p,)
DestroyWindow.restype = ctypes.c_int

IsWindow = _user32.IsWindow
IsWindow.argtypes = (ctypes.c_void_p,)
IsWindow.restype = ctypes.c_int

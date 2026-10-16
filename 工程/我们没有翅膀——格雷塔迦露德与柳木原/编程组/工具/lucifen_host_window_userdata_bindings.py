import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

_PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)

if _PTR_SIZE == 4:
    GetWindowLongPtrA = user32.GetWindowLongA
    SetWindowLongPtrA = user32.SetWindowLongA
elif _PTR_SIZE == 8:
    GetWindowLongPtrA = user32.GetWindowLongPtrA
    SetWindowLongPtrA = user32.SetWindowLongPtrA
else:
    raise RuntimeError("unsupported c_void_p size: %d" % (_PTR_SIZE,))

GetWindowLongPtrA.argtypes = [ctypes.c_void_p, ctypes.c_int]
GetWindowLongPtrA.restype = ctypes.c_ssize_t

SetWindowLongPtrA.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
SetWindowLongPtrA.restype = ctypes.c_ssize_t

DefWindowProcA = user32.DefWindowProcA
DefWindowProcA.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_size_t, ctypes.c_ssize_t]
DefWindowProcA.restype = ctypes.c_ssize_t

import ctypes
system=ctypes.WinDLL('user32',use_last_error=True)
MsgWaitForMultipleObjects=system.MsgWaitForMultipleObjects
MsgWaitForMultipleObjects.argtypes=[ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32]
MsgWaitForMultipleObjects.restype=ctypes.c_uint32

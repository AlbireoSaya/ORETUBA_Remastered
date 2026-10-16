import ctypes
system=ctypes.WinDLL('user32',use_last_error=True)
GetQueueStatus=system.GetQueueStatus
GetQueueStatus.argtypes=[ctypes.c_uint32]
GetQueueStatus.restype=ctypes.c_uint32

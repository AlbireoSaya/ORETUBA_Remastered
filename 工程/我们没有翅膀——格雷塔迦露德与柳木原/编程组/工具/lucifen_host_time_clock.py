import ctypes
system=ctypes.WinDLL('winmm',use_last_error=True)
timeGetTime=system.timeGetTime
timeGetTime.argtypes=[]
timeGetTime.restype=ctypes.c_uint32
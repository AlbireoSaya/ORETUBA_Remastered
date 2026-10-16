import ctypes
system=ctypes.WinDLL('kernel32',use_last_error=True)
GetCurrentThread=system.GetCurrentThread
GetCurrentThread.argtypes=[]
GetCurrentThread.restype=ctypes.c_void_p

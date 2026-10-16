import ctypes

k = ctypes.WinDLL("kernel32", use_last_error=True)

GetLocalTime = k.GetLocalTime
GetLocalTime.argtypes = [ctypes.c_void_p]
GetLocalTime.restype = None

GetSystemTime = k.GetSystemTime
GetSystemTime.argtypes = [ctypes.c_void_p]
GetSystemTime.restype = None

QueryPerformanceCounter = k.QueryPerformanceCounter
QueryPerformanceCounter.argtypes = [ctypes.c_void_p]
QueryPerformanceCounter.restype = ctypes.c_int

QueryPerformanceFrequency = k.QueryPerformanceFrequency
QueryPerformanceFrequency.argtypes = [ctypes.c_void_p]
QueryPerformanceFrequency.restype = ctypes.c_int

GetTickCount = k.GetTickCount
GetTickCount.argtypes = []
GetTickCount.restype = ctypes.c_uint32
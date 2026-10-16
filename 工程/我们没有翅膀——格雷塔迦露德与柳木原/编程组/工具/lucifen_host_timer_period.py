import ctypes

system = ctypes.WinDLL('winmm', use_last_error=True)

timeBeginPeriod = system.timeBeginPeriod
timeBeginPeriod.argtypes = [ctypes.c_uint32]
timeBeginPeriod.restype = ctypes.c_uint32

timeEndPeriod = system.timeEndPeriod
timeEndPeriod.argtypes = [ctypes.c_uint32]
timeEndPeriod.restype = ctypes.c_uint32

"""Thread exit-code query binding (kernel32!GetExitCodeThread).

Generic Win32 SDK binding only. No game data, assets, or handles touched here.
"""

import ctypes

system = ctypes.WinDLL('kernel32', use_last_error=True)

GetExitCodeThread = system.GetExitCodeThread
GetExitCodeThread.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
GetExitCodeThread.restype = ctypes.c_int

"""lucifen_host_thread_create.py —— kernel32!CreateThread 纯签名绑定。

本模块仅做 ctypes 声明，不创建线程、不调用任何 API、
不把 guest 函数指针交给 OS、不提供任何包装器。
"""

import ctypes

HOST_THREADPROC = ctypes.WINFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)

system = ctypes.WinDLL('kernel32', use_last_error=True)

CreateThread = system.CreateThread
CreateThread.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    HOST_THREADPROC,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32),
]
CreateThread.restype = ctypes.c_void_p

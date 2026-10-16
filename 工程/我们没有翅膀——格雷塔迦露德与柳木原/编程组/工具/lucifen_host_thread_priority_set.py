# -*- coding: utf-8 -*-
"""thread_priority_set

仅绑定 kernel32.SetThreadPriority，不调用该函数，
不改变任何系统线程优先级。
"""

import ctypes

system = ctypes.WinDLL('kernel32', use_last_error=True)

SetThreadPriority = system.SetThreadPriority
SetThreadPriority.argtypes = [ctypes.c_void_p, ctypes.c_int]
SetThreadPriority.restype = ctypes.c_int

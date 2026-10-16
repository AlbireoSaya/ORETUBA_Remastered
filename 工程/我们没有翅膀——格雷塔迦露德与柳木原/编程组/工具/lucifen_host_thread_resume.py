# -*- coding: utf-8 -*-
"""lucifen_host_thread_resume —— 通用 SDK/字节格式工具（纯 ctypes 绑定层）

职责范围（严格限定）：
    仅绑定 Windows kernel32 中 ResumeThread 的调用签名，供上层
    thread_resume 候选逻辑按需调用。本模块自身：

    * 仅 import ctypes，不引入任何其它依赖；
    * 只做符号解析与 argtypes / restype 声明；
    * 不调用函数，不恢复任何实际线程，不产生任何副作用性系统调用。

契约：
    ResumeThread(ctypes.c_void_p(handle)) -> ctypes.c_uint32
        handle 为线程句柄（HANDLE），需具备 THREAD_SUSPEND_RESUME 权限。
        返回值为线程先前挂起计数；失败返回 0xFFFFFFFF
        （调用方须自行以 ctypes.get_last_error() / get_last_error 语义判定）。

备注：
    使用 use_last_error=True 使 ctypes 在每次调用后缓存 LastError，
    避免与其它库的 Win32 调用交叉污染错误码。
"""

import ctypes

# 仅加载 kernel32；use_last_error=True 以便按需读取缓存错误码。
system = ctypes.WinDLL('kernel32', use_last_error=True)

# 线程挂起计数恢复接口（HANDLE -> DWORD）。
ResumeThread = system.ResumeThread
ResumeThread.argtypes = [ctypes.c_void_p]
ResumeThread.restype = ctypes.c_uint32

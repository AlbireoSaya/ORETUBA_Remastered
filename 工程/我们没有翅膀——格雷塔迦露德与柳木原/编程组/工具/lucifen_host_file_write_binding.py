"""真实宿主 WriteFile 原型声明。

仅声明 kernel32!WriteFile 的 ctypes 原型，不打开文件、不调用 API、不加 errcheck。
caller 负责：精确的 workspace path 映射、owned 完整 host handle、
数据/计数 buffer 的 lifespan 与 guards、同步 overlapped 传 None、guest ABI 转换。
本模块不 sandbox、不自动校验 guest。
所有 writes 仅限 workspace；root 派单 branch issue/ISSUE-20261011-02-original-fidelity。
"""

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WriteFile = kernel32.WriteFile
WriteFile.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32),
    ctypes.c_void_p,
]
WriteFile.restype = ctypes.c_int
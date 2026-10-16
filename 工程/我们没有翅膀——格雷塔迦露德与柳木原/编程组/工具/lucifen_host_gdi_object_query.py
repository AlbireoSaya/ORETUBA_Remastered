"""lucifen_host_gdi_object_query

GDI 宿主侧对象查询通用声明模块（Windows）。

本模块只做两件事：

1. 加载 ``gdi32`` 动态库；
2. 为 ``GetObjectA`` 绑定调用签名（argtypes / restype）。

约束与边界：

* 导入期不调用任何 Win32 API，本模块不产生任何系统调用；
* 不分配、不校验缓冲区，指针合法性与缓冲区容量由调用方负责；
* 不含任何业务数据、游戏内容、凭据或环境相关配置。

声明签名（Win32）::

    int GetObjectA(HANDLE h, int c, LPVOID pv);

    h  : GDI 对象句柄（HBITMAP / HBRUSH / HPEN / HFONT / HPALETTE ...）
    c  : pv 所指向缓冲区的大小（字节）；传入 0 时返回所需字节数
    pv : 接收对象信息的缓冲区指针，可为 NULL

    返回值：成功时返回写入的字节数；失败时返回 0。

调用方错误处理约定（此处仅说明，不主动调用）：
    ``use_last_error=True`` 已开启，可在调用后使用
    ``ctypes.get_last_error()`` 取回线程局部错误码；但注意 GetObjectA
    失败时并不保证设置 last error，返回值 0 才是权威判据。

运行时要求：仅 Windows 平台可用（依赖 ``ctypes.WinDLL``）。
"""

import ctypes

__all__ = ["system", "GetObjectA"]

# gdi32 动态库句柄。use_last_error=True 使 last error 走 ctypes 线程局部存储。
system = ctypes.WinDLL("gdi32", use_last_error=True)

# GetObjectA 函数绑定与签名声明（仅声明，不调用）。
GetObjectA = system.GetObjectA
GetObjectA.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
GetObjectA.restype = ctypes.c_int

"""Win32 shell32 ``SHGetSpecialFolderPathA`` 泛用原生绑定（typed binding，只读查询用途）。

原型：``BOOL SHGetSpecialFolderPathA(HWND hwndOwner, LPSTR lpszPath, int csidl, BOOL fCreate)``。

调用方责任（本模块不做任何校验、也不调用该函数）：
- 传入的 ``lpszPath`` 必须指向至少 260 字节（MAX_PATH）的可写缓冲区；本绑定不做长度检查，
  缓冲区过小属于调用方错误，原生 API 可能截断或写入失败。
- 指针以 ``c_void_p`` 映射；调用方自行把字节缓冲（例如 ``ctypes.create_string_buffer(260)``）
  转换为指向首字节的整型地址后再传入，本模块不代为持有或生命周期管理。
- ``fCreate`` 策略由调用方决定：``fCreate=0`` 表示只查询、不创建目录；``fCreate=1`` 允许原生
  API 在目标 CSIDL 目录不存在时尝试创建。
- root 侧只使用 ``fCreate=0`` 的只读查询语义。原 guest 请求 ``fCreate=1`` 的目录创建效果，
  由后续显式工区 storage adapter 承担，本绑定不声明、也不构成对该效果的等价完整原生 API 替代。

载荷只有导出变量 ``SHGetSpecialFolderPathA``：DLL 加载与函数原型设置，不调用函数、不访问
文件系统、不写入系统状态。
"""

import ctypes

__all__ = ["SHGetSpecialFolderPathA"]

_shell32 = ctypes.WinDLL("shell32", use_last_error=True)

SHGetSpecialFolderPathA = _shell32.SHGetSpecialFolderPathA
SHGetSpecialFolderPathA.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
]
SHGetSpecialFolderPathA.restype = ctypes.c_int
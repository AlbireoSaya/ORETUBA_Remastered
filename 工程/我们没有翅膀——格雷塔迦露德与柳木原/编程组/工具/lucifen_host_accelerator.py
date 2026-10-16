"""lucifen_host_accelerator.py — Win32 加速键表(ACCEL/HACCEL)只读声明层。

仅使用 ctypes 绑定 user32 三个 API,不加载游戏 EXE/DLL,不实现任何 .ACC 解析器,
导入本模块不产生任何 Win32 调用副作用(无 Create/Copy/Destroy 调用)。

生命周期语义(重要):
CreateAcceleratorTableA 返回的 HACCEL 为 **owned table**,所有权归调用方,
非空句柄必须由调用方 DestroyAcceleratorTable 释放,不可泄漏、不可重复释放;
它与 LoadAcceleratorsA/W(从资源加载的加速键表)不同——后者由系统/模块资源
持有并在应用终止时自动释放；本调用方仅销毁自己 Create 创建的表，
不销毁 Load 加载的借用表。

ACCEL 使用 ctypes 默认自然对齐(fVirt 1B + 填充 1B + key 2B + cmd 2B = 6B),
与 Windows SDK winuser.h 的 ACCEL 布局一致。
"""

from __future__ import annotations

import ctypes

__all__ = [
    "ACCEL",
    "CreateAcceleratorTableA",
    "CopyAcceleratorTableA",
    "DestroyAcceleratorTable",
]


class ACCEL(ctypes.Structure):
    """加速键条目;自然对齐,勿设置 _pack_。"""

    _fields_ = [
        ("fVirt", ctypes.c_ubyte),
        ("key", ctypes.c_ushort),
        ("cmd", ctypes.c_ushort),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)

CreateAcceleratorTableA = user32.CreateAcceleratorTableA
CreateAcceleratorTableA.argtypes = [ctypes.POINTER(ACCEL), ctypes.c_int]
CreateAcceleratorTableA.restype = ctypes.c_void_p

CopyAcceleratorTableA = user32.CopyAcceleratorTableA
CopyAcceleratorTableA.argtypes = [ctypes.c_void_p, ctypes.POINTER(ACCEL), ctypes.c_int]
CopyAcceleratorTableA.restype = ctypes.c_int

DestroyAcceleratorTable = user32.DestroyAcceleratorTable
DestroyAcceleratorTable.argtypes = [ctypes.c_void_p]
DestroyAcceleratorTable.restype = ctypes.c_int
"""lucifen_host_font_create.py

GDI32 函数 ``CreateFontIndirectA`` 的声明式绑定模块。

本模块仅完成动态库加载与函数原型声明（argtypes / restype），
不调用任何系统函数，不构造字体对象，不产生任何副作用级别的 GDI 操作。
实际的字体创建由调用方在具备有效上下文时自行执行。
"""

from __future__ import annotations

import ctypes

from lucifen_host_logfont_a import LOGFONTA

__all__ = [
    "system",
    "CreateFontIndirectA",
]

# GDI32 动态库句柄；use_last_error=True 以便调用方通过
# ctypes.get_last_error() 获取线程局部错误码。
system = ctypes.WinDLL("gdi32", use_last_error=True)

# CreateFontIndirectA 函数指针声明（仅声明，不调用）。
CreateFontIndirectA = system.CreateFontIndirectA
CreateFontIndirectA.argtypes = [ctypes.POINTER(LOGFONTA)]
CreateFontIndirectA.restype = ctypes.c_void_p

# -*- coding: utf-8 -*-
# lucifen_host_lstrcpyn_a.py
# 单一职责：以 raw ctypes 绑定 Windows 原生 kernel32!lstrcpynA，并导出同名变量。
# 不定义函数、不调用该 API、无 __main__ 入口、不执行任何命令、不触碰游戏目录。
# 导入失败（kernel32 加载失败 / 符号缺失）由 ctypes 直接抛出异常，保持可观测，不做静默兜底。
# 调用方注意：n 为目标缓冲区容量，源串可短于 n；本绑定不代做任何 NUL 之后的读取。

import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

lstrcpynA = kernel32.lstrcpynA
lstrcpynA.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
lstrcpynA.restype = ctypes.c_void_p

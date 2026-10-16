"""GDI32 RestoreDC 声明模块。

仅完成 Win32 GDI32 RestoreDC 的 ctypes 声明，不在导入期调用。
第二参数 nSavedDC 为有符号 c_int，保留 -1 等负数语义。
"""

from __future__ import annotations

import ctypes

__all__ = ["system", "RestoreDC", "RESTORE_DC_MOST_RECENT"]

# RestoreDC(hdc, -1) 恢复最近一次 SaveDC 保存的状态。
RESTORE_DC_MOST_RECENT = -1

system = ctypes.WinDLL("gdi32", use_last_error=True)

RestoreDC = system.RestoreDC
RestoreDC.argtypes = [ctypes.c_void_p, ctypes.c_int]
RestoreDC.restype = ctypes.c_int

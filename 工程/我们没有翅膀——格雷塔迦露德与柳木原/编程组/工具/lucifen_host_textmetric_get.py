"""lucifen_host_textmetric_get

GDI32 GetTextMetricsA 绑定声明模块。

仅做符号声明与参数/返回类型标注，不调用任何 OS 接口。
"""

import ctypes

from lucifen_host_textmetric_a import TEXTMETRICA

__all__ = ["system", "GetTextMetricsA"]

system = ctypes.WinDLL("gdi32", use_last_error=True)

GetTextMetricsA = system.GetTextMetricsA
GetTextMetricsA.argtypes = [ctypes.c_void_p, ctypes.POINTER(TEXTMETRICA)]
GetTextMetricsA.restype = ctypes.c_int

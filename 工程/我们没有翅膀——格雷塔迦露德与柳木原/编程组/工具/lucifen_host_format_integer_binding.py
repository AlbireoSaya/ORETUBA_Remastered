"""lucifen_host_format_integer_binding.py

自有 SDK 精确声明：user32!wsprintfA 的限定整数绑定。

范围限定：
- 仅声明 cdecl 调用入口，供调用者以单一整数格式（%d 或 %02d）使用；
- 格式串与输出容量由调用者限定与负责，本模块不注入格式、不持有缓冲；
- 本模块不对任意格式、任意容量作安全性宣称；
- 模块导入期仅做符号声明，不调用 API，不分配对象。
"""

import ctypes

__all__ = ["wsprintfA_one_integer"]

# use_last_error=True：cdecl，保留 Win32 最后错误，供调用者按需读取
system = ctypes.CDLL("user32", use_last_error=True)

wsprintfA_one_integer = system.wsprintfA

# int wsprintfA(LPSTR lpOut, LPCSTR lpFmt, int value);
# 仅绑定单一整数实参形态，变参部分不声明
wsprintfA_one_integer.argtypes = [
    ctypes.c_void_p,   # lpOut: 调用者提供的输出缓冲
    ctypes.c_void_p,   # lpFmt: 调用者限定的单一 %d / %02d 格式串
    ctypes.c_int32,    # 唯一整数实参
]
wsprintfA_one_integer.restype = ctypes.c_int

"""完整 host 函数指针原型，参数/返回 HIMC 为 borrowed HIMC 句柄，不是 guest 地址。"""
import ctypes

IMMASSOCIATECONTEXTEX = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint32,
)

IMMASSOCIATECONTEXT = ctypes.WINFUNCTYPE(
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
)
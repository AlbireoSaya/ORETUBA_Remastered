"""lucifen_host_nccalcsize：NCCALCSIZE_PARAMS / RECT 结构声明，仅类型定义，不调用 API。"""
import ctypes
from lucifen_host_windowpos import WINDOWPOS


class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_int32),
        ('top', ctypes.c_int32),
        ('right', ctypes.c_int32),
        ('bottom', ctypes.c_int32),
    ]


class NCCALCSIZE_PARAMS(ctypes.Structure):
    _fields_ = [
        ('rgrc', RECT * 3),
        ('lppos', ctypes.POINTER(WINDOWPOS)),
    ]
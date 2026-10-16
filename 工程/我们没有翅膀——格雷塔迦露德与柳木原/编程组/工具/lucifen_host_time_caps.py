"""lucifen_host_time_caps.py

Windows 多媒体定时器设备能力（TIMECAPS）SDK 声明模块。

职责边界：仅声明 winmm!timeGetDevCaps 的 ctypes 类型与函数签名，
不发起任何查询调用、不做结果包装、不缓存设备能力。
调用方自行决定何时调用 timeGetDevCaps，并用 MMSYSERR_NOERROR 判定成功。
"""

import ctypes


class TIMECAPS(ctypes.Structure):
    """TIMECAPS（timeapi.h）

    字段按自然布局排列：两个 32 位无符号整数，sizeof(TIMECAPS) == 8。
    wPeriodMin / wPeriodMax 为该设备支持的定时器周期下限 / 上限（毫秒）。
    """

    _fields_ = [
        ('wPeriodMin', ctypes.c_uint32),
        ('wPeriodMax', ctypes.c_uint32),
    ]


# winmm 句柄；use_last_error=True 保留 LastError 语义，不触发任何 API 调用。
system = ctypes.WinDLL('winmm', use_last_error=True)

timeGetDevCaps = system.timeGetDevCaps
timeGetDevCaps.argtypes = [ctypes.POINTER(TIMECAPS), ctypes.c_uint32]
timeGetDevCaps.restype = ctypes.c_uint32  # MMRESULT


MMSYSERR_NOERROR = 0


__all__ = [
    'TIMECAPS',
    'system',
    'timeGetDevCaps',
    'MMSYSERR_NOERROR',
]

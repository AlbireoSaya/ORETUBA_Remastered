# -*- coding: utf-8 -*-
"""lucifen_host_textmetric_a.py

Win32 ``TEXTMETRICA``（ANSI 版）结构的 ctypes 声明。

仅做**结构声明**：不加载或调用任何系统库/API，不访问注册表、文件、
网络或进程，不包含密钥、原作文本或任何外部资源。使用 ctypes 默认
自然对齐，未指定 ``_pack_``。

布局约定（``c_int32`` 对齐为 4 的常规平台）：
    sizeof(TEXTMETRICA)          == 56
    TEXTMETRICA.tmAscent.offset  == 4
    TEXTMETRICA.tmCharSet.offset == 52

字段顺序：
    11 × c_int32 : tmHeight, tmAscent, tmDescent, tmInternalLeading,
                   tmExternalLeading, tmAveCharWidth, tmMaxCharWidth,
                   tmWeight, tmOverhang, tmDigitizedAspectX,
                   tmDigitizedAspectY
     9 × c_ubyte : tmFirstChar, tmLastChar, tmDefaultChar, tmBreakChar,
                   tmItalic, tmUnderlined, tmStruckOut, tmPitchAndFamily,
                   tmCharSet
"""

from __future__ import annotations

import ctypes

__all__ = ["TEXTMETRICA"]


class TEXTMETRICA(ctypes.Structure):
    """Win32 ``TEXTMETRICA`` 结构（ANSI 字符集版本）。

    11 个 32 位有符号度量字段之后紧跟 9 个无符号字节字段；
    布局随 ctypes 默认自然对齐展开（未使用 ``_pack_``）。
    """

    _fields_ = [
        ("tmHeight", ctypes.c_int32),
        ("tmAscent", ctypes.c_int32),
        ("tmDescent", ctypes.c_int32),
        ("tmInternalLeading", ctypes.c_int32),
        ("tmExternalLeading", ctypes.c_int32),
        ("tmAveCharWidth", ctypes.c_int32),
        ("tmMaxCharWidth", ctypes.c_int32),
        ("tmWeight", ctypes.c_int32),
        ("tmOverhang", ctypes.c_int32),
        ("tmDigitizedAspectX", ctypes.c_int32),
        ("tmDigitizedAspectY", ctypes.c_int32),
        ("tmFirstChar", ctypes.c_ubyte),
        ("tmLastChar", ctypes.c_ubyte),
        ("tmDefaultChar", ctypes.c_ubyte),
        ("tmBreakChar", ctypes.c_ubyte),
        ("tmItalic", ctypes.c_ubyte),
        ("tmUnderlined", ctypes.c_ubyte),
        ("tmStruckOut", ctypes.c_ubyte),
        ("tmPitchAndFamily", ctypes.c_ubyte),
        ("tmCharSet", ctypes.c_ubyte),
    ]


def _self_check() -> None:
    """校验布局常量，纯本地计算，无任何 OS 调用。"""
    assert ctypes.sizeof(TEXTMETRICA) == 56
    assert TEXTMETRICA.tmAscent.offset == 4
    assert TEXTMETRICA.tmCharSet.offset == 52
    assert (
        TEXTMETRICA.tmCharSet.offset + ctypes.sizeof(ctypes.c_ubyte)
        <= ctypes.sizeof(TEXTMETRICA)
    )


if __name__ == "__main__":
    _self_check()
    print("TEXTMETRICA layout OK: sizeof=%d" % ctypes.sizeof(TEXTMETRICA))

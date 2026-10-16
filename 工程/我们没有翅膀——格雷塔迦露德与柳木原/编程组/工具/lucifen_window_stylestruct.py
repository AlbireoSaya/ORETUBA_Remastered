import ctypes
import struct  # 公开：STYLESTRUCT / pack_stylestruct / apply_stylestruct
# STYLESTRUCT 语义：WM_STYLECHANGING(0x7C, allow_new_change=True) 允许改 styleNew；
# WM_STYLECHANGED(0x7D, allow_new_change=False) 只读，styleNew 必须沿用原值。


class STYLESTRUCT(ctypes.Structure):
    """styleOld / styleNew 各为 c_uint32，总计 8 字节。"""

    _fields_ = [
        ("styleOld", ctypes.c_uint32),
        ("styleNew", ctypes.c_uint32),
    ]


def _require_native(native):
    if not isinstance(native, STYLESTRUCT):
        raise TypeError("native must be a STYLESTRUCT instance")
    return native


def pack_stylestruct(native):
    _require_native(native)
    return struct.pack("<II", native.styleOld, native.styleNew)


def apply_stylestruct(native, data, allow_new_change):
    _require_native(native)
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != 8:
        raise ValueError("data must be exactly 8 bytes")
    if type(allow_new_change) is not bool:
        raise TypeError("allow_new_change must be a strict bool")
    style_old, style_new = struct.unpack("<II", data)
    if style_old != native.styleOld:
        raise ValueError("data.styleOld must equal native.styleOld")
    if not allow_new_change and style_new != native.styleNew:
        raise ValueError("styleNew is read-only when allow_new_change is False")
    native.styleNew = style_new
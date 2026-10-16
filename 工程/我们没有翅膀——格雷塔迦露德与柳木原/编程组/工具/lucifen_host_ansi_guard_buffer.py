import ctypes

_GUARD = b"\xa5" * 16
_GUARD_LEN = len(_GUARD)
_MIN_LEN, _MAX_LEN = 1, 4096


def make_guarded(data):
    """bytes 1..4096 -> c_char_Array_N，内容 16*A5 + data + 16*A5，无额外末 NUL。"""
    if type(data) is not bytes:
        raise TypeError("data must be exactly bytes")
    n = len(data)
    if not _MIN_LEN <= n <= _MAX_LEN:
        raise ValueError("data length must be in 1..4096")
    return ctypes.create_string_buffer(_GUARD + data + _GUARD, n + 2 * _GUARD_LEN)


def read_guarded(buf, length):
    """校验首尾 16*A5 哨兵后返回 buf.raw[16:16+length]；哨兵被破坏则 RuntimeError。"""
    if type(length) is not int:
        raise TypeError("length must be exactly int")
    if not _MIN_LEN <= length <= _MAX_LEN:
        raise ValueError("length must be in 1..4096")
    if not (isinstance(buf, ctypes.Array) and buf._type_ is ctypes.c_char):
        raise TypeError("buf must be a ctypes c_char array")
    if ctypes.sizeof(buf) != length + 2 * _GUARD_LEN:
        raise ValueError("buffer size must equal length + 32")
    raw = buf.raw
    if raw[:_GUARD_LEN] != _GUARD or raw[_GUARD_LEN + length:length + 2 * _GUARD_LEN] != _GUARD:
        raise RuntimeError("guard bytes corrupted")
    return raw[_GUARD_LEN:_GUARD_LEN + length]

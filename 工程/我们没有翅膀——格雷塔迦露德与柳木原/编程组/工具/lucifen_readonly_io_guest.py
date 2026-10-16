# lucifen_readonly_io_guest.py
# Read-only guest IO wrappers over the lucifen host files interface.

ERROR_INVALID_PARAMETER = 87

_MAX_READ = 1048576
_U32_MAX = 0xFFFFFFFF
_U32_SPACE = 0x100000000
_SIGNED_MIN = 0x80000000
_TOKEN_MIN = 1
_TOKEN_MAX = 0xFFFFFFFE

__all__ = ["bridge_ReadFile", "bridge_SetFilePointer", "bridge_CloseHandle"]


def _strict_int(value):
    return type(value) is int


def _u32(value):
    return type(value) is int and 0 <= value <= _U32_MAX


def _u32_nonzero(value):
    return type(value) is int and 1 <= value <= _U32_MAX


def _token(value):
    return type(value) is int and _TOKEN_MIN <= value <= _TOKEN_MAX


def _zero_strict(value):
    return type(value) is int and value == 0


def _overlap(base_a, len_a, base_b, len_b):
    if len_a <= 0 or len_b <= 0:
        return False
    return max(base_a, base_b) < min(base_a + len_a, base_b + len_b)


def _read_guest(read, addr, length):
    try:
        buf = read(addr, length)
    except Exception:
        return None
    if type(buf) is bytes or type(buf) is bytearray:
        if len(buf) == length:
            return buf
    return None


def _write_guest(write, addr, data):
    try:
        write(addr, data)
    except Exception:
        return False
    return True


def bridge_ReadFile(files, read, write, token, dst, count, count_ptr, overlapped=0):
    if not _token(token):
        raise ValueError('unsupported')
    if not _u32_nonzero(dst):
        raise ValueError('unsupported')
    if not _u32_nonzero(count_ptr):
        raise ValueError('unsupported')
    if not _strict_int(count) or count < 0 or count > _MAX_READ:
        raise ValueError('unsupported')
    if not _zero_strict(overlapped):
        raise ValueError('unsupported')
    if dst + count > _U32_SPACE:
        raise ValueError('unsupported')
    if count_ptr + 4 > _U32_SPACE:
        raise ValueError('unsupported')
    if _overlap(dst, count, count_ptr, 4):
        raise ValueError('unsupported')

    if _read_guest(read, count_ptr, 4) is None:
        raise ValueError('unsupported')
    if count > 0 and _read_guest(read, dst, count) is None:
        raise ValueError('unsupported')

    try:
        result = files.read(token, count)
    except Exception:
        raise ValueError('unsupported')
    if not isinstance(result, tuple) or len(result) != 3:
        raise ValueError('unsupported')
    ok, data, err = result
    if type(ok) is not bool:
        raise ValueError('unsupported')
    if type(data) is not bytes and type(data) is not bytearray:
        raise ValueError('unsupported')
    if not _u32(err):
        raise ValueError('unsupported')
    if len(data) > count:
        raise ValueError('unsupported')

    actual = len(data)
    if actual > 0:
        if not _write_guest(write, dst, bytes(data)):
            raise ValueError('unsupported')
    if not _write_guest(write, count_ptr, actual.to_bytes(4, "little")):
        raise ValueError('unsupported')
    return (int(ok), err)


def bridge_SetFilePointer(files, read, write, token, low_u32, high_ptr, method):
    if not _token(token):
        raise ValueError('unsupported')
    if not _u32(low_u32):
        raise ValueError('unsupported')
    if not _zero_strict(high_ptr):
        raise ValueError('unsupported')
    if type(method) is not int or method not in (0, 1, 2):
        raise ValueError('unsupported')
    distance = low_u32 - _U32_SPACE if low_u32 >= _SIGNED_MIN else low_u32
    try:
        result = files.seek(token, distance, method)
    except Exception:
        raise ValueError('unsupported')
    if not isinstance(result, tuple) or len(result) != 2:
        raise ValueError('unsupported')
    new_low, err = result
    if not _u32(new_low):
        raise ValueError('unsupported')
    if not _u32(err):
        raise ValueError('unsupported')
    return (new_low, err)


def bridge_CloseHandle(files, token):
    if not _token(token):
        raise ValueError('unsupported')
    try:
        result = files.close(token)
    except Exception:
        raise ValueError('unsupported')
    if not isinstance(result, tuple) or len(result) != 2:
        raise ValueError('unsupported')
    ok, err = result
    if type(ok) is not bool:
        raise ValueError('unsupported')
    if not _u32(err):
        raise ValueError('unsupported')
    return (1 if ok else 0, err)
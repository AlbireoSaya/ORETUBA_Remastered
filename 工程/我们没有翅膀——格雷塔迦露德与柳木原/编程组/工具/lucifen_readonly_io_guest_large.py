import lucifen_readonly_io_guest as _base


def bridge_ReadFile_large(files, read, write, token, dst, count, count_ptr, overlapped=0, max_read=32 << 20):
    if type(max_read) is not int:
        raise ValueError('unsupported')
    if max_read < 1 or max_read > (64 << 20):
        raise ValueError('unsupported')
    if not _base._token(token):
        raise ValueError('unsupported')
    if not _base._u32_nonzero(dst):
        raise ValueError('unsupported')
    if not _base._u32_nonzero(count_ptr):
        raise ValueError('unsupported')
    if not _base._strict_int(count) or count < 0 or count > max_read:
        raise ValueError('unsupported')
    if not _base._zero_strict(overlapped):
        raise ValueError('unsupported')
    if dst + count > _base._U32_SPACE:
        raise ValueError('unsupported')
    if count_ptr + 4 > _base._U32_SPACE:
        raise ValueError('unsupported')
    if _base._overlap(dst, count, count_ptr, 4):
        raise ValueError('unsupported')

    if _base._read_guest(read, count_ptr, 4) is None:
        raise ValueError('unsupported')
    if count > 0 and _base._read_guest(read, dst, count) is None:
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
    if not _base._u32(err):
        raise ValueError('unsupported')
    if len(data) > count:
        raise ValueError('unsupported')

    actual = len(data)
    if actual > 0:
        if not _base._write_guest(write, dst, bytes(data)):
            raise ValueError('unsupported')
    if not _base._write_guest(write, count_ptr, actual.to_bytes(4, "little")):
        raise ValueError('unsupported')
    return (int(ok), err)

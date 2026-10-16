"""Guest ANSI string prefix reader (read-only, standard library only)."""

__all__ = ["read_ansi_prefix"]

_MAX_ADDR = 0xFFFFFFFF
_MAX_LIMIT = 4096


def read_ansi_prefix(read, source, limit):
    """Return the NUL-terminated ANSI prefix at ``source``, at most ``limit`` bytes."""
    if type(source) is not int or not 1 <= source <= _MAX_ADDR:
        raise ValueError("source must be an int within 1..0xFFFFFFFF")
    if type(limit) is not int or not 1 <= limit <= _MAX_LIMIT:
        raise ValueError("limit must be an int within 1..4096")
    out = bytearray()
    for i in range(limit - 1):
        addr = source + i
        if addr > _MAX_ADDR:
            raise ValueError("read address exceeds 0xFFFFFFFF")
        chunk = read(addr, 1)
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise ValueError("read must return bytes-like of length 1")
        raw = bytes(chunk)
        if len(raw) != 1:
            raise ValueError("read returned %d bytes, expected 1" % len(raw))
        if raw[0] == 0:
            return bytes(out)
        out.append(raw[0])
    return bytes(out)

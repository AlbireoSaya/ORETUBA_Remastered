import struct


def decode_accelerator_resource(data):
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("accelerator resource must be bytes")
    data = bytes(data)
    if not data or len(data) % 8:
        raise ValueError("accelerator resource must be non-empty and 8-byte aligned")
    count = len(data) // 8
    if count > 32767:
        raise ValueError("accelerator resource has too many entries")
    out = []
    for i in range(count):
        flags, key, cmd, pad = struct.unpack_from("<4H", data, i * 8)
        if flags & ~0x9F or pad:
            raise ValueError("invalid accelerator flags or nonzero padding")
        if (flags & 0x80) != (0x80 if i == count - 1 else 0):
            raise ValueError("0x80 flag must be set on the last entry only")
        out.append((flags & 0x1F, key, cmd))
    return out
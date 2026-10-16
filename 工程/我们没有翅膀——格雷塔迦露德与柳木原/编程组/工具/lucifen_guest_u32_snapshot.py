import hashlib
import struct

from lucifen_guest_snapshot_bounds import validate_span_u32


def snapshot_u32(read, base, byte_count, max_bytes=8192):
    """Read one exact span and return its little-endian u32 view plus SHA-256.

    ``read`` is called exactly once with ``(base, byte_count)``.  Exceptions
    raised by ``read`` propagate unchanged; no I/O is performed here.
    """
    validate_span_u32(base, byte_count, max_bytes)

    data = read(base, byte_count)

    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise ValueError(
            "read() must return bytes, bytearray or memoryview, got %s"
            % type(data).__name__
        )

    if isinstance(data, memoryview):
        data = data.tobytes()
    elif isinstance(data, bytearray):
        data = bytes(data)

    if len(data) != byte_count:
        raise ValueError(
            "read() returned %d bytes, expected exactly %d"
            % (len(data), byte_count)
        )

    digest = hashlib.sha256(data).hexdigest()
    words = list(struct.unpack("<%dI" % (byte_count // 4), data))

    return {
        "base": base,
        "byte_count": byte_count,
        "sha256": digest,
        "words": words,
    }
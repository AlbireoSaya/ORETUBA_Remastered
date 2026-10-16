"""Bounds validation for a guest snapshot span inside a 32-bit address space.

Standard library only. No I/O. This module defines exactly one function.
"""


def validate_span_u32(base, byte_count, max_bytes=8192):
    """Validate a guest-memory span described by base and byte_count.

    Enforced rules:
      * base, byte_count and max_bytes must each be exactly `int`
        (bool and int subclasses are rejected by the `type(x) is int` check).
      * max_bytes: positive, 4-byte aligned, and <= 65536.
      * byte_count: positive, 4-byte aligned, and <= max_bytes.
      * base: positive, 4-byte aligned, and representable as u32.
      * base + byte_count must not exceed 2**32.

    Returns None when every rule holds; raises ValueError otherwise.
    """
    if type(base) is not int:
        raise ValueError("base must be int, got " + type(base).__name__)
    if type(byte_count) is not int:
        raise ValueError("byte_count must be int, got " + type(byte_count).__name__)
    if type(max_bytes) is not int:
        raise ValueError("max_bytes must be int, got " + type(max_bytes).__name__)

    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive, got " + repr(max_bytes))
    if max_bytes > 65536:
        raise ValueError("max_bytes must be <= 65536, got " + repr(max_bytes))
    if max_bytes % 4 != 0:
        raise ValueError("max_bytes must be 4-byte aligned, got " + repr(max_bytes))

    if byte_count <= 0:
        raise ValueError("byte_count must be positive, got " + repr(byte_count))
    if byte_count > max_bytes:
        raise ValueError(
            "byte_count must be <= max_bytes, got "
            + repr(byte_count)
            + " > "
            + repr(max_bytes)
        )
    if byte_count % 4 != 0:
        raise ValueError("byte_count must be 4-byte aligned, got " + repr(byte_count))

    if base <= 0:
        raise ValueError("base must be positive, got " + repr(base))
    if base > 0xFFFFFFFF:
        raise ValueError("base must fit in u32, got " + repr(base))
    if base % 4 != 0:
        raise ValueError("base must be 4-byte aligned, got " + repr(base))

    end = base + byte_count
    if end > 2 ** 32:
        raise ValueError(
            "base + byte_count must be <= 2**32, got base="
            + repr(base)
            + " byte_count="
            + repr(byte_count)
            + " end="
            + repr(end)
        )

    return None
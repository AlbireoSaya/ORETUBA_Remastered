"""r_vm_shadow_range.py — 仅标准库；无 IO。"""

U32 = 0xffffffff


def locate(segments, a, n):
    a &= U32
    for base, data in segments:
        if base <= a and a + n <= base + len(data):
            return data, a - base
    raise ValueError("unmapped")


def word(segments, q):
    if q & 3:
        raise ValueError("unaligned")
    value = 0
    for i in range(4):
        try:
            data, off = locate(segments, q + i, 1)
        except ValueError:
            v = 0
        else:
            v = data[off]
        value |= v << (8 * i)
    return value & U32
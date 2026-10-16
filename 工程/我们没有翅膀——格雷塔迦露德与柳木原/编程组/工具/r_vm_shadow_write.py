import struct
from r_vm_shadow_range import locate


def _base(q, n, ranges):
    q &= 0xffffffff
    for start, end_exclusive in ranges:
        if start <= q and q + n <= end_exclusive:
            return q
    raise ValueError("shadow range out of bounds")


def write8(seg, q, v, ranges):
    data, off = locate(seg, _base(q, 1, ranges), 1)
    data[off] = v & 255


def write32(seg, q, v, ranges):
    data, off = locate(seg, _base(q, 4, ranges), 4)
    struct.pack_into("<I", data, off, v & 0xffffffff)
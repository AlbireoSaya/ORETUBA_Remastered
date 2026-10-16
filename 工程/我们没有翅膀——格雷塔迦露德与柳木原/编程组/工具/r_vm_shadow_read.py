import struct
from r_vm_shadow_range import locate


def read8(seg, q):
    data, off = locate(seg, q, 1)
    return data[off]


def read32(seg, q):
    data, off = locate(seg, q, 4)
    return struct.unpack_from("<I", data, off)[0]
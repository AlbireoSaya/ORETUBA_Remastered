import struct


def pack_guest_nccalcsize(params, pos_guest_ptr):
    values = []
    for rect in params.rgrc:
        values.append(rect.left)
        values.append(rect.top)
        values.append(rect.right)
        values.append(rect.bottom)
    return struct.pack('<12iI', *values, pos_guest_ptr)
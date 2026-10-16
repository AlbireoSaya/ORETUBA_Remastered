import struct


def decode_guest_nccalcsize(data, expected_guest_pos):
    values = struct.unpack('<12iI', data)
    if values[12] != expected_guest_pos:
        raise ValueError('pointer mismatch')
    return values[:12]

def write_nccalcsize_rects(params, values):
    for i in range(3):
        left, top, right, bottom = values[i * 4:i * 4 + 4]
        rect = params.rgrc[i]
        rect.left = left
        rect.top = top
        rect.right = right
        rect.bottom = bottom

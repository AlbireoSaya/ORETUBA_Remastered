import struct


def decode_guest_windowpos(data, expected_hwnd, expected_insert):
    result = struct.unpack('<2I4iI', data)
    if result[0] != expected_hwnd or result[1] != expected_insert:
        raise ValueError('pointer mismatch')
    return result

def write_windowpos_numeric(pos, values):
    x, y, cx, cy, flags = values[2:7]
    pos.x = x
    pos.y = y
    pos.cx = cx
    pos.cy = cy
    pos.flags = flags
    return pos

import struct

U32_MAX = 0xFFFFFFFF
I32_MIN = -0x80000000
I32_MAX = 0x7FFFFFFF

def _int_strict(v):
    if type(v) is not int:
        raise TypeError("expected int")
    return v

def _u32(name, v):
    v = _int_strict(v)
    if not 0 <= v <= U32_MAX:
        raise ValueError(f"{name} out of u32 range")
    return v

def _i32(name, v):
    v = _int_strict(v)
    if not I32_MIN <= v <= I32_MAX:
        raise ValueError(f"{name} out of i32 range")
    return v

def pack_guest_msg(msg, hwnd_token, wparam, lparam):
    hwnd_token = _u32("hwnd_token", hwnd_token)
    wparam = _u32("wparam", wparam)
    lparam = _i32("lparam", lparam)
    message = _u32("msg.message", int(msg.message))
    time = _u32("msg.time", int(msg.time))
    lPrivate = _u32("msg.lPrivate", int(msg.lPrivate))
    x = _i32("msg.pt.x", int(msg.pt.x))
    y = _i32("msg.pt.y", int(msg.pt.y))
    return struct.pack("<IIIiIiiI", hwnd_token, message, wparam, lparam, time, x, y, lPrivate)

"""Synthetic client mouse message packer. It does not send OS input."""

def pack_client_mouse(message, x, y, flags=0):
    if type(message) is not int or message not in (0x200, 0x201, 0x202):
        raise ValueError("message must be 0x200, 0x201, or 0x202")
    if type(x) is not int or type(y) is not int:
        raise ValueError("x and y must be integers")
    if not (-32768 <= x <= 32767 and -32768 <= y <= 32767):
        raise ValueError("x and y must be signed 16-bit values")
    if type(flags) is not int or not (0 <= flags <= 0x7F):
        raise ValueError("flags must be 0..0x7f")
    lparam = ((y & 0xFFFF) << 16) | (x & 0xFFFF)
    return {
        "message": message,
        "wparam": flags,
        "lparam": lparam,
        "client_point": (x, y),
        "synthetic_fixture_input": True,
    }

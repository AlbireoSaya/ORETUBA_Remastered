import struct

_FMT = struct.Struct("<IIIiIiiI")
_FIELDS = ("hwnd", "message", "wParam", "lParam", "time", "pt_x", "pt_y", "lPrivate")


def unpack_guest_msg(data):
    """Struct-only decode of one 32-byte guest message.

    Reinterprets bytes losslessly (lParam signed). Never builds OS
    pointers, never executes the message, and claims no coverage of
    all possible messages.
    """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) != _FMT.size:
        raise ValueError("data must be exactly 32 bytes")
    return dict(zip(_FIELDS, _FMT.unpack(data)))

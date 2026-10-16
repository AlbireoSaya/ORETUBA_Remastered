import struct


def pack_guest_createstruct(cs, lp_create, hinstance, hmenu, hwnd_parent, name_ptr, class_ptr):
    return struct.pack(
        "<12I",
        lp_create,
        hinstance,
        hmenu,
        hwnd_parent,
        int(cs.cy) & 0xffffffff,
        int(cs.cx) & 0xffffffff,
        int(cs.y) & 0xffffffff,
        int(cs.x) & 0xffffffff,
        int(cs.style) & 0xffffffff,
        name_ptr,
        class_ptr,
        int(cs.dwExStyle) & 0xffffffff,
    )

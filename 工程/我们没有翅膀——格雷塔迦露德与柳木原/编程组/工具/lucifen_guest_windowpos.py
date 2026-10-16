import struct


def pack_guest_windowpos(pos, hwnd_guest, insert_after_guest):
    """Pack GUEST WINDOWPOS 的 7 个 32 位字段为小端字节串。

    hwnd_guest / insert_after_guest 必须是 guest 地址空间内的窗口句柄值，
    由 caller 负责 host->guest 指针映射；不得传入原 host 指针，否则
    struct.pack('<7I') 会因超出 0xffffffff 抛 struct.error 而不被静默截断。
    pos.x/y/cx/cy/flags 按 32 位掩码后写入。
    """
    return struct.pack(
        '<7I',
        hwnd_guest,
        insert_after_guest,
        pos.x & 0xffffffff,
        pos.y & 0xffffffff,
        pos.cx & 0xffffffff,
        pos.cy & 0xffffffff,
        pos.flags & 0xffffffff,
    )
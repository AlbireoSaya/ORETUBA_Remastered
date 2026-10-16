def _exact_int(value):
    return type(value) is int


def map_setcursor_message(host_wparam, lparam, own_host_hwnd, guest_hwnd):
    if not (
        _exact_int(host_wparam)
        and _exact_int(lparam)
        and _exact_int(own_host_hwnd)
        and _exact_int(guest_hwnd)
    ):
        raise ValueError("all arguments must be exact builtin int")
    if not (0 < own_host_hwnd <= 2**64 - 1):
        raise ValueError("own_host_hwnd out of range")
    if host_wparam != own_host_hwnd:
        raise ValueError("host_wparam must match own_host_hwnd exactly")
    if not (1 <= guest_hwnd <= 2**32 - 1):
        raise ValueError("guest_hwnd out of range")
    if not (-2**31 <= lparam <= 2**32 - 1):
        raise ValueError("lparam out of range")

    packed = lparam & 0xFFFFFFFF
    low = packed & 0xFFFF
    hit_test = low - 0x10000 if low >= 0x8000 else low
    trigger_message = (packed >> 16) & 0xFFFF

    return {
        "guest_wparam": guest_hwnd,
        "guest_lparam": packed,
        "hit_test": hit_test,
        "trigger_message": trigger_message,
    }
"""Current-head-only guest OS emulation of Win32 x86 RtlUnwind (pure, no host API). Zero frames ABOVE the target are unwound, and the target itself is not unwound; this is not host RtlUnwind and not full SEH."""

UINT32_MAX = 0xFFFFFFFF


class UnsupportedUnwind(ValueError):
    """The requested guest unwind is outside the one supported emulation case."""


def _u32(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise UnsupportedUnwind(name + " must be a non-bool uint32")
    if not 0 <= value <= UINT32_MAX:
        raise UnsupportedUnwind(name + " must be a uint32")
    return value


def _range_covers(executable_ranges, ip):
    if isinstance(executable_ranges, (str, bytes, bytearray)):
        raise UnsupportedUnwind("executable_ranges must be a sequence of pairs")
    try:
        entries = iter(executable_ranges)
    except TypeError:
        raise UnsupportedUnwind("executable_ranges must be iterable")
    hit = False
    for entry in entries:
        if (isinstance(entry, (str, bytes, bytearray))
                or not isinstance(entry, (tuple, list)) or len(entry) != 2):
            raise UnsupportedUnwind("each executable range must be a [lo, hi) pair")
        lo = _u32("range lo", entry[0])
        hi = _u32("range hi", entry[1])
        if lo >= hi:
            raise UnsupportedUnwind("each executable range needs lo < hi")
        if lo <= ip < hi:
            hit = True
    return hit


def plan_current_frame_unwind(record_flags, head, target_frame, target_ip,
                              return_value, esp, return_address,
                              stack_low, stack_high, executable_ranges):
    """Plan a guest RtlUnwind for the current head frame only: frames unwound = 0, zero frames ABOVE the target are unwound, and the target itself is not unwound. Other target frames and exit-unwind are rejected as unsupported; pure, no CPU or guest state mutation."""
    record_flags = _u32("record_flags", record_flags)
    head = _u32("head", head)
    target_frame = _u32("target_frame", target_frame)
    target_ip = _u32("target_ip", target_ip)
    return_value = _u32("return_value", return_value)
    esp = _u32("esp", esp)
    return_address = _u32("return_address", return_address)
    stack_low = _u32("stack_low", stack_low)
    stack_high = _u32("stack_high", stack_high)

    if record_flags not in (0, 1):
        raise UnsupportedUnwind("record_flags must be 0 or 1")
    if stack_low >= stack_high:
        raise UnsupportedUnwind("stack_low must be below stack_high")
    if esp & 3:
        raise UnsupportedUnwind("esp must be 4-byte aligned")
    if esp < stack_low or esp + 20 > stack_high:
        raise UnsupportedUnwind("esp..esp+20 must lie within the stack")
    if head & 3:
        raise UnsupportedUnwind("head must be 4-byte aligned")
    if head < stack_low or head + 8 > stack_high:
        raise UnsupportedUnwind("head..head+8 must lie within the stack")
    if head < esp + 20:
        raise UnsupportedUnwind("head must be at or above esp+20")
    if target_frame != head:
        raise UnsupportedUnwind("only the current frame (target_frame == head) is supported")
    if target_ip != return_address:
        raise UnsupportedUnwind("target_ip must equal return_address")
    if not _range_covers(executable_ranges, target_ip):
        raise UnsupportedUnwind("target_ip must fall inside a well-formed executable range")

    return {
        "flags": record_flags | 2,
        "esp": esp + 20,
        "eip": target_ip,
        "eax": return_value,
        "frames_unwound": 0,
        "emulated_os_boundary": True,
    }

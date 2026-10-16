import struct

def fill32_span_reference(data, pitch, origin, clip, rect, color):
    q = lambda v: isinstance(v, (tuple, list)) and len(v) == 4 and all(
        type(i) is int and -(1 << 31) <= i < (1 << 31) for i in v)
    if type(pitch) is not int or pitch % 4:
        raise ValueError("pitch must be a non-bool int multiple of 4")
    if type(origin) is not int or origin < 0:
        raise ValueError("origin must be a non-bool int >= 0")
    if type(color) is not int or not 0 <= color < (1 << 32):
        raise ValueError("color must be a non-bool u32")
    if not q(clip) or (rect is not None and not q(rect)):
        raise ValueError("clip and non-None rect must be four non-bool signed 32-bit ints")
    work = bytearray(data)
    n = len(work)
    r = clip if rect is None else rect
    left, top = max(clip[0], r[0]), max(clip[1], r[1])
    right, bottom = min(clip[2], r[2]), min(clip[3], r[3])
    if left >= right or top >= bottom:
        return bytes(work), None
    for y in range(top, bottom):
        for x in range(left, right):
            pos = origin + y * pitch + x * 4
            if not 0 <= pos <= n - 4:
                raise ValueError("span position out of range")
            struct.pack_into("<I", work, pos, color)
    return bytes(work), (left, top, right, bottom)

def set_clip_reference(width, height, old, requested):
    def _check_int(value, *, non_negative=False):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError
        if non_negative:
            if value < 0 or value > 2147483647:
                raise ValueError
        else:
            if value < -2147483648 or value > 2147483647:
                raise ValueError

    def _check_rect(value):
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            raise ValueError
        for item in value:
            _check_int(item)

    _check_int(width, non_negative=True)
    _check_int(height, non_negative=True)
    _check_rect(old)

    if requested is None:
        return ((0, 0, width, height), True)

    _check_rect(requested)
    left, top, right, bottom = requested

    if left >= right or top >= bottom:
        return (tuple(old), False)

    return (
        (
            max(0, left),
            max(0, top),
            min(width, right),
            min(height, bottom),
        ),
        True,
    )

def host_z_proc():
    import ctypes
    fn = ctypes.WinDLL("kernel32", use_last_error=True).lstrcpyA
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    fn.restype = ctypes.c_void_p
    return fn

import ctypes

def host_copy_z(payload, before):
    if type(payload) is not bytes or type(before) is not bytes or b"\x00" in payload or not 1 <= len(before) <= 4096 or len(payload) >= len(before):
        raise ValueError
    guard = b"Q" * 16
    dst = ctypes.create_string_buffer(before + guard)
    src = ctypes.create_string_buffer(payload + b"\x00")
    ret = host_z_proc()(dst, src)
    if ret != ctypes.addressof(dst) or dst.raw[len(before):len(before) + 16] != guard:
        raise RuntimeError
    return dst.raw[:len(before)]

def read_z(read_bytes, source, capacity):
    payload = bytearray()
    for i in range(capacity):
        chunk = read_bytes(source + i, 1)
        if len(chunk) != 1:
            raise ValueError("short read")
        if chunk[0] == 0:
            return bytes(payload)
        payload.append(chunk[0])
    raise ValueError("unterminated")

def bridge_lstrcpyA(read_bytes, write_bytes, destination, source, capacity):
    if type(destination) is not int or type(source) is not int or type(capacity) is not int:
        raise ValueError
    if destination <= 0 or source <= 0 or not (1 <= capacity <= 4096):
        raise ValueError
    payload = read_z(read_bytes, source, capacity)
    if len(payload) + 1 > capacity:
        raise ValueError
    if destination < source + len(payload) + 1 and source < destination + capacity:
        raise ValueError("overlap")
    before = read_bytes(destination, capacity)
    if len(before) != capacity:
        raise ValueError
    out = host_copy_z(payload, before)
    if type(out) is not bytes or len(out) != capacity:
        raise ValueError
    write_bytes(destination, out)
    return destination
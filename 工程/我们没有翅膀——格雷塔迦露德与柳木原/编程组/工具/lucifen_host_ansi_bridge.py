def host_copy_proc():
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel32.lstrcpynA
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    fn.restype = ctypes.c_void_p
    return fn

import ctypes

def host_copy_bytes(a, b, n):
    dst = ctypes.create_string_buffer(b + b'\0')
    src = ctypes.create_string_buffer(a + b'\0')
    ret = host_copy_proc()(dst, src, n)
    if ret != ctypes.addressof(dst):
        raise RuntimeError('lstrcpynA return != destination')
    if dst.raw[n] != 0:
        raise RuntimeError('guard byte at index n clobbered')
    return dst.raw[:n]

def bridge_lstrcpynA(read_bytes, write_bytes, destination, source, max_length):
    if type(source) is not int or type(destination) is not int or source <= 0 or destination <= 0:
        raise ValueError("source and destination must be positive integers")
    if type(max_length) is not int or not 1 <= max_length <= 4096:
        raise ValueError("max_length must be an integer in 1..4096")
    if destination < source + max_length and source < destination + max_length:
        raise ValueError("source and destination ranges overlap")
    src = read_bytes(source, max_length)
    dst = read_bytes(destination, max_length)
    if len(src) != max_length or len(dst) != max_length:
        raise ValueError("exact length read required")
    out = host_copy_bytes(src, dst, max_length)
    if not isinstance(out, (bytes, bytearray)) or len(out) != max_length:
        raise ValueError("host_copy_bytes returned wrong length")
    write_bytes(destination, bytes(out))
    return destination
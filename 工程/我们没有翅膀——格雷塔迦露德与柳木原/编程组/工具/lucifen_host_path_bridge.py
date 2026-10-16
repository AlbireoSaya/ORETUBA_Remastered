from lucifen_host_string_bridge import read_z
import ctypes

def host_length_z(payload):
    if type(payload) is not bytes or b"\x00" in payload or len(payload) > 4095:
        raise ValueError("payload must be NUL-free bytes with len <= 4095")
    buf = ctypes.create_string_buffer(payload)
    fn = ctypes.WinDLL("kernel32.dll").lstrlenA
    fn.argtypes = [ctypes.c_void_p]
    fn.restype = ctypes.c_int
    n = fn(ctypes.cast(buf, ctypes.c_void_p))
    if n != len(payload) or buf.raw != payload + b"\x00":
        raise RuntimeError("lstrlenA round-trip mismatch")
    return n
def host_concat_z(payload, before):
    import ctypes
    if type(payload) is not bytes or type(before) is not bytes:
        raise ValueError
    if b"\0" in payload:
        raise ValueError
    n = len(before)
    if n < 1 or n > 4096 or b"\0" not in before:
        raise ValueError
    prefix = before.split(b"\0", 1)[0]
    expected = prefix + payload + b"\0"
    if len(expected) > n:
        raise ValueError
    guard = b"\xA5" * 128
    src = ctypes.create_string_buffer(payload)
    dst = ctypes.create_string_buffer(guard + before + guard)
    fn = ctypes.WinDLL("kernel32").lstrcatA
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    fn.restype = ctypes.c_void_p
    da, sa = ctypes.addressof(dst), ctypes.addressof(src)
    dp = da + 128
    ret = fn(ctypes.c_void_p(dp), ctypes.c_void_p(sa))
    if ret != dp:
        raise RuntimeError
    if dst.raw[:128] != guard or dst.raw[128 + n:128 + n + 128] != guard:
        raise RuntimeError
    if src.raw != payload + b"\0":
        raise RuntimeError
    out = dst.raw[128:128 + n]
    if out != expected + before[len(expected):]:
        raise RuntimeError
    return out
def bridge_lstrlenA(read, src, capacity=4096):
    if type(src) is not int or not (1 <= src <= 0xFFFFFFFF):
        raise ValueError("src")
    if type(capacity) is not int or not (1 <= capacity <= 4096):
        raise ValueError("capacity")
    payload = read_z(read, src, capacity)
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("read_z")
    payload = bytes(payload)
    if src + len(payload) + 1 > 0x100000000:
        raise ValueError("src range")
    return host_length_z(payload)

def bridge_lstrcatA(read, write, dst, src, capacity):
    if type(dst) is not int or not (1 <= dst <= 0xFFFFFFFF):
        raise ValueError("dst")
    if type(src) is not int or not (1 <= src <= 0xFFFFFFFF):
        raise ValueError("src")
    if type(capacity) is not int or not (1 <= capacity <= 4096):
        raise ValueError("capacity")
    if dst + capacity > 0x100000000:
        raise ValueError("dst range")
    source = read_z(read, src, 4096)
    if not isinstance(source, (bytes, bytearray)):
        raise TypeError("read_z")
    source = bytes(source)
    if src + len(source) + 1 > 0x100000000:
        raise ValueError("src range")
    if src < dst + capacity and dst < src + len(source) + 1:
        raise ValueError("overlap")
    before = read(dst, capacity)
    if not isinstance(before, (bytes, bytearray)) or len(before) != capacity:
        raise ValueError("dst read")
    before = bytes(before)
    actual = host_concat_z(source, before)
    if not isinstance(actual, (bytes, bytearray)) or len(actual) != capacity:
        raise ValueError("host_concat_z")
    actual = bytes(actual)
    write(dst, actual)
    return dst
import ctypes

def host_open_missing_readonly(pathbytes, access, share, security, creation, flags, template):
    if type(pathbytes) is not bytes or not (1 <= len(pathbytes) <= 259) or b"\x00" in pathbytes:
        raise ValueError("invalid pathbytes")
    params = (access, share, security, creation, flags, template)
    if any(type(p) is not int for p in params):
        raise ValueError("parameters must be strict int")
    if params != (0x80000000, 1, 0, 3, 0x80, 0):
        raise ValueError("parameters must be (0x80000000, 1, 0, 3, 0x80, 0)")
    k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
    k32.CreateFileA.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    k32.CreateFileA.restype = ctypes.c_void_p
    path_src = ctypes.create_string_buffer(pathbytes)
    handle = k32.CreateFileA(
        ctypes.cast(path_src, ctypes.c_void_p),
        access, share, security, creation, flags, template,
    )
    last_error = ctypes.get_last_error()
    invalid = ctypes.c_void_p(-1).value
    if handle != invalid:
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        k32.CloseHandle.restype = ctypes.c_int
        k32.CloseHandle(handle)
        raise RuntimeError("unexpected existing file")
    if last_error not in (2, 3):
        raise RuntimeError("unexpected last_error: %r" % (last_error,))
    return (0xffffffff, last_error)
import ctypes

_G = b'\xa5' * 128
_u32 = ctypes.WinDLL('user32.dll'); _u32.CharLowerA.argtypes = [ctypes.c_void_p]; _u32.CharLowerA.restype = ctypes.c_void_p


def host_lower_ascii_z(payload):
    if type(payload) is not bytes or len(payload) > 4095: raise ValueError('payload must be bytes, len<=4095')
    if any(b == 0 or b > 127 for b in payload): raise ValueError('payload must be non-NUL ASCII 1..127')
    init = _G + payload + b'\x00' + _G
    buf = ctypes.create_string_buffer(init, len(init)); ptr = ctypes.addressof(buf) + 128
    if ptr < 0x10000: raise ValueError('pointer below 0x10000')
    try: ret = _u32.CharLowerA(ctypes.c_void_p(ptr))
    except Exception as exc: raise RuntimeError('CharLowerA raised') from exc
    if ret is None or int(ret) != ptr: raise RuntimeError('ret != passed pointer')
    raw = buf.raw
    if raw[:128] != _G or raw[-128:] != _G: raise RuntimeError('guard corrupted')
    if raw[128 + len(payload)] != 0: raise RuntimeError('NUL moved')
    out = raw[128:128 + len(payload)]
    if out != payload.lower(): raise RuntimeError('not payload.lower()')
    return out


def bridge_CharLowerA(read, write, src, capacity=4096):
    if type(src) is not int or not 0x10000 <= src <= 0xFFFFFFFF: raise ValueError('bad src')
    if type(capacity) is not int or not 1 <= capacity <= 4096: raise ValueError('bad capacity')
    payload = read_z(read, src, capacity)
    if type(payload) is not bytes: raise ValueError('read(src) must return bytes')
    if src + len(payload) + 1 > 2 ** 32: raise ValueError('src+len+1 > 2**32')
    actual = host_lower_ascii_z(payload)
    write(src, actual + b'\x00')
    return src
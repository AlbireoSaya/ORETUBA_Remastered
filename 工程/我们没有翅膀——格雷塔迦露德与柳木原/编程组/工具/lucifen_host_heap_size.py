"""Windows kernel32.HeapSize bridge.

Caller must guarantee heap and ptr are already-owned real Windows objects.
This module does not claim ownership and does not validate OS ownership.
"""
import ctypes

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.HeapSize.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
_kernel32.HeapSize.restype = ctypes.c_size_t

_SIZE_MAX = ctypes.c_size_t(-1).value
_ERROR_INVALID_PARAMETER = 87


def _valid_ptr(v):
    return type(v) is int and v > 0 and v <= (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1


def host_heap_size(heap, flags, ptr):
    """Call kernel32.HeapSize and return (size, last_error).

    heap/ptr must be non-bool ints, non-zero, and within pointer width.
    flags must be int 0. The caller must guarantee heap/ptr are already-owned
    real Windows objects; this function does not claim ownership or validate
    OS ownership. On failure size is SIZE_MAX and last_error is GetLastError.
    """
    if not _valid_ptr(heap) or type(flags) is not int or flags != 0 or not _valid_ptr(ptr):
        ctypes.set_last_error(_ERROR_INVALID_PARAMETER)
        return _SIZE_MAX, ctypes.get_last_error()
    ctypes.set_last_error(0)
    size = int(_kernel32.HeapSize(ctypes.c_void_p(heap), flags, ctypes.c_void_p(ptr)))
    if size == _SIZE_MAX:
        return size, ctypes.get_last_error()
    return size, 0

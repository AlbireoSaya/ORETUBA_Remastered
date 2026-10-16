import ctypes
from ctypes import POINTER, c_void_p, c_size_t, c_int, c_uint32, c_int32, WINFUNCTYPE, sizeof, cast

"""Raw host COM interface helpers for IMalloc.

Caller is responsible for providing a valid SHGetMalloc interface and for
ownership/lifetime management. This module does not accept guest pointers and
does not claim to provide any OS sandbox.
"""

shell32 = ctypes.WinDLL('shell32', use_last_error=True)
SHGetMalloc = shell32.SHGetMalloc
SHGetMalloc.argtypes = [POINTER(c_void_p)]
SHGetMalloc.restype = c_int32

_ALLOC = WINFUNCTYPE(c_void_p, c_void_p, c_size_t)
_FREE = WINFUNCTYPE(None, c_void_p, c_void_p)
_GET_SIZE = WINFUNCTYPE(c_size_t, c_void_p, c_void_p)
_DID_ALLOC = WINFUNCTYPE(c_int, c_void_p, c_void_p)
_RELEASE = WINFUNCTYPE(c_uint32, c_void_p)


def _method_addr(interface, slot):
    vtable = cast(c_void_p(interface), POINTER(c_void_p))[0]
    return cast(c_void_p(vtable + slot * sizeof(c_void_p)), POINTER(c_void_p))[0]


def imalloc_alloc(interface, size):
    return _ALLOC(_method_addr(interface, 3))(interface, size)


def imalloc_free(interface, block):
    _FREE(_method_addr(interface, 5))(interface, block)


def imalloc_get_size(interface, block):
    return _GET_SIZE(_method_addr(interface, 6))(interface, block)


def imalloc_did_alloc(interface, block):
    return _DID_ALLOC(_method_addr(interface, 7))(interface, block)


def imalloc_release(interface):
    return _RELEASE(_method_addr(interface, 2))(interface)
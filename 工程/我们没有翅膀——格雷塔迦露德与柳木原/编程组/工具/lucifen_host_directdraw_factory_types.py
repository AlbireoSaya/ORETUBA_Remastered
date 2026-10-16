"""Host DirectDraw / IUnknown callable prototypes (signature declarations only).

Caller contract: each prototype may only be constructed with a fully
verified host program address, obtained either by GetProcAddress on the
exact real system32 module or by an owned, real COM vtable slot 2 check.
GUID, host out-buffer lifetime plus guard, full host interface, ownership
and guest ABI remain the caller's responsibility. No sandbox and no
verification happens here; guest addresses must never be passed in, and
no original guest OS code is registered. These three constructors expose
signatures only: the caller explicitly builds the callable from a proc
address later.
"""
import ctypes

DirectDrawCreateProto = ctypes.WINFUNCTYPE(
    ctypes.c_int32,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p,
)

DirectDrawCreateExProto = ctypes.WINFUNCTYPE(
    ctypes.c_int32,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p,
    ctypes.c_void_p,
)

IUnknownReleaseProto = ctypes.WINFUNCTYPE(
    ctypes.c_uint32,
    ctypes.c_void_p,
)

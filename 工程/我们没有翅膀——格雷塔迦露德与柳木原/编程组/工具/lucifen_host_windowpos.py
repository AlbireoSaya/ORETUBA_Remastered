"""WINDOWPOS structure definition for lucifen host-side interop.

IMPORTANT: the HWND/hWndInsertAfter fields hold *host* pointers. Before any
value is handed to guest code these MUST be mapped (translated) into the
guest address space; never truncate them (a 64-bit pointer narrowed to
32 bits silently corrupts the guest view). Let ctypes apply natural
alignment -- _pack_ is intentionally NOT set, so the layout is the ABI
default (28 bytes on 32-bit hosts, 40 bytes on 64-bit hosts), which the
root process verifies empirically on the running platform.

This module only declares the layout. It performs no OS calls and touches
no game bytes, so it is safe to import from workspace-only code.
"""

import ctypes


class WINDOWPOS(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("hWndInsertAfter", ctypes.c_void_p),
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
        ("cx", ctypes.c_int32),
        ("cy", ctypes.c_int32),
        ("flags", ctypes.c_uint32),
    ]
    # No _pack_: keep the natural (platform ABI) alignment described above.
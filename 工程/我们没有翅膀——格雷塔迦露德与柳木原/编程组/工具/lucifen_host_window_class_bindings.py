"""lucifen_host_window_class_bindings.py

Raw Win32 window-class / window-procedure / key-state bindings for the host side
of the lucifen host window layer.

This module is bindings only.  It declares the ctypes structures and the five
raw function prototypes the host layer needs and loads ``user32`` exactly once.
The only thing it does at import time is load the system library
(``WinDLL``); it never registers, unregisters, queries or dispatches anything
by itself.

Caller responsibilities (this module provides none of this logic)
-----------------------------------------------------------------
* Architecture layouts, validated by the caller before use:

      pointer size 32-bit (``ctypes.sizeof(ctypes.c_void_p) == 4``):
          WNDCLASSA   == 40 bytes
          WNDCLASSEXA == 48 bytes

      pointer size 64-bit (``ctypes.sizeof(ctypes.c_void_p) == 8``):
          WNDCLASSA   == 72 bytes
          WNDCLASSEXA == 80 bytes

  The caller compares the concrete layout against these sizes; this module
  performs no size check and no adaptation.

* The caller validates every full host handle (``hInstance``, ``hIcon``,
  ``hCursor``, ``hbrBackground`` and, for the EX form, ``hIconSm``) before it
  reaches ``RegisterClassA`` / ``RegisterClassExA``.

* ``lpszMenuName`` and ``lpszClassName`` are ANSI strings.  Their buffers are
  owned and guarded by the caller and must outlive the registered class.  They
  stay ``c_void_p`` here on purpose: this module never allocates, copies,
  widens or frees them, and never keeps a reference to them.

* Only an actual host Python callback may be registered as a window procedure.
  Original guest 32-bit functions/addresses are never registered with, or
  passed to, the OS; if original guest callback code is executed it must run
  through the host trampoline, and that execution requires that no outer
  ``emu_start`` is active.

* This module provides no callbacks, no handle map, no sandbox and no
  validation logic.  The host layer owns all of that.

* ``UnregisterClassA`` is called by the caller only for the host's own class,
  and only after every window created from that class has been destroyed.

* ``GetKeyState`` returns the raw native ``SHORT`` bit pattern as ``c_int16``.
  Callers preserve the actual bits, including the high-order down bit and
  low-order toggle bit; this module never forces, clears or synthesizes native input state.
"""

import ctypes
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_size_t,
    ctypes.c_ssize_t,
)

class WNDCLASSA(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.DWORD),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int32),
        ("cbWndExtra", ctypes.c_int32),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_void_p),
        ("lpszClassName", ctypes.c_void_p),
    ]

class WNDCLASSEXA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("style", wintypes.DWORD),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int32),
        ("cbWndExtra", ctypes.c_int32),
        ("hInstance", ctypes.c_void_p),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", ctypes.c_void_p),
        ("lpszClassName", ctypes.c_void_p),
        ("hIconSm", ctypes.c_void_p),
    ]

RegisterClassA = _user32.RegisterClassA
RegisterClassA.argtypes = [ctypes.POINTER(WNDCLASSA)]
RegisterClassA.restype = ctypes.c_uint16

RegisterClassExA = _user32.RegisterClassExA
RegisterClassExA.argtypes = [ctypes.POINTER(WNDCLASSEXA)]
RegisterClassExA.restype = ctypes.c_uint16

UnregisterClassA = _user32.UnregisterClassA
UnregisterClassA.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
UnregisterClassA.restype = ctypes.c_int

GetKeyState = _user32.GetKeyState
GetKeyState.argtypes = [ctypes.c_int]
GetKeyState.restype = ctypes.c_int16

DefWindowProcA = _user32.DefWindowProcA
DefWindowProcA.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_size_t,
    ctypes.c_ssize_t,
]
DefWindowProcA.restype = ctypes.c_ssize_t

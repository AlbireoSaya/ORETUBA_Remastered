"""Host-side Windows unnamed event objects (kernel32) for the Lucifen host process.

Ownership model: every handle in this module is a host (Win64) HANDLE created and
owned by a single host thread. Handles are kept at full pointer width; nothing here
is a guest-handle ABI and nothing here starts an original engine thread.
"""

import ctypes
import threading
from ctypes import wintypes

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)

_k32.CreateEventA.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPVOID]
_k32.CreateEventA.restype = ctypes.c_void_p
_k32.CloseHandle.argtypes = [ctypes.c_void_p]
_k32.CloseHandle.restype = wintypes.BOOL
_k32.SetEvent.argtypes = [ctypes.c_void_p]
_k32.SetEvent.restype = wintypes.BOOL
_k32.ResetEvent.argtypes = [ctypes.c_void_p]
_k32.ResetEvent.restype = wintypes.BOOL
_k32.WaitForSingleObject.argtypes = [ctypes.c_void_p, wintypes.DWORD]
_k32.WaitForSingleObject.restype = wintypes.DWORD

WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
WAIT_FAILED = 0xFFFFFFFF


class HostEvents:
    """Tracks host event HANDLEs owned by the thread that builds this object."""

    def __init__(self):
        self._owner = threading.get_ident()
        self._handles = set()

    def _check_thread(self):
        if threading.get_ident() != self._owner:
            raise RuntimeError("HostEvents may only be used from its creating thread")

    def _check_owned(self, handle):
        if not isinstance(handle, int) or handle not in self._handles:
            raise ValueError("handle is not owned by this HostEvents instance")
        return handle

    def create(self, manual, initial):
        self._check_thread()
        if type(manual) is not int or type(initial) is not int or manual not in (0, 1) or initial not in (0, 1):
            raise ValueError("manual and initial must be the ints 0 or 1")
        handle = _k32.CreateEventA(None, manual, initial, None)
        if not handle:
            raise OSError(ctypes.get_last_error(), "CreateEventA failed")
        handle = int(handle)
        self._handles.add(handle)
        return handle

    def close(self, handle):
        self._check_thread()
        self._check_owned(handle)
        if not _k32.CloseHandle(ctypes.c_void_p(handle)):
            raise OSError(ctypes.get_last_error(), "CloseHandle failed")
        self._handles.discard(handle)

    def close_all(self):
        self._check_thread()
        failure = None
        for handle in list(self._handles):
            if not _k32.CloseHandle(ctypes.c_void_p(handle)):
                failure = ctypes.get_last_error()
                continue
            self._handles.discard(handle)
        if failure is not None:
            raise OSError(failure, "CloseHandle failed during close_all")

    def set(self, handle):
        self._check_thread()
        self._check_owned(handle)
        if not _k32.SetEvent(ctypes.c_void_p(handle)):
            raise OSError(ctypes.get_last_error(), "SetEvent failed")

    def reset(self, handle):
        self._check_thread()
        self._check_owned(handle)
        if not _k32.ResetEvent(ctypes.c_void_p(handle)):
            raise OSError(ctypes.get_last_error(), "ResetEvent failed")

    def wait_zero(self, handle):
        self._check_thread()
        self._check_owned(handle)
        result = _k32.WaitForSingleObject(ctypes.c_void_p(handle), 0)
        if result == WAIT_FAILED:
            raise OSError(ctypes.get_last_error(), "WaitForSingleObject failed")
        if result not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
            raise OSError(ctypes.get_last_error(), "unexpected wait result %d" % result)
        return result

    @property
    def live_count(self):
        self._check_thread()
        return len(self._handles)

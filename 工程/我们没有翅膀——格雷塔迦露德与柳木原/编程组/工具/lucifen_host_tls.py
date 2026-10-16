"""Generic Windows TLS host wrapper (ctypes). Caller-owned memory only; this
module never allocates or frees memory and never dereferences a pointer."""

from __future__ import annotations

import ctypes

__all__ = [
    "HostTLS",
    "TLS_OUT_OF_INDEXES",
    "current_thread_id",
    "get_last_error",
    "set_last_error",
]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_TlsAlloc = kernel32.TlsAlloc
_TlsAlloc.argtypes = ()
_TlsAlloc.restype = ctypes.c_uint32

_TlsGetValue = kernel32.TlsGetValue
_TlsGetValue.argtypes = (ctypes.c_uint32,)
_TlsGetValue.restype = ctypes.c_void_p

_TlsSetValue = kernel32.TlsSetValue
_TlsSetValue.argtypes = (ctypes.c_uint32, ctypes.c_void_p)
_TlsSetValue.restype = ctypes.c_int

_TlsFree = kernel32.TlsFree
_TlsFree.argtypes = (ctypes.c_uint32,)
_TlsFree.restype = ctypes.c_int

_GetCurrentThreadId = kernel32.GetCurrentThreadId
_GetCurrentThreadId.argtypes = ()
_GetCurrentThreadId.restype = ctypes.c_uint32

_GetLastError = kernel32.GetLastError
_GetLastError.argtypes = ()
_GetLastError.restype = ctypes.c_uint32

_SetLastError = kernel32.SetLastError
_SetLastError.argtypes = (ctypes.c_uint32,)
_SetLastError.restype = None

TLS_OUT_OF_INDEXES = 0xFFFFFFFF
_U32_MAX = 0xFFFFFFFF

E_THREAD = -1     # wrong owner thread before mutation
E_INDEX = -2      # index not a strict non-bool u32
E_OWNED = -3      # index not owned by this host
E_POINTER = -4    # pointer not 0 / not a live registered host pointer
E_NOTEMPTY = -5   # free refused: slot holds a non-null value


def current_thread_id():
    """Real GetCurrentThreadId() as an int."""
    return _GetCurrentThreadId()


def get_last_error():
    """Real GetLastError() as an int."""
    return _GetLastError()


def set_last_error(value):
    """Real SetLastError(); value must be a strict non-bool u32."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("last error must be an int")
    if value < 0 or value > _U32_MAX:
        raise ValueError("last error out of u32 range")
    _SetLastError(value)


def _is_u32(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= _U32_MAX


class HostTLS:
    """Per-thread TLS slots over kernel32, memory passports via `memory.size`."""

    def __init__(self, memory):
        self.memory = memory
        self.owner = _GetCurrentThreadId()
        self.owned = set()
        self._ptr_bits = 8 * ctypes.sizeof(ctypes.c_void_p)

    def _in_thread(self):
        return _GetCurrentThreadId() == self.owner

    def _pointer_error(self, ptr):
        if isinstance(ptr, bool) or not isinstance(ptr, int) or ptr < 0:
            return E_POINTER
        if ptr == 0:
            return 0
        if ptr >= (1 << self._ptr_bits):
            return E_POINTER
        size = None
        if self.memory is not None:
            try:
                size = self.memory.size(ptr)
            except Exception:
                return E_POINTER
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            return E_POINTER
        return 0

    def alloc(self):
        """-> (index, err); registers index only on real success."""
        if not self._in_thread():
            return TLS_OUT_OF_INDEXES, E_THREAD
        index = _TlsAlloc()
        err = ctypes.get_last_error()
        if index == TLS_OUT_OF_INDEXES:
            return TLS_OUT_OF_INDEXES, (err or _GetLastError())
        self.owned.add(index)
        return index, 0

    def get(self, index):
        """-> (host pointer or 0, err); null value is success when last error is 0.

        Validation failures are reported as negative E_* codes and never as
        Windows errors; the Windows API is only touched after validation.
        """
        if not _is_u32(index):
            return 0, E_INDEX
        if index not in self.owned:
            return 0, E_OWNED
        if not self._in_thread():
            return 0, E_THREAD
        ctypes.set_last_error(0)
        value = _TlsGetValue(index)
        err = ctypes.get_last_error()
        if value:
            return int(value), 0
        if err:
            return 0, err
        return 0, 0

    def set(self, index, ptr):
        """-> (ok, err); ptr is 0 or a strict int registered with memory.size>0."""
        if not _is_u32(index):
            return False, E_INDEX
        if index not in self.owned:
            return False, E_OWNED
        if not self._in_thread():
            return False, E_THREAD
        bad = self._pointer_error(ptr)
        if bad:
            return False, bad
        ctypes.set_last_error(0)
        ok = _TlsSetValue(index, ptr)
        err = ctypes.get_last_error()
        if not ok:
            return False, (err or _GetLastError())
        return True, 0

    def free(self, index):
        """-> (ok, err); requires a genuine empty slot (get -> 0, err 0)."""
        if not _is_u32(index):
            return False, E_INDEX
        if index not in self.owned:
            return False, E_OWNED
        if not self._in_thread():
            return False, E_THREAD
        value, err = self.get(index)
        if err:
            return False, err
        if value:
            return False, E_NOTEMPTY
        ctypes.set_last_error(0)
        ok = _TlsFree(index)
        err = ctypes.get_last_error()
        if not ok:
            return False, (err or _GetLastError())
        self.owned.discard(index)
        return True, 0

    def close_all(self):
        """Owner-only. Clear every owned slot to 0, then free it.

        -> list of (index, err) failures (index None when the thread is wrong);
        ownership of every failed slot is preserved.
        """
        failures = []
        if not self._in_thread():
            return [(None, E_THREAD)]
        for index in sorted(self.owned):
            ctypes.set_last_error(0)
            ok = _TlsSetValue(index, None)
            err = ctypes.get_last_error()
            if not ok:
                failures.append((index, err or _GetLastError()))
                continue
            ctypes.set_last_error(0)
            ok = _TlsFree(index)
            err = ctypes.get_last_error()
            if not ok:
                failures.append((index, err or _GetLastError()))
                continue
            self.owned.discard(index)
        return failures

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close_all()
        return False
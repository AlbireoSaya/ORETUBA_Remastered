"""Minimal Windows host32/64 ctypes wrapper around HeapAlloc/GlobalAlloc host memory.

Only the operations implemented below are supported; no guest mapping, no faking.
"""

import ctypes

HEAP_NO_SERIALIZE = 0x00000001
HEAP_ZERO_MEMORY = 0x00000008
GMEM_FIXED = 0x0000

_MAX_BYTES = 1 << 20
_ALLOWED_HEAP_OPTIONS = (0, HEAP_NO_SERIALIZE)
_ALLOWED_HEAP_ALLOC_FLAGS = (0, HEAP_ZERO_MEMORY)

_HANDLE = ctypes.c_void_p
_LPVOID = ctypes.c_void_p
_DWORD = ctypes.c_uint32
_UINT = ctypes.c_uint32
_SIZE_T = ctypes.c_size_t
_BOOL = ctypes.c_int

if ctypes.sizeof(ctypes.c_void_p) not in (4, 8):
    raise RuntimeError("HostMemory requires a 32-bit or 64-bit host CPython (pointer width 4 or 8 bytes)")

_kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

_kernel32.HeapCreate.argtypes = (_DWORD, _SIZE_T, _SIZE_T)
_kernel32.HeapCreate.restype = _HANDLE

_kernel32.HeapAlloc.argtypes = (_HANDLE, _DWORD, _SIZE_T)
_kernel32.HeapAlloc.restype = _LPVOID

_kernel32.HeapFree.argtypes = (_HANDLE, _DWORD, _LPVOID)
_kernel32.HeapFree.restype = _BOOL

_kernel32.HeapDestroy.argtypes = (_HANDLE,)
_kernel32.HeapDestroy.restype = _BOOL

_kernel32.GlobalAlloc.argtypes = (_UINT, _SIZE_T)
_kernel32.GlobalAlloc.restype = _HANDLE

_kernel32.GlobalFree.argtypes = (_HANDLE,)
_kernel32.GlobalFree.restype = _HANDLE

__all__ = [
    "HostMemory",
    "HEAP_NO_SERIALIZE",
    "HEAP_ZERO_MEMORY",
    "GMEM_FIXED",
]


def _strict_int(value, name):
    if type(value) is not int:
        raise TypeError("%s must be int, got %s" % (name, type(value).__name__))
    return value


def _ptr_to_int(value):
    return 0 if value is None else int(value)


class _Block(object):
    __slots__ = ("kind", "owner", "size")

    def __init__(self, kind, owner, size):
        self.kind = kind
        self.owner = owner
        self.size = size


class HostMemory(object):
    """Registered heap/global host allocations with real Win32 calls."""

    def __init__(self):
        self._heaps = {}
        self._blocks = {}
        self._close_failures = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close_all()
        except Exception as close_error:
            if exc is not None:
                raise close_error from exc
            raise
        return False

    def heap_create(self, options, initial, maximum):
        options = _strict_int(options, "options")
        initial = _strict_int(initial, "initial")
        maximum = _strict_int(maximum, "maximum")
        if options not in _ALLOWED_HEAP_OPTIONS:
            raise ValueError("options must be 0 or HEAP_NO_SERIALIZE (1)")
        if not (0 <= initial <= _MAX_BYTES):
            raise ValueError("initial must be within 0..%d" % _MAX_BYTES)
        if maximum != 0:
            raise ValueError("maximum must be 0 (growable heap)")

        handle = _ptr_to_int(
            self._HeapCreate_internal(_DWORD(options), _SIZE_T(initial), _SIZE_T(maximum))
        )
        if handle == 0:
            return 0
        try:
            self._heaps[handle] = set()
        except BaseException:
            self._heaps.pop(handle, None)
            _kernel32.HeapDestroy(_HANDLE(handle))
            raise
        return handle

    def heap_alloc(self, heap, flags, size):
        heap = _strict_int(heap, "heap")
        flags = _strict_int(flags, "flags")
        size = _strict_int(size, "size")
        if heap not in self._heaps:
            raise ValueError("heap is not registered by this HostMemory instance")
        if flags not in _ALLOWED_HEAP_ALLOC_FLAGS:
            raise ValueError("flags must be 0 or HEAP_ZERO_MEMORY (8)")
        if not (1 <= size <= _MAX_BYTES):
            raise ValueError("size must be within 1..%d" % _MAX_BYTES)

        ptr = _ptr_to_int(
            _kernel32.HeapAlloc(_HANDLE(heap), _DWORD(flags), _SIZE_T(size))
        )
        if ptr == 0:
            return 0
        try:
            self._blocks[ptr] = _Block("heap", heap, size)
            self._heaps[heap].add(ptr)
        except BaseException:
            self._blocks.pop(ptr, None)
            self._heaps[heap].discard(ptr)
            _kernel32.HeapFree(_HANDLE(heap), _DWORD(0), _LPVOID(ptr))
            raise
        return ptr

    def heap_free(self, heap, flags, ptr):
        heap = _strict_int(heap, "heap")
        flags = _strict_int(flags, "flags")
        ptr = _strict_int(ptr, "ptr")
        if flags != 0:
            raise ValueError("flags must be 0 for heap_free")
        if heap not in self._heaps:
            raise ValueError("heap is not registered by this HostMemory instance")
        block = self._blocks.get(ptr)
        if block is None or block.kind != "heap" or block.owner != heap:
            raise ValueError("ptr is not a registered heap block of this heap")

        ok = bool(_kernel32.HeapFree(_HANDLE(heap), _DWORD(flags), _LPVOID(ptr)))
        if ok:
            self._blocks.pop(ptr, None)
            self._heaps[heap].discard(ptr)
        return ok

    def heap_destroy(self, heap):
        heap = _strict_int(heap, "heap")
        if heap not in self._heaps:
            raise ValueError("heap is not registered by this HostMemory instance")
        if self._heaps[heap]:
            raise RuntimeError("heap still owns live blocks; free them first")

        ok = bool(_kernel32.HeapDestroy(_HANDLE(heap)))
        if ok:
            del self._heaps[heap]
        return ok

    def global_alloc(self, flags, size):
        flags = _strict_int(flags, "flags")
        size = _strict_int(size, "size")
        if flags != GMEM_FIXED:
            raise ValueError("only GMEM_FIXED (0) is supported")
        if not (1 <= size <= _MAX_BYTES):
            raise ValueError("size must be within 1..%d" % _MAX_BYTES)

        ptr = _ptr_to_int(_kernel32.GlobalAlloc(_UINT(flags), _SIZE_T(size)))
        if ptr == 0:
            return 0
        try:
            self._blocks[ptr] = _Block("global", 0, size)
        except BaseException:
            self._blocks.pop(ptr, None)
            _kernel32.GlobalFree(_HANDLE(ptr))
            raise
        return ptr

    def global_free(self, ptr):
        ptr = _strict_int(ptr, "ptr")
        block = self._blocks.get(ptr)
        if block is None or block.kind != "global":
            raise ValueError("ptr is not a registered global block")

        rc = _ptr_to_int(_kernel32.GlobalFree(_HANDLE(ptr)))
        if rc == 0:
            self._blocks.pop(ptr, None)
            return 0
        return rc

    def read(self, ptr, n):
        ptr = _strict_int(ptr, "ptr")
        n = _strict_int(n, "n")
        block = self._blocks.get(ptr)
        if block is None:
            raise ValueError("ptr is not a registered block")
        if not (0 <= n <= block.size):
            raise ValueError("n must be within 0..%d" % block.size)
        return ctypes.string_at(ptr, n)

    def write(self, ptr, data):
        ptr = _strict_int(ptr, "ptr")
        if type(data) is not bytes:
            raise TypeError("data must be bytes, got %s" % type(data).__name__)
        block = self._blocks.get(ptr)
        if block is None:
            raise ValueError("ptr is not a registered block")
        if len(data) > block.size:
            raise ValueError("data length exceeds registered size %d" % block.size)
        ctypes.memmove(ptr, data, len(data))
        return None

    def size(self, ptr):
        ptr = _strict_int(ptr, "ptr")
        block = self._blocks.get(ptr)
        if block is None:
            raise ValueError("ptr is not a registered block")
        return block.size

    def close_all(self):
        failures = []

        for ptr, block in list(self._blocks.items()):
            if block.kind != "global":
                continue
            try:
                rc = _ptr_to_int(_kernel32.GlobalFree(_HANDLE(ptr)))
            except BaseException as exc:
                failures.append(("global_free", ptr, repr(exc)))
                continue
            if rc == 0:
                self._blocks.pop(ptr, None)
            else:
                failures.append(("global_free", ptr, rc))

        for ptr, block in list(self._blocks.items()):
            if block.kind != "heap":
                continue
            owner = block.owner
            try:
                ok = bool(_kernel32.HeapFree(_HANDLE(owner), _DWORD(0), _LPVOID(ptr)))
            except BaseException as exc:
                failures.append(("heap_free", ptr, repr(exc)))
                continue
            if ok:
                self._blocks.pop(ptr, None)
                owner_blocks = self._heaps.get(owner)
                if owner_blocks is not None:
                    owner_blocks.discard(ptr)
            else:
                failures.append(("heap_free", ptr, 0))

        for heap in list(self._heaps.keys()):
            live = self._heaps.get(heap)
            if live:
                failures.append(("heap_destroy_skipped", heap, len(live)))
                continue
            try:
                ok = bool(_kernel32.HeapDestroy(_HANDLE(heap)))
            except BaseException as exc:
                failures.append(("heap_destroy", heap, repr(exc)))
                continue
            if ok:
                del self._heaps[heap]
            else:
                failures.append(("heap_destroy", heap, 0))

        self._close_failures = list(failures)
        if failures:
            raise RuntimeError("close_all could not release everything: %r" % (failures,))

    def _HeapCreate_internal(self, options, initial, maximum):
        return _kernel32.HeapCreate(options, initial, maximum)

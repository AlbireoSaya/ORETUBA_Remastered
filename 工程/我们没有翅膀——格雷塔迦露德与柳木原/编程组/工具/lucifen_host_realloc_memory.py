"""Real Win32 HeapReAlloc layered on lucifen_host_memory.

Adds HostReallocMemory, a HostMemory subclass whose heap_realloc reallocates an
already registered heap block through the real HeapReAlloc entry point. The
returned passport replaces the old one on success; failure leaves the old
passport, heap set and size untouched. No emulation, no extra alloc/free.
"""

import ctypes

from lucifen_host_memory import HostMemory, _Block, _strict_int

_HANDLE = ctypes.c_void_p
_LPVOID = ctypes.c_void_p
_DWORD = ctypes.c_uint32
_SIZE_T = ctypes.c_size_t

_MAX_BYTES = 1 << 20
_ALLOWED_HEAP_REALLOC_FLAGS = (0, 8, 16, 24)

system = ctypes.WinDLL("kernel32", use_last_error=True)

system.HeapReAlloc.argtypes = (_HANDLE, _DWORD, _LPVOID, _SIZE_T)
system.HeapReAlloc.restype = _LPVOID

__all__ = ["HostReallocMemory"]


def _ptr_to_int(value):
    return 0 if value is None else int(value)


class HostReallocMemory(HostMemory):
    """HostMemory that can reallocate its own registered heap blocks."""

    def heap_realloc(self, heap, flags, ptr, size):
        heap = _strict_int(heap, "heap")
        flags = _strict_int(flags, "flags")
        ptr = _strict_int(ptr, "ptr")
        size = _strict_int(size, "size")

        if heap not in self._heaps:
            raise ValueError("heap is not registered by this HostMemory instance")
        block = self._blocks.get(ptr)
        if block is None or block.kind != "heap" or block.owner != heap:
            raise ValueError("ptr is not a registered heap block of this heap")
        if flags not in _ALLOWED_HEAP_REALLOC_FLAGS:
            raise ValueError("flags must be one of 0, 8, 16, 24")
        if not (1 <= size <= _MAX_BYTES):
            raise ValueError("size must be within 1..%d" % _MAX_BYTES)

        new_ptr = _ptr_to_int(
            system.HeapReAlloc(
                _HANDLE(heap), _DWORD(flags), _LPVOID(ptr), _SIZE_T(size)
            )
        )
        if new_ptr == 0:
            return 0

        block.size = size
        if new_ptr != ptr:
            del self._blocks[ptr]
            self._heaps[heap].discard(ptr)
            self._blocks[new_ptr] = block
            self._heaps[heap].add(new_ptr)
        return new_ptr
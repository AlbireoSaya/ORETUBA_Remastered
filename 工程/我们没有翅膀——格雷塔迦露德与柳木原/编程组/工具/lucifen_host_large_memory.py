import ctypes
import lucifen_host_memory as _base
from lucifen_host_memory import _Block, _strict_int
from lucifen_host_realloc_memory import HostReallocMemory, system as _realloc_api


class HostLargeMemory(HostReallocMemory):
    def __init__(self, max_bytes=32 << 20):
        if type(max_bytes) is not int:
            raise TypeError("max_bytes must be int")
        if not (1 <= max_bytes <= 64 << 20):
            raise ValueError("max_bytes out of range")
        super().__init__()
        self._max_bytes = max_bytes

    def heap_alloc(self, heap, flags, size):
        heap = _strict_int(heap, "heap")
        flags = _strict_int(flags, "flags")
        size = _strict_int(size, "size")
        if heap not in self._heaps:
            raise ValueError("heap is not registered by this HostMemory instance")
        if flags not in _base._ALLOWED_HEAP_ALLOC_FLAGS:
            raise ValueError("flags must be 0 or HEAP_ZERO_MEMORY (8)")
        if not (1 <= size <= self._max_bytes):
            raise ValueError("size must be within 1..%d" % self._max_bytes)

        ptr = _base._ptr_to_int(
            _base._kernel32.HeapAlloc(ctypes.c_void_p(heap), ctypes.c_uint32(flags), ctypes.c_size_t(size))
        )
        if ptr == 0:
            return 0
        try:
            self._blocks[ptr] = _Block("heap", heap, size)
            self._heaps[heap].add(ptr)
        except BaseException:
            self._blocks.pop(ptr, None)
            self._heaps[heap].discard(ptr)
            _base._kernel32.HeapFree(ctypes.c_void_p(heap), ctypes.c_uint32(0), ctypes.c_void_p(ptr))
            raise
        return ptr

    def global_alloc(self, flags, size):
        flags = _strict_int(flags, "flags")
        size = _strict_int(size, "size")
        if flags != 0:
            raise ValueError("only GMEM_FIXED (0) is supported")
        if not (1 <= size <= self._max_bytes):
            raise ValueError("size must be within 1..%d" % self._max_bytes)

        ptr = int(_base._kernel32.GlobalAlloc(ctypes.c_uint32(flags), ctypes.c_size_t(size)) or 0)
        if ptr == 0:
            return 0
        try:
            self._blocks[ptr] = _Block("global", 0, size)
        except BaseException:
            self._blocks.pop(ptr, None)
            _base._kernel32.GlobalFree(ctypes.c_void_p(ptr))
            raise
        return ptr

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
        if flags not in (0, 8, 16, 24):
            raise ValueError("flags must be one of 0, 8, 16, 24")
        if not (1 <= size <= self._max_bytes):
            raise ValueError("size must be within 1..%d" % self._max_bytes)

        raw = _realloc_api.HeapReAlloc(
            ctypes.c_void_p(heap),
            ctypes.c_uint32(flags),
            ctypes.c_void_p(ptr),
            ctypes.c_size_t(size),
        )
        new_ptr = int(raw or 0)
        if new_ptr == 0:
            return 0

        block.size = size
        if new_ptr != ptr:
            del self._blocks[ptr]
            self._heaps[heap].discard(ptr)
            self._blocks[new_ptr] = block
            self._heaps[heap].add(new_ptr)
        return new_ptr

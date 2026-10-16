from lucifen_guest_memory_bridge import PAGE,GUARD,_ceil_page,_FILL_GUARD,_FILL_BYTE
from lucifen_guest_realloc_bridge import GuestReallocBlocks


class GuestLargeBlocks(GuestReallocBlocks):
    def __init__(self, uc, host, start=0x07000000, stop=0x17000000, max_bytes=32 << 20):
        if type(max_bytes) is not int or not (1 <= max_bytes <= (64 << 20)):
            raise ValueError("max_bytes must be an int in 1..64<<20")
        super().__init__(uc, host, start, stop)
        self._max_bytes = max_bytes

    def bind(self, hostptr):
        if type(hostptr) is not int or hostptr <= 0:
            raise ValueError("hostptr must be a non-bool positive int")
        if hostptr in self._by_host:
            raise ValueError("hostptr already bound")
        size = self._host.size(hostptr)
        if type(size) is not int or not (1 <= size <= self._max_bytes):
            raise ValueError("host block not registered or bad size")
        blob = bytes(self._host.read(hostptr, size))
        if len(blob) != size:
            raise ValueError("host read size mismatch")
        map_size = _ceil_page(size + 2 * GUARD)
        base = self._next
        if base + map_size > self._stop:
            raise MemoryError("guest arena exhausted")
        payload = base + GUARD
        self._uc.mem_map(base, map_size)
        try:
            self._uc.mem_write(base, _FILL_BYTE * map_size)
            self._uc.mem_write(payload, blob)
            self._by_guest[payload] = (hostptr, base, map_size, size)
            self._by_host[hostptr] = payload
        except BaseException:
            self._by_guest.pop(payload, None)
            self._by_host.pop(hostptr, None)
            try:
                self._uc.mem_unmap(base, map_size)
            except Exception:
                pass
            raise
        self._next = base + map_size
        return payload

    def remap_after_realloc(self, old_guest, new_host):
        oldhost, base, span, oldsize = self._entry(old_guest)
        self._check(old_guest)
        if type(new_host) is not int or new_host <= 0:
            raise ValueError("new_host must be a non-bool positive int")
        newsize = self._host.size(new_host)
        if type(newsize) is not int or not (1 <= newsize <= self._max_bytes):
            raise ValueError("new host block not registered or bad size")
        if new_host != oldhost and new_host in self._by_host:
            raise ValueError("new_host already bound")
        blob = bytes(self._host.read(new_host, newsize))
        if len(blob) != newsize:
            raise ValueError("host read size mismatch")
        if new_host == oldhost:
            return self._samehost(old_guest, newsize, blob)
        return self._moved(old_guest, new_host)

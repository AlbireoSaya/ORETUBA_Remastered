from lucifen_guest_memory_bridge import GuestMemoryBlocks,PAGE,GUARD,MAX_HOST_SIZE,_ceil_page,_FILL_GUARD,_FILL_BYTE

class GuestReallocBlocks(GuestMemoryBlocks):
    def remap_after_realloc(self, old_guest, new_host):
        oldhost, base, span, oldsize = self._entry(old_guest)
        self._check(old_guest)
        if type(new_host) is not int or new_host <= 0:
            raise ValueError("new_host must be a non-bool positive int")
        newsize = self._host.size(new_host)
        if type(newsize) is not int or not (1 <= newsize <= MAX_HOST_SIZE):
            raise ValueError("new host block not registered or bad size")
        if new_host != oldhost and new_host in self._by_host:
            raise ValueError("new_host already bound")
        blob = bytes(self._host.read(new_host, newsize))
        if len(blob) != newsize:
            raise ValueError("host read size mismatch")
        if new_host == oldhost:
            return self._samehost(old_guest, newsize, blob)
        return self._moved(old_guest, new_host)

    def _moved(self, old_guest, new_host):
        new_guest = self.bind(new_host)
        self.unmap(old_guest)
        return new_guest

    def _samehost(self, old_guest, new_size, blob):
        hostptr, base, map_size, old_size = self._entry(old_guest)
        need = _ceil_page(new_size + 2 * GUARD)
        span = max(map_size, need)
        grew = need > map_size
        old_map = None
        added = 0
        try:
            if grew:
                if base + need > self._stop:
                    raise MemoryError("guest arena exhausted")
                start = base + map_size
                end = base + need
                for lo, hi, perms in self._uc.mem_regions():
                    if lo < end and hi >= start:
                        raise MemoryError("guest region overlap")
                old_map = bytes(self._uc.mem_read(base, map_size))
                self._uc.mem_map(start, need - map_size)
                added = need - map_size
                self._uc.mem_write(start, _FILL_BYTE * added)
            else:
                old_map = bytes(self._uc.mem_read(base, map_size))
            self._uc.mem_write(old_guest, blob)
            self._uc.mem_write(old_guest + new_size, _FILL_GUARD)
        except BaseException:
            if old_map is not None:
                try:
                    self._uc.mem_write(base, old_map)
                except Exception:
                    pass
            if added:
                try:
                    self._uc.mem_unmap(base + map_size, added)
                except Exception:
                    pass
            raise
        self._by_guest[old_guest] = (hostptr, base, span, new_size)
        new_end = base + span
        if new_end > self._next:
            self._next = new_end
        return old_guest

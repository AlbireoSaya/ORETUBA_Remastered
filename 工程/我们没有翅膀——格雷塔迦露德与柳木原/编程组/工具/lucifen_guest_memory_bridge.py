PAGE = 4096
GUARD = 128
FILL = 0xA5
MAX_HOST_SIZE = 1 << 20
U32_MAX = 0xFFFFFFFF

_FILL_BYTE = bytes([FILL])
_FILL_GUARD = _FILL_BYTE * GUARD


def _ceil_page(n):
    return -(-n // PAGE) * PAGE


class GuestMemoryBlocks:
    def __init__(self, uc, host, start=0x07000000, stop=0x17000000):
        if type(start) is not int or type(stop) is not int:
            raise TypeError("start/stop must be int")
        if start % PAGE or stop % PAGE:
            raise ValueError("start/stop must be page aligned")
        if not (1 <= start < stop <= (1 << 32)):
            raise ValueError("start/stop out of u32 page range")
        self._uc = uc
        self._host = host
        self._start = start
        self._stop = stop
        self._next = start
        self._by_guest = {}
        self._by_host = {}

    @property
    def live_count(self):
        return len(self._by_guest)

    def bind(self, hostptr):
        if type(hostptr) is not int or hostptr <= 0:
            raise ValueError("hostptr must be a non-bool positive int")
        if hostptr in self._by_host:
            raise ValueError("hostptr already bound")
        size = self._host.size(hostptr)
        if type(size) is not int or not (1 <= size <= MAX_HOST_SIZE):
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

    def _entry(self, guestptr):
        if type(guestptr) is not int or not (0 <= guestptr <= U32_MAX):
            raise ValueError("guestptr must be a non-bool u32 int")
        ent = self._by_guest.get(guestptr)
        if ent is None:
            raise KeyError("guestptr not registered")
        return ent

    def _check(self, guestptr):
        hostptr, base, map_size, size = self._entry(guestptr)
        if bytes(self._uc.mem_read(base, GUARD)) != _FILL_GUARD:
            raise ValueError("front guard corrupted")
        if bytes(self._uc.mem_read(guestptr + size, GUARD)) != _FILL_GUARD:
            raise ValueError("back guard corrupted")
        data = bytes(self._uc.mem_read(guestptr, size))
        if len(data) != size:
            raise ValueError("guest read size mismatch")
        return data

    def sync(self, guestptr):
        hostptr, base, map_size, size = self._entry(guestptr)
        data = self._check(guestptr)
        self._host.write(hostptr, data)
        back = bytes(self._host.read(hostptr, size))
        if back != data:
            raise AssertionError("host sync mismatch")
        return data

    def host_pointer(self, guestptr):
        return self._entry(guestptr)[0]

    def size(self, guestptr):
        return self._entry(guestptr)[3]

    def unmap(self, guestptr):
        hostptr, base, map_size, size = self._entry(guestptr)
        self._check(guestptr)
        self._uc.mem_unmap(base, map_size)
        del self._by_guest[guestptr]
        self._by_host.pop(hostptr, None)

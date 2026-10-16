def _exact_int(value):
    if type(value) is not int:
        raise ValueError("expected exact int")
    return value

class GuestCursorHandles:
    _MAX = 0xFFFFFFFF

    def __init__(self, base=0x69fc0000, host_bits=64):
        base = _exact_int(base)
        host_bits = _exact_int(host_bits)
        if not 1 <= base <= self._MAX:
            raise ValueError("base")
        if host_bits not in (32, 64):
            raise ValueError("host_bits")
        self.base = base
        self.host_bits = host_bits
        self._next = base
        self.dict_by_guest = {}
        self._by_host = {}

    def intern(self, host):
        host = _exact_int(host)
        if not 0 <= host <= (1 << self.host_bits) - 1:
            raise ValueError("host")
        if host == 0:
            return 0
        if host in self._by_host:
            return self._by_host[host]
        token = self._next
        if token > self._MAX:
            raise OverflowError("guest cursor tokens exhausted")
        self._next += 0x100
        self._by_host[host] = token
        self.dict_by_guest[token] = host
        return token

    def to_host(self, guest):
        guest = _exact_int(guest)
        if not 0 <= guest <= self._MAX:
            raise ValueError("guest")
        if guest == 0:
            return 0
        if guest not in self.dict_by_guest:
            raise KeyError(guest)
        return self.dict_by_guest[guest]

    @property
    def live_count(self):
        return len(self.dict_by_guest)

    def clear(self):
        self.dict_by_guest.clear()
        self._by_host.clear()
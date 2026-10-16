import ctypes

class GuestThreadHandles:
    def __init__(self):
        self._guest_to_host = {}
        self._host_to_guest = {}

    @property
    def live_count(self):
        return len(self._guest_to_host)

    @staticmethod
    def _check_guest(guest):
        if type(guest) is not int or not 1 <= guest <= 0xFFFFFFFF:
            raise ValueError("guest must be int in 1..FFFFFFFF")

    @staticmethod
    def _check_host(host):
        bits = ctypes.sizeof(ctypes.c_void_p) * 8
        if type(host) is not int or not 1 <= host <= (1 << bits) - 1:
            raise ValueError("host must be int in 1..(1<<(sizeof(c_void_p)*8))-1")

    def register(self, guest, host):
        self._check_guest(guest)
        self._check_host(host)
        if guest in self._guest_to_host:
            raise ValueError("guest already registered")
        if host in self._host_to_guest:
            raise ValueError("host already registered")
        self._guest_to_host[guest] = host
        self._host_to_guest[host] = guest

    def resolve(self, guest):
        self._check_guest(guest)
        if guest not in self._guest_to_host:
            raise ValueError("guest not registered")
        return self._guest_to_host[guest]

    def remove(self, guest):
        self._check_guest(guest)
        if guest not in self._guest_to_host:
            raise ValueError("guest not registered")
        host = self._guest_to_host.pop(guest)
        del self._host_to_guest[host]
        return host

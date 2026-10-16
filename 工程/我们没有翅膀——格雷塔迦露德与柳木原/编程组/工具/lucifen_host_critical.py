"""Host-side critical-section proxy for single-threaded guests (32/64-bit Windows)."""

import ctypes
import threading

__all__ = ("HostCritical", "guest_interlocked_exchange_stub")

_VOIDP, _ADDR = ctypes.c_void_p, ctypes.addressof
_WORDS = 6 if ctypes.sizeof(_VOIDP) == 4 else 5  # Windows 32-bit CRITICAL_SECTION is 24 bytes (6 pointer-sized words); Windows 64-bit is 40 bytes (5 pointer-sized words)
_NAMES = ("InitializeCriticalSection", "EnterCriticalSection",
          "LeaveCriticalSection", "DeleteCriticalSection")


class HostCritical:
    """One CRITICAL_SECTION surrogate per guest lock key; never handed to guest."""

    def __init__(self):
        if ctypes.sizeof(_VOIDP) not in (4, 8):
            raise RuntimeError("HostCritical requires 32-bit or 64-bit Windows (pointer width 4 or 8 bytes)")
        self._k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        for name in _NAMES:
            fn = getattr(self._k32, name)
            fn.argtypes, fn.restype = [_VOIDP], None
        self._sections = {}  # key -> (surrogate, depth)
        self._owners = {}  # key -> owning threading ident

    @property
    def live_count(self):
        return len(self._sections)

    @staticmethod
    def _key(key):
        if isinstance(key, bool) or not isinstance(key, int):
            raise ValueError("key must be a non-bool integer")
        if not 1 <= key <= 0xFFFFFFFF or key % 4:
            raise ValueError("key must be in 1..FFFFFFFF and 4-aligned")
        return key

    def _entry(self, key):
        if key not in self._sections:
            raise RuntimeError("key is not initialised")
        if self._owners[key] != threading.get_ident():
            raise RuntimeError("key is owned by another thread")
        return self._sections[key]

    def init(self, key):
        key = self._key(key)
        if key in self._sections:
            raise RuntimeError("key is already initialised")
        surrogate = (_VOIDP * _WORDS)()
        self._k32.InitializeCriticalSection(_ADDR(surrogate))
        self._sections[key] = (surrogate, 0)
        self._owners[key] = threading.get_ident()

    def enter(self, key):
        key = self._key(key)
        surrogate, depth = self._entry(key)
        self._k32.EnterCriticalSection(_ADDR(surrogate))
        self._sections[key] = (surrogate, depth + 1)

    def leave(self, key):
        key = self._key(key)
        surrogate, depth = self._entry(key)
        if depth == 0:
            raise RuntimeError("key is not held")
        self._sections[key] = (surrogate, depth - 1)
        self._k32.LeaveCriticalSection(_ADDR(surrogate))

    def delete(self, key):
        key = self._key(key)
        surrogate, depth = self._entry(key)
        if depth != 0:
            raise RuntimeError("key is still held")
        self._k32.DeleteCriticalSection(_ADDR(surrogate))
        del self._sections[key]
        del self._owners[key]

    def close_all(self):
        for key in list(self._sections):
            self.delete(key)


def guest_interlocked_exchange_stub():
    """x86 stdcall LONG InterlockedExchange(LONG *target, LONG value).

    [esp+4] is the LONG* and [esp+8] the new value; the real CPU ``xchg``
    supplies atomicity.  Unicorn single-threaded guest CPUs only: this is a
    hand-assembled stub, not the 64-bit Windows InterlockedExchange API.
    """
    return bytes((
        0x8B, 0x4C, 0x24, 0x04,  # mov ecx, [esp+4]
        0x8B, 0x44, 0x24, 0x08,  # mov eax, [esp+8]
        0x87, 0x01,              # xchg [ecx], eax
        0xC2, 0x08, 0x00,        # ret 8
    ))

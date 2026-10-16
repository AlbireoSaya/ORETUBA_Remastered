import ctypes
from lucifen_host_critical import HostCritical
from lucifen_host_tls import current_thread_id


class HostSharedCritical(HostCritical):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._owner_tid = current_thread_id()
        self._allowed = {self._owner_tid}
        self._holders = {}

    def register_thread(self, tid):
        if current_thread_id() != self._owner_tid:
            return False
        if isinstance(tid, bool) or not isinstance(tid, int):
            return False
        if tid < 1 or tid > 0xFFFFFFFF:
            return False
        if tid in self._allowed:
            return False
        self._allowed.add(tid)
        return True

    def _entry(self, key):
        tid = current_thread_id()
        if tid not in self._allowed:
            raise RuntimeError("caller thread %r not registered" % (tid,))
        if key not in self._sections:
            raise RuntimeError("section %r not initialized" % (key,))
        return self._sections[key]

    def init(self, key):
        tid = current_thread_id()
        if tid not in self._allowed:
            raise RuntimeError("caller thread %r not registered" % (tid,))
        super().init(key)
        self._holders[key] = None

    def enter(self, key):
        key = self._key(key)
        surrogate, _ = self._entry(key)
        self._k32.EnterCriticalSection(ctypes.addressof(surrogate))
        _, depth = self._sections[key]
        self._sections[key] = (surrogate, depth + 1)
        self._holders[key] = current_thread_id()

    def leave(self, key):
        k = self._key(key)
        self._entry(k)
        section = self._sections.get(k)
        if section is None:
            raise RuntimeError("HostSharedCritical.leave: unknown critical section")
        buf, depth = section
        if depth <= 0 or self._holders.get(k) != current_thread_id():
            raise RuntimeError("HostSharedCritical.leave: lock not held by current thread")
        depth -= 1
        self._sections[k] = (buf, depth)
        if depth == 0:
            self._holders[k] = None
        self._k32.LeaveCriticalSection(ctypes.addressof(buf))

    def delete(self, key):
        super().delete(key)
        self._holders.pop(key, None)

    def unregister_current_thread(self):
        tid = current_thread_id()
        if tid not in self._allowed or tid == self._owner_tid:
            raise RuntimeError("current thread is not allowed to unregister")
        if any(holder == tid for holder in self._holders.values()):
            raise RuntimeError("current thread still holds critical section keys")
        self._allowed.remove(tid)

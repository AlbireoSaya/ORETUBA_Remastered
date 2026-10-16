from lucifen_host_tls import HostTLS, current_thread_id, E_THREAD, E_INDEX, E_OWNED, E_NOTEMPTY, _is_u32

class HostSharedTLS(HostTLS):
    def __init__(self, memory):
        super().__init__(memory)
        self._allowed = {self.owner}
        self._seen = {}

    def register_thread(self, tid):
        if current_thread_id() != self.owner:
            return False, E_THREAD
        if isinstance(tid, bool) or not _is_u32(tid) or tid == 0:
            return False, E_INDEX
        if tid in self._allowed:
            return False, E_OWNED
        self._allowed.add(tid)
        return True, None

    def _in_thread(self):
        return current_thread_id() in self._allowed

    def get(self, index):
        value, err = super().get(index)
        if err == 0:
            tid = current_thread_id()
            self._seen[(tid, index)] = value
        return value, err

    def set(self, index, ptr):
        ok, err = super().set(index, ptr)
        if ok and not err:
            self._seen[(current_thread_id(), index)] = ptr
        return ok, err

    def free(self, index):
        if not _is_u32(index):
            return (False, E_INDEX)
        tid = current_thread_id()
        if index not in self.owned:
            return (False, E_OWNED)
        if not self._in_thread():
            return (False, E_THREAD)
        for (other_tid, other_index), value in self._seen.items():
            if other_index == index and other_tid != tid and value != 0:
                return (False, E_NOTEMPTY)
        ok, err = super().free(index)
        if ok:
            for key in [k for k in self._seen if k[1] == index]:
                del self._seen[key]
        return (ok, err)

    def unregister_current_thread(self):
        tid = current_thread_id()
        if tid == self.owner or tid not in self._allowed:
            raise RuntimeError(E_THREAD)
        for index in sorted(self.owned):
            ok, err = self.set(index, 0)
            if not ok:
                raise RuntimeError(err if err is not None else E_OWNED)
        for key in [key for key in self._seen if key[0] == tid]:
            del self._seen[key]
        self._allowed.discard(tid)

    def close_all(self):
        if current_thread_id() != self.owner or self._allowed != {self.owner}:
            return [(None, E_THREAD)]
        failures = super().close_all()
        self._seen = {
            key: value
            for key, value in self._seen.items()
            if key[1] in self.owned
        }
        return failures

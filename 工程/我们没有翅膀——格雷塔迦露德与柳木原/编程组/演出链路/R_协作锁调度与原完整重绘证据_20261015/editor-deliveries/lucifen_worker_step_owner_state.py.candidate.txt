from lucifen_host_tls import current_thread_id


class WorkerStepOwnerState:
    def __init__(self, gate):
        self._gate = gate
        self._owner_tid = current_thread_id()
        self._generation = 0
        self._parked = False
        self._payload = None

    def _assert_owner(self):
        if current_thread_id() != self._owner_tid:
            raise RuntimeError("worker step owner mismatch")

    @property
    def generation(self):
        self._assert_owner()
        return self._generation

    @property
    def payload(self):
        self._assert_owner()
        if not self._parked:
            raise RuntimeError("worker step payload is not parked")
        return self._payload
"""单次真实 worker 交接门：仅一次 park/resume 握手，不创建线程、不关闭资源。"""

import threading

from lucifen_host_tls import current_thread_id

class WorkerParkGate:
    _MAX_WAIT = 60

    def __init__(self):
        self._owner = current_thread_id()
        self._lock = threading.RLock()
        self._parked = threading.Event()
        self._resume = threading.Event()
        self._state = "new"
        self._payload = None
        self._worker_tid = None

    def _is_owner(self):
        return current_thread_id() == self._owner

    def park(self, payload):
        if self._is_owner():
            raise RuntimeError("park must be called from a non-owner worker thread")
        with self._lock:
            if self._state != "new":
                raise RuntimeError("park requires state 'new', got %r" % (self._state,))
            self._worker_tid = current_thread_id()
            self._payload = payload
            self._state = "parked"
        self._parked.set()
        self._resume.wait()
        return payload

    def wait_park(self, timeout):
        if not self._is_owner():
            raise RuntimeError("wait_park must be called from the owner thread")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be a non-bool int or float")
        if timeout != timeout or timeout <= 0 or timeout > self._MAX_WAIT:
            raise ValueError("timeout must be finite, positive and <= 60")
        return self._parked.wait(float(timeout))

    @property
    def payload(self):
        if not self._is_owner():
            raise RuntimeError("payload is owner readable only")
        if self._state not in ("parked", "released"):
            raise RuntimeError("payload unavailable in state %r" % (self._state,))
        return self._payload

    @property
    def worker_tid(self):
        return self._worker_tid

    def release(self):
        if not self._is_owner():
            raise RuntimeError("release must be called from the owner thread")
        with self._lock:
            if self._state != "parked":
                raise RuntimeError("release requires state 'parked', got %r" % (self._state,))
            self._state = "released"
            self._resume.set()

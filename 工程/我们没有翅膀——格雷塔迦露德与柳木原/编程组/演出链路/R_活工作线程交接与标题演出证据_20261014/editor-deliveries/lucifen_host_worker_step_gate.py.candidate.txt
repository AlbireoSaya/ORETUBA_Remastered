import math

from lucifen_host_worker_step_state import WorkerStepState, current_thread_id


class WorkerStepGate(WorkerStepState):
    def wait_park(self, expected_generation, timeout):
        if current_thread_id() != self._owner_tid:
            raise RuntimeError("wait_park not owner")
        if type(expected_generation) is not int or expected_generation < 1:
            raise ValueError("invalid expected_generation")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError("invalid timeout")
        with self._condition:
            if self._generation > expected_generation or expected_generation > self._generation + 1:
                raise RuntimeError("invalid generation")
            if self._condition.wait_for(lambda: self._parked and self._generation == expected_generation, timeout):
                return self._payload
            return None

    def release(self, expected_generation, command):
        if current_thread_id() != self._owner_tid:
            raise RuntimeError("release not owner")
        if type(expected_generation) is not int or expected_generation < 1:
            raise ValueError("invalid expected_generation")
        if command not in ("continue", "finish"):
            raise ValueError("invalid command")
        with self._condition:
            if not self._parked or self._generation != expected_generation or self._released_generation >= expected_generation:
                raise RuntimeError("not parked")
            self._command = command
            self._released_generation = expected_generation
            self._parked = False
            self._condition.notify_all()
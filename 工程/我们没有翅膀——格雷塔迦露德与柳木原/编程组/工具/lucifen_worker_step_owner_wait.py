from lucifen_worker_step_owner_state import WorkerStepOwnerState


class WorkerStepOwnerWait(WorkerStepOwnerState):
    def wait_next(self, timeout=10):
        self._assert_owner()
        if self._parked:
            raise RuntimeError("worker step owner already parked")
        result = self._gate.wait_park(self._generation + 1, timeout)
        if result is None:
            return None
        self._generation += 1
        self._parked = True
        self._payload = result
        return result

from lucifen_worker_step_owner_wait import WorkerStepOwnerWait


class WorkerStepOwner(WorkerStepOwnerWait):
    def release(self, command):
        self._assert_owner()
        if not self._parked:
            raise RuntimeError("worker step owner is not parked")
        self._gate.release(self._generation, command)
        self._parked = False
        self._payload = None

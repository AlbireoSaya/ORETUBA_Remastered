from lucifen_worker_step_owner import WorkerStepOwner

def raises(exc, fn):
    try: fn()
    except exc: return
    raise AssertionError("expected " + exc.__name__)

class DummyGate:
    def __init__(self):
        self.n, self.payload, self.released = 0, {"ok": 1}, []
    def wait_park(self, gen, timeout):
        self.n += 1
        return None if self.n == 1 else self.payload
    def release(self, gen, command):
        if command not in ("continue", "finish"): raise ValueError(command)
        self.released.append((gen, command))

gate = DummyGate()
owner = WorkerStepOwner(gate)
assert owner.wait_next(10) is None and owner.generation == 0
raises(RuntimeError, lambda: owner.payload)
raises(RuntimeError, lambda: owner.release("continue"))
assert owner.wait_next(10) == gate.payload and owner.generation == 1
raises(RuntimeError, lambda: owner.wait_next(10))
raises(ValueError, lambda: owner.release("bogus"))
assert owner.generation == 1 and owner.payload == gate.payload
assert owner.release("continue") is None
raises(RuntimeError, lambda: owner.payload)
raises(RuntimeError, lambda: owner.release("continue"))
assert owner.wait_next(10) == gate.payload and owner.generation == 2
assert owner.release("finish") is None

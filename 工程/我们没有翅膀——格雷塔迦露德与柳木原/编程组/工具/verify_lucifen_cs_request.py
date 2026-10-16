from lucifen_cooperative_cs_request import CriticalYieldRequest

def raises(e, f):
    try:
        f()
    except e:
        return
    raise AssertionError("not raised")

r = CriticalYieldRequest()
r.request(1, 2, 3)
assert r.pending == (1, 2, 3)
assert r.released(1, 2, 1) is None
assert r.pending == (1, 2, 3)
assert r.released(9, 2, 0) is None
assert r.pending == (1, 2, 3)
assert r.released(1, 9, 0) is None
assert r.pending == (1, 2, 3)
assert r.released(1, 2, 0) == (1, 2, 3)
assert r.pending is None
raises(RuntimeError, lambda: (r.request(1, 2, 3), r.request(4, 5, 6)))
assert r.pending == (1, 2, 3)
assert r.cancel() == (1, 2, 3)
assert r.pending is None
raises(ValueError, lambda: CriticalYieldRequest().request(True, 1, 2))
raises(ValueError, lambda: CriticalYieldRequest().request(1, 2, 2))
raises(ValueError, lambda: CriticalYieldRequest().released(1, 2, True))
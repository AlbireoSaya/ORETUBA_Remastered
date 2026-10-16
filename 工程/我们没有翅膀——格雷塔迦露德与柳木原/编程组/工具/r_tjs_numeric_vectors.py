import random
from lucifen_inline_vm_reference import value_op

def numeric_cases():
    vals = [0, 1, 0x7fffffff, 0x80000000, 0xffffffff, 0xfffffffe, 0x80000001, -1, -0x80000000, 0x100000000]
    binary = [13, 19, 20, 41, 44, 45]
    cases = []
    for op in binary:
        for a in vals:
            for b in vals:
                cases.append({"op": op, "a": a, "b": b, "expected": value_op(op, a, b)})
    rng = random.Random(0x54a7)
    for _ in range(128):
        a = rng.getrandbits(32)
        b = rng.getrandbits(32)
        for op in binary:
            cases.append({"op": op, "a": a, "b": b, "expected": value_op(op, a, b)})
    for a in vals:
        cases.append({"op": 23, "a": a, "b": 0, "expected": value_op(23, a, 0)})
    return cases
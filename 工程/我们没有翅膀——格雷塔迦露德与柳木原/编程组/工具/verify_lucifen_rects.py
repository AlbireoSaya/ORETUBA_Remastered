import json
from copy import deepcopy
from lucifen_verify_rect_union import rect_union_spans

def main():
    rects = [[0, 0, 2, 2], [1, 1, 4, 3]]
    snap = deepcopy(rects)
    got = rect_union_spans(4, 3, rects)
    assert got == [(0, 0, 2), (1, 0, 4), (2, 1, 4)], got
    assert rects == snap, "input mutated"
    assert rect_union_spans(4, 3, []) == []
    for bad in ([[0, 0, True, 2]], [[-1, 0, 2, 2]], [[1, 1, 1, 2]]):
        try:
            rect_union_spans(4, 3, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError: %r" % (bad,))
    try:
        rect_union_spans(True, 3, [])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: bool width")
    print(json.dumps({"passed": True, "testedscope": "rect_union_spans union, immutability, empty, invalid"}))

if __name__ == "__main__":
    main()
